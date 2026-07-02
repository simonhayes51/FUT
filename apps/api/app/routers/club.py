"""Club Manager — the user's owned players (the SBC solve material)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClubPlayer, User
from ..schemas import ClubPlayerOut

router = APIRouter(prefix="/club", tags=["club"])


@router.get("", response_model=list[ClubPlayerOut])
def get_club(db: Session = Depends(get_db)):
    user = db.scalars(select(User).limit(1)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="No user")
    rows = db.scalars(
        select(ClubPlayer).where(ClubPlayer.user_id == user.id)
    ).all()
    out: list[ClubPlayerOut] = []
    for row in rows:
        p = row.player
        out.append(
            ClubPlayerOut(
                player_id=p.id,
                name=p.name,
                rating=p.rating,
                position=p.position,
                club=p.club,
                league=p.league,
                nation=p.nation,
                card_type=p.card_type,
                quantity=row.quantity,
                untradeable=row.untradeable,
                is_favourite=row.is_favourite,
                market_value=p.price,
            )
        )
    out.sort(key=lambda c: c.rating, reverse=True)
    return out
