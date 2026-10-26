# Adding a human in the loop

*Level 2 · [Game design and orchestration](../game_design_orchestration.md) · previous: [Turning an answer into a legal action](../legal_action/legal_action.md) (not yet drafted) · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Brief

Copied from [`../content_plan.md`](../content_plan.md), "Level 2 page briefs", section 5 (agreed with the
owner 2026-10-26); the plan keeps its copy until the owner moves it.

**Reader question:** what does it take to seat a human at a table of AI agents, when the game must stop
for the human, wait, survive a restart and continue without changing what the AI players already did?

**Promise:** interrupts, checkpoints, repeated execution, caching and the server host. The cross-game
cache incident remains optional deeper reading (Level 3).

**Open with the game:** a person at the table may think for minutes, close the tab or come back after a
server restart, while nine AI players have already acted. Then the framework.

**Featured story:** the resume that re-ran the AI votes, told as caught and fixed: (1) the tally, the
server's cross-check refusing a wrong lynch, the first-ballot fix crashing the other way, the latest
ballot kept; (2) the cause, a subgraph invoked inside a node is a black box, so a resume re-runs the
step, about 8 AI vote calls re-billed per human vote (nine-seat); (3) the cache, with an uncached twin
for humans; (4) the key, pickled keys never hit after a checkpoint round-trip, so canonical JSON; 20
ballots replayed.

**Subsections:** (1) a human's turn is an interrupt in the same pipeline (105, decision 11); (2) what
LangGraph did at the pause, the three-row incident table, LangGraph 1.1.10 (105); (3) why the AI turns
are cached and the human's never, the toy graph's two lines, the declined alternative, the evidence
scope, the limited-uses sentences (106, 114, 165); (4) three things kept, three scopes, the table
chapter 6 points back to (106); (5) a cache key must name its scope, one paragraph, the fix's
verification and no statement about served games since, the Level 3 link (115); (6) running the
engine inside the web server, three options, the parity check, 8 then 64 threads (111); (7) checks and
limits (114, 116).

**Level 3:** [The cache key that crossed games](cache_key.md), beneath subsection 5.

**Tags:** human-in-the-loop systems, checkpointing, cache-key design, asynchronous programming.
Reliability named without claiming exactly-once execution.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Not independently verified; the verifier
handoff is in the completion note at the bottom. -->

## Page copy (draft)

A human player may take minutes to vote, close the tab or return after a server restart. The game
needs to wait for that answer, then continue through the same rules that apply to the AI players.
The difficult part was preserving decisions the AI players had already made: in the first test with
two humans, resuming the game asked AI voters again, and some changed their votes.

I used checkpoints to save the game and a separate cache to reuse completed AI turns. These solve
different problems. The checkpoint survives a server restart; the cache lives in memory and expires
after six hours. The game can therefore resume after a restart, but it cannot guarantee the same AI
answers if those cached turns are gone.

### A human's answer enters the same turn pipeline

Every turn follows the same sequence: build the seat's input, get a decision, validate it, then apply
it. For an AI seat, the decision comes from a model. For a human seat, LangGraph's `interrupt()` pauses
execution until an answer arrives. LangGraph is the framework that runs the game as a graph of steps,
or *nodes*.

The server stores the game's checkpoint in PostgreSQL under its game id. It shows the human the legal
answers and submits the chosen answer in the same format as a model's reply. Both therefore pass
through the same validation and resolution logic. An absent human's turn can be delegated to the
seat's AI agent.

Sharing the pipeline also creates a small translation task. AI speech includes tags identifying whom
the speaker questions or accuses; the scheduler uses those tags to offer replies. Human text needs a
separate model call to add them, as explained in
[Orchestrating the conversation](../conversation/conversation.md). Human speech also enters other
players' prompts without a distinct human-input label; that information-boundary issue belongs to
chapter 2.

### Resuming the vote changed the ballots

The first two-human test game, on 2026-08-19, stopped at the vote resolution. The server maintained a
tally of streamed ballots as a cross-check: its tally said a player was eliminated, while the engine's
said nobody was. The check prevented the server from announcing that inconsistent result.

I first treated this as duplicate delivery and kept each voter's first ballot. The next game failed
in the opposite direction. Capturing the engine's stream revealed the cause: after the human answered,
the engine re-ran the AI votes. Some voters changed their minds, leaving the server counting earlier
ballots that the engine no longer held. Keeping each voter's **latest** ballot made the two tallies
agree. It did not prevent the repeated model calls or preserve the original decisions.

The pause also exposed two delivery behaviours at the server boundary:

| What reached the server | How I handled it |
|---|---|
| The same interrupt appeared at each level of nested graphs | Read interrupts only at the top level |
| A human's interrupt arrived only after the other turns in its parallel step finished | Announce the human turn when dispatched, while still accepting the answer only through the interrupt |

*These behaviours were recorded with LangGraph 1.1.10. Duplicate interrupts and the tally mismatch
were found in August; early turn announcements were added in October.*

### Reusing AI decisions when the step runs again

The repeated votes came from how I connected the graphs. The day and the wolves' night each run as a
*subgraph*, called from inside a parent node. That wrapper constructs the input explicitly to control
which information crosses the boundary. When the run resumes, the wrapper starts again, including the
AI turns in the interrupted step.

A model-free toy graph made the distinction visible: with parallel turns directly in the parent
graph, the completed AI turn ran once across a pause and resume; with those turns inside a subgraph
called by a wrapper, it ran twice (LangGraph 1.1.10, 2026-10-26).

I could have changed the subgraph wiring, but that would also require redesigning the information
boundary. Instead, I kept that boundary and cached completed AI turns. When the wrapper repeats a
turn with the same input, the node cache returns its earlier result without another model call.
Individual night actions that already run as ordinary parent-graph nodes do not need this workaround.

Human turns take an uncached copy of the same node. A human decision must consume the submitted
answer when resumed. In the tested setup, caching a node that could interrupt also caused resume
failures, including in a later probe on LangGraph 1.2.14. Dispatching humans to the uncached node
preserves the shared validation code without caching the interaction.

![Within the cache lifetime and server process, a resumed vote reuses cached AI ballots and accepts the human answer through an uncached node](../exhibits/pause_and_resume.svg)

*The vote with three illustrative AI seats. Cached ballots are reused only while their entries remain
available; a checkpoint alone does not preserve them.*

The cache initially missed even when the turn's values were unchanged. Its default key used Python's
pickle serialisation, which included object metadata that differed after loading a checkpoint. I
changed the key to canonical JSON: a consistent representation of the input's values. A round-trip
test checks that saving and reloading an input leaves its key unchanged. In one nine-seat verification
game on 2026-08-19, the fix replayed 20 ballots from cache, each matching its original. That game used
the earlier wolves' kill vote; the current ten-seat game gives that choice to one wolf.

Limited-use actions are handled separately. Bullets and investigation uses are deducted in night
resolution, after the human's pause, using the night's starting counts. Tests check that repeating
that calculation gives the same counts and that a human Vigilante's paused-and-resumed shot spends
one bullet. The latter covers one scripted game, lineup and seed; it does not establish exactly-once
execution.

### What survives a pause or restart?

The checkpoint and two caches have distinct jobs. Only the checkpoint stores durable game progress.

| Mechanism | What it retains | Boundary |
|---|---|---|
| Game checkpoint | Game state needed to resume | Stored in PostgreSQL under the game id; survives a server restart |
| AI node cache | Completed AI turn results | In process memory for six hours; keyed by turn input and game id |
| Provider prompt cache | A reusable prefix of model input | Reduces input-processing cost; does not retain the model's answer |

After a restart or cache expiry, the pending step can call the AI players again. The latest-ballot
tally keeps the announced result consistent with the engine, but the AI choices may differ from the
ones made before the pause. The cache also assumes the model and other settings outside the turn's
input stay unchanged during a game.

### A stable cache key also needs a game boundary

The opening round later reused the same cache pattern. Unlike a vote, an opening can contain no
transcript to distinguish it from an opening in another game. The key did not include the game id,
although all games in one server process shared the cache.

The October incident record attributes one game's fallback pass to a cached failed opening from an
earlier game. I added the game id to every cached turn's input. Regression tests check both
requirements: the same turn keeps its key after checkpoint reload, and turns from different games
get different keys. In a scripted before-and-after control using two deals, the old code reused five
openings across games; the fixed code reused none. The fix was deployed on 2026-10-26. The number of
hosted games affected before the fix is unknown.

The key has to recognise a repeated turn **within** a game without treating a similar turn in another
game as the same work. The incident and its verification are developed in
[The cache key that crossed games](cache_key.md).

### Hosting the game without blocking the web server

A hosted game must also keep browser connections responsive while model calls are pending. The
engine's steps are synchronous, but the web server uses an asynchronous event loop. Running a blocking
step directly on that loop would hold up other streams.

I considered three ways to connect them:

| Option | Decision and trade-off |
|---|---|
| Give each game a thread and bridge its events to the server | Rejected: adds thread management alongside LangGraph's existing pool |
| Use LangGraph's asynchronous streaming API with the synchronous engine | Chosen: blocking steps run in a thread pool while the server streams asynchronously |
| Rewrite the engine as asynchronous | Rejected: broad changes across the engine and its command-line, batch and evaluation callers; a partial conversion could still block the loop |

Before adopting the asynchronous API, a model-free check exercised the interrupt and cache behaviour
the server depends on. This kept one engine for hosted and batch games, at the cost of relying on
LangGraph to manage the boundary between blocking work and asynchronous execution.

Thread capacity still mattered. On 2026-10-17, the server's eight-worker pool queued a checkpoint write
behind model calls, delaying a human wolf's prompt. I increased the pool to 64 because those workers
mostly wait on network responses. That addressed the observed scheduling problem; it was not a
capacity benchmark.

### What the checks establish

The checks exercise pause and resume, stable cache keys, isolation between games, and limited-use
actions. Scripted games also run through the real graph and the server's streaming layer. The resume
toy alone does not test every configuration path: LangGraph can pass checkpoint configuration
implicitly, so a separate unit test checks the explicit forwarding helper.

These checks support the execution design, not a claim about the human playing experience or
exactly-once event delivery. In particular, the server can log a turn's events just before the
checkpoint is written. A hard crash in that interval could cause those events to be emitted again.
I accepted that window because blanket deduplication would also suppress legitimate repeated events.
The restart and cache-expiry limitation above remains: durable progress does not mean durable AI
answers.

**Evidence.**

- [Orchestration: how a game runs as a graph](../../../evidence/gameplay/orchestration/report.md),
  "Human seats", "Checkpoints and the two caches", decisions 2 and 11–13, "How it was checked" and
  "What is not established".
- [Server: encountered challenges](../../../frontend/docs/server_encountered_challenges.md), §1–6 (the
  pause incidents, the twin, the key) and §8 (the event log ahead of the checkpoint).
- [Server design notes](../../../frontend/docs/server_design_notes.md), §5 (the concurrency decision).
- [Deploy log](../../../frontend/docs/deploy_log.md), 2026-10-26 (the fix's deploy).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: content plan brief 5 ("open with the game"); orchestration/report.md "The problem" (a human
can take any seat; stops, waits, continues after a restart). "Two months later": 2026-08-19 → 2026-10-17.
Pipeline and interrupt: orchestration/report.md "One turn, end to end", "Human seats", decision 11;
discussion/report.md decision 5 (node per turn, checkpoints at node boundaries). PostgreSQL:
"Checkpointing" paragraph; server/graph_runtime.py::GraphRuntime. Delegation: "Human seats"
(server_design_notes §7, AFK fail-safe). Tag cost: decision 11; discussion decision 8. Unlabelled human
line: map block 98 (chapter 2's).
Tally story: server_encountered_challenges.md §2 (the cross-check "crashed" at a day resolution; first
fix kept the first ballot, next game crashed the other way; stream capture; last-write-wins). Incident
table: map 105; orchestration report "Human seats" table rows 1-2; decision 3 "Costs" (announce_human_turn
2026-10-06; the pack's skills 2026-10-17). Server doc §1 for "once per nesting level".
Black box and 8 calls: §3 (nine-seat; "~8 AI vote calls"); map 106, 110; orchestration decision 8.
Toy graph lines: orchestration "Human seats" (2026-10-26, LangGraph 1.1.10, no model); map 114. Solo
nights resumed surgically: same paragraph.
Declined alternative: §3; decision 12 "Instead of". Twin: §4; decision 12 (1.2.14 probe 2026-10-07).
Key: §5 (pickle; pydantic fields set, four vs ten; canonical JSON; round-trip test); 20 ballots, 17 + 3,
identical: §5 "Live confirmation"; nine-seat pack vote since replaced: decision 12 "Evidence".
Limited uses: map 165; orchestration decision 2 and "How it was checked" row; tests
test_uses_are_spent_in_the_resolution_once_per_night_and_a_decline_spends_nothing and
test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume (tests/engine/test_ten_seat_game.py).
Three stores: orchestration "Checkpoints and the two caches serve different purposes"; TTL six hours
(Agents/config/langgraph.py TURN_CACHE_TTL_SECONDS = 6 * 3600); map 106.
Cache key paragraph: orchestration decision 12, "The cross-game cache bug" (opening round adopted
2026-10-07, b66ce7b4; 14926d10 07:44 Haiku, all calls failed; 51226f24 GPT-6 Luna nine minutes later,
same lineup, player_9 Serial Killer, generation_failed pass without a captured prompt; "the record
identifies this as replay"); fix and tests (test_turn_cache_key.py); control: "What is not established"
bullet 5; deploy: deploy_log 2026-10-26 (2ecec0cc). Extent: 11 of 68 captures, restart times unchecked.
Lesson wording: map 115 ("a fix that makes a key stable can widen it").
Async host: server_design_notes.md §5 (options a/b/c; ~89 functions, 23 .invoke sites; partial
conversion blocks the loop; toy parity check before migrating; trade-off accepted); decision 13.
Sizing: server/app.py comment at set_default_executor (8 threads, 4-CPU host, ~10 model-bound nodes in
a night step, human wolf's prompt seconds late, 2026-10-17; 64 threads).
Checks: orchestration "How it was checked" (test_subgraph_interrupt.py docstring and
test_child_config_unit.py; test_turn_cache_key.py; test_ten_seat_game.py through the translator).
Limits: map 116; orchestration "What is not established"; server_encountered_challenges.md §8. -->

<!-- Editorial revision, 2026-10-26
The original brief remains above as planning history. Page copy now centres on the changed-ballot
incident, separates tally consistency from answer reuse, and states cache durability limits up front.
The interrupt table has two rows: the vote-tally incident is explained in prose rather than repeated.
Cross-game identifiers, the second model check and detailed key metadata remain in the source report
for the Level 3 draft. This was an editorial pass, not an implementation or experimental audit.
Verifier handoff: confirm the incident attribution (the missing call was not directly captured), the
recorded deployment, and the restart/resume scope before publication. No claim is made about served
games after deployment. The evidence/source list above is retained for tracing the draft.
-->
