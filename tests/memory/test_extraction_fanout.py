"""Per-role extraction: prefix/tail split + concurrent fan-out merge.

The model call is mocked (no network) — these cover the cache-shape invariant
(prefix byte-identical across roles, role only in the tail) and the fan-out's
merge/partial-failure behaviour, not LLM quality.
"""

from __future__ import annotations

import unittest

import Agents.memory.extraction.extraction_agent as ea
from Agents.memory.extraction import (
    EXTRACTION_ROLES,
    build_role_extraction_prefix,
    build_role_extraction_prompt,
    build_role_extraction_tail,
)
from Agents.memory.persistence import ExtractionConfig
from Agents.schemas import GameStrategyOutput
from Agents.schemas.memory import Observation, StrategyPoint

_INPUTS = {
    "formatted_roles": "ROLES",
    "formatted_discussions": "DISCUSSION with a {stray brace}",
    "formatted_strategy_notes": "NOTES",
    "formatted_previous_strategies": "PREV",
    "game_outcome": "villagers",
}


def _fake_invoke(_llm, prompt: str, _run_name: str) -> GameStrategyOutput:
    """Infer the target role from the tail and return one obs + one sp for it."""
    role = prompt.rsplit("ASSIGNED ROLE: ", 1)[1].split("\n", 1)[0].strip()
    obs = Observation(
        perspective=role, action_phase="day_vote", situation="s",
        information_landscape="il", game_phase="early", approach="a",
        impact_on_final_game_outcome="net o", immediate_response="imm", net_verdict="positive",
    )
    sp = StrategyPoint(
        perspective=role, action_phase="day_vote", situation="When x",
        information_landscape="il", game_phase="early", action="do y",
    )
    return GameStrategyOutput(observations=[obs], strategy_points=[sp])


class PrefixTailSplitTests(unittest.TestCase):
    def test_prefix_is_byte_identical_across_roles(self) -> None:
        # The cache requirement: the prefix never varies with the target role.
        prefixes = {build_role_extraction_prefix(_INPUTS) for _ in range(5)}
        self.assertEqual(len(prefixes), 1)

    def test_prefix_has_v5_rules_and_no_unfilled_placeholders(self) -> None:
        prefix = build_role_extraction_prefix(_INPUTS)
        self.assertIn("Serial Killer", prefix)
        self.assertNotIn("8 players", prefix)
        # the only brace left should be the stray one from the substituted value
        self.assertNotIn("{", prefix.replace("{stray brace}", ""))

    def test_tail_locks_the_role(self) -> None:
        for role in EXTRACTION_ROLES:
            tail = build_role_extraction_tail(role)
            self.assertIn(f'perspective="{role}"', tail)
            self.assertIn(f"ASSIGNED ROLE: {role}", tail)
            self.assertNotIn("{", tail)

    def test_combined_is_prefix_plus_tail(self) -> None:
        prefix = build_role_extraction_prefix(_INPUTS)
        for role in EXTRACTION_ROLES:
            self.assertEqual(
                build_role_extraction_prompt(_INPUTS, role),
                prefix + build_role_extraction_tail(role),
            )


class FanoutMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = ea._invoke_extraction_model
        ea._invoke_extraction_model = _fake_invoke

    def tearDown(self) -> None:
        ea._invoke_extraction_model = self._orig

    def test_merges_all_roles_in_order(self) -> None:
        res = ea.extract_postgame_per_role("PREFIX\n", max_workers=6)
        assert res is not None
        self.assertEqual(
            [o.perspective for o in res.output.observations], list(EXTRACTION_ROLES)
        )
        self.assertEqual(
            [s.perspective for s in res.output.strategy_points], list(EXTRACTION_ROLES)
        )
        self.assertEqual(res.model_used, "per_role")

    def test_partial_failure_drops_only_failed_role(self) -> None:
        def boom_on_wolf(llm, prompt, run_name):
            if "ASSIGNED ROLE: wolf" in prompt:
                raise RuntimeError("boom")
            return _fake_invoke(llm, prompt, run_name)

        ea._invoke_extraction_model = boom_on_wolf
        res = ea.extract_postgame_per_role(
            "PREFIX\n", max_workers=6, max_retries=0, backup_max_retries=0
        )
        assert res is not None
        perspectives = [o.perspective for o in res.output.observations]
        self.assertNotIn("wolf", perspectives)
        self.assertEqual(len(perspectives), 5)
        self.assertIn("missing: wolf", res.model_used)

    def test_total_failure_returns_none(self) -> None:
        def always_boom(llm, prompt, run_name):
            raise RuntimeError("boom")

        ea._invoke_extraction_model = always_boom
        res = ea.extract_postgame_per_role(
            "PREFIX\n", max_workers=6, max_retries=0, backup_max_retries=0
        )
        self.assertIsNone(res)


class ExtractionConfigDefaultTests(unittest.TestCase):
    def test_per_role_is_the_default(self) -> None:
        self.assertTrue(ExtractionConfig().per_role)
        self.assertEqual(ExtractionConfig().max_workers, 6)


if __name__ == "__main__":
    unittest.main()
