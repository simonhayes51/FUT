"""SBC Centre — challenges, value ratings and 'should I complete?' signal."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SBC
from ..schemas import SBCOut

router = APIRouter(prefix="/sbcs", tags=["sbcs"])


@router.get("", response_model=list[SBCOut])
def list_sbcs(db: Session = Depends(get_db)):
    return db.scalars(select(SBC).order_by(SBC.value_rating.desc())).all()


@router.get("/{sbc_id}", response_model=SBCOut)
def get_sbc(sbc_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    sbc = db.get(SBC, sbc_id)
    if sbc is None:
        raise HTTPException(status_code=404, detail="SBC not found")
    return sbc
