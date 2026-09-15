"""The frontend's copy of the API contract must match the server that serves it.

The TypeScript types under frontend/src/types/contracts are generated from the server's
OpenAPI document. The document is kept on disk next to them so that a change to a route
or a DTO fails here, in the server suite, instead of surfacing as a 422 in the browser
weeks later. To accept a change: ``cd frontend && npm run generate-api-types``, which
rewrites both the saved document and the generated types, then commit both.
"""

import json
import pathlib

from server.openapi import document

SNAPSHOT = (pathlib.Path(__file__).resolve().parents[2]
            / "frontend/src/types/contracts/openapi.json")


def test_saved_openapi_matches_the_server():
    saved = json.loads(SNAPSHOT.read_text())
    live = document()
    assert live == saved, (
        "the server's API changed but frontend/src/types/contracts/openapi.json did not; "
        "run `npm run generate-api-types` in frontend/ and commit the result")
