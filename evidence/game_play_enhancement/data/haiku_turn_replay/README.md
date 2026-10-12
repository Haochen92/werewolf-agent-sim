# The first Haiku 5.5 game: its failures replayed (2026-10-12)

Eighteen discussion turns frozen from the owner's live game `403f4dbc` (`cases.jsonl`, built by
`evaluation/experiments/haiku_game_turn_cases.py` from the game's LangGraph checkpoints on the server's
Postgres, read-only), in the hallucination bench's case format. Each case carries a hand-written
expectation; the bench's golden judge (Claude Sonnet 5.5, sent as one Message Batch) reads every part of
every sample against it: the public message, the private strategy note and the reads. Five samples per
case and arm, Claude Haiku 5.5 at effort low, memory off. An opening-round turn is replayed as a sweep
turn. Run by `poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_game.json`
(and `..._vote_v2.json`); summaries here, full output in
`evaluation/eval_results/hallucination_bench/haiku_game_403f*/`. Record: `../../discussion_evidence.md` §8.6.

Arms: **before** (the code at 746197c4, from a worktree), **after v1** (the three fixes, the vote line's
first wording), **after v2** (the vote line reworded; vote_reason turns only).

Slices: **visit** (a visit read the wrong way round), **repeat** (restating what one already said, asking
again what was answered), **vote_reason** (a town seat on a voting day's open floor that passed and then
voted a player out). Context: **origin** when no visit misreading is yet in the speaker's transcript,
**cascade** when other players have already made it.

Per turn, five samples each: passes / samples whose public message broke the expectation / samples bad in
any part.

| Slice | Context | Turn | Before | After v1 | After v2 |
|---|---|---|---|---|---|
| visit | origin | d3 investigator answers "I visited nobody" | 0 / 2 / 2 | 0 / 0 / 2 | |
| visit | cascade | d3 investigator, later | 0 / 5 / 5 | 0 / 2 / 4 | |
| visit | cascade | d3 sentinel, later | 0 / 1 / 4 | 0 / 0 / 0 | |
| visit | cascade (control) | d3 sentinel, who had it right | 0 / 2 / 3 | 0 / 1 / 1 | |
| visit | origin | d5 sentinel reports an empty watch | 0 / 3 / 3 | 0 / 2 / 2 | |
| visit | origin | d6 vigilante clears a player on that watch | 5 / 0 / 0 | 4 / 0 / 0 | |
| visit | cascade (control) | d6 speculator, who had it right | 0 / 3 / 3 | 0 / 0 / 0 | |
| repeat | cascade | d3 sentinel, third telling | 0 / 5 / 5 | 0 / 5 / 5 | |
| repeat | cascade | d3 sentinel, fourth telling | 0 / 5 / 5 | 0 / 5 / 5 | |
| repeat | cascade | d3 investigator, asked again | 0 / 4 / 4 | 0 / 2 / 2 | |
| repeat | origin | d3 illusionist re-asks an answered question | 0 / 4 / 4 | 0 / 5 / 5 | |
| repeat | cascade | d3 illusionist re-asks again | 0 / 5 / 5 | 0 / 4 / 4 | |
| repeat | cascade | d6 speculator restates its night | 0 / 4 / 4 | 0 / 2 / 2 | |
| vote_reason | cascade | d3 sigilist | 5 / 0 / 4 | 5 / 0 / 5 | 2 / 3 / 5 |
| vote_reason | cascade | d3 healer | 5 / 0 / 4 | 5 / 0 / 4 | 3 / 2 / 4 |
| vote_reason | origin | d4 vigilante | 4 / 0 / 0 | 3 / 1 / 1 | 2 / 0 / 0 |
| vote_reason | origin | d4 healer | 5 / 0 / 1 | 5 / 0 / 1 | 4 / 0 / 0 |
| vote_reason | cascade | d5 vigilante | 5 / 0 / 0 | 5 / 0 / 0 | 5 / 0 / 0 |

Totals. Visit, public messages bad: 16 of 35 before, 5 after (origin 5 → 2 of 15, cascade 11 → 3 of 20).
Repeat: 27 of 30 → 23 of 30. Vote reason, passes: 24 of 25 before, 23 after v1, 16 after v2. The
vote_reason turns' violations are almost all the day 3 visit misreading in private reads (a cascade),
not the vote line; v2's day 3 messages say it aloud. Every visit sample was also read by hand before the
verdicts came back (about 19 → 6 bad messages); one judge verdict read in the vote_reason output was wrong
(it called "the Illusionist was revealed as a wolf" false).
