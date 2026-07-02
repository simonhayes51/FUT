"""Market ticker — the live price engine.

``apply_tick`` advances every tracked player's BIN by a volatility-scaled random
walk, appends a price point, drifts supply/demand, and fires any price alerts it
crosses. It returns the deltas so the caller can broadcast them.

The same function is driven two ways:

* **In-process** (default, dev/demo) — an asyncio loop in the app lifespan calls
  it every few seconds and pushes updates straight to WebSocket clients.
* **Celery** (production) — a beat task calls it and publishes to Redis, which a
  subscriber fans out to WebSocket clients across all API workers.
"""
from __future__ import annotations

import datetime as dt
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import MarketAnalytics, Player, PriceAlert, PricePoint

_RNG = random.Random()


def apply_tick(db: Session) -> dict:
    """Advance the market by one step. Returns {"prices": [...], "alerts": [...]}."""
    now = dt.datetime.now(dt.timezone.utc)

    # Only players with an analytics row are "tracked" on the live tape — this
    # keeps generic fodder out of the stream.
    rows = db.execute(
        select(Player, MarketAnalytics).join(
            MarketAnalytics, MarketAnalytics.player_id == Player.id
        )
    ).all()

    price_updates: list[dict] = []
    for player, analytics in rows:
        vol = analytics.volatility if analytics else 0.3
        delta = _RNG.gauss(0, vol * 0.012 + 0.003)
        new_price = max(200, int(player.price * (1 + delta)))
        player.price = new_price
        # prev_price is the ~24h baseline set at seed; the day change rolls as we move.
        if player.prev_price:
            player.price_change_pct = round(
                (new_price - player.prev_price) / player.prev_price * 100, 2
            )
        db.add(PricePoint(player_id=player.id, price=new_price, recorded_at=now))

        if analytics:
            analytics.demand = max(5, min(99, analytics.demand + _RNG.randint(-2, 2)))
            analytics.supply = max(5, min(99, analytics.supply + _RNG.randint(-2, 2)))
            analytics.volume = max(100, analytics.volume + _RNG.randint(-150, 200))

        price_updates.append(
            {
                "player_id": player.id,
                "name": player.name,
                "rating": player.rating,
                "price": new_price,
                "price_change_pct": player.price_change_pct,
            }
        )

    # Fire any alerts the new prices crossed (one-shot: deactivate on trigger).
    alert_events: list[dict] = []
    active = db.scalars(select(PriceAlert).where(PriceAlert.is_active.is_(True))).all()
    price_by_id = {u["player_id"]: u for u in price_updates}
    for alert in active:
        upd = price_by_id.get(alert.player_id)
        if upd is None:
            continue
        price = upd["price"]
        hit = (
            (alert.direction == "below" and price <= alert.target_price)
            or (alert.direction == "above" and price >= alert.target_price)
        )
        if hit:
            alert.is_active = False
            alert_events.append(
                {
                    "player_id": alert.player_id,
                    "name": upd["name"],
                    "price": price,
                    "target": alert.target_price,
                    "direction": alert.direction,
                }
            )

    db.commit()
    return {
        "type": "tick",
        "ts": now.isoformat(),
        "prices": price_updates,
        "alerts": alert_events,
    }
