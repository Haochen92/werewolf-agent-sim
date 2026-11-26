# U0. System architecture: the concepts, and a review of my system

**Reading time:** about 45 minutes · **Builds on:** nothing · **Feeds write-up chapters:** 7 and 8

**The question these notes answer:** when two parts of a system disagree about a fact, which one do
I believe?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

## What these notes cover

1. How to draw a system as components, and what each kind of component is responsible for.
2. Authoritative records: which store wins when two disagree, and how the other is repaired.
3. Trust boundaries, and where input has to be checked.
4. The main architectural choice, in-process work against separate workers, and what each costs.
5. A review of my Werewolf system against all four, ending with a claim about it that the code supports.

Table-by-table and function-by-function detail is in Appendix B, not in the body.

**Covered in other notes:** blocking work and the thread pool (U2), event logs and replay (U3),
redelivery (U4), who may read which record (U7), traces (U8), keys (U10), prompt injection (U11).
Where these notes touch one of those, they say only enough to place it on the diagram.

---

# Part 1 — The architecture of a system

## 1.1 What is system architecture?

The running example is an online ticket-booking application.

A customer visits the website, selects a concert seat, pays for it and receives a ticket by email.

From the customer's perspective, this feels like one application. But behind the scenes, different
components perform different jobs.

A simplified architecture looks like this:

```text
Customer's browser
        |
        v
     API Server
        |
        +----> Database
        |
        +----> Payment Provider
        |
        +----> Job Queue
                  |
                  v
                Worker
                  |
                  v
             Email Provider
```

Each component has a responsibility:

| Component | Responsibility |
|---|---|
| Browser (client) | Displays information and collects user input |
| API server | Processes requests and enforces business rules |
| Database | Persists orders, users and seat allocations |
| Payment provider | Processes payments |
| Job queue | Holds background work awaiting processing |
| Worker | Executes background jobs, such as sending tickets |

A worker that does the system's main work, and not a side job like email, is often called the
**engine**. A video site's transcoder is one; so is the part of my project that plays the game.

**System architecture describes how these components fit together, communicate and divide responsibility.**

It isn't primarily about which programming language or framework each component uses. The more
important questions are:

- What is each component responsible for?
- Why does it exist separately?
- How does information move between components?
- What happens if a component fails?

### Check

Suppose sending a confirmation email sometimes takes 15 seconds.

Why hand this to a background worker instead of making the customer wait while the API server sends it?

*Consider the user's experience, and what happens when the email provider is unavailable.*

<details>
<summary>Answer</summary>

The payment request can finish without waiting for the email. The API server records the successful order and queues an email job for background processing.

This improves response time and separates payment completion from email delivery. A worker can also retry temporary email failures.

However, the queue adds infrastructure and requires us to handle failed or duplicate jobs.
</details>

## 1.2 What are authoritative records?

A more subtle problem: the ticket system holds several representations of the same information.

- The database records that seat A12 is booked.
- The browser still displays A12 as available.
- A cache also says A12 is available.

Which one is right?

The system needs a defined **source of truth**, or authoritative record. In this example, the orders database
is authoritative for seat ownership. The browser and cache merely hold copies of that information.

```text
Orders database
  Seat A12: Booked
         |
         v
Availability cache
  Seat A12: Available   <-- Stale copy
         |
         v
Customer's browser
  Seat A12: Available   <-- Stale display
```

When the representations disagree, the orders database is trusted and the others are corrected.

The principle:

**Different components can hold related information, but each fact has one component with authority over it.**

And there may be multiple authoritative records in a system. For the ticket application:

| Question | Authoritative record |
|---|---|
| Who owns seat A12? | Orders database |
| Did money actually move? | Payment provider's ledger |
| Has the email job completed? | Job-status table |

The payment provider has authority over the payment itself, while the shop's database maintains
the application's order status. These are related facts, but they aren't identical.

Also missing from the table: nothing records what the customer's screen showed. The shop
knows what the server sent. What the browser rendered is a fact no store holds.

### Why does this matter?

Consider a crash immediately after the payment provider charges a customer, but before the shop's database records the payment.

The provider says "paid." The database says "pending."

Simply trusting the local database would be wrong. The fix is a recovery process that reconciles the status with the payment provider.

Knowing which record has authority says **where to look when components disagree and how to repair inconsistent state**.

### Quick check

A task queue says a background job has been delivered, but the database says its processing status is still "pending."

Does delivery prove the job finished?

**Answer:** No. Delivery means a worker received the job, not that it successfully completed it. That takes a separate completion record or acknowledgement mechanism.

---

## 1.3 What is a trust boundary?

Not every component in a system is equally trustworthy.

Consider this request to the ticket application:

```text
POST /purchase

seat: A12
price: $1
```

What if the actual ticket price is $150?

The browser is controlled by the customer. A malicious user can modify the request and submit whatever price they want. Therefore, the server must not blindly trust it. Instead, the server retrieves the authoritative price and validates the purchase.

This is a **trust boundary**: the line between the parts the operator runs and the parts they don't. Information crossing it comes from somewhere the operator cannot vouch for.

Common examples include:

- Browser → API server
- External payment provider → the application
- Uploaded document → an LLM application
- LLM-generated tool arguments → a tool that changes data

Crossing a trust boundary doesn't mean the input is malicious. It means it cannot be assumed safe or correct.

The rule:

**Validate information at the boundary where it enters a more trusted part of the system.**

U7, U10 and U11 go deeper. Here it is enough to mark where the boundaries sit.

---

# Part 2 — The main architecture choice

There isn't one correct architecture for every application.

Back to the ticket example. For a small shop with few customers, the API server might do
most of the work itself, in its own process. For a large ticketing platform, it makes sense to move
the main work out to separate workers.

| Design | What it buys | What it costs | Fits when |
|---|---|---|---|
| Main work inside the server process | One process to deploy; results reach the user directly, with nothing in between | A restart stops every job at once; jobs and web requests share one machine | Few jobs at a time, each watched live, one operator |
| Separate workers behind a queue | Workers scale and restart on their own; the API server stays small | A queue to run, a message format between processes, and replies must find the right worker | Many jobs, or jobs that run with nobody watching |

Neither row is the better design. A small application with a handful of concurrent jobs gets more
complexity than value from a queue and a worker fleet. A platform that needs thousands of
long-running jobs to survive restarts independently needs the second row.

The useful statement about any design is **what it gains, what it gives up, and when that trade is the right one**.

---

# Part 3 — My Werewolf system

## 3.1 The big picture

My Werewolf application lets people watch or join games played by AI agents. It is a browser, two
application containers behind a proxy, several model providers, and one Postgres database that holds
the records.

```text
 OUTSIDE (not mine)               ┆  MY HOST (Docker)
                                  ┆
 Browser ───── HTTPS ────────────▶┆  Caddy ─┬─ other paths ─▶ Next.js frontend (the pages)
   page + seat cookie             ┆         │
   watches:  one event stream     ┆         └─ /api/* ──────▶ FastAPI server (one process)
   acts:     POST a turn          ┆                             └─ GameSession, one per game
                                  ┆                                  │ drives
                                  ┆                                  ▼
                                  ┆                             LangGraph engine
 Model providers ◀─ prompts + key ┼──────────────────────────────────┤
 (several)        ── replies ─────┼─────────────────────────────────▶│
                                  ┆                                  ▼ writes
                                  ┆   Postgres (one database)
                                  ┆     games ............ identity, seats, status
                                  ┆     events ........... every event the game sent, in order
                                  ┆     checkpoints ...... the engine's saved state
                                  ┆     prompt_captures .. what each AI player was sent
                                  ┆     game_cast ........ which character stood at each seat
                                  ┆   Langfuse (its own stack) .. one trace per game run
```

For each part, this section says what it is responsible for and the design decision behind it.

### Browser, Caddy and the frontend

Caddy is the single front door. It sends `/api/*` to the FastAPI server and every other path to the
Next.js frontend. A browser watches a game over one long-lived event stream and acts by POSTing a
turn.

The frontend decides nothing about the game. It shows what the server sends and asks the server for
what the player wants; the rules run on the server.

### FastAPI server and GameSession

The server is one process. Each running game is one `GameSession` inside it, and that session does
three jobs: it drives the engine, it sends the engine's output to everyone watching, and it holds a
human player's question until their answer arrives.

**The engine runs inside the server process.** This is the first row of the table in Part 2, and it
is the main architectural choice in the project. What it buys: one thing to deploy, and the engine's
output streams straight to viewers with nothing in between. What it costs: a restart stops every
running game at once, and games share the machine with web requests. The first cost is why the
records in 3.2 exist. The second is U2's subject.

### LangGraph engine and the model providers

LangGraph runs the game as a workflow: the phases, whose turn it is, and each AI player's decision.
For every decision it sends a prompt to a model provider and reads the reply. The providers are
outside services, paid per call.

### Postgres

One database holds every record of a game. Nothing that matters lives only in the server's memory,
which is what lets a game continue after the process restarts.

### Langfuse

Each game run is one trace in a self-hosted Langfuse: every model call, its prompt, its reply and its
timing. A trace is for investigating what happened. The game never reads it, so it is not one of the
game's records. U8 covers it.

## 3.2 The system keeps different kinds of records

This is the part of these notes that matters most for my project.

My Postgres database holds five records of a game. Each answers a different question.

| Record | Question it answers |
|---|---|
| `games` row | Which game is this, who sits where, and is it running, completed or dropped? |
| `events` | What did the game send, in what order, and who may see each event? |
| LangGraph checkpoints | Where is the engine, and what does it need to carry on? |
| `prompt_captures` | What was each AI player sent? (Written when the game ends, for the leak audit.) |
| `game_cast` | Which character stood at each seat? |

(Token usage is also kept, as a column on the `games` row.)

### Example: a game is interrupted

The server restarts in the middle of a discussion. Before it went down, the engine was partway
through the day, several lines had been spoken, and viewers' browsers were showing them.

When the server comes back, it has two different questions to answer.

**Question A: where does the engine carry on from?** From its checkpoint. On boot the server
rebuilds each running game from its `games` row, its events and its cast, and the engine resumes
from the last checkpoint.

**Question B: what does a reconnecting browser receive?** The `events` table, replayed in order,
with each event passed through the audience rule for that viewer's seat.

Why not use the checkpoint for both? Because the two records hold different things. The checkpoint
is the engine's entire state: every seat's role, every private finding, everything the engine needs
to take its next step. It is not a list of what was shown, and it is not safe to show. The event log
is the opposite: an ordered list of what the game sent, where each type of event has an audience
(everyone, the wolves, one seat, or observers only). A viewer's feed can be rebuilt from the second
and cannot be rebuilt from the first.

The two are also written at different moments. An event is saved as soon as the engine produces it.
A checkpoint is saved only when the whole engine step has finished. So after a crash, the event log
can be up to one step ahead of the checkpoint: the engine restarts from a point that doesn't yet
include work whose events were already sent. I found this on 2026-09-12. **Two durable records of
the same game are not automatically in step with each other.** How the re-run is absorbed belongs to
U3.

### Check

A viewer reconnects after their browser crashes.

Which record is used to replay the events they missed: the event log or the LangGraph checkpoint? And what must the server apply while replaying?

<details>
<summary>Answer</summary>

The event log. It keeps what the game sent, in order, and each type of event has an audience.

The server applies the audience rule for the viewer's seat as it replays, so a spectator's replay
leaves out what only the wolves or one seat may see. The checkpoint is for the engine, and it holds
every secret in the game.
</details>

## 3.3 Where are the trust boundaries?

The dotted line in the diagram is the trust boundary. Two things sit outside it.

**The browser.** Anyone can craft an HTTP request, so the server checks every turn twice. First,
who is asking: the seat cookie must prove a seat in this game, or the request is refused. Second,
what they are asking: the answer must fit the question that seat was actually asked, so a player
cannot vote when it isn't their vote or name a target the turn doesn't allow.

**The model providers.** A reply is text from a service I don't run. The engine parses every reply
against a schema before using it, and the game's rules run in my code, not in the model. The
boundary is crossed in the other direction too: every prompt, and the API key, leave my host.
What goes into a prompt is therefore a decision about what leaves.

### A different line: who may know what

There is a second kind of line in this system, and it is worth keeping the name separate. Inside the
trusted side, the engine knows everything, and no player may. The Investigator's findings must not
reach another player's prompt or a spectator's screen.

That is an **authorization** rule, not a trust boundary: the data is yours and correct, and the
question is who may read it. My project enforces it in two places. Each AI player's prompt is
built only from what that seat may know. Each event has an audience, checked per viewer at the
moment it is sent. U7 examines how well those hold.

---

# Part 4 — What would change at a larger scale?

Suppose the application had to run hundreds of games at once instead of a handful.

One server process could no longer hold them, and one restart would interrupt all of them. The
redesign is the second row of the Part 2 table:

```text
Browsers
   |
   v
API servers
   |
   v
Job queue
   |
   +----> Game worker A
   +----> Game worker B
   +----> Game worker C
               |
               v
        Shared persistence
```

Workers now scale and restart independently of the API servers. Each thing the single process gave
for free becomes a question to answer:

- How does a human's answer reach the worker running their game?
- How does a worker's output reach the API server holding the viewer's stream?
- How is a game recovered if its worker disappears?
- What stops two workers from running the same game at once?

My current design answers all four the same way: there is one process, so everything is already
in the same place. That is what "simpler" means concretely, and it is why the design fits a few
live games and one operator.

These are not answered here. They are the context for U2 to U6.

---

# Part 5 — Worked problems

Each is answered from memory first; my answers are in Appendix A.

## Problem A: The same concepts in another system

An AI contract-review service. A lawyer uploads a contract. An LLM analyses it, identifies risky clauses, and returns findings for the lawyer to accept or reject. The analysis can take several minutes.

1. Identify the main components of the system.
2. Which record is authoritative for the lawyer's final decisions? For a review's status?
3. Should the analysis run inside the API request or in a background worker, and why?
4. Identify two trust boundaries.

## Problem B: My system, without the diagram

1. What the frontend, FastAPI server and LangGraph engine are each responsible for.
2. Why the project needs both checkpoints and an event log.
3. One advantage and one cost of running the game engine within the server process.

In plain words, not vocabulary.

## Problem C: A claim, checked against the code

A draft sentence for the write-up:

> "My server keeps five records in Postgres, and the events table tells you exactly what each player saw."

What in it is supported, what isn't, and what is the accurate wording?

## Problem D: A system I know

A component diagram of a system that is not this project: an app I use, or something from a
previous job. Mark the trust boundary, and for each store write the fact it is the record of.
Then find one copy in it that could go stale.

---

# Part 6 — Summary

**1. Architecture is about responsibilities and interactions.** A component diagram shows which parts exist, what each does and how they communicate.

**2. Each fact has one authority.** For each important fact, know which record wins when two disagree, and repair the other from it.

**3. Copies go stale, and durable records drift.** A cache or a screen may lag the record. Two records written at different moments can disagree after a crash.

**4. Check at the trust boundary.** Whatever comes from a part I don't run is checked before it affects anything. Who may read my own data is a separate question: authorization.

**5. Every design pays for what it buys.** Splitting components buys scaling and isolation and costs coordination. Keeping them together buys simplicity and costs a shared fate.

### My system in one paragraph

My Werewolf application has a Next.js frontend, a FastAPI server, and a LangGraph game engine running inside the server process. One Postgres database holds the records: the game row, the event log, the engine's checkpoints and the prompt captures. After a restart the engine resumes from its checkpoint, and browsers replay the event log filtered by what their seat may see. Running the engine in-process means one thing to deploy and output that streams straight to viewers; the cost is that a restart stops every game at once and games share the machine with web requests, which fits a few live games and would not fit hundreds.

### Mix-ups to avoid

These are the places I got stuck in the 2026-11-11 revision, each checked against the code that day.

| Easy to mix up | The difference |
|---|---|
| Caddy vs the FastAPI server | Caddy **routes** requests. The server **guards** every request and **hosts** each game: it runs the session, streams events to viewers and saves the records |
| Authentication / authorization / validation | *Who are you?* (the seat cookie) / *Are you allowed?* (does this seat owe a turn; may this viewer see this event) / *Is the request acceptable?* (shape, length, target in `valid_targets`) |
| Sent / received / seen | What a seat was **sent**: the event log filtered by the audience rule. What the browser **received**: its own cursor (`Last-Event-ID`). What the person **saw**: no record holds it |
| Checkpoint vs event log on resume | The checkpoint restarts the **engine**, both after a human pause and after a crash. The event log rebuilds the **session** and every **browser**. The log holds everything showable, private reads and memories included, each with an audience; the checkpoint also holds what is never shown. Events are saved after every chunk, with no shutdown flush |
| LangGraph vs Langfuse | LangGraph writes the **checkpoints** (into my own Postgres). Langfuse keeps **traces**, which the game never reads |
| Trust boundary | About **control**, not hostility: anything I don't run is outside, model providers and other APIs included. Verify, then rely |
| Scaling a service | Can any copy answer any request? My server: no, because games live in its memory. That's why it runs one process and can't sit behind a load balancer until games move to workers |

### Interview card

One idea per sentence, to rebuild the details from.

> **Records:** the checkpoint is the engine's full state, used to resume; the event log is what was
> sent, filtered per viewer. Two records, two readers.
>
> **Main design choice:** the engine runs inside the server, so everything for one game lives in one
> place, and streaming and human answers come for free. The cost is that a restart stops every game,
> which the checkpoints cover, and it can't scale past one process.
>
> **At scale:** move games to workers behind a queue and make the API stateless. The new problems are
> routing answers, streaming output back, and making sure only one worker runs each game.

The deeper points from that revision are kept for the units that own them:
[U3](working/u03_seed_notes.md) (why the engine resumes from the checkpoint, not the log),
[U4](working/u04_seed_notes.md) (at-least-once, idempotency, dual writes; dota2pred as the worked example) and
[U5](working/u05_seed_notes.md) (moving games to workers: the GameSession split, leases).

---

# Appendix A — Answers to the problems

## Problem A: AI contract review

**1. Components:** browser, API server, database, contract file storage, job queue, analysis worker and LLM provider.

**2. Records:** the decisions table in the application database is authoritative for what the lawyer accepted or rejected. A jobs table is authoritative for each review's status. The queue holds only work still to do, so the jobs table wins a disagreement between them.

**3. Worker choice:** the analysis takes minutes and nobody needs to watch it live, so a background worker behind a queue fits. The API returns a job identifier at once and the worker does the analysis. A smaller deployment could use another durable way to run background work.

**4. Trust boundaries:** browser to server, which includes the uploaded contract; and LLM provider to application. The contract text deserves a note of its own: it comes from outside and goes into a prompt, so it can carry instructions aimed at the model (U11).

## Problem B: Werewolf

**1. Responsibilities:** the frontend shows what the server sends and collects the player's input. The FastAPI server takes requests, runs one session per game, streams each game's events to viewers and holds a human's question until they answer. The LangGraph engine runs the game: phases, turns and each AI player's decision.

**2. Two records:** the checkpoint is the engine's whole state, secrets included, saved so the engine can carry on after a restart. The event log is the ordered list of what the game sent, each event with an audience, so a viewer's feed can be replayed. Neither can do the other's job.

**3. Trade-off:** one process to deploy, and output streams straight to viewers. A restart stops every running game at once, and games share the machine with web requests.

## Problem C: The claim

**Supported:** one Postgres database holds the game's records, and the events table holds every event the game sent, in order, each type with an audience.

**Not supported:** "five records" is loose (four tables plus the cast table, with usage as a column, depending on how they are counted). "Exactly what each player saw" claims too much: the table records what the server *sent* a seat. No record holds what a screen rendered.

**Accurate wording:** "One Postgres database holds my game records: the game row, the event log, LangGraph's checkpoints and the prompt captures. Filtering the event log by one seat's audience gives what that player was sent."

## Problem D: A system I know

There is no single answer. Four questions to check the drawing against. Does every box either run or
keep data? Is everything the user's device sends on the outside of the trust boundary? Is there, for
each store, one named fact where it wins a disagreement? And is the stale copy something
rebuilt from a record (a cache, a search index, a screen), not a second record?

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read),
**test** (named; not run unless stated), **incident** (a dated record). Read against the code on
2026-10-31; the trust-boundary entries were added on 2026-11-11.*

**The parts**

- Caddy sends `/api/*` to the server and every other path to the Next.js frontend. A browser
  watches a game over one SSE stream and sends a turn with a POST. **code**
  [docker-compose.yml](../../../docker-compose.yml) header comment;
  [games.py](../../../server/routes/games.py)::`event_stream`, `submit_turn`
- The server is FastAPI on one asyncio loop. At boot, `lifespan` gives the loop a 64-thread pool,
  recovers running games and starts the sweeper. **code** [app.py](../../../server/app.py)::`lifespan`
- Each running game is one `GameSession` with one asyncio task. `_drive_graph` reads the engine's
  `astream()`, and LangGraph runs the synchronous nodes on the thread pool. **code**
  [game_session.py](../../../server/game/game_session.py)::`start`, `_drive_graph`
- A human's turn is where browser and engine meet: `park` holds the question, `submit_turn` takes
  the POSTed answer, `_collect_answers` resumes the engine. **code**
  [game_session.py](../../../server/game/game_session.py)::`park`, `submit_turn`, `_collect_answers`
- The providers: Google, Anthropic, Mistral, and DeepSeek and others over the OpenAI protocol.
  **code** [providers/\_\_init\_\_.py](../../../Agents/llm_factory/providers/__init__.py)
- Each run of a game is one trace in a self-hosted Langfuse. **code**
  [game_session.py](../../../server/game/game_session.py)::`_run`

**The records**

- `games` row: which game, who sits where, and whether it is running, completed or dropped. It
  never holds a player's key. **code** [game.py](../../../server/database_models/game.py)::`GameRow`
- `events`: every event the game sent, by `seq`. Each event type has a tier (public, wolves, one
  seat, observer). `entitled()` applies the tier per viewer at send time, and at game over everyone
  becomes an observer. **code** [game.py](../../../server/database_models/game.py)::`EventRow`;
  [events.py](../../../server/schemas/events.py)::`EVENT_TIERS`;
  [entitlement.py](../../../server/game/entitlement.py)::`entitled`
- Checkpoints: LangGraph's own tables in the same database, keyed by game id. They say where the
  engine is, open questions included. **code**
  [graph_runtime.py](../../../server/graph_runtime.py)::`GraphRuntime.startup`
- `prompt_captures`: every prompt the AI players were sent and every private read they made,
  written when the game ends, for the leak audit. A resumed game's capture is marked `partial`;
  a dropped game gets none. **code**
  [capture.py](../../../server/database_models/capture.py)::`PromptCaptureRow`;
  [game_session.py](../../../server/game/game_session.py)::`_save_capture`
- Usage: tokens and call time per model and hour, the `usage` column on the games row. **code**
  [game.py](../../../server/database_models/game.py)::`GameRow.usage`
- `game_cast`: the character at each seat, written by the running game. The database also holds
  settings, the model menu, prices, characters and the lessons. **code**
  [database_models/\_\_init\_\_.py](../../../server/database_models/__init__.py);
  [game_session.py](../../../server/game/game_session.py)::`_persist_tail`
- After a restart, `revive` rebuilds each running game from its row, events and cast; the engine
  carries on from its checkpoint. **code**
  [live_game_registry.py](../../../server/game/live_game_registry.py)::`revive`. **test**
  `test_parked_game_revives_reparked_and_resumes_on_the_answer` (not run; no real Postgres)
  [test_durability.py](../../../tests/server/test_durability.py)

**The trust boundaries**

- A turn is accepted only from a cookie that proves a seat in the game (403 otherwise), and only if
  the answer fits the turn that seat owes (409 when it owes none, 422 when the answer breaks the
  turn's contract). **code** [games.py](../../../server/routes/games.py)::`_proven_seat`, `submit_turn`
- Model replies are parsed against a Pydantic schema. **code**
  [common.py](../../../Agents/llm_factory/providers/common.py). What the engine does with a reply that
  fails to parse was not read for these notes (see U1).

**Incidents on record**

- 2026-08-20 to 22: the durability row records "restart smoke passed" on real Postgres; its
  sentence on key-funded games predates resuming with the key. **incident**
  [build_plan.md](../../../frontend/docs/build_plan.md) "Session durability"
- 2026-09-12: the events table can run one engine step ahead of the checkpoint. **incident**
  [server_encountered_challenges.md](../../../frontend/docs/server_encountered_challenges.md) §8
- 2026-10-17: a human's prompt surfaced seconds late with 8 pool threads; the pool went to 64.
  **incident** (dated comment) [app.py](../../../server/app.py)::`lifespan`

**Not established**

- How many games one process can hold: no load test in what was read.
- A nightly leak audit over the captures: the cron is not installed. **incident** (note dated
  2026-10-26) [server/README.md](../../../server/README.md) "Running it"
- What a player's screen rendered. The events table records what the server sent their seat.

**Reading**

- [server/README.md](../../../server/README.md), "Layout": every module and what it owns.
- [server_design_notes.md](../../../frontend/docs/server_design_notes.md) §5 "The machinery" for how
  LangGraph orders its checkpoint write and runs sync nodes on threads; §5b for the scaling story
  behind Part 4.
- [server_encountered_challenges.md](../../../frontend/docs/server_encountered_challenges.md) §8: two
  records of one game disagreeing.
