# When three models agreed on the wrong label

*Level 3 · Evaluation › [Building reference labels and reviewing outputs](reference_labels.md) · status: page copy drafted 2026-10-25 with the level prompts, reviewed in the main session; for the owner's review.*

## Brief

Explain the 619 unanimous and 244
split cases, what was reviewed and what was trusted, class-specific errors and what reviewing only
disagreements would have missed. Review was not a fully independent human benchmark; preserve that limit.
Level 2 keeps the central finding, not just a teaser.

The parent page keeps the finding and its essential caveats; this page adds the method and analysis.
Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: Removed the inference that directional majority errors establish dependence between model errors.
The observed unanimous-discard reversals remain the evidence that agreement was insufficient. Check
the protocol wording against its intended status; it is not presented as completed validation.
Verified 2026-10-25 (main session): round order is A (this panel) → B (the mixed-vendor relevance panel) → C (protocol written) (labeling/experiment_log.md §3a–3c). 'The subsequent panels still lacked that validation' implied panels after the protocol; rewritten to the actual order, and the calibration step stated as built 2026-10-23, not yet run on a panel.
-->

## Page copy (draft)

A panel of three models labelled 863 memory cases so that a person would only need to decide the cases
they disagreed on. That plan was only as good as one assumption: that when all three models agreed,
they were right. Reviewing the disagreements showed errors falling mostly on one side. A review of the
agreed cases on that side then found that all three models had been wrong on 80 of the 373 cases where
they unanimously chose "discard".

The finding changed which labels were reviewed, and how later panels were built. Its scope matters as
much as its numbers. The review was done once, by the owner working with Claude, and was never checked
by a second reviewer. So it measures how far the panel departed from that review, not its error rate
against an independent human benchmark. This page explains how the review was set up, what it found
for each kind of label and lesson, and what it leaves unknown.

### The task the panel labelled

The agents keep lessons from past games in two forms. An **observation** records a situation, what was
tried and how it turned out. A **strategy point** gives advice for a situation. After each game, a
deduplication step ("dedup") compares each new lesson with the most similar stored lessons and decides
whether to **keep** it or **discard** it as a duplicate.

The labels followed the dedup prompt's own rule. An observation duplicates a stored one only if its
situation, approach and outcome all match. A different outcome makes it a contrasting lesson, which is
kept. A strategy point duplicates a stored one when the situation is the same and the advice points the
same way.

The labels were needed to train a small dedup classifier, which required 500 to 1,000 examples; only
65 hand-labelled cases existed. The 863 cases were made by running lessons extracted from recorded games
of the original nine-player game through dedup against a stored set, in May 2026. Only cases that a
model, rather than a similarity cut-off, had decided were kept. The lessons came from 10 recorded games,
each extracted several times by different models. The 863 cases therefore share games and stored
lessons; they are not 863 independent situations.

### The plan: agreement decides what a person reads

Three models from Google's Gemini family labelled every case keep or discard. The plan was simple:
accept a unanimous label, and send each split to a person.

| Panel result | Cases |
|---|---|
| All three said discard | 373 |
| All three said keep | 246 |
| Split, two votes to one | 244 |
| **All cases** | **863** |

### What the split cases showed

I reviewed all 244 split cases with Claude, checking each against the dedup prompt's rule. The review
settled 97 as discards and 147 as keeps. The two kinds of majority did not fail equally often:

- when two of the three models said **discard**, the majority was wrong 37% of the time;
- when two said **keep**, it was wrong 7% of the time.

The discard-heavy disagreements prompted a further question: were unanimous discards also hiding
mistakes? The split cases could not answer it. Reviewing the agreed cases on that side would test
whether the panel's apparent consensus was safe to accept.

### Reviewing the tier that looked safe

All 373 unanimous discards were therefore reviewed, in several passes. Strategy points were split by
two cheap signals. One was a keyword check for opposing advice, such as "avoid suspicion" against "lead
the discussion". The other was the similarity score recorded for the case, with 0.85 as the dividing
line. Observations were reviewed in one full pass.

| Unanimous discards | Cases | Changed to keep | Rate |
|---|---|---|---|
| Strategy points flagged by the keyword check | 65 | 17 | 26% |
| Strategy points, not flagged, similarity below 0.85 | 162 | 37 | 23% |
| Strategy points, not flagged, similarity 0.85 or above | 57 | 6 | 11% |
| Observations, all | 89 | 20 | 22% |
| **All unanimous discards** | **373** | **80** | **21%** |

*Each case was decided against the dedup rule; the passes only ordered the work.*

The table shows why the cheap signals could not replace the review. The keyword check found the most
obvious errors, yet strategy points it did not flag, with lower similarity, were wrong almost as often.
The high-similarity group had the lowest reversal rate, but 6 of 57 such cases still changed. Observations need
three fields to match before they count as duplicates, yet they were wrong about as often as strategy
points.

The wrong discards fell into four recorded patterns:

1. **Opposite advice:** "defend yourself" treated as the same as "accuse others".
2. **Different situations:** a stored lesson matched to a new one from a substantially different game
   state.
3. **Opposite outcomes:** "the plan succeeded" and "the plan failed" treated as duplicates.
4. **Different tactics:** similar situations, but materially different advice.

In each pattern the two lessons shared a topic while differing in what they advised or reported.

### What reviewing only disagreements would have missed

Taken together, the review gives an error rate for each agreement tier except one:

| Agreement tier | Wrong in the review |
|---|---|
| All three said keep | Not measured (246 cases trusted) |
| Two said keep | 7% |
| Two said discard | 37% |
| All three said discard | 21% (80 of 373) |

Unanimity reduced the error rate on the discard side, but did not make it safe. Under the original plan,
the 80 unanimous discards that the review overturned would have entered the training data with the
panel's answer. They were the hardest cases in the set: when the training data was ranked by difficulty,
these came first. With the split cases whose majority was wrong, they made up 139 hard cases that were
given three times their weight in training.

### What changed

The next panel, for memory-search relevance labels, also ran without a check against people. After it, the lesson was written into a labelling protocol: measure each agreement tier's error against a human-labelled sample before accepting a panel's labels. The step that performs that check was built in October 2026 and has not yet been run on a panel.

The next panel mixed vendors. A round of relevance labels for memory search used five models from
several vendors, with no review. The models formed two camps that agreed within themselves but not
with each other. Measured against two models whose labels were collected by hand (ChatGPT and Claude
Sonnet), the merged labels over-credited relevance on 514 of 1,848 items. The mixed panel exposed
disagreement between groups of models. It did not show which camp was right, and it was not checked
against a person.

The hand calculations became a design for checking a panel against a person: an error rate for each
agreement tier, and a test for a lean in one direction. In October 2026 that check was built as a
calibration step in the labelling pipeline. It has not yet been run on a panel.

The classifier trained on these labels did not reach the accuracy of the prompted models on the
65-case hand-labelled set, and dedup stayed a prompted model call. That result tested a small
classifier, not the labels.

### What the review does not show

**It is not an independent human benchmark.** The review was one pass by the owner working with Claude,
a model from a different vendor than the panel. That made it a different kind of judge, but not a second
person, and no one else checked its decisions. The record also notes that Claude sometimes judged from a
shortened version of the text until told to read it in full. The 37% and 21% are rates of disagreement
with this review.

**The unanimous keeps are unmeasured.** They were accepted because the observed errors leaned
towards discarding, but that reasoning did not measure the accuracy of the keeps. No sample was
reviewed. Their error rate is unknown.

**The rates describe this pool.** The cases come from 10 recorded games of the original nine-player
game, labelled by three models with one prompt. Cases share games and stored lessons, so their number
overstates how many independent situations were seen. The tier rates are not a general estimate of how
often model panels err.

**A mixed panel is not shown to be safe.** The later round exposed disagreement within a panel drawn
from several vendors. It does not show that agreement in a mixed panel can be accepted without a
person's check. The calibration step exists so that each tier's error rate is measured rather than
assumed.

**Evidence.**

- [Labelling: golden sets and sampled reads](../../../evidence/evaluation/labeling/report.md), case 2
  (the panel, the review and the later rounds).
- [The labelling record](../../../evidence/evaluation/labeling/experiment_log.md), §3a–3c (the panel's
  design, the bias, the mixed-vendor round and the protocol that followed).
- [Dedup classifier log](../../../evidence/fine_tuning/dedup_classifier/experiment_log.md), "Co-labeling
  Results", "Final Labeled Dataset Composition" and "SFT Dataset Construction" (the passes, the patterns,
  the final set and the difficulty tiers).

<!-- Sources for the page copy (drafted 2026-10-25):
Opening and counts: labeling/report.md case 2 (863; 619 / 244; 373 unanimous D reviewed; 246 unanimous
K trusted; 617 records; owner with Claude; 37% / 7% / 21%; review never checked).
Dedup task and rule: dedup/per_extraction/experiment_log.md "What counts as a duplicate"; the review
"examined against the dedup prompt criteria": dedup_classifier log "Phase 1".
500–1,000 needed, 65 existed: report.md case 2 and dedup_classifier log "Key findings".
Case generation (extraction artifacts run through per-extraction dedup against the stored set; LLM-
decided cases only; 60 extractions from 10 unique game transcripts): dedup_classifier log "Dataset
Generation Run", "Extraction sources selected" (the note under the table) and "Output format".
Three Gemini flash models: dedup_classifier log "Multi-model triage".
244 → 97 D / 147 K; 36.6% / 6.9%: dedup_classifier log "Phase 1" and "Labeling reliability from round 1".
The "unrelated mistakes" sentence is an inference, labelled as "suggested"; the record calls it "a
strong, directional D-bias shared across all three models" (labeling/experiment_log.md §3a).
Pass table (65/17, 162/37, 57/6, 89/20, 373/80): dedup_classifier log "Phase 2". Keyword examples and
the four patterns: "Common false-D error patterns". Pass readings: "Co-labeling process findings" 2–4.
Tier table: dedup_classifier log "Labeling reliability from round 1" (the "~5% est." for unanimous K is
an estimate, not a review result, so the page says "not measured").
Difficulty tiers; 139 cases in tiers 1–2 oversampled 3x: "SFT Dataset Construction".
Routing rule: labeling/experiment_log.md §3a "Decide"; "Efficient pipeline" in the dedup_classifier log.
Mixed-vendor round: report.md case 2 "Result"; labeling/experiment_log.md §3b. Protocol and calibration
step: labeling/experiment_log.md §3c and §4; report.md case 2 "How far to trust it" (built 2026-10-23,
not yet run on a panel).
Classifier outcome (43%, 65–69% vs 83–85% on the 65-case set; dedup stays an API call):
dedup_classifier log "Evaluation" sections and "Conclusion".
Claude truncation note: dedup_classifier log "Co-labeling process findings" 1.
-->

<!-- Completion note (2026-10-25)

Structure. Follows the Level 3 layout: question and conclusion with the essential caveat in the opening;
setup (the task, the rule, the case pool); method (the plan, then the two review phases); results with
three tables; what changed; what it does not show. The parent's featured subsection keeps the finding
(37%, 21%, 80 cases), the agreement-as-sameness point, the review's limits and the mixed-vendor round.
This page adds the case pool and its units, the per-pass and per-type results, the error patterns, the
per-tier table and the training consequence.

For the verifier:
1. Split-case denominators: the records give the two majority error rates but not the number of split
   cases with each majority. Not derived here. Available from colabeling_log.jsonl if wanted.
2. "The similarity score recorded for the case": the log says "low similarity (<0.85)" without naming
   which score (the closest candidate's cosine, presumably). Please confirm the wording.
3. "Lessons came from 10 recorded games": the log says the 60 extraction "games" come from 10 unique
   game transcripts. Whether all 863 LLM-decided cases came from all 10 is implied, not stated.
4. "Only cases that a model, rather than a similarity cut-off, had decided": the log says only
   LLM-decided cases were used (auto decisions excluded). Confirm the 863 are exactly those.
5. "Given three times their weight in training": the log says tiers 1–2 were "oversampled 3x".
6. The mixed-vendor round's agreement percentages conflict between the report (73% / 36–43%) and the
   June log (71–74% / 56–68%); I used only "514 of 1,848" and "two camps", as on the parent page.
   "The two voters run by hand" stands for the report's "two careful models" (ChatGPT and Claude Sonnet,
   run by hand per the log); please confirm.
7. Ownership: "I reviewed ... with Claude" rests on the record's "Manual (claude + user)" and the
   report's "the owner with Claude". The record does not say how the work was divided between them, and
   the page does not claim the owner read every case.
8. The classifier paragraph: the log attributes the failure to model size (the 4B run), so "that result
   tested a small classifier, not the labels" is a scope statement, not a claim that the labels were
   validated by it.

Mechanism claims: the dedup rule is taken from the May-era per-extraction record; today's dedup adds a
deterministic gate on structured fields (Agents/memory/dedup_gate.py) that did not exist then. The May
panel ran on ad-hoc scripts later generalised into evaluation/src/labeling/ (voter.py: unanimous /
strict majority / tie to a person), so the page describes the May design from the records. The
calibration step's existence and state are from labeling/report.md and evaluation/src/labeling/
calibration.py; it is not described in detail here (the parent page has its gate).

Left off deliberately: model versions (Opus 4.6, the three flash model names), the classifier's training
infrastructure and interruptions, the "26.4% overrode flash-3.5" figure (a different comparison), the
record's ~5% estimate for unanimous keeps (an estimate, not a review result), and costs. Nothing from
the Handle-with-care list is relevant to this page beyond keeping the review's limit beside the claim.

Rubric self-scores (Level 3 additions, 0/1/2): added depth 2; method inspectability 2 (inputs, rule,
passes, what was trusted); counting units 2 (cases vs games; 617 reviewed of 863; tiers); decision-rule
precision 2 (the original routing plan and the revised rule are kept apart); analytical assumptions 2
(the shared-lean reading is labelled as inference; the unanimous-keep rate is unmeasured);
scope alignment 2 (one pool, one prompt, one vendor family; the later round is a different task);
bounded consequence 2 (what changed, and that a mixed panel is not shown safe).
Level 2 required criteria: experimental separation 2, interpretation 2, evidence and ownership 2.
Approximate length: 1,500 words of page copy, at the top of the range.
-->
