"""Unit tests for the locked 3-faction terminal rule (Agents/nodes.py).

Pure functions over a synthetic OrchestratorGraph dict plus one real death-path
run — no graph, no LLM. Covers:

  * ``determine_winner`` — the rule whose off-by-one would silently invalidate
    every win-rate number in Phase C.
  * ``_faction_counts`` — the SK-in-villager-bucket accounting it relies on.
  * ``_max_days_winner`` — the cost-backstop tiebreak.
  * the SK count invariant: ``surviving_villagers`` (the non-wolf bucket)
    contains the serial killer IFF ``serial_killer_player`` is set, and the two
    are cleared together on death.

Accounting fact under test: ``surviving_villagers`` is the *non-wolf* bucket and
INCLUDES the serial killer; town = non_wolf - sk. The builder below mirrors that.

Why the invariant test only covers the day lynch: the SK is night-immune
(``_resolved`` returns "immune" for ``sk_player`` in night_resolution), so a
day lynch is the ONLY path that can remove the SK from the bucket. And the SK is
the only faction ``_faction_counts`` subtracts out — healer/investigator/vigilante
are plain town in the count — so the lynch path is the whole count-affecting surface.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from Agents.nodes import (
    _faction_counts,
    _max_days_winner,
    _nullify_special_roles,
    day_resolution,
    determine_winner,
)
from Agents.schemas import DayVote
from Agents.schemas.metrics import Metrics


def state(wolves: int = 0, town: int = 0, sk: bool = False, **extra) -> dict:
    """Build a state with the given survivor counts.

    ``town`` is the number of pure-town survivors; when ``sk`` is set the SK is
    added to ``surviving_villagers`` (the non-wolf bucket) on top of ``town``,
    mirroring the live invariant (SK in the bucket + marker set).
    """
    villagers = [f"t{i}" for i in range(town)]
    if sk:
        villagers = [*villagers, "sk_player"]
    s = {
        "surviving_wolves": [f"w{i}" for i in range(wolves)],
        "surviving_villagers": villagers,
        "serial_killer_player": "sk_player" if sk else None,
    }
    s.update(extra)
    return s


# --- _faction_counts: the SK-bucket accounting -------------------------------

def test_faction_counts_excludes_sk_from_town():
    # 2 pure town + SK in the non-wolf bucket -> town=2, sk=1, not town=3.
    assert _faction_counts(state(wolves=1, town=2, sk=True)) == (1, 2, 1)


def test_faction_counts_no_sk():
    assert _faction_counts(state(wolves=2, town=3, sk=False)) == (2, 3, 0)


def test_faction_counts_defaults_on_empty_state():
    assert _faction_counts({}) == (0, 0, 0)


# --- determine_winner: TOWN --------------------------------------------------

@pytest.mark.parametrize("wolves,town,sk,expected", [
    (0, 3, False, "villagers"),   # wolves cleared, no SK
    (0, 1, False, "villagers"),   # last lone villager still counts as a win
    (0, 0, False, "villagers"),   # degenerate: nobody hostile left
])
def test_town_wins(wolves, town, sk, expected):
    assert determine_winner(state(wolves, town, sk)) == expected


def test_town_does_not_win_while_sk_alive():
    # wolves cleared but SK still breathing -> not a town win yet.
    assert determine_winner(state(wolves=0, town=2, sk=True)) is None


# --- determine_winner: WOLVES (parity, only once SK is gone) -----------------

@pytest.mark.parametrize("wolves,town,expected", [
    (2, 2, "wolves"),   # exact parity W==T
    (3, 1, "wolves"),   # majority
    (1, 1, "wolves"),   # parity at the smallest scale
])
def test_wolves_win_on_parity_no_sk(wolves, town, expected):
    assert determine_winner(state(wolves, town, sk=False)) == expected


def test_wolves_do_not_win_below_parity():
    assert determine_winner(state(wolves=1, town=3, sk=False)) is None


def test_wolf_parity_blocked_while_sk_alive():
    # W>=T (1>=1) but the SK wildcard is still in play -> rule 3 requires sk==0.
    assert determine_winner(state(wolves=1, town=1, sk=True)) is None


# --- determine_winner: SERIAL KILLER (night-immune, T+W <= 1) ----------------

@pytest.mark.parametrize("wolves,town", [
    (0, 1),   # 1v1 vs town: day vote ties -> no lynch -> SK can't lose
    (1, 0),   # 1v1 vs a wolf
    (0, 0),   # SK is the last one standing
])
def test_sk_wins_when_one_or_fewer_others(wolves, town):
    assert determine_winner(state(wolves, town, sk=True)) == "serial_killer"


@pytest.mark.parametrize("wolves,town", [
    (0, 2),   # SK + 2 town -> T+W=2 -> not yet
    (1, 1),   # SK + wolf + town -> T+W=2 -> not yet
    (2, 0),   # SK + 2 wolves -> T+W=2 -> not yet
])
def test_sk_does_not_win_with_two_or_more_others(wolves, town):
    assert determine_winner(state(wolves, town, sk=True)) is None


# --- determine_winner: ongoing ----------------------------------------------

def test_game_continues_balanced():
    assert determine_winner(state(wolves=1, town=2, sk=False)) is None


# --- _max_days_winner: cost-backstop tiebreak --------------------------------

def test_max_days_largest_faction_wins():
    assert _max_days_winner(state(wolves=3, town=1, sk=False)) == "wolves"
    assert _max_days_winner(state(wolves=1, town=2, sk=True)) == "villagers"


def test_max_days_tie_is_draw():
    # villagers==wolves at the top -> ambiguous -> draw (None).
    assert _max_days_winner(state(wolves=2, town=2, sk=False)) is None


# --- _nullify_special_roles: the marker half of the invariant ----------------

@pytest.mark.parametrize("role_key", [
    "healer_player",
    "investigator_player",
    "serial_killer_player",
    "vigilante_player",
])
def test_nullify_clears_the_dead_players_role_marker(role_key):
    st = {role_key: "victim"}
    update: dict = {}
    _nullify_special_roles(update, "victim", st)
    assert update[role_key] is None


def test_nullify_is_noop_for_a_plain_player():
    st = {"serial_killer_player": "sk_player", "healer_player": "doc"}
    update: dict = {}
    _nullify_special_roles(update, "plain_villager", st)
    assert update == {}  # nobody special died -> no markers touched


def test_nullify_only_touches_the_matching_marker():
    st = {"serial_killer_player": "sk_player", "healer_player": "doc"}
    update: dict = {}
    _nullify_special_roles(update, "sk_player", st)
    assert update == {"serial_killer_player": None}  # healer untouched


# --- day_resolution: the full SK-lynch coupling ------------------------------
# The one count-affecting death path. Asserts marker-clear and bucket-removal
# happen together, and that determine_winner then reflects the new counts.

class _NullSpan:
    def update(self, *args, **kwargs):
        pass


class _NullObservation:
    """Stand-in for langfuse.start_as_current_observation(...) (a context manager)."""

    def __enter__(self):
        return _NullSpan()

    def __exit__(self, *exc):
        return False


def _fake_langfuse():
    fake = SimpleNamespace()
    fake.start_as_current_observation = lambda *a, **k: _NullObservation()
    return fake


def _lynch_runtime() -> SimpleNamespace:
    return SimpleNamespace(context={"metrics": Metrics()})


def _lynch_state(sk_alive: bool) -> dict:
    # 1 wolf, 1 town, + SK -> SK alive blocks the wolf parity (W=1 >= town=1).
    villagers = ["t0"] + (["sk_player"] if sk_alive else [])
    return {
        "current_day": 2,
        "surviving_wolves": ["w0"],
        "surviving_villagers": villagers,
        "serial_killer_player": "sk_player" if sk_alive else None,
        "healer_player": None,
        "investigator_player": None,
        "vigilante_player": None,
        "roles": {"w0": "wolf", "t0": "villager", "sk_player": "serial_killer"},
        "day_votes": [
            DayVote(voter="w0", votee="sk_player"),
            DayVote(voter="t0", votee="sk_player"),
        ],
        "day_channel": [],
        "no_lynch_streak": 0,
    }


def test_lynching_sk_clears_marker_and_bucket_together():
    with patch("Agents.nodes.orchestrator.langfuse", _fake_langfuse()):
        update = day_resolution(_lynch_state(sk_alive=True), _lynch_runtime())

    # The two halves of the invariant move as one: marker -> None AND the SK
    # leaves the non-wolf bucket. Divergence here is the silent-count bug.
    assert update["serial_killer_player"] is None
    assert "sk_player" not in update["surviving_villagers"]
    assert update["surviving_villagers"] == ["t0"]


def test_winner_resolves_after_sk_lynch():
    # Before the lynch: W=1 >= town=1 but SK alive -> game continues.
    assert determine_winner(_lynch_state(sk_alive=True)) is None

    with patch("Agents.nodes.orchestrator.langfuse", _fake_langfuse()):
        update = day_resolution(_lynch_state(sk_alive=True), _lynch_runtime())

    # Apply the resolution's update, then re-resolve: SK gone, W=1 >= town=1
    # with sk==0 -> wolves win. A stale marker would wrongly keep this at None.
    after = {**_lynch_state(sk_alive=True), **update}
    assert determine_winner(after) == "wolves"


def test_faction_survivors_splits_sk_out_of_town():
    # The durable-record helper (scripts.run_batch.faction_survivors) must NOT report the SK as a
    # villager, even though surviving_villagers (the non-wolf bucket) contains it. Mirrors the smoke
    # endgame: player_1 wolf, player_8 SK both alive.
    from scripts.run_batch import faction_survivors

    result = {
        "surviving_wolves": ["player_1"],
        "surviving_villagers": ["player_8", "player_2"],  # non-wolf bucket: SK + a real villager
        "roles": {"player_1": "wolf", "player_8": "serial_killer", "player_2": "villager"},
    }
    fs = faction_survivors(result)
    assert fs == {
        "wolves": ["player_1"],
        "town": ["player_2"],          # SK excluded
        "serial_killer": ["player_8"],  # SK surfaced on its own axis
    }


def test_faction_survivors_handles_empty_state():
    from scripts.run_batch import faction_survivors

    assert faction_survivors({}) == {"wolves": [], "town": [], "serial_killer": []}
