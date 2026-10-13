"""Guard the cluster_synth SP path: gate_key partition (verdict-agnostic → mixed-verdict clusters),
cluster formatting, and the synthesis output container shape."""

from types import SimpleNamespace

from Agents.memory import strategy_synthesis as ss
from Agents.schemas.memory import cell_strategy_schema_for


def _obs(situation, verdict, approach="a", outcome="o", **gate):
    base = {"situation": situation, "net_verdict": verdict, "approach": approach, "outcome": outcome}
    base.update(gate)
    return SimpleNamespace(value=base)


def test_sp_container_wraps_the_cell_schema():
    sp_schema = cell_strategy_schema_for("villager", "day_vote")
    container = ss._sp_container(sp_schema)
    assert set(container.model_fields) == {"strategy_points"}
    assert container.model_fields["strategy_points"].annotation == list[sp_schema]


def test_format_cluster_tags_each_obs_with_verdict():
    items = {"k1": _obs("S1", "positive"), "k2": _obs("S2", "negative")}
    out = ss._format_cluster(["k1", "k2"], items)
    assert "(outcome: positive)" in out and "(outcome: negative)" in out
    assert "situation: S1" in out and "approach:" in out


def test_format_cluster_shows_the_immediate_and_end_of_game_effects_apart():
    obs = _obs("S1", "mixed")
    obs.value["dimensions"] = {"immediate_response": "drew the night kill",
                               "impact_on_final_game_outcome": "the town lynched a wolf next day"}
    out = ss._format_cluster(["k1"], {"k1": obs})
    assert "immediate effect: drew the night kill" in out
    assert "end-of-game effect: the town lynched a wolf next day" in out
    assert "\noutcome:" not in out


def test_the_synthesis_prompt_carries_the_ten_seat_rules_and_no_opposite_rule():
    from Agents.prompts.compose import pool_rules_block
    from Agents.prompts.extraction import CELL_SP_SYNTHESIS_PROMPT

    rules = pool_rules_block()
    assert rules.startswith("Team composition (10 players, four sides):")
    assert "Necromancer" in rules and "Fortune Teller" in rules and "Villager" not in rules
    prompt = CELL_SP_SYNTHESIS_PROMPT.format(game_rules=rules, role="sentinel", phase="night_action",
                                             observations="[1]", dimension_menu="- x")
    assert "Emit 0-3 strategy points" in prompt
    assert "corrective/opposite" not in prompt


def test_synth_partition_is_gate_key_not_verdict(monkeypatch):
    # Two obs share the situation regime (gate_key) but DIFFER on net_verdict. The SP-synth partition
    # uses gate_key only, so they must land in ONE partition (mixed verdicts together) — unlike the
    # obs-dedup partition, which would split them by verdict.
    gate = {"is_swing": False, "players_alive": 6, "consensus_direction": "opposes_my_read"}
    items = {
        "pos": _obs("S", "positive", **gate),
        "neg": _obs("S", "negative", **gate),
    }
    monkeypatch.setattr(ss, "_fetch_namespace_items", lambda store, ns: items)
    seen_partitions = []

    def fake_build(store, ns, part, config, seed_keys=None):
        seen_partitions.append(set(part))
        return [list(part)] if len(part) > 1 else []

    monkeypatch.setattr(ss, "_build_clusters_for_items", fake_build)
    _items, clusters = ss.cluster_observations_for_synth(None, ("observations", "villager", "day_vote"), None)
    # one partition holding BOTH the positive and negative obs
    assert {"pos", "neg"} in seen_partitions
    assert clusters == [["pos", "neg"]]


def test_synthesis_never_clusters_lessons_of_a_different_stage(monkeypatch):
    # A point written from mixed-stage lessons carries a stage label true for only some of them, and
    # the live stage filter trusts that label: partner lost and uses left (some vs none) split too.
    from types import SimpleNamespace

    import Agents.memory.strategy_synthesis as synth

    def obs(**dims):
        return SimpleNamespace(value={"is_swing": False, "players_alive": 9, "consensus_direction": "none",
                                      "dimensions": dims})

    items = {"a": obs(uses_left=2), "b": obs(uses_left=1), "c": obs(uses_left=0),
             "d": obs(ally_revealed=True, uses_left=1)}
    monkeypatch.setattr(synth, "_build_clusters_for_items",
                        lambda store, ns, part, config, seed_keys=None: [sorted(part)])
    _, clusters = synth.cluster_observations_for_synth(None, ("observations", "illusionist", "night_action"),
                                                       None, items=items)
    assert sorted(clusters) == [["a", "b"], ["c"], ["d"]]
