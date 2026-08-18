"""The captured-game stream fixture: every v2 part of a REAL game, replayable offline.

One source of truth for the fixture path and the header check (previously duplicated in
the translator and server-runtime suites). `load_fixture_parts()` is the plain loader for
module-scope use (e.g. a module-scoped replay fixture); the `fixture_parts` fixture
re-reads per test, so no test can mutate another's parts.
"""

from __future__ import annotations

import json
import pathlib

import pytest

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "notebooks/fixtures/chunk_catalogue.jsonl"


def load_fixture_parts() -> list[dict]:
    with FIXTURE.open() as f:
        header = json.loads(f.readline())["_header"]
        assert header["stream"]["version"] == "v2"
        return [json.loads(line) for line in f]


@pytest.fixture
def fixture_parts() -> list[dict]:
    return load_fixture_parts()
