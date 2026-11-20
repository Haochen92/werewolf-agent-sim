# Owner check: the accusation tags

## What this measures

In the day discussion every speaker tags its own message with the players it addresses and a stance
toward each: accusation, defense, agreement or neutral. The accusation tags decide who gets a closing
defence before the vote and whom the scheduler makes answer next. This check measures how often the
speaker's own accusation tags match whom you, reading the message, say it accuses. Your label is the
truth; the comparison is made afterwards and you never see the tags.

## What you do

1. Open `export/batch_01.md` to `export/batch_10.md` (50 messages from
   31 games, 5 per batch).
2. For each message, read the lines before it, then the message, and decide whom it accuses.
3. Write your answer in the `label` of the row with the same key in `export/answers_template.json`
   (`note` is for anything you were unsure about). The rows are in the same order as the batches.
4. Save the filled file as `human.json` in this folder and run
   `poetry run python -m evaluation.experiments.owner_check_accusation_tags score`.
   A label written loosely (`player_10, player_3`) is rejected with the exact fix to make.

## The rubric

A message ACCUSES a player when it suspects or blames that player of being evil or of lying.
- Suspicion counts even when hedged ("they are my top suspect, though I'm not certain").
- Saying a player's claim or report is false counts: that blames them of lying.
- It does NOT accuse a player it defends or supports, agrees with, or mentions with no clear
  stance. Passing commentary, such as noting that someone has been quiet, is not an accusation.
- A question accuses only when it plainly casts suspicion; a plain request for information does not.
Judge this message only, reading it in the light of the lines before it: a player it accused
earlier, but not in this message, is not accused here. Dead players can be accused too.

The label is `none`, or the ids of every accused player in seat order (lowest seat number
first), comma-joined with no spaces.

For example `player_4`, or `player_3,player_10` (seat 3 before seat 10).

## Worked examples

These are made up from the definitions the speakers were given; none is from the sample.

- *"player_4 says they are the healer but will not name one person they protected. I think that
  claim is a lie, and I'm voting player_4."* → `player_4`. It blames player_4 of lying.
- *"player_6 has been very quiet today. player_2, what did you see last night?"* → `none`. Noting
  that someone is quiet is passing commentary, and the question asks for information without
  casting suspicion.
- *"I trust player_3's check. That leaves player_9 or player_5 as our wolf: both pushed the same
  story yesterday."* → `player_5,player_9`. It suspects both (ids in seat order); supporting
  player_3 is a defence, not an accusation.
