# Pausing the game for a human

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

A person at the table plays at a person's pace. They may think for minutes before voting, close the
tab and come back, or return after the server has restarted, while the AI players around them
have already spoken, voted or chosen their night targets. Seating a human among AI agents therefore
asks three things of the game: stop at the human's turn and wait, survive a restart while waiting, and
continue without changing what the AI players already did.

The game runs on LangGraph, a framework that executes a program as a graph of steps and saves its
state after each one. I made a human's turn a pause inside the same pipeline as a model's turn, so a
human's answer is checked exactly like a model's. Pausing and surviving a restart needed no redesign.
Keeping the AI players' answers did: the first game with two human players showed that resuming re-ran
the AI votes, and some voters changed their minds. The fix took a cache of AI turns, a separate path
for human turns and a key that survives a saved-and-reloaded state. Two months later that cache served
one game's turn to another, because its key did not name the game.

### A human's turn is a pause in the same pipeline

Every turn, AI or human, runs one pipeline: build the seat's input, get a decision, validate it, apply
it. For a human seat, the decision step calls LangGraph's `interrupt()`, which stops the run. The
engine saves a *checkpoint*, a snapshot of the game's state, under the game's id; on the server it is
stored in PostgreSQL, so a paused game survives a restart. The server shows the human the legal
answers, and the answer resumes the run shaped like a model's reply, so it takes the same validation
and the same path to the game's resolution. A human who has gone away does not stall the table: the
turn is delegated to the seat's own AI agent.

The discussion already ran one graph *node*, one step of the graph, per turn, and LangGraph saves a
checkpoint between nodes, so the pause fitted the existing graph. Sharing the pipeline had two costs. A model's
line carries tags naming whom it questions or accuses, which the turn scheduler reads; a human's free
text has none, so a separate model call tags it
([Orchestrating the conversation](../conversation/conversation.md)). And a human's line enters other
players' prompts like any other line, unlabelled as human input; that gap belongs to the chapter on
information boundaries.

<!-- **Link (planned):** the unlabelled human line (map block 98) → chapter 2, "Secrets and untrusted
input". -->

### What the framework did at the pause

The first test game with two human players (2026-08-19) stopped at a day's vote. The server keeps its
own tally of the ballots it streams, as a cross-check, and it refused to broadcast a result the engine
had not reached: the server's tally said one player was voted out, the engine's said nobody was. The
first fix assumed ballots were being delivered twice and kept each voter's first ballot; the next game
failed the other way. A capture of everything the engine streamed showed the cause. When the human's
vote paused the round, the engine set aside the AI votes already cast; on resume it asked every AI
voter again, and some changed their minds. The server had been counting ballots the engine no longer
held. The tally now keeps each voter's latest ballot, so it converges on the set the engine counts.

That was one of three framework behaviours the pause exposed. Two of them involve *subgraphs*: the day
and the wolves' night each run as a graph of their own, called as one step of the main game graph.

| What happened | Cause | Fix |
|---|---|---|
| Every interrupt reached the server once per nesting level: twice, or three times from a subgraph inside a subgraph | LangGraph repeats an interrupt at every level it passes through | The server reads interrupts only at the top level, where each exists exactly once |
| The server's vote tally disagreed with the engine's | On resume the engine re-runs the step's AI votes, and some voters change their minds | The tally keeps each voter's latest ballot |
| A human's ballot opened only after the AI players had voted | An interrupt inside a subgraph reaches the server only when its parallel step ends | Human turns are announced when they are dispatched; the interrupt stays the only place an answer is taken |

*LangGraph 1.1.10, the version still pinned. The first two rows come from the 2026-08-19 test games;
the third was fixed on 2026-10-06, and for the wolves' skills on 2026-10-17.*

### Why the AI turns are cached, and the human's never

The re-run had a structural cause. LangGraph can resume a paused parallel step surgically, keeping the
results of the turns that finished and re-running only the paused one, but only for a subgraph it
manages itself. Here the day and the wolves' night are
subgraphs that a parent node calls like a function, building their input by hand, because that
hand-built input is the privacy boundary: the one place where what each seat may see is narrowed
([Executing a day and night](../day_and_night/day_and_night.md) explains the wiring). To LangGraph such
a node is a black box, so on resume it re-runs the whole node, and with it the AI turns of the step
in progress. In the nine-seat game, every human vote re-billed about 8 AI vote calls. A toy graph with no
model shows the difference:

> With the parallel nodes in the parent graph, the AI sibling ran once across a human's pause and resume.
> With the same nodes inside a subgraph called from a wrapper node, it ran twice.

*Toy graph, LangGraph 1.1.10, 2026-10-26.* The roles that act alone at night are ordinary nodes of the
main graph, resumed surgically, so they need no cache.

Letting LangGraph manage the subgraphs would make resumes surgical, but it would mean redesigning how
the privacy boundary is enforced. I kept the boundary and made the re-run free instead. LangGraph's
node cache records a node's result against its input and replays it when the same input comes again,
so a re-run AI turn returns its original answer without a model call.

Human turns cannot share that cache. A cached node that can pause crashed on resume in this version,
and still did when probed on LangGraph 1.2.14 (2026-10-07). On any version, a cache would be wrong for
a person: it would replay their old answer instead of asking. So each cached node has an uncached
twin, the same code under a second name, and the step that dispatches turns sends each human seat
through the twin.

The first verification game still made no cache hits. The cache's default key serialised the input
with Python's pickle, which encodes how an object was built as well as its values. A re-run's input is
rebuilt from the checkpoint, and the rebuilt object differed: the data-validation library records which
fields were set explicitly, four on the original and all ten on the rebuilt copy. Equal values gave a
different key, so the cache missed in exactly the case it existed for. The key became the input's
canonical JSON, its values in a fixed order, and a test round-trips a realistic input through the real
checkpoint serialiser and checks that the key is unchanged. After the fix, the verification game, which
dealt a human wolf, replayed 20 ballots from cache (17 day votes and 3 wolf kill votes), each identical to its original.
That is one nine-seat game (2026-08-19), in which the wolves still voted on their kill; in the ten-seat
game one wolf chooses it.

The re-run cannot spend a limited use twice. A Vigilante's bullet or an Investigator's check is
deducted only in the night's resolution, which runs after every night turn and computes the new counts
from the night's starting state, and a human's pause always comes before it. Tests check both halves:
the resolution run twice gives the same counts, and a scripted game whose human Vigilante pauses and
resumes with a shot ends with one bullet left. For one lineup and seed with a scripted model, that
shows the count is right, not that the step runs exactly once.

### Three things kept, three scopes

A pause depends on three different stores, and each keeps something different for a different time.

| What is kept | What it holds | Scope and limit |
|---|---|---|
| Game checkpoint | The game's state after every step, so a paused game can resume | Saved under the game's id; in PostgreSQL on the server, so it survives a restart |
| AI node cache | A finished AI turn's result, replayed when its step re-runs | In the server process's memory, for six hours; keyed by the turn's input and, since 2026-10-26, the game id |
| Provider prompt cache | An identical start of a model's input, reused by the model provider | Cuts the cost of reading input; never keeps an answer |

A surviving checkpoint does not guarantee a surviving cache entry: after a restart, or a pause longer
than six hours, the game resumes, but the AI turns in the paused step need fresh calls.

### A cache key must name its scope

On 2026-10-07 the day-1 opening round, in which every player may make a claim at once, adopted the
same cached pattern. A vote's input contains the day's transcript, which ties it to its game; a day-1
opening's input can hold nothing particular to its game. The key held no game id, and one cache serves
every game in the server process. On 2026-10-17 every model call in game `14926d10`, on Claude Haiku
5.5, failed, so each opening became a fallback pass. Nine minutes later game `51226f24`, on GPT-6 Luna
with the same lineup, made every opening call but one: its Serial Killer, the one seat whose role
matched, returned the same failed pass without a captured prompt. The record identifies it as a replay
of a fallback cached like an answer.

The fix puts the game id in every cached turn's input. Regression tests check that a key survives the
checkpoint round-trip and that two games' openings get different keys; the isolation test fails
without the game id. In a before-and-after control on two deals with a scripted model, the code before
the fix served five of the second game's openings from the first game's cache, and the fixed code
none; two Claude Haiku 5.5 games on those deals, back to back in one process, each made all ten opening
calls. The fix was deployed on 2026-10-26. It is the one cross-game replay in the record; how many
hosted games crossed before the fix is not known. Making the key stable enough to survive a
reload had also made it wide enough to span games.

**Link:** Explore how five reasonable choices composed into a key that crossed games →
[The cache key that crossed games](cache_key.md).

### Running the engine inside the web server

The graph runs the same way in batch runs and command-line play; this decision exists because a hosted
game streams to people in their browsers. The engine is synchronous: each step blocks while it waits for a model.
The web server is asynchronous: one event loop serves every connected viewer, so anything that blocks
it freezes every stream. Something had to absorb the blocking. On 2026-08-08 I chose among three
options:

- **A thread per game, bridged to the event loop.** The textbook pattern, but it duplicates the thread
  pool LangGraph already runs. Rejected.
- **Stream the graph through LangGraph's asynchronous API.** LangGraph runs the synchronous steps in
  its own thread pool, and the server's own code stays on one thread. Chosen.
- **Rewrite the engine as asynchronous.** About 89 functions and 23 call sites would change, and every
  synchronous user (command-line play, batch runs, evaluation runners) with them, for no visible
  change; a partial conversion would silently block the loop. Rejected.

Before migrating, a toy check with no model re-verified the behaviours the server relies on,
interrupts and cached replays among them, under the asynchronous API. The cost I accepted: the
boundary between blocking and asynchronous code sits inside LangGraph's thread pool, not in code the
server owns.

The pool needed sizing later. Its default of 8 threads on the 4-CPU server queued the checkpoint
writer behind about ten model-bound steps in one night, so a human wolf's prompt appeared seconds late
(observed 2026-10-17). The threads mostly wait on the network, so the server now runs 64.

### Checks and limits

**What the tests check.** A toy parent graph and subgraph are paused and resumed twice on one thread.
The test states its own blind spot: it would pass even if the helper that hands configuration to the
subgraphs returned nothing, because LangGraph also passes the checkpointer along implicitly, so that
helper is pinned by a unit test of its own. The cache key is tested for the checkpoint round-trip and
for isolation between games, and the limited uses as described above. A scripted model plays whole
games on the real graph through the server's streaming layer. These checks show the wiring works; they
say nothing about how people play.

**What is not established.**

- **A resume still re-runs the step.** A cache hit avoids the model call; a miss after six hours or a
  restart re-bills the AI turns and may change their answers. The latest-ballot tally keeps the result
  consistent with what the engine counted, not the original choice.
- **The cache assumes nothing outside a turn's input changes its answer within a game.** Switching
  the model mid-game would break that.
- **The server's event log can run one step ahead of the checkpoint.** A hard crash in that window
  could send a sequential turn's events twice. The window is one database write wide, and a blanket
  deduplication would also drop events that legitimately repeat, so it was accepted.
- **How many games the cache crossed before the fix.** One case is in the record. Only 11 of the 68
  hosted games have prompt captures, and restart times, which bound the cache, were not
  checked.

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

<!-- Completion note (2026-10-26)
Structure. The brief's seven subsections in its order. The featured story runs across subsections 2
(the tally) and 3 (cause, cache, twin, key), as the brief assigns it. The limited-uses passage
(block 165) is three sentences in subsection 3, not the plan's "one or two": both tests and the scope
needed their own clauses; cut to two if the owner prefers. Subsection 5 is two paragraphs, not the
plan's one: the incident, then the fix and its checks; one paragraph ran past 250 words. The incident
table keeps the plan's three rows (the orchestration report's table has six; the cache rows are told
in prose in subsection 3). The opening's roadmap paragraph was cut in the length pass.

For the verifier:
- "Two months later the same cache served one game's turn to another": one recorded case
  (2026-10-17), attributed by the record, not directly captured (player_9 has no captured prompt).
  The Level 3 brief's verification item 1.
- The control sentence combines two facts from the orchestration report's "What is not established":
  the scripted-model replay on pre-fix vs fixed code (5 → 0) and the two Haiku games on the fixed code
  (all ten opening calls each). Check that the Haiku pair ran on the fixed code (the report implies it;
  the deploy log's pre-flight is a separate check).
- "On 2026-08-08 I chose among three options": first person for a server decision; the design notes
  are written as "we". The orchestration code is the owner's; confirm the server decision is too.
- "The first test game with two human players ... stopped at a day's vote": §2 says the server
  crashed "at a day resolution" in the first real two-human test game; "vote" is the resolution of
  a day's vote.
- "Two Claude Haiku 5.5 games ... back to back in one process": not a served game; no statement about
  served games since the deploy is made.
Left off deliberately: test authorship and the "not yet audited" line; test counts (851, 1144); the
allowlist incident (§6) and the cookie path (§7, not chapter 1's); commit hashes in prose. -->
