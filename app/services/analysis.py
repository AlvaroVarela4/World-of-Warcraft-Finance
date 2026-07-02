import logging
from statistics import median

from sqlalchemy import select, func, distinct

from app.utils.currency import format_price             # nuevo import arriba


from app.database.session import SessionLocal
from app.database.models import Snapshot, Auction, Realm, Item

logger = logging.getLogger(__name__)


def latest_snapshot_id(source: str = "commodities") -> int | None:
    """ID del snapshot más reciente de un tipo dado."""
    with SessionLocal() as session:
        return session.scalar(
            select(Snapshot.id)
            .where(Snapshot.source == source)
            .order_by(Snapshot.fetched_at.desc())
            .limit(1)
        )


def price_stats_for_item(item_id: int, snapshot_id: int) -> dict | None:
    """Estadísticas de precio de un objeto en un snapshot concreto."""
    with SessionLocal() as session:
        rows = session.execute(
            select(Auction.unit_price, Auction.quantity)
            .where(Auction.snapshot_id == snapshot_id, Auction.item_id == item_id)
        ).all()

    if not rows:
        return None

    prices = [r.unit_price for r in rows]
    total_qty = sum(r.quantity for r in rows)
    return {
        "item_id": item_id,
        "listings": len(prices),
        "total_quantity": total_qty,
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": round(sum(prices) / len(prices)),
        "median_price": round(median(prices)),
    }


def market_overview(snapshot_id: int, limit: int = 20) -> list[dict]:
    """Resumen por objeto: nº de listados y precio mínimo, agregado en la BBDD."""
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Auction.item_id,
                func.count().label("listings"),
                func.sum(Auction.quantity).label("total_quantity"),
                func.min(Auction.unit_price).label("min_price"),
                func.avg(Auction.unit_price).label("avg_price"),
            )
            .where(Auction.snapshot_id == snapshot_id)
            .group_by(Auction.item_id)
            .order_by(func.count().desc())
            .limit(limit)
        ).all()

    return [
        {
            "item_id": r.item_id,
            "listings": r.listings,
            "total_quantity": r.total_quantity,
            "min_price": r.min_price,
            "avg_price": round(r.avg_price),
        }
        for r in rows
    ]
    
def market_overview_named(
    snapshot_id: int,
    limit: int = 20,
    quality: str | None = None,
    item_subclass: str | None = None,
    inventory_type: str | None = None,
) -> list[dict]:
    """Resumen por objeto con nombre legible y precios formateados.

    Los filtros opcionales acotan el universo de items ANTES de quedarnos
    con el top N por volumen, no después (si no, "top 25 y luego filtrar"
    podría devolver muy pocas o ninguna fila).
    """
    with SessionLocal() as session:
        q = (
            select(
                Auction.item_id,
                Item.name,
                Item.quality,
                Item.icon,
                Item.item_class,
                Snapshot.fetched_at,
                func.count().label("listings"),
                func.sum(Auction.quantity).label("total_quantity"),
                func.min(Auction.unit_price).label("min_price"),
                func.percentile_cont(0.5).within_group(Auction.unit_price).label("median_price"),
            )
            .join(Item, Item.id == Auction.item_id, isouter=True)
            .join(Snapshot, Snapshot.id == Auction.snapshot_id)
            .where(Auction.snapshot_id == snapshot_id)
        )
        if quality:
            q = q.where(Item.quality == quality)
        if item_subclass:
            q = q.where(Item.item_subclass == item_subclass)
        if inventory_type:
            q = q.where(Item.inventory_type == inventory_type)

        rows = session.execute(
            q.group_by(Auction.item_id, Item.name, Item.quality, Item.icon, Item.item_class, Snapshot.fetched_at)
            .order_by(func.sum(Auction.quantity).desc())
            .limit(limit)
        ).all()

    return [
        {
            "item_id": r.item_id,
            "name": r.name or f"(item {r.item_id})",  # fallback si no se resolvió
            "quality": r.quality,
            "icon": r.icon,
            "item_class": r.item_class,
            "last_seen": r.fetched_at.isoformat(),
            "listings": r.listings,
            "total_quantity": r.total_quantity,
            "min_price": r.min_price,
            "min_price_fmt": format_price(r.min_price),
            "median_price": round(r.median_price),
            "median_price_fmt": format_price(round(r.median_price)),
        }
        for r in rows
    ]


def all_realms() -> list[dict]:
    """Todos los reinos sincronizados (independientemente de si tienen snapshots)."""
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Realm.connected_realm_id,
                func.min(Realm.name).label("name"),
                func.min(Realm.region).label("region"),
            )
            .group_by(Realm.connected_realm_id)
            .order_by(func.min(Realm.name))
        ).all()
    return [
        {"connected_realm_id": r.connected_realm_id, "name": r.name, "region": r.region}
        for r in rows
    ]


def search_items_by_name(query: str, limit: int = 20) -> list[dict]:
    """Busca items por nombre en el catálogo local (tabla items precargada)."""
    with SessionLocal() as session:
        rows = session.execute(
            select(Item.id, Item.name, Item.quality, Item.item_class, Item.icon)
            .where(Item.name.ilike(f"%{query}%"))
            .order_by(Item.name)
            .limit(limit)
        ).all()
    return [
        {
            "id": r.id,
            "name": r.name or f"(item {r.id})",
            "quality": r.quality,
            "item_class": r.item_class,
            "icon": r.icon,
        }
        for r in rows
    ]


def available_realms() -> list[dict]:
    """Reinos que tienen al menos un snapshot guardado, con nombre legible."""
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Snapshot.connected_realm_id,
                func.min(Realm.name).label("name"),  # un connected realm agrupa varios
            )
            .join(Realm, Realm.connected_realm_id == Snapshot.connected_realm_id)
            .where(Snapshot.source == "realm")
            .group_by(Snapshot.connected_realm_id)
            .order_by(func.min(Realm.name))
        ).all()
    return [{"connected_realm_id": r.connected_realm_id, "name": r.name} for r in rows]


def latest_realm_snapshot_id(connected_realm_id: int) -> int | None:
    """Snapshot más reciente de un reino concreto."""
    with SessionLocal() as session:
        return session.scalar(
            select(Snapshot.id)
            .where(
                Snapshot.source == "realm",
                Snapshot.connected_realm_id == connected_realm_id,
            )
            .order_by(Snapshot.fetched_at.desc())
            .limit(1)
        )


def items_in_realm(connected_realm_id: int, name_filter: str = "", limit: int = 100) -> list[dict]:
    """Items del snapshot más reciente de un reino, filtrados opcionalmente por nombre."""
    with SessionLocal() as session:
        latest_id = session.scalar(
            select(Snapshot.id)
            .where(
                Snapshot.connected_realm_id == connected_realm_id,
                Snapshot.source == "realm",
            )
            .order_by(Snapshot.fetched_at.desc())
            .limit(1)
        )
        if latest_id is None:
            return []

        # Outer join: partimos de Auction para que aparezcan items aunque no
        # estén en la tabla Item todavía (resolve.py no ejecutado para este reino).
        q = (
            select(
                Auction.item_id.label("id"),
                Item.name,
                Item.quality,
            )
            .outerjoin(Item, Item.id == Auction.item_id)
            .where(Auction.snapshot_id == latest_id)
            .group_by(Auction.item_id, Item.name, Item.quality)
        )
        if name_filter:
            q = q.where(Item.name.ilike(f"%{name_filter}%"))
        else:
            # Con nombres resueltos primero; los sin nombre al final
            q = q.order_by(Item.name.is_(None), Item.name, Auction.item_id)

        rows = session.execute(q.limit(limit)).all()

    return [
        {"id": r.id, "name": r.name or f"(item {r.id})", "quality": r.quality}
        for r in rows
    ]


def price_history_for_item(item_id: int, connected_realm_id: int, n_snapshots: int = 60) -> list[dict]:
    """Histórico de precios de un objeto en un reino: min/avg/max por snapshot, orden cronológico."""
    with SessionLocal() as session:
        recent_snapshots = (
            select(Snapshot.id)
            .where(
                Snapshot.connected_realm_id == connected_realm_id,
                Snapshot.source == "realm",
            )
            .order_by(Snapshot.fetched_at.desc())
            .limit(n_snapshots)
            .scalar_subquery()
        )

        rows = session.execute(
            select(
                Snapshot.id,
                Snapshot.fetched_at,
                func.min(Auction.unit_price).label("min_price"),
                func.percentile_cont(0.5).within_group(Auction.unit_price).label("median_price"),
                func.max(Auction.unit_price).label("max_price"),
                func.sum(Auction.quantity).label("total_quantity"),
                func.count().label("listings"),
            )
            .join(Auction, Auction.snapshot_id == Snapshot.id)
            .where(
                Snapshot.id.in_(recent_snapshots),
                Auction.item_id == item_id,
            )
            .group_by(Snapshot.id, Snapshot.fetched_at)
            .order_by(Snapshot.fetched_at.asc())
        ).all()

    return [
        {
            "snapshot_id": r.id,
            "fetched_at": r.fetched_at,
            "min_price": r.min_price,
            "median_price": round(r.median_price),
            "max_price": r.max_price,
            "total_quantity": r.total_quantity,
            "listings": r.listings,
        }
        for r in rows
    ]


_LISTING_SORT_COLUMNS = {
    "unit_price": Auction.unit_price,
    "quantity": Auction.quantity,
}


def current_listings_for_item(
    item_id: int,
    connected_realm_id: int,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "unit_price",
    sort_dir: str = "asc",
) -> dict:
    """Listados individuales del objeto en el último snapshot del reino, paginados y ordenados.

    Devuelve también el total de listados para que el front pueda paginar
    hasta cubrir el volumen total (antes se truncaba siempre a los N más
    baratos sin forma de ver el resto). El orden se aplica en la base de
    datos (no en el cliente) para que sea consistente entre páginas.
    """
    with SessionLocal() as session:
        snapshot = session.execute(
            select(Snapshot.id, Snapshot.fetched_at)
            .where(
                Snapshot.connected_realm_id == connected_realm_id,
                Snapshot.source == "realm",
            )
            .order_by(Snapshot.fetched_at.desc())
            .limit(1)
        ).first()
        if snapshot is None:
            return {"total": 0, "items": []}
        latest_id, fetched_at = snapshot

        total = session.scalar(
            select(func.count())
            .where(Auction.snapshot_id == latest_id, Auction.item_id == item_id)
        )

        column = _LISTING_SORT_COLUMNS.get(sort_by, Auction.unit_price)
        order = column.desc() if sort_dir == "desc" else column.asc()

        rows = session.execute(
            select(Auction.quantity, Auction.unit_price, Auction.time_left)
            .where(Auction.snapshot_id == latest_id, Auction.item_id == item_id)
            .order_by(order)
            .limit(limit)
            .offset(offset)
        ).all()

    return {
        "total": total,
        "items": [
            {
                "quantity": r.quantity,
                "unit_price": r.unit_price,
                "unit_price_fmt": format_price(r.unit_price),
                "time_left": r.time_left or "—",
                "last_seen": fetched_at.isoformat(),
            }
            for r in rows
        ],
    }


def filter_options() -> dict:
    """Valores disponibles para los filtros de la barra lateral.

    Subclase y ranura se acotan a Armadura: es el único item_class donde
    "Tela/Cuero/Malla/Placas" y "Cabeza/Manos/Piernas" tienen sentido como
    filtro; el resto de clases mezclan tipos de arma, materiales de oficio,
    nombres de estadística de gema, etc., que solo añadirían ruido.
    """
    with SessionLocal() as session:
        qualities = sorted(
            session.scalars(select(distinct(Item.quality)).where(Item.quality.isnot(None))).all()
        )
        item_subclasses = sorted(
            session.scalars(
                select(distinct(Item.item_subclass))
                .where(Item.item_class == "Armadura", Item.item_subclass.isnot(None))
            ).all()
        )
        inventory_types = sorted(
            session.scalars(
                select(distinct(Item.inventory_type))
                .where(Item.item_class == "Armadura", Item.inventory_type.isnot(None))
            ).all()
        )

    return {
        "qualities": qualities,
        "item_subclasses": item_subclasses,
        "inventory_types": inventory_types,
    }