# Explanation prototype: Making assessments explicit and testing how they shape decisions

Page: `writeup/context_engineering/structured_assessments/turn_request.md` · Level 2 · Purpose: design decisions
tested by replays (example B), in the order the purpose unfolds · Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (`../../_authoring/l2_outlines.md`, "Page 3";
the owner's rulings at its top apply). No second stop; the sample passage below is the prototype.

Authoring material, not page copy. The cold reviewer does not see it. Topics: `../../content_plan.md`
§2 section 3, §5, §6, §7; presentation: `l2_outlines.md` page 3; constraints: `writeup/_planning/map.md`
blocks 145–150, 152 and the chapter's Handle-with-care list; the owner's chain-of-thought ruling in
`writeup/_planning/skills_inventory.md` ("Terms corrected or held back").

## Reader and explanation

- **Reader outcome:** the reader can say how an agent's turn is made to state its assessments as
  fields before it acts, what each field lets an investigator see when a decision goes wrong, and why
  a fuller assessment still had to be tested against the decision it produced (compare-candidates
  helped where evidence was strong and broke the ballot it was written for).
- **Starting knowledge:** the Level 1 section supplies the diagnostic motive, the two failures (an
  instruction in a field description skipped; vote-first notes that never committed, and the May
  field moved before the action changing the action), the four-field order, that the record is
  written assessment not internal reasoning, the three agreement figures (75%, 87.5%, 92.5%) and the
  adverse 40% → 26%. New here: the fields by what each holds; required field; frozen turn / replay;
  the lot; thinking effort as a call setting.
- **Concept order:** what a written assessment must reveal (the four fields, seen on one turn) →
  how to get the requested work into the answer at all (required, unambiguous, only when it applies)
  → where it sits relative to the action, and why order compliance is not decision quality → whether
  asking for more of it helps (the main case) → choices the prompt steered by accident (a separate
  failure class) → thinking effort as a separate lever, and what the current combination leaves
  untested.
- **Likely confusion:** reading "the action follows the written reasoning" as "the reasoning
  improved" or as a claim about the model's hidden reasoning; and reading the compare-candidates
  result as a finding about the sentence in general rather than on one game's votes. Both are
  prevented by the scoping sentence in the opening and the limit beside the result.
- **Section order:**
  0. Opening: the purpose, the term named once with its scope, replays as the method with the
     swing-of-five limit (two short paragraphs).
  1. What the written assessment needs to reveal: the healer's frozen turn as an annotated record
     (reads, verdicts, note, action), what each field let me see; the remedy is page 4's.
  2. Getting the requested assessment into the answer: three ways the work went missing and what
     made it appear (required verdict field + instruction in the prompt body 0.27 → 0.97; every
     field required, "no" a value; a field only when it applies: verdicts only with lessons, the
     per-turn brief, passes 24 of 25 → 16 of 25); the `TurnOutput` skeleton.
  3. Putting assessment before action: the July reads detail; the prompt/schema disagreement in the
     text output mode (15 of 24 → 13 of 23 → 24 of 24); compliance kept apart from quality; today's
     order untested for message quality.
  4. Testing whether a fuller assessment helps (main case): compare-candidates with its setup, the
     Vigilante ballot beside the day-4 reads, cost, why not kept; then the ballot tag and cite-exactly
     in a short table; one sentence on prescribed suspicion cues removed, kept on principle.
  5. When the prompt supplies an accidental cue: the night-1 lot and the example's named seat.
  6. Giving the model more thinking effort: one short table; close with what the current combination
     leaves untested and a one-sentence pointer to the same pattern in other calls.

## Sample passage

The difficult passage is §1: the reader has to see, from the fields alone, what kind of failure a turn
holds. Draft (the exhibit is a real replay sample of the frozen turn; the note it was shown is the one
the game recorded):

> The healer had been roleblocked on night 1. By the middle of day 2 the trailseer had said it followed
> player_7 to the healer that night, and player_7 had admitted the visit without claiming a role. In this
> cast only the Chanteuse, a wolf, can block, and a block is a visit. The healer passed all three of its
> turns that day. Its written assessment shows which kind of failure that was.
>
> | Field | What the healer wrote (one replay sample, the prompt as played) | What it let me see |
> |---|---|---|
> | Reads | player_3: unclear (low): claims trailseer; follow result on player_7 to player_8 is unverified but plausible · player_7: unclear (low): admits visiting player_8 on night 1, no role claim | It recognised the clue: it knew it had been visited, and by whom. |
> | Verdicts | none asked for: no lesson was shown on this turn | No retrieved lesson was in play, so none was misapplied. |
> | Strategy note | "I was roleblocked night 1 and have no results. … Stay quiet unless addressed, watch for claims and the first vote … Do not reveal my role without need." | The approach it set: keep silent and keep the role hidden. |
> | Action | passed | The action followed the note. |
>
> The facts were recognised and the decision agreed with the written approach. What is missing is the
> step between them: nothing connects "I was blocked" to "the blocker visited me" and so to player_7.
> That narrows the failure to a missed inference, and it is the case the deduction engine on the next
> page was built around.

## Evidence and scope

- **Sources:** `evidence/gameplay/turn_prompt/report.md` decisions 5–12 and 15, "What is not
  established"; `turn_prompt/experiment_log.md` §3, §7, §11; `evidence/caching/experiment_log.md` §12,
  §16; `evidence/gameplay/discussion_evidence.md` §7.5, §8.6, §8.7, §6.7;
  `evidence/memory_system/effectiveness/decision_replay/experiment_log.md` (adoption confound step 2);
  `evidence/gameplay/deduction/report.md` §2, §5; `deduction/experiment_log.md` §2, §4, §5, §9; data
  `evidence/gameplay/deduction/data/deduction_injection/` (case `9b3219e5dc1eb831`, as played, low,
  sample 0 of `judged_haiku_low.jsonl`; the carried note from the case state).
- **Claim and limits:** mechanism (fields, order, conditional composition) and replay-tested decisions.
  The action follows the written reasoning; not that reasoning improved; hidden reasoning tokens are a
  separate chain. Replays are selected turns of one game, ten samples each; wording changes moved
  single cases by up to five of ten, so each result is local. Compare-candidates: one game, 11 votes.
  The lot: a rule set for every prompt, not a law of models. Thinking study: enforced-mode counts
  with the live-mode re-run named in a clause; "reported no reasoning tokens".
- **Elsewhere:** the replay method (Evaluation's replays page); the output contract (chapter 1's
  agent turn page); the output-mode story and the layout (chapter 6); the healer's remedy and the
  uptake results (page 4, Level 3); the dedup judge (Memory). Handle with care: counts over 1–5
  scores (no 4.00 → 4.38); the 20% → 10% suspicion-cue drop confounded with an easier board, so
  "kept on principle"; no model family names; the thinking study told once; no p-values; the reply
  brief's "As I said" result in notes only.
- **Open questions:**
  1. The §1 exhibit is a replay sample of the frozen turn (2026-10-16 run, schema enforced), not the
     game's own answer: the frozen case keeps the state before the turn (notes, transcript, night
     records) but not the reads the game's turn wrote. The sample's note and action match what the
     game recorded (passed; the note's stance). The page labels it as a replay sample. If the owner
     wants the game's own fields, they would have to be pulled from the game's checkpoints.
  2. §3's July reads detail: the source gives the override change as a rate (0.06 → 0.17) with no
     denominator named; the page says "about three times as often" and keeps the rate in the comment.
  3. §6: the outline's counts (98 of 160 against 65; 47 against 49 of 115) come from the run that
     pinned the enforced schema; the live-mode re-run (97 of 157 against 122 of 158) is in the same
     log §9 and is named in one clause with a link to chapter 6, which already states it as 62% → 77%.
  4. The outline's §2 says "every field is required" applies to the verdict lists too; the report
     names them as the exception (they default to empty and are removed when no lessons are shown).
     The page says so.
  5. The §1 sample comes from the 2026-10-16 run with the schema enforced; whether game 2f19d908
     itself (2026-10-14) was played in the text mode is not stated in the deduction log. The caption
     names the sample's mode and avoids calling the mode "as played".
  6. The Level 1 says the May adoption field "changed the action itself"; the source is one judge's
     1–5 action score on unpaired turns. This page says "a judge rated actions higher"; the Level 1
     sentence is the owner's to adjust.
  7. Word count: about 3,100 of page copy (about 2,700 of prose outside the tables and the schema
     block) against the 1,200–2,000 guide. The exhibits (the annotated turn, the schema skeleton, the
     thinking table) are about 400 words; the two editorial runs asked for orientation the page lacked
     (the game, the cast and ballots, both output modes, the noise limit's source, the unreported
     ballots) worth about 400 more, and the claims run added scope clauses. What could still go, in the outline's cut-list order: the
     brief's result in §2, the ballot-tag and cite-exactly paragraph, §5's first paragraph. Left for
     the owner to decide rather than cut past the reviewers' findings.
  8. The Level 1's "Explore" line for this page is a placeholder with no link, so `parent_context.py`
     reports "opened directly" on the real tree; the editorial runs used a scratch copy with the link
     added. The Level 1 needs the link once the page is accepted.

## Review resolution

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| **Editorial run 1 (opus, 03:50Z).** §4: the Vigilante ballot could not be followed without the cast, which seats were frozen, and the fact that the recorded ballot was a minority draw (blocking) | Fixed: a cast sentence (Vigilante and Sentinel town, Speculator chose town, Necromancer the one hostile seat, the owner's own), the eleven ballots named by voter, and "the recorded ballot turned out to be a minority draw: 7 of 10 to the Necromancer, 1 to the Sentinel" before the 0 of 10 (data README) | §4 reread whole |
| Ed. 1: day-4 "30 samples" and "the suspect" unexplained | Fixed: "the three day-4 controls, 30 samples, had to find player_1, a wolf" | §4 |
| Ed. 1: the opening's failure list differed from the parent's and the healer example landed outside it | Fixed: one list (missed fact; went wrong between facts and conclusion, including a lesson; decided against its assessment), the example lands on the middle item as an inference not drawn | §0–§1 |
| Ed. 1: 0.27 → 0.97 credited to the instruction move while the parent credits the required field | Fixed: both changes stated, the number attributed as the record does ("that move is what the record credits") | §2 |
| Ed. 1: "three things went missing" did not fit the third item (extra output); the brief and the vote-now line had no stated goal | Fixed: lead-in "failed to match the request in three ways"; the brief moved to its own paragraph with why fewer passes count (votes cast with no reason the town could weigh, §8.6) | §2 |
| Ed. 1: the suspicion-cue paragraph belongs with cues, not with "does a fuller assessment help" | Fixed: moved to §5, retitled "When the prompt supplies the answer" (by design, then by accident); a local change to the approved outline, recorded here | §4–§5 |
| Ed. 1: the thinking table's vote figures turned out to be from the enforced mode only after the table; mixed cost column; no denominator on 82 → 27 | Fixed: output mode in each row, a live-mode vote row added (97 of 157 vs 122 of 158), denominators, cost and time labelled per row | §6 |
| Ed. 1: why thinking effort is on a page that scopes out hidden reasoning | Fixed: framing line, it is the other lever on whether a seat uses what it has and every wording result must be read against it (§6.7, deduction log §2) | §6 |
| Ed. 1: July reads: no referent, override direction unstated, judge unnamed, reads shown back unstated | Fixed in one sentence: the replay that added them; the override is the check memory was meant to get; a model judge; reads shown back next turn (decision 1) | §3 |
| Ed. 1: the schema block names observations and five fields against "four fields" | Fixed: the opening of §1 names reads, verdicts on lessons and observations (two lists, only when memory supplied something), note, then decision | §1 |
| Ed. 1: §5 populations (two 96s) and "seat 1 had taken" | Fixed: 96 night-1 calls named (three roles on 32 situations), "player_1 had been the target" | §5 |
| Ed. 1: healer's and trailseer's seat numbers missing | Fixed in the setup sentence | §1 |
| Ed. 1: a new day-4 result in the closing | Kept, reworded as a limit on the day-4 controls the reader has now met ("also fell across three versions of the code in the same game"); the outline asks for the one sentence | §6 |
| Ed. 1: caption dense; opening overclaims "tested against the decisions" | Fixed: caption cut; "some for whether the field appeared, some for the decision" | — |
| Ed. 1 application question: would prompt-and-schema agreement the other way round work? | Added the recorded reading (the prompt's opening line pulled the model) and that the other direction was not tried; no claim beyond that | §3 |
| **Editorial run 2 (opus, 03:55Z, after the §4/§5 revision).** The "structure, not instruction" lead-in contradicted by the first example, where the gain is credited to a moved instruction (blocking) | Fixed with the claims finding below: the thesis is now "where the request sat, in the answer's fields and the prompt body, as much as what it said"; §2's lead-in says "the request moved, into the answer's shape or into the prompt body" | §0, §2 |
| Ed. 2: 13 → 17 called "helped" against the page's own swing-of-five; the day-4 code-version caveat two sections later (blocking) | Fixed: "helped" now rests on the citations (11 vs 2 of 30); the vote change is stated as within the swing single cases show on these ballots; the day-4 fall stays in the close as a limit on those controls (chapter 6 owns the thread) | §4 |
| Ed. 2: eleven cases listed, four reported | Fixed: one sentence on the rest (Speculator abstained either way, no version resisted the day-6 bluff, day-3 controls 30 and 28 of 30) | §4 |
| Ed. 2: "schema sent as text" used before it is defined | Fixed: both output modes defined in the opening's method paragraph | §0 |
| Ed. 2: 18 turns vs 25 samples; "nine seats" | Fixed with claims finding 17: five open-floor turns, five samples each; "six of the nine samples" dropped | §2 |
| Ed. 2: why reads before verdicts | Fixed: the schema was reordered to match what the prompt asked; "which assessment field should come first was not itself tested" | §3 |
| Ed. 2: "three times as often" compared with what; "thinner"; "July" | Fixed: compared with reads written after the note; the judge named; month dropped | §3 |
| Ed. 2: which model plays now; levels; the wording experiments' level | Fixed: "wherever it is still used"; "all replayed at the lower level of the model in use"; levels left as lower/higher on purpose (the two models' settings differ in name) | §6 |
| Ed. 2: the game never described; roles unglossed; "I was the Necromancer" unexpected | Fixed: one game line in §1 (town, wolves, solo seats, day votes, night actions, the owner sometimes plays); glosses for healer, trailseer, Chanteuse, Speculator, Necromancer; "the Sentinel's claim true" | §1, §4 |
| Ed. 2: §5 belongs elsewhere | Declined to move (the outline places the lot and the example here); the section now opens with why it belongs: a written assessment can only justify the choice it is asked about, and with no evidence the prompt itself decided | §5 |
| Ed. 2: the noise limit's source arrives late; 24 misquotes of what | Fixed: the source named in the method paragraph ("when true facts were added to one game's ballot lines"); the misquote count has no denominator in the source, so "unchanged at 24 before and after on that replay set" | §0, §4 |
| Ed. 2: observations vs lessons; the compliance paragraph repeats the parent | Fixed: one clause each in §1; the compliance paragraph cut to two sentences | §1, §3 |
| **Claims review (opus, 03:55Z).** "Each was tested against the decisions it produced" overstated (all-required rule, verdict drop, suspicion cues untested on decisions) | Fixed: "replayed where they could move a decision, some measured on whether the field appeared, some on the decision itself" | §0 |
| Claims 2 and 4: 0.27 → 0.97 is the share of answers giving one verdict per item (row reliability), measured on observations with the forced field already present; credited to the instruction move | Fixed: measure restated, the forced field "gave each verdict a slot", coverage "rose only when the instruction moved", "with the field itself unchanged" (forced_schema_screen log checked) | §2 |
| Claims 3: the verdict lists default to empty today | Fixed: "the one exception to the rule below; they default to empty, and coverage rests on that prompt-body instruction" (lineup_output.py checked) | §2 |
| Claims 5: the exhibit's night record said "learned nothing tonight"; the silence has its own cause; the sample's mode unnamed | Fixed: the night record's clause on the page, "under a night record whose last clause worked against that step and a self-set stance of silence"; caption says "with the schema enforced"; both deferred to page 4 | §1 |
| Claims 6: ballot tag "without moving the day's total" wrong for day 5 | Already removed before the claims run; now "more than any effect tested" | §4 |
| Claims 7 and 8: 13 → 17 "not significant"; evidence-dependence stated as a property | Fixed as above; "on this game it helped where the evidence was strong and hurt where it was thin, so its effect looked dependent on evidence a fixed wording cannot see in advance" | §4 |
| Claims 9: cite-the-record was an earlier study on an earlier model with no reasoning tokens | Fixed: so stated, "did not reduce misquotes there" in substance ("unchanged … on that replay set") | §4 |
| Claims 10: "changed the action" rests on a 1–5 judge score | Fixed on this page: "a judge rated actions higher once the field … moved before them". The Level 1 says "changed the action itself"; flagged for the owner, not edited | §3 |
| Claims 11: the example's effect never re-measured | Fixed: "points to the example as the cue … its effect on day 2 was not re-measured" | §5 |
| Claims 12: 267 are samples (89 cases × 3) | Fixed in the table and the prose ("36 of its 89 cases") | §6 |
| Claims 13: the dedup judge's finding is input order, not answer order; "as much as the instructions do" unmeasured | Fixed: "a related pattern, that where a request or a fact sits changes the result … the deduplication judge's input order" | §6 |
| Claims 14: three of the seven baseline votes rested on a misquote | Fixed: clause added | §4 |
| Claims 15: "the same model" read as today's model | Fixed: "on that earlier model" | §3 |
| Claims 16: the 1,200 characters were the memory instructions alone | Fixed: "The memory instructions, about 1,200 characters, and later the verdict fields and their example" | §2 |
| Claims 17: the 25 samples are the five vote-reason turns; the after arm bundled other changes; first wording 23 | Fixed: five turns, five samples each; the 23 and the bundling are in the sources comment (the page gives the second wording's result as the record does) | §2 |
| Claims, not checked: whether game 2f19d908 was played in the text mode (decides whether "as played" names the mode) | Open question 5 below | — |

Check technical repairs against sources. A misunderstanding can identify a problem even when the
reviewer's proposed solution is wrong. Record material findings, not cosmetic bookkeeping.

## Trial record

Draft snapshots: `turn_request.first-draft.md` (before reviewer edits); `turn_request.reviewed-draft.md`
(after both editorial runs and the claims run). Reviews: `turn_request.review-editorial.claude.20261031T035033Z.*`,
`turn_request.review-editorial.claude.20261031T035534Z.*` (the second, on the revised §4/§5),
`turn_request.review-claims.claude.20261031T035539Z.*`. Owner revision: not yet.
Model and owner interventions: drafted by one Claude Code agent on the default model, in parallel with
pages 1, 2 and 4; outline approved in conversation 2026-10-31 (no second stop); reviewers run with the
`claude` CLI.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
