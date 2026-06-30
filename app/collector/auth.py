import time
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BlizzardAuth:
    """Token OAuth (client credentials) cacheado y renovado al expirar."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def _is_valid(self) -> bool:
        # margen de 60s para no usar un token a punto de caducar
        return self._access_token is not None and time.time() < self._expires_at - 60

    def get_token(self) -> str:
        if self._is_valid():
            return self._access_token

        logger.info("Solicitando nuevo token OAuth a Battle.net")
        response = httpx.post(
            settings.oauth_token_url,
            data={"grant_type": "client_credentials"},
            auth=(settings.blizzard_client_id, settings.blizzard_client_secret),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        self._access_token = payload["access_token"]
        self._expires_at = time.time() + payload["expires_in"]
        logger.info("Token obtenido (expira en %s s)", payload["expires_in"])
        return self._access_token