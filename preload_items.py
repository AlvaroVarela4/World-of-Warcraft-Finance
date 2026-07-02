"""
Precarga masiva del catálogo de items desde la API de Blizzard.

Itera por cada clase de item (Arma, Armadura, Consumible, etc.) para evitar
el límite de 1.000 resultados del endpoint de búsqueda genérico.

Uso:
    python preload_items.py
"""
import logging
from sqlalchemy.dialects.postgresql import insert

from app.collector.blizzard_client import BlizzardClient
from app.config import settings
from app.database.session import init_db, SessionLocal
from app.database.models import Item

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# IDs de clase de item en WoW (obtenidos de /data/wow/item-class/index)
ITEM_CLASS_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19, 20]


def fetch_class(client: BlizzardClient, class_id: int) -> list[dict]:
    """Descarga todos los items de una clase paginando hasta agotar resultados."""
    rows: list[dict] = []
    page = 1
    while True:
        data = client._get("/data/wow/search/item", settings.static_namespace, {
            "_pageSize": 1000,
            "_page": page,
            "orderby": "id",
            "item_class.id": class_id,
        })
        results = data.get("results", [])
        if not results:
            break

        for r in results:
            d = r.get("data", {})
            name_obj = d.get("name") or {}
            name = name_obj.get("es_ES") or name_obj.get("en_US")
            quality = (d.get("quality") or {}).get("type")
            cls_name = ((d.get("item_class") or {}).get("name") or {})
            item_class = cls_name.get("es_ES") or cls_name.get("en_US")
            subclass_name = ((d.get("item_subclass") or {}).get("name") or {})
            item_subclass = subclass_name.get("es_ES") or subclass_name.get("en_US")
            inv_name = ((d.get("inventory_type") or {}).get("name") or {})
            inventory_type = inv_name.get("es_ES") or inv_name.get("en_US")
            rows.append({
                "id":              d["id"],
                "name":            name,
                "quality":         quality,
                "item_class":      item_class,
                "item_subclass":   item_subclass,
                "inventory_type":  inventory_type,
                "icon":            None,
            })

        page_count = data.get("pageCount", 1)
        capped = data.get("resultCountCapped", False)
        logger.info("    Clase %s, página %s/%s (%s items)%s",
                    class_id, page, page_count, len(results),
                    " [cap]" if capped else "")

        if page >= page_count:
            break
        page += 1

    return rows


def upsert(rows: list[dict]) -> None:
    if not rows:
        return
    with SessionLocal() as session:
        stmt = insert(Item).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name":            stmt.excluded.name,
                "quality":         stmt.excluded.quality,
                "item_class":      stmt.excluded.item_class,
                "item_subclass":   stmt.excluded.item_subclass,
                "inventory_type":  stmt.excluded.inventory_type,
                # icon no se sobreescribe si ya fue resuelto
            },
        )
        session.execute(stmt)
        session.commit()


def preload_all_items() -> None:
    init_db()
    client = BlizzardClient()
    total = 0
    try:
        for class_id in ITEM_CLASS_IDS:
            logger.info("Procesando clase %s...", class_id)
            rows = fetch_class(client, class_id)
            upsert(rows)
            total += len(rows)
            logger.info("  → %s items en clase %s (total: %s)", len(rows), class_id, total)

        logger.info("Precarga completada: %s items en total.", total)
    finally:
        client.close()


if __name__ == "__main__":
    preload_all_items()
