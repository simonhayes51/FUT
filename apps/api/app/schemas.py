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
    formation: str
    squad_size: int
    min_rating: int
    min_chemistry: int


class SolveOptions(BaseModel):
    objective: str = "cheapest"  # cheapest | highest_rating | min_club_loss
    use_club: bool = True  # use players you already own
    buy_missing: bool = True  # allow buying market fodder to fill gaps
    protect_icons: bool = True
    protect_favourites: bool = True
    protect_first_owner: bool = False
    max_card_rating: int | None = None  # don't consume cards above this rating


class SquadSlot(BaseModel):
    player_id: int
    name: str
    rating: int
    position: str
    assigned_position: str = ""  # formation slot this card fills
    club: str
    league: str
    nation: str
    card_type: str
    source: str  # club | market
    cost: int
    market_value: int


class SolveResult(BaseModel):
    sbc_id: int
    sbc_name: str
    objective: str
    feasible: bool
    squad_rating: int
    required_rating: int
    chemistry: int
    required_chemistry: int
    total_cost: int  # coins to buy the missing cards
    club_value_used: int  # value of owned cards consumed
    squad: list[SquadSlot]
    to_buy: list[SquadSlot]
    unmet: list[str]


class CompleteResult(BaseModel):
    sbc_id: int
    sbc_name: str
    success: bool
    coins_spent: int
    club_cards_used: int
    new_balance: int
    message: str


class SetSolveRequest(BaseModel):
    sbc_ids: list[int]
    options: SolveOptions = SolveOptions()


class SetSolveResult(BaseModel):
    results: list[SolveResult]
    total_coins: int
    total_club_value_used: int
    all_feasible: bool


class ClubPlayerOut(BaseModel):
    player_id: int
    name: str
    rating: int
    position: str
    club: str
    league: str
    nation: str
    card_type: str
    quantity: int
    untradeable: bool
    is_favourite: bool
    market_value: int


class TaxResult(BaseModel):
    sale_price: int
    tax: int
    net_received: int


class HealthOut(BaseModel):
    status: str
    environment: str
