"""Crash reports to Sentry: off without a DSN; a game's failure is tagged with its game and never
carries the player's key or a frame's locals."""
from __future__ import annotations

import sentry_sdk
from sentry_sdk.transport import Transport

from server import error_reporting
from server.config import server_settings


class _Captured(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.events = []

    def capture_envelope(self, envelope):
        self.events += [item.payload.json for item in envelope.items if item.type == "event"]


def test_reporting_is_off_without_a_dsn(monkeypatch):
    monkeypatch.setattr(server_settings, "SENTRY_DSN", "")
    assert error_reporting.init_error_reporting() is False
    # and a failure with reporting off goes nowhere, quietly
    error_reporting.report_game_failure(ValueError("x"), game_id="g", model="m", byok=False)


def test_a_game_failure_is_tagged_and_never_carries_the_key():
    transport = _Captured()
    sentry_sdk.init(dsn="https://public@o0.ingest.sentry.io/0", transport=transport,
                    include_local_variables=False)
    try:
        api_key = "sk-ant-secret-123"
        try:
            raise RuntimeError(f"provider said no to {api_key}")
        except RuntimeError as exc:
            error_reporting.report_game_failure(exc, game_id="g1", model="anthropic/claude",
                                                byok=True, secret=api_key)
        sentry_sdk.flush()
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.init()  # back to a client that sends nothing

    (event,) = transport.events
    assert event["tags"]["game_id"] == "g1" and event["tags"]["byok"] == "yes"
    assert "sk-ant-secret-123" not in str(event)
    assert "***" in event["exception"]["values"][0]["value"]
