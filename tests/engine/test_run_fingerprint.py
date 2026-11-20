"""The prompt hash covers every prompt source file, nested folders included, and the fingerprint
says which definition of the hash it carries. Tested on a temporary prompts folder, never on the
real prompt files, so a wording change elsewhere cannot break these tests."""

import pytest

import Agents.run_fingerprint as run_fingerprint


@pytest.fixture
def prompts(tmp_path, monkeypatch):
    """A small prompts folder with a top-level module and a nested role card. The hash is cached
    per process, so the cache is cleared before and after each test."""
    (tmp_path / "roles").mkdir()
    (tmp_path / "common.py").write_text("RULES = 'shared rules'\n")
    (tmp_path / "roles" / "healer.py").write_text("CARD = 'protect one player each night'\n")
    monkeypatch.setattr(run_fingerprint, "_PROMPTS_DIR", tmp_path)
    run_fingerprint.prompt_bundle_hash.cache_clear()
    yield tmp_path
    run_fingerprint.prompt_bundle_hash.cache_clear()


def fresh_hash() -> str:
    run_fingerprint.prompt_bundle_hash.cache_clear()
    return run_fingerprint.prompt_bundle_hash()


def test_the_hash_is_the_same_on_two_calls_over_the_same_tree(prompts):
    assert fresh_hash() == fresh_hash()


def test_editing_a_file_in_a_nested_folder_changes_the_hash(prompts):
    before = fresh_hash()
    (prompts / "roles" / "healer.py").write_text("CARD = 'protect two players each night'\n")

    assert fresh_hash() != before


def test_two_files_with_the_same_name_in_different_folders_are_told_apart(prompts):
    # Arrange: hash a prompt file in one folder
    (prompts / "memory").mkdir()
    (prompts / "memory" / "context.py").write_text("TEXT = 'same bytes'\n")
    in_memory = fresh_hash()

    # Act: replace it with a file of the same name and bytes in another folder
    (prompts / "memory" / "context.py").unlink()
    (prompts / "extraction").mkdir()
    (prompts / "extraction" / "context.py").write_text("TEXT = 'same bytes'\n")

    # Assert
    assert fresh_hash() != in_memory


def test_compiled_files_and_the_goldens_folder_do_not_affect_the_hash(prompts):
    # Arrange
    before = fresh_hash()

    # Act: add a compiled file and a goldens folder
    (prompts / "roles" / "__pycache__").mkdir()
    (prompts / "roles" / "__pycache__" / "healer.py").write_text("stale copy\n")
    (prompts / "goldens").mkdir()
    (prompts / "goldens" / "render.py").write_text("def main(): ...\n")
    (prompts / "goldens" / "rules.txt").write_text("rendered text\n")

    # Assert
    assert fresh_hash() == before


def test_the_fingerprint_carries_its_schema_version_first(prompts):
    # Act
    fingerprint = run_fingerprint.runtime_fingerprint()

    # Assert
    assert next(iter(fingerprint)) == "fingerprint_schema"
    assert fingerprint["fingerprint_schema"] == 3
    assert fingerprint["prompt_bundle_hash"] == fresh_hash()


@pytest.mark.parametrize(("game_model", "google_route", "backend"), [
    ("anthropic/claude-haiku-5-5", "vertex", "anthropic"),
    ("openrouter/qwen/qwen3-32b", "vertex", "openrouter"),
    ("gemini-3.1-flash-lite", "vertex", "vertex"),
    ("gemini-3.1-flash-lite", "google", "google"),
])
def test_the_backend_is_the_one_the_game_model_is_routed_to(
        prompts, monkeypatch, game_model, google_route, backend):
    # Arrange
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", game_model)
    monkeypatch.setenv("LLM_BACKEND", google_route)

    # Act
    fingerprint = run_fingerprint.runtime_fingerprint()

    # Assert
    assert fingerprint["llm_backend"] == backend
    assert ("vertex_location" in fingerprint) == (backend == "vertex")
