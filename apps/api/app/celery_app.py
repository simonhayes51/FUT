"""Celery app + beat schedule for production price ingest.

In production this runs alongside the API:

    celery -A app.celery_app.celery worker --loglevel=info
    celery -A app.celery_app.celery beat --loglevel=info

The beat task ticks the market and publishes updates to Redis; each API worker
runs a Redis subscriber (see ``main.py``) that fans the updates out to its
WebSocket clients. In dev we skip all of this and tick in-process instead.
"""
from __future__ import annotations

import json

from celery import Celery

from .config import get_settings

settings = get_settings()

celery = Celery(
    "fcedge",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery.conf.beat_schedule = {
    "market-tick": {
        "task": "app.celery_app.market_tick",
        "schedule": settings.tick_interval_seconds,
    }
}
celery.conf.timezone = "UTC"

MARKET_CHANNEL = "fcedge:market"


@celery.task(name="app.celery_app.market_tick")
def market_tick() -> int:
    """Advance the market and publish the deltas to Redis for WS fan-out."""
    import redis

    from .database import SessionLocal
    from .ticker import apply_tick

    db = SessionLocal()
    try:
        update = apply_tick(db)
    finally:
        db.close()

    r = redis.Redis.from_url(settings.redis_url)
    r.publish(MARKET_CHANNEL, json.dumps(update))
    return len(update["prices"])
