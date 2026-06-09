import httpx
from app.config import settings

class FredClient:
    def __init__(self,http_client:httpx.AsyncClient):
        self.http_client=http_client
        self.api_key=settings.FRED_API_KEY

    async def latest_rate(self,series_id:str):
        if not self.api_key:
            return None
        r=await self.http_client.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id":series_id,
                "api_key":self.api_key,
                "file_type":"json",
                "sort_order":"desc",
                "limit":10
            },
            timeout=30
        )
        r.raise_for_status()
        for obs in r.json().get("observations",[]):
            try:
                return float(obs["value"])/100
            except Exception:
                continue
        return None