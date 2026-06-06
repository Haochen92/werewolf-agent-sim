# Phase A #3 — Consolidated tracing: night-action eval coverage

## Goal

Close the **night-action eval gap**. Day actions (discuss/vote) routed through
`_run_memory_informed_action`, which emits an `agent_action_eval_*` Langfuse span carrying a full
`EvalCase` (situations, retrieved observations + strategy points, the decision, adoptions) **and**
does memory retrieval. Night actions (healer / investigator / serial-killer / vigilante) called
`_run_agent` directly — no eval span, no retrieval, no `EvalCase` — so the eval pool was day-only and
night memory had no *read* side (the *write* side already existed: postgame extraction writes
`night_action` namespace entries).

Decision (locked with design discussion, 2026-06-06): **option B — make night a first-class
memory-informed action.** One change delivers both the eval span and flag-gated retrieval, so #4
(night memory) shrinks to content/quality, not plumbing. Wolf night discussion is **deferred** (it is
a combined discuss+vote into `wolf_channel`, a different shape from a single-target pick).

## As-built

Single-target night roles (healer/investigator/serial_killer/vigilante) now route through a new
`_run_memory_informed_night_action` (agents.py), the night sibling of `_run_memory_informed_action`.
Built for maximum reuse:

- **`_enrich_payload_with_memory` reused verbatim** — already role-agnostic; keys retrieval on
  `(role, "night_action")`, builds situations via the per-role `*_SITUATION_SUMMARY` prompts.
- **Extracted shared helpers** out of the day path: `_process_strategy_adoption` (retrieved/used
  counts + `StrategyAdoption` records) and `_build_eval_private_context`. Day path refactored to use
  them (behaviour-preserving).
- **`EvalCase` gained `agent_night_action: NightAction|None`** (`{role, target}`) — a night action is
  a target selection, not a message/vote. `EvalPrivateContext` gained `vigilante_results`.
- **`NIGHT_ACTION_MEMORY_CONTEXT`** prompt block added to the 4 night prompts so retrieved memory
  actually reaches the agent (placeholders were already supplied by `build_agent_prompt_input`). Side
  fix: night roles now also see their own `previous_strategy` note for the first time.
- **Plumbing**: `current_day`/`current_round=0`/`strategy_adoptions` threaded through the 4 night
  graph states + parent invokers; child `strategy_adoptions` propagated to the orchestrator
  accumulator. Act fns upgraded to `(payload, config, runtime)` (LangGraph injects them).
- Retrieval is gated by the **same `memory_config`** as day, so the SK night memory on/off A/B works
  the moment this lands.

### Dead-code removed alongside (sequential model made them inert)

- `final_discussion_round_notice` — gated on `current_round >= max_discussion_rounds`, which can never
  fire now that the scheduler hardcodes day `current_round=0`; no prompt referenced the key.
- `max_discussion_rounds_per_day` — its only consumer was that notice; the sequential scheduler never
  read it. Removed the `GameConfig` field, prompt passthrough, agents.py wiring, and the
  `--max-discussion-rounds-per-day` CLI flag / `game_config_from_args`. The general `game_config`
  override seam in run_batch is kept (now `None`) for future overrides.

(The broader `round` concept is still load-bearing in **wolf night** (2-round loop + `WolfChannel.round`)
and in the eval layer (`EvalCase.round`, span names, frozen JSONL). Its removal is **deferred to the
v5 / Phase B label-once cut**, where frozen eval data is regenerated anyway — and the wolf-night round
logic comes out with the deferred wolf-night-eval adapter.)

## Verification (3 memory-off/on smoke games, py3.11 venv)

All clean, 0 errors / 0 quota failures. Reproduce:

```
PY=~/.cache/pypoetry/virtualenvs/werewolf-game-v7lKgM40-py3.11/bin/python
# 1) memory-off — no crash, night eval spans emit
$PY scripts/run_batch.py --configs all_disabled --runs-per-config 1 \
    --no-memory-seed --no-memory-dump --session-prefix nighteval_memoff
# 2) memory-on, healer+investigator seeded from a populated store
$PY scripts/run_batch.py --configs specials_only \
    --seed-store-dir Agents/memory_stores/v4_deduped --no-memory-dump \
    --session-prefix nighteval_memon
# 3) memory-on, ALL roles — the night-immune SK guarantees day>=2 night actions
$PY scripts/run_batch.py --configs all_enabled \
    --seed-store-dir Agents/memory_stores/v4_deduped --no-memory-dump \
    --session-prefix nighteval_memon_all
```

| Run | Config | Winner/Day | Night eval spans | Key finding |
|---|---|---|---|---|
| memoff | all_disabled | serial_killer / 4 | 14 (vig×4, sk×4, inv×3, heal×3) | All nested under root; `agent_night_action` targets correct; `mem=False` / `memory_disabled_for_role`. No orphan traces. |
| memon | specials_only | villagers / 5 | 8 | No crash; healer+investigator died nights 1–2 (SK), so never reached a day≥2 night → memory branch not exercised here. |
| memon_all | all_enabled | serial_killer / 5 | 12 (9 with `memory_enabled=True`) | **Decisive.** See below. |

**`memon_all` (the decisive run):**
- **Healer (player_7), nights 2–4**: `memory_enabled=True`, retrieved **3 obs + 3 strategy points**
  from v4's `healer/night_action`, and **adopted** them (`adopted_strategy_keys` = [1], [3], [2]).
  Full read loop confirmed: retrieve → render → consume → adoption recorded.
- **SK (player_4) & vigilante (player_6), nights 2–4**: `memory_enabled=True`, situation generated,
  retrieval ran, returned 0 — correct: these new roles have empty `night_action` namespaces in v4.
  Confirms the branch fires; content arrives once #4 populates those namespaces.
- **Night 1**: skipped (`mem=False`, `day_1`) for all, matching the day-1 retrieval rule.

## Status & deferred

- ✅ Night-action eval coverage + night-memory **read side** complete and verified. The SK night
  memory on/off A/B (Phase C headline) is now mechanically wired.
- ⏭ **Deferred to #4 (night memory):** content/quality — SK/vigilante `night_action` namespaces are
  empty (need extraction to populate them; verify extraction enumerates the new roles), night-aware
  situation prompts, and whether night retrieval measurably improves decisions.
- ⏭ **Deferred:** wolf-night-discussion eval adapter; `round` schema/wolf-night-round removal at the
  v5 cut.

Artifacts: `evidence/tracing/smoke_*.log`, `batch_results/nighteval_*.jsonl`.
