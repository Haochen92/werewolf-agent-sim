# Play-quality metrics: the working record

*This is the full trust write-up of every play-quality score as it stood on 2026-10-23: Part A, the nine-seat
de-lucked basket as written in June–July 2026 with its dated corrections, and Part B, the ten scores added in
October, each with its code paths, line numbers and records. The plain summary is [report.md](report.md),
written 2026-10-24 from this text; sections cited elsewhere as "metrics B3" or "B5" are here. The design
record of the nine-seat proxies (how they were built, all 48 candidates, the July audit logs) is
[`../../metrics/`](../../metrics/README.md).*

*Widened 2026-10-23 to play-quality scores generally. Added the ten-seat game's metrics and decision grades, the read Brier score, vote-target accuracy, the leverage anchor, the discussion structure counts, the balance counts, and two prompt-claim checks. The nine-seat de-lucked basket, the spoke's original subject, is kept below as written in June–July 2026, with dated corrections.*

**What this page covers.** Scores that code works out from a saved game record to say how well the
agents played. Examples are the share of votes that hit a real threat, a grade for each decision, a
score for how right a player's guesses were, and counts of who won. No AI model is needed to work
them out, so they cost nothing and give the same answer every time.

There are six groups:

1. **The nine-seat basket** (June–July 2026, nine-seat game). Do these per-role scores go up when
   that side wins? They are "de-lucked": each counts chances taken out of chances given, not raw
   totals, so luck matters less.
2. **Ten-seat metrics and decision grades** (October 2026, ten-seat game). For the live game, did
   each role's action do what the rules say it should, and was each decision good, neutral or bad
   according to the owner's table?
3. **Read and vote scores.** Did players' guesses about who holds which role turn out right (the
   read Brier score, nine-seat July 2026 and ten-seat October 2026)? Did votes land on a real threat
   (both games)? Does a measure of how much is at stake on a turn pick out the turns that decide the
   game (the leverage anchor, June 2026, nine-seat)?
4. **Counts used to judge prompt and rule changes** (October 2026). What does day discussion rest
   on, how did each speaking-order design behave, and which side wins under each rule set? The first
   two use nine-seat games and the balance games are ten-seat.
5. **Checks of advice in the prompts** (June 2026, nine-seat). Does the wolves' "blend your vote"
   tactic go with winning, and did the investigator's wolf find reach the village?
6. **The batch summary.** Win rates and averages of each score for one batch of games.

For each score the page says how it is worked out, what it can and cannot claim, how far it was
checked, and where its code and record are. This page rates **how far each score can be trusted**.
It does not re-argue what any design found. Those results stay in the evidence folders named in each
section. Checks that give only a pass or fail with no score, such as the speaking-order and
failed-attack audits, are in [deterministic_audits](../deterministic_audits/report.md). How all the
evaluation reports fit together: [the hub](../report.md). Where each claim comes from:
[the source map](../source_map.md). The code and record for every score are listed in the Sources
table at the end.

"Validated against win" below means a test showed that games with a higher score are games that
side won more often.

| Check | Trust | Main limit |
|---|---|---|
| Nine-seat basket: town scores (Part A) | ✅ | Validated against win on the nine-seat game only |
| Nine-seat basket: investigator scores (Part A) | 🟡 | Only "finds turned into lynches" is validated |
| Nine-seat basket: wolf and serial killer scores (Part A) | ⚠️ | Serial killer only partly covered; wolf day attacks not measured |
| Nine-seat basket: town discussion (Part A) | 🟡 | One supporting score only; none for wolf discussion |
| Ten-seat metrics and decision grades (§B1) | ⚠️ | Exact counts, hand-checked on one game, never validated against win |
| Read Brier score (§B2) | 🟡 | Exact, but only two confidence levels, most reads "unclear", not validated against win or a person |
| Vote-target accuracy (§B3) | ✅ as a count | Validated against win on the nine-seat game only |
| Leverage anchor (§B4) | 🟡 | Nine-seat town day votes only |
| Discussion census, Phase 2 step 8 counts, balance batches (§B5–B7) | ✅ as exact counts · 🟡 as readings | 4–31 games each, one model |
| Blend-tactic check (§B8) | 🟡 | A trend only (p=0.07) |
| Investigator transmission (§B9) | ⚠️ | Keyword matching, not meaning |
| Batch summary (§B10) | none of its own | Each number is only as good as the score it averages |

**Bottom line.** The most trustworthy scores are still the nine-seat town basket. The live game is
ten-seat, and no play-quality score has been validated against win there. The code reflects this:
it labels no score "validated" when it sends scores to Langfuse, the project's tracing dashboard.

## Objective the apparatus targets

A win/loss outcome is too lucky and too coarse to rank skill at N=30. The metrics layer replaces it with **de-lucked outcome proxies** (opportunity-conditioned rates) — but a proxy is only useful if it actually tracks winning. The validation harness exists to prove that.

*(2026-10-23.)* Since October 2026 most play-quality work has not been a memory A/B. It has been prompt and rules changes judged on a few games: Phase 1–3 of the day discussion, the ten-seat cast, balance and persona voices. Those changes need scores that are cheap, exact and repeatable, even when the sample is too small to validate them against win. The added sections below catalogue those scores. They keep two questions apart. Is the count exact? Usually yes, because code reads it from the record. Does the count mean good play? Usually not shown.

---

## Part A — the nine-seat de-lucked basket (written June–July 2026)

### L1 — the instrument

- **Compute surface** `Agents/compute_metrics.py`: `_compute_base_metrics` (raw counts) → `_compute_derived_metrics` (de-lucked rates) → `compute_game_metrics` → `ComputedGameMetrics`, a **63-field flat artifact** (`schemas/metrics.py:214-256`). `push_scores_to_langfuse` (`:519-550`) pushes **every non-None field indiscriminately** — no curated-basket filter, so unvalidated/diagnostic/plumbing fields land in Langfuse co-equal with validated proxies.
  - *Correction (2026-10-23):* `ComputedGameMetrics` now has 84 fields, at `Agents/schemas/metrics.py:254`. `push_scores_to_langfuse` is at `Agents/compute_metrics.py:741`. The "indiscriminate" push was replaced by the tiering described two bullets down.
- **Validation harness** `evidence/metrics/proxy_win_monotonicity.py` + `core/stats.py::point_biserial`: per-proxy point-biserial r vs that proxy's **own faction's win**, expected sign from a design-intent table; reads existing `batch_results/*.jsonl` (zero new games); reported twice (pooled N=50 + memory-OFF-only N=30, because the memory treatment moves both proxy and win). The 3-faction refinement re-ran the same discipline at N=180. `point_biserial` returns NaN on degenerate inputs (<3 rows / constant proxy / single-class).
  - *Correction (2026-10-23):* the harness was promoted on 2026-07-04 to `evaluation/src/instrument_validation/proxies/proxy_win_monotonicity.py` (`instrument_validation/README.md`). The `.py` file is no longer in `evidence/metrics/`; the dated record is `evidence/metrics/proxy_win_monotonicity.md`. Its siblings in the same package are `proxy_rescue.py`, `proxy_followup_rescue.py`, `accusation_metrics.py`, `claim_conversion.py`, `diagnose_wolf_sk_proxies.py` and the shared loader `metrics_common.py`.
- **`score_tier_design` (the typed GameScore projection): still NOT BUILT** — markdown design only; no `class GameScore`. But a **minimal trust tiering shipped 2026-07-02** as a guardrail short of the full projection: `Agents/compute_metrics.py` now carries `VALIDATED_BASKET_METRICS` (11 point-biserial-checked proxies), `DIAGNOSTIC_METRICS` (3 audit-graduated, context-not-basket), and `DO_NOT_USE_METRICS` (5 wrong-sign/uninterpretable); `push_scores_to_langfuse` renames the DNU set with a `dnu_` prefix and tags every score with its tier. So a *validated wrong-sign* proxy can no longer be silently averaged into a verdict. The full GameScore projection (which would stop the `suspicion_drawn`↔`blending` double-count *by construction*) remains the deferred apparatus upgrade.
  - *Correction (2026-10-23):* still no `class GameScore` in the repo. Since the ten-seat port (October 2026), no score is tagged "validated". `_metric_tier` (`compute_metrics.py:731`) returns "validated" only for names in `VALIDATED_ON_TEN_SEAT_METRICS`, which is empty. Every other score pushes as "diagnostic", and the `dnu_` set as "do_not_use". The code says why: live games are ten-seat, and the basket was validated on the nine-seat game (`compute_metrics.py:725-728`; plan `memory_system/v8/plan.md` §8.4). `VALIDATED_BASKET_METRICS` still lists the 11 nine-seat-validated proxies. It now records what was validated, and the push no longer reads it.

### L2 — trust, per basket

**Town — ✅ VALIDATED (the trustworthy core).** `correct_elimination_rate` +0.65, `town_mislynch_rate` −0.65, `serial_killer_lynched` +0.64 (n=50) / +0.85 (n=30), `town_vote_accuracy` +0.62, `mislynches` −0.57 — all |r|≈0.55-0.65, p<0.01, **in both pooled and OFF-only views**; reconfirmed at N=180. The only unambiguously validated basket.

**Investigator — 🟡 PARTIAL.** The find-*rate* proxies are **NOT validated** — `threat_find_rate` −0.09, `wolf_find_rate` −0.14, and `investigator_found_wolf_day` **+0.38, p=0.039 — significantly WRONG-SIGN** (later find ↔ more wins, plausibly game-length-confounded; not length-normalised). N=180 confirms the dead floor (find rates ~0). What rescues the channel is **conversion**: `investigator_find_to_lynch_rate` +0.396, p<0.001 — VALIDATED. (So old v5-pilot investigator claims rest on unvalidated proxies — hypothesis only.)

**Deceiver (wolf/SK) — ⚠️ SPLIT.** *Validated:* `sk_power_roles_killed` +0.323, `sk_kill_rate` +0.258 (raw +0.61 is survival-confounded → de-lucked), `sk_wolf_kills` +0.303 partial|survival (has a mechanism), `wolf_unconditioned_blending_rate` +0.270. *Tautology shipped-with-caveat:* `suspicion_drawn` (SK −0.714) is **outcome-proximate** (votes-at-SK is its only removal path) AND **opponent-coupled** (it's `town_vote_accuracy` from the other seat — one event, never two pieces of evidence); the in-code comment carries the caveat. *Unmeasured:* wolf **night-offense null** (+0.104, n.s.), **day-offense unmeasured** (`wolf_steering_rate` can't tell leading a bandwagon from joining it). The wolf's biggest win-correlate is `sk_lynched` +0.455 — the town removing the SK, an environmental event, not a wolf action.

**Discussion (metrics-proxy) — 🔴 NULL / DEFERRED.** Phase-1 `wolf_lead_score` r=−0.093 (p=0.51, n=53) — NULL but *cleanly*: lead-vs-blend is a genuinely distinct signal (decorrelated from vote metrics), the infra works, but active wolf offense carries no win signal and barely happens (127/180 games had no wolf accusing the eventual mislynch target). Phase-2 LLM tagger deferred. **NOT the v7 loop tagger** (which is built).
- *Correction (2026-10-23):* the v7 loop's discussion tagger has fed no credit since 2026-07-13, and it is out of the write-up (`../llm_judge/discussion_tagger.md`). The town side gained a diagnostic proxy on 2026-07-02 (the dated section below). The wolf side still has no validated proxy.

**Cross-cutting L2:**
- **Multiple-comparison exposure:** ~30 proxies tested vs win, **no built-in Bonferroni**; the docs apply it by hand where it bites (e.g. `sk_unconditioned_blending` +0.196 p=.019 flagged SUGGESTIVE, fails a ~12-test Bonferroni). The monotonicity doc explicitly says "ranks proxies by trustworthiness; not a causal claim."
- **Small-N degeneracy on the wolf basket at N=50** (`wolf_blending_rate`/`dissent_rate` NaN — wolves won 2/30 OFF); the N=180 refinement is what gives the wolf/SK figures power.
- **Tautology discipline applied** (survival↔win for `sk_nights_survived` +0.555; the de-lucked `sk_kill_rate` is the skill-bearing replacement). Good apparatus hygiene.
- *(2026-10-23)* **Every number in this part is nine-seat.** The figures come from June–July 2026 batch records (`v6ab`, `ab_*`), played on the Gemini models of that time. On a ten-seat game, 21 of these metrics (`NINE_SEAT_ONLY_METRICS`, `compute_metrics.py:580`) are set to None and recomputed from the night record. The serial killer's three counts are None when the game dealt a necromancer instead (Part B1).

### Verdict + cheapest upgrade

Per the table at top. **Cheapest *trustworthy* upgrade:** not re-running the starved wolf day-offense channel (Phase-1 already ran it null at n=53), but **graduating the two NEW validated proxies that already exist in code but sit outside any tiered basket** — `investigator_find_to_lynch_rate` (+0.40) and `power_roles_killed_by_evil` (−0.40) are computed and validated but the indiscriminate push gives them no priority. The cheapest *apparatus* upgrade is **building the `GameScore` projection** (currently design-only), which stops the Langfuse/judge double-counting of `suspicion_drawn`↔`blending` and survival↔kill-rate twins **by construction**.

- *Correction (2026-10-23):* both proxies are in `VALIDATED_BASKET_METRICS` (`compute_metrics.py:698-710`), so that upgrade is done. The cheapest upgrade now is to re-run the same point-biserial discipline on ten-seat records. Plan §8.3 names the memory-off seeding games as the data for it. That run is $0, but at dozens of games it could only show large correlations. It has not been run.

### Evidence (code + L2 artifacts)

- **Code:** `Agents/compute_metrics.py`, `Agents/schemas/metrics.py`, `evaluation/src/core/stats.py`, `../../metrics/proxy_win_monotonicity.py`, `../../metrics/design/discussion_lead_vs_blend.py` (both **point at** the canonical `core/stats.py`, not copied).
  - *Correction (2026-10-23):* the first `.py` now lives at `evaluation/src/instrument_validation/proxies/proxy_win_monotonicity.py`. `../../metrics/design/discussion_lead_vs_blend.py` is still in place.
- **L2 artifacts (pointed-at):** `../../metrics/{proxy_win_monotonicity,experiment_log}.md` + `../../metrics/design/{town_metric_refinement,deceiver_metric_refinement,score_tier_design,discussion_scoring_plan}.md` — the validation docs are a **shared hub** referenced from 6 other evidence folders (point-at, per the "store the pointer" rule).

### Colocation call (JIT, 2026-06-28)

**Stays put — pointed-at.** The validation docs are a shared cross-folder hub; moving them breaks 6 inbound refs. (Note: `variance_reduction_levers.md` was **mis-filed** in metrics/ — it's A/B *methodology*, not a metric; the deferred relocation was executed 2026-07-07 and it now lives at [`../experimental_controls/variance_reduction_levers.md`](../experimental_controls/variance_reduction_levers.md).)

*(Inspected 2026-06-28. source_map metrics claims verified accurate; sharpenings folded into the ledger.)*

### 2026-07-02 metrics-audit update (proxy rescue/discovery + structural-bias falsification)

A $0, zero-LLM audit re-ran the incumbent validation discipline on N=180 v6ab (with split-half confirmation and pre-registered signs) to probe the basket's *holes* rather than its errors. Full logs + per-candidate verdicts stay in `evidence/metrics/metrics_audit/` (pointed-at, not copied): [`proxy_discovery_log.md`](../../metrics/metrics_audit/proxy_discovery_log.md) (workstream 1) and [`scheduler_bias_log.md`](../../metrics/metrics_audit/scheduler_bias_log.md) (workstream 2). What moved:

**Deceiver (⚠️→ one diagnostic added).** `wolf_power_kill_rate` is the **first wolf-night proxy to clear the bar** — but only once conditioned on the environment. Pooled it is null (+0.13, n.s.); the mechanism is that wolves *cannot win when `sk_lynched=0`* (the SK wins by default), so 77/180 games carry zero wolf-skill information yet dilute the flat correlation. Within `sk_lynched=1` (n=103, 39 wolf wins) it is **+0.31 (p=.002)**, split-half stable (+0.26 / +0.38) and robust to partialling out both `sk_lynched` and `game_length` (+0.190, p=.011). This reframes the earlier "wolf night-offense doesn't convert (−0.10)" as a **not-conditioned-on-the-SK-axis artifact**, not an absence. Adopted **diagnostic**, not basket-promoted (pending a larger wolf-win N). Corollary: *the flat point-biserial is structurally miscalibrated for wolf proxies* — any wolf null in the older refinement docs should be re-read as "diluted," not "absent."

**Discussion (🔴→🟡, town side).** `town_accusation_precision` (town accusations on true threats / all) is the **first town-discussion proxy**: **+0.34 (p<.001)**, both halves p≤.002, Bonferroni-passing. **Accepted as diagnostic, not independent evidence** — it couples with the already-validated `town_vote_accuracy` at r=+0.558 (~31% shared variance), so it re-expresses the "town IDs threats" construct on the discussion surface rather than confirming a good town twice. The metrics-side wolf lead-vs-blend proxy *stays 🔴 null* — and the audit sharpened *why*: `wolf_accusation_on_town_rate` was pre-registered **+** (framing offense should help wolves) and came back **−0.33 (p<.001, both halves)** — a **pre-registered sign FALSIFICATION**. Wolves that attack town lose more; wolves that accuse real threats win more, the blending mirror of the validated `wolf_unconditioned_blending_rate` (+0.27). Only the pre-registration makes that a legible finding rather than a silent flip.

**Investigator (🟡, unchanged verdict, softened rationale).** The v5 scare — `investigator_found_wolf_day` **significantly wrong-sign** (+0.38, p=.039, n=30) — **dissolves at N=180 to +0.15 n.s.**; neither length-normalizing nor partialling `game_length` pushes it to the expected negative. So the sign confusion was **small-N noise plus mild length coupling, not a robust backwards relationship**. The find-rate cluster stays quarantined (`dnu_`), but the rationale downgrades from "significantly wrong-sign" to "null; the earliness sign is N-fragile." Only the conversion proxy (`investigator_find_to_lynch_rate`) is validated, now joined by the confirmed timing refinement `investigator_find_next_round_convergence` **+0.31 (both halves)** — adopted diagnostic, transmission-cluster. A related program is **BLOCKED**: claim-conditioned joins need `DaySummary.structured.role_claims`, present in **0/180** v6ab and 0/50 v5 (an A4 addition postdating both epochs) — unbuildable until a post-A4 batch is itself win-validated.

**The nulls are NOT scheduler artifacts (structural-bias falsification).** A sibling workstream tested whether the role-blind discussion scheduler *starves* the behaviors these proxies measure. It found **no floor-starvation**: investigator and wolf are the floor-*richest* roles (turns/alive-day 2.45 and 2.04; investigator spoke-zero rate 0.10), pending-find investigators speak before the vote **58/58 (100%)**, wolves hold pre-bandwagon proactive floor on **76.5%** of pile-on days (and decline 35% of proactive offers), and the 12 unconverted investigator finds decompose to **0 no-floor / 0 late-floor** vs 7 withheld / 5 revealed-but-ignored. So the wolf-steering null and investigator non-conversion are **agent/town behavior, not scheduler-shaped**. One question stays open: the novelty gate's role-selectivity is **unmeasurable from existing records** (a gated pass and a voluntary pass write the identical marker) — the 2-field instrumentation to fix it shipped, so a future gate-selectivity audit is unblocked on new records only.

**The whiff-visibility finding (prices a held game-design change).** When a wolf's night-kill hits the night-immune SK, the kill *silently whiffs* — and the wolf **never notices 68% of the time** (vs 31% on an *announced* heal; the wolf's noticing rate tracks visibility). The vigilante, handed an explicit immune note, converts the whiff to day-action **0.75–0.89 from a ~0 base**. So the binding layer is **visibility, not wolf skill or scheduler floor** — evidence that supports (does not decide) the held change to disclose failed kills to the wolf, priced honestly at an epoch reset. Relevant to metrics because `sk_lynched` (+0.455) is the wolf's biggest win-correlate and is currently an *environmental* event, not a wolf skill.

**Adoption + tiering (shipped).** The three survivors (`wolf_power_kill_rate`, `town_accusation_precision`, `investigator_find_next_round_convergence`) were adopted into a **`DIAGNOSTIC_METRICS`** tier beside — not inside — `VALIDATED_BASKET_METRICS`, pushed with `tier="diagnostic"` and carrying their caveats as attribute docstrings (A2's `sk_lynched` conditioning, B1's r=+0.558 coupling, C1's refinement status). The `dnu_`-prefixed `DO_NOT_USE_METRICS` (the investigator find-rate cluster + `wolf_steering_rate`) keep them out of any silent average. Basket promotion of the diagnostics remains pending a larger wolf-win N. All $0/zero-LLM, ran at `4b1449e`. Label caveat carried forward: the accusation graph rides `addressed_targets` self-labels (tuned for scheduling, not measurement), whose error rate as measurement input is still uncharacterized.

- *Correction (2026-10-23):* this paragraph first cited test counts. They are dropped here because the tests in `tests/` are largely AI-written and unaudited. The logic is pinned in `tests/engine/test_diagnostic_metrics.py` and `tests/evaluation/test_metrics_audit_proxies.py`, which shows where it is checked, not that it is right. On the label caveat: in October 2026 the speakers' accusation tags agreed with an independent LLM judge on 145 of 183 agent messages (79%), and missed an accusation on 24 of 183 (13%) (`game_play_enhancement/discussion_evidence.md` §7.1). That compares the tags with an uncalibrated judge, not with a human. The scheduler access audit and the whiff conversion audit (`evaluation/src/audits/{scheduler_access_audit,whiff_conversion_audit}.py`) are now catalogued in `../deterministic_audits/`.

*(Update inspected 2026-07-02 from the metrics-audit logs; findings verified against `proxy_discovery_log.md` §3 and `scheduler_bias_log.md` §3 + the tiering constants in `Agents/compute_metrics.py`. Diagnostic-tier, not basket-promoted — the trustworthy core is unchanged.)*

---

## Part B — play-quality scores added 2026-10-23

Each section gives what the score is, how it is computed, what it can and cannot claim, how far it was checked, and where the code and the record are. They are ordered by how much current work leans on them.

### B1. Ten-seat game metrics and decision grades (October 2026, ten-seat) — ⚠️

**What they are.** There are two scorers for the ten-seat game, both deterministic.
- **Per-game metrics.** `Agents/ten_seat_metrics.py` recomputes the 21 nine-seat-only metrics from each night's full record. That record holds every choice, what the rules made of it, and each actor's result. Sides come from the role registry, not from role names. The module also adds proxies for the new roles:
  - Chanteuse blocks: real, critical and wasted.
  - Illusionist conceals: landed, and landed while hiding a town role's record.
  - Necromancer: nights survived.
  - Speculator: pick night, picked side, and whether it won.
  - Fortune Teller: points.
  - Sentinel and Trailseer: results that named an evil visitor.
  - Sigilist: hits.
- **Per-decision grades.** `Agents/memory/consolidation/grading.py` grades one decision as positive, neutral or negative, or leaves it unscored (None). It follows the owner's table (`memory_system/v8/plan.md` §9.6 item 10; the reasons are in `decisions.md` §12). Credit uses the grades. So does `scripts/grade_observations.py`, which grades the decision each extracted observation names.

**How they work.** `compute_game_metrics` (`Agents/compute_metrics.py:612`) treats a game with no `wolf` role as ten-seat and sets the 21 nine-seat-only fields to None. If every night carries its full record, it then fills them from that record. Games recorded from 2026-10-11 on do (`has_night_records`). The port was needed because the nine-seat code read per-role night fields that a ten-seat game never fills. Those metrics read 0 even when the event happened, "every one of 28 ten-seat balance games, 2026-10-11" (code comment, `compute_metrics.py:575-579`). Metrics landed in `e5763cd1` (2026-10-11), grades in `d9141ce2` (2026-10-13).

**What they can claim.** What the engine recorded, exactly and reproducibly: a block cancelled a town action, a bet scored, a decision matched the table's "good" row.

**What they cannot claim.** That any of these numbers tracks winning or skill.
- None is validated against win on the ten-seat game. `VALIDATED_ON_TEN_SEAT_METRICS` is empty, so every one pushes as "diagnostic". The nine-seat validations "do not carry over" (plan §8.3).
- The grade table is a ruling. It encodes what the owner judged ideal, neutral or undesirable for each turn kind. The code can match the table exactly; whether the table rewards good play is a separate question no one has tested.

**How far checked.**
- The metrics were checked by hand against one pilot game (`decisions.md` §8).
- The table's rows are pinned in `tests/memory/test_ten_seat_grading.py`. Those tests are AI-written and unaudited. They show the code follows the table, not that the table is right.
- One sanity read: on the 12 memory-off seeding games the mean grades "look as the rules predict". The Fortune Teller is at −0.60 because most bets miss, the Sigilist at −0.35, and the pack's kill at +0.42 (`memory_system/v8/experiment_log.md`, 2026-10-13).
- Coverage: grades reached 1,711 of the 2,277 observations from 40 games. An observation goes ungraded when it names no single decision, when its decision is unscored, or when a served game's wire cannot rebuild the result (same log).
- The grades serve as the reference in the verdict-halo study (`../deterministic_audits/experiment_log.md` §5d), which treats them as truth. That study measures the extraction verdict against the grades, not the grades themselves.

**Code · record.** `Agents/ten_seat_metrics.py`, `Agents/memory/consolidation/grading.py`, `scripts/grade_observations.py` · `memory_system/v8/{plan.md §8.1–8.4 and §9.6, decisions.md §8 and §12–13, experiment_log.md 2026-10-13}`.

### B2. Read Brier score (nine-seat July 2026; ten-seat October 2026) — 🟡

**What it is.** Before each decision a seat writes a *read* of each other player. A read is a suspected role and a confidence ("high" or "low"), or "unclear". The Brier score measures how well committed reads match the roles revealed at game end. Each read scores (p − hit)², where p is 0.85 for high and 0.65 for low, and hit is 1 if the suspected role is the true role. Lower is better. "Unclear" reads make no claim. They are left out of the Brier and reported as an unclear rate. A read the seat already *knows* is masked out (the *knowledge mask*), so the score measures inference, not private information.

**How it works.** There are two implementations.
- `evaluation/src/loop/read_ledger.py` (nine-seat, from 2026-07-09 records on). Its mask drops a wolf's reads on packmates and the investigator's reads on players it has checked. Its side accuracy uses the nine-seat threat set `{"wolf", "serial_killer"}`. Plan §8.4 lists it among the frozen nine-seat harness.
- A ten-seat re-implementation inside `evaluation/experiments/persona_voice_games_score.py` (October 2026), with sides from the role sheet. Its mask drops only a pack seat's read on a packmate. A seat's read on a player its own night result already named, such as an investigator's checked player, is scored as an inference.

Credit keeps read accuracy apart from lesson scores on purpose (`credit/report.md` §1 and §4).

**What it can claim.** Whether committed reads matched revealed roles, by role, phase and arm, on the same deals.

**What it cannot claim.**
- A calibration curve. Two confidence levels give a two-point check only (`read_ledger.py:28-30`).
- Much about most reads. In the 16 persona-voice games, 86.8% (voices off) and 87.3% (voices on) of reads were "unclear". The Brier rests on 1,105 and 973 committed reads.
- That a lower Brier means better play. It has not been tested against win or against a human's reading.
- Run on a ten-seat record, the nine-seat ledger would score sides with the nine-seat threat set without warning, so ten-seat work must use the re-implementation.

**How far checked.** Exact by construction. No validation against an outcome is recorded. Its one use as a headline: the persona-voice games, Brier 0.155 (off) and 0.129 (on), voices on better in 7 of 8 pairs, sign test p≈0.07, 8 pairs (`game_play_enhancement/data/persona_voice_games/README.md`).

**Code · record.** `evaluation/src/loop/read_ledger.py`, `evaluation/experiments/persona_voice_games_score.py` · `credit/report.md` §1, §4; `game_play_enhancement/data/persona_voice_games/`.

### B3. Vote-target accuracy (nine-seat and ten-seat) — ✅ as a count

**What it is.** A vote is right when it names a real threat. Three forms are in use:
- `town_vote_accuracy` in the per-game metrics (`compute_metrics.py:536`): the share of town votes that landed on a threat. Threats come from the registry's sides, so it computes on ten-seat games too. It is in the nine-seat validated basket (+0.62, Part A) and unvalidated on ten seats.
- `score_vote` / `hit_threat` in `Agents/memory/consolidation/decision_scoring.py` (eval callers import it through `evaluation/src/loop/decision_scoring.py`): one vote scored against the true roles. It is the measure in the frozen-turn replay screens. Its threat set is the literal `{"wolf", "serial_killer"}` (line 23), so it is nine-seat only. On a ten-seat record a vote on the Chanteuse would score as a miss.
- An exact target per day in `evaluation/experiments/haiku_vote_score.py`. For game 403f4dbc's replayed votes, the right answer for each day is written in the script (for example, player_6 the Illusionist on day 3). The vote field is limited to legal targets, so no judge is needed. Beside it the scorer counts evidence mentions with a regex. That is a mention count, not a judgment of soundness (its docstring). The replay itself is catalogued in `../evaluation_scopes/turn/`.

**What it can claim.** Whether the vote hit the threat. That is the outcome itself, so the count is exact.

**What it cannot claim.** Whether the vote was well reasoned on the information the seat had. A lucky vote counts as right, and a sound vote on a well-hidden threat counts as wrong. The nine-seat validation against win is the only evidence that the count tracks skill.

**Code · record.** As above · Part A; `game_play_enhancement/discussion_evidence.md` §8.7; `../evaluation_scopes/turn/`.

### B4. Leverage anchor (June 2026, nine-seat) — 🟡

**What it is.** A test of whether a deterministic measure of how much a board is at stake can pick out the decisive turns. The measure is `is_swing` and `distance_to_parity`, computed from the alive list and the true roles. Extraction selection and the case sampler lean on it.

**How it works.** `evaluation/src/instrument_validation/proxies/leverage_anchor_separation.py` uses town day-votes in 180 `v6ab` games. It computes P(town wins | vote hit a threat) − P(town wins | vote missed) within leverage strata. No model is called.

**Result and what it can claim** (`memory_system/v7/plan.md`, LEVERAGE-ANCHOR entry):
- The gap was flat across strata: +0.35 / +0.37 for `is_swing` true/false, and +0.35 / +0.41 for distance ≤1 and ≥3. So leverage does not rank votes by marginal impact.
- P(win | miss) fell from 0.23 to 0.00 at high leverage: a miss there was fatal. So the anchor separates do-or-die turns.

**What it cannot claim.** Anything about night actions or discussion, which the record says are untested. It is a stratified correlation with the outcome as the measure, on one nine-seat epoch.

**Code · record.** `instrument_validation/proxies/leverage_anchor_separation.py` (promoted 2026-07-04) · `memory_system/v7/plan.md`; `memory_system/v7/experiment_log.md` (the 2026-06-19 ruling on how extraction uses it).

### B5. Discussion census (October 2026, over nine-seat games of 2026-09-17) — ✅ counts · 🟡 labels

**What it is.** A free first look at what day discussion rests on, run before the discussion redesign.

**How it works.** `evaluation/experiments/discussion_evidence.py census` does two things.
- It counts the evidence label that the in-game day summary attaches to each accusation. The labels are voting record, behaviour pattern, communication style and concrete claim.
- It counts what needs no model: passes chosen by the player against turns skipped by the novelty gate, messages per day, and words per message.

Data: the 28 most recent games, four batches of 7, run 2026-09-17 at `e1a2e3dd` on `gemini-3.5-flash-lite`, memory off (`discussion_evidence.md` §2).

**What it can claim.**
- The structural counts are exact: 1,166 messages and 517 passes, of which 367 were the novelty gate.
- The label shares give a direction. Of 194 accusations, 47% rested on behaviour and 20% on a concrete claim.

**What it cannot claim.** Independent labels. The labels come from the same model that plays, and they are coarse. The record says so and sends the real measurement to the independent judge (`../llm_judge/experiment_log.md` §8).

**How far checked.** The record shows why counts of meaning need a read. A first keyword count said 32 summaries named a quiet player. Reading the matches found 4 of 124, because most hits were day-1 lines such as "no players are staying quiet yet" (§2.4). A random 25 of the "behaviour pattern" accusations were read by hand to see what the bucket held.

**Code · record.** `evaluation/experiments/discussion_evidence.py` · `game_play_enhancement/discussion_evidence.md` §2.

### B6. Phase 2 step 8 per-day counts (2026-10-07, nine-seat) — ✅ counts · 🟡 reading

**What it is.** Structural counts per voting day, used to compare day-discussion scheduler designs. The counts cover openings spoken, lines per day, reactive and sweep lines, lines held by the echo gate, closings run and whether the defended player was lynched, seconds per day, and model calls per day.

**How it works.** `evaluation/experiments/phase2_step8_capture.py` plays a game the production way and logs chunk arrival times and every model call. `phase2_step8_counts.py` counts from the record, the chunks and the call log. A count a baseline has no field for prints "n/a" and is never approximated. Calls per day are cross-checked against gate calls re-derived from the transcript. The two agree on every voting day of the four games but one, which was a retry (`data/phase2_step8_games/README.md`).

**What it can claim.** The mechanics: for example, 5 of 106 opening turns spoken across four games, and closings run on 7 of 12 voting days with the defended player voted out all 7 times (`data/phase2_step8_games/report.md`).

**What it cannot claim.** Rates. There are four games on `gemini-3.5-flash-lite`. In game 3, 36 of 115 successful calls went to the rescue model, and game 4 was played as its replacement. The evidence-judge labels in the same table come from the uncalibrated judge in `../llm_judge/experiment_log.md` §8.

**Code · record.** `evaluation/experiments/phase2_step8_{capture,counts}.py` · `game_play_enhancement/data/phase2_step8_games/{README,report,counts}.md`; `discussion_evidence.md` §7.3–7.4.

### B7. Balance batches (2026-10-09 and 10, ten-seat) — ✅ counts · 🟡 reading

**What it is.** Winners per batch of AI-only ten-seat games, used to set the role rules.

**How it works.** `evaluation/experiments/phase3_capture.py` plays and records each game. Each batch's folder holds a per-game table: drawn seats, winner, days, calls, cost and rescued turns. 31 games ran on `gemini-3.5-flash-lite`, memory off, two at a time (`discussion_evidence.md` §8.3).

**What it can claim.**
- Winners by rule set: 13–0 town in the first 13 games, then 3–3, 6–0 and 5–1.
- Exact counts the record states, such as "the pack aimed 34 of its 56 kills at the information roles".

**What it cannot claim.**
- That a rule caused a lynch. The record says "a preceding result does not prove the cause". The lynch-provenance counts are a hand reading of each game.
- Anything stable. Each batch is six games.
- Balance on today's model. The record states every reading is of flash-lite play, and that "balance has to be re-read on the model the live game uses" (§8.5 item 5). Live seats now default to Claude Haiku 5.5 (`Agents/llm_factory/accessors.py:24`). No balance batch on Haiku is in the record.

**Code · record.** `evaluation/experiments/phase3_capture.py` · `game_play_enhancement/data/phase3_{games,balance,balance_2,balance_3,balance_4}/`; `discussion_evidence.md` §8.3.

### B8. Prompt-claims audit: the wolf "blend your vote" tactic (2026-06-17, nine-seat) — 🟡

**What it is.** A check on whether a tactic written into the wolf prompt is true. It correlates the validated camouflage proxy `wolf_unconditioned_blending_rate` with wolf win.

**Result** (`generation_prompt/prompt_claims_audit/experiment_log.md`): pooled r=+0.164, p=0.070, n=122. Wolves won 38% at high blend against 25% at low blend. This is consistent with an earlier r=+0.20, p=0.003, n=220. The baseline-only slice (n=22) flips sign and is underpowered.

**What it can claim.** A trend in the tactic's favour, leaning on the earlier larger sample for significance.

**What it cannot claim.** Cause. The record says both tested claims are correlational, since blending could co-move with game state.

**Code · record.** `evidence/generation_prompt/prompt_claims_audit/blend_claim_test.py`. This is study code kept inside the evidence folder as a dated artifact; it reuses `evaluation/src/core/stats.py::point_biserial` · the same folder's `experiment_log.md`.

### B9. Investigator transmission (June 2026, nine-seat) — ⚠️

**What it is.** A per-game measure of whether the investigator's confirmed wolf read reached the village. The flags are `has_wolf_read`, `claimed` (named the wolf with a claim word), `vague_mention` (named it without one), `voted`, `transmitted` (claimed or voted) and `removed` (that wolf lynched later).

**How it works.** `evaluation/src/studies/investigator_transmission.py` reads batch records only. "Claimed" is a keyword match: the wolf's name plus one of "wolf", "confirmed", "investigated" or "scanned".

**What it can claim.** A bracket on transmission. In the v6 strategy-point A/B, the investigator voted the confirmed wolf about 100% of the time, asserted it about 33–67% of the time, and the wolf was removed after a confirmed read about 60–67% of the time in every arm (`memory_system/effectiveness/v6_sp_ab/experiment_log.md` finding 5).

**What it cannot claim.** Whether a message actually asserted the read. A keyword match cannot judge meaning, and the record calls the analysis "lexical/qualitative (judge-confirmation pending)". The script's docstring also warns that `transmitted` is post-treatment, so its cross-tab with win is descriptive only.

**Code · record.** `evaluation/src/studies/investigator_transmission.py`. Both records cite it at the old path `evaluation/src/experiments/` · `memory_system/effectiveness/v6_sp_ab/experiment_log.md`; `generation_prompt/prompt_claims_audit/experiment_log.md`.

### B10. Batch summary (`scripts/analyze_batch.py`) — no trust of its own

**What it is.** Win rates by winner, plus mean, median, standard deviation and range of each metric, per batch config. The output is markdown or JSON. It was ported to the ten-seat roles (plan §8.4; the role list at `analyze_batch.py:75`).

**What to know.** It reads the `computed_metrics` stored in each record at game time and does not recompute (`extract_metrics`, line 124). A ten-seat record written before the 2026-10-11 port therefore carries the old nine-seat values, including the zeros. It does no paired comparison and gives no interval. Each number is as good as the metric it averages. No record in `evidence/` cites a run of it.

**Code · record.** `scripts/analyze_batch.py` · none.

---

## Cross-cutting (2026-10-23)

- **Every validation against win is nine-seat.** The basket, the 2026-07-02 diagnostics, the leverage anchor and the blend check all rest on June–July 2026 records. The live game is ten-seat, and no score has been validated against win there. The code makes this explicit: nothing pushes as "validated".
- **Exact counts, small samples, one model.** The October scores are counts code reads from records. The counts are exact. The samples are 4 to 31 games, mostly on `gemini-3.5-flash-lite`, so they show direction and mechanism, not size.
- **Three scorers still carry nine-seat role names.** `score_vote` (threats `{"wolf", "serial_killer"}`), `read_ledger.py` (the same set and a `wolf` mask) and the discussion-evidence judge's role join (`EVIL = {"wolf", "serial_killer"}`, `../llm_judge/experiment_log.md` §8). On a ten-seat record they run without error and score the new evil roles as town. Ten-seat work uses `grading.py`, `ten_seat_metrics.py` and the persona scorer's side-based reads instead.
- **Counts of meaning need a read.** Where a score counts something semantic (quiet players named, a read "claimed", evidence cited), the record shows keyword counts being wrong until the matches were read (B5, B9). The structural counts never needed that.

## Sources

| Instrument | Code | Record |
|---|---|---|
| Nine-seat basket + validation | `Agents/compute_metrics.py`, `Agents/schemas/metrics.py`, `evaluation/src/instrument_validation/proxies/`, `evaluation/src/core/stats.py` | `metrics/{proxy_win_monotonicity,experiment_log}.md`, `metrics/design/`, `metrics/metrics_audit/` |
| Tiering and the push | `Agents/compute_metrics.py:688-776` | `memory_system/v8/plan.md` §8.4 |
| Ten-seat metrics | `Agents/ten_seat_metrics.py`; `compute_game_metrics` | `memory_system/v8/{plan.md §8.1–8.4, decisions.md §8}` |
| Ten-seat decision grades | `Agents/memory/consolidation/grading.py`, `scripts/grade_observations.py` | `memory_system/v8/{plan.md §9.6, decisions.md §12–13, experiment_log.md}`; `credit/report.md` §2 |
| Read Brier | `evaluation/src/loop/read_ledger.py`, `evaluation/experiments/persona_voice_games_score.py` | `credit/report.md` §1, §4; `game_play_enhancement/data/persona_voice_games/` |
| Vote-target accuracy | `compute_metrics.py:536`, `Agents/memory/consolidation/decision_scoring.py`, `evaluation/experiments/haiku_vote_score.py` | Part A; `discussion_evidence.md` §8.7 |
| Leverage anchor | `instrument_validation/proxies/leverage_anchor_separation.py` | `memory_system/v7/plan.md`, `memory_system/v7/experiment_log.md` |
| Discussion census | `evaluation/experiments/discussion_evidence.py` (`census`) | `game_play_enhancement/discussion_evidence.md` §2 |
| Phase 2 step 8 counts | `evaluation/experiments/phase2_step8_{capture,counts}.py` | `game_play_enhancement/data/phase2_step8_games/` |
| Balance batches | `evaluation/experiments/phase3_capture.py` | `game_play_enhancement/data/phase3_{games,balance*}/`; `discussion_evidence.md` §8.3, §8.5 |
| Blend-tactic check | `evidence/generation_prompt/prompt_claims_audit/blend_claim_test.py` | same folder, `experiment_log.md` |
| Investigator transmission | `evaluation/src/studies/investigator_transmission.py` | `memory_system/effectiveness/v6_sp_ab/experiment_log.md` |
| Batch summary | `scripts/analyze_batch.py` | none |

*Written 2026-06-28 and 2026-07-02 (Part A); widened 2026-10-23 (Part B, corrections, verdict, sources), checked against the code at the working tree of that date. Whether the agents play well, as opposed to how well we can score it, lives in the design folders named above.*

---

## 2026-10-24 — the ten-seat win check

**Why.** Every check against win above is nine-seat, and `VALIDATED_ON_TEN_SEAT_METRICS` is empty. By
October enough ten-seat games with full night records existed for a first check, at no cost.

**What was run.** `evaluation/experiments/ten_seat_win_check.py`: 78 ten-seat games from 2026-10-11 on
(the batch list and full table are in [`data/ten_seat_win_check/`](data/ten_seat_win_check/README.md)).
Each game's metrics recomputed from its record; each score correlated with its side's win over all
games, within batch, and over the 49 memory-off games. Town won 46, wolves 17, the lone killer 15
(serial killer 7, necromancer 8). A first count said 119 games; it looked for each night's choices,
and the 41 phase-3 games of 2026-10-09 and 10 have choices but no outcome, so their ten-seat scores
cannot be rebuilt.

**Directions were not fixed beforehand for the new roles' scores** (owner's call, 2026-10-24: run
first, then read the results). Scores the June check also tested carry June's direction; the rest are
exploratory.

**Carried over** (same direction as June, holding within batch and with memory off):
- share of lynches on a threat +0.49 (range +0.30 to +0.64); share on townspeople −0.45; townspeople
  lynched −0.38;
- town power roles lost to night kills −0.55; the town lynching the lone killer +0.38;
- the serial killer's kills of town power roles +0.48 (45 games, 7 serial killer wins);
- wolves voting with the day's lynch +0.29 (70 games; +0.22, not significant, with memory off);
- new: the Chanteuse's blocks of a real town action +0.31 (+0.45 with memory off).

**Vote accuracy.** +0.37 over all games, +0.24 (p = 0.10) with memory off. The split is by batch more
than by memory: +0.54 in the 29 memory-on games (nearly all Haiku), +0.37 in the memory-off Haiku
persona games, +0.08 and +0.16 in the flash-lite seeding and evil-cover batches (12 games each).
Average vote accuracy was the same with memory on and off (0.57, 0.59). Memory and model cannot be
told apart in this pool.

**The healer.** Save rate −0.03 (range −0.26 to +0.20, 75 games), against +0.36 on nine seats; June's
size is ruled out. What the records show:
- a save is a night the healer protected a player who was attacked (by anyone) and lived
  (`Agents/rules/night.py`, the verdict step); the rate divides town saves by protection nights that
  went ahead, so a Chanteuse block (30 nights) counts for and against nothing;
- 220 protections went ahead: 79 saves, 141 on a player nobody attacked;
- about one save a game whether town won (1.07, over 3.25 protection nights) or lost (1.03, over
  2.48); the healer's number of protection nights, i.e. its survival, goes with winning (+0.29);
- the saves were real (in 56 of 79 nobody died that night), but 36 of the saved died later, and in
  23 someone else died the same night to the other killer.
- Owner's reading (2026-10-24): by the rules a save is one more townsperson for the next day, so it
  is a good decision whatever follows. On ten seats, with more information roles to guard and two
  killers a night, whom to save is a harder guess and one save decides the game less often.

**The vigilante.** Dealt in all 78 games; fired in 19, holding fire on 177 nights. 22 shots went
ahead: 16 at evil players, 3 at townspeople, 3 at neutral roles. Correct-shot rate +0.29 over 19
games (range −0.19 to +0.66): accurate when it fires, too rare to test against win.

**The information roles.** Sentinel watches named an evil player 40 times (39 games), Trailseer
follows 58 times (45 games), investigator finds 22 times (20 games). Of 134 evil players the three
named, 81 (60%) were later lynched. Per game, the number named shows no link with the town winning
(+0.09); the share later lynched leans the right way (+0.19, p = 0.12, 66 games). Same pattern as the
nine-seat finding that a find turned into a lynch mattered and the find rate did not; too few games to
confirm it here. Per-role scores: Sentinel +0.12 (range −0.11 to +0.33), Trailseer +0.03, Sigilist
hits +0.20 (p = 0.09).

**Rare events.** Critical Chanteuse blocks: 35 in 26 games (+0.10). Investigator finds turned into
lynches: 20 games (+0.29, range −0.18 to +0.65).

**Close to the win itself.** The necromancer's nights survived +0.51: it has to survive to win, as the
serial killer's nights survived did on nine seats (+0.555).

**Not computed on ten seats.** `investigator_find_next_round_convergence` checks for the literal role
`"wolf"` (`_investigator_find_next_round_convergence`), and `wolf_blending_rate` counts days by the
nine-seat wolf role. Both return nothing on ten seats rather than a wrong number. *Correction, same
day:* the three scorers in Part B's cross-cutting note were switched to the role registry that morning
(`f13c43ea`), so they no longer mis-score ten-seat records. With `query_criticality`, which counts the
literal wolf and serial-killer roles, three places still carry nine-seat role names.

**Owner's reading of the method (2026-10-24).** A move the rules define as good (a save, a find, a
shot on an evil player) is graded by the rules; the win correlation is support on top, not the
definition. At 78 games most nulls are "too few games to test", not failures.

**Not done.** No score was added to `VALIDATED_ON_TEN_SEAT_METRICS`; that changes the live push's
labels and is the owner's decision.
