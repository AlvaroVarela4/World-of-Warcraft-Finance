from fastapi import APIRouter, HTTPException

from app.services.analysis import all_realms, latest_realm_snapshot_id
from app.collector.blizzard_client import BlizzardClient
from app.collector.collector import save_realm_auctions
from app.collector.items import resolve_items, item_ids_in_snapshot

router = APIRouter()


@router.get("/realms")
def get_realms():
    return all_realms()


@router.post("/realms/{realm_id}/sync")
def sync_realm_now(realm_id: int):
    """Descarga subastas frescas de Blizzard para este reino y resuelve items nuevos."""
    client = BlizzardClient()
    try:
        try:
            count = save_realm_auctions(client, realm_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"No se pudo consultar la API de Blizzard: {exc}")

        snapshot_id = latest_realm_snapshot_id(realm_id)
        if snapshot_id:
            ids = item_ids_in_snapshot(snapshot_id)
            resolve_items(client, ids)
    finally:
        client.close()

    return {"auctions": count, "snapshot_id": snapshot_id}
