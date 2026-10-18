# Counter-claim accounts, vote replay (2026-10-18)

**Question (owner):** two of the wolves' three wins in the evil cover games
(`../evil_cover_games/`) were counter-claims the town decided wrong. Slice 16 (deduction catalogue,
`evidence/reasoning_failures/deduction_catalogue.md`) adds to the counter-claim line what each claimant
names as the role:

> As the Investigator, player_2 names a check of player_7 on night 1 (Not suspicious), which a reveal of
> player_7's role would test; player_5 names no check result.

Does a town seat's vote move off the real claimant?

**Method.**
- Runner: `evaluation/experiments/counter_claim_vote_screen.py`.
- Turns: every town seat's vote on a day of the 8 cover games whose re-rendered seat block has the
  sentence: 10 turns on 3 days.
  - voices-06 day 2: the real Investigator (player_2, a check named) against the Necromancer (player_5,
    "kept my check"). The case the line was built for.
  - voices-05 day 4 and voices-07 day 3: the Sigilist. Here the fake (the Illusionist) names sigils and
    the real Sigilist names none.
- Arms, 3 samples each (Haiku 5.5, thinking low; 60 calls, 3 failed to parse). Both re-render the blocks
  with the checked-out engine; `without` removes the sentence. No judge: the vote is the measure.

## Results

Votes to lynch, per arm (a vote for the real claimant is the town's mistake):

| | without: fake / real | with: fake / real |
|---|---|---|
| voices-06 day 2 (Investigator; 4 seats) | 7 / 4 | **5 / 7** |
| voices-07 day 3 (Sigilist; 5 seats) | 2 / 12 | 4 / 10 |
| voices-05 day 4 (Sigilist; 1 seat) | 3 / 0 | 3 / 0 |
| All | 12 / 16 | 12 / 17 |

## Reading

1. **The line does not help, and in its own case it hurt.** In voices-06 the Sigilist and the Sentinel
   voted out the fake 3 of 3 times without it, and the real Investigator 2 of 3 times with it. The
   Sentinel was the check's own target, told "player_2 names a check of you … (Not suspicious)".
2. **A likely cause is name salience,** not the content: the line names the real claimant first and
   longest, and the models pick the seat a prompt names first (memory: prompt list order bias).
3. **The Sigilist days moved slightly the right way,** where the fake named results and the real one
   none: the worry that naming results rewards a fake did not show.
4. **Limits.** 10 turns, 3 samples, one model. Three days of three games. A direction, not an estimate.

**Decision (owner, 2026-10-18): dropped.** The line is a true fact (it passes the coverage ruling's one
bar), but it did not move votes toward the truth. Past the facts the block already had, the vote is the
model's call; rewording the line around the name bias would tune it to the model, not add a fact. The
engine change was never committed, so the runner now finds no turns at HEAD; the line's rule and
wording are in the catalogue's slice 16 row.
