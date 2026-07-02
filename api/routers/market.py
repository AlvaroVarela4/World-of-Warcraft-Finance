from fastapi import APIRouter, Query

from app.services.analysis import (
    latest_realm_snapshot_id,
    price_history_for_item,
    current_listings_for_item,
    market_overview_named,
)

router = APIRouter()


@router.get("/market/{realm_id}/overview")
def market_overview(
    realm_id: int,
    limit: int = Query(25, le=50),
    quality: str | None = None,
    item_subclass: str | None = None,
    inventory_type: str | None = None,
):
    snapshot_id = latest_realm_snapshot_id(realm_id)
    if snapshot_id is None:
        return []
    return market_overview_named(
        snapshot_id, limit=limit,
        quality=quality, item_subclass=item_subclass, inventory_type=inventory_type,
    )


@router.get("/market/{realm_id}/history/{item_id}")
def price_history(realm_id: int, item_id: int, n: int = Query(30, le=120)):
    return price_history_for_item(item_id, realm_id, n_snapshots=n)


@router.get("/market/{realm_id}/listings/{item_id}")
def item_listings(
    realm_id: int, item_id: int,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("unit_price", pattern="^(unit_price|quantity)$"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    return current_listings_for_item(
        item_id, realm_id, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir,
    )
