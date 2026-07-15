"""Faction win-clocks computed from PUBLIC board facts.

The game's terminal rule (``Agents.nodes.orchestrator.determine_winner``) gives each faction a
countdown clock — eliminations until that faction's win condition is met:

- wolf clock = (town + SK) − wolves. Counting the SK among the bodies is exact, not an
  approximation: wolves cannot win while the SK lives, so its death is one of the eliminations
  the clock counts.
- SK clock = (town + wolves) − 1 — night-immune + a guaranteed kill ⇒ the SK wins with one
  other survivor left. Absent while no SK is alive.
- town clock = wolves + SK — town wins when both threat factions are gone.

Every clock is read by all three factions at once (zero-sum: one faction's win clock is the
others' danger clock). ``distance_to_parity`` = min of the two EVIL clocks — "the leading
remaining evil faction", the model-facing field definition; ``is_swing`` = min of ALL THREE
clocks ≤ 1 — "the game can end within one elimination, in some direction" (the 2026-07-11
ruling, evidence/credit/report.md §6).

These numbers are PUBLIC information, not omniscient: the cast is fixed and announced in the
rules, and every death path announces the dead player's role (``DeathRecord``), so the fixed
cast minus the revealed dead is exactly what remains — and the clocks need only COUNTS, never
identities. That is why the live memory-query fill states them as known board facts
(``Agents.memory.retrieval.situation_agent``) and why the eval-side truth
(``evaluation.src.loop.decision_scoring.query_criticality``) computes the same arithmetic from
the true role map: the two must agree wherever the census exists.
"""

from collections.abc import Iterable, Mapping

THREAT_ROLE_NAMES = ("wolf", "serial_killer")


def _role_of(death) -> str | None:
    """A DeathRecord's revealed role, tolerant of dict-shaped records (replayed/JSON payloads)."""
    return death.get("role") if isinstance(death, Mapping) else getattr(death, "role", None)


def alive_role_counts(
    cast_role_counts: Mapping[str, int], dead_roster: Iterable
) -> dict[str, int]:
    """The public census of roles still in play: the fixed cast minus the revealed dead."""
    remaining = dict(cast_role_counts)
    for dead in dead_roster:
        role = _role_of(dead)
        if role:
            remaining[role] = remaining.get(role, 0) - 1
    return remaining


def criticality_from_counts(wolves: int, sk: int, town: int) -> tuple[int, int, bool]:
    """``(players_alive, distance_to_parity, is_swing)`` from live faction counts."""
    n = wolves + sk + town
    wolf_clock = (town + sk) - wolves
    town_clock = wolves + sk
    clocks = [wolf_clock, town_clock]
    evil_clocks = [wolf_clock]
    if sk:
        sk_clock = (town + wolves) - 1
        clocks.append(sk_clock)
        evil_clocks.append(sk_clock)
    return n, min(evil_clocks), min(clocks) <= 1


def criticality_from_census(
    cast_role_counts: Mapping[str, int] | None, dead_roster: Iterable | None
) -> tuple[int, int, bool] | None:
    """Census-based criticality — the agent-knowable derivation. ``None`` when no census is
    available (legacy payloads that never carried ``cast_role_counts``), so callers can fall
    back to the LLM's own fill."""
    if not cast_role_counts:
        return None
    remaining = alive_role_counts(cast_role_counts, dead_roster or [])
    wolves = max(0, remaining.get("wolf", 0))
    sk = max(0, remaining.get("serial_killer", 0))
    town = sum(
        max(0, count) for role, count in remaining.items() if role not in THREAT_ROLE_NAMES
    )
    return criticality_from_counts(wolves, sk, town)
