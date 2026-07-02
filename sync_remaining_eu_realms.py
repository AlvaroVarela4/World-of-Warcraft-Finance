"""
Sincroniza TODOS los connected realms de EU que aún no tienen subastas
cargadas, y a continuación rellena los iconos que falten para los items
que ya aparecen en alguna subasta real.

No requiere lista de nombres: descubre automáticamente qué reinos EU del
registro (`python sync.py`) aún no se han sincronizado.

Uso:
    python sync_remaining_eu_realms.py
"""
import logging

from sqlalchemy import select, distinct

from app.collector.blizzard_client import BlizzardClient
from app.collector.collector import save_realm_auctions
from app.collector.items import (
    resolve_items,
    item_ids_in_snapshot,
    items_missing_icon_with_auctions,
    resolve_missing_icons,
)
from app.database.session import init_db, SessionLocal
from app.database.models import Realm, Snapshot
from app.services.analysis import latest_realm_snapshot_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def pending_eu_connected_realm_ids() -> list[int]:
    with SessionLocal() as session:
        all_eu = set(
            session.scalars(
                select(distinct(Realm.connected_realm_id)).where(Realm.region == "eu")
            ).all()
        )
        already = set(
            session.scalars(
                select(distinct(Snapshot.connected_realm_id)).where(Snapshot.source == "realm")
            ).all()
        )
    return sorted(all_eu - already - {None})


def sync_remaining(client: BlizzardClient) -> tuple[int, list[int]]:
    ids = pending_eu_connected_realm_ids()
    logger.info("Connected realms EU pendientes: %s", len(ids))
    ok, failed = 0, []
    for n, cr_id in enumerate(ids, 1):
        try:
            count = save_realm_auctions(client, cr_id)
            logger.info("  [%s/%s] realm %s: %s subastas guardadas", n, len(ids), cr_id, count)
            ok += 1
        except Exception as exc:
            logger.error("  [%s/%s] realm %s: FALLÓ (%s)", n, len(ids), cr_id, exc)
            failed.append(cr_id)
    return ok, failed


def resolve_new_items(client: BlizzardClient, synced_ids: list[int]) -> None:
    logger.info("Resolviendo metadatos de items nuevos...")
    for cr_id in synced_ids:
        snap_id = latest_realm_snapshot_id(cr_id)
        if snap_id:
            ids = item_ids_in_snapshot(snap_id)
            resolve_items(client, ids)


def backfill_icons(client: BlizzardClient) -> None:
    missing = items_missing_icon_with_auctions()
    logger.info("Items con subastas y sin icono: %s", len(missing))
    resolve_missing_icons(client, missing)


def main() -> None:
    init_db()
    client = BlizzardClient()
    try:
        ids_before = pending_eu_connected_realm_ids()
        ok, failed = sync_remaining(client)
        synced_ids = [i for i in ids_before if i not in failed]

        resolve_new_items(client, synced_ids)
        backfill_icons(client)
    finally:
        client.close()

    logger.info("Proceso completo. Reinos sincronizados: %s. Fallos: %s", ok, failed or "ninguno")


if __name__ == "__main__":
    main()
