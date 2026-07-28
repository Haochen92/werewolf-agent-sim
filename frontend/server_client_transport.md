# Server ↔ Client Transport & Event Schema — Design Record

> **What this is:** the decision record for how the game backend talks to the frontend — the
> transport (SSE + POST), the wire pattern (an event log the client folds), the event schema
> (one discriminated union with audience filtering), and the relationship to LangGraph's own
> state. Each section states the problem, the chosen design, the alternatives considered and
> why they were dropped, and the trade-off knowingly accepted.
>
> **Status (2026-07-28):** design ruled; implementation of `server/schemas/events.py` in
> progress; server app + frontend not yet built. Companion docs: `frontend/design_log.md`
> (product design, esp. §8 pacing and §11 ghost mode), `Agents/schemas/game_events.py`
> (the internal transcript records these wire events are translated from).

---

## 1. The big picture — what actually travels

Three kinds of traffic cross the server↔client boundary, and only three:

| # | Payload | Direction | Channel | When |
|---|---------|-----------|---------|------|
| 1 | **GameConfig** | client → server | plain POST `/games` | once, at game start |
| 2 | **GameEvent stream** | server → client | SSE `/games/{id}/stream` | continuously, as the game runs |
| 3 | **input_request / HumanTurnResponse** | server → client / client → server | SSE event / plain POST `/games/{id}/action` | each human turn |

Two rules fall out of this table and never bend:

- **SSE only ever carries server → client data.** Anything the client sends (config, a vote,
  a speech) is an ordinary HTTP POST. SSE is a one-way pipe by design, not by limitation.
- **`input_request` and `HumanTurnResponse` are a matched pair, not one payload.** The server
  asks over SSE ("your turn — here are your legal targets"); the human answers over POST.
  They travel on different channels in different directions, linked by a `request_id`
  (a late or duplicate answer gets a 409, not a silent double-apply).

---

## 2. Transport: SSE + POST — not WebSockets, not a message broker

### The decision rule

> **Look at the *upstream* direction (client → server). If it is discrete, human-paced
> actions, SSE + POST wins. If it is machine-paced, high-frequency, or binary, you need
> WebSockets.**

Our upstream is a human clicking "vote" a few times per minute at most. That is the textbook
SSE + POST case.

### Why not WebSockets

| Consideration | SSE + POST | WebSockets |
|---|---|---|
| Fits our traffic shape | ✅ downstream stream + occasional upstream POSTs | ✅ but overkill |
| Auto-reconnect with resume point | ✅ built into `EventSource` (`Last-Event-ID`) | ❌ hand-rolled |
| Plain HTTP toolchain (auth, proxies, curl-debuggable) | ✅ | ⚠️ separate upgrade path, separate middleware |
| Needed for bidirectional? | POST covers our upstream fine | only wins when upstream is *continuous* |

The trap to avoid: "games like Town of Salem use WebSockets, so a game needs WebSockets."
Real-time *multiplayer* games have machine-paced upstream (cursor positions, keystroke-speed
chat, presence pings). Our upstream is a turn-based click. **"Uses WS in the wild" ≠ "needs
WS"** — much of the wild is ecosystem inertia.

*Trade-off accepted:* if a future feature ever needs continuous upstream (live voice, shared
cursors), SSE won't stretch to it and that feature would get its own WS endpoint. No current
or planned feature does.

### Why no message broker (Redis Streams etc.)

A broker earns its complexity when producers and consumers live in **different processes**.
Our server is a single asyncio FastAPI process: the game loop (producer) and the SSE
connections (consumers) share one event loop. The in-process equivalent is trivial:

- one append-only in-memory list of events per game (the log),
- one `asyncio.Queue` per connected subscriber (the fan-out).

We wrap this in a small `EventBus` class so that *if* the server ever splits into multiple
processes, the swap to Redis is one class, not a rewrite. That's insurance, not speculation —
we don't build the Redis path until a second process exists.

---

## 3. Wire pattern: an event log the client folds

### The four ways to keep a client in sync

When a server pushes updates over SSE, there are four broad patterns:

| Pattern | Each message contains | Example | History kept? |
|---|---|---|---|
| **State sync** | the full current state | Dota Oracle predictor (this owner's other project) | no |
| **Delta sync** | a diff/patch against last state | JSON Patch streams | no |
| **Event log** ← ours | one discrete fact ("p3 voted p5") | this project | **yes — the log IS the history** |
| **Notify-and-pull** | "something changed, come fetch" | webhook-style | no |

### The selection heuristic

> **Does the history itself have product value?** If yes → event log. If only the latest
> state matters → state sync.

For the Dota predictor, only the current prediction matters; last minute's prediction is
garbage — state sync was correct there. For werewolf, the history **is** the product three
times over:

1. **Live play** — the transcript on screen is the accumulated events.
2. **Reconnect** — a returning client replays the events it missed (§7).
3. **Replay mode** — a finished game's event file *is* the free-tier product, and the X-ray
   inspector is a richer read of the same log (§5, observer tier).

One list of ordered events, three consumers. State sync would rebuild each of those three as
a separate feature; the event log gets them from one artifact.

### What the client does with events

The frontend holds a **board state** (transcript, dead roster, phase, tally…) that is a pure
fold of events — a ~40-line reducer:

```ts
function onEvent(board: Board, e: GameEvent): Board {
  switch (e.type) {
    case "speech":       return { ...board, transcript: [...board.transcript, e] };
    case "death":        return { ...board, deadRoster: [...board.deadRoster, e],
                                  alive: board.alive.filter(p => p !== e.player) };
    case "phase_change": return { ...board, phase: e.phase, day: e.day };
    // ... exhaustive — the compiler errors if a variant is unhandled
  }
}
```

Key property: **the board is a disposable derived cache.** Throw it away, refold the log,
get it back. The client is never the source of truth for anything. And the frontend contains
**zero LangGraph code** — it speaks only `GameEvent`.

---

## 4. What this is NOT: pure event sourcing (a naming collision, defused)

"Event sourcing" names two different things at two different layers, and conflating them is
the most common critique this design will meet:

- **Layer 1 — wire format:** "send small facts; the client accumulates them." We do this.
- **Layer 2 — persistence architecture:** "the event log is the *database*; application
  state is derived by replaying it; the engine itself runs on the log." We deliberately do
  **not** do this.

> **One-liner: event-style on the wire, checkpoint-based underneath.**

### Where each truth lives

| Record | Is the authority for | If lost |
|---|---|---|
| **LangGraph checkpoint** | running the game: resume, HITL interrupts, crash recovery | a running game cannot continue |
| **Event log** | what each audience saw; replay mode; the X-ray record of *finished* games | running game unaffected; replay/history lost |
| **Client board state** | nothing — disposable render cache | refold the log |

Note the lifecycle split: for a **running** game the checkpoint is boss; for a **finished**
game the event log is the authoritative record (finished-game checkpoints are disposable).
That's why "presentation stream" undersells the log — the honest term is a **durable,
audience-filtered domain-event projection**.

### Why pure event sourcing was dropped

The litmus test: *"delete every LangGraph checkpoint — can the game restart from the events
alone?"* For us, no, and intentionally so. Making the answer yes would require:

1. **Rewriting the engine's memory.** In pure ES, reading state means folding the log and
   writing state means appending an event — the log IS the engine's memory. LangGraph
   already gives us exactly that fold structure internally (nodes emit deltas, reducers fold
   them, checkpoints persist it), with durability included. Pure ES means re-implementing
   what LangGraph already does, around a store we'd have to build.
2. **The marquee ES benefit has nothing to bite on.** ES's headline promise is "rebuild any
   state by replaying the log." We already own rebuild-and-resume via checkpoints. Building
   a second, everything-included record to earn an ability we have is work with no payoff.
3. **It would force every secret into one canonical log.** For replay-to-rebuild to work,
   the log must contain role assignments, night targets, scheduler internals — and that same
   log is what the server reads to feed clients. Every client-facing read would then touch a
   store containing all secrets, protected only by filtering code being correct forever.
   Our split is safer *by construction*: engine internals are never written into the wire
   log at all — you can't leak what isn't in the store (§6).

### Relationship between the log and LangGraph's records

The event log is **not** extracted from checkpoints. It is a translation of the stream of
*committed state updates*, observed live:

```
1. EVERYTHING that happens during execution
   (LLM calls, retries, validation failures, novelty-gate deliberation, prompt building)
        │   most of this never touches state — invisible to the stream by construction
        ▼
2. COMMITTED STATE UPDATES            ← what stream_mode="updates" hands the server
   {day_channel: [entry]}, {dead_roster: [record]}, {current_phase: "night"} ...
        │   translate() — the hand-written mapping (§8)
        ▼
3. THE EVENT LOG
   SpeechEvent, DeathEvent, PhaseChangeEvent ... (renamed, reshaped, audience-tagged)
```

A checkpoint is a *snapshot*; the log is a *history*. They are siblings derived from the
same execution, not parent and child. Two log entries come from outside the update stream:
`input_request` (born from the `__interrupt__` control signal) and `turn_started` (the one
deliberate pre-commit event — see §9).

### Caveat: checkpoint storage grows quadratically (bounded, mitigated, upgrade path known)

Verified in installed source (`langgraph 1.1.10` / `langgraph-checkpoint 4.1.1`, 2026-07-28):
append channels checkpoint their **full current value** every superstep they change
(`BinaryOperatorAggregate.checkpoint()` returns `self.value`), so cumulative checkpoint
bytes over a game grow triangularly — O(n²) across the history, though each *individual*
checkpoint is O(n) and unchanged channels are never re-serialized (savers write blobs only
for `new_versions`).

- **Why it doesn't bite here:** a full game's transcript is ~100 KB across a bounded run
  (~10 days, then over) → a few MB per game thread. Noise.
- **The real mitigation is retention, not channel format:** resume needs only the latest
  checkpoint, and the checkpoint's authority ends when the game does (see the truth table
  above). M2 rule: *finished game → event log persisted → checkpoint thread deleted.*
- **Upgrade path if the live service ever cares:** `langgraph 1.2` introduced
  `DeltaChannel` (`langgraph.channels.delta`) — per-step delta blobs + a full snapshot
  every `snapshot_frequency` steps (default 50), turning storage O(n²) → O(n) with resume
  bounded by walk-back-to-nearest-snapshot. Drop-in annotation swap for plain list-append
  channels (reducer must be batching-invariant; check the custom `merge_strategies` reducer
  before converting). Old full-value checkpoints migrate gracefully as base state. Not
  adopted at time of writing (we're on 1.1.10); revisit at the next LangGraph bump.
  Aside: `DeltaChannel` is LangGraph adopting for persistence the same
  deltas-plus-periodic-snapshot shape this design uses on the wire (§3, §7).

---

## 5. The event schema: one flat union, audience as routing

### Shape

One file (`server/schemas/events.py`), one vocabulary: ~12 small Pydantic classes, each a
complete self-describing fact, joined in a discriminated union:

```python
class SpeechEvent(BaseModel):
    type: Literal["speech"] = "speech"
    seq: int          # monotonic per game — the ordering + resume cursor
    day: int
    player: str       # or "game_master"
    message: str

GameEvent = Annotated[
    SpeechEvent | DeathEvent | VoteCastEvent | PhaseChangeEvent | ...,
    Field(discriminator="type"),
]
```

Every SSE message is **one small complete event** — never a growing blob, never a partial
patch.

### What qualifies as an event at all

> **An event is a committed game fact that at least one audience is entitled to learn.**

Two tests, both must pass:

1. **Committed** — it became game truth (a state commit; not a retry, not a gated
   candidate presented as speech). This is the §8 emission rule restated as a schema rule.
2. **Non-empty audience** — some seat, faction, or the observer/X-ray may know it.
   Scheduler internals fail this test and are never events.

The tempting-but-wrong definition is *"causes a UI change displayed to the user."* That gets
the dependency backwards — the UI is a *consumer* of events, so defining events by UI
effects makes the contract chase the renderer. Two concrete failures: `strategy_note`
changes no live player's UI at all yet clearly qualifies (the post-game X-ray is entitled to
it), and a single `death` event causes *three* UI changes (roster append, alive-list
removal, a toast) — counting by UI mutations would mint three events for one fact. UI change
is a consequence for tiers that have live UIs, not the criterion.

(The one sanctioned exception to test 1 is `turn_started` — pre-commit, but it asserts only
"X's turn began," which is already true when emitted. See §9.)

### The variant criterion — when a fact gets its own type

> **A fact gets its own event type when it has a different SHAPE or a different AUDIENCE —
> never because of who did it, and never because of what it does to the UI.**

The two-question test, both axes checked independently:

1. **Different shape?** It carries different fields than any existing type
   (`wolf_speech` carries `round`; `speech` doesn't → separate types).
2. **Different audience?** Even at identical shape, different clearance → different type —
   because the filter selects *whole events by type*, so audience must be decidable from
   `type` alone (never one type with an "is this the private version?" flag).

Same shape AND same audience → reuse the existing type. The two rejected axes, and why:

- **Who did it** (role-tagged variants): a role tag on day speech changes neither shape nor
  audience for the receiver — all day speech renders as the same chat bubble — so it carries
  zero renderable information while carrying the game's central secret (see the dropped-
  alternatives table below and §6).
- **Type of UI state change** (phase-change vs message-append): *append vs overwrite* is the
  reducer's business, not the vocabulary's. `speech` and `vote_cast` are both client-side
  appends yet are obviously distinct events — distinct *facts*; conversely "day advanced"
  and "phase advanced" are plausibly one fact → one `phase_change` event carrying both
  fields, even though clients fold it as two overwrites. The taxonomy is **domain facts,
  not UI operations** — events say what happened in the game; each client (live board,
  replay theater, X-ray) decides what that does to its own screen.

Putting both criteria together, the decision loop for any candidate fact:

```
Is it committed game truth?                       no → not an event (engine internal)
Is anyone entitled to know it?                    no → not an event
Is it derivable from already-public events?       yes → client-side derived state, not an event
Same shape+audience as an existing type?          yes → reuse that type
Otherwise                                         → new variant + audience entry, done
```

The third line matters more than it looks: a fact can be public *and* wrong to ship.
`no_lynch_streak` is public information, but it is a pure fold of events the client already
receives (`vote_cast`, `death`) — broadcasting it would create two sources of the same truth
that can disagree. Entitled-but-derivable facts are the client reducer's job.

Worked example — a future `heal_result`: committed ✓, healer-seat entitled ✓, no existing
seat-private type with that shape → new variant, `SEAT_PRIVATE` row in the audience map.

### Where events come from: three sources

Deriving the vocabulary from the state schema alone misses events, because not every game
fact lives in state. The stream chunk is `{node_name: delta}`, and **both halves carry
information**:

| Source | What it yields | Examples |
|---|---|---|
| **State deltas** (the dict half) | most events — committed facts | `speech`, `death`, `vote_cast`, `investigation_result` |
| **Interrupt signals** (`__interrupt__` chunks) | the human-turn handshake | `input_request` |
| **Node identity** (the name half) | facts encoded in *graph position*, not data | `phase_change`, `turn_started` |

The third source is easy to miss and worth dwelling on: **phase is not a state key anywhere
in this codebase.** "It's day" means "the `DAY_PHASE` node is running" — the topology encodes
it, so the state never says it. `translate()` therefore keys on node names as well as delta
contents: `INITIALIZE_GAME` commits → `phase_change(day=1)`; `START_VOTING` →
`phase_change("voting")`; `DAY_RESOLUTION` → `phase_change("night")`; `ONE_MORE_DAY` → dawn.

The general statement: some facts live in **data**, some live in **where the program counter
is** — and a wire contract must externalize both, because the client has no program counter.

### The four audience tiers

Audience is a **routing classification, not a schema structure** — the schema file is one
flat list; tiers are rows in a server-side lookup table:

| Tier | Who receives | Example events |
|---|---|---|
| **Public** | every connection | `speech`, `vote_cast`, `death`, `phase_change`, `game_over` |
| **Faction** | wolf seats | `wolf_speech`, `wolf_vote` |
| **Seat** | exactly one player | `role_assigned`, `investigation_result`, `shot_result`, `input_request` |
| **Observer** | **no playing seat, ever** | `strategy_note`, firing reasons, novelty-gate rejections |

```python
AUDIENCE: dict[str, Audience] = {
    "speech": PUBLIC, "death": PUBLIC, ...,
    "wolf_speech": FACTION_WOLF,
    "investigation_result": SEAT_PRIVATE,
    "strategy_note": OBSERVER,
}
```

The audience label is deliberately **not a field on the wire** — it's derivable from `type`,
and shipping it would invite client-side filtering (see §6 for why that's fatal). A dict
also makes the boundary mechanically auditable: an exhaustiveness test asserts every event
type has an audience entry.

**The observer tier is the X-ray.** During live play, observer events are appended to the
log but streamed to nobody. At `game_over`, the clearance flips: the finished game's full
log — thoughts included — unlocks for the (former) player, and replay mode reads it from the
start. Mechanically that's one boolean in the filter predicate
(`allowed(event, seat, game_finished)`), not a second log or format. What the X-ray shows is
what agents *committed* (strategy notes, gated candidates) — recorded state, not raw
chain-of-thought, which is never state and never logged.

### Alternatives considered and dropped

| Alternative | Why dropped |
|---|---|
| **Four per-tier unions / endpoints** | No connection receives exactly one tier — a wolf gets public + faction + seat events *interleaved in one ordered stream*. Per-tier partitions force the client to re-merge (union-of-unions = the flat union with extra ceremony) and turn one `seq` cursor into four. Tiers classify *routing*; types classify *shape* — orthogonal axes, don't fold one into the other. |
| **One big board-state blob per update** | State sync — loses the history that is the product here (§3), and oversends on every tick. |
| **Inheritance (`BaseEvent` subclasses)** | OpenAPI→TS codegen maps `allOf` hierarchies awkwardly; flat siblings with a shared envelope shape cost nothing and generate cleanly. (The minor reason — merely friction.) |
| **Role-tagged variants (`TownSpeechEvent`, `WolfSpeechEvent` for day speech)** | Fatal regardless of implementation: the role tag crosses the wire, and anything on the wire is public to that client (§6). Dead even with flat classes. |
| **One event type with per-audience field redaction** (blank fields per seat) | Leaks become field-level bugs the type system can't see; optional fields make weak TS types (`role?:` — redacted, or not applicable?). Whole-event include/exclude keeps the filter a one-line predicate and the leak test a stream-level assertion. **Rule: a different per-seat version of a fact = a different event type, never a mutated field.** |

*Trade-off accepted:* the flat union grows monotonically — every new fact-shape is a new
class. Fine at ~12–20 variants; would want namespacing at hundreds, which a fixed rulebook
game will never reach.

---

## 6. The security model: the wire is the boundary

> **Anything sent to a client is public to that client.** "The UI doesn't display it" is not
> a defense — the data sits in plaintext in the browser's network tab. This is a social
> deduction game; the entire product is "you don't know who the wolves are," so the
> incentive to press F12 is maximal (and the demo's audience is engineers).

Consequences, all following from that one sentence:

- **Filtering is server-side, per connection, whole-event.** The projection selects which
  events a connection receives; it never edits fields.
- **No secret-bearing metadata rides "hidden" fields** — no role discriminators on public
  events, no audience labels on the wire.
- **The engine's secrets aren't in the wire log at all** (§4) — defense in depth: one class
  of leak is impossible by construction rather than prevented by filtering.
- **The boundary gets a standing test**: `check_event_stream_isolation` joins the existing
  `tests/leak_test.py` `check_*` family, asserting per-seat streams contain no
  out-of-clearance events. Same principle as the prompt-payload leak tests — there the
  boundary is what enters the model's prompt; here it's what crosses the wire.

---

## 7. Reconnect and catch-up: replay the log, never send the checkpoint

**How reconnect works:** every event carries a per-game monotonic `seq`, sent as the SSE
event id. On a dropped connection, `EventSource` auto-reconnects and sends `Last-Event-ID`;
the server replies with only the **missed suffix** of that seat's filtered log. A fresh
connect (page load) replays the filtered log from `seq` 1. Either way, the client runs the
*same reducer* over the backlog as over live events — reconnect is not a special case.

**Why not send current state (the checkpoint) instead?** Three reasons, in order:

1. **The checkpoint is radioactive.** It contains every secret. Serving state to a seat
   would require a *second* per-seat filter — state-shaped, alongside the event-shaped one —
   doubling the leak surface and the leak-test obligation. The event backlog is by
   construction exactly what that seat was ever allowed to see.
2. **It would need a second wire schema and client path.** A `BoardSnapshot` DTO, its
   codegen, and "install snapshot, reconcile with events already held" client logic — the
   reconcile step is where sync bugs classically live. Suffix replay needs zero new code.
3. **There is no cost to optimize.** A whole game is a few hundred small events — tens of
   KB, folded in milliseconds. Snapshotting is a real optimization for *unbounded* logs
   (an event-sourced bank sends balance + recent deltas); our log is bounded by one game.
   If a future mode ever unbounds it, the snapshot would be a *derived, per-audience* fold
   of the filtered log — never the raw checkpoint (reason 1 is permanent).

---

## 8. Emission: events are born at commit points

The server drives the graph with `stream(..., stream_mode="updates", subgraphs=True)` and
translates each committed state delta into events — a **stream consumer**, requiring no
changes inside the graph:

```
LangGraph node commits a delta ──► stream yields {node: delta} ──► translate() ──► bus.publish(events)
                                   (interrupts arrive as __interrupt__ chunks
                                    in the same iteration → input_request event)
```

Why commit-point emission is a correctness rule, not a convenience: **the novelty gate can
veto a generated speech after generation**, and validation retries can discard model output.
Emitting at "end of LLM generation" would broadcast things that never became game truth
(ghost text that then vanishes). Listening at the commit boundary makes non-truth invisible
by construction — a retried call or gated speech never touches state, so it never becomes a
player-visible event. (The gated *candidate* does surface — as an observer-tier event, which
is exactly the said-vs-thought X-ray material.)

### Keeping the wire schema honest against the graph schema

Wire events are hand-translated from internal records
(`Agents/schemas/game_events.py` → `server/schemas/events.py`), **not** auto-generated from
them — deliberately: observability fields (`firing_reason`, `gated_candidate`) must not ride
public events, and the split keeps internal refactors from silently changing the public
contract. The coupling is confined to one function plus one alarm:

- **`translate()`** — the single place internal deltas become wire events.
- **An exhaustiveness test** — `assert set(state_keys) == MAPPED | IGNORED`: every state key
  is either explicitly translated or explicitly ignored. Add a state field and forget to
  decide → red test, not silent drift.

### Phase events: the marker table (deliberate hardcoding, alarmed)

The updates stream has **no entry signal** — chunks arrive at node *commits*, never at node
starts — so phase transitions are announced at the commit of the node that causes them, via
a hardcoded **marker table** in `translate()`: `INITIALIZE_GAME` → day 1 discussion,
`START_VOTING` → voting, `DAY_RESOLUTION` → night, `ONE_MORE_DAY` → dawn.

Hardcoding is the right call, not a shortcut: the table mirrors the graph topology, which is
itself static, in the same repo, versioned by the same commits — two representations of one
design, changed in the same PR. And there is no non-hardcoded alternative: deriving phases
from chunk namespaces at runtime still needs a mapping from node names to the client-facing
phase vocabulary (which is *designed* — flat, night-opaque — not the graph's internal
names); that's the same table smeared across inference logic, plus lag.

Two rules keep it honest:

- **Conditional edges disambiguate by delta content, not prediction.** `DAY_RESOLUTION`
  branches (night vs game over), so blindly emitting `phase_change("night")` at its commit
  would announce a night that never comes on a game-ending lynch. The branch condition is in
  the delta already (the winner determination): emit `phase_change("night")` only if no
  winner; else emit nothing and let `END_GAME`'s commit produce `game_over` — mirroring the
  routing function's own input, not guessing.
- **The node-axis exhaustiveness alarm** — the marker table's twin of the state-key test:
  `assert graph_node_names == PHASE_MARKERS.keys() | PHASE_IGNORED`. Add a node and forget
  to decide its phase consequence → red test, not silent drift.

Net effect: `translate()` is not a pure per-chunk function but a small **state machine over
the chunk stream** — per-chunk mapping + the topology table. The general coupling policy
this exemplifies (with the state-key table, the openapi.json drift guard, and the leak
tests): cross-boundary couplings are allowed; *silent* ones are not — name the coupling,
confine it to one place, and put an exhaustiveness alarm on it.

---

## 9. Typing UX: stream events, not tokens

(Ruled in `design_log.md` §8; recorded here because it's a transport decision.)

An agent's turn is presented as: `turn_started` event → typing indicator → beat → the
committed `speech` event, rendered with a **client-side typewriter effect**. No token
streaming, ever, because:

1. the novelty gate can veto a speech post-generation — streamed tokens would visibly vanish;
2. validation retries would show ghost text;
3. a corrected/retried message breaks the fiction of a character speaking.

`turn_started` is the schema's one deliberate pre-commit event: it announces "X is thinking,"
which is true the moment the node starts, and commits us to nothing about what (or whether)
X will say. The typewriter gives token-streaming's *feel* with none of its truthfulness
problems.

### Night pacing: there is deliberately no `night_progress` event

At night, seats without an action (villagers) or whose action resolved early would otherwise
stare at a silent screen. The fix is entirely client-side, because everything needed is
already local: the seat's own `role_assigned` ("you have no night action" / "you act after
the wolves"), `phase_change("night")`, and the night *order*, which is public rulebook
knowledge shipped as a frontend constant. The client fills the silence with ambient pacing
(flavor beats, a fixed-rhythm "night deepens…") that carries no information.

A *truthful* progress signal ("the healer is acting now…") is forbidden, not just skipped:
night sub-phase nodes are routed around when their role is dead, so real progress — even
night *duration* correlating with which sub-nodes ran — is a timing side-channel on
role-aliveness that the dead roster hasn't announced. Night's inner structure maps to:
nothing public; wolf-faction sees its own activity (`wolf_turn_started`); each acting seat
sees its own `input_request`. Public gets exactly two truths: `phase_change("night")` and
dawn's deaths.

This is the general division of labor at its sharpest: **the wire promises truth and order;
pacing and drama are the client's job** — the dawn-reveal beat (client may hold rendering
night deaths until the dawn `phase_change`), the typewriter effect, and the night-idle
screen are all the same rule.

---

## 10. How the frontend knows the shapes: generated types, one source of truth

Nobody hand-writes the TypeScript interfaces. The contract has exactly one authoritative
definition — the Pydantic file — and everything downstream is generated or tested against it:

```
server/schemas/events.py  (Pydantic, discriminated union)
        │  app.openapi() dump (script)
        ▼
server/openapi.json       (committed; contains oneOf + discriminator)
        │  openapi-typescript (frontend build step)
        ▼
generated .d.ts           (tagged TS union)
        │  import
        ▼
frontend reducer          (switch on `type`; compiler-enforced exhaustive)
```

- **Drift guard:** CI regenerates `openapi.json` and runs `git diff --exit-code` — a schema
  change that skipped regeneration fails the build.
- **SSE blind spot, fixed:** OpenAPI doesn't describe SSE payloads, so the union is
  registered in the spec via the replay route
  (`GET /games/{id}/events -> list[GameEvent]`) — a route we want anyway.
- **Every client build contains the full union** — a villager's client *knows the shape of*
  `wolf_speech`; it just never receives one. Privacy is which events the server put on your
  connection (§6), never which types your client was compiled with.

---

## Appendix: the one-paragraph version

> The backend drives the LangGraph game and, at each committed state update, translates the
> delta into small typed **GameEvents** — one flat discriminated union, each event tagged
> server-side with an audience (public / wolf-faction / single-seat / observer). A per-seat
> server-side filter selects whole events per SSE connection; the client folds its stream
> into a disposable board state with one reducer, and reconnect is just replaying the missed
> suffix by `seq`. Execution truth stays in LangGraph checkpoints; the event log is a
> durable, audience-filtered projection that doubles as the replay product and the post-game
> X-ray. **Event-style on the wire, checkpoint-based underneath** — SSE + POST because the
> upstream is human-paced clicks, and not pure event sourcing because the engine's state
> transitions include LLM decisions: replaying a log can't re-derive those, so making the
> engine run on the log would cost a rewrite to buy nothing, while keeping engine internals
> out of the log entirely removes a class of leaks instead of filtering it.
