from typing import Any

import httpx

from app.config import settings


class MassiveClient:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.base_url = settings.MASSIVE_BASE_URL.rstrip("/")
        self.api_key = settings.MASSIVE_API_KEY

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(
                "MASSIVE_API_KEY is not configured. Add it to your .env file."
            )

        request_params = dict(params or {})
        request_params["apiKey"] = self.api_key

        response = await self.http_client.get(
            f"{self.base_url}{path}",
            params=request_params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
