"""AI SBC Solver — build a valid squad for an SBC from a player pool.

Two exact game mechanics are modelled:

* **Squad rating** — FUT's above-average-weighted formula (an 84-rated squad is
  *not* just eleven 84s; higher cards pull the rating up faster).
* **Chemistry** — the modern FC 24/25 count-based model (club/league/nation
  thresholds, no positional links), capped at 33.

The solver itself is a transparent heuristic: seed with the cheapest eleven,
then run cost-aware local-search swaps to lift the squad to the required rating
and chemistry. It is deterministic (stable sort + fixed tie-breaks) so results
are reproducible and testable. Production would swap this for an ILP/constraint
solver behind the same interface — the API contract does not change.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Modern chemistry thresholds: count of squad-mates sharing the attribute → points.
_CLUB = {7: 3, 4: 2, 2: 1}
_LEAGUE = {8: 3, 5: 2, 3: 1}
_NATION = {8: 3, 5: 2, 2: 1}


@dataclass
class Candidate:
    player_id: int
    name: str
    rating: int
    position: str
    club: str
    league: str
    nation: str
    card_type: str
    cost: int  # coins you must spend to field this card (0 if already owned)
    market_value: int  # BIN — used for "least club value lost"
    source: str  # "club" | "market"
    untradeable: bool = False

    @property
    def is_icon(self) -> bool:
        return self.card_type == "Icon"


@dataclass
class Solution:
    squad: list[Candidate]
    squad_rating: int
    chemistry: int
    total_cost: int  # coins to buy the missing cards
    club_value_used: int  # market value of owned cards consumed
    feasible: bool
    to_buy: list[Candidate] = field(default_factory=list)
    unmet: list[str] = field(default_factory=list)


def squad_rating(squad: list[Candidate]) -> int:
    """FUT squad rating: average plus the above-average excess, redistributed."""
    n = len(squad)
    if n == 0:
        return 0
    ratings = [c.rating for c in squad]
    total = sum(ratings)
    avg = total / n
    excess = sum(r - avg for r in ratings if r > avg)
    return int((total + excess) / n + 1e-9)


def _points(count: int, table: dict[int, int]) -> int:
    for threshold, pts in table.items():  # dicts iterate high→low as defined
        if count >= threshold:
            return pts
    return 0


def chemistry(squad: list[Candidate]) -> int:
    """Modern count-based chemistry, capped at 33.

    Icons always earn full chemistry and contribute a doubled nation tally to
    their team-mates (their league/club boosts are simplified away).
    """
    clubs: dict[str, int] = {}
    leagues: dict[str, int] = {}
    nations: dict[str, int] = {}
    for c in squad:
        clubs[c.club] = clubs.get(c.club, 0) + 1
        leagues[c.league] = leagues.get(c.league, 0) + 1
        weight = 2 if c.is_icon else 1
        nations[c.nation] = nations.get(c.nation, 0) + weight

    total = 0
    for c in squad:
        if c.is_icon:
            total += 3
            continue
        pts = (
            _points(clubs.get(c.club, 0), _CLUB)
            + _points(leagues.get(c.league, 0), _LEAGUE)
            + _points(nations.get(c.nation, 0), _NATION)
        )
        total += min(3, pts)
    return min(33, total)


def _weight_key(objective: str):
    """Return a per-candidate sort key: lower is preferred."""
    if objective == "highest_rating":
        return lambda c: (-c.rating, c.cost, c.market_value)
    if objective == "min_club_loss":
        # Every card lost costs something: club value burned, or coins spent.
        return lambda c: (c.market_value if c.source == "club" else c.cost, -c.rating)
    # cheapest (default): spend the fewest coins, then — among free owned cards —
    # burn the least club value, so we don't waste an 86 to fill an 85 squad.
    return lambda c: (c.cost, c.market_value, -c.rating)


# Coins spent always outweigh club value burned in the "cheapest" objective.
_SPEND = 1_000_000


def _delta_weight(c: Candidate, objective: str) -> int:
    if objective == "highest_rating":
        return -c.rating
    if objective == "min_club_loss":
        return c.market_value if c.source == "club" else c.cost
    # cheapest: coins dominate; club value burned is the tie-break.
    return c.cost * _SPEND + c.market_value


def solve(
    pool: list[Candidate],
    *,
    size: int = 11,
    min_rating: int = 0,
    min_chemistry: int = 0,
    objective: str = "cheapest",
) -> Solution:
    if len(pool) < size:
        return Solution([], 0, 0, 0, 0, feasible=False, unmet=["Not enough players in pool"])

    key = _weight_key(objective)
    ordered = sorted(pool, key=key)
    squad = ordered[:size]
    remaining = ordered[size:]

    # --- Phase 1: lift squad rating with the cheapest upgrade swaps ----------
    for _ in range(600):
        if squad_rating(squad) >= min_rating:
            break
        worst = min(squad, key=lambda c: c.rating)
        upgrades = [c for c in remaining if c.rating > worst.rating]
        if not upgrades:
            break
        best = min(
            upgrades,
            key=lambda c: (_delta_weight(c, objective) - _delta_weight(worst, objective), -c.rating),
        )
        squad.remove(worst)
        remaining.remove(best)
        squad.append(best)
        remaining.append(worst)

    # --- Phase 2: lift chemistry without dropping below the rating floor -----
    for _ in range(400):
        cur_chem = chemistry(squad)
        if cur_chem >= min_chemistry:
            break
        best_swap: tuple[Candidate, Candidate] | None = None
        best_score: tuple[int, int] | None = None
        for out_p in squad:
            trial_base = [c for c in squad if c is not out_p]
            for in_c in remaining:
                trial = trial_base + [in_c]
                if squad_rating(trial) < min_rating:
                    continue
                gain = chemistry(trial) - cur_chem
                if gain <= 0:
                    continue
                added_weight = _delta_weight(in_c, objective) - _delta_weight(out_p, objective)
                score = (gain, -added_weight)
                if best_score is None or score > best_score:
                    best_score = score
                    best_swap = (out_p, in_c)
        if best_swap is None:
            break
        out_p, in_c = best_swap
        squad.remove(out_p)
        remaining.remove(in_c)
        squad.append(in_c)
        remaining.append(out_p)

    rating = squad_rating(squad)
    chem = chemistry(squad)
    to_buy = [c for c in squad if c.source == "market"]
    total_cost = sum(c.cost for c in to_buy)
    club_value_used = sum(c.market_value for c in squad if c.source == "club")

    unmet: list[str] = []
    if rating < min_rating:
        unmet.append(f"Squad rating {rating} < required {min_rating}")
    if chem < min_chemistry:
        unmet.append(f"Chemistry {chem} < required {min_chemistry}")

    return Solution(
        squad=sorted(squad, key=lambda c: c.rating, reverse=True),
        squad_rating=rating,
        chemistry=chem,
        total_cost=total_cost,
        club_value_used=club_value_used,
        feasible=not unmet,
        to_buy=sorted(to_buy, key=lambda c: c.cost),
        unmet=unmet,
    )
