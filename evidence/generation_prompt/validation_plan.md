# Validation plan — dead-roster board + alive-roles + suspicion read list

> **What this is.** The pre-registered test suite for the §9 board-state additions to the
> generation prompt ([experiment_log.md](experiment_log.md) §9): the dead-roster block, the
> alive-roles line, and the suspicion read list with per-read `why` (all three SHIPPED 2026-07-09 —
> see the status table). Written **before** the build completed, so every probe commits to its expectation in
> advance; where a probe's outcome forced a change to the plan itself, the amendment is made **in
> place, dated, with the original left visible** — the plan's honesty is that its predictions can
> be seen failing. Results append to the journey log as §§10–12's verify→decide beats; all scripts,
> case files, and result docs colocate in [`validation/`](validation/).
>
> **Gating logic.** T1-baseline and T4 run first (cheap — a few dollars of reader calls — /
> build-time). T2 and T3 share one paired replay batch. **Ship-blockers: T2's regression tripwires and T4.** T1-improvement and T3 grade
> the *instrument* — they inform iteration, not shipping.
>
> **Status (2026-07-09).**
>
> | probe | status | result |
> |---|---|---|
> | T1 baseline | ✅ ran 2026-07-07; re-instrumented + re-run 2026-07-08 | [validation/hallucination_baseline.md](validation/hallucination_baseline.md) — premise revises UP |
> | T1b counterfactual replay | ✅ ran 2026-07-07 | [validation/t1b_results.md](validation/t1b_results.md) — expectation falsified, informatively |
> | T2 non-regression | ✅ ran 2026-07-07 | [validation/t2_results.md](validation/t2_results.md) — PASS, no tripwire |
> | T3 replay stage (a/b + ordering A/B) | ✅ ran 2026-07-07 | same file — instrument viable; `reads_first` ships provisionally |
> | T1c pre-ship A/B replay (run 1 + escalation run 2) | ✅ ran 2026-07-08 | [experiment_log.md](experiment_log.md) §12 — **pre-registered pooled primary CONFIRMED on 100 fresh contexts: 48%→30%, p=0.0032** (run 1: directional, pooled post-hoc p=0.010; effect replicated across independent samples) |
> | T4 harness checks | ✅ built 2026-07-09; smoke-validated same day | leak check `check_reads_isolation` in the boundaries suite (needle law redesigned after smoke false-positives — see the T4 amendment); enumeration + monitor-only 0.85 tripwire in `Agents/turn/decision.py`; legacy `EvalCase` records load (reads + board inputs captured on new cases); full suite green |
> | T5 epoch bookkeeping | ✅ with the build 2026-07-09 | `prompt_bundle_hash` auto-bumps (it hashes `Agents/prompts/*.py`, which the bundle edits); the schema-side change (reads fields in `output.py`) is covered by git SHA only — the known gap stands. **Epoch break: records generated from 2026-07-09 are a new prompt epoch; never compare across it.** Proxy-basket diff parked with the post-ship batch |
> | T1-improvement rate re-measure · T3 live scoring · read-feedback dynamics · scheduler effects · T5 basket | ⏳ parked | piggyback on the first post-ship batch — never a dedicated run; T1-improvement protocol + expectations pre-registered under T1 below |
>
> **Shipped 2026-07-09.** The validated bundle (dead-roster board + alive-roles line + reads list,
> `reads_first` order) is live in the generation pipeline for day discuss/vote + the four
> single-actor night roles. Wolf-night turns stay unchanged — they were outside the tested surface
> (no single-decision template); extending the board there is a post-ship candidate, arbitrated by
> the parked night re-measure (the 9.6% night-note cell).

---

## T1 — Role-hallucination baseline → improvement check

*Catches: is the board's premise real — do agents actually misstate role facts today — and does
the board reduce it?* The premise was face-valid, never measured; a board justified by an
unmeasured problem is a board that can't be judged.

**Method: a four-stage detection pipeline.** Each stage does only what it can do reliably, so a
parser is never asked to judge meaning and an LLM is never asked to guarantee recall.

1. **Find every text that touches a checkable fact.** Deterministic anchors flag any unit that
   names an entity or states a count the structured game record can contradict: a dead `player_N`,
   a role word whose holders are all dead, an explicit count claim, or a claim-attribution. The
   screen covers both public chat and private `updated_strategy` notes, because a false private
   belief drives votes and night targets as directly as a public one. Anchoring on entities and
   counts — closed sets that can be matched exhaustively — makes candidate recall provable by
   construction for any hallucination that names a dead entity or states a count. Anchor-less
   fabrications (pronoun references, invented events naming no id or role word) are out of scope by
   design.
2. **Throw away only what is provably fine.** Drop game_master messages (rendered from state, they
   cannot hallucinate) and count claims that match the true alive count. Nothing is dropped on
   position or phrasing, since a wrong recap of the GM is itself an error class.
3. **A cheap LLM reads the rest against a fact sheet.** Each surviving candidate is judged against a
   deterministic fact sheet built from the game record — deaths with revealed role, day, and
   attacker; alive players and per-role counts; public vote records; logged role-claims; and the
   speaker's own first-hand knowledge. No transcript is sent. A speaker-knowledge check separates a
   strategic lie (deliberate_deception, public messages only) from a genuine hallucination.
   Calibrated on a golden set, the reader runs as a cascade: a cheap model reads everything as the
   recall layer, a stronger model re-reads its positives as the precision layer.
4. **A human checks the LLM's positives and a sample of its negatives.** All public positives are
   read; the private positives and a sample of the reader's rejections are sampled to set precision
   and the miss rate.

Each confirmed case is tagged **day vs night**: the board ships day-only, so the night share of
hallucinations directly decides whether the night prompts need the block too.

**Code home (user call, 2026-07-07): the screen is a standing audit, the reader a graduated judge.**
Both recompute over game records and re-run on any relevant batch. The screen lives at
`evaluation/src/audits/role_hallucination_screen.py` (zero-LLM, honoring the audits package
contract) with an `eval-role-hallucination` console entry; the reader lives at
`evaluation/src/judges/role_fact_read.py` with an `eval-role-hallucination-read` console entry.
Their outputs are the evidence artifacts here
([validation/hallucination_baseline.md](validation/hallucination_baseline.md) plus the candidate and
verdict `.jsonl` files), each pointing back at the code per the store-the-pointer rule.

**Datasets.** All 50 `v2_full` games in both paired arms (epoch 2026-06-22, closest to the current
prompt bundle). Reported per-epoch, never pooled.

**T1b — counterfactual case replay (the cheap causal stage).** Before any fresh-batch rate
comparison: **decision-replay each confirmed baseline case** with the dead-roster block added to
its otherwise-identical frozen input (the roster derives deterministically from the game record).
Same context, one variable — does the misstatement persist? This buys case-level causal evidence
at about one LLM call per case. **Pre-registered decision rule:** persistence rate per class;
classes 1–3 should collapse under the board; class 4 needs the claims anchor, not the board. The
population-level check — the same screen + read on a fresh batch — piggybacks on the first
post-ship batch, never a dedicated run.

> **Outcome (T1 census re-run 2026-07-08; T1b 2026-07-07):** T1's re-instrumented census
> **revises the premise upward** — role-fact hallucination is common once private reasoning is in
> scope: ≈3.0% of public messages and ≈4.0% of private notes carry a role-fact error, with
> night-action notes the worst surface at ≈9.6% (direct evidence for extending the board to night).
> Re-verification also refuted one of the old manual baseline's four cases as an arm mix-up; three
> stand (see the census report). T1b then **falsified the collapse expectation** — the one recurring
> case survives an explicit correct board. The board ships as cheap hygiene, not a measured fix; the
> read list inherited the hypothesis and T3(b) gained a composition-coherence metric. Full story:
> [validation/hallucination_baseline.md](validation/hallucination_baseline.md) and
> [experiment_log.md](experiment_log.md) §10.

**T1c — pre-ship A/B decision replay at census scale (pre-registered 2026-07-08, before the run).**
*Catches: does the new prompt bundle causally reduce hallucination on the inputs where it happens —
before any live game is paid for?* This is T1b's method with its power problem fixed: T1b had 4
cases and no per-case power; the census supplies hundreds, so the aggregate paired rate is a real
statistic at one sample per case. **Design (minimal, escalation pre-registered):** 60
composition-class census positives (stratified public message / private note / night) + 20 matched
anchored-but-consistent controls, each regenerated from its frozen input (sidecar memories and
previous_strategy, NOT cold) under two arms — `old` (generation-era prompt, no board) vs
`new_bundle` (dead roster + alive-roles line + reads_first schema with enumerated read targets) —
k=1, ~160 generations. Outputs are judged by the standing census reader cascade; the metric is the
**arm-vs-arm paired hallucination rate**, never flip-vs-original (T2's lesson: original-comparison
is noise-dominated at temp 1.0). Controls check the new bundle does not *induce* errors on clean
turns. **Expectations:** the board content alone should not collapse composition (T1b); the reads
commitment is the live hypothesis, and replay is turn-cold on read feedback, which biases *against*
the reads arm (cold reads were lazier in T3) — so a reduction here is conservative evidence, and a
null is ambiguous rather than damning. **Decision rule:** clear reduction (paired discordants
one-sided, sign test) → ship-confidence rises and the live smoke confirms; muddy → escalate by
adding the next 60 cases before concluding; reversal on controls (new arm induces errors) → block
and diagnose. Selection-on-positives makes this an error-prone-context rate, not a population rate;
the population claim stays with T1-improvement below.

**T1c escalation run (pre-registered 2026-07-08 — after run 1's results, before run 2 executes).**
Run 1's positives-only primary came out directional (p≈0.08), and its controls collapsed into a
second error-prone stratum (35% old-arm error rate on regeneration — context predicts error, not
the original output's luck). Per the escalation rule, run 2 tests the reformulated hypothesis on
**fresh cases only, none reused from run 1**: primary = the **pooled paired hallucination rate over
all sampled error-prone contexts** (composition positives and anchored-but-consistent controls
alike; ~60 + ~40), old vs new_bundle, k=1, one-sided sign test at α=0.05. Expectation: a reduction
comparable to run 1's pooled 45%→28%. Run 1's pooled number stays labelled post-hoc; run 2's is
confirmatory by construction because the metric was fixed before its data existed.

**T1-improvement — the post-ship rate re-measure (parked; pre-registered 2026-07-08).** Runs on
the first post-ship batch (the T5 smoke or the first live batch with the board and reads live) —
never a dedicated run. Method: the standing census, unchanged — `eval-role-hallucination` then
`eval-role-hallucination-read --stage2-from` over the new batch records, with the reader's golden
gate re-checked once on the new epoch before its verdicts are trusted. **Comparison discipline:**
the new rates are reported per-epoch and set beside the v2_full census, never pooled — this is a
descriptive before/after across an epoch break (the whole prompt bundle changes, not just the
board), so it grades the release, not any single block. The causal per-case evidence stays T1b's
job; if a causal rate claim is ever needed, it takes a paired board-on/off arm batch.
**Pre-registered expectations:** (a) the board alone should NOT collapse the composition class —
T1b showed the recurring composition error survives an explicit correct board — so composition
persisting is not a failed release; what would move it is the read list binding beliefs, which
T3(b)'s composition-coherence metric arbitrates; (b) the night-board extension targets the
census's worst number, the ≈9.6% night-action-note rate — this is the single cell with the most
headroom and the clearest attribution; (c) no prediction is registered for the attacker-typed
roster (its motivating case was refuted; it rides as free information). **Decision rule:** nothing
gates on this (the changes are already live when it runs); it decides iteration — whether the
night board stays, and it feeds the live re-arbitration of the reads ordering.

## T2 — Non-regression via decision replay: strategy application must survive the added fields

*Catches: attention dilution on flash-lite.* The known failure shape — "one row per memory
degrades as memory count grows" — now applies with 8 forced reads plus whys sitting *before* the
verdicts' consumers in the schema. If the added material dilutes the verdict machinery §6 built,
the ship is blocked.

**Method: paired decision replay, not full games (user call, 2026-07-07).** The obvious design —
run paired full games old-vs-new — measures the wrong thing: games diverge after the first changed
turn, so every later decision compares mismatched inputs. Replay holds the frozen decision input
fixed and varies only the schema bundle — the same methodology that produced the §6 reorder
evidence, on the graduated `evaluation/src/replay/decision_screen/` engine. Sample ~100–200
decisions from `v2_full` records, stratified by role × phase (discuss/vote/night), each replayed
old-schema vs new-schema (+ the deterministically derived dead-roster block in the new arm;
prior-reads input runs **cold** — see the parked items). Compare per pair:

- **verdict coverage** — verdicts emitted / memories shown; the 0.97 stat (§6) must hold
- **follow / override / not_relevant distribution** — no collapse to a degenerate bucket
- **verdict→action coherence** — `follow` on an SP advising X → action consistent with X; the
  paired action-flip rate old-vs-new is the headline drift number
- **schema validity** — parse-retry rate, missing-field rate
- **actual output-token cost per call** — the read list + whys are the dominant add; measure it,
  don't estimate it

**Decision rule:** any coverage or coherence collapse, or a parse-rate spike, blocks the ship. The
paired design is what makes N≈100 decisions statistically real — each comparison is matched at the
decision (McNemar-style), not averaged across different games.

**Parked for the first live batch — replay structurally cannot see these:** the read-feedback
accumulation dynamic (frozen records hold no prior reads, so replay is always turn-one-cold),
`pass_turn`/scheduler-coupled effects, and T5's game-level proxy basket.

**Artifacts:** [validation/regression_replay.py](validation/regression_replay.py),
[validation/t2_results.md](validation/t2_results.md).

> **Outcome (2026-07-07):** PASS on every tripwire — coverage ~1.0 in all arms, zero parse
> failures, board token-free, reads +60% output tokens. One method lesson recorded: flip-vs-original
> is noise-dominated at temp 1.0 (the *unchanged* arm flips ~50%), so the next replay design needs
> same-arm resample pairs before between-arm flips can be read. [experiment_log.md](experiment_log.md) §11.1.

## T3 — Reads instrument validation (soundness + consistency)

*Catches: are the reads and whys real judgments, or decorative fields the model fills to satisfy
the schema?* Three layers on the same replay/smoke data:

**(a) Reads vs ground truth.** At reveal: accuracy / Brier vs true roles, **knowledge-masked** —
wolf packmates and investigator-checked players are excluded from skill scoring, because those
reads test honesty, not skill. They are used instead as **golden probes**: a wolf's read on its
packmate must be correct and high-confidence, or the field is junk. Degeneracy checks:
`unclear`/`low` share, per-player entropy, herding (read ≈ room consensus). The reference bar is
the cast-prior baseline forecaster (guess the cast composition), not zero — beating zero is free.

**(b) Reads ↔ strategy ↔ action coherence — and the ordering question.** A deterministic partial
check (names and role words extracted from `updated_strategy`, compared against the read list; the
vote target should sit among the agent's worst reads) plus a sampled read of disagreements.
**Amendment, post-T1b (2026-07-07): a composition-coherence metric** — the rate of composition
claims in the message/strategy that contradict the agent's own committed reads. T1b showed passive
board text does not stop "remaining wolf" reasoning; the live hypothesis is that a forced
per-player commitment does, and this metric is what tests it.

**Schema order ships as verdicts → reads → `updated_strategy` → action** — evidence before plan,
the commitment lever measured twice (§3, §6 of the journey log); strategy-first risks the reads
becoming post-hoc justification of a plan already written. Because that rationale is an inference
from past reorders rather than a measurement of *this* schema, the order is also tested: an
**ordering A/B** runs as a third replay arm on T2's sampled decisions (same frozen inputs,
reads-first vs strategy-first), with (b)'s coherence metrics deciding.

**(c) The whys.** A distinct-ratio screen (boilerplate detector), `unchanged`-sentinel honesty
(the share of `unchanged` whys whose enum actually changed — should be ≈0), and a sampled
grounding read (does the why cite something that happened; investigator whys must cite their
checks). Whys are inspected, never scored into credit — agents confabulate rationales, so valence
stays on the enum vs ground truth.

**Artifacts:** [validation/regression_replay.py](validation/regression_replay.py) (shared with
T2), [validation/t2_results.md](validation/t2_results.md); live-batch scoring
(`reads_scoring.py`, Brier-vs-cast-prior, full knowledge masking) is parked with the live items.

> **Outcome of the replay stage (2026-07-07):** instrument viable — golden probe 9/9,
> non-degenerate, accuracy above blind random; completeness 0.85 became its own thread (see T4).
> The ordering A/B split rather than crowned: `reads_first` triples SP override, `reads_after`
> writes better reads; `reads_first` ships provisionally, re-arbitrated in the live smoke via the
> composition-coherence metric. [experiment_log.md](experiment_log.md) §11.1.

## T4 — Harness checks (build-time, blocking)

- **Leak test.** Reads, whys, and private board variants must never reach another agent's payload
  or the transcript — a new `check_*` in the agent-boundaries suite. Payload construction is the
  system's only enforced privacy boundary, so this is where the check belongs.
- **Completeness — one read per living non-self player.** The policy here was revised twice as
  evidence arrived; the sequence is kept visible:
  - *As pre-registered:* monitor completeness; no enforcement mechanism specified.
  - *Post-T2 (superseded):* the replay found completeness 0.85 with a selective-omission
    signature, and the first decision was a hard parse-time validator with a retry naming the
    omitted players.
  - *Final policy (user call, 2026-07-07), superseding the validator:* two follow-up probes
    re-decided it. Dynamic enumeration — the instruction line itself lists the expected targets
    via a derived `read_targets` key (surviving minus self, filled in
    `build_agent_prompt_input`, never hard-coded ids) — lifts completeness 0.85 → 0.93; an
    importance check showed the residue is harmless (agents essentially never act on an unread
    player, and misses skew toward nothing-to-say villagers). So: **(a) enumeration ships,
    (b) missing reads are imputed at analysis time as `unclear/low` (cast-prior for Brier),
    (c) completeness is a monitored metric with a ~0.85 tripwire, (d) no content retry.** The
    standard transport/parse retry layer (429s, schema-invalid) is separate and stays. The named
    trade: a ~7% soft denominator in exchange for zero added latency and no re-generation cost.
- **Schema mechanics.** The all-required schema compiles; legacy records still load.

> **Outcome (built with the ship, 2026-07-09):** all three checks landed as specified.
> `check_reads_isolation` (whys as scan needles, `unchanged`/short needles skipped) joined the
> boundaries suite and the per-game batch leak gate; the completeness tripwire logs (never retries)
> below 0.85 against the same enumeration the prompt shows; legacy `EvalCase` records load, and new
> cases capture the reads AND the board inputs (`dead_roster` + `cast_role_counts`) so a frozen
> case reproduces the exact prompt without rejoining the game record. Tests:
> `tests/test_player_reads.py`; full suite green.
>
> **Amendment (2026-07-09, post-smoke): the leak check's needle law was wrong — redesigned.** The
> first live smoke (2 memory-on games) tripped the gate on every game; forensics traced **every hit
> to shared vocabulary, zero real leaks** — one-line whys like "confirmed healer" also live in
> public discussion, in retrieved store memories from other games, and in the author's own strategy
> note, so a bare substring scan cannot attribute them. The check is now two-pass: **(1) structural
> (primary)** — any prompt_input containing a rendered read-object token (`suspected_role`, a
> `reads` key) is a leak, which is the realistic template/formatter regression; **(2) prose
> (secondary)** — only whys ≥40 chars, only against OTHER players' prompts, and only when the why
> does not itself occur in the game's public text (channel + summaries). The smoke's false-positive
> classes are pinned as regression tests. Instrument note from the same smoke, for T3's live
> scoring: **wolves hedge packmate reads during discussion turns** (1/7 honest) but are honest at
> vote time (2/2) — the golden probe should be scored on vote/night turns.

## T5 — Epoch bookkeeping (documentation, not a test)

A new `prompt_bundle_hash` is stamped, and the smoke's proxy basket (win rates, vote accuracy,
game length) is diffed old-vs-new and *documented* — not gated on. The reads are a
chain-of-thought effect and may legitimately change play; that is an epoch break to record, not a
regression to block on. (Known gap, inherited from the provenance mechanism: output schemas live
outside `Agents/prompts/`, so schema changes are covered by the git SHA only, not the bundle
hash.)

---

**Execution order.** T1-baseline first ($0, existing records) → T4 with the build → one
decision-replay batch feeds T2 + T3 + T1b + the ordering arm (no full games required) → the parked
live items (read-feedback dynamics, scheduler effects, T5 basket, T1 rate re-measure) piggyback on
the first post-ship batch.

*Pre-registered 2026-07-07; amendments dated in place (T3(b) composition-coherence, T4 completeness
policy); status table and prose legibility revised 2026-07-08; T1 instrument upgraded and census
re-run 2026-07-08 — expectations and decision rules unchanged. Bundle shipped to the live pipeline
2026-07-09 (T4 built, T5 stamped); only the parked post-ship items remain open. Results narrative:
[experiment_log.md](experiment_log.md) §§9–12.*
