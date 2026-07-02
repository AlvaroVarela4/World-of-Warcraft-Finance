from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    connected_realm_id: Mapped[int | None] = mapped_column(index=True)
    source: Mapped[str] = mapped_column(default="realm")  # "realm" o "commodities"
    fetched_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    auctions: Mapped[list["Auction"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class Realm(Base):
    __tablename__ = "realms"

    # id del reino "clásico" (no el del connected realm)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    connected_realm_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str]
    slug: Mapped[str]
    region: Mapped[str]
    timezone: Mapped[str | None]
 
    
class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str | None]
    quality: Mapped[str | None] = mapped_column(index=True)
    item_class: Mapped[str | None]
    item_subclass: Mapped[str | None] = mapped_column(index=True)   # "Tela", "Cuero", "Malla", "Placas"...
    inventory_type: Mapped[str | None] = mapped_column(index=True)  # "Cabeza", "Manos", "Piernas"...
    icon: Mapped[str | None]            # URL completa del icono (render.worldofwarcraft.com)
    # JSON crudo del campo "preview_item" de la API (stats, daño de arma,
    # descripciones de consumibles...), listo para pintar un tooltip tipo juego.
    tooltip_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    
class Auction(Base):
    __tablename__ = "auctions"

    # BigInteger: con millones de filas el contador desbordaría un INTEGER
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), index=True)
    item_id: Mapped[int] = mapped_column(index=True)
    quantity: Mapped[int]
    # BigInteger: los precios en cobre superan fácilmente el límite de INTEGER
    unit_price: Mapped[int] = mapped_column(BigInteger)
    time_left: Mapped[str | None]

    snapshot: Mapped["Snapshot"] = relationship(back_populates="auctions")


Index("ix_auctions_item_snapshot", Auction.item_id, Auction.snapshot_id)

