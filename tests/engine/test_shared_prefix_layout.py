"""The shared-prefix prompt layout (Agents/prompts/layout.py, WW_PROMPT_LAYOUT=shared_prefix): every
seat turn and memory lookup opens with the same system message and public record, the record ends on
the user message's only transcript rule (where Claude marks and OpenAI breaks), a held-back draft never
reaches a prompt and its note is dropped, and OpenAI requests get explicit breakpoints. With the flag
unset, today's templates are untouched (the exact-prompt golden pins them)."""
from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from Agents.llm_factory.providers.common import TRANSCRIPT_RULE
from Agents.prompts.layout import LAYOUT_ENV, PUBLIC_RECORD, SHARED_SYSTEM
from Agents.schemas import DayChannel
from Agents.schemas.roles import ROLE_SPECS
from tests.fixtures.day_discuss_prompt_golden import ROLES, _seat, speaker_payload


@pytest.fixture
def shared(monkeypatch):
    monkeypatch.setenv(LAYOUT_ENV, "shared_prefix")


def _templates():
    from Agents.prompts.day_discuss import day_discuss_template
    from Agents.prompts.day_vote import day_vote_template
    from Agents.prompts.memory.situation_summary import situation_summary_template
    from Agents.prompts.night import carrier_template, night_template, wolf_chat_template

    out = {"lookup": situation_summary_template()}
    for role in ROLES:
        out[f"discuss:{role}"] = day_discuss_template(role)
        out[f"vote:{role}"] = day_vote_template(role)
        if ROLE_SPECS[role].pack:
            out[f"wolf_chat:{role}"] = wolf_chat_template(role)
            out[f"carrier:{role}"] = carrier_template(role)
        if ROLE_SPECS[role].target_field:
            out[f"night:{role}"] = night_template(role)
    return out


def _render(template, inputs: dict) -> list[tuple[str, str]]:
    values = {v: inputs.get(v, f"<{v}>") for v in template.input_variables}
    return [(m.type, m.content) for m in template.invoke(values).to_messages()]


def _prefix(messages: list[tuple[str, str]]) -> str:
    """The system message and the user message up to and including its transcript rule."""
    (_, system), (_, human) = messages
    rule = TRANSCRIPT_RULE.search(human)
    return system + "\n" + human[: rule.end()]


def test_every_template_opens_with_the_shared_system_and_public_record(shared):
    for name, template in _templates().items():
        system, human = (m.prompt.template for m in template.messages)
        assert system == SHARED_SYSTEM, name
        assert human.startswith(PUBLIC_RECORD), name
        assert len(TRANSCRIPT_RULE.findall(human)) == 1, name  # the only boundary in the message


def test_the_rendered_prefix_is_the_same_for_every_seat_and_call_type(shared):
    # One game (the fixture's board for a healer speaker, where the trailseer and the sigilist are
    # dead), every living seat's payload, every call type's template: one prefix.
    from Agents.nodes.day.flow import build_speaker_send
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from Agents.schemas import FiringReason
    from tests.fixtures.day_discuss_prompt_golden import board

    state = board("healer")
    living = [r for r in ROLES if _seat(r) not in {d.player for d in state["dead_roster"]}]
    prefixes = set()
    for role in living:
        payload = build_speaker_send(state, _seat(role), role, FiringReason(tier="proactive", owes=[])).arg
        inputs = build_agent_prompt_input(payload)
        for template in _templates().values():
            prefixes.add(_prefix(_render(template, inputs)))
    assert len(living) >= 6 and len(prefixes) == 1
    assert "player_4: player_2, why abstain?" in prefixes.pop()  # the real transcript, not a placeholder


def test_a_held_back_draft_reaches_no_prompt_in_the_shared_layout(monkeypatch):
    from Agents.prompts.day_discuss import day_discuss_template
    from Agents.prompts.prompt_inputs import build_agent_prompt_input

    role = ROLES[0]
    payload = speaker_payload(role)
    payload["day_channel"] = [*payload["day_channel"], DayChannel(
        day=payload["current_day"], seq=99, player=_seat(role), message="", passed=True, gated=True,
        gated_candidate="my secret draft")]
    today = _render(day_discuss_template(role), build_agent_prompt_input(payload))
    assert "my secret draft" in today[1][1]  # today's layout shows it to its author
    monkeypatch.setenv(LAYOUT_ENV, "shared_prefix")
    shared_layout = _render(day_discuss_template(role), build_agent_prompt_input(payload))
    assert "my secret draft" not in shared_layout[1][1]


def test_without_the_flag_the_role_card_stays_in_the_system_message(monkeypatch):
    monkeypatch.delenv(LAYOUT_ENV, raising=False)
    from Agents.prompts.day_discuss import day_discuss_template

    system = day_discuss_template(ROLES[0]).messages[0].prompt.template
    assert system != SHARED_SYSTEM and "Core Strategy" in system


def test_a_round_turns_note_is_kept_only_for_a_line_the_filter_let_through(shared, monkeypatch):
    from Agents.nodes.day import flow
    from Agents.schemas import RoundCandidate

    said = DayChannel(day=2, seq=0, player="player_1", message="I am the sentinel.")
    held = DayChannel(day=2, seq=0, player="player_2", message="Same point again.")
    candidates = [RoundCandidate(day=2, day_round="opening", entry=said, strategy="note 1"),
                  RoundCandidate(day=2, day_round="opening", entry=held, strategy="note 2")]

    def hold_player_2(ordered):
        return [e.model_copy(update={"passed": True, "gated": True, "gated_candidate": e.message, "message": ""})
                if e.player == "player_2" else e for e in ordered]

    monkeypatch.setattr(flow, "filter_openings", hold_player_2)
    monkeypatch.setattr(flow, "_round_order", lambda state: ["player_1", "player_2"])
    state = {"current_day": 2, "day_round": "opening", "round_candidates": candidates,
             "day_channel": [], "human_players": []}
    out = flow.collect_round(state, {"configurable": {}})
    assert out["agent_strategies"] == {"player_1": "note 1"}


def _openai_payload(model: str) -> dict:
    from Agents.llm_factory.providers.openai_compat import _ToolCallStructuredChatOpenAI

    llm = _ToolCallStructuredChatOpenAI(model=model, api_key="k")
    text = "== Today's discussion ==\nplayer_1: hi\nplayer_2: hello\n=========================\nYour turn."
    return llm._get_request_payload([SystemMessage("the rules"), HumanMessage(text)])


def test_openai_gets_explicit_breakpoints_on_the_rules_and_the_public_record(shared):
    payload = _openai_payload("gpt-6-luna")
    assert payload["extra_body"]["prompt_cache_options"] == {"mode": "explicit"}
    system, user = payload["messages"]
    assert system["content"][0]["prompt_cache_breakpoint"] == {"mode": "explicit"}
    marked = [p["text"] for p in user["content"] if "prompt_cache_breakpoint" in p]
    assert marked[-1] == "player_2: hello\n"
    assert "prompt_cache_breakpoint" not in user["content"][-1]  # the turn's own part is never written
    assert user["content"][-1]["text"].startswith("=====")


def test_openai_breakpoints_only_for_models_that_take_them_and_only_in_the_shared_layout(monkeypatch):
    monkeypatch.setenv(LAYOUT_ENV, "shared_prefix")
    assert "extra_body" not in _openai_payload("deepseek-v4-pro")
    monkeypatch.delenv(LAYOUT_ENV)
    payload = _openai_payload("gpt-6-luna")
    assert "extra_body" not in payload and isinstance(payload["messages"][1]["content"], str)
