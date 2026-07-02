"""SBC Centre — challenges, value ratings and the AI SBC Solver."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClubPlayer, Player, SBC, User
from ..schemas import SBCOut, SolveOptions, SolveResult, SquadSlot
from ..solver import Candidate, solve

router = APIRouter(prefix="/sbcs", tags=["sbcs"])


@router.get("", response_model=list[SBCOut])
def list_sbcs(db: Session = Depends(get_db)):
    return db.scalars(select(SBC).order_by(SBC.value_rating.desc())).all()


@router.get("/{sbc_id}", response_model=SBCOut)
def get_sbc(sbc_id: int, db: Session = Depends(get_db)):
    sbc = db.get(SBC, sbc_id)
    if sbc is None:
        raise HTTPException(status_code=404, detail="SBC not found")
    return sbc


def _demo_user(db: Session) -> User:
    user = db.scalars(select(User).limit(1)).first()
    if user is None:  # pragma: no cover
        raise HTTPException(status_code=404, detail="No user")
    return user


def _slot(c: Candidate) -> SquadSlot:
    return SquadSlot(
        player_id=c.player_id,
        name=c.name,
        rating=c.rating,
        position=c.position,
        club=c.club,
        league=c.league,
        nation=c.nation,
        card_type=c.card_type,
        source=c.source,
        cost=c.cost,
        market_value=c.market_value,
    )


def _build_pool(
    db: Session, user: User, sbc: SBC, opts: SolveOptions
) -> list[Candidate]:
    pool: list[Candidate] = []
    seen: set[int] = set()

    # 1) Players the user owns (free to use, but may burn club value).
    if opts.use_club:
        club_rows = db.scalars(
            select(ClubPlayer).where(ClubPlayer.user_id == user.id)
        ).all()
        for row in club_rows:
            p = row.player
            if opts.protect_icons and p.card_type == "Icon":
                continue
            if opts.protect_favourites and row.is_favourite:
                continue
            if opts.protect_first_owner and row.first_owner:
                continue
            if opts.max_card_rating is not None and p.rating > opts.max_card_rating:
                continue
            seen.add(p.id)
            # A duplicate (quantity>1) can fill more than one slot.
            for _ in range(min(row.quantity, 3)):
                pool.append(
                    Candidate(
                        player_id=p.id,
                        name=p.name,
                        rating=p.rating,
                        position=p.position,
                        club=p.club,
                        league=p.league,
                        nation=p.nation,
                        card_type=p.card_type,
                        cost=0,
                        market_value=p.price,
                        source="club",
                        untradeable=row.untradeable,
                    )
                )

    # 2) Market fodder to buy. Restrict to a sensible rating band around the
    #    requirement so we don't offer to buy a 91 to fill an 84 squad.
    if opts.buy_missing:
        lo = max(0, sbc.min_rating - 6)
        hi = sbc.min_rating + 4
        market = db.scalars(
            select(Player)
            .where(Player.rating >= lo, Player.rating <= hi, Player.card_type != "Icon")
            .order_by(Player.price)
        ).all()
        for p in market:
            if p.id in seen:
                continue
            pool.append(
                Candidate(
                    player_id=p.id,
                    name=p.name,
                    rating=p.rating,
                    position=p.position,
                    club=p.club,
                    league=p.league,
                    nation=p.nation,
                    card_type=p.card_type,
                    cost=p.price,
                    market_value=p.price,
                    source="market",
                )
            )
    return pool


@router.post("/{sbc_id}/solve", response_model=SolveResult)
def solve_sbc(sbc_id: int, opts: SolveOptions, db: Session = Depends(get_db)):
    """Build a squad that satisfies an SBC, optimised for the chosen objective."""
    sbc = db.get(SBC, sbc_id)
    if sbc is None:
        raise HTTPException(status_code=404, detail="SBC not found")
    if opts.objective not in {"cheapest", "highest_rating", "min_club_loss"}:
        raise HTTPException(status_code=422, detail="Unknown objective")

    user = _demo_user(db)
    pool = _build_pool(db, user, sbc, opts)

    result = solve(
        pool,
        size=sbc.squad_size,
        min_rating=sbc.min_rating,
        min_chemistry=sbc.min_chemistry,
        objective=opts.objective,
    )

    return SolveResult(
        sbc_id=sbc.id,
        sbc_name=sbc.name,
        objective=opts.objective,
        feasible=result.feasible,
        squad_rating=result.squad_rating,
        required_rating=sbc.min_rating,
        chemistry=result.chemistry,
        required_chemistry=sbc.min_chemistry,
        total_cost=result.total_cost,
        club_value_used=result.club_value_used,
        squad=[_slot(c) for c in result.squad],
        to_buy=[_slot(c) for c in result.to_buy],
        unmet=result.unmet,
    )
