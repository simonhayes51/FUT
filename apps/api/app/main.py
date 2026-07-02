"""FC Edge API — FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import club, dashboard, market, players, sbc
from .schemas import HealthOut

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on boot. Production uses Alembic migrations (Phase 1 backlog)
    # but create_all keeps local/dev and CI single-command.
    Base.metadata.create_all(bind=engine)
    yield


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


@app.get("/api/v1/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    return HealthOut(status="ok", environment=settings.environment)
