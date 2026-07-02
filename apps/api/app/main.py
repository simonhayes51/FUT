"""FC Edge API — FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
import contextlib
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, SessionLocal, engine
from .realtime import manager
from .routers import club, coach, dashboard, market, players, sbc
from .schemas import HealthOut
from .ticker import apply_tick

settings = get_settings()


async def _in_process_ticker() -> None:
    """Dev/demo tape: tick the market and push straight to WebSocket clients."""
    while True:
        await asyncio.sleep(settings.tick_interval_seconds)
        if manager.count == 0:
            continue  # nobody listening — skip the DB write
        # apply_tick is blocking (sync SQLAlchemy); keep it off the event loop.
        update = await asyncio.to_thread(_tick_once)
        await manager.broadcast(update)


def _tick_once() -> dict:
    db = SessionLocal()
    try:
        return apply_tick(db)
    finally:
        db.close()


async def _redis_subscriber() -> None:  # pragma: no cover - needs Redis + Celery
    """Production fan-out: rebroadcast Celery-published ticks to WS clients."""
    import redis.asyncio as aioredis

    from .celery_app import MARKET_CHANNEL

    client = aioredis.from_url(settings.redis_url)
    pubsub = client.pubsub()
    await pubsub.subscribe(MARKET_CHANNEL)
    async for message in pubsub.listen():
        if message.get("type") != "message":
            continue
        with contextlib.suppress(Exception):
            await manager.broadcast(json.loads(message["data"]))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on boot. Production uses Alembic migrations (Phase 1 backlog)
    # but create_all keeps local/dev and CI single-command.
    Base.metadata.create_all(bind=engine)

    task: asyncio.Task | None = None
    if settings.enable_ticker:
        task = asyncio.create_task(_in_process_ticker())
    else:
        # Web workers in production subscribe to Celery-driven ticks instead.
        with contextlib.suppress(Exception):
            task = asyncio.create_task(_redis_subscriber())

    yield

    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="The market-intelligence API powering FC Edge.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(sbc.router, prefix="/api/v1")
app.include_router(club.router, prefix="/api/v1")
app.include_router(coach.router, prefix="/api/v1")


@app.websocket("/api/v1/ws/market")
async def ws_market(ws: WebSocket) -> None:
    """Live market tape: streams {type:'tick', prices:[...], alerts:[...]}."""
    await manager.connect(ws)
    try:
        while True:
            # We don't expect client messages; this just detects disconnects.
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception:
        await manager.disconnect(ws)


@app.get("/api/v1/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    return HealthOut(status="ok", environment=settings.environment)
