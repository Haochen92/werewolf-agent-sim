# Orchestrating the conversation

*Level 2 · [Game design and orchestration](../game_design_orchestration.md) · previous: [Designing evidence worth debating](../evidence_design/evidence_design.md) · next: [Multi-Agent Game Orchestration](../day_and_night/day_and_night.md) · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Original drafting brief

This brief records the earlier outline. The 2026-10-27 editorial revision and verification questions
are recorded in [the editorial notes](../editorial_notes.md).

Copied from [`../content_plan.md`](../content_plan.md), "Level 2 page briefs", section 2 (condensed); the
plan keeps its copy until the owner moves it.

**Reader question:** when every player is a model call, how does the engine decide who speaks, what gets
published and when the day ends, without the machinery itself becoming evidence the players argue
about?

**Promise:** openings, replies, speaking opportunities, publication filters and closing defences.
Silence is the featured investigation; the voices are a short final subsection.

**Featured story:** silence had three sources, and the largest was invisible (block 126): 367 of 517
passes came from a judge's hold; three passes in a row ended day 1 in 28 of 28 games; on 8 of 96 voting
days a player was never offered a turn. Separating "never offered", "held" and "chose to pass"
redirected the October rebuild, ending in the calibration that made speech the default and moved the
filter after the line (128).

**Subsections:** (1) what a good day needs, and what code decides, the day's flow, about 30 calls a
voting day (117); (2) talk in sequence, vote at once, the five openers, the acceptance study's scope
(118); (3) turn order is computed, not chosen: debts, freshness, the pair cap, sweeps, the stateless
scheduler, the tags, the player_7 / player_9 exchange, the tag numbers with their scopes (119, 120);
(4) silence had three sources (126); (5) the opening round and the investigator-lynch chain (122, 127);
(6) speak by default, filter after the line: the calibration, the volume-knob table, the shipped gate,
why a separate judge, what a held line leaves behind, the readers' scope, the possible Level 3 link
(128, 121, 123); (7) a last word for the most-accused, its effect on votes unmeasured (124); (8) how
players sound (125); (9) how it is checked, and what is not established (129, 130).

**Cross-links:** page 3 (parallel and sequential steps as execution); chapter 2 (what each speaker may
see); chapter 3 (the vote-reason and reply briefs, block 145; the night-1 lot, block 146); Evaluation
(the readers' calibration, hardening task 1b).

**Level 3 (possible, owner to decide):** "Silence calibration: a volume knob, not a filter", beneath
subsection 6.

**Tags:** multi-agent orchestration, dialogue management, event-driven scheduling, output guardrails,
LLM-as-a-judge.

This page's exhibit rows are proposed in the drafting notes, for the owner to merge into
[`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Not independently verified. -->

## Page copy (draft)

In a human game, players follow the discussion continuously and speak when they have something to
add. A model sees the conversation only when it is called. The engine must therefore decide when to
invite each player, while leaving the player to decide what to say.

That creates three separate decisions: who gets a turn, whether their line reaches the table, and
when the discussion ends. They affect what the players infer about one another. A player the engine
never calls can look like someone choosing to stay quiet; a publication filter can hide a defence.
The rules need to provide opportunities to share evidence and answer accusations while keeping the
day short enough to reach a vote.

```
Day 1      opening round → day summary → night
Day 2 on   opening round → discussion → closing defence → day summary → vote
```

Openings and closing defences are collected in parallel. Discussion runs one speaker at a time, so
each player can respond to the latest line. Votes use the same completed transcript and are revealed
together, preventing a voter from adapting to a visible tally.

### Why discussion runs in sequence

The first design asked every player to speak from the same snapshot and revealed their answers
together. In one game, five of eight players opened with versions of “Does anyone have any initial
thoughts?” Sequential turns let later speakers hear those contributions and respond to them.

That makes a response possible without guaranteeing one. It also makes the day slower and gives
later speakers more information. A small June acceptance study compared four sequential games with
eight concurrent games already on disk, on Gemini 3.1 Flash-Lite. The games were unpaired and the
reader had built the design, so the study illustrated differences rather than isolating an effect.
The [execution page](../day_and_night/day_and_night.md) explains how the graph runs sequential
conversation alongside parallel votes and opening rounds.

### Giving everyone an opening

Every living player is invited to an opening round at the start of the day. This gives someone
holding private evidence a chance to share it without singling out an investigative role.

An opening may contain a role claim or counterclaim, the speaker's own night result if the morning
has not already published it, or a reasoned challenge to an earlier claim. Passing is normal here: a
player may have nothing to disclose or may choose to keep a result private. The openings are
generated together because a mostly silent round would otherwise require waiting for each player in
sequence. Restricting the kinds of opening also reduces the generic statements produced when players
all answer the same snapshot.

### Choosing the next speaker

After the openings, the scheduler picks speakers from the day's transcript. It gives priority to a
player who owes an answer. When nobody owes one, it offers the open floor. An earlier weighted score
mixed pressure, novelty and talk time, making a reply compete with unrelated priorities; the two
explicit routes make that obligation easier to enforce and test. Because the order comes from these
rules, the game rules tell every player that the order of speech is the moderator's doing and says
nothing about a role.

**Debts come from the speaker's own tags.** Each line carries tags written in the same structured
answer, so they cost no extra call: for each player addressed, a form (question, response or
mention) and a stance (accusation, defence, agreement or neutral), since most lines here are a
question and an accusation at once. A question or accusation opens a debt. Whoever owes speaks
first, the newest debt first, and a player owing three accusers answers all three in one turn. Any
later line by the debtor that engages the speaker clears the debt, whatever its form tag says,
because models mislabel the form: in June, a reply tagged as a mention never cleared, and the same
player was picked seven times in a row.

A real exchange from an October test game (nine-seat, Flash-Lite, day 2), with the tags each speaker
wrote:

```
player_7 (open floor)            → player_9: question, accusation
  "Checking someone who died on night one is awfully convenient since it can't be cross-checked.
   Player_9, if you're the real investigator, who are you looking at tonight?"
player_9 (reply, owes player_7)  → player_7: response, defence
  "Player_7, I didn't plan for player_1 to get hit by both the wolves and the serial killer on
   night one. It's just bad luck that my first check died right away."
```

Player_9 spoke next because player_7's tags opened a debt, not because a model chose it, and its
prompt said so: "You were directly addressed by player_7. Respond to them this turn." The reply
defends the earlier check but never says whom player_9 will investigate. The scheduler can give a
turn; it cannot make the turn an answer. The [turn-prompt
report](../../../evidence/gameplay/turn_prompt/report.md) explains the wording supplied to the
player.

**Two limits keep a feud from taking the day.** The draft's talk-time penalty could never silence a
player who had been addressed, so two players locked on each other could trade lines forever.
*Freshness* replaced it: while B still owes A, another question or accusation from A to B, however
reworded, opens nothing, and because it keys on who pressed whom, no model has to judge whether the
wording is new. A *cap per pair* stops the exchange after two rounds of A pressing and B answering,
until the pair has gone untouched for as many turns as there are living players.

**When nobody owes a reply, the open floor provides another route to speak.** A sweep offers turns
in seat order to players who have not spoken today. New questions and accusations are answered
before the sweep continues. This gives quiet players an opportunity without requiring the scheduler
to guess whether they hold useful evidence.

**Recomputed every turn.** The scheduler keeps no counters; before each turn it works out who owes
whom from the transcript itself. Counters would be the obvious design, but one missed update and
they disagree with the transcript for the rest of the day. Recomputing cannot drift, and a test can
write a transcript by hand and check the pick. The cost: the transcript must hold everything the
scheduler needs, so a human's untagged free text gets a separate tagging call ([Adding a human in
the loop](../human_in_the_loop/human_in_the_loop.md)).

**The scheduler depends on accurate tags.** An untagged accusation creates no reply debt, so the
accused is not queued to respond. Model-generated tags performed better than simple text matching in a
small comparison. A separate model review suggested missed accusations were the main weakness, but
without human-checked labels it cannot establish their frequency. A prepared dataset awaits
hand-labelling to measure accusation recall.

### Deciding which lines reach the table

An opportunity to speak does not guarantee publication. Openings are generated together, so one model
call checks the batch for permitted content and repetition. It checks the kind of statement, not its
truth: a false role claim can still be published.

Open-floor turns arrive one at a time. After generation, an echo gate compares each line with the
day's discussion, holding repetition and filler while keeping new facts, reasoned interpretations and
questions. This separate check was introduced because players' own decisions to pass did not reliably
distinguish useful speech from repetition.

Human lines bypass both checks, and direct replies are exempt from the echo gate. Both checks fail
open: an error keeps the line. A held line and its accompanying private note are discarded; its tags
create no reply obligation, and its author gets no further turn that day. This keeps unpublished
speech from affecting play, but makes a mistaken hold costly.

### Ending discussion and hearing a closing defence

When no reply is owed, the scheduler offers players who have not spoken a turn, resolving any new reply
obligations before continuing. A second sweep runs only if the first produces a published line.
Discussion ends once both the obligations and sweeps are complete. A cap limits discussion, but reaching
it still allows each player with an outstanding reply one final turn, so accusations are not cut off
unanswered.

Up to two players accused by at least two distinct players then receive a closing defence before
voting. These turns are generated together, with no new accusations or replies. Selection uses public
accusation tags; using private reads would leak information through who gets called.

Code announces only the selected players' names. It does not summarise the case or name their
accusers, because an incorrect statement in the moderator's voice could be mistaken for an
authoritative fact.

The mechanism has run in test games, but whether a closing defence changes voting behaviour remains
unmeasured.

<!-- Supporting notes (moved out of the page copy 2026-10-28; interview defence, not page text).
Source: ../../../evidence/gameplay/discussion/report.md#decision-18 (the closing defence); the cap and
drain: #decision-19 and #decision-20 in the same report.
- Why most-accused, not an unanswered accusation: the trigger first wanted was an accusation still
  unanswered, but the scheduler lets an accused player reply before the day can end, so those existed
  only on capped days. Most-accused works: in the 28 nine-seat games on the June design, the lynched
  player was among the day's most-accused on 61 of 67 voting days.
- Why the cap drains instead of stopping: a hard stop had left accusations hanging; on the June
  design, every day that ended with one unanswered had hit the cap. The cap is three real lines per
  living player; at the cap each debtor answers at most once more.
- A model summary of the case was the obvious alternative to the code-written line; rejected because
  players take moderator lines as fact. The code line first named the accusers too; a tag can be
  wrong, so since 2026-10-16 it names only who is called.
- A turn for each accused player's top accuser was considered and dropped: two more calls, and one more
  prominent turn for a wolf pushing a lynch.
- Test games (nine-seat, October 2026): the closing ran on 7 of 12 voting days in four games, and the
  defended player was voted out all 7 times.
- Design intent: the accused player's last word before the vote, as in Town of Salem, without a second
  vote. -->

### Why silence needed more than one fix

The earlier sequential design ended discussion after three consecutive passes. A separate novelty
judge could also withhold a generated line. Reviewing 28 nine-seat games revealed three different
causes of silence:

- **Held:** the judge withheld 367 of 517 recorded passes.
- **Never offered:** the stopping rule ended every first-day discussion after only three players had
  been offered turns.
- **Chose to pass:** players voluntarily declined to speak in the remaining 150 passes.

Most recorded passes therefore came from withheld speech, not players choosing silence. Players who
never received a turn were a separate scheduling failure.

The rebuild addressed these causes separately. An opening round gives every player a turn, and sweeps
replace the three-pass stopping rule. Deciding whether speech is worth publishing happens after
generation, through the checks described above. The calibration below explains why that decision moved
out of the player's own choice to pass.

<!-- Supporting notes (moved out of the page copy 2026-10-28; interview defence, not page text).
Source: ../../../evidence/gameplay/discussion_evidence.md §2.4 (the pass breakdown) and the
never-offered table (line ~978); records = June design, Gemini 3.5 Flash-Lite, played 2026-09-17.
- Held = 71% of passes (367 of 517): the table saw only a player who said nothing.
- Never offered: day 1 ended after the first three players passed in 28 of 28 games (8 of 9 games on
  the website); on 8 of 96 voting days a living player was never offered a turn.
- Did players read silence as behaviour? Less than expected: a read of 25 sampled accusations put
  quietness behind roughly one accusation in eight; a keyword search found speaking order cited as
  evidence on 5 of 95 days (never checked by a judge). The moderator-order rule is now on the page
  under "Choosing the next speaker".
- Silence was not why the talk was thin: that came from one exact source of information nobody
  contested, taken up in ../evidence_design/evidence_design.md. -->

### Testing who should judge a contribution

In a small replay study, model readers judged many lines generated from previously passed turns
worthwhile, raising doubts about players' decisions to pass. Removing the pass instruction encouraged
more speech on turns whose earlier lines had been labelled both worthwhile and repetitive. The new
lines were not relabelled, so this measured willingness to speak rather than their quality.

This motivated revising the existing check after generation. On the calibration sample, the revised echo gate caught
some repetition without withholding any lines judged worthwhile. It still missed substantial
repetition, and the labels came from model readers rather than validated human judgements. The checks
support the design choice, but do not establish better reasoning or game quality.

[Deciding when an agent should speak](silence_calibration.md) explains the silence policy, its
implementation and the calibration that informed it, including where the gate cannot detect repetition.

<!-- Supporting notes (moved out of the page copy 2026-10-28; interview defence, not page text).
The L3 silence_calibration.md explains the policy and selected evidence. Full variant tables remain
in evidence/gameplay/data/silence_calibration/README.md.
- Who decides: turns sampled from 16 ten-seat games, passes replayed with an instruction to speak,
  blind model readers (one Sonnet reader per line). Open floor: 23 of 40 forced lines judged
  worthwhile against 13 of 25 posted lines.
- Pass-rule wording barely moved decisions; cutting "a pass costs nothing here" raised open-floor
  speech from 20 of 64 turns to 41 of 64, for both worthwhile and restating turns (a volume knob).
- The shipped gate on 65 judged open-floor lines: held 10 of 29 restatements and 0 of 36 worthwhile
  lines; the previous gate held none of either.
- Four games on the deals of four earlier games: published open-floor turns 41 of 100 → 54 of 93; all
  seven held lines repeated a recent contribution.
- Limits: one model reader per line, never checked against a person; forced speech may differ from
  voluntary speech; the prompt comparisons reused the original line's judgement (a turn's value is its
  first-step verdict) rather than judging each newly generated line.
- Trade-off accepted: an extra checking call and substantial remaining repetition, to reduce the chance
  that useful contributions stay unheard. -->

### An opening can still distort the discussion

In its first games (nine-seat, Gemini 3.5 Flash-Lite, 2026-10-07), every investigator who claimed in
a day-2 opening was voted out that day: three of three, 7 votes to 1 each time. Reading the games
showed a chain:

1. Night-1 targets fell on seat 1: with nothing to go on, the model takes the lowest player number. In
   all four test games the investigator checked player_1.
2. So the investigator's first result was about the player most likely to be dead by morning, and the
   opening rule told it to announce that result even when the morning had already revealed it.
3. Everyone else passed, so the investigator's was the only name on the table, and the open floor and
   the vote piled onto it.

Two fixes followed. The opening rule now says a result the morning already made public is not news.
And on night 1 the engine draws a default target by lot, described on [the day and night
page](../day_and_night/day_and_night.md). The record lists the fixes, not a later
lynch rate for claimants.

### Giving characters a voice

Each website character gets a short voice instruction in its player's prompt. It describes tone,
such as “Brisk and polite, like a porter on a busy shift: short and practical”, without signalling a
role or side. Batch games run without voices, and human players are not assigned one.

A separate rewrite call was rejected after 19 of 90 rewrites changed something a listener could act
on, even though blind readers preferred the wording in 74 cases. Putting the voice in the original
turn avoids that second transformation. It does not establish that voice instructions leave
decisions unchanged: the frozen-turn comparison was small, whole games also differed in speech
volume, and factual errors in voiced lines have not been counted. The [voice
studies](../../../evidence/gameplay/data/persona_line/README.md) record those comparisons.

### What the checks establish, and where the rules fail

The scheduler's rules are tested apart from their effect: unit tests on hand-written transcripts,
with no model, pin debts opening and closing, freshness, the pair cap and its reset, the sweeps, the
drain and the choice of who gets a closing turn. They show the rules work as written, not that they
make a good day. The tags, opening filter and gate have separate behavioural checks (the opening
filter's, for one, kept 13 real openings and held one planted padding line: a small check, not an
accuracy estimate); whole-game reads supplement those tests. Any revision has to keep three things apart, **getting a turn**,
**publishing a line** and **answering a question**, since one can improve while another gets worse:
the player_9 exchange got a turn and was published, and still did not answer.

What is not established:

- **No standing regression bar.** There are no fixed thresholds for repetition, response
  opportunities, substantive answers or participation under the current design, and today's discussion
  has not been measured against the nine-seat design's.
- **The tags are the weak joint.** A rebuttal that tags nobody opens no debt. In one October test game
  (nine-seat, Flash-Lite, day 3), the accusations against player_7 carried no tags, so every route to
  speak failed together: no reply was queued; its open-floor line, a defence, reached the gate without
  the exemption for answering an accuser and was held as a repeat; a held player is not asked again;
  and no closing ran. Player_7 was voted out as a villager without having spoken that day.
- **Order effects are unmeasured.** A later speaker's advantage and the framing set by early speakers
  have not been quantified; a comparison with seats permuted is the proposed test.
- **The numbers were set by hand and never swept:** two rounds per pair, the reset after a table's
  worth of turns, two sweeps, three lines per player. One shipped wrong: the reset sat at three tables'
  worth instead of one, and was corrected about 20 days later, found on a reading of the code.

**Evidence.**

- [The day discussion: who speaks, when, and when the day ends](../../../evidence/gameplay/discussion/report.md),
  "The problem", "A day today", decisions 1–4, 7–21, "How it was checked" and "What is not
  established".
- [Discussion evidence](../../../evidence/gameplay/discussion_evidence.md), §2.4 (the three sources of
  silence), §7.1 (what the game records say), §7.4 step 8 and §7.5 (the October test games and the
  investigator chain).
- [Silence calibration](../../../evidence/gameplay/data/silence_calibration/README.md), steps 1–5.
- [Voice rewrite study](../../../evidence/gameplay/data/voice_rewrite/README.md),
  [prompted-voice line study](../../../evidence/gameplay/data/persona_line/README.md) and
  [paired voice games](../../../evidence/gameplay/data/persona_voice_games/README.md).
- [June acceptance study](../../../evidence/gameplay/discussion/quality_gate/experiment_log.md).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: map 117; discussion/report.md "The problem" (the engine decides the rest), decision 15
("they may read the machinery as behaviour"); content plan brief 2 reader question.
Needs and two choices: report "The problem" (four needs; two distinctions); day flow: "A day today"
(closing only if anyone has two accusers: stated in the closing subsection); ~30 calls: "Who decides
what" footnote and discussion_evidence §7.4 step 8 (four games, flash-lite, memory off, "about 30 calls
a voting day"); model gemini-3.5-flash-lite per §7.4 step 8 and §7.3.
Sequence vs concurrent: decision 1 (sound first choice; five openers verbatim; enables, does not
guarantee; cost; acceptance study: 4 vs 8, gemini-3.1-flash-lite, written rubric, unpaired, reader had
built the design, descriptive; tag concurrent-baseline). Lexical echo metric (0.00 vs 0.05–0.06) left
out: the 0.60 threshold misses paraphrase, so it needs a caveat longer than its value here. Parallel
open floor: decision 7 (2026-10-07, seven lines to keep two, tag phase2-parallel-proactive); nine-seat
flash-lite from §7.4 (the step 6 capture predates the step 8 games, same model).
Scheduler: decisions 3 (weighted score, two hard paths), 8–10 (tags, two dimensions, any engagement
discharges; seven times in a row, June), 11 (freshness, pair cap, talk-time penalty replaced, reset),
4 (stateless; human tags), 19–20 (drain; cap 3/player, floor 6; 10 capped June days with an open
accusation debt per §7.1; the cap never reached in four October games, closest day 11 of 12, cut for
length); "Reactive turns" exchange and prompt line verbatim (phase2-step8-game1, day 2); "The sweeps".
Tag numbers: decision 8 evidence (Smoke 1, June, gemini-3.1-flash-lite, 30 frozen cases, 11
disagreements favoured the model; 145/183, 24 missed, 1 added, message-level, judge unchecked;
2026-10-28: owner's wording, counts kept here only; "small comparison" = Smoke 1, "model
review" = the 183-message judge read; the hand-labelled set is
evidence/evaluation/labeling/owner_checks/accusation_tags/, not yet labelled). Quietness "one in eight": §2.4 extrapolates from 25 sampled accusations in
the "behaviour pattern" bucket (about a fifth about silence), hence "a read of sampled accusations". Vote-reason / reply briefs: block 145, chapter 3 (linked to the
turn-prompt report until the chapter 3 page exists).
Three sources: discussion_evidence §2.4 (517 passes, 367 novelty gate, 150 chose, 71%; 25 sampled
accusations, ~1 in 8; 5 of 95 days, keyword search, unjudged) and §7.1 (28 of 28, 8 of 9 website, 8 of
96 voting days); model and date: discussion_evidence closing sources line (gemini-3.5-flash-lite on
Vertex) and report decision 12 (played 2026-09-17); §2.5 (thin talk = one uncontested source; engine
silence not the main cause). Rule sentence: decision 15 ("less than expected"). Mapping to the rebuild:
map 126 ("redirected the October rebuild (the opening round, the sweeps, default speech)"); decisions
16, 20, 13.
Opening: "The opening round"; decision 16, ../../../evidence/gameplay/discussion/report.md#decision-16 (why a round, at once, restricted, allow-list; 13 + 1
offline; 5 of 106); decision 6 (no guaranteed slot for the investigator: priority would single it out).
Chain: decision 17 (2026-10-07, nine-seat, gemini-3.5-flash-lite, three of three, 7-1; three links;
two fixes); §7.4 step 8 (5 of 106, no evil claim). Night-1 lot evidence: block 146, chapter 3.
Gate: "The sweeps" (holds/keeps/exemptions/fails open); low thinking: Agents/turn/echo_gate.py
get_llm_judge("low"), checked 2026-10-26. Separate judge: decision 12 (Smokes 2-4, 20/20 and 20/20,
temperature 0 and 1.0; does not isolate the cause); discussion/experiment_log.md Smokes 2-4
(flash-lite, June).
Calibration: decision 13; silence_calibration/README.md step 1 (162 turns, 16 games = the persona voice
games, Haiku 5.5; 156 lines; four blind Sonnet subagents, one per line, blind to spoken/held/forced;
open-floor pass 40 at 57% = 23; posted open floor 25 at 52% = 13), step 2 (rewrite moved no decision),
step 3 table (pass sentence cut: worth hearing 13/35 → 23/35; D 7/29 → 18/29; total 20/64 → 41/64;
37/24 → 66/62), step 4 (v3 as ported 10/29, 0/36; current bar 0/29, 0/36), step 5 (4 games on the
deals of voices-01..04; 41 of 100 → 54 of 93; 7 held, all restating a line spoken shortly before).
Readers unchecked: map 128, hardening task 1b. "Holds about a third": report "What is not
established". Failed call vs wrong verdict: portfolio-writing-prompt evidence discipline; content plan
page 4 subsection 6. Held line: decision 14 (note dropped; no debt; closing; not re-asked; four
accusers of six; four calls nothing kept); the 2026-10-14 layout change left out (dated history, not
needed to explain the rule).
Closing: "The closing defence"; decision 18 (design intent, Town of Salem; trigger; 61 of 67 (28 June
games); public tags not private reads; code-written line; names dropped 2026-10-16; top-accuser turn
dropped; 7 of 12 voting days, 7 of 7 voted out, effect open); §7.1 (unanswered accusations only on
capped days).
Voices: "The voices"; decision 21; voice_rewrite/README.md (30 lines, three voices, Haiku 5.5
rewriter, blind Sonnet subagents; 74/90; 19/90; gate 1 of 19; drift pair verbatim); persona_line/
README.md (15 frozen Haiku turns judged as 30 voiced-vs-plain pairs, 10 per voice, plus 10
plain-vs-plain pairs; stance 9/30 vs 3/10; the 25-of-30 naturalness preference left out for length);
persona_voice_games/README.md (8 pairs, Haiku 5.5, Brier better 7 of 8; p ≈ 0.07 and the town-wins
figures left out, the plan asks for a lean; 206 vs 246 lines ≈ 19% more). Voices on in hosted games:
server/game/run_config.py persona_voices=True (checked 2026-10-26).
Checks and limits: "How it was checked" (tests/engine/test_scheduler.py, test_sweep.py,
test_closing.py, test_day_rounds.py; four games read in full per version); "When to revisit the
design" (getting a turn / publishing / answering); "What is not established" (no regression bar; tags
weak joint; held-defence case = discussion_evidence §9 item 9, phase2-step8-game1, day 3; order
effects, seat-permuted test; knobs; opening-order sentence, Agents/prompts/game_rules.py line 43
"in an order drawn at random that day", checked 2026-10-26); decision 11 (reset shipped wrong ~20
days, found 2026-06-24). Discussion quality vs nine-seat: gameplay hub problem 2; content plan
"No overclaims". -->
