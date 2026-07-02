"""
Resuelve los nombres e información de los items de la Blizzard API y los
guarda en la tabla `items` para que el dashboard pueda mostrarlos por nombre.

Uso:
    python resolve.py                  # resuelve el último snapshot de commodities
    python resolve.py realm            # resuelve TODOS los snapshots de reino
    python resolve.py realm <snap_id>  # resuelve un snapshot de reino concreto
"""
import logging
import sys

from app.collector.blizzard_client import BlizzardClient
from app.database.session import init_db
from app.collector.items import resolve_items, item_ids_in_snapshot
from app.services.analysis import latest_snapshot_id, available_realms, latest_realm_snapshot_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def resolve_snapshot(client: BlizzardClient, snapshot_id: int, label: str = "") -> None:
    ids = item_ids_in_snapshot(snapshot_id)
    tag = f"[{label}] " if label else ""
    logger.info("%sSnapshot %s → %s items distintos", tag, snapshot_id, len(ids))
    resolve_items(client, ids)


def main() -> None:
    init_db()
    mode = sys.argv[1] if len(sys.argv) > 1 else "commodities"

    client = BlizzardClient()
    try:
        if mode == "commodities":
            snap = latest_snapshot_id("commodities")
            if snap is None:
                print("No hay snapshots de commodities. Ejecuta primero main.py.")
                return
            resolve_snapshot(client, snap, label="commodities")

        elif mode == "realm":
            if len(sys.argv) > 2:
                # snapshot concreto
                snap_id = int(sys.argv[2])
                resolve_snapshot(client, snap_id, label=f"snapshot {snap_id}")
            else:
                # todos los reinos con datos
                realms = available_realms()
                if not realms:
                    print("No hay snapshots de reinos. Ejecuta primero sync_realms_batch.py.")
                    return
                for realm in realms:
                    snap = latest_realm_snapshot_id(realm["connected_realm_id"])
                    if snap:
                        resolve_snapshot(client, snap, label=realm["name"])
        else:
            print(__doc__)
    finally:
        client.close()


if __name__ == "__main__":
    main()
