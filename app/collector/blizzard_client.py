import logging
import httpx

from app.config import settings
from app.collector.auth import BlizzardAuth

logger = logging.getLogger(__name__)


class BlizzardClient:
    def __init__(self, auth: BlizzardAuth | None = None) -> None:
        self.auth = auth or BlizzardAuth()
        self._client = httpx.Client(base_url=settings.api_base_url, timeout=60)

    def _get(self, path: str, namespace: str, params: dict | None = None) -> dict:
        params = params or {}
        params.update({"namespace": namespace, "locale": settings.blizzard_locale})
        headers = {"Authorization": f"Bearer {self.auth.get_token()}"}
        response = self._client.get(path, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_connected_realms(self) -> dict:
        return self._get("/data/wow/connected-realm/index", settings.dynamic_namespace)

    def get_auctions(self, connected_realm_id: int) -> dict:
        return self._get(
            f"/data/wow/connected-realm/{connected_realm_id}/auctions",
            settings.dynamic_namespace,
        )

    def get_commodities(self) -> dict:
        # subastas de materiales/consumibles, a nivel de toda la región
        return self._get("/data/wow/auctions/commodities", settings.dynamic_namespace)

    def close(self) -> None:
        self._client.close()