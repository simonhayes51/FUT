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
