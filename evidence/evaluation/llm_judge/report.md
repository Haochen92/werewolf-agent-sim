# LLM Judges — how we score the memory pipeline, and how far to trust it

> **What this system is.** The agent plays Werewolf, a hidden-role game: a town tries to vote out the
> werewolves (and a lone serial killer) across alternating rounds of open day discussion and secret night
> actions. To play better over time, the agent keeps an *episodic memory*. After each game it writes two
> kinds of note: *observations* (a situation, what it did, and how it turned out) and *strategy points* (a
> situation, and the action to take). Notes are filed by role and game phase, then retrieved later by matching
> the current situation.
>
> This report covers how we **evaluate** those memory components using LLM judges. An LLM judge is a language
> model scoring another model's output against a rubric. It is the cheapest and noisiest of the three ways we
> check quality; the other two, [spot-checking cases by hand](../sampled_human_review/report.md) and
> [building human-labelled answer keys](../labeling/report.md) ("golden sets"), are written up separately. Six
> components are judged here: at decision time the agent **summarises** its situation, **retrieves** notes,
> and **applies** them; offline the system **extracts** notes from finished games, **deduplicates** the store,
> and **summarises each day's discussion**. The overview that ties all the evaluation together is the
> [parent report](../report.md).

## 1. What the judge layer is, and what it decided

One judge grades every memory component. It is a single model, configured in one place, that scores each
output in a fixed structure and retries once if parsing fails. It records its exact configuration with every
run so two results can be compared fairly. Each component is judged against the standard it was built to meet,
rather than against whatever the judge model happens to prefer. (How those standards are set is section 3.)

The fair test of whether this layer earned its place is simple: what did a judge actually decide? A judge
whose scores changed no decision did nothing. Going through the record, the answer is modest.

- **Two design calls were judge-driven, and both rest on little data from the old pipeline.** A judge's scores
  were the deciding input in exactly two places: which model to use for extraction (compared on 5–10 games),
  and locking version 2 of the application prompt (120 cases, judge-scored only). Both were settled in May, on
  the pre-v7 pipeline, and neither was re-run on the current version. Real influence, thin evidence, and stale.
- **One finding mattered without settling anything.** The deduplication quality judge found that the
  merge-writing model invents game details on about a third of its merges (3 of 9 cases). Batch deduplication
  is already off by default for a plainer reason: it is expensive, so it runs as an occasional offline sweep
  rather than after every game. The fabrication finding is the reason that sweep will not be switched to run
  automatically until a safeguard is added.
- **Three calls were made without the judge, because the judge was too weak to make them.** The
  situation-summary design was settled by a human-labelled answer key, which dropped one prompt option (worth
  −0.08) and kept another (worth +0.06). Retrieval depth, how many notes to pull, was settled by a
  downstream outcome measure. The day-summary format was a design choice, because later code needs structured
  fields, and its model was picked by reading real summaries and weighing speed. The judge's scores were
  statistically flat across the prompt versions, and where they did separate the models, they pointed at the
  slow one that latency ruled out.

The pattern is the point. These judges are good at detecting problems but poor at ranking near-equal options,
so the decisions that needed a reliable ranking went to better-anchored instruments, and the judges did the
cheaper work of flagging faults.

On that flagging: the judges have no agency of their own. A person reading their output, noticing inconsistent
scores or a dimension stuck at one value, is what caught the bugs since fixed. Two were in the extraction
judge's own prompt: one applied a rule to the wrong field and deflated scores by 1.19; another, once fixed,
raised a score by 0.69. One was a retrieval shortcut that inflated a score when too few notes were retrieved.
One was an engagement number, later retracted from about 0.70 to 0.55. It had read high because an
instruction buried in a structured-output field was being ignored: the model silently skipped about a third
of the notes, and the skipped ones were disproportionately the inapplicable ones. Moving that instruction
into the visible prompt body made it score every note, and the true rate came out lower.

The honest limit is that none of the live judges is calibrated. Each is one model scoring another, with no
human-checked answer key behind the numbers, so they are best read as smoke alarms rather than gauges. The
larger wins of the eval system (the head-to-head verdict that memory helps, and two configuration bugs the
harness caught) come from other layers and are covered in the [parent report](../report.md).

One more limit is worth stating plainly, because it is easy to miss: none of this reached the current version.
The two judge-driven calls, and the situation-summary golden set that outranked the judge, all ran on the
pre-v7 pipeline (v4-era stores, May prompts). The choices that survive into v7, per-role extraction and the
2.5 Pro extractor, were validated back then and carried forward, not re-judged. v7's genuinely new parts, the
dimensional memory schema and the credit-aware synthesised strategy notes, have no LLM-judge score at all.
On v7 specifically, the LLM-judge layer drove no design decision; what stands behind v7 is the outcome and
deterministic instruments described in the [parent report](../report.md).

## 2. The harness

All six judges share one harness, so every component is scored the same way and any comparison is fair. Each
choice below is a deliberate tradeoff, not incidental plumbing.

- **One model, chosen in one place.** The judge model is set centrally (in `judges/config.py`; default Gemini
  2.5 Pro) rather than hard-coded in each judge, so a comparison can pin it in a single spot.
- **Each judge's model is matched to its rubric.** The stronger model, Gemini 3.1 Pro, judges the two rubrics
  that are holistic quality calls: the situation-summary and the extraction model bake-off. The cheaper 2.5
  Flash judges the two that are closer to a factual check: retrieval and application. The rest run on 2.5 Pro.
  The rule is to spend model capacity where the rubric needs judgment, and where a dimension is purely
  checkable, to compute it rather than pay a model to estimate it (section 5).
- **The judge is a different model from the one it grades.** A model tends to prefer its own output, so
  wherever it can be, the judge and the generator are different models. Across the live pipeline they are: the
  agent plays on Flash-lite and is judged by Flash or Pro, Flash-lite situation summaries are judged by 3.1
  Pro, and 2.5 Pro extractions are judged by Flash or 3.1 Pro. The one exception is batch deduplication, where
  2.5 Pro both writes the merges and scores their quality; that is acceptable only because the decision-grade
  signal for dedup is the deterministic scorer, not this LLM layer (section 5). One constraint bounds all of
  it: every model is a Gemini tier, chosen so that backend, pricing, and tokenizer stay comparable, so "a
  different model" means a different tier rather than a different vendor.
- **The model is held fixed on both sides of a comparison.** As long as the same judge scores both options in
  a head-to-head, which the run log records, the model cancels out and the score gap still reflects the design
  change. The cost is that scores do not transfer across components or read as absolute levels: a 4.2 from Pro
  is not a 4.2 from Flash.
- **A failed score is dropped, not guessed.** Each judge asks for its scores as structured JSON, validates
  them against a fixed schema, and retries once. If that still fails it returns nothing, and the row is left
  out of the average. Silently dropping the row is a small risk, noted in section 6.
- **The configuration is recorded, not locked.** The model backend (Google AI or Vertex, which shift scores
  even at temperature 0) is read from the environment, but stamped into each run's record and checked to be
  constant within a run. Drift between runs is therefore detected rather than prevented, and a person still
  confirms the backend matches before comparing two runs.

## 3. How the rubric dimensions are chosen

The scoring dimensions are not invented separately for each judge. Two principles generate them.

**First, judge against the same standard the writer was given.** For the components that describe a game
situation, the eval reuses the exact instructions the agent itself was written to follow. Two shared documents,
one on how to describe a situation and one on how certain to be about who is what, are injected into both the
generator's prompt and the judge's prompt. So the judge checks whether the output met the standard we set, not
whether another model happens to like it. (The two documents are `SITUATION_STANDARDS` and
`EPISTEMIC_STATUS_RULE` in `Agents/prompts/standards.py`.)

- The situation standard defines the descriptive dimensions (how much the village knows, how aligned it is,
  how exposed the agent is, what phase the game is in) plus a specificity test: used as a search query, would
  this description match only similar situations, or almost anything? That test is the source of the recurring
  specificity dimension, since a note is only useful if it can be retrieved at the right moment.
- The certainty rule defines a five-level scale, from "my own confirmed finding" down to "unknown", and
  forbids naming players by ID. It is the source of the epistemic and role-perspective dimensions. This is the
  pipeline's signature concern: in a hidden-role game, a note that leaks knowledge the role could not have is
  worse than no note at all.

**Second, for the remaining judges, work backward from what the consumer needs.** The day-summary,
deduplication, and application judges use their own rubrics, and each dimension answers a single question:
what must this component get right for whatever uses its output next? The day-summary rubric says this
outright. It is scored on what "downstream consumers use for agent decisions, situation characterization, and
post-game extraction", which is why it has a dimension for labelling the *type* of evidence behind each
suspicion. Deduplication is scored on making the right keep-or-merge call and preserving information without
inventing it. Application is scored on whether the agent actually used the notes it retrieved.

So the rubrics come from two clear sources, reusing the writer's standard or decomposing the consumer's needs,
rather than from one master list or from ad-hoc choices.

## 4. The six judges at a glance

One rubric per component. The trust column uses five tags: ✅ validated, 🟡 partial, ⚠️ asserted but
unverified, 🔴 weak or null, ⏸ designed but not run. Fuller detail is in the linked per-component notes.

| Judge | What it scores | Model | What it found | Trust |
|---|---|---|---|---|
| **Situation-summary** (pairwise + single-rubric) · [detail](agent_decision.md) | faithfulness, specificity, retrieval-usefulness, non-redundancy, role-perspective | 3.1 Pro (both modes) | drove no design call; a human-labelled key did (dropped a −0.08 option, kept a +0.06 one) | 🟡 an answer key exists but isn't wired to the live judge |
| **Retrieval** · [detail](agent_decision.md) | relevance, efficiency, redundancy of the retrieved notes | 2.5 Flash | the version actually shipping (plain similarity search, no reranking) is the least-measured | 🔴 uncalibrated, and inflates efficiency when few notes are returned (section 6) |
| **Application** · [detail](agent_decision.md) | action quality, use of strategy, grounding, adoption accuracy | 2.5 Flash | note adoption stays flat near 50% across prompt versions (the prompt changed accuracy, not volume); 120 cases from only 3 games, pre-v7 (v4 store, May prompts), one outlier swings it | ⏸ calibration designed, never run (section 6) |
| **Extraction** (8 dimensions) · [detail](extraction.md) | specificity, epistemic, grounding, coverage, diversity, perspective, strategy-depth, novelty | 2.5 Pro | two prompt bugs found by inspection and fixed; the original five dimensions cluster near 4.0 and barely discriminate; drove the extraction model choice (5–10 games) | 🟡 debugged, not calibrated; the newest synthesised notes are unjudged |
| **Dedup quality** · [detail](../labeling/dedup.md) | merge quality, information preservation, fabrication | 2.5 Pro | the merge-writing model it scores (also 2.5 Pro) invents details in 3 of 9 cases; a faster merge-writer (3.5 Flash) fabricates 0% but drops whole fields, so 2.5 Pro was chosen deliberately: losing fields was judged the worse defect than inventing them | 🟡 weak layer; dedup's strong instrument is the deterministic scorer, not this |
| **Day-summary** (5 dimensions) · [detail](day_summary.md) | completeness, accuracy, evidence-type, village-dynamics, epistemic | 2.5 Pro | the judge is shown the transcript, so the content dimensions move but the "is this section present" dimensions sit at the maximum; flat across versions | ⚠️ a smoke test, too weak to rank versions |

Two judges sit off this list: a turn-level pipeline judge used in the end-to-end runs, and per-role and
pairwise variants of the extraction judge used for model ranking. A separate deterministic check, not a judge,
found and fixed a player-ID leak in extraction (from 84% down to 0–3%); it is covered in
[the extraction note](extraction.md).

## 5. Anchoring — deciding how much to trust a score

A judge's number is trustworthy only if it is anchored to something outside the judge. Without an anchor it
can flag a problem but cannot reliably rank two options. There are three kinds of anchor, strongest first.

1. **A real outcome.** Does the dimension predict something that matters, such as winning the game or
   retrieving the right note? This is the strongest anchor, because an outcome cannot be wrong about what
   matters. It is why the game's outcome-based metrics, which track winning at a correlation around 0.6, are
   the most trusted numbers in the whole eval system.
2. **A human answer key.** How well does the judge agree with human labels on a sample? This is the fallback
   when there is no clean outcome, and it is what a golden set provides.
3. **A direct computation.** When the thing being measured is cheaply checkable, such as how many distinct
   notes were returned or whether a banned player-ID appears, compute it rather than ask a model to estimate
   it.

This turns "the score isn't anchored" from one complaint into five situations, and only the last is a real
design failure:

| The dimension is… | The fix is… |
|---|---|
| cheaply checkable (player-ID leakage, distinct-note counts) | compute it directly; an LLM score here is a wasted opportunity |
| checkable in principle but hard to label (fabrication, whether a claim is grounded in the transcript) | an LLM judge is the best available proxy: a golden set is expensive and sometimes hard even to define, so an uncalibrated judge is a reasonable stand-in as long as you flag it as directional |
| subjective but consequential (specificity, strategy depth) | anchor to an outcome if possible, otherwise a human answer key |
| subjective with no outcome to tie to | a human answer key; this genuinely is not a counting problem |
| stuck at one value regardless of input | redesign or delete the dimension; no anchor fixes a gauge that never moves |

The deduplication fabrication check is the clearest case of the second row. Deciding whether a merged note
introduced a fact that is not in the source entries is a genuine semantic judgment, not a lookup, and there is
no obvious deterministic label to build. So an uncalibrated LLM judge earns its place there: the honest move
is to read its number as directional and say so, not to pretend a computation was on offer.

The way to tell an honestly subjective dimension from a badly designed one is whether it moves. A dimension
that sits at the same value no matter how good or bad the input is measuring the format the prompt forces, not
the quality. Four such failures recur across the judges.

- A dimension pinned near its maximum carries no information. Village-dynamics sits at 5.00, and extraction's
  original five dimensions cluster at 4.00.
- Saturation can be built in. When the judge is shown the ground truth, as the day-summary judge is shown the
  transcript, the dimensions that only check whether a section is present are forced high, and only the
  dimensions that compare content against the transcript actually vary.
- Generating and judging in one pass confounds the two. Where a harness both produces an output and scores it,
  a change in the score cannot be separated from a change in generation.
- Scoring on the outcome smuggles in a halo. A dimension conditioned on whether the side won measures the win,
  not the property it claims to measure.

## 6. Open gaps, and why each is open

In priority order. Current as of 2026-06-30.

1. **The application judge is uncalibrated, and calibrating it is both the highest-value fix and a cheap one.**
   The procedure is already designed: about 28 cases, labelled blind, checked for agreement within one point
   and for directional bias. Roughly half a day, no new code. It is unfinished not because it is hard, but
   because it calibrates a secondary judge. The headline result of the project, whether memory raises the win
   rate, needs no judge at all, so under a finish-and-freeze deadline this loses to shipping. (Calibrating the
   judges against human labels in general is a larger program, deferred until the memory work proves out. The
   one answer key built regardless is for deduplication, because dedup ships in every store.)
2. **The answer keys that exist are not connected to the live judges.** A graded retrieval key could calibrate
   the retrieval judge, and a trained reranker key sits offline. Both need re-labelling against the current
   store, which has not been done.
3. **The retrieval judge inflates one score when too few notes are retrieved.** It sets efficiency to the
   maximum and pools that into the average with no counter, which can bias one side of a comparison. The fix is
   about two lines, and it is flagged so a future run does not misread the number.
4. **The newest synthesised notes are not judged at all.** The extraction judge could score them but has not
   been pointed at them, because that part of the pipeline is not yet validated.

The cheapest improvement in every case is the same move: calibrate one judge, or connect one answer key that
already exists. None of it needs new machinery.

---

*Written 2026-06-30, drawing on the four per-component apparatus notes linked above. The question of whether
each memory component actually works, as opposed to how well we can measure it, lives in that component's own
folder, for example [the deduplication design report](../../dedup/report.md).*
