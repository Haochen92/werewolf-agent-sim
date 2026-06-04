"""Unit tests for the sequential-discussion scheduler (Agents/scheduler.py).

Pure functions over a synthetic transcript — no LLM, no graph. Covers the locked
Phase-0 design: reactive obligations (open/discharge/freshness/K-cap/cooldown),
proactive ranking (quietest-first + seeded tiebreak, pass rotation), and the
select_next_speaker flow (cap -> reactive -> trailing-pass -> proactive).
"""
from __future__ import annotations

from Agents.game_config import DEFAULT_GAME_CONFIG, GameConfig
from Agents.schemas import AddressedTarget, DayChannel
from Agents.scheduler import (
    build_reactive_queue,
    rank_proactive,
    select_next_speaker,
)


# --- builders -----------------------------------------------------------------

def at(target: str, form: str, stance: str = "neutral") -> AddressedTarget:
    return AddressedTarget(target=target, addressed_form=form, stance=stance)


def msg(seq: int, player: str, targets=None, passed: bool = False) -> DayChannel:
    return DayChannel(
        day=1, seq=seq, player=player, message="x",
        addressed_targets=targets or [], passed=passed,
    )


def queue(day_channel, per_pair_cap=2, cooldown=99):
    """build_reactive_queue with a large cooldown by default (cooldown off unless tested)."""
    return build_reactive_queue(day_channel, per_pair_cap=per_pair_cap, reengagement_cooldown=cooldown)


SURV = ["A", "B", "C", "D"]


# --- build_reactive_queue: open / discharge -----------------------------------

def test_question_opens_obligation_on_target():
    q = queue([msg(0, "A", [at("B", "question")])])
    assert [(i.agent_id, i.creditors, i.latest_sequence) for i in q] == [("B", ["A"], 0)]


def test_accusation_opens_defense_obligation():
    q = queue([msg(0, "A", [at("B", "mention", "accusation")])])
    assert [i.agent_id for i in q] == ["B"]


def test_response_discharges_open_obligation():
    q = queue([
        msg(0, "A", [at("B", "question")]),
        msg(1, "B", [at("A", "response", "defense")]),
    ])
    assert q == []  # B answered A -> nothing open


def test_bare_response_with_no_debt_is_inert():
    q = queue([msg(0, "B", [at("A", "response", "agreement")])])
    assert q == []  # phantom ledger entry, but never open -> not in queue


# --- freshness ----------------------------------------------------------------

def test_restating_while_open_adds_no_second_obligation():
    q = queue([
        msg(0, "A", [at("B", "question", "accusation")]),
        msg(1, "A", [at("B", "mention", "accusation")]),  # freshness no-op
    ])
    # one obligation, recency NOT bumped to seq 1 (anti-spam)
    assert len(q) == 1
    assert q[0].agent_id == "B"
    assert q[0].latest_sequence == 0


# --- per-pair K-cap (consecutive) + cooldown ----------------------------------

def test_kplus1_open_blocked_within_burst():
    q = queue([
        msg(0, "A", [at("B", "question")]),
        msg(1, "B", [at("A", "response")]),    # cycle 1
        msg(2, "A", [at("B", "question")]),
        msg(3, "B", [at("A", "response")]),    # cycle 2
        msg(4, "A", [at("B", "question")]),    # (K+1)th open -> BLOCKED
    ], per_pair_cap=2)
    assert q == []  # nothing open: the 3rd open was refused


def test_different_speaker_is_a_fresh_edge():
    q = queue([
        msg(0, "A", [at("B", "question")]),
        msg(1, "B", [at("A", "response")]),    # A->B cycle 1
        msg(2, "A", [at("B", "question")]),
        msg(3, "B", [at("A", "response")]),    # A->B cycle 2 (exhausted)
        msg(4, "A", [at("B", "question")]),    # A->B blocked
        msg(5, "C", [at("B", "mention", "accusation")]),  # C->B: brand-new edge
    ], per_pair_cap=2)
    assert [(i.agent_id, i.creditors) for i in q] == [("B", ["C"])]


def test_cooldown_resets_cap_after_untouched_gap():
    base = [
        msg(0, "A", [at("B", "question")]),
        msg(1, "B", [at("A", "response")]),
        msg(2, "A", [at("B", "question")]),
        msg(3, "B", [at("A", "response")]),    # cycles=2, last_touch=3
        msg(4, "A", [at("B", "question")]),    # blocked (gap 1 < 3)
    ]
    assert queue(base, per_pair_cap=2, cooldown=3) == []
    # gap of 7 (>= M=3) since last touch at seq3 -> cap resets -> reopens
    q = queue(base + [msg(10, "A", [at("B", "question")])], per_pair_cap=2, cooldown=3)
    assert [(i.agent_id, i.latest_sequence) for i in q] == [("B", 10)]


# --- counter-accusation: one message discharges AND opens the reverse ---------

def test_counter_accusation_discharges_and_opens_reverse():
    q = queue([
        msg(0, "A", [at("B", "question", "accusation")]),       # B owes A
        msg(1, "B", [at("A", "response", "accusation")]),       # B answers A AND accuses A
    ])
    # A->B discharged; B->A newly open -> A now owes B
    assert [(i.agent_id, i.creditors, i.latest_sequence) for i in q] == [("A", ["B"], 1)]


# --- grouping: multi-accused answers everyone in one turn ---------------------

def test_multiple_creditors_group_under_one_debtor():
    q = queue([
        msg(0, "A", [at("B", "question")]),
        msg(1, "C", [at("B", "mention", "accusation")]),
    ])
    assert len(q) == 1
    item = q[0]
    assert item.agent_id == "B"
    assert sorted(item.creditors) == ["A", "C"]
    assert item.latest_sequence == 1  # freshest poke


def test_queue_sorted_by_recency_desc():
    q = queue([
        msg(0, "A", [at("B", "question")]),   # B owes A @0
        msg(1, "C", [at("D", "question")]),   # D owes C @1
    ])
    assert [i.agent_id for i in q] == ["D", "B"]  # most-recent first


# --- rank_proactive -----------------------------------------------------------

def test_proactive_ranks_quietest_first():
    # only A has spoken (seq 0) -> A ranks last; never-spoke rank ahead
    ranked = rank_proactive([msg(0, "A")], SURV, seed=0)
    assert ranked[-1] == "A"


def test_proactive_pass_marker_rotates_passer_down():
    # a pass is a real DayChannel entry -> advances recency -> passer sinks
    ranked = rank_proactive([msg(0, "B", passed=True)], SURV, seed=0)
    assert ranked[-1] == "B"


def test_proactive_seeded_deterministic_and_a_survivor():
    a = rank_proactive([], SURV, seed=7)
    b = rank_proactive([], SURV, seed=7)
    assert a == b
    assert set(a) == set(SURV)


# --- select_next_speaker: full flow -------------------------------------------

def test_reactive_takes_priority_over_proactive():
    d = select_next_speaker([msg(0, "A", [at("B", "question")])], SURV, DEFAULT_GAME_CONFIG, seed=0)
    assert d.terminate is False
    assert d.speaker == "B"
    assert d.firing_reason.tier == "reactive"
    assert d.firing_reason.owes == ["A"]


def test_opener_is_proactive_and_deterministic():
    d1 = select_next_speaker([], SURV, DEFAULT_GAME_CONFIG, seed=3)
    d2 = select_next_speaker([], SURV, DEFAULT_GAME_CONFIG, seed=3)
    assert d1.firing_reason.tier == "proactive"
    assert d1.speaker in SURV
    assert d1.speaker == d2.speaker


def test_trailing_p_passes_terminates():
    cfg = DEFAULT_GAME_CONFIG
    passes = [msg(i, p, passed=True) for i, p in enumerate(["A", "B", "C"][: cfg.proactive_budget])]
    d = select_next_speaker(passes, SURV, cfg, seed=0)
    assert d.terminate is True
    assert d.terminate_reason == "trailing_passes"


def test_one_real_utterance_resets_pass_streak():
    cfg = DEFAULT_GAME_CONFIG
    # P-1 passes then a real utterance: streak broken -> not terminate
    entries = [msg(0, "A", passed=True), msg(1, "B", passed=True), msg(2, "C")]
    d = select_next_speaker(entries, SURV, cfg, seed=0)
    assert d.terminate is False
    assert d.firing_reason.tier == "proactive"


def test_cap_counts_real_utterances_only():
    cfg = DEFAULT_GAME_CONFIG
    cap = cfg.utterance_cap(len(SURV))
    at_cap = [msg(i, "A" if i % 2 else "B") for i in range(cap)]
    assert select_next_speaker(at_cap, SURV, cfg, seed=0).terminate_reason == "cap"
    # cap-1 real utterances + a couple passes must NOT cap (passes don't count)
    below = [msg(i, "A") for i in range(cap - 1)] + [msg(98, "C", passed=True), msg(99, "D", passed=True)]
    assert select_next_speaker(below, SURV, cfg, seed=0).terminate is False


def test_no_eligible_when_no_survivors():
    d = select_next_speaker([], [], DEFAULT_GAME_CONFIG, seed=0)
    assert d.terminate is True
    assert d.terminate_reason == "no_eligible"
