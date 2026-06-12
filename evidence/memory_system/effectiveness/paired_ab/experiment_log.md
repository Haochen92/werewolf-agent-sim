# Paired memory A/B — run playbook

**Status: RUNNING (2026-06-11).** Baseline + 3 arms launched, parallel, 0 errors/429s.

## ⭐ Epoch-shift finding — baseline re-run fresh (2026-06-11)

The 10 fresh baseline games came back **villagers 10% / SK 60% / wolves 30%**, vs the
original 30 baseline's **67% / 27% / 7%** (Fisher **p=0.0028**) — a systematic shift
(town down, SK up), despite byte-identical play prompts and no game-rule/scheduler code
change since the baseline commit `b9756960`. Most likely cause: `gemini-3.1-flash-lite`
model drift (Vertex-side) or small-N variance. Either way the original-epoch baselines
can't serve as the off-control. **Fix:** re-run the 20 recovered `game_id`s as fresh
baseline in the current epoch (`ab_baseline_recovered.jsonl`, `recovered_ids.json`) so all
30 baselines are same-epoch AND carry full `computed_metrics` → clean paired win **and**
proxies at N=30. The original baseline + `seed_set.json` recovered winners are no longer
used for the comparison.

### Can we pin or detect the drift? (investigation 2026-06-11)

Probed whether `gemini-3.1-flash-lite` alias drift is preventable/detectable:

- **Not pinnable.** Vertex `models.list()` shows only `gemini-3.1-flash-lite` (alias) and
  `gemini-3.1-flash-lite-preview` (a preview — *less* stable) for this generation. No dated
  snapshot (no `-001`) exists to pin to, unlike older gens (`gemini-2.0-flash-lite-001`
  does exist). So Google can repoint the alias silently and we can't freeze it.
- **Not detectable from responses.** The served `model_version` (both langchain
  `response_metadata` and the raw `google.genai` response) just echoes the alias
  `gemini-3.1-flash-lite` — no underlying snapshot id. So there's nothing extra to log in
  `runtime_fingerprint` that would surface drift; the fingerprint's `game_model` already
  records the alias, and that's all Vertex exposes.
- **What the fingerprint DOES catch:** backend (`llm_backend`: vertex/google) and region
  (`vertex_location`). Those changes are visible; alias-snapshot drift is not.

**Consequences / standing rules:** (1) same-epoch fresh baseline is mandatory for any A/B —
never pair against historical-epoch outcomes; (2) optional active guard = a temp-0 canary
prompt set run alongside batches, watched for output-distribution shift (temp=1.0 can't
separate drift from variance); (3) revisit pinning once Google ships a dated
`gemini-3.1-flash-lite-NNN` snapshot.

## Design

Per-role memory ablation on the frozen **v5_0** store (consumption mode), paired on a
shared seed set so each arm replays identical role draws → McNemar.

- **Arms (memory-on for the named role(s) only):**
  - `wolf_only` — resolves whether the pilot's wolf lift is empowerment vs town degradation
  - `serial_killer_only`
  - `town_only` — villager + healer + investigator + vigilante (full town faction; where the
    validated proxies live: vote accuracy, mislynches, |r|≈0.6)
- **Baseline:** `all_disabled` (memory off).
- **Treatment (all arms):** `--retrieval-types observations_only --reranking rerank_disabled
  --filtering filter_disabled`, `top_k=5` (observations-only saturation point,
  evidence/retrieval/capacity_limits). `--no-memory-dump` so the store can't grow → constant treatment.

## Seed set (`seed_set.json`, frozen by `scripts/make_ab_seed_set.py`)

30 game_ids = **20 recovered** baseline game_ids (from `extraction_v5_0.jsonl`, with recorded
baseline winner: 12 villagers / 7 serial_killer / 1 wolves) + **10 fresh** uuid4s. Verified
2026-06-11: a game_id reproduces its exact role draw (`crc32(game_id)` → choice → shuffle, 20/20),
and all play-path code is unchanged since the baseline commit b9756960 (only behavior-neutral
eval plumbing changed) → pairing arm games against the recorded baseline outcomes is clean.

- `arms_game_ids.json` — all 30, for the arms.
- `baseline_fresh_ids.json` — the 10 fresh, for the baseline top-up (the 20 recovered already
  have recorded outcomes in `seed_set.json`).

## Run commands

1. **10 fresh baseline games** (memory off, cheap ~$0.20/game):
   ```
   poetry run python scripts/run_batch.py --configs all_disabled \
     --game-ids-file evidence/memory_system/effectiveness/paired_ab/baseline_fresh_ids.json \
     --no-memory-dump --session-prefix ab_baseline --output batch_results/ab_baseline.jsonl
   ```
2. **3 arms × 30 games** (read-only on frozen v5_0 → parallel-safe):
   ```
   poetry run python scripts/run_batch.py \
     --configs wolf_only serial_killer_only town_only \
     --retrieval-types observations_only --reranking rerank_disabled --filtering filter_disabled \
     --game-ids-file evidence/memory_system/effectiveness/paired_ab/arms_game_ids.json \
     --no-memory-dump --memory-store-dir memory_stores/v5_0 \
     --session-prefix ab_arms --output batch_results/ab_arms.jsonl
   ```

## ⭐ Pre-registration — reranked-arm predictions (written 2026-06-11, BEFORE any reranked game completed; reranked arms at 0/30 at commit time)

Calling the shots before the data, to avoid the multiple-comparisons trap (~5 arms × ~8 proxies
≈ 40 tests → expect ~2 false positives at p<0.05 even if memory does nothing; the pilot's
"70%→97% proven" was the best of 6 cells and did NOT replicate).

- **PRIMARY endpoint = ONE validated proxy per arm (NOT win rate).** Win rate is underpowered at
  N=30 (~1 bit/game), so it is demoted to a directional co-read: reported, but a flat win rate is
  "underpowered," not "refuted." The powered primaries are the monotonicity-validated proxies
  (chosen by the INDEPENDENT proxy-monotonicity check, before any A/B result).
- **Called shots — reranked-observation arms (each vs its RAW counterpart):**
  - `rerank-town` (the strong bet) — PRIMARY `town_vote_accuracy`. PREDICT reranked-town > raw-town
    (sharper retrieval → less diluted town reasoning). Flat → raw retrieval was already adequate.
  - `rerank-wolf` — H: low raw-retrieval precision was the bottleneck. PRIMARY `town_vote_accuracy` /
    `mislynches`; PREDICT town detection DROPS vs raw-wolf (sharper wolf memory → wolves hide
    better). Win rate = underpowered headline. Flat → content, not precision, is the limit.
  - `rerank-sk` — exploratory (no strong prior); no called shot.
  - **⭐AMENDMENT (written before scoring the full N=30 reranked results):** the reranked arms are a
    BUNDLE — reranked-top-3 (curation) vs raw-top-5. Interpretation rule fixed now: a **POSITIVE**
    reranked result = the *curation bundle* wins (conservative — claims the bundle, not "precision"
    specifically; and it wins DESPITE v4's count prior that cap=5 ≥ cap=3, so the tighter set is a
    slight handicap). A **NEGATIVE/null** result = AMBIGUOUS (selection-neutral OR the tighter count
    hurt) → named follow-up: **raw cap=3 vs reranked keep=3** (equal count) to isolate selection from
    count. Justified by the CONFIG (`RERANK_KEEP=3`, a setup fact), not outcomes; partial N=6
    reranked numbers were glimpsed in an analyzer smoke-test, full N=30 unscored at amend time.
- **Called shot — raw all-on arm (`all_enabled`, no reranker), vs the same-epoch baseline:**
  - H (derived from the isolation arms): town memory *helped* town and evil memory *didn't help*
    evil, so if effects compose additively, all-on leaves town **neutral-to-better** — which
    CONTRADICTS the pilot's confounded "all-on → town collapses −32pp, wolves flip to 40%."
    PRIMARY `town_vote_accuracy` + villager win rate. **PREDICT all-on does NOT replicate the pilot's
    town collapse: town proxies/win hold or improve vs baseline.** If town instead collapses → a
    destructive interaction the isolation arms can't see (and the pilot effect is real, not just the
    confound). This is the clean same-epoch replication test of the finding that started the whole
    investigation.
- **Decision rule:** a called shot that hits = confirmatory evidence. Any OTHER metric that lights
  up = exploratory lead ("needs its own follow-up"), not a conclusion. p-values uncorrected AND with
  a Bonferroni note over the pre-specified primaries (≤3 tests). The raw arms already ran, so their
  proxy hits inherit the validated-basket protection but are reported with the multiplicity
  caveat — not as called shots.

## Analysis

Per arm, pair each of the 30 arm games to its baseline by `game_id`: the 20 recovered ids
pair against `seed_set.json` recorded winners; the 10 fresh ids pair against the `ab_baseline`
run. McNemar on the arm's faction win (wolf-faction for wolf_only, SK for serial_killer_only,
town for town_only) + the validated de-lucked proxies. Reuse `evaluation/src/core/stats.py`.

## Raw results — N=30 paired, FINAL (2026-06-11)

Same-epoch baseline (villagers 27% / SK 40% / wolves 33%). Numbers in `report.md`.

- **town_only:** villager win 27%→43% (+17pp, McNemar p=0.27, underpowered). Validated proxies move
  together, several significant: `correct_elimination_rate` +0.17 (p=0.028), `town_mislynch_rate`
  −0.17 (p=0.036), `healer_town_save_rate` +0.23 (p=0.005), `town_vote_accuracy` +0.15 (p=0.053).
  ⭐Cleanest positive: town memory improves town decision quality.
- **wolf_only:** wolf win FLAT 33%→30% (p=1.000) — no evidence memory helps wolves; the pilot's
  "wolf memory is powerful" does NOT replicate. Town proxies nominally up (mislynch p=0.042).
- **serial_killer_only:** SK win 40%→20% (p=0.146, suggestive-not-sig); SK memory didn't help SK.
- **Cross-arm pattern + multiplicity:** town decision-quality proxies improve in ALL arms; ~7 of 24
  tests p<0.05 vs ~1.2 expected by chance → a real signal exists, but NO single hit survives
  Bonferroni (0.05/24 = 0.002) — the town arm's CONSISTENCY (4 directional hits) is the strongest
  evidence, not any one p. Diagnosed: retrieval works (~3.4 obs/decision), store not dup-cluttered
  (0% near-dups) but semantically dense → low raw-retrieval precision is the leading suspect for the
  weak/absent evil-arm effects. Win rate underpowered in every arm (the proxies carry the signal).
- **Headline (raw):** memory helps TOWN decision quality (multiple validated proxies significant,
  consistent, with a directional +17pp win); no detectable benefit to wolf or SK. The reranked and
  all-on arms (pre-registered above) test the precision hypothesis and the interaction/replication.

## Reranker validity check (2026-06-11, while reranked arms running)

Confirmed the reranked arms test precision, not a reorder of the same 5:
- Pool IS wide: `RERANK_TOP_K=10`; measured pre-rerank `candidate_observations` mean **10.8**
  (max 19) per wolf decision → reranker picks the best ~3 from ~11.
- Count: `RERANK_KEEP=3` → reranked delivers **3.0** obs/decision; raw delivers **3.44** (its
  top_k=5 collapses post-dedup). So the reranked arm = a **CURATION treatment**: sharper selection
  (best ~3 of ~11) PLUS a marginally tighter set. These move together and directly probe the
  retrieval-overload/clutter hypothesis — "does a tighter, higher-quality top-set beat raw retrieval"
  — which is also the deployment-realistic lever. NOT a 5-vs-3 confound (counts are close; keep=5
  would have over-delivered vs raw). The pre-registered called shots score the same comparison under
  this reading.

## FINAL CONCLUSION — all arms, N=30 paired (2026-06-11)

### Called-shot scorecard (pre-registered + amended before unblinding)
- ⭐**all-on — CONFIRMED.** Predicted town does NOT collapse (contra the pilot's confounded −32pp).
  Actual: villager win 27%→**50%** (+23pp, McNemar p=0.167) with town-positive proxies
  (correct_elim p=0.030, mislynch_rate p=0.039, serial_killer_lynched p=0.046). Town IMPROVED, did
  not collapse → the pilot's "memory degrades town" was the confound (moving store + old epoch).
- **rerank-town — MISSED.** Predicted curated > raw on town_vote_accuracy. Actual rerank 0.686 ≈ raw
  0.710 (Δ−0.023, p=0.52); paired town WIN raw 43% vs rerank 60% also NOT sig (McNemar p=0.302). Per
  the amendment → the "ambiguous, count-isolation follow-up" branch. Curation did not beat raw.
- **rerank-wolf — NULL.** Directionally as predicted (town detection down: vote_accuracy −0.041,
  mislynches +0.067) but trivial / non-sig (p>0.65). Not confirmed.

### The robust finding (convergent across all 4 town-memory arms)
**Memory helps TOWN.** Every arm where town holds memory rises: raw town +17pp, reranked town +33pp
(**win p=0.013**, mislynches p=0.015), all-on +23pp — and the validated decision-quality proxies move
town-positive consistently (correct_elim, mislynch_rate, healer_town_save). The **convergence across
independent arms** is the evidence; individual win tests are underpowered but the direction is
unanimous, and the reranked-town arm is the only one reaching win-rate significance (60% vs 27%).

### The nulls
- **Wolf / SK memory: no benefit.** wolf flat (raw 33→30 p=1.0; rerank 33→20); SK down (raw 40→20;
  rerank 40→23). Memory does not help the deceiving roles.
- **Curation ≈ raw: retrieval RANKING is not the lever.** Town memory helps whether raw or curated;
  sharpening selection (reranking) added no significant gain over raw → the "low-precision bottleneck"
  hypothesis is unsupported. (Reranked-town's significance is vs *baseline*; vs *raw* it's null.)

### Caveats
- Win rate underpowered (N=30); proxies carry the signal. Multiplicity: many uncorrected tests — the
  town direction is too consistent across arms to be noise, but no single proxy survives strict
  Bonferroni alone; consistency + reranked-town win p=0.013 + mislynches p=0.015 are load-bearing.
- Exploratory (not pre-registered): reranked-SK shows sig town proxies (vote_accuracy p=0.040,
  correct_elim p=0.041) — a lead, not a shot.
- Targeted N=60 on the town arm would likely push its proxies past correction; the per-decision LLM
  judge is the more power-efficient follow-up.

### Headline
On a drift-corrected, same-epoch paired design with pre-registered shots: **episodic memory
consistently improves town decision quality and win rate** (convergent across 4 arms; reranked-town
win p=0.013); **it does not help the wolf or SK**; **retrieval reranking adds nothing over raw**; and
**the pilot's "memory collapses town" alarm was a confound — refuted by the clean all-on arm
(town +23pp).**

## Interpreting the wolf/SK null — diagnostic ladder (2026-06-12, not yet run)

The town-helps / deception-doesn't split is the surprising result, so before "fixing" the wolf arm we
scope WHY. Two free checks already narrow it:
- **Store volume is NOT town-biased.** wolf 80 obs + 66 strategy points, SK 79 + 68 — same scale as
  villager. "Town-biased in volume" is weak.
- **Wolf content IS genuine deception craft**, not town diagnostics in disguise (sampled e.g. "don't
  just deny — counter-claim or frame a third player to redirect the village"). "Wolf memories are town
  knowledge relabeled" is weak.

That leaves four candidate layers — and critically, **"no measured effect" ≠ "no effect."** Our
validated proxy basket is town-centric by construction (wolf social proxies failed validation, win is
underpowered at N=30 — see [[project-metrics]]), so we may lack an instrument that could even SEE a
wolf gain. The ladder therefore starts at the measurement layer, not the memory system. Free → paid:

1. **Validate a wolf/SK instrument on data we already own (FREE, do first).** We now have 240 games —
   ~5× the original proxy-validation corpus. Re-run monotonicity for deception-side candidates: wolf
   survival days, day-of-first-wolf-lynch, votes-attracted-while-alive, kill-target quality (power-role
   hit rate), SK survival. If none correlate with wolf wins even at N=240 → honest conclusion is "we
   currently cannot measure wolf skill" and any fix arm is premature. If one validates → that is the
   pre-registerable primary metric for a wolf arm.
2. **Role-scoped retrieval-precision audit (FREE, from the A/B's own logs).** Pull wolf/SK decision
   points (incl. WOLF-NIGHT kill-vote + SK night cases) from `batch_results/eval_cases/`, memory-on
   arms; eyeball top-5 on-point rate split by role (same method as the store-wide ~1/6 density check).
   Deception situations are more game-specific, so the embedder may generalize worse → a plausible
   retrieval gap. If wolf retrieves comparably to town, move on.
3. **Application audit, exploiting the paired design (CHEAP).** For decisions where a relevant memory
   WAS in context: does the wolf's reasoning use it, and does its action differ from the paired
   memory-off game at the same decision point? ~20–30 manual reads, OR scope the parked per-decision
   LLM judge to wolf/SK arms only — the narrow case where that judge earns its cost (a few dollars).
4. **Harm-channel check (FREE, from `raw_metrics` dumps).** SK 40→20 is a HARM signature, not an
   absence signature. Paired on-vs-off: do memory-on wolves/SK die earlier? If yes, memory is creating
   tells / inducing bolder play — a different (and more interesting) problem than "memory ignored."

**Fix mapping (freeze-aware).**
- Retrieval gap → freeze-safe config levers ONLY: per-role `top_k`, namespace scoping, pool width.
  Retrieval/rerank prompt re-tunes are frozen until Phase B.
- Content thinness/genericness (if step 2 shows wolf memories systematically off-point) → the
  **namespace-augmentation pipeline is already built and parked** ([[project-namespace-augmentation]]);
  re-mining frozen games with frozen prompts is freeze-safe.
- Application gap (memory in context, ignored) → injection-prompt territory = FROZEN → named Phase B
  item, not a now-fix.
- Harm channel → that's a RESULT, not a bug. Write it up.
- Only then: one pre-registered wolf arm with the chosen fix, same seeds, current epoch window (~$18),
  primary = the proxy validated in step 1.

**The mechanistic prior (hold onto this).** The default hypothesis assumes memory leverage is
role-symmetric; mechanistically it probably isn't. Town plays an INFERENCE game — accumulated
cross-game patterns compound. Wolf/SK day play is GENERATIVE deception (in-the-moment execution
quality) and the night kill is a small action space dominated by within-game info (whoever claimed
investigator dies). If the ladder bottoms out at "memories are relevant, retrieved, read, and STILL
don't move decisions," then **"memory helps reasoning, not deception"** is the real finding — and with
a diagnosed mechanism behind it, that is a stronger portfolio result than a forced positive.

### Diagnostic results (2026-06-12 — steps 1 & 4 run; all exploratory, post-hoc cuts)

Scripts colocated here: `diagnose_wolf_sk_proxies.py` (ladder steps 1+4) and
`diagnose_wolf_blending.py` (the blending follow-up). Read-only over `batch_results/ab_*.jsonl`.
Pooling gotcha encoded in both: arms SHARE game_ids with baseline (the pairing key) — dedupe by
(arm, game_id), never by game_id alone.

**Step 1 — proxy revalidation at N=240** (~5× the original n=50 corpus, wolves now win ~30% not 7%):

- `wolf_power_role_targeting_rate` **VALIDATES** (+0.18 p=0.006 pooled; +0.35 p=0.060
  baseline-only, same sign) — the first validated wolf proxy.
- `sk_nights_survived` re-validates strongly (+0.48 p<0.001 n=240).
- Stock `wolf_blending_rate`/`dissent_rate`: no longer degenerate, just ~0 at n=100 — but see the
  blending follow-up below: the stock definition is the artifact, not the concept.
- `wolf_steering_rate` trends wrong-sign pooled (−0.14 p=0.081); `wolf_killed_healer_day` /
  `wolf_killed_investigator_day` WRONG SIGN (+0.60 p=0.025 sig. baseline) — kill-TIMING metrics
  are game-length-confounded, the same trap as `investigator_found_wolf_day`. Excluded.

**Step 4 — SK harm channel = day-social, not night-targeting.** SK-mem-on (arms_sk+rr_sk, n=60)
vs no-SK-no-town-mem (baseline+arms_wolf+rr_wolf, n=90 — pool chosen to dodge the town-skill
confound on lynchings): night survival UNCHANGED (3.32 vs 3.43) and kills similar, but
`sk_exit_method` shifts **lynched 63%→78%** (Fisher p=0.070). SK wins ≡ survived count, so
+lynchings = −wins. Memory isn't degrading SK's night game; it's making the SK detectable by day.

**The two-edged sword (wolf).** Memory improves the validated night skill — power_targeting 0.459
baseline → 0.544 raw-wolf / 0.511 rr-wolf, with arms_town (wolves memory-free) at 0.448 as a clean
negative control — while detectability rises in the same arms: `wolf_elim_rate` 0.227 → 0.292 /
0.340, with town memory-free, so the wolves are leaking rather than town hunting better.

**Blending follow-up (user's qualitative pushback — vindicated).** The stock blending metric is
conditioned on wolf-elimination days (`compute_metrics.py`): a game where wolves blend perfectly
and are never caught contributes ZERO observations — it samples disaster states exclusively, so
its null cannot refute "blending matters." Measured UNCONDITIONED (fraction of a living wolf's
votes aligned with the day's lynch, all lynch days, from raw `day_resolutions`):

- **Validates vs wolf win:** r=+0.43 p=0.024 baseline-only; +0.20 p=0.003 pooled n=220.
- **Micro-mechanism confirmed** ("dissent to protect a piled partner → removed next day"):
  dissenting wolf lynched next day **49%** (32/65) vs **31%** (11/35) when blended.
- **The leak is visible in the vote record:** wolf-memory arms blend WORSE — baseline 0.838 →
  arms_wolf 0.643 / rr_wolf 0.649. Working hypothesis: memory content prescribes ACTION
  (counter-claim, frame, protect) and shifts wolves from camouflage to active maneuvering, which
  town reads. Anomalies kept honest: allon=0.761 (wolves also hold memory there — possible
  town-memory interaction) and a general dip across ALL arms vs baseline (some environment noise).

**Consequences.** (a) The night-only-memory arm now has a sharp pre-registerable behavioral
prediction: unconditioned blending returns to ~baseline while power_targeting stays elevated.
(b) Unconditioned blending is a candidate for promotion into `compute_metrics` (measurement-only,
freeze-safe). (c) Day-strategy-point arms for deceivers are the RISKY variant under this
mechanism (more action-prescribing content on the leaking surface); SP-at-night is the safe test.

## Mechanism refinement → the MYOPIC-FRAMING hypothesis (2026-06-12)

The "two-edged sword" left one question open: *why* does memory shift wolves from camouflage to
maneuvering? The chain that narrowed it (each step a read over the A/B sidecars + store):

1. **"Was the prescriptive content even retrieved?"** (user challenge). Wolf *observations* are NOT
   prescriptive — they are episodic situation/approach/outcome records, balanced polarity. So the
   leak isn't "memory tells wolves to attack."
2. **Approach-imitation vs outcome-learning.** The `approach` fields are a catalog of active
   maneuvers (discredit investigator, protest vote, force tie). If agents integrated OUTCOMES,
   blending should have *risen* (most active-defense precedents end badly) — it FELL. First
   hypothesis: agency induction (imitate the *form* of precedents, not the lesson).
3. **Namespace scoping retracted the crude cuts** (user re-cut). Retrieval at `day_vote` is
   namespace-scoped (926/926 from observations/wolf/day_vote); a keyword "active/passive" classifier
   mislabels (bussing tagged "active") and a dose-response is non-monotonic = situation ENDOGENEITY
   (retrieval reflects situation severity — can't read causation off it). What SURVIVED: exposure is
   concentrated (top-8 entries = 72% of retrievals), and **the two most-retrieved DISSENT precedents
   are SUCCESS-FRAMED AT FACE VALUE** — ×137 "voted for the accusing investigator… helped us survive
   the day's vote. However… permanent record used later"; ×75 tie-force "protected both wolves…
   chaos to exploit" (pure positive, no cost recorded).
4. **→ MYOPIC OUTCOME FRAMING.** Extraction credits the immediate result in the lead clause and
   defers the cost to a subordinate "However…"; a skimming agent absorbs the headline verb-phrase
   (action → survival) and under-weights the trailing concession. Two distinct failure modes:
   ×137-type = a *reading* failure (cost IS recorded but in the weak clause); ×75-type = a
   *recording* failure (cost never traced — extractor stopped at the next-day effect, or N=1 it
   genuinely never backfired). They need different fixes — net-first composition repairs ×137,
   a required end-of-game verdict repairs ×75.

## The net-horizon fix (AGREED design, delegated build — `v5_0_nethorizon`)

Freeze-clean because it is a **config-flag store variant** (default `v5_0` untouched, frozen) and
**not a play-prompt change** (extraction runs post-game; no game-generation epoch shift). Shape:

- **Extraction schema** (`Agents/schemas/memory.py` `Observation`, model-visible @ :41): `outcome`
  (:99) → two REQUIRED fields, `impact_on_final_game_outcome` (declared FIRST; `Field(description=)`
  = the end-of-game judgment rule: net effect on this role's win condition; helped-today-but-led-to-
  elimination = NET NEGATIVE, say so; untraceable → "unclear" + why; name the causal chain) +
  `immediate_response`. New `composed_outcome` @property, NET-FIRST, mirroring `composed_situation`
  (:106) → single stored `outcome` string → StoredObservation schema UNCHANGED, zero downstream
  ripple. Reading order = composition order.
- **Prompt** (`Agents/prompts/extraction.py`): the outcome bullet lives in THREE live spots — :107,
  the per-role block :328 (the v5 path: `ROLE_EXTRACTION_PREFIX`+`TAIL` @ :408), :522 — all change,
  plus matching `Field(description=)` and the PERSPECTIVE-RULE lines that name `outcome`.
- **Metadata (NOT injected):** `net_verdict` enum (positive/negative/mixed/unclear; its unclear-rate
  = a free extraction-reliability metric; "unclear" is a first-class value, honoring genuine N=1
  ambiguity rather than forcing a false positive). `source_game_winner` (+ `role_faction_won`) =
  objective game_id→batch-winner join at dump time, no LLM, soft-signal only, NEVER a hard filter.
- **Validity invariant:** embeddings stay SITUATION-ONLY → retrieval byte-identical between `v5_0`
  and the variant → outcome framing is the only difference. Gate: situation/approach embedding-sim
  vs v5_0 ≈ 1.0. One re-extraction pass produces ALL roles → one store serves the wolf AND SK arms.

## Step-3 ECHO READ — the free gate (2026-06-12, RESULT) — PASSED → build warranted

Decisive pre-build test: on memory-on wolf decisions that DISSENT (vote off the day's eventual
lynch — the behavior the unconditioned-blending finding ties to next-day removal), does the wolf's
private `updated_strategy` ECHO a retrieved precedent? If not, framing isn't the lever and the
variant build is skipped (fall back to night-only). Pure local read — arm sidecars
(`retrieved_observations` + `updated_strategy`) joined to batch `day_resolutions`, baseline tagged
per game_id+day. Script: `echo_read.py`; full detail: `echo_read_decisions.json`.

- **47** dissent wolf `day_vote` decisions with retrieval (arms_wolf + rr_wolf); **22** are PAIRED
  FLIPS (baseline blended that same game_id+day → memory-on wolf dissented) = the causal-suspect set.
- **Retrieved precedents** at these flips are dominated by the success-framed dissent/bussing cluster
  (vote-own-partner-to-look-correct, vote-the-accusing-investigator, protest-vote, force-tie), scores
  0.80–0.87 — the ×137/×75 family.
- **The `updated_strategy` echoes the precedent's approach-class** in the clear majority: vote the
  vocal accuser / suspicion-driver, distance from partner, keep the village divided, deflect pressure.
- **Cost-blindness is UNIFORM** (the key finding): in 0/22 does the wolf reason about the permanent
  voting-record cost that the retrieved outcome encodes in its trailing clause. #19/#22 are the loop
  caught live — the anti-investigator-record cost has ALREADY materialized ("my vote against the
  investigator is now a major liability") and the wolf dissents AGAIN.
- **#17 is confirmatory-by-counter-example:** the one precedent framed as an UNAMBIGUOUS failure
  ("early aggressive votes → exposure of wolves") produced the correct read — the wolf ABSTAINED to
  blend, citing it. When framing leads with the cost, the agent reads the cost. That is the fix's
  mechanism, observed prospectively.
- **Honest limit:** wolves are usually under scrutiny at these moments, so voting the accuser is also
  a rational in-situ move; the read shows thematic echo + uniform cost-blindness, NOT isolated
  causation (situation endogeneity). The `v5_0_nethorizon` paired A/B is the decisive causal test.

**Decision:** gate PASSED (dissents echo; cost-clause ignored; #17 shows reframing flips behavior) →
**proceed to the variant build + pre-registered wolf and SK arms.** Predictions (pre-registered):
wolf primary = unconditioned blending recovers toward 0.84; secondaries wolf_elim_rate → ~0.227,
power_targeting stays elevated, wolf win directional. SK: `sk_exit_method` lynched-rate back toward
baseline, survival/win directional. (SK echo read is a separate day_discussion-content cut — the
solo SK has no vote-pile to blend with — flagged as a lighter secondary, not a build blocker.)

## `v5_0_nethorizon` BUILT + validity diagnostic CLEAN (2026-06-12)

The net-horizon treatment is implemented (commits e7494fe schema / 8ac5adc prompt) and the variant
store is built. Build: `scripts/build_nethorizon_store.py` — full offline re-extraction of the 20
frozen v5_0 games with the net-first outcome framing, then the SAME downstream dedup, into a fresh
store. ⭐**Scoped to wolf + serial_killer only** (user cost call): the `wolf_only`/`serial_killer_only`
arms only ever retrieve their own role's namespace, so re-extracting the 4 town roles would be unread
waste → 40 pro calls, not 120. (A town/all-on nethorizon arm, if ever wanted, extracts the rest
incrementally.)

- **Store comparable to v5_0:** wolf+SK obs 164 (v5_0 159); per-namespace counts within normal
  extraction variance (e.g. wolf/day_vote 26→21, wolf/night_action 25→34). 142 strategy points.
- **The fix is on-disk** (stored `outcome` = the net-first `@computed_field`, verbatim): outcomes now
  LEAD with the verdict. ×137 reading-fix — wolf/day_vote "Mixed. …bought one more day… but the
  investigator identified them… leading to the wolves' loss." ×75 recording-fix — "Unclear. …However
  it was the Day-2 vote, not this one, that led to their demise, making the net impact hard to
  trace." (honest 'unclear' instead of a forced false positive).
- **net_verdict distribution** (n=164): positive 69 / negative 66 / mixed 27 / **unclear 2 (1.2%)**.
  The ~42% negative is the treatment working — costs the old success-first framing buried are now
  surfaced; the low unclear-rate is a clean extraction-reliability read. `source_game_winner` +
  `role_faction_won` stamped on all 164 (objective join; soft-signal only).
- **Validity diagnostic (NON-BLOCKING) — `situation_sim.py`:** per (role,phase) bucket, cross-store
  situation-embedding nearest-neighbour vs v5_0's own within-store density floor (v5_0 and nethorizon
  are both fresh stochastic extractions, so the floor IS the noise model). Result: **cross-store NN
  0.934 ≥ within-v5 floor 0.922 in EVERY namespace** → nethorizon situations land as close to v5_0 as
  v5_0 entries are to each other → NO systematic situation drift from the outcome reframing →
  retrieval is comparable and a paired arm isolates the framing. (Embeddings stay situation-only by
  construction, so the reframed outcome cannot enter the embedded text — invariant held.)

⭐**NEXT (paused for review before the paid step):** pre-register + run the wolf and SK arms on
`memory_stores/v5_0_nethorizon`, same 30-id seed set, in-epoch, observations-only, top_k=5,
`--no-memory-dump` — identical to the paired A/B treatment, swapping ONLY the store. Wolf primary =
`wolf_unconditioned_blending_rate` (predict recovery toward 0.84 vs wolf-mem 0.64); key contrast = vs
the v5_0 raw-memory wolf arm (framing vs no-fix, same retrieval). ~$6–8/arm.

## Code pointers

- Net-horizon: `scripts/build_nethorizon_store.py`, `situation_sim.py`, design `nethorizon_design.md`;
  schema `Agents/schemas/memory.py` (Observation outcome split), prompt `Agents/prompts/extraction.py`.
- Echo read: `echo_read.py` (+ `echo_read_decisions.json`); diagnostics `diagnose_wolf_sk_proxies.py`
  / `diagnose_wolf_blending.py`.
- Seed pinning: `scripts/run_batch.py --game-ids-file` → `run_game(game_id=…)` →
  `build_game_config` → `initialize_game` (role draw `crc32(game_id)`).
- Seed-set generator: `scripts/make_ab_seed_set.py`.
- Treatment presets: `MEMORY_CONFIGS` / `RETRIEVAL_TYPES_CONFIGS` in `run_batch.py`; `top_k`
  in `Agents/memory/enrichment/pipeline.py`.
