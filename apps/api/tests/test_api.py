"""Smoke + contract tests. Run: `pytest` from apps/api (uses a temp SQLite db)."""
from __future__ import annotations

import os
import tempfile

# Point the app at a throwaway database before importing anything.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app.ai import rate_player  # noqa: E402
from app.main import app  # noqa: E402
from app.models import MarketAnalytics, Player, PricePoint  # noqa: E402
from app.seed import run as seed_run  # noqa: E402

seed_run()
client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_shape():
    r = client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    for key in ("club_value", "coin_balance", "trending", "assistant_briefing"):
        assert key in body
    assert len(body["assistant_briefing"]) >= 1


def test_scanner_categories():
    r = client.get("/api/v1/market/scanner?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert "best_investments" in data
    assert len(data["best_investments"]) <= 5


def test_player_detail_has_ai_and_history():
    detail = client.get("/api/v1/players/1").json()
    assert detail["ai"]["score"] >= 1
    assert detail["ai"]["verdict"] in {"BUY", "HOLD", "SELL", "AVOID"}
    assert len(detail["history"]) > 0
    assert set(detail["ai"]["reasons"])  # non-empty reasons


def test_tax_calculator():
    r = client.get("/api/v1/players/1/tax?sale_price=100000")
    assert r.json() == {"sale_price": 100000, "tax": 5000, "net_received": 95000}


def _cand(rating, league="L", nation="N", club="C", cost=0, source="club", ct="Gold"):
    from app.solver import Candidate

    return Candidate(
        player_id=0, name="x", rating=rating, position="CM", club=club,
        league=league, nation=nation, card_type=ct, cost=cost,
        market_value=cost or 500, source=source,
    )


def test_squad_rating_rewards_above_average():
    from app.solver import squad_rating

    flat = [_cand(84) for _ in range(11)]
    assert squad_rating(flat) == 84
    # A single 99 among 84s must pull the rating above the plain mean (84.something).
    mixed = [_cand(99)] + [_cand(84) for _ in range(10)]
    assert squad_rating(mixed) >= 86


def test_chemistry_counts_shared_attributes():
    from app.solver import chemistry

    # 11 same league + nation + varied clubs → strong chemistry.
    strong = [_cand(84, league="Serie A", nation="Italy", club=f"C{i}") for i in range(11)]
    weak = [_cand(84, league=f"L{i}", nation=f"N{i}", club=f"C{i}") for i in range(11)]
    assert chemistry(strong) > chemistry(weak)
    assert 0 <= chemistry(strong) <= 33


def test_solver_meets_requirements_when_feasible():
    from app.solver import solve

    pool = [_cand(85, league="Serie A", nation="Italy", club=f"C{i}") for i in range(20)]
    sol = solve(pool, size=11, min_rating=85, min_chemistry=20, objective="cheapest")
    assert sol.feasible
    assert sol.squad_rating >= 85
    assert sol.chemistry >= 20
    assert len(sol.squad) == 11


def test_solver_reports_infeasible():
    from app.solver import solve

    pool = [_cand(80) for _ in range(11)]  # can't reach an 88 squad
    sol = solve(pool, size=11, min_rating=88, min_chemistry=0)
    assert not sol.feasible
    assert sol.unmet


def test_solve_endpoint_objectives():
    for objective in ("cheapest", "highest_rating", "min_club_loss"):
        r = client.post("/api/v1/sbcs/3/solve", json={"objective": objective})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["feasible"] is True
        assert body["squad_rating"] >= body["required_rating"]
        assert body["chemistry"] >= body["required_chemistry"]
        assert len(body["squad"]) == 11


def test_formation_assignment():
    from app.formations import assign, matched_count

    # A textbook 4-3-3 line-up is fully assignable.
    positions = ["GK", "RB", "CB", "CB", "LB", "CM", "CM", "CM", "RW", "ST", "LW"]
    slots = ["GK", "RB", "CB", "CB", "LB", "CM", "CM", "CM", "RW", "ST", "LW"]
    assert assign(positions, slots) is not None
    # Eleven strikers cannot fill a back line.
    assert matched_count(["ST"] * 11, slots) < 11


def test_solver_v2_assigns_positions():
    from app.solver import solve

    slots = ["GK", "RB", "CB", "CB", "LB", "CM", "CM", "CM", "RW", "ST", "LW"]
    pool = [
        _cand(85, league="Serie A", nation="Italy", club=f"C{i}")
        for i in range(30)
    ]
    for c, pos in zip(pool, (slots * 3)):
        c.position = pos
    sol = solve(pool, size=11, min_rating=84, min_chemistry=15,
                objective="cheapest", formation="4-3-3")
    assert sol.feasible
    assert all(c.assigned_position for c in sol.squad)


def test_coach_answers_and_grounds_in_data():
    for q in ("What should I invest in?", "How do I make 500k?", "Which SBC should I do?"):
        r = client.post("/api/v1/coach/ask", json={"question": q})
        assert r.status_code == 200
        body = r.json()
        assert body["engine"] == "heuristic"  # no OPENAI key in tests
        assert len(body["answer"]) > 20
        assert len(body["suggestions"]) == 4


def test_solve_set_returns_per_sbc_results():
    r = client.post("/api/v1/sbcs/solve-set", json={"sbc_ids": [1, 2], "options": {}})
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 2
    assert "total_coins" in body


def test_complete_sbc_spends_and_consumes():
    before = client.get("/api/v1/dashboard").json()["coin_balance"]
    r = client.post("/api/v1/sbcs/1/complete", json={"objective": "cheapest"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["new_balance"] == before - body["coins_spent"]


def test_high_demand_low_supply_scores_higher():
    """The engine must reward demand pressure — a core trust property."""
    import datetime as dt

    p = Player(name="Test", rating=90, position="ST", club="X", league="Y", nation="Z", price=100000)
    base = dt.datetime(2026, 1, 1)
    prices = [
        PricePoint(price=100000, recorded_at=base + dt.timedelta(hours=i)) for i in range(4)
    ]
    hot = MarketAnalytics(lowest_bin=95000, highest_bin=110000, volume=5000, supply=20, demand=90, volatility=0.2)
    cold = MarketAnalytics(lowest_bin=95000, highest_bin=110000, volume=5000, supply=90, demand=20, volatility=0.2)
    assert rate_player(p, prices, hot).score > rate_player(p, prices, cold).score
