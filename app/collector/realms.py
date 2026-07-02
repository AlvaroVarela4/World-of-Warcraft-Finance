import logging

from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.collector.blizzard_client import BlizzardClient
from app.database.session import SessionLocal
from app.database.models import Realm

logger = logging.getLogger(__name__)


def sync_realms(client: BlizzardClient) -> int:
    """Descarga todos los connected realms y cachea sus reinos en la BBDD."""
    index = client.get_connected_realms()
    rows: list[dict] = []

    for entry in index["connected_realms"]:
        cr_id = client.extract_id_from_href(entry["href"])
        detail = client.get_connected_realm(cr_id)
        for realm in detail["realms"]:
            rows.append(
                {
                    "id": realm["id"],
                    "connected_realm_id": cr_id,
                    "name": realm["name"],
                    "slug": realm["slug"],
                    "region": settings.blizzard_region,
                    "timezone": realm.get("timezone"),
                }
            )

    with SessionLocal() as session:
        # upsert: si el reino ya existe, actualiza nombre/datos en vez de duplicar
        stmt = insert(Realm).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "connected_realm_id": stmt.excluded.connected_realm_id,
                "name": stmt.excluded.name,
                "slug": stmt.excluded.slug,
                "timezone": stmt.excluded.timezone,
            },
        )
        session.execute(stmt)
        session.commit()

    logger.info("Sincronizados %s reinos", len(rows))
    return len(rows)