# Per-Day Replay — Design Spec

> **STATUS: DESIGN — NOT BUILT.** Dated **2026-07-02**. This is an execution-ready specification,
> not a report of results. No `day_replay.py` exists yet; the file layout in §7 is proposed. This
> spec is the deliverable of Phase 6 of the "harden the eval instruments" pass
> (`.claude/plans/first-read-evidence-evaluation-source-ma-gentle-wirth.md`).

**Scope.** A harness that re-runs a *single day* of a recorded game under a swapped condition
(memory ON vs OFF), on-policy within that day, sharing an identical frozen history with the recording.
It sits between the per-turn decision-replay *screen* (`evaluation/src/experiments/decision_replay.py`
— off-policy, one decision, no propagation) and a full paired batch A/B (`evidence/.../paired_ab/` —
on-policy end-to-end, ~$0.50/game). Its niche: **on-policy day-level evidence at ~1/5 the cost of a
full game**, so the within-day causal effect of a condition can be measured given a fixed prefix.

> **Orientation — the three replay altitudes.**
>
> | Altitude | On-policy? | Propagates? | Cost | What it isolates |
> |---|---|---|---|---|
> | Per-turn screen (`decision_replay`) | no (frozen context) | no | ~$0 (mechanical) / cheap | one decision, memory block swapped |
> | **Per-day replay (this doc)** | **within the day** | **within the day** | **~$0.10–0.15/day** | within-day effect, fixed prefix |
> | Full paired A/B (`paired_ab`) | end-to-end | whole game | ~$0.50/game | game-outcome / compounding effect |
>
> The reconstruction contract (§2) is the whole risk surface: a day replay is only as valid as the
> day-entry state it rebuilds. Everything below hangs on getting that state byte-faithful.

---

## 1. Unit & protocol

**Unit of analysis:** a `(game G, day k)` pair with **k ≥ 2**. Day 1 is a pre-voting day
(`GameConfig.first_voting_day == 2`; day 1 runs ~one discussion round and `route_after_day_summary`
returns `END` before `START_VOTING`), so it produces no lynch and no vote-accuracy signal — it is
excluded. Day 2 is the **primary stratum** (see §3).

**Protocol.** For each replayed `(G, k)`:

1. Reconstruct the day-`k` entry state = the exact `DayGraphState` payload that
   `Agents/graphs/parent.py::day_phase` builds when the live orchestrator enters day `k` (§2).
2. Compile the **live day subgraph** (`Agents/graphs/day.py::build_day_graph`) once per arm, each with
   its own store (§2 store row). Reusing the production subgraph — not a reimplementation — is the
   point: the scheduler, `fan_out_vote`/`allow_abstain` gating, summary node, and vote fan-out are the
   real ones, so replay drift can only come from the reconstructed *state*, never from a divergent
   harness.
3. Invoke the compiled graph on the reconstructed payload, **on-policy within the day**: the scheduler
   picks real speakers, agents generate real utterances, votes are cast live. The prefix (days `< k`)
   is **frozen** — supplied as history, never re-simulated.
4. Score the resulting day (§4). One arm per condition; both arms share step-1's reconstructed state
   byte-for-byte except for the store/`memory_config`.

**`config` / `configurable` contents (per invocation).** The day subgraph reads two things off
`RunnableConfig`:

- `configurable.game_id` — **reuse the recorded game's `game_id` verbatim.** The scheduler seeds
  proactive ranking with `cycle_seed(game_id, current_day, len(current_day_discussion))`
  (`Agents/turn/scheduler.py:17-23`, called from `Agents/nodes/day/flow.py:63`). `cycle_seed` is
  `zlib.crc32(f"{game_id}:{day}:{cycle}")` — pure and replayable. Reusing `game_id` keeps the
  tie-break RNG identical to the recording, so any behavioral divergence is attributable to the
  condition, not to reshuffled speaker order. (`game_id` also seeds role assignment in
  `initialize_game`, but role assignment is out of scope here — we import the recorded `roles` dict
  directly, §2.)
- `recursion_limit` — set to `game_config.discussion_recursion_limit(num_survivors)` exactly as
  `day_phase` does (`= 2 * proactive_budget * utterance_cap(N) + 10`), so the scheduler's graceful
  cap/trailing-pass terminate fires before a `GraphRecursionError`.
- `memory_config` (the per-role ON/OFF toggle dict) + the store attached at `.compile(store=...)` are
  the **only** things that differ between arms.

The `GraphContext` runtime (`context=`) supplies the `eval_sink` and `metrics` accumulator; a replay
run uses a fresh throwaway `metrics` and may sink eval-cases to this evidence folder.

---

## 2. State-reconstruction contract

The contract **is** `day_phase`'s payload (`Agents/graphs/parent.py:80-94`) — 13 keys. Every one must
be reproduced; a day replay whose entry state differs from what the live game held on day `k` is
measuring the wrong counterfactual. Each field's source:

| `DayGraphState` field | Source | How |
|---|---|---|
| `roles` | batch record | `record["roles"]` verbatim (full `{player: role}`, all 9). |
| `current_day` | — | literal `k`. |
| `current_round` | — | literal `0` (as `day_phase` sets it). |
| `day_votes` | — | literal `[]` (fresh; the day hasn't voted yet). |
| `human_player` | — | sentinel `""` (eval games have no human; `speaker_id == ""` is never true, so no one is flagged human — matches the recorded run, where `human_player` is vestigial and absent from the record). |
| `day_channel` | batch record | `[m for m in record["day_channel"] if m.day < k]` — the full prior transcript **including** each night's game-master death announcement (night-`(k-1)` deaths are stamped `day=k-1` by `night_kill_resolution`, so `day < k` includes them) and each prior day's vote-result message. Re-hydrate each dict into a `DayChannel` schema object. |
| `day_summaries` | batch record | `[s for s in record["day_summaries"] if s.day < k]` — includes both the discussion `DaySummary` and the vote-result / night-death `DaySummary` for each prior day. Re-hydrate into `DaySummary`. |
| `surviving_wolves` | **recomputed + hard-asserted** | Start from `roles`, remove every lynch in `day_resolutions[day < k]` (`voted_player`) and every death in `night_resolutions[day < k]` (`deaths[]`); keep the `wolf`-role remainder. **Then hard-assert equality against the day-`k` sidecar** `private_context.surviving_wolves` (present on every day-`k` EvalCase). Mismatch → **raise, never warn** (§6). |
| `surviving_villagers` | **recomputed + hard-asserted** | Same reconstruction, non-`wolf` remainder (town + SK bucket, per `initialize_game`). Hard-assert against sidecar `private_context.surviving_villagers`. |
| `no_lynch_streak` | recomputed | `no_lynch_streak_before(k, record["day_resolutions"])` — already implemented in `evaluation/src/loop/decision_scoring.py:73-82` (a lynch resets to 0, a no-lynch day increments). Reuse it; do not reimplement. This drives `fan_out_vote`'s `allow_abstain` gate. |
| `agent_strategies` | sidecar | `{player: <that player's day-k first EvalCase>.output.eval_case.private_context.previous_strategy}` over all survivors. This is the running strategy note each agent carried into day `k`. |
| `investigator_results` | batch record **or** sidecar | `record["investigator_results"]` filtered to `day < k` (top-level on the batch record) — cross-check against the investigator's day-`k` sidecar `private_context.investigator_results`. |
| `vigilante_results` | **sidecar only** | Batch records do **not** carry `vigilante_results` at top level (verified: absent from every `ab_*.jsonl`). Read from the vigilante's day-`k` `private_context.vigilante_results`. If no vigilante is alive at day `k`, `[]`. |

**Span-wrapper nesting.** Sidecar EvalCases are Langfuse observation dumps: the payload lives at
`case["output"]["eval_case"].<field>`, and private state at
`case["output"]["eval_case"]["private_context"].<field>`. Reading `case[<field>]` directly returns
`None` and produces false "field empty everywhere" reads. Sidecar path is
`record["eval_cases_path"]` (`batch_results/eval_cases/<session>/<game_id>.jsonl`); the day-`k` cases
are those with `output.eval_case.day == k`.

**Mandatory cross-assert.** The survivor reconstruction (from resolutions) and the sidecar
`private_context` survivor lists are two independent derivations of the same fact. They **must** be
asserted equal per `(G, k)` before any LLM call. This is the single cheapest guard against a silent
off-by-one in the resolution replay poisoning an entire run. It is a **hard fail**, logged with the
diff, never a warning.

**Store, per arm** (`evaluation/src/replay/retrieval.py::build_store_from_snapshots`):
- **OFF arm:** empty store (or `memory_config` all-false → retrieval skipped). Matches the recording
  in the counterfactual of §3.
- **ON arm:** `build_store_from_snapshots(observations.json, strategy_points.json)` from the frozen
  store snapshot that the batch used. The snapshot's namespaces are expanded to `(kind, role, phase)`
  cells and re-embedded into a fresh `InMemoryStore`.

### Known-unreconstructible items (v1 scope boundaries — state these, don't paper over them)

1. **Mid-batch store evolution.** In loop-era runs (`town_only_run*`, `v2_full`) each game's
   post-game extraction mutates the store, so the store state *at game G* cannot be rebuilt from a
   single snapshot. **v1 is restricted to frozen-store arms** (`ab_*` / `v6ab_*`), where the store is
   fixed for the whole batch and one snapshot reconstructs it faithfully.
2. **Mid-game strategy-adoption store mutations.** Adoption-counter / strategy-point mutations that a
   live game applies mid-run are not captured in the day-`k` snapshot. Document as a caveat; the
   frozen-store restriction bounds but does not fully eliminate it.
3. **Fingerprint / code-drift labeling.** The replay runs at *today's* code (prompts, models, backend)
   against a prefix recorded under the batch's fingerprint. Every replay record must stamp both the
   recorded `runtime_fingerprint` and the current git SHA, and the acceptance gate (§6) measures
   whether that drift is within the self-agreement noise floor before any ON-vs-OFF claim is trusted.

---

## 3. Counterfactual validity

**Source from memory-OFF recordings.** Pick `(G, k)` from games actually *played with memory OFF*
(the OFF/baseline arm of a paired `ab_*` batch). The frozen prefix (days `< k`) was then generated by
agents with no memory, so:

- The **OFF replay arm is on-policy by construction** — its no-memory prefix is exactly what a
  no-memory agent would have produced, so re-running day `k` OFF should reproduce recorded behavior
  (this is the acceptance gate, §6).
- The **ON replay arm** is the clean counterfactual: "what if this agent had memory at *this*
  decision point, given an identical history." The ON effect is the *pure within-day* delta from
  adding the store, with the prefix held fixed.

If we instead sourced from an ON game, the OFF arm would be **off-policy** — asked to act on a history
that memory-enabled agents produced but a memory-less agent could not have — contaminating the
baseline. Hence: OFF-sourced only, in v1.

**Day-2 as primary stratum.** Day 2 has the largest, most comparable entry state across games (one
night of deaths, full-ish rosters, `no_lynch_streak` typically 0 → abstain-gating identical), so
entry-state variance is lowest. Deeper days are admissible as a secondary stratum but must be
**stratified by entry-state equivalence** (survivor count, `no_lynch_streak`, faction balance) — an
ON-vs-OFF comparison across mismatched entry states confounds the condition with the board.

**No multi-day chaining in v1.** A replayed day ends at `COLLECT_VOTES`; we do **not** feed its
outcome into a replayed night and a replayed day `k+1`. Chaining would (a) require reconstructing the
full `OrchestratorGraph` state including night `*_player` markers and `vigilante_bullets` (out of the
`DayGraphState` contract), and (b) compound reconstruction error across cycles, defeating the "fixed
prefix" cleanliness. Multi-day propagation is precisely what the full paired A/B already measures;
this harness deliberately does not try to.

---

## 4. Scoring & statistics

All day-level, all deterministic (no LLM judge — this is the objective half, mirroring
`decision_scoring.py`).

**Deterministic day outcomes** (per replayed day, both arms):
- **Lynch outcome** via the plurality rule factored out of `Agents/nodes/orchestrator.py::day_resolution`
  (lines 158-164): `lynched = plurality if plurality and plurality != "abstain" else None`, where
  `plurality` is the unique argmax of the vote `Counter` (a tie, an abstain plurality, or no votes →
  no-lynch). **Factor this rule into a shared pure helper** (it currently lives inline in the node,
  entangled with state mutation and Langfuse spans) and call it from both the live node and the replay
  scorer, so the replay's "who got lynched" is byte-identical to production. Then:
  - `threat_lynched` (binary): `roles[lynched] in {"wolf", "serial_killer"}`.
  - `town_mislynched` (binary): `lynched is not None and roles[lynched] not in {"wolf","serial_killer"}`.
- **Town vote accuracy** (dense): for each town voter, `score_vote(votee, roles)`
  (`decision_scoring.py:48-63`) → `hit_threat`; day-level `town_vote_accuracy` = mean `hit_threat`
  over town voters (abstain is its own bucket, neither hit nor mislynch — report `abstain_rate`
  alongside). `allow_abstain` for the day is reconstructed by `allow_abstain_for(k, day_resolutions)`
  so both arms are offered the same choice set the original had.

**Pairing & tests.** Pair per `(G, k)` — OFF replay vs ON replay of the *same* day (shared prefix,
shared role draw → the tightest possible pairing). Using `evaluation/src/core/stats.py`:
- `mcnemar_exact(off, on)` on the binary day outcomes (`threat_lynched`, `town_mislynched`) — exact
  two-sided binomial on discordant pairs.
- `wilcoxon_paired(off, on)` on `town_vote_accuracy` (dense, per game-day).

**Analysis unit.** Primary analysis = **one replayed day per game** (day 2), so pairs are independent
games — clean McNemar/Wilcoxon. Replaying multiple days from the same game yields *correlated*
game-days (shared roles/prefix); that is a **secondary, stratified** analysis only, and its N must not
be pooled naively with the primary as if independent.

---

## 5. Cost model

Anchored to a full game ≈ **$0.50** and the verified caps
(`GameConfig.utterance_cap(N) = max(min, ceil(3·N))`, i.e. multiplier 3;
`utterance_cap(9) = 27`, `utterance_cap(7) = 21`).

Per **single-arm day replay** (day 2, ~7–9 survivors):
- Discussion: ~`utterance_cap(N)` real utterances → ~21–27 LLM calls (plus a few pass cycles that
  don't count toward the cap).
- Voting: 1 call per survivor → ~7–9 calls.
- Day summary: 1 call.
- ⇒ **OFF arm ≈ 30–37 LLM calls.** **ON arm ≈ +50–100%** on the memory-consuming calls (each
  memory-enabled utterance/vote triggers a situation-summarization + retrieval call), so the ON arm
  roughly doubles the marginal LLM cost of the calls that use memory.

⇒ **~$0.10–0.15 per day replay** ≈ **20–30% of a full game** — consistent with a day being ~1 of ~4
cycles and voting/summary being cheaper than a full night.

**Campaign budget:** 30 paired game-days (60 arm-replays) ≈ **$6–12** + a **$3–5 acceptance-gate**
run (§6) ⇒ **≈ $10–17 total** to stand the harness up and produce first evidence.

> **Correction vs the Phase-6 summary:** the summary cited "utterance_cap(9)≈25"; the verified cap is
> **27** (multiplier 3, not ~2.8). Day-2 games usually have 7–8 survivors (cap 21–24), so the
> per-replay dollar figures are unchanged, but the cap constant is 3·N, not ~25-flat.

---

## 6. Acceptance gate (step 1 of any future build — build this before trusting one ON-vs-OFF number)

**Unchanged-condition replay.** Before measuring any ON-vs-OFF effect, replay **10–15 game-days ×
2–3 tie-break seeds under the *recorded* condition** (OFF-sourced day replayed OFF) and check it
reproduces the recorded day. Two tiers:

- **Hard invariants (deterministic — assert equality, hard-fail on violation):**
  - reconstructed `allow_abstain` for the day == what the recording offered,
  - reconstructed survivor set == day-`k` sidecar `private_context` survivors (the §2 cross-assert),
  - every cast vote targets a legal (surviving) player or `abstain`.
- **Statistical indistinguishability (distributional — the replay is content-reactive, so never
  demand transcript equality):** replayed vs recorded days must be statistically indistinguishable on
  `town_vote_accuracy`, `town_mislynched` rate, `abstain_rate`, real-utterance count, and
  lynched-role distribution. **The measured self-agreement becomes the harness's cited noise floor** —
  every later ON-vs-OFF effect is reported against it, and an effect inside the floor is "not
  distinguishable from replay noise."

**Risks & the guard each gets:**
- **State fidelity** → the §2 hard-fail cross-assert. **Never warn-and-continue**; a silent
  reconstruction bug poisons the whole run (this is the recurrence class the tagger's swallow-all
  `except` already caused elsewhere in the codebase).
- **Content-reactive scheduler** → the scheduler picks speakers from live transcript content, so two
  valid replays diverge in wording and turn order even under identical seeds. The gate is therefore
  **distributional, never transcript-equality**.
- **Store re-embedding drift** → `build_store_from_snapshots` re-embeds the snapshot at replay time; a
  changed embedding model/backend shifts retrieval keys silently. Guard: compare replayed vs recorded
  **retrieval keys at the same turns** (the recorded EvalCases carry `retrieved_observations` /
  `retrieved_strategy_points` — assert the replay retrieves the same items at matched decisions, or
  quantify the drift as part of the noise floor). Pairs with the plan's embedding-canary-pairs test.

---

## 7. Proposed code layout (NOT built)

Follows the eval architecture rule (`CLAUDE.md`): reusable logic under `evaluation/src/`, a thin
config-driven runner under `evaluation/src/experiments/`, evidence to this folder.

- **`evaluation/src/replay/day.py`** (new — reusable):
  - `day_entry_state(record, sidecar, k) -> DayGraphState` — the §2 reconstruction contract, including
    the mandatory survivor cross-assert (hard-fail).
  - `replay_store_for_arm(arm, snapshot_paths) -> InMemoryStore | None` — thin wrapper over
    `build_store_from_snapshots` (ON) / empty (OFF).
  - `replay_day(record, sidecar, k, arm, config) -> DayReplayResult` — compile `build_day_graph` with
    the arm's store, invoke on the reconstructed payload, return the scored day (§4).
- **`evaluation/src/experiments/day_replay.py`** (new — thin runner):
  - CLI `--batch <ab_*.jsonl> --day <k> --n <pairs> --arms off,on [--validate]`.
  - `--validate` runs the §6 acceptance gate (unchanged-condition replay) instead of the ON-vs-OFF
    comparison.
  - Reuses `core/stats.py` for the paired tests; writes results + provenance (both fingerprints) to
    `evidence/memory_system/effectiveness/day_replay/`.
- **The plurality/no-lynch helper** (§4) should be factored out of
  `Agents/nodes/orchestrator.py::day_resolution` into a shared pure function both the live node and the
  scorer import — so production and replay share one lynch rule by construction.

---

## 8. What this harness answers — and what it can't

**Answers:** the **within-day causal effect** of a condition (memory ON vs OFF) on a day's decisions,
given a *fixed history* — measured on-policy (real discussion + voting), paired at the tightest unit
(same game, same day, same prefix), at ~1/5 the cost of a full game.

**Cannot answer:** the **game-outcome / compounding effect**. Because the prefix is frozen and there is
no multi-day chaining, this harness says nothing about how a within-day advantage propagates to a win,
or whether memory compounds across days. **That question stays with the full paired batch A/B**
(`paired_ab`) — the open v7 compounding question is not something a day replay can close.

Its designed slot in the ladder: **on-policy day evidence between the per-turn screen** (cheap but
off-policy, no propagation) **and the full paired run** (on-policy but 5× the cost and confounded by
whole-game variance). It gives a mechanism-level, on-policy hook at a price that makes a 30-pair
campaign a ~$10–17 decision, not a ~$60 one.

---

## Sources (verified in code at commit `4b1449e`, 2026-07-02)

- `Agents/graphs/parent.py::day_phase` (`:65-107`) — the day-entry `DayGraphState` payload (the §2
  contract, 13 keys).
- `Agents/graphs/day.py::build_day_graph` (`:40-98`) — the live day subgraph reused in §1.
- `Agents/nodes/day/flow.py` — `route_speaker`/`day_scheduler` (`:36-86`, `cycle_seed` call at `:63`),
  `fan_out_vote`/`allow_abstain` gate (`:192-200`), `route_after_day_summary` pre-voting-day `END`
  (`:279-288`), `summarize_day_discussion` (`:203-276`).
- `Agents/nodes/orchestrator.py::day_resolution` (`:147-242`) — the plurality/no-lynch rule (§4) to
  factor out; `initialize_game` (`:55-115`) for the survivor-bucket / `roles` shape;
  `one_more_day`/night-death stamping context.
- `Agents/turn/scheduler.py::cycle_seed` (`:17-23`) — `zlib.crc32(f"{game_id}:{day}:{cycle}")`, pure &
  replayable (§1 seed determinism).
- `evaluation/src/replay/retrieval.py::build_store_from_snapshots` (`:49-101`) — per-arm store
  reconstruction (§2 store row).
- `evaluation/src/core/stats.py` — `mcnemar_exact` (`:93-114`), `wilcoxon_paired` (`:117-129`) (§4).
- `evaluation/src/loop/decision_scoring.py` — `score_vote` (`:48-63`), `no_lynch_streak_before`
  (`:73-82`), `allow_abstain_for` (`:85-96`) (§2, §4).
- `Agents/game_config.py::GameConfig` — `utterance_cap` (multiplier 3; `cap(9)=27`),
  `first_voting_day=2`, `discussion_recursion_limit`, `abstain_enabled`, `no_lynch_force_after=2` (§1, §5).
- Data shapes confirmed against `batch_results/ab_arms_town.jsonl` (a frozen-store `ab_*` batch) and
  its sidecar `batch_results/eval_cases/ab_arms_town_town_only/<game_id>.jsonl` — batch top-level keys
  (`day_channel`, `day_summaries`, `day_resolutions`, `night_resolutions`, `investigator_results`,
  `roles`, `eval_cases_path`; **no** `vigilante_results`, **no** `human_player`), sidecar
  `agent_action_eval` nesting `output.eval_case.private_context.{surviving_*, previous_strategy,
  investigator_results, vigilante_results}`, and night-death announcements stamped `day=k-1`.
