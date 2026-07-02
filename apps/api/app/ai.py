"""FC Edge market intelligence engine.

Produces the AI Investment Rating shown across the product. It is a transparent,
deterministic model over the same signals a human trader watches:

* price momentum (recent trend of the BIN series)
* supply vs demand imbalance
* volatility (risk)
* structural catalysts (upcoming SBC, promo/meta demand)

Keeping it deterministic means the rating is explainable ("why 93/100?") and
reproducible in tests. The optional LLM Coach (see ``coach.py`` roadmap) layers
natural-language reasoning on top of these numbers — it never replaces them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import MarketAnalytics, Player, PricePoint


@dataclass
class AIRating:
    score: int  # 0-100 overall investment rating
    confidence: int  # 0-100
    verdict: str  # BUY / HOLD / SELL / AVOID
    risk: str  # Low / Medium / High
    time_horizon: str
    expected_roi_pct: float
    suggested_buy: int
    suggested_sell: int
    expected_peak: int
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "confidence": self.confidence,
            "verdict": self.verdict,
            "risk": self.risk,
            "time_horizon": self.time_horizon,
            "expected_roi_pct": round(self.expected_roi_pct, 1),
            "suggested_buy": self.suggested_buy,
            "suggested_sell": self.suggested_sell,
            "expected_peak": self.expected_peak,
            "reasons": self.reasons,
        }


def _momentum(prices: list[PricePoint]) -> float:
    """Return recent price momentum in the range roughly [-1, 1]."""
    if len(prices) < 4:
        return 0.0
    series = [p.price for p in sorted(prices, key=lambda p: p.recorded_at)]
    window = max(2, len(series) // 4)
    early = sum(series[:window]) / window
    late = sum(series[-window:]) / window
    if early == 0:
        return 0.0
    return max(-1.0, min(1.0, (late - early) / early))


def rate_player(
    player: Player,
    prices: list[PricePoint],
    analytics: MarketAnalytics | None,
    *,
    has_upcoming_sbc: bool = False,
) -> AIRating:
    momentum = _momentum(prices)
    supply = analytics.supply if analytics else 50
    demand = analytics.demand if analytics else 50
    volatility = analytics.volatility if analytics else 0.3

    # --- Score components (each contributes to a 0-100 total) -----------------
    # Demand pressure: high demand + low supply is the classic "about to rise".
    pressure = (demand - supply)  # -100..100
    score = 50.0
    score += pressure * 0.25
    score += momentum * 18
    score += 12 if has_upcoming_sbc else 0
    # Meta cards (high rated, popular leagues) carry a structural premium.
    if player.rating >= 88:
        score += 6
    score = int(max(1, min(100, round(score))))

    # Confidence falls as volatility rises and as we have less data.
    data_conf = min(1.0, len(prices) / 48)
    confidence = int(max(20, min(99, round((1 - volatility) * 70 + data_conf * 30))))

    risk = "Low" if volatility < 0.25 else "Medium" if volatility < 0.5 else "High"

    if score >= 75:
        verdict = "BUY"
    elif score >= 55:
        verdict = "HOLD"
    elif score >= 40:
        verdict = "SELL"
    else:
        verdict = "AVOID"

    base = player.price or (analytics.lowest_bin if analytics else 0)
    # Suggested entry slightly below current BIN; target scaled by conviction.
    suggested_buy = int(base * 0.96)
    upside = 0.04 + max(0.0, (score - 50) / 100) * 0.6
    suggested_sell = int(base * (1 + upside))
    expected_peak = int(base * (1 + upside * 1.25))
    # ROI is net of the 5% EA sell tax.
    expected_roi = 0.0
    if suggested_buy:
        expected_roi = ((suggested_sell * 0.95) - suggested_buy) / suggested_buy * 100

    horizon = (
        "1-3 days"
        if has_upcoming_sbc
        else "1-2 weeks"
        if verdict in {"BUY", "HOLD"}
        else "Sell now"
    )

    reasons: list[str] = []
    if has_upcoming_sbc:
        reasons.append("Upcoming SBC likely to drive demand")
    if demand - supply > 20:
        reasons.append("High demand versus low supply")
    elif supply - demand > 20:
        reasons.append("Oversupplied — downward pressure")
    if momentum > 0.05:
        reasons.append(f"Positive price momentum (+{momentum * 100:.0f}%)")
    elif momentum < -0.05:
        reasons.append(f"Falling price trend ({momentum * 100:.0f}%)")
    if player.rating >= 88:
        reasons.append("Meta-rated card with sustained Weekend League demand")
    if volatility >= 0.5:
        reasons.append("High volatility — size positions carefully")
    if not reasons:
        reasons.append("Stable market with no strong directional signal")

    return AIRating(
        score=score,
        confidence=confidence,
        verdict=verdict,
        risk=risk,
        time_horizon=horizon,
        expected_roi_pct=expected_roi,
        suggested_buy=suggested_buy,
        suggested_sell=suggested_sell,
        expected_peak=expected_peak,
        reasons=reasons,
    )
