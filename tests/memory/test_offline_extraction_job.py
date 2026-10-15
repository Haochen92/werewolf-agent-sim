"""The offline extraction job's plumbing (decisions §11), with the model calls faked: each game's first
call goes direct (it writes the game's prefix to the 1-hour cache), the rest go in one batch with
their game's prefix marked and their cell schema as text after it (an enforced schema is part of
Claude's cache key), a call the batch loses is retried direct with the schema enforced, and the
de-halo pass rewrites the verdicts it judges."""

from Agents.llm_factory.providers import anthropic as claude_structured
from Agents.memory.extraction import offline
from Agents.memory.persistence.config import DehaloConfig
from Agents.schemas.dehalo import Judgment, Judgments
from Agents.schemas.evaluation import ExtractionCase


def _case(game_id):
    return ExtractionCase(game_id=game_id, roles={"player_1": "healer", "player_2": "chanteuse"},
                          lineup=["healer", "chanteuse"], game_outcome="villagers",
                          formatted_discussions=f"record of {game_id}", formatted_strategy_notes="notes")


def _answer(schema, n=1):
    obs_schema = schema.model_fields["observations"].annotation.__args__[0]
    fields = {}
    for name, f in obs_schema.model_fields.items():
        ann = f.annotation
        fields[name] = (2 if ann is int else False if ann is bool else
                        getattr(ann, "__args__", ("x",))[0] if str(ann).startswith("typing.Literal") else "x")
    return schema(observations=[obs_schema.model_validate(fields) for _ in range(n)])


def test_first_call_direct_rest_batched_lost_calls_retried(monkeypatch):
    direct, batched, rounds = [], {}, []

    def fake_parse(prompt, schema, model, thinking_level=None, cache_prefix=None, cache_ttl=None,
                   schema_in_prompt=False):
        direct.append((prompt, cache_prefix, cache_ttl, schema_in_prompt))
        return (Judgments(judgments=[]) if schema is Judgments else _answer(schema)), {}

    def fake_batch(requests, model, thinking_level=None, cache_prefix=None, poll_seconds=30, cache_ttl=None,
                   schema_in_prompt=False):
        assert schema_in_prompt  # one cached prefix for every cell: the schema goes after it
        rounds.append(sorted(requests))
        batched.update(requests)
        keys = sorted(requests)
        return {k: (None if k == keys[0] else _answer(requests[k][1])) for k in keys}  # one lost each round

    monkeypatch.setattr(claude_structured, "parse_with_claude", fake_parse)
    monkeypatch.setattr(claude_structured, "batch_parse", fake_batch)
    cases = [_case("game-a"), _case("game-b")]
    out = offline.extract_cases(cases, "claude-haiku-5-5", "off")

    per_game = len(offline.cell_calls(cases[0])[1])  # 2 roles x 3 phases
    assert per_game == 6
    assert len(batched) == 2 * per_game - 2  # all but each game's lead call
    assert len(rounds) == 2 and rounds[1] == [rounds[0][0]]  # the lost call batched again first
    for prompt, _schema, prefix in batched.values():
        assert prompt.startswith(prefix) and "record of game-" in prefix
    assert len(direct) == 3 and all(ttl == "1h" for _p, _pre, ttl, _sip in direct)
    # the two leads write the shared prefix with the schema as text; the call lost twice goes direct,
    # enforced, with no cache marker (under its own schema it would write a prefix nobody reads)
    assert sorted(sip for *_x, sip in direct) == [False, True, True]
    assert [pre for _p, pre, _t, sip in direct if not sip] == [None]
    assert all(len(out[g]["observations"]) == per_game and not out[g]["missing"] for g in ("game-a", "game-b"))
    phases = {o.action_phase for o in out["game-a"]["observations"]}
    assert phases == {"day_discussion", "day_vote", "night_action"}


def test_the_dehalo_batch_rewrites_the_judged_verdicts(monkeypatch):
    case = _case("game-c")
    obs_schema = offline.cell_calls(case)[1][0][3]
    [obs] = _answer(obs_schema).observations
    obs.net_verdict = "positive"
    extracted = {"game-c": {"observations": [obs], "missing": [], "model_used": "m"}}
    verdict = Judgment(index=1, revised_verdict="unclear", halo=True, reason="outcome, not the move")
    monkeypatch.setattr(claude_structured, "batch_parse",
                        lambda requests, *a, **k: {key: Judgments(judgments=[verdict]) for key in requests})
    records = offline.dehalo_cases([case], extracted, DehaloConfig(enabled=True, model="claude-haiku-5-5"))
    assert obs.net_verdict == "unclear" and records["game-c"]["revised"] == 1
