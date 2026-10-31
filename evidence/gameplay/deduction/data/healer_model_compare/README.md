# The healer's key turn across engine, thinking, output mode and model (2026-10-30)

Record: `../../experiment_log.md` §8. One frozen turn: the healer's day-2 turn in game 2f19d908 right
after player_7 admitted visiting it (case `9b3219e5dc1eb831`, "as played", in
`../deduction_injection/cases.jsonl`). Runner: `evaluation/experiments/healer_model_compare.py`.

| Path | What it is |
|---|---|
| `turn_engine_on.md` | The turn as today's code renders it, with the engine's roleblock line in the night record: the input every subagent read |
| `turn_engine_off.md` | The same turn with the game's deduction mode "off" (night record as the game showed it; no engine block) |
| `subagent_samples/{haiku,sonnet,opus}_NN.json` | 10 answers per model from Claude Code subagents, each in a fresh context, told to act as the game model and write one JSON object; engine on |
| `game_path/no_engine_low.jsonl`, `no_engine_high.jsonl` | Haiku 5.5 through the game's own call path, engine off, thinking low / high, output mode `json_mode` (the live mode) |
| `game_path/no_engine_sonnet_low.jsonl`, `no_engine_opus_low.jsonl` | Sonnet 5.5 and Opus 5.5, same settings (engine off, low, `json_mode`) |
| `configs/` | The bench configs for the engine-on game-path arms (`engine_on_enforced_schema.json`: Haiku low, `json_schema`; `engine_on_live_mode.json`: Haiku low and high, `json_mode`) and the one-case dataset they read (`anchor_case.jsonl`). As run, the configs pointed at a scratch copy of that dataset |

The engine-on game-path samples are in `evaluation/eval_results/hallucination_bench/healer_model_anchor/`
(enforced schema) and `healer_model_anchor_live_mode/` (live mode), each with the bench's fact-check
verdicts.

Measures, fixed before the runs: whether the private read of player_7 says Chanteuse; whether the seat
spoke; whether its public message ties player_7 to the block. Reads come from the structured `reads`
field; messages were read by hand.
