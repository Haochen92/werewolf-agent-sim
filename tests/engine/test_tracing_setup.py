"""The Langfuse client is built by a call, never by importing Agents.tracing, and the code
version reaches it as an argument."""

from types import SimpleNamespace

import pytest

import Agents.tracing as tracing


@pytest.fixture
def built(monkeypatch):
    """Start with no client, and record what each one is built with instead of building it."""
    calls = []

    def fake_langfuse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(flush=lambda: None)

    monkeypatch.setattr(tracing, "_client", None)
    monkeypatch.setattr(tracing, "Langfuse", fake_langfuse)
    monkeypatch.setattr(tracing, "git_revision", lambda: {"git_commit": "abc123", "git_dirty": False})
    monkeypatch.delenv("LANGFUSE_RELEASE", raising=False)
    return calls


def test_the_client_is_built_once_with_the_commit_as_its_release(built):
    first = tracing.init_tracing()

    assert tracing.init_tracing() is first
    assert tracing.get_langfuse() is first
    assert built == [{"release": "abc123"}]


def test_an_explicit_release_variable_wins_over_the_commit(built, monkeypatch):
    monkeypatch.setenv("LANGFUSE_RELEASE", "v-from-deploy")

    tracing.init_tracing()

    assert built == [{"release": "v-from-deploy"}]


def test_first_use_builds_the_client_when_no_entry_point_did(built):
    assert tracing.get_langfuse() is tracing.init_tracing()
    assert len(built) == 1


def test_the_callback_handler_is_never_built_before_the_client(built, monkeypatch):
    order = []
    monkeypatch.setattr(tracing, "get_langfuse", lambda: order.append("client"))
    monkeypatch.setattr(tracing, "CallbackHandler", lambda **_: order.append("handler"))

    tracing.create_langfuse_handler()

    assert order == ["client", "handler"]
