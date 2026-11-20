# U5. Human-in-the-loop: durable pauses and reliable resumption

**Reading time:** about 60 minutes for Parts 1 to 3 (estimate); Part 6, 5 minutes · **Builds on:** U2 (async tasks), U3 (checkpoints), U4 (retries, idempotency, dual writes) · **Related:** U6 (browser events and reconnection), U7 (seat authorization) · **Feeds write-up chapter:** 7 and 8

**The question:** if a workflow waits hours or days for a person, how does it continue correctly
when the person answers, even if the server restarted in between?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

**Reading path.** Parts 1 and 2 explain the mechanisms. Part 3 is my implementation. Part 4 is
design alternatives and can wait for a second read. Part 5 is a pointer to a separate document. Part 6 is the summary and the problems.

## The whole idea

```text
Check receipt → Ask manager → WAIT → Manager responds → Pay claim
                               ↑
                   may take days; the server may restart
```

A waiting workflow must save its progress and the question it is waiting on. When the answer
arrives, as a new request, the server finds that question, validates the answer, and resumes the
saved workflow.

That gives four engineering questions:

| Concept | The question it answers |
|---|---|
| Persistence | What must be saved so the workflow survives a restart? |
| Resumption | Where does execution resume, and what might run twice? |
| Correlation | How does a later request find the right waiting workflow, and is the answer valid? |
| Timeout | What happens when the person never responds? |

---

# Part 1 — Four fundamentals

The example throughout is an expense claim: check the receipt, ask the manager to approve, pay.

## 1.1 Persistence: surviving a restart

Consider one function:

```python
check_receipt()
ask_manager()
await_approval()        # maybe days
pay_claim()
```

A function keeps its progress in process memory: which line it is on, and its local variables.
If that is the only place the progress exists, three things go wrong.

- **A crash or deploy destroys the waiting execution.** Nothing remembers that claim 88 had its
  receipt checked and was waiting for approval.
- **Every waiting claim holds a task in memory** (and in a blocking design, a thread).
- **With several servers, the approval request may reach a different process** from the one that
  is waiting.

**Durable execution** means saving enough workflow state to rebuild the progress. For example:

```text
claim 88 | receipt checked | awaiting manager approval | approval question open
```

A **checkpoint** is the saved state at a step boundary, from which the engine can continue (U3).
It does not save the running Python function or its local variables. Work that was unfinished
at the last checkpoint may be run again.

### Persisting state is different from keeping a task alive

These are two separate choices. Both designs below are durable.

| | A. Persist, and keep the task | B. Persist, and release the task |
|---|---|---|
| During the wait | The task stays suspended, for example awaiting a future | The task has ended. Only the saved state and the question remain |
| When the person replies | The future is completed and the existing task carries on | A new task or worker loads the checkpoint and resumes |
| After a crash | The task is created again from the checkpoint | The next resume loads the same checkpoint |
| Trade-off | Simple control flow inside one process. The task uses memory and belongs to that process | Nothing held while idle. Needs a queue, dispatch, and a rule for who owns a workflow |
| My game | This one | Not implemented (Part 5) |

Why persist at all in design A, if the task is still there? For crash recovery. The task is
convenient while it survives, and the checkpoint is what is left when it does not. A suspended
task is not using the CPU, but it does hold some memory (U2).

### Check

A function waits on a persistent queue, but its own progress is never saved. Does the durable
queue guarantee the function can be rebuilt after a restart?

<details>
<summary>Answer</summary>

No. The message in the queue survives. The function's position and local variables were in
memory and are gone. A durable channel for the answer and a saved workflow are separate things.
</details>

## 1.2 Resumption: what gets repeated?

### Checkpoints are boundaries, not snapshots of every instruction

```text
Step 1 complete → [checkpoint] → Step 2 starts → CRASH
                       └────────→ Step 2 may run again
```

The work after the last checkpoint is the work in flight (U3). Running it again matters when it
has an effect outside the workflow, such as an email or a payment.

### What LangGraph does at a pause

In the checkpoint-and-interrupt arrangement my engine uses, **resuming a paused node runs that
node again from its first line**. This time the `interrupt()` call returns the person's answer
instead of pausing. This is how this engine behaves. It is not part of the definition of
durability, and other engines differ (Part 4).

```text
Node: find approver → send email → interrupt(wait for answer)

First run:    find approver → send email → pause
After reply:  find approver → send email AGAIN → interrupt returns the answer
```

**Rule: anything before the interrupt must be safe to repeat.** Working out the question is
safe. Sending an email is not.

A better layout:

```text
Node 1: notify the approver → save completion
Node 2: build the question; interrupt()      ← runs again on resume
Node 3: pay the claim (with an idempotency key)
```

Moving the email out of the paused node stops a normal resume from sending it again.

### A separate node is still not enough: the dual-write gap

The process can crash after the email is sent and before "node 1 complete" is saved. Recovery
then runs node 1 again and sends the email again. That is U4's dual-write problem
([U4 section 1.3](04_delivery_and_idempotency.md)).

So there are two sources of repeats, with different defences:

| Source of the repeat | Why it happens | Defence |
|---|---|---|
| Replay at a pause | Code before `interrupt()` runs again on resume | Keep that code read-only or safe to repeat; move effects to their own node |
| A crash before the checkpoint | The effect happened, but the save does not record that it did | An idempotency key, such as `notify-claim-88` or `pay-claim-88` |

What must not happen twice is the effect. Saving "complete" twice is harmless. Two things make
the key work:

- **The receiver stores the key**, not my workflow. The mail service or payment provider records
  the key and performs the effect as one operation, and drops a second request with the same
  key. If my workflow stored it, a crash could fall between the effect and that save.
- **The retry must produce the same key.** So the key is built from saved facts (the claim, the
  step), never a random id or a counter made during the run (U4 section 1.2).

### Check

A node adds 1 to a dashboard counter and then interrupts. What happens when it resumes? What
changes if the add is moved into its own node? What can still go wrong?

<details>
<summary>Answer</summary>

On resume the node runs again from its first line, so the counter shows 2 for one claim. In its
own node, a normal resume no longer repeats the add. A crash after the add and before that
node's checkpoint still repeats it. The fix that covers both is to make the add safe to repeat:
count the claims whose status is "awaiting approval" instead of keeping a running total (U4
section 1.2).
</details>

## 1.3 Correlation: how the answer finds the wait

With an ordinary call, the answer comes back to the line that asked:

```python
result = db.query("SELECT ...")   # the same code asks and receives the answer
```

A person's answer does not come back that way. The manager clicks "approve" hours later, and
the click arrives as a new HTTP request at a web route. That route's handler is a separate
function that knows nothing about claim 88's workflow. Nothing links the click to the waiting
workflow unless the application makes the link.

So the application gives each question an identity (for example "claim 88, approval by the
manager"), sends it out with the question, and uses it to find the open question when the
response arrives. This is a **correlation id**. Correlation is not authentication: the server
must still check who is answering and whether the answer is allowed.

| Possible problem | Required check |
|---|---|
| An old approval link is clicked after the claim was withdrawn or reassigned | Is this exact question still open? |
| A double click, or a retried request | Has this question already been answered? |
| The wrong manager, or an answer that is not one of the choices | Is this person allowed to answer, and is this choice allowed by the question as it was asked? |

The stored question therefore has to include: who may answer, what they may answer, and whether
it is still open.

**The answer needs to be durable too.** If the server replies "accepted" and crashes before the
answer is saved, recovery opens the question again. The answer should be saved before the
server says it was accepted (U4).

## 1.4 Timeout: what if no one answers?

A wait needs three things:

1. **A deadline.** Saved, if it must survive a restart.
2. **Something that notices it has passed.** A saved timestamp does nothing by itself; a timer
   or a background sweep has to check it.
3. **A policy for what happens next.**

| Policy | Example |
|---|---|
| Remind and keep waiting | The manager is probably busy |
| Escalate | A director takes over the approval |
| Take a default | My game lets the seat's AI agent act for an absent player |
| Cancel | The request is no longer useful |

### Check

A claim is escalated to a director on Thursday. On Friday the original manager approves through
the old link. What should happen, and what must have been saved for it to happen?

<details>
<summary>Answer</summary>

It depends on what escalation means, and either way each question needs its own saved record:
an id, who may answer, and whether it is open or closed.

| Policy | On Thursday | The manager's Friday click |
|---|---|---|
| Escalation transfers the question | The manager's question is closed and the director's is opened | Refused: that question is closed |
| Escalation adds an approver | The manager's question stays open and the director's is opened too | Accepted, and the director's question is closed |

The second policy has two questions open for one claim, so both people can click at the same
moment. Accepting an answer then has to be "first one wins": checking that the claim is still
undecided and marking it decided must be one step (the check-then-act race, U2 section 1.6).
The payment keeps its idempotency key under both.

What does not work under either policy is a link that names only "claim 88". The server could
not tell the manager's question from the director's. That is a key that is too broad (U4
section 1.2), and it is the same fault as my server matching an answer to a seat and not to a
question (U4 gap 1).
</details>

## 1.5 Worked timeline: claim 88

```text
Mon  Check the receipt → save.
     Notify the manager, in its own step → save.
     Record the open approval question, who may answer, the choices,
     and a Thursday deadline → save.
     (In design B, no task stays alive during the wait.)

Tue  The server restarts. The saved progress and the question remain.

Wed  The manager's new HTTP request names the question.
     The server checks the person and the answer, and saves the answer.
     A worker loads the checkpoint and resumes the approval node.
     That node runs again, so its code before the interrupt is safe to repeat.
     The payment uses an idempotency key.

Wed  The browser retries the click. That question is closed: refused.

     (No response instead? On Thursday the deadline job escalates.)
```

This one scenario connects persistence, replay safety, correlation and timeout. These four
together are the core mental model.

---

# Part 2 — What the engine does, and what my application does

Before the Werewolf code, the responsibilities are separated:

| Responsibility | The engine (LangGraph) | My application |
|---|---|---|
| Save and read workflow progress | Checkpointing, into Postgres | Chooses the game ids, and decides when to rebuild a game |
| Pause and continue execution | `interrupt()` and resume | Delivers the right human answer to the paused workflow |
| Identify the browser and the player | Not provided | Seat token, cookie, the open question, validation |
| Keep a game available to people | Not automatic | The session's task, answer slots, event stream, reconnect handling |
| Handle absence and expiry | Not provided by an interrupt | Timers, the AI substitute, cleanup of idle games |

A checkpoint is only part of the solution. LangGraph does not rebuild my server's runtime
objects after a deploy, and it cannot restore anything that was held only in Python memory.

**Two kinds of replay, which are separate mechanisms:**

- *Workflow replay:* resuming the engine runs a node again (this note and U4).
- *Browser event replay:* a reconnecting browser is sent saved event messages again (U6).

---

# Part 3 — My Werewolf server: what it actually does

## 3.1 Why the design matters: a real voting failure

On 2026-08-19, the first game with two human seats stopped during a vote. The server's ballot
count disagreed with the engine's, so the result was not announced.

The cause was replay. After a human responded, the paused step ran again, so the AI seats voted
again. Some gave different votes, and the counts no longer matched.

In my game a human's pause happens inside a step that also does AI work. So the pause has to be
safe without producing inconsistent AI decisions or duplicate events for viewers.

## 3.2 A human turn from start to finish

Every seat follows the same pipeline:

```text
Build the seat's input → Obtain a decision → Validate it → Apply it
```

An AI seat obtains its decision from a model. A human seat obtains it from a LangGraph pause
and a later browser response.

Example: seat 4 is human, the nine other seats are AI, and all are voting.

| Stage | What happens |
|---|---|
| 1. Announce | The vote step begins. The engine works out seat 4's question from the game's state (seat, role, phase, day, legal targets) and sends it to the server at once. The server builds the question object (`HumanTurnRequest`) from it, keeps it in memory, creates an empty answer slot, and sends the browser a "your turn" event with the legal choices |
| 2. Interrupt | Seat 4's part of the step builds the question and pauses. LangGraph stores the pause and its question in the game's Postgres checkpoint, under the game id |
| 3. Wait | The nine AI seats vote. The step cannot finish, so the engine's stream ends. The game's task waits until every open human answer slot is filled |
| 4. Receive | The browser submits seat 4's vote in a new request. The server proves the seat from its cookie, validates the answer against the open question, marks the seat as answered, and fills its slot |
| 5. Resume | Once every required human answer is present, the waiting task resumes the engine with those answers |
| 6. Re-execute | LangGraph runs the paused step again. The interrupt now returns the answer. It is checked a second time, converted into the shape of a model's decision, and applied |

### What is saved in the question?

The interrupt carries the seat, phase, day, legal targets, and whether the turn may be passed.
The server validates an answer against that question:

- **Discussion:** a message of up to 500 characters, or a pass where passing is allowed.
- **Vote or night action:** a target from the legal targets. Passing is not allowed.
- **Unexpected fields:** rejected.

The browser enforces the 500-character limit too (the text box's `maxLength`, `LINE_MAX` in
`frontend/src/stage/instruments/turn-dock.ts`). That check is for the player's convenience; the
server's is the rule, because a request can be sent without the page. The limit is written once
in each codebase, and nothing ties the two together.

The server does not trust the browser because it sent a target. It checks that the action is
valid for the turn that is actually open.

### How does the server find the right answer slot?

The server keeps one in-memory slot for each human seat that owes an answer. An incoming
request is matched to its seat, and that seat's slot is filled. When several humans are
interrupted in the same step, the game waits for all of them and then sends the answers to
LangGraph together, each under the id the engine gave its interrupt.

**Known limitation.** The server matches an answer by seat, not by question. A retry of an
earlier answer that arrives after the same seat has been asked something new is accepted as the
answer to the new question (U4 gap 1). Not fixed. The cause is in my own answer route, on the
leg between the browser and the server. The leg between the server and the engine uses the
engine's interrupt id and is correct, and the early announcement did not create the gap.

### Why is the resumed step safe?

- **The human seat's code before the interrupt only builds the question** from the game's state.
  It has no outside effect, so running it again is safe.
- **The AI seats' work is the expensive and variable part.** The turn cache
  ([U4 section 3.2](04_delivery_and_idempotency.md#32-a-step-that-runs-again)) returns their
  earlier decisions on an ordinary resume, while the process is still alive.
- **Human seats use an uncached copy of the turn step.** A cached human answer would be played
  back instead of asking the person, and the library fails if a cached step pauses.

**Why the AI seats run again at all.** The day and the wolves' night are subgraphs called from
inside a single node of the main graph. That node builds each subgraph's input by hand, which
is where I control what each seat may know. The cost: on resume the engine treats the whole
call as one interrupted step and starts it from the top.

A test graph with no model showed the difference. With the parallel turns placed directly in
the main graph, a finished turn did not run again across a pause. Inside a subgraph called from
a node, it did.

### Detail: why the server announces human turns early

Nesting caused a second problem. A pause inside a parallel step of a subgraph reaches the server
only when the whole step has ended, so a human's prompt used to appear after every AI seat had
finished.

There are three parties, and the browser only ever talks to the server:

```text
Engine (LangGraph)  ⇄  Server (my code)  ⇄  Browser
```

Before, the engine told the server about a human's turn only through the interrupt:

```text
Engine: the vote step starts; 9 AI seats call their models...   (20+ seconds)
Engine → Server:  "interrupt abc123: seat 4 owes a vote"        (when the step ends)
Server → Browser: "your turn"
```

Now the step sends a heads-up as it starts:

```text
Engine → Server:  "seat 4 will owe a vote" + phase, day, legal targets   (as the step starts)
Server → Browser: "your turn"                                            (at once)
Engine: 9 AI seats call their models...
Engine → Server:  "interrupt abc123: seat 4 owes a vote"                 (when the step ends)
Server: attaches abc123 to the question it already opened
```

- **The heads-up carries the whole question**: seat, role, phase, day and the legal targets,
  worked out from the game's state. The server builds the question from it, with no interrupt
  id. Whether the turn may be passed follows the engine's rule (discussion and wolf chat: yes;
  a vote or night action: no).
- **An answer that arrives before the interrupt** waits in the seat's slot.
- **The interrupt adds only its id.** The server sees a question already open for that seat, day
  and phase, attaches the id, and sends no second prompt. The announced question stays the one
  answers are checked against.
- **The interrupt is still the only point where the graph takes the answer.**

The question is therefore built twice from the same state, once for the heads-up and once
inside the step. The design relies on both giving the same legal targets. Read in the code; I
found no test that compares the two.

This is also why the interrupt id cannot be the question id sent to the browser (U4 gap 1): it
does not exist yet when "your turn" is sent.

This changes when the browser can show the turn. It is not a second way to resume the graph.

*Code:* [`_human_player_action` and `validate_human_response`](../../../Agents/turn/human_turn.py);
[`GameSession.park`, `submit_turn` and `_collect_answers`](../../../server/game/game_session.py).

### Check

A human's vote is accepted by the server, but the HTTP response is lost, and the browser retries
two seconds later. Then the same happens on a discussion turn, but the retry arrives after the
seat has been asked to speak again. What does the server do in each case?

<details>
<summary>Answer</summary>

The vote: the first copy marked the seat as answered, so the retry finds nothing owed and is
refused. The browser treats that as "already answered". The discussion turn: the server matches
by seat, not by question, so the retry is checked against the new question and, being a legal
message, is accepted as its answer. An id for the question, sent back with the answer, would let
the server refuse it.
</details>

## 3.3 What is persisted, and what exists only in memory?

My system is design A from section 1.1: checkpoint the game, and keep a waiting task in the
same process.

**Persisted.** All in the one Postgres database; these survive a restart.

| What | Where | Written by |
|---|---|---|
| The engine's state, including the pause and its question | LangGraph's checkpoint tables, under the game id | LangGraph, at each step boundary |
| The events already sent to viewers | The `events` table | My server, as events are produced |
| The game's status, seats, seat tokens and model | The game's row in the `games` table | My server |
| The cast (which character sits in which seat) | The `game_cast` table | My server |

**In the server's memory only.** These are lost on a restart; section 3.5 says what each loss
costs.

| What | What it is for |
|---|---|
| Each seat's answer slot | Holds a human's answer until the engine resumes |
| The game's task | Waits for the answers and drives the engine |
| The seat clocks and their deadlines | Turn timers (section 3.4) |
| The turn cache | Saves repeating the AI seats' calls on a resume |
| A player's own API key | Pays for the model calls. The game's row records only that the game uses one, not the key |

What follows from the split:

- **The game is recoverable.** The row, the event history, the cast and the checkpoint are all
  there at start-up.
- **The active task is not.** Recovery has to create new session objects, answer slots, clocks
  and a task.
- **A waiting game still uses memory.** Its task, slots and clocks stay registered until it
  resumes, expires, or the server shuts down. Games are rebuilt from saved records only at
  start-up; nothing unloads a waiting game and loads it again later.
- **The architecture is single-process.** A second process cannot take over a wait, because the
  answer must reach the process whose memory holds the slot.

In one line: **the Postgres checkpoint provides recovery; the in-memory task and slots make an
ordinary human answer easy to handle inside one process.**

*Code:* [`GameSession` (its docstring lists every field and where it lives)](../../../server/game/game_session.py);
[`GraphRuntime.startup`](../../../server/graph_runtime.py) builds the Postgres checkpoint saver.

## 3.4 What happens when a player disappears?

The policy differs between a table with several humans and a game with one.

| Behaviour | Several human seats | One human seat |
|---|---|---|
| Turn timer | 120 seconds for a connected player who does not answer. A disconnect shortens it to 30 seconds from that moment, and reconnecting restores the original deadline, so a 10-second drop changes nothing. None once the seat's agent has played 2 turns in a row for an absent player | No turn timer |
| What notices that the time is up | A timer task for each waiting seat: an asyncio task that sleeps until the deadline, and is cancelled if the human answers first | After each piece of engine output, the game's task checks whether the player is connected |
| What then happens | The seat's own AI agent plays that one turn, with what the seat knows | While the player is away, the game stops reading the engine's output until they reconnect |
| Nobody connected at all | The questions stay open and no model is called. The first player back gives every waiting seat a fresh 120 seconds | The game stays stopped |
| Cleanup of abandoned games | Dropped once the wait is 24 hours old, if nobody is connected at that moment | Dropped once the wait is 1 hour old, if nobody is connected at that moment |

Further details:

- **Where the numbers come from.** 30 seconds: a closed connection was measured to be noticed
  within 1 to 10 seconds (2026-09-09), so 30 leaves room for the browser to retry. 2 missed
  turns: in a multiplayer test on 2026-10-15, a friend who had left held every one of their
  turns for 30 seconds. Both are recorded in the comments of `seat_clocks.py`.
- **The AI takeover is an ordinary answer**, not a hard-coded move. A player can ask for it on
  purpose, and the timer sends the same answer.
- **Waiting for a drafted line gives time back** to the player's clock: up to 20 seconds, with
  at most 3 drafts a turn.
- **The one-human stop has no grace period.** The smallest thing that can be held back is a
  whole step, and the step in flight runs either way, so a short disconnection costs nothing.
- **The turn deadline is not persisted.** A restart gives a waiting seat a fresh 120 seconds.
- **A solo player who is connected but idle is never timed out.** There is no turn clock, and
  the 1-hour cleanup applies only when nobody is connected.

*Code:* [`SeatClocks`](../../../server/game/seat_clocks.py);
[`GameSession._wait_for_absent_player`](../../../server/game/game_session.py);
[`is_expired`](../../../server/housekeeping/sweeper.py).

## 3.5 Restart recovery: the actual sequence

The guiding scenario: seat 4 has been asked to vote, and the server restarts before the answer
arrives.

1. **Shutdown.** The game's clocks and task are cancelled. Nothing new is written: the pause is
   already in the checkpoint, and the game's row still says "running".
2. **Start-up.** Recovery loads the rows marked "running" and rebuilds each game's session from
   its row: the seats and tokens, the saved events, the cast.
3. **Restore the wait.** Recovery asks LangGraph's checkpoint what is paused, and opens each of
   those questions again in memory, with a fresh answer slot and a fresh 120-second clock. A
   new task waits for the answers.
4. **The browser reconnects.** Seat 4's cookie still proves the seat, because the token was
   saved in the row. The server sends the saved events (with the earlier "your turn" among
   them) and the new deadline.
5. **The human votes.** From here it is the normal path of section 3.2: validate, fill the
   slot, resume.

**LangGraph does not run recovery by itself.** It provides saving, reading and continuing. My
start-up code chooses the games, rebuilds the runtime, opens the questions, and connects the
later browser input back to the engine.

| LangGraph provides | My server implements |
|---|---|
| Saving state at step boundaries, including a pause and its question, in Postgres under the game id | Selecting the "running" rows to recover |
| Reading the saved state: what is paused, and what step is next | Rebuilding the session, loading the event history, restoring the event counter, creating the answer slots |
| Continuing from the checkpoint, with a supplied answer | Waiting for the human's input and then calling "continue" |
| | Replaying saved events to a reconnecting browser |

Reading a checkpoint does not run the engine, so it produces no new event for the browser.
That distinction decides what can be duplicated.

### Three kinds of repetition during recovery

| Moment | Is the engine running? | What can repeat? | What protects against it |
|---|---|---|---|
| The server reopens the saved question | No | Nothing. Reading the checkpoint runs nothing and emits nothing | Nothing is needed. The question keeps its original event number |
| The browser reconnects | No | Saved events the browser already has are sent again | The browser sends the last number it saw, the server replays the rest, and the browser drops numbers it has seen (U6) |
| The human answers and the engine resumes | Yes | The AI decisions of the paused step are computed again, because the in-memory cache was lost. They would produce new events | The send-once guards ([U4 section 3.2](04_delivery_and_idempotency.md#32-a-step-that-runs-again)) |

So "the question appears again after a restart" does not mean the engine ran the human turn
twice. Reopening a question from the checkpoint, and replaying the event history, are both
different from resuming the graph.

### Detail: a gap in the order of two saves

There is one situation in which the same question gets a second event number:

1. My server saves a "your turn" event as soon as the engine reports the pause.
2. LangGraph saves the checkpoint holding that pause slightly later, in the background.
3. The process crashes between the two. The event exists, and the checkpoint does not record
   the pause.
4. On recovery the server finds nothing paused and tells the engine to continue. The engine
   reaches the human's question again, and the translator makes a new "your turn" event.
5. The translator's memory of which turns were announced was lost in the restart and is not
   rebuilt from the saved events, so the second announcement is not suppressed.

Read in the code, not reproduced. It is a possible gap, not an incident that has happened.

### What changes after a restart?

| Item | After the restart |
|---|---|
| The game's state and the open question | Restored from the checkpoint |
| The player's seat | Restored from the game's row. The seat cookie lasts 24 hours |
| The turn clock | Reset to a new 120 seconds |
| The age of the wait, for the 1-hour or 24-hour cleanup | Continues from the row's last update |
| A human answer that was accepted but not yet part of a checkpoint | Lost. The player is asked again |
| The AI work in the paused step | Runs and is billed again, because the turn cache was in memory |
| A waiting room | Lost. It has no saved row, and its address returns "not found" |
| A game using a player's own API key | Rebuilt without the key and without a running task. A seat holder is asked for a key, and the game resumes when the provider accepts it. A backup key is lost |

**Evidence limit.** The recovery tests use a stand-in graph and an in-memory database. The path
through real Postgres and the real engine was checked by hand, and no automated test kills and
restarts the server (U3 gap 1).

*Code:* [`recover_registry`](../../../server/housekeeping/recovery.py);
[`LiveGameRegistry.revive` and `_resume_from_checkpoint`](../../../server/game/live_game_registry.py).

### Check

Three humans are voting. Two have submitted and the third has not. The server restarts. What is
in the checkpoint, what was only in memory, and what does each player see on reconnecting?

<details>
<summary>Answer</summary>

The checkpoint holds three open questions. The two submitted votes were only in memory, because
the task was waiting for all three before resuming the engine. So recovery opens all three
questions again, and all three players are asked to vote, each with a fresh 120 seconds. Nothing
else is lost: the game, their seats and the events they had seen are restored.
</details>

## 3.6 Known limitations

| Gap | Consequence | Possible direction |
|---|---|---|
| 1. A waiting game belongs to one process | Its task and slots use that process's memory, for up to 24 hours, and another server cannot continue the wait | Persist the waiting question and send resume work to workers (Part 5 and the workers document) |
| 2. An answer accepted just before a restart is lost | The player has to submit again. Nothing is wrong, only repeated | Save the answer before replying "accepted" |
| 3. The turn deadline is in memory | A restart resets the timer to 120 seconds | Save the deadline with the game's row |
| 4. A solo player who is connected but idle has no timeout | The game can wait indefinitely while the browser stays connected | A long turn clock for that case |
| 5. Recovery of a nested interrupt is not verified end to end | Recovery reads paused questions from the top level of the saved state. It is unconfirmed, against the real engine, that a pause inside a called subgraph always appears there | A test with real LangGraph, real Postgres and a real process restart (improvements, row 9) |
| 6. Nothing watches for a game that hangs without a human interrupt | The clocks and the cleanup cover only games waiting on a person | Detection of stalled work, separate from the turn clocks |

Two more limits come from earlier sections: an answer is matched by seat and not by question
(U4 gap 1), and the crash window between the event save and the checkpoint save (section 3.5).

The design makes a deliberate trade-off: simple single-process play with checkpoint-based
recovery, in place of a more complex multi-worker architecture.

---

# Part 4 — Design choices

**Where should a wait live?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Memory only | Simplest | A restart loses the progress | A waiting room (not saved) |
| Checkpoint, plus a suspended task | Durable recovery, and simple futures | An in-memory session, owned by one process | Games today |
| Checkpoint, with the task released | No idle task; any worker can take over | A queue, ownership, and a way to deliver events | Not used |
| A managed durable-execution service | Provides much of that machinery | A service to run, and code written to its rules | Not used |

The managed service is a way of getting the third row, not a fourth place to keep a wait.

**How does the engine resume?**

| Approach | Consequence | My system |
|---|---|---|
| Poll for the answer inside one live step | The wait is a running execution, and dies with the process | No |
| Checkpoint, and run the paused node again | Simple. Code before the interrupt runs again | Yes: LangGraph |
| Record each completed activity in an execution history, and replay the code against it | Completed work is reused, not redone. The code must take the same path on every replay, and a platform is needed. Temporal is an example | No |

**Several people answer in one step: when are the answers handed over?**

| Strategy | Benefit | Cost | My system |
|---|---|---|---|
| Resume once per answer | Each answer reaches the engine, and a checkpoint, at once | The node is replayed once per answer | No |
| Collect all, resume once | One resume for the group | Earlier answers sit in memory until the last arrives; a restart loses them | Yes |

**Ending the wait.** My game uses several policies: the seat's AI agent substitutes for an absent
human in a game with several humans; no model work is done while nobody is connected; and an
abandoned game is dropped after 1 hour (one human) or 24 hours (several). Reminders and
escalation are not used.

**Judgment.** For a few games on one server, a checkpoint plus a waiting task is the simplest
adequate choice. The more elaborate architecture is not more correct. It solves different
problems: scale, and which process owns a game.

---

# Part 5 — Several workers (a pointer)

Design B from section 1.1, persist and release the task, is where durable execution leads when
one process is no longer enough: the open question is a record, the answer becomes a queued
"resume" job, and any worker loads the checkpoint and continues. My server does not do this.

That design is mostly about scaling and ownership, not about waiting for a person, so it has
its own document: [Worker processes on one server: dividing work and coordinating state](working/u15_detail_workers_and_leases.md).
It belongs with U15 (capacity).

What this note needs from it is three sentences:

- **What it would take.** A queue for resume jobs, a shared channel for events, and a **lease**:
  a claim on a game that expires, so a dead worker cannot hold a game for ever.
- **What breaks first.** The turn cache is in one process's memory, so a resume on another
  worker would call the AI seats again.
- **Why it is not built.** One server holds the games today, and where that stops being true
  has not been measured.

---

# Part 6 — Review

## In 30 seconds

A workflow waiting on a human must persist its checkpoint and the open question. The response
arrives later as a new request, so the server correlates and validates it, then resumes from the
saved state. In my LangGraph setup the paused node runs again, so effects must be safe to
repeat; a crash can also repeat a node whose completion was not yet saved. The wait needs a
timeout policy. A multi-worker version needs a durable resume queue and ownership that can be
recovered. A waiting task can stay in memory or be released; the checkpoint provides recovery in
either case.

## My Werewolf server in one paragraph

A human turn is a LangGraph interrupt, checkpointed in Postgres under the game id. My single
server also holds the game's task and one answer slot per seat in memory. A browser's answer is
authenticated, checked against the open question, and collected before the engine resumes. The
paused step runs again: the human's code before the interrupt only rebuilds the question, and
the AI seats' earlier decisions come from the turn cache on a normal resume in the same process.
After a restart, my recovery code rebuilds the session and opens the saved question again. The
clock resets, the cache is gone so the AI calls are made again, and a human answer that was
accepted but not yet checkpointed is lost. It is a deliberate single-process design.

## Problems

Each is answered from memory first; my answers are in Appendix A.

**A. Transfer.** A bank's sign-up flow waits up to two weeks for a customer to upload a passport
photo. The flow is one function that waits. What goes wrong, and what are the four things a
redesign has to settle?

**B. My system.** What runs again after a human votes, and what makes each part harmless? What
is in Postgres and what is only in memory? What happens when a player disconnects, with one
human and with several?

**C. Evidence.** Is "a waiting game resumes exactly where it was after a restart" supported? Is
"the turn-cache key fix is validated" supported? Give the accurate wording for each.

**D. The sharp question.** How does a long-running workflow wait days for a human and survive a
redeploy? In under a minute, then with replay, correlation, timeout and leases added.

---

# Appendix A — Answers to the problems

**A. The passport upload.** A wait in memory is lost on a deploy, holds resources, and is tied to
one process. The redesign settles: (1) persistence: a saved row or checkpoint per sign-up, with
the open question; (2) resumption: the "please upload" email in its own step, with a key, and
opening the account made idempotent; (3) correlation: the upload link names the sign-up and the
step, and the upload is checked (right customer, a passport, still open, not already received);
(4) timeout: a saved deadline, a job that checks it, and a policy such as a reminder at 3 days
and cancelling at 14.

**B. Werewolf.** The human's code before the interrupt runs again and only rebuilds the question.
The AI seats run again because the subgraph is called from inside one node; the turn cache
returns their earlier votes with no model call, until a restart empties it. Saved: the
checkpoint with the question, the events, the game's row with the seat tokens, the cast. Memory
only: the task, the answer slots, the clocks, the cache, a player's own API key. Several humans:
a disconnected seat's timer drops to 30 seconds and then the seat's AI plays, as long as some
human is connected; with nobody connected the game waits. One human: the game stops reading
engine output until the player reconnects, and is dropped once it has been stopped for an hour
with nobody connected.

**C. The claims.** "Exactly where it was" is too strong: the clock resets, an answer accepted but
not checkpointed is lost, and the AI seats are called again and may answer differently. The
tests use a stand-in graph and an in-memory database; the real restart was checked by hand, not
by an automated test. Accurate: "The game is rebuilt from saved state, reopens its question,
and runs the paused step again when answered." The turn-cache key now includes the game id
(commit `fd07c0f8`), tests pin it (`tests/engine/test_turn_cache_key.py`::`test_key_separates_games`
and `test_two_games_never_share_a_day_one_opening_key`; named, not run), and the fix was
deployed on 2026-10-26. Hosted games since then were not audited. Accurate: "Fixed, covered by
tests, deployed; no recurrence reported."

**D. The sharp question.** Save the checkpoint and the open question. Identify and validate the
later answer. Resume in a way that is safe to replay, with idempotent effects. Define a deadline
and something that enforces it. With several workers, queue the resume work and control
ownership with leases that expire, while still guarding against duplicates.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named; not
run), **library** (read in the library's source, not measured), **doc** (a written record, not
re-read in the code), **inferred** (reasoned from code that was read). Read against the code on
2026-11-13. Paths are from the repository root.*

**The human turn (3.2)**

- One call pauses the engine: **code** [`Agents/turn/human_turn.py`](../../../Agents/turn/human_turn.py)::`_human_player_action`;
  both turn pipelines branch on `payload["human_player"]`: **code** [`Agents/turn/pipeline.py`](../../../Agents/turn/pipeline.py)
- The question's fields: **code** [`Agents/schemas/human_player.py`](../../../Agents/schemas/human_player.py)::`HumanTurnRequest`;
  the checks, `MAX_LINE_CHARS = 500`, no extra fields: **code** `human_turn.py`::`validate_human_response`,
  `HumanTurnResponse`
- Uncached human copies `round_turn_human`, `vote_human`, `CARRIER_KILL_HUMAN`,
  `PACK_SKILL_HUMAN`; a cached step that pauses fails on resume (langgraph 1.1.10 and 1.2.14):
  **code** [`Agents/graphs/day.py`](../../../Agents/graphs/day.py), [`Agents/graphs/night/pack.py`](../../../Agents/graphs/night/pack.py)
- Park, the per-seat future, the batch keyed by interrupt id: **code**
  [`server/game/game_session.py`](../../../server/game/game_session.py)::`park`, `submit_turn`, `_collect_answers`; **test**
  `tests/server/test_game_session.py`::`test_interrupt_parks_validates_and_resumes`,
  `test_parallel_interrupts_park_per_seat_and_resume_as_one_batch`
- The answer route, 403 without a seat, 409 for nothing owed, 422 for an illegal answer: **code**
  [`server/routes/games.py`](../../../server/routes/games.py)::`submit_turn`, `_proven_seat`. No test sends one seat's answer twice
- A finished turn runs once in the main graph and twice inside a called subgraph: **doc**
  `writeup/game_design_orchestration/human_in_the_loop/human_in_the_loop.md` (2026-10-26)
- The early announcement, the held answer and the adoption: **code**
  `human_turn.py`::`announce_human_turn`, `game_session.py`::`announce`, `park`; **doc**
  [`frontend/docs/server_client_transport.md`](../../../frontend/docs/server_client_transport.md) section 8b; **test**
  `test_an_announced_vote_opens_at_once_and_its_answer_waits_for_the_interrupt`

**What is persisted (3.3)**

- `AsyncPostgresSaver` on a pool of at most 4 connections; thread id is the game id: **code**
  [`server/graph_runtime.py`](../../../server/graph_runtime.py), [`Agents/config/langgraph.py`](../../../Agents/config/langgraph.py)::`build_runnable_config`
- The save mode is the library's default, written in the background: **library**; nothing in
  `server/` or `Agents/` sets it
- The memory-only fields: **code** `game_session.py`, the class docstring and `__init__`
- A waiting game stays registered; `revive` is called only at start-up: **code**
  `game_session.py`::`_maybe_idle`, [`server/game/live_game_registry.py`](../../../server/game/live_game_registry.py)

**A player who disappears (3.4)**

- `AFK_TIMEOUT_SECONDS = 120`, `ABSENCE_GRACE_SECONDS = 30`, `GONE_AFTER_TURNS = 2`; clocks only
  with more than one seat token: **code** [`server/game/seat_clocks.py`](../../../server/game/seat_clocks.py), `game_session.py`
- Expiry delegates when a human is connected and parks when none is: **code**
  `seat_clocks.py`::`_expire`; **test** `test_afk_timeout_delegates_the_parked_turn`,
  `test_afk_expiry_parks_when_nobody_is_connected`
- `DRAFTS_PER_TURN = 3`, `DRAFT_CREDIT_CAP_S = 20`: **code** `game_session.py`::`draft_line`
- The one-human stop: **code** `game_session.py`::`_wait_for_absent_player`; **test**
  `test_a_solo_game_stops_while_its_player_is_away_and_resumes_on_their_return`
- `SOLO_PARK_TTL_SECONDS = 3600`, `MULTI_PARK_TTL_SECONDS = 86400`, `ROOM_LIST_TTL_SECONDS = 7200`;
  the sweep runs every 60 seconds and skips a game with a human connected: **code**
  [`server/config.py`](../../../server/config.py), [`server/housekeeping/sweeper.py`](../../../server/housekeeping/sweeper.py)::`is_expired`

**Restart recovery (3.5)**

- Shutdown cancels and writes nothing: **code** `live_game_registry.py`::`shutdown`,
  `game_session.py`::`suspend`
- Recovery: **code** [`server/housekeeping/recovery.py`](../../../server/housekeeping/recovery.py)::`recover_registry`,
  `live_game_registry.py`::`revive`, `_resume_from_checkpoint`, `game_session.py`::`reload_history`;
  **test** `tests/server/test_durability.py`::`test_parked_game_revives_reparked_and_resumes_on_the_answer`,
  `test_restart_before_every_resolution_matches_uninterrupted_play`
- Re-opening a question sends no new event; the browser gets the original from the replay:
  **code** `game_session.py`::`park`, `server/routes/games.py`::`event_stream`
- Seat tokens are stored in the game's row, in plain text; cookie `max_age` 24 hours: **code**
  `live_game_registry.py`::`revive`, [`server/routes/_shared.py`](../../../server/routes/_shared.py)::`set_seat_cookie`
- A lost accepted answer: **inferred** from the futures being in memory only
- The key-funded game: **code** `live_game_registry.py`::`resume_with_key`; **test**
  `test_byok_game_waits_for_its_key_and_resumes_when_a_seat_holder_funds_it`
- The recovery tests use a stand-in graph; the real path was checked by hand: **code** the
  header of `tests/server/test_durability.py`

**dota2pred (in the workers document, working/u15_detail_workers_and_leases.md)**

- The deployment's `concurrency_limit=1` and the start-up step that marks leftover runs as
  crashed: **code** `live_orchestrator_app/src/live_orchestrator_app/deploy_service.py`::`create_deployment`,
  `_crash_orphaned_runs`
- The stale sweep finds entries by the time in their stream id, older than
  `COMPLETION_FREE_FEED_WINDOW_SECONDS = 7200`, and claims up to 50 a cycle with `XCLAIM`:
  **code** `redis_services/redis_service.py`::`fetch_expired_events`, `claim_expired_events`

**Incidents on record**

- 2026-08-19: the first two-human game stopped at the vote; resuming had re-run the AI votes.
  [`frontend/docs/server_encountered_challenges.md`](../../../frontend/docs/server_encountered_challenges.md) sections 2 to 4
- 2026-10-17: a human wolf's prompt waited for the other wolf's model call (commit `2814776d`);
  the same file and `server_client_transport.md` section 8b

**Not established**

- That a pause inside a smaller graph always appears at the top level of the saved state on
  langgraph 1.1.10. The recovery tests use a stand-in.
- Whether the routing that announces a human's turn runs again on a resume and, if so, whether
  it can re-open a question that then gets no pause. The docstrings say routers run again; not
  traced.
- Whether the browser can be shown a prompt before the checkpoint holding its pause is
  committed. Read in the library's source only.
- How a wrongly shaped answer body is turned into a status code.

**Framework specifics, pointed to**

- Interrupts arriving once per level of nested graphs, and the engine redoing work after an
  answer: `frontend/docs/server_encountered_challenges.md` sections 1 and 3
- The human turn as a design, with its options: `frontend/docs/server_client_transport.md`
  section 8b; the write-up page `writeup/game_design_orchestration/human_in_the_loop/`

**Reading** (titles only; no links, because I have not checked the addresses)

- Temporal's documentation, "What is durable execution?": the general idea in 1.1 and 1.2, and the recorded-history row of Part 4, from
  a service built for it.
- LangGraph's documentation on interrupts and on persistence: the pause as this library does
  it, including that a paused node starts again from its first line.
- Martin Kleppmann, *Designing Data-Intensive Applications*, chapter 8, the section on leases
  and fencing: why a lease alone does not guarantee a single runner (the workers document).
