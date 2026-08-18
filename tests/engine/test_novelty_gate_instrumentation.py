"""Novelty-gate instrumentation (metrics-audit Workstream 2, §B): the pass marker now records
whether a proactive turn was novelty-GATED vs VOLUNTARILY passed, plus the discarded candidate text
— so a future gate-selectivity audit can tell them apart (previously one indistinguishable marker).

⚠️ The gated candidate was SILENCED: it must never reach an agent prompt. These tests pin (1) the
leak boundary (the day-channel formatters drop passed markers, so the candidate is absent from every
constructed agent payload) and (2) gated-vs-voluntary distinguishability on a synthetic record."""

from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import DayChannel, FiringReason
from tests.leak_test import check_gated_candidate_isolation

GATED_TEXT = "ZZZ_SILENCED_ECHO_CANDIDATE_ZZZ"


def _channel():
    """A day-1 channel with a real message, a novelty-gated pass (carrying the discarded text), and
    a voluntary pass — the three marker kinds the instrumentation must keep distinct."""
    return [
        DayChannel(day=1, seq=0, player="v1", message="I think w1 is a wolf."),
        DayChannel(
            day=1, seq=1, player="w2", message="", passed=True,
            firing_reason=FiringReason(tier="proactive"),
            gated=True, gated_candidate=GATED_TEXT,
        ),
        DayChannel(
            day=1, seq=2, player="v2", message="", passed=True,
            firing_reason=FiringReason(tier="proactive"),
            gated=False,
        ),
    ]


# --------------------------------------------------------------------------- leak boundary


def test_gated_candidate_absent_from_constructed_agent_payload():
    # build_agent_prompt_input is the payload -> prompt-input construction that reaches the model.
    payload = {
        "player_id": "v3",
        "player_role": "villager",
        "current_day": 1,
        "day_channel": _channel(),
    }
    prompt_input = build_agent_prompt_input(payload)
    blob = repr(prompt_input)
    assert GATED_TEXT not in blob, "novelty-gated candidate text leaked into the agent prompt input"
    # sanity: real spoken messages DO surface (the formatter isn't just dropping everything)
    assert "I think w1 is a wolf." in prompt_input["day_channel"]


def test_check_leak_helper_passes_clean_and_catches_injection():
    clean_log = [{
        "player_id": "v3", "player_role": "villager",
        "prompt_input": build_agent_prompt_input({
            "player_id": "v3", "player_role": "villager",
            "current_day": 1, "day_channel": _channel(),
        }),
    }]
    assert check_gated_candidate_isolation(clean_log, [GATED_TEXT]) == []

    # Positive control: a regression that formatted the candidate into a prompt must be caught.
    leaky_log = [{
        "player_id": "v3", "player_role": "villager",
        "prompt_input": {"day_channel": f"w2: {GATED_TEXT}"},
    }]
    assert check_gated_candidate_isolation(leaky_log, [GATED_TEXT])


# --------------------------------------------------------------------------- distinguishability


def test_gated_vs_voluntary_pass_are_distinguishable():
    ch = _channel()
    gated = [m for m in ch if m.passed and m.gated]
    voluntary = [m for m in ch if m.passed and not m.gated]
    assert len(gated) == 1 and len(voluntary) == 1
    # The gated pass carries the discarded text; the voluntary pass carries none.
    assert gated[0].gated_candidate == GATED_TEXT
    assert voluntary[0].gated_candidate == ""
    # Both remain hidden pass markers (message empty, passed True) — only `gated` tells them apart,
    # which is exactly what the previously-blocked gate-selectivity audit needs.
    assert gated[0].message == "" and voluntary[0].message == ""


def test_real_utterances_are_never_gated():
    real = DayChannel(day=1, seq=0, player="v1", message="hello")
    assert real.gated is False and real.gated_candidate == ""
