"""Unit tests for the sequential-discussion scheduler (Agents/scheduler.py).

Pure functions over a synthetic transcript — no LLM, no graph. Covers the reactive
obligations (open/discharge/freshness/K-cap/cooldown) and the select_next_speaker flow
(cap -> reactive -> terminate). The proactive tier the scheduler once had (quietest-first
picks, trailing-pass termination) was replaced by the day's rounds on 2026-10-07 (Phase 2).
"""
from __future__ import annotations

from Agents.game_config import DEFAULT_GAME_CONFIG
from Agents.schemas import (
    AddressedTarget,
    DayChannel,
    DiscussionPassReason,
    FiringReason,
)
from Agents.turn.scheduler import (
    build_reactive_queue,
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


def test_reactive_generation_failure_discharges_without_fake_response():
    failed_turn = DayChannel(
        day=1,
        seq=1,
        player="B",
        message="",
        passed=True,
        pass_reason=DiscussionPassReason.GENERATION_FAILED,
        firing_reason=FiringReason(tier="reactive", owes=["A"]),
    )
    q = queue([
        msg(0, "A", [at("B", "question")]),
        failed_turn,
    ])

    assert failed_turn.addressed_targets == []
    assert q == []


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


def test_counter_question_discharges_and_opens_reverse():
    # Regression (live 2026-07-26): B's reply tagged as pure `question` must still discharge
    # B's debt — excluding it re-fired B into near-duplicate turns (reactive turns bypass the
    # novelty gate), and the repeats read as "B never answered" to the rest of the table.
    q = queue([
        msg(0, "A", [at("B", "question", "accusation")]),  # B owes A
        msg(1, "B", [at("A", "question")]),                # B counter-asks: engagement
    ])
    # B's debt discharged; B's question opens the reverse -> A owes B, no B re-fire.
    assert [(i.agent_id, i.creditors, i.latest_sequence) for i in q] == [("A", ["B"], 1)]


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


# --- select_next_speaker: full flow -------------------------------------------

def test_open_obligation_fires_the_debtor():
    d = select_next_speaker([msg(0, "A", [at("B", "question")])], SURV, DEFAULT_GAME_CONFIG)
    assert d.terminate is False
    assert d.speaker == "B"
    assert d.firing_reason.tier == "reactive"
    assert d.firing_reason.owes == ["A"]


def test_cap_counts_real_utterances_only():
    cfg = DEFAULT_GAME_CONFIG
    cap = cfg.utterance_cap(len(SURV))
    at_cap = [msg(i, "A" if i % 2 else "B") for i in range(cap)]  # nothing owed: ends at once
    assert select_next_speaker(at_cap, SURV, cfg).terminate_reason == "cap"
    # cap-1 real utterances + a couple passes must NOT cap (passes don't count); with nothing
    # owed, the chains are simply over.
    below = [msg(i, "A") for i in range(cap - 1)] + [msg(98, "C", passed=True), msg(99, "D", passed=True)]
    assert select_next_speaker(below, SURV, cfg).terminate_reason == "no_obligations"


def test_nothing_owed_ends_the_chains():
    d = select_next_speaker([], SURV, DEFAULT_GAME_CONFIG)
    assert d.terminate is True
    assert d.terminate_reason == "no_obligations"


def test_invalid_target_ignored_with_valid_players():
    # "all" (not a real player) must not become an obligation's debtor; B (valid) does.
    q = build_reactive_queue(
        [msg(0, "A", [at("all", "question"), at("B", "question")])],
        per_pair_cap=2,
        reengagement_cooldown=99,
        valid_players={"A", "B", "C"},
    )
    assert [(i.agent_id, i.creditors) for i in q] == [("B", ["A"])]


def test_select_next_never_picks_non_survivor_target():
    # An agent addressing "all" (not a real player) owes nobody an answer and nobody owes it one:
    # the chains end rather than a non-survivor being scheduled (no KeyError upstream).
    d = select_next_speaker(
        [msg(0, "A", [at("all", "question", "accusation")])],
        ["A", "B", "C"],
        DEFAULT_GAME_CONFIG,
    )
    assert d.terminate is True
    assert d.terminate_reason == "no_obligations"
