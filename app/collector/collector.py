import logging
from datetime import datetime

from sqlalchemy import insert

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


def _save_auctions(connected_realm_id: int | None, source: str, auctions: list[dict]) -> int:
    """Crea un snapshot e inserta sus subastas con un INSERT en bloque.

    Usamos Core (insert() + lista de dicts) en vez de instanciar objetos ORM
    Auction uno a uno: con decenas/cientos de miles de filas por snapshot
    (commodities ronda las 200k), SQLAlchemy agrupa los valores en pocas
    sentencias INSERT en lugar de gestionar cada fila en el unit-of-work,
    lo que reduce la carga de varios minutos a unos segundos.
    """
    with SessionLocal() as session:
        snapshot = Snapshot(connected_realm_id=connected_realm_id, source=source)
        session.add(snapshot)
        session.flush()  # para disponer de snapshot.id

        rows = [
            {
                "snapshot_id": snapshot.id,
                "item_id": a["item"]["id"],
                "quantity": a["quantity"],
                "unit_price": price,
                "time_left": a.get("time_left"),
            }
            for a in auctions
            if (price := _unit_price(a)) is not None
        ]
        if rows:
            session.execute(insert(Auction), rows)
        session.commit()
        return len(rows)


def save_commodities(client: BlizzardClient, since: datetime | None = None) -> int | None:
    """Descarga y guarda las commodities de la región.

    Con `since` (fetched_at del último snapshot), devuelve None sin tocar la
    BD si Blizzard no ha publicado un volcado nuevo desde entonces.
    """
    data = client.get_commodities(since=since)
    if data is None:
        logger.info("Commodities sin cambios desde el último snapshot; no se guarda nada")
        return None
    count = _save_auctions(None, "commodities", data["auctions"])
    logger.info("Guardadas %s subastas (commodities)", count)
    return count


def save_realm_auctions(
    client: BlizzardClient, connected_realm_id: int, since: datetime | None = None
) -> int | None:
    """Descarga y guarda las subastas de un connected realm concreto.

    Con `since` (fetched_at del último snapshot del reino), devuelve None sin
    tocar la BD si Blizzard no ha publicado un volcado nuevo desde entonces.
    """
    data = client.get_auctions(connected_realm_id, since=since)
    if data is None:
        logger.info(
            "Realm %s sin cambios desde el último snapshot; no se guarda nada",
            connected_realm_id,
        )
        return None
    count = _save_auctions(connected_realm_id, "realm", data["auctions"])
    logger.info("Guardadas %s subastas del realm %s", count, connected_realm_id)
    return count