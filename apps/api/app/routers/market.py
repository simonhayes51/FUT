"""Market Scanner — the continuously-updating opportunity feed.

Each endpoint returns a ranked ``ScannerRow`` list. The frontend renders these
as the homepage tiles (Best Investments, Fastest Risers, …). Ranking here runs
in Python over the seeded set; at scale these become materialised views keyed
off the analytics snapshots.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import rate_player
from ..database import get_db
from ..models import MarketAnalytics, Player, PricePoint
from ..schemas import PlayerSummary, ScannerRow

router = APIRouter(prefix="/market", tags=["market"])


def _load(db: Session) -> list[tuple[Player, MarketAnalytics | None, list[PricePoint]]]:
    players = db.scalars(select(Player)).all()
    rows = []
    for p in players:
        analytics = db.get(MarketAnalytics, p.id)
        prices = db.scalars(
            select(PricePoint)
            .where(PricePoint.player_id == p.id)
            .order_by(PricePoint.recorded_at)
        ).all()
        rows.append((p, analytics, list(prices)))
    return rows


def _row(player: Player, metric: float, label: str) -> ScannerRow:
    return ScannerRow(
        player=PlayerSummary.model_validate(player),
        metric=round(metric, 2),
        label=label,
    )


@router.get("/scanner", response_model=dict[str, list[ScannerRow]])
def scanner(limit: int = Query(default=8, ge=1, le=25), db: Session = Depends(get_db)):
    """Return every scanner category in a single call (dashboard payload)."""
    data = _load(db)

    rated = []
    for player, analytics, prices in data:
        has_sbc = bool(analytics and analytics.demand - analytics.supply > 25)
        ai = rate_player(player, prices, analytics, has_upcoming_sbc=has_sbc)
        rated.append((player, analytics, ai))

    def top(key, label, reverse=True):
        ordered = sorted(rated, key=key, reverse=reverse)[:limit]
        return [_row(p, float(key((p, a, ai))), label) for p, a, ai in ordered]

    best_investments = top(
        lambda t: t[2].score, "AI Investment Score"
    )
    fastest_risers = top(
        lambda t: t[0].price_change_pct, "24h % change"
    )
    fastest_fallers = top(
        lambda t: t[0].price_change_pct, "24h % change", reverse=False
    )
    highest_volume = top(
        lambda t: (t[1].volume if t[1] else 0), "Market volume"
    )
    highest_profit = top(
        lambda t: t[2].expected_roi_pct, "Expected ROI %"
    )
    undervalued = top(
        lambda t: (t[1].demand - t[1].supply if t[1] else 0), "Demand pressure"
    )

    return {
        "best_investments": best_investments,
        "fastest_risers": fastest_risers,
        "fastest_fallers": fastest_fallers,
        "highest_volume": highest_volume,
        "highest_profit": highest_profit,
        "most_undervalued": undervalued,
    }
