"""The captured-game stream fixtures: every v2 chunk of a REAL game, replayable offline.

Two captured games. ``FIXTURE`` is the 2026-08 game of the sequential day (one speaker at a
time from the first turn; no rounds), kept because the index-pinned spot checks and the
session suites' FakeGraph are built on it. ``FIXTURE_PHASE2`` is the 2026-10 game of the day
with rounds (discussion_evidence.md §7: the opening, proactive rounds, the closing), which
has the round nodes' chunks and ``round_players``. One source of truth for both paths and the
header check. `load_fixture_chunks()` is the plain loader for module-scope use (e.g. a
module-scoped replay fixture); the `fixture_chunks` fixture re-reads per test, so no test
can mutate another's chunks.
"""

from __future__ import annotations

import json
import pathlib

import pytest

_FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[2] / "notebooks/fixtures"
FIXTURE = _FIXTURES_DIR / "chunk_catalogue.jsonl"
FIXTURE_PHASE2 = _FIXTURES_DIR / "chunk_catalogue_phase2.jsonl"


def load_fixture_chunks(path: pathlib.Path = FIXTURE) -> list[dict]:
    with path.open() as f:
        header = json.loads(f.readline())["_header"]
        assert header["stream"]["version"] == "v2"
        return [json.loads(line) for line in f]


@pytest.fixture
def fixture_chunks() -> list[dict]:
    return load_fixture_chunks()
