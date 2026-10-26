# Silence calibration: a volume knob, not a filter

*Level 3 · [Game design and orchestration](../game_design_orchestration.md) · parent: [Orchestrating the conversation](conversation.md), "Speak by default, filter after the line" · status: page copy drafted 2026-10-26 with the level prompts, as a complete study; to be updated when the owner's labels arrive; for the owner's review.*

## Brief

Copied from [`../content_plan.md`](../content_plan.md), "Level 3 candidates", "Possible", condensed; the
plan keeps its copy until the owner moves it.

**Reader question:** can a model player's own choice to pass be tuned into a filter for useful speech?

**Added value:** readers will learn how replaying each voluntary pass with "do not pass", blind
classification of the forced lines, and a one-sentence ablation showed that the choice to pass did not
separate value; and how the shipped gate was then measured on the same lines.

**Why separate:** the replay design, the counting units (turns drawn, lines judged, samples per arm),
the four-lever table and the gate's bar-by-thinking table need sustained attention. The parent's
argument is how the day is run.

**What stays on Level 2:** the result (held-back lines 23 of 40 worth hearing against 13 of 25 posted;
the volume-knob table), the shipped gate's 10 of 29 restatements and 0 of 36 worthwhile lines, the
whole-game counts, and the readers' scope.

**Owner's ruling (2026-10-26):** draft it now as a complete study; update it when the owner's own labels
arrive (Evaluation hardening task 1b). Present it as an engineering decision informed by model
judgements: one Claude Sonnet reader per line, never checked against a person, and 23–46 turns per
cell, stated where the results are, not as a closing caveat. The gate as shipped is 10 of 29; 12 of 29
was the trial bar before porting.

**Tags:** output guardrails, LLM-as-a-judge, blind annotation, ablation.

This page's exhibit rows (SC-…) are proposed in the drafting notes, for the owner to merge into
[`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Editorially drafted, not independently
verified; the questions for the verifier are in the drafting notes (NOTES_sc.md). -->

## Page copy (draft)

Silence calibration is the study that decided who separates useful lines from repeats on the open
floor: the player, by choosing whether to speak, or a separate check after the line is written. The
open floor is the part of a day's discussion where nobody owes anyone an answer, and the engine offers
the floor, one at a time, to the players who have not spoken yet. Until this study, a player given the floor there decided for itself
whether to speak or to pass.

The study started from reading games: players with a different reading of the evidence were staying
quiet. The obvious fix was to reword the rule that tells a player when to pass, so that it speaks when
it has something new and passes when it would only repeat. That fix adds no model call. But it works
only if a player's own choice can tell a useful line from a restatement, so I tested that first.

It could not. Lines the players held back were worth hearing about as often as lines they posted.
Rewriting the rule moved nothing, and the one sentence whose removal did move behaviour changed how
much players spoke, not which lines: a volume knob, not a filter. So players now speak by default, and
the echo gate, a separate model call, holds restatements after the line is written. The decision rests
on blind model judgements of each line; this page shows how they were collected and how much they
carry.

### What decided a pass before the change

In an earlier version of the day, most silence had been the engine's doing, and a redesign removed
those sources (the parent's "Silence had three sources"). What remained on the open floor was the
player's own choice. The rules told a player to pass if it had nothing new to add, and ended: "a
pass costs nothing here." After a player spoke, the echo gate held the line only if it made "the same
point as an earlier line", and in the 16 games this study drew from, it held nothing. So every silence
on the open floor was a player's decision, which is what a better rule would have to tune.

### Making a pass visible

A pass leaves no line, so there is nothing to judge. To see what a pass held back, I replayed it. The
16 source games (ten-seat, Claude Haiku 5.5, 2026-10-18) captured every turn's full prompt input, so
any turn can be run again on exactly what its player saw. Each sampled pass was replayed once, with one
instruction added after the prompt: "whatever the rules above say about passing, do not pass this
time. Write the message you would say if you spoke now, as you would say it." A forced line is what a
player writes when told not to pass, which may differ from what it would have said by choice.

The turns were drawn with a fixed seed, 162 in all:

- 40 passes each from the opening round and the open floor, each replayed;
- the 7 lines the opening round's filter had held;
- 25 posted lines each from the opening, the open floor and the replies players owed.

Six replays failed, all of them opening passes, leaving 156 lines. Most of this page follows the 65
open-floor lines: 40 forced and 25 posted.

Four Claude Sonnet readers divided the lines between them, one reader per line. Each saw the line with
what its speaker had seen (summaries of the earlier days and the day's discussion so far), but not
whether the line had been posted, held or forced. The reader sorted the line into one of four kinds (a
new fact, meaning a role claim or the speaker's own night result; a new reading of known facts; a
question or test nobody had asked; or a restatement, a repeated request or filler) and said whether it
was worth hearing. "Worth hearing" followed the kinds: yes for every new fact and new reading, for 32 of
34 questions, and for no restatement. So on this page a *worthwhile* line is one of the first three
kinds. The readers' bar was strict: anything already on the table counted as a restatement.

Here is a pass that hid something. A watch is a night result showing who visited a player. With nobody
yet having spoken on day 4, a player who had passed wrote, when told not to:

> "Player_1's night 2 watch said player_2 and player_3 visited player_7. Player_3 is now dead, so only
> player_2 can be checked against that. player_2, what did you do on night 2, and who did you go to?"

Its reader called it a new question.

### The choice to pass did not separate value

If the choice to pass worked as a filter, the lines players held back would be mostly restatement and
the lines they posted mostly worthwhile. On the open floor they came out about the same:

| Open-floor line | Lines | New fact | New reading | New question | Restatement or filler | Worthwhile |
|---|---|---|---|---|---|---|
| Held back by a pass, forced on replay | 40 | 1 | 11 | 11 | 17 | 23 (57%) |
| Posted | 25 | 1 | 7 | 5 | 12 | 13 (52%) |

*One blind reader's verdict per line; 16 ten-seat Haiku 5.5 games, 2026-10-18.*

What the passes held back was readings and questions, not facts. The rule licensed new information
and private results, never a different reading of what everyone already knew. Meanwhile about half of
what players did post restated something, so loosening the same rule would add restatement along with
the readings. Each verdict here is one Claude Sonnet reader's, with 25 to 40 lines a row, and no person
has yet checked the readers; how that check is being built is on [Designing and validating LLM
judges](../../evaluation/llm_judges/llm_judges.md).

The opening round looked different. Every posted opening line was a new fact, and most of what an
opening pass held back was a role claim or a night result its player chose to keep, a strategy the role
cards allow rather than a misjudged rule. The opening was left as it was.

This result set the test for any new wording. A better rule would not just change how often players
speak: on the same turns, it would make a player speak more often when its line would be worthwhile,
and less often when it would be a restatement.

### Four changes to the prompt, one that moved

Each change was tried on the drawn turns it applies to. Every turn was sampled twice, once with the
prompt as it was and once with the change, one sample each, and the record shows whether the player
spoke. A turn keeps the value its reader gave it in the first step; the lines written in these samples
were not judged again. So each row asks: on turns where the player had something worth saying, did it
speak more often, and on turns where it had only a restatement, less often?

The four changes were: the pass rule rewritten around the kinds (speak for a fact, a reading of your
own "worth saying even if the table leans the other way", or a question; pass for a restatement); the
private note a player carries from its previous turn, blanked; six role cards' "Blend in and
participate like an ordinary town player." softened to "Take an active part in the discussion."; and
one sentence, "a pass costs nothing here", cut from the open floor's rules.

| Change (turns it applies to) | Worthwhile turns where the player spoke | Restating turns where the player spoke |
|---|---|---|
| Pass rule rewritten (90: open floor and owed replies) | 24 of 46 → 25 of 47 | 21 of 43 → 21 of 43 |
| Private note blanked (90) | 24 of 46 → 27 of 46 | 21 of 42 → 23 of 42 |
| "Blend in" softened (48, those six roles) | 12 of 25 → 10 of 25 | 10 of 23 → 11 of 23 |
| **"A pass costs nothing here" cut (65, open floor)** | **13 of 35 → 23 of 35** | **7 of 29 → 18 of 29** |

*Before → after; one sample per turn and version, 23 to 46 turns a cell; a turn's value is its
first-step verdict. Denominators differ where a sample failed. Haiku 5.5, 2026-10-18.*

The rewrite moved one turn. Blanking the note and softening "blend in" moved two or three turns either
way, which one sample per turn cannot tell apart from noise. Cutting one sentence moved everything:
open-floor speech went from 20 of 64 turns to 41 of 64. But it moved both columns. Before the cut, on
these turns, a player spoke on 37% of worthwhile turns and 24% of restating ones; after it, on 66% and
62%. More of what players had held back got said, restatement nearly tripled, and the little
separation there had been was gone.

That is a volume knob. No wording tried made a player better at judging whether its own line added
anything; the one lever found set only how much it spoke. If the sorting could not happen before the
line, it had to happen after.

### The gate, measured on the same lines

I made speech the default on the open floor by cutting the sentence, and gave the sorting to the echo
gate. The gate is one cheap model call per open-floor line. It reads the new line against the day's
spoken lines and answers in three steps: the line's point, what it adds (exactly "nothing" if it adds
nothing), and only then whose earlier line it repeats. Code holds the line only when the answer to
"what it adds" is "nothing", and keeps it if the call fails. The old bar, "the same point as an earlier
line", let through agreement, repeated requests and filler, which the readers counted as restatement,
so the bar had to widen.

Because the 65 open-floor lines already had blind verdicts, each candidate bar could be run on them
offline, with the earlier lines the gate would have seen rebuilt from the captures:

| Bar, at the gate's thinking level | Restatements held, of 29 | Worthwhile lines held, of 36 |
|---|---|---|
| Old: "the same point as an earlier line" (minimal, as in the games) | 0 | 0 |
| New: holds restatement, agreement with no new reason, a repeated request and filler (low) | 10 | 0 |
| New, stricter: repeating the morning's report of the night, or a second general call for claims, adds nothing (low) | 12 | 0 |
| **New, stricter, as shipped in the game (low)** | **10** | **0** |

*Reference: the first step's blind verdicts, one reader per line.*

The thinking level, i.e. how much the model reasons before it answers, mattered as much as the
wording. At minimal, both new bars held fewer restatements (8 and 9) and one worthwhile line each, so
the gate runs at low. Run-to-run variation is real too: one bar run twice held 5 and then 8
restatements, so a gap of two or three lines is not a ranking. Ported into the game's own gate code,
the stricter bar held 10, inside that spread of its trial's 12.

The shipped gate holds about a third of the restatements and none of the worthwhile lines. It errs
toward keeping, which is the way a filter in the live game should err: a wrongly held line silences a
player who had something to say, while a missed restatement costs one line of the table's attention.

Here is a line the gate catches. A follow, like a watch, is a night result, showing whom a player
visited; the Sentinel and the Trailseer are the roles that get them. On day 2 of one game, a player who
had passed was made to speak right after this line:

```
player_5: "Night 1 was a save on player_7, so whoever is holding a watch or follow should speak up with
           what they saw. …"
player_7: "Agreed the save tells us little until someone with a watch or follow posts a named visitor.
           Suggest anyone holding a Sentinel or Trailseer result post it now, even a blank one, so we
           can test claims against each other rather than against silence."
```

Its reader called player_7's line a restatement, and the shipped gate held it as a repeat of
player_5's.

The gate also has a blind spot. Six of the 29 restatements were the first line on an empty floor. The
gate is not called when nobody has spoken yet, and it never sees the morning's report of the night,
so a first line that restates the record always passes. Most of those six restated the record and then asked for
claims, and on a silent table, such a line is arguably what moves the game.

Putting the two measurements together gives an estimate, not a measured outcome. With the sentence cut,
a player speaks on about two-thirds of both kinds of turn, and the gate then removes about a third of
the restatements and none of the worthwhile lines. So about two-thirds of the worthwhile turns should
reach the table, against 37% before, while restatement reaching the table still rises above its old
24%. I accepted that cost, plus one more model call per open-floor turn, to hear the lines players had
been holding back.

### Four whole games

The change then ran in whole games: four ten-seat Haiku games on the deals of four of the source
games, with voices on as before, so each has a "before" game on the same deal. A pair diverges after
its first line that differs.

| Open floor, four games | Before | After |
|---|---|---|
| Turns with a published line | 41 of 100 | 54 of 93 |
| Lines held by the gate | 0 | 7 |
| Passes | 59 | 32 |

The four games were read in full. All seven held lines restated a line spoken shortly before: the same
question, the same pressure, or "nobody has given a reason". None held a fact or a claim. Four games
show the gate behaving as designed in play; they do not measure whether the games got better.

### What it settled, and what is still open

The study settled where the sorting happens. The player decides what to say, and a separate call that
did not write the line decides whether it reaches the table, the same separation of writer and checker
that the parent page argues for.

Three things are open. The readers' verdicts have not yet been compared with a person's: a sample of
the gate's decisions is being labelled by hand, and this page will be updated with those labels when
they are done. No level of restatement was ever set as acceptable, so the gate's third is where
the bar landed, not a target. And the whole-game effect on how well players reason has not been
measured.

**Evidence.**

- [Silence calibration](../../../evidence/gameplay/data/silence_calibration/README.md), steps 1–5 (the
  draw, the replays, the blind verdicts, the rule variant, the levers, the gate check and the four
  games).
- [The day discussion: who speaks, when, and when the day ends](../../../evidence/gameplay/discussion/report.md),
  "The sweeps" and decisions 12–14.
- [Discussion evidence](../../../evidence/gameplay/discussion_evidence.md), §2.4 (the June design's
  silence) and §7.4 step 4c (the gate's earlier bar).
- [Persona voice games](../../../evidence/gameplay/data/persona_voice_games/README.md) (the 16 source
  games).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: silence_calibration/README.md step 1 "Question (owner)" (a player with a genuinely different
view got silenced; how to calibrate on principle); content plan Level 3 "Possible" row; report decision
13 ("Instead of: tuning the rule that tells a player when to pass").
Before the change: discussion_evidence §2.4 (517 passes, 367 judge holds; June design) via the parent's
"Silence had three sources"; §7.4 step 4c (the per-line gate under "the same point" bar, owner
2026-10-07); the pass sentence verbatim from README step 3 ("If you have nothing new to add, set
pass_turn=true; a pass costs nothing here."); README step 1 reading 3 (the gate never fired in the 16
games, 0 novelty-gated turns).
Replay: README step 1 Method (source = the 16 persona voice games, every turn's prompt input captured;
draw, seeded; forced replays; six failed, 156 lines; four blind Sonnet subagents; kinds A–D; worth
hearing); runner evaluation/experiments/silence_calibration.py (FORCE string verbatim: "Measurement
turn: whatever the rules above say about passing, do not pass this time. Write the message you would
say if you spoke now, as you would say it, and set pass_turn to false."; SEED 20261018; DRAW
strata; asserts anthropic/claude-haiku-5-5 at thinking low; SUMMARY_TAIL 3000 chars of earlier
summaries). persona_voice_games/README.md (8 pairs, Haiku 5.5, thinking low, memory off, 2026-10-18).
"Worth hearing" tracking: README step 1 ("yes for every A and B, for 32 of 34 C, and for no D"). Strict
bar: README step 1 Limits. Six failures all opening passes: opening-pass row n = 34 of 40.
Example 1: items.jsonl turn voices-08.off:4:player_5:1 (pass_reason voluntary, forced, context today
"No messages yet."); verdict C ("asks player_2 what they did night 2, since only they can be checked").
Results table: README step 1 Results rows "Open-floor pass, forced line" and "Posted open floor";
re-tallied from blind_key.json + verdicts_1..4.jsonl (forced proactive A1 B11 C11 D17; posted proactive
A1 B7 C5 D12; each judge 39 items). Reading: README step 1 reading 2. Opening: reading 1. Readers
unchecked: map 128, hardening task 1b; Evaluation llm_judges.md "The open gap".
Decision rule: README step 1 "Next (proposed)" (P(A–C | spoke) up, P(A–C | passed) down; measure the
decision's discrimination, not its level).
Levers: README step 2 (variant 1 wording; 90 later turns; table) and step 3 (no_note, no_pass_sentence,
no_blend_in; turns touched 90/65/48; table; reading 1–3; limits: one sample per turn and arm, 23–46
turns per cell, value = step 1's line); lever_scores.json; runner lever_score() (the "before" arm is
step 2's current arm on the same turns). 20 of 64 → 41 of 64 and 37/24 → 66/62: README step 3 reading.
Gate: README step 4 (owner ruling 2026-10-18; method: 65 lines, earlier entries rebuilt from the
capture; hold when "adds" is exactly "nothing"; table incl. v2 minimal two runs 5/29 and 8/29, only the
second's rows kept; v3 low 12/29; v3 as ported 10/29, 0/36; the six empty-floor D lines, the gate not
called and blind to the morning report); gate_check_scores.json, gate_check_judge_low_scores.json,
gate_check_ported.jsonl (10 D held, 0 A–C held, re-tallied). Agents/turn/echo_gate.py (three-step
answer; hold only when adds == "nothing"; returns "" when no spoken lines; game_master lines excluded;
fails open; get_llm_judge("low")), checked 2026-10-26. "Errs toward keeping": the reasoning is editorial (the
Evaluation page llm_judges.md makes the same point); not a recorded design rationale.
Example 2: items.jsonl voices-07.on:2:player_7:1 (forced from a voluntary pass; today context = player_3
and player_5 lines verbatim, cut with ellipses); verdicts D ("agrees, repeats ask for named visitor")
and voices-07.on:2:player_5:1 posted D ("echoes player_3's call for watch/follow results");
gate_check_ported.jsonl held = "player_5" and "player_3" respectively.
Estimate: README step 4 "Expected open floor" (uses the trial bar's ~40% of D; restated here
qualitatively with the shipped gate's third, no new figure).
Cost: report decision 13 "Cost accepted".
Whole games: README step 5 (four Haiku games on voices-01..04's deals, voices on; 41 of 100 → 54 of
93; held 0 → 7; passed 59 → 32; read in full; all seven restate a line spoken shortly before; none held
a fact or a claim); games_scores.json re-summed.
Settled/open: report decision 12 (generator-verifier separation) via the parent; hardening task 1b and
llm_judges.md "The open gap" (labelling packets prepared, echo gate among the three sources); report
"What is not established" (no standing regression bar). -->
