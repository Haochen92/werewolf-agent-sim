"""The captured-game stream fixture: every v2 chunk of a REAL game, replayable offline.

``FIXTURE`` is the 2026-10 ten-seat game (notebooks/fixtures/chunk_catalogue_phase3.jsonl):
the lineup dealt from the twelve-role pool, the day with rounds (the opening, the sweep, the
vote), the pack's chat, carrier and skills, the solo night nodes and the committed night
report. AI-only, memory off; the town won on night 3. The index-pinned spot checks, the
goldens and the session suites' FakeGraph are built on it. ``FIXTURE_PHASE2`` names the same
file: the ten-seat capture has the round nodes' chunks and ``round_players`` too, so one
capture serves both.

The two nine-seat captures, chunk_catalogue.jsonl (2026-08, the sequential day) and
chunk_catalogue_phase2.jsonl (2026-10, the day with rounds), stay on disk as records of the
nine-seat game, but no longer replay on this translator: their nodes (healer_act, the wolf
vote) and keys (healer_player, ...) are unregistered.

`load_fixture_chunks()` is the plain loader for module-scope use (e.g. a module-scoped replay
fixture); the `fixture_chunks` fixture re-reads per test, so no test can mutate another's
chunks.
"""

from __future__ import annotations

import json
import pathlib

import pytest

_FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[2] / "notebooks/fixtures"
FIXTURE = _FIXTURES_DIR / "chunk_catalogue_phase3.jsonl"
FIXTURE_PHASE2 = FIXTURE


def load_fixture_chunks(path: pathlib.Path = FIXTURE) -> list[dict]:
    with path.open() as f:
        header = json.loads(f.readline())["_header"]
        assert header["stream"]["version"] == "v2"
        return [json.loads(line) for line in f]


@pytest.fixture
def fixture_chunks() -> list[dict]:
    return load_fixture_chunks()
