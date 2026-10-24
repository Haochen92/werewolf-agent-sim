# Owner check: the echo gate

## What this measures

The echo gate (`Agents/turn/echo_gate.py`) holds an open-floor line it judges a restatement or
filler, so the table hears each point once. Its bar was set on open-floor lines that four blind
Sonnet readers sorted into four kinds. You label 50 of those same lines, blind,
on the readers' scale. Your labels then measure two things:

1. **The readers**: how often their kind matches yours (four-way, A / B / C / D).
2. **The shipped gate**: how often its decision matches yours on its own two-way scale: the gate
   **held** the line = **D**, the gate **let it be spoken** = **not D**. For this comparison your
   A, B and C all count as "not D"; `score` writes that binary copy of your answers to
   `human_binary.json` for you. Nothing to do by hand.

The lines are shown exactly as the readers saw them. Nothing in the packet says what the readers
or the gate decided, whether the line was spoken, or how the lines were drawn.

## What you do

1. Open `export/batch_01.md` and work through the batches in order.
2. For each item, decide its kind (A, B, C or D) using the rubric below.
3. Write the letter as the `label` of that item's row in `export/answers_template.json` (find the
   row by the key in the item's heading). Use `note` for anything worth remembering (optional).
4. Save the filled-in file as `human.json` in this folder (next to this guide).
5. Run `poetry run python -m evaluation.experiments.owner_check_echo_gate score`.

## What each item shows

- **Speaker** and the stage of the day.
- **Earlier days**: the most recent part of the earlier days' summary (it is cut to its last 3,000
  characters, so it may start mid-sentence).
- **Today's discussion** so far, as the speaker saw it.
- **THE LINE**: what you label.

Judge newness only against what is shown, as the readers did.

## The rubric (the readers' own wording)

Judge only THE LINE, against what the table already had (the earlier days and today's discussion shown):
- "A": it adds a new fact: a role claim or counterclaim, or the speaker's own night action or result that the table has not heard yet.
- "B": it adds a new inference, or a different reading of facts already known: a reason, a consequence, or a point of view nobody has put today.
- "C": it asks a pointed question or proposes a test that would move the game (who to check, what someone must explain), and that ask was not already made today.
- "D": it restates what was already said, agrees without a new reason, asks again for what was already asked, or is filler ("nothing to go on yet", "let's hear claims").
If a line does several things, pick the most valuable kind it really delivers. Judge newness strictly against the context shown: a fact or point already on the table is D, however well put.
Whether the line is true or a good move for the speaker's side does not matter.

## Worked examples

These are made up from the rubric's own wording, not taken from the packet.

1. **D.** Today, player_2 has already said "we should hear claims before we vote". THE LINE, from
   player_7: "Nothing to go on yet, let's hear claims." It asks again for what was already asked,
   and the rest is filler. Kind D.
2. **B.** The summary shows player_4 voted to eliminate both seats that were later revealed as town;
   nobody has pointed this out today. THE LINE: "player_4 has now voted against two town seats in
   a row, and both times switched late, so I trust their reads least." The votes are known facts,
   but the reading and its reason are new. Kind B. Had another player already made that point
   today, it would be D, however well put.
3. **C (a line that does several things).** player_5 has said the day-2 vote looked coordinated.
   THE LINE: "I agree with player_5 about day 2. player_8, why did you switch to abstain at the last
   moment?" The agreement adds no new reason (D on its own), but nobody has asked player_8 that
   today. Pick the most valuable kind the line really delivers: C.

Whether the line is true, or a good move for the speaker's side, never matters.

## Files

| File | What it is |
|---|---|
| `export/batch_NN.md` | The lines to label, 5 per batch |
| `export/answers_template.json` | Your answers file (fill in `label`, save as `human.json`) |
| `candidates.json` | The lines with their context (the export's source) |
| `strata.json` | Which stratum each drawn line came from (do not open before labelling) |
| `labels_readers.json`, `labels_echo_gate.json` | The two sources compared (do not open before labelling) |
| `calib_readers.json`, `calib_echo_gate.json` | The calibration configs `score` runs |
| `reports/` | Written by `score`: one markdown and one JSON report per source |
