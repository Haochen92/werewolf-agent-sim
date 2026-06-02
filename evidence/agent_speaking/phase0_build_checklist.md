# Phase 0 — Build Checklist (dependency-ordered)

Consolidated, build-ready view of the locked Phase 0 design. The authoritative *reasoning* lives in
`experiment_log.md` ("Locked decisions", "Phase 0 — DESIGN VALIDATED & CLOSED", smoke-test sections);
this file is the linear build sequence with touchpoints + acceptance criteria. Build order = commit
order. File:line refs are from the 2026-06-01 grounding pass (verify before editing).

> **Ownership:** core app feature — written and owned by the human. This is a spec/checklist, not the
> implementation. Items marked **⚠️ CONFIRM** are design details discussed but not fully nailed —
> decide them before building that stage.

---

## Stage 0 — Feature branch
- [ ] Branch off `main` (e.g. `feat/sequential-discussion`). Incremental commits per stage so the
      redesign is keep/drop-able as a unit.

---

## Stage 1 — Schema foundation (`DayChannel`, speech-acts, `seq`)
*Implements: Point 2 (speech-acts), Point 4 (round→seq). Everything else builds on this.*

- [ ] `DayChannel` (`Agents/schemas/game_events.py:6-10`): **drop `round`**, **add `seq: int`**
      (monotonic per-day utterance index), **add `addressed: list[AddressedTarget]`**.
- [ ] New `AddressedTarget{ target: str, address_form: AddressForm, stance: Stance }` — **2-D, revised
      2026-06-02** (smoke test 1b proved the 1-D `act` enum was lossy). `AddressForm =
      question | response | mention` (scheduler-primary: does it demand a reply / is it a reply?);
      `Stance = accusation | defense | agreement | neutral` (brief + coalition/defense tracing). The
      old `act` enum incl. `none` is **dropped**. "Addressed nobody" = the *empty list*.
- [ ] `DayDiscussOutput` (`Agents/schemas/output.py:16-22`): add `addressed: list[AddressedTarget]`
      **right after `message`** (autoregressive: label who you addressed while the message is freshest,
      before `updated_strategy`). All-required, and `addressed` itself required-not-`default_factory`
      (flash-lite optional-field gotcha → model always emits it, `[]` when nobody).
  - ✅ **message nullability RESOLVED → `message: str` (required, NOT `str | None`).** Three reasons:
        (a) flash-lite JSON-parse gotcha on nullable fields; (b) in the sequential model silence is an
        *upstream* scheduler/novelty decision — by the time a role node runs, the agent speaks, so the
        null-valve is a relic of the concurrent self-select model; (c) drop the prompt's `return null`
        in Stage 5 to match.
  - **Scheduler mapping this schema feeds (Stage 2):** tier-1 = `form==question ∨ stance==accusation`;
        discharge (loop-close / debt relief) = `form==response`; low-pressure (no forced turn) =
        `form==mention ∧ stance≠accusation`. **Freshness dedup keys on `(speaker→target, stance)` —
        form EXCLUDED** (a re-accusation rephrased statement→question must not read as fresh; question
        looping is bounded by per-pair max-K + global cap, not freshness).
- [ ] `seq` assignment: set when appending a `DayChannel` = count of today's messages so far. The
      `game_master` night announcement (`Agents/nodes.py:504-551`) is an entry too → it takes the
      first `seq` of the day.
- [ ] `format_day_channel` (`Agents/formatters.py:11-20`): replace `[Day X, Round Y]` with seq-based
      (or `[Day X]`); stop referencing `.round`.
- [ ] **Enumerate every `.round` reader before cutting** (`grep -rn "\.round"`). Known: `check_round`
      (`Agents/nodes.py`), `StrategyAdoption.round` (`Agents/schemas/memory.py:260`), `EvalResult.round`
      (`evaluation/core/schemas.py:28`), situation cache key (`evaluation/components/situation_summary.py:127`),
      application replay (`evaluation/components/application.py`). Day-path consumers must change now;
      eval/output-schema consumers can ride the v5 migration but must at least not crash.

**Acceptance:** schema compiles; day graph still constructs; legacy frozen eval sets still load
(Pydantic v2 ignores the dropped `round`); a smoke replay produces `addressed` (cross-check vs
`[Pp]layer\s*_?\d+` regex on the message, as in `smoke_act_fields.py`).

---

## Stage 2 — Scheduler primitives (pure functions over the transcript)
*Implements: Point 1 (stateless scheduler), Point 5 (pressure/debt/freshness/K-cap). No LLM here —
unit-testable.*

- [ ] `PressureCalculator(today's day_channel ordered by seq) -> {agent: (tier, score)}`:
  - tier from the 2-D fields: **tier-1** = `form==question ∨ stance==accusation`; within tier-1,
    order `question` before bare `accusation`. `form==response` = discharge (debt relief).
    `form==mention ∧ stance≠accusation` = low-pressure (no forced turn).
  - recency decay over a rolling window; drop self-mentions.
  - **freshness/dedup**: a restated `(speaker→target, stance)` within the window adds **no** fresh
    pressure (**form EXCLUDED** — a rephrased re-accusation must not read as fresh). This kills
    pure-repetition ping-pong; question-looping is bounded by per-pair max-K + global cap, not freshness.
  - **per-pair max-K** re-engagement cap (≈2): after K `(A→B)` re-triggers in the window, further
    mutual triggers stop creating tier-1 (the only lever that bounds *escalating* domination — debt
    cannot, see below).
- [ ] `DebtTracker(last N utterances) -> {agent: debt, quiet_nudge}`. **Debt must NOT demote out of
      the addressed/tier-1 tier** (a direct fresh address is always answerable once). Debt/quiet-nudge
      only move the *proactive/low-pressure* ordering.
- [ ] Tiered score `pressure + intent − debt + quiet_nudge + seeded_random`, **strict tiers**:
      seeded-random breaks ties *within* a tier only. Seed off `(game_id, day, seq)` for reproducible
      resume.
- [ ] `EligibilityGate` — **reactive obligations + ranked proactive opportunity** (Smoke 4 redesign;
      NO novelty gate):
  - **reactive queue** = *undischarged* obligations over the window: addressed with `form==question`
    → owes an answer (top); `stance==accusation` → owes a defense. **Cleared** when answered
    (`form==response` toward the asker). Reactive speakers bypass any gate — they have a deterministic
    reason. *Order within tier-1: question before accusation.*
  - **proactive opportunity** fires **only when the reactive queue is empty** (quiet cycle),
    budget-capped (Phase 0 = **1**). Candidate ranked by cheap deterministic heuristics:
    (a) **has unrevealed private info** — heavy weight, NOT a strict first-sort (a guaranteed slot is a
    power-role tell — P3); (b) **hasn't spoken recently** (`DebtTracker`); (c) **suspicion-graph
    centrality among players NOT already reactive-queued** (uses `addressed_targets` accusation edges;
    restrict to non-targeted to avoid double-counting reactive). **Seeded-random** tiebreak among top
    candidates `(game_id, day, seq)`. *No novelty check — proactive = scheduler-created opportunity,
    bounded by the budget, not by a proof of novelty.*
  - **day-start opener floor = 1** (forced first utterance), seeded-random.
  - *Dependency:* the per-pair-K + freshness caps above are what let the reactive queue drain so
    proactive can ever fire (else continuous accusations starve it).

**Acceptance:** unit tests on synthetic transcripts — A questions B ⇒ B reactive (owes answer); B
responds to A ⇒ obligation cleared; restated accusation ⇒ no fresh obligation; K+1th `(A→B)` ⇒ no
tier-1; reactive non-empty ⇒ no proactive; reactive empty ⇒ exactly 1 proactive, ranked + seeded;
empty-pressure day start ⇒ opener floor fires exactly once.

---

## Stage 3 — ~~Novelty gate~~ REMOVED (Smoke test 4, 2026-06-02)
*The folded situation-summary novelty gate was falsified (self-judged novelty doesn't discriminate —
variant A labels everything `repeated`, variant B everything `new`). Silence is now deterministic in
Stage 2 (reactive obligations + budget-capped ranked proactive). There is no Stage 3.*

- [ ] **Remove** the `novelty` / `novelty_reasoning` fields from `SituationSummary` (Stage 1) — they
      don't discriminate and cost ~2% situation drift.
- [ ] `_generate_situations_for_agent` keeps returning `composed_situations` (no novelty to surface).
- [ ] Situation summary + generation stay **live per-turn** (computed at dispatch — no staleness).
- **Deferred refinement (only if logs show proactive redundancy):** embedding-similarity novelty —
      embed a 1-line draft, cosine vs transcript (embeddings already computed for retrieval), threshold.
      0 extra LLM calls, disinterested by geometry. See Smoke 4 "future refinements".

---

## Stage 4 — Graph rewiring (`SCHEDULE` node + self-loop)
*Implements: Point 1 (self-looping subgraph). Replaces `PREPARE_ROUND`/`fan_out`/`COLLECT`/`check_round`.*

- [ ] New `SCHEDULE` node: recompute pressure/eligibility (Stage 2 pure fns), pick speaker **or**
      terminate, write `{next_speaker, firing_reason, gating_mode}` to state.
- [ ] `route_speaker` conditional edge: **single `Send`** to the chosen existing role node
      (`villager_discuss`/… `Agents/agents.py:878-939`), reusing per-speaker payload construction
      (`fan_out_day` logic, `Agents/nodes.py:88-176`) — one `Send` instead of N. On terminate →
      `SUMMARIZE_DAY_DISCUSSION`.
- [ ] Role node loops back to `SCHEDULE`. Build the day graph accordingly (`Agents/graphs/day.py:29-72`).
- [ ] **Voting nodes untouched** (already simultaneous/blind).
- [ ] Day-start: night announcement already appended by `night_resolution`; trigger the opener floor.
- ✅ **proactive-silence bookkeeping — NO LONGER NEEDED** (Smoke 4). With the novelty gate removed, a
      selected proactive candidate **always speaks** (the budget+ranking already chose them); there's
      no `already_said` self-silence and so no re-pick/re-spend problem. The transient "tried" set is
      dropped.
- ⚠️ **CONFIRM role-node gating flag (simplified).** `gating_mode` now only distinguishes the
      *firing-reason brief* (reactive: "answer player_X" / "defend player_X" vs proactive: "share a new
      read") passed to `_run_memory_informed_action` (`Agents/agents.py:655`). **No self-silence path** —
      neither mode can abort; both always emit a message.

**Acceptance:** a day runs sequentially, one speaker per cycle; per-utterance node boundaries show as
separate Langfuse spans; discussion converges or hits the cap; vote still parallel/blind.

---

## Stage 5 — Prompt edits
*Implements: silence-gate decision (remove only the generation-prompt null-return), firing-reason brief.*

- [ ] Remove the `return message = null` instruction from `DISCUSSION_SILENCE_RULE`
      (`Agents/prompts/common.py:39-48`). **Keep the content discipline** ("don't restate, don't
      repeat appeals, don't agree without adding reasoning").
- [ ] Role discuss prompts (`Agents/prompts/day.py`): consume `firing_reason` as the message **brief**
      ("answer player_3's question" / "defend player_6's accusation" / "share new read"); instruct
      emission of the `addressed` speech-act fields.

**Acceptance:** generated messages are non-redundant, anchored to the brief; `addressed` populated and
consistent with the message text (regex cross-check); piled-on agents *defend* rather than re-appeal.

---

## Stage 6 — Termination + caps
*Implements: Point 5.*

- [ ] Convergence: after each utterance, recompute eligibility; terminate when the **reactive queue is
      empty AND the proactive budget for this quiet stretch is spent** (no novelty check — Smoke 4).
- [ ] Global cap: max utterances/day (rough default ~2–3× surviving players). Per-pair K (Stage 2).

**Acceptance:** ping-pong stress test (two mutual accusers) terminates without hitting the global cap
in the pure-repetition case; quiet day ⇒ short discussion seeded by the opener floor.

---

## Cross-cutting
- [ ] **Tracing:** `SCHEDULE` logs per-turn scores (pressure/debt/tier/chosen + reason) — inspectable
      for tuning. (Folds into the broader Phase A tracing rework.)
- [ ] **Params** centralized with defaults (tune later, not now): pressure type-weights, recency
      window, debt magnitude, quiet-nudge, global cap, per-pair K, opener-floor = **1**, proactive
      budget = **1** (Phase 0), proactive ranking weights (private-info / recency / centrality).

## Build-time residuals to carry (NOT blockers)
- Speech-act: the 1-D accusation-over-labeling residual was **resolved by the 2-D revision**
  (it was axis-conflation, not error — smoke test 1b). Remaining: at-scale validity of the 2-field
  structure + blind-judge-at-scale; `response`/`mention` are rare in endgame slices (common early).
- **Proactive redundancy** (replaces the dropped novelty residual) — with no novelty gate, a proactive
  speaker on a quiet cycle *might* restate. **Observe in logs.** Bounded by budget=1 + content
  discipline. If it bites, add embedding-similarity novelty (0 extra LLM calls — Smoke 4 refinement).
- Proactive ranking heuristics deferred to later phases: stance-vs-majority, strategy-profile "push",
  info-value (need extra logic / semantic parsing — not Phase 0). Cross-candidate dedup via wave/batch.
- Optional: free-text **RAG-query stability vs temp** — separate test, only if query consistency bites.

## After Phase 0
Build → **discussion-quality gate** (does sequential read better than concurrent?) → Phase 1 (human)
→ 2 (novelty refinement) → 3 (voice) → 4 (FT, optional). Closing Phase 0 unblocks parked Phase A
items (+roles, tracing, night memory, v5 DB; fold `round→seq` into v5). See experiment_log
"After Phase 0".
