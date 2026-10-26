# Deterministic evaluation: checks done by code

This page covers evaluation done by code alone, with no AI model and no human reader: why the project
uses it, where, and how far it can be trusted. How it fits with the other ways the project evaluates
(LLM judges, human reads, golden labels) is in [the hub](../report.md). Each case below shows its
approach, not every detail; the full detail of the checks this folder owns is in
[the detailed record](experiment_log.md), and the rest is in the report linked from each case.

## Why deterministic evaluation

A code check compares an output with an answer the code can work out for itself: from the game record,
from the rules, or from a fixed list of allowed values. When such an answer exists, code beats the
other two ways of judging an output.

| | Code check | LLM judge | Human read |
|---|---|---|---|
| **Cost** | Free | Paid per item | The owner's time |
| **Speed** | Instant | Seconds per item | Minutes per item |
| **Coverage** | Every item | Every item, at a price | A sample |
| **Same answer every run** | Yes | No: answers vary run to run | No: readers tire and drift |
| **Exact when** | The answer can be computed: a field, a count, a rule | Never fully | It is the reference for meaning |
| **Fails at** | Meaning, rewording, rules nobody wrote down | Bias, and it needs checking against people | Volume |
| **How it fails** | Silently: a check fed no input still passes | Confidently wrong | Inconsistently |
| **Can do what the others can't** | Search every possibility (every deal of roles) | Read meaning at scale | Set the standard the others are checked against |

So the rule the project follows is: **use code wherever the answer can be computed, and a reader only
for meaning.** Two things follow from the table's "how it fails" row. A code check needs its own test
(plant a fault and require a catch), because a check that never fires looks the same as one that passes.
And a code check can only be as wide as the rule someone wrote, so each case below says what it leaves
out.

## Where the project uses it

Every code-only check in the project. The five cases after this table are the ones whose approach
differs; the other checks follow one of those approaches and are detailed in their own reports.

The **Case** column says which approach a check uses: **1** check every output against a rule ·
**2** compare with independent test code that works out the right answer · **3** score a model's
structured output against the true value · **4** code narrows, then a reader judges · **5** guard the
experiment's own setup.

| Check | What it checks | Result | Trust | Case | Detail |
|---|---|---|---|---|---|
| Leak checks after every batch game | Every prompt input a player received, against the true roles: wolf names reach only wolves, night results only their owner, dead players get no prompt | The first run (June 2026) caught 109 leaks from a code change; 0 since the fix | ✅ | 1 | log §1a |
| Leak tests on the code that builds prompts | Unit tests build each player's prompt inputs and confirm each secret reaches only its owner; each test also plants a leak to prove the check catches it | All pass | ✅ | 1 | log §1b |
| Leak audit for games on the website | The same checks as the first row, run over games played on the live site | Built and tested, never run: the nightly job was never installed | 🟡 | 1 | log §1c |
| Tests of what each player is told | Each player gets an accurate private record of its own night actions, and past days in a fixed order (game record, then claims, then summaries) | All pass; added after agents cited private facts as public (October 2026) | ✅ | 1 | log §1d |
| Deduction engine: truth tests | Every conclusion the engine writes into a prompt (e.g. "player_7 must be the Chanteuse"), against the true roles in random games and against every deal of roles the player's knowledge allows | No false conclusion in 20,000 random nights per test | ✅ | 2 | log §2a–b |
| Deduction engine: four real failures | Four turns where players reasoned wrong in real games: the engine must write the right conclusions and none of the tempting false ones | All four pass; the only test of what the engine misses | 🟡 | 2 | log §2c |
| Deduction engine: impossible-role count | The engine's fast way of listing each player's possible roles never keeps a role a full search rules out | 0 such cases in 150 random games (3,408 player views) | ✅ (one run) | 2 | log §2d |
| Deduction engine: prompt length | How much text the engine adds to each prompt | Median 1,199 characters over 278 saved turns | 🟡 (before later changes) | 2 | log §2e |
| Memory search filters, recomputed | When a player asks memory for help, a model fills fields (players alive, bullets left, swing vote) that search filters lessons by; code recomputes each from the game state | Players alive right 97% of the time, bullets left 16%; these fields are now computed by code | ✅ (record, July 2026) | 3 | log §5a–b |
| Stored uses-left count, recomputed | Observations written after a game state how many uses of a limited ability were left; code replays the game's nights to get the true count | 84% exact (196 observations); 89% after the definition was reworded (527) | 🟡 | 3 | log §5c |
| Verdict halo | Whether the extraction model's verdict on a play (positive or negative) follows the decision's grade or just whether the player's side won | The verdict follows the win about twice as strongly as the grade (1,472 observations) | 🟡 (the grade itself is not validated) | 3 | log §5d |
| Vote accuracy | Whether each vote named a real threat (a wolf or the lone killer), from the true roles | The score used for every replayed vote | ✅ as a count | 3 | [metrics log](../metrics/experiment_log.md) B3 |
| Ten-seat metrics and decision grades | Each game's scores rebuilt from its night record, and each decision graded good, neutral or bad by the owner's table | Exact counts; hand-checked on one pilot game; grades reached 1,711 of 2,277 observations | ⚠️ (grades never tested against win as a whole) | 3 | [metrics](../metrics/report.md) §6 |
| Check of each score against winning (ten-seat) | Whether each score goes with its side's win, over 78 ten-seat games, within batch and with memory off | Lynch scores, power roles lost at night and wolf blending carry over; the healer save rate does not; most new roles' scores need more games | 🟡 (one run, mixed models) | — | [metrics](../metrics/report.md) §4 |
| Duplicate-filter scoring | Whether memory's duplicate filter kept, dropped or merged each lesson the way a human labeller did | The best setup matched 99 of 111 human decisions (89%) | 🟡 | 3 | [labeling](../labeling/dedup.md) |
| Factual-error pre-screen | Code finds every statement that mentions a dead player, a role whose holders are all dead, or a player count, so a model reader can check those | Passed 2,461 of 7,846 statements to the reader; about 3% of public messages had an error | ✅ within its scope | 4 | [factual_errors](../factual_errors/report.md), Case 1 |
| Memory-setup guard ("arm guard") | In a memory-on vs memory-off experiment, each side really ran the memory setup it declared; the run stops if not | Added after a run gave memory to every side by mistake; held in the July run | ✅ | 5 | [experimental controls](../experimental_controls/report.md) |
| Run-stamp check ("fingerprint") | Model, backend, prompt version and commit do not change partway through a learning-loop run | Stops the run on any change | ✅ | 5 | [experimental controls](../experimental_controls/report.md) |
| Embedding-model check | The embedding model behind memory search has not changed without notice: 12 fixed text pairs must score as pinned | Never seen to fire; runs in batches, not on the live site | ✅ | 5 | log §4 |
| Same-deal test ("seedability") | A game id always deals the same roles to the same seats, so both sides of an experiment can play the same deals | Passes | ✅ | 5 | [experimental controls](../experimental_controls/report.md) |
| Prompt snapshot ("prompt golden") | The day-discussion prompt renders exactly as stored, so it cannot change by accident | Passes; covers this one prompt only | 🟡 | 5 | [experimental controls](../experimental_controls/report.md) |
| New-model format checks | A candidate model returns replies the game can parse, on short test prompts and on real turns | Caught DeepSeek V4 Pro: passed 27 of 27 test prompts, answered 3 of 6 real turns in plain text | 🟡 | 5 | [model_admission](../model_admission/report.md) §2 |
| Speaking-order audit (nine-seat) | From saved games: did the rule that picks who speaks next keep any role from talking | No; investigators with news spoke before the vote on 58 of 58 days | 🟡 | 3 | log §3a |
| Failed-attack audit (nine-seat) | From saved games: when an attack on the night-immune serial killer failed, did the attacker act on it the next day | Only when told: the vigilante did on 6 of 8 and 8 of 9; the wolves, not told, ignored it in 45 of 66 notes. Wolves are now told | 🟡 | 3 | log §3b |
| Do-or-die turn flags (nine-seat) | A rule marking critical turns (wolves near parity, four or fewer alive) to point the lesson writer at them | Did not help: 3 of 12 turns captured with or without the flags | ⚠️ | — | log §3c |

"log" is [the detailed record](experiment_log.md).

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only.

---

## Case 1. Audit every output against a rule: the leak checks

**What and why.** Werewolf only works if each player knows what its role allows and nothing more. If a
villager's prompt contains the wolves' names, the game is not harder or easier. It is void.

**Why code.** Whether a prompt leaks is already in the data: who owns which secret, and which prompt
went to whom. So code checks every prompt, exactly and at no cost. A judge reading thousands of prompts
per game would cost money and could miss one; a sample would probably miss a rare leak.

**How it works.** Every prompt is built from a *payload*, the bundle of fields one player is handed, and
only that step filters what a player receives. So the checks sit there, at four points:
- after every batch game, nine checks read every logged prompt input against the true roles, and one
  leak fails the batch;
- unit tests build every payload with the real builders, check each private field's audience, and plant
  a leak to require the check to catch it;
- tests pin what each player is told about its own night actions and the past days, after an October
  fix;
- an audit runs the same checks over games saved from the live site.

**Result.** The first run, on 2026-06-06, caught 109 leaks: a refactor had handed every player
everything.

```
LEAK: player_2 (healer) received surviving_wolves: player_4, player_5
LEAK: player_9 (investigator) received surviving_wolves: player_4, player_5
```

The leaked fields never reached the final prompt text, so no game result was affected. After the fix the
count was 0. The checks have needed checking too: four false alarms each led to a narrower rule, and on
2026-10-14 three checks were found to have been checking nothing on live games, because the runner never
passed them their inputs. Fixed the same day.

**How far to trust it.** ✅ for what it encodes. It cannot see:
- a reworded leak (the free-text check matches exact wording; this is where a judge would help);
- memory: nothing checks that the lesson store served matches the player's role;
- two prompts that are never logged, and the final prompt text;
- website games: the nightly audit was found not installed on 2026-10-23, so none has been checked.

**Code and data.** `tests/leak_test.py`, `tests/engine/test_*_payload_leaks.py`,
`server/housekeeping/leak_audit.py`; [agent_boundaries](../../agent_boundaries/report.md) §3–5.

## Case 2. Test against an independent oracle: the deduction engine

**What and why.** The deduction engine writes conclusions into each player's prompt, such as "player_7
must be the Chanteuse". Players take those lines on trust (in replays of one turn, 10 out of 10 copied
the line into their notes), so one false "certain" line would mislead every game where it fires.

**Why code.** Proving a conclusion is certain means trying every way the roles could have been dealt,
given what the player knows. LLMs cannot do that search reliably; the players kept getting it wrong,
which is why the engine exists. Code tries every deal.

**How it works.** An *oracle* is separate test code that works out the right answer from the rules, so
the engine's answer can be compared with it.
- **Random games:** deal a random cast, play random legal moves, resolve the night with the real engine,
  and check every line against the true roles. 20,000 nights per test, and every kind of line must fire
  at least once, so none passes by never appearing.
- **Exhaustive check:** list every deal of roles that fits what a player knows; every "certain" line
  must hold in all of them. Over 8,000 player views.
- **No peeking:** swapping other players' hidden roles must leave a player's lines unchanged.
- **Four real failure cases:** turns from real games where players reasoned wrong, with the sentences
  the engine must and must not write. These are the only test of what the engine fails to say.
- **Tests of the tests:** rules were broken on purpose as each part was built, and the random games
  caught every one.

**Result.** No false line in any run. The engine's quick solver never kept an impossible role on 150
random games (3,408 player views). All four failure cases pass.

**How far to trust it.** ✅ for soundness within what was tested: no line contradicted the oracle in
the runs and the four failure cases above. 🟡 for coverage, which rests on four
cases. The oracle and the engine share the same written rules, so a rule misread the same way in both
passes.

**Code and data.** `tests/engine/deduction/`, `tests/factories/random_nights.py`,
`role_assignments.py`; [reasoning_failures](../../gameplay/deduction/report.md) §1, §3.

## Case 3. Score a model's structured output against the truth: the memory search filters

**What and why.** When a player asks its memory for help during a game, a model first summarises the
player's situation and fills in a few fields: players alive, the vigilante's bullets left, whether this
is a swing vote. Memory search used those fields as metadata filters on the stored lessons. If a field
was wrong, the search filtered on the wrong value. (Stored lessons carry the same kind of fields,
written at extraction; one of them, the uses-left count, was checked the same way: 84% exact. See
the detailed record §5c.)

**Why code.** The true values are in the game record. Code can recompute every one and compare, across
thousands of cases, for free.

**How it works.** For every recorded search (nine-seat, July 2026), recompute each field from the game
state and compare it with what the model wrote. A rule was fixed before the run: if any field the
filter relied on scored under 80%, the earlier result "this filtering doesn't help" would be reopened.

**Result.** The model got the values it was handed right and the values it had to work out wrong.
Players alive was right 97% of the time (6,099 cases); bullets left 16% (1,109); the wolves' "swing
vote" 61% (439), worse than always answering "no" (83%). The rule fired, and the design changed: these
fields are now computed by code instead of asked of the model.

The same approach scores votes (did a vote land on a real threat, against the true roles) and duplicate
decisions (against a human answer key). Wherever a model's output is a closed choice, code scores it.

**How far to trust it.** ✅ as a record. The counts are decisions, not games, so cases within one game
are related. The audit's own input had a bug first (176 cases with an empty roster), caught and fixed
before the result was read.

**Code and data.** `evaluation/src/instrument_validation/dimensions/dimension_audit.py`; detail in
[the detailed record](experiment_log.md) §5.

## Case 4. Let code narrow, then a reader judge: the factual-error screen

**What and why.** Agents sometimes state things the game record contradicts: hunting "the last wolf"
when both wolves are dead, or citing a check they never made. Measuring how often means reading every
statement, which is too much to do by hand.

**Why code first.** Whether a statement is wrong is a question of meaning, so a reader has to decide.
But whether a statement *could* be wrong is often mechanical: players and roles come from closed lists.
Code can find every statement that names a dead player, a role whose holders are all dead, or a wrong
count, so nothing in that scope is skipped.

**How it works.** Code flags candidates and drops only what it can prove fine. A cheap model reads every
candidate against a fact sheet built from the record, set to catch too much; a stronger model re-reads
its positives; the owner checks the result, including a sample of what was rejected.

**Result.** Code passed 2,461 of 7,846 units to the reader. About 3% of public messages carried an
error (68 of 2,292, nine-seat, July 2026). In the rejected sample, 2 to 3 of 15 were real errors, so the
counts are floors.

**How far to trust it.** ✅ for the screen within its scope. An error that names nothing ("the guy we
lynched") is outside it by design. Its role list is the nine-seat game's, so it has not run on the
ten-seat game.

**Code and data.** `evaluation/src/audits/role_hallucination_screen.py`; detail in
[factual_errors](../factual_errors/report.md), Case 1.

## Case 5. Guard the experiment itself: arm guard, embedding check, prompt golden

**What and why.** An experiment can be wrong before any output is judged: one side runs the wrong setup,
a provider changes a model under the same name, or a prompt changes by accident. Each of these
happened.

**Why code.** Each is a fact about the run's own setup, so it can be asserted before or during the run,
and the run can stop before it spends money.

**How it works.**
- **Arm guard.** One June memory run gave memory to every side while it was believed to be town-only, so
  its "control" was really a treatment. Now the run reads each side's actual memory setting and stops if
  it differs from the declared one.
- **Fingerprint check.** Every game is stamped with the model, backend, prompt hash and commit; a change
  within one loop run stops it.
- **Embedding check.** At the start of every batch, 12 fixed text pairs are embedded and compared with
  pinned values; a move over 0.02 stops the run.
- **Seedability and prompt golden.** A game id must reproduce its deal, and the day-discussion prompt
  must render byte for byte as stored, or a test fails.
- **Admission format checks.** A candidate model must return turns the game can use, on real turns as
  well as short probes.

**Result.** The arm guard held in the July pre-registered run. The admission check caught a model that
passed all 27 short probes but answered 3 of 6 real turns in prose; real-turn failures now count in its
verdict.

**How far to trust it.** ✅ where the check is code-enforced. Two caveats: comparing runs across days
is still a manual step, and the prompt golden covers only the day-discussion prompt. The embedding
check never runs on the live site.

**Code and data.** `evaluation/src/loop/invariants.py`, `Agents/run_fingerprint.py`,
`evaluation/src/audits/embedding_canary.py`, `tests/engine/test_seedability.py`; detail in
[experimental controls](../experimental_controls/report.md) and [model_admission](../model_admission/report.md).

---

## How they run, and what would make them stronger

The leak checks and the embedding check run automatically in every batch. Everything else is a test or
a script someone has to run, because the repository has no CI. On 2026-10-23 every test named here
passed. The tests are largely AI-written and not yet audited, so this page names specific tests and
what each asserts, never a test count.

On the owner's pending list in [`writeup/map.md`](../../../writeup/map.md):
- **Install the nightly leak-audit cron**, so website games are checked. It changes the host, so it
  needs the owner's yes.
- **Add CI** that runs these tests on every change. None of them calls a model.

Also open, with no plan: a check that the memory store served matches the player's role.

**Bottom line.** These are the most trustworthy checks in the project, but each finds only what someone
wrote it to look for.

*Written 2026-10-23 and checked against the working tree on `feature-frontend-v1`. Which commit each
count ran on is in the full evaluation ledger ([experiment log](../experiment_log.md), Part 2); which files are not
in git, in [the source map](../source_map.md).*
