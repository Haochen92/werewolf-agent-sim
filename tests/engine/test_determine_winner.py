"""Unit tests for the four-side terminal rule (Agents/nodes/orchestrator.py; role_sheet.md, "Win logic").

Pure functions over a synthetic OrchestratorGraph dict plus one real death-path run — no graph, no
LLM. Covers:

  * ``side_counts`` — the living players of each side (town, wolves, lone_killer, neutral), read
    off ``roles`` and the two survivor buckets.
  * ``determine_winner`` — the rule whose off-by-one would silently invalidate every win-rate
    number: town needs a living town player; wolves win once the lone killer is gone and they
    equal or outnumber town plus the neutral; the lone killer wins at one other living player or
    fewer, the neutral included.
  * ``is_draw`` and ``neutral_result`` — a board with no side alive, and how the neutral fared
    beside the winner (the speculator by its pick, the fortune teller by its points).
  * ``_max_days_winner`` — the cost-backstop tiebreak.
  * ``remove_from_buckets`` — a death is one removal from a bucket; there are no role markers.

Accounting fact under test: ``surviving_villagers`` is the NON-WOLF bucket (town, the lone killer
and the neutral); the sides are split by role, never by bucket. The builder below mirrors that.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from Agents.nodes import (
    _max_days_winner,
    day_resolution,
    determine_winner,
    is_draw,
    neutral_result,
    remove_from_buckets,
    side_counts,
)
from Agents.schemas import DayVote
from Agents.schemas.metrics import Metrics
from Agents.schemas.roles import TOWN, lineup, roles_on

TOWN_ROLES = roles_on(TOWN)
WOLF_ROLES = ["chanteuse", "illusionist"]
POINTS_TO_WIN = 3


def state(
    wolves: int = 0,
    town: int = 0,
    killer: bool = False,
    neutral: bool = False,
    *,
    killer_role: str = "serial_killer",
    neutral_role: str = "speculator",
    **extra,
) -> dict:
    """A state with the given living players per side. The full deal is in ``roles`` (the dead
    are in the role map but in no bucket); the buckets hold only the living, split by side."""
    wolf_players = [f"w{i}" for i in range(wolves)]
    town_players = [f"t{i}" for i in range(town)]
    roles = {f"w{i}": WOLF_ROLES[i % 2] for i in range(2)}
    roles.update({f"t{i}": TOWN_ROLES[i % len(TOWN_ROLES)] for i in range(len(TOWN_ROLES))})
    roles["k"] = killer_role
    roles["n"] = neutral_role
    s = {
        "roles": roles,
        "lineup": lineup(killer_role, neutral_role),
        "surviving_wolves": wolf_players,
        "surviving_villagers": [*town_players, *(["k"] if killer else []), *(["n"] if neutral else [])],
    }
    s.update(extra)
    return s


# --- side_counts: the living, by side -----------------------------------------------------

def test_side_counts_split_the_non_wolf_bucket_by_role():
    # The lone killer and the neutral ride the non-wolf bucket but are not town.
    assert side_counts(state(wolves=1, town=2, killer=True, neutral=True)) == {
        "town": 2, "wolves": 1, "lone_killer": 1, "neutral": 1,
    }


def test_side_counts_ignore_the_dead():
    # Every role is in the role map; only the buckets say who is alive.
    assert side_counts(state(wolves=2, town=3)) == {"town": 3, "wolves": 2, "lone_killer": 0, "neutral": 0}


def test_side_counts_default_on_empty_state():
    assert side_counts({}) == {"town": 0, "wolves": 0, "lone_killer": 0, "neutral": 0}


# --- remove_from_buckets: a death is one removal --------------------------------------------

def test_remove_from_buckets_takes_the_dead_out_of_both_buckets():
    st = state(wolves=2, town=2, killer=True)
    update: dict = {}
    remove_from_buckets(update, st, ["w1", "k"])
    assert update == {"surviving_wolves": ["w0"], "surviving_villagers": ["t0", "t1"]}
    assert st["surviving_wolves"] == ["w0", "w1"]  # the state itself is untouched


# --- determine_winner: TOWN -----------------------------------------------------------------

@pytest.mark.parametrize("town,neutral", [
    (3, False),  # wolves and the lone killer cleared
    (1, False),  # the last town player still counts
    (1, True),   # the neutral is no side: town still wins beside it
])
def test_town_wins(town, neutral):
    assert determine_winner(state(wolves=0, town=town, neutral=neutral)) == "villagers"


def test_town_does_not_win_while_the_lone_killer_lives():
    assert determine_winner(state(wolves=0, town=2, killer=True)) is None


def test_town_needs_a_living_town_player():
    # No wolf, no lone killer, no town: nobody wins, the board is a draw.
    board = state(wolves=0, town=0, neutral=True)
    assert determine_winner(board) is None
    assert is_draw(board)


# --- determine_winner: WOLVES (once the lone killer is gone, against town + neutral) ----------

@pytest.mark.parametrize("wolves,town,neutral", [
    (2, 2, False),  # exact parity
    (2, 1, True),   # two wolves vs one town + the speculator cannot be out-voted (role sheet)
    (3, 1, False),  # majority
    (1, 1, False),  # parity at the smallest scale
    (1, 0, True),   # one wolf vs the neutral alone
])
def test_wolves_win_when_they_equal_or_outnumber_town_and_neutral(wolves, town, neutral):
    assert determine_winner(state(wolves, town, neutral=neutral)) == "wolves"


@pytest.mark.parametrize("wolves,town,neutral", [
    (2, 2, True),   # two vs two + the speculator plays on (role sheet)
    (1, 1, True),   # the neutral's vote tips the count
    (1, 3, False),  # below parity
])
def test_wolves_do_not_win_below_town_plus_neutral(wolves, town, neutral):
    assert determine_winner(state(wolves, town, neutral=neutral)) is None


def test_wolf_parity_blocked_while_the_lone_killer_lives():
    assert determine_winner(state(wolves=1, town=1, killer=True)) is None


# --- determine_winner: the LONE KILLER (at most one other living player) ----------------------

@pytest.mark.parametrize("wolves,town,neutral", [
    (0, 1, False),  # 1v1 vs town: the day vote ties, no lynch, the killer cannot lose
    (1, 0, False),  # 1v1 vs a wolf
    (0, 0, True),   # 1v1 vs the speculator (role sheet)
    (0, 0, False),  # the killer is the last one standing
])
def test_lone_killer_wins_at_one_other_or_fewer(wolves, town, neutral):
    assert determine_winner(state(wolves, town, killer=True, neutral=neutral)) == "serial_killer"


@pytest.mark.parametrize("wolves,town,neutral", [
    (0, 1, True),   # the killer, the speculator and one town player play on (role sheet)
    (0, 2, False),
    (1, 1, False),
    (2, 0, False),  # the killer vs two wolves plays on
])
def test_lone_killer_does_not_win_with_two_or_more_others(wolves, town, neutral):
    assert determine_winner(state(wolves, town, killer=True, neutral=neutral)) is None


def test_the_necromancer_wins_under_its_own_name():
    board = state(wolves=0, town=1, killer=True, killer_role="necromancer")
    assert determine_winner(board) == "necromancer"


# --- determine_winner: ongoing --------------------------------------------------------------

def test_game_continues_balanced():
    assert determine_winner(state(wolves=1, town=2)) is None
    assert not is_draw(state(wolves=1, town=2))


# --- the draw and the neutral's result ------------------------------------------------------

def test_a_draw_is_won_only_by_a_self_picked_speculator():
    # The last wolf and the last town player killed each other: no side is alive.
    board = state(wolves=0, town=0, neutral=True, speculator_pick="self")
    assert is_draw(board)
    assert determine_winner(board) is None
    assert neutral_result(board, None, POINTS_TO_WIN) == "won"
    picked_town = {**board, "speculator_pick": "town"}
    assert neutral_result(picked_town, None, POINTS_TO_WIN) == "lost"


@pytest.mark.parametrize("pick,winner,expected", [
    ("town", "villagers", "won"),
    ("town", "wolves", "lost"),
    ("wolves", "wolves", "won"),
    ("wolves", "villagers", "lost"),
    ("lone_killer", "serial_killer", "won"),
    ("lone_killer", "necromancer", "won"),
    ("lone_killer", "villagers", "lost"),
    (None, "villagers", "lost"),  # never picked (dying before picking is a loss)
])
def test_the_speculator_wins_with_the_side_it_picked(pick, winner, expected):
    # Alive or dead (ruling 2026-10-09): the speculator is dead in this board.
    board = state(wolves=1, town=1, speculator_pick=pick)
    assert neutral_result(board, winner, POINTS_TO_WIN) == expected


def test_a_self_pick_loses_unless_the_speculator_stands_alone():
    board = state(wolves=0, town=1, neutral=True, speculator_pick="self")
    assert neutral_result(board, "villagers", POINTS_TO_WIN) == "lost"


@pytest.mark.parametrize("points,expected", [
    (POINTS_TO_WIN, f"won ({POINTS_TO_WIN} points)"),
    (POINTS_TO_WIN + 1, f"won ({POINTS_TO_WIN + 1} points)"),
    (POINTS_TO_WIN - 1, f"lost ({POINTS_TO_WIN - 1} points)"),
    (0, "lost (0 points)"),
])
def test_the_fortune_teller_wins_on_its_points_whoever_won(points, expected):
    board = state(wolves=0, town=2, neutral=True, neutral_role="fortune_teller", fortune_points=points)
    assert neutral_result(board, "villagers", POINTS_TO_WIN) == expected
    assert neutral_result(board, "wolves", POINTS_TO_WIN) == expected


# --- _max_days_winner: cost-backstop tiebreak -----------------------------------------------

def test_max_days_largest_side_wins():
    assert _max_days_winner(state(wolves=3, town=1)) == "wolves"
    assert _max_days_winner(state(wolves=1, town=2, killer=True)) == "villagers"


def test_max_days_tie_is_draw():
    # town == wolves at the top -> ambiguous -> draw (None).
    assert _max_days_winner(state(wolves=2, town=2)) is None


def test_max_days_the_neutral_is_no_side():
    # The neutral counts toward no side's size: one wolf, one town and the speculator is a tie.
    assert _max_days_winner(state(wolves=1, town=1, neutral=True)) is None


# --- day_resolution: the lone-killer lynch ---------------------------------------------------
# The lone killer cannot die at night on most nights, so the lynch is how it usually leaves the
# board: the bucket removal and the winner afterwards must agree.

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


def _lynch_state() -> dict:
    # 1 wolf, 1 town + the serial killer -> the killer alive blocks the wolf parity (W=1 >= T=1).
    return state(
        wolves=1, town=1, killer=True,
        current_day=2,
        day_votes=[DayVote(voter="w0", votee="k"), DayVote(voter="t0", votee="k")],
        day_channel=[],
        no_lynch_streak=0,
    )


def test_lynching_the_lone_killer_takes_it_out_of_the_bucket():
    with patch("Agents.nodes.orchestrator.langfuse", _fake_langfuse()):
        update = day_resolution(_lynch_state(), _lynch_runtime())

    assert update["voted_player"] == "k"
    assert update["surviving_villagers"] == ["t0"]
    assert update["surviving_wolves"] == ["w0"]


def test_winner_resolves_after_the_lone_killer_lynch():
    # Before the lynch: W=1 >= town=1 but the killer is alive -> the game continues.
    assert determine_winner(_lynch_state()) is None

    with patch("Agents.nodes.orchestrator.langfuse", _fake_langfuse()):
        update = day_resolution(_lynch_state(), _lynch_runtime())

    # The killer gone, W=1 >= town=1 -> wolves win.
    after = {**_lynch_state(), **update}
    assert determine_winner(after) == "wolves"


# --- the durable record's survivor breakdown --------------------------------------------------

def test_faction_survivors_splits_the_non_wolf_bucket_by_side():
    # The durable-record helper (scripts.run_batch.faction_survivors) must NOT report the lone
    # killer or the neutral as town, even though surviving_villagers (the non-wolf bucket) holds them.
    from scripts.run_batch import faction_survivors

    result = {
        "surviving_wolves": ["player_1"],
        "surviving_villagers": ["player_8", "player_2", "player_5"],
        "roles": {"player_1": "chanteuse", "player_8": "serial_killer", "player_2": "healer",
                  "player_5": "speculator"},
    }
    assert faction_survivors(result) == {
        "wolves": ["player_1"],
        "town": ["player_2"],
        "serial_killer": ["player_8"],
        "lone_killer": ["player_8"],
        "neutral": ["player_5"],
    }


def test_faction_survivors_handles_empty_state():
    from scripts.run_batch import faction_survivors

    assert faction_survivors({}) == {
        "wolves": [], "town": [], "serial_killer": [], "lone_killer": [], "neutral": [],
    }
