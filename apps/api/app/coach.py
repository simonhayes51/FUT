"""AI Coach — natural-language answers grounded in live market + club data.

Two modes, same interface:

* **LLM mode** (when ``OPENAI_API_KEY`` is set) — a compact, freshly-built market
  context is handed to the model so answers reflect *today's* prices, not the
  model's training data.
* **Heuristic mode** (default, fully offline) — intent is classified from the
  question and the answer is composed directly from the database.

Both return the same shape, so the frontend never needs to know which ran. The
grounding context is identical in both modes — the LLM only adds phrasing.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai import rate_player
from .config import get_settings
from .models import ClubPlayer, MarketAnalytics, Player, PricePoint, SBC, Trade, User


@dataclass
class CoachContext:
    top_picks: list[tuple[Player, object]]  # (player, AIRating)
    risers: list[Player]
    fallers: list[Player]
    best_sbcs: list[SBC]
    club_fodder_value: int
    realised_profit: int

    def as_prompt(self) -> str:
        picks = ", ".join(
            f"{p.name} ({p.rating}) {r.verdict} {r.score}/100 @ {p.price:,}"
            for p, r in self.top_picks[:5]
        )
        sbcs = ", ".join(f"{s.name} (value {s.value_rating}/100)" for s in self.best_sbcs[:3])
        return (
            f"Top AI investment picks: {picks}.\n"
            f"Fastest risers: {', '.join(p.name for p in self.risers[:4])}.\n"
            f"Fastest fallers: {', '.join(p.name for p in self.fallers[:4])}.\n"
            f"Best-value SBCs right now: {sbcs}.\n"
            f"User club fodder value: {self.club_fodder_value:,} coins. "
            f"Realised transfer profit: {self.realised_profit:,} coins."
        )


def build_context(db: Session) -> CoachContext:
    players = db.scalars(select(Player).order_by(Player.rating.desc()).limit(40)).all()
    scored: list[tuple[Player, object]] = []
    for p in players:
        analytics = db.get(MarketAnalytics, p.id)
        prices = db.scalars(select(PricePoint).where(PricePoint.player_id == p.id)).all()
        has_sbc = bool(analytics and analytics.demand - analytics.supply > 25)
        scored.append((p, rate_player(p, list(prices), analytics, has_upcoming_sbc=has_sbc)))
    scored.sort(key=lambda t: t[1].score, reverse=True)

    movers = db.scalars(select(Player).order_by(Player.price_change_pct.desc())).all()
    risers = [p for p in movers if p.price_change_pct > 0][:5]
    fallers = list(reversed(movers))[:5]

    best_sbcs = db.scalars(select(SBC).order_by(SBC.value_rating.desc()).limit(3)).all()

    club_rows = db.scalars(select(ClubPlayer)).all()
    fodder_value = sum(
        r.player.price * r.quantity for r in club_rows if r.player.rating <= 84
    )
    profit = sum(t.net_profit for t in db.scalars(select(Trade)).all())

    return CoachContext(
        top_picks=scored,
        risers=risers,
        fallers=fallers,
        best_sbcs=list(best_sbcs),
        club_fodder_value=fodder_value,
        realised_profit=profit,
    )


# --- Heuristic responder ------------------------------------------------------

_INTENTS = {
    "invest": ["invest", "buy", "snipe", "pick up", "get into"],
    "sell": ["sell", "dump", "offload", "cash out"],
    "sbc": ["sbc", "squad building", "challenge", "fodder"],
    "coins": ["coins", "profit", "make money", "500k", "100k", "1m", "million", "grind"],
}


def _classify(question: str) -> str:
    q = question.lower()
    best, best_hits = "general", 0
    for intent, words in _INTENTS.items():
        hits = sum(1 for w in words if w in q)
        if hits > best_hits:
            best, best_hits = intent, hits
    return best


def _heuristic_answer(question: str, ctx: CoachContext) -> str:
    intent = _classify(question)

    if intent == "invest":
        lines = ["Here are the strongest investments on the market right now:"]
        for p, r in ctx.top_picks[:4]:
            if r.verdict not in {"BUY", "HOLD"}:
                continue
            lines.append(
                f"• **{p.name}** ({p.rating}) — {r.verdict} at {r.score}/100, "
                f"buy ≈ {r.suggested_buy:,}, target ≈ {r.suggested_sell:,} "
                f"({r.expected_roi_pct:+.0f}% ROI). {r.reasons[0]}."
            )
        lines.append("\nStagger your buys and set price alerts near the suggested entry.")
        return "\n".join(lines)

    if intent == "sell":
        lines = ["Consider taking profit on these — momentum or rating says sell:"]
        sells = [(p, r) for p, r in ctx.top_picks if r.verdict in {"SELL", "AVOID"}]
        for p, r in (sells or ctx.top_picks)[:4]:
            lines.append(f"• **{p.name}** ({p.rating}) — {r.verdict}, {r.reasons[0]}.")
        if ctx.fallers:
            lines.append(
                f"\n{ctx.fallers[0].name} is falling fastest "
                f"({ctx.fallers[0].price_change_pct:+.1f}%) — exit before it drops further."
            )
        return "\n".join(lines)

    if intent == "sbc":
        lines = ["Best-value SBCs to prioritise:"]
        for s in ctx.best_sbcs:
            net = s.pack_value - s.estimated_cost
            lines.append(
                f"• **{s.name}** — value {s.value_rating}/100, cost ≈ {s.estimated_cost:,}"
                + (f", net {net:+,}" if s.pack_value else f", reward: {s.reward}")
                + "."
            )
        lines.append(
            f"\nYou're holding ~{ctx.club_fodder_value:,} coins of fodder — "
            "use the AI SBC Solver to complete these from your club for near-zero coins."
        )
        return "\n".join(lines)

    if intent == "coins":
        top = ctx.top_picks[0]
        lines = [
            "A realistic plan to grow your balance:",
            f"1. **Flip fodder into SBCs** — you have ~{ctx.club_fodder_value:,} coins of "
            f"fodder; completing '{ctx.best_sbcs[0].name}' from club is near-free profit.",
            f"2. **Invest** in {top[0].name} ({top[1].verdict} {top[1].score}/100, "
            f"{top[1].expected_roi_pct:+.0f}% expected) and 2–3 more BUY-rated cards.",
            "3. **Snipe** the fastest fallers as they bottom out: "
            + ", ".join(p.name for p in ctx.fallers[:3])
            + ".",
            f"\nYou've already realised {ctx.realised_profit:,} coins in trades — "
            "compounding these three streams is how you hit the next milestone.",
        ]
        return "\n".join(lines)

    # general
    top = ctx.top_picks[0]
    return (
        f"Market snapshot: **{ctx.risers[0].name}** leads the risers "
        f"({ctx.risers[0].price_change_pct:+.1f}%), while **{ctx.fallers[0].name}** "
        f"is the biggest faller. My top AI pick is **{top[0].name}** "
        f"({top[1].verdict}, {top[1].score}/100). Best SBC to do is "
        f"**{ctx.best_sbcs[0].name}**. Ask me what to buy, what to sell, "
        f"which SBC to complete, or how to make coins."
    )


def answer(question: str, db: Session) -> dict:
    ctx = build_context(db)
    settings = get_settings()

    used_llm = False
    text: str | None = None
    if settings.openai_api_key:
        try:
            text = _llm_answer(question, ctx, settings.openai_api_key)
            used_llm = True
        except Exception:  # pragma: no cover - network/LLM failure → graceful fallback
            text = None
    if text is None:
        text = _heuristic_answer(question, ctx)

    return {
        "answer": text,
        "engine": "llm" if used_llm else "heuristic",
        "suggestions": [
            "What should I invest in?",
            "Which SBC is worth doing?",
            "How do I make 500k?",
            "Who should I sell?",
        ],
    }


def _llm_answer(question: str, ctx: CoachContext, api_key: str) -> str:  # pragma: no cover
    """Call OpenAI with the live market context grounding the answer."""
    import httpx

    system = (
        "You are FC Edge's AI Coach, an expert EA Sports FC trader. Answer the "
        "user's question in 4-6 short sentences using ONLY the live market data "
        "provided. Be specific with player names, prices and numbers. Never invent "
        "cards or prices not in the context."
    )
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Live data:\n{ctx.as_prompt()}\n\nQuestion: {question}"},
            ],
            "temperature": 0.4,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
