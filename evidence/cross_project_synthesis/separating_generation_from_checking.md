# Separating generation from checking

**The lesson.** Where the call that produced something had an incentive or an information advantage that
could distort its own judgment, the judgment was moved out of it. What replaced it differed with the
problem: a second model reviewing outcome-driven verdicts, a detector denied the hidden roles, and a
separate check on a finished message for repetition. These are different interventions, and none
guarantees independence or correctness on its own; each check had failures of its own and needed its
own validation.

Recorded 2026-10-13, from a review of the write-up plan.

## The interventions, kept apart

| Instance | The generator's problem | Separate call | Different model | Information withheld | Code decides |
|---|---|---|---|---|---|
| Extraction de-halo | Knows the outcome; verdicts follow the side's win | Yes | Yes (Haiku 5.5 after Gemini extraction) | No: it also sees the game | No |
| Tell detection | Mining knows every role, so its counts are coloured by them | Yes | No (same Flash-Lite) | Yes: no roles | Role join is a lookup |
| Discussion echo gate | An agent judging its own point's novelty is biased | Yes | No (the game's model) | No: it sees the day's lines | Yes: the hold rule and exemptions |

## 1. Memory extraction: the de-halo pass

**Problem.** The extraction judge reads the whole game, ending included, and gives each observation a
`net_verdict`. Measured against the deterministic grade of each observation's own decision (1,472
observations, 40 ten-seat games), the verdict's weight on the side having won is +0.80 and on the
decision's grade +0.40 (`memory_system/v8/decisions.md` §13). The verdict reaches synthesis, dedup and
the replay's verdict stamp.

**Check.** A second call by a different model (Claude Haiku 5.5 by default) re-reads each verdict
against the game record and rewrites unsupported ones to "unclear", or flips them
(`Agents/memory/extraction/dehalo.py:1-11`, `Agents/memory/persistence/config.py:73`). The originals are
kept.

**Result.** It removes about a third of the halo, on one side only: weight on the side won +0.80 → +0.53
(grade +0.40 → +0.36). At the role level (482 observations, 19 games): +0.74 → +0.50. Losing sides'
negatives fall from 53% to 27%; winning sides' positives barely move, 57% → 54%.

**Not fixed.** Most of the halo remains, and the pass rewrites only the verdict word, not the judge's
effect text. The reviewer also sees the outcome, so a different model is not independent information.
That is a likely reason it does so little, though not tested. The structural answer came later:
each observation now names its decision, which gets a deterministic grade; synthesis can read either the
verdict or the grade (a config setting; which writes better lessons is unmeasured).

**Live.** De-halo runs in offline extraction; both outcome signals are stored.

## 2. Tell extraction: mining and detection

**Problem.** A tell is a behaviour-to-role statistic ("a player who counter-accuses their accuser of
using a role claim as a distraction turned out evil 27 of 30 times"). Mining discovers candidate tells
with the whole game and the roles in view, so what it notices and how often it notices it is coloured
by who turned out to be what. Its rows cannot supply the counts.

**Check.** A separate detection pass scans each game against a frozen checklist without the roles. It
names the exhibitor's seat, never a role; the role join is a deterministic lookup. Only detection rows
feed the counts (`store_curation/tells.md:17-20, 37-39`). Same model as mining.

**Result.** Detector golden, N=40: discussion precision 0.93, day recall 87%; votes 0.77 and 77%
(`store_curation/tells.md:273`). The mined tells held up on 60 held-out games (12 paired boards × 5
arms, so the effective n is between 12 and 60).

**Not fixed.** A single cheap-model detection pass was unstable; it needed two runs per game, unioned
(`extraction/tell_extraction/experiment_log.md`, version at `2382b34c`, §13–16). Whether the injected book improved play was
never separated: the v7 endpoint run bundled it with the strategy lessons.

**Live.** No. Nine-seat era; not ported to ten seats; the book is off in the deployed game.

## 3. Discussion: the echo gate

**Problem.** Agents repeated points already made. The first design asked each agent to label its own
point's novelty inside its own call, which costs nothing extra. As a standalone judge on a fixed outside
candidate the label separated cleanly (20/20 on both polar sets). Asked of the agent's own point it
failed both ways: framed against the situation it called almost everything repeated, framed against its
contribution almost everything new ("self-authorship optimism")
(`sequential_discussion/experiment_log.md:289-307`).

**Check.** After the line is written, a separate call with the game's own model, at minimal thinking,
states the line's point and what it adds, and may name a repeated line only when it adds nothing. Code
holds the line only on that pair, checks that the named line was really spoken, and skips the gate for
human seats and for replies to a player who named the speaker. Proactive turns only; it fails open
(`Agents/turn/echo_gate.py:70-109`, `Agents/turn/resolve.py:127-155`).

**Result.** On 146 offline lines the shipped prompt held 27 (18%), down from 43 (29%) for the first
form; by hand about half the holds are clear repeats
(`game_play_enhancement/data/line_echo_check/README.md:16-34`). In four live games (2026-10-07) it held
19 lines in the three games read by hand; about 12 were clear repeats
(`game_play_enhancement/data/phase2_step8_games/report.md:20-26`).

**Not fixed.** The judge errs toward holding: it reads crediting an earlier speaker as a repeat, which is
why code, not the judge's naming alone, decides. Once it held an accused villager's only defence, who
was then lynched without having spoken: the exemption for answering an accuser reads the speakers' own
accusation tags, whose errors run one way: of 183 messages, 24 tags missed an accusation a judge saw
and 1 named one it did not (`discussion_evidence.md:977-981`, §9 item 8). How many repeats it lets
through is unmeasured.

**Live.** Yes.

## What the three show together

- **A different model is not the same as independence.** De-halo uses a different model and stays
  mostly haloed, plausibly because it sees the same outcome. Detection uses the same model and works
  because the roles are withheld. The echo gate uses the same model and works because the judge did not
  write the line.
- **Each check is a new instrument with failures of its own.** The echo judge over-holds, and its
  exemption inherits the errors of the tags it reads; the detector needed an ensemble; de-halo is
  one-sided. Each needed its own validation, and all three remain only partly measured.
- **Where a rule could be code, it became code.** The echo hold rule and exemptions, the tell role join,
  and the deterministic decision grade next to the extraction verdict.

## Where it goes in the write-up

Each instance stays in its own segment: de-halo under memory extraction, detection under tells, the
echo gate under discussion. The engineering-lessons section gets one paragraph linking back to them.
Draft:

> Across the system, I separated generation from checking where the original call had an incentive or
> an information advantage that could distort its judgment. The check varied with the problem: a second
> model reviewing outcome-driven extraction verdicts, a detector denied the hidden roles when counting
> tells, and a separate check of each finished discussion line for repetition. These are different
> interventions, and none guarantees independence: the second model still sees the outcome and removes
> only a third of the halo, while the detector, on the same model, works because it never sees the roles.
