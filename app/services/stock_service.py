import asyncio
from datetime import date, timedelta
from typing import Any
import httpx

from app.clients.massive_client import MassiveClient


TODAY = date.today()
DEFAULT_FROM = (TODAY - timedelta(days=730)).isoformat()
DEFAULT_TO = TODAY.isoformat()


def parse_tickers(raw: str) -> list[str]:
    normalized = (
        raw.replace("\n", ",")
        .replace(";", ",")
        .replace("|", ",")
        .replace(" ", ",")
    )

    return sorted({
        ticker.strip().upper()
        for ticker in normalized.split(",")
        if ticker.strip()
    })


def safe_number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def nz(value: Any) -> float | None:
    value = safe_number(value)
    return value if value is not None and value > 0 else None


def normalize_endpoint_result(raw: dict[str, Any] | list[Any] | None) -> list[dict[str, Any]]:
    if raw is None:
        return []

    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]

    if isinstance(raw, dict):
        if isinstance(raw.get("results"), list):
            return raw["results"]

        if isinstance(raw.get("results"), dict):
            return [raw["results"]]

    return []


def extract_aggs(raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = (raw or {}).get("results") or []
    cleaned = []

    for row in rows:
        cleaned.append({
            "timestamp": row.get("t"),
            "open": safe_number(row.get("o")),
            "high": safe_number(row.get("h")),
            "low": safe_number(row.get("l")),
            "close": safe_number(row.get("c")),
            "volume": safe_number(row.get("v")),
            "vwap": safe_number(row.get("vw")),
            "transactions": row.get("n"),
        })

    return cleaned


def extract_latest_from_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    result = (snapshot or {}).get("ticker") or (snapshot or {}).get("results") or (snapshot or {})

    day = result.get("day") or {}
    prev_day = result.get("prevDay") or result.get("prev_day") or {}
    last_trade = result.get("lastTrade") or result.get("last_trade") or {}
    last_quote = result.get("lastQuote") or result.get("last_quote") or {}

    last_price = (
        safe_number(last_trade.get("p"))
        or safe_number(day.get("c"))
        or safe_number(prev_day.get("c"))
    )

    previous_close = safe_number(prev_day.get("c"))
    change = None
    change_percent = None

    if last_price is not None and previous_close not in (None, 0):
        change = last_price - previous_close
        change_percent = (change / previous_close) * 100

    return {
        "price": last_price,
        "previous_close": previous_close,
        "change": change,
        "change_percent": change_percent,
        "day_open": safe_number(day.get("o")),
        "day_high": safe_number(day.get("h")),
        "day_low": safe_number(day.get("l")),
        "day_close": safe_number(day.get("c")),
        "day_volume": safe_number(day.get("v")),
        "last_trade_timestamp": last_trade.get("t"),
        "bid": safe_number(last_quote.get("p") or last_quote.get("bp")),
        "ask": safe_number(last_quote.get("P") or last_quote.get("ap")),
    }


def latest_financial_period(rows: list[dict[str, Any]] | None):
    if not rows:
        return None

    def date_key(row):
        return (
            row.get("period_end")
            or row.get("filing_date")
            or row.get("end_date")
            or row.get("report_period")
            or row.get("fiscal_period_end_date")
            or row.get("period_of_report_date")
            or ""
        )

    return sorted(rows, key=date_key, reverse=True)[0]


def analyze_supply_demand(
    quotes: list[dict[str, Any]] | None,
    trades: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    valid_quotes = []

    for q in quotes or []:
        bid = nz(q.get("bid_price") or q.get("bp"))
        ask = nz(q.get("ask_price") or q.get("ap"))
        bid_size = nz(q.get("bid_size") or q.get("bs"))
        ask_size = nz(q.get("ask_size") or q.get("as"))

        valid_quotes.append({
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "raw": q,
        })

    two_sided = next((q for q in valid_quotes if q["bid"] and q["ask"]), None)
    latest = two_sided or (valid_quotes[0] if valid_quotes else {})

    bid = latest.get("bid")
    ask = latest.get("ask")
    bid_size = latest.get("bid_size")
    ask_size = latest.get("ask_size")

    mid = ((bid + ask) / 2) if bid and ask else None
    spread = (ask - bid) if bid and ask else None
    spread_pct = (spread / mid * 100) if spread is not None and mid else None

    bid_depth = sum(q["bid_size"] or 0 for q in valid_quotes)
    ask_depth = sum(q["ask_size"] or 0 for q in valid_quotes)
    quote_imbalance_pct = (
        bid_depth / (bid_depth + ask_depth) * 100
        if bid_depth + ask_depth
        else None
    )

    trade_prices = [nz(t.get("price") or t.get("p")) for t in trades or []]
    trade_prices = [p for p in trade_prices if p is not None]

    trade_sizes = [nz(t.get("size") or t.get("s") or t.get("decimal_size")) for t in trades or []]
    trade_sizes = [s for s in trade_sizes if s is not None]

    avg_trade_price = sum(trade_prices) / len(trade_prices) if trade_prices else None
    trade_volume = sum(trade_sizes) if trade_sizes else None

    trade_pressure = "UNKNOWN"

    if avg_trade_price and mid:
        if avg_trade_price > mid:
            trade_pressure = "BUY_PRESSURE"
        elif avg_trade_price < mid:
            trade_pressure = "SELL_PRESSURE"
        else:
            trade_pressure = "NEUTRAL"
    elif quote_imbalance_pct is not None:
        if quote_imbalance_pct > 60:
            trade_pressure = "BID_DEPTH_DOMINANT"
        elif quote_imbalance_pct < 40:
            trade_pressure = "ASK_DEPTH_DOMINANT"
        else:
            trade_pressure = "BALANCED_DEPTH"

    liquidity_signal = "NEUTRAL"

    if quote_imbalance_pct is not None and quote_imbalance_pct > 60 and trade_pressure in ["BUY_PRESSURE", "BID_DEPTH_DOMINANT"]:
        liquidity_signal = "BULLISH_SUPPLY_DEMAND"
    elif quote_imbalance_pct is not None and quote_imbalance_pct < 40 and trade_pressure in ["SELL_PRESSURE", "ASK_DEPTH_DOMINANT"]:
        liquidity_signal = "BEARISH_SUPPLY_DEMAND"

    return {
        "bid": bid,
        "ask": ask,
        "bid_size": bid_size,
        "ask_size": ask_size,
        "mid": mid,
        "spread": spread,
        "spread_pct": spread_pct,
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "quote_imbalance_pct": quote_imbalance_pct,
        "avg_trade_price": avg_trade_price,
        "trade_volume": trade_volume,
        "trade_pressure": trade_pressure,
        "liquidity_signal": liquidity_signal,
        "quote_count": len(quotes or []),
        "trade_count": len(trades or []),
        "two_sided_quote_found": bool(two_sided),
    }


async def guarded_call(
    client: MassiveClient,
    label: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    try:
        data = await client.get(path, params)
        return label, {"ok": True, "data": data, "error": None}
    except Exception as exc:
        return label, {"ok": False, "data": None, "error": str(exc)}


async def fetch_ticker_bundle(
    client: MassiveClient,
    ticker: str,
    from_date: str,
    to_date: str,
) -> dict[str, Any]:
    calls = [
        guarded_call(
            client,
            "snapshot",
            f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}",
        ),
        guarded_call(
            client,
            "daily_bars",
            f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}",
            {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000,
            },
        ),
        guarded_call(
            client,
            "previous_day",
            f"/v2/aggs/ticker/{ticker}/prev",
            {"adjusted": "true"},
        ),
        guarded_call(
            client,
            "dividends",
            "/stocks/v1/dividends",
            {"ticker": ticker, "limit": 100},
        ),
        guarded_call(
            client,
            "splits",
            "/stocks/v1/splits",
            {"ticker": ticker, "limit": 100},
        ),
        guarded_call(
            client,
            "ratios",
            "/stocks/financials/v1/ratios",
            {"ticker": ticker, "limit": 12},
        ),
        guarded_call(
            client,
            "income_statements",
            "/stocks/financials/v1/income-statements",
            {"tickers": ticker, "limit": 20, "sort": "period_end.desc"},
        ),
        guarded_call(
            client,
            "balance_sheets",
            "/stocks/financials/v1/balance-sheets",
            {"tickers": ticker, "limit": 20, "sort": "period_end.desc"},
        ),
        guarded_call(
            client,
            "cash_flow_statements",
            "/stocks/financials/v1/cash-flow-statements",
            {"tickers": ticker, "limit": 20, "sort": "period_end.desc"},
        ),
        guarded_call(
            client,
            "news",
            "/v2/reference/news",
            {"ticker": ticker, "limit": 5, "order": "desc", "sort": "published_utc"},
        ),
        guarded_call(
            client,
            "quotes",
            f"/v3/quotes/{ticker}",
            {"limit": 100},
        ),
        guarded_call(
            client,
            "trades",
            f"/v3/trades/{ticker}",
            {"limit": 100},
        ),
    ]

    raw_results = dict(await asyncio.gather(*calls))

    snapshot_raw = raw_results["snapshot"]["data"] if raw_results["snapshot"]["ok"] else {}
    bars_raw = raw_results["daily_bars"]["data"] if raw_results["daily_bars"]["ok"] else {}

    ratios = normalize_endpoint_result(raw_results["ratios"]["data"]) if raw_results["ratios"]["ok"] else []
    income = normalize_endpoint_result(raw_results["income_statements"]["data"]) if raw_results["income_statements"]["ok"] else []
    balance = normalize_endpoint_result(raw_results["balance_sheets"]["data"]) if raw_results["balance_sheets"]["ok"] else []
    cash_flow = normalize_endpoint_result(raw_results["cash_flow_statements"]["data"]) if raw_results["cash_flow_statements"]["ok"] else []
    dividends = normalize_endpoint_result(raw_results["dividends"]["data"]) if raw_results["dividends"]["ok"] else []
    splits = normalize_endpoint_result(raw_results["splits"]["data"]) if raw_results["splits"]["ok"] else []
    news = normalize_endpoint_result(raw_results["news"]["data"]) if raw_results["news"]["ok"] else []
    quotes = normalize_endpoint_result(raw_results["quotes"]["data"]) if raw_results["quotes"]["ok"] else []
    trades = normalize_endpoint_result(raw_results["trades"]["data"]) if raw_results["trades"]["ok"] else []

    return {
        "ticker": ticker,
        "overview": extract_latest_from_snapshot(snapshot_raw),
        "price_history": extract_aggs(bars_raw),
        "fundamentals": {
            "latest_income_statement": latest_financial_period(income),
            "latest_balance_sheet": latest_financial_period(balance),
            "latest_cash_flow_statement": latest_financial_period(cash_flow),
            "income_statements": income,
            "balance_sheets": balance,
            "cash_flow_statements": cash_flow,
        },
        "ratios": ratios,
        "corporate_actions": {
            "dividends": dividends,
            "splits": splits,
        },
        "news": news,
        "market_microstructure": {
            "quotes": quotes[:25],
            "trades": trades[:25],
            "supply_demand": analyze_supply_demand(quotes, trades),
        },
        "supply_chain_exposure": {
            "status": "placeholder",
            "message": (
                "Future module: join ticker-level market movement with order book, "
                "supplier, inventory, backlog, lead-time, and demand signal data."
            ),
            "suggested_partitions": [
                "symbol",
                "event_date",
                "source_system",
                "ingestion_hour",
            ],
        },
        "endpoint_health": {
            key: {
                "ok": value["ok"],
                "error": value["error"],
            }
            for key, value in raw_results.items()
        },
    }


async def get_stock_dashboard(
    tickers: str,
    from_date: str = DEFAULT_FROM,
    to_date: str = DEFAULT_TO,
) -> dict[str, Any]:
    parsed = parse_tickers(tickers)

    if not parsed:
        return {
            "count": 0,
            "tickers": [],
            "from_date": from_date,
            "to_date": to_date,
            "results": [],
            "error": "No valid tickers supplied.",
        }

    async with httpx.AsyncClient() as http_client:
        massive_client = MassiveClient(http_client)
        results = await asyncio.gather(*[
            fetch_ticker_bundle(massive_client, ticker, from_date, to_date)
            for ticker in parsed
        ])

    return {
        "count": len(parsed),
        "tickers": parsed,
        "from_date": from_date,
        "to_date": to_date,
        "results": results,
    }
