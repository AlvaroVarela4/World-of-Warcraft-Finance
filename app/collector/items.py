import logging

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.collector.blizzard_client import BlizzardClient
from app.database.session import SessionLocal
from app.database.models import Item, Auction

logger = logging.getLogger(__name__)


def _known_item_ids() -> set[int]:
    with SessionLocal() as session:
        return set(session.scalars(select(Item.id)).all())


def item_ids_in_snapshot(snapshot_id: int) -> set[int]:
    with SessionLocal() as session:
        return set(
            session.scalars(
                select(Auction.item_id)
                .where(Auction.snapshot_id == snapshot_id)
                .distinct()
            ).all()
        )


def resolve_items(client: BlizzardClient, item_ids: set[int]) -> int:
    """Pide a la API solo los items que aún no tenemos cacheados."""
    missing = item_ids - _known_item_ids()
    if not missing:
        logger.info("Todos los items ya estaban cacheados")
        return 0

    logger.info("Resolviendo %s items nuevos (de %s en total)", len(missing), len(item_ids))
    rows: list[dict] = []
    for i, item_id in enumerate(missing, 1):
        try:
            data = client.get_item(item_id)
            icon_url = None
            try:
                media = client.get_item_media(item_id)
                icon_url = next(
                    (a["value"] for a in media.get("assets", []) if a.get("key") == "icon"),
                    None,
                )
            except Exception:
                pass
            rows.append(
                {
                    "id": item_id,
                    "name": data.get("name"),
                    "quality": (data.get("quality") or {}).get("type"),
                    "item_class": (data.get("item_class") or {}).get("name"),
                    "item_subclass": (data.get("item_subclass") or {}).get("name"),
                    "inventory_type": (data.get("inventory_type") or {}).get("name"),
                    "icon": icon_url,
                }
            )
        except Exception as exc:
            logger.warning("No se pudo resolver el item %s: %s", item_id, exc)
            rows.append({
                "id": item_id, "name": None, "quality": None, "item_class": None,
                "item_subclass": None, "inventory_type": None, "icon": None,
            })

        if i % 100 == 0:
            logger.info("  %s/%s", i, len(missing))

    with SessionLocal() as session:
        stmt = insert(Item).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "quality": stmt.excluded.quality,
                "item_class": stmt.excluded.item_class,
                "item_subclass": stmt.excluded.item_subclass,
                "inventory_type": stmt.excluded.inventory_type,
                "icon": stmt.excluded.icon,
            },
        )
        session.execute(stmt)
        session.commit()

    logger.info("Cacheados %s items", len(rows))
    return len(rows)


def items_missing_icon_with_auctions(limit: int | None = None) -> list[int]:
    """Items que ya aparecen en alguna subasta real pero no tienen icono cacheado.

    Acotamos a items con subastas (no todo el catálogo) porque solo esos son
    los que el usuario puede llegar a ver/seleccionar en la app.
    """
    with SessionLocal() as session:
        q = (
            select(Auction.item_id)
            .join(Item, Item.id == Auction.item_id)
            .where(Item.icon.is_(None))
            .distinct()
        )
        if limit:
            q = q.limit(limit)
        return list(session.scalars(q).all())


def resolve_missing_icons(client: BlizzardClient, item_ids: list[int]) -> int:
    """Rellena solo el icono de items que ya tienen nombre/calidad resueltos.

    A diferencia de resolve_items (que pide get_item + get_item_media), aquí
    solo hace falta /media por item: la mitad de llamadas para el mismo
    resultado, ya que el resto de campos viene del catálogo precargado.
    """
    if not item_ids:
        logger.info("No hay items pendientes de icono")
        return 0

    logger.info("Resolviendo icono de %s items", len(item_ids))
    updated = 0
    with SessionLocal() as session:
        for i, item_id in enumerate(item_ids, 1):
            try:
                media = client.get_item_media(item_id)
                icon_url = next(
                    (a["value"] for a in media.get("assets", []) if a.get("key") == "icon"),
                    None,
                )
            except Exception as exc:
                logger.warning("No se pudo resolver el icono del item %s: %s", item_id, exc)
                continue

            if icon_url:
                session.execute(update(Item).where(Item.id == item_id).values(icon=icon_url))
                updated += 1

            if i % 200 == 0:
                logger.info("  %s/%s (commit parcial)", i, len(item_ids))
                session.commit()

        session.commit()

    logger.info("Iconos actualizados: %s/%s", updated, len(item_ids))
    return updated