# Evaluating models before switching

*Level 2 · [Evaluation](../evaluation.md) · previous: [Designing fair comparisons](../fair_comparisons/fair_comparisons.md) · status: page copy drafted 2026-10-25 with the Level 2 prompt, reviewed in the main session; for the owner's review.*

## Brief

**Reader question:** What must a candidate model demonstrate before it can serve a real game?

Subsections: short integration probes; quality on saved turns; real games and stage timing; cost and
reliability; current admission policy versus a stricter quality gate. This is a practical workflow,
not a ranking of model brands.

**Lead story:** 27 of 27 short probes passed, but 3 of 6 real turns returned prose. Follow that with
what replay quality could distinguish, and what only live games exposed. Keep cost optimisation and
provider-incident implementation in their own portfolio chapters, linked internally.

**Exhibit:** question → check → finding → decision, with integration failure separate from quality
measurement. Explain that menu exclusion currently uses cost, latency and integration; quality is recorded.

**Source:** [model admission](../../../evidence/evaluation/model_admission/report.md). Its combined admission
command is built but not yet run on a candidate; do not present it as a repeatedly exercised pipeline.

**Level 3:** none initially. A provider-integration comparison can remain a readable subsection unless
the adapter details later justify their own investigation.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: Confirm that the shortened field-order and setting examples preserve their original comparisons.
The six-point rerun spread is now described as an observed spread and provisional tolerance, not a
significance threshold. No model results were recomputed.
Verified 2026-10-25 (main session): field order (Haiku 15 of 24 in order, 24 of 24 after reads-first schemas; experiment_log.md §1), rerun spread (Haiku 10% vs 16% of 70; Flash-Lite 34–39%; report.md §1) and the vote setting (98 vs 65 of 160; §4) are preserved by the shortened text. No change needed.
-->

## Page copy (draft)

A model can be added to the game's menu, or made the default for a job, only after three checks:
short integration probes, quality replays on saved game turns, and real games. Each check answers a
different question. A probe asks whether the game can act on the model's replies. A replay asks
whether the model makes clearly more errors than the current one on known difficult turns. A real
game shows what happens when its replies shape later turns, and whether the live stage can keep
moving while it thinks.

Measuring quality is a separate question from deciding what quality should exclude. While the
project is experimental, I drop a model only when it costs too much, is too slow for live play or
cannot be integrated. Quality is measured and recorded, but it is not a reason for exclusion. Two
models with far more factual errors than the default remain on the menu; two others were not taken
because they were too slow.

| Question | Check | Example finding | Decision it informs |
|---|---|---|---|
| Can the game act on every reply? | Short probes for each way of requesting structured output, then real turns | Passed 27 of 27 probes; answered 3 of 6 real turns in prose | Integration: can exclude a model or calling mode |
| Is it clearly worse on known failures? | Replay of saved turns beside the current model, read by AI judges | 32% and 43% of replies with a factual error, against the default's 9% | Quality: recorded; used to choose settings; does not exclude |
| What appears only in a full game? | AI-only games read against a rubric | A literal reading of one role card misled four games | Quality and rules text |
| Can it keep up with the stage, at a price? | Seconds per call; stage waits replayed from served games | Two candidates too slow; the default kept the stage waiting 3–5% of the time | Latency and cost: can exclude |

*Integration failures and quality measurements are kept apart: the first can remove a model today;
the second is recorded beside it.*

### Short probes, then real turns

The game acts on structured replies: a vote must name a target, and a discussion turn must include
the player's suspicions as well as its message. Providers offer different ways of requesting that
structure. The model may be required to call a tool whose arguments follow the schema, the provider
may enforce the schema directly, or the schema may be written into the prompt and checked by code.

The probes request every reply type several times at temperature 1.0, in each available mode. A
reply passes if it parses, fills the field the game acts on, names a listed player or an allowed
choice such as abstaining, and includes the player's suspicions. The probes cost little, but those
prompts are short. The same run therefore sends a few real discussion turns through the production
prompt template: two saved turns, each rendered three ways, for six real turns.

#### Featured story: 27 of 27 probes, 3 of 6 real turns in prose

In the probes for the original nine-player game, DeepSeek V4 Pro passed all 27 calls in three
modes. The forced tool call was one of them, but it had used no reasoning tokens even though
thinking was requested. The runner prefers a passing mode in which the model actually reasons, so it
recommended offering the tool without requiring it.

On real turns, that mode failed. The model answered three of the six turns in prose instead of a
usable move. The short prompts had shown that the model could produce the format. They had not shown
that it would choose the format on a long game input when prose was also allowed.

The runner now reports real-turn failures beside its recommended mode, citing this case. The
recommendation was not adopted. The model is listed with thinking off, using the forced tool call.

A second check looked beyond whether replies parsed. On real turns, one model sometimes wrote its
message before its suspicions, reversing the intended order of committing to a read before speaking.
Listing the suspicions first in the schema restored that order in the tested replies. Format validity
alone had missed a requirement about how the response was produced.

#### Checking that a setting took effect

The forced tool call turned thinking off without an error, on both DeepSeek and Haiku. On Haiku it
passed 45 of 51 calls with no reasoning tokens, while the provider-enforced schema passed 51 of 51
with reasoning. Only the recorded reasoning-token count showed the difference. The probes therefore
record that count, prefer a mode that reasons when thinking is requested, and give each model its
own calling mode.

Production now uses the prompt-written mode for Haiku and GPT-6 Luna, by my decision on 14 October
2026. In the October trials it failed about once in 400 calls on each model. A reply that breaks
the schema is requested again with the schema enforced. This is a retry, not proof that every
schema-valid reply is sensible.

### What a quality replay can decide

A quality replay holds saved game turns fixed. The candidate and the current model each regenerate
the same turns several times, and the same AI judges read every reply for statements that contradict
the game record. A reply with at least one is a bad sample. A sign test compares the models turn by
turn: it counts the turns where the candidate did better and worse, and asks whether that split is
more lopsided than chance would produce. The turns come from the [factual-error test
set](../factual_errors/factual_errors.md).

On the original nine-player set, 89 saved turns with two replies each, the comparison separated
clearly worse candidates. It could not rank the close one.

| Model (setting) | Replies with a factual error | Turns better / worse than the default | Sign test p |
|---|---|---|---|
| Gemini 3.5 Flash-Lite, medium thinking (default then) | 16 of 178 (9%) | — | — |
| GPT-6 Luna, medium thinking | 10 of 178 (6%) | 10 / 4 | 0.18 |
| GLM-5.3 Flash, no thinking | 57 of 177 (32%) | 3 / 33 | < 0.0001 |
| DeepSeek V4.1 Flash, no thinking | 77 of 178 (43%) | 1 / 48 | < 0.0001 |

*Original nine-player game, October 2026; one run per model. Both clearly worse models remain on
the menu under the current policy.*

A repeat run showed how much a result could change with the model held fixed. On the expanded
ten-player game's 14 saved turns, Haiku at low thinking produced bad samples in 10% of 70 replies in
one run and 16% in another, with the same turns, judges and day. Four runs of Flash-Lite ranged from
34% to 39%. An unchanged model therefore moved by six percentage points between these two runs. That observed
spread is a reason to be cautious about small differences; it is not a calibrated significance
threshold. These runs distinguished large deficits more clearly than close candidates.

Three further limits apply. The judges were Gemini models, the same family as the default they
compared against, and that possible bias was not measured. The nine-player turns had been chosen
from the default's own errors, which favours any candidate. Neither set included night actions, and
only the ten-player work tested votes separately.

Replays also informed settings within a model. Haiku's low-thinking setting showed no clear factual-error
disadvantage on the tested discussion turns and was faster, so seats use it. On a separate set of 16
vote turns, medium thinking selected an evil player in 98 of 160 replies, against 65 at low. Those turns
were selected because the evidence pointed towards a target; the score measures that target match,
not the full quality of voting. Medium thinking for votes has not yet been adopted.

### What only real games showed

A replay measures the failures it was built from. Six AI-only ten-player games on Gemini 3.5 Flash
showed the limit of that measurement. The stronger model had largely removed the reasoning errors
held in its replay, but in full games invalid deductions fell only from about one per 12 lines heard
to one per 15. Games contained claims and contested readings the replay did not hold. The
[factual-errors page](../factual_errors/factual_errors.md) treats that stronger-model comparison as
part of diagnosing reasoning failures.

Four games on GPT-6 Luna exposed a gap in the rules instead of a weakness in the model. The sentinel
watches one player at night and sees who visited them. The engine leaves the sentinel out of the
visitor list it receives, but its role card said only “Watching is a visit”. In all four games, a
player argued that the sentinel should therefore have appeared in its own list. The real sentinel
accepted that reading and was voted out in three games. Eleven of Luna's 14 invalid deductions, in
about 166 lines, came from this one chain. This chain was not observed in the comparison games on
the other models.

Four to six games per model exposed failure kinds like these. That made them useful for discovery,
without providing a precise estimate of win rates or error frequency. The
[replays-and-games page](../replays_and_games/replays_and_games.md) explains that trade-off between
scopes.

### Fast enough for the live stage

The live game's display sets the latency requirement. The server never waits for the stage: it runs
ahead, and the browser plays each beat at full length. A speech line is shown for 5 to 15 seconds,
and a pass for 4 seconds. A model call is fast enough if its result arrives before the stage needs
it; otherwise the stage shows the speaker thinking and every player waits.

Seconds per call alone excluded two candidates. In the nine-player probes, MiniMax M3 took 23–64
seconds on real turns and Qwen3.8 Flash 37–135, against 4–8 for the default. Neither was taken, and
GLM-5.3 Flash was taken without thinking.

A stage-fit measurement now replays served games against the stage's own timing code. It does not
make any model calls. The stage's beats are rebuilt from each game's event log and compared with the
time each event left the server, read from the game's trace.

| Model | Games | Discussion turn: median, slowest 5% | Share of stage time spent waiting |
|---|---|---|---|
| Claude Haiku 5.5 (default) | 7 | 5.4 s, 10.8 s | 2.7–5.1% |
| DeepSeek V4.1 Flash | 3 | 3.5 s, 4.5 s | 0.1–0.3% |
| GPT-6 Luna | 2 | 6.4 s, 9.3 s | 2.1–5.3% |
| Gemini 3.5 Flash-Lite | 1 | 5.2 s, 8.0 s | 3.6–4.1% |

*Served ten-player games with a human seat, from 11 October 2026. Each range comes from two ways of
handling the stage's backlog when the human acts.*

On Haiku, most waiting occurs during runs of passes. A pass is shown for 4 seconds, while the next
seat's call takes a median of 5.4 seconds even when it also passes. The morning after a night also
waits, because the wolves' chat lines, kill and abilities run one after another: about 24 seconds on
night 1. After a speech, most turns finish in time. The pass and night waits could also be reduced on
the stage, with a longer pass hold or a visible decision beat; that product choice has not been made.

DeepSeek V4.1 Flash kept up with the stage almost entirely. It also had the highest error rate in the
nine-player quality replay. Those measurements come from different game versions, but together they
show why one score cannot decide whether a model is suitable. The seven Haiku games are all games I
played while building the site, so the latency limits derived from them are provisional.

### Cost and reliability

Cost is computed for each game from its token counts and dated price rows, including cache and batch
rates. <!-- **Link (planned):** How prompt layout and caching reduced the cost of a game → the cost
optimisation chapter. -->

A provider that held requests for minutes during live play led to a 30-second request budget and a
rescue model for every menu entry. <!-- **Link (planned):** How a stalled provider is detected and
replaced mid-game → the provider-stall rescue chapter. -->

### One command for the next candidate

Until October each check was a separate tool, and each result was interpreted after the run. A
combined admission command, built on 24 October 2026, runs the probes, the replays and code-scored
votes from one configuration. It applies criteria written into that configuration before the run,
names the cheapest passing thinking level and returns admit, reject or incomplete when a criterion
could not be measured. It has not yet been run on a candidate, so these are designed criteria rather
than a proven pipeline. Real games remain a separate manual step.

Each criterion comes from an earlier result. Integration requires every probe to pass, no real turn
to fail and reasoning to be present when thinking is requested. The provisional quality limit allows at most six
percentage points more bad samples than the current model, using the observed rerun difference above
as a practical tolerance rather than a statistical guarantee. The vote limit, ten
points, is derived from sampling spread rather than a measured rerun, and remains provisional. The
speed limits are a 5.5-second median and 11-second slowest 5% for discussion turns, matching the
default model's stage fit.

Current policy is built into the command. By default the quality and vote criteria are advisory:
they are reported beside the verdict but cannot cause a rejection. They become blocking only if the
configuration enables them, for example in a commercial release.

### What admission does not yet cover

The checks are uneven across the project's jobs. Votes and discussion turns received the most
attention. The day summary was compared on six days from two games. Memory extraction was compared on
one or two games. No judge was rechecked after a model change, because no human-labelled set exists
for those judges. The [LLM-judges page](../llm_judges/llm_judges.md) describes that validation step.

Two common migration safeguards have not been used. No model has been released to a share of live
games before everyone received it, and no check confirms that a model will play a lying role. A wolf
that refuses or softens a lie would break the game.

The next step is a run of the combined command on a real candidate, followed by one timed game per
candidate against the stage-fit limits.

**Evidence.**

- [Model admission: choosing and switching models](../../../evidence/evaluation/model_admission/report.md) (the five questions, the probe and replay tables, stage fit, the combined command and its criteria).
- [Model admission: the working record](../../../evidence/evaluation/model_admission/experiment_log.md), §1 (probe records, field order, calling modes), §3 (replay as a gate, rerun spread), §4 (thinking level for votes), §6 (seat-model games).
- [Stage fit: does the model keep ahead of the stage?](../../../frontend/docs/stage_fit/README.md) (method, waits by beat, provisional limits).
- [GPT-6 Luna games](../../../evidence/gameplay/data/phase3_luna_games/README.md) (the sentinel rule chain) and [Gemini 3.5 Flash games](../../../evidence/gameplay/data/phase3_flash_games/README.md) (replay gain versus full games).

<!-- Sources (checked 2026-10-25):
Three checks in order; what each answers: report.md "In short"; experiment_log.md "What the apparatus is for".
Policy (dropped only for cost, latency, integration; quality recorded; GLM 32% and DeepSeek V4.1 Flash 43%
listed; MiniMax and Qwen not taken for latency; quality would gate if commercialised): report.md "What decides
admission today"; gate.py mark_advisory_criteria docstring (owner 2026-10-24).
Exhibit rows: report.md §1–3; Luna README "One unstated rule"; stage-fit README.
Probe mechanics (temperature 1.0; parse, acted-on field, listed player or allowed token, reads present; real
prompts = two frozen discussion turns × three renderings = 6): experiment_log.md §1 "How it works";
evaluation/src/model_admission/probes.py; evaluation/src/cli_runner/model_admission.py.
DeepSeek V4 Pro: 27/27 under forced_tool (0 reasoning), auto_tool and json_mode; recommended auto_tool; 3 of 6
real turns in prose; recommendation not adopted; row keeps forced tool call, no thinking: experiment_log.md §1
records table and "DeepSeek" bullet; report.md §2 table. Runner now reports real-turn failures: the code
comment at cli_runner/model_admission.py l.64–69.
Field order 17/17 probes; Haiku json_mode 15/24; asked for order 13/23 (one failed); reads-first 24/24:
experiment_log.md §1 "Field order on Haiku's real turns"; report.md §2 finding 4.
Thinking off under forced tool call: Haiku 45/51, 0 reasoning; json_schema 51/51, 312 reasoning tokens a
call: experiment_log.md §1 (2026-10-11). Mode preference logic: probes.recommend_mode.
json_mode in production since 2026-10-14 by the owner's decision; ~1 in 400; enforced-schema retry: report.md §2
finding 3; commit 7f508c4d.
Replay method, bad sample, sign test: report.md §1 "Replays against the current model"; experiment_log.md §3.
Nine-seat table: report.md §1 (89 cases, 2 samples). Default at the time = flash-lite (report §2 table).
Rerun spread 10% vs 16%, flash-lite 34–39% over four runs: report.md §1 "How far to trust".
Gemini judges same family; curated cases from flash-lite's errors; no vote or night turns in the replay:
report.md §1 "How far to trust".
Haiku low vs medium (10–16% vs 16%; 9.5 vs 13.7 s; seats at low); votes 98/160 vs 65/160, 12 better / 1 worse;
cases chosen where evidence pointed one way; approved on condition; no vote-specific level in code:
report.md §1 "cheapest thinking level"; experiment_log.md §4.
Flash games: invalid deductions 1 per 12 → 1 per 15; replay gain larger: report.md §1 "Real games";
phase3_flash_games README l.50–57.
Luna sentinel chain (four games, card "Watching is a visit", engine omits the sentinel; voted out in l01, l02,
l04; 11 of 14 in ~166 lines): phase3_luna_games README l.44–54; report.md §1 "Real games".
Latency: MiniMax 23–64 s, Qwen 37–135 s, flash-lite 4–8 s; GLM without thinking: report.md §3 "Speed";
experiment_log.md §1 records table.
Stage fit: report.md §3 table; frontend/docs/stage_fit/README.md (method steps 1–4, two readings, waits by beat,
"seven games, all played by the owner while building", product choice not made).
Cost one-liner: report.md §3 "Price". Stall one-liner: report.md §4.
Combined command: report.md §6; gate.py overall_verdict / mark_advisory_criteria / cheapest_passing_level;
evaluation/config/template/admission_example.json (criteria and note). Vote scorer check 98/160 exact, 66 vs 65,
Necromancer day-4 vote: report.md §6.
Coverage gaps (summary six days from two games; extraction one or two games; judges not rechecked, no labelled
set): report.md §1 per-task table and "Earlier and lighter choices". Not done (canary; lying-role check):
report.md "Not done, against common practice".
-->

<!-- Completion note (2026-10-25)

Structure. Follows the brief's subsections, with two local changes: (1) the admission policy is stated in
the opening beside the exhibit, because the Level 1 summary and the brief both make the measurement/policy
split the page's central distinction; the "stricter quality gate" material then sits in the combined-command
subsection, where the config switch implements it. (2) Cost and reliability are one short subsection with two
planned links, per the task. The thinking-off finding gets its own short subsection under integration because
it is a distinct lesson (check that a setting took effect) and the Level 1 challenge table points here for
silent configuration failures. No Level 3 page, as instructed.

Claims I was unsure of, and why.
- "The runner prefers a passing mode in which the model actually reasons, so it recommended offering the tool
  without requiring it." The recorded recommendation is auto_tool and recommend_mode prefers reasoning modes;
  the link is now CONFIRMED by the record itself: data/admission_2026_10_04/eval_results/
  deepseek__deepseek-v4-pro.json, recommended_mode_why = "passed every call and reasons (1373.7 tokens a
  call); forced_tool also passed but did not reason".
- "The runner now reports real-turn failures beside its recommended mode." The report says real-turn failures
  "now count against a mode". In code (cli_runner/model_admission.py l.64–69) the standalone probe runner only
  appends "but it failed N of M real game turns" to the recommendation's reason; it does not change the mode.
  The combined command's gate (gate.py l.214–225) does make real-turn failures a blocking integration criterion.
  I worded the page to match the code.
- Stronger-model replay figures conflict between sources: the Flash games README and this report say 1 error in
  50 samples against flash-lite's 11; the factual-errors report and its drafted Level 2 page say 6 bad samples
  in 40 against 1. They may be different counts (errors vs bad samples; different case sets). I left both
  replay numbers off this page, kept only the game figures (1 per 12 → 1 per 15) and linked the factual-errors
  page. Needs reconciling before either page publishes.
- "Only the ten-player work tested votes separately": the 16-vote replay is ten-seat (served ten-seat games);
  the nine-seat bench had no vote cases scored as votes. Report says "no vote or night turns in the replay".
  Worth a verifier glance.
- Cost and stage-fit games: "Served ten-player games with a human seat, from 11 October 2026" is from the
  stage-fit README; one Luna game was excluded (unreadable trace) and is not mentioned on the page.
- The combined command's cost criterion: the gate supports token ceilings (schemas.py CostCriteria), but the
  worked example sets none ("cost is read from the report's table"). The page does not claim the command gates
  cost; it says quality is advisory and lists integration and speed criteria.
- Today's code vs historical runs: the probe runner's real-turn annotation was added after the 2026-10-04 run;
  the Haiku reads-first schema change post-dates the 15/24 run. The page presents both as "now".

Mechanism claims checked in code: recommend_mode and reasoning-token counting (evaluation/src/model_admission/
probes.py); real-turn failure handling (evaluation/src/cli_runner/model_admission.py); advisory quality,
admit/reject/incomplete, cheapest passing level (evaluation/src/model_admission/gate.py); quality_rejects false
and criteria values (evaluation/config/template/admission_example.json); enforced-schema retry (commit 7f508c4d
message); stall budget settings (Agents/llm_factory/health.py, only for the planned-link sentence); catalogue
rows for DeepSeek (Agents/llm_factory/catalog.py).

Deliberately left off (Handle with care and the general "stays off" list): AI-written, unaudited admission
tests; the live structured-output check (one recorded run, no saved output, missing Claude credential branch);
records kept on one machine until 2026-10-23; rulings never written down and the catalogue-note audit (two
notes with no record); the catalogue seed still listing json_schema; the unverified third-party Flash price and
the earlier understated costs (cost chapter's business). Also left off: per-game costs (incomparable units, and
the cost chapter owns them), the experiment log's "rejected four of six October candidates" (it reads as a
quality gate, which contradicts the current policy), model pinning and drift (fair-comparisons page owns it),
the majority-of-three vote result, the day-summary judging rerun.

Rubric self-scores (0/1/2):
- Reader orientation 2: opening states the three checks and the measurement-versus-policy decision; exhibit maps them.
- Added depth 2: probe mechanics, two integration failures, the sign test and rerun spread, stage-fit method and
  the combined command's criteria go well beyond Level 1.
- Conceptual coverage 2: integration, quality on replays, failures only games show, latency, cost/reliability
  (linked), and policy are each distinguishable; the featured story does not stand for quality failures.
- Paragraph clarity 2: one job per paragraph; the replay subsection's limits are a separate paragraph.
- Narrative economy 2: each subsection has its own decision; stronger-model diagnosis and scope trade-offs are
  linked, not retold.
- Experimental separation 2 (required): nine-seat replay, ten-seat rerun, vote replay, Flash games, Luna games
  and stage fit each keep their own sample and game version; the DeepSeek V4.1 Flash contrast says the two
  measurements come from different game versions.
- Interpretation 2 (required): the DeepSeek prose finding is stated as what the probes did not show, not as a
  mechanism; "right" votes are labelled a target match; stage-fit limits are provisional; the combined command
  is described as built, not run.
- Evidence and ownership 2 (required): "I" only for the policy, the json_mode production decision and the
  games the owner played; probe and replay runs are neutral. Numbers taken as reported.
- Technical accessibility 2: calling modes, bad sample, sign test and the stage's beats are explained on first use.
- Exhibits and links 1: the flow table is the brief's exhibit as a table, not a drawn diagram; whether a drawn
  version is wanted is open. Two planned chapter links await those chapters.

Length: about 2,400 words of page copy including tables and captions (file total 4,112 words, of which the
two comments are roughly 1,700), above the 1,200–2,000 guide. The extra is in the stage-fit and
combined-command subsections, each a distinct decision. If cuts are wanted, the first candidates are the
vote-scorer check paragraph, the Haiku field-order paragraph (a second instance of the featured lesson) and the
thinking-level-for-votes paragraph.
-->
