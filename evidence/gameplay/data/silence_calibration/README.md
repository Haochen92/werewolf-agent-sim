# Silence calibration, step 1: false silence and noise by round (2026-10-18)

**Question (owner):** the silence rules feel too strict: a player with a genuinely different view got
silenced. How do we calibrate silence on principle, strict in the opening and more lenient later?

**Method.** Runner: `evaluation/experiments/silence_calibration.py`.
- **Source:** the 16 persona voice games (`../persona_voice_games/`), where every turn's prompt input
  was captured. All 1,271 discuss turns (closings left out) pair one to one with the channel entries
  they produced.
- **Draw** (seeded): 40 voluntary passes each from the opening and the open floor, every held line
  (7, all the opening filter's, before its fix), and 25 posted lines each from the opening, the open
  floor and the reactive discussion.
- **Forced replays:** each drawn pass was replayed once on its own prompt input with one instruction
  added ("do not pass this time; write the message you would say"). Six replays failed and drop out,
  leaving 156 lines.
- **Judging:** four blind Sonnet subagents saw each line with what the seat saw (the earlier days'
  summaries and today's discussion), not whether it was spoken, held or forced. Kinds:
  - (A) a new fact: a claim, or the speaker's own night result;
  - (B) a new inference or a different reading of known facts;
  - (C) a pointed question or test not yet asked;
  - (D) a restatement, a repeated ask, or filler.

  Plus "worth hearing" (yes/no).
- **Cost:** 80 replays, about $0.12.

## Results

| Turn | n | A | B | C | D | A+B+C |
|---|---|---|---|---|---|---|
| Held by the opening filter (old) | 7 | 4 | 1 | 1 | 1 | 86% |
| Opening pass, forced line | 34 | 10 | 2 | 3 | 19 | 44% |
| Open-floor pass, forced line | 40 | 1 | 11 | 11 | 17 | 57% |
| Posted opening | 25 | 25 | 0 | 0 | 0 | 100% |
| Posted open floor | 25 | 1 | 7 | 5 | 12 | 52% |
| Posted reactive | 25 | 5 | 1 | 5 | 14 | 44% |

"Worth hearing" tracked the kinds: yes for every A and B, for 32 of 34 C, and for no D.

## Reading

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
3. **The echo gate never fired** in these 16 games (0 novelty-gated turns), although about half of
   the posted open-floor lines were judged restatements. It is not broken: its bar is the owner's
   Phase 2 ruling, "the same point as an earlier line". A line adding a request or a next step
   passes, and so does filler, which repeats no particular line. The judges' D is wider: a repeated
   ask, an agreement without a new reason, filler. Whether the gate should hold filler is part of
   the calibration.
4. **Reactive turns** must answer an address, so some D there is an answer that restates. That half
   is not purely a calibration fault.

**Limits.**
- A forced line is what a seat writes when told not to pass, which may not be what it would have said
  by choice.
- 25–40 lines per row, one judge per line.
- The judges' bar for "new" is strict (anything already on the table is D).

**Next (proposed):** make the criterion explicit and measure the decision's discrimination, not its
level:
- P(A–C | spoke) should rise and P(A–C | passed) fall, on the same replayed turns.
- Candidates: a silence rule that names B and C as reasons to speak and D concretely as the reason to
  pass, for the open floor and the discussion only (the opening stays strict); and a look at why the
  echo gate does not catch the restatements.

# Step 2: the silence rule rewritten around the kinds (2026-10-18)

**Method.**
- The same 162 drawn turns were resampled twice, once under the current discussion silence rule and
  once under variant 1 (`SILENCE_RULE_V1` in the runner). Variant 1 lists A, B and C as the reasons
  to speak, including "a different reading … worth saying even if the table leans the other way",
  and D as the reason to pass. The opening rules were unchanged.
- Each turn's value is step 1's verdict on its line.
- Output: `variant_samples.jsonl`, `variant_scores.json`.
- Cost: 324 calls, about $0.40.

| Speaks when step 1 judged the turn… | Current | Variant 1 |
|---|---|---|
| Later turns, worth hearing (A–C) | 24/46 | 25/47 |
| Later turns, D | 21/43 | 21/43 |
| Opening, worth hearing | 22/46 | 24/46 |
| Opening, D | 0/20 | 2/20 |

The rewrite moved no decision on the open floor. The spoken lines were not judged.

# Step 3: the other things that tell a seat to pass (2026-10-18)

**Method.**
- The 90 later turns were resampled with one part of the prompt removed at a time, each beside
  step 2's current arm on the same turns:
  - `no_note`: the seat's carried-forward note blanked (all 90 turns);
  - `no_pass_sentence`: the open floor's "If you have nothing new to add, set pass_turn=true; a pass
    costs nothing here." cut (the 65 open-floor turns);
  - `no_blend_in`: the role cards' "Blend in and participate like an ordinary town player." changed
    to "Take an active part in the discussion." (the 48 turns of the six cards that have it).
- Output: `lever_samples.jsonl`, `lever_scores.json`.
- Cost: 203 calls (2 failed), about $0.25.

| Speaks when step 1 judged the turn… | Current | Lever pulled |
|---|---|---|
| Note blanked: worth hearing | 24/46 | 27/46 |
| Note blanked: D | 21/42 | 23/42 |
| Pass sentence cut: worth hearing | 13/35 | 23/35 |
| Pass sentence cut: D | 7/29 | 18/29 |
| "Blend in" softened: worth hearing | 12/25 | 10/25 |
| "Blend in" softened: D | 10/23 | 11/23 |

## Reading

1. **One sentence sets the volume of the open floor.** Cutting "a pass costs nothing here" doubles
   open-floor speech: 20 of 64 turns to 41 of 64. The note and the role cards' caution move
   nothing beyond sampling noise, and neither did step 2's rule rewrite.
2. **It is a volume knob, not a filter.** With the sentence in, the seat speaks on 37% of the
   turns worth hearing and on 24% of the D turns. With it out, those figures are 66% and 62%. More
   of what the owner missed gets said, but restatement nearly triples, and the little separation
   there was disappears.
3. **So the seat cannot calibrate itself by rule text.** No wording tried here made it better at
   telling whether its own line adds something. The separation would have to come after the
   draft: let the seat speak and have a check hold the D lines. The opening filter already works
   that way for the opening, and the echo gate does for the later rounds, but the gate's bar
   ("the same point as an earlier line", the owner's Phase 2 ruling) lets D through.

**Limits.**
- One sample per turn and arm, with 23–46 turns per cell.
- Each turn's value is step 1's line, not the line spoken in the arm.

# Step 4: the gate does the sorting (2026-10-18)

**Ruling (owner, 2026-10-18), on step 3's reading:**
- seats speak by default on the open floor, so "a pass costs nothing here" is cut;
- the echo gate sorts, holding restatements and filler;
- the opening stays as it is.

**Method.**
- Runner: `gate_check` in `silence_calibration.py`, with an optional output tag.
- Lines: the 65 open-floor lines step 1 judged blind (25 posted, 40 forced), each with the day's
  earlier entries the gate would have seen, rebuilt from the capture.
- Two candidate bars, held when the judge's "adds" is exactly "nothing":
  - v2 (`GATE_V2_SYSTEM`): A–C kept, D held;
  - v3 (`GATE_V3_SYSTEM`) adds that repeating the morning report is not a new fact, and that a
    general call for claims is new only if no one has made one yet.
- Output: `gate_check*.jsonl`, `gate_check*_scores.json`.

| Gate | Judge thinking | D held | A–C held |
|---|---|---|---|
| Current ("the same point") | minimal (as live) | 0/29 | 0/36 |
| v2 | minimal | 5/29, 8/29 (two runs; only the second's rows are kept) | 1/36 |
| v3 | minimal | 9/29 | 1/36 |
| Current | low | 4/29 | 0/36 |
| v2 | low | 10/29 | 0/36 |
| **v3** | **low** | **12/29** | **0/36** |
| v3 as ported into `Agents/turn/echo_gate.py` | low | 10/29 | 0/36 |

- **Where the gate misses:** the six D lines spoken on an empty floor (no earlier spoken line) were
  never held. The gate is not called there, and it does not see the morning report. Most of these
  lines restate the record and then ask for claims, which the step-1 judges called filler. On a
  silent table such a line is arguably what moves the game.
- **Expected open floor:** with the sentence cut, seats speak on 66% of worthwhile turns and 62% of
  D turns (step 3). With the gate holding about 40% of D and no worthwhile line, about 66% and 37%
  reach the table, against 37% and 24% before. More of what was being held back is heard, at a
  modest rise in restatement.

**Built:**
- `PROACTIVE_ROUND_RULES` without the sentence (it now says a line that adds nothing is held, as a
  repeat was);
- the gate's new bar and verdict descriptions (`LineEchoVerdict`), with filler held under
  `same_point_as: "none"`;
- the gate at low thinking (`get_llm_judge("low")`); the opening filter stays at minimal.

**Not yet measured:** whole games under the new open floor.

# Step 5: whole games under the step-4 build (2026-10-18)

**Method.**
- Four Haiku games (`games/`, run with `persona_voice_games.py --out`), on the deals of persona
  games voices-01..04 with voices on, so each has a "before" game on the same deal (which diverges
  after the first differing line).
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
