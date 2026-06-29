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
in [`report.md`](report.md) §1 (`../../fine_tuning/cross_encoder/reranker/experiment_log.md` §"Reusable
labeling pipeline"). Acting on Round A's lesson, the reranker round **diversified the panel across
vendors**: ChatGPT + flash-lite + Mistral + NIM.

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
contains a careful judge," not "agreement is safe" (`../../retrieval/context_eval/experiment_log.md`).

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

Criticality-ordered; freshness **2026-06-29**. Full gap list + the closing artifacts: [`report.md`](report.md)
§3; the build: [`plan.md`](plan.md).

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
(§"Reusable labeling pipeline", §"Systematic auto-model bias") · `../../retrieval/context_eval/experiment_log.md`
(§6 "The labeling protocol") · `../../fine_tuning/cross_encoder/dedup_prefilter/experiment_log.md`.
Code: `evaluation/src/labeling/`. Companions: [`report.md`](report.md) · [`plan.md`](plan.md).

*(Build-journey log, drafted 2026-06-29. Subject to revision as the labelling + scorer inspection continues.)*
