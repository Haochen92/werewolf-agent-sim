# Carrying earlier days forward: the day summary and the claim ledger

*Level 2 · [Context engineering](../context_engineering.md) · separate revision for review, 2026-10-31*

## Page copy (draft)

Each turn is a new model call, so nothing carries over unless the prompt carries it. The agent's own
earlier thinking returns as the private note it wrote last turn; the earlier days' discussion needs more
than that.

### Why condense the discussion and structure its claims?

Today's discussion is shown as spoken. By day four, earlier discussions can run to hundreds of
lines, repeated in every player's calls. I chose to condense each earlier day to reduce that
repetition. Full transcripts remain an alternative; no comparison has established that summaries
produce better play.

The claim ledger serves a separate need. A **claim** is a player's statement about its own role or
night action. Claims span days: a check claimed on day 2 can be compared with a role revealed on
night 3. The ledger gathers each player's claims and checks them against public game facts.
Those code checks need fields identifying the claimant, action, target and result. Even if players
received full transcripts, the same checks would still require extracting those fields.

Speaking agents supply their own claim fields. A daily summary supplies a fallback and records the
accusations, plans and retractions. Later prompts combine these records with the engine's exact
announcements, keeping their sources distinct.

### One call, two lists

At the end of each day's discussion, before the vote, one model call writes two lists and nothing else.

- **Accusations.** One entry per distinct accusation: who made it, the target, the accusers' stated
  reasoning, the target's defence, and who else disputed it and why, at most 30 words a field.
- **Role claims.** Each role claim made that day, marked claimed or retracted, with the night actions the
  player says it took, in fixed words rather than prose: the action (investigate, protect, watch,
  block…), the night, the target, and a result from a fixed list (`suspicious`, `saved_from_attack`,
  `roleblocked`, `not_said`…). Each entry keeps the player's stated plans for the coming night apart from
  the actions it says it took, because a plan is not something that happened.

The fixed words are for code to read, as the next section shows. The summariser is told to leave out the
vote tally and the night's deaths, which the engine records exactly, to attribute everything it writes
to a named player, and never to state a player's claim as fact.

The ledger prefers a speaker's own role and night-action fields. It uses the summary's transcription
only when the player supplied no field of that kind that day, including for human players and older
games. Accusations, retractions and plans come from the summary alone.

In the example below, the Investigator's Suspicious result fits a wolf, including the Illusionist,
a wolf role that hides a victim's role. The Trailseer follows a player and learns whom they visited.

The record is stored with a plain-text rendering. This is day 2 of a real game, with the defences and
disputes shortened:

> Key accusations and defenses: player_5 → player_9: player_5 argued player_9 is a wolf because
> player_5's night-1 investigation of player_9 read Suspicious. […] Defense: player_9 said a single
> Suspicious read can't be verified […] Disputed: player_3 argued player_5's Suspicious read is only a
> claim until someone backs it up […] | player_3 → player_8: player_3 argued player_8 is worth watching
> because player_3's night-1 follow on player_7 showed player_7 went to player_8. […]
> Role claims: player_5 claimed investigator — Night 1: checked player_9, says they read Suspicious;
> player_3 claimed trailseer — Night 1: followed player_7

### What a player reads: three blocks, three authors

For a structured summary, the prompt does not show the stored rendering directly. Each prompt rebuilds a "Previous days" section in three
labelled blocks, in order of how far to trust them; the labels were added after a code review found
engine facts and a model's summary looking the same once rendered ([page 1](../explicit_game_information/facts.md) tells
that review). This is that section in a player's prompt on day 3 of the same game, built in part from
the summary above:

```text
== Previous days ==
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_1 was attacked by the wolves and the serial killer last night. Their role is hidden by an illusionist.
[Day 2] Here's the vote result for day 2:
  player_2 voted to eliminate player_9
  ... (one line per voter)
Player player_9 has been voted out and was a illusionist.
[Day 2] Night of day 2: player_3 was attacked by the wolves and the serial killer last night. They were a trailseer. ...

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed investigator (day 2).
  Night 1: checked player_9, says they read Suspicious. Record: player_9 was revealed as illusionist, as claimed.
player_3: claimed trailseer (day 2). Record: revealed as trailseer when they died on night 2, as claimed.
  Night 1: followed player_7; says they visited player_8 (a visit alone does not establish what they did there).

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_5 → player_9 (revealed illusionist, voted out day 2): player_5 argued player_9 is a wolf because ...
[Day 2] player_3 (revealed trailseer, killed night 2) → player_8: player_3 argued player_8 is worth watching because ...
```

When player_9 died as an Illusionist, player_5's Suspicious read was borne out, and the ledger says so;
player_3's line carries the visit its follow saw, with the ledger's own note on what a visit does not
establish.

The blocks have different responsibilities:

1. **The game master's record** comes from the engine: night outcomes, votes and revealed roles.
   The summariser does not rewrite these facts.
2. **The claim ledger** combines claims into a history per player and checks them against public
   facts. It adds a “Record:” or “Rules:” line only when an announcement or rule settles a check.
   A claim about a living player's role can remain unverified. If a shot player survived, for example,
   that might reflect protection or the Serial Killer's night immunity; survival alone does not settle
   a claimed save. The ledger is rebuilt every prompt, so a new reveal updates the checks.
3. **The accusations** remain the summariser's account of what players argued, labelled as such.

### How a carried-forward error cascades, and the guard each case produced

A summary line is not one player's mistake. Every player reads it the next morning, and a player that
rejected a claim while reading the discussion may accept the same claim from the summary. Two recorded
cases each produced a guard.

**A premise returned as narration.** In a nine-seat game in early October, a wolf argued on day 3 from
something only the wolves knew: their attack on the Serial Killer, a lone killer immune to night attacks, had failed.
The engine does not publicly announce that failed attack. Villagers called the
argument fabricated and the wolf was voted out. The summary of that day read:

> "Player_2 has survived night attacks and remained unharmed without claiming a healer, which these
> players argue points to serial killer night immunity."

The conclusion is attributed; the premise is stated as fact. Three town players treated the survived
attacks as fact on day 4 after rejecting the claim in the previous day's discussion, making the summary
a likely route. The summariser was changed to attribute every statement, including the premise of an
accusation, to a speaker. Its narrative section was subsequently removed in favour of the two lists.

**A speaker's own words misread.** Attribution was not enough when the summariser misread what a speaker
had said about itself. In a ten-seat game from early October, the Investigator said on day 2:

| What the Investigator said | What the summary recorded |
|---|---|
| "I was roleblocked last night, which confirms we have an active Chanteuse in play." | "player_2 claimed chanteuse — Night 1: blocked player_2" |

The Chanteuse is the wolf that blocks a player's night action. Something done *to* the Investigator
became a claim *by* it. On day 3 a town player opened on that claim. The Investigator then accepted the
false account of its own statement, saying it had claimed Chanteuse "to draw fire", against its own
private note, and was voted out 7 to 1, though its own check had correctly found the Chanteuse
Suspicious. The game's lone killer, a third side, won.

The Investigator had left its claim field empty, so the ledger used the summary's transcription.
Nothing checked that a player cannot block itself. The repair addressed both stages: the summariser
was told that “I was roleblocked” claims no role, and the ledger rejects a claimed self-block and the
Chanteuse claim resting on it.

The code rule needed a narrow scope. Its first version removed a claimed role whenever all recorded
actions targeted the speaker. That also removed a true Vigilante claim after “held my fire” was
misrecorded as shooting itself. Replaying days containing true claims caught the mistake before the
rule shipped, and the rule was narrowed.

The summary replay did not establish that the new instruction prevents the invention: it never
recurred in the five samples before or the five after. The code rule is the guard for this particular
false record, with a unit test checking its behaviour. Speakers' fields were also extended to include
their claimed night actions, reducing reliance on summary transcription.

### Why judging left the model

The summariser now records claims without judging their truth. Earlier versions asked it to compare
claims and accusations with the game record, but its verdicts were often unverified or subjective.
Checks that the public record can settle moved to code.

The remaining model-written record checks were tested on six days from two games. Each day was
summarised five times by the game's model and five by a stronger model. The stronger model judged
those 60 summaries and the six originals against the discussion and game record. Across the 66
summaries, 27 record checks were written and all 27 were judged wrong. That checking task was removed
from the summariser.

The comparison also found misleading errors in 18 of 30 summaries from each model, so it provided no
reason to switch to the stronger summariser. These are model judgements of an earlier prompt, which
still requested record checks, not an error rate for today's summary.

### How it is checked, and how it runs

The summary failures found in the ten-seat games (the self-block, a record-check line copied from the
prompt's own example, dropped denials, misfiled roleblocks) were frozen as **replay cases**: the summariser gets exactly the input it
had in the game, five samples a case, and the check reads the structured fields and the ledger built from
them, not prose. Each fix was replayed before and after. Two examples:

| Known failure | Before the fix | After the fix |
|---|---|---|
| A spoken denial ("I didn't visit anyone last night") had no field to go in and was lost | 30 of 30 samples lost (six days, five samples each) | 7 of 30 on one summariser model and 0 of 30 on another, once a "did not act" action existed |
| "I was roleblocked" filed as a denial (a different misfiling from the Chanteuse case: the attempt dropped, not a role invented) | 15 of 15 on one summariser model, 6 of 15 on another | 0 of 15 on both, once the summariser was told a roleblock is an attempt |

These are regression checks on known failures, not error rates; the same replays checked that true
claims were still kept, and the denial fix may have cost a few, which five samples cannot settle. The
ledger's rules and the "Previous days" rendering are pinned by unit tests.

In a game the summary runs on the model the seats play on. A call that stalls or fails goes to a rescue
model where the game has a second one assigned, and otherwise the day is stored as the raw transcript
and shown as written (the production chapter has that path).

### What is not established

The comparison with full earlier transcripts remains open. Condensation reduces the discussion
carried into later calls, and structured claims support code checks; neither establishes that players
make better decisions with the resulting record.

Plans, retractions and accusations still depend on the summary alone. Claims the public record cannot
settle remain for the player to weigh. There is no overall error rate for the current summary prompt:
the results here concern selected failures and small samples. The older quality judge assessed sections
the summary no longer writes ([Evaluation's judges page](../../evaluation/llm_judges/llm_judges.md)).

These records preserve continuity within one game. Lessons carried between games belong to the
[Memory chapter](../../memory/memory.md).

**Evidence.**

- [The day summary: how a past day reaches later prompts](../../../evidence/extraction/day_summary/report.md)
  (the current design, the checks, the misread-roleblock game) and its [build journey](../../../evidence/extraction/day_summary/experiment_log.md).
- [Discussion evidence](../../../evidence/gameplay/discussion_evidence.md), §6.4–6.6 (the premise returned
  as narration, the attributed summary, transcription and the ledger) and §8.4 (the ten-seat audit and the
  replays).
- [The turn prompt](../../../evidence/gameplay/turn_prompt/report.md), decisions 3 (the labelled blocks)
  and 13 (claims as fields).

<!-- Sources for the page copy (checked 2026-10-31):
Opening: the private note as continuity: turn_prompt/experiment_log.md §2 (updated_strategy "fed back next
turn"); the parent page tells it too. Hundreds of lines by day four, every call: day_summary/report.md §1.
Why not the transcript: day_summary/report.md §1 (size) and §8 first bullet (fields are what code reads);
the claims-span-days need is the chapter's content plan §2 section 2 and the l2 outline; no recorded
"plain transcript failed" incident exists and none is claimed. Chapter 1's evidence-design page owns why
claims carry the talk (its numbers stay off here).
Two lists, 30 words a field, fixed result words, plans apart, never the vote or the night outcome,
attribution, "never a claim as fact": day_summary/report.md §2; experiment_log.md ③ 2026-10-04 "a plan is not
an action". The rendered summary is game 2f19d908 day 2 (Claude Haiku 5.5 in every seat), report §2; the
defences and disputes are shortened with "[…]" (both accusations kept after the round-2 editorial review, so
the ledger's player_8 line can be traced); "(evidence type: concrete_claim)" is in the stored rendering, is
not shown to seats (report §3, "older summary sections ... not shown"), and is elided as "[…]" on the page.
The role gloss after the block: wolves read Suspicious to the Investigator; the Illusionist is a wolf role
that hides a victim's role; the Trailseer follows a player and learns whom they visited:
evidence/gameplay/roles/role_sheet.md (shared rules; the role table).
The "Previous days" block: report §3, lifted whole (owner's ruling 2026-10-31); game 2f19d908 day 3, from
evidence/gameplay/deduction/data/deduction_placement_n10/prompts/AC2_before_note.txt. The three authors, the
check list (the page gives three of the four kinds; the fourth, more living claimants than the cast holds,
is in report §3 item 2), the silent case (a shot player who lived), rebuilt every prompt: report §3 items
1–3; discussion_evidence.md §6.6 (the ledger's checks). The headers' origin in the 2026-10-03 code review:
turn_prompt/report.md decision 3; map block 143.
Case 1: game 46355b89, nine-seat, Gemini 3.5 Flash-Lite, memory off, 2026-10-03; the day-4 summary line
quoted verbatim; "the conclusion is attributed; the premise is stated as fact"; three town players treated
it as fact: discussion_evidence.md §6.4; experiment_log.md ③ 2026-10-03. Attribution = summary v3
(2026-10-03); "village dynamics" dropped with v4 the next day (2026-10-04): experiment_log.md ③, §6.6.
Bench (OFF THE PAGE after the claims review 2026-10-31): hallucination_bench_v2, 89 frozen moments, 3
samples each, 267 samples; the "before" arm is the fidelity-baseline code and the "after, re-summarised"
arm is the whole 2026-10-03 fidelity pass (rules on silent night events, each night actor's record, the
labelled blocks, "voted to eliminate", the vote turn shown its note) plus the v3 summary: 97/267 (36%) →
82/267 (31%), 24 better / 14 worse, p = 0.14; the arm that isolates the re-summarised days is "after" 86/267
(32%) against 82/267 (31%). So the number belongs to the pass (page 1 and decision 3 credit it there), not
to attribution alone, and the page now says the summary's share was not isolated: §6.5; report §6. The
second likely cause of item 3 (the rules never said a failed attack on the serial killer is silent; fixed
as R-a) is §6.4 "Likely causes". v4 against v3 made no difference (31% against 32%, 11/11) and cut stored
summaries 55%: §6.6. Both bench arms ran with seats at a setting that reported no reasoning tokens
(§6.7); with no bench number on the page the caveat is in these notes only.
Case 2: game e06, ten-seat, Gemini 3.5 Flash-Lite seats, read 2026-10-10: report §7; discussion_evidence.md
§8.4; experiment_log.md ③ 2026-10-10. The two lines verbatim; the sigilist opened day 3 on it; the
investigator's "I claimed chanteuse yesterday to draw fire away from town PRs" (quoted in part on the page);
7 to 1; its own check had the Chanteuse Suspicious; the Necromancer (a lone killer) won. Why it got through
(no claim field filled → summary fallback; nothing checked a self-block): report §7. The fix, commit
6248fc58: the instruction (roleblocked / protected / visited claim no role) and the ledger rule (drop an
action that can only have been done to the speaker; drop the role only for a Chanteuse on a self-block):
report §7; Agents/rules/claim_ledger.py (_DONE_TO_ONESELF and the comment at the chanteuse branch). The
first broader rule and the lost Vigilante ("held my fire" written as shooting itself, e02 day 3), caught by
the replay before it shipped: gameplay/data/phase3_summary_replay/README.md "Reading"; §8.4. Limit: the
invented claim did not recur "in 10 samples on either arm" (README) / "in 10 replayed samples, before or
after the fix" (report §7); at five samples a case that is read as five before and five after, as the
round-1 claims reviewer also read it; the ledger rule and a test guard it. The serial killer gloss (lone
killer, night-immune, failed attack never announced): role_sheet.md; discussion_evidence.md §6.4. "The
same players had rejected it on day 3": §6.4 item 3. KEPT APART AND OFF THE PAGE: "5 of 5 → 0 of 5" is the later e06 speakers' repeat of the claim in
the turn replay with the fixed ledger (discussion_evidence.md §8.4 "The replays"), not the summary itself.
Judging left the model: v3's record_check and per-claim verdicts (supported / contradicted / unverified);
nearly all "unverified"; the compact claim record dropped the field; the owner ruled "supported" subjective;
code took over 2026-10-04: experiment_log.md ③ 2026-10-04; §6.6. The record check on accusations stayed
until 2026-10-16. The stronger-summariser test: 2 Haiku games, 6 days with speech, 5 summaries per model
per day (60) plus the 6 the games used = 66 judged; both models 18 of 30 flawed; 27 record checks written,
all 27 judged wrong (20 Haiku, 6 Sonnet, 1 live), none a real conflict; removed commit d4f14fa7:
deduction/experiment_log.md §3; report §6. The judge (Sonnet 5.5) was one of the two models compared; the
log's 2026-10-24 note says the equal 18 of 30 and the record-check finding hold, the error-kind split is
what it weakens; the page uses only the former two and says the judge was the stronger model. "Flawed" is
defined on the page by the log's error list (misattributed, invented, missed, dropped rebuttal, claim as
fact, wrong record_check). "Judged wrong", never "wrong".
Speaker's own fields: the role claim field from the ten-seat game (2026-10-09); claimed night actions
2026-10-18 (commit c957fdb5); turn_prompt/report.md decision 13 dates the pair 2026-10-17. Ledger reads the
speaker first, summary for a player with no field (human, older game); summary the only source of
accusations, retractions, plans: report §4, §8; decision 13 (a human seat has no fields).
Replay cases: frozen inputs, five samples a case, scored on fields and the ledger; the cases came from five
games read by hand plus a scan of 31 games for two patterns (a self-targeted action, the copied record
check), with denial and roleblock cases added later, so "the failures found", not "each failure":
phase3_summary_replay/README.md; report §6; §8.4. Side cost: after the denial fix Flash-Lite lost 2 of 20
true claims on control cases where it had lost 0 (README: possibly a cost of the longer instructions, not
established). Denials
30 of 30 lost → Gemini 3.5 Flash-Lite 7 of 30, Gemini 3.5 Flash 0 of 30 (no_action added, commit
0c605e89); "I was roleblocked" filed as a denial by GPT-6 Luna 15 of 15 → 0 of 15 and Flash-Lite 6 of 15 →
0 of 15: report §6; §8.4; experiment_log.md ③ 2026-10-10. Model names kept here, off the prose. The lost
Vigilante (e02 day 3) was a control case, a day where a true claim must be kept: README table. The
record check was narrowed on 2026-10-04 (false "never announced" flags, §6.6) and its copied example
removed on 2026-10-10 (6248fc58) before its removal on 2026-10-16: "patched twice".
Unit tests: tests/engine/test_claim_ledger.py, tests/engine/test_information_fidelity.py (passed at c0732f88),
tests/engine/test_model_fallback.py: report §6. Bench seats reported no reasoning tokens; reasoning on cut
31% → 10%: report §6; §6.7 ("reported no reasoning tokens", never "did no reasoning").
Runtime: the game's own model; medium thinking unless the catalogue sets another level; structured output
with the schema enforced on retry; 90-second wait; rescue model; raw transcript last; each summary saved as
an evaluation case (tracing, off the page): report §5. The rescue path (2026-10-21) is the production
chapter's; its Level 1 file does not exist yet, so no link.
Not established: never compared with the raw transcript, and why it stays (bounded prompts; the ledger,
the accusations block and the deduction engine's claim view read its fields): report §8 first bullet. Plans,
retractions, accusations on the summary alone; claims the record cannot check; no population error rate; the
May five-dimension judge scores sections no longer written: report §8; experiment_log.md ④. Not memory:
content plan §6 (within a game, never stored across games).
Kept off the page (handle-with-care and the outline's "stays off" column): the note's stale-plan cost; the
97% figure; the full check list and formatter names; the rescue detail and tracing; population-rate numbers;
model family names in prose; "code checks every claim" without "against the public record". -->

<!-- Supporting material relocated during the 2026-10-31 revision.
The following superseded passages are retained as authoring history, not current claims.

### Why earlier days cannot simply be replayed

Today's discussion is shown to every player as it was spoken. Earlier days cannot be: by day four they
run to hundreds of lines, repeated in every call of ten seats. Size decides that earlier days are
condensed; it does not decide the form. The evidence the town can test is **claims**, a player's
statements about its own role and its nights, as distinct from its accusations of others (the game is
designed to make them testable: [chapter 1's evidence-design
page](../../game_design_orchestration/evidence_design/evidence_design.md)). Claims span days: a claim
made on day 2 is tested by a role revealed on night 3. So a player needs each player's claims gathered in
one place and set against what the game has announced since, and code can gather claims and check them
against the record only if they arrive as fields, not prose. That is why claims reach the ledger as
fields: stated by the speaker in its own answer where it makes one, and otherwise transcribed by one
model call at the end of each day, which also records the day's accusations. Code builds the rest.



Role claims also have a second, better source. A speaking player states the role it claims in a field of
its own answer (since the ten-seat game began in early October) and, since mid-October, the night actions
it says it took, in the same fixed words ([page 3](../structured_assessments/turn_request.md) explains the answer's
fields). The summary's transcription is the fallback for any player that filled no field of that kind
that day: a model player that made no claim, a human player, whose typed line has no fields, or a game
recorded before the fields existed. Accusations, retractions and plans come from the summary alone.

The examples below use four roles. The Investigator checks a player at night (twice a game) and learns
whether they read Suspicious, which the wolves do. The Illusionist is a wolf that hides a victim's role. The Trailseer
follows a player and learns whom they visited. The serial killer is a lone killer playing against both
sides; it survives night attacks, and the game never announces a failed attack on it.



The three blocks have three authors.

1. **The game master's record** is written by the engine, not by a model: each night's outcome, each
   vote ballot by ballot, and each role revealed at death. The summariser has no hand in these facts, so
   a summary error cannot lose or alter them.
2. **The claim ledger** is built by code. It takes each player's role claims and claimed night actions
   from the speaker's own fields first and from the summary's transcription only where the speaker gave
   no field of that kind, folds them into one history per player, then checks each entry against what the engine has made
   public: a dead claimant's revealed role, an investigation result against the target's revealed role, a
   claimed save against the announced saves. A check, marked "Record:" (or "Rules:" when a rule rather
   than an announcement decides it), states a fact and nothing more. Where the record fits more than one
   reading it says nothing (a shot player who lived may have been saved, or may be the serial killer,
   whose survival is never announced), and a claim the record cannot contradict, such as a check on a
   living player, stays a claim. The ledger is never stored: every prompt rebuilds it, so a role revealed
   overnight appears in the next morning's checks.
3. **The accusations** come straight from the summary's list, each player tagged with the role revealed
   if it has died. A model wrote them, and the block's header says so.



The conclusion is attributed; the premise is stated as fact. On day 4 three town players, shown only
this summary of day 3, treated the survived attacks as fact; they had rejected the same claim the day
before, while reading the discussion, so the summary is the likely route. The guard was attribution: I
changed the summariser to write every statement as something a named player said, including the premise
an accusation rests on. That rewrite kept the summary's prose sections; the one that retold the day as a
story, where the premise had entered as narration, went in a second rewrite the next day, which left the
two lists above.



The line got through because the Investigator's answer had a claim field and it left the field empty,
describing its night in speech only, so for that player the ledger fell back on the summary's
transcription, and nothing checked that a player cannot block itself. The fix has two parts. The
summariser is told that something done to a player is not that player's claim: "I was roleblocked", "I was protected" and "someone visited me" claim no role. And the
ledger drops a claimed action that can only have been done to the speaker (a block, a watch, a check on
oneself), dropping the claimed role with it only for the one case seen here, a Chanteuse claim resting on
a self-block. A first, broader version of that rule dropped the role whenever every claimed action was
on the speaker, and lost a true Vigilante whose "held my fire" the summariser had written as shooting
itself. Re-running the summariser on frozen days, including days where a true claim has to survive (the
**summary replay** described below), caught it before it shipped, and the rule was narrowed.

The code rule is the guard, not the instruction. In re-runs of that day's summary, five before the fix
and five after, the invented claim never recurred: it is rare, so the replay cannot show that the instruction
prevents it. The ledger rule catches it whenever the summary records the claim as a block on the
speaker, whatever was said in the day, and a unit test pins the rule. The same line is also why a
speaker's fields were extended from its role to its claimed night actions.



The rule behind the design, that the summariser records what was said and never judges whether it is
true, came from trying the alternative. The attribution rewrite of early October did more than
attribute: it gave the summariser the game master's record and asked it to check each accusation against
the record and to give each role claim a verdict, supported, contradicted or unverified. Nearly every
verdict was "unverified", and "supported" was a subjective call. In the second rewrite a day later the
verdicts went, and the claim ledger took over checking claims against the record in code. One piece of
judging stayed: the check each accusation got against the record.

That check, patched twice after wrong flags, went after a later test. Six days from two games were each
re-summarised five times by the game's model and five times by a stronger one, and the stronger model
then judged those 60 summaries, and the 6 the games had used, against the transcript and the record.
Across all 66 the record check was written 27 times, and all 27 were judged wrong; none reported a real
conflict. It was removed, and with it the last piece of judging the summariser did.

The same test had been run to decide whether a stronger model should write the summaries, and it said
no: each model had an error that would mislead a later reader (a claim misattributed, invented or missed,
a rebuttal dropped, a claim written as fact, a wrong record check) in 18 of its 30 summaries, judged by the
stronger model itself, which if anything favoured it. So the summary stayed on the game's model. Those
18 of 30 measure the mid-October prompt, which still asked for the record check and whose counted errors
include it; they are not a rate for today's prompt, which has none (the close says what is measured
today).



The summary has never been compared with giving players the full earlier transcripts, so whether they
lose anything by reading a record of a day instead of the day is unknown. The summary is kept for the
two reasons the page opened with: it bounds the prompt as a game runs on, and its fields are what code
reads, in the ledger, the accusations block and the [deduction
engine](../deduction_engine/deduction_engine.md), which builds each player's view of the claims from the
ledger. The missing comparison bears on the first reason, not the second.

Three gaps follow from the design. Plans, retractions and accusations rest on the summary alone, with no
speaker field to cross-check them, so a slip in any of them reaches every player. A claim the record
cannot contradict stays a claim for the player to weigh. And there is no error rate for today's prompt on
today's model: the counts above are replayed cases and small samples, and the quality judge built in May
scores sections the summary no longer writes ([Evaluation's judges
page](../../evaluation/llm_judges/llm_judges.md) tells that story).

The summary is continuity within a game, not memory: it is written for each day of one game and never
carried into another. Lessons carried between games are the [Memory chapter](../../memory/memory.md)'s.


-->
