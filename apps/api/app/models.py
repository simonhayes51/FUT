"""SQLAlchemy models — the core FC Edge schema.

The schema is deliberately normalised around three domains:

* **Catalogue** – players and their static attributes.
* **Market** – time-series prices plus derived analytics snapshots.
* **User** – portfolio, trades, watchlists and alerts.

Price history is the highest-volume table; in production it is partitioned by
month and fed materialised views for the hourly/daily/weekly/monthly graphs.
Here we keep it as a plain table so the same models run on SQLite.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    rating: Mapped[int] = mapped_column(Integer, index=True)
    position: Mapped[str] = mapped_column(String(8))
    club: Mapped[str] = mapped_column(String(80))
    league: Mapped[str] = mapped_column(String(80), index=True)
    nation: Mapped[str] = mapped_column(String(80), index=True)
    card_type: Mapped[str] = mapped_column(String(40), default="Gold")  # Gold/Icon/TOTW…
    image_url: Mapped[str | None] = mapped_column(String(400), nullable=True)

    # Denormalised "latest price" columns so listing pages never have to join
    # the price_history table. Kept in sync by the ingest/seed job.
    price: Mapped[int] = mapped_column(Integer, default=0)
    price_change_pct: Mapped[float] = mapped_column(Float, default=0.0)
    prev_price: Mapped[int] = mapped_column(Integer, default=0)

    prices: Mapped[list["PricePoint"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
    analytics: Mapped["MarketAnalytics | None"] = relationship(
        back_populates="player", uselist=False, cascade="all, delete-orphan"
    )


class PricePoint(Base):
    """A single (player, timestamp) BIN price observation."""

    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint("player_id", "recorded_at", name="uq_price_player_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    price: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)

    player: Mapped[Player] = relationship(back_populates="prices")


class MarketAnalytics(Base):
    """Derived intelligence snapshot for a player.

    In production this is refreshed by a Celery job from the price series and
    market signals (SBC calendar, promo demand, supply). Here it is seeded.
    """

    __tablename__ = "market_analytics"

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    lowest_bin: Mapped[int] = mapped_column(Integer, default=0)
    highest_bin: Mapped[int] = mapped_column(Integer, default=0)
    volume: Mapped[int] = mapped_column(Integer, default=0)
    supply: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    demand: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    volatility: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1

    buy_score: Mapped[int] = mapped_column(Integer, default=0)
    sell_score: Mapped[int] = mapped_column(Integer, default=0)
    hold_score: Mapped[int] = mapped_column(Integer, default=0)

    player: Mapped[Player] = relationship(back_populates="analytics")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    provider: Mapped[str] = mapped_column(String(20), default="email")  # google/apple/discord
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    coin_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    investments: Mapped[list["Investment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    watchlist: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["PriceAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Investment(Base):
    """An open position the user is holding for profit."""

    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    buy_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    opened_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="investments")
    player: Mapped[Player] = relationship()


class Trade(Base):
    """A completed buy→sell cycle, used for performance analytics."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    buy_price: Mapped[int] = mapped_column(Integer)
    sell_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    closed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="trades")
    player: Mapped[Player] = relationship()

    # EA charges 5% market tax on every sale.
    EA_TAX = 0.05

    @property
    def net_profit(self) -> int:
        gross = self.sell_price * self.quantity
        tax = round(gross * self.EA_TAX)
        return gross - tax - (self.buy_price * self.quantity)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "player_id", name="uq_watch_user_player"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    added_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="watchlist")
    player: Mapped[Player] = relationship()


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    # "above" fires when price >= target, "below" when price <= target.
    direction: Mapped[str] = mapped_column(String(8), default="below")
    target_price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="alerts")
    player: Mapped[Player] = relationship()


class SBC(Base):
    __tablename__ = "sbcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(60), default="Player")
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    requirements: Mapped[str] = mapped_column(Text, default="")  # JSON-encoded
    reward: Mapped[str] = mapped_column(String(160), default="")
    estimated_cost: Mapped[int] = mapped_column(Integer, default=0)
    pack_value: Mapped[int] = mapped_column(Integer, default=0)
    value_rating: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium")
    repeatable: Mapped[bool] = mapped_column(Boolean, default=False)
