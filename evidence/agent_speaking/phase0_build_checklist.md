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

> **STATUS: largely DONE & COMMITTED** (831b908..e4d4d21). Committed field names (authoritative):
> `DayChannel{day, seq, player, message, addressed_targets}`, `AddressedTarget{target, addressed_form,
> stance}`. The bullets below keep the *original* `addressed`/`address_form` draft naming — superseded by
> the committed names; ignore the drift. **Two Stage-1 follow-ups remain (2026-06-03):**
> - [ ] **`DayChannel.passed: bool = False`** + **`DayDiscussOutput.pass_turn: bool`** (required) — the
>       proactive silence valve. A pass appends a hidden `passed=True` marker (empty message, no targets);
>       `pass_turn` maps into it. Reactive turns always emit `pass_turn=False`. (See log "Point 3 prelude".)
> - [ ] **Display trim:** drop `seq` from all formatters + `day` from the agent-facing (today-only)
>       transcript → render `player_id: message`; formatter **skips `passed` rows**. Storage unchanged;
>       keep `day` in postgame/summary formatters. (See log "DayChannel storage vs display".)

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
*Implements: Point 1 (stateless scheduler), Point 5 (freshness/K-cap/termination). No LLM — unit-testable.*

> **DESIGN CLOSED 2026-06-03** — see experiment_log "Stage 2 design pass" + "Point 3 prelude". Model =
> **reactive/proactive** (NOT a unified weighted score — `intent`/blended-score dropped). Proactive is
> **role-blind** (private-info + centrality dropped for Phase 0). Scheduler is **stateless** (recompute
> from `day_channel` each SCHEDULE cycle; one transcript scan scores all agents). Params live in
> `game_config.py` (committed c25a675).
>
> **Use the COMMITTED schema field names** (`game_events.py`): `DayChannel.addressed_targets`,
> `AddressedTarget.addressed_form` ∈ {question,response,mention}, `.stance` ∈
> {accusation,defense,agreement,neutral}, `.target`, `DayChannel.passed`. (Earlier drafts said
> `addressed`/`address_form`/`form` — naming drift; ignore.)

Four pure fns of *(today's `day_channel` + within-day-immutable game state)*:

- [ ] `build_reactive_queue(today) -> list[ReactiveItem]` — obligations **keyed by the obligated agent**
      (grouped, so a multi-accused agent answers everyone in one turn):
  - per `addressed_target`: `addressed_form=="question"` → target owes an answer; `stance=="accusation"`
    → target owes a defense; `addressed_form=="response"` → **discharges the *speaker's own*** debt to
    that target.
  - **freshness**: while an edge `(speaker→target, stance)` is *open* (target hasn't discharged), a
    restatement (`addressed_form` **and wording** excluded) adds **no** second obligation.
  - **per-pair K** (`per_pair_reengagement_cap`=2): the edge can create an obligation at most K times *per
    consecutive burst*; (K+1)th blocked. A *different speaker* = a different edge = fresh.
  - **cooldown reset** (`reengagement_cooldown(n)=ceil(multiplier·n)`, M≈survivors): K is **consecutive,
    not total-per-day** — if a pair sits M utterances *untouched* (no open *or* close), its `cycles` resets
    to 0 so a cooled feud may reopen once the room has moved on. Suggested `Balance` record per pair:
    `{open_seq, cycles, last_touch_seq}`; stamp `last_touch_seq` on **both** open and close; apply the
    reset guard *before* the freshness/K/open checks. (2026-06-04; retires the proactive-valve backstop.)
- [ ] `speech_recency(today) -> {agent: turns_since_spoke}` — **derived** (`current_seq − last_spoke_seq`,
      ∞ if silent). A `passed` marker advances `last_spoke` too. Feeds proactive only; never demotes a
      reactive obligation.
- [ ] `rank_proactive(candidates, recency, seed) -> ranked` — **role-blind: recency + seeded-random
      ONLY.** (Private-info/centrality dropped — see log; investigator reveal is a strategic *agent*
      decision, not a scheduling one.) Seed = `(session_id, day, seq)`.
- [ ] `select_next(today, survivors, game_config, seed) -> Decision` — **reactive-first → proactive →
      terminate**:
  - reactive non-empty → highest-priority obligated agent (order: recency-of-address; question-vs-
    accusation is a Phase-2 tiebreak, not now).
  - reactive empty → top proactive candidate **not in the current trailing-pass streak** (the role node
    may set `pass_turn`).
  - **TERMINATE** when: the trailing `proactive_budget`(=3) utterances are **all passes** (P distinct
    agents declined in a row); OR `utterance_cap(survivors)` real utterances reached; OR no eligible
    speaker. **A pass = a hidden `DayChannel(passed=True)` marker, NOT a no-append** (so the stateless
    scheduler can see it; any *real* utterance resets the pass streak).
  - **opener**: day start is just the first quiet cycle (same rule); `opener_floor`=1 is the practical
    minimum unless P agents decline.

**Acceptance** (unit tests, synthetic transcripts, **no LLM**): A questions B ⇒ B reactive (owes answer);
B responds to A ⇒ cleared; restated accusation while open ⇒ no fresh obligation; (K+1)th `(A→B)` ⇒ no
obligation; `C→B` ⇒ fresh (different edge); reactive non-empty ⇒ no proactive; reactive empty ⇒ 1
proactive (ranked + seeded); `proactive_budget` consecutive passes ⇒ terminate; any real utterance resets
the streak; `utterance_cap` real utterances ⇒ terminate.

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

> **Design closed 2026-06-03** (log "Point 3 prelude"). Key wiring facts: scheduler is stateless →
> **no new shared `DayGraphState` field** (the decision is consumed immediately by the routing edge);
> `firing_reason` rides the transient `Send` payload (tracing copy → Langfuse span). **SCHEDULE owns ALL
> termination** (the role node always loops back).

- [ ] New `SCHEDULE` node: run `select_next` (Stage 2 pure fns over `day_channel`); emit the decision
      (consumed by `route_speaker`). Log per-turn scores + chosen + reason to the Langfuse span.
- [ ] `route_speaker` conditional edge: **single `Send`** to the chosen existing role node
      (`villager_discuss`/… `Agents/agents.py:878-939`), reusing per-speaker payload construction
      (`fan_out_day` logic, `Agents/nodes.py:88-176`) — one `Send` instead of N, **plus `firing_reason`
      in the payload**. On terminate → `SUMMARIZE_DAY_DISCUSSION`.
- [ ] Role node **always** loops back to `SCHEDULE` (plain edge — *not* a `Command`-to-SUMMARIZE branch;
      passes are visible to SCHEDULE so it decides termination). Build the day graph accordingly
      (`Agents/graphs/day.py:29-72`).
- [ ] **`recursion_limit`** at the day-graph invoke (`Agents/graphs/parent.py:28,37`): derive from the
      cap → `game_config.discussion_recursion_limit(len(survivors))` (=2·cap+10) so the graceful cap
      fires before `GraphRecursionError`. Interim hardcoded `100` is safe ≤15 players.
- [ ] **Voting nodes untouched** (already simultaneous/blind).
- [ ] Day-start: night announcement already appended by `night_resolution`; first SCHEDULE cycle is the
      opener (quiet cycle → proactive path → `opener_floor`).
- ✅ **proactive silence — RECORDED, not suppressed** (revised 2026-06-03). A proactive pick **may**
      `pass_turn`; the role node then appends a **hidden `DayChannel(passed=True)`** marker (empty
      message, no targets) and loops to SCHEDULE. SCHEDULE counts trailing passes → terminate at
      `proactive_budget` consecutive. No transient state, no re-pick logic. Reactive picks never pass.
- [ ] **Role-node firing-reason brief.** `firing_reason` (reactive: "answer player_X" / "defend against
      player_X" vs proactive: "share a new read") passed via the `Send` payload to
      `_run_memory_informed_action` (`Agents/agents.py:655`). Reactive turns force `pass_turn=False`;
      only proactive turns may pass.

**Acceptance:** a day runs sequentially, one speaker per cycle; per-utterance node boundaries show as
separate Langfuse spans; a quiet stretch of `proactive_budget` passes terminates; cap is the backstop;
vote still parallel/blind.

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

- [ ] Convergence (revised 2026-06-03, folded into `select_next`): terminate when the **trailing
      `proactive_budget`(=3) utterances are all `passed` markers** (P distinct agents declined in a row);
      any real utterance resets the streak. No novelty check (Smoke 4).
- [ ] Global cap (backstop): `game_config.utterance_cap(survivors)` = `max(6, ceil(3.0·survivors))` real
      utterances (passes excluded). Per-pair K=2 (Stage 2).

**Acceptance:** ping-pong stress test (two mutual accusers) terminates via per-pair-K + freshness without
hitting the global cap in the pure-repetition case; quiet day ⇒ short discussion ended by P consecutive
passes.

---

## Cross-cutting
- [ ] **Tracing:** `SCHEDULE` logs per-turn ranking + chosen speaker + `firing_reason` to the Langfuse
      span — inspectable for tuning. (Folds into the broader Phase A tracing rework.)
- [x] **Params** centralized in `game_config.py` (committed c25a675): `discussion_utterance_multiplier`
      =3.0, `min_discussion_utterances`=6, `per_pair_reengagement_cap`=2, `proactive_budget`=**3**,
      `opener_floor`=1, + `utterance_cap()`/`discussion_recursion_limit()`. Proactive ranking is
      **role-blind = recency + seeded-random ONLY** (private-info + centrality dropped — see log). Tune later.

## Build-time residuals to carry (NOT blockers)
- Speech-act: the 1-D accusation-over-labeling residual was **resolved by the 2-D revision**
  (it was axis-conflation, not error — smoke test 1b). Remaining: at-scale validity of the 2-field
  structure + blind-judge-at-scale; `response`/`mention` are rare in endgame slices (common early).
- **Proactive redundancy** (replaces the dropped novelty residual) — with no novelty gate, a proactive
  speaker on a quiet cycle *might* restate. **Observe in logs.** Bounded by `proactive_budget`(=3) +
  `pass_turn` + content discipline. If it bites, add embedding-similarity novelty (0 extra LLM calls).
- Proactive ranking heuristics deferred to later phases: stance-vs-majority, strategy-profile "push",
  info-value (need extra logic / semantic parsing — not Phase 0). Cross-candidate dedup via wave/batch.
- Optional: free-text **RAG-query stability vs temp** — separate test, only if query consistency bites.

## After Phase 0
Build → **discussion-quality gate** (does sequential read better than concurrent?) → Phase 1 (human)
→ 2 (novelty refinement) → 3 (voice) → 4 (FT, optional). Closing Phase 0 unblocks parked Phase A
items (+roles, tracing, night memory, v5 DB; fold `round→seq` into v5). See experiment_log
"After Phase 0".
