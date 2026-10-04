"""The model admission run's offline parts: which calling mode it recommends, and the three real
prompts its caching probe sends (evaluation/src/model_admission/probes.py)."""
import json

from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.model_admission import probes


def _result(mode, passed, reasoning):
    total = 27
    return {"mode": mode, "passed": f"{passed}/{total}", "all_passed": passed == total,
            "mean_per_call": {"reasoning": reasoning}}


def test_with_thinking_asked_a_mode_that_reasons_beats_one_that_silently_does_not():
    results = [_result("forced_tool", 27, 0), _result("auto_tool", 26, 40), _result("json_mode", 27, 350)]
    mode, why = probes.recommend_mode(results, "medium")
    assert mode == "json_mode" and "forced_tool also passed but did not reason" in why
    assert probes.recommend_mode(results, "minimal")[0] == "forced_tool"


def test_no_mode_passing_every_call_recommends_nothing():
    mode, why = probes.recommend_mode([_result("forced_tool", 20, 0), _result("json_mode", 25, 300)], None)
    assert mode is None and "json_mode at 25/27" in why


def test_real_prompts_fall_back_to_the_mode_that_passed_most():
    assert probes.best_mode([_result("forced_tool", 0, 0), _result("auto_tool", 17, 1200),
                             _result("json_mode", 26, 1700)]) == "json_mode"


def test_the_caching_probe_renders_a_next_turn_that_extends_the_first_and_another_seat():
    rows = [json.loads(line) for line in
            (REPO_ROOT / "evaluation/frozen_eval_sets/hallucination_bench_v2.jsonl").read_text().splitlines()]
    case = next(r for r in rows if r["phase"] == "day_discussion" and r["day"] >= 2)
    variants = probes.turn_variants(case)
    texts = {name: probes._text(*probes._render(c)[::2]) for name, c in variants.items()}
    assert variants["other_seat"]["speaker"] != case["speaker"]
    assert len(texts["next_turn"]) > len(texts["first"])
    # The same seat's next prompt shares most of the first; another seat shares less of it.
    same = probes._shared_prefix(texts["first"], texts["next_turn"])
    other = probes._shared_prefix(texts["first"], texts["other_seat"])
    assert same > other > 0
    assert "I want to hear from everyone" in texts["next_turn"]
