from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from Agents.memory_batch_deduplication import _put_memory_with_retries
from Agents.memory_persistence import (
    _batch_with_retries,
    seed_memory_from_json_files,
)


class TransientEmbeddingError(Exception):
    status_code = 502


class PermanentEmbeddingError(Exception):
    status_code = 400


class FailingStore:
    def __init__(self, failures: list[Exception] | None = None) -> None:
        self.failures = failures or []
        self.batch_calls: list[list[Any]] = []

    def batch(self, ops: list[Any]) -> None:
        self.batch_calls.append(ops)
        if self.failures:
            raise self.failures.pop(0)


class FailingPutStore:
    def __init__(self, failures: list[Exception] | None = None) -> None:
        self.failures = failures or []
        self.put_calls: list[tuple[tuple[str, str], str, dict[str, Any]]] = []

    def put(self, namespace: tuple[str, str], key: str, value: dict[str, Any]) -> None:
        self.put_calls.append((namespace, key, value))
        if self.failures:
            raise self.failures.pop(0)


class MemoryPersistenceTests(unittest.TestCase):
    def test_batch_with_retries_retries_transient_errors(self) -> None:
        store = FailingStore([TransientEmbeddingError("502 Bad Gateway")])
        sleeps: list[float] = []

        _batch_with_retries(
            store,
            ["op"],
            retry_attempts=3,
            retry_initial_delay=0.25,
            retry_max_delay=1.0,
            sleep=sleeps.append,
        )

        self.assertEqual(2, len(store.batch_calls))
        self.assertEqual([0.25], sleeps)

    def test_batch_with_retries_does_not_retry_permanent_errors(self) -> None:
        store = FailingStore([PermanentEmbeddingError("400 Bad Request")])
        sleeps: list[float] = []

        with self.assertRaises(PermanentEmbeddingError):
            _batch_with_retries(
                store,
                ["op"],
                retry_attempts=3,
                retry_initial_delay=0.25,
                retry_max_delay=1.0,
                sleep=sleeps.append,
            )

        self.assertEqual(1, len(store.batch_calls))
        self.assertEqual([], sleeps)

    def test_seed_memory_from_json_files_uses_retrying_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            observations_path = root / "observations.json"
            strategy_points_path = root / "strategy_points.json"
            observations_path.write_text(
                json.dumps(
                    {
                        "namespaces": {
                            "observations/villager": [
                                {"key": "a", "value": {"content": "alpha"}},
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            strategy_points_path.write_text(
                json.dumps(
                    {
                        "namespaces": {
                            "strategy_points/villager": [
                                {
                                    "key": "b",
                                    "value": {"content": "beta", "action": "act"},
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            store = FailingStore([TransientEmbeddingError("server error 502")])

            counts = seed_memory_from_json_files(
                observations_path=observations_path,
                strategy_points_path=strategy_points_path,
                target_store=store,  # type: ignore[arg-type]
                retry_attempts=2,
                retry_initial_delay=0,
            )

        self.assertEqual(
            {"observations": 1, "strategies": 0, "strategy_points": 1},
            counts,
        )
        self.assertEqual(3, len(store.batch_calls))

    def test_put_memory_with_retries_retries_transient_embedding_errors(self) -> None:
        store = FailingPutStore([TransientEmbeddingError("502 Bad Gateway")])

        _put_memory_with_retries(
            store,  # type: ignore[arg-type]
            ("observations", "villager"),
            "a",
            {"content": "alpha"},
        )

        self.assertEqual(2, len(store.put_calls))


if __name__ == "__main__":
    unittest.main()
