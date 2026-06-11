"""Langfuse read path: enumerate-then-name-scope (never fetch-all a heavy trace),
structural parent selection for extraction, batched-path fallback, and the dedup
LLM-run exclusion."""

import unittest
from unittest.mock import Mock, patch

import evaluation.src.data.langfuse as lf


def _trace(observations):
    return {"observations": observations}


def _row(name, output, obs_id="o1", parent=None):
    return {
        "id": obs_id,
        "name": name,
        "type": "SPAN",
        "parent_observation_id": parent,
        "metadata": {},
        "input": None,
        "output": output,
    }


def _eval_case_payload(name):
    return {
        "span_name": name,
        "player_id": "p1",
        "player_role": "wolf",
        "day": 1,
        "round": 1,
        "action_phase": "day_discussion",
        "memory_enabled": False,
    }


class FakeApi:
    """Minimal api double: trace.get enumerates; observations.get_many serves
    full rows per exact name, optionally erroring on the batched filter path."""

    def __init__(self, observations, rows_by_name, fail_on_filter=True):
        self.trace = Mock()
        self.trace.get.return_value = _trace(observations)
        self.get_many_calls = []
        self._rows_by_name = rows_by_name
        self._fail_on_filter = fail_on_filter

        def get_many(**kwargs):
            self.get_many_calls.append(kwargs)
            if kwargs.get("filter") is not None:
                if self._fail_on_filter:
                    raise RuntimeError("422: narrow your request")
                matching = [
                    row
                    for rows in self._rows_by_name.values()
                    for row in rows
                ]
                return {"data": matching if kwargs.get("page", 1) == 1 else []}
            name = kwargs["name"]
            page = kwargs.get("page", 1)
            return {"data": self._rows_by_name.get(name, []) if page == 1 else []}

        self.observations = Mock()
        self.observations.get_many.side_effect = get_many


def _patched(api):
    fake_client = Mock()
    fake_client.api = api
    return patch.object(lf, "langfuse", fake_client)


class ExtractionParentSelectionTests(unittest.TestCase):
    def test_structural_parent_beats_prefix_collision(self):
        parent = {
            "id": "p1",
            "name": "postgame_extraction_game123",
            "type": "SPAN",
            "parent_observation_id": "root",
        }
        children = [
            {
                "id": f"c{i}",
                "name": f"postgame_extraction_{role}_primary_cached",
                "type": "GENERATION",
                "parent_observation_id": "p1",
            }
            for i, role in enumerate(["wolf", "villager", "healer"])
        ]
        api = FakeApi(
            observations=[parent, *children],
            rows_by_name={
                "postgame_extraction_game123": [
                    _row(
                        "postgame_extraction_game123",
                        {"extraction_case": {"game_id": "game123"}},
                        obs_id="p1",
                    )
                ]
            },
        )
        with _patched(api):
            cases = lf.fetch_extraction_cases("t1")

        self.assertEqual([c.game_id for c in cases], ["game123"])
        # exactly one name-scoped fetch, for the parent only
        names_fetched = [c.get("name") for c in api.get_many_calls]
        self.assertEqual(names_fetched, ["postgame_extraction_game123"])


class BatchedFallbackTests(unittest.TestCase):
    def test_batched_apierror_falls_back_to_per_name(self):
        names = [f"agent_action_eval_p{i}_day_1_round_1_day_discussion" for i in range(12)]
        observations = [
            {"id": f"o{i}", "name": name, "type": "SPAN", "parent_observation_id": None}
            for i, name in enumerate(names)
        ]
        rows_by_name = {
            name: [_row(name, {"eval_case": _eval_case_payload(name)}, obs_id=f"o{i}")]
            for i, name in enumerate(names)
        }
        api = FakeApi(observations, rows_by_name, fail_on_filter=True)
        with _patched(api):
            cases = lf.fetch_eval_cases("t1")

        self.assertEqual(len(cases), 12)
        # first call tried the batched filter, then one per name
        self.assertIsNotNone(api.get_many_calls[0].get("filter"))
        self.assertEqual(len(api.get_many_calls), 1 + 12)

    def test_batched_path_used_when_supported(self):
        names = [f"agent_action_eval_p{i}_day_1_round_1_day_discussion" for i in range(12)]
        observations = [
            {"id": f"o{i}", "name": name, "type": "SPAN", "parent_observation_id": None}
            for i, name in enumerate(names)
        ]
        rows_by_name = {
            name: [_row(name, {"eval_case": _eval_case_payload(name)}, obs_id=f"o{i}")]
            for i, name in enumerate(names)
        }
        api = FakeApi(observations, rows_by_name, fail_on_filter=False)
        with _patched(api):
            cases = lf.fetch_eval_cases("t1")

        self.assertEqual(len(cases), 12)
        self.assertEqual(len(api.get_many_calls), 1)


class DedupExclusionTests(unittest.TestCase):
    def test_dedup_llm_runs_never_fetched(self):
        observations = [
            {
                "id": "d1",
                "name": "dedup_observation_wolf_vote_1",
                "type": "SPAN",
                "parent_observation_id": None,
            },
            # the LLM runs share the prefix but carry no case
            {"id": "g1", "name": "dedup_observation", "type": "GENERATION",
             "parent_observation_id": "d1"},
            {"id": "g2", "name": "dedup_strategy_point", "type": "GENERATION",
             "parent_observation_id": "d1"},
        ]
        api = FakeApi(
            observations,
            rows_by_name={
                "dedup_observation_wolf_vote_1": [
                    _row(
                        "dedup_observation_wolf_vote_1",
                        {"dedup_case": {"game_id": "g", "decision": "D"}},
                        obs_id="d1",
                    )
                ]
            },
        )
        with _patched(api):
            cases = lf.fetch_dedup_cases("t1")

        self.assertEqual(len(cases), 1)
        names_fetched = {c.get("name") for c in api.get_many_calls}
        self.assertNotIn("dedup_observation", names_fetched)
        self.assertNotIn("dedup_strategy_point", names_fetched)


if __name__ == "__main__":
    unittest.main()
