# Tracing & Observability

**Scope:** Most evaluable moments in a game — agent decisions, post-game extraction, dedup, and day
summaries — are captured as one of four *cases* (`EvalCase`, `ExtractionCase`, `DedupCase`,
`DaySummaryCase`), written to two sinks at once (the live Langfuse trace + a local JSONL sidecar) in one
shared shape, and frozen into reproducible eval sets. This is the **capture** half of evaluation — the
instrument that makes judging possible. The **judge** half (score design, LLM-judges, metric validation)
is the *evaluation system* and is out of scope here (see the `metrics/` and `memory_system/` evidence).
The one seam between them — pushing computed scores back onto the trace — is §2.8.
**Last updated:** 2026-06-27 (consolidates the dated logs in `implementation_notes/`).
**Runtime:** **Langfuse 3.14.6** — the OpenTelemetry-based v3 Python SDK, self-hosted — with the
LangGraph `CallbackHandler` integration. Framework behaviours asserted below (§2) are described against
that version; a reader on another should re-confirm.

## Why — the motivation behind the tracing system

Two goals drive everything below.

1. **Measure whether the memory system actually works.** A core objective of this project is an
   episodic-memory system that makes an agent play *better* with it than without. Win-rate alone is a
   noisy signal at the sample sizes we can afford (N≈30–50), but under a fair, paired A/B it still tells
   us whether we're moving in the right direction.

   The harder problem is that the memory system isn't one thing — it's a pipeline of components that can
   each fail independently, and a single win-rate number can't tell you *which* one. Day-summary
   extraction distils each day's discussion into the facts later turns rely on; situation-summary
   generation forms the query that drives semantic retrieval; the agent's own reasoning turns retrieved
   memory into a decision; game design shapes the raw material (e.g. moving discussion from parallel to
   sequential, or adding roles); and post-game extraction, store management, and synthesis decide what
   gets remembered at all. Each is a potential failure point, so we have to observe, evaluate, and debug
   them *individually* before asking whether the whole system works end-to-end — and tracing is what
   makes each of those stages observable.
2. **Build a frozen dataset for labelling and future fine-tuning.** Capturing every decision as a
   structured case gives us a durable, curatable corpus we can later label and turn into training data —
   e.g. a cross-encoder reranker for retrieval, or a dedup classifier — without re-running games.

## Infrastructure decisions

**Choosing the observability backend** — the shortlist was LangSmith, Arize Phoenix, and Langfuse.

1. **The bar: self-hostable and open-source/free.** For a solo project the backend has to run locally, so
   the trace data is ours, it costs nothing per trace, and we can retroactively mine *any* old span into a
   new case type later. This **dropped LangSmith** — a closed SaaS whose self-hosting sits behind a paid
   tier. Phoenix and Langfuse both clear it.
2. **The tiebreak: fit, since Phoenix and Langfuse are both OSS and self-hostable.** Two things this
   pipeline leans on chose Langfuse over Phoenix:
   - **Explicit, hand-shaped spans.** The design writes a structured case into a span's `output` at the
     exact decision point and reads it back by name (§2.3–§2.4). Langfuse's SDK is built for that manual
     span shaping; Phoenix leans auto-instrumentation-first (its instrumentors auto-capture framework
     calls), so a bespoke "put my `EvalCase` in this span" cuts against its grain.
   - **Ease of LangGraph wiring.** Langfuse's standard LangChain `CallbackHandler` covers LangGraph out of
     the box — the span tree emits automatically (§2.2) with near-zero glue.

   It was a fit judgment at decision time, not a benchmarked shootout — but a considered one, on those two
   axes. Langfuse then bundles scores, sessions, and prompt/version management as first-class features the
   pipeline goes on to use (§2.7–§2.8).

Those two goals, on a self-hosted Langfuse, produce one capture pipeline — and the rest of the report is
its *how* (each §2 section opens with why its piece exists, then how it works):

> **Orientation — the capture pipeline.** Every gradable decision flows along one path:
>
> **game decision → Langfuse span** ─┬─ **span output:** a frozen `*Case` (the gradable record)
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ **local sidecar JSONL** (same shape) ← **PRIMARY** for builds
> → `eval-build-*` freezes the selected cases → `frozen_eval_sets/<id>.jsonl`
>
> The mental model the whole design turns on: **the trace is for *watching*; the case is for
> *building*. Two sinks, one shape.** Every identifier below (`freeze_case`, `EvalCaseSink`,
> `span_names`, `EvalProvenance`, `runtime_fingerprint`) hangs somewhere on this path.

---

## Vocabulary

The ten terms the rest of this report leans on (skip if fluent):


| Term                            | Plain meaning                                                                                                                              | Lives in                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| **trace**                       | the full record of one game run — a tree of spans under one root                                                                          | Langfuse                                  |
| **span**                        | one node in that tree: a subgraph / node / LLM call, with input, output, timing                                                            | Langfuse (auto-made by the callback)      |
| **case**                        | a*frozen, self-describing* record of one gradable unit of work, written into a span's `output`                                             | `Agents/schemas/evaluation.py`            |
| **EvalCase**                    | the case for one agent decision (day message / vote / night action) — the richest case type                                               | `agent_action_eval_*` spans               |
| **sink**                        | the in-process accumulator (`EvalCaseSink`) that keeps a local copy of every case during a game                                            | `Agents/observability/case_sink.py`       |
| **sidecar**                     | the per-game JSONL the sink is flushed to after the game (`batch_results/eval_cases/…`)                                                   | disk — the**primary** source             |
| **frozen eval set**             | a curated, immutable dataset of cases selected from sidecars; the input a judge replays against                                            | `evaluation/frozen_eval_sets/<id>.jsonl`  |
| **candidate pool**              | the*wide* retrieval set (before rerank/filter narrowed it), kept on the case so the reranker can be trained/judged on what it actually saw | `EvalCase.candidate_*`                    |
| **release / fingerprint / SHA** | three views of "what*code* produced this" — see §2.7                                                                                     | trace`release` field + metadata + records |
| **provenance**                  | the*data/config* identity of a case (which store? rerank/filter on?) — distinct from the *code* fingerprint                               | `EvalCase.provenance`                     |

---

## 1. The guarantee (current contract)

Each game run produces, in one Langfuse trace:

- **One root span** (`werewolf-game`) wrapping the whole game, with the LangGraph callback handler
  auto-nesting a child span for every subgraph / node / LLM call beneath it.
- **A frozen, self-describing *case* at every gradable decision**, written into that decision's span
  output **and** teed to a local per-game JSONL sidecar — byte-identical normalized shape, so one set
  of converters reads either source.

**The four case types** (each = a gradable unit of work; span prefix is the single-source name it's
fetched by):


| Case             | Span prefix            | What it freezes                                                                                   | Captured for                                                                  |
| ---------------- | ---------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `EvalCase`       | `agent_action_eval_`   | one agent decision (day message / day vote / night action) + its full information set + retrieval | situation/retrieval/application judges; reranker + agent-dialogue fine-tuning |
| `ExtractionCase` | `postgame_extraction_` | one game's post-game extraction (inputs → observations / strategy points)                        | extraction judge                                                              |
| `DedupCase`      | `dedup_`               | one dedup decision (new entry vs candidate pool + verdict + similarities)                         | dedup judge; dedup-classifier fine-tuning                                     |
| `DaySummaryCase` | `day_summary_eval_`    | one day's summary (raw transcript → summary)                                                     | day-summary judge                                                             |

**Self-describing, by construction.** A frozen case carries everything needed to re-judge it offline
without re-reading game state or re-joining the trace: the decision-time information set (visible
discussion + role-private context), the retrieval (final picks **and** the pre-rerank candidate pool),
the agent's actual output, and an `EvalProvenance` stamp (store dir + rerank/filter flags). The trace
additionally carries the game's `runtime_fingerprint` (code SHA, prompt-bundle hash, model IDs,
backend) and the git commit as Langfuse's first-class `release`.

**How it's persisted.** `run_batch` writes a game-run log `batch_results/<session_prefix>.jsonl` and a
per-game eval-case sidecar `batch_results/eval_cases/<session_id>/<game_id>.jsonl`; the log record
points to the sidecar via `eval_cases_path`. Frozen eval sets are then built **local-sidecar-first**,
with a Langfuse read path retained only as a fallback for games that predate local emission.

**The rule, quotable:** *emit the gradable record locally at decision-time; the tracer is the
secondary archive, not the source of truth.* §4 is the incident that forced that rule.

What this contract does **not** yet cover is in §5.

## Worked example — one vote, end to end

The four case types above stay abstract until you watch one move. Follow a single decision — **villager
`player_3` casts a day-2 vote** — as a concrete `EvalCase`; every term in the mechanism (§2) is a step
here:

1. **The span opens.** The day subgraph runs `player_3`'s vote node; the LangGraph callback handler
   (§2.1) auto-creates a span for it under the game's root trace (no manual code). The emission site
   also names a child span `agent_action_eval_player_3_day_2_round_0_vote` (name built by
   `span_names.py`, §2.5).
2. **The case is built (§2.3).** At decision time the code assembles an `EvalCase`: the visible day-2
   discussion, `player_3`'s private context (its previous-strategy note — a villager has no wolf
   channel / investigator results), `memory_enabled`, the situation queries it generated, the
   observations/strategy points retrieved (plus the wider `candidate_*` pool if rerank/filter ran), the
   `provenance` stamp, and the actual `agent_vote`.
3. **`freeze_case` tees it to two places (§2.4).** It stamps the live span's `trace_id` +
   `observation_id` onto the case, dumps it once, writes it into the span's `output` (`{"eval_case": …}`,
   visible in the Langfuse UI), **and** appends the same dict to the local `EvalCaseSink`. Same shape,
   two destinations; `case_id = {trace_id}:{observation_id}` is identical in both.
4. **The game ends; the sink is persisted (§2.6).** `run_game` returns `eval_sink.records`; `run_batch`
   writes them to `batch_results/eval_cases/<session>/<game_id>.jsonl` and records the `eval_cases_path`
   pointer in the game-run log.
5. **A frozen set is built (§2.6).** `eval-build-*` reads that sidecar (no Langfuse call), converts the
   span dict back into an `EvalCase` via `eval_case_from_span`, samples it among the others, and writes
   `evaluation/frozen_eval_sets/<id>.jsonl`.
6. **(Out of scope — the judge.)** Later a runner replays `player_3`'s frozen vote against a judge or
   gold label. That's the *evaluation system*, not this report.

## 2. The mechanism

### 2.1 Langfuse wiring

This section is about the two pieces of plumbing in `Agents/tracing.py` that connect the game to
Langfuse. First, the basics: the file opens **one shared connection to Langfuse for the whole run**.
`langfuse = get_client()` hands back the *same* client object every time anyone asks for it, so every
part of the program records into the same place instead of each opening its own connection. Two things
about this wiring are worth understanding.

**1. Every game's trace is labelled with the exact code version that produced it.**

*The problem.* A trace on its own doesn't say *which version of the code* generated it. Without that you
can't tell two A/B arms apart after the run, or trace a regression back to the commit that introduced
it.

*The fix, in plain terms.* When the program starts, the code reads the current git commit and stamps it
onto every trace as Langfuse's built-in **`release`** label — a field you can filter and group by
directly in the Langfuse UI. You don't set this by hand: the code writes it, so it is **not** a
configured value and won't appear in `.env` (which only holds the Langfuse login credentials). If you
*do* want to override it — say, a CI pipeline tagging a run — an explicit value still wins; the code
only fills it in when nothing else has. So the takeaway most readers need is just: **games are
auto-tagged with their code version, and you filter by that tag in Langfuse.**

*Mechanism — skip unless you're debugging release-stamping (verified, Langfuse 3.14.6).*

The whole subtlety is **timing**, and an analogy makes it click. Think of Langfuse's tracer as a
**label-printer for traces**. When the printer is switched on, it loads one stamp — *"made by this code
version"* — and from then on, every trace it prints carries that same stamp. The catch: the stamp is
loaded **only at switch-on**, and can't be swapped while the printer is running.

The printer switches on the **first time anything asks Langfuse for a client** (the first `get_client()`
call). At that instant, it reads the code version from an environment variable (`LANGFUSE_RELEASE`) to
decide what the stamp says. So the version has to be set *before* that first request. If it isn't, the
printer switches on with a blank stamp — every trace in the run goes out unlabelled, and nothing later
can add the version back.

That single rule — *set it before switch-on* — is the only reason the code is ordered the way it is.
`Agents/tracing.py` writes the git commit into the variable at **import time**, which runs before it ever
asks for the client, so the stamp is always loaded in time. (And `run_batch.py` reads the `.env` file
first, so a version you set by hand still wins over the default.)

In API terms, mapping the analogy onto the SDK: the "printer" is the process-wide **`TracerProvider`**,
set up once. The "stamp" is an **OpenTelemetry Resource** — a fixed bag of facts about who produced the
telemetry, with the version inside it. The Resource is attached to the `TracerProvider` and shipped with
every span; Langfuse then lifts the version into the trace's `release` column. "Switch-on" is the
`set_tracer_provider` call, which fires only while the provider is still OTel's placeholder
(`ProxyTracerProvider`) — i.e. exactly once. Call chain: `_init_tracer_provider`
(`resource_manager.py:453,460`) reads the value into
`Resource.create({LangfuseOtelSpanAttributes.RELEASE: <sha>, …})`, then installs the provider
(`resource_manager.py:467,474`).

**2. Each game gets its own recorder that captures every step automatically.**

`build_game_config()` hands LangGraph a fresh `CallbackHandler` per game (in its `callbacks` list). This
is the piece that makes the whole span tree appear *on its own* — every subgraph, node, and model call
is recorded as a nested span with no manual logging code (§2.2). The same config also tucks the full
`runtime_fingerprint()` (the complete provenance bundle, §2.7) into the trace's metadata, so the record
of *what produced this run* travels with the trace.

### 2.2 Trace & span hierarchy

`run_game` (`Agents/main.py`) opens the root span as a context manager
(`langfuse.start_as_current_observation(as_type="span", name="werewolf-game")`), then
`root.update_trace(...)` stamps the trace name, `session_id`, and a metadata block (game_id + every
memory/rerank/filter/persistence config). The LangGraph callback handler attached in §2.1
auto-captures all downstream subgraph/node/LLM runs as nested spans — **the tree comes for free from
the callback; the case spans (§2.3) are the only manually-shaped observations.** `Metrics` and the
`EvalCaseSink` are threaded into the graph via LangGraph **runtime context**
(`context={"metrics": ..., "eval_sink": ...}`), not graph state — so they accumulate per-game with no
global mutable state and no cross-game races.

### 2.3 The case abstraction — the frozen case is the unit of truth, not raw state

**Why capture this much.** To re-judge a decision offline you must freeze everything the agent had: what
it saw, what it retrieved (including the wide pre-rerank pool), what it decided, and how it rated each
memory. (Capture pays off for secondary uses too — debugging a run, inspecting LangGraph state step by
step, the planned frontend "X-ray" of each agent's mind [`frontend/design_log.md`], a considered
rendered-prompt leak spot-check [`agent_boundaries/report.md` §5] — but *measuring the memory system* is
what made it non-optional.)

**Why freeze it *now*, not derive it later.** An earlier design kept the case implicit in the full trace
and re-derived it on read — flexible (recombine raw spans into any case shape on demand), but it couldn't
hold. Part of a case exists *only* at decision-time — the pre-rerank candidate pool, the assembled
`private_context`, the situation queries that drove retrieval — and can't be reconstructed from raw spans
afterward; and bulk-reading heavy traces back to re-derive cases didn't scale (§4). So the case is shaped
*eagerly* at the decision point and frozen whole. The flexibility that survives is at the *set* layer
(sample/select frozen cases into any eval set, §2.6) and a *retroactive-mining* escape hatch (`fetch_spans`
over the retained full trace can still turn any span into a net-new case type, §2.6); what's gone is
re-shaping an *existing* case's content after the fact — a field not frozen at decision-time is
unrecoverable (wolf-night, which freezes no case at all, is the limiting proof — §5).

The contract every consumer relies on: **read a frozen `*Case` from a span's output, never raw game
state.** `EvalCase` (`Agents/schemas/evaluation.py`, `schema_version="eval_case_v2"`) is the richest;
its fields group into the information set a judge needs:


| Group           | Fields                                                                                                                                                                      | Why captured                                                                                              |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Identity        | `trace_id`, `observation_id`, `span_name`, `player_id`, `player_role`, `day`, `round`, `action_phase`                                                                       | `case_id = {trace_id}:{observation_id}` is the stable, source-independent key (§2.4)                     |
| Information set | `visible_discussion`, `private_context` (`EvalPrivateContext`: previous strategy, day summaries, wolf channel, investigator/vigilante results, surviving rosters)           | reproduces*exactly what the agent could see* at decision time                                             |
| Retrieval       | `memory_enabled`, `retrieval_skipped_reason`, `situations`, `situation_dimensions` (v6 query enums), `retrieved_*`, **`candidate_*`** (pre-rerank pool w/ embedding scores) | judging retrieval + training the reranker need the pool that*entered* reranking, not just the final top-k |
| Output          | `agent_message` \| `agent_vote` \| `agent_night_action`                                                                                                                     | the decision actually taken (a night action is a target pick, so it's its own field)                      |
| Credit signals  | `strategy_verdicts`, `strategy_index_to_key`, `adopted_strategy_*`, `memory_applicability`, `updated_strategy`                                                              | the agent's per-item follow/override/not-relevant judgements, joinable to the exact stored entry          |
| Provenance      | `provenance` (`EvalProvenance`: store_dir, reranking_enabled, filtering_enabled)                                                                                            | makes the case self-describing — see §2.7                                                               |

`schema_version` gates format migrations across runs. The other three case types follow the same
frozen, self-describing pattern at coarser granularity (game / dedup-decision / day).

### 2.4 Dual-sink emission — one shape, two destinations

**Why a local sink at all.** A tracer is for *watching* a run, not for storing data you read back in
bulk. Langfuse's read APIs make that concrete: they cap query cost (and return a 422 on heavy traces),
they truncate large fields, and they tie the eval pipeline to a service being up. So each case is written
to **both** places at once during the game — the Langfuse span and an in-process local sink. At game-end
the local sink is flushed to a durable JSONL file. That local file is the *primary* source for builds;
Langfuse is the *secondary*, retrospective archive (the lesson of §4).

The mechanism — a single function, `freeze_case(span, case, *, kind, case_key, sink)`
(`Agents/observability/case_sink.py`), is called at every emission site. It (a) stamps the live span's
identity onto the case (`case.trace_id = span.trace_id`, `case.observation_id = span.id`), (b)
`model_dump`s it once, (c) appends a **normalized span-dict** to the local `EvalCaseSink`, and (d)
returns the payload for the producer's `span.update(output={case_key: payload})`. The local record is
deliberately the *exact* shape the Langfuse read side produces from a fetched span —
`{kind, id, name, trace_id, output: {case_key: payload}, ...}` — so the `*_case_from_span` converters
and frozen-set builders apply **verbatim to either source.** Because both copies carry the same real
`(trace_id, observation_id)`, a case's identity is **source-independent**: a frozen set built from
local sidecars and one built from Langfuse contain the same case ids, and judge score push-back works
on either. `run_game` returns the accumulated `eval_sink.records` on the `GameOutcome` so `run_batch`
can persist them.

### 2.5 Span names — a single source of truth

`Agents/observability/span_names.py` is the only place span names are defined; both producers (the
emission sites) and the consumer (`evaluation/src/data/langfuse.py`) import the prefixes + builder
functions from it, so a rename can never silently strand a builder matching a stale prefix. One
deliberate sharp edge is documented there: the extraction parent case-span
(`postgame_extraction_<game_id>`) and its per-role child LLM runs (`postgame_extraction_<role>_...`)
**share a prefix** — so a name-scoped reader must select the parent *structurally*, not by prefix
alone, and the dedup LLM run names (`DEDUP_LLM_RUN_NAMES`) must be excluded up front. (That collision
is also one of the things the §4 fix had to get right.)

### 2.6 Persistence & the data plane

**Why freeze into curated sets.** Replaying a decision, judging it, or training on it all require holding
every other variable constant and staying re-runnable; re-reading the trace each time would re-instantiate
nondeterministic retrieval and possibly-drifted models, and a *mutable* set silently orphans every result
computed against its old contents. So cases are sampled into immutable, hash-linked frozen sets — the
stable input to all replay/judging/training (`decision_replay/`, the same-seed `paired_ab/`, hash-lineage
in `refactor/provenance_lineage_rationale.md`).

The flow is four stages, not duplicated stores (`evaluation/README.md` "Data plane"):

```
run_batch ─→ batch_results/<session>.jsonl              (game log; self-stamped fingerprint + configs + game_id/trace_id)
          ─→ batch_results/eval_cases/<session>/<game>.jsonl   (per-game sidecar; pointer in eval_cases_path)
  → eval-build-* freezes cases ─→ frozen_eval_sets/<id>.jsonl (+ <id>.manifest.json)
       source = local sidecars (config `local_results`, PREFERRED — no Langfuse read)
              | or Langfuse traces (for games predating local emission)
  → eval-* runners ─→ eval_results/…                     (the judge side — out of scope here)
```

The **Langfuse read path** (`evaluation/src/data/langfuse.py`, the fallback) is the post-§4 design:
`trace.get()` to enumerate observation names/ids cheaply, then a name-scoped `get_many()` to pull only
the parent case-span with full output — with a batched server-side prefix-filter fast path and a
per-name fallback. A generic `fetch_spans` preserves the ability to retroactively mine *any* span into
a new case type later (a real benefit of a self-hosted archive).

### 2.7 Provenance stamping

**Why provenance.** Runs are comparable only if you know they used the same code, prompts, models, store,
and backend; without that stamp you get *silent staleness* (a result pointing at inputs quietly rebuilt)
and *unattributable confounds* — exactly why win-rate alone can mislead. Concretely: an early A/B saw the
*same* memory-on condition swing 96.7%→73.3% between batches, not from sampling noise but a quiet
store/namespace change underneath it — invisible without a stamp. The honest boundary: this buys
*traceability and drift-detection, not byte-reproducibility* — LLM output isn't byte-reproducible (temp-0
even differs across backends), so the target is statistical equivalence from a provably-identical setup
(`refactor/provenance_lineage_rationale.md`, `model_drift/drift_surfaces_and_guards.md`).

The mechanism produces four terms, easily confused:


| Term                       | What it is                                                                                                                   | Where it lives                         | Changes when                      |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------- |
| **git SHA** (`git_commit`) | the full commit hash (`git rev-parse HEAD`), plus a `git_dirty` flag for uncommitted edits to tracked files                  | inside`runtime_fingerprint`            | code is committed (or dirtied)    |
| **release**                | that*same SHA*, promoted to Langfuse's first-class, filterable trace field (§2.1)                                           | trace`release` column                  | = the SHA                         |
| **prompt_bundle_hash**     | SHA-256 (16 hex) over every`Agents/prompts/*.py` — a targeted fingerprint of just the prompts + rendering layer             | inside`runtime_fingerprint`            | a prompt / formatter file changes |
| **runtime_fingerprint**    | the*full bundle*: `git_commit` + `git_dirty` + `prompt_bundle_hash` + model IDs + temps/thinking + backend + embedding model | trace**metadata** + every batch record | any of the above                  |

**The join key.** The same `git_commit` SHA is written into *three* places: the trace's `release` field,
the trace metadata's `runtime_fingerprint`, and every `batch_results` JSONL record. Because the value is
identical in all three, it stitches them together. The workflow: filter traces by `release` in the UI,
read the full fingerprint from the trace metadata, line that up with the batch records, then
`git checkout` the exact code. Each form has its own job — **`release` is the cheap one-field filter,
`runtime_fingerprint` is the complete record, and the SHA is the join key between them.**
(`prompt_bundle_hash` is the sharper signal when you specifically care whether two runs had identical
prompts — e.g. comparing A/B arms across a code change that didn't touch prompts.)

Two layers, by design — **code vs data:**

- **Code level (git-versioned):** the `runtime_fingerprint` above. Model / prompt / backend are *code*,
  so they're versioned in git, not copied into the data. (Details: `evidence/prompt_versioning/`.)
- **Data level (case-stamped):** `EvalProvenance{store_dir, reranking_enabled, filtering_enabled}` on
  every `EvalCase`. The frozen dataset embeds the case but strips it from the trace, so without this the
  store/config that *conditioned a retrieval* is only recoverable by re-joining the trace. Stamping it
  on the case keeps the frozen record self-describing (its absence was that confound; closed as
  sufficiency-audit gap #4, §3).

### 2.8 Score capture — the seam to the evaluation system

The one place the capture layer touches the judge layer: after a game,
`push_scores_to_langfuse(game_metrics, trace_id, session_id)` (`Agents/compute_metrics.py`) writes
each non-null computed metric as a **Langfuse score** (`create_score`, `NUMERIC` or `CATEGORICAL`),
with a deterministic `score_id` for idempotency, scoped to the trace and (if present) the session. That
is the *capture* of scores — they become filterable/aggregatable alongside the traces. **What those
scores mean, how the deterministic proxies are designed and validated, and the LLM-judge pipeline are
the evaluation system, not this report** (`evidence/metrics/`, `evidence/memory_system/`).

## 3. How we verify capture is *sufficient*

The bar is not "does a trace appear" but "does a game emit **everything every downstream consumer
needs**." The method (the 2026-06-06 tracing-sufficiency audit): map the production eval pipeline →
catalog each consumer (judges, fine-tuning, replay) → find where a consumer needs a field the trace
doesn't carry. That audit found five gaps and has since closed four — #2 pre-rerank pool, #3 day-summary
case, #4 case-level provenance (all plumbing), and #5 the computed-metrics + night-decision dump (now in
each batch record, §2.6, and pushed to Langfuse scores, §2.8; night decisions are captured as
`EvalCase`s) — leaving only #1, the wolf-night case, deferred (§5).

Capture is checked on live smoke games, not asserted (raw logs in `implementation_notes/`):

- **Night-action coverage** (the Phase A#3 work): single-target night roles
  (healer/investigator/SK/vigilante) were routed through a new memory-informed night path so they emit
  an `EvalCase` + run retrieval like day actions. Verified across memory-off/on smokes: night eval
  spans emit, nest under the root, carry the correct `agent_night_action` target; in the decisive
  all-roles run the healer retrieved 3 obs + 3 strategy points on nights 2–4 and recorded adoption,
  while SK/vigilante correctly returned 0 (empty namespaces) — the branch fires, content arrives once
  populated.
- **Sufficiency live-check:** on a seeded all-enabled game, **72/72** eval cases carried
  `provenance.store_dir`, and **46/72** carried the pre-rerank candidate pool (the other 26 = day-1
  retrieval skips + empty SK/vig namespaces, both expected).
- **Source equivalence:** for a throwaway game, the local-sidecar build and the Langfuse build
  produced **identical `(trace_id, observation_id)` case sets** — proving the dual-sink shapes don't
  diverge.

## 4. Case study — the 422 collapse (2026-06-11)

Building a frozen eval set from Langfuse started failing with a **422** on heavy games: in one
5-trace session, **3 succeeded and 2 errored** — short games passed, long games didn't. The cause was
a latent inefficiency in the read side, not a tracing bug: the shared fetch helper pulled **every**
span of a trace via paginated `observations.get_many` (a 9-player sequential game logs hundreds–to–
thousands of spans) and filtered client-side, and Langfuse's query-cost guard rejects that once a
trace is large enough. The fix made **local emission the primary source** (the case was already built
in-process and dumped to the span — it just had no local sink) and reworked the Langfuse path into a
cheap `trace.get`-then-name-scoped-`get_many`. Result: all 20 `v5_seed_b*` games built with **zero
422**, every record's `formatted_discussions` full-length (20–43 KB). This is the incident that turned
"emit locally, tracer is secondary" from a nicety into the load-bearing rule (§1).

*The rest of this section is the forensic detail — skip by subhead (Cause / Why the obvious fixes
failed / Fix / Verification / Lessons) if the verdict is all you need.*

**Cause — the tracer was the primary eval store.** The eval cases were always built at game-time
(`turn/actions.py` for `EvalCase`, `orchestrator.py` for `ExtractionCase`) and dumped into span
output, but `run_batch` persisted only raw metrics — so the only way to *read a case back* was to
re-fetch it from Langfuse. As span volume grew (v5's longer games), the fetch-all read pattern crossed
Langfuse's cost guard. The instrument for *watching* a run had been quietly drafted into being the
*source of truth* for building eval sets, and it doesn't scale to that.

**Why the obvious fixes failed.** (a) Date-bounding doesn't help — the cost is the heavy trace's own
span count, already `trace_id`-filtered; a window inside its ~15-min life shrinks nothing. (b)
`trace.get` alone doesn't help — it enumerates all span ids in one call (no 422) but **truncates large
`output`** (the extraction span came back 8.3 KB with *no* `extraction_case` key, vs `get_many`'s full
38 KB) — so it can enumerate but can't carry the case content. (c) A naive name-scoped fetch grabs the
wrong span — the `postgame_extraction_` prefix matches both the parent case-span and per-role child
runs (§2.5), so the parent must be selected structurally.

**Fix (7 commits, dependency-ordered).** Span-name single source of truth (`span_names.py`) →
`EvalCaseSink` + `freeze_case` (the dual-sink, identical-shape design of §2.4) → tee at all five
emission sites → `run_batch` per-game sidecar + record pointers → builders gain the `local_results`
source with an input hash-chain to the batch run → Langfuse read rework (delete fetch-all; enumerate →
name-scoped fetch; keep generic `fetch_spans` for retroactive mining).

**Verification.** The repro session (previously 3 ok / 2×422) fetched all 5 traces (25–38 KB each);
the primary-path smoke wrote a 148-case sidecar read with **no Langfuse call**, and the local vs
Langfuse copies had **identical `(trace_id, observation_id)` sets**. Post-acceptance hardening found
live: the SDK's ~5 s default read timeout is too tight for `trace.get` on a fresh heavy trace
(~7 s on 1,439 obs) → now an explicit 120 s timeout.

**Lessons.**

- **The tracer is for watching, not for being your eval store.** Emit the gradable record to a durable
  local artifact at run-time; treat the observability backend as a *secondary* archive. The pattern
  transfers to any tracing stack.
- **Make the local and remote records the *same shape*.** One converter set then reads either source,
  and case identity is source-independent — no divergence to maintain.
- **Define span names once.** Producer/consumer drift across a rename is silent (the builder just
  matches nothing); a single source of truth makes it a compile-time-ish concern.
- **A latent inefficiency surfaces as a hard failure at scale.** The read pattern was "fine" on v4
  games; the same code 422'd on v5. Scale-test the read path against your *largest* expected trace.

## 5. Known gaps — what isn't captured / verified yet

Ordered by criticality (likelihood × impact × detectability). Each carries a freshness date so a later
reader knows whether to re-confirm. A gap stays listed even when minor — the list *is* the audit trail.

### Wolf-night discussion emits no `EvalCase` — criticality: medium

- **Gap.** Single-target night actions are first-class cases (§3), but **wolf night discussion is
  not** — it's a combined discuss-and-vote into `wolf_channel`, a different shape from a single-target
  pick, so it was deferred rather than forced into the day pattern. Consequence: the wolf-night
  decision is **absent from the eval pool**, so application/pipeline judging and any wolf-night memory
  read have no case to consume there. It's a coverage hole, not a correctness bug.
- **Considered solution.** A wolf-night `EvalCase` adapter (emission-only first, full memory context
  later); flagged to land with the deferred wolf-night `round`-schema cleanup.
- **Status — open, verified 2026-06-27.** Deferred since 2026-06-06; not yet built.

### `round` is vestigial in the eval layer — criticality: low

- **Gap.** The sequential scheduler hardcodes day `current_round=0`, but `round` still lives in
  `EvalCase.round`, span names, and frozen JSONL (and is genuinely load-bearing only in wolf-night's
  2-round loop). Its removal was deferred to a label-once regeneration cut where frozen data is rebuilt
  anyway, and comes out with the wolf-night-eval adapter above.
- **Status — open, verified 2026-06-27.** Harmless (a constant slot); a cleanliness item, not a risk.

### Pre-fix artifacts carry an empty day-summary `game_id` slot — criticality: low (historical)

- **Gap.** Day-summary spans before the 2026-06-11 fix read `game_id` from graph state (where it's
  unset) rather than config, so their names are `day_summary_eval__day_N`. Already-run games (incl. the
  v5 seed batch) keep the empty slot; join those by `trace_id`, which is the identity anyway. Fixed for
  all games since.
- **Status — closed for new games 2026-06-11**; the note remains for anyone reading old artifacts.

### Self-hosted assumption — criticality: low (context, not a defect)

- The 422 in §4 was a **query-cost guard on a self-hosted Langfuse**, not API rate-limiting; there are
  no external rate limits in this deployment. A managed-cloud move would add rate-limit considerations
  to the (now secondary) read path. Recorded so the §4 reasoning isn't misread as cloud-throttling.
- **Status — informational, verified 2026-06-27.**

---

## Key decisions (why this shape, not the alternative)

Each §2 section opens with why its piece exists; this table recaps the cross-cutting *shape* choices —
why each took the form it did, and what it rejected:


| Decision                                                                     | Why                                                                                                        | Rejected alternative                                                                         |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Shape each case eagerly at decision-time, not late-derived**               | decision-time-only fields (pre-rerank pool, private ctx) can't be rebuilt later; bulk late-read 422'd (§4) | late-bind: persist raw, derive cases on read — flexible but lossy + doesn't scale (§4)      |
| **Emit cases locally at game-time; tracer = secondary archive**              | the read path 422'd on heavy traces (§4); a local artifact you own is durable, scalable, offline-readable | keep the tracer as the eval store — doesn't scale (§4)                                     |
| **Local + Langfuse records share one shape**                                 | one converter set reads either source; case identity is source-independent                                 | two converters → silent drift between the sources                                           |
| **`Metrics` + `EvalCaseSink` on LangGraph runtime context, not graph state** | per-game accumulation, no global mutable state, no cross-game races                                        | module globals → races + manual reset between games                                         |
| **Single source of truth for span names**                                    | a rename can't silently strand a builder matching a stale prefix                                           | hardcode names on both sides → producer/consumer drift (the original bug)                   |
| **Provenance split: code in git, data on the case**                          | code is already git-versioned; only the data/config identity needs copying onto the frozen case            | stuff everything into the trace → not self-describing once frozen (the §3 gap-#4 confound) |
| **`release` *and* `runtime_fingerprint`**                                    | release = cheap first-class filter; fingerprint = complete record; SHA joins them (§2.7)                  | one or the other → either un-filterable or incomplete                                       |

---

## Sources & references

**Source logs (raw — the proof behind §3–§4):** `implementation_notes/experiment_log.md` (Phase A#3
night-eval coverage, 2026-06-06) · `implementation_notes/ISSUE_frozen_set_fetch.md` +
`implementation_notes/frozen_set_fetch_explained.md` (the 422 collapse + fix, 2026-06-11) ·
`implementation_notes/smoke_*.log`.

**Code:** `Agents/observability/` (sink + span names) · `Agents/tracing.py` · `Agents/main.py` ·
`Agents/schemas/evaluation.py` (the case schemas) · `evaluation/src/data/` (the read side) ·
`evaluation/README.md` "Data plane".
