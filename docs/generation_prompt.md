# The generation prompt — how an agent's action prompt is assembled

**Orientation.** Every in-game agent action (day discuss, day vote, night action) is one LLM call built
the same way: a **role-gated payload** is constructed at the graph node, formatted into **named prompt
keys**, and slotted into a **fixed per-phase scaffold**. Three stages, three homes:

```
graph node (Send builder)      →  prompt_inputs.py                →  day_discuss / day_vote / night .py
payload: WHAT this agent may see   build_agent_prompt_input():        the scaffold: WHERE each block sits
(the enforced privacy boundary)    payload → formatted prompt keys    in the template
```

This doc is the standing reference for that pipeline: the scaffold order, the block inventory, and the
rules that govern adding a new block. Per-module detail lives in the code docstrings
([`Agents/prompts/day_discuss.py`](../Agents/prompts/day_discuss.py),
[`Agents/prompts/night.py`](../Agents/prompts/night.py),
[`Agents/prompts/prompt_inputs.py`](../Agents/prompts/prompt_inputs.py)). **How the prompt got this
shape** — the origin, the caching bet that died, the reason-before-act reordering, the flash-lite
all-required rule — is the journey log at
[`evidence/generation_prompt/experiment_log.md`](../evidence/generation_prompt/experiment_log.md).

---

## Stage 1 — payload construction (the privacy boundary)

Each phase's Send builder assembles the payload dict for one agent. **This is the only enforced
information boundary in the system**: an agent can only be prompted with what its payload contains, so
role-private data (wolf rosters, investigator results, wolf channel) is gated *here*, not in the
template. Any new private field must be gated in the Send builder and covered by a `check_*` leak test —
see [`evidence/agent_boundaries/report.md`](../evidence/agent_boundaries/report.md).

## Stage 2 — formatting (`build_agent_prompt_input`)

[`prompt_inputs.py`](../Agents/prompts/prompt_inputs.py) converts the raw payload into the string keys
the templates consume — one formatter per block (`format_dead_roster`, `format_day_channel_for_day`,
`format_day_summaries`, `format_retrieved_observations`, …, all in
[`prompt_formatters.py`](../Agents/prompts/prompt_formatters.py)). Conditional instructions are computed
here too: the abstain rule, the scheduler's `firing_brief` ("you were addressed by X — respond"), and
the obs×strategy synergy instruction (fires only when both memory types are actually present).

## Stage 3 — the scaffold

All roles share one scaffold per phase (a factory holds the shared text once; each role is a one-line
table entry). Day discussion, in template order:

**System message**
1. `GAME_PREAMBLE` — built on `GAME_RULES`, the single source of truth for roles/abilities/win
   conditions (composed into play *and* extraction prompts so rules can never drift between copies).
2. The role's `CORE_STRATEGY` ([`roles.py`](../Agents/prompts/roles.py)) — role identity + goals.
3. Discussion tone + silence rule + response format (discuss-only blocks, live in `day_discuss.py`).

**Human message**
4. Turn header — `current_day`, `firing_brief`.
5. Memory context — retrieved observations / strategy points + the verdict instructions
   ([`prompts/memory/`](../Agents/prompts/memory/)); `previous_strategy` (the agent's own running
   notes, fed back privately).
6. Shared transcript block (`_DISCUSS_TRANSCRIPT`):
   - `== Dead so far (public) ==` — the structured **dead roster** (player, revealed role, when/how
     died). Deterministic public info; replaces re-parsing the GM's death prose.
   - `== Previous days summary ==` — persisted `DaySummary` records (also model-visible downstream).
   - `== Today's discussion ==` — the day channel as plain `player_id: message` lines (`seq`/tags are
     storage, not display).
7. Role info line(s) — surviving players, plus that role's private results (investigator findings,
   vigilante shot results, wolf roster/channel).
8. Optional trailer — only the wolf uses it (speak-like-a-villager cover reminder).

Night actions use the same shape minus the discussion-only blocks (no tone/silence rule; the four
single-actor roles share `_night_template`; the 2-round wolf night discussion is hand-written).

## Block inventory

| Block | Source | Phases | Visibility |
|---|---|---|---|
| game rules / preamble | `common.GAME_RULES` | all | public, static |
| role core strategy | `roles.py` | all | role-scoped, static |
| tone + silence rule + format | `day_discuss.py` | day discuss | public, static |
| abstain instruction | `prompt_inputs` (conditional) | day vote | public |
| firing brief | scheduler `firing_reason` | day discuss | per-turn |
| dead roster | `dead_roster` state (`DeathRecord`) | **day discuss + vote** (not night yet) | public, per-day |
| previous-day summaries | persisted `DaySummary` | all | public |
| today's discussion | `day_channel` | day | public |
| wolf channel | payload-gated | wolf turns | **private** |
| investigator / vigilante results | payload-gated | those roles | **private** |
| previous_strategy | agent's own notes | all | **private, fed back** |
| retrieved obs / strategy points + verdict instructions | memory retrieval | all | **private** |

## Rules for adding a block

1. **Privacy first.** New private input ⇒ Send-builder gating + a `check_*` leak test. Payload
   construction is the boundary; templates are not trusted to filter.
2. **Content boundary.** Prompt = rules + deterministic public facts + how-to-behave. Interpretations
   ("what signals mean") belong to memory, never hardcoded into prompts —
   [`evidence/generation_prompt/prompt_boundary/`](../evidence/generation_prompt/prompt_boundary/experiment_log.md). The dead roster passes
   this test (deterministic public fact); a "who is suspicious" hint would not.
3. **Stable-early, volatile-late.** Static role-agnostic text at the head, per-turn content at the tail.
   Implicit caching currently doesn't fire on the game backend (see
   [`evidence/caching/report.md`](../evidence/caching/report.md)), but the prefix-checkpoint scheme is
   the standing upgrade path — don't make it worse.
4. **Output side is frozen-by-convention.** Action schemas ([`schemas/output.py`](../Agents/schemas/output.py))
   are model-visible: no class docstrings, `Field(description=)` edits need a prompt-freeze review,
   all-required fields (flash-lite drops optionals). Pre-action fields come **before** the action
   (prospective commitment: verdicts → strategy → action), so reasoning conditions the act.
5. **Any prompt change is a new epoch.** Run records carry the `runtime_fingerprint` (prompt hash);
   never compare across it ([fingerprinting build journey](../evidence/tracing/fingerprinting/experiment_log.md)).

## Current deltas (freshness: 2026-07-07)

- **Dead roster** shipped for day discuss + day vote (uncommitted on `feature-dimension-schema`);
  **night prompts don't carry it yet** — night actors still infer deaths from day summaries.
- **Alive-roles line** (cast minus dead reveals — derivable public info) — agreed, not built.
- **Suspicion read list** (per-player one-line `why` → `suspected_role` → confidence, emitted
  pre-action and fed back privately like `previous_strategy`; `why` is required with an `unchanged`
  sentinel, and is inspectable/attribution material only — never scored on its content) — planned;
  design context in the tagger/credit re-derivation memory and the belief-instrument discussion
  (2026-07-07).
