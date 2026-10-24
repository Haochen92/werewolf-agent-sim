# Evaluation scopes: one turn, one day, one game

The project tests a change by running the same controlled experiment at three scopes: one frozen turn, one
replayed day, or whole games. The experiment is always the same: hold everything fixed except the change,
run both versions side by side, and compare. What changes with the scope is how much is held fixed, and so
what the test can see, what it costs and how many samples it needs.

In software terms the three are **unit, integration and end-to-end tests**. A frozen turn isolates one
decision with its inputs fixed, as a unit test isolates one component. A replayed day lets the parts that
react to each other inside a day (the speaking order, the other players, the votes) play live. Whole games
run the system as it really runs. One difference from software tests: these are statistical, not pass/fail.
The same input is sampled many times and versions are compared by rate, because a model's answer varies.
The usual name in agent evaluation is a **turn-level** (or step-level) eval, against an end-to-end
(trajectory) eval.

| Scope | What is held fixed | What it can show | Cost | Samples needed | State |
|---|---|---|---|---|---|
| **[Turn](turn/report.md)** (unit) | Everything up to one turn: the board, the transcript, the seat's private record and memory | Whether a change reaches a decision, and which way it pushes | Under $0.01 to about $0.25 a screen | Tens of samples per arm, with a noise floor | Built; 14 screens, June–October 2026 |
| **Day** (integration) | The earlier days; the chosen day plays live | Effects that build within a day: more talk, replies to a claim, an abstain cascade | About $0.10–0.15 a day; a 30-pair campaign about $10–17 | 30 pairs of days, after an acceptance gate | Designed July 2026, not built |
| **[Game](game/report.md)** (end-to-end) | Only the deal (and the code, model and time window) | Outcomes (who wins, balance), effects that cascade across days, and the system running for real | About $0.08–0.26 a ten-seat game on Haiku; $15–30 for a June 30-game arm | 30 games a side detect only a win gap of about 35 points | Built; three memory A/Bs (nine-seat) and two October smoke runs (ten-seat) |

**Why the smaller scopes need fewer samples.** In a whole game the change touches a few decisions and
everything else (the deal, every other player's moves, how each day unfolds) varies around it, and the two
games part ways at the first line that differs. That noise buries a small effect. A frozen turn holds all
of it fixed, so the only spread left is the model's own sampling, and each sample is one call.

**When to move up a scope.** Start at the turn. Move up only when:
1. the question is an outcome over a game, such as who wins or whether the sides stay balanced;
2. the effect builds across turns: a lesson used on day 1 changes who is alive on day 3, or a change makes
   players talk more and so gives everyone more to read;
3. a new feature has to be shown running in the real game loop: no crashes, the leak check passing, the
   real cost per game.

**What each scope cannot see.** A turn cannot see what a change does later in the day, because the frozen
history was produced without it (the turn page's examples: an abstain cascade, replies to a denial already
in the transcript). A game cannot say why something changed, and at the sizes run here it gives a direction
for wins, not an estimate. The missing day scope is the gap the October screens kept hitting.

**The same controls apply at every scope**: both versions in one time window, one change per arm, one judge
scoring both, a noise floor before reading an effect. They are in
[experimental controls](../experimental_controls/report.md). Replays scored for factual errors are in
[factual_errors](../factual_errors/report.md); replays used to choose a model in
[model_admission](../model_admission/report.md).

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Build the day scope, starting with its acceptance gate** | Designed in July 2026, never built | Effects within a day measured without the noise of whole games |
| Design | **2. Choose the scope from the question before running** | The October voices question ran as whole games; turn replays answered it more cleanly | Each question asked at the cheapest scope that can see its effect |
| Analysis | **3. Report a noise floor at every scope** | Done in a few turn screens; whole games relied on paired tests | Every effect read against its own scope's noise |

**Bottom line.** One experiment at three scopes. The turn scope is the project's workhorse, cheap and
sharp for one decision; whole games are the only way to see outcomes and cascades, and are expensive and
noisy; the day scope between them is designed and still missing.

*Created 2026-10-24, when `replay_screens/` became [`turn/`](turn/report.md) and `whole_game_evaluation/`
became [`game/`](game/report.md); each keeps its own report and experiment log.*
