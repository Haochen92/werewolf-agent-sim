# Labeling Pipeline — Build-Journey Log

> **What this is.** The chronological story of how the labelling apparatus came to be, distilled from the
> rounds where it was actually used — the dedup classifier, the reranker, and the context-eval golden.
> It is a **synthesis with pointers**: the primary, frozen records live in those folders (linked inline);
> this log pulls the *highlights that matter for the apparatus* — especially the points where the current
> tooling hit a wall and a human had to step in by hand, because those walls are what motivate the build
> in [`plan.md`](plan.md). Companion reference: [`report.md`](report.md).
>
> **Chronological-supersession contract:** earlier rounds are shown as they happened, including findings
> later rounds refined; `(→ §N)` is navigation, not laundering. Sources footer at the end.

## ① Motivation — why a labelling *factory* at all

By mid-2026 two workstreams both needed the same scarce thing: **trusted golden labels at volume.** The
dedup-classifier fine-tune needed 500–1,000 labelled Keep/Discard cases; only **65 human-labelled cases
existed** (`../../fine_tuning/dedup_classifier/experiment_log.md`). The retrieval reranker needed graded
0/1/2 relevance labels. And the cheap LLM-judges across the eval funnel needed a *gold* to be validated
against at all.

Prompt engineering had plateaued — the best dedup prompt (v11b) sat at ~83% vs the 65-case golden — so the
incumbent answer, "just write a better prompt," was a defensible but exhausted lever: a prompt can bias a
model toward a class, but it can't reshape its decision boundary. The other incumbent, **human-only
labelling**, is the gold standard for *correctness* but does not scale — hand-labelling 1,000 cases is
not a solo-project budget. **Root cause:** we had no way to produce labels that were both *trustworthy*
and *plentiful* — no golden-label factory with a quality-control bench.

## ② Design — multi-model co-labeling triage

The proposed design, from first principles: **independent voters make agreement a signal, and humans
spend their budget only where the signal is weak.**

- Run a small **panel** of models over every item.
- Where the panel **agrees**, provisionally auto-label (cheap, scales with the corpus).
- Where it **disagrees**, route to a **human** (expensive, but capped at the hard minority).
- **Merge** model + human labels into one golden set.

**Alternatives weighed and rejected.** *Human-only* — correct but unscalable (the budget problem above).
*Single strong model* — scales, but inherits one model's blind spots and produces no agreement signal to
triage on. The panel buys both scale *and* a triage signal a single model can't give.

**Virtue, by construction (not yet validated — that's ③):** the human cost becomes *fixed-ish* (you only
pay for disagreements), and agreement gives a free first-pass confidence proxy. The open question the
design does **not** answer up front — and which ③ turns out to hinge on — is whether *agreement actually
means correctness.*

## ③ Implement → Verify → Decide

### 3a. Round A — dedup classifier: 3-model panel, and the bias that broke the assumption

**Implement.** Three Gemini flash models (3.5-flash, flash-lite, 2.5-flash) labelled 863 LLM-decided dedup
cases in parallel; split into **619 unanimous / 244 disagreement**
(`../../fine_tuning/dedup_classifier/experiment_log.md` §"Co-labeling Results").

**Verify — *Catches:* is panel agreement trustworthy enough to auto-label on?** The disagreement review
came back lopsided: **majority-D was wrong 37% of the time, majority-K only 7%** — a strong, directional
**D-bias shared across all three models.** That asymmetry was alarming enough to audit the *supposedly
safe* tier: of **373 unanimous-D** cases, **21.4% flipped to K** on human review.

**Decide.** Unanimity is **not** automatically safe. The efficient rule became: auto-label the K-majority
tiers (~5–7% error), **human-review every D-majority and unanimous-D case.** The deeper finding, and the
first wall: **three same-vendor models share a correlated bias, so their *unanimous agreement* can be
confidently wrong** — "agreement that looks like reliability but is shared blindness." Crucially, *every
bit of this was discovered by hand* — manual review tables, computed in prose. The tooling produced the
votes; it had no way to detect the skew.

### 3b. Round B — reranker: the reusable module, and vendor diversity that *still* shared bias

**Implement.** The ad-hoc dedup labelling scripts were generalized into the reusable
`evaluation/labeling/` module (engine / voter / merger / exporter + adapters; `merger` later retired
2026-06-29 → `pipeline.consolidate`, which actually composes — see [`report.md`](report.md)) — the front half described
in Appendix A §1 below (`../../fine_tuning/cross_encoder/reranker/experiment_log.md` §"Reusable
labeling pipeline"). Acting on Round A's lesson, the reranker round **diversified the panel across
vendors**: flash-lite, Mistral and Llama 3.1 8B on NIM, with ChatGPT and Claude Sonnet run by hand as two
more voters (*corrected 2026-10-23*; the source log calls the result "all-LLM ground truth").

**Verify — *Catches:* does vendor diversity decorrelate the bias Round A found?** Partly, but not enough.
The three *auto* models **systematically inflated relevance** vs ChatGPT (which had full game context):
44% grade-2 vs ChatGPT's 31%, and the auto models **agreed with each other (71–74%) more than with
ChatGPT (56–68%)** (§"Systematic auto-model bias in new labels"). The shared over-crediting was caught
**only by the different-class judge**, not by any intra-panel statistic.

**Decide.** Vendor diversity helps but does not eliminate correlated bias; **a panel cannot self-validate
— only an external, different-class instrument (a strong judge, ultimately a human) can catch a shared
blind spot.** Second wall: the module could now *run* a diverse panel, but still had no calibration step;
the over-crediting was, again, found and quantified by hand.

### 3c. Round C — context-eval: locating the bias, and writing the protocol

**Implement / Verify — *Catches:* when the weak labeler and strong judges disagree, who is right, and by
how much?** On 400 items, panel-vs-strong-judge agreement was measured with a **95% CI ≈ ±4.9%**, and the
analysis **located** the reranker label bias precisely: the leak lived in the *majority* tier, while the
"unanimous" tier had looked clean only because it *included a careful strong judge* — "agreement that
contains a careful judge," not "agreement is safe" (`context_eval/experiment_log.md`).

**Decide.** These three rounds had, between them, hand-derived every piece of a real validation
methodology. Round C wrote it down as a **pre-registered protocol** (`context_eval` §6): rubric-first;
a stratified **human anchor** (~150 judgments); a vendor-diverse panel; **calibrate panel→human with an
acceptance test** (agreement ≥80%, 95% CI lower-bound ≥75%, no significant directional bias);
**staged bias detection** (McNemar for presence, **TOST** for absence, vs a pre-registered δ);
the **"unanimity is suspect a priori"** tier audit; and a **sample-size table** (±10%→~62 judgments,
±8%→~96, ±5%→~246). This protocol *is* the design for the pipeline's missing second half.

### 3d. Aside — dedup-prefilter: the sample-size lesson

A parallel thread made the confidence point concrete: a strategy-point eval set of **25 cases** could not
distinguish an 8% difference — the 95% CIs "overlap heavily at this sample size; we need 100+ cases"
(`../../fine_tuning/cross_encoder/dedup_prefilter/experiment_log.md`). This is why the build includes a
**sample-size calculator** and frames the human anchor as a *fixed* cost set by the target CI half-width,
not by corpus size.

## ④ Limitations / future work

Criticality-ordered; freshness **2026-06-29**. Full gap list + the closing artifacts: Appendix A §3 below; the build: [`plan.md`](plan.md).

1. **The validation half is not code (HIGH).** Across all three rounds, the calibration that made the
   labels *trustworthy* — the per-tier error rates, the directional-bias finding, the agreement CI — was
   done **by hand, every time.** The reusable module captured only the *production* front (panel → vote →
   route → merge). The pipeline can make labels; it cannot yet say whether they are right.
2. **Correlated panel bias is the central risk, and it is invisible to the current tooling (HIGH).** Rounds
   A and B both showed a same-/similar-vendor panel sharing a directional bias that *intra-panel agreement
   cannot reveal* — only an external instrument caught it. The module's only agreement code is a
   descriptive tally. Detecting this needs the McNemar/TOST + tier-audit layer (plan.md).
3. **No confidence interval, and design-effect makes a naive one wrong (MEDIUM-HIGH).** Judgments cluster
   within a case; a plain binomial CI on the anchor would overstate precision. The build needs a
   cluster-robust (by-case bootstrap) CI.
4. **Everything above is gated on a human anchor + a stable substrate (context).** The protocol carries an
   explicit execution-deferred banner; the labels would be built on about-to-change games. So the second
   half is *designed and primitive-ready, deliberately unbuilt* — not an oversight.

**The arc, in one line:** we built a label factory, learned three times over that a model panel can be
confidently wrong in a way only a human can catch, wrote the protocol that turns that lesson into a
quality-control bench — and that bench is the build still ahead of us.

## Sources

Primary frozen records (this log is their apparatus-level synthesis):
`../../fine_tuning/dedup_classifier/experiment_log.md` · `../../fine_tuning/cross_encoder/reranker/experiment_log.md`
(§"Reusable labeling pipeline", §"Systematic auto-model bias") · `context_eval/experiment_log.md`
(§6 "The labeling protocol") · `../../fine_tuning/cross_encoder/dedup_prefilter/experiment_log.md`.
Code: `evaluation/src/labeling/`. Companions: [`report.md`](report.md) · [`plan.md`](plan.md).

*(Build-journey log, drafted 2026-06-29. Subject to revision as the labelling + scorer inspection continues.)*

## Appendix A. The pipeline as built (the report's 2026-06-29 text, moved here 2026-10-23)

*Kept as written then, with one dated correction. Section numbers are the old report's.*

### 1. Current capabilities — what the pipeline does today

Present-tense contract, enforced in `evaluation/src/labeling/`:

**Given** a candidates file + a `LabelingAdapter` for the domain, the pipeline **produces** a consensus
golden-label set with a per-item agreement category, plus a `ties.json` of unresolved disagreements
routed to a human. Concretely:

| Stage | Module | What it guarantees |
|-------|--------|--------------------|
| **Single entry point** | `pipeline.py` (`run`/`label`/`export`/`consolidate`) | **NEW 2026-06-29** — one config-driven staged CLI assembling the automated stages: `LABEL → [EXPORT off-ramp] → CONSOLIDATE`. `run` = LABEL→CONSOLIDATE (no-human fast path). Before this, the pieces had no caller and couldn't compose (see *Topological flow* below). |
| **Multi-model labelling** | `engine.py::label_items` | Runs *N* models per item concurrently, **per-model token-bucket rate limiting**, checkpoint-every-*k* + **resume**. Adapter-pluggable; optional **structured output**. |
| **Consensus vote** | `voter.py::vote` | Per-item consensus → a **categorical** confidence: `unanimous` / `majority` / `tie_tiebreaker` / `tie` / `no_response`. **Rule:** majority = strict >½; an unresolved tie / no-consensus is **routed to a human**; an optional tiebreaker model can break ties. |
| **Consolidate** | `pipeline.py::stage_consolidate` | Votes across each engine entry's `model_scores` **+ human label files** (keyed by the entry's own `case_index:key`); emits consensus + `ties.json` + agreement tally. **Adapter-agnostic + multi-model-native** — replaces the now-**deleted** `merger.merge` (reranker-era: one-model-per-file + composite-key only, never composed with `dedup`). |
| **Human export** | `exporter.py::export_for_manual` | Batched markdown for hand-labelling in ChatGPT/Claude. Driven by `pipeline export`. |
| **Domain adapters** | `adapters/{reranker,dedup,context_relevance}.py` (+ `get_adapter` factory) | Per-task rubric prompt + response parsing + key normalization. New tasks subclass `LabelingAdapter` (`base.py`). `dedup` also opts into **structured output** (`response_schema`/`parse_structured`) for parse-robust golden minting. |
| **Dedup golden driver** | `dedup_golden_builder.py` | Runs `engine.label_items([one ModelSpec], DedupAdapter)` → the `eval_auto_dedup` golden shape. **Folds in the old `auto_dedup_labeler`** (deleted 2026-06-29) so the engine+adapter path — not a hand-rolled loop — mints the dedup golden. *Correction 2026-10-23: its default model moved from `gemini-2.5-pro` to Claude Haiku 5.5 on 2026-10-12 (commit `e70f1627`); no golden has been minted with the new default on record.* |
| **Human / retrieval CLIs** | `manual_labelers/{batch_dedup,situation_retrieval,day_summary}_labeler.py` | Interactive `show/sample/label/progress` tools (one runs live-store retrieval). **Not adapters, no panel, no copy-paste export** — the human labels in-terminal ("mode 3"). They don't fit the per-item LLM shape (cluster-MERGE ops, golden-query authoring, coverage annotation), so they're grouped in `manual_labelers/` (moved 2026-06-29) rather than the pipeline proper. |
| **Config** | `config.py` | `LabelingPipelineConfig` (the entry-point config) · `ModelSpec` · `VotingConfig` · `ExportConfig`. JSON-serializable, same pattern as `core/config_schema`. (The dead `LabelingRunConfig`/`MergeConfig`/`ManualSourceConfig` were removed with `merger`.) |

**In one sentence:** the pipeline can run a vendor-diverse panel over a corpus, fuse it into consensus
labels, split the corpus into *auto-labelled* (panel agrees) vs *routed-to-human* (panel disagrees), and
**merge the returned human labels into the final golden** — it is **human-in-the-loop by construction**,
the front half of the protocol in [`experiment_log.md`](experiment_log.md) and `context_eval` §6. (What it
does *not* yet do is tell you *which* agreements are safe to keep without a human — that's §3.)

#### Topological flow (how to run it)

```
   CONFIG (LabelingPipelineConfig): candidates + adapter + models + output_dir
                          │
  ┌──────────────────── AUTOMATED ──────────────────────────────────┐
  │  [1] LABEL        pipeline label  → model_scores.json             │
  │         (optional human off-ramp ↓ instead of / alongside [1])    │
  │  [E] EXPORT       pipeline export → export_batches/*.md           │
  │         🧑 human labels in ChatGPT/Claude → response file         │
  │  [2] CONSOLIDATE  pipeline consolidate (+ manual_sources)         │
  │         → consensus_golden.json + ties.json                      │
  └──────────────────────────┬───────────────────────────────────────┘
              🧑 human resolves ties.json → add as a manual_source → re-consolidate
                             │
  ┌──────────── NOT YET BUILT (plan.md second half) ─────────────────┐
  │  [3] CALIBRATE  panel-vs-human agreement+CI, McNemar/TOST, audit  │
  └───────────────────────────────────────────────────────────────────┘
```

- **No-human run:** `pipeline run --config run.json` (LABEL → CONSOLIDATE).
- **Copy-paste run:** `pipeline export` → label batches in ChatGPT/Claude → save responses → set
  `manual_sources` in the config → `pipeline consolidate`.
- **Resolve disagreements:** resolve `ties.json`, add it as a `manual_source`, re-run `consolidate`.

**Why staged, not one call.** Each human point (EXPORT copy-paste; ties resolution; the CALIBRATE
anchor) is a *stage boundary*. A single non-stop entry point can't pause for a human; a staged +
resumable CLI can.

**What assembling it fixed (an apparatus finding).** Before 2026-06-29 the consolidation pieces
(`merger`/`exporter`) had **no caller and had never actually run end-to-end** — every golden to date was
stitched together by bespoke per-domain code, not by the reusable module. Wiring the stages into a single
entry point (`pipeline.stage_consolidate`) is what surfaced that they didn't compose; the new path votes
across the panel's per-model scores directly and is **adapter-agnostic + multi-model-native**
(smoke-tested in `tests/evaluation/test_labeling_pipeline.py`). The superseded `merger.merge` was
**retired** (git history preserves it).

### 2. How we know the current capabilities work (verification)

Not asserted — *used*, **with humans doing the load-bearing labelling**. The triage front produced two
real golden sets, and in both the human was decisive, not decorative:
- **Dedup classifier** — 3-model panel over 863 LLM-decided cases → 619 unanimous / 244 disagreement →
  **humans reviewed all 244 disagreements *and* audited the 373 "safe" unanimous-D cases (617 manual-review
  records), correcting ~26% of the baseline model's calls** → the 863-case D/K golden (see
  [`experiment_log.md`](experiment_log.md) §3a, source: `../../fine_tuning/dedup_classifier/experiment_log.md`).
- **Reranker** — round 1: a four-model panel (ChatGPT, flash-lite, 3.5-flash, Qwen) with manual review
  correcting 14 of 84 reviewed items; round 2: a five-model vote over 1,848 items (flash-lite, Mistral,
  Llama 3.1 8B on NIM, and ChatGPT and Claude Sonnet run by hand as voters, not as a human review) → the
  0/1/2 relevance golden. *Correction 2026-10-23: this bullet first called ChatGPT and Sonnet "human
  manual batches" and put the 14-of-84 review in the vendor-diverse round; the source log calls round 2
  "all-LLM ground truth".* (source: `../../fine_tuning/cross_encoder/reranker/experiment_log.md`). Here too the
  human was decisive — and the round's lesson (the auto models **over-credited relevance together**,
  caught only by a different-class judge, not by intra-panel agreement) is the second piece of evidence
  for §3's headline gap.

So the front half is **load-bearing and exercised**, and **the goldens are panel + human merges** — not
model-only auto-labels. What the pipeline *cannot* do is **measure** when the panel is trustworthy enough
to keep the cases a human *didn't* read — turn "the panel agreed" into a calibrated confidence. That is §3.

### 3. Limitations + what we plan to build (known gaps)

Criticality-ordered (likelihood × impact × detectability). Freshness: **verified 2026-06-29** against the
current `evaluation/src/labeling/` tree; *re-checked 2026-10-23: none of the seven gaps has been closed*.
The build that closes them is [`plan.md`](plan.md); each gap below names the artifact that will close it.

1. **No panel→human calibration / acceptance test — criticality: HIGH.** Human labels *exist* and are
   merged in (above) — the gap is **code that statistically compares the panel to a human anchor**, so the
   pipeline cannot certify "the panel is trustworthy enough to auto-accept the cases no human read." The
   protocol's acceptance gate (agreement ≥80%, 95% CI lower-bound ≥75%, no significant directional bias)
   was computed **by hand** in every round. → builds `calibration.py::calibrate()` + the gate.
2. **No statistical bias detection — criticality: HIGH.** The most important empirical finding of the
   labelling work is that **a same-vendor panel shares a correlated bias that intra-panel agreement
   cannot reveal** (the dedup D-bias; the reranker over-crediting — §3 of the log). The module's only
   agreement code is `voter.agreement_stats`, a **descriptive tally** — it cannot detect directional
   skew. → builds `calibration.py::bias_test()` (McNemar/sign for *presence*, TOST for *absence* vs a
   pre-registered δ).
3. **No confidence interval on the labelling — criticality: MEDIUM-HIGH.** The voter's "confidence" is
   *categorical* (how the panel voted), **not statistical** (how much to trust it vs truth). There is no
   agreement CI, and — critically — judgments **cluster within a case** (design effect), so a naive
   binomial CI would *overstate* precision. → builds a **cluster-robust (by-case bootstrap) agreement CI**
   + a `sample_size_for_ci()` calculator (the ±X%→N table).
4. **No per-judge / unanimity-tier audit — criticality: MEDIUM.** The protocol's "unanimity is suspect a
   priori" insight needs the skew test run *on the unanimous-agree subset specifically*; and per-judge
   skew (which vendor pulls which way) is never reported. → builds `calibration.py::tier_audit()` + a
   per-judge skew table.
5. **No inter-annotator κ — criticality: LOW.** When a 2nd human dual-labels a slice, there's no Cohen's
   κ. → builds `cohens_kappa()`.
6. **No stratified anchor sampler — criticality: MEDIUM (it gates everything above).** The calibration
   needs ~100–250 human *judgments* stratified by type × agreement-pattern × role, oversampling the
   confident-agree zone, spread across cases. The existing `data/sampling.py` samples *game cases* (wrong
   unit). → builds `anchor.py`.
7. **Rubric parity human↔panel — criticality: LOW.** The panel prompt embeds the rubric
   (`adapter.format_prompt`), but `exporter.format_for_manual` is generic — the human and the panel should
   judge against the *identical* rubric + worked edge cases. → small `exporter`/adapter extension.

**The through-line:** items 1–4 are one missing capability — *the pipeline can produce labels but cannot
say whether they are right*. It is a factory with no quality-control bench. The protocol that designs the
bench already exists (`context_eval` §6); the statistical primitives already exist (`core/stats.py`:
Clopper–Pearson `binomial_ci`, exact `mcnemar_exact`); what's missing is the ~one module that wires them
to a human anchor. That is [`plan.md`](plan.md).

### 4. The build plan (summary)

Full plan: [`plan.md`](plan.md). In brief: a new `calibration.py` + `anchor.py`, three small `core/stats`
additions (TOST, κ, cluster-robust agreement CI), a `CalibrationConfig`, and a thin staged driver that
runs `panel → sample → [human pause] → calibrate → decide(stop/expand) → gold`. Sequenced MVP-first
(Phase 1 = the acceptance test on pure `core/stats` reuse). **Gated**, not urgent: it needs a
vendor-diverse panel run, ~100–250 human judgments, and a stable substrate — so the build unlocks value
only when labelling restarts (which is itself gated on v7 proving memory compounds).

> *Correction 2026-10-23.* That gate resolved the other way. The v7 compounding test closed negative in
> July 2026 (town decision score 0.147 lower with memory, p≈0.06, pre-registered; owner closed the
> memory research on 2026-07-21; [`../../execution_plan/report.md`](../../execution_plan/report.md)).
> Labelling through this pipeline has not restarted. The October 2026 labelling on the ten-seat game was
> done instead by Claude model readers launched from the chat, reading packets with the answer hidden
> (§5.3 and the v8 records). Those readers bypass the panel, the vote and the human export, so none of
> the October reference sets has panel agreement or a calibration behind it.

### 5. Other reference sets (added 2026-10-23)

Three answer keys outside the pipeline, each made for one calibration or check. A reference set here is
only as good as whoever labelled it, so each section says who did.

#### 5.1 The embedding prefilter's calibration sets (May and October 2026, nine-seat content)

**What it is.** The *prefilter* is the no-model first layer of online dedup: it auto-keeps a new memory
whose embedding similarity to every stored candidate is low, auto-discards one whose similarity is
near-identical, and sends the middle to the dedup model. Its four thresholds are calibrated against
labelled pairs. Record: [`../../dedup/embedding_prefilter/experiment_log.md`](../../dedup/embedding_prefilter/experiment_log.md).

**How it works.** Two sets, swept for the widest thresholds with zero labelled errors:
- the 65-case online dedup golden (`evaluation/frozen_eval_sets/dedup_v2_golden_labels.json`), labelled
  by a human over two sessions and two revision rounds ([`dedup.md`](dedup.md));
- a 232-case cross-game set (`evaluation/frozen_eval_sets/auto_dedup_v1_cross_game.jsonl`), built by
  searching five games' extractions against a store from five other games, and labelled keep or discard
  by running the production dedup prompt through `gemini-3.5-flash` and `gemini-3.1-flash-lite`. The two
  models agreed on 175 of 232 (75.4%); flash-lite leaned heavily to discard.

**What it can claim.** On `gemini-embedding-001` (May 2026), the 232-case set caught a small-sample
artifact in the 65: a strategy-point discard line of 0.90, clean on the 25 golden strategy points, would
have misfired on the broader set, so the line was set at 0.93. That is the set doing its job.

**How far it was checked.** Three findings from the 2026-10-14 revisit, two of them corrections:
- When the store moved to `qwen/qwen3-embedding-8b` on 2026-10-12, the thresholds were re-derived on the
  65 human cases only. Re-embedding the 232 showed they do not hold there: the strategy-point discard
  line would auto-discard two labelled keeps (`evaluation/experiments/prefilter_similarity_exhibit.py`;
  `data/cross_game_sims_by_embedder.json`). That path is dormant live, so no harm followed, but the
  calibration rests on the small, old set again.
- The May observation counts do not reproduce from the cache stored beside the record; the record now
  reads those boundaries as near-zero-error, not zero-error.
- The July move to `gemini-embedding-2` never remapped the thresholds; found in October and left, since
  that path was retiring.

The 232 labels are model labels. Their 75% inter-model agreement and the known discard lean of one
labeller are the only check on them; no human read of the 232 is recorded. Both sets hold nine-seat,
v4-era memories. Code: `evaluation/src/studies/{eval_auto_dedup,auto_dedup_dataset_builder,batch_dedup_merge_eval}.py`,
`scripts/sweep_2d_thresholds.py`.

#### 5.2 The tell detector's labelled cases (July 2026, nine-seat)

**What it is.** A *tell* is a public behaviour that hints at a hidden role. A detector that cannot see
the roles (`evaluation/src/loop/tells.py`) scans each player of each game for a fixed checklist of
behaviours; code joins the revealed roles afterwards. The labelled cases measure whether the detector
finds what is there. Record: [`../../extraction/tell_extraction/report.md`](../../extraction/tell_extraction/report.md)
§4; [`experiment_log.md`](../../extraction/tell_extraction/experiment_log.md) ⑧, ⑩, ⑪.

**How it works.** Forty cases from five games: 20 drawn from the detector's own detections and 20 from
places it found nothing on leading behaviours. Five Claude Opus adjudicators, one per game, labelled them
without seeing the detector's answers. Then the owner reviewed every detection in one game. Probe code is
frozen in `evidence/extraction/tell_extraction/scripts/` (`golden_sampler.py`, `golden_score.py`,
`owner_golden_build.py`).

**What it can claim.** On those 40 cases, the cached detector (the default since 2026-07-13) was right on
0.93 of its discussion detections and found 87% of the labelled discussion behaviours; on votes, 0.83
and 77%. The owner upheld 7 of 8 detections in the game reviewed. That supports using the detector in
the research loop, not a general accuracy figure.

**How far it was checked.** The labels are model labels with one human-checked game behind them. Half
the cases came from the detector's own output, which limits how independent the check is. A six-game
human benchmark (24 cases) was built and then relaxed after the first game. The detector is nine-seat
research code; nothing has been detected on a ten-seat game.

#### 5.3 The readers' duplicate groups for the point dedup (2026-10-13, ten-seat)

**What it is.** Four Claude Sonnet subagents each read a quarter of the cells of the 40-game ten-seat
store (605 synthesized strategy points) against the pool's rules block. They marked points that state a
wrong rule and grouped points that give the same move in the same situation and stage. They found 65
duplicate groups, 78 points to drop. Those groups then served as the reference for a dry run of the
batch point dedup. Record: [`../../memory_system/v8/experiment_log.md`](../../memory_system/v8/experiment_log.md),
the entries of 2026-10-13; reader output `memory_system/v8/data/reextract/points/`.

**How it works.** `evaluation/experiments/v8_sp_dedup_dry_run.py` runs the point dedup without writing,
with its production judge (`gemini-3.1-flash-lite`), under two ways of splitting a cell before comparing
(by direction and honesty, or by honesty only), and counts how many of the readers' groups it catches.
Output: `memory_system/v8/data/reextract/dedup_dry_run/`.

**What it can claim.** Against the readers' groups, the dedup caught 9 of 65 under the production split
and 16 of 65 with the looser one, and 25 of its 55 drops under the looser split merged points from
different stages. That located the problem in the judge, not only the split.

**How far it was checked.** The reference is one pass by model readers. The readers were not
interchangeable: on the rule screen, one quarter flagged 4 errors and another 13. The record gives no
per-reader duplicate counts and no human read of the groups. The groups were applied when the published
store `ten_seat_v2` was built (owner, 2026-10-13), so they are used as labels without a check of their own.

### Sources

| What | Where |
|---|---|
| The pipeline | `evaluation/src/labeling/{engine,voter,exporter,base,config,pipeline}.py`, `adapters/{reranker,dedup,context_relevance}.py`, `dedup_golden_builder.py`, `manual_labelers/` |
| Scorers that read the goldens | `evaluation/src/labeling/label_scorer/` (NDCG, reranker comparison); dedup: `evaluation/src/audits/{dedup_score,batch_dedup_score}.py`, see [`dedup.md`](dedup.md) |
| Statistical primitives to reuse | `evaluation/src/core/stats.py` |
| Tests for the pipeline | `tests/evaluation/test_labeling_pipeline.py`, `tests/evaluation/test_dedup_golden_builder.py` |
| Design spec for the unbuilt half | `context_eval/experiment_log.md` §6 |
| Journey and limitation evidence | [`experiment_log.md`](experiment_log.md); `../../fine_tuning/dedup_classifier/`, `../../fine_tuning/cross_encoder/reranker/`, `context_eval/`, `../../fine_tuning/cross_encoder/dedup_prefilter/` |
| Prefilter calibration sets | `evaluation/frozen_eval_sets/dedup_v2_golden_labels.json`, `auto_dedup_v1_cross_game.jsonl`; `../../dedup/embedding_prefilter/` (log and `data/`); `evaluation/experiments/prefilter_similarity_exhibit.py`; Qwen re-derivation in `../../memory_system/v8/data/embedder_migration/` |
| Tell-detector cases | `evaluation/src/loop/tells.py`; `../../extraction/tell_extraction/outputs/` (`adjudication_cases.json`, `golden_verdicts.json`, `owner_golden/owner_verdicts.json`); frozen probes in `../../extraction/tell_extraction/scripts/` |
| Readers' duplicate groups and the dry run | `../../memory_system/v8/data/reextract/points/`; `evaluation/experiments/v8_sp_dedup_dry_run.py`; `../../memory_system/v8/data/reextract/dedup_dry_run/` |

## Appendix B. Every key, and the planned ones (inventory of 2026-10-23)

The table of every built key is in [report.md](report.md). Keys designed or planned but not built:

| Planned key | Status | Where it is planned |
|---|---|---|
| `calibration.py` + `anchor.py`: the panel measured against ~100–250 human judgments | Not built | [plan.md](plan.md) |
| Two retrieval golds (summary recall; reranker pure-query) with a ~150-item human anchor | Deferred 2026-06-01 | `context_eval/experiment_log.md` §6 |
| Application (strategy-adoption) judge, ~28 blind labels | Never run | `../../memory_system/strategy_adoption/judge_validation_protocol.md` |
| Owner session on the factual-error judge, 50–100 verdicts | Pending | `writeup/map.md`, "Evaluation hardening tasks" |
| Owner checks of the silence readers and the rule-error readers, 30–50 items each | Pending, conditional | `writeup/map.md`, same section |
| Owner hand check of the discussion-evidence judge | Not done | [llm_judge](../llm_judge/report.md) |
| Reference-point keys for the day-summary, post-game and situation-summary judges | Planned only | `../llm_judge/golden_set_method.md` |
| 20–30 hand labels on frozen merge outputs (fabrication) | Suggested | [dedup.md](dedup.md) |
| Six-game owner tell benchmark (24 cells) | Relaxed after one game | `../../extraction/tell_extraction/outputs/owner_golden/` |
| A larger dedup key (100–150 cases; 100+ strategy points) | Planned | `../../fine_tuning/dedup_classifier/experiment_log.md`; `../../fine_tuning/cross_encoder/dedup_prefilter/experiment_log.md` |
| A ~20-case subset re-scored against model drift | Guard rule only | `../experimental_controls/drift_surfaces_and_guards.md` |

**Mismatches between records, found by the inventory.** Not corrected at source (the records are frozen):
- The online dedup key's file metadata says "50 sampled … 25/25" and "D=31, M=2, K=32"; its 65 labels count
  K34 / D30 / M-K 1. `dedup_v2_tricky_cases.md` still shows a merge label, although merges were relabelled
  keep at v11.
- The batch dedup key has 149 items in the file and the batch log; the dedup classifier log says 152.
- The dedup classifier set is 863 cases (390 D / 473 K) in its own log and 861 (389 / 472) in the prefilter log.
- The situation-retrieval key's description says "40 + 69" cases; the file and the reranker log hold 108.
- The "82% within-band agreement" in `judge_validation_protocol.md` is an example of how to report the
  result, not a measured number.
