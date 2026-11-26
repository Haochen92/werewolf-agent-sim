"""Can the Vigilante test still fail? Runs the test against two deliberately broken versions of the
bullet rule and expects it to fail on both. 2026-11-17.

The breaks are made with pytest's monkeypatch inside this process; no engine file is edited.

- spent_twice: the night resolution spends the shot's bullet twice.
- spent_per_run_of_the_turn: one bullet is spent for each time the Vigilante's night turn ran
  before its shot was resolved. A human's turn runs once up to the pause and again on resume, so
  this break shows only across a pause: it is the double spend the test exists to catch.

Run each case in its own process, from the repository root: the test's game id is fixed, and a
second game under the same id in one process resumes on top of the first's checkpoint.
  F=evidence/_study/engineering_notes/measurements/u13_vig_mutations.py
  for k in control spent_twice spent_per_run; do poetry run pytest -q -p no:cacheprovider $F -k $k; done
Every case passes when the test under check FAILS on the broken rule; the control case passes when
the test passes on the unbroken engine.
"""
from collections import Counter

import pytest

from Agents.nodes.night import resolution, solo
from tests.engine import test_ten_seat_game as T

TEST = T.test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume


def _break_spent_twice(monkeypatch):
    real = resolution._spent

    def spent_twice(state, choices, outcome):
        once = real(state, choices, outcome)
        return real({**state, "uses_left": once}, choices, outcome)

    monkeypatch.setattr(resolution, "_spent", spent_twice)


def _break_spent_per_run_of_the_turn(monkeypatch):
    runs = Counter()  # (day, actor) -> times the Vigilante's night turn started
    real_turn, real_spent = solo.run_memory_informed_night_action, resolution._spent

    def counted_turn(payload, *args, **kwargs):
        if payload["player_role"] == "vigilante":
            runs[(payload["current_day"], payload["player_id"])] += 1  # work done before the pause
        return real_turn(payload, *args, **kwargs)

    def spent_per_run(state, choices, outcome):
        uses = real_spent(state, choices, outcome)
        before = state.get("uses_left", {}).get("vigilante")
        for c in choices:
            if c.role == "vigilante" and before is not None and uses.get("vigilante") == before - 1:
                uses["vigilante"] = max(0, before - runs[(state["current_day"], c.actor)])
        return uses

    monkeypatch.setattr(solo, "run_memory_informed_night_action", counted_turn)
    monkeypatch.setattr(resolution, "_spent", spent_per_run)


def test_control_the_unbroken_engine_passes(monkeypatch):
    TEST(monkeypatch)


@pytest.mark.parametrize("brk", [_break_spent_twice, _break_spent_per_run_of_the_turn])
def test_the_vigilante_test_fails_when_the_bullet_rule_is_broken(monkeypatch, brk):
    brk(monkeypatch)
    with pytest.raises(AssertionError) as failure:
        TEST(monkeypatch)
    # It must fail on the bullet count, not on some other assertion the break happened to upset.
    assert 'final["uses_left"]["vigilante"] == 1' in failure.traceback[-1].statement.lines[0]
