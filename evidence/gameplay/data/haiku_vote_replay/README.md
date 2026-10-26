# The votes of the first Haiku 5.5 game, replayed (2026-10-16)

Eleven day votes frozen from the owner's live game `403f4dbc` (`cases.jsonl`, built by
`evaluation/experiments/haiku_vote_cases.py` from the game's LangGraph checkpoints on the server's Postgres,
read-only). Each case is the state at the vote fan-out: the day's whole discussion and no ballot yet.
Ten samples per case and arm on Claude Haiku 5.5 at effort low, memory off. Run by `poetry run
eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_vote_compare.json`. Full output is in
`evaluation/eval_results/hallucination_bench/haiku_vote_compare/`; `votes.jsonl` here has every sample's vote,
reads, note and golden verdicts, and `bench_summary_votes.json` the judge's summary. Record: `../../discussion_evidence.md` §8.7.

The question was whether one sentence in the shared rules block, asking that reads compare the living players,
would stop the day-5 vigilante from voting out the real sentinel ([haiku_sentinel_vote](../haiku_sentinel_vote/README.md)).

**Arms**, each a git worktree:

| Arm | Code |
|---|---|
| pre-fixes | 746197c4, before the October 12 fixes (the before arm of [haiku_turn_replay](../haiku_turn_replay/README.md)) |
| layout tag | 09af8272, tag `prompt-layout-baseline`: the October 12 fixes and reads-first, still the earlier prompt layout |
| current | 1757a49c, the shared-prefix layout (October 14) |
| compare | 1757a49c plus the sentence, appended to `REASONING_DISCIPLINE` in `Agents/prompts/common.py` |
| ballot tag | 1757a49c plus each ballot's target tagged with its revealed role, "voted to eliminate player_4 (revealed investigator, killed night 3)" (a `tag_ballot_targets` in `Agents/prompts/prompt_formatters.py`, not kept) |

Current and compare were the planned test. The first two were added after the current arm's day-4 votes came out
far below the original game's; ballot tag after that, and it is scored by vote only (`evaluation/experiments/haiku_vote_score.py`, no judge).

**Cases.** A vote is right if it names the actual threat: player_6 (illusionist) on day 3, player_1
(chanteuse) on day 4, and player_3 (Necromancer) on days 5 and 6.

- Day 5: the vigilante and the speculator (which had picked Town) voted out player_9, the real sentinel.
  The day-5 sentinel itself voted player_3 (control).
- Day 6: player_3 claimed sigilist for the first time, unchallenged; the real sigilist had died with its role
  hidden. The vigilante then voted out the speculator, and the speculator voted the vigilante.
- Controls: three town voters on day 3 (vigilante, healer, sentinel) and on day 4 (the same three). All voted
  right in the original game.

Votes right, out of 10 per case:

| Day | Voter | Original vote | pre-fixes | layout tag | current | compare | ballot tag |
|---|---|---|---|---|---|---|---|
| 5 | vigilante | player_9 | 4 (3 on player_9) | 3 (6 on player_9) | 7 (1 on player_9, 2 abstain) | 0 (3 on player_9, 6 abstain) | 4 (3 on player_9) |
| 5 | speculator | player_9 | 4 | 2 | 0 (10 abstain) | 0 (9 abstain) | 0 (10 abstain) |
| 5 | sentinel (control) | player_3 | 8 | 8 | 7 | 6 | 3 |
| 6 | vigilante | player_10 | 0 | 0 | 1 | 2 | 1 |
| 6 | speculator | player_2 | 0 | 0 | 0 | 0 | 0 |
| 3 | three town voters (controls) | player_6 | 30 of 30 | 30 of 30 | 30 of 30 | 28 of 30 (2 abstain) | 30 of 30 |
| 4 | vigilante (control) | player_1 | 10 | 6 | 6 | 7 | 2 (6 abstain) |
| 4 | healer (control) | player_1 | 5 | 4 | 3 | 3 | 1 |
| 4 | sentinel (control) | player_1 | 10 | 10 | 4 | 7 | 9 |

What the reads cite, counted per sample with a regex over the reads (a mention count, not a judgment of soundness):

| Count | pre-fixes | layout tag | current | compare | ballot tag |
|---|---|---|---|---|---|
| Day 4: the read of player_1 cites its day-3 vote on the investigator | 19 / 30 | 12 / 30 | 2 / 30 | 11 / 30 | 0 / 30 |
| Day 5 vigilante: the read of player_3 cites its day-4 abstain | 8 / 10 | 9 / 10 | 8 / 10 | 3 / 10 | 5 / 10 |
| Day 5 vigilante: the read of player_3 says nothing separates it from the others | 1 / 10 | 0 / 10 | 0 / 10 | 7 / 10 | 0 / 10 |
| Day 5 vigilante: the read of player_3 says it voted out player_4 (false; player_1 did) | 0 / 10 | 0 / 10 | 3 / 10 | 0 / 10 | 0 / 10 |
| Day 6 vigilante: reads player_3 as the sigilist | 10 / 10 | 10 / 10 | 7 / 10 | 8 / 10 | 9 / 10 |

Cost per vote sample (current → compare): reads 517 → 802 characters on average, output tokens 960 → 1,297,
input 8,931 → 9,048 (the sentence sits in the cached system block). On the 18 discussion turns of
haiku_turn_replay, five samples each (`hallucination_bench_haiku_game_compare.json`, `bench_summary_discussion.json`),
samples bad in any part were 48 of 90 on both arms (6 turns better, 5 worse, sign test p = 1.0), and output tokens
rose 1,155 → 1,281.

**Judge.** Claude Sonnet 5.5 read each sample's note and reads against the case's expectation, as one Message
Batch. Its verdicts are a fact guard here, not the measure. Day 3's flags (current 25 of 30 samples, compare 29
of 30) are the known day-3 visit misreading carried into private reads (§8.6). The day-4 expectation is
ambiguous: "player_5 was killed by a reanimated wolf with the role hidden" was read as hiding the attacker's
role, so a note saying the body was the illusionist was flagged. The morning announcement says exactly that
("Their role is hidden by a reanimated illusionist"), so the day-4 flags are false positives and are not used.
The discussion bench's `_D4_FACTS` expectation (haiku_turn_replay) has the same wording.

Limits: one game; a case's ten samples share one prompt, so they show the spread of the model's answers to that
prompt, not ten situations. The day-5 vigilante's votes on player_9 range from 1 to 6 of 10 across the three
arms without the sentence: too wide to credit any code change with fixing that ballot. Pooled counts over the
three day-4 voters treat their samples as independent.
