"""Player catalogue, search, detail and price history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import rate_player
from ..database import get_db
from ..models import MarketAnalytics, Player, PricePoint
from ..schemas import (
    AIRatingOut,
    AnalyticsOut,
    PlayerDetail,
    PlayerSummary,
    PricePointOut,
    TaxResult,
)

router = APIRouter(prefix="/players", tags=["players"])

EA_TAX = 0.05


@router.get("", response_model=list[PlayerSummary])
def list_players(
    q: str | None = Query(default=None, description="Name search"),
    league: str | None = None,
    nation: str | None = None,
    min_rating: int = Query(default=0, ge=0, le=99),
    limit: int = Query(default=40, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Player).where(Player.rating >= min_rating)
    if q:
        stmt = stmt.where(Player.name.ilike(f"%{q}%"))
    if league:
        stmt = stmt.where(Player.league == league)
    if nation:
        stmt = stmt.where(Player.nation == nation)
    stmt = stmt.order_by(Player.rating.desc()).offset(offset).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    prices = db.scalars(
        select(PricePoint)
        .where(PricePoint.player_id == player_id)
        .order_by(PricePoint.recorded_at)
    ).all()
    analytics = db.get(MarketAnalytics, player_id)

    # An upcoming SBC catalyst is inferred from strong demand pressure here;
    # in production it is joined from the SBC requirement calendar.
    has_sbc = bool(analytics and analytics.demand - analytics.supply > 25)
    rating = rate_player(player, list(prices), analytics, has_upcoming_sbc=has_sbc)

    detail = PlayerDetail.model_validate(player)
    detail.analytics = (
        AnalyticsOut.model_validate(analytics) if analytics else None
    )
    detail.ai = AIRatingOut(**rating.as_dict())
    detail.history = [
        PricePointOut(price=p.price, recorded_at=p.recorded_at) for p in prices
    ]
    return detail


@router.get("/{player_id}/tax", response_model=TaxResult)
def tax_calculator(player_id: int, sale_price: int = Query(gt=0)):
    """Return the net coins received after EA's 5% market tax."""
    tax = round(sale_price * EA_TAX)
    return TaxResult(sale_price=sale_price, tax=tax, net_received=sale_price - tax)
