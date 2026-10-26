# Orchestration: how a game runs as a graph

The orchestration layer turns ten independent players into one consistent game. Code controls the
phase order, information access and rule resolution; models supply player decisions and a few
language-processing steps. LangGraph provides the execution graph and checkpoints, so a game can
pause for a human and resume without a separate human-only engine.

The main trade-off is at that pause-and-resume boundary. The day and pack phases run as subgraphs
inside wrapper nodes. Resuming a human turn can re-run AI turns in the same parallel step. A node
cache reuses their answers, avoiding another model call **when the cache hits**.

A bug fixed on **2026-10-26** exposed a missing part of that design: the cache key identified the
turn's payload but not its game. Two games could therefore reuse the same opening answer, even with
different models. The recorded incident replayed a failed turn as a pass in another game. The fix
adds the game id to every cached turn's payload. This is a graph-execution cache, separate from the
provider's prompt cache used to reduce input cost.

The architecture connects explicit control flow, private turn payloads and checkpointed state.
The resume incidents show why those boundaries matter: a turn must receive the right information,
its result must merge into the right state, and a cached answer must belong to the right game. This
report owns those graph-level decisions; component
reports explain discussion policy, prompts, rules and evaluations in more detail.

Read [the current architecture](#a-game-today) first, then use
[the decision index](#decision-index) for the reasons and trade-offs. The
[cache incident](#the-cross-game-cache-bug-fixed-2026-10-26) separates the failure, fix and evidence.
[Checks](#how-it-was-checked), [limits](#what-is-not-established) and
[revision criteria](#when-to-revisit-the-design) describe what remains uncertain.

**Version and evidence.** The code described here is at `b9e445fd` (2026-10-26), which includes the
cache-key fix (`fd07c0f8`) and the `run_batch` guard (`c28ceacc`), with LangGraph 1.1.10 pinned. It
was first written against `588a3273`. Incidents and measurements belong to the versions named with
them. No alternative orchestration design was compared: the evidence consists of implementation
tests, recorded incidents and their fixes.

## The problem

A game has ten seats, and each AI turn normally requires a model call. Days, when the living players
talk and then
vote one player out, alternate with nights, when roles act in secret. Something has to decide who acts
when, what each actor is shown, what the actions add up to, and when the game ends. Four requirements:

- **Each turn comes in a defined order, with the right information**, and nothing private of anyone
  else's.
- **The state is shared and consistent.** Ten agents read one transcript and one record of deaths and
  votes, so an error in it reaches all of them.
- **A human can take any seat**: the game stops at the human's turn, waits, and continues, even after
  a server restart.
- **A failed model call has a legal fallback.** Provider or output failures should not leave the
  game waiting for an action it cannot resolve.

The key boundary is between rules and judgement: **code controls legal actions, state transitions
and outcomes; models choose actions and interpret language.** Models also summarise discussion and
classify some messages, so their errors can affect what later turns read. The orchestration layer
must make those contributions distinguishable from engine facts.

## A game today

### The parent graph

The game is a LangGraph state graph (`Agents/graphs/parent.py::build_parent_graph`). A *node* is a step
that reads the game's state and returns changes to it; an *edge* says which node runs next; a *router*
is an edge that decides in code. One cycle is a day and the night after it.

```text
START
  → INITIALIZE_GAME        deal ten seats from twelve roles, seeded by the game id
  → DAY_PHASE              the day subgraph, invoked from inside this node
  → DAY_RESOLUTION         count the votes; remove and announce the player voted out
  → check_game_end_day ─── a side has won, no side is left, or day 12 ──→ END_GAME
  → NIGHT_START            a marker: the night begins
  → route_night_actors     one parallel step:
       ├─ PACK_NIGHT_PHASE           the pack's subgraph, while a wolf is alive
       └─ <ROLE>_NIGHT_PHASE …       one named node per solo role that acts tonight
  → NIGHT_RESOLUTION       the barrier: every choice resolved at once
  → check_game_end_night ─ a side has won, no side is left, or day 12 ──→ END_GAME
  → ONE_MORE_DAY → DAY_PHASE …
END_GAME → POST_GAME_ANALYSIS → END
```

In the parent graph, nodes outside the day and night phases make no model calls. These include the win check
(`Agents/nodes/orchestrator.py::determine_winner`) and the post-game step, which saves the game for
offline lesson extraction. The night is one parallel step: the router lists the pack, if a wolf is
alive, and every solo role able to act tonight (`acts_tonight`). `NIGHT_RESOLUTION` runs once all have
finished, so it sees every choice, and applies the rules the
[roles report](../roles/report.md) states as "the night resolves in one pass"
(`Agents/rules/night.py::resolve_night`).

### The day subgraph

The day is a graph of its own (`Agents/graphs/day.py`), detailed in
[the discussion report](../discussion/report.md):

```text
START → START_OPENING ─ one Send per survivor ─→ round_turn | round_turn_human → COLLECT_ROUND
COLLECT_ROUND ─ day 1 ─────────────────────────────────────────→ SUMMARIZE_DAY_DISCUSSION
              └ voting day → SCHEDULE ⇄ discuss      (route_speaker sends one turn, or ends)
                             SCHEDULE ─ ended, someone has two accusers → START_CLOSING
                                       └ ended, otherwise ───────────→ SUMMARIZE_DAY_DISCUSSION
START_CLOSING ─ one Send per accused ─→ round_turn | round_turn_human → COLLECT_ROUND → SUMMARIZE…
SUMMARIZE_DAY_DISCUSSION ─ day 1 → END
                         └ voting day → START_VOTING ─ one Send per survivor ─→ vote | vote_human
                                                                               → COLLECT_VOTES → END
```

A `Send` starts one node with a payload built for it. **Rounds and the vote are parallel**: a router
sends every player in the round to the same node at once, and a collecting node is the barrier.
`COLLECT_ROUND` orders and numbers the round's lines, because turns run in parallel would each number
themselves from the same transcript (`Agents/nodes/day/flow.py::collect_round`). **The discussion is
sequential**: `SCHEDULE` is an empty hub whose router recomputes from the transcript who speaks next and
sends one turn to `discuss`, which loops back (`route_speaker`;
`Agents/turn/scheduler.py::select_next_speaker`). **The summary is one model call** recording the day for
later prompts ([day summary](../../extraction/day_summary/report.md)).

### The nights

**The pack's night** is the other subgraph (`Agents/graphs/night/pack.py`). The wolves chat one at a
time, the carrier first, for at most three rounds; a round of passes ends the chat early, and a lone
wolf skips it. The carrier, rotating through the living wolves in seat order, names the kill. Then each
wolf's own skill turn (the Chanteuse's block, the Illusionist's conceal) runs in parallel.

**Each solo role's night** is one parent node named after the role (`HEALER_NIGHT_PHASE`, …), all built
by `Agents/nodes/night/solo.py::solo_night_phase(role)`: one body that builds the payload, runs the turn
and returns the choice. What differs per role is data, from the registry
(`Agents/schemas/roles.py::ROLE_SPECS`: the action, the output field, the word for declining, the uses)
and from the role's card.

### State, and how a subgraph's result comes back

State is a typed dictionary per graph (`Agents/state/`). `OrchestratorGraph` holds the whole game;
`DayGraphState` one day, rebuilt each morning; `PackNightGraph` one night; `DayActorState` and
`NightTurnState` document one turn's payload. A *reducer* says how changes combine: the transcripts and
records append, each seat's private note merges by seat (`Agents/state/reducers.py::merge_strategies`),
and the night's choices accumulate across the parallel branches until cleared for the next night.

The two subgraphs are *invoked imperatively*: `DAY_PHASE` and `PACK_NIGHT_PHASE` are ordinary nodes that
build the subgraph's input by hand and call `.invoke()`. The result is folded back by hand too: the
subgraph returns its full updated transcript, and the wrapper returns only the new entries
(`result["day_channel"][len(sent):]`), which the parent's reducer appends once (`parent.py`, module
docstring).

**Checkpointing.** The parent is compiled with a *checkpointer*, which saves the state after every step
under the game's id: in memory for batch and CLI games (`Agents/memory/checkpointer.py`), in PostgreSQL
on the server, so a paused game survives a restart (`server/graph_runtime.py::GraphRuntime`). The
subgraphs inherit it through the config the wrapper passes down
(`Agents/config/langgraph.py::child_runnable_config`).

**The step budget.** LangGraph's `recursion_limit` caps execution steps, including loops through the
discussion scheduler. The root config sets 100,
which the pack's subgraph inherits. The day gets its own, computed each day from the survivors
(`discussion_recursion_limit`): two steps per discussion turn, for twice the speaking cap (a pass for
every real line), a pass by every survivor in each sweep and one drain turn per survivor, plus the
rounds and headroom for the summary and the vote.

### One turn, end to end

Every turn runs one pipeline, with an entry for day turns and one for night turns
(`Agents/turn/pipeline.py`):

1. **Payload.** A router builds it from state: the public record for everyone, private fields only for
   their owner (`flow.py::_private_fields`, `night_turn_payload`, the pack's `_pack_payload`). Nothing
   downstream narrows it, so this is the leak boundary ([agent_boundaries](../../agent_boundaries/report.md)).
2. **Human branch.** A human's seat pauses here for the human's answer (below).
3. **Memory.** Lessons from earlier games are added when memory is on for the role, never on day 1.
4. **The model call.** A structured-output call returns the seat's reads of every other player, its
   private note, then the action (`Agents/turn/agent_player.py::run_agent`). A target field lists only
   that seat's legal targets.
5. **Fallback.** A reply that breaks the schema is asked again; a stalled provider hands the turn to the
   game's rescue model, if it has one. A discussion turn that still fails becomes a pass; a vote or night
   action becomes a random legal move or the role's word for declining.
6. **Record.** An AI turn is saved as an evaluation case in the trace; the node returns one transcript
   line, vote or night choice, plus the note.

The prompt and the answer fields are [the turn-prompt report](../turn_prompt/report.md)'s; the echo gate
and the opening filter, which decide whether a line is published, are
[the discussion report](../discussion/report.md)'s. The prompt opens with the same text for every seat,
so the provider can reuse that input through its prompt cache
([turn prompt, decision 14](../turn_prompt/report.md#decision-14)). This saves input processing; it
does not reuse an earlier player's answer. Answer reuse is handled by the node cache described below.

### Who decides what

| Decision | Made by |
|---|---|
| The deal, the order of phases, when the game ends | Code: `initialize_game`, the routers, `determine_winner` |
| Who speaks next; when the discussion ends; who gets a closing turn | Code, from the transcript's speech-act tags |
| Legal targets; the night's outcome; the vote's result | Code: the output schema, `resolve_night`, `tally_day_vote` |
| Chance, when there is no reason to choose (a night-1 target) | Code, by lot ([turn prompt, decision 5](../turn_prompt/report.md#decision-5)) |
| What follows with certainty from a seat's facts; whether a claim fits the record | Code: the [deduction engine](../deduction/report.md), the claim ledger |
| Whether an opening line is of an allowed kind; whether a sweep line adds anything | One cheap model call each |
| What the day said, for later days | The summariser, one model call |
| What a player says, whom it suspects, its vote and night target, whether to pass | The player's model |

### What the agents share

Agents never message each other directly. They share four records, rebuilt into every prompt: **the
transcript** of today's published lines; **the game master's record**, the engine's exact announcements
of each night and vote; **the day summaries**, condensed accounts of earlier discussion; and **the
claim ledger**, every claim per player checked against the record, rebuilt by code for each prompt.

Because every seat reads the same records, one agent's error can become the room's premise. The July
2026 factual-error census (nine-seat) found errors clustered, the worst game-day having 24, with
examples of one
player's false premise becoming others' starting point
([factual errors](../../evaluation/factual_errors/report.md), step 1). In ten-seat game `e06` (read on
2026-10-10), the summariser turned "I was roleblocked" into a Chanteuse claim, and the real investigator
was voted out 7 to 1 ([day summary](../../extraction/day_summary/report.md) §7). The safeguards are
structural: each record is labelled by how far to trust it, with the game master's first; code, not the
summariser, checks claims; and a held line reaches no prompt.

### Human seats

A human seat takes the same pipeline. `run_human_decision` (`Agents/turn/human_turn.py`) calls
LangGraph's `interrupt()`: the run stops, the checkpoint is saved, and the server shows the human the
legal answers. The answer resumes the run and is shaped like a model's reply, so it is validated the same
way. A human who is away delegates the turn, and the seat's agent plays it.

Human support exposed several problems at the boundary between checkpoints, subgraphs and caching.
The server's record
([`server_encountered_challenges.md`](../../../frontend/docs/server_encountered_challenges.md)
§1–6, 2026-08-19, LangGraph 1.1.10) records these incidents and fixes:

| Problem | Cause | Fix |
|---|---|---|
| Each interrupt arrived once per nesting level: twice, or three times from a subgraph inside a subgraph (§1) | LangGraph echoes it at every level | The server reads interrupts only at the root, where each exists once |
| The server's vote tally disagreed with the engine's (§2) | On resume the engine re-runs the AI votes of the same step, and some voters changed their minds | The tally keeps each voter's latest ballot |
| Each human vote re-billed about 8 AI vote calls (§3) | LangGraph re-runs a whole imperatively invoked subgraph node, and its in-flight step | Cache the AI turn nodes, so a re-run replays the recorded answer (§4) |
| A cache on a node that can interrupt crashed on resume (§4) | A LangGraph limitation; also, a cache would replay a human's old answer | An uncached twin of each cached node, for human seats |
| The cache never hit (§5) | The default key pickles the payload, which differs after a checkpoint round-trip | A key from the payload's values (`turn_cache_key`); the next game replayed 20 ballots |
| A class missing from the checkpoint allowlist (§6) | Added to state, never registered | Registered; a test checks every model in state |

The current cached nodes are the day's `round_turn` and `vote` and the pack's `CARRIER_KILL` and `PACK_SKILL`,
with a six-hour lifetime intended to cover a human's pause. The cache lives in process memory, so
expiry or a restart can remove those saved answers even when the game checkpoint survives. The
report lists `discuss`, the pack's chat and solo-night nodes as uncached. Discussion and pack
chat turns run sequentially, so no AI sibling shares their step. Solo nights do run in parallel, but
as ordinary parent nodes, which LangGraph resumes surgically: a finished sibling's write is saved
with the checkpoint and only the paused node runs again. A toy graph on LangGraph 1.1.10 (2026-10-26,
no model) shows both wirings: with the parallel nodes in the parent, the AI sibling ran once across a
human's pause and resume; with the same nodes inside a subgraph invoked from a wrapper, it ran twice.
When a human wolf pauses inside the pack's subgraph, the parent re-runs only that wrapper; the solo
siblings keep their saved results.

### Checkpoints and the two caches serve different purposes

| Mechanism | What it retains | Scope and limitation |
|---|---|---|
| Game checkpoint | Execution state needed to pause and resume | Keyed by game id; PostgreSQL on the server survives restarts |
| AI node cache | A completed turn's returned result | Process memory, six-hour lifetime; the key now includes game id and payload values |
| Provider prompt cache | A reusable prefix of model input | Reduces input processing; it does not preserve an AI turn's chosen action |

A surviving checkpoint does not guarantee a surviving node-cache entry. The game can resume after a
restart, but AI turns replayed during that resume may need fresh calls. The recent bug concerned
isolation between games in the node cache, not persistence of the checkpoint or provider caching.

---

## The decisions behind it

Each decision gives the choice, what it was chosen over and why, the cost accepted, and the evidence.
Where no record gives the reason, the text says so.

### Decision index

| Question | Decisions | Evidence and remaining uncertainty |
|---|---|---|
| Where does control live? | [1–2](#decision-1): code-driven flow, one structured call per turn; the night resolved once | Stated principle; tests on the rules; no comparison with an agent-driven design |
| What shape is the graph? | [3–7](#decision-3): subgraphs only for phases with a flow, generic nodes, a node per discussion turn, parallel and sequential steps, the pack's night | Whole-game tests; the first subgraphs' reason not recorded |
| How does state move? | [8–10](#decision-8): one leak boundary, appended-slice fold-back, a computed budget | Leak checks on every batch game; one fold-back bug fixed |
| How does a human join? | [11–13](#decision-11): interrupts, cached AI turns with uncached twins, an async host | Resume incidents, one historical verification game, and the October cross-game cache fix |

### Where control lives

<a id="decision-1"></a>

#### 1. Code drives the flow; the model answers one structured question per turn.

- *The choice:* routers decide every transition. A turn is one call bound to the turn's schema
  (`with_structured_output` in `run_agent`). A seat has no tools.
- *Why:* each component's report states the principle. Discussion: "A model is used only where code
  cannot answer." Turn prompt: "Facts are computed by code; judgement is the model's", and the
  scheduler, ledger and vote count read the answer's fields. The deduction engine moved rule-based
  inference into code because seats holding the facts still failed to connect them.
- *Chosen over:* no record names a rejected alternative, and none says why a tool loop was not used.
- *Cost accepted:* the model can do only what a field allows. Legal targets live in the schema, so an
  enforced schema differs per seat and per vote; since 2026-10-14 Haiku's schema is written as text and
  checked in code ([turn prompt](../turn_prompt/report.md), "Model settings, validation and retries").

<a id="decision-2"></a>

#### 2. The night is resolved once, by code, after every choice is in.

`NIGHT_RESOLUTION` writes the deaths, each actor's private record, the uses spent and the morning
report. Night actions are simultaneous: a killed healer's protection still applies, and a killed
investigator's check happened but its result is not delivered
(`Agents/nodes/night/resolution.py::night_resolution`). Resolving after a barrier makes the order of the
parallel branches irrelevant. The rules are the [roles report](../roles/report.md)'s; tests pin them on
the resolution layer (`tests/engine/test_ten_seat_game.py`).

### The shape of the graph

<a id="decision-3"></a>

#### 3. A subgraph where a phase has its own flow; a named node where a turn is one step.

- *The rule today:* the day and the pack's night are subgraphs because each has an internal flow (a
  scheduler loop and parallel rounds; a chat, a kill and parallel skills). A solo night is one model
  turn, so it is one parent node.
- *How it got here:* the first graph files (2026-05-01, `db288e6c`) gave the day and each night role a
  subgraph (`day.py`, `healer.py`, `investigator.py`, `wolf_night.py`). **Why subgraphs were chosen then
  is not recorded.** On 2026-06-08 (`fbe4cff1`) they became one file per role, so that "adding a future
  night role is now a drop-in of parallel files". The ten-seat census listed "one subgraph, act node and
  state per role" among the assumptions to rewrite ([wiring census](../roles/phase3_wiring_census.md)
  §2), and on 2026-10-09 (`e874d2d9`) the solo roles' nights became named nodes sharing one body.
- *Why the collapse:* the commit says what changed, not why. The record implies the reason: with twelve
  roles, a subgraph per role gives every one-step night a state schema, a wrapper and a fold-back, while
  the registry already carries the differences as data. The names were kept "so the graph, the traces
  and the translator still read role by role" (`solo.py`, module docstring).
- *Benefits of retaining multi-step subgraphs:* each has its own recursion budget (decision 10),
  state schema and node cache, and it runs alone in
  tests (`test_day_rounds.py` compiles the day graph; `test_wolf_night_sequential.py` invokes the pack's).
- *Costs:* the fold-back and its 2026-07-23 bug (decision 9); config plumbing; an interrupt echoed per
  nesting level; a human's answer re-running the step's AI siblings (decision 12). And an interrupt in a
  subgraph reaches the server only when its parallel step ends, so a human's ballot opened after the
  agents had voted; human turns are now announced from the routing edge (`announce_human_turn`,
  2026-10-06; the pack's skills, 2026-10-17).

<a id="decision-4"></a>

#### 4. One generic node per kind of turn; the role is data.

In June the day had a named node per role (`villager_discuss`, `wolf_discuss`, …), because the scheduler
routed a speaker to the node named after its role; 12 day and 4 night functions had identical bodies
apart from the prompt, and factories removed the repetition (`d37369f`, `1db5d7b`, 2026-06-08;
[node-factory record](../../refactor/node_factory_pattern.md)). Today the day has one `discuss`, one
`round_turn` and one `vote` node; the role rides the payload and selects the prompt
(`Agents/nodes/day/actors.py`). The day graph's docstring states the rule: "role-specific *content* is
payload data, not topology." The cost, which the record implies: the day's graph and node-level traces
no longer read role by role, the reason the solo nights kept their names.

<a id="decision-5"></a>

#### 5. One node per discussion turn, looping back to the scheduler.

Each discussion turn is one `Send` to `discuss`, which returns to `SCHEDULE`. LangGraph checkpoints
between nodes, so each turn can be streamed, a game can resume after any turn, and a human's turn can
pause the graph. The cost is more steps per day, which the budget allows for (decision 10). The detailed
decision is [the discussion report's decision 5](../discussion/report.md#decision-5).

<a id="decision-6"></a>

#### 6. Use parallel turns for a shared snapshot; sequential turns for conversation.

A parallel step gives every player the same snapshot and waits for the slowest branch, rather than
adding every branch's latency: right for a
vote, a skill or a round of mostly passes. In open talk it produced near-identical lines, in the June
concurrent design and again in a parallel open floor tried and reverted on 2026-10-07. Sequential turns
cost one model call in series per speaker. The decisions and evidence are the discussion report's
[1](../discussion/report.md#decision-1), [7](../discussion/report.md#decision-7) and
[16](../discussion/report.md#decision-16).

<a id="decision-7"></a>

#### 7. The pack's night: a chat, the carrier's kill, then parallel skills (2026-10-09).

- *Instead of:* the nine-seat pack night, a sequential talk then a parallel binding vote on the kill
  (from 2026-07-26, `5ed2446f`).
- *Why:* the ten-seat rules give the kill to one wolf, who "performs the kill and is the only wolf who
  visits for it"; "there is no pack vote" ([role sheet](../roles/role_sheet.md), "Pack rules"; the vote
  was dropped in its 2026-10-08 check). The record implies the reason: the Sentinel and Trailseer see
  visitors by name, so one wolf must be the visitor. The skills follow the kill because the Illusionist
  decides on the victim (`pack_fan_out_skills`). The three-round cap was ruled on 2026-10-08.
- *Evidence:* `tests/engine/test_wolf_night_sequential.py` pins the routing (one chat turn at a time,
  the carrier first, the early end, the cap, a spent skill skipped). Three ten-seat games read in full on
  2026-10-09 ran every pack mechanic as specified ([discussion_evidence](../discussion_evidence.md) §8.2).

### How state moves

<a id="decision-8"></a>

#### 8. The payload builder is the one place information is narrowed.

LangGraph hands a `Send`-dispatched node its payload unfiltered, so the state types document the
intended fields but do not enforce privacy
([agent_boundaries](../../agent_boundaries/report.md) §1–2). One enforcer is one place to test: the
leak checks' first run (2026-06-06) caught 109 leaks from a refactor
([deterministic audits](../../evaluation/deterministic_audits/report.md), case 1). The server record
gives this as the reason the subgraphs are invoked from inside a node: the hand-built input is the
privacy boundary (§3). That invocation pattern also causes the resume behaviour addressed in decision 12.

<a id="decision-9"></a>

#### 9. Return only new list entries to the parent; merge notes by seat.

The parent's list fields append, so returning a subgraph's whole grown list would duplicate the history;
each wrapper returns the entries after the input list's original length. The per-seat merge comes
from a bug fixed on 2026-07-23 (`d1cbd2f8`).
The solo night phases folded back a one-key note into a field that overwrote, so each night wiped every
other seat's note. Its test records the damage: notes broken for every seat but the first night actor,
nearly all seats blank from day 2, and a corrupted end-of-game map that memory extraction reads. The
field now merges per key (`tests/engine/test_agent_strategies_merge.py`). The cost: each wrapper must
know what it sent, and a new list field needs the same slice.

<a id="decision-10"></a>

#### 10. The day's recursion budget is computed from the speaking cap.

The discussion loops once per turn, and the number of turns depends on who is alive. The function's
stated aim is that "the graceful cap always fires before an ungraceful GraphRecursionError": the budget
comes from the rules that end the discussion, so the cap and its drain end the day first. No record
names a rejected alternative. The cost is upkeep: the budget gained a term with each change to the day,
for the rounds, the drain and passing sweep turns ([discussion_evidence](../discussion_evidence.md)
§7.4).

### How a human joins

<a id="decision-11"></a>

#### 11. A human's turn is an interrupt inside the same pipeline.

Every turn already ends at a node boundary with a checkpoint, so the graph could pause for a human
without a redesign (decision 5). The answer is shaped like a model's reply, so both seats take one
resolution path and face the same legal actions (`human_turn.py`, module docstring). The cost: a
human's free text has no speech-act tags, so a separate model call tags it for the scheduler
([discussion report](../discussion/report.md), decision 8).

<a id="decision-12"></a>

#### 12. AI turns in parallel steps are cached; human turns go through an uncached twin.

- *Instead of:* making the subgraphs nodes LangGraph manages, so a resume continues only the paused turn.
  The server record names that alternative and its cost: redesigning the privacy boundary (§3).
- *Why:* a cache hit reuses the completed result, avoiding another model call and preserving the
  original AI choice. A human's answer comes from the person, not the
  payload, and a cache around `interrupt()` crashes on resume (§4), as it still did when probed on
  LangGraph 1.2.14 on 2026-10-07 (`day.py`, comment at the cached nodes).
- *Cost accepted:* two nodes per cached turn kind, and a cache kept in process memory for six hours.
- *Evidence:* the 2026-08-19 verification game, with a human wolf, replayed 20 ballots from cache (17
  day votes, 3 wolf kill votes), each identical to its original (§5). It ran on the nine-seat pack vote,
  since replaced.

##### The cross-game cache bug (fixed 2026-10-26)

**Failure mechanism.** The August key was computed from the turn payload's values, but the payload
had no game id. LangGraph scopes this cache by node and key, not by checkpoint thread. Because the
compiled subgraphs and cache serve every game in the process, identical payloads in different games
could retrieve the same answer—even when the games used different models.

Vote payloads include the game's transcript, which makes identical payloads less likely. The
opening round adopted the same caching pattern on 2026-10-07 (`b66ce7b4`), exposing a simpler
collision: a day-1 opening can contain no information unique to its game. In an offline check,
**8 of 66 pairs among 12 freshly dealt games** had at least one seat with identical opening keys.
That establishes reachable key collisions, not how often served games reused an answer.

**Recorded incident.** In game `14926d10` (2026-10-17 07:44, Claude Haiku 5.5), every model call
failed and each opening became a `generation_failed` pass. Nine minutes later, game `51226f24`
(GPT-6 Luna, same lineup) made every opening call except one. Its Serial Killer at `player_9`, the
one seat whose role matched, returned a `generation_failed` pass without a captured prompt. The
record identifies this as replay of the earlier game's failed turn: a fallback result had been
cached just like a successful answer.

**Fix.** The wrappers now copy the game id from the run config into subgraph state, and every cached
turn's payload carries it (`turn_cache_key`, docstring). This preserves reuse during a resume of the
same game while separating otherwise identical turns in different games. The regression test
checks that a payload retains its key through checkpoint serialization and that openings from two
games get different keys; the isolation test fails without the game id.

**Related checkpoint safeguard.** The same change makes `run_batch` reject paired game ids across
multiple configs in one process. The checkpoint thread is also keyed by game id: reusing it could
resume the second experiment arm on the first arm's finished thread. This is a separate identity
collision in checkpoint state, not another node-cache hit. No recorded run did that.

**Extent and remaining uncertainty.** One cross-game replay is identified in the served-game record.
The other 19 potentially matching served-game pairs show no copy; restarts clearing the cache are a
possible explanation, but restart times were not checked. Only 11 of 68 served games have prompt
captures, limiting detection. No recorded batch or capture game lost a day-1 call. The regression
tests support the key fix; this report records no served-game verification after that fix.

<a id="decision-13"></a>

#### 13. The synchronous engine runs under `astream` in the async server (2026-08-08).

Every node is synchronous, and `astream` already runs synchronous nodes in LangGraph's thread pool, so a
thread per game would duplicate the framework's machinery; an async engine was rejected as an
engine-wide rewrite with no visible change. A toy check with no model confirmed the four behaviours the
server relies on under `astream`, interrupts and cached replays among them, before migrating. The cost:
the boundary between blocking and async code sits inside LangGraph, not in application code
([`server_design_notes.md`](../../../frontend/docs/server_design_notes.md) §5).

---

## How it was checked

| What | How | How far to trust it |
|---|---|---|
| A whole game on the real parent graph | A scripted model fills whatever schema it gets; the game streams through the server's translator, for both drawn lineups, and every dealt solo role is routed (`tests/engine/test_ten_seat_game.py`) | The wiring runs end to end; no model, so nothing about play |
| Interrupt and resume through an imperatively invoked subgraph | A toy parent and subgraph, paused and resumed twice on one thread (`test_subgraph_interrupt.py`) | Its docstring warns it cannot check the config helper, which `test_child_config_unit.py` pins |
| Cache and checkpoint identity | A payload round-tripped through the real serializer keeps its key; two games' day-1 openings get different keys (`test_turn_cache_key.py`). Paired ids across multiple configs are refused (`test_run_batch_experiment.py`) | Regression coverage for key stability and game isolation; no post-fix served-game verification recorded here |
| State preservation | A one-key note update keeps other seats' notes (`test_agent_strategies_merge.py`); every model in state is allowlisted (`test_checkpoint_allowlist.py`) | Regression coverage for the note-merge and serialization failures |
| The pack's night, the day's rounds, human seats | `test_wolf_night_sequential.py`, `test_day_rounds.py`, `test_human_seat.py`, `test_human_turn_announced.py` | Implementation evidence |
| The leak boundary | Nine checks on every batch game, unit tests on each builder (`tests/leak_test.py`) | Covers the encoded leak cases; no later leak reported here |
| The cache in a real game | The 2026-08-19 verification game | One historical game, on the nine-seat pack vote; predates the October key fix |

The original review records that all tests named above passed on 2026-10-26. They are largely AI-written and
not yet audited.

## What is not established

- **No comparison with another orchestration design**, and no record of why a tool loop was not used.
- **The first subgraphs' reason is not recorded**; the October collapse's is inferred (decision 3).
- **How many served games the cache crossed before the fix.** One case is in the record (decision 12).
  Only 11 of the 68 served games have prompt captures, and for the rest a copied pass is visible only
  when its private note is distinctive; restart times, which bound the cache, were not checked.
- **Resume still re-runs the step; cache hits avoid fresh model calls.** A miss after expiry or a
  restart can re-bill AI turns and change their answers. Keeping each voter's latest ballot addresses
  tally disagreement, but does not preserve the original choice.
- **The October cache fix is not yet verified in served games.** It was committed on 2026-10-26
  (`fd07c0f8`) and deployed the same day (server image `2ecec0cc`: the live `dd985ebe` plus the fix),
  after a pre-flight in the production image found two dealt games' opening keys apart; no game has
  been served on it yet. Two games played back to back in one process on Claude Haiku 5.5 (2026-10-26),
  on deals chosen to share six seats' roles, each made all ten day-1 opening calls. The same two deals
  with the test suite's scripted model, run on the code before the fix, served five of the second
  game's openings from the first game's cache; on the fixed code, none.
- **The parent's recursion limit is the root default of 100**, not derived from the game's length.

## When to revisit the design

| Choice | Assumption to test | Evidence that would justify revisiting it |
|---|---|---|
| Imperatively invoked subgraphs (3, 8, 12) | Reusing completed AI turns on cache hits is an acceptable trade-off for retaining the current privacy boundary | Cache misses in served games, or a LangGraph release that resumes such a subgraph surgically or allows a cache around `interrupt()` |
| A named node per solo night (3) | Solo nights stay one step | A solo role gains an internal flow |
| A process-wide cache keyed by payload and game id (12) | Within one game, nothing outside the payload changes a cached turn's answer | A setting that changes a turn's answer mid-game without entering the payload, such as a model switch |
| One structured call per turn (1) | Every action is one code can list | An action code cannot enumerate, or information the payload cannot carry |
| The computed day budget (10) | Each rule that adds steps updates the formula | A `GraphRecursionError` in a day |

## Code and data

| Part | Code |
|---|---|
| The parent graph, the wrappers and the fold-back | `Agents/graphs/parent.py` (`build_parent_graph`, `day_phase`, `pack_night_phase`, `SOLO_NIGHT_PHASES`) |
| The day | `Agents/graphs/day.py`; `Agents/nodes/day/flow.py`, `actors.py` |
| The nights | `Agents/graphs/night/pack.py`; `Agents/nodes/night/pack.py`, `solo.py`, `resolution.py`; `Agents/nodes/orchestrator.py` (`route_night_actors`, `acts_tonight`) |
| Day resolution and the win | `Agents/nodes/orchestrator.py` (`day_resolution`, `determine_winner`, `check_game_end_day`, `check_game_end_night`) |
| State | `Agents/state/` (`orchestrator.py`, `day.py`, `night.py`, `reducers.py`) |
| One turn; human seats | `Agents/turn/pipeline.py`, `agent_player.py::run_agent`, `action_space.py`, `human_turn.py` |
| Config, budget, cache key | `Agents/config/langgraph.py` (`child_runnable_config`, `discussion_recursion_limit`, `turn_cache_key`, `TURN_CACHE_TTL_SECONDS`) |
| Checkpointers | `Agents/memory/checkpointer.py::durable_serde`; `server/graph_runtime.py::GraphRuntime` |

The records are `frontend/docs/server_encountered_challenges.md` §1–6 and `server_design_notes.md` §5
(the human seat and the server), [node_factory_pattern.md](../../refactor/node_factory_pattern.md)
(June's factories), [the wiring census](../roles/phase3_wiring_census.md) and
[discussion_evidence](../discussion_evidence.md) §7.4 and §8.2 (the October rebuilds).

*Written 2026-10-26 from the code and the linked reports; no new experiments beyond the offline
checks named in decision 12 and the resume toy in "Human seats".*
