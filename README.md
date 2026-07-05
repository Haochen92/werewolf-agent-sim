# Werewolf Agent Sim

A research platform where LLM agents play Werewolf — a hidden-information,
social-deduction party game where a secret minority (the wolves) tries to
survive elimination while the majority (the town) tries to find them by argument
and voting. The agents run on [LangGraph](https://langchain-ai.github.io/langgraph/),
and across many games they build an **episodic memory store**: a growing set of
records of past situations that are retrieved to inform decisions in later games.

The research question is twofold. First, does cross-game memory measurably
improve how the agents play? Second, can a *self-consolidating* memory loop — one
that reviews its own past games and rewrites its memory — make that improvement
**compound** over time? This is a portfolio project, so both artifacts matter
equally: the game engine, and the evaluation methodology used to judge it.

## What we found so far

- **Static memory helps.** Giving town-faction agents a fixed, pre-built memory
  store measurably improves their decisions versus playing with no memory.
  See [`evidence/memory_system/effectiveness/`](evidence/memory_system/effectiveness/)
  and the apparatus report [`evidence/evaluation/report.md`](evidence/evaluation/report.md).
- **Whether the loop compounds is still open.** The "v7" self-consolidating loop
  is built and has been run, but the question of whether it produces *compounding*
  gains is not yet settled — the first paid runs were invalidated by the harness's
  own checks. See [`evidence/v7_final/report.md`](evidence/v7_final/report.md) and
  the measurement plan in [`evidence/execution_plan/`](evidence/execution_plan/).

(All quantitative claims and their caveats live in the evidence reports, not here.)

## Repository map

| Path | What it is |
|---|---|
| [`Agents/`](Agents/) | The production game engine. `graphs/` holds the LangGraph topology (start at [`graphs/parent.py`](Agents/graphs/parent.py) — the day/night cycle); `nodes/` holds the node bodies; `turn/` is the per-turn decision engine; `memory/` is the memory pipeline (extraction → dedup → store → retrieval). |
| [`evaluation/`](evaluation/) | The measurement system: replay harnesses, LLM judges, deterministic audits, and the v7 loop driver. [`evaluation/README.md`](evaluation/README.md) is its full map. |
| [`evidence/`](evidence/) | The experiment record — one folder per experiment, each with logs, data artifacts, and a `report.md`. [`evidence/README.md`](evidence/README.md) is the catalog. |
| [`writeup/`](writeup/) | The distilled portfolio story (in progress; chapters landing during the evidence read pass). |
| [`docs/`](docs/) | How-it-works technical references (in progress). |
| [`scripts/`](scripts/) | Batch-generation entry points: [`run_batch.py`](scripts/run_batch.py) and [`analyze_batch.py`](scripts/analyze_batch.py). |
| [`tests/`](tests/) | Unit and invariant tests, including prompt-isolation leak checks (`tests/leak_test.py`) that assert one agent's private context never reaches another. |

Data planes and supporting stacks: [`memory_stores/`](memory_stores/) (versioned
memory snapshots), [`batch_results/`](batch_results/) (game-run records),
[`models/`](models/) and [`training/`](training/) (fine-tuned reranker assets),
[`langfuse/`](langfuse/) (self-hosted tracing stack), [`frontend/`](frontend/)
(game viewer, developed in a separate worktree), and [`archive/`](archive/)
(retired files — see its README).

## How an experiment flows

The project's core discipline is that every claim traces back to a reproducible
run. Take the memory-effectiveness A/B test as the worked example. A config and
runner ([`scripts/run_batch.py`](scripts/run_batch.py)) play many games in two
arms — memory-on versus memory-off — over the same board draws. Each game is
written to a records file in [`batch_results/`](batch_results/) as JSONL, stamped
with a **runtime fingerprint** (the git commit SHA, a hash of the prompts, and
the model IDs) so a result can always be tied to the exact code that produced it.
The [`evaluation/`](evaluation/) code then scores those records, and the
conclusion is frozen into a report:
[`evidence/memory_system/effectiveness/report.md`](evidence/memory_system/effectiveness/report.md).

```text
config + runner        game records              analysis            frozen record
scripts/run_batch.py → batch_results/*.jsonl  → evaluation/ code  → evidence/.../report.md
(memory-on vs -off)    (+ runtime fingerprint)   (judges/audits)     (conclusions + pointers)
```

The dividing rule: **`evaluation/` holds the reusable measurement code;
`evidence/` holds the frozen record plus pointers back to the code that made it.**

## Where to start, by reader

- **Story first (what and why):** [`writeup/`](writeup/) — until its chapters
  land, read [`evidence/README.md`](evidence/README.md) and
  [`evidence/evaluation/report.md`](evidence/evaluation/report.md).
- **Code first (how it runs):** [`Agents/graphs/parent.py`](Agents/graphs/parent.py)
  for the game topology, then [`Agents/turn/`](Agents/turn/) for how a single
  agent decides.
- **Evidence first (is this real?):** [`evidence/evaluation/report.md`](evidence/evaluation/report.md)
  — the apparatus trust report, which documents how far to trust each measurement,
  including a log of times the eval caught and corrected its own mistakes.

## Quickstart

Requires **Python 3.11.12** and [Poetry](https://python-poetry.org/).

```bash
poetry install

# Set credentials: a Google AI API key...
export GOOGLE_API_KEY=...        # or place it in a .env file
# ...or Vertex AI credentials, if using the Vertex backend.

# Play a single game:
poetry run werewolf-game

# See the batch-generation options:
poetry run python scripts/run_batch.py --help
```
