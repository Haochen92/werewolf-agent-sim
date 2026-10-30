# Matching advice to the current situation (Level 2, draft)

Restructured 2026-10-27 after the owner's review: two halves, describing a situation (the fields, why they
were chosen, how both sides fill them alike, the query) and finding the lessons that fit (cells, search,
the fit review as the case for filtering, the stage filter). The epistemic rule stays on the extraction
page; lookup reuse and the retry detail left the page. Claim scope is recorded in
[`../memory_presented_set.md`](../memory_presented_set.md).

---

## Matching advice to the current situation

A lesson is right on some boards and wrong on others. Two Vigilante night lessons in the published store:

> "With no confirmed wolf, no caught lie and no public evidence naming a specific player, hold fire and keep
> your bullets, since a blind shot risks killing a Town player and spends a bullet that cannot be
> recovered."
>
> "If you have publicly claimed Vigilante and still hold unspent bullets, fire at the best-supported suspect
> tonight instead of holding again. … an unspent claimed bullet makes you the wolves' priority kill and dies
> with you."

These recommendations assume different conditions. The first was written for an early night with eight
or nine others alive; the second for a Vigilante who had claimed openly, with six alive and the evil side
one or two kills from parity. Retrieving advice about the right role and action is not enough: the
conditions that justify it must also match.

My first memory put each role's whole strategy document into every prompt, without selecting advice for
the current situation. Players applied advice where it did not hold. I replaced this with
**retrieval-augmented generation (RAG)**: before a decision, the system describes the player's situation,
searches for lessons associated with similar situations, and adds a small selection to the prompt.
[Extracting and synthesising lessons](../extraction_synthesis/extraction_synthesis.md) explains how those
lessons are produced.

The retrieval design has two responsibilities: represent the conditions that change a decision, and
select lessons whose conditions match. A shared situation schema addresses the first; semantic search
and explicit constraints address the second.

### Representing the conditions that matter

Each lesson is stored with its **situation**: a description of the board at the moment the lesson applies,
written in a fixed set of fields. In June 2026 I rebuilt those fields by going through every role and phase
with one question: what about the board changes the right decision here?

A replay showed what the old fields missed. A lesson written for the final three players was put into 20
mid-game town votes, and players rejected it 13 times, on the numbers: "we are still at 5 players, not
final-three." Players reason on exact counts, but the only field that carried the stage of the game was a
three-way label: early, mid or late.

The rebuilt fields describe what the Vigilante pair turns on:

| Field | What it records |
|---|---|
| Stakes | Players alive, how many eliminations the nearest evil side needs to win, whether today could decide the game, and a sentence on what that means |
| Information | What is confirmed, claimed or unknown, and the gap between what the player knows privately and what is public |
| The room | Where the discussion stands and the player's own position in it |
| Exposure | How much suspicion the player faces now, and what a visible move would cost |
| Targets | Who the realistic choices are |
| Counters | Uses of a limited ability left; whether a wolf's partner has been revealed |

Each role and phase uses the subset that matters to it: a discussion turn weighs the room, a night action
the targets and the cost of spending an ability.

Extraction records these conditions in observations; synthesis writes the situations attached to
lessons. Before a live decision, a short call to the player's model describes up to two distinct problems
it faces, using the same role-and-phase schema. One shared function assembles the text fields in a fixed
order for embedding. This keeps stored situations and live queries structurally consistent, although the
model can still misdescribe the board.

Both stored situations and queries must use only what that player could know, following the knowledge
rule on the extraction page. They describe the board; the recommendation remains a separate field and
is not embedded for situation matching.

#### Semantic similarity and structured constraints

Search compares **embeddings**, vectors that place texts with similar meaning close together. Semantic
similarity does not reliably preserve distinctions such as five players alive versus eight, or agreement
versus opposition. Each situation therefore has two complementary representations:

- **Structured fields** hold numbers and labels such as players alive, uses left and whether a wolf's
  partner has been revealed. Code can use these as explicit retrieval constraints.
- **Embedded prose** describes their strategic meaning, such as “one elimination from a wolf win”.
  Search uses this to find situations with similar context.

The structured values themselves are excluded from the embedding. Their reliability matters: a July
2026 audit of over 20,000 query situations found that the model counted players alive correctly 97% of
the time, but the Vigilante's bullets left only 16% of the time. Code now computes the values it can,
supplies them to the model and overwrites the corresponding output fields. This makes those fields
reliable and reduces the risk of contradictory prose, without guaranteeing the model's description.

Code can compute these values only for a live query. A stored lesson's values are written by the
extraction model, because a lesson drawn from a whole game has no single board to compute them from: the
one stored field checked, uses left, was exact 84% of the time, and a hard filter would inherit every
error. Cells are also small, so exact constraints leave many decisions with nothing: even the coarse stage
filter below, with players alive in three bands, left 17 of 96 lookups empty when it did not refill. So the
prose keeps carrying what the numbers mean, and a board one step away still matches.

More descriptive detail does not necessarily improve retrieval either. In a small ranking study, the
model regenerated its queries with an added “core dilemma” field, and they were scored against relevance
labels gathered with 20 hand-written ideal queries. On the six cases that could be compared fairly, they
ranked lower. That first comparison also changed other parts of the prompt, but removing the field alone
was the largest single gain of the round. It stayed removed.

**Link (Level 3):** [The field that felt right and lowered retrieval](../../../evidence/extraction/situation_summary/report.md#6-case-study-the-field-that-felt-right-and-lowered-retrieval):
the hand-written queries, relevance labels and comparison limits.

### Finding the lessons that fit

#### Selecting a small set of lessons

The store is divided by role and decision phase: a Healer's night action, a wolf's day vote, a Seer's
discussion turn. Each division is a **cell**. A player searches only the cell for its own role and the
decision in front of it, so a Healer choosing whom to protect never sees advice about whom to vote out, and
no player reads lessons written from another role's point of view.

The search returns a capped selection of nearby lessons, removes duplicate hits across queries and
supplies at most six lessons to the player. Selection also favours lessons with a positive recorded
history while reserving an opportunity for untested advice. These are selection heuristics, not proof
of effectiveness; [Curating the lessons](../curating_lessons/curating_lessons.md) explains the credit and
retention rules.

The lookup policy skips the first day and night, and human seats bypass the agent pipeline. Town
discussion turns also receive no lessons, following the credit problem discussed in the curation page:
the scoring rules cannot adequately assess the cost of withholding information.

#### Did retrieval find applicable lessons?

Semantic search often returned lessons about the right role and action but the wrong circumstances—for
example, endgame advice while seven to nine players remained. I sampled 96 lookups from seven ten-seat
games, using a store built from 12 games. Four model reviewers judged only 36 lookups to contain at least
one applicable lesson.

| Reviewer assessment | Finding |
|---|---|
| Lessons judged applicable | 39 of 268 (15%) |
| Lessons judged partly applicable | 79 of 268 (29%) |
| Lessons judged inapplicable | 150 of 268 (56%) |
| Lookups with at least one lesson judged applicable | 36 of 96 |

#### Metadata filtering by game stage

This motivated **metadata filtering by game stage**. The filter excludes lessons with incompatible
player counts, partner status or remaining ability uses, then optionally refills the empty slots with
other candidates. Player counts are grouped into three bands: eight or more, five to seven, and four
or fewer.

A replay on a larger, 40-game ten-seat store compared the options below. A new set of four model
reviewers assessed all three options using the same rubric; the unfiltered baseline is for this larger
store, not the 12-game store above.

| Setting | Lessons judged applicable | Lookups with at least one lesson judged applicable |
|---|---|---|
| No filter | 19% | 41 of 96 |
| Stage filter, refilled from same-stage lessons | 24% | 52 of 96 |
| Stage filter, gaps left empty | 27% | 33 of 96 (17 empty) |

Stricter selection created a trade-off. Removing mismatched candidates improved the proportion judged
applicable while leaving some decisions without advice. Refilling helped on the larger store,
increasing lookups with an applicable lesson from 41 to 52. On the smaller store, replacements were
mostly still judged unsuitable, suggesting that sparse coverage limited what retrieval could find.

Filtering remains disabled by default because coverage in the current ten-seat store is still limited.
Older nine-seat stores are much larger, but contain lessons from a different cast and ruleset; their
size does not resolve gaps in the ten-seat store. As more ten-seat games supply observations and lessons,
the store may offer enough suitable alternatives to make filtering worthwhile. That needs to be checked
again as it grows. The filter can also exclude useful advice at player-count boundaries and does not
check every event a lesson might require, such as a rival role claim.

These results are model reviewers' assessments, not the gameplay agents' acceptance or rejection rates.
I read a sample of the cases, but the reviewers were not systematically calibrated against human labels.
The review also did not separate missing store coverage from ranking or situation-description errors;
that is a proposed follow-up.

### What remains open

A future follow-up would review every lesson in the relevant cell for each of the 96 recorded ten-seat
queries, using the preserved 40-game store. This would help distinguish missing coverage from applicable
lessons ranked below the returned set, with and without metadata filtering. Query errors would be
tracked alongside those results rather than treated as a separate, mutually exclusive cause.

Before relying on model reviewers, I would label a blind sample and measure their agreement with it.
Reviewers would cite the deciding facts for each assessment. Code could check metadata compatibility,
but passing those checks would not establish applicability, and stored metadata would also need
verification. This investigation is proposed future work and has not been run.

The latest published store has not had an equivalent review. Whether better retrieval leads to better
play remains a separate [gameplay comparison](../testing_memory/testing_memory.md).

<!-- Sources and verification, 2026-10-27:
Owner clarification: stage filtering remains off because the current ten-seat store has limited
coverage; revisit as additional ten-seat runs supply lessons. Larger historical nine-seat stores do
not resolve current coverage. Future growth is a possibility, not a measured filtering benefit.
Follow-up framing: applicability figures are uncalibrated model-review labels, not player adoption or
objective ground truth. Full-cell coverage/ranking audit and blind human calibration are future work
only; no new research run. Causes can overlap. The 40-game replay used a new reviewer set relative to
the 12-game read (v8 experiment_log, 2026-10-13), with shared reviewers across its filter conditions.
Owner-requested revision: consolidated shared representation; shortened query and selection mechanics;
retained both fit tables and their distinct store baselines. Removed claims that the example lessons
are proven sound, deterministic fields guarantee prose, or opening turns cannot match advice. Older
reranking counts omitted from the narrative; source direction remains 38% -> 36% non-applicability.
Vigilante pair: memory_records strategy_points/vigilante/night_action keys 379dfbbe-e067-4e8d-8b4d-275a5f22c7b7
(situation: early night, eight or nine others alive, information-starved) and
92ce4379-07f9-44a7-bfe0-c0075b5ee573 (claimed Vigilante, six alive, evil one or two kills from parity,
information-starved); actions quoted, the second abridged.
First version: evidence/memory_system/experiment_log.md Era 1 Phase 0 (injected wholesale; advice applied
where it did not hold).
Field choice: evidence/extraction/situation_dimensions/report.md §1 and §3 (June 2026 walkthrough; the
final-three lesson rejected 13 of 20 times; the before/after table, condensed); per-cell schemas
Agents/schemas/memory.py.
Numbers vs prose: situation_dimensions §1, §3; audit §5 (20,284 query situations, 6,275 decisions, three
nine-seat runs; players alive 97% of 6,099; bullets 16.4% of 1,109; no AI judge); computed and overwritten:
situation_agent.py _override_deterministic_dims.
Shared composition: Agents/schemas/memory.py::compose_situation_embed; situation_summary/report.md §1;
knowledge rule: Agents/prompts/standards.py EPISTEMIC_STATUS_RULE (told on the extraction page).
Query: situation_agent.py (player's game model, max two situations; one retry, then a generic role-and-day
query in the same cell: situation_summary §4); query errors: 37 of 96, situation_summary §5.
Core dilemma: situation_summary/report.md §6 (owner-written ideal queries for 20 frozen cases; 340 labels;
dilemma field lowered ranking on the six fairly scorable cases, 0.79 vs 0.87; removal the largest gain;
108 later labels by a model). The labels' authorship: "human-labelled", the owner's ranking test.
Cells and isolation: Agents/memory/retrieval/accessors.py (role-keyed namespaces; a caller queries only
its own role); evidence/agent_boundaries/report.md (enforced by construction).
Caps and ordering: retrieval/pipeline.py (fetch 5), accessors.py (keep 3; cross-situation dedupe),
filters.py (proven = >=5 follows and positive > negative; exploration swaps the lowest proven).
Skips: plan_gating.py (day 1; TOWN_UNSERVED_PHASES = day discussion; v8 decisions §17); humans bypass.
Fit review: v8/experiment_log.md (2026-10-12; 12-game store; four Sonnet subagents; 39/79/150 of 268;
36 of 96; Healer 0.887 vs 0.829); gate games had no town day lookups. Owner's own sample read: owner,
2026-10-27.
Stage filter: dimension_gating.py (stage_mismatch, drop_other_stages; alive buckets 8+, 5-7, <=4);
v8/report.md and situation_summary §5 (40-game pre-publish store, same readers; 19%/41, 24%/52, 27%/33
with 17 empty; refill on the 12-game store mostly misfits, 2 of 28). Off: Agents/config/run.py
DEFAULT_STAGE_FILTER = False.
Gating: situation_dimensions §6 (24 held-out nine-seat town votes; changed the top five in 23; not
applicable 38% -> 36%; left off; verdict "no benefit measured"). Reranker: evidence/retrieval/report.md
(nine-seat, directions only, stayed off). Event-keyed misfits: situation_dimensions §7.
Removed from the page (owner, 2026-10-27): lookup reuse and the 60 -> 38 count (v8 decisions §10); the
seats' follow/override verdicts (65 sound, 25 mixed); retry detail (chapter 1 agent turn). -->
