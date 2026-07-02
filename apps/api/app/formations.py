"""Formations and position assignment for the AI SBC Solver v2.

Modern FC chemistry only counts a player who is *in position*, so a valid squad
must be assignable to its formation's slots. We model each formation as an
ordered list of slot positions and check assignability with maximum bipartite
matching (Kuhn's algorithm) over "which players can play which slot".
"""
from __future__ import annotations

# Slot a natural position can cover (primary + common alt-positions).
_ELIGIBLE: dict[str, set[str]] = {
    "GK": {"GK"},
    "CB": {"CB"},
    "RB": {"RB", "RWB"},
    "LB": {"LB", "LWB"},
    "RWB": {"RB", "RWB"},
    "LWB": {"LB", "LWB"},
    "CDM": {"CDM", "CM"},
    "CM": {"CM", "CDM", "CAM"},
    "CAM": {"CAM", "CM"},
    "RM": {"RM", "RW"},
    "LM": {"LM", "LW"},
    "RW": {"RW", "RM"},
    "LW": {"LW", "LM"},
    "CF": {"CF", "ST", "CAM"},
    "ST": {"ST", "CF"},
}

FORMATIONS: dict[str, list[str]] = {
    "4-3-3": ["GK", "RB", "CB", "CB", "LB", "CM", "CM", "CM", "RW", "ST", "LW"],
    "4-4-2": ["GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST"],
    "4-2-3-1": ["GK", "RB", "CB", "CB", "LB", "CDM", "CDM", "RM", "CAM", "LM", "ST"],
}


def can_play(natural_position: str, slot: str) -> bool:
    return slot in _ELIGIBLE.get(natural_position, {natural_position})


def slots_for(formation: str) -> list[str]:
    return FORMATIONS.get(formation, FORMATIONS["4-3-3"])


def assign_partial(positions: list[str], slots: list[str]) -> list[int]:
    """Best-effort matching. Returns ``slot_to_player`` with -1 for unfilled slots.

    ``positions[i]`` is player i's natural position.
    """
    n_slots = len(slots)
    slot_to_player = [-1] * n_slots

    def augment(player: int, seen: set[int]) -> bool:
        for s in range(n_slots):
            if s in seen or not can_play(positions[player], slots[s]):
                continue
            seen.add(s)
            if slot_to_player[s] == -1 or augment(slot_to_player[s], seen):
                slot_to_player[s] = player
                return True
        return False

    for player in range(len(positions)):
        augment(player, set())
    return slot_to_player


def assign(positions: list[str], slots: list[str]) -> list[int] | None:
    """Full assignment, or ``None`` if the squad cannot fill the formation."""
    result = assign_partial(positions, slots)
    return None if any(p == -1 for p in result) else result


def matched_count(positions: list[str], slots: list[str]) -> int:
    return sum(1 for p in assign_partial(positions, slots) if p != -1)
