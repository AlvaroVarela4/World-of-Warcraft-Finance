import logging
from datetime import datetime, timezone
from email.utils import format_datetime

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

    def _get_if_modified(
        self, path: str, namespace: str, since: datetime | None, params: dict | None = None
    ) -> dict | None:
        """GET condicional con If-Modified-Since.

        Blizzard regenera los volcados de subastas ~1 vez por hora; con este
        header el servidor responde 304 (sin cuerpo) si no hay datos nuevos,
        lo que evita descargar y almacenar snapshots idénticos al anterior.
        Devuelve None en ese caso.
        """
        params = params or {}
        params.update({"namespace": namespace, "locale": settings.blizzard_locale})
        headers = {"Authorization": f"Bearer {self.auth.get_token()}"}
        if since is not None:
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)  # fetched_at se guarda en UTC
            headers["If-Modified-Since"] = format_datetime(
                since.astimezone(timezone.utc), usegmt=True
            )
        response = self._client.get(path, params=params, headers=headers)
        if response.status_code == 304:
            return None
        response.raise_for_status()
        return response.json()

    def get_connected_realms(self) -> dict:                    # plural: índice
        return self._get("/data/wow/connected-realm/index", settings.dynamic_namespace)

    def get_connected_realm(self, connected_realm_id: int) -> dict:   # singular: detalle
        return self._get(
            f"/data/wow/connected-realm/{connected_realm_id}",
            settings.dynamic_namespace,
        )

    def get_auctions(self, connected_realm_id: int, since: datetime | None = None) -> dict | None:
        # con since, devuelve None si Blizzard no ha publicado datos nuevos desde entonces
        return self._get_if_modified(
            f"/data/wow/connected-realm/{connected_realm_id}/auctions",
            settings.dynamic_namespace,
            since,
        )

    def get_commodities(self, since: datetime | None = None) -> dict | None:
        # subastas de materiales/consumibles, a nivel de toda la región
        return self._get_if_modified(
            "/data/wow/auctions/commodities", settings.dynamic_namespace, since
        )



    def get_item(self, item_id: int) -> dict:
        return self._get(f"/data/wow/item/{item_id}", settings.static_namespace)

    def get_item_media(self, item_id: int) -> dict:
        return self._get(f"/data/wow/media/item/{item_id}", settings.static_namespace)

    def search_items(self, page: int = 1, page_size: int = 1000) -> dict:
        return self._get("/data/wow/search/item", settings.static_namespace, {
            "_pageSize": page_size,
            "_page": page,
            "orderby": "id",
        })

    def close(self) -> None:
        self._client.close()
    
    @staticmethod
    def extract_id_from_href(href: str) -> int:
        # ".../connected-realm/1080?namespace=dynamic-eu" -> 1080
        return int(href.rstrip("/").split("/")[-1].split("?")[0])
    
    
    