import math, asyncio
from typing import Any
import httpx
from app.clients.massive_client import MassiveClient
from app.clients.fred_client import FredClient
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
MARKET_BENCHMARKS=["SPY","QQQ","DIA","IWM"]
SECTOR_BENCHMARKS=["XLK","XLF","XLV","XLY","XLP","XLE","XLI","XLB","XLRE","XLU","XLC"]

def pct(a,b):
    try:return None if a in (None,0) or b in (None,0) else (a-b)/b*100
    except Exception:return None

def returns(series):
    return [(series[i]-series[i-1])/series[i-1] for i in range(1,len(series)) if series[i-1] not in (None,0) and series[i] is not None]

def mean(x):return sum(x)/len(x) if x else None

def stdev(x):
    if len(x)<2:return None
    m=mean(x);return math.sqrt(sum((v-m)**2 for v in x)/(len(x)-1))

def annual_return(r):return mean(r)*252 if r else None
def annual_vol(r):return stdev(r)*math.sqrt(252) if len(r)>1 else None

def sharpe(r,rf):
    ar=annual_return(r);vol=annual_vol(r)
    return None if ar is None or not vol else (ar-rf)/vol

def max_drawdown(prices):
    peak=None;worst=0
    for p in prices:
        if p is None:continue
        peak=p if peak is None else max(peak,p)
        if peak:worst=min(worst,(p-peak)/peak)
    return worst*100

def corr(a,b):
    n=min(len(a),len(b));a=a[-n:];b=b[-n:]
    if n<2:return None
    ma,mb=mean(a),mean(b)
    sa=math.sqrt(sum((x-ma)**2 for x in a))
    sb=math.sqrt(sum((y-mb)**2 for y in b))
    return None if not sa or not sb else sum((a[i]-ma)*(b[i]-mb) for i in range(n))/(sa*sb)

def beta(stock,market):
    n=min(len(stock),len(market));stock=stock[-n:];market=market[-n:]
    if n<2:return None
    ms,mm=mean(stock),mean(market)
    var=sum((m-mm)**2 for m in market)
    return None if not var else sum((stock[i]-ms)*(market[i]-mm) for i in range(n))/var

def make_features(prices,lookback=10):
    X=[];y=[]
    for i in range(lookback,len(prices)):
        X.append(prices[i-lookback:i])
        y.append(prices[i])
    return np.array(X),np.array(y)

def forecast_models(prices,horizon,models):
    out={}
    if len(prices)<60:return out
    prices=[float(p) for p in prices if p is not None]
    last=prices[-1]

    if "linear_regression" in models:
        x=np.arange(len(prices)).reshape(-1,1)
        m=LinearRegression().fit(x,prices)
        fp=float(m.predict([[len(prices)+horizon]])[0])
        out["linear_regression"]={"forecast_price":fp,"forecast_change_pct":pct(fp,last)}

    if "moving_average" in models:
        ma=mean(prices[-20:])
        out["moving_average"]={"forecast_price":ma,"forecast_change_pct":pct(ma,last)}

    if "exponential_smoothing" in models:
        alpha=.2;s=prices[0]
        for p in prices[1:]:s=alpha*p+(1-alpha)*s
        out["exponential_smoothing"]={"forecast_price":s,"forecast_change_pct":pct(s,last)}

    if "momentum" in models:
        r=returns(prices[-30:]);avg=mean(r) or 0;fp=last*((1+avg)**horizon)
        out["momentum"]={"forecast_price":fp,"forecast_change_pct":pct(fp,last)}

    X,y=make_features(prices,10)

    if "random_forest" in models and len(X)>30:
        m=RandomForestRegressor(n_estimators=100,random_state=42)
        m.fit(X,y)
        window=np.array(prices[-10:])
        for _ in range(horizon):
            pred=float(m.predict([window])[0])
            window=np.append(window[1:],pred)
        out["random_forest"]={"forecast_price":pred,"forecast_change_pct":pct(pred,last)}

    if "gradient_boosting" in models and len(X)>30:
        m=GradientBoostingRegressor(random_state=42)
        m.fit(X,y)
        window=np.array(prices[-10:])
        for _ in range(horizon):
            pred=float(m.predict([window])[0])
            window=np.append(window[1:],pred)
        out["gradient_boosting"]={"forecast_price":pred,"forecast_change_pct":pct(pred,last)}

    if "arima" in models:
        try:
            m=ARIMA(prices,order=(5,1,0)).fit()
            fp=float(m.forecast(steps=horizon)[-1])
            out["arima"]={"forecast_price":fp,"forecast_change_pct":pct(fp,last)}
        except Exception as e:
            out["arima"]={"error":str(e)}

    return out

async def fetch_benchmark(client,ticker,from_date,to_date):
    try:
        raw=await client.get(f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}",{"adjusted":"true","sort":"asc","limit":50000})
        rows=raw.get("results") or []
        return ticker,[{"date":r.get("t"),"close":r.get("c")} for r in rows]
    except Exception:
        return ticker,[]

async def run_financial_ml_analysis(payload:dict[str,Any]):
    models=payload.get("models") or ["linear_regression","moving_average","exponential_smoothing","momentum"]
    horizon=int(payload.get("horizon_days") or 30)
    from_date=payload.get("from_date")
    to_date=payload.get("to_date")
    tickers=payload.get("tickers") or []
    results=payload.get("results") or []

    risk_free_series=payload.get("risk_free_series") or "DGS3MO"
    rf_fallback=float(payload.get("risk_free_rate") or .045)
    fred_rate=None

    async with httpx.AsyncClient() as h:
        fc=FredClient(h)
        try:fred_rate=await fc.latest_rate(risk_free_series)
        except Exception:fred_rate=None
        mc=MassiveClient(h)
        bench=dict(await asyncio.gather(*[fetch_benchmark(mc,t,from_date,to_date) for t in MARKET_BENCHMARKS+SECTOR_BENCHMARKS]))

    rf=fred_rate if fred_rate is not None else rf_fallback
    spy_prices=[r["close"] for r in bench.get("SPY",[]) if r.get("close") is not None]
    spy_returns=returns(spy_prices)
    market_return=annual_return(spy_returns) or 0

    summary=[]
    stock_returns={}

    for item in results:
        ticker=item.get("ticker")
        prices=[r.get("close") for r in item.get("price_history",[]) if r.get("close") is not None]
        r=returns(prices);stock_returns[ticker]=r
        b=beta(r,spy_returns)
        capm=None if b is None else rf+b*(market_return-rf)
        ar=annual_return(r);vol=annual_vol(r)
        best_sector=None;best_corr=-2

        for s in SECTOR_BENCHMARKS:
            sr=returns([x["close"] for x in bench.get(s,[]) if x.get("close") is not None])
            c=corr(r,sr)
            if c is not None and c>best_corr:best_sector=s;best_corr=c

        score=50
        sh=sharpe(r,rf)
        if sh is not None and sh>1:score+=15
        if ar is not None and ar>market_return:score+=15
        if vol is not None and vol<.35:score+=5
        if max_drawdown(prices)<-30:score-=10

        score=max(0,min(100,score))
        signal="BUY" if score>=70 else "SELL" if score<=40 else "HOLD"

        summary.append({"ticker":ticker,"latest_price":prices[-1] if prices else None,"annual_return_pct":None if ar is None else ar*100,"annual_volatility_pct":None if vol is None else vol*100,"sharpe":sh,"beta_vs_spy":b,"capm_expected_return_pct":None if capm is None else capm*100,"alpha_pct":None if ar is None or capm is None else (ar-capm)*100,"max_drawdown_pct":max_drawdown(prices),"best_sector_benchmark":best_sector,"sector_correlation":best_corr if best_corr!=-2 else None,"decision_support_signal":signal,"model_score":score,"forecasts":forecast_models(prices,horizon,models)})

    starting_fund=float(payload.get("starting_fund") or 10000)

    buy_stocks=[x for x in summary if x.get("decision_support_signal")=="BUY"]
    hold_stocks=[x for x in summary if x.get("decision_support_signal")=="HOLD"]

    if buy_stocks:
        cash_pct=5
        alloc_base=buy_stocks
    elif hold_stocks:
        cash_pct=25
        alloc_base=hold_stocks
    else:
        cash_pct=75
        alloc_base=summary

    investable=starting_fund*(1-cash_pct/100)
    total_score=sum(max(1,x.get("model_score") or 1) for x in alloc_base) or 1

    allocation=[{"ticker":x["ticker"],"weight_pct":(max(1,x.get("model_score") or 1)/total_score)*(100-cash_pct),"dollar_amount":investable*(max(1,x.get("model_score") or 1)/total_score)} for x in alloc_base]
    allocation.append({"ticker":"CASH","weight_pct":cash_pct,"dollar_amount":starting_fund*(cash_pct/100)})

    matrix=[]
    for a in tickers:
        row=[]
        for b in tickers:row.append(corr(stock_returns.get(a,[]),stock_returns.get(b,[])))
        matrix.append(row)

    return {"disclaimer":"Decision-support analytics only. Not financial advice.","recommended_allocation":allocation,"starting_fund":starting_fund,"cash_pct":cash_pct,"risk_free_rate":rf,"risk_free_series":risk_free_series,"risk_free_source":"FRED" if fred_rate is not None else "fallback","models":models,"horizon_days":horizon,"market_benchmark":"SPY","sector_benchmarks":SECTOR_BENCHMARKS,"summary":summary,"correlation_matrix":{"tickers":tickers,"matrix":matrix}}