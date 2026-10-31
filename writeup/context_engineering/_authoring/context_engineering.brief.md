# Explanation prototype: chapter 3, Level 1 (title pending)

Page: `writeup/context_engineering/context_engineering.md` · Level 1 · Purpose: the chapter page for
Group B's first chapter · Date: 2026-10-30
Checkpoint: re-cut 2026-10-30 on the owner's spine (the value proposition: keeping the facts straight
for a small, low-cost model is harder than it looks; four kinds of failure, four remedies). Owner agreed
the spine, the chain-of-thought wording and the title direction; sample passage unchanged. Topics agreed in `../content_plan.md` (revised 2026-10-29).

Authoring material, not page copy. The cold reviewer does not see it.

## Reader and explanation

- **Reader outcome:** the reader understands that keeping the facts straight for a small, low-cost
  model is harder than it looks: giving it the game state and a general instruction was not enough, and
  each kind of failure observed needed its own remedy.
- **Starting knowledge:** chapter 1 (the game, roles, day and night, one model call per turn);
  chapter 2 (each seat receives only what it may know). New here: a lie (part of the game) vs a mistake
  about the record; a recorded claim vs an established fact; written reasoning before the action.
- **Concept order (owner spine, 2026-10-30; organised by kind of failure, not as a ladder: the only real
  sequence is the engine coming after the rest):** the naive approach and why it fails → getting facts
  wrong → losing earlier context → not using the information in the decision → not connecting the dots.
- **Likely confusion:** "checked claims" read as true facts; a replay result read as an error rate; the
  engine's uptake read as better play; "chain of thought" read as a claim that reasoning improved.
- **Section order:**
  - Intro: the obvious approach (give the model the game state and a general instruction) and why it
    was not enough on a small, low-cost model; mistakes about the record, distinct from lies; about 3%
    of public messages in the earlier game; four kinds of failure, each with its own remedy; code
    computes facts, the model keeps judgement; context engineering named as the discipline; the figure
    of one turn's prompt grouped by author.
  - Getting the facts wrong (misreading, inventing, miscounting): printing the facts alone did not stop
    the error; facts printed and worded as the player's own record, rules stated in full; lead: the
    board plus a read of every player, 48% → 30% on 100 error-prone turns, or the Sentinel (10/10 →
    0/10); the invented check stays Evaluation's.
  - Losing earlier context: the day summary and the claim ledger, the three blocks by author, claim vs
    fact (the sample passage).
  - Not using the information in the decision: the answer structured so the model writes its assessment
    before acting (reads with reasons, a verdict on each lesson shown, the private note, then the
    action): a structured form of chain of thought; lead: reasoning and verdicts before the vote raised
    agreement between stated reasoning and the vote from 75% to 92.5%; limit: the action changed, not
    proof that reasoning improved. Compare-candidates moves to Level 2 page 3.
  - Not connecting the dots: the deduction engine, graded certain / conditional / alternatives, built
    after the rest; held to chapter 2's boundary in one or two sentences; lead: the roleblocked healer
    (the deduction in 10 of 10 replays, still silent). Optional, if the owner runs it: whether a larger
    model connects the dots without the engine.
  - Close: no whole-game error rate after the changes; a plain link to Memory.

## Sample passage

*(Section 2 as page copy. The table's middle row quotes a real prompt line from the day-summary
report §3; the rest is description.)*

#### Carrying earlier days forward without changing who said what

A player cannot reread every earlier day, so each day is condensed once it ends. A mistake in that
condensed account is not one player's private error: every player reads it the next morning. So each
statement keeps its source, and a player reads earlier days as three blocks with different authors.

| Block | Written by | Example |
|---|---|---|
| The game master's record | the game engine | night outcomes, every ballot, each revealed role |
| Claims | each speaker's own claim fields, checked by code against the record | "player_5: claimed investigator. Night 1: checked player_9, says they read Suspicious. Record: player_9 was revealed as illusionist, as claimed." |
| Accusations | a summariser model | who argued what against whom, labelled as claims, not facts |

A record check confirms only what the public record can settle. Where the record fits more than one
reading it says nothing, and a claim the record cannot contradict stays a claim.

The rule came from a game a summary decided. The Investigator said "I was roleblocked last night"; the
summary recorded it as the Investigator claiming to be the Chanteuse, the wolf role that blocks. The
next day another player raised the claim, the Investigator accepted the false premise about itself, and
it was voted out 7 to 1. The summariser now records what was said and never judges it, and code drops
any claimed action that could only have been done to the speaker. The error was too rare to recur when
the day was replayed, so the code rule, pinned by a test, is the guard.

*(About 260 words: over the Level 1 section guide. If the checkpoint keeps the table, the game story
shrinks to two sentences and its detail moves to Level 2 page 2.)*

## Evidence and scope

- **Sources:** `../content_plan.md` §2 (sections, sources per case); day summary:
  `evidence/extraction/day_summary/report.md` §3, §4, §7; Sentinel: `evidence/gameplay/turn_prompt/report.md`
  decision 4; compare-candidates: decision 9; healer: `evidence/gameplay/deduction/report.md` §2, §5.
- **Claim and limits:** mechanisms plus replays of selected failures; no whole-game error rate after the
  changes; engine uptake, not changed behaviour; the summary fix guarded by code, not by the instruction.
- **Elsewhere:** how errors were found and counted → Evaluation; the invented check → Evaluation and
  Level 2 page 1; the engine's correctness tests → Evaluation's code checks; the hidden-roles test in
  full (Alice/Bob table) → Level 2 page 4.
- **Open questions:** the chapter title (see the checkpoint).

## Review resolution

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| Ed #1 (blocking): game terms before introduction | Explained: one orienting sentence on night visits and day votes; each role glossed where used. Full game intro declined (chapter 1 carries it) | Intro, all sections |
| Ed #2 (blocking): replay method only at the end | Relocated: method and its limit in the intro; the closing caveat removed | Intro, close |
| Ed #3, claims #1: what the healer saw and what the engine did | Corrected: the only reported visit; the engine replaced the misleading "learned nothing" clause with the certain line and added general lines; naming player_7 left to the model; 2→8 scoped as engine on vs the original record. Also corrected in the deduction log §8 and the report note | Section 4 |
| Ed #4, claims #4: 92.5% vs 75% | Corrected: 40 replayed votes, earlier model, a judge naming the voted player from the reasoning; both changes credited; "the vote follows the reasoning more closely" | Section 3 |
| Ed #5, claims #3: e06 paragraph and fix | Corrected: the never-judge principle stated on its own; e06 as why a code guard is needed; fix as in §7 | Section 2 |
| Ed #6: "lessons from memory" undefined | Explained in one clause | Section 3 |
| Ed #7, claims #12: which sentence the Sentinel replay tested | Corrected: the missing rule sentence; the ranking line no longer attributed to it | Section 1 |
| Ed #8: opening list did not match the sections | Corrected: four kinds named in section order | Intro |
| Ed #9: "earlier nine-player game" | Explained: "the first, nine-player version of the game" | Intro |
| Ed #10, claims #2, #7: "no reasoning"; other models | Corrected: reasoning tokens; the two mechanisms named; other models scoped to "no reasoning tokens under an enforced format at their low settings" | Section 3 |
| Ed #11: mixed paragraph | Relocated: the repeated caveat removed; test and authorship kept as one short paragraph | Section 4 |
| Ed #12, claims #8: figure labels and caption | Corrected: grouped by source; claims stay claims | Figure |
| Claims #5: one model framed for all evidence | Corrected: "the small, low-cost models the game has run on" | Intro |
| Claims #6: "So" made printing the fix for an error printing did not fix | Relocated: the "remaining wolf" example moved to the intro as evidence that printing alone was not enough | Intro, section 1 |
| Claims #9: "every turn" | Corrected: "a turn took nearly three times as long on this case" | Section 4 |
| Claims #10: closing "each result is a replay of a failure" | Removed with the closing caveat; the intro says "most results" | Intro |
| Claims #11: claims row | Corrected: the summary's transcription when a player filled no field | Section 2 |
| Claims #13: "from the rules alone" | Corrected: "the rules and what the player has seen" | Section 4 |

| Restructure (owner 2026-10-30) | New opening section "What a player needs for its turn": the input table with a first-version column and a real Healer excerpt; the four failures become refinements of its rows | Whole page |
| Ed3 #1 (blocking), claims3 #2: the excerpt mixed renders | Corrected: excerpt from the engine-off render, whose night line is the one the game showed | Opening, section 5 |
| Claims3 #1: 92.5% vs 75% without the reorder's cost | Corrected: the same study's 2x2 (votes right 26% against 40% with the note first) stated; "the vote follows the reasoning, including when it is wrong" | Section 4 |
| Claims3 #3: order of events (later replay presented as the deciding criterion) | Corrected: "The engine came first; a later replay showed the other ways" | Section 5 |
| Claims3 #4–#10, Ed3 #2–#11 | Corrected as suggested: earlier nine-player version (July); no "skipped thinking"; not like-for-like; night-results row; "a higher thinking setting"; "about twenty times"; "filled gaps"; units and the two bundled changes for 48%→30%; claim fields introduced; principle scoped to "most"; e06 chain spelled out with its replay note; the stray note sentence removed; "grading rule" explained | Throughout |

Word count after the third round: 2,211 (the owner asked for the opening to be the most detailed part).

Earlier word count after resolution: 1,477 (Level 1 guide about 700–900; chapter 1's Level 1 page is about 1,800). Additions
over the first draft answer the two blocking findings and the healer scoping.

## Trial record

Draft snapshots: `context_engineering.first-draft.md`; reviewed draft saved after the re-review.
Model and owner interventions: owner reframe 2026-10-30 (problem, not skill, as the chapter's centre).
