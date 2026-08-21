# Server design notes — write-up seeds

> Parking doc (started 2026-08-08, during the owner's events.py/translate.py review). Each entry
> is a design argument that surfaced in review and deserves long-form treatment in the write-up's
> backend chapter — captured here so it isn't lost, NOT polished prose. Sibling docs:
> `event_derivation.md` (the wire contract), `server_client_transport.md` (transport decisions).

## 1. The part clock vs the checkpoint clock (why the translator never calls get_state)

The translator maintains its own shadow of graph state instead of querying the live graph.
The forcing argument is a race, not taste — the two clocks disagree in **both directions**:

- **State behind parts** (mid-superstep): stream parts are emitted as each task finishes, but
  writes only reach a checkpoint when the whole superstep commits. The spike proved LLM wolves'
  vote parts arrive while the human wolf's interrupt is still pending — `get_state()` at that
  moment doesn't contain votes the stream already delivered.
- **State ahead of parts** (consumer lag): the graph doesn't wait for the translator. Concrete
  failure: translating day 3's vote part after the graph already ran ONE_MORE_DAY —
  `get_state()` answers `current_day=4, day_votes=[]`. The ballots are wiped and the day stamp
  is wrong. The kernel cross-check would raise; without it we'd ship wrong data silently.

The shadow advances in lockstep with the parts, so every event derives from the world as of its
own commit. Testability is the dividend, not the driver: stream-only input is why the 307-part
fixture replays with no graph/LLM/checkpointer (18 offline tests, frontend mock data). Fair
concession if pushed: get_state + an injected state-provider mock could be made testable too —
but it stays incorrect under the race, so the mock buys nothing.

## 2. Translator state = a part-driven shadow of parent state, plus wire-only counters

Most translator fields mirror parent-state keys, rebuilt from the same deltas that built the
graph state (roles, current_day, wolves, targets, the vote buffers ↔ day_votes / wolf_channel
votes). Two fields have NO graph equivalent, and that's the state-purity principle in mirror
image: `seq` (the wire's global event counter) and phase-marker bookkeeping — the engine has no
`phase` key at all; phase is encoded positionally (which nodes are running), not as data. No
wire-only keys in graph state ⇒ wire-only bookkeeping lives in the translator.

## 3. Handler = node; the design lives in the rules, not the handlers

Each `_h_<node>` converts that node's delta into 0..N events (initialize_game → ~13,
post_game_analysis → 0), dispatched mechanically by node name, declared in the derivation doc's
walk order. After the module's load-bearing rules (cached drop, double emission, buffers,
kernel cross-check, exhaustiveness), each handler is boilerplate transcription of one ruled
table — which is the point: review the rules and _FOLDS, and the handlers audit themselves
against `event_derivation.md` side by side.

The one deliberate break in handler locality: entitlement buffers. Ballot content arrives in
`_h_vote` / `_h_wolf_night_vote` (emit nothing, store) and ships from `_h_collect_votes` /
`_h_collect_wolf_votes` (empty delta, flush the batch). Arrival ≠ release is the blind-voting
ruling made visible in code shape.

## 4. NIGHT_START: the owner overruled the lazy flag (a good reversal story)

Original design: no night anchor node exists (day→night is a conditional edge, and edges don't
stream), so the translator inferred night from the first night-scoped part, with a
`_night_announced` once-latch. Defended on engine-purity grounds (no wire-only nodes in the
graph) and fixture cost. Owner's counters, which won on 2026-08-08: (a) the graph already
accepts marker nodes (START_VOTING, START_WOLF_VOTE) and consistency matters; (b) it makes
`check_game_end_day` a clean binary (END_GAME | NIGHT_START) instead of end-check + fan-out
fused in one router. Result: NIGHT_START no-op node after the end-game check (ghost-night after
a final day structurally impossible — the owner spotted that hazard first), `route_night_actors`
fans out separately, translator inference deleted for a three-line handler. Cost paid: the
captured fixture predates the node — re-capture at the real-game smoke.

Write-up framing: phase is positional in the engine; the wire needs it as data; the design
question is WHERE to reify it (translator inference vs graph marker), and the answer moved when
the consistency + router-clarity arguments beat the purity + fixture-cost arguments.

## 5. Concurrency model: hosting a sync engine inside an async server (decided 2026-08-08)

**The problem** (the sync-over-async problem): graph.stream() is a long-running synchronous
generator that blocks for seconds per LLM call; FastAPI/uvicorn is a single-threaded event
loop. Run the game inline and every connected viewer freezes for every model call. Something
must absorb the blocking — the question is what, and who owns it.

**Options considered.**
- *(a) Dedicated thread per game* driving sync stream(), bridged to the loop with
  call_soon_threadsafe. The textbook pattern for a blocking workload in an async server
  (FastAPI does exactly this internally for sync route handlers), and it sat on the
  empirically verified path — every spike verdict and the 307-part fixture were captured on
  sync stream(). Cost: a hand-rolled thread boundary in application code (resume via
  thread-safe queue, every viewer-facing call bridged).
- *(b) astream() on the event loop.* Key subtlety that makes this NOT the obvious winner it
  first appears: the engine is 100% sync (zero async defs, zero ainvoke), and astream does
  not make sync code non-blocking — LangGraph runs sync nodes in an internal thread-pool
  executor. Threads never disappear; ownership moves into the framework. Gain: application
  code becomes single-threaded on the loop (asyncio.Queue resume, no bridge). Risk at
  decision time: async-path part semantics were unverified.
- *(c) Async-native engine* (every node async def, every call ainvoke) — the only option
  where asyncio genuinely replaces threads. Rejected: an engine-wide rewrite for zero
  user-visible change.

**Decision: (b).** The framework already owns the threads either way, so (a)'s explicitness
duplicates machinery LangGraph provides; and (b) is the design an async server reader
expects. The verification risk was closed before migrating, not accepted: a toy parity
check (no LLM) re-verified all four spike semantics on astream — v2 envelope,
interrupt-in-updates, mid-superstep sibling parts, cached-tag replay, all identical — plus
a fifth check that a time.sleep(1) sync node leaves the loop ticking (executor confirmed).
Migration landed same day, 851 tests green; the fake-graph and fixture tests pinned
behavior on both sides of the swap.

**Named trade-off accepted:** the blocking/async boundary is now implicit (inside
LangGraph's executor) rather than explicit in application code; (c) remains the eventual
clean end-state if the engine is ever rewritten async-native.

**The machinery, source-verified** (langgraph 1.1.10, `pregel/_executor.py`): fan-out
parallelism exists under EVERY option — a superstep's Send tasks run concurrently on both
APIs (measured: 8 parallel 0.5s nodes finish in 0.51s on sync invoke AND astream). What
differs is the scheduler. Sync path: `BackgroundExecutor` submits each task to a stdlib
ThreadPoolExecutor (cap min(32, cores+4)) — preemptive OS threads; the GIL serializes Python
bytecode but is released during I/O waits, so LLM waits genuinely overlap ("parallel
waiting, serialized computing"). Async path: `AsyncBackgroundExecutor` makes each task an
asyncio task — cooperative interleaving at await points — but sync node bodies are wrapped
in run_in_executor (`pregel/_call.py`), so under (b) the loop schedules while threads still
absorb the blocking; only (c) would run nodes as pure coroutines (cheaper per unit: ~KB
frame vs ~8MB thread stack reservation, userspace switch vs kernel context-switch — material
at thousands of concurrent waits, not nine). Bonus find: the async executor honors a
`max_concurrency` config key via a built-in asyncio.Semaphore — API-rate limiting at scale
is one config line, not custom code; per-game concurrency is structurally capped at ~9 live
agents regardless.

**Why (b) over (c), the arithmetic:** async is viral — the await must reach the LLM through
every intermediate function, so (c) converts the whole game-path call chain (~89 functions,
23 .invoke sites, the extraction fan-out), and a graph with async nodes can no longer be run
by the sync API at all, dragging every sync consumer (CLI, run_batch, eval runners, direct-
call tests) into the migration. A PARTIAL conversion is worse than either end: one sync
helper called from an async node blocks the loop silently — today's all-sync-nodes-in-
executor state is exactly what makes the mixed codebase safe. (b) buys over (a): a
cross-thread bug class made unrepresentable in application code, task cancellability, one
idiom. (c) buys over (b): executor-cap scale headroom and true cancellation (a cancel
propagates into the await and aborts the HTTP call; an executor thread runs its node to
completion) — significant only far beyond portfolio scale. The server code is identical
under (b) and (c), so (b) forecloses nothing.

## 5b. The `_games` dict and the two-step scaling story (2026-08-12)

`_games` is an in-process registry of LIVE MACHINES (running task + parked SSE generators +
graph mid-execution) — which is why "use Redis instead" is a category error: Redis holds
data, not half-finished computations. The design question decomposes into two independent
evolutions, neither needed at demo scale:
1. **Durability of the record (M2):** the losable value is each session's event log, and
   event sourcing makes the log sufficient — append each translated event to persistent
   storage (SQLite/Postgres/Redis Streams) and finished games survive restarts; the dict
   returns to registering only running machines. Cheap; single process preserved.
2. **Distribution of the machines:** at many-games scale, game workers run the graph loops
   and publish events into a broker (Redis Streams + consumer groups); the API tier
   subscribes and fans out to SSE. The dict dissolves (registry → keys, fan-out → streams);
   new costs: infra, serialization boundaries, cross-process resume for the human turn.
The punchline: the event-sourced wire contract makes both steps client-invisible and
translator-invisible — the log's schema IS the serialization format. The contract, not the
dict, is what future-proofed the architecture.

## 5c. Game failure modes — the fault model (2026-08-17)

Five distinct ways a viewer's game can be interrupted. Each has a different status, and the
statuses are the design story: solved-by-architecture / cheap-but-unwired / specified-unbuilt /
undetected. (Terminology: these are the server's *failure modes*; the list as a whole is its
*fault model*.)

1. **The viewer's side dies** (closed tab, back button, network blip) — **solved by the
   architecture.** The game never stopped; it runs server-side regardless of who watches.
   Recovery = reconnect and replay: the client reopens the stream from its last-seen event
   number and rebuilds its screen by re-folding events. This is what event sourcing buys —
   the recovery path IS the ordinary read path. (Remaining polish: honor the browser's
   automatic Last-Event-ID reconnect header — open ruling.)
2. **One game crashes** (exception in the engine, e.g. a dead BYOK key) — **surfaced
   cleanly; resumption possible but deliberately unwired.** The session records a redacted
   error, other games are untouched, the player starts a new game (ruled 2026-08-12).
   The nuance worth remembering: the process is still alive, so the game's checkpoints
   still exist in memory — a retry endpoint (re-enter the resume loop, e.g. with a fresh
   key) would continue the game from its last committed step with nothing lost. ~20 lines
   plus policy questions (which errors retryable, how often). Unbuilt by scoping choice,
   not capability.
3. **The server process dies** (crash, container restart, deploy) — **fatal today;
   fix specified, unbuilt (M2).** Everything is RAM: the registry, every event log (the
   truth itself), every graph checkpoint (MemorySaver). Every screen freezes; reconnects
   404. The fix is continuous persistence, never save-on-crash (a crash grants no notice —
   write-ahead thinking): engine = compile with the Postgres checkpointer (LangGraph
   already writes at every superstep commit; the swap only changes WHERE), wire = append
   each event to storage as it is born, recovery = reload checkpoints + replay logs.
   Accepted for the demo: live games are twenty minutes and disposable.
4. **A game hangs** (provider outage, stuck call — nothing fails, nothing moves) —
   **undetected.** No watchdog notices "no part produced for N minutes"; viewers see
   keep-alives and a frozen board. Missing piece: a stall timeout that converts a hang
   into mode 2. Punch-list item.
5. **The human goes AFK** (graph parked at their turn forever) — **undetected; policy
   undecided.** Not a malfunction — the system is doing what it was told. Needs a turn
   timer; the engine already has a legal random-fallback/technical-pass path a timeout
   could invoke. Related to the parked session-reaping question.

One-line summary for the write-up: the failure story is layered exactly like the recovery
story — the client layer heals by replay, the game layer by checkpoint, the process layer
by persistence; and the two liveness gaps (stall, AFK) are detection problems, not
recovery problems.

## 6. Smaller ruled arguments worth one paragraph each

- **input_request ships {player, action_kind, candidates}, never HumanTurnRequest**: the prompt
  payload is the event log re-rendered as prose (a second source of truth) and churns with
  every prompt epoch — the wire contract must not track prompt engineering. (2026-08-08)
- **day_summary keeps its gm_message-verbatim vote-result entry** (stream-completeness: the D+1
  recap card composes purely from day_summary events), while the night-side append folds (dawn
  gm_message opens D+1 directly below the recap card — adjacent duplication). Wire-level text
  repetition accepted; each page renders it once. (2026-08-08)
- **Annotations are separate events joined by about_channel_seq** because one event has one
  tier: the speech is public, its scheduler trace is observer-only. The join key is the
  state-side transcript seq (passes included), renamed channel_seq on the wire because the
  durable base class owns the global `seq`.
- **The reconnect model: three nested lifetimes, two cursor channels (ruled 2026-08-18, ①).**
  A viewer's connection has three layers that die at different times: the HTTP connection
  (dies on any blip; many per page), the browser's EventSource object (survives blips, owns
  auto-retry, remembers `lastEventId` from our `id:` lines; dies on page refresh/close), and
  the app's own persistence (survives refresh only if the frontend saves it). The two cursor
  channels map onto the two death boundaries: the **Last-Event-ID header** heals
  connection-death (the browser auto-reconnects with the ORIGINAL url verbatim — the query
  cursor is a fossil from construction — and carries its living position in this header;
  entirely client-side memory, the server stays stateless), and the **?last_seq= query
  param** heals object-death (page refresh, x-ray refetch, curl — a fresh object told where
  to start). Server rule: header wins when present (one line in event_stream; regression
  test pins it). Two supporting facts: pacing frames carry no `id:` line, so the browser's
  cursor only ever holds durable seqs; and mid-game REFRESH survival is a frontend job —
  persist the max seen seq (e.g. sessionStorage) into the new connection's query param,
  or accept a free full replay.
- **The reconnect cursor is tier-aware (ruled 2026-08-18).** `last_seq` honestly means
  "I have every event <= N *that I was entitled to when it was sent*" — for withheld tiers
  the cursor is a lie, and treating it as plain "I have everything <= N" silently drops the
  R7 reveal backlog below the cursor for reconnecting viewers. Two variants, same root:
  reconnect AFTER game over (the replay path skips the backlog) and reconnect MID-game with
  the unlock arriving live (the flush path skips it — the owner spotted this second variant
  during the code walk, which flipped the decision from a client-side contract to the
  server fix). Fix: `cursor_skips()` in `_sse` — skip as already-delivered only if
  `seq <= last_seq` AND the viewer was entitled LIVE; applied in both the replay and the
  flush. Regression tests pin both variants. Frontend note: a post-game "x-ray replay"
  button needs no server support — any client can refetch the full revealed log with
  `last_seq=0`.
- **BYOK (player-supplied API key): BUILT 2026-08-12, pattern 2 (ephemeral pass-through).**
  Key in POST /games → `GameSession` memory field → dies with the session; never on
  RunConfig (the runtime_fingerprint stamps configs into records — a key there would be
  persisted). Client-side-only BYOK is structurally unavailable because the game is
  server-side orchestration (the browser can't hold the wolf's identity). Delivery is a
  ContextVar (`llm_factory.GAME_API_KEY`), not an argument: set inside the game's asyncio
  task, and LangGraph copies task context into its worker threads — verified by toy
  (two concurrent games, different keys, every sync node saw its own game's key) — so
  ZERO node/helper signatures changed. Two factory consequences: `create_chat_model`'s
  memo key includes the game key (cross-game client reuse would bill the wrong player),
  and the accessor-level `lru_cache(maxsize=1)`s were removed (they'd freeze the first
  game's client process-wide). A per-game key also forces the google (API-key) backend
  over vertex — the player's key is a Developer-API key, and billing it is the point.
  Mid-game key death: surfaces via `GameSession.error` (key-redacted before viewers see
  it), player restarts with a valid key — ruled acceptable for v1. Tests: tests/test_byok.py
  (factory isolation, task-local delivery, redaction).
- **BYOK v1.5 same day (owner-ruled): multi-provider = tested-models-only registry.**
  `SUPPORTED_GAME_MODELS` (server/runtime.py) is the support policy as code: a model is
  selectable iff it has carried real games — the full Gemini suite that has (owner-ruled
  2026-08-12: 2.5-pro, 3.1-flash-lite default, 3.5-flash-lite, 3.6-flash) +
  deepseek/deepseek-v4-pro (CLI + HITL games) — and each row names its SAME-CREDENTIAL
  rescue model (None = rescue disabled; the typed technical-pass path absorbs failures)
  plus a display label: GET /models serves the frontend's selection menu directly.
  The rescue ruling: never ask for a second key and never bill the server for a BYOK
  game's rescue — derive the rescue from the same key, or don't rescue. The ContextVar
  grew into a `GameLLM(api_key, model, rescue_model)` struct; the key applies ONLY to the
  selected model's provider family, so off-family calls (Gemini pro extraction during a
  DeepSeek game) fall to server env credentials — moot live, since served games skip
  post-game extraction (`dump_enabled=False`). Per-game model selection also demotes the
  `.env` model vars to what they really were: local-dev/CLI defaults. OpenRouter was
  considered and deferred by the same policy — it is a DIFFERENT serving path (proxy
  tool-calling translation), so "DeepSeek via OpenRouter" is untested even though DeepSeek
  native is tested; it enters the registry the day its smoke game passes. Known gap: no
  per-provider structured-output validity harness exists — "tested" = survived real games;
  a cheap admission smoke (bind every game schema once per provider, ~8 calls) is the
  missing artifact if the registry is to grow honestly. GET /models serves the menu. OAuth-style delegation ("Sign in with Claude/ChatGPT") was
  considered and is unavailable, not just deferred: those tokens spend subscription
  entitlement (not metered API), are restricted to the provider's own/approved clients,
  and exist for no backend in our factory — a raw key is the only credential every
  provider shares.

## 7. The AFK fail-safe: delegate the turn to the seat's own agent (ruled 2026-08-20)

A solo game can wait forever — leave for lunch mid-turn and the game is simply paused for
you; nobody minds. Multiplayer breaks that luxury: the moment two humans share a table, one
absent player at a vote freezes everyone else, indefinitely. So multiplayer games carry a
pre-planned fail-safe — designed in from the start, not a patch — that keeps the game moving
without a missing player's input.

**The design that was discarded first.** The obvious fail-safe is a table of scripted
defaults, one per kind of turn: silently pass the discussion, abstain from the vote, hold
the vigilante's fire, pick a random legal target where the game demands one. Writing that
table out surfaced two facts that reshaped the plan. First, a pleasant one: a human may
*always* decline to speak in day discussion — even when directly called out — because the
engine deliberately treats a human's silence as an answer. Second, an awkward one: wolf
night-talk **cannot be passed at all** under the game's own rules. The rule-checker demands
a real message from a wolf, and the engine re-checks every answer on resume — there is no
way to sneak a silent default past it. The scripted-table design was therefore stuck
choosing between weakening that rule or putting canned words in an absent wolf's mouth for
the other wolves' AIs to read and react to as if their packmate had really said them.

**The ruling.** Neither. When the clock runs out, **hand the turn to the seat's own AI**.
One special answer — "delegate" — is legal for *every* kind of turn, and it tells the
engine: play this one turn for me, the normal AI way. Everything hard about that already
existed: the AI path's retries, its backup model, its last-resort technical pass if
generation fails entirely, and the billing plumbing that charges the game's own API key.
The absent wolf doesn't get canned words — their AI argues and votes with the pack for
real. About thirty lines of code, most of them the words "if the answer says delegate,
fall through to the AI path."

**The mechanics.** A 120-second stopwatch starts whenever the game asks a human for input —
but only in games with two or more human seats; solo games never arm it. Two details keep
it honest. The stopwatch is tied to the *exact question* it was started for, not to the
player: if you answer at second 119 and the game immediately asks you something new, the
old stopwatch — ringing at second 120 — recognizes that its question is gone and dies
quietly, so the new question gets its full two minutes. And if a real answer arrives at the
very moment the clock rings, whoever is second simply bounces off the same guard that
already ignores an accidental double-click. The "it's your turn" message sent to the screen
also carries *"and you have until 14:32:05"*, so the client renders a countdown without a
follow-up request. (The field is named `deadline`, not `timeout` — it is a moment in time,
not a number of seconds.)

**What to know.** Delegated turns are indistinguishable from AI play to everyone else at
the table — by design. The fail-safe also completes the lost-seat story from the
authentication design (transport doc §6b): a player who loses their seat credential on a
dead phone stops being a crisis — after each 120-second window their seat plays itself, the
table never stalls, and if they recover the credential they resume from their next turn.
That convergence — disconnection and absence being the *same* failure with the *same*
remedy — is the reason this game gets away with having no user accounts at all. One
boundary to respect: the timer never needs to know what kind of turn it is defaulting,
*because* the delegate answer is legal everywhere. If a future turn type ever makes
delegation illegal, the timer design breaks — don't do that.
