# Hallucination bench

> **What this is.** A standing benchmark for factual errors in what the agents say: a player
> claiming a check it never made, hunting "the last wolf" when both wolves are dead, calling a
> revealed wolf the serial killer. It replays frozen game turns under any prompt version or model
> and has a judge count the errors. Code: `eval-hallucination-bench` and
> `eval-build-hallucination-bench` (`evaluation/README.md`, *Hallucination bench*). Built 2026-10-03.

## Why

Two findings made a standing measurement necessary.

- **Errors are common, and a single one can decide a game.** The July census found role-fact errors
  in about 3% of public messages and 4% of private notes
  ([`generation_prompt/validation/`](../../generation_prompt/validation/hallucination_baseline.md)).
  In a live game on 2026-10-03, the investigator announced a check it never made, the village voted
  out an innocent player on that claim, and the serial killer won.
- **Replaying one turn finds the cause, but not how often it happens.** Replaying that investigator
  turn showed that the wording of its results caused the invented check: 20 of 20 samples on the old
  wording, 0 of 20 on the new one
  ([`game_play_enhancement/discussion_evidence.md`](../../game_play_enhancement/discussion_evidence.md) §6.2).
  Choosing a model, or checking that a prompt change doesn't bring old errors back, needs many such
  turns measured the same way every time.

The July ship test (T1c) did this once, as study code. The bench makes it a maintained tool.

## How it works

**A case is one agent turn frozen as the game state** the engine held when the agent spoke: the
transcript so far, earlier summaries, deaths and revealed roles, the agent's private results and its
previous note. Replay rebuilds the turn's inputs with the engine's own builders and renders today's
template, so the same case can be run under any prompt version or model. The prompt is never
stored, only the state.

**An arm is a model plus a prompt version.** Each arm runs in its own process, because prompt
versions are switches read when the code loads. Gemini, DeepSeek, NVIDIA-hosted models, OpenAI and
Grok are supported.

**Two judges, each told only what it needs.**
- Most cases use the July census reader. It checks each statement against a fact sheet built from
  the game record (deaths, roles still alive, votes, logged claims), so no expected answer has to be
  written by hand. A cheap model reads every statement that touches a checkable fact, and a stronger
  model re-reads its positives.
- Hand-picked cases carry a written expectation instead (for the investigator: the only checks it
  made). A narrow judge decides whether a statement breaks it.

**Cases are chosen by what still fails.** The pool is the 227 census turns confirmed wrong in July,
plus 40 turns judged correct as controls. Most July errors were one-off slips: a July replay found
three of four confirmed cases never recurred. So each candidate was replayed three times under
today's prompts, and kept only if it still went wrong at least twice.

## v1

Screened on `gemini-3.5-flash-lite` with the current (v2) prompts, memory off, 3 samples per case.

| | Bad samples |
|---|---|
| Census turns confirmed wrong in July | 153 / 684 (22%) |
| Controls | 4 / 120 (3%) |

The commonest error was miscounting who is left: an agent hunting "the remaining wolf" while the
dead roster in its own prompt shows both wolves gone. By role, vigilante turns went wrong most often
(37% of samples) and investigator turns least (0%).

The frozen set, `evaluation/frozen_eval_sets/hallucination_bench_v1.jsonl`, holds 125 cases in four
slices, each reported apart:

| Slice | Cases | What it answers |
|---|---|---|
| curated | 44 | Did a prompt change fix errors today's prompts still make? |
| random | 40 | Which model makes fewer errors? (drawn regardless of the screen) |
| control | 40 | Is the judge raising false alarms? |
| pinned | 1 | Does a fixed failure stay fixed? (the investigator's invented check) |

**v2 (2026-10-03)** adds four pinned cases from live game 46355b89. Its first use, the
information-fidelity pass, is in
[`game_play_enhancement/discussion_evidence.md`](../../game_play_enhancement/discussion_evidence.md) §6.5;
the code audit behind it is [`code_audit_2026_10_03.md`](code_audit_2026_10_03.md).

## What to trust, and what not to

- **The judge was right on 10 of 12 hand-checked verdicts.** Both misses came from the fact sheet
  naming only one attacker for a player killed by two; that was fixed before the final judging.
- **An old case is today's turn on a June board.** Its state fits today's code, but the history it
  carries (summaries, messages, earlier notes) was written under June prompts. Results are split by
  source so live-game cases, which match today's games, can be read apart; they should replace the
  June ones over time.
- **The curated slice leans toward the screen model's own mistakes,** since flash-lite chose it.
  Compare models on the random slice, and rerun flash-lite as an arm every time: even it scores
  better on a rerun than in the screen.
- **A replayed vote turn must not see the vote's result.** The game record files a day's vote result
  and the following night's deaths under that day. The first build read them back into vote turns,
  so the agent saw its own outcome. That was a replay error, not a game error: in a live game the
  result is posted after the votes. It was caught by reading the controls by hand and fixed before
  v1. The July ship test rebuilt vote turns the same way, so its error rates on vote turns run high.
- **Day turns only.** Night turns go through different builders and are not covered yet.

*Provenance: commits `a14de67`..`ab48570` (2026-10-03); screen run
`evaluation/eval_results/hallucination_bench/screen_v1/` (not tracked); the set's manifest records
the screen arm, rates and hand-check.*
