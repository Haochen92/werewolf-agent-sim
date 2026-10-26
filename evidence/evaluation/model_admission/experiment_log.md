# Model admission: the working record

*This is the full trust write-up of the model checks as it stood on 2026-10-23, with every run's record
table, the error codes, the cache floors and the check of the catalogue notes against the records. The
plain summary is [report.md](report.md), written 2026-10-24 from this text. "The bench" here is the
factual-error test set of [factual_errors](../factual_errors/report.md): the nine-seat test set and, for
the ten-seat runs, the fourteen frozen Phase 3 turns.*

*Written 2026-10-23.*

**What this page covers.** This page covers the checks used to choose a seat model (the AI model
that plays a player) and its settings, to choose the models for the offline jobs, and to measure what
they all cost. A model gets onto the game's menu by passing three checks in order: short test
prompts, a comparison with the default model on saved game turns, and then real games. The test
prompts cost pennies per model.

There are five groups:

1. **Admission probes** (§1–2). Can the model return replies the game can act on? Which calling mode
   (how a request asks for structured output) keeps its thinking on? Runs on 2026-10-04 (nine-seat)
   and on 10-11 and 10-13 (ten-seat). A separate live check asks every menu model once.
2. **The bench** (§3). On the same saved turns, does the model make clearly more factual errors than
   the default model? AI judges grade the replies. Nine-seat on 2026-10-04; ten-seat 2026-10-10 to
   10-12.
3. **Settings and job models** (§4, §5, §7). Which thinking level suits votes? Which model should
   write the day summary? Which models should run the offline memory jobs? All October 2026.
4. **Full games** (§6, §8). What goes wrong only in a full game, and what does a game cost? Ten-seat
   games on 2026-10-10. The July 2026 nine-seat choice is kept as history.
5. **Cost accounting** (§9). What did each game cost, from its token counts and dated prices?

§10 checks the model catalogue's notes against these records.

This page rates **how far each check can be trusted**. The choices these checks fed into are made
in the design folders. Prompt layout and caching are in [the caching report](../../caching/report.md).
The thinking budget is in [the reasoning-failures log](../../reasoning_failures/experiment_log.md)
§2–3. The agents' missing reasoning step and the ten-seat games are in
[the discussion evidence](../../game_play_enhancement/discussion_evidence.md) §6.7 and §8.4. The
extraction model is in [the v8 memory log](../../memory_system/v8/experiment_log.md). The July
choice is in [the July model selection](model_selection.md). The bench itself is rated
in [factual_errors](../factual_errors/report.md). How all the evaluation reports fit
together: [the hub](../report.md).

**This is the first written record of the admission results.** The raw outputs were never in git:
20 admission records from 2026-10-04, 10-11 and 10-13, and the bench runs used for admission. On
2026-10-23 they were moved into [`data/`](data/README.md), one folder per run. Each folder holds the
run's config and a file recording where the data came from. The configs are also in git
(`evaluation/config/model_admission/`, `evaluation/config/hallucination_bench_phase3_*.json`). Every
number below was read from those files on 2026-10-23.

| Check | Trust | Main limit |
|---|---|---|
| Admission probes (§1) | 🟡 | A pass/fail gate; cannot rank close models |
| Live check of menu models (§2) | ⚠️ | One call per model and schema |
| The bench as a gate (§3) | 🟡 | Two runs of the same model can differ by about 6 points (70 samples) |
| Thinking level, replayed on saved turns (§4) | 🟡 | Votes are scored exactly, but each case is one saved turn with no later days |
| Summary-writer comparison (§5) | ⚠️ | One AI judge's reading, six days from two games |
| Seat-model games (§6) | ⚠️ | Four to six games per model |
| Memory-job model comparisons (§7) | ⚠️ | One or two games, one reader |
| July seat-model choice (§8) | ⚠️ (historical) | Owner's unblinded reads of one or two games per model |
| Cost accounting (§9) | 🟡 | Exact arithmetic, but only as right as the dated price rows |

**Bottom line.** Use these checks as a gate, not as a ranking. The probes and the bench answer two
questions: can a model play the game's turns at all, and is it clearly worse than the default? Both
have caught real failures that a short check would have missed. Neither can put close candidates
in order.

## What the apparatus is for

The game's seat models are rows in a **model catalogue**: database tables `models` and `model_prices`,
seeded from `Agents/llm_factory/catalog.py` (`SEED_MODELS`) and edited with `scripts/model_catalog.py`.
Each row holds a model's thinking level, its **calling mode** (how a request asks for structured
output), its rescue model and a free-text note. A running server re-reads the catalogue every ten
seconds. A model reaches the menu by passing three checks in order:

1. the admission run, a battery of short probes (§1);
2. a bench arm against the default model on frozen turns (§3);
3. one or more real games (§6).

The catalogue notes are where the outcome is summarised. They are checked against the records in §10.

**Calling modes**, defined once (`evaluation/src/model_admission/probes.py`, `MODE_ORDER`):
- `native`: Gemini's own constrained output.
- `forced_tool`: the model must call a tool whose arguments are the schema.
- `json_schema`: the provider enforces the JSON schema on the reply.
- `auto_tool`: the tool is offered, but the model may answer in prose.
- `json_mode`: the schema is written as text after the prompt, and the reply is validated in code
  against the same schema. This is the **unenforced** mode.

## 1. The admission run (`eval-model-admission`) — 🟡

**What it is.** A probe battery run once per candidate model
(`evaluation/src/cli_runner/model_admission.py`, logic in `evaluation/src/model_admission/`). It costs
"pennies per model" (module docstring). It writes one JSON record per model, stamped with the runtime
fingerprint (git SHA and prompt-bundle hash).

**How it works.** Four probes:
- **Structured output per calling mode.** Every seat schema is asked for `samples_per_schema` times
  (default 3) at temperature 1.0, with a three-sentence in-character table prompt and one role line per
  schema (`seat_schemas.py`). `reply_problem` passes a reply if it parses as the schema, if the field
  the game acts on is filled, if that field names a listed player or an allowed token such as
  `"abstain"`, and if the reply has player reads. The probe also records reasoning tokens, so a thinking
  level the provider silently ignores shows up as 0.
- **Recommended mode** (`recommend_mode`). A mode must pass every call. When thinking is asked for, a
  passing mode that actually reasons beats one that does not. Otherwise the earliest mode in
  `MODE_ORDER` wins.
- **Cache floor** (`probe_cache_floor`). For each target size, an identical prompt with a fresh nonce is
  sent up to three times with waits, and the cached tokens the provider reports are recorded. The size
  is a target at about 4 characters a token; the provider's own count is kept beside it.
- **Real prompts** (`probe_real_prompts`). Two frozen discussion turns (eight in the 2026-10-13 runs),
  each rendered three ways through the production template: the speaker's turn, the same speaker's next
  turn after one more message, and another living seat's turn. The probe records failures, the field
  order of the reply, and the share of input served from cache.

**What it can claim.** That a model under a given mode returns replies the game can act on, at that
sample size. Which mode keeps its thinking on. Roughly where the provider starts caching. Whether real
turns fail where short probes pass. **What it cannot claim.** Anything about play quality: the one
semantic check is that a target names a real player. The cache floor is a bracket between tested sizes,
not an exact minimum. The cache shares come from one probe sequence per case and are not a whole-game
figure (caching report §4.2 makes the same point).

**How far it was checked.** The instrument corrected itself once. On 2026-10-04 DeepSeek V4 Pro passed
27 of 27 probes under `auto_tool` but answered 3 of its 6 real turns in prose. The runner now adds
real-turn failures to the recommendation (the code comment in `admit` cites this case). The same pattern
recurred on field order: short probes kept the schema's field order 17 of 17 times on 2026-10-13, while
Haiku's real turns kept it 15 of 24 times (below). The offline logic (mode choice, the three rendered
variants, field-order parsing) is pinned by `tests/evaluation/test_model_admission.py`. Like most of
`tests/`, that file is AI-written and unaudited.

### The records

**2026-10-04, nine-seat game** (9 seat schemas × 3 samples = 27 calls per mode, thinking medium; real
turns from `hallucination_bench_v2.jsonl`). Forced tool calls failed with reasoning on for most
providers, and no two providers passed the same set of modes. "—" means the mode was not run.

| Model | native | forced_tool | json_schema | auto_tool | json_mode | Recommended | Real turns failed | Real-turn time |
|---|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite | 27/27 | — | — | — | — | native | 0 of 6 | 4–8 s |
| DeepSeek V4 Pro | — | 27/27, 0 reasoning | — | 27/27 | 27/27 | auto_tool | 3 of 6 (prose) | 19–92 s |
| GPT-6 Luna | — | 0/27 (400) | 27/27 | 0/27 (400) | 27/27 | json_schema | 0 of 6 | 6–16 s |
| GLM-5.3 Flash (OpenRouter) | — | 0/27 (404) | 0/27 (404) | 26/27 | 27/27 | json_mode | 0 of 6 | 12–15 s |
| MiniMax M3 (OpenRouter) | — | 0/27 (404) | 0/27 (404) | 13/27 | 27/27 | json_mode | 0 of 6 | 23–64 s |
| Qwen3.8 Flash (OpenRouter) | — | 0/27 (400) | 21/27 † | 17/27 | 26/27 | none | 6 of 6 (400); 0 of 6 † | 37–135 s † |

† From a second run in `json_schema` alone (`admission_2026_10_04_json_schema`).

- **Error codes.** Luna's 400s say that function tools with `reasoning_effort` are not supported for
  the model. The OpenRouter 404s say that no endpoint was found for the request. The OpenRouter rows are
  pinned to each maker's own servers (config note).
- **DeepSeek.** The recommendation was not adopted. The catalogue row keeps the factory default, a
  forced tool call (`Agents/llm_factory/chat.py`), with no thinking level set.
- **Latency was decisive for three candidates.** MiniMax and Qwen were not taken onto the menu, and
  GLM was taken without thinking. No ruling for these is written in `evidence/`; the reasons are not
  found beyond the config notes.

**2026-10-11, Claude Haiku 5.5, ten-seat game** (17 schemas × 3 = 51 calls, thinking medium):
- `forced_tool`: 45 of 51, with 0 reasoning tokens, so a forced tool call turns its thinking off. All
  six failures were replies with no player reads.
- `json_schema`: 51 of 51, 312 reasoning tokens a call, 5.2 s.
- `auto_tool`: 48 of 51.
- Recommended `json_schema`. Real turns failed 0 of 6, at 9–17 s.

**2026-10-13, the unenforced-schema trials, ten-seat** (thinking low; 17 schemas × 10 = 170 calls per
mode; 24 real turns from eight frozen Phase 3 turns, in `json_mode`). The unenforced mode failed about
once in 400 calls on each model, which is what made it a candidate for production.

| | Haiku `json_schema` | Haiku `json_mode` | Luna `json_schema` | Luna `json_mode` |
|---|---|---|---|---|
| Probes, trial | 170/170 | 170/170 | 167/170 (3 with no reads) | 170/170 |
| Probes, repeat | — | 170/170 | — | 169/170 |
| Real turns failed, trial / repeat | — | 0/24 / 1/24 | — | 0/24 / 0/24 |
| Real turns in the schema's field order (repeat) | — | 15/24 | — | 24/24 |

**Field order on Haiku's real turns** (one sample a schema, 24 real turns each):
- `json_mode`: 15 of 24 in order.
- `json_schema`: 24 of 24.
- `json_mode` with the instruction asking for the schema's order: 13 of 23, and one reply failed.
- `json_mode` after the schemas put the reads first: 24 of 24.

The schema orders its fields on purpose, so that the model commits to its reads before it writes the
message (`field_order` docstring). The reordering was therefore a quality risk that pass counts could
not show.

**Dated note (2026-10-23).** The catalogue seed still lists `json_schema` for Luna and Haiku. Production
has used `json_mode` for both since 2026-10-14, by the owner's decision (caching report §3.5); a seat
whose `json_mode` reply breaks the schema is asked again with the schema enforced (commit `7f508c4d`).
The 2026-10-13 shared-prefix smoke runs passed 17 of 17 probes and 0 of 24 real-turn failures in both
modes on both models.

**Cache floor** (smallest tested size that read any cache; input → cached tokens as the provider
counted them):

| Model | Floor | Evidence |
|---|---|---|
| DeepSeek V4 Pro, Qwen3.8 Flash, GLM-5.3 Flash | 256-token target | 260 → 256, 280 → 256, 270 → 256 |
| MiniMax M3 | partial from 256, near-full from 1,024 | 423 → 128; 1,096 → 1,095 |
| Claude Haiku 5.5 (cache marks placed by the factory) | 512-token target | 393 → 0; 733 → 717 |
| GPT-6 Luna | 2,048-token target | 934 → 0; 1,797 → 1,794 |
| Gemini 3.5 Flash-Lite (Vertex) | none found | 0 up to the 4,096 target (3,636 tokens); real turns of 4,155–5,258 tokens also 0 |

The cached share of real turns per model is reported in caching report §4.2, from these same records.
The figures there match the records, with one exception noted for the reviewer.

## 2. The live structured-output gate — ⚠️

**What it is.** `tests/live/test_model_structured_output.py`, marked `live`, so it is skipped by
default. It asks every menu row (`menu_models()`) for every seat schema once, at the row's own thinking
level and catalogue mode. It uses the same schema table and the same `reply_problem` check as the
admission run.

**What it can claim.** That each menu model still fills each schema today, once. It catches a renamed
model id or a provider regression before a game fails mid-turn. **What it cannot claim.** A failure
rate: one call per pair is one sample, and the docstring itself says to rerun a failing case several
times.

**How far it was checked.**
- Its only recorded result is in the docstring: the 2026-09-10 run, every row clean except DeepSeek
  V4.1 Flash on the wolf vote, at about one failure in three. No run output is saved anywhere.
- `_credential_missing` has no branch for `anthropic/` models. Haiku 5.5, the default seat model
  (`DEFAULT_GAME_MODEL`), falls through to the Google-credential check. It is skipped when no Google
  credential is present, and runs without checking for a Claude key when one is.
- The module docstring still says the binding is "the factory's tool-calling path". The test now uses
  each row's catalogue mode (`chat.py`).

## 3. The bench as the admission step — 🟡

**What it is.** A candidate's arm in the hallucination bench, run against the default model on the same
frozen turns with the same judges. A **bad sample** is a reply in which the judge finds at least one
statement contradicting the game's facts. The bench, its cases and its judges are described in
[`../factual_errors/report.md`](../factual_errors/report.md). This section covers only the
bench's use as a gate.

**How it works.** Each arm regenerates every case `n` times. The summary gives each arm's bad-sample
rate by slice, and a per-case **sign test** against the first arm: for each case, whether the arm had
fewer or more bad samples than the reference arm, and a two-sided binomial p over the cases that
differ (`summarize` in `cli_runner/regen_replay/both/hallucination_bench.py`). Two sets were used:
- **Nine-seat, 2026-10-04.** `hallucination_bench_v2.jsonl`, 89 cases (44 curated, 5 pinned, 40
  controls; the random slice was left out), 2 samples a case. Judged by the census reader
  (`gemini-3.1-flash-lite` reads, `gemini-3.5-flash` re-reads its positives) and the golden judge
  (`gemini-3.1-flash-lite`), the code defaults on that date.
- **Ten-seat, 2026-10-10 to 10-12.** The fourteen Phase 3 frozen turns
  (`evidence/game_play_enhancement/data/phase3_turn_replay/cases.jsonl`): eight reasoning failures, two
  controls and four turns from game f02 on the illusionist rule. 5 samples a case (70 per arm), each
  checked against a hand-written expectation. The configs name the judges: `gemini-3.1-flash-lite`
  reads, `gemini-3.5-flash` re-reads and judges the goldens.

**The records, nine-seat.** Luna at medium was the only candidate not worse than the reference; both
cheap no-thinking candidates were worse on most cases that differed.

| Arm | Bad samples | Cases better / worse than reference | Sign p | Seconds a sample | Reasoning tokens |
|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite, medium (reference) | 16/178 (9%) | — | — | 6.9 | 1,376 |
| GPT-6 Luna, medium | 10/178 (6%) | 10 / 4 | 0.18 | 15.1 | 1,120 |
| GPT-6 Luna, high | 19/178 (11%) | 10 / 12 | 0.83 | 23.9 | 2,026 |
| GLM-5.3 Flash, no thinking | 57/177 (32%) | 3 / 33 | < 0.0001 | 15.2 | 137 |
| DeepSeek V4.1 Flash, no thinking | 77/178 (43%) | 1 / 48 | < 0.0001 | 3.3 | 0 |

The GLM run copied the reference arm's generations and verdicts from the main run rather than
regenerating them (its config note). DeepSeek V4.1 Flash failed the bench but is still a listed row
in the catalogue seed. No written ruling was found.

**The records, ten-seat.** Every candidate arm was compared with Gemini 3.5 Flash-Lite, regenerated in
the same run on that day's code.

| Run (date) | Arm | Bad samples | Better / worse than flash-lite | Sign p | s a turn | Reasoning |
|---|---|---|---|---|---|---|
| `phase3_luna` (10-10) | flash-lite | 25/70 (36%) | — | — | 9.1 | 1,501 |
| | Luna, medium | 10/70 (14%) | 7 / 2 | 0.18 | 19.1 | 1,278 |
| `phase3_haiku` (10-11) | flash-lite | 27/69 (39%) | — | — | 6.2 | 1,410 |
| | Haiku, thinking off (`forced_tool`) | 21/67 (31%) | 6 / 5 | 1.0 | 4.1 | 0 |
| | Haiku, medium | 11/70 (16%) | 7 / 3 | 0.34 | 13.7 | 2,131 |
| `phase3_haiku_low` (10-11) | flash-lite | 26/70 (37%) | — | — | 6.2 | 1,362 |
| | Haiku, low | 7/70 (10%) | 8 / 0 | 0.008 | 9.4 | 1,217 |
| `phase3_luna_haiku` (10-11) | flash-lite | 24/70 (34%) | — | — | 8.3 | 1,455 |
| | Luna, low | 5/70 (7%) | 8 / 1 | 0.039 | 8.1 | 394 |
| | Luna, medium | 3/70 (4%) | 7 / 1 | 0.070 | 16.3 | 1,256 |
| | Haiku, low | 11/70 (16%) | 6 / 2 | 0.29 | 9.5 | 1,250 |

`phase3_haiku_summary` (10-12) kept Haiku turns at low and varied only the earlier days' summaries.
The rate was 6 of 70 (9%) with the summaries the games were played with, 10 of 70 (14%) when Haiku at
low rewrote them, and 7 of 70 (10%) when Haiku at medium rewrote them. Against the played summaries the
two rewrites were 2 better / 5 worse (p 0.45) and 4 / 4 (p 1.0). The summary's default level is medium
(`DEFAULT_SUMMARY_THINKING_LEVEL`).

The 2026-10-13 Luna run on the shared-prefix layout (18 turns, judged by Claude Haiku 5.5) is reported
in caching report §4.4. Its numbers compare within that run only.

**What it can claim.** "Clearly worse than the default" on the turns the bench holds. The nine-seat
GLM and DeepSeek arms and the ten-seat Haiku-low arm are clear by the sign test. **What it cannot
claim.** A ranking between close arms, or play quality beyond factual errors on discussion turns
(caching report §6: no ten-seat vote or night cases).

**How far to trust it.**
- **Run-to-run spread is about 6 points.** Haiku at low scored 10% and 16% in two runs on the same 14
  turns, judges and code day. Flash-lite scored 34–39% across four runs. A difference under about 6
  points at 70 samples is not distinguishable from rerunning the same arm.
- **The judges are Gemini, the same family as the reference arm.** This applies to every gate run
  above. Whether that biases the comparison was not measured. The census reader was hand-checked at 10
  of 12 verdicts (bench report). The flash-lite golden judge was found unreliable in §6.5 of
  `discussion_evidence.md`. The ten-seat runs used `gemini-3.5-flash` as the golden judge. Its accuracy
  on the admission runs is not recorded. The Phase 3 turn replay's first use was hand-read verdict by
  verdict (§8.4).
- **The nine-seat curated slice was chosen from flash-lite's own errors.** It therefore leans in a
  candidate's favour. The bench report advises comparing models on the random slice, and the admission
  runs left that slice out.
- **Nine-seat and ten-seat numbers do not compare.** The cases, prompts and game differ.

## 4. The thinking budget, by frozen-turn replay — 🟡

**What it is.** Haiku 5.5 at thinking `low` against `medium` on frozen turns of two served ten-seat
games (`evaluation/experiments/haiku_effort_{cases,score}.py`, configs
`hallucination_bench_haiku_effort_{votes,turns}.json`, cases in
`reasoning_failures/data/haiku_effort_replay/`). It ran in October 2026.

**How it works.** A vote is scored by its target, an exact match on a structured field. "Right" means
the vote lands on an evil player. That is an outcome measure, not a judgment of the vote, and the cases
were chosen where the evidence pointed one way. For one game day the log defines a measure from the
evidence instead: a vote fits if it goes to one of the two unclaimed players, or abstains. Discussion
turns and the facts in a vote's notes are judged by Claude Sonnet 5.5 against hand-written
expectations.

**The record** (log §2): 16 vote cases at 10 samples each; 115 discussion samples a level.

| | Low | Medium |
|---|---|---|
| Votes right | 65/160 (41%) | 98/160 (61%) |
| Discussion samples flawed | 49/115 | 47/115 |
| Output tokens a vote | 852 | 2,317 |

- **Votes.** Medium was better on 12 vote cases and worse on 1 (sign test p 0.003).
- **Notes and discussion.** Notes had errors in 50% of samples at low and 46% at medium (p 0.21).
- **Majority voting.** A majority of three low-effort votes was right as often as one (39% against
  41%), because the same context produces the same wrong belief.

**How far to trust it.** The vote score involves no model, so it is the strongest number in this spoke
after the sign tests on the bench. It is off-policy: one frozen turn, with no effect on later days.
The Sonnet judge on notes and discussion is uncalibrated. **Status.** Medium for votes was approved,
on condition that a prompt change was tried first (log §6). No vote-specific thinking level exists in
`Agents/` or `server/`; the catalogue holds one turn level per model, `low` for Haiku.

## 5. The summariser model — ⚠️

**What it is.** Haiku 5.5 against Sonnet 5.5 for the day summary
(`evaluation/experiments/haiku_summary_compare.py`; data in
`reasoning_failures/data/haiku_summary_compare/`, October 2026). Every day with a spoken line in two
games (6 days) was re-summarised 5 times per model from its own checkpoint. The live summary was kept
as a third arm. Sonnet 5.5 judged every summary in one Message Batch.

**The record** (log §3): 18 of 30 summaries flawed on each model, and 3 of 6 live summaries flawed.

**How far to trust it.**
- **The first judging was invalid and was rerun.** The judge saw the moderator's closing line, which
  the summariser never sees, and took its old accuser wording as the truth. Only the second run is
  reported; the first run's verdicts are kept beside it.
- **The judge is Sonnet, one of the two arms, and it is uncalibrated.** Self-preference was not tested.
- **Six days from two games.** The result is a tie on that sample, not evidence that the models are
  equal in general.

## 6. Seat-model games — ⚠️

**What it is.** One model in every seat and as the summariser, AI-only ten-seat games, memory off,
captured by `evaluation/experiments/phase3_capture.py` on 2026-10-10: six games on Gemini 3.5 Flash
(`game_play_enhancement/data/phase3_flash_games/`) and four on GPT-6 Luna at medium (`phase3_luna_games/`).
Each game's cost comes from its usage meter. Readers audited each game against the
`phase3_reads/README.md` rubric: three Opus agents for Flash, two for Luna. The transcripts show the
true roles, so the reads are not blind.

**The record.**
- **Cost per game:** Flash $2.72, flash-lite (batch 4) $0.72, Luna $0.17.
- **Invalid deductions:** Flash about one per 15 heard lines, flash-lite one per 12. Luna 14 in about
  166 lines, 11 of them from one misread rule about the sentinel.

**What it can claim.** Discussion texture, the cost per game, and failure kinds that only a full game
shows. Luna's literal reading of the sentinel's card exposed a gap in the rules text that the looser
models never hit. **What it cannot claim.** Win rates (four to six games) or a per-line error rate
with a confidence interval.

**How far to trust it.**
- **The replay overstated the stronger model's gain.** On the frozen turns Flash made 1 error in 50
  samples against flash-lite's 11. In full games its invalid-deduction rate barely moved (README, "The
  audit"). The bench measures the failures it was built from. Games are what show the rest, so the
  admission plan's last step is not redundant.
- **One price is unverified.** Flash's cost uses a third-party price listing that was not checked
  against Google's page (README).

The first served Haiku 5.5 game, Haiku's game-stage check, is in `discussion_evidence.md` §8.6.

## 7. Memory-pipeline model comparisons — ⚠️

Three one-off comparisons chose the models of the offline memory jobs in October 2026 (records under
`memory_system/v8/data/`; narrative in `memory_system/v8/experiment_log.md`, 2026-10-11).
- **Extraction model.** Two pilot games were re-extracted with the same prompts by Gemini 3.8 Flash and
  3.5 Flash-Lite (`extraction_model_comparison/`). Gemini 2.5 Pro's cost came from Langfuse, not a
  rerun. The code that produced the two re-extractions is not found by name; the log describes the
  call path.
- **Claude extraction and the de-halo judge.** `evaluation/experiments/claude_extraction_compare.py`
  and `dehalo_compare.py` each ran on one game (`dehalo_compare/`). The **de-halo judge** is a second
  model call that revises verdicts that follow the game's outcome rather than the decision. "Halo" and
  "errors" were counted by one reader, and the log says the judge varies between runs.

**How far to trust it.** One or two games, single samples and one reader: these comparisons show cost
per game well and quality only by direction. **Dated note (2026-10-23).** The 2026-10-11 ruling (Gemini
3.8 Flash extraction plus a Haiku de-halo pass) was superseded on 2026-10-15. The offline jobs moved to
Claude (commit `d839e6f3`), and `scripts/extract_batch.py` now defaults to Sonnet 5.5. Its comment says
Haiku writes seat ids into lessons in a v8 batch check, and that check is not found as a separate
record. The v5-era `evaluation/src/studies/extraction_model_comparison.py` has its frozen record in
`v7_final/extraction_screens/`.

## 8. July seat-model selection — ⚠️ (historical)

[`model_selection.md`](model_selection.md), 2026-07-26, nine-seat game. The
instruments were the game's bill from Langfuse token counts × list prices, the owner's unblinded reads
of one or two full games per model, and turn latency as felt in live play. Game length varied about
two-fold between games and was not corrected for. Its selection table is superseded: the default seat
model is now Claude Haiku 5.5 (`DEFAULT_GAME_MODEL`, `Agents/llm_factory/accessors.py`). Its method
note still stands: use public benchmarks to shortlist, and measure on the game.

## 9. Cost and cache accounting — 🟡

**What it is.**
- **Game cost.** A game records its tokens by model and UTC hour (`server/game/usage.py`). Cost is
  computed when it is read, from the dated price rows (`Agents/llm_factory/pricing.py`, table
  `model_prices`), so fixing a price corrects every game it applied to.
- **Cache writes** are priced at a premium: 1.25× input on Claude and GPT-6, and 2× for Claude's
  one-hour cache (caching report §5).
- **Langfuse model definitions** are generated from the same rows (`scripts/model_catalog.py
  sync-langfuse`).
- **Pre-call estimates.** `evaluation/src/core/costs.py` prices with the catalogue and estimates tokens
  at 4 characters a token.
- **v7 loop spend.** `evaluation/src/loop/cost.py` sums Langfuse trace totals, with an ingestion lag at
  the end of a run.
- **Cache share per game.** `evaluation/experiments/game_cache_share.py` splits each game's input into
  read from cache, written to cache and neither, by call type, from traces (caching experiment log §11).

**How far to trust it.** The arithmetic involves no model and is deterministic. It is right only to
the extent that the price rows and the names usage is recorded under are right, and both have been
wrong. Before the October 2026 fixes, traces counted OpenAI's cache writes as free and recorded
Claude's reads and writes under unpriced names, so some earlier game costs were understated (caching
report §5). The rules are pinned by `tests/engine/test_pricing.py`, `test_langfuse_prices.py` and
`test_shared_prefix_layout.py`. These are AI-written and unaudited, and are cited for what they pin,
not as evidence of quality.

## 10. The catalogue notes, checked against the records

The seed's notes (`Agents/llm_factory/catalog.py`) are the shortest summary of admission. The live
database rows could not be read for this check.

| Row | Claim in the note | Record | Holds? |
|---|---|---|---|
| Gemini 3.5 Flash-Lite | 0 reasoning at minimal and low; bad samples 31% → 10% at medium | `discussion_evidence.md` §6.7: 82/267 → 27/267 | yes |
| Gemini 3.1 Flash-Lite | reasons at low; 15% bad | §6.7: 39/267 | yes |
| DeepSeek V4.1 Flash | drops required fields on about one wolf vote in three (2026-09-10) | the live test's docstring only; no saved output | not re-checkable |
| GPT-6 Luna | both tool modes refused with reasoning on, so `json_schema` | `admission_2026_10_04`: `forced_tool` and `auto_tool` 0/27, HTTP 400 | yes |
| GPT-6 Luna | low 7% against medium 4%, a tie case by case; ~390 against ~1,260 reasoning; 8 s against 16 | `phase3_luna_haiku`: 5/70, 3/70; 3 cases better and 3 worse (computed for this spoke from the judged files); 394 / 1,256; 8.1 / 16.3 s | yes |
| Claude Haiku 5.5 | low: 10–16% bad against flash-lite's 34–39%, ~9.5 s | `phase3_haiku_low`, `phase3_luna_haiku`, `phase3_haiku` | yes |
| Claude Haiku 5.5 | forced tool call turns thinking off; `json_schema` 51/51 against 45/51 | `admission_2026_10_11_claude` | yes as admitted; the production mode has been `json_mode` since 2026-10-14 (§1) |
| GLM-5.3 Flash | `json_mode`, 32% bad | `admission_bench_glm_2026_10_04`: 57/177 | yes |
| GLM-5.3 Flash | with thinking, 34–55 s a call | not in any admission record (the medium run reasoned 11–26 tokens a call, 5–9 s); stated only in the bench config's note | not found |
| Claude Sonnet 5.5 | refuses `tool_choice` "tool" and "any" (2026-10-12) | no admission record for Sonnet | not found |

## Verdict and cheapest upgrades

The gate does the job it was built for. It rejected four of six October candidates and kept Luna's
thinking on by choosing a mode the probes showed would keep it. It caught DeepSeek's prose replies and
Haiku's reordered fields on real turns, and it put a measured, dated note on every admitted row. Its
limits are the sample sizes (27–170 calls, 70 bench samples), Gemini judges grading a Gemini reference,
the missing vote and night cases, and records that until now existed only on one machine.

Cheapest upgrades (not scheduled):
- ~~**Move the 20 admission records and the eight admission bench summaries into this folder.**~~ Done
  2026-10-23: graduated into [`data/`](data/README.md), with the bench arms' judged files.
- **Add the `anthropic/` credential branch to the live gate,** and save its output per run.

## Sources

| What | Code | Record | Tracked? |
|---|---|---|---|
| Admission run | `evaluation/src/cli_runner/model_admission.py` (`eval-model-admission`), `evaluation/src/model_admission/{probes,seat_schemas}.py` | [`data/<label>/`](data/README.md) (20 records, 2026-10-04/11/13, graduated 2026-10-23); configs `evaluation/config/model_admission/*.json` | yes |
| Live schema gate | `tests/live/test_model_structured_output.py` | none (docstring note of 2026-09-10) | — |
| Admission bench arms | `evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py` (`eval-hallucination-bench`) | [`data/`](data/README.md)`{admission_bench_2026_10_04,admission_bench_glm_2026_10_04,phase3_luna,phase3_haiku,phase3_haiku_low,phase3_luna_haiku,phase3_haiku_summary,shared_prefix_luna_2026_10_13}/eval_results/` (`summary.json` and judged files, graduated 2026-10-23); configs `evaluation/config/model_admission/bench_*.json`, `evaluation/config/hallucination_bench_phase3_*.json`, `hallucination_bench_shared_prefix_luna.json` | yes |
| Thinking budget | `evaluation/experiments/haiku_effort_{cases,score}.py` | `reasoning_failures/experiment_log.md` §2; `reasoning_failures/data/haiku_effort_replay/` | yes |
| Summariser model | `evaluation/experiments/haiku_summary_compare.py` | `reasoning_failures/experiment_log.md` §3; `reasoning_failures/data/haiku_summary_compare/` | yes |
| Seat-model games | `evaluation/experiments/phase3_capture.py` | `game_play_enhancement/data/phase3_{flash,luna}_games/README.md`; `discussion_evidence.md` §8.4 | yes |
| Extraction and de-halo models | `evaluation/experiments/{claude_extraction_compare,dehalo_compare}.py`; v5 `evaluation/src/studies/extraction_model_comparison.py` | `memory_system/v8/experiment_log.md` (2026-10-11); `memory_system/v8/data/{extraction_model_comparison,dehalo_compare}/`; v5: `v7_final/extraction_screens/` | yes |
| July selection | none | `model_selection/report.md` | yes |
| Cost and cache accounting | `Agents/llm_factory/{pricing,catalog}.py`, `server/game/usage.py`, `evaluation/src/core/costs.py`, `evaluation/src/loop/cost.py`, `evaluation/experiments/game_cache_share.py`, `scripts/model_catalog.py` | `caching/report.md` §4–5; `caching/experiment_log.md` §11 | yes |
| Catalogue notes | `Agents/llm_factory/catalog.py` (`SEED_MODELS`, 2026-10-12) | §10 above | yes |

*Written 2026-10-23 from the untracked admission and bench records, the tracked configs, and the
evidence folders named above. The model choices themselves belong to those folders.*
