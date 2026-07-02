"""AI Coach endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..coach import answer
from ..database import get_db

router = APIRouter(prefix="/coach", tags=["coach"])


class CoachQuestion(BaseModel):
    question: str


class CoachAnswer(BaseModel):
    answer: str
    engine: str  # llm | heuristic
    suggestions: list[str]


@router.post("/ask", response_model=CoachAnswer)
def ask(payload: CoachQuestion, db: Session = Depends(get_db)):
    return answer(payload.question, db)
