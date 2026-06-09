from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.services.research_service import analyze_research
from app.config import settings
from app.services.stock_service import DEFAULT_FROM, DEFAULT_TO, get_stock_dashboard
from app.services.financial_ml_service import run_financial_ml_analysis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(
    title="Market MVP ",
    description="Pull-on-demand market data dashboard REST APIs.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this before production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "massive_api_key_configured": bool(settings.MASSIVE_API_KEY),
        "massive_base_url": settings.MASSIVE_BASE_URL,
    }


@app.get("/api/stocks")
async def get_stocks(
    tickers: str = Query(
        ...,
        description="Comma, semicolon, pipe, space, or newline-delimited ticker symbols.",
    ),
    from_date: str = Query(
        DEFAULT_FROM,
        description="Start date for daily aggregate bars, YYYY-MM-DD.",
    ),
    to_date: str = Query(
        DEFAULT_TO,
        description="End date for daily aggregate bars, YYYY-MM-DD.",
    ),
):
    return await get_stock_dashboard(tickers, from_date, to_date)

@app.post("/api/research")
async def research(payload:dict):
    return await analyze_research(payload)

@app.post("/api/financial-ml-analysis")
async def financial_ml_analysis(payload:dict):
    return await run_financial_ml_analysis(payload)
