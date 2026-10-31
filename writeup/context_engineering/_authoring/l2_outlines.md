# Context engineering: Level 2 outlines for approval

Status: proposed 2026-10-31; all four pages revised the same day on the owner's feedback, page 4 twice.
The Level 1's fourth section was applied on 2026-10-31 (appendix B is the record of the proposal). No drafting until every outline is refined (owner 2026-10-31). One owner stop per page,
here. Once a page's outline is approved, its drafting agent records "checkpoint: outline approved in
conversation 2026-10-31" in the brief, still writes the sample passage into the brief, and runs the rest
of the skill without a second stop. Topics come from `../content_plan.md` §4 (2026-10-29); this file adds
the presentation and reconciles each page with the Level 1 page as it stands after the owner's 2026-10-30
re-cut.

## Rulings (owner 2026-10-31)

- The defaults recommended under "Open questions" stand: page 1 features the board-and-reads bundle;
  page 2 lifts the "Previous days" block whole for now; page 3 keeps decision 7's audit to one sentence;
  page 4 labels the Alice/Bob table an illustration and states the 2026-10-30 live-mode result; one agent
  per page in parallel on the default model; the Level 3 waits for page 4's review; file names as proposed.
- Every term gets a clause of clarification on first use, without becoming a definition. "Board" is the
  example: never bare. The list under page 1 applies to every page.

## What changed since the content plan

- The Level 1 page is now organised by four kinds of failure (misreading facts, distorting earlier
  information, not using evidence in the action, missing an implication), with an opening section on
  what a player needs for its turn. The Level 2 titles still fit; the pages must build on what the Level
  1 sections now tell rather than restate them. What each section already tells is listed per page below.
- The Level 1 tells the field-order study (75% → 92.5%) and the compare-candidates reversal in its
  third section. Page 3 adds how the order was found and the Claude reorder; it does not retell them.
- The deduction report gained a note (2026-10-30; experiment log §8): in the live output mode the
  engine's line took the healer's read of player_7 from 2 to 8 of 10; at a high thinking setting the
  same model made the link alone 9 of 10; two larger models made it without the engine. That reframes
  page 4's result and needs a home (open question 5).
- The output-mode finding (the enforced schema left Haiku with no reported reasoning tokens in some samples; the schema sent as text, adopted 2026-10-14 for caching, restored them and lifted play on the replayed turn and votes) is chapter 6's story, told on its cache-layout page as a consequence of implementing caching (owner 2026-10-31). Pages 3 and 4 name the live mode where a result depends on it and link there.
- Evaluation's code-checks page already lists the hidden-roles swap as a row in its table and promises a
  link to "how the engine reaches its conclusions". Page 4 explains that test with the owner's Alice/Bob
  table, per the 2026-10-30 ruling; Evaluation keeps the row.

## Proposed files

| # | Page | File |
|---|---|---|
| 1 | Making facts available and unambiguous | `writeup/context_engineering/explicit_game_information/facts.md` |
| 2 | Carrying earlier days forward: the day summary and the claim ledger | `writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md` |
| 3 | Making assessments explicit and testing how they shape decisions (retitled 2026-10-31) | `writeup/context_engineering/structured_assessments/turn_request.md` |
| 4 | Working out selected conclusions in code: the deduction engine | `writeup/context_engineering/deduction_engine/deduction_engine.md` |
| 4a | Level 3: the roleblocked healer (after page 4 is reviewed) | `writeup/context_engineering/deduction_engine/roleblocked_healer.md` |

Word guide per page: 1,200–2,000 of page copy. Page 3 has the most material and a cut list below.

---

## Page 1. Making facts available and unambiguous

*Revised 2026-10-31 on the owner's feedback: organised as five successive questions, with "information
absent" kept apart from "information present but needing reconstruction". The earlier three-way split
(never printed / printed ambiguously / rule unstated) missed the second case, which is what the two
board lines were built for.*

**Page type.** Successive questions (closest example: B, `evidence_design.md`): each answer sets up the
next question, and the one planned comparison comes last, where it tests the page's premise.

**Reader's question.** When a model player gets a fact wrong, what was wrong with how the fact reached
it, and what form stops the error?

**Central answer.** Two problems look the same from the outside. Some information never reached the
prompt. Other information was there but had to be reconstructed from prose, or was worded so that it
could mean something else, or needed a rule the prompt never stated. Code now prints as data what a
player would otherwise work out, writes each result as the player's own act on a named night, and states
the rules in full and above any player's account of them. Printing the facts was not by itself enough:
the one planned comparison tested the printed facts together with a forced read of every player.

**What the Level 1 already tells.** The two board lines and role counts, night results worded as the
player's own act, rules that say what an ability observes, the Sentinel concession (10 of 10 → 0 of
10), and that a correct roles line had not stopped a survivor-count error. Page 1 gives the Sentinel one
sentence at most.

**Featured comparison (owner 2026-10-31): the board-and-reads bundle,** placed in §5 as the answer to
"did making the facts explicit suffice?". It tested §1's repair plus the reads, in July, before the
October repairs of §2–§4; those have their own replays, told in their sections.

**Section order.**

| § | Question | What the reader learns, and how | Carried by | Stays off or elsewhere |
|---|---|---|---|---|
| 0 | Opening | Absent information and information present but needing reconstruction fail the same way from the outside and need different repairs; the principle: code prints what a player would otherwise work out | Two short paragraphs | The ~3% rate beyond "about 3% of public messages in the earlier nine-player version" |
| 1 | What was the agent expected to reconstruct? | The living list and the transcript's death announcements held the facts, but who had died, as what, and which roles were still possible had to be worked out across days; survivor arithmetic (hunting "the remaining wolf" with no wolf alive) was the commonest census error; every call now carries two lines: the dead with the role revealed at death and when, and the roles still in play with a hidden-role body stated in words | A small before/after: one game-master announcement as it appears in the transcript, then the two lines ("player_8 (trailseer, night 1), player_9 (sigilist, lynched day 2)" and the roles-still-in-play line). **The "before" must be lifted from a recorded game or the golden fixture; if none is at hand, label it an illustration** | Whether printing sufficed (§5) |
| 2 | What information never reached the prompt? | A code review of the path from engine events to prompts found 12 places a fact was lost or blurred: the healer had no record of its own protections; a vote overwrote a private note it never showed; engine facts looked like a model's summary once rendered. The engine now writes each night actor's own record, one line a night, with quiet nights explained ("you chose not to act", "you had no checks left") | The night-record line; 8 addressed and 4 partly, "addressed" meaning the wiring, not that the model follows it; 97 → 82 of 267 as "an improvement in this sample, with substantial uncertainty" | The three labelled blocks (page 2); the vote-note fix beyond a clause |
| 3 | What could the wording mean? | A result line that read like a public death reveal ("Day 3: player_5 was revealed as healer"); every result now names the actor, the target and the night, with "(last night)" marked. The invented check as supporting evidence: what the investigator said against what its prompt said, rewording removed the invention in all 20 replays, the fix shipped in every game because it was a correctness bug | The quote pair; one sentence of result; link to Evaluation for how it was found and the variants tested | The four-variant table (Evaluation's featured story); "the wording, not the reasoning" |
| 4 | What mechanics needed spelling out? | By October invented facts were rare and the commonest error was a wrong inference about what an ability observes: which way a visit goes, what a watch or a follow cannot see, that an illusionist carrying its own kill leaves no trace. Games turned on rules the engine applied and the prompt never stated, and a player's wrong statement of a rule was repeated by others. The missing rules went into the rules block or the role card, with a line ranking the rules above any player's statement of one | The visit rule on 18 frozen turns (wrong-way readings 16 of 35 → 5); the illusionist case as the limit (10 of 10 → 7 of 10, 4 of 10 with the ranking line; later speakers repeated a false rule already in the transcript) | The Sentinel beyond one sentence; model names |
| 5 | Did making the facts explicit suffice? | Not on its own: in the first replay, of four confirmed errors three never recurred in any arm and the fourth recurred with a correct roles line in the prompt. So a one-line read of every living player, written before the action and shown back next turn, was added, and the pair was tested as a bundle: on 100 fresh error-prone turns, 48% bad on the old prompt against 30% (29 pairs better, 11 worse). Cost: about 60% more output per call. Limits: selected error-prone turns, one sample each, judged by the census's model reader; vote turns rebuilt with the vote's own result in view; the two changes never separated; the question was fixed before the second run. Why the reads sit before the action is page 3's | The comparison with its limits beside it; one sentence that it tested §1's lines plus the reads, not the later repairs | T2/T3 token counts, the coverage monitor (notes) |
| 6 | What is not established | No error rate on the ten-seat game; no test of today's prompt as a whole against an earlier one; players recite rule sentences as arguments | Two or three sentences | The opening-order sentence mismatch (chapter 1) |

**Terms to gloss on first use (owner 2026-10-31; applies to every page).** A clause, not a definition:
- never "board" bare: "the two board lines: who has died and as what, and which roles are still in play";
- "read": the one-line assessment of another player each turn asks for;
- "replay" / "frozen turn": a recorded turn rebuilt from the saved game and answered again by the model, several samples each;
- "census": the July count of errors over 50 games of the earlier nine-player version;
- "the bundle": the two board lines and the reads, tested together;
- "night record": the engine's line, one per night, of what the player itself did;
- "role card", "game master's record", "rules block": say what each holds the first time it appears.

**Bridges.** Chapter 1's evidence-design page links here for rules stated in full; Evaluation's
factual-errors page for how errors were found and counted; Evaluation's replays page once, at the first
replay; page 2 for the labelled blocks; page 3 for the reads' place in the answer.

**Handle with care.** The bundle's two changes are never separated; never "the wording, not the
reasoning"; no model family names in prose; 20 of 20 is one turn of one game; "addressed" is wiring.

---

## Page 2. Carrying earlier days forward: the day summary and the claim ledger

*Revised 2026-10-31 on the owner's feedback: establish the need before the mechanism, and give the
challenges as costs of the solution, not as the reason for it. The reader's objection ("why not pass the
plain transcript?") is answered by the need, not by a defence in the setup.*

**Page type.** Need → what was built → the risk the solution introduced → how it is guarded → checks →
limits (example B's successive questions, with example A's path-following for the mechanism).

**Reader's question.** Each turn is a new model call. How does what was said on an earlier day reach a
player later, and why not simply hand it the earlier transcript?

**Central answer.** Earlier days are condensed once because the discussions grow past what every call of
ten seats should repeat, and because the evidence the town acts on, who claimed what and whether the
record has borne it out, spans days and must be gathered per player and checked. Code can gather and
check from fields, not prose. So one model call per day transcribes two lists in fixed words and never
judges them; code folds the claims into a ledger, checks each against what the engine has made public,
and labels the three blocks a player reads by their author. Condensing created its own risk: a summary
line is every player's input. One mis-transcribed line decided a game, and the guard against it moved
into code.

**What the record gives as the need (so the page does not invent a failure).**
- The summary was there from the start (May): the need is size and repetition, not a recorded "buried
  fact" failure, and no comparison against the raw transcript has been run. Say so once, at the close.
- The ledger's need is real and recorded: claims are the evidence the town acts on (chapter 1 owns the
  numbers) and span days; the summariser was first asked to judge them itself (v3, 2026-10-03), and its
  verdicts were subjective, mostly "unverified", and lost between days. Code took over on 2026-10-04.
- The private strategy note is the other continuity: one clause here, with its honest rationale (an
  agent could not otherwise build on its own earlier thinking within a game); its cost is page 4's.

**What the Level 1 already tells (as of 2026-10-31).** Why a note and a summary are needed, in outline;
that fields let code build a ledger and check it against public facts; the principle that anything
carried forward can carry an error forward, with e06 in one sentence; and the guard at a glance
(recording apart from judging; the speaker's own fields; code says only what the record settles). It no
longer tells the incident, the self-block rule or any concrete check. Page 2 carries all three in full
and does not restate the principle at length. Sections 0–1 stay to about 150 words together.

**Featured story: one summary line that decided a game (e06)**, placed as the second of two cascade cases in §4.
What the investigator said, what the summary recorded (the two lines side by side), why the ledger passed
it on (no claim field filled, so the summary was the fallback, and nothing checked that a player cannot
block itself), the fix in two parts, and the caught fault: the first, broader rule also dropped a true
Vigilante claim and the replay caught it before it shipped. Limit: the invented claim did not recur in 10
replays before or after, so the code rule, pinned by a test, is the guard.

**Section order.**

| § | Question | What the reader learns, and how | Carried by | Stays off or elsewhere |
|---|---|---|---|---|
| 0 | What a new call lacks | Nothing carries over unless the prompt carries it: the agent's own thinking (the private note, one clause) and the earlier days | Two short paragraphs; the sample passage above | The note's stale-plan cost (page 4, Level 3) |
| 1 | Why earlier days cannot simply be replayed | Size and repetition in one clause (hundreds of lines by day four, in every call of ten seats); then the need that decides the design: claims decide the game and span days, so each player's claims must be gathered in one place and set against the record; code can do that from fields, not prose. This answers the objection as a reason | One sentence linking chapter 1 for why claims decide the talk | The 97% figure (chapter 1's); any "buried fact" claim |
| 2 | What was built: one call, two lists | At the end of each day, before the vote, one call writes accusations (speaker, target, reasoning, defence, who disputed) and role claims with night actions in fixed words from a fixed result list; plans kept apart because a plan is not something that happened; it never writes the vote or the night outcome, which the engine records exactly | A real rendered summary (day 2 of one game) | Older sections (alliances, dynamics); the May judge (Evaluation's judges page) |
| 3 | What a player reads: three blocks, three authors (exhibit) | The engine's exact record, the claim ledger built by code, the summariser's accusations, in trust order with their header lines; the ledger folds claims per player across days and checks each against public facts; where the record fits more than one reading it says nothing, and a claim the record cannot contradict stays a claim; rebuilt every prompt | The real "Previous days" block, lifted whole (owner 2026-10-31); two check lines, one that confirms and one that stays silent | The full check list; formatter names |
| 4 | How a carried-forward error cascades, and the guard each case produced (featured) | A summary line is every player's input the next morning. Two recorded cases, two guards. First: the narrative summary let a wolf's premise that town had rejected on day 3 return as fact on day 4 ("the conclusion was attributed; the premise was stated as fact"), so every statement became attributed to its speaker. Second, e06 in full as above: attribution was not enough when the summariser misread the speaker's own words, so the guard moved into code (the self-block rule), with the caught fault and the limit | The day-4 summary line from the first case; the two lines side by side from e06 | The "5 of 5 → 0 of 5" later-speaker figure (notes); the first case's bench result beyond one clause (36% → 31%, a direction) |
| 5 | Why judging left the model | The evidence for the rule, not a restatement: asked to judge claims itself (v3), the summariser's verdicts were subjective, mostly "unverified", and lost between days; its record check was judged wrong all 27 times it was written across 66 summaries, and was removed. So the speaker states its own claims in fields first and the summary is the fallback (a human player, an older game) | The 27 of 27 as design evidence, "judged wrong" by a model reading against transcript and record | The stronger-model comparison as a result (one sentence: 18 of 30 flawed in each arm, so it stayed on the game's model) |
| 6 | How it is checked, and how it runs | Known failures frozen as replay cases, five samples each, before and after (spoken denials 30 of 30 lost → 7 and 0 of 30; "I was roleblocked" misfiled 15 of 15 → 0 of 15); the bench comparisons ran on seats that did not reason, one sentence; runs on the game's own model with a rescue model and a raw-transcript fallback | A two-row before/after table | Rescue detail (chapter 7); tracing |
| 7 | What is not established | Never compared with giving players the raw transcript, and why the summary stays regardless (bounded prompts; the ledger and the deduction engine read its fields); plans, retractions and accusations rest on the summary alone; claims the record cannot check stay claims; the summary is not memory | Three or four sentences | Population error-rate numbers beyond "none for today's prompt" |

**Terms to gloss on first use.** "claim": a player's statement of its own role or night action, as
distinct from an accusation; "ledger": the per-player history of claims that code keeps and checks;
"game master's record": the engine's exact announcements; "record check"; "fields" / "fixed words";
"replay case".

**Bridges.** Chapter 1's content plan (the claim field and the shared-record fixes) and its
evidence-design page (why claims decide the talk) link here; Memory: within a game, never stored across
games; chapter 7 for the rescue model; Evaluation's judges page for the retired five-dimension judge.

**Handle with care.** Never "code checks every claim" without "against the public record"; the two e06
numbers kept apart; no recorded failure of the raw transcript, so no claim that the summary fixed one; the
bench ran on seats with no reasoning step; "judged wrong", not "wrong".

**For the Level 1 section (owner's question 2026-10-31).** The same order fits the Level 1 paragraph: the
sample passage above replaces its first two paragraphs; the objection and the "not shown better than full
transcripts" caveat move to the section's last sentence; the risk → e06 → separation → limit paragraphs
stay as written.

---

## Page 3. Making assessments explicit and testing how they shape decisions

*Retitled 2026-10-31 to "Making the reasoning explicit: a structured chain of thought" after the compare-candidates section was dropped by the owner; the outline below is the record as agreed before that.*

*Revised 2026-10-31 on the owner's proposal: organised around the purpose the Level 1 section now
gives it (make the assessments explicit enough to inspect, connect them to the action, and check whether
that connection helps), not as a tour of prompt choices tested by replay. The earlier title, "Testing
how each turn is asked: instructions, answer order and thinking effort", is retired; the Level 1 link and
the content plan's row follow. File: `writeup/context_engineering/structured_assessments/turn_request.md` (stem
unchanged).*

**Page type.** Design decisions tested by replays (example B), in the order the purpose unfolds: what the
record must reveal → getting it into the answer → putting it before the action → testing whether more of
it helps → cues the prompt supplied by accident → thinking effort as a separate lever.

**Reader's question.** How do you get an agent to state the assessments a decision needs, use them when
it acts, and leave enough evidence to investigate a failure?

**Central answer.** Instructions alone did not reliably produce the requested assessments. Required
fields gave each assessment a place in the answer, and the prompt's wording and the schema's order had to
agree about when to produce it. Those records make it possible to tell a misread clue from a misapplied
lesson from a decision that ignored its own assessment. But completing an assessment, or acting
consistently with it, did not establish better play, so each change was tested against the decisions it
produced, and some were dropped.

**What the Level 1 already tells (as of 2026-10-31).** The diagnostic motive; the two failures (an
instruction in a field's description was skipped until the verdict became a required field; with the
vote first, a quarter of notes never committed, and the May field moved before the action changed the
action); the four-field order; that the record is written assessment, not internal reasoning; the three
agreement figures (75%, 87.5%, 92.5%) and the adverse 40% → 26%. Page 3 recalls each in a clause and adds
the exhibit, the delivery and reorder detail, the tests, the accidental cues and the thinking level.

**The term.** The opening names the design once, where the Level 1 heading lands: an explicit, structured
chain of thought, written as fields the answer must fill, with one sentence that it is the agent's written
assessment and the model's hidden reasoning tokens are a separate chain (owner 2026-10-30). Section
headings describe what each section explains rather than naming the technique.

**Main test case (owner 2026-10-31): compare-candidates.** An instruction asking each read to compare
candidates elicited the decisive evidence more often where it was strong (the day-4 reads cited the
decisive vote 11 of 30 times against 2) and broke the ballot it was written for (the Vigilante's vote for
the real threat fell from 7 of 10 to 0 of 10, abstaining in 6), at 960 → 1,297 output tokens a vote. It
develops the Level 1's warning directly: a fuller assessment changed the assessment, and the decision still
had to be checked. The night-1 lot moves to §5 as a different failure class.

**Section order.**

| § | Section (working heading) | What the reader learns, and how | Carried by | Stays off or elsewhere |
|---|---|---|---|---|
| 0 | Opening | The purpose in the reader's terms; the term named once with its scope; replays of frozen turns as the method, with the swing-of-five limit stated here once | Two short paragraphs | The replay method (link Evaluation's replays page) |
| 1 | What the written assessment needs to reveal | The diagnostic need recalled from the Level 1 in a clause, then an annotated turn: the reads, the lesson verdicts, the note and the action, with what each field lets an investigator see (did it recognise the clue; how did it treat the lesson; what approach did it set against the action it took) | **Exhibit:** the roleblocked healer's turn, whose notes held every premise for three turns and never connected them: the record located the failure; page 4 owns the remedy. Lift a real rendered output from the frozen case (`evidence/gameplay/data/deduction_injection/` or the acceptance case); if none can be lifted, label the exhibit an annotated schema, not a demonstrated diagnosis | The engine's lines and the uptake result (page 4) |
| 2 | Getting the requested assessment into the answer | Three ways the requested work went missing and what made it appear: an instruction in a field's description was ignored until the verdict became a required field, and moving the instruction into the prompt body took coverage 0.27 → 0.97; every field is required and "no" is a value, so an absent field is never ambiguous; a field or instruction appears only when it applies (verdict fields and memory instructions only when lessons are shown, after 426 turns shown no lessons copied the example verdict; the per-turn brief says why the seat is asked, and a town seat on a voting day is asked to decide its vote now, passes 24 of 25 → 16 of 25) | The `TurnOutput` skeleton; the brief's sentence | The reply brief's "As I said" result (notes); the 1,200 characters |
| 3 | Putting assessment before action | The ordering decisions beyond the Level 1: the reads joined in July before the note and tripled how often a seat overrode a lesson's suggestion, while reading lazier with no earlier reads to update; the prompt's opening line and the schema disagreed about order, and in the text output mode the model kept the schema's order on 15 of 24 real turns, asking in words gave 13 of 23, and reordering the schema to match the prompt gave 24 of 24. Recall the Level 1's agreement-versus-correctness finding in one clause; keep compliance with the order distinct from better decisions; today's order is untested for message quality | Counts, not 1–5 scores | The three agreement figures and the 40% → 26% (told on Level 1; link back); the judge scores |
| 4 | Testing whether a fuller assessment helps (main case) | Compare-candidates as above, with its setup (11 frozen votes from one game, 10 samples each) and why it was not kept. Then short: tag each ballot with its outcome moved per-case results both ways; cite the record exactly left 24 misquotes before and after (a request to cite produces prose nothing checks). One sentence on what the prompt deliberately does not say: prescribed suspicion cues were removed because they built an answer into the prompt, kept on principle, not on the counts | The Vigilante ballot beside the 11 of 30 against 2; a short table for the other two | p-values; the per-player vote layout; the tactical-advice audit (notes, with a link to the evidence) |
| 5 | When the prompt supplies an accidental cue | A separate failure class: the choice followed the seat number or the example, not the evidence. Two observations, two changes: night-1 actions fell on the lowest seat (the investigator checked player_1 in 21 of 28 games) and shuffling the lists changed nothing (95 of 96 still the lowest-numbered seat), so the engine draws a lot on night 1 and offers it (actions then on all nine seats, 6 to 16 each); the example's named seat drew 40 accusation tags and 41 votes on day 2 against medians of about 8 and 12, so an example never names a legal answer | The lot sentence beside the seat-1 counts | The accusation-tag method; the Vigilante's exemption beyond a clause |
| 6 | Giving the model more thinking effort | A separate lever from written assessment, a call setting: 82 → 27 of 267 on one model at about 2.4 times the cost; on today's model votes right 98 of 160 against 65 while discussion did not improve (47 against 49 bad of 115), about $0.23 a game against $0.12, votes at the higher level an open decision. Close with what is untested about the current combination: today's order and the text output mode for message quality; the day-4 vote lead entangled with thinking level and layout (one sentence, link chapter 6); the same pattern in other calls in one sentence (the dedup judge's order and lean in Memory; narrow questions in Evaluation's judges) | One short table | "The model did no reasoning" (say "reported no reasoning tokens"); the output-mode story (chapter 6's cache-layout page); the layout's cost and participation (chapter 6) |

**Cut list if the draft runs long** (in this order): the reply brief's result; the two minor dropped
sentences to one line; §3's July reads detail to one sentence; the closing pointer to other calls.

**Terms to gloss on first use.** "read", "verdict", "strategy note" (the fields, by what each holds);
"required field"; "frozen turn" / "replay"; "the lot"; "thinking effort" (a call setting, counted in
reasoning tokens).

**Bridges.** Chapter 1's output contract links here for field order and required fields; Evaluation's
replays page once; page 4 for the healer's remedy and the thinking study; chapter 6 for the layout and
the output mode; Memory for the dedup judge.

**Handle with care.** "Chain of thought" named once with the claim scoped (the action follows the written
reasoning; not that reasoning improved; hidden reasoning tokens are a separate chain). Counts over 1–5
scores; the suspicion-cue drop (20% → 10%) is confounded with an easier board, so "kept on principle";
"one model" rather than names; the thinking study told once; the lot's rule stated as the rule it set,
not as a general law of models.

---

## Page 4. Working out selected conclusions in code: the deduction engine

*Revised 2026-10-31 on the owner's proposal: the mechanism before the experiments; one worked example
through the page; certainty kept apart from information access; the evil side explained once; the results
trimmed to the three screens, with the Level 3 taking the rest. Title unchanged. The Level 1's fourth
section was applied the same day, so this outline builds on it as applied.*

**Page type.** Architecture or mechanism (example A for following the path through the system), with a
short comparative passage for the replayed decisions.

**Reader's question.** How does the engine derive a conclusion from what a player is allowed to know,
decide how strongly to state it, and check that it deserves to be put in front of the player?

**Central answer.** It reads only the seat's permitted view, turns the game's mechanics into constraints,
and narrows what each player could still be until nothing changes. Every conclusion carries its grade in
its wording, because a line in the prompt is taken up almost every time and a wrong certainty would be a
false premise in every game where it fires. Two checks keep it in bounds: its output must not change when
only hidden facts change, and it states consequences, never whom to suspect or what to say. On three
replayed failures its lines changed what the first speaker did; whether that improves whole games is
unmeasured, and more thinking or a larger model made the healer's connection without it.

**What the Level 1 already tells (as applied 2026-10-31).** The healer's missed inference; constraint
propagation in a clause; the two boundaries in a sentence each; the three grades with the "Alice is the
Chanteuse" example; the live-mode healer result (2 → 8 of 10, spoke 7 of 10 against 3), the Sentinel's
report errors 6 → 2 of 40 with replies unchanged, the cover screen in a clause; whole-game effect
unmeasured; larger models or more thinking made the connection alone. No authorship sentence. Page 4
restates none of these at length: it supplies the mechanism, the grading rule's reasons, the two checks
and each screen's setup and limit.

**The one worked example: the roleblocked healer, carried through the page.** Its turn gives §2 the
path (blocked on night 1 → only the Chanteuse could block and a block is a visit → the Chanteuse came to
it; the trailseer's report and player_7's admission → either player_7 is the Chanteuse or two players
came), §3 the grades (the first line certain, the second a list of alternatives under a named claim), §4
what the engine does not add (no "suspect player_7"), and §5 the first row of the results. The three-row
A/B/C illustration appears once, in §2, labelled illustrative, because the healer's lines do not narrow
candidate roles and the reader needs to see propagation do that.

**Section order.**

| § | Section (working heading) | What the reader learns, and how | Carried by | Stays off or elsewhere |
|---|---|---|---|---|
| 1 | What the engine is responsible for | The failure class in two sentences (facts present, first inference missed) and the choice: compute selected consequences in code and leave judgement to the model. Why it was worth trying after prompt repairs, stated as cost, not necessity: the levers tried each helped somewhere and none resolved these failures within the live model's budget; more thinking or a larger model makes the connection alone at about 2.8 times the turn time or roughly twenty times the seat cost, and the engine buys most of that gap at the live setting's speed | Two paragraphs | The four-attempt table (notes, with the log linked); the ~3% rate (page 1) |
| 2 | From visible facts to a conclusion | The healer's turn followed through the engine: the seat's view built from its own payload (public events, its role and night results, pack facts if a wolf; never the hidden roles) → mechanics as constraints, with roles described by traits so a rule asks what a role *is* (blockable, night-immune, reads Suspicious) → the possible roles for each player narrowed by constraint propagation, shown on the three-row illustration (A and B must use up Healer and Sentinel, so C cannot hold either), with the four kinds of rule in one sentence each and why it stops → the rendered line beside the healer's own night record. Each conclusion keeps its premises, so a line can be traced to its rule and evidence | The healer's first line; the A/B/C table, labelled illustrative | The eight levels (one sentence and a link); the acceptance-case seat block (notes); runtime figures |
| 3 | How strongly can the conclusion be stated? | The three grades with their reasons: certain holds in every legal game compatible with the seat's information; conditional holds if named claims are true, produced by rerunning propagation with the claim assumed; alternatives list every branch without promoting one. Why a reported visitor cannot be named the blocker (a second visitor could have blocked; a true report does not prove the reporter's role). What happens when the inputs contradict (the solver returns no candidate result, never a forced answer). Why the grade sits in the wording: an injected line is taken up almost every time | The healer's two lines side by side; one conditional line | The grade table in full (evidence catalogue §0) |
| 4 | What the engine may know, and what it leaves to the player | First, information access: the question is not "was private information put in the wrong input?" but "did the advice use hidden information?"; the test in words before its name (change the hidden roles, hold the seat's visible information fixed, require identical deductions), the owner's Alice/Bob table labelled an illustration; what it shows and does not: a conclusion can respect the boundary and still be wrong, and correctness is a separate check (link Evaluation's code-checks page). Second, consequences against advice: the lines state what follows from the rules and the record, never whom to suspect or what to say; for a wolf or lone killer the lines list which roles it could claim without contradiction and which night stories fit, and the role card gives the advice; one cover line beside one card sentence; the counter-claimant line screened and dropped because it moved votes toward the named seat | The Alice/Bob table; one cover line | The rest of the suite (oracle, random nights, trait flips: Evaluation); "proved"; the cover screen's counts (§5) |
| 5 | What changed in replayed decisions | One compact table, three rows, each with comparison and limit beside the result: the healer's turn in the live output mode (read of player_7 as the Chanteuse 2 → 8 of 10, spoke 7 of 10 against 3; engine on against the original night record, not one line isolated; one turn, 10 samples a setting; an earlier replay of the same turn with the schema enforced (the log's §4) found the lines taken up and no speech, told on the Level 3); the Sentinel misreading its own watch (own report errors 6 → 2 of 40, replies 17 of 55 unchanged; 19 frozen turns, 5 samples; the frozen replies cannot measure how discussion would run after a corrected first message, so the downstream effect is unresolved); evil covers (claims 36 → 44, denials 4 → 0 on 41 pressured turns, two samples each; arms labelled by different judges, exploratory). Then the limits on where the engine adds value: Haiku at a high setting 9 of 10 alone at about 2.8 times the time; two larger models 9 and 10 of 10 alone; the bundled whole games (wolves 3 of 8 against 0 with revised cards, not attributable, link chapter 1) | The three-row table | The carried-note 2×2, placement screens, the vote case and the moderator line (Level 3); p-values |
| 6 | Scope and remaining questions | Supported coverage: the standard twelve roles and limits, outside which every seat gets nothing; coverage of missed deductions rests on four acceptance cases and one level never fired on 278 turns; no town-side whole-game comparison or post-engine error rate; the authorship sentence (the engine, solver included, written by an AI coding assistant to the owner's requirement, grading rule, acceptance cases and experiments; on this page only); links to Evaluation's code checks and to the Level 3 | Four or five sentences | Judge agreement, test authorship |

**Level 3 scope (grows with this revision).** "The roleblocked healer": the enforced-mode uptake result
and its date and mode; the carried-note 2×2 (9 of 20 against 3 of 20); the placement screens; the
investigator's vote case and the moderator closing line; the 2026-10-30 model and thinking comparison in
full with its subagent-harness caveat. Drafted after page 4 is reviewed.

**Terms to gloss on first use.** "the seat's view" (not `SeatView`); "constraint propagation" and
"metamorphic test" in words before the name; "acceptance case"; "frozen turn"; "output mode" (schema
enforced by the provider or sent as text; chapter 6 owns why it changed); "cover" (a false role claim an
evil seat can hold up).

**Bridges.** Chapter 2 for the permitted view; Evaluation's code-checks page for correctness ("Testing
whether deductions deserve certainty"); page 3 for the thinking study; chapter 1 for the covers and the
evil contest; chapter 6 for the output mode; the Level 3 beneath §5.

**Handle with care.** "Checked", never "proved"; never "all ten stayed silent" without the mode and the
date, and never as the current result; the boundary test shows independence from hidden information on
the cases tested, not correctness; the rationale is cost, never "prompts failed" or "the last resort";
the Sentinel replay leaves the downstream effect unresolved, not understated; the cover screen's arms were
labelled by different judges; the wolves' 3 of 8 cannot be split from the cards; authorship in one
sentence here, test authorship unmentioned; "a small model at a low setting" names the scope, not a
model family.

---

## Open questions for the owner

1. **Page 1's featured story.** The board-and-reads bundle (recommended: the one planned comparison, new
   to the portfolio, carries "printing alone was not enough") or the invented check as the content plan
   defaulted (already Evaluation's featured story with the same table)?
2. **Page 2's exhibit.** The real "Previous days" block runs about 20 lines. Lift it whole (recommended;
   it is the page's one exhibit) or cut to one line per block?
3. **Page 3's §3.** Keep decision 7's audit to one sentence (recommended) or drop it entirely? Its
   evidence is correlations and an untested rewrite.
4. **Page 4's §4.** The Alice/Bob table is the owner's illustration, not a specific test's state. Label
   it "illustration" on the page (recommended) or replace it with the real test's case?
5. **The 2026-10-30 live-mode result.** State it on page 4 (recommended: it scopes the engine's help to a
   small model at a low setting, which is the chapter's spine) and carry the table on the Level 3, or hold
   it for the Level 3 only?
6. **Drafting.** One agent per page, four in parallel, default model (claim calibration is where
   subagents slip); or Opus for pages 1 and 2, whose claims are the plainest? Start the Level 3 only after
   page 4 is reviewed.
7. **File names** as proposed above, or the content plan's longer titles as folder names?

---

## Appendix: proposed rewrite of the Level 1 section "Preserve earlier information without changing its meaning"

Proposed 2026-10-31 at the owner's request. Applied the same day: only the second half (the risk and the
guard), in a shorter form the owner chose, from "Anything carried forward can carry an error forward too"
to "stays a claim for the agent to weigh". The first half (need before mechanism) stays a proposal. About 360 words against the
current 343. Need first (note, size, claims that span days), then what was built, then the risk the
solution introduced, then the guard and its limit, with the one caveat last. Sources as in the page's
comment: `turn_prompt/experiment_log.md` §2 (the note's origin), `day_summary/report.md` §1–§4, §7–§8.

> Each turn is a new model call, so nothing carries over unless the prompt carries it. Two things need
> carrying. The agent's own earlier thinking returns as a private note it wrote last turn, so it can build
> on its plan instead of forming one afresh. The earlier days' discussion needs more than that.
>
> By day four those discussions run to hundreds of lines, repeated in every call of ten seats. Today's
> discussion is shown as spoken; earlier days cannot be. More important, claims are the evidence the town
> acts on: who said they were the Investigator, what they said they found, and whether anything announced
> since bears it out. Claims span days, so a player needs each player's claims gathered in one place and
> checked against the record. Code can do that from fields, not from prose.
>
> So at the end of each day, before the vote, one model call records the day as two lists in fixed words:
> who accused whom and why, and what each player claimed about its role and its nights. Code folds the
> claims into a **claim ledger**, one history per player, and checks each entry against what the game has
> announced: for example, whether a dead claimant's revealed role matches its claim.
>
> Condensing a day creates its own risk. A summary line is not one player's mistake; every player reads it
> the next morning. An Investigator said, "I was roleblocked last night." The summary recorded this as a
> claim to be the Chanteuse, the role that blocks other players. The next day agents repeated the invented
> claim, the Investigator accepted the false account of its own statement, and it was voted out 7 to 1.
>
> The design now keeps recording apart from checking. The summariser writes what was said, attributed to
> its speaker, and never judges it. Speaking agents state their own claims in fields, so the ledger reads
> the speaker first and the summary only when a speaker filled none. The ledger says only what the record
> settles: a claim it cannot contradict, such as a check on a living player, stays a claim, and the agent
> must still decide whether to trust it. It also drops an action that can only have been done to the
> speaker, the rule the incident was missing. This design has not been compared with giving players the
> full transcript; it is kept because it bounds the prompt and gives code fields to check.


## Appendix B: proposed rewrite of the Level 1 section "Compute selected implications"

Proposed 2026-10-31 at the owner's feedback (no authorship sentence; "all ten stayed silent" superseded
by the live-mode re-run; the two boundaries stated; the three replay screens in one sentence each). Applied
by the owner the same day. Sources: `deduction/report.md` §2–§3 and its 2026-10-30 note; `deduction/experiment_log.md` §8;
`gameplay/data/visit_wording_ab/README.md` arm C; `deduction/report.md` §5 (covers).

> Some agents had the relevant facts and still missed the connection between them. A healer's notes
> recorded that it had been roleblocked, that only the Chanteuse could block, and that another player had
> admitted visiting it, and never drew the conclusion. After input repairs and experiments with prompts and
> thinking effort, I chose to supply selected inferences in code: a **deduction engine** that starts from
> the seat's permitted information, narrows what each player could still be by constraint propagation,
> repeatedly eliminating possibilities the rules exclude, and writes its conclusions into the prompt.
>
> Two lines bound what it may say. It works only from what that seat is allowed to know, never the hidden
> roles; that is tested by changing the hidden roles while holding the seat's visible information fixed and
> requiring the same output. And it supplies consequences, not judgement: it states what follows from the
> rules and the record, never whom to suspect or what to say. Each line also carries its own grade. "The
> Chanteuse visited you" follows from the healer's own result; "Alice is the Chanteuse" does not follow from
> a report that Alice visited, because another visitor could have blocked. So a line is certain, conditional
> on a named claim, or a list of the alternatives.
>
> Replayed on the healer's turn in the game's live output mode, the engine's lines took its read of the
> visitor as the Chanteuse from 2 of 10 to 8 of 10, and it spoke in 7 of 10 against 3. On a second kind of
> failure, a Sentinel misreading its own watch, two lines cut its own report errors from 6 of 40 to 2 of 40,
> while replies to it, already arguing inside the recorded transcript, did not change. A third screen found
> that a wolf given facts for a cover claimed more and denied less. These are replays of chosen failures on
> one small model. Whether the lines improve whole games has not been measured, and a stronger model, or the
> same model at a higher thinking setting, made the healer's connection without them.
