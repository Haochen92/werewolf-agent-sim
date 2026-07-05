"""Cold-import regression guard for the tracing<->memory circular-import class of bug.

This bug is invisible to the normal suite: pytest's own import order primes ``Agents.memory``
before anything imports ``Agents.tracing``, so the cycle never triggers under pytest. The failure
only surfaces when a top-level module (e.g. ``Agents.main`` / ``Agents.turn``) is imported COLD in a
fresh interpreter, where ``Agents.tracing`` loads first and its import chain re-enters
``Agents.memory.retrieval`` mid-initialization.

Each module below must therefore import successfully on its own in a fresh subprocess (one
subprocess per module, so nothing primes the import order for the next).
"""
import subprocess
import sys

import pytest

COLD_IMPORT_MODULES = [
    "Agents.main",
    "Agents.turn",
    "Agents.memory",
    "Agents.memory.retrieval",
    "Agents.tracing",
]


@pytest.mark.parametrize("module", COLD_IMPORT_MODULES)
def test_cold_import_succeeds(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"cold `import {module}` failed (exit {result.returncode}):\n{result.stderr}"
    )
