import logging

from app.collector.blizzard_client import BlizzardClient
from app.database.session import SessionLocal
from app.database.models import Snapshot, Auction

logger = logging.getLogger(__name__)


def _unit_price(raw: dict) -> int | None:
    # commodities trae unit_price; las subastas de objeto traen buyout (total)
    if "unit_price" in raw:
        return raw["unit_price"]
    if "buyout" in raw:
        qty = raw.get("quantity", 1) or 1
        return raw["buyout"] // qty
    return None  # solo puja, sin compra directa -> lo ignoramos


def save_commodities(client: BlizzardClient) -> int:
    data = client.get_commodities()
    with SessionLocal() as session:
        snapshot = Snapshot(connected_realm_id=None, source="commodities")
        session.add(snapshot)
        session.flush()  # para disponer de snapshot.id

        rows = [
            Auction(
                snapshot_id=snapshot.id,
                item_id=a["item"]["id"],
                quantity=a["quantity"],
                unit_price=price,
                time_left=a.get("time_left"),
            )
            for a in data["auctions"]
            if (price := _unit_price(a)) is not None
        ]
        session.add_all(rows)
        session.commit()
        logger.info("Guardadas %s subastas (snapshot %s)", len(rows), snapshot.id)
        return len(rows)