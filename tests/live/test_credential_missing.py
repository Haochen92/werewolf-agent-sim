"""The live gate's skip check, offline: a model must be skipped for its own provider's missing key,
not judged by another's (Claude seats were once checked under the Google credential)."""

import pytest

from Agents.llm_factory.providers import openai_compat
from tests.live.test_model_structured_output import _KEY_ENV, _credential_missing

_GOOGLE_ENVS = ("GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS")


@pytest.fixture
def bare_env(monkeypatch, tmp_path):
    """No provider key set and no gcloud ADC file, whatever the developer's shell or .env holds."""
    for env in (*_KEY_ENV.values(), *_GOOGLE_ENVS):
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return monkeypatch


def test_every_prefix_the_factory_routes_has_a_key():
    assert set(openai_compat.PREFIXES) | {"anthropic/", "mistral/"} <= set(_KEY_ENV)


@pytest.mark.parametrize("prefix,key_env", sorted(_KEY_ENV.items()))
def test_a_prefixed_model_is_judged_by_its_own_key(bare_env, prefix, key_env):
    model = prefix + "some-model"
    assert _credential_missing(model) == f"{key_env} not set"
    # Another provider's key, Google's included, does not stand in for it.
    for other in (*(e for e in _KEY_ENV.values() if e != key_env), *_GOOGLE_ENVS):
        bare_env.setenv(other, "x")
    assert _credential_missing(model) == f"{key_env} not set"
    bare_env.setenv(key_env, "x")
    assert _credential_missing(model) is None


def test_a_bare_gemini_id_is_judged_by_the_google_credential(bare_env):
    bare_env.setenv("CLAUDE_API_KEY", "x")
    assert "no Google credential" in _credential_missing("gemini-2.5-flash")
    bare_env.setenv("GOOGLE_API_KEY", "x")
    assert _credential_missing("gemini-2.5-flash") is None
