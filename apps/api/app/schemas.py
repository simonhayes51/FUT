"""Pydantic response/request models — the public API contract."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr


class PlayerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rating: int
    position: str
    club: str
    league: str
    nation: str
    card_type: str
    image_url: str | None = None
    price: int
    price_change_pct: float


class PricePointOut(BaseModel):
    price: int
    recorded_at: dt.datetime


class AnalyticsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lowest_bin: int
    highest_bin: int
    volume: int
    supply: int
    demand: int
    volatility: float
    buy_score: int
    sell_score: int
    hold_score: int


class AIRatingOut(BaseModel):
    score: int
    confidence: int
    verdict: str
    risk: str
    time_horizon: str
    expected_roi_pct: float
    suggested_buy: int
    suggested_sell: int
    expected_peak: int
    reasons: list[str]


class PlayerDetail(PlayerSummary):
    analytics: AnalyticsOut | None = None
    ai: AIRatingOut | None = None
    history: list[PricePointOut] = []


class ScannerRow(BaseModel):
    player: PlayerSummary
    metric: float
    label: str


class DashboardOut(BaseModel):
    club_value: int
    coin_balance: int
    transfer_profit: int
    profit_this_week: int
    profit_this_month: int
    open_positions: int
    watchlist_count: int
    active_alerts: int
    trending: list[PlayerSummary]
    top_investments: list[ScannerRow]
    assistant_briefing: list[str]


class SBCOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    expires_at: dt.datetime | None
    reward: str
    estimated_cost: int
    pack_value: int
    value_rating: int
    difficulty: str
    repeatable: bool


class TaxResult(BaseModel):
    sale_price: int
    tax: int
    net_received: int


class HealthOut(BaseModel):
    status: str
    environment: str
