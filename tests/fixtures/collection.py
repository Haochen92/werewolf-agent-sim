"""Markers given by where a test lives, so a test cannot be filed in a folder and miss its marker.

Every test under a folder named `integration` (`tests/server/integration/`,
`tests/memory/integration/`) gets the `integration` marker. The marker does not deselect
anything by default: `poetry run pytest` runs the integration tests too, and
`-m "not integration"` leaves them out.
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "integration" in item.path.parent.parts:
            item.add_marker(pytest.mark.integration)
