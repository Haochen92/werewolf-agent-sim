# Cost and latency

*Self-contained Level 1 draft, 2026-10-30. Optional investigations are listed in the content plan; no Level 2 pages are required.*

## Page copy (draft)

### Keeping a ten-agent game affordable and responsive

A game of Werewolf asks ten players to discuss, vote and use their night abilities over several days. When those players are agents, each decision requires a model call. A short message on the screen may have required the model to read thousands of tokens and produce private assessments as well as the words it says aloud.

I aimed to keep each game inexpensive while preserving useful agent behaviour and a responsive experience for the human player. That means considering cost alongside the quality of the decisions and how long the player waits. These constraints shape model choice, thinking effort, prompt layout and how much work happens during play.

#### Where the cost comes from

The workload extends beyond the visible conversation:

| Work | What the model processes or produces |
|---|---|
| Discussion, votes and night actions | Read rules, public history and private information; produce a decision alongside private assessments and strategy notes in the same response |
| Summaries and speech checks | Additional calls to preserve earlier discussion and check whether a new line contributes anything |
| Optional memory | Calls to prepare searches for relevant lessons; separate offline work to extract lessons from completed games |

Together, these can amount to hundreds of calls. The bill depends on both how many calls the game creates and what each call consumes: ordinary input, cached input, cache writes where charged separately, and generated output, including billed reasoning tokens. Input volume alone can be misleading. Across sixteen AI-only Haiku games with memory off, roughly nine-tenths of the tokens were input, but output accounted for about half the bill: output tokens cost more, while much of the repeated input was cached.

The frontend's completed-game averages give a practical reference. In the snapshot recorded for this write-up, the displayed model-call costs were approximately:

| Model | Average model-call cost per completed game |
|---|---:|
| DeepSeek V4.1 Flash | $0.10 |
| GPT-6 Luna | $0.11 |
| GLM 5.3 Flash | $0.09 |
| Haiku 5.5 | $0.15 |

These are observed costs from different games, not a controlled price comparison: game length and settings affect how much work each game creates. They exclude hosting costs.

For a separate memory-on reference, two ten-seat AI-only Haiku games cost **about $0.21 and $0.26**, calculated from their recorded usage. That covers playing with retrieved lessons, not the offline work of creating those lessons. Because these were different runs, the gap from the frontend averages does not isolate the cost of enabling memory.

To understand changes in the bill, I record token usage by call type and distinguish cache reads from writes. This matters when comparing an optimisation: reducing input charges may have little effect if the model writes more, takes more turns or needs retries. The cost records originally missed some cache charges; correcting that accounting was necessary before judging the savings.

#### Measure the wait the player experiences

A five-second model call need not produce a five-second pause. While the browser shows one speech, the server can already be generating the next event. If it finishes before the player is ready to move on, the latency is hidden by the presentation.

The stage waits when it catches up with the events the server has prepared. Two simplified examples show the difference:

| Time until the stage needs the next event | Time until that event is ready | Visible wait |
|---|---:|---:|
| 8 seconds of presentation remain | 5 seconds | None |
| 4 seconds of presentation remain | 6 seconds | 2 seconds |

This makes the sequence of work important. Votes can be collected in parallel, because each agent votes from the same completed discussion. A conversational reply depends on what the previous speaker said. The wolf pack's night actions also follow a chain of discussion and decisions. Those dependencies can delay the next event even when individual calls are reasonably fast.

I reconstructed the stage's waiting time from game events and model traces. Across seven hosted Haiku games played by me during development, the estimate was **roughly 3–5% of stage playing time**, excluding time spent waiting for the human. The range comes from two assumptions about how much previously generated content remained queued for presentation; it is not a range between the fastest and slowest games.

Passes exposed the mismatch particularly clearly. A pass was displayed for four seconds, while a discussion call took a median 5.4 seconds. Several passes in succession could exhaust the queued events. Showing a pass longer would hide some pauses but also lengthen the game. The useful target is responsive pacing, rather than hiding latency by making every event slower.

#### The levers and their trade-offs

Some settings trade cost and speed against the agent's ability to use evidence or the time available for discussion. Others offer savings when the workload meets their requirements.

**Settings with a trade-off**

| Lever | Towards lower cost or shorter waits | Towards more capability or room to play | What determines the choice |
|---|---|---|---|
| **Model tier** | Smaller models are typically cheaper and faster, but may struggle with the task | More capable models usually cost more; latency needs measuring | Does the improvement on game tasks justify the additional cost and wait? |
| **Thinking effort** | Less reasoning usually reduces output cost and response time, but may miss useful deductions | More reasoning can improve decisions, while adding cost and latency | Which tasks actually improve with more effort? |
| **Historical context** | More compression reduces repeated input, but risks losing evidence and adds summarisation work | More original history preserves detail, but increases input and may still be misread | What information must survive for later decisions? |
| **Discussion allowance** | Tighter limits bound calls and transcript growth, but can cut useful exchanges short | More turns allow fuller discussion, but can add repetition, cost and playing time | Have players had enough opportunity to contribute and answer accusations? |

The model-speed tendency is reflected in [provider guidance](https://developers.openai.com/api/docs/guides/latency-optimization). It is a starting assumption for testing, not a measured ranking of the models in this project.

**Optimisations with conditions**

| Optimisation | Benefit | Limitation or condition |
|---|---|---|
| **Prompt caching** | Reduces charges for repeated input | Does not discount output. Requires reusable input and provider support; rearranging prompts can change behaviour. Cache-write charges can outweigh savings when reuse is low. |
| **Offline batching** | Discounts eligible input and output, including expensive generated analysis | Results arrive later, so only work that live play does not immediately depend on can move here. Retries and cache misses still affect the bill. |

The following sections show how these choices worked out in the game.

#### Choose the model and thinking effort for each job

The project assigns models by job. A model used for every agent turn must remain affordable across hundreds of calls and keep up with live play. Frequency is not the only consideration: a day summary runs once per day, but its mistakes can enter every agent's later context. That makes it a reasonable place to test additional reasoning effort or a stronger model, even when upgrading every seat would be too expensive.

Post-game lesson extraction has a different requirement: turn a particular game into advice that transfers to another. One failure was retaining player IDs in extracted observations, tying the advice to seats that would mean something different next time. That failure helped rule out cheaper extraction models. Extraction and synthesis can justify stronger models and longer responses, and their results are not needed for the next live turn.

Candidates are checked on actual game tasks. Public benchmarks can help shortlist them, but they do not establish whether a model follows the game's rules, returns valid actions or responds fast enough in this workload. The [model-admission page](../evaluation/model_admission/model_admission.md) explains those checks. Selection is bounded by the candidates I have had the time, budget and access to test.

Thinking effort is another setting to calibrate by task. More reasoning can improve a decision, but it also generates more billed output and can delay the response. A replay of 16 selected vote cases in Haiku's live output mode illustrates the trade-off: medium effort chose an actual threat in 77% of valid samples, compared with 62% at low effort, while output rose from about 1,440 to 2,120 tokens per vote. These were selected cases replayed repeatedly, not a full-game comparison. Whether to adopt medium effort for votes remains open.

The benefit did not extend automatically to discussion. An earlier discussion replay, using enforced structured output, found little change in factual errors while turn time rose from 6.7 to 11.2 seconds. That result belongs to its tested output mode, but it gives a reason to evaluate effort separately for discussion and voting rather than raise it everywhere.

#### Reuse shared input without losing useful behaviour

Most seats repeatedly read the same rules and public conversation. **Prompt caching** lets the provider reuse processing for an unchanged beginning of the prompt and charge less for that input. It does not reuse the previous answer: the model still generates a new response for the current turn. **Caching discounts repeated input, not generated output**, so output-heavy tasks can remain expensive even with good cache reuse.

The prompt layout puts shared material before the details that differ by seat:

```text
Rules
Earlier days' summaries and today's public transcript
──────────────── cache boundary ────────────────
Board details, role card and instructions for this task
Private results, strategy notes and any retrieved lessons
```

Previously, each seat's role card appeared before the transcript. That made the prompts diverge early, preventing other seats from reusing the processed conversation. Moving private material later allows reuse across seats and task types. The growing transcript still needs suitable cache boundaries, and providers differ in how those boundaries are specified.

Reuse has to be verified in usage records. In the tested Gemini configurations on Vertex, automatic caching returned no reads; explicit caches worked in offline extraction. Other providers required their own handling. A repeated prompt alone was not evidence of a saving.

The layout also changes where the model encounters its instructions, so I checked its effects in games. In a small comparison using the same two deals per arm, the revised layout reduced Luna's cost per call by **28%**. Haiku's cost per call stayed about the same: with the unenforced schema, it generated more reasoning, consuming the input saving.

Haiku also participated more under the revised layout. Its games therefore contained more discussion and cost more overall. I kept the additional participation, although an improvement in play quality was not established. This is the trade-off that a cache-hit rate alone would miss: the prompt was cheaper to read, but the game produced more work.

*Explore: Making prompt caching work across providers →*

#### Bound the work without cutting off the game

Model settings and caching change the price of work. The game design also controls how much work exists. Longer discussions create more decisions and more text for every later agent to read; retaining every past transcript makes that repeated input grow across days.

Summaries replace earlier days' full transcripts with a shorter account. That adds a call and risks omitting or distorting evidence, so their role is to preserve usable context as well as bound input growth. The discussion cap bounds turns while allowing outstanding replies to finish rather than cutting the conversation off immediately.

A separate speech checker holds repetitive lines before they enter the public transcript. It adds a call and can suppress a useful contribution. Because it runs after generation, the candidate line has already been paid for: any input saving comes from keeping repetition out of later prompts.

The [conversation chapter](../game_design_orchestration/conversation/conversation.md) explains the speaking rules and their calibration. Here the cost implication is that fewer calls or shorter transcripts are only useful when the remaining discussion still gives agent players enough information and opportunity to act.

#### Move work outside the live game when it can wait

Post-game lesson extraction reviews completed games for useful observations; synthesis turns selected observations into reusable advice. Neither result is needed to continue the live game, so this work can run offline. It can take the time needed for analysis without making the human player wait.

Offline processing also makes the work eligible for discounted batch APIs. **Unlike prompt caching, batch pricing can discount both input and output.** That is particularly useful for these tasks: stronger models generating substantial analysis can incur a large output bill even when their input is mostly cached. Caching and batching therefore address different parts of the cost and can be combined where the provider supports it.

The discount still applies to the work actually performed, including retries and cache misses. One Sonnet extraction run processed 21 games in 630 calls and cost **$19.99 against an estimate of about $9.50**. Validation retries wrote new caches instead of reusing the shared input, and some requests within the batch also wrote rather than read it.

The investigation led to a revised retry path and better error logging. The saving from that fix has not yet been measured in a comparable full run. The practical lesson was to budget for cache misses and retries as well as the successful requests.

I also explored replacing memory-ranking and duplicate-checking API calls with small trained models. Those models were benchmarked but are not deployed, so they do not contribute to the measured savings. Their training results belong in the [supporting investigation](../../evidence/fine_tuning/report.md); the live cost figures above describe the API-based game.

<!--
Sources and editorial scope, 2026-10-30:
- Owner revision: removed arbitrary $0.30 budget; goal is inexpensive games with useful behaviour
  and responsive play. Self-contained L1, optional L3s. No cross-provider price forecast.
- Frontend averages supplied by owner in conversation: DeepSeek $0.10, Luna $0.11, GLM $0.09,
  Haiku $0.15. Rounded snapshot, not independently fetched. Before publication record sample
  counts, snapshot date and memory setting. server/routes/system.py and schemas/requests.py
  confirm separate completed-game means and counts for memory on/off, not these specific values.
- content_plan.md historical claims inventory: memory-on Haiku games $0.2146/197 calls and
  $0.2550/228 calls, re-derived from batch_results/cache_ab_2026_10_13/haiku_after.jsonl.
  No reanalysis performed in this edit. These are gameplay costs, not offline extraction.
- evidence/caching/experiment_log.md section 17: sixteen-game aggregate, roughly 90% input
  tokens but about half the bill output. Uses the existing analysis, not a fresh numerical audit.
- evidence/extraction/post_game/report.md section 4: seat IDs in extracted observations helped
  rule out cheaper models. Summary rationale describes where to test additional effort; does
  not claim a stronger summariser proved better.
- Former quiet-game reference retained in evidence/gameplay/data/persona_voice_games/README.md:
  16 games, $0.08–0.26, memory off. Removed from main copy to avoid competing cost samples.
- evidence/caching/report.md sections 1, 3.2, 4.1–4.6, 5: shared layout, provider observations,
  paired game comparison, participation, retry costs, accounting corrections.
- frontend/docs/stage_fit/README.md: seven Haiku games, reconstruction assumptions,
  2.7–5.1%, pass and discussion timings, parallel votes and sequential wolf night chain.
  Simplified timing table is explanatory arithmetic, not two measured events.
- evidence/gameplay/deduction/experiment_log.md sections 2 and 9: separate output modes,
  selected vote samples (valid-only rates), output tokens, discussion latency, pending decision.
  Section 9 read from owner's current working tree, including recent revisions.
- writeup/game_design_orchestration/conversation/conversation.md: cap drains obligations;
  after-generation echo gate. These mechanisms are not claimed as measured net cost savings.
- evidence/extraction/day_summary/report.md and context-engineering chapter: historical
  context compression and fidelity trade-off; no claimed comparison proving net savings.
- evidence/fine_tuning/report.md: trained/benchmarked, not deployed; no claimed production saving.
- Optional L3 destinations are recorded in content_plan.md. No links to nonexistent pages.
- Public tag: LLM inference optimisation.
-->
