# Building reference labels and reviewing outputs

*Level 2 · [Evaluation](../evaluation.md) · previous: [Designing and validating LLM judges](../llm_judges/llm_judges.md) · next: [Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md) · status: page copy drafted 2026-10-25 with the level prompts, reviewed in the main session; for the owner's review.*

## Brief

**Reader question:** What should count as the answer when the evaluator itself can be wrong?

Subsections: reusable reference sets versus one-off reviews; selecting and blinding examples; turning
subjective criteria into labelling rules; using model panels without treating agreement as truth;
measuring disagreement and deciding what needs human review.

**Lead story:** the 863-case model panel, where review overturned even unanimous discard labels.
Explain why reviewing disagreements alone would miss shared errors. The smaller human-labelled dedup
set shows that human labels also need clear criteria and revision, not automatic trust.

**Sampled reads belong here as a full subsection:** explain the seeded packets, hidden version labels,
fixed rubric, scoring after unblinding and distinction between model readers and people. Use the
persona-line comparison's unchanged baseline to show why an apparent stance change needed context.

**Exhibits:** a readable example review packet; panel agreement → review → corrected labels; a small
confusion table with denominators where supported. Explain precision/recall or agreement at the point
they answer the reader's question, rather than listing metric names.

**Sources:** [labelling](../../../evidence/evaluation/labeling/report.md),
[sampled reads](../../../evidence/evaluation/labeling/sampled_reads/report.md), and scoring.

**Level 3:** [When three models agreed on the wrong label](model_panel_review.md), linked beneath the subsection it deepens.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: The parent retains the panel result, review scope and unmeasured unanimous keeps; the later-panel
counts now live in Level 3. Check whether sample-size calculations account for clustering before
presenting their nominal precision as achieved. Blinding is described as reducing, not eliminating, bias.
Verified 2026-10-25 (main session): sample sizes are a plain normal approximation (evaluation/src/labeling/anchor.py sample_size_for_ci) and the calibration step uses an ordinary binomial interval (calibration.py via core.stats.binomial_ci); nothing in the labelling pipeline adjusts for clustering. The page's 'may overstate precision' is accurate. No change needed.
-->

## Page copy (draft)

An LLM judge is checked by comparing its answers with reference labels: answers to the same items
used as the reference for assessing the judge. When the question is about meaning, such as whether
two stored lessons say the same thing, someone has to write those labels, and they can be wrong too.
So a reference is only as trustworthy as its labelling, and as the checks made on that labelling.

This page explains how the project built its references and reviewed outputs. It covers what the
labels were for, how a judgement became a written labelling rule, how one-off comparisons hid which
version produced each output, and how disagreement decided where a person's time went. The main example
is a panel of three models whose unanimous answers turned out to be wrong too often to trust without
review.

The labelling approaches used in the project fail in different ways:

| Who writes the labels | Scale reached here | Typical failure |
|---|---|---|
| One person labels every item | Tens of items | One person's drift; too few items to separate close results |
| A panel of models, with a person reviewing | Hundreds of items | Models that share a bias agree confidently and wrongly |
| Models only | Larger sets without human review | Agreement can conceal errors shared by the models |
| A written expectation for each test case | Tens of cases | A wrong expectation makes every verdict on that case wrong |

*Below, labels made or checked by a person are called **gold**. Labels made by models and not checked by
a person are **silver**: a useful reference, but not ground truth.*

### Reusable reference sets and one-off reviews

Labels serve two different purposes. A **golden set** is kept and reused: a cheaper check, such as a
classifier, a threshold or an LLM judge, is scored against it now and again after later changes. A
**sampled read** is done once, to choose between two versions of a prompt or feature, and its labels are
not reused. Both use the same techniques. The difference is how much later work depends on the labels
being right.

A golden set is not always the best reference. When code can compute the answer from the game record,
code is the reference, and an outcome such as a player's true role is better than anyone's opinion of
it. Golden sets cover what is left: judgements of meaning. A set can be small. Thirty to a hundred
items, mixing easy and hard cases, can measure a judge's agreement before the judge labels at scale.
For a known failure kept as a test case, the label is a written expectation of a correct answer. That
form is explained with the [factual-error test cases](../factual_errors/factual_errors.md).

The current state is uneven. The project's gold sets all come from the original nine-player game,
labelled between May and July 2026. The reference sets made for the expanded ten-player game are either
model-read or written expectations, and no person has yet checked a sample of the model-read ones.

### Turning a judgement into a labelling rule

The agents keep lessons from past games in two forms. An **observation** records a situation, what was
tried and how it turned out. A **strategy point** gives advice for a situation. After each game, a
deduplication step ("dedup") compares each new lesson with the most similar stored ones and decides
whether to keep it or discard it as a duplicate. The dedup models made this call wrongly often enough
that their own answers could not serve as the reference, so one person labelled a set of 65 cases by
hand, over two sessions.

Labelling needed a rule, not a feeling of similarity. An observation counted as a duplicate only if its
situation, approach and outcome all matched a stored one; a different outcome made it a contrasting
lesson worth keeping. A strategy point counted as a duplicate when the situation was the same and the
advice pointed the same way. Genuinely borderline cases were recorded with both labels acceptable, and
scored both strictly and leniently.

Even so, the labels needed revising. Twice, every model tested rejected the same few labels. When cheap
and expensive models all fail the same case, the label may be the problem, so those cases were read
again against the rule. In the first round, four of the six "merge" labels were wrong. Merge, a third
label used at the time, folded a variant into an existing lesson. In the second round, 32 cases where
models disagreed were re-read with a sharper test: would a search that finds one lesson also find the
other? Ten labels changed, mostly from discard to keep, and 14 changed across the two rounds.

Revising labels because models disagree carries its own risk: it can pull the reference towards the
models. Writing the test into the rule limited that risk. The case was decided by the rule, not by
adopting the models' answer. The set then guided the dedup prompt to about 83% agreement. In October
2026 it also set the similarity cut-offs for a new embedding model. Its limits remain: one labeller, no
second opinion, and only 25 strategy points, too few to separate an 8-point difference between versions.

### Featured story: using a model panel without treating agreement as truth

Training a small dedup classifier needed 500 to 1,000 labelled cases, and only the 65 existed. Labelling
a thousand by hand was too much for one person. The panel design was meant to save that effort: several
models label every case, a unanimous label is kept, and a person decides the split cases. It rested on
one assumption nobody had tested: that agreement means correctness.

Three models from one vendor's family (Google's Gemini) labelled 863 dedup cases from the original
nine-player game. They agreed on 619 cases and split on 244. I reviewed the split cases, working with
Claude. The errors fell mostly on one side: when two of the three models said discard, they were wrong
37% of the time; when two said keep, 7%. That suggested a lean towards discarding that the three models
shared. So the 373 cases where all three said discard, the tier that looked safest, were reviewed too.

| Panel result | Cases | Reviewed? | What the review found |
|---|---|---|---|
| Split, two votes to one | 244 | All | A discard majority was wrong 37% of the time; a keep majority 7% |
| All three said discard | 373 | All | 80 changed to keep (21%) |
| All three said keep | 246 | No; trusted | Not measured |

*863 cases from the original nine-player game, May 2026; 617 reviewed. The final set had 390 discards
and 473 keeps.*

Reviewing only the disagreements would have missed those 80 cases. They would have gone into the
training data as settled discards. Agreement had not protected the training set from wrong discards.
If agreement determines which items a person reviews, some agreed labels need checking too.

The review was the reference here, and nobody checked it in turn. It was one pass by the owner working
with a model, not two independent people, so the 37% and 21% measure disagreement with that review.
They are not error rates against an independent human benchmark. The unanimous keeps were trusted
because the bias ran towards discarding, but their error rate was never measured.

A later panel mixed vendors, but still lacked a human check. It exposed disagreement between groups
of models without establishing which group was right. The linked investigation follows that change
and the review breakdown in detail.

**Link:** See how the review found a shared bias, class by class, and what trusting agreement would have
missed → [When three models agreed on the wrong label](model_panel_review.md).

### Hiding the version: blind sampled reads

From October 2026, one-off comparisons were read by Claude models started from the working session,
not by people. The owner set the question, often wrote the rubric, and made the decision from the
readers' summaries. Each read followed the same steps:

1. **Generate.** Replay recorded turns, or play games, under each version, and save every response.
2. **Draw.** A seeded random draw picks the items when there are too many to read.
3. **Packet.** Shuffle the items with a fixed seed and give each an opaque id. The reader sees what the
   speaking player could see and what it said. It never sees the version, the speaker's role or its
   private notes. A separate key file maps each id back.
4. **Read.** Each reader applies a fixed rubric and returns one verdict per item, usually with a quote
   or a reason.
5. **Unblind and score.** Code joins the verdicts to the key and counts them per version.

> **q04**
> A: player_1, fair question. I'm the sentinel. My only watch was night 2 on player_6, and it showed
> player_4 and player_8 at their door. [...]
> B: player_1, I watched player_6 on night 2 and it showed player_4 and player_8 coming to them. That is
> all I have. [...]

*One item from a stance packet, shortened, as the reader saw it. The sentinel watches one player at
night and sees who visits them. Which message came from which version is recorded only in the key
file.*

Hiding version labels reduces one opportunity for a reader to favour a version; distinctive content
may still reveal it. It does not make the reader's labels
correct, and a model reader is not a human check.

A read also needs a baseline from inside the experiment. One read tested a single line added to a
player's prompt to describe its speaking voice. Readers judged whether a listener would take the same
position and request from two messages. A voiced message differed in stance from a plain one in 9 of 30
pairs. Alone, that could look like the voice changing what a player argued. But the same packets
included pairs of two plain responses to the same unchanged prompt, and those differed in 3 of 10. In
this sample, adding a voice changed stance no more often than drawing a second response did. With only
10 baseline pairs, a modest effect could still be hidden by that variation.

Readers can also find what a code check misses. In a read of rewritten messages, readers found that 19
of 90 rewrites changed something a listener could act on. A code check of facts, run beside them, caught
1 of those 19.

These reads have clear limits. Each item had one reader, so agreement between readers is unknown for
every rubric. When fresh readers happened to re-read one screen's packets, counts of an act (whether a
player claimed a role) held exactly. A judgement label, whether a message explained an accusation or a
visit, moved from 29 to 19 of 73. Most pools were drawn from known failure cases, so they describe those
turns, not play in general. No rubric from these reads has yet been compared with the owner's own labels.

### Measuring disagreement and deciding what a person reviews

The panel's failure was directional: it called "discard" too often. A single agreement rate can hide a
lean like that. Three scores make it visible when a source is compared with a reference:

- **Agreement**, with its interval, and **Cohen's kappa**, which discounts the agreement expected by
  chance from how often each label occurs. That matters when one label dominates, because a source can
  then agree often just by choosing it.
- **Precision and recall for each label.** Of the items a source labels "discard", precision is the
  share the reference also calls discard. Recall is the share of the reference's discards the source
  finds. Together they show which label a source over-uses.
- **A test of the two kinds of disagreement** (an exact McNemar test). It asks whether the source's
  disagreements with the reference fall on one side more often than chance allows.

For the panel, all of this was worked out by hand. A calibration step built in October 2026 now
computes it. It compares one model source with a person's labels and applies a pass bar. By default
that bar is at least 80% agreement, a 95% interval whose lower bound is at least 75%, and no significant
lean. It has not yet been run on real labels. Owner-check packets are ready for three model sources in
the expanded game: each speaker's own tag of whom it accused, the gate that decides which open-discussion
messages are heard, and the factual-error judge. Each packet gives a written rule with worked examples,
and keeps the source's answers out of view until labelling is finished.

Two practical choices decide how much a check of this kind can establish. The sample is sized from the
precision needed: about 62 items for an interval of ±10 points, and 246 for ±5, at an expected agreement
near 80%. The sample is also spread across games to reduce clustering. Items from the same game can still be
related, so an interval that treats every item as independent may overstate precision.

The panel adds one more rule. When agreement decides what a person reviews, each agreement tier needs its
own measured error rate, unanimous tiers included.

### What remains open

The project's gold sets come from the original nine-player game. In the expanded game, references are
model-read or written expectations, and the judges and tags that rely on them have not yet been checked
against a person. The next step is small and ready: the owner labels the prepared samples, and the
calibration step reports whether each model source meets its bar. Until then, those references show
what model readers saw, not agreement with a person. How the judges themselves are designed and
validated is on [Designing and validating LLM judges](../llm_judges/llm_judges.md).

**Evidence.**

- [Labelling: golden sets and sampled reads](../../../evidence/evaluation/labeling/report.md): the shared
  techniques, every golden set, case 1 (the 65-case dedup set) and case 2 (the panel).
- [Sampled reads](../../../evidence/evaluation/labeling/sampled_reads/report.md): the October packet
  reads, §2–4.
- [Dedup: evaluation apparatus](../../../evidence/evaluation/labeling/dedup.md): the human dedup sets and
  their scoring.
- [Per-extraction dedup log](../../../evidence/dedup/per_extraction/experiment_log.md): the duplicate rule
  and the two label revisions.
- [Scales and scores](../../../evidence/evaluation/scoring/report.md): agreement, kappa, precision and
  recall, McNemar, intervals.
- [Persona line screen](../../../evidence/gameplay/data/persona_line/README.md): the
  plain-against-plain baseline.

<!-- Sources for the page copy (drafted 2026-10-25):
Opening, gold/silver: labeling/report.md intro ("gold ... silver"). Ways-of-labelling table: report.md
"Ways of labelling, compared" (scale and typical-failure rows, wording condensed).
Reusable vs one-off: labeling/report.md "Two uses, one set of techniques"; sampled_reads/report.md intro
and §1. Code/outcome first, 30–100 items: report.md "When a golden set is needed". Written expectations:
report.md case 4 (one sentence + link to the factual-errors page, which owns it).
Gold sets all nine-seat May–July; ten-seat model-read or expectations, none person-checked:
report.md "What the table shows" and "What is missing".
Dedup task (observation / strategy point; keep or discard against the most similar stored ones; after
every game): dedup/per_extraction/experiment_log.md "What counts as a duplicate" and §① (new entry vs
its top-k candidates). The duplicate rule (three fields for observations; same situation + same action
direction for strategy points): same section. also_acceptable borderlines, strict and lenient: §②
"Building the golden set". Two sessions; 65 cases: §② and labeling/report.md case 1.
Revisions: round 1, uniform cross-model failure, 4 of 6 MERGE labels wrong: §③ Phase 1; round 2, 32
cross-model disagreements, 10 changed mostly D→K by the retrieval test: §③ Phase 2; 14 total:
report.md case 1 and dedup.md. "The case was decided by the rule": §③ Phase 2 ("applying the retrieval
test as the decisive criterion"; six labelling principles). The risk sentence is my framing, not a
recorded finding.
~83% at the end; October embedding thresholds; one labeller; 25 SPs cannot separate 8%:
report.md case 1 and case 5.
Panel: report.md case 2; labeling/experiment_log.md §3a; fine_tuning/dedup_classifier/experiment_log.md
"Co-labeling Results" and "Final Labeled Dataset Composition" (617 records; 390 D / 473 K;
review "Manual (claude + user)"). 500–1,000 needed: report.md case 2. 37% / 7% (36.6% / 6.9% in the
fine-tuning log), 80 of 373 = 21.4%, 246 trusted.
Routing rule: labeling/experiment_log.md §3a "Decide"; dedup_classifier log "Labeling reliability".
Review never checked: report.md case 2 "How far to trust it".
Reranker rounds: report.md case 2 "Result" (round 2: five models, no review; two camps; 514 of 1,848
over-credited vs the two careful models); labeling/experiment_log.md §3b (ChatGPT and Claude Sonnet
run by hand as voters).
Sampled reads: sampled_reads/report.md "Who the readers are", §2 (five steps; four features), §3
(voice rewrite 19 of 90, gate 1), §4 (re-reads: 13 and 33 held; 29 → 19 of 73; one reader per item;
pools of failure cases; no owner calibration). Persona line: §2 and persona_line/README.md (stance
question; 9 of 30 vs 3 of 10; 10-pair baseline limit). Packet item: persona_line/stance_packet_1.md
item q04, shortened (both messages cut after their second sentence).
Scores: scoring/report.md Layer 2 and Layer 3 (kappa, precision/recall, McNemar on the disagreements,
exact intervals, items from one game not independent, owner checks spread across games).
Calibration step and its gate: labeling/report.md "Anchor to a person" and "What is missing";
the gate values from code (see completion note). Owner-check packets for three sources:
report.md §5 of the techniques and "Golden sets against what is deployed today" rows 1–3;
owner_checks/factual_errors/GUIDE.md (written rule, worked examples, judge answers kept out of view).
Sample sizes 62 / 246: report.md technique 1 and "What we would do differently", row 1.
-->

<!-- Completion note (2026-10-25)

Structure. The brief's subsection order was: reusable vs one-off; selecting and blinding; labelling
rules; model panels; measuring disagreement. I moved "labelling rules" (the 65-case dedup set) before
the panel, because the panel story needs the dedup task and the duplicate rule already explained, and
moved "selecting and blinding" (the sampled reads) after the panel, so the lead story comes earlier.
Selection without bias (seeded, outcome-blind draws) is folded into the sampled-reads subsection
rather than given its own heading. I added a short closing "What remains open". The retrieval
"incomplete-label" case (map.md) is not used: the brief does not ask for it and the page is near length.
The brief's exhibit "a small confusion table with denominators" is the tier table; a true confusion
table is not possible from the report numbers (see below).

Claims I was unsure of, for the verifier:
1. The split-case denominators. The records give 37% (36.6%) and 7% (6.9%) but not how many of the 244
   split cases had a discard majority and how many a keep majority. I did not derive them. The verifier
   could take them from the review log (colabeling_log.jsonl) if a fuller table is wanted.
2. Reranker round 2. labeling/report.md (rewritten 2026-10-23) gives two camps at 73% within and 36–43%
   across; labeling/experiment_log.md §3b (June) gives 71–74% among the auto models and 56–68% with
   ChatGPT. These may be different measures. I used neither set of percentages, only the report's
   "514 of 1,848 over-credited, measured against the two careful models". I wrote "the two voters run by
   hand" for "the two careful models"; the log names ChatGPT and Claude Sonnet as the hand-run voters.
   Please confirm they are the same two.
3. Who labelled the 65-case set. The records say "human", "a person", "we"; the report's comparison
   table implies the owner's time. I wrote "one person labelled", without "I".
4. "Every model tested rejected the same few labels" for both revision rounds. Round 1 is recorded as
   uniform cross-model failure; round 2 as "32 cross-model disagreements reviewed", "triggered the same
   way". I kept "twice" on that basis.
5. Sample sizes. The report gives 62 / 96 / 246; the code's docstring gives 62 / 97 / 246 at p = 0.8.
   I used only 62 and 246, and took "at an expected agreement near 80%" from the code.
6. I named the panel's vendor (Gemini) because the same-vendor point depends on it. Remove it if model
   names should stay off the page.

Mechanism claims checked in code:
- Blind packets: evaluation/experiments/persona_line_screen.py `packets()` (seeded shuffle, opaque ids
  q00.., random A/B order per item, blind_key.json written separately). The five steps are from the
  sampled-reads report; I checked one runner, not all seven.
- Calibration gate defaults: evaluation/src/labeling/config.py (min_agreement 0.80, min_ci_lower 0.75,
  bias_alpha 0.05); evaluation/src/labeling/calibration.py (kappa, binomial interval, exact McNemar).
- Sample sizes: evaluation/src/labeling/anchor.py `sample_size_for_ci` docstring.
- Today's pipeline voting (unanimous / strict majority / tie routed to a person): voter.py. The May
  863-case round ran on ad-hoc scripts that were later generalised into this pipeline, so the page
  describes the May design from the records, not from today's code.
- Dedup: the page describes the May-era mechanism (new lesson against its most similar stored ones,
  keep or discard). Today's code adds a deterministic gate on structured fields (Agents/memory/
  dedup_gate.py) that did not exist when the labels were made; that does not affect this page's claims.

Left off deliberately (Handle with care, and the general bookkeeping rule): that July reads left no
record; the runner's named owner second-reader pass with no record found; the Phase 3 reads' rubric
not kept; the dedup label file's stale metadata; labellers unnamed for some sets; the subscription and
cost details; the judge's model name from the owner-check guide; how long since the labelling stage
was used. Kept, because they change how to read results: the review was never checked; one reader per
item; no person has checked the expanded game's model-read sets; the calibration step is built but not
run on real labels.

Rubric self-scores (Level 2, 0/1/2):
- Reader orientation 2: the opening states the problem (references can be wrong) and the decisions.
- Added depth 2: the rule-writing, label revision, tier table, blind steps and scores go beyond Level 1.
- Conceptual coverage 2: human labels needing revision, model-panel shared bias, model readers with
  blinding, and agreement measures stay distinguishable; written expectations are linked.
- Paragraph clarity 2 (I split the panel's result from its scope).
- Narrative economy 2: the panel's finding is told once; the Level 3 page carries the class detail.
- Experimental separation 2 (required): the 65-case set, the 863-case panel, the reranker round, the
  persona read and the voice-rewrite read are each named with their own sample and setting.
- Interpretation 2 (required): "suggested a lean" is labelled as inference; agreement measures sameness;
  the review is the reference, not human validation; the persona baseline is limited to 10 pairs.
- Evidence and ownership 2 (required): "I" only for the panel review (record: claude + user); model
  readers stated as Claude models; the 65-case labeller written neutrally; numbers as in the reports.
- Technical accessibility 2: dedup, gold/silver, kappa, precision/recall and McNemar explained in place.
- Exhibits and links 2: the comparison table, the tier table and one packet item each support a claim;
  the Level 3 link sits under the featured subsection, which keeps the finding and its caveat.
Approximate length: 2,000 words of page copy including tables and captions, at the top of the range.
-->
