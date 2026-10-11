"""Root conftest = plugin manifest only (the dota2pred pattern): fixtures live in
tests/fixtures/, one module per resource; hand-written data builders (plain functions,
imported not registered) live in tests/factories/builders.py."""

import os

# The test suite must not report to Langfuse: a developer's .env carries real keys, and every
# session test that starts a game would otherwise land as a one-observation trace in the
# research project. Set before Agents.tracing is imported, which builds the client once per
# process. An explicit LANGFUSE_TRACING_ENABLED=true in the environment still wins.
os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")
# Nor call a paid model from a game's post-game extraction: the de-halo pass is on by default in
# production (Agents/memory/persistence/config.py). Its own tests turn it on with a stubbed judge.
os.environ.setdefault("MEMORY_DEHALO_ENABLED", "false")

pytest_plugins = [
    "tests.fixtures.stream",
    "tests.fixtures.server",
    "tests.factories.events",
]
