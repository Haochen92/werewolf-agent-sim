# Werewolf Agent Sim

## Environment

- Always use `poetry run` to execute Python commands (e.g. `poetry run python -c "..."`, `poetry run pytest`).
- Do not use bare `python` or `pip` — the project uses Poetry for dependency management.

## Commit Patterns

- When committing, break changes into incremental commits in logical dependency order — commit the foundation first, then what builds on it.
- Even if many files changed together, group them into commits by what was done, not by when it was done.
- Each commit should represent one coherent step that makes sense on its own.
