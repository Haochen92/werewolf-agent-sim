# Stage fit: does the model keep ahead of the stage? (2026-10-24)

**The question.** The server never waits for the stage: it runs ahead, and the browser plays each beat at
its full hold (a speech line at 2.4 words a second for 5 to 15 s, a pass 4 s, a verdict 6 s;
`src/stage/beats/beatsFor.ts`). A model call is fast enough when its event has arrived before the stage
reaches it. When it has not, the stage stands with nothing to play. How often does that happen on the
models players can choose, and where?

**The answer.** On Claude Haiku 5.5, the default seat model, the stage would have waited for the model
**2.7–5.1% of its playing time** (252–471 s over 9,260 s of stage, seven games). Most of the waiting comes
in runs of passes, where a pass shows for 4 s but the next seat still takes a full call. DeepSeek V4.1 Flash,
about twice as fast, kept ahead almost always (0.1–0.3%).

This replaces the one earlier measurement, by hand on a flash-lite game (`../live_timing_sheet.md`,
2026-10-01), with a measurement that can be rerun on any served game. [2026-10-26: it replaces
that game's per-call latencies only; it measures the waits, not the lag, so the timing sheet's lag
figures are still the flash-lite game's.]

## How it was measured

For every completed served game since 2026-10-11 (`evaluation/experiments/stage_fit.py`, no model calls):

1. **The beats.** The game's event log is cut into the beats its seated human's live stage would play, by
   the stage's own cutter (`../../scripts/beats-for-log.ts`: `beatsFor`, xray off, the human as `me`, live).
2. **When each event left the server**, from the game's Langfuse trace. A seat's speech or pass is matched
   to its `day_channel_<seat>` span, a vote to `day_votes_<seat>`, a pack line to `wolf_channel_<seat>`, a
   night action to its role's target span (only where the counts agree), and the night result, lynch
   result and day summary to their own nodes. A round's lines and a day's votes leave together, when the
   round or vote is collected. Every other event leaves with the one before it.
3. **When the human acted.** Each action resumes the engine as a new run nested under the game's run.
4. **The stage.** Each beat starts at the later of the stage being free and its last needed event having
   arrived. Time the engine spent waiting for the human is the human's, not the model's, and is left out.

Two readings bound the result:
- **restart:** at each human action the stage starts afresh from the action (a solo prompt waits for the
  stage, so the stage is at the prompt when the human acts);
- **continuous:** the simulated stage's own backlog is carried on. In several games the simulated stage
  ran behind the real one (the human acted before it reached the prompt, by up to a few minutes), most
  likely from page reloads, which jump the stage to the latest beat; a stage that runs behind hides waits.

## What it found

**Seconds per model call**, from the traces (all games since 2026-10-11):

| Call | Haiku 5.5: median | slowest 5% | worst | DeepSeek V4.1 Flash: median | slowest 5% |
|---|---|---|---|---|---|
| Discussion turn | 5.4 | 10.8 | 16.6 | 3.5 | 4.5 |
| Opening or closing round turn | 4.1 | 7.1 | 11.7 | 2.7 | 3.8 |
| Vote | 6.1 | 10.6 | 14.5 | 3.5 | 4.4 |
| Night role (each) | 3–8 | 6–11.5 | 18.3 | 2.5–3.5 | 3.5–4.2 |
| Pack chat line | 3.1 | 5.3 | 6.6 | 2.8 | 3.6 |
| Day summary | 11.1 | 26.8 | 30.0 | 2.0 | 5.1 |

Gemini 3.5 Flash-Lite (one game) and GPT-6 Luna (two games) are close to Haiku: a discussion turn at 5.2
and 6.4 s median.

**How much of the stage's playing time it waited** (games with a human; the AI-only game never waits, its
stage only falls further behind):

| Model | Games | Stage time | Waiting |
|---|---|---|---|
| Claude Haiku 5.5 | 7 | 9,260 s | 252–471 s (2.7–5.1%) |
| DeepSeek V4.1 Flash | 3 | 3,628 s | 4–10 s (0.1–0.3%) |
| GPT-6 Luna | 2 | 1,742 s | 36–93 s (2.1–5.3%) |
| Gemini 3.5 Flash-Lite | 1 | 1,139 s | 41–46 s (3.6–4.1%) |

**Where Haiku makes it wait** (restart reading):

| Beat | Waits | Seconds | Longest | Why |
|---|---|---|---|---|
| A pass, or a run of passes | 21 | 270 | 25 s | A pass shows for 4 s; the next seat's call takes 5.4 s median, whether it speaks or passes |
| The morning shutter, after a night | 8 | 117 | 29 s | The other roles decide in parallel in 3–4 s, but the pack's chain runs one step after another: its chat lines (about 3 s each, six on night 1), then the carrier's kill, then the pack's skills, about 24 s on night 1, longer than what the stage shows at night |
| A speech | 27 | 74 | 11 s | A line shows for 5–15 s plus a 2 s "thinking" beat, so most turns fit |
| Votes | 3 | 9 | 7 s | Ballots are written in parallel, behind the vote's own beats |

## The latency each phase can afford (provisional)

| Phase | What the stage gives the next call | Haiku today | Provisional limit |
|---|---|---|---|
| Discussion, after a pass | 4 s (the pass hold) | 5.4 s median: waits | Median at or under 4 s for no waits; at or under today's 5.4 s median and 11 s slowest 5% not to be worse than the default |
| Discussion, after a speech | 5–15 s (the line's hold) plus 2 s | 10.8 s slowest 5%: mostly fits | Slowest 5% at or under 11 s |
| Votes | the vote's opening beats, with all ballots written at once | 10.6 s slowest 5%: rarely waits | Slowest 5% at or under 11 s |
| Night | what the stage shows at night, against the pack's chain (chat lines, kill, skills) one after another | 15–30 s waits at the morning | The pack's chain added up must fit the night's display; not yet a per-call limit |

These are provisional: seven games, all played by the owner while building, on today's beat holds (games
played before a hold changed would have looked slightly different), with the human's action times read from
the trace. The pass and night waits could also be closed on the stage instead of with a faster model,
by holding passes a little longer or showing the seats deciding, or by shortening or overlapping the pack's chain at night;
that is a product choice and is not made here.

## Files

- `results.json`: every game's waits, the pooled figures, the waits by beat, and every node's latency.
- Runner: `evaluation/experiments/stage_fit.py`; beat cutter wrapper: `../../scripts/beats-for-log.ts`.
- Raw events and traces are cached, gitignored, in `evaluation/eval_results/stage_fit/`.
- Left out: game 51226f24 (GPT-6 Luna), whose trace's resumes could not be read (the simulation stopped
  after 52 s).

    poetry run python -m evaluation.experiments.stage_fit --since 2026-10-11 --exclude 51226f24 \
        --out frontend/docs/stage_fit/results.json
