"""Print the server's OpenAPI document, so the frontend's types can be generated with no
server running: ``poetry run python -m server.openapi``. The frontend keeps the output at
``frontend/src/types/contracts/openapi.json`` and ``tests/server/test_openapi_snapshot.py``
fails when the routes or schemas no longer match that copy."""

from __future__ import annotations

import json
import sys

from server.app import create_app


def document() -> dict:
    return create_app().openapi()


if __name__ == "__main__":
    json.dump(document(), sys.stdout, indent=2)
    sys.stdout.write("\n")
