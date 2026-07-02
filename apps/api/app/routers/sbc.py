"""SBC Centre — challenges, value ratings and the AI SBC Solver (v2)."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClubPlayer, Player, SBC, User
from ..schemas import (
    CompleteResult,
    SBCOut,
    SetSolveRequest,
    SetSolveResult,
    SolveOptions,
    SolveResult,
    SquadSlot,
)
from ..solver import Candidate, Solution, solve

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
        assigned_position=c.assigned_position or c.position,
        club=c.club,
        league=c.league,
        nation=c.nation,
        card_type=c.card_type,
        source=c.source,
        cost=c.cost,
        market_value=c.market_value,
    )


def _club_candidates(db: Session, user: User, opts: SolveOptions) -> list[Candidate]:
    if not opts.use_club:
        return []
    out: list[Candidate] = []
    rows = db.scalars(select(ClubPlayer).where(ClubPlayer.user_id == user.id)).all()
    for row in rows:
        p = row.player
        if opts.protect_icons and p.card_type == "Icon":
            continue
        if opts.protect_favourites and row.is_favourite:
            continue
        if opts.protect_first_owner and row.first_owner:
            continue
        if opts.max_card_rating is not None and p.rating > opts.max_card_rating:
            continue
        for _ in range(min(row.quantity, 3)):
            out.append(
                Candidate(
                    player_id=p.id, name=p.name, rating=p.rating, position=p.position,
                    club=p.club, league=p.league, nation=p.nation, card_type=p.card_type,
                    cost=0, market_value=p.price, source="club", untradeable=row.untradeable,
                )
            )
    return out


def _market_candidates(db: Session, sbc: SBC, opts: SolveOptions, exclude: set[int]) -> list[Candidate]:
    if not opts.buy_missing:
        return []
    lo, hi = max(0, sbc.min_rating - 6), sbc.min_rating + 4
    players = db.scalars(
        select(Player)
        .where(Player.rating >= lo, Player.rating <= hi, Player.card_type != "Icon")
        .order_by(Player.price)
    ).all()
    return [
        Candidate(
            player_id=p.id, name=p.name, rating=p.rating, position=p.position,
            club=p.club, league=p.league, nation=p.nation, card_type=p.card_type,
            cost=p.price, market_value=p.price, source="market",
        )
        for p in players
        if p.id not in exclude
    ]


def _to_result(sbc: SBC, objective: str, sol: Solution) -> SolveResult:
    return SolveResult(
        sbc_id=sbc.id,
        sbc_name=sbc.name,
        objective=objective,
        feasible=sol.feasible,
        squad_rating=sol.squad_rating,
        required_rating=sbc.min_rating,
        chemistry=sol.chemistry,
        required_chemistry=sbc.min_chemistry,
        total_cost=sol.total_cost,
        club_value_used=sol.club_value_used,
        squad=[_slot(c) for c in sol.squad],
        to_buy=[_slot(c) for c in sol.to_buy],
        unmet=sol.unmet,
    )


@router.post("/{sbc_id}/solve", response_model=SolveResult)
def solve_sbc(sbc_id: int, opts: SolveOptions, db: Session = Depends(get_db)):
    """Build a squad that satisfies an SBC, optimised for the chosen objective."""
    sbc = db.get(SBC, sbc_id)
    if sbc is None:
        raise HTTPException(status_code=404, detail="SBC not found")
    if opts.objective not in {"cheapest", "highest_rating", "min_club_loss"}:
        raise HTTPException(status_code=422, detail="Unknown objective")

    user = _demo_user(db)
    club = _club_candidates(db, user, opts)
    market = _market_candidates(db, sbc, opts, exclude={c.player_id for c in club})
    sol = solve(
        club + market,
        size=sbc.squad_size,
        min_rating=sbc.min_rating,
        min_chemistry=sbc.min_chemistry,
        objective=opts.objective,
        formation=sbc.formation,
    )
    return _to_result(sbc, opts.objective, sol)


@router.post("/{sbc_id}/complete", response_model=CompleteResult)
def complete_sbc(sbc_id: int, opts: SolveOptions, db: Session = Depends(get_db)):
    """Solve then *commit*: spend coins, consume club fodder, submit the SBC."""
    sbc = db.get(SBC, sbc_id)
    if sbc is None:
        raise HTTPException(status_code=404, detail="SBC not found")
    user = _demo_user(db)
    club = _club_candidates(db, user, opts)
    market = _market_candidates(db, sbc, opts, exclude={c.player_id for c in club})
    sol = solve(
        club + market,
        size=sbc.squad_size,
        min_rating=sbc.min_rating,
        min_chemistry=sbc.min_chemistry,
        objective=opts.objective,
        formation=sbc.formation,
    )

    if not sol.feasible:
        return CompleteResult(
            sbc_id=sbc.id, sbc_name=sbc.name, success=False, coins_spent=0,
            club_cards_used=0, new_balance=user.coin_balance,
            message="No valid solution: " + "; ".join(sol.unmet),
        )
    if sol.total_cost > user.coin_balance:
        return CompleteResult(
            sbc_id=sbc.id, sbc_name=sbc.name, success=False, coins_spent=0,
            club_cards_used=0, new_balance=user.coin_balance,
            message=f"Need {sol.total_cost:,} coins to buy fodder, you have {user.coin_balance:,}.",
        )

    # Consume: deduct coins for bought cards, remove used club duplicates.
    used_club = Counter(c.player_id for c in sol.squad if c.source == "club")
    for player_id, qty in used_club.items():
        row = db.scalar(
            select(ClubPlayer).where(
                ClubPlayer.user_id == user.id, ClubPlayer.player_id == player_id
            )
        )
        if row is None:
            continue
        row.quantity -= qty
        if row.quantity <= 0:
            db.delete(row)
    user.coin_balance -= sol.total_cost
    db.commit()

    return CompleteResult(
        sbc_id=sbc.id,
        sbc_name=sbc.name,
        success=True,
        coins_spent=sol.total_cost,
        club_cards_used=sum(used_club.values()),
        new_balance=user.coin_balance,
        message=f"Submitted '{sbc.name}'. Reward: {sbc.reward}.",
    )


@router.post("/solve-set", response_model=SetSolveResult)
def solve_set(payload: SetSolveRequest, db: Session = Depends(get_db)):
    """Solve several SBCs against one shared club, consuming fodder as it goes."""
    user = _demo_user(db)
    opts = payload.options
    # Build the club pool once; club cards consumed by one SBC can't fill another.
    remaining_club = _club_candidates(db, user, opts)

    results: list[SolveResult] = []
    for sbc_id in payload.sbc_ids:
        sbc = db.get(SBC, sbc_id)
        if sbc is None:
            continue
        market = _market_candidates(db, sbc, opts, exclude={c.player_id for c in remaining_club})
        sol = solve(
            remaining_club + market,
            size=sbc.squad_size,
            min_rating=sbc.min_rating,
            min_chemistry=sbc.min_chemistry,
            objective=opts.objective,
            formation=sbc.formation,
        )
        results.append(_to_result(sbc, opts.objective, sol))
        # Remove the exact club Candidate objects this squad consumed.
        used = {id(c) for c in sol.squad if c.source == "club"}
        remaining_club = [c for c in remaining_club if id(c) not in used]

    return SetSolveResult(
        results=results,
        total_coins=sum(r.total_cost for r in results),
        total_club_value_used=sum(r.club_value_used for r in results),
        all_feasible=all(r.feasible for r in results) and bool(results),
    )
