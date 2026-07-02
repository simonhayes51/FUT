"""Seed the database with a realistic demo dataset.

Generates ~30 players each with a month of hourly-ish price history, analytics
snapshots, a demo user, a portfolio, trades, a watchlist, alerts and SBCs.

Run with::

    python -m app.seed
"""
from __future__ import annotations

import datetime as dt
import math
import random

from sqlalchemy import delete

from .database import Base, SessionLocal, engine
from .models import (
    ClubPlayer,
    Investment,
    MarketAnalytics,
    Player,
    PriceAlert,
    PricePoint,
    SBC,
    Trade,
    User,
    WatchlistItem,
)

RNG = random.Random(51)  # deterministic seed → reproducible demo

# (name, rating, position, club, league, nation, card_type, base_price)
ROSTER = [
    ("Mbappé", 91, "ST", "Real Madrid", "LALIGA EA SPORTS", "France", "Gold", 1_450_000),
    ("Haaland", 91, "ST", "Manchester City", "Premier League", "Norway", "Gold", 980_000),
    ("Bellingham", 90, "CM", "Real Madrid", "LALIGA EA SPORTS", "England", "Gold", 720_000),
    ("Vinícius Jr", 90, "LW", "Real Madrid", "LALIGA EA SPORTS", "Brazil", "Gold", 690_000),
    ("Rodri", 90, "CDM", "Manchester City", "Premier League", "Spain", "Gold", 540_000),
    ("Saka", 88, "RW", "Arsenal", "Premier League", "England", "Gold", 210_000),
    ("Ødegaard", 88, "CAM", "Arsenal", "Premier League", "Norway", "Gold", 175_000),
    ("Wirtz", 88, "CAM", "Bayer Leverkusen", "Bundesliga", "Germany", "Gold", 168_000),
    ("Salah", 89, "RW", "Liverpool", "Premier League", "Egypt", "Gold", 260_000),
    ("Kane", 90, "ST", "Bayern München", "Bundesliga", "England", "Gold", 430_000),
    ("Martínez", 86, "GK", "Aston Villa", "Premier League", "Argentina", "Gold", 62_000),
    ("Rüdiger", 86, "CB", "Real Madrid", "LALIGA EA SPORTS", "Germany", "Gold", 58_000),
    ("Hakimi", 86, "RB", "Paris SG", "Ligue 1", "Morocco", "Gold", 71_000),
    ("Theo Hernández", 86, "LB", "AC Milan", "Serie A", "France", "Gold", 66_000),
    ("Rice", 87, "CDM", "Arsenal", "Premier League", "England", "Gold", 120_000),
    ("Foden", 88, "CAM", "Manchester City", "Premier League", "England", "Gold", 190_000),
    ("Lautaro", 88, "ST", "Inter", "Serie A", "Argentina", "Gold", 205_000),
    ("Leão", 86, "LW", "AC Milan", "Serie A", "Portugal", "Gold", 78_000),
    ("Musiala", 87, "CAM", "Bayern München", "Bundesliga", "Germany", "Gold", 135_000),
    ("Griezmann", 87, "CF", "Atlético Madrid", "LALIGA EA SPORTS", "France", "Gold", 98_000),
    ("Pedri", 87, "CM", "Barcelona", "LALIGA EA SPORTS", "Spain", "Gold", 110_000),
    ("Gündoğan", 85, "CM", "Manchester City", "Premier League", "Germany", "Gold", 44_000),
    ("Dias", 88, "CB", "Manchester City", "Premier League", "Portugal", "Gold", 165_000),
    ("Van Dijk", 89, "CB", "Liverpool", "Premier League", "Netherlands", "Gold", 240_000),
    ("Zidane", 96, "CAM", "Icons", "Icons", "France", "Icon", 3_600_000),
    ("Ronaldinho", 95, "CAM", "Icons", "Icons", "Brazil", "Icon", 2_100_000),
    ("Henry", 95, "ST", "Icons", "Icons", "France", "Icon", 1_900_000),
    ("Gullit", 92, "CM", "Icons", "Icons", "Netherlands", "Icon", 720_000),
    ("Yamal", 87, "RW", "Barcelona", "LALIGA EA SPORTS", "Spain", "Gold", 260_000),
    ("Palmer", 87, "CAM", "Chelsea", "Premier League", "England", "Gold", 230_000),
]

# name, category, requirements(text), reward, cost, pack, rating, difficulty,
# repeatable, formation, min_rating, min_chemistry
SBCS = [
    ("Foundations III", "Foundation", "82-rated squad · 15 chem", "Small Gold Players Pack", 9_500, 14_000, 66, "Easy", True, "4-4-2", 82, 15),
    ("Marquee Matchups", "Challenge", "84-rated squad · 20 chem", "Mixed Players Pack", 24_000, 30_000, 71, "Easy", False, "4-3-3", 84, 20),
    ("85+ Upgrade", "Upgrade", "85-rated squad · 22 chem", "85+ Rare Player Pick", 68_000, 90_000, 78, "Medium", True, "4-3-3", 85, 22),
    ("TOTW Player: Wirtz", "Player", "87-rated squad · 25 chem", "89 Wirtz (untradeable)", 175_000, 0, 62, "Medium", False, "4-2-3-1", 87, 25),
    ("League SBC: Premier League", "League", "84-rated · 26 chem", "Rare Electrum Players Pack", 33_000, 45_000, 69, "Medium", False, "4-3-3", 84, 26),
    ("Icon: Gullit", "Icon", "88-rated squad · 28 chem", "92 Gullit (untradeable)", 640_000, 0, 84, "Hard", False, "4-3-3", 88, 28),
]

# Fodder catalogue: generic golds (78-86) used to fill and solve SBCs. Clustered
# by league/nation so chemistry is achievable. (rating → typical BIN discard.)
FODDER_LEAGUES = {
    "Premier League": ["England", "England", "Brazil", "France", "Spain", "Portugal"],
    "LALIGA EA SPORTS": ["Spain", "Spain", "Argentina", "Brazil", "France", "Uruguay"],
    "Serie A": ["Italy", "Italy", "Argentina", "France", "Brazil", "Serbia"],
    "Bundesliga": ["Germany", "Germany", "Austria", "France", "Japan", "Netherlands"],
    "Ligue 1": ["France", "France", "Morocco", "Brazil", "Senegal", "Spain"],
}
_FIRST = ["Alex", "Marco", "Luca", "Diego", "Tom", "Leon", "Sam", "Karim", "Yuki",
          "Pavel", "Noah", "Ivan", "Bruno", "Kai", "Omar", "Felix", "Dani", "Ren"]
_LAST = ["Silva", "Costa", "Meyer", "Rossi", "Dubois", "Novak", "Kane", "Sané",
         "Torres", "Bauer", "Moreau", "Popov", "Haas", "Vidal", "Berg", "Fischer",
         "Nagy", "Weber", "Lopez", "Traoré", "Conti", "Petit", "Ricci", "Sousa"]


def _fodder_price(rating: int) -> int:
    # Rough discard-value curve fans out steeply at the top end.
    table = {78: 550, 79: 650, 80: 800, 81: 1100, 82: 1600, 83: 2600,
             84: 4500, 85: 9000, 86: 16000}
    return int(table.get(rating, 700) * RNG.uniform(0.9, 1.15))


def _make_fodder() -> list[tuple]:
    rows: list[tuple] = []
    positions = ["GK", "CB", "RB", "LB", "CDM", "CM", "CAM", "RW", "LW", "ST"]
    used: set[str] = set()
    for league, nations in FODDER_LEAGUES.items():
        for _ in range(28):  # ~28 per league → 140 fodder cards
            rating = RNG.choices(
                [78, 79, 80, 81, 82, 83, 84, 85, 86],
                weights=[8, 12, 16, 16, 14, 12, 9, 7, 6],
            )[0]
            name = f"{RNG.choice(_FIRST)} {RNG.choice(_LAST)}"
            while name in used:
                name = f"{RNG.choice(_FIRST)} {RNG.choice(_LAST)}"
            used.add(name)
            rows.append((
                name, rating, RNG.choice(positions), f"{league.split()[0]} FC",
                league, RNG.choice(nations), "Gold", _fodder_price(rating),
            ))
    return rows


def _price_series(base: int, hours: int) -> list[int]:
    """Generate a plausible BIN series: trend + weekly cycle + noise."""
    series = []
    trend = RNG.uniform(-0.0008, 0.0012)  # per-hour drift
    for h in range(hours):
        weekly = math.sin((h / 168) * 2 * math.pi) * 0.04  # WL cycle
        noise = RNG.uniform(-0.02, 0.02)
        factor = 1 + trend * h + weekly + noise
        series.append(max(200, int(base * factor)))
    return series


def run() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = dt.datetime.now(dt.timezone.utc)
        hours = 24 * 30  # one month

        players: list[Player] = []
        for name, rating, pos, club, league, nation, ctype, base in ROSTER:
            series = _price_series(base, hours)
            price = series[-1]
            prev = series[-24]
            change = (price - prev) / prev * 100 if prev else 0.0

            player = Player(
                name=name,
                rating=rating,
                position=pos,
                club=club,
                league=league,
                nation=nation,
                card_type=ctype,
                price=price,
                prev_price=prev,
                price_change_pct=round(change, 2),
            )
            db.add(player)
            db.flush()
            players.append(player)

            # Store a downsampled series (every 3h) to keep the seed light.
            for h in range(0, hours, 3):
                db.add(
                    PricePoint(
                        player_id=player.id,
                        price=series[h],
                        recorded_at=now - dt.timedelta(hours=hours - h),
                    )
                )

            lo, hi = min(series[-48:]), max(series[-48:])
            volatility = round(min(1.0, (hi - lo) / max(1, price)), 3)
            supply = RNG.randint(20, 80)
            demand = RNG.randint(20, 95)
            db.add(
                MarketAnalytics(
                    player_id=player.id,
                    lowest_bin=lo,
                    highest_bin=hi,
                    volume=RNG.randint(400, 9000),
                    supply=supply,
                    demand=demand,
                    volatility=volatility,
                    buy_score=max(0, demand - supply),
                    sell_score=max(0, supply - demand),
                    hold_score=100 - abs(demand - supply),
                )
            )

        # --- Fodder catalogue (SBC solve material) ---------------------------
        # Lightweight: a current price only, no history/analytics, so they stay
        # out of the trending/scanner surfaces but are searchable and solvable.
        fodder: list[Player] = []
        for name, rating, pos, club, league, nation, ctype, price in _make_fodder():
            fp = Player(
                name=name, rating=rating, position=pos, club=club, league=league,
                nation=nation, card_type=ctype, price=price, prev_price=price,
                price_change_pct=0.0,
            )
            db.add(fp)
            db.flush()
            fodder.append(fp)
        players.extend(fodder)

        # --- Demo user + portfolio -------------------------------------------
        user = User(
            email="simon@fcedge.app",
            display_name="Simon Hayes",
            provider="email",
            is_premium=True,
            coin_balance=1_240_000,
        )
        db.add(user)
        db.flush()

        stars = players[: len(ROSTER)]  # tradeable market cards, not fodder

        for player in RNG.sample(stars, 5):
            db.add(
                Investment(
                    user_id=user.id,
                    player_id=player.id,
                    buy_price=int(player.prev_price * 0.9),
                    quantity=RNG.randint(1, 4),
                )
            )
            db.add(WatchlistItem(user_id=user.id, player_id=player.id))

        for player in RNG.sample(stars, 8):
            buy = int(player.prev_price * RNG.uniform(0.82, 0.94))
            sell = int(player.prev_price * RNG.uniform(1.0, 1.18))
            db.add(
                Trade(
                    user_id=user.id,
                    player_id=player.id,
                    buy_price=buy,
                    sell_price=sell,
                    quantity=RNG.randint(1, 3),
                    closed_at=now - dt.timedelta(days=RNG.randint(1, 25)),
                )
            )

        for player in RNG.sample(stars, 4):
            db.add(
                PriceAlert(
                    user_id=user.id,
                    player_id=player.id,
                    direction="below",
                    target_price=int(player.price * 0.9),
                )
            )

        # --- The user's club (raw material for the AI SBC Solver) ------------
        # Own most of the fodder, some duplicated, plus a couple of icons and
        # a favourite star so the "protect" options are demonstrable.
        club_pool = RNG.sample(fodder, int(len(fodder) * 0.8))
        for fp in club_pool:
            db.add(
                ClubPlayer(
                    user_id=user.id,
                    player_id=fp.id,
                    quantity=RNG.choices([1, 2, 3], weights=[7, 2, 1])[0],
                    untradeable=RNG.random() < 0.35,
                    first_owner=RNG.random() < 0.25,
                )
            )
        icons = [p for p in stars if p.card_type == "Icon"]
        for ic in icons:
            db.add(
                ClubPlayer(user_id=user.id, player_id=ic.id, quantity=1,
                           untradeable=True, is_favourite=True)
            )
        # A favourite gold the user never wants burned.
        fav = next(p for p in stars if p.name == "Saka")
        db.add(ClubPlayer(user_id=user.id, player_id=fav.id, quantity=1,
                          untradeable=True, is_favourite=True))

        for name, cat, req, reward, cost, pack, rating, diff, repeat, formation, min_r, min_c in SBCS:
            db.add(
                SBC(
                    name=name,
                    category=cat,
                    requirements=req,
                    reward=reward,
                    estimated_cost=cost,
                    pack_value=pack,
                    value_rating=rating,
                    difficulty=diff,
                    repeatable=repeat,
                    formation=formation,
                    squad_size=11,
                    min_rating=min_r,
                    min_chemistry=min_c,
                    expires_at=now + dt.timedelta(days=RNG.randint(2, 14)),
                )
            )

        db.commit()
        club_count = len(club_pool) + len(icons) + 1
        print(
            f"Seeded {len(players)} players ({len(fodder)} fodder), "
            f"{len(SBCS)} SBCs, {club_count} club players and demo user {user.email}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
