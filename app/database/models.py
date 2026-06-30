from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index
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


class Auction(Base):
    __tablename__ = "auctions"

    # PK propia: el ID de subasta de Blizzard no es único entre snapshots
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), index=True)
    item_id: Mapped[int] = mapped_column(index=True)
    quantity: Mapped[int]
    unit_price: Mapped[int]  # en cobre
    time_left: Mapped[str | None]

    snapshot: Mapped["Snapshot"] = relationship(back_populates="auctions")


Index("ix_auctions_item_snapshot", Auction.item_id, Auction.snapshot_id)