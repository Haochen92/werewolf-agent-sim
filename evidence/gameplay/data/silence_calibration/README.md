# Silence calibration: who sorts the open floor's lines (2026-10-18)

> **What this is.** The record of a one-day study, in five steps, that moved the job of keeping
> repetition off the open floor from the player's own decision to pass to the echo gate. Each step's
> method, results and reading are as written on 2026-10-18. Where a reading claimed more than its
> evidence carries, a dated correction (2026-10-28) sits directly beneath it; the original wording is
> kept. Later steps supersede earlier ones.
>
> **Companion docs.** The shipped design is decision 13 in
> [the day discussion report](../../discussion/report.md). The 16 source games are recorded in
> [persona voice games](../persona_voice_games/README.md). Runner:
> `evaluation/experiments/silence_calibration.py`, committed with this record at `a6e1be83`.

## Terms

The steps below use these words without re-defining them.

- **Seat**: one player in the game. The readings say "seat" where the write-up says "player".
- **Opening round**: at the start of each day, every living player is asked at once and may make a
  role claim, share a night result, or pass. One model call, the **opening filter**, checks the
  batch before it is published.
- **Open floor** (in code, a *proactive sweep* turn): when nobody owes an answer, the engine offers a
  turn, one at a time in seat order, to each player who has not spoken yet. The player either speaks
  or passes.
- **Reactive turn** (an owed reply): a player who was questioned or accused must answer. It always
  speaks and is never gated.
- **Later turns**: open-floor turns and reactive turns together, i.e. everything after the opening.
- **The pass sentence**: the line in the open floor's rules, "If you have nothing new to add, set
  pass_turn=true; a pass costs nothing here."
- **Echo gate**: one model call per open-floor line, after the line is written. It reads the line
  against the day's spoken lines and holds it if it repeats. Before this study its bar was "the same
  point as an earlier line" (the owner's Phase 2 ruling, 2026-10-07).
- **Forced line**: what a player writes when one of its passes is replayed with "do not pass this time"
  added to the prompt.
- **The four kinds** each judged line was sorted into:
  - **A**: a new fact, meaning a role claim or the speaker's own night result;
  - **B**: a new inference, or a different reading of facts already known;
  - **C**: a pointed question or test nobody has asked yet;
  - **D**: a restatement, a repeated request, or filler.

  **Worthwhile** (written "A–C" or "A+B+C") means one of the first three kinds.
- **Thinking level** (*minimal*, *low*): how much the gate's model reasons before it answers.

## Why the study was needed

The pass sentence and the echo gate both exist for a real reason: before any check on repetition, a
single day could hold twenty near-identical messages of agreement
([discussion evidence](../../discussion_evidence.md), §1). In the June design the gate was the larger
cause of silence (367 of 517 passes in 28 games, §2.4); Phase 2 narrowed its bar to "the same point",
so by October the open floor's silence came from the players' own passes.

**The owner's question (2026-10-18):** the silence rules feel too strict: a player with a genuinely
different view got silenced. How do we calibrate silence on principle, strict in the opening and more
lenient later?

The question underneath: does a player's own decision to speak or pass separate a worthwhile line from
a repetition? If it does, the pass sentence can be tuned. If it does not, the sorting has to happen
somewhere else.

---

## Step 1: what did the passes hold back?

*Catches:* a pass leaves no line, so whether it hid something worthwhile cannot be seen without
replaying it.

**Method.**
- **Source:** the 16 persona voice games (ten-seat, Haiku 5.5, 2026-10-18), where every turn's prompt
  input was captured. All 1,271 discussion turns (closing defences left out) pair one to one with the
  transcript entries they produced.
- **Draw** (seeded, 162 turns): 40 voluntary passes each from the opening and the open floor; every
  line the opening filter held (7, all from before its 2026-10-18 fix `5cc25d67`, which now keeps a
  follow, a watch and every other night result); and 25 posted lines each from the opening, the open
  floor and reactive turns.
- **Forced replays:** each drawn pass was replayed once on its own captured prompt input, with one
  instruction added ("do not pass this time; write the message you would say"). Six replays failed,
  all opening passes, leaving 156 lines.
- **Judging:** four blind Sonnet subagents divided the lines, one reader per line. Each saw the line
  with what the player had seen (the earlier days' summaries and the day's discussion so far), but not
  whether it had been posted, held or forced. Each sorted the line into one of the four kinds and said
  whether it was worth hearing (yes/no).
- **Cost:** 80 replays, about $0.12.

### Results

| Turn | n | A | B | C | D | A+B+C |
|---|---|---|---|---|---|---|
| Held by the opening filter (before its fix) | 7 | 4 | 1 | 1 | 1 | 86% |
| Opening pass, forced line | 34 | 10 | 2 | 3 | 19 | 44% |
| Open-floor pass, forced line | 40 | 1 | 11 | 11 | 17 | 57% |
| Posted opening | 25 | 25 | 0 | 0 | 0 | 100% |
| Posted open floor | 25 | 1 | 7 | 5 | 12 | 52% |
| Posted reactive | 25 | 5 | 1 | 5 | 14 | 44% |

"Worth hearing" tracked the kinds: yes for every A and B, for 32 of 34 C, and for no D.

### Reading

1. **The opening is clean.** Every posted opening line was a new fact. What the opening passes hold
   back is mostly a role claim or a night result the seat chose to keep (10 of 15 A–C lines: "I'm the
   trailseer…", "I'm the sentinel…"). That is a strategic choice the role cards encourage ("keep my
   role hidden for now"), not a misjudged silence rule; whether seats should claim earlier is a
   separate question (owner observation 3, day-1 claims).
2. **On the open floor the speak-or-pass decision does not separate value.**
   - Passes would have said something worth hearing 57% of the time; posted lines were worth hearing
     52% of the time.
   - What the passes held is the owner's case: new readings and questions (B 11, C 11), not new facts.
     The silence rule licenses new information, a change of suspicion, and private role information,
     but never "a different reading of what is already known".
   - Meanwhile about half of what is posted restates.
   - The problem is not strictness in general but the criterion: made more lenient as is, it would
     add the restatements too.
3. **The echo gate never fired** in these 16 games (0 lines held), although about half of the posted
   open-floor lines were judged restatements. It is not broken: its bar is "the same point as an
   earlier line". A line adding a request or a next step passes, and so does filler, which repeats no
   particular line. The readers' D is wider: a repeated ask, an agreement without a new reason,
   filler. Whether the gate should hold filler is part of the calibration.
4. **Reactive turns** must answer an address, so some D there is an answer that restates. That half
   is not purely a calibration fault.

**Limits.**
- A forced line is what a seat writes when told not to pass, which may not be what it would have said
  by choice.
- 25–40 lines per row, one reader per line, and no person has checked the readers.
- The readers' bar for "new" is strict: anything already on the table is D.

**Next (proposed):** make the criterion explicit and measure whether the decision *separates* value,
not how often players speak. On the same replayed turns, a better rule would make a player speak more
often on worthwhile turns and less often on D turns. Candidates: a pass rule that names B and C as
reasons to speak and D concretely as the reason to pass, for later turns only (the opening stays
strict); and a look at why the echo gate does not catch the restatements.

---

## Step 2: the pass rule rewritten around the kinds

*Catches:* the rule never licensed a different reading (Step 1, reading 2). Does naming B and C as
reasons to speak release them without releasing D?

**Method.**
- All 162 drawn turns were resampled twice, once under the current rule and once under variant 1
  (`SILENCE_RULE_V1` in the runner). Variant 1 lists A, B and C as the reasons to speak, including "a
  different reading … worth saying even if the table leans the other way", and D as the reason to
  pass. The opening's rules were unchanged.
- Each turn keeps Step 1's verdict on its line as its label. The lines written in this step were not
  judged.
- Output: `variant_samples.jsonl`, `variant_scores.json`.
- Cost: 324 calls, about $0.40.

| Player speaks, on turns Step 1 judged… | Current rule | Variant 1 |
|---|---|---|
| Later turns, worthwhile (A–C) | 24/46 | 25/47 |
| Later turns, D | 21/43 | 21/43 |
| Opening, worthwhile | 22/46 | 24/46 |
| Opening, D | 0/20 | 2/20 |

The rewrite moved no decision on the open floor. The spoken lines were not judged.

> **Correction (2026-10-28).** "No decision" is one turn: 24 of 46 → 25 of 47 on worthwhile later
> turns. The rows combine open-floor turns with reactive turns, so this table does not show the open
> floor alone.

---

## Step 3: the other things in the prompt that tell a seat to pass

*Catches:* if rewording the rule did nothing, is something else in the prompt holding players back?

**Method.**
- The 90 later turns (65 open-floor, 25 reactive) were resampled with one part of the prompt changed
  at a time, each beside Step 2's current-rule sample on the same turns:
  - `no_note`: the private note a player carries from its previous turn, blanked (all 90 turns);
  - `no_pass_sentence`: the whole pass sentence cut (the 65 open-floor turns);
  - `no_blend_in`: the role cards' "Blend in and participate like an ordinary town player." changed
    to "Take an active part in the discussion." (the 48 turns of the six cards that have it).
- As in Step 2, each turn keeps Step 1's label; the lines written here were not judged.
- Output: `lever_samples.jsonl`, `lever_scores.json`.
- Cost: 203 calls (2 failed), about $0.25.

| Player speaks, on turns Step 1 judged… | Current | Changed |
|---|---|---|
| Note blanked: worthwhile | 24/46 | 27/46 |
| Note blanked: D | 21/42 | 23/42 |
| Pass sentence cut: worthwhile | 13/35 | 23/35 |
| Pass sentence cut: D | 7/29 | 18/29 |
| "Blend in" softened: worthwhile | 12/25 | 10/25 |
| "Blend in" softened: D | 10/23 | 11/23 |

### Reading

1. **One sentence sets the volume of the open floor.** Cutting "a pass costs nothing here" doubles
   open-floor speech: 20 of 64 turns to 41 of 64. The note and the role cards' caution move
   nothing beyond sampling noise, and neither did Step 2's rule rewrite.
2. **It is a volume knob, not a filter.** With the sentence in, the seat speaks on 37% of the
   worthwhile turns and on 24% of the D turns. With it out, those figures are 66% and 62%. More
   of what the owner missed gets said, but restatement nearly triples, and the little separation
   there was disappears.
3. **So the seat cannot calibrate itself by rule text.** No wording tried here made it better at
   telling whether its own line adds something. The separation would have to come after the
   draft: let the seat speak and have a check hold the D lines. The opening filter already works
   that way for the opening, and the echo gate does for the later rounds, but the gate's bar
   ("the same point as an earlier line") lets D through.

> **Correction (2026-10-28).**
> - **What was cut.** Reading 1 names the clause, but the method cut the whole pass sentence, "If you
>   have nothing new to add, set pass_turn=true; a pass costs nothing here." The trial does not
>   isolate the clause.
> - **What the numbers measure.** Each turn keeps Step 1's label, and the lines written with the
>   sentence cut were not judged. So the table shows how *willing* players were to speak on turns
>   whose earlier line was worthwhile or D, not whether the new lines were worthwhile. "Restatement
>   nearly triples" means players spoke on 18 D-labelled turns instead of 7, not that 18 new
>   restatements were counted.
> - **How far the conclusion reaches.** With one sample per turn, readings 2 and 3 support: speech
>   rose in both groups of turns, and no tested wording made speaking decisions more selective. They
>   do not show that no instruction could; more samples or wording not tried here remain untested.

**Limits.**
- One sample per turn and version, with 23–46 turns per cell.
- Each turn's value is Step 1's line, not the line spoken in this step.

---

## Step 4: the echo gate does the sorting

**Ruling (owner, 2026-10-18), on Step 3's reading:**
- players speak by default on the open floor, so the pass sentence is cut (the ruling named its last
  clause, "a pass costs nothing here"; the whole sentence went);
- the echo gate sorts, holding restatements and filler;
- the opening stays as it is.

*Catches:* can a check that reads the finished line hold D without holding worthwhile lines?

**Method.**
- Runner: `gate_check` in `silence_calibration.py`, with an optional output tag.
- Lines: the 65 open-floor lines Step 1 judged blind (25 posted, 40 forced), each with the day's
  earlier entries the gate would have seen, rebuilt from the capture.
- Two candidate bars. Both answer in three steps (the line's point, what it adds, then whose line it
  repeats) and hold the line when "what it adds" is exactly "nothing":
  - v2 (`GATE_V2_SYSTEM`): A–C kept, D held;
  - v3 (`GATE_V3_SYSTEM`) adds that repeating the morning's report of the night is not a new fact, and
    that a general call for claims is new only if no one has made one yet.
- Output: `gate_check*.jsonl`, `gate_check*_scores.json`.

| Gate | Thinking level | D held, of 29 | Worthwhile held, of 36 |
|---|---|---|---|
| Current ("the same point") | minimal (as live) | 0 | 0 |
| v2 | minimal | 5, then 8 (two runs; only the second's rows are kept) | 1 |
| v3 | minimal | 9 | 1 |
| Current | low | 4 | 0 |
| v2 | low | 10 | 0 |
| **v3** | **low** | **12** | **0** |
| v3 as ported into `Agents/turn/echo_gate.py` | low | 10 | 0 |

The thinking level mattered as much as the wording: both new bars held more D and no worthwhile line
at low. The two v2 runs at minimal (5 and 8) show that a gap of two or three lines between bars is
within run-to-run variation. The ported gate's 10 sits inside that spread of v3's 12.

- **Where the gate misses:** the six D lines spoken before anyone else had spoken that day were never
  held. The gate is not called when there is no earlier spoken line, and it does not see the morning's
  report. Most of these lines restate the record and then ask for claims, which the Step 1 readers
  called filler. On a silent table such a line is arguably what moves the game.
- **Expected open floor:** with the sentence cut, seats speak on 66% of worthwhile turns and 62% of
  D turns (Step 3). With the gate holding about 40% of D and no worthwhile line, about 66% and 37%
  reach the table, against 37% and 24% before. More of what was being held back is heard, at a
  modest rise in restatement.

> **Correction (2026-10-28).** The "expected open floor" figures are a calculation, not a
> measurement. They hold only if two untested assumptions hold: that Step 1's labels still describe
> the lines written with the sentence cut, and that the gate behaves on those new lines as it did on
> the labelled ones. They also use the v3 trial's 12 of 29 (about 40%); the gate as shipped held 10 of
> 29 (about a third).

**Built:**
- `PROACTIVE_ROUND_RULES` without the pass sentence (it now says a line that adds nothing is held, as
  a repeat was);
- the gate's new bar and verdict descriptions (`LineEchoVerdict`), with filler held under
  `same_point_as: "none"`;
- the gate at low thinking (`get_llm_judge("low")`); the opening filter stays at minimal.

**Not yet measured:** whole games under the new open floor.

---

## Step 5: whole games under the Step 4 build

*Catches:* does the gate behave in play as it did offline, holding repetition and nothing else?

**Method.**
- Four Haiku games (`games/`, run with `persona_voice_games.py --out`), on the deals of persona games
  voices-01 to voices-04 with persona voices on, so each has a "before" game on the same deal. A pair
  diverges after its first differing line.
- Scored with `silence_calibration games_score` (`games_scores.json`).
- Cost: $0.55.
- All leak checks pass.

| Open floor, 4 games | Before | After |
|---|---|---|
| Turns spoken | 41 of 100 (41%) | 54 of 93 (58%) |
| Held by the gate | 0 | 7 |
| Passed | 59 | 32 |
| Winners | — | serial killer, town, town, town |

**Read in full (every line, vote and note):**
- **All seven held lines restate a line spoken shortly before:** the same question, the same
  pressure, or "nobody has given a reason". None held a fact or a claim.
- **The open floor carries the game:**
  - Questions get answers, and contradictions are pressed.
  - Three of the four games found a killer through it: voices-02's serial killer slipped "check" and
    was caught by an unclaimed trailseer's follow, and voices-03's illusionist was voted out for
    dodging its night.
  - Claims still arrive by the opening of day 3 or later.
- **Day 1 is silent in every game:** it is the opening alone, every seat passed, and there is no
  discussion on day 1 by design (`Agents/graphs/day.py`). The same was true before.
- **Bad town votes, each with its cause:**
  - voices-01 day 2: the town's sentinel was lynched 7–1 over a wolf count it had guessed and
    withdrawn, with a trailseer's stated vote starting the pile.
  - voices-01 day 3: the vigilante was lynched after saying it "held fire", a vigilante-only phrase
    nobody read as a claim. The serial killer's fake investigator claim stood, although only one
    investigator slot was open (the dead, hidden player_9).
  - voices-02 day 3: a true sentinel's three-visitor watch was disbelieved because "the report
    never said who came". The Chanteuse's fake healer claim went unchallenged.
  - voices-04 day 3: the sigilist was lynched on a rules misreading. The rules say "a blocked player
    is told 'You were roleblocked'", but the game tells only a player who chose an action, and the
    sigilist chose none on night 1. The table took its true "no notice" for a lie.
- **Voice slip:**
  - The Whale's "occasional sea phrase" made a healer say it "kept watch over player_8" (voices-03),
    a sentinel's verb for a protect, corrected a turn later.
  - The same voice opened a line with "Captain's log, day two." (voices-04).

> **Note (2026-10-28).** The readings describe the four "after" games; they were not compared with
> the "before" games for quality. Four games show the gate holding only repetition in play. They do
> not show that the extra lines made the discussion better.

---

## Status (2026-10-28)

**Shipped (2026-10-18):** the pass sentence is cut from the open floor's rules, so players speak by
default (a pass is still allowed); the echo gate holds a line that adds nothing, under the v3 bar at
low thinking; the opening is unchanged.

**Open:**
- No person has checked the readers' labels. A sample of the gate's decisions is prepared for hand
  labelling (Evaluation hardening task 1b).
- No level of restatement was set as acceptable, so the gate's 10 of 29 is where the bar landed, not
  a target.
- The whole-game effect on how well players reason has not been measured.

## Files

| File | What it holds |
|---|---|
| `items.jsonl` | The 162 drawn turns: game, day, player, role, round, kind (pass, posted, held), the line, and whether it was forced |
| `blind_key.json` | Maps each anonymous item id (`s000`…) to its turn and kind, kept from the readers |
| `packet_1.md` … `packet_4.md` | What each blind reader saw: the line and its context, without its kind |
| `verdicts_1.jsonl` … `verdicts_4.jsonl` | Each reader's kind, worth-hearing verdict and one-line note per item |
| `variant_samples.jsonl`, `variant_scores.json` | Step 2's samples and tallies |
| `lever_samples.jsonl`, `lever_scores.json` | Step 3's samples and tallies |
| `gate_check*.jsonl`, `gate_check*_scores.json` | Step 4's gate runs (`_judge_low` = low thinking; `_ported` = the shipped gate) |
| `games/`, `games_scores.json` | Step 5's four games (capture and manifest each) and their tallies |
