from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pydantic import BaseModel

from evaluation.src.core.manifest import (
    build_manifest,
    embed,
    fingerprint_input,
    sha256_of,
    write_sidecar,
)


class _Cfg(BaseModel):
    eval_set_id: str
    seed: int = 42


class FingerprintInputTests(unittest.TestCase):
    def test_jsonl_count_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.jsonl"
            p.write_text('{"a": 1}\n{"a": 2}\n\n{"a": 3}\n', encoding="utf-8")
            fp = fingerprint_input(p)
            self.assertEqual(fp["count"], 3)  # blank line ignored
            self.assertEqual(fp["sha256"], sha256_of(p))
            self.assertEqual(len(fp["sha256"]), 64)

    def test_json_list_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "labels.json"
            p.write_text(json.dumps([1, 2, 3, 4]), encoding="utf-8")
            self.assertEqual(fingerprint_input(p)["count"], 4)

    def test_json_object_count_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "obj.json"
            p.write_text(json.dumps({"k": "v"}), encoding="utf-8")
            self.assertIsNone(fingerprint_input(p)["count"])

    def test_content_change_changes_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "d.jsonl"
            p.write_text('{"a": 1}\n', encoding="utf-8")
            before = sha256_of(p)
            p.write_text('{"a": 2}\n', encoding="utf-8")  # same name, new content
            self.assertNotEqual(before, sha256_of(p))  # drift is detectable


class BuildManifestTests(unittest.TestCase):
    def test_core_fields(self) -> None:
        cfg = _Cfg(eval_set_id="dedup_v2")
        m = build_manifest(
            artifact="evaluation/frozen_eval_sets/dedup_v2.jsonl",
            config=cfg,
            created_from="v4_action_phase_v2, 30 games",
            case_count=390,
        )
        self.assertEqual(m["artifact"], "evaluation/frozen_eval_sets/dedup_v2.jsonl")
        self.assertIn("git_commit", m)
        self.assertEqual(m["config"]["eval_set_id"], "dedup_v2")
        self.assertEqual(m["case_count"], 390)
        self.assertEqual(m["created_from"], "v4_action_phase_v2, 30 games")
        self.assertEqual(m["inputs"], [])

    def test_config_sha256_is_stable_and_content_addressed(self) -> None:
        a = build_manifest(artifact="x.jsonl", config=_Cfg(eval_set_id="e", seed=1))
        b = build_manifest(artifact="x.jsonl", config=_Cfg(eval_set_id="e", seed=1))
        c = build_manifest(artifact="x.jsonl", config=_Cfg(eval_set_id="e", seed=2))
        self.assertEqual(a["config_sha256"], b["config_sha256"])  # same config -> same hash
        self.assertNotEqual(a["config_sha256"], c["config_sha256"])  # differs -> differs

    def test_inputs_are_content_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.jsonl"
            src.write_text('{"x": 1}\n', encoding="utf-8")
            m = build_manifest(artifact="out.jsonl", inputs=[src])
            self.assertEqual(len(m["inputs"]), 1)
            self.assertEqual(m["inputs"][0]["sha256"], sha256_of(src))

    def test_dict_config_accepted(self) -> None:
        m = build_manifest(artifact="x.jsonl", config={"judge_model": "flash"})
        self.assertEqual(m["config"]["judge_model"], "flash")
        self.assertIsNotNone(m["config_sha256"])


class CarrierTests(unittest.TestCase):
    def test_write_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "dedup_v2.jsonl"
            artifact.write_text('{"a": 1}\n', encoding="utf-8")
            sidecar = write_sidecar(artifact, config=_Cfg(eval_set_id="dedup_v2"), case_count=1)
            self.assertEqual(sidecar.name, "dedup_v2.manifest.json")
            loaded = json.loads(sidecar.read_text())
            self.assertEqual(loaded["config"]["eval_set_id"], "dedup_v2")

    def test_embed_attaches_under_manifest_key(self) -> None:
        record = {"score": 0.9}
        out = embed(record, artifact="evaluation/eval_results/dedup/x.json",
                    config={"judge_model": "flash"})
        self.assertIs(out, record)
        self.assertIn("_manifest", record)
        self.assertEqual(record["_manifest"]["config"]["judge_model"], "flash")
        self.assertEqual(record["score"], 0.9)


if __name__ == "__main__":
    unittest.main()
