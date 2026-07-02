from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py está en app/, así que subimos dos niveles hasta la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    blizzard_client_id: str
    blizzard_client_secret: str
    blizzard_region: str = "eu"
    blizzard_locale: str = "es_ES"
    database_url: str = "sqlite:///wow_auctions.db"

    # ── Scheduler de histórico de mercado (scheduler.py) ──────────────
    # Blizzard regenera los volcados de subastas aprox. cada hora, así que
    # intervalos menores solo producen respuestas 304 (sin datos nuevos).
    scheduler_interval_minutes: int = 60
    # Nombres de reino separados por comas (ej: "Sanguino,Zul'jin").
    # Vacío = todos los reinos que ya tienen algún snapshot guardado.
    scheduler_realms: str = ""
    # Capturar también el volcado regional de commodities (~200k filas/snapshot)
    scheduler_include_commodities: bool = False

    @property
    def oauth_token_url(self) -> str:
        return "https://oauth.battle.net/token"

    @property
    def api_base_url(self) -> str:
        return f"https://{self.blizzard_region}.api.blizzard.com"

    @property
    def dynamic_namespace(self) -> str:
        return f"dynamic-{self.blizzard_region}"

    @property
    def static_namespace(self) -> str:
        return f"static-{self.blizzard_region}"


settings = Settings()