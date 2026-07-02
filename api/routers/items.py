from fastapi import APIRouter, Query, HTTPException

from app.services.analysis import search_items_by_name, filter_options
from app.collector.blizzard_client import BlizzardClient
from app.database.session import SessionLocal
from app.database.models import Item

router = APIRouter()


@router.get("/items/search")
def search_items(q: str = Query("", min_length=0), limit: int = Query(20, le=50)):
    if not q.strip():
        return []
    return search_items_by_name(q.strip(), limit=limit)


@router.get("/items/filters")
def get_filter_options():
    return filter_options()


@router.get("/items/{item_id}/icon")
def get_item_icon(item_id: int):
    """Devuelve el icono del item. Si no está cacheado, lo descarga de Blizzard."""
    with SessionLocal() as session:
        item = session.get(Item, item_id)
        if item and item.icon:
            return {"icon": item.icon}

    client = BlizzardClient()
    try:
        media = client.get_item_media(item_id)
        icon_url = next(
            (a["value"] for a in media.get("assets", []) if a.get("key") == "icon"),
            None,
        )
    except Exception:
        icon_url = None
    finally:
        client.close()

    if icon_url:
        with SessionLocal() as session:
            item = session.get(Item, item_id)
            if item:
                item.icon = icon_url
                session.commit()

    return {"icon": icon_url}


@router.get("/items/{item_id}/tooltip")
def get_item_tooltip(item_id: int):
    """Datos para el tooltip (stats, daño, descripción...). Cachea en BD tras la primera consulta."""
    with SessionLocal() as session:
        item = session.get(Item, item_id)
        if item and item.tooltip_data is not None:
            return item.tooltip_data

    client = BlizzardClient()
    try:
        data = client.get_item(item_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Item no encontrado en la API de Blizzard")
    finally:
        client.close()

    preview = data.get("preview_item", {})

    with SessionLocal() as session:
        item = session.get(Item, item_id)
        if item:
            item.tooltip_data = preview
            session.commit()

    return preview
