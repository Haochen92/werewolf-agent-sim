# Hardening Pass — journey log

> **What this is.** The chronological record of the 2026-07 eval-instrument hardening pass: an
> independent review of the four methodologies the memory-design conclusions rest on, the code
> changes that review drove, and the re-runs and verdict re-assessments that followed. Later
> entries supersede earlier ones. Companion docs: the reliability ledger
> ([`../source_map.md`](../source_map.md)), the eval-chapter hub ([`../report.md`](../report.md)),
> and — once the pass concludes — a verdict-first `report.md` in this folder.
>
> **Review surface.** Code changes from this pass are reviewable as `git diff` against `4b1449e`
> (the commit the review ran on) side-by-side with this log; each beat names its files. Nothing is
> committed until the human review; commits then land in dependency order, one logical group each.
>
> **Provenance.** Review ran at `4b1449e` on `feature-dimension-schema`, 2026-07-02. The approved
> execution spec is the plan file (session-local); everything load-bearing from it is restated here
> so this folder is self-contained. Implementation was delegated to subagents working from that
> spec; each beat cites the implementing agent's report.

## §1 · Motivation — why harden now

The store-progression conclusions (`../../memory_system/store_progression.md`) — static memory
helps town (the v5_0 anchor), retrieval precision is not the lever (v6_1), compounding is open
(v7) — rest on four measurement methodologies. The consolidation review (`../source_map.md`,
verify-in-code pass 2026-06-28) had already tagged several instruments as unverified or
uncalibrated, but the tags were passive: nothing had been *fixed*, and no test had been re-run on
a hardened instrument. The gap this pass addresses: before the design verdicts are frozen into the
portfolio write-up, harden the tools those verdicts came from, re-run only the tests whose verdict
depended on an un-hardened tool, and update the verdicts where they move. The four methodologies:

1. **Screen/decision replay** — cheap per-turn A/B on frozen decisions, used to pre-screen changes
   before paid game runs.
2. **Proxy metrics + the day tagger** — the de-lucked outcome proxies that carry the signal where
   win-rate is underpowered (MDE ≈36pp at N=30).
3. **Sampled human + pro-LLM review** — the ad-hoc case-reading that made most qualitative calls.
4. **The v6 dimension schema** — the structured situation fields (including agent-state
   dimensions) that retrieval gating and the criticality screens depend on.

## §2 · The independent review — findings that drove everything below

A fresh code-and-evidence read (three parallel code-readers over the replay harness, the
metrics/tagger layer, and the v6 schema), deliberately re-deriving rather than trusting the
existing reliability tags. Findings ordered by how much they changed the plan.

### §2.1 The v6 dimensions are LLM-filled and were never audited against ground truth (new finding)

Every dimension is filled by an LLM at both extraction time
(`evaluation/src/experiments/reextract_cells.py:186-201` copies the extractor's numerics straight
into the store) and query time (`Agents/memory/enrichment/situation_agent.py:71-114`). No tool
compares any filled value to ground truth — even where deterministic truth is computable from the
board (`players_alive`, `distance_to_parity`, `is_swing` via
`criticality_screen.py::query_criticality`; `bullets_left` and `ally_revealed` from the game
record). The one guard that exists (`Agents/memory/validators.py::coerce_consensus_direction`) is
a prose-keyword check, not a truth check. This is load-bearing: production dimension gating
(`Agents/memory/retrieval/dimension_gating.py`) gates on `players_alive`(bucketed) / `is_swing` /
`exposure_class` / `info_landscape_class`, and the gating and criticality screens returned
~0/negative. If the fills are inaccurate, those screens tested noise, and their nulls are
**uninformative rather than negative** — a different conclusion than the one currently recorded.
A $0 deterministic audit distinguishes the two worlds (§Phase 1 beat, pending). Data fact that
makes the audit possible: query-side `situation_dimensions` are persisted only in the loop-era
sidecars (`batch_results/{town_only_run1,town_only_run2,v2_full,legacy}`, ≈9k filled objects,
nested as `output.eval_case.situation_dimensions`); the ab_*/v6ab_* sessions predate the v6 query
path and carry none.

### §2.2 Replay coverage is thinnest exactly where the open questions live

The per-turn replay screen is validated (converges with the paired A/B) but cannot replay the
deceiver side: wolf day-votes are excluded (`evaluation/src/loop/decision_scoring.py:31`,
`REPLAYABLE_TOWN_ROLES` = villager/healer/investigator) and `ACTION_SPECS`
(`evaluation/src/replay/application.py:33`) lacks vigilante and serial-killer day-vote specs. The
two open scientific questions — wolf memory and compounding — sit on the side the screen can't
see. Additional defects: `_select_diverse` round-robins earliest decisions first, so pooled
day-3+ aggregates are early-weighted; the lexical echo proxy does not track the judge it proxies
(Spearman rho=0.14) and was never formally retired.

### §2.3 The tagger path fails silently, and its validation evidence is stdout-only

The v7 credit signal rides the discussion tagger, and three failure modes are silent:
`_tag` catches all exceptions and returns empty `DayTags` with only a warning
(`evaluation/src/loop/discussion_tagger.py:251-253`); a missing eval-cases sidecar silently
degrades role_claims/private_reads; and the tag cache is keyed `(game_id, version)` only, which
already caused one cross-arm cache hit ("scored OFF with ON tags"). Separately, the tagger's
validation — the partial r ≈ +0.56 wolf / +0.60 SK vs win, the number that makes it a trustworthy
deceiver metric — exists only as stdout from `evidence/v7_final/v2_full/tagger_skill_retest.py`
plus one experiment-log section; the load-bearing scripts write no artifact.

### §2.4 Known-but-unfixed instrument bugs, and wrong-sign proxies pushed co-equal

Two items the 06-28 verify-pass flagged were still unfixed: the retrieval judge's `<2 items`
short-circuit sets efficiency to the maximum and silently pools those rows into judged averages
(arm-asymmetric, since thin arms return ≤1 item more often — `evaluation/src/judges/retrieval.py`);
and `push_scores_to_langfuse` (`Agents/compute_metrics.py:519-550`) pushes all ~50 metric fields
co-equal, including `investigator_found_wolf_day`, which validates *significantly wrong-sign*
(+0.38 — later finds correlate with wins because of game-length confounding). One drift surface
has no detection at all: the embedding alias can move silently, which would quietly deflate
retrieval and invalidate dedup thresholds; the proposed canary-pairs check was never built.

### §2.5 What the review deliberately did NOT re-open

The town proxy basket re-verified as the trustworthy core (point-biserial vs win at N=50/180).
Wolf day-offense being unmeasured by a deterministic proxy is a *finding*, not a tooling gap: the
clean lead-vs-blend build was run and was null, with a strong datum (109/169 mislynch days had no
wolf among the accusers — town mislynches itself), and the tagger is the validated instrument for
wolf discussion skill. The sampled-human-review gap was confirmed exactly as documented in
[`../sampled_human_review/report.md`](../sampled_human_review/report.md); its existing plan is
sound and is executed in this pass rather than redesigned.

### §2.6 The resulting plan

Seven phases, with hardening gating spend: **P0** cheap instrument fixes (no LLM cost) → **P1**
the $0 dimension-accuracy audit with a pre-registered confirm/re-open decision rule → **P2**
application-judge calibration (before the sampler, because the sampler selects on judge outliers)
→ **P3** the diagnosis-sampler build + a semantic dimension spot-check → **P4** a ~$3–5 wolf
replay screen → **P5** priced re-runs, each gated on the phase that hardens its instrument
(town-only loop rerun ~$65; wolf-direct A/B ~$60–70; conditional gating re-screen ~$10–15) →
**P6** a per-day replay design doc (design only) → **P7** re-assess the design verdicts.

---

## §3 · Phase 6 — per-day replay: design doc (done 2026-07-02)

Done first because it is documentation-only and shares no files with Phase 0. The motivating gap
(§2.2, and the decision-replay evidence's own "open frontiers" list): the per-turn screen is
off-policy and structurally blind to within-day trajectory effects, and nothing replays a full
day. The review established feasibility — the batch game record already carries the whole ordered
`day_channel`, full vote resolutions, night resolutions, and configs, and the sidecar carries
every turn as an EvalCase — so the design was specced rather than built, per the pass's
design-only scope for this item.

**Artifact:** [`../../memory_system/effectiveness/day_replay/design.md`](../../memory_system/effectiveness/day_replay/design.md)
(marked DESIGN — NOT BUILT). Core design: replay day k≥2 of a recorded game through the live day
subgraph, on-policy within the day, frozen prefix; hard-fail state-reconstruction asserts; source
from memory-OFF recordings so the off arm is on-policy by construction; deterministic day-level
scoring, paired per (game, day); ≈$0.10–0.15 per day-replay (~20–30% of a full game). The
acceptance gate is the honest part: an unchanged-condition replay of 10–15 game-days must be
statistically indistinguishable from the recorded days before any A/B spend, and the measured
self-agreement becomes the harness's cited noise floor.

**Corrections the code-verification forced on the design** (assumption corrections, surfaced per
the style guide): `vigilante_results` is sidecar-only, absent from the batch record top level
(the spec's contract table splits its source from `investigator_results` accordingly);
`utterance_cap` is `max(min, ceil(3·N))`, not the ~25-at-9-players first estimated (dollar figures
survive, the constant is corrected); night deaths are stamped with the *concluding* day's number,
so the naive `day < k` prefix filter is correct but only for a non-obvious reason, now documented.
Open design questions flagged in-doc: the plurality/no-lynch rule is inline in `day_resolution`
(entangled with state mutation) and must be factored into a pure shared helper when the harness is
built; store re-embedding drift is bounded but not eliminated by the frozen-store restriction and
should be wired to the embedding-canary check from Phase 0.

---

## §4 · Phase 0 — instrument fixes (done 2026-07-02)

Ten fixes, all motivated by §2 findings; no LLM spend. Suite went 405 → 413 passed (8 new tests,
zero regressions). Reviewable as the `git diff` slice touching the files named per item. Each item
below leads with the problem, then the fix, per the journey-log discipline.

**4.1 Retrieval-judge fallback rows biased judged averages (§2.4).** The `<2 items` short-circuit
returned synthetic efficiency=5 rows that pooled silently into averages, inflating thin arms. Fix:
`RetrievalScores` gained `is_fallback` (`evaluation/src/core/schemas.py`), the short-circuit sets
it, and `summarize_records` (`evaluation/src/experiments/retrieval.py`) now excludes fallback rows
from every judged average and reports `fallback_rows=N`. *Catches:* `tests/test_retrieval_judge_fallback.py`
proves the average is 2.00 where the old pooled math said 4.00. Tradeoff: fallback rows carry no
signal at all now (rather than a corrected value) — acceptable because a synthetic score is worse
than a smaller N, and the count keeps the asymmetry visible.

**4.2 Tagger failed silently (§2.3).** `_tag`'s swallow-all left a failed day contributing zero
tags with only a warning. Fix (`evaluation/src/loop/discussion_tagger.py`): per-day failures are
collected and summarized as an end-of-game `logger.error`; a new `strict` param re-raises; a
missing `eval_cases_path` now warns loudly once per game (role_claims/private_reads degrade there).
*Catches:* `tests/test_tagger_inputs.py` forces an exception and asserts the counter + `strict`
re-raise.

**4.3 Tag-cache could serve one arm's tags to the other (§2.3).** The `(game_id, version)` key had
already caused a cross-arm hit once. Fix: a session/trace slug is folded into the cache filename
AND a `provenance` field is stored in the record and asserted on read; a mismatched record re-tags
fresh instead of returning foreign tags. Legacy files without provenance stay trusted because the
slug already partitions them. *Catches:* same test file — cross-arm non-collision, mismatch → re-tag,
match → hit.

**4.4 The tagger's validation numbers had no artifact (§2.3).** `tagger_skill_retest.py` and
`tagger_deleak_ablation.py` (frozen evidence scripts in `evidence/v7_final/v2_full/`) now
additionally write `*_results.json` next to themselves; statistics logic untouched, and they were
not re-run (paid) — the artifacts appear on next execution.

**4.5 Deceiver decisions were not replayable (§2.2).** Fix: `ACTION_SPECS`
(`evaluation/src/replay/application.py`) gained vigilante and serial-killer day-vote/discussion
specs; `evaluation/src/loop/decision_scoring.py` gained `REPLAYABLE_DECEIVER_ROLES` and
`wolf_vote_is_good` (the deceiver lens: a vote that induces a town mislynch, the mirror of town
`hit_threat`); `run_causal` in `decision_replay.py` takes a `--lens {town,wolf}` flag so a wolf/SK
run scores on its own win condition. **Assumption corrected:** the night-kill replay the plan
listed as an open frontier was already fully wired (`_replay_night` + `NIGHT_SPECS` + `--night`) —
only the day-vote side was actually missing.

**4.6 Day-sampling artifact (§2.2).** `_select_diverse` was rewritten to round-robin across days
(seed-deterministic), removing the day-2-first weighting that early-loaded pooled aggregates.

**4.7 Echo proxy retired (§2.2).** `_echo`/`run_echo_consideration` are marked deprecated and warn
on use; kept functional only so the rho=0.14 invalidation stays reproducible. Dated retirement
note appended to `evidence/memory_system/effectiveness/decision_replay/experiment_log.md`.

**4.8 Wrong-sign proxies pushed co-equal (§2.4).** `Agents/compute_metrics.py` gained
`DO_NOT_USE_METRICS` (the five wrong-sign/broken proxies, led by `investigator_found_wolf_day`)
and `VALIDATED_BASKET_METRICS` (the eleven trusted ones); the Langfuse push renames DNU metrics
with a `dnu_` prefix and tags every score with its tier. Deliberately minimal — no GameScore class;
the tiering is a guardrail, not the deferred scoring redesign.

**4.9 Embedding drift had no detection (§2.4).** New `evaluation/src/core/embedding_canary.py`:
12 fixed domain pairs, pinned similarities in `embedding_canary_pins.json` (generated live, sims
0.70–0.91), `check_embedding_canary` re-embeds at batch start and raises `EmbeddingCanaryDrift`
beyond epsilon 0.02. Wired default-on into `scripts/run_batch.py` (`--skip-embedding-canary` to
opt out); a missing fixture warns and skips rather than blocking. This converts the one silent,
undetectable drift surface (§2.4) into a loud crash.

**4.10 Sidecar shape documented.** The `output.eval_case.<field>` span-wrapper nesting and the
loop-era-only availability of `situation_dimensions` are now stated in
`evaluation/src/data/sources/sidecar.py` and `evaluation/README.md` — the misread had already cost
one analysis a false "field is empty everywhere" conclusion.

*Ops note for future runs:* single-file test invocation needs `poetry run python -m pytest`
(no conftest; bare `pytest <file>` can't import the packages).

---

## §5 · Phase 1 — the v6 dimension-accuracy audit: RE-OPEN fired (done 2026-07-02)

The §2.1 finding put to the test: recompute deterministic truth for every LLM-filled query-side
dimension in the loop-era sidecars and compare. Suite 413 → 421 passed. Full design, pre-registered
decision rule, and interpreted tables live in the audit's own log —
[`../../extraction/situation_dimensions/dimension_accuracy_audit/experiment_log.md`](../../extraction/situation_dimensions/dimension_accuracy_audit/experiment_log.md)
— this beat records the verdict and what it changes.

**What was built.** `evaluation/src/experiments/dimension_audit.py` ($0, deterministic; the paid
`--regen` arm exists but hard-refuses to run pending spend sign-off); `query_criticality` lifted
from the criticality screen into `evaluation/src/loop/decision_scoring.py` as the shared truth
home; 8 unit tests over the truth functions. Coverage: 6,267 dim-filled cases across
town_only_run1 (25.9%), town_only_run2 (24.7%), v2_full (42.2% — the only run with wolf/SK dims);
the 5 `legacy` smoke runs predate dimension capture and are excluded, stated rather than skipped.
The ~25–42% rates are the structural ceiling (dims fill only on the memory-ON retrieving side),
not missingness.

**Results, split by what the agent could know.**

| Dimension | Epistemic class | Accuracy | Read |
|---|---|---|---|
| `players_alive` | agent-knowable | 0.970 exact / **0.990 bucket** | sound — the gate's primary key held |
| `ally_revealed` | agent-knowable | 0.975 | sound |
| `bullets_left` | agent-knowable | **0.164** | broken — systematically under-counts; day-2 accuracy 0.0 |
| `is_swing` (wolf side ≈ true) | ~true accuracy | **0.606** | **worse than a constant** — always-False scores 0.827 on a 0.173 base rate |
| `is_swing` (town side) | vs-omniscient | 0.469 | conflated with epistemic limit; not separately damning |
| `distance_to_parity` | vs-omniscient | 0.05–0.09 exact, MAE ≈2 | unusable as an exact key (matches its default-off status) |

**The verdict: RE-OPEN.** The rule pre-registered before the run said RE-OPEN if any gated
dimension fell below 0.80. Alive-bucket passed at 0.990, but wolf-side `is_swing` at 0.606 fired
the condition (the enum-kappa clause stays pending Phase 3, and cannot rescue a CONFIRM). Mean
gated-dim error ē≈0.202 implies the gate's alignment tilt was attenuated to ≈0.60 of its nominal
strength. So the recorded dimension-gating null is **partly uninformative, not a clean content
verdict**: the gate keyed on one reliable dimension, one anti-informative one, and two enums no
one has validated. This authorizes the ~$10–15 gating re-screen with deterministic
`players_alive`/offline `is_swing` substituted in — spend not yet approved, and it must run before
any prompt surgery on the enums.

**A truth-computation catch, kept in place per the no-laundering rule.** Wolf `night_action` cases
persist an empty `surviving_players` roster (176 cases); the first pass scored fills against a
bogus roster of 0 and manufactured a wolf +2 over-count. The runner now counts these as
`no_roster` and skips criticality truth there; corrected wolf `players_alive` = 0.97. The RE-OPEN
verdict was unaffected, but the episode is itself evidence for the audit's premise — a
deterministic checker is only as good as its own inputs, and it earned one bug fix before its
first real read.

**What this does and does not say.** It audits the *query* side, where the board moment is pinned.
Stored-side extraction fills pass the weak internal-consistency bounds 100% on v6_1, which bounds
nothing tightly; their real check is the Phase 3 sampled review. The criticality *screen* is
untouched by the `is_swing` result on its query side (it computed truth deterministically) — the
re-opened verdict is specifically the *gating* screen's, plus the general lesson that
`players_alive` should be `len(surviving_players)` and never an LLM fill (3% wrong for no reason),
and `bullets_left` should come from the game record.

---

## §6 · Fill fix — agent-knowable dims computed, not LLM-filled (done 2026-07-02)

The §5 structural corollary, green-lit as a $0 item (the paid re-screen stays held). Suite
421 → 431 passed (10 new tests). Detail section lives in the audit's own log
([`../../extraction/situation_dimensions/dimension_accuracy_audit/experiment_log.md`](../../extraction/situation_dimensions/dimension_accuracy_audit/experiment_log.md) §6).

**The change.** At query time, after the situation LLM returns, `situation_agent.py` now
overwrites the agent-knowable dimensions from game state before dims and embeds are composed:
`players_alive` from the living roster, `bullets_left` from the vigilante's counter,
`ally_revealed` from pack-size vs initial wolf count. `distance_to_parity`/`is_swing` stay
LLM-filled — they need true roles the live agent cannot see (their offline substitution belongs to
the held re-screen). A debug log records every override that changed a value, so future runs
measure residual LLM fill error for free.

**Two payload facts the fix surfaced (assumption corrections).** First, `players_alive` was never
a plain `len(surviving_players)`: single-actor night payloads exclude the actor (off-by-one), and
wolf payloads carry no role-blind roster at all — the helper self-corrects via a membership check
plus a wolf branch. This retroactively explains part of the LLM's 3% error as a *payload
ambiguity*, not pure model sloppiness. Second, the vigilante's day payload dropped the bullets
counter entirely (it rides a `VillagerDayState`), so `vigilante_bullets` had to be threaded
orchestrator → `DayGraphState` → day-payload builders; `initial_wolf_count` reaches the wolf
payload as a scalar count only, so the private-info leak boundary is untouched.

**Scope guarantees verified.** The numeric dims carry no embed marker, so the override changes
only the gating filter input — composed embed strings and retrieval matching are unchanged.
Stored records are untouched (query-time only; future queries benefit). Named residual: the LLM's
prose (`criticality_stakes`) is derived from its own possibly-wrong numbers and is not re-derived,
so corrected numerics can disagree with prose in the same object — accepted rather than spending a
second LLM call per turn; flagged in code.

---

## §7 · Phase 3 (build half) — the diagnosis sampler exists (done 2026-07-02)

Rung ② of the modality ladder gets its apparatus (§2.5; spec = the pre-existing
[`../sampled_human_review/plan.md`](../sampled_human_review/plan.md)). Built at $0; suite
431 → 445 passed (14 new tests). The spot-check that *uses* it (the enum-kappa half of the §5
decision rule) needs ~2h of human labeling and stays pending.

**What was built.** `evaluation/src/diagnosis/sampler.py` + thin runner
`evaluation/src/experiments/case_sampler.py` (console entry `eval-case-sample`, registers on next
install). Selection combines three channels: deterministic score-outliers (decision scores via
`score_vote`/`score_night_target`, lensed per faction), a deterministic leverage anchor
(`query_criticality` from the frozen board — never the LLM fill, citing §5's worse-than-constant
`is_swing`), and a stratified background cohort via `data/sampling.py` (seed-deterministic).
Judge-score outliers exist as an opt-in channel and every such case is flagged `(uncalibrated)` —
the Phase-2 ordering constraint honored in code rather than by procedure. The halo rule is
enforced, not advised: `assert_outcome_blind` raises on any outcome-named signal, verified against
the real `winner` field. Replay is wired but refuses to run (paid; same guard discipline as the
audit's `--regen`). Verdicts persist to a durable JSONL; each case renders as a human-readable
review packet.

**Smoke result (real data, read-only).** A 9-case cohort from `ab_nh_town`: 3 outlier / 3
leverage / 4 stratified; roles and phases mixed; byte-identical strata across two same-seed runs.
Artifacts under [`../sampled_human_review/sampler_smoke/`](../sampled_human_review/sampler_smoke/).

**One deviation from the spec, disclosed.** The plan's "flag every `is_swing` case" anchor
selected 126/143 cases on real data — late game is structurally pivotal, so an all-swing anchor
floods the handful and stops being a second axis. The anchor is now top-K nearest-parity
(`--n-leverage`), which keeps leverage combinable with the other channels. This is a spec
refinement forced by data, not a scope change.

---

*(Remaining beats — the held paid items and Phase 7 verdict updates — are appended if/when they run.)*

## Sources

- Review inputs: [`../source_map.md`](../source_map.md) (reliability ledger + 06-28 verify-pass),
  [`../report.md`](../report.md), [`../../memory_system/store_progression.md`](../../memory_system/store_progression.md),
  the per-modality spokes under `../llm_judge/` · `../labeling/` · `../sampled_human_review/`.
- Code read at `4b1449e`: `evaluation/src/experiments/decision_replay.py`,
  `evaluation/src/replay/*`, `evaluation/src/loop/{decision_scoring,discussion_tagger,credit,measure}.py`,
  `evaluation/src/judges/retrieval.py`, `Agents/compute_metrics.py`, `Agents/schemas/memory.py`,
  `Agents/memory/{enrichment/situation_agent.py,retrieval/dimension_gating.py,validators.py}`,
  `evaluation/src/experiments/{criticality_screen,forced_schema_screen,dimension_gating_screen,reextract_cells}.py`.
