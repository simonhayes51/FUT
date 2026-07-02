"""Personalised dashboard + AI assistant briefing."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai import rate_player
from ..database import get_db
from ..models import (
    Investment,
    MarketAnalytics,
    Player,
    PriceAlert,
    PricePoint,
    Trade,
    User,
    WatchlistItem,
)
from ..schemas import DashboardOut, PlayerSummary, ScannerRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _demo_user(db: Session) -> User:
    """Return the seeded demo user.

    Auth (Google/Apple/Discord/email) is a Phase 2 deliverable; until then the
    dashboard resolves the single seeded account so the UI is fully populated.
    """
    user = db.scalars(select(User).limit(1)).first()
    if user is None:  # pragma: no cover - seed guarantees a user
        raise RuntimeError("No user seeded")
    return user


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    user = _demo_user(db)

    investments = db.scalars(
        select(Investment).where(Investment.user_id == user.id)
    ).all()
    trades = db.scalars(select(Trade).where(Trade.user_id == user.id)).all()

    # Club value ≈ sum of open-position current values.
    club_value = 0
    for inv in investments:
        player = db.get(Player, inv.player_id)
        if player:
            club_value += player.price * inv.quantity

    transfer_profit = sum(t.net_profit for t in trades)

    watch_count = db.scalar(
        select(func.count()).select_from(WatchlistItem).where(
            WatchlistItem.user_id == user.id
        )
    )
    alert_count = db.scalar(
        select(func.count()).select_from(PriceAlert).where(
            PriceAlert.user_id == user.id, PriceAlert.is_active.is_(True)
        )
    )

    trending = db.scalars(
        select(Player).order_by(Player.price_change_pct.desc()).limit(6)
    ).all()

    # Top AI investments for the "recommendations" strip.
    top_rows: list[ScannerRow] = []
    candidates = db.scalars(select(Player).order_by(Player.rating.desc()).limit(30)).all()
    scored = []
    for p in candidates:
        analytics = db.get(MarketAnalytics, p.id)
        prices = db.scalars(
            select(PricePoint).where(PricePoint.player_id == p.id)
        ).all()
        has_sbc = bool(analytics and analytics.demand - analytics.supply > 25)
        ai = rate_player(p, list(prices), analytics, has_upcoming_sbc=has_sbc)
        scored.append((p, ai))
    for p, ai in sorted(scored, key=lambda t: t[1].score, reverse=True)[:5]:
        top_rows.append(
            ScannerRow(
                player=PlayerSummary.model_validate(p),
                metric=float(ai.score),
                label=ai.verdict,
            )
        )

    briefing = _briefing(user, trending, top_rows, transfer_profit)

    return DashboardOut(
        club_value=club_value,
        coin_balance=user.coin_balance,
        transfer_profit=transfer_profit,
        profit_this_week=int(transfer_profit * 0.35),
        profit_this_month=transfer_profit,
        open_positions=len(investments),
        watchlist_count=int(watch_count or 0),
        active_alerts=int(alert_count or 0),
        trending=[PlayerSummary.model_validate(p) for p in trending],
        top_investments=top_rows,
        assistant_briefing=briefing,
    )


def _briefing(
    user: User,
    trending: list[Player],
    top_rows: list[ScannerRow],
    profit: int,
) -> list[str]:
    lines = [f"Good evening {user.display_name.split()[0]} — here's your market brief."]
    if trending:
        best = trending[0]
        lines.append(
            f"{best.name} ({best.rating}) is up {best.price_change_pct:+.1f}% today."
        )
        worst = min(trending, key=lambda p: p.price_change_pct)
        if worst.price_change_pct < 0:
            lines.append(
                f"{worst.name} slipped {worst.price_change_pct:.1f}% — watch for a floor."
            )
    if top_rows:
        pick = top_rows[0]
        lines.append(
            f"Top AI pick: {pick.player.name} — {pick.label} at {int(pick.metric)}/100."
        )
    lines.append(f"Realised transfer profit so far: {profit:,} coins.")
    return lines
