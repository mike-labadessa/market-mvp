import asyncio,json
from openai import AsyncOpenAI
from google import genai
from app.config import settings

SYSTEM_PROMPT="""You are an enterprise investment banking research analyst. Provide decision-support research only, not financial advice. Analyze the full merged multi-ticker dataset together. Do not stop after the first ticker. Compare every ticker against the others. Return a structured output with: Portfolio Summary, Ranking Table, Per-Ticker Thesis, Buy/Hold/Sell Decision-Support Signal, Key Risks, Data Gaps, Diligence Questions. Every ticker must receive a Buy, Hold, or Sell signal with a short rationale based only on supplied data."""
def pct(a,b):
    try:
        return None if a in (None,0) or b in (None,0) else (a-b)/b*100
    except Exception:
        return None

def latest(rows,key):
    vals=[r.get(key) for r in rows or [] if r.get(key) is not None]
    return vals[-1] if vals else None

def signal_from_score(score):
    if score is None:
        return "HOLD"
    if score >= 70:
        return "BUY"
    if score <= 40:
        return "SELL"
    return "HOLD"

def score_stock(m):
    score = 50

    if (m.get("price_90d_change_pct") or 0) > 10:
        score += 8
    if (m.get("price_90d_change_pct") or 0) < -10:
        score -= 8
    if (m.get("gross_margin_pct") or 0) > 40:
        score += 8
    if (m.get("net_margin_pct") or 0) > 15:
        score += 8
    if (m.get("ocf_margin_pct") or 0) > 15:
        score += 8
    if (m.get("liabilities_to_assets_pct") or 0) > 75:
        score -= 10
    if (m.get("operating_cash_flow") or 0) < 0:
        score -= 15
    if (m.get("net_income") or 0) < 0:
        score -= 15

    return max(0, min(100, score))

def enrich_payload(payload):
    merged=[]

    for item in payload.get("results",[]):
        history=item.get("price_history",[])
        closes=[r.get("close") for r in history if r.get("close") is not None]
        vols=[r.get("volume") for r in history if r.get("volume") is not None]

        inc=item.get("fundamentals",{}).get("latest_income_statement") or {}
        bal=item.get("fundamentals",{}).get("latest_balance_sheet") or {}
        cf=item.get("fundamentals",{}).get("latest_cash_flow_statement") or {}

        revenue=inc.get("revenue")
        gross_profit=inc.get("gross_profit")
        operating_income=inc.get("operating_income")
        ebitda=inc.get("ebitda")
        net_income=inc.get("net_income_loss_attributable_common_shareholders") or inc.get("consolidated_net_income_loss") or inc.get("net_income")
        operating_cash_flow=cf.get("net_cash_from_operating_activities") or cf.get("cash_from_operating_activities_continuing_operations")
        assets=bal.get("assets") or bal.get("total_assets")
        liabilities=bal.get("liabilities") or bal.get("total_liabilities")

        metrics={
            "ticker":item.get("ticker"),
            "news":[{"title":n.get("title"),"description":n.get("description"),"published_utc":n.get("published_utc"),"publisher":(n.get("publisher") or {}).get("name"),"sentiment_insights":n.get("insights",[]),"keywords":n.get("keywords",[])} for n in item.get("news",[])[:5]],
            "latest_price":closes[-1] if closes else None,
            "price_30d_change_pct":pct(closes[-1],closes[-31]) if len(closes)>31 else None,
            "price_90d_change_pct":pct(closes[-1],closes[-91]) if len(closes)>91 else None,
            "price_1y_change_pct":pct(closes[-1],closes[-253]) if len(closes)>253 else None,
            "avg_volume_30d":sum(vols[-30:])/len(vols[-30:]) if len(vols)>=30 else None,
            "revenue":revenue,
            "gross_profit":gross_profit,
            "operating_income":operating_income,
            "ebitda":ebitda,
            "net_income":net_income,
            "operating_cash_flow":operating_cash_flow,
            "assets":assets,
            "liabilities":liabilities,
            "gross_margin_pct":pct(gross_profit,revenue),
            "operating_margin_pct":pct(operating_income,revenue),
            "ebitda_margin_pct":pct(ebitda,revenue),
            "net_margin_pct":pct(net_income,revenue),
            "ocf_margin_pct":pct(operating_cash_flow,revenue),
            "liabilities_to_assets_pct":pct(liabilities,assets),
            "dividend_count":len(item.get("corporate_actions",{}).get("dividends",[])),
            "split_count":len(item.get("corporate_actions",{}).get("splits",[])),
            "endpoint_health":item.get("endpoint_health")
        }

        metrics["model_score"]=score_stock(metrics)
        metrics["decision_support_signal"]=signal_from_score(metrics["model_score"])
        merged.append(metrics)

    ranked=sorted(merged,key=lambda x:x.get("model_score") or 0,reverse=True)

    return {
        "universe":payload.get("tickers"),
        "count":payload.get("count"),
        "merged_multi_ticker_analysis":ranked,
        "ranking_instructions":"Compare all tickers together. Do not analyze only the first ticker. Every ticker must have a Buy/Hold/Sell decision-support signal."
    }

def compact_context(payload):
    return json.dumps(enrich_payload(payload),default=str)[:20000]

async def openai_research(payload):
    if not settings.OPENAI_API_KEY:return {"provider":"openai","ok":False,"text":"OPENAI_API_KEY not configured."}
    client=AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    r=await client.responses.create(model="gpt-4.1-mini",input=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":"Analyze this market/fundamental dataset for enterprise decision support:\n"+compact_context(payload)}])
    return {"provider":"openai","ok":True,"text":r.output_text}

async def gemini_research(payload):
    if not settings.GEMINI_API_KEY:return {"provider":"gemini","ok":False,"text":"GEMINI_API_KEY not configured."}
    def run():
        client=genai.Client(api_key=settings.GEMINI_API_KEY)
        r=client.models.generate_content(model="gemini-2.5-flash",contents=SYSTEM_PROMPT+"\n\nAnalyze this market/fundamental dataset for enterprise decision support:\n"+compact_context(payload))
        return r.text
    text=await asyncio.to_thread(run)
    return {"provider":"gemini","ok":True,"text":text}

async def analyze_research(payload):
    a,b=await asyncio.gather(openai_research(payload),gemini_research(payload))
    return {"disclaimer":"Decision-support research only. Not financial advice.","openai":a,"gemini":b}