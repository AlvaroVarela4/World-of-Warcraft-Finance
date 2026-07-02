"""
Sincroniza las subastas de varios reinos en una sola ejecución.

Reutiliza un único cliente (y por tanto un único token OAuth) para todos los
reinos, y resuelve los nombres de los items nuevos al final. Pensado para
escalar de unos pocos reinos a una lista mayor sin cambiar de herramienta.

Requisito previo: el registro de reinos debe existir (`python sync.py`).

Uso:
    python sync_realms_batch.py Sanguino Bloodhoof Zul'jin ...
"""
import logging
import sys

from sqlalchemy import select

from app.collector.blizzard_client import BlizzardClient
from app.collector.collector import save_realm_auctions
from app.collector.items import resolve_items, item_ids_in_snapshot
from app.database.session import init_db, SessionLocal
from app.database.models import Realm
from app.services.analysis import latest_realm_snapshot_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def resolve_connected_realm_ids(names: list[str]) -> dict[str, int]:
    """Mapea nombres de reino -> connected_realm_id, usando el registro local."""
    with SessionLocal() as session:
        rows = session.execute(
            select(Realm.name, Realm.connected_realm_id)
            .where(Realm.name.in_(names))
        ).all()
    found = {r.name: r.connected_realm_id for r in rows}
    missing = set(names) - set(found.keys())
    if missing:
        logger.warning(
            "No se encontraron en el registro: %s (¿nombre exacto? ¿ejecutaste sync.py?)",
            ", ".join(sorted(missing)),
        )
    return found


def sync_batch(realm_names: list[str]) -> None:
    init_db()
    name_to_id = resolve_connected_realm_ids(realm_names)
    if not name_to_id:
        logger.error("Ningún reino válido para sincronizar. Abortando.")
        return

    # varios nombres pueden compartir connected_realm_id; lo sincronizamos una vez
    unique_ids = sorted(set(name_to_id.values()))
    logger.info("Sincronizando %s connected realms: %s", len(unique_ids), unique_ids)

    client = BlizzardClient()
    ok, failed = 0, []
    try:
        for cr_id in unique_ids:
            try:
                count = save_realm_auctions(client, cr_id)
                logger.info("  realm %s: %s subastas guardadas", cr_id, count)
                ok += 1
            except Exception as exc:
                logger.error("  realm %s: FALLÓ (%s)", cr_id, exc)
                failed.append(cr_id)

        # Resolver nombres/iconos de items nuevos vistos en estos snapshots.
        # resolve_items ya deduplica contra lo cacheado, así que items
        # compartidos entre reinos solo se piden una vez a la API.
        logger.info("Resolviendo metadatos de items nuevos...")
        for cr_id in unique_ids:
            if cr_id in failed:
                continue
            snap_id = latest_realm_snapshot_id(cr_id)
            if snap_id:
                ids = item_ids_in_snapshot(snap_id)
                resolve_items(client, ids)
    finally:
        client.close()

    logger.info("Completado: %s/%s reinos sincronizados. Fallos: %s", ok, len(unique_ids), failed or "ninguno")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python sync_realms_batch.py <Reino1> <Reino2> ...")
        print("Ejemplo: python sync_realms_batch.py Sanguino Bloodhoof")
        return
    sync_batch(sys.argv[1:])


if __name__ == "__main__":
    main()
