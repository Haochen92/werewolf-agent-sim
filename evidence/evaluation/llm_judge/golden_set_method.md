# Golden Sets for Extraction Judges — Method

> **Scope.** A shared method for the *extraction-family* LLM judges — the ones that grade whether a model
> pulled the right **set of items** out of a source: day-summary, post-game extraction, and the
> situation-summary (which extracts what is critical about the current situation). It is the concrete answer
> to the gap those apparatus reports each name as their headline: **no golden / human anchor**. It does
> **not** cover the two neighbouring tasks that need a *different* gold type — retrieval (relevance ranking)
> and the agent decision itself (gradeable by deterministic / behavioral proxy, not content coverage). See
> *Where it applies*.
>
> **Status: planned, not built.** No golden set exists yet, and labeling is parked (see the ship roadmap).
> This doc is the method we would build to, grounded in the summarization-eval literature, so the plan is
> legible even while execution is deferred.

## The problem it solves

An extraction judge that scores blind — a rubric with no reference answer — keeps hitting two failure modes in
our apparatus reports. It **saturates** on any dimension the prompt forces into existence: the judge can
confirm a section is present but not whether its *content* is right, so that dimension pins near 5.00 and
carries no information. And it is **uncalibrated**: nothing tells us whether a 4.6 means a good extraction or a
lenient judge. Both symptoms trace to one missing thing — a reference answer to grade against.

## The principle

For each frozen transcript, a human authors the **reference points** a correct output must contain: the
specific facts, claims, or lessons of that case. An LLM judge then scores how many of those points the model's
output actually expresses. Two rules make it work.

- **Grade by meaning, not by string.** The model paraphrases and picks its own vocabulary, so exact-string or
  regex matching misses real coverage. The judge checks semantic presence instead.
- **Score both directions, separately.** Coverage of the reference points is **recall**. Faithfulness to the
  transcript — did the output invent anything? — is **precision**. A summary can cover every reference point
  and still fabricate a vote, so the two are reported apart. They fail in opposite ways.

This is not a workaround; it is the established method. It is the **Pyramid method** from summarization eval,
whose reference points are called *Summary Content Units*, and the modern LLM variants work the same way —
**FActScore**-style claim decomposition, key-point recall, claim-based rubric grading. All of them are
human-authored atomic reference claims plus an LLM judge checking semantic presence.

## The refinements that decide whether it works

The shape above is easy to copy. These habits are the difference between a golden set that measures and one
that quietly misleads.

- **Atomic and binary points.** One checkable fact per point — "player_3 accused player_5 of coordinated
  voting," not "player_3 made accusations and defended their claim." If you find yourself wanting a "partial"
  grade, split the point. Partial matches produce noisy, incomparable scores.
- **Anchor each point to its source.** When the annotator writes a point, attach the transcript line it came
  from. It costs almost nothing and pays off twice: it disciplines the annotator into writing points that are
  actually in the dialogue, and it makes auditing a suspicious judge score fast.
- **Make the judge cite before it credits.** Do not ask only "is this point present?" Require the judge to
  quote the output sentence that expresses the point, then decide. LLM judges are systematically lenient, and
  the quote requirement is the cheapest known correction. Check one point per call, or a small batch under
  structured output, rather than all points at once.
- **Calibrate the judge once.** The golden set calibrates the summarizer; nothing yet calibrates the judge. On
  one or two pairs, do the matching by hand and compute per-point agreement with the judge. Above ~90% you can
  trust it at scale. Below it, the fix is usually point *granularity*, not the judge prompt.
- **Tier points by severity.** Missing a vote action or a role claim is a different failure than missing a
  throwaway accusation. Either weight the points, or report must-have and nice-to-have coverage separately. A
  single flat percentage hides exactly the failures that matter most here.

Two shortcuts keep the cost down without giving up the "gold":

- **Draft with a model, verify by hand.** A strong model drafts the reference points from the transcript, and
  the human edits and verifies each against the source. Editing is 3-5× faster than authoring, and as long as
  a human approves every point against the source, the set is still gold.
- **Include a couple of easy pairs.** If the eval is all hard cases, a 60% score is ambiguous between "hard
  set" and "broken summarizer." One or two easy pairs give a ceiling to read the hard ones against.

## Where it applies

| Judge | Reference points are… | Recall (coverage) | Precision (faithfulness) |
|---|---|---|---|
| **Day-summary** | the day's accusations, role claims, and vote actions | maps to the `completeness` dim, and turns the saturated `village_dynamics` / `evidence_type_clarity` pair into real discriminators | `accuracy` + `epistemic_correctness`, checked against the transcript |
| **Post-game extraction** | the game's critical observations and strategy-points a good mining must surface | makes the `coverage` dim a measured quantity instead of a blind rubric score | the `grounding` dim, checked against the game record |
| **Situation-summary** | the strategically critical elements of the current situation — who is exposed, the consensus/alignment state, the key threats and information gaps | how many of those elements the summary names, giving the two currently **ungrounded** summary judges (pairwise + single-rubric) a reference anchor | faithfulness to the actual game state (no invented exposure or consensus) |

Two neighbouring tasks need a *different* gold type, and forcing coverage grading onto them would measure the
wrong thing.

- **Retrieval** is graded on relevance *ranking*, and already has its own gold — a situation-NDCG set, a
  different construction (see the context-based retrieval eval).
- **The agent decision itself** is not an extraction, so there is no reference *set* to cover — but it is not
  ungradeable either; its two halves each admit a crude ground truth of their own. The **action** (a vote, a
  heal) can be scored against a role-appropriate reference: a wolf voting to blend in, a healer protecting a
  likely town target rather than a random villager. The **discussion** is harder, but behavioral proxies
  stand in — revealing versus concealing a role when the situation calls for it. These are de-lucked
  outcome / behavior proxies, a separate track from reference-point coverage.

One clarification, since it can look like an exception: the pairwise-preference judge that situation-summary
uses *today* is itself an ungrounded LLM judge with no labels. That is exactly why situation-summary sits in
the coverage table above, not here — the task is extraction, and the current instrument simply hasn't been
anchored yet.

## Status and next step

Planned, not built. The cheapest first cut is a handful of hard pairs plus one easy pair per task, reference
points drafted-then-verified, and a citing judge scoring recall against them with the existing groundedness
dimension as the precision side. It stays deferred while labeling is parked and these judges are not the
binding constraint; when labeling restarts, this is the construction to follow.

*(Method captured 2026-07-02 from an external review that placed the approach in the Pyramid/SCU + FActScore
lineage. Consumers: [`day_summary.md`](day_summary.md), [`extraction.md`](extraction.md), and the
situation-summary stage of [`agent_decision.md`](agent_decision.md) point here for their "golden set"
upgrade.)*
