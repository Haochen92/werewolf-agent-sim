# Phase 3: the reasoning failures replayed (2026-10-10)

Ten discussion turns frozen from the captured ten-seat games (`cases.jsonl`, built by
`evaluation/experiments/phase3_turn_cases.py`): the game state just before the speaker spoke,
rebuilt from the game's record and chunks in the hallucination bench's case format. Eight are
turns that went wrong in the hand-read games (`../phase3_reads/`), two are controls where a player
reasoned correctly on the same evidence. Each case carries a hand-written expectation, and the
bench's golden judge (gemini-3.5-flash) reads every sample against it. Run by
`poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_phase3_turns.json`;
the full output is in `evaluation/eval_results/hallucination_bench/phase3_turns/`, the summary here
(`bench_summary.json`). Five samples per case and arm, memory off. A round turn is replayed as a
sweep turn (the bench rebuilds discussion turns only).

Arms: **flashlite_committed** (gemini-3.5-flash-lite on the code at 56b21471, from a worktree),
**flashlite_fixed** (flash-lite on the working tree: the claim-ledger and summariser fixes),
**flash_fixed** (gemini-3.5-flash on the working tree: the capability test).

Samples whose spoken message broke the expectation (a sample can also break it only in its private
strategy note or reads; those counts are in the bench output):

| Case | Kind | flash-lite, committed | flash-lite, fixed | flash, fixed |
|---|---|---|---|---|
| e04 d2 trailseer: a sighting taken as support for an investigator claim | positive | 3/5 | 2/5 | 0/5 |
| e04 d2 sentinel: the same evidence | control | 2/5 | 2/5 | 0/5 |
| d03 d3 investigator: "a watch and a protection prove my results" | positive | 0/5 | 0/5 | 0/5 |
| b02 d4 sentinel: an empty watch read as an empty house | positive | 0/5 | 0/5 | 0/5 |
| b02 d4 trailseer: an empty watch read as an empty house | positive | 2/5 | 3/5 | 0/5 |
| b02 d4 trailseer: an empty trail read as no night ability | positive | 1/5 | 1/5 | 0/5 |
| e04 d3 speculator: a necromancer using a body the night its owner died | positive | 1/5 | 0/5 | 1/5 |
| e04 d3 sentinel: the same timeline | control | 2/5 | 3/5 | 0/5 |
| e06 d3 sigilist: repeating the invented chanteuse claim | positive | 5/5 | 0/5 | 0/5 |
| e06 d3 investigator: accepting the invented claim about itself | positive | 5/5 | 0/5 | 0/5 |
| **Positives** | | **17/40** | **6/40** | **1/40** |
| **Controls** | | **4/10** | **5/10** | **0/10** |

## Reading

- **The claim-ledger fix ends the invented-claim chain.** On the committed code both e06 speakers
  repeated or accepted "player_2 claimed chanteuse" every time; on the fixed code neither did, in
  any sample, on either model.
- **The other errors are mostly model capability.** Flash-lite still takes a sighting as support
  for a role claim, reads an empty watch as an empty house, and gets the necromancer's timeline
  wrong, on the controls as often as on the positives: the original control lines were the lucky
  draws. gemini-3.5-flash makes one such error in fifty samples on identical prompts, so for
  these the prompt and context are adequate and the model is the limit.
- **Cost of the stronger model, per turn:** the same input (about 6,600 tokens), fewer output
  tokens (1,190 against 1,930, about half the reasoning), similar time (7.5 s against 8 s). The
  price per token is higher; the price table is in the memory note on Gemini models.
- **Judge check.** The verdicts were read by hand for every case before these counts were used.
  The first pass marked the e06 cases bad for a correct statement ("player_2 claimed
  investigator", true on day 3): the expectation had said "never claimed any role". The
  expectation was corrected and the samples re-judged. One remaining verdict is borderline (b02,
  a trailseer quoting the other player's "empty house" while arguing against it).

Ten cases and five samples: a regression set and a capability test, not a rate.
