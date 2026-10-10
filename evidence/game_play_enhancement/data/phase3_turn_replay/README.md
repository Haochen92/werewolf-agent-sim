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

## The f02 rule: does stating it stop the misreading? (2026-10-10)

In f02 four players asserted that "the Illusionist's visit to hide a body is always seen by a Trailseer"
and voted out the real trailseer, whose empty trail on the illusionist was right (it had carried its own
kill). The owner then ruled such an illusionist invisible at that door, and a sentence saying so went
into the shared rules and the illusionist's card. Four day-4 turns were frozen (three that asserted the
false rule, and the trailseer's correct defence as a control) and replayed before and after the sentence
on both models (`evaluation/config/hallucination_bench_phase3_f02_rule.json`; before = a worktree at
fb193104), five samples each, judged against one expectation and read by hand
(`bench_summary_f02_rule.json`):

| Turn | flash before / after | flash-lite before / after |
|---|---|---|
| player_1, the first to assert the false rule | 1/5 → 0/5 | 1/5 → 1/5 |
| player_7, after it had been asserted several times | 5/5 → 4/5 | 5/5 → 5/5 |
| player_9, likewise | 5/5 → 3/5 | 5/5 → 5/5 |
| player_3, the trailseer (control) | 0/5 → 0/5 | 0/5 → 0/5 |

The first speaker seldom makes the error at all (the game drew a one-in-five); once the false rule has
been asserted a few times in the transcript, later speakers repeat it against the rules text in front of
them. The stated rule helps the stronger model a little and flash-lite not at all. Stating the rule
guards the origin of a misreading; it does not stop a cascade once one has started.

### A rule claim is a claim (2026-10-10)

The cascade turns test resistance to a confident false rule from peers, which a real game can produce
anyway (a misreading, or an evil seat lying about a rule; f02's necromancer was among the loudest). The
prompts already ranked the game master's record above anything a player says about events, but not the
rules above what a player says about rules. One line was added to the shared rules: "These rules are
exact. A player's statement of how a rule works is a claim like any other, and where it disagrees with
these rules, these rules are right." The same four turns, five samples each
(`evaluation/config/hallucination_bench_phase3_f02_hierarchy.json`, `bench_summary_f02_hierarchy.json`),
against the illusionist-sentence arms above:

| Turn | flash, sentence / + line | flash-lite, sentence / + line |
|---|---|---|
| player_1 (origin) | 0/5 → 1/5 | 1/5 → 0/5 |
| player_7 (cascade) | 4/5 → 3/5 | 5/5 → 5/5 |
| player_9 (cascade) | 3/5 → 1/5 | 5/5 → 5/5 |
| player_3 (control) | 0/5 → 0/5 | 0/5 → 0/5 |

On the stronger model the cascade turns went 10/10 with no rule sentence, 7/10 with it, 4/10 with the
line as well; one flash sigilist now argues the rule correctly against the table. Flash-lite repeats the
false rule every time under all three prompts. The origin and control changes are within noise.

## The sentinel's own visit (2026-10-10, from the Luna games)

The engine leaves a sentinel out of its own visitor list; the card said only "Watching is a visit". Four
turns from the Luna games were frozen (the two players who raised it and the two real sentinels who
conceded, l01 and l04 day 2) and replayed before and after the card gained "Watching is a visit, but the
Sentinel is not among the visitors it is told of: its own watch never appears in its result", five samples
each (`bench_summary_sentinel_before.json`, `_after.json`):

| Turn | Luna before / after | flash-lite before / after |
|---|---|---|
| l01 player_1, raising it | 0/5 → 0/5 | 0/5 → 0/5 |
| l01 player_3, the real sentinel | 5/5 → 0/5 | 0/5 → 0/5 |
| l04 player_5, raising it | 0/5 → 0/5 | 0/5 → 0/5 |
| l04 player_10, the real sentinel | 5/5 → 0/5 | 0/5 → 0/5 |

The raising turns seldom raise it at all on a replay (the games drew it), but once raised, the real Luna
sentinel conceded every time on the old card and never on the new one. Flash-lite did not concede in any
sample before or after: the gap was one a literal reader falls into.
