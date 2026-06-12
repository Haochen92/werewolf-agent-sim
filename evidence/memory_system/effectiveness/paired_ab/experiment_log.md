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

## ⭐ PRE-REGISTRATION — nethorizon arms (written BEFORE any arm game completed, 2026-06-12)

Both arms on `memory_stores/v5_0_nethorizon`, same 30-id seed set (`arms_game_ids.json`), in-epoch,
observations-only, top_k=5, rerank/filter disabled, `--no-memory-dump` — identical to the paired-A/B
treatment, swapping ONLY the store. Outputs `batch_results/ab_nh_wolf.jsonl` / `ab_nh_sk.jsonl`.

- **wolf-nethorizon** — PRIMARY `wolf_unconditioned_blending_rate`. The decisive contrast is **vs the
  v5_0 raw-memory wolf arm** (`ab_arms_wolf`, same retrieval/seeds): framing-fix vs no-fix. PREDICT
  blending RECOVERS toward baseline 0.84 from the v5_0-raw 0.64. Secondaries (same contrast):
  `wolf_elimination_rate` DOWN toward baseline 0.227 (from raw 0.29), `wolf_power_role_targeting_rate`
  STAYS elevated (the validated night gain must NOT be sacrificed), wolf win directional. Also report
  vs same-epoch baseline (off). **POSITIVE = net-horizon framing fixed the day leak** (blending up,
  detectability down, night held). FLAT = framing isn't the lever → night-only arm is next.
- **sk-nethorizon** — PRIMARY `sk_exit_method` lynched-rate back toward baseline (from the SK-mem 78%),
  `sk_nights_survived` held, SK win directional. POSITIVE = framing reduces SK day-detectability.
- Win rate = underpowered directional co-read at N=30 (the proxies carry it). All non-primary cuts
  exploratory. ~$6–8/arm; arms launched together (read-only on the frozen store → parallel-safe).

## ⭐ NAMED PHASE B FOLLOW-UP — the application-ADHERENCE lever (from the live-arm qualitative read)

While the arms ran (N=8), a qualitative trace surfaced the mechanism behind a possibly-flat wolf
result — and it is NOT in extraction. Worked case (game 22e2fd88, surviving wolf player_5, day-3
no-buss decision; player_7 the partner being lynched):

- **Retrieval was excellent** — 3 on-point memories (score 0.82–0.85), matched-situation near-identical
  to his query ("Investigator claim accuses my wolf ally, lynch pressure").
- **Framing was correct** — TWO led with "Negative: voting against the Investigator became the evidence
  that got the wolf lynched"; one even named the right play ("rather than join the majority to lynch
  their own partner and solidify their cover…" = BUSS); a third gave a Positive alternative (force a
  tie).
- **He did the warned-against move anyway** — voted the Investigator to defend player_7: *"if I don't
  support player_7 I'll be outed once he's eliminated… my only chance to survive."* In-the-moment
  linked-fate read OVERRODE the cross-game lesson. (Lynched day 5.)

⭐**Diagnosis: this is an ADHERENCE gap, not a retrieval or framing gap.** The memory was correct,
retrieved, and well-framed, and still under-weighted at decision time. → The lever is the
APPLICATION / injection layer, which is Phase B (agent-visible = prompt-freeze).

**Reframe (important): the target is CALIBRATION, not OBEDIENCE.** player_5's gamble was rational-ish;
tuning toward "always heed the precedent" would just recreate approach-imitation (copy the move
instead of weighing it). The goal = make the agent WEIGH the retrieved net-outcome vs its situational
read ("survives-today-but-leaves-a-record usually loses"), not obey.

**Net-horizon is the PRECONDITION, not a competitor:** you can't tune an agent to heed a verdict that
is itself myopic. This experiment makes the lesson correct/front-loaded; Phase B makes the agent act
on it. So a flat blending result here does NOT waste the build — it sets up the adherence work.

**Phase B experiments (named):** (1) injection-prompt A/B at decision time — current "here are relevant
observations" vs "+ explicit weigh-the-net-outcome guidance"; paired arms, validated proxies, same
machinery. (2) ⭐**the `net_verdict`-injection arm** — we STORE positive/negative/mixed/unclear as
metadata but do NOT inject it (the design reserved this as a separate follow-up); surface the one-word
flag and test whether it moves adherence more than buried prose. (3) fallback = fine-tune the
application model on good-adherence examples (parked fine-tuning Project).

**Guards:** injection prompts are agent-visible → self-inflicted epoch → fresh same-epoch baselines +
pre-registration + validated primary. ⭐**Ceiling honesty:** cornered/doomed wolves (e.g. player_7) are
unfixable by any prompt AND are already excluded from the blending metric (perspective rule); the
addressable population is the SURVIVING-wolf linked-fate gambles like player_5 → expect a partial
effect, not a flip. Walking into Phase B with "memory correct + retrieved but under-weighted at
decision time" is a far stronger position than "wolf null, unclear why."

## ⭐ SK harm mechanism + the wolf/SK DIFFERENTIAL prediction (qualitative, raw SK arm, 2026-06-12)

Why memory hurts the SK *net*-negative (vs flat for the wolf). Read of 5 lynched-SK games in the raw
arm (`ab_arms_sk`, SK lynched in 24/30):

- **What the SK retrieves:** a recurring theme of ACTIVE anti-investigator maneuvering modeled as
  skilled play — "expressed skepticism toward the Investigator's claim and voted for them," "sowed
  doubt, framed it as reckless," "blended into the chorus of suspicion against the investigator,"
  "actively discredited the wolf's reasoning, labeled it 'noise'." Several success-framed ("eliminated
  a major threat," "blended perfectly").
- **Why that's poison for the SK specifically:** solo + night-immune → its ONLY death is a day-lynch,
  and the investigator is its existential threat (a check confirms it). So any active visibility —
  especially attacking the investigator — draws exactly the attention that kills it. One retrieved
  memory says it outright: "…contributed to a tie… However, it put the serial killer on the
  investigator's and vigilante's radar, directly leading to their elimination." The SK's optimal play
  is near-total passivity; memory pushes it toward activity (the same agency-induction as wolves,
  landing on the role least able to afford being seen).
- **The asymmetry (why SK net-negative, wolf flat):** WOLF = memory helps the night (power-targeting)
  AND hurts the day → offset → flat. SK = night already maxed (immune; survival unchanged 3.4→3.3,
  memory can't improve it) → NO offsetting gain → pure day-detectability harm → net-negative.

⭐**DIFFERENTIAL PREDICTION (falsifiable, for the running nethorizon arms):** the two failures have
DIFFERENT causes, so net-horizon should hit them differently. WOLF = an ADHERENCE gap (it overrode a
correct, well-framed memory — see player_5) → framing alone is the wrong lever → expect LITTLE
movement. SK = a FRAMING gap (its memories OVER-CREDIT active anti-investigator plays that actually
lead to lynching) → net-first reframing surfaces "active play → drew attention → lynched" → **expect
MORE movement on the SK arm than the wolf arm.** If the nethorizon SK lynched-rate drops while wolf
blending stays flat, this differential is confirmed; if both stay flat, the lever is application-layer
for BOTH (→ Phase B adherence work covers SK too). (Caveat: 5 decisions, qualitative, raw arm.)

## ⭐ TOWN per-role breakdown — the INVESTIGATOR is the town's wolf/SK (2026-06-12, descriptive N=30)

The town arm won +17pp as a faction, but that aggregate hides per-role variation. Breaking
`ab_arms_town` vs same-epoch baseline by individual power role (paired N=30, DESCRIPTIVE point
estimates — NOT significance-tested; the per-role proxies are the unvalidated noisy ones):

- **Healer — clear benefit:** survival 23%→40%, night-killed 73%→43%, town_save_rate 0.37→0.60.
- **Vigilante — clear benefit:** survival 20%→43%, night-killed 63%→40%, correct_shot 0.50→0.65,
  friendly_fire 0.33→0.27.
- **Investigator — the OUTLIER, but the MOST TENTATIVE read:** its CLEAN signals are actually fine —
  mislynched less (voted-out 40%→27%), survives slightly more (13%→23%), night-killed ~flat. The ONLY
  negative is `wolf_find` 0.43→0.33 / `threat_find` 0.56→0.46 — and that is precisely the MESSIEST
  proxy (find-rate / `found_wolf_day` already FAILED monotonicity earlier; investigators die fast → few
  investigations/game → high variance). So "memory hurts the investigator" rests on the one signal we
  trust least; the find-rate drop could be noise. What's more robust is the QUALITATIVE mechanism
  (social-read targeting whiffing on engaged town) — but that's 5 decisions. NET: a flagged LEAD, the
  weakest of the three per-role reads; healer/vig benefits rest on cleaner signals (survival,
  night-killed, validated save-rate) and are firm.

**Investigator mechanism (qualitative, 5 night-2 target choices, 3 hit / 2 whiff):** target selection
is SOCIAL-READ driven, not information-driven — "investigate the player most vocal against my claim /
actively steering the group / to fulfil a public promise and earn trust." The 2 whiffs were exactly
that heuristic landing on engaged TOWN members (a vocal villager, a steering healer). Its retrieved
memories are dominated by (a) investigator-died-early SURVIVAL anxiety ("my elimination meant I failed
to help") → pushes trust-building/survival over threat-hunting, and (b) "investigate the vocal/skeptical
player" precedents — several of which WHIFFED in the memory itself. → agency-induction again: imitating
a behavioral-heuristic play (social-read targeting) that looks skilled but is noisier than the role's
baseline, plus survival/trust-management crowding out pure information value. Caveats: 5 decisions,
noisy unvalidated proxy, and social-read targeting may be near-optimal given how little info an early
investigator has.

⭐**NAMED FOLLOW-UP (per-role, deferred):** (1) significance-test the investigator find-rate drop at
N=30 (Wilcoxon) — promote from descriptive if it survives; (2) the investigator is a candidate for the
SAME Phase B adherence/framing work as wolf/SK (its memories over-weight social-read targeting +
survival) — though net-horizon won't obviously help target SELECTION, so this is more likely an
injection-layer "weigh information value over social reads" item; (3) per-role breakdown should be a
STANDARD cut in future town arms, not just the faction aggregate — the aggregate masked it here.

**⭐Investigator find-rate drop = DENOMINATOR ARTIFACT (2026-06-12, `diagnose_investigator_confound.py`):**
the probe's raw wolf-find drop (0.43→0.33) doesn't survive luck adjustment. Town memory doubles
investigator survival → checks land deeper into wolf-depleted games, so the random-check expectation
itself falls (0.250 off → 0.208–0.228 on). Per-check LIFT over random is flat-to-up
(+0.110 off vs +0.094 raw / +0.243 rr / +0.160 all-on), check volume rises (1.67→~2.1/game), and
**distinct wolves identified per game rises** (0.60 → 0.63 raw / 0.90 rr / 0.83 all-on) — total
information delivered to town is UP. Threat-find (wolf OR SK) is stronger still: per-check rate
flat-to-up even UNADJUSTED (0.500→0.508/0.597/0.554 — the probe's 0.56→0.46 was per-game,
exposure-diluted), lift up in EVERY memory arm (+0.123→+0.163/+0.253/+0.209), distinct threats/game
0.83→0.97/1.20/1.20. Same trap family as kill-timing and conditioned blending
(survival/length-confounded rates). → Verdict: **no town analog of the wolf/SK harm**; all three town
power roles benefit or hold. AMENDS follow-up (1) above: significance-test the *lift*, not the raw
rate — a raw-rate Wilcoxon would confirm an artifact. The qualitative social-read-targeting read
stands (it's about target choice, not the rate metric) but loses its quantitative backing; keep
follow-up (2) as a Phase B audit item, not a known regression. Caveat: ~50–65 checks per arm →
SE on lift ~±0.07; this refutes the regression, it doesn't establish the rr improvement.

## ⭐⭐ FINAL — net-horizon arms scored, N=30 both (2026-06-12, `report_nethorizon.md`)

Scored against the pre-registration. Decisive contrast = nethorizon vs the v5_0-RAW arm (same
retrieval/seeds → isolates the outcome framing).

- **SK — framing-gap prediction SUPPORTED.** vs raw: `sk_lynched` 0.80→**0.63** (−17pp), win 20%→**37%**
  (+17pp). Net-horizon REMOVES the SK harm; vs baseline it lands ~even (0.63 vs 0.60; 37% vs 40%) →
  neutralizes the harm to memory-off level, does NOT exceed it. (My N=18 "slightly above baseline" was
  a small-N wobble that firmed up — flagged at the time.)
- **Wolf — adherence-gap prediction SUPPORTED.** vs raw: `unconditioned_blending` 0.639→0.668 (Δ+0.03,
  p=0.75) = FLAT; still far below baseline 0.851 (Δ−0.164, p=0.064 → the harm PERSISTS);
  `wolf_elimination_rate` slightly worse. Framing did NOT fix the wolf. Power-targeting preserved
  (night gain intact).
- ⭐**DIFFERENTIAL CONFIRMED (directionally):** SK moved (lynched −17pp, win +17pp); wolf barely
  (blending +0.03). Exactly the pre-registered call — net-horizon fixes the FRAMING-gap role (SK), not
  the ADHERENCE-gap role (wolf). The wolf/SK split is internally consistent.
- ⚠️**ALL NONSIG at N=30** (every proxy + win p>0.06; win underpowered by design). These are
  DIRECTIONAL confirmations of a prediction made BEFORE the data, NOT proven effects. The strength is
  the matched direction + internal consistency, not any p-value.

**Adoption (per the pre-reg "adopt-if-win before Phase B labels"):** net-horizon is a **Pareto-safe
improvement** — directionally HELPS the SK (removes harm), does NOT hurt the wolf (blending +0.03,
power-targeting preserved), and is the more *principled* extraction (leading with the net end-of-game
verdict is correct on its own terms, independent of the arm). ⭐RECOMMEND adopting it as the v5 default
extraction framing BEFORE Phase B labels are minted (obs rerank uses full entries → outcome wording is
label-visible → adopt-then-label, never mix). The wolf's residual harm is the named Phase B
**application-adherence** item (injection-layer: make the agent WEIGH the net verdict vs its
in-the-moment read), NOT another extraction change. Decision is the user's (directional evidence).

## ⭐ TOWN regression (pre-registered) + the all-on scoping rule (2026-06-12)

⭐**Why town needs its own regression:** the nh wolf/SK arms regression-tested the new prompt on stores
whose content was BROKEN (the harmful framing). Town is the OPPOSITE case — the family that
demonstrably BENEFITED from the old framing (+17pp) — and nothing has yet tested whether net-first
framing DISTURBS that benefit. So after extending the store with the 4 town roles (villager,
investigator, healer, vigilante), run a town regression.

**Pre-registration (REGRESSION check — null = PASS, not a hoped improvement):** `nh_town` on the
extended `v5_0_nethorizon` vs this epoch's `ab_arms_town` (same seeds, in-epoch; opponents memory-free
in BOTH, so the only delta is town's rewritten memory content). PRIMARY = the validated town basket
(`town_vote_accuracy`, `town_mislynch_rate`, `correct_elimination_rate`) HOLDS — does NOT degrade vs
old-framing town. Per-role secondary: healer/vig benefits hold. A null (≈ ab_arms_town) is a clean
PASS → the rewrite is safe for town. A drop = net-first disturbs town reasoning → investigate before
adopting.

⭐**Why NOT all-on for this:** on the new store the SK is fixed and wins more → town wins LESS, so an
all-on arm masquerades as a town regression when it's actually the SK fix working. All-on CANNOT
isolate the rewrite's effect on town. All-on has its own reserved slot: the **mandatory freeze-time
gate** (all-on + fresh baseline, run together, POST dedup-retune — tests the shipped config
holistically). Optional in-epoch `nh all-on` now (~$9) re-anchors the headline on the new store; if
run, its pre-registered pass condition is **town proxies holding** — town WIN-rate is ALLOWED to dip
below the old +23pp, because a functioning SK eats town wins (a dip there is the fix, not a regression).

## ⭐ Phase B item — BATCH-MERGE redesign for the split-outcome schema (2026-06-12)

The net-horizon schema changes what "duplicate" means for the batch-dedup MERGE step (online keep/drop
is unaffected — it composes outcome to one string, no merge). New merge logic:

- **Merge key becomes `situation + approach + net_verdict`, not situation alone.** Same situation +
  approach but DIFFERENT net verdict = NOT a duplicate — it's the CONTRAST that teaches "this move
  works here, fails there." And because retrieval is situation-only, both co-retrieve on the same query
  → the agent sees both "worked" and "failed" → learns context-dependence. Merging across verdicts
  would COLLAPSE exactly the signal net-horizon built. (same-ST/diff-LT → keep both; diff-ST/same-LT →
  likely merge; the verdict dominates.)
- **Metadata merge** (splits into freeze-safe CODE vs Phase B PROMPT): `observation_count` → SUM;
  `net_verdict` → only same-verdict entries merge so it's preserved (no "mixed" fudge); `source_game_
  winner`/`role_faction_won` → a single value is meaningless post-merge → aggregate into a RATE
  (fraction of merged source-games the role won) = strictly more useful, a soft per-approach
  success-signal. The aggregation is apply-layer CODE (freeze-safe, specc-able now); the similarity
  decision is the MERGE PROMPT (the one freeze carve-out, inside the Phase B labelling cycle).
- **Bonus (helps the documented "merge under-fires on verbose v5 entries"):** feed the merge prompt the
  STRUCTURED fields (situation/approach/immediate/impact/net_verdict), not the prose blob, so it
  compares on the right dimensions. Needs a FRESH golden merge set on net-horizon entries (old set is
  pre-split-schema, OOD).

## ⭐ Town regression — drift adjudication + pre-registered interim stop (2026-06-12, BEFORE N=20)

**Logged before the data to keep the stop honest.** The town regression (`ab_nh_town` vs `ab_arms_town`)
showed a large early FAIL signal at N=10 — paired, same game_ids: villager win 70%→30%, town_vote_accuracy
0.917→0.559, mislynch 0.150→0.475, correct_elim 0.850→0.525 (4/4 basket proxies wrong-way). But the two
arms are **cross-day** (raw `ab_arms_town` 06-11 13:11, `ab_nh_town` 06-12) — fingerprints show identical
model IDs (`gemini-3.1-flash-lite` / `gemini-2.5-pro`) but a ~25h gap can't exclude silent server-side
drift under the same ID. (The N=10 raw side is also a lucky strong subset: 0.917/70% vs the raw arm's true
0.710/43% → the −0.36 is inflated and will shrink as the raw side regresses to mean.)

**Drift gate (must pass FIRST):** canary `ab_canary_0612` = 10 no-memory `all_disabled` games on the exact
`ab_baseline` seeds, today's epoch. Memory-off → isolates pure model drift. Clean (`town_vote_accuracy`
≈ 0.560, villager win ≈ ab_baseline) → no drift, regression real, yesterday's raw stays a valid comparator.
Material move → confound; the whole nh-vs-raw set must re-pair against FRESH same-epoch raw arms (nh arms
themselves stay — already today's epoch; original 06-11 paired A/B is within-day, untouched).

**Pre-registered interim stop @ N=20:** IF canary clean AND paired `town_vote_accuracy` Δ ≤ −0.10 AND
≥3/4 basket proxies still wrong-way → **STOP**, conclude net-first FAILS the town regression, report as a
planned interim stop at **N=20** (never rounded to the pre-registered N=30). ELSE (gap within ~±0.05, or
proxies mixed) → run full 30 (the ambiguous zone where the last 10 games carry information). Legitimate as
asymmetric early stopping: halting a regression in its pre-registered FAIL direction at a large effect,
not p-hunting a positive. If net-first fails town, adopt it **per-namespace** (wolf/SK net-first, town keeps
old framing — role namespaces independent, store already split), not globally.

## Code pointers

- Net-horizon: `scripts/build_nethorizon_store.py` (`--seed-from` adds roles to an existing store),
  `situation_sim.py`, design `nethorizon_design.md`;
  schema `Agents/schemas/memory.py` (Observation outcome split), prompt `Agents/prompts/extraction.py`.
- Echo read: `echo_read.py` (+ `echo_read_decisions.json`); diagnostics `diagnose_wolf_sk_proxies.py`
  / `diagnose_wolf_blending.py` / `diagnose_investigator_confound.py`.
- Seed pinning: `scripts/run_batch.py --game-ids-file` → `run_game(game_id=…)` →
  `build_game_config` → `initialize_game` (role draw `crc32(game_id)`).
- Seed-set generator: `scripts/make_ab_seed_set.py`.
- Treatment presets: `MEMORY_CONFIGS` / `RETRIEVAL_TYPES_CONFIGS` in `run_batch.py`; `top_k`
  in `Agents/memory/enrichment/pipeline.py`.
