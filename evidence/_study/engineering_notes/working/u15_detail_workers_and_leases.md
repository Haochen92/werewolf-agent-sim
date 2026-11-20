# Detail for U15. Worker processes on one server: dividing work and coordinating state

**Status:** a design my Werewolf server does not have. Nothing here is built or run. ·
**Builds on:** U2 (races), U4 (at-least-once, dual writes, idempotency), U5 (the checkpoint and
the paused question) · **Belongs with:** U15 (capacity), which points here.

**The question:** one process runs every game today. What changes when games run on several
worker processes on the same server, and how do they coordinate without sharing application memory?

## Scope: several processes on one server

This note covers **single-server, multiple-process programming**. A process is a running
program with its own ordinary application memory; a server here means the machine hosting
those processes. Several workers do not imply several machines. A worker is a process whose
job is to execute assigned work; it may use threads or async tasks internally (U2).

This arrangement exercises coordination problems also found in distributed systems: passing
messages, deciding who may change shared state, handling repeated work, and recovering from
one participant's failure. Separate workers can isolate some process failures, but all still
depend on the same host. A host outage stops all of them; memory exhaustion can affect their
neighbours too. This is not a highly available deployment.

U15 asks how much work the server can sustain. This note explains one architecture for dividing
that work. U3–U5 explain persistence, repeated effects and human waits; they supply the recovery
mechanisms rather than the reason workers exist.

## 1. The architecture, through one job

A report-generation service accepts requests while earlier reports are still being built.
One design puts report generation in separate processes. The API accepts a request, records a
job and returns its identifier. Workers take jobs independently of the HTTP request's lifetime.

```text
One server
┌─────────────────────────────────────────────┐
│ API process                                 │
│   accepts requests; serves progress          │
│          │                     ▲            │
│          ▼                     │            │
│ Postgres: jobs, state and results            │
│          ▲                     ▲            │
│          │                     │            │
│     Worker process A      Worker process B   │
└─────────────────────────────────────────────┘
```

A **job** describes work to perform, such as “generate report 51”. A **queue** holds work
waiting for execution. A **worker pool** is a set of workers taking work from that queue.
The queue distributes jobs; it does not itself perform them or make their effects safe to repeat.

One request follows this path:

1. The API validates the request and commits a job record before reporting acceptance.
2. A free worker claims the job atomically: two workers must not both win the same claim.
3. The worker loads the inputs, builds the report and records progress and the result.
4. After the result is saved, it marks the job complete. Failed attempts may need retrying (U4).
5. The browser asks the API for progress or receives a streamed update. The API reads shared
   records; the worker cannot update the API's Python objects as though it were another thread.

The processes communicate through explicit **interprocess communication**: for example a pipe,
a process-safe queue, or a database. In this example Postgres provides the shared records.
The worker's local memory holds temporary working data, not the only copy of an accepted job.

This is one alternative to doing work in the API's own threads or async tasks. It separates
execution from request handling and allows separate concurrency limits and process restarts.
It also adds dispatch, communication and coordination costs.

## 2. What is the unit of work?

A worker's lifetime and a job's lifetime are different: one long-lived worker can process many
jobs. A job can occupy one execution slot while other slots on that worker remain available.
For a game, there are at least two possible job boundaries:

| Job boundary | What happens during a human wait | What it requires |
|---|---|---|
| Run a whole game | The worker retains the game's task and local state | Answers must reach that worker; recovery is needed if it dies |
| Advance a game until its next pause or completion | The worker saves the waiting state and releases the task; an answer creates new work | Shared state sufficient for another worker to resume, plus coordination between successive jobs |

Both use workers. Rebuilding from a checkpoint on every human answer is a choice in the second
design, not a property of worker architectures. Neither design requires splitting individual
seats into separate processes.

**Claiming a job is different from owning a game.** Two distinct jobs may both ask to advance
game 51. Giving each job to a different worker does not prevent conflicting game updates. The
design must also serialize advances for that game, through ownership or an atomic state check.
Different games can still run concurrently.

## 3. Workers and capacity

A queue absorbs a temporary burst by making work wait. If work keeps arriving faster than the
workers finish it, the backlog and waiting time keep growing. **Backpressure** means slowing
or refusing incoming work when the system cannot keep up. A limit on active jobs needs a policy
for queued jobs too: how many can wait, for how long, and what the caller sees when admission
is refused.

Adding a worker can use otherwise idle CPU cores or bypass a process-local bottleneck. It does
not add host memory, database capacity or model-provider quota. Each process may create its own
connection pool and caches, increasing total consumption. Two workers each allowing ten model
calls can permit twenty calls together; local limits are not a shared budget.

U15 therefore has to compare the measured bottleneck before and after changing the process
count. Useful observations are active jobs, queue length, age of the oldest waiting job, job
execution time and resource usage. More workers help only while the limiting resource permits
more useful work.

## 4. Applying the design to Werewolf

The following is a proposal, not the implemented server. It chooses jobs that advance a game
until the next pause or completion, using the checkpoint mechanism discussed in U5 section 3.5.
One API process and several workers can all run on the same host. The existing recovery path
is a starting point; it does not establish that arbitrary worker handoffs already work.

Today `GameSession` does three jobs: it runs the engine, sends output to viewers, and holds the
human answer slots. A worker-based design separates them.

| Responsibility | Where it would go |
|---|---|
| Run the engine | A worker process that takes jobs from a queue |
| Deliver output to viewers | The API process holding browser connections. It reads saved events; notifications can prompt a read |
| Hold an unanswered human question | A persisted question and checkpoint, not a suspended task |

```text
TODAY:    task interrupts → awaits an in-memory future → answer fills the future
          → the same task resumes

WORKERS:  task interrupts → question and checkpoint are persisted → task is released
                                   ↓
          new HTTP answer → validated and stored → a resume job is queued
                                   ↓
          any free worker loads the checkpoint and resumes
```

In the second design the human's response starts new execution work. Nothing holds the game's
task while the human thinks, though the queue, the database and the open viewer connections
still cost something.

| | Today | Proposed workers with release at a pause |
|---|---|---|
| A process restart or crash | Every game on the process stops; start-up rebuilds them | The affected worker's games are recovered by another worker |
| Routing an answer | It must reach the process holding the waiting slot | The API stores it for a worker to pick up |
| A human's answer | An in-process future | A queued resume request, which can be duplicated or lost (U4) |
| Events | The game sends directly to viewers | Worker → saved events → API process → browser |
| New components | None | A job queue, shared event records and ownership control |

**Two choices about workers.** One worker can run several games, or each game can have its own
process. Several games per worker has less process overhead; one process per game isolates a
process crash to that game, and costs a process start and memory for each. A leak can still exhaust
shared host memory without effective resource limits. Either way, work is assigned at the game
level, not by individual seat: the seats already run side by side inside one game and share its
state (U2).

**Preventing two workers from advancing one game.** A **lease** is a claim on a game that
expires. Worker A takes it and renews it with **heartbeats**. If A dies, the lease expires and
worker B can recover the game; without the expiry, a dead worker would block the game for ever.
But a worker that is slow, not dead, may carry on after its lease expired while B has started.
So a lease does not give exactly-once execution, and idempotency is still needed (U4).

**The same point in dota2pred.** Its orchestration run is limited to one at a time, and that
limit had no expiry. When a deploy replaced the container, the run in progress died with it, but
Prefect's database still listed that run as "running". The container was gone; the run's record
was not, and it held the only slot, so no new run could start. A start-up step now marks any
leftover "running" records as crashed. Its stale-match sweep, by contrast, takes over Redis
stream entries older than two hours with `XCLAIM`, which transfers ownership when an entry has
been idle long enough. The claim does not automatically expire: a recovery process must perform
that takeover.

## What would the queue be?

An ordinary in-process queue is not a shared worker queue. However, processes can exchange work
through an in-memory mechanism such as Python’s `multiprocessing.Queue`. Persistence is a separate
requirement: accepted jobs must survive the relevant process or host restart. That is why this
proposal uses a persisted queue. Redis durability would depend on its persistence configuration.

Two real options. Redis Streams is the pattern I know from dota2pred:

| The design | In Redis Streams |
|---|---|
| The queue | A stream, written with `XADD` |
| A worker takes a job | `XREADGROUP` in a consumer group |
| "This job is being worked on" | The pending entries list |
| Acknowledge last | `XACK` after the work is saved |
| Take over from a dead worker | `XCLAIM` or `XAUTOCLAIM` on entries idle too long |

Redis claims a message, not a game. Two jobs for game 51 can go to two workers at once, so ownership of the game still needs separate coordination; this proposal uses a game lease.

The other option is Postgres, which the server already runs: a `jobs` table read with
`SELECT ... FOR UPDATE SKIP LOCKED` (each worker gets a different row), `owner` and
`lease_expires_at` columns on the game's row, and `LISTEN` / `NOTIFY` to say "game 51 has
something new". The row lock covers a short transaction that records the claim, then commits;
it is not held across a long model call. After commit, persisted job status and lease rules govern
recovery. `SKIP LOCKED` alone does not provide that lifecycle.

| | Postgres table | Redis Streams |
|---|---|---|
| New service to run | No | Yes |
| Queue the job in the same transaction as saving the answer | Yes | No: a dual write (U4 section 1.3) |
| Built-in claim of stale work | No, a query I write | Yes |
| Capacity evidence here | Not benchmarked; a candidate using the existing database | Not benchmarked; another service to operate |

For this server Postgres would come first. Saving the answer and queuing the resume job in one
transaction removes the dual write that dota2pred has between its database and Redis.

### Detail: six failure points in the worker design

A way to learn the design without building it: break it at one point and predict what happens.
The answers are reasoned from the design above. None of this is built or run.

**1. A worker picks up "resume game 51 with seat 4's vote", and dies mid-step.**

<details>
<summary>Answer</summary>

The last committed checkpoint provides a recovery point. Work and external effects since that
checkpoint may repeat (U4). What matters is when the job was
removed from the queue. If it was removed on pick-up, the vote is gone: the browser was told
"accepted" and the game waits for ever. So the job is removed only after the step's checkpoint
is saved (acknowledge last, U4 section 1.3). The lease expires, another worker takes the job,
and the step runs again. The check and state change must be serialized for the game; two workers independently
reading the same open question is not sufficient.
</details>

**2. The queue delivers the same resume job twice.**

<details>
<summary>Answer</summary>

This design uses at-least-once delivery (U4), so duplicates are expected; not every queue
automatically provides that guarantee. The second worker loads the checkpoint
and must be able to see that this answer was already used. So the job names the question it
answers, and the worker drops it if the checkpoint is no longer paused on that question. Without
a question id, the second copy could be applied to the seat's next question, which is U4 gap 1
again.
</details>

**3. Worker A stalls for a minute on a slow call. Its lease expires and worker B takes the game.
Then A wakes up.**

<details>
<summary>Answer</summary>

Both now believe they own the game, and both will save. A lease alone does not stop this. The
usual defence is a number that goes up each time the lease is taken, sent with every save; the
database refuses a save carrying an older number (called fencing). Both workers may also have
produced events for the same step, so the send-once guards would have to be checked against
saved data, not a worker's memory.
</details>

**4. A worker saves an event to the table, then publishes it to the viewers' channel. The
publish is lost.**

<details>
<summary>Answer</summary>

Two stores, so a dual write (U4 section 1.3). If the channel carries the event itself, viewers
miss it. The safer shape: the table is the record, and the channel only says "game 51 has
something new". The API server then reads the table from the viewer's last number, so a lost
message need not lose an event (U6). Periodic polling or reconnect catch-up must trigger another
read if the notification is missed; a saved row alone does not wake the API process.
</details>

**5. The human answers, and the step is resumed on a different worker from the one that
paused it.**

<details>
<summary>Answer</summary>

The turn cache is in the first worker's memory, so the AI seats are called again and may decide
differently. Today that happens only after a restart. With workers it could happen on every
human turn, and it is the fault behind the 2026-08-19 vote failure (U5 section 3.1). The AI seats'
results would have to be saved somewhere every worker can read before the step pauses.
</details>

**6. Seat 4's 120 seconds run out at the same moment their answer is put on the queue.**

<details>
<summary>Answer</summary>

In this release-on-pause design, a sleeping game task is not the durable timer. The deadline is saved, and a
sweep queues "play seat 4's turn with its agent". Now two jobs answer one question. The first
to atomically change the question from open to resolved wins under a first-accepted policy. The
winning answer or fallback and its resume job are recorded in the same transaction; the loser
does nothing. The question id identifies the contest, but the atomic conditional update settles
it (U2 section 1.6). A strict deadline policy must additionally reject answers accepted after
the deadline; queue execution order alone cannot enforce that policy.
</details>

## Where this note stops

The stopping point is being able to trace a job, explain where its state lives, prevent conflicting
updates, recover an interrupted attempt and explain when another worker helps capacity. These
are useful foundations for system design discussions; this note alone is not complete interview
preparation.

Moving workers onto a second host keeps many of these ideas, but adds an independently failing
machine and network path. A worker may be alive yet unable to reach the database; a timeout does
not prove it died. API replicas need request routing and shared state. The database and queue
still need their own availability plan. Replication copies data to multiple nodes; partitioning
splits data or work among nodes. Their consistency and failure trade-offs belong in a separate
extension, not the core explanation here.

**When is it worth it?** When measurements or operational needs justify separating execution from
request handling, using additional cores, or reducing the impact of one worker process failing.
If host memory or provider quota is already the bottleneck, adding local workers does not remove
it. All workers on one host still stop when that host fails.

## Mechanism references

- [Python multiprocessing: exchanging objects between processes](https://docs.python.org/3/library/multiprocessing.html#exchanging-objects-between-processes): process queues exist; this is distinct from durable storage.
- [Postgres SELECT locking clauses](https://www.postgresql.org/docs/18/sql-select.html#SQL-FOR-UPDATE-SHARE): `SKIP LOCKED` can serve competing consumers of a queue-like table.
- [Postgres LISTEN](https://www.postgresql.org/docs/15/sql-listen.html): notifications go to listening sessions; saved rows and a catch-up path provide recovery.
- [Redis XCLAIM](https://redis.io/docs/latest/commands/xclaim/): explicit transfer of pending-message ownership based on idle time.

*Revised 2026-11-14: added the single-host architecture, job boundaries and capacity explanation;
corrected queue, claim and race semantics. The Werewolf worker design remains a proposal. Existing
project incident accounts were retained, not independently reverified in this revision.*
