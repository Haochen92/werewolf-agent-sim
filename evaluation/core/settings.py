"""Project-level settings used by evaluation CLIs.

The evaluation package writes local datasets and result files relative to the
repository root, not relative to the ``evaluation`` package directory.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_project_env() -> None:
    """Load the repository ``.env`` file for local eval commands."""
    load_dotenv(REPO_ROOT / ".env")
