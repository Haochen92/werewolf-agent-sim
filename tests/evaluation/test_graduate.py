from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.src.cli_runner.graduate_run import (
    graduate,
    referenced_inputs,
    referenced_models,
)


class ReferencedInputsTests(unittest.TestCase):
    def test_pulls_dataset_and_path_keys(self) -> None:
        config = {
            "dataset": "evaluation/frozen_eval_sets/x.jsonl",
            "snapshots": [
                {
                    "label": "v4",
                    "observations_path": "memory_stores/v4/observations.json",
                    "strategy_points_path": "memory_stores/v4/strategy_points.json",
                }
            ],
            "top_k": 3,
            "judge_model": "gemini-2.5-flash",
        }
        self.assertEqual(
            referenced_inputs(config),
            [
                "evaluation/frozen_eval_sets/x.jsonl",
                "memory_stores/v4/observations.json",
                "memory_stores/v4/strategy_points.json",
            ],
        )

    def test_dedupes_preserving_order(self) -> None:
        config = {"dataset": "a.jsonl", "snapshots": [{"observations_path": "a.jsonl"}]}
        self.assertEqual(referenced_inputs(config), ["a.jsonl"])

    def test_models_are_unique_sorted_aliases(self) -> None:
        config = {
            "judge_model": "gemini-2.5-pro",
            "summary": {"model": "gemini-2.5-flash"},
            "baseline": {"model": "gemini-2.5-flash"},
        }
        self.assertEqual(
            referenced_models(config), ["gemini-2.5-flash", "gemini-2.5-pro"]
        )


class GraduateTests(unittest.TestCase):
    def _setup(self, tmp: Path) -> tuple[Path, Path, Path]:
        dataset = tmp / "set.jsonl"
        dataset.write_text('{"case": 1}\n{"case": 2}\n', encoding="utf-8")
        result = tmp / "eval_results" / "retrieval_eval_001.jsonl"
        result.parent.mkdir(parents=True)
        result.write_text('{"score": 0.9}\n', encoding="utf-8")
        config = tmp / "config" / "rerank.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps({"dataset": str(dataset), "judge_model": "gemini-2.5-flash"}),
            encoding="utf-8",
        )
        return dataset, result, config

    def test_graduation_copies_and_stamps_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            dataset, result, config = self._setup(tmp)
            evidence = tmp / "evidence" / "retrieval/store_dedup"
            summary = graduate(
                result=result, config_path=config, experiment=str(evidence)
            )

            dest = evidence / "eval_results" / "retrieval_eval_001.jsonl"
            sidecar = dest.with_suffix(".manifest.json")
            self.assertTrue(dest.is_file())
            self.assertTrue((evidence / "eval_configs" / "rerank.json").is_file())
            self.assertTrue(sidecar.is_file())

            manifest = json.loads(sidecar.read_text())
            self.assertIn("git_commit", manifest)
            self.assertIsNotNone(manifest["config_sha256"])
            # dataset was content-hashed into the lineage
            self.assertEqual(len(manifest["inputs"]), 1)
            self.assertEqual(manifest["inputs"][0]["count"], 2)
            self.assertNotIn("missing_inputs", manifest)
            self.assertEqual(manifest["models"], ["gemini-2.5-flash"])

    def test_missing_input_is_recorded_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _, result, _ = self._setup(tmp)
            config = tmp / "config" / "broken.json"
            config.write_text(
                json.dumps({"dataset": str(tmp / "gone.jsonl")}), encoding="utf-8"
            )
            evidence = tmp / "evidence" / "exp"
            summary = graduate(
                result=result, config_path=config, experiment=str(evidence)
            )
            self.assertTrue(summary["missing_inputs"])
            manifest = json.loads(
                (evidence / "eval_results" / "retrieval_eval_001.manifest.json").read_text()
            )
            self.assertIn("missing_inputs", manifest)
            self.assertEqual(manifest["inputs"], [])  # nothing hashable

    def test_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _, result, config = self._setup(tmp)
            evidence = tmp / "evidence" / "exp"
            graduate(result=result, config_path=config, experiment=str(evidence))
            with self.assertRaises(FileExistsError):
                graduate(result=result, config_path=config, experiment=str(evidence))
            # --force succeeds
            summary = graduate(
                result=result, config_path=config, experiment=str(evidence), force=True
            )
            self.assertFalse(summary["dry_run"])

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _, result, config = self._setup(tmp)
            evidence = tmp / "evidence" / "exp"
            summary = graduate(
                result=result, config_path=config, experiment=str(evidence), dry_run=True
            )
            self.assertTrue(summary["dry_run"])
            self.assertFalse((evidence / "eval_results").exists())


if __name__ == "__main__":
    unittest.main()
