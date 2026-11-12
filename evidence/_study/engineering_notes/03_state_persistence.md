# U3. State persistence: the concepts, and a review of my system

**Reading time:** about 80 minutes (including checks; estimate) · **Builds on:** U0, U2 · **Feeds write-up chapters:** 7 and 8

**The question these notes answer:** the process dies in the middle of a task. What must already
have been saved, and what can be rebuilt from it?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

U2 ended on a fact it could not use: everything a game holds in one process's memory is gone when
that process stops. This note is about what is kept outside it.

## What these notes cover

1. What a crash takes, and the two things that can be saved against it: the current state, or the
   list of what happened.
2. When a save happens, and why the moment decides how much work is lost.
3. How work starts again, and what it means that some of it is done twice.
4. Which record is believed when two of them disagree.
5. A review of what my Werewolf server saves, when, and what a restart really does, with the gaps.

**Covered in other notes:** which store is the record of which fact (U0), the saver's lock as a
concurrency limit (U2), making a repeated action harmless (U4), a game waiting for a person (U5),
catching a viewer up after a reconnect (U6), and traces (U8).

---

# Part 1 — What survives a crash

A long task holds its progress in memory while it runs. This part is about getting that progress
somewhere safer, and about the price of each way of doing it. It answers five questions:

1. **What does a crash take?** (memory, and durable storage)
2. **What is saved: the state, or what happened?** (a snapshot, an event log)
3. **When is it saved?** (save points, and the window of loss)
4. **How does the work start again?** (resume, replay, and redone work)
5. **Which record is believed?** (one authority for each fact)

The example throughout is a food-delivery service. An order goes through steps: placed, paid,
accepted by the restaurant, rider assigned, picked up, delivered. One server program moves each
order along, and the customer watches a tracker in the app.

## 1.1 What does a crash take?

The server keeps each open order as an object in its memory: the items, the current step, which
rider was chosen, how many times the restaurant was reminded. That is fast, and it is gone the
moment the process stops. A deploy, a crash, or the machine running out of memory all end the
same way: forty orders in progress, and a new process that knows about none of them.

**Durable** storage is storage that survives the process: a database, or a file on disk. Anything
that must outlive a restart has to be written there before the restart happens. A crash gives no
warning, so "save on the way out" is not a plan. The saving has to happen as the work goes.

So for every piece of state there is one question: if the process died right now, would this be
needed, and where would it come from? There are three honest answers.

| Answer | Example in the delivery service |
|---|---|
| It is saved | The order's items and its current step |
| It can be rebuilt from what is saved | The order total, worked out again from the items |
| It is lost, and that is acceptable | Which customers currently have the tracker open |

The dangerous state is the kind nobody asked the question about.

## 1.2 What is saved: the state, or what happened?

The support team is asked why order 88 changed riders twice. Its current row says only "rider:
Sam". That row is enough to find the current rider; it cannot explain the changes that were
overwritten.

**A snapshot** records state at a particular point: "order 88 is at step *rider assigned*, rider
is Sam, reminders sent: 2". It can contain whatever state recovery needs, including history if
that history is part of the state. A current-state snapshot alone does not preserve each change.
Keeping older snapshots preserves earlier states, but may still miss changes between saves.

**An event log** records selected facts as an ordered sequence: "order placed", "payment
confirmed", "restaurant accepted", "rider Sam assigned". **Append-only** means normal changes
are new entries rather than edits to previous entries. It does not mean retention is impossible.
A log records only the facts its designers chose to capture; it is not automatically a complete
history of the system or proof that a customer actually saw a message.

| | Current-state snapshot alone | Event log |
|---|---|---|
| Stores | State at the save point | Recorded changes in order |
| To find current state | Load it | Apply relevant events, if they contain enough information |
| History | Only what is included in the state or retained older snapshots | The events retained, at the detail recorded |
| Cost | Size of the saved state and frequency of saves | Event storage and the work of reading and applying events |

Reading recorded events and applying them again is **replay**. The resulting view is a
**projection**. The same order events might build the customer tracker and a report of rider
changes, provided they contain the fields each view needs.

### Check

The current order row says Sam. A log records "rider changed" twice, without names or reasons.
Can support explain why the rider changed, or reconstruct the previous riders?

<details>
<summary>Answer</summary>

Neither record contains enough information. The log establishes two changes but not who or why.
Recording the previous and new rider and a reason would support those questions. Having a log
is useful only for questions its recorded facts can answer.
</details>

### When the log becomes the record

Suppose every change needed to rebuild an order is committed as an event. The current row is
then derived from those events, rather than maintained as an independent truth. This is
**event sourcing**: the log is authoritative for the order state. An audit log beside an
independently updated order row is not, by itself, event sourcing.

For order 88, applying "placed", then "payment confirmed", then "restaurant accepted" produces
state "accepted". Applying "rider Sam assigned" changes the rider to Sam. Applying each event
to the state produced so far is also called **folding** the events.

Order matters. "Sam assigned" followed by "assignment cancelled" leaves no rider; reversing
those entries leaves Sam. The writer assigns a **sequence number** within the order's stream,
and the storage path enforces that order. Two writers cannot safely choose the same next number
independently: a single writer or a conditional append must resolve competing writes. A timestamp
alone does not settle that race. These numbers order one stream; they need not order all orders
in the service.

Rebuilding the tracker applies recorded facts. It does not charge the card again or ask which
rider is nearest now. Those are new actions, with their own handling of repeats (U4).

### Check

An order's events are numbered 1 to 4. Event 4 says "rider Sam assigned". The nearest rider is now
Ana. What should replay choose, and does replay send Sam another assignment message?

<details>
<summary>Answer</summary>

Replay sets the rider to Sam from event 4. It does not make the choice again. Rebuilding this
projection sends no messages. A separate process that acts on events needs protection against
repeating its effects; replay alone does not provide that protection.
</details>

## 1.3 When is it saved?

The server has chosen Sam, but the database has not confirmed the write. Killing the process now
may lose that choice. Starting a write and completing a durable save are different moments.
The **window of loss** is the work since the last successful durable save that cannot be rebuilt
from another surviving record.

For a system recovering only from snapshots, the choices include:

- **Save after every step and wait before continuing:** at most the current unsaved step needs
  repeating, assuming the writes succeed.
- **Save on a thirty-second timer:** roughly an interval of work can be lost, plus write delay;
  failed or delayed saves can make the window larger.
- **Save only at completion:** no intermediate progress is recoverable from that snapshot.

Waiting adds the write's latency to the path. Saving in the background overlaps work with the
write, but progress can outrun the durable record. There is no general one-step bound without a
rule that limits how far work may advance.

In the event-sourced order, each accepted change is saved in the log before the server confirms
it. A derived tracker may update later. A crash can lose the tracker's in-memory view without
losing the committed order changes, because the tracker can be rebuilt.

Saving before confirming a change avoids promising a choice that exists only in memory. It
does not eliminate every uncertainty: the write may succeed and the process die before the
confirmation reaches the customer. Retrying that request safely belongs to U4.

### Check

A service starts a snapshot write every thirty seconds, but the database has rejected writes for
two minutes. Can it promise at most thirty seconds of lost progress?

<details>
<summary>Answer</summary>

No. The boundary is the last successful durable save, not the last timer tick. The service must
stop accepting progress, retain it in another durable record, or accept and expose a larger loss
window. The timer alone establishes no such guarantee.
</details>

## 1.4 How does the work start again?

A new process finds order 88 unfinished. What it does next depends on what was saved.

**Load a snapshot and continue.** If the snapshot contains the workflow state and its position,
load it and continue there. Work whose results were not saved may need repeating. A snapshot of
only the customer-facing fields is not necessarily sufficient to resume the workflow.

**Replay an authoritative log.** Start from an empty order and apply its recorded changes in
sequence. This recovers the state represented by those events without repeating the decisions
that produced them. Recovery needs compatible event readers and enough information in the log.

**Load a snapshot, then replay the later events.** Long histories make replay expensive. Save the
state after event N together with N, then recover by loading that state and applying events after
N. The snapshot and its position must describe the same prefix of the same stream. Including
N again could apply a change twice; skipping N+1 could lose a change.

For order 88, a snapshot after event 3 says "accepted, no rider". Event 4 says "rider Sam
assigned". Recovery loads the snapshot, applies event 4, and obtains "rider Sam assigned".
It does not ask the dispatch service to choose again. An older valid snapshot still works; it
just requires replaying more events. If the complete log remains, a missing snapshot can be
rebuilt from it.

A snapshot shortens recovery but does not shrink the log by itself. **Compaction** or retention
can discard older detail while preserving enough for a chosen recovery boundary. That can
sacrifice historical queries or the ability to build new projections from the beginning. Before
deleting events, decide which recovery and audit uses must remain possible.

**Re-run workflow code against recorded results.** A workflow engine can instead record its
execution history and use recorded activity results while replaying workflow code. The workflow
must remain compatible with that history and obey the engine's determinism rules. Calls without
a durably recorded outcome may still need retrying or reconciliation. This is a different replay
contract from folding domain events into an order; U5 takes up durable workflows.

The question common to these designs is **which results survived**, not "which steps always run
twice?" A recorded result can be reused. Missing work may be repeated. A pure calculation can be
repeated harmlessly; a new rider choice may differ; a payment may have succeeded even when its
result was lost. Recovery of state and safe repetition of effects are separate obligations.

### Check

A snapshot is labelled "through event 40". The log ends at event 43. Which events are applied on
recovery? What if the snapshot actually contains state only through event 39?

<details>
<summary>Answer</summary>

Apply 41, 42 and 43, in order. If the label is wrong, event 40 is silently omitted. Save the
snapshot state and its matching stream position together from a consistent view. A newer label
cannot make an older state correct.
</details>

## 1.5 Which record is believed?

The tracker says "accepted" while event 4 already says "rider Sam assigned". In an event-sourced
design, this is a stale projection. The log wins for the rider, and applying the missing event
brings the tracker up to date. A snapshot behind the log is also expected, not a competing truth.

A different design can keep a workflow checkpoint and a separate log of outgoing messages.
The checkpoint holds internal state; the message log records what was sent. Neither necessarily
contains enough information to reconstruct the other. This is the shape used by my project.

| Design | Authority for the order's rider | Meaning of a snapshot or view behind the log |
|---|---|---|
| Event sourcing, optionally with snapshots | The order's event stream | Catch up by applying the later events |
| Workflow checkpoint plus outgoing-message log | Checkpoint for workflow state; message log for recorded output | Inspect what each record means; replaying messages may not reconstruct workflow state |

The second design still needs a rule where the facts overlap. If the message log says Sam but
restarting the workflow chooses Ana, naming two authorities does not resolve the assignment.
The design must preserve and reuse the committed choice, coordinate persistence and publication,
or explicitly reconcile the conflict. Suppressing a second message alone leaves two answers.

The useful question is: is this snapshot a saved projection of the log, or an independent record
of different state? That determines whether "load it and replay the tail" is valid.

## 1.6 One order, one crash, start to finish

Here the delivery service uses event sourcing. The order stream records every state change
needed by this example, and the server confirms a change only after its append succeeds.

```text
18:02  Save events 1 (placed) and 2 (payment confirmed).
18:05  Save event 3 (restaurant accepted).
       Save snapshot: order 88, through event 3, state "accepted, no rider".
18:11  Dispatch chooses Sam. Save event 4 (rider Sam assigned).
       The tracker applies event 4 and shows Sam.
       A new snapshot starts writing, but the process dies before it completes.

       Surviving records: snapshot through 3; log through 4.
       Lost: in-memory tracker and connections. The committed choice survives.

18:12  Load the valid snapshot through 3.
       Read events after 3, in order: event 4.
       Apply "rider Sam assigned". Recovered order: rider Sam.
       Rebuild the tracker from the recorded state. Do not choose or notify again.
```

An incomplete new snapshot is ignored; recovery uses the previous valid one. If there were no
snapshot, replaying events 1 to 4 would give the same state at greater cost. If the crash had
happened before event 4 committed, the choice would not be recoverable from these records.

Contrast the separate-message-log design: if only the outgoing message "Sam assigned" survived
while the workflow checkpoint still said "accepted", resuming the workflow might choose Ana.
A guard could suppress the new message while leaving Ana in the workflow. Section 3.6 examines
that possible failure in my system. It is a consequence of that persistence contract, not a
necessary property of snapshots and logs.

---

# Part 2 — The choices

The decisions below are not alternatives to each other. The choices are inside each one. Within a
table, a system can use more than one row, in different places; the last column says where mine
uses each.

**Which record carries the state?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| Current-state snapshot alone | Direct loading | Earlier changes unavailable unless separately retained | Current state is sufficient | Checkpoints provide engine recovery state; earlier checkpoints are also kept |
| Authoritative event log, replayed from the beginning | Rebuildable state and recorded history | Replay cost; event ordering and version compatibility | History and alternative views justify the extra design work | Events rebuild the server's view, not the engine |
| Authoritative log plus snapshots at known positions | History with shorter recovery | Consistent state/position pairs; snapshot storage | Streams are long enough to make full replay costly | Not the engine recovery design |
| Workflow checkpoint plus a separate output log | Internal execution state and a record of output | A recovery contract for overlapping facts | The output log omits internal workflow state | Checkpoints resume the engine; events rebuild the server's view |

Retention is a separate choice in each design. Keeping the full log preserves recorded history;
compacting or deleting an old prefix can reduce storage but limits later replay and audit uses.

**When does a save happen?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| After each step, and wait for it | Confirmed saves survive the assumed process crash | One write's delay on every step | Losing a step is expensive | Events: written and waited for after every chunk of engine output |
| After each step, in the background | Overlaps writing with work | Uncommitted progress may be lost; writes still consume capacity | Redoing a step is cheap | Checkpoints: the library's default mode, which I never changed |
| On a timer | Fewer writes | Loss since the last successful save, including delays and failures | The data is a tally, not a commitment | Usage counts: at most every 30 seconds |
| Only at the end | Nothing during the run | Everything in progress is lost | The task is short, or the data is optional | The prompt capture for the leak audit |

**How does work start again?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| Resume from the snapshot | Direct loading of saved workflow state | Unsaved work may need repeating | Steps can be repeated | The engine, after a restart and after every human answer |
| Replay the log to rebuild state | Reuses recorded facts without making decisions again | The log must hold everything the task needs | State is fully derivable from events | The server's view of a game (what was sent, the send-once guards). Not the engine. |
| Load snapshot at N, replay after N | Avoids replaying the whole history | Snapshot must match its stream position | Long event streams | Not used for engine recovery |
| Re-run code against recorded results | Reuses outcomes recorded in workflow history | Compatible deterministic workflow code; unresolved calls still need handling | Long workflows where a repeated call is costly | Not used |

**What is done about work that runs twice?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| Accept the repeat | Nothing to build | The repeat's cost, and a possibly different answer | Repeats are rare and cheap | A sequential turn in flight at a crash: the model is called again |
| Cache the first result | The repeat is free and identical | The cache has to survive whatever caused the repeat | Results are costly or non-deterministic | AI turns in parallel steps are cached, in memory. It covers a human pause. It does not cover a restart. |
| Refuse to send the same thing twice | No doubled output | The first output and the new state can differ | Output must not repeat | The translator's send-once guards, rebuilt from the log on restart |
| Persist the choice before showing it, then reuse it | Avoids showing an unrecoverable choice | Coordinated save and publication; delivery retries remain | The output is a commitment | Not used |

The requirements decide which rows fit: recovery time, required history, tolerated loss and the
cost of repeated work. A design that cannot preserve a promised fact is unsuitable for that promise.

---

# Part 3 — My Werewolf system

## 3.1 The picture I had wrong

Until I checked the code on 2026-11-11, I held this picture: the checkpoint is only used to build
events, and after a restart a game is rebuilt from the event log, since the database holds it
anyway. A draft of the write-up said "recovery replays the event log".

That is not what the server does. The engine restarts from the checkpoint. The event log is used
too, but only to rebuild the server's own view of the game. The log is never fed into the engine.
The rest of this part is why, and what follows from it.

## 3.2 What a crash takes

Everything below lives only in the server process's memory.

| Lost on a restart | What the restart does about it |
|---|---|
| The futures a game waits on for human answers, and the list of open questions | Rebuilt: the open questions are read from the checkpoint and asked again |
| An answer a human had submitted that had not yet been saved | Lost. The seat is asked again. |
| Each viewer's queue | Gone. The browser reconnects and is caught up from the log (U6). |
| The cache of AI turns | Empty. Section 3.6 is about what that costs. |
| The breaker's stall count (U1) | Starts from zero. The game tries its main model first again. |
| The clocks on human seats | Started again with a full time limit |
| The progress bar's state | New. No bar shows until the engine's next output. |
| A player's own API key | Never stored, on purpose. The game waits until a seat holder supplies it again. |
| Usage counts since the last save | Up to 30 seconds of them |
| The prompt capture so far | Lost, and the capture is marked partial |
| Waiting rooms that had not started | Gone, by an earlier ruling |

A planned shutdown is no gentler than a crash. It cancels each game's task and its clocks and
writes nothing extra. So the save points in 3.4 are all there is.

## 3.3 What is saved

A game writes to three records in Postgres, and each has one job.

| Record | Kind | What it holds | Believed for |
|---|---|---|---|
| Checkpoints | A snapshot after each engine step, kept as a chain | The engine's whole state: rule counters, who acts next, the input of a paused human turn, open questions | Running the game |
| The events table | An append-only log, keyed by game and event number | Every event, each marked with who may see it | What each audience was sent; the replay of a finished game |
| The game's row | One row, updated in place | Identity, status, seats, model, usage, completion details | Whether the game exists and what state it is in |

There is no separate replay archive. A finished game's replay is its rows in the events table.

**Why the engine resumes from the checkpoint and not from the log.** The log holds everything
that can be shown. The checkpoint holds everything the engine needs, and some of that is never
shown: how many uses a role has left, a streak counter, the exact input of the turn a human is in
the middle of, and where the engine is in its run. The log cannot restart the engine because that
state is not in it. My engine does not implement reconstruction from a complete domain-event
stream or re-execution against a recorded workflow history. Those are different designs, not
alternative ways to read my existing events table.

**Where the server reads a checkpoint.** In three places only: restart recovery, the preview of a
paused human turn, and the prompt capture after a game ends. Events are never built from a
checkpoint. They come from the engine's live output, through the translator.

The lesson store is a fourth thing in Postgres, and games mostly read it. One exception: a game
with memory on updates counters in it during a turn. Section 3.8 returns to that.

## 3.4 When it is saved

The two main records are saved on different schedules.

**Events: after every chunk, and waited for.** Each time the engine puts out a chunk, the game's
task translates it into events and writes them to the table before reading the next chunk. The
write ignores an event number it already has, so a repeat does no harm. If the write fails, the
unsaved events stay queued and the whole tail is tried again after the next chunk.

**Checkpoints: after every step, in the background.** The graph library starts the save and moves
on to the next step without waiting. This is its default mode, called "async", and my code never
sets another. Two finer points, both read in the library's source:

- The library also saves each task's result on its own as that task finishes, again in the
  background. My seed note said "the checkpoint is written only when a whole step finishes", which
  left this out. It matters in 3.6.
- The day phase and the wolf pack's phase are graphs inside the main graph. They save their own
  checkpoints, one for each inner step, through the same saver.

**Everything else.** Usage counts are saved at most every 30 seconds and at the end. The game's
status changes when it finishes or fails. The prompt capture is saved once, after the game ends.

**The one-step lead.** Put the two schedules together: an event is written and waited for, while
the checkpoint for the same step is still on its way. A crash in that gap leaves the events table
one step ahead of the checkpoint. That was recorded as a known behaviour when the server was
built, and the library code that causes it is unchanged.

## 3.5 Starting again

At start-up the server opens the database and the graph, then looks for games to bring back.

1. **Which games.** Every game whose row says "running". A finished or failed game is not
   touched. If bringing one game back raises an error, that game is marked failed with the reason
   "recovery failed on restart", and the rest carry on.
2. **The server's view, from the log.** The game's events are loaded and replayed into a fresh
   translator. That restores the event counter, who has which role, and the send-once guards.
   This recovery replay rebuilds the server's memory, not the engine's.
3. **The engine, from the checkpoint.** The server reads the game's latest checkpoint.
   - If nothing is left to run, the game had in fact finished and only its row was out of date.
     The row is closed.
   - Otherwise every open question in the checkpoint is asked again, and the engine is started
     from that point.
4. **A game on a player's own key** is rebuilt but not started. It waits for a seat holder to
   send the key again, since the key was never stored.

A viewer who reconnects is replayed the log from the last event their browser received, with each
event filtered for what that viewer may see, and then gets live events. A solo game whose player
has not reconnected reads one chunk and waits (the backpressure of U2's section 3.4).

**How this is tested.** The recovery logic has tests, and they pass. They run against a stand-in
for the graph and the database, as the test file's own header says. The real path, a server
killed and restarted against real Postgres, was checked by hand in August and is recorded in one
line as "restart smoke passed". No automated test kills and restarts a real game.

## 3.6 The work that is done twice

Resuming from a checkpoint re-runs the step that was in flight. In my engine that happens in two
situations, and they differ in one important way.

**After a human answers.** The engine pauses a step to ask a person. When the answer comes, the
library runs the paused step again from the top. If that step holds several seats acting side by
side, such as a vote, the AI seats that had already finished are run again too. That would be a
second model call for each, and possibly a different answer.

The fix is a cache on those AI turns. A repeated turn with the same input is answered from the
cache, with no model call and the same result. Human turns are never cached: a cached human answer
would be played back instead of asking the person.

**After a restart.** The same re-run happens, but the cache was in the process's memory and is now
empty. So the AI seats of the step in flight call the model again, are billed again, and may
answer differently. The cache covers a pause. It does not cover a restart.

What exactly is redone depends on where the step sits. I measured this with a small stand-in
graph using an in-memory saver and the blocking stream, not Postgres and the async stream.
Appendix B records those limits; this is not a real-process restart measurement.

| The crash lands in | Run again | Not run again |
|---|---|---|
| A parallel step in the main graph (the solo night roles) | Only the tasks that had not finished | Finished tasks: their saved results are reused |
| A parallel step inside the day or pack phase (a vote, a round) | Every task of that step, finished or not | All earlier steps of the phase |
| A one-at-a-time step inside the day phase (a discussion turn) | That turn | All earlier turns |

**What stops a repeated turn being shown twice.** The translator keeps send-once guards, and a
restart rebuilds them from the log. A discussion line with a day and number it has already sent
is dropped. Wolf chat, memory events and private reads are guarded the same way. Votes need no
guard: ballots are held back until the whole vote is collected, so a re-run ballot is simply the
one that counts.

**What that leaves.** This is Part 1's worked case with the rider. Suppose a discussion turn's
line was written to the events table, and the process died before the checkpoint for that step
landed. After the restart the turn runs again and the model may write a different line. The guard
drops the new line, so viewers keep the old one. The engine's state holds the new one, and the
next speakers are prompted with it. The log and the engine then disagree about what that player
said. I read this in the code. It has not been reproduced, and no test covers it.

### Check

A game is in the middle of a day vote: seven AI seats have voted and three are still calling the
model. The server process is killed and restarted. How many model calls are made for this vote
after the restart, and why is the answer different from a pause for a human voter?

<details>
<summary>Answer</summary>

The stand-in experiment predicts ten, assuming all ten seats are AI and the vote step was not
durably completed. This has not been verified with a real Postgres restart. In that experiment,
every seat of the inner step runs again, and
the cache that would have answered the seven finished seats was in memory and is gone. After a
human pause in the same process the cache is still there, so the seven are answered from it and
only the unfinished work is done. No ballot was shown before the crash, because ballots are held
until the vote is collected, so the re-run does not contradict anything a viewer saw.
</details>

## 3.7 The saver

One saver object serves every game, with a pool of 4 database connections. Its shared lock
serializes database access through that saver, so the pool does not provide four concurrent
checkpoint operations. Appendix B retains the correction to U2 about which operations hold the
lock while waiting for a thread, and the option of a saver per game. U2 section 3.7 (gap 1.2)
has the fix in full: a saver per game, all sharing the one pool, each carried by a cheap copy of
the compiled graph. It is chosen to build and not yet built.

Recovery also depends on reading saved state back into the right types. The saver has an
allow-list of classes it may reconstruct. Missing classes have previously loaded as plain data
with a warning; a test now checks the list against the engine's state types.

## 3.8 Gaps

The first five are also rows 9 to 13 of [improvements.md](improvements.md), the one list of
limitations across the notes.

**1. The real restart path has no automated test.** The logic is tested against stand-ins. A kill
and restart of a real game on real Postgres was last checked by hand in August.

**2. A restart can leave the log and the engine disagreeing about a line.** Section 3.6. Read in
the code, not reproduced. Three candidate changes to investigate; none is verified here as closing the whole crash window:

| Fix | Good | Bad |
|---|---|---|
| Wait for checkpoints and coordinate publication with their completion | Could ensure the choice is durable before viewers receive it | Waiting before the next step alone does not establish output ordering; verify that path and measure latency |
| On a re-run, reuse the line already in the log | Viewers and engine agree | The engine would read its own output back from the log, which crosses the authority line of 3.3 |
| Persist turn results and reuse them on restart | A recorded result can prevent another model call and a changed line | Requires stable keys and saving the result before publication; cache misses and failed writes still need handling |

**3. The turn cache does not survive a restart.** AI seats of the step in flight are billed again.
The third row could avoid repeated calls whose results were successfully recorded.

**4. Nothing is ever deleted.** No code removes a finished game's checkpoints or events. The
design notes say retention was left out on purpose and never built. Nobody has measured how large
one game's saved state is. The one figure on record is an estimate of a few megabytes per game,
with growth faster than the number of steps.

**5. A re-run turn may count twice in the lesson store.** A game with memory on bumps counters in
the lesson store during a turn. A turn that runs twice would bump them twice. This is my reading
of the code and I did not trace the conditions under which those writes happen.

**6. Smaller losses that are accepted:** up to 30 seconds of usage counts, a human's answer that
had not been saved, and the prompt capture of a game that was restarted.

---

# Part 4 — What would change at a larger scale?

**Games on workers.** U2's Part 4 said games can only be spread over several processes once their
progress is in a durable record. It already is, which is the good news of this note. What is not
ready is everything in 3.2 that lives in memory, and the turn cache above all: a game moved to
another worker would meet an empty cache exactly as after a restart.

**Waiting for saves.** With one process, a lost step costs a few repeated model calls. With many
workers and games moving between them, restarts of one kind or another become routine, and the
disagreement of gap 2 becomes routine with them. The first change I would investigate is coordinating output publication with durable checkpoint
completion, testing crash positions on both sides of the writes and measuring the latency cost.

**Retention.** Storage accumulates even at low volume. Finished-game checkpoints are candidates
for deletion because viewer replay uses events, but deletion must follow completion of prompt
capture and any required debugging or recovery uses. Measure size and define a retention boundary
before removing either checkpoints or events.

---

# Part 5 — Worked problems

Each is answered from memory first; my answers are in Appendix A.

## Problem A: The same concepts in another system

A chat service rewrites one JSON conversation snapshot after each message. It shows the message
before the save completes. After crashes, users report missing messages; support also cannot
reconstruct earlier versions of edited messages. Each conversation can grow to 100,000 changes.

1. Choose records and an authority for message content and edits. What must succeed before a
   message is acknowledged as saved? Does this establish that another user saw it?
2. Design recovery using a snapshot through event 800 and a log through event 805. What must
   the snapshot's label mean, and which events are applied?
3. Two server processes edit the same conversation at once. Who assigns order, and why are
   timestamps alone insufficient? Which two projections could use the resulting log?
4. What does deleting events 1 to 800 buy and lose? What if support needs all previous edits?
5. An event says an AI reply was generated. Does replay call the model again? What must the
   event contain to reconstruct the reply?

## Problem B: My system, without Part 3 open

1. Which three records does a game write, and what is each one believed for?
2. After a restart, what is rebuilt from the event log and what from the checkpoint?
3. Why can the engine not be restarted from the event log?

## Problem C: A claim, checked against the code

"If the server restarts in the middle of a game, the game carries on exactly where it was and
nothing is lost."

Which parts of this does the code support, which does it contradict, and what has never been
tested?

## Problem D: The sharp question

What can an event log tell that a state snapshot cannot, and what does it cost? Answer with
one example from outside this project and one from mine.

---

# Part 6 — Summary

**1. A crash takes everything in memory, without warning.** What must survive is written as the
work goes. For each piece of state: is it saved, can it be rebuilt, or is losing it acceptable?

**2. Decide whether the log is authoritative or supplementary.** Event sourcing rebuilds state
from recorded changes. An output log may omit state needed to resume the producer.

**3. Recover from successful durable saves, not scheduled writes.** Define when a result may be
confirmed and what happens when persistence is slow or fails.

**4. A snapshot used to accelerate replay needs a matching position.** Load state through N,
then apply events after N in order. Retention must preserve the history each recovery path needs.

**5. Rebuilding state does not mean repeating its effects.** Reuse recorded outcomes; identify
unsaved or uncertain work separately. A guard against duplicate output does not guarantee that
the recovered internal state agrees with the original output.

### My system in one paragraph

A game writes three records: checkpoints (a snapshot of the engine's state after each step), the
events table (an append-only log of everything each audience was sent) and the game's row. Events
are written and waited for after every chunk of engine output; checkpoints are saved in the
background, so the log can be one step ahead after a crash. On a restart the server rebuilds its
own view of each running game by replaying the log, and restarts the engine from the checkpoint,
asking open human questions again. Unsaved work can run again. Within one process a cache can
reuse completed AI turns in cached parallel steps; after a restart the cache is empty, so those
turns can be billed again and
may differ, and a send-once guard keeps viewers from seeing a line twice while the engine may hold
a different one. The recovery logic is tested against stand-ins; a real kill and restart was last
checked by hand. No checkpoint or event retention is implemented.

U4 takes up the remaining question: how to handle a repeated action without repeating its effect.

---

# Appendix A — Answers to the problems

## Problem A: The chat service

1. One suitable design is an authoritative per-conversation event stream containing message IDs,
   original content and subsequent edits. Acknowledge a saved change only after its append
   commits. The current conversation is a projection. This records accepted content, not proof
   of display on another device; that would need separate delivery or display evidence. A
   transactionally maintained current row plus edit history is another valid design if its
   authority and recovery rules are explicit.
2. Assuming the snapshot contains exactly the state after event 800, load it and apply 801 to
   805 in order. Persist the state and its matching position consistently. If the snapshot is
   absent, the full retained log can rebuild the conversation from the beginning.
3. The append path assigns and enforces per-conversation sequence numbers, using a single writer
   or conditional appends against the expected stream version. A competing write must reload
   and resolve the conflict. Equal or skewed timestamps cannot establish the intended order.
   The current conversation and support's edit-history view are two projections.
4. Removing the prefix reduces storage. A valid snapshot plus the tail may still restore the
   current conversation, but cannot necessarily reconstruct earlier edits or new historical
   views. If support needs every edit, preserve those events in the live log or an accessible
   archive. A snapshot alone is not permission to delete its source history.
5. Projection replay uses the recorded reply text and message ID, not a fresh model call. An
   event that merely says "generated" is insufficient. If no outcome was durably recorded,
   recovery faces a separate decision about retrying the call and accepting its cost and
   potentially different answer.

## Problem B: Werewolf

1. Checkpoints, for running the game. The events table, for what each audience was sent and the
   replay of finished games. The game's row, for whether the game exists and its status.
2. From the log: the server's view, meaning the event counter, roles and the send-once guards.
   From the checkpoint: the engine's state and the open human questions.
3. The log holds what can be shown. The engine also needs state that is never shown: rule
   counters, the input of a paused turn, and where it is in its run. The existing event stream
   and recovery code do not implement reconstruction of that state.

## Problem C: The claim

**Supported:** a running game is found at start-up and brought back; the engine restarts from its
last checkpoint; open human questions are asked again; viewers are caught up from the log; all
steps included in durable checkpoints are available for recovery. A step finishing in memory
is not sufficient evidence that it survived.

**Contradicted:** "exactly where it was" and "nothing is lost". The step in flight runs again. A
human answer not yet saved is lost. After a restart the AI turns of that step are billed again and
may differ, and a discussion line can end up different in the log and in the engine. Up to 30
seconds of usage counts and the prompt capture are lost.

**Never tested:** an automated kill and restart of a real game on real Postgres; the disagreement
between log and engine; the behaviour of saves already under way when the process stops.

A claim the code supports: "a restarted server brings its running games back from their last
saved step, asks any open human question again, and catches viewers up from the event log; the
step in flight is repeated, which can re-bill AI turns."

## Problem D: The sharp question

A log can say how the present state came about, and can be read again for a purpose nobody had in
mind when it was written, if the needed facts were captured. A current-state snapshot alone does
not explain the sequence of changes. The cost is size, the work
of replaying, and having to decide what the log is believed for when it disagrees with other
records.

Outside example: a delivery order's log can answer "why was the rider changed twice?" if it
records the reasons for reassignment; its current rider field cannot. From my system: one events table serves the wolves' view, the spectators' view and
the replay of a finished game, and an audience can be widened at game over, because every event is
stored once with who may see it. The project serves those views from events; its checkpoints
are used for engine state.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **library** (the
installed library's source was read), **measured** (a local script, with no network and no
database), **test** (named; run or not run is stated), **doc** (a project document says so and it
was not confirmed in code), **none**. A code read was done for this note on 2026-11-12. Items I
checked a second time myself are marked "re-checked". Library versions: langgraph 1.1.10,
langgraph-checkpoint 4.2.0, langgraph-checkpoint-postgres 3.1.0.*

**What a crash takes (3.2)**

- The in-memory items and what recovery does with each: **code**
  [game_session.py](../../../server/game/game_session.py),
  [seat_clocks.py](../../../server/game/seat_clocks.py),
  [live_game_registry.py](../../../server/game/live_game_registry.py),
  `Agents/llm_factory/health.py`
- A planned shutdown writes nothing extra: `LiveGameRegistry.shutdown` calls `suspend()` on each
  session. **code**
- What happens to background saves already submitted when the task is cancelled: **none**

**What is saved (3.3)**

- The saver: `AsyncPostgresSaver`, built in `GraphRuntime.startup` and passed to
  `parent_graph.compile`. **code** [graph_runtime.py](../../../server/graph_runtime.py)
- Events: `GameRepository.record_events`, with `on_conflict_do_nothing` on game and event number.
  **code** (re-checked) [game_repository.py](../../../server/storage/game_repository.py)
- The three checkpoint tables and their keys: **library** `checkpoint/postgres/base.py`
- No separate replay archive: **code** (the comment in `_drive_graph`; `complete_game`)
- The three places the server reads a checkpoint: `_resume_from_checkpoint`, `_save_capture`,
  `_turn_payload`. **code**
- The authority split written down: **doc** `frontend/docs/server_client_transport.md` section 4;
  `frontend/docs/server_design_notes.md` section 5c
- The lesson store written during a turn: `process_strategy_adoption`, called from
  `Agents/turn/pipeline.py`. **code**; the conditions of those calls: **none**

**When it is saved (3.4)**

- Events awaited after every chunk: `_drive_graph` calls `await self._persist_tail()`. **code**
  (re-checked)
- A failed save retries the whole unsaved tail: **test**
  `test_failed_saves_retry_the_whole_unsaved_tail_and_human_assignment` (run, passed)
- Checkpoint saves in the background, per step and per task: **library**
  `langgraph/pregel/_loop.py` (`put_writes`, `after_tick`, `_put_checkpoint`)
- The default mode is "async" and the project never sets another: **library**
  `langgraph/pregel/main.py` (re-checked); **code** (search of `Agents/`, `server/`, `scripts/`)
- Inner graphs save their own checkpoints through the parent's saver: **library**; **measured**
- Usage at most every 30 seconds: `_USAGE_SAVE_EVERY_S = 30.0`. **code** (re-checked)
- The one-step lead recorded when the server was built: **doc**
  `frontend/docs/server_encountered_challenges.md` section 8

**Starting again (3.5)**

- Start-up order: **code** [app.py](../../../server/app.py)::`lifespan`
- Only "running" games are recovered: `RECOVERABLE_STATUSES = (RUNNING,)`. **code** (re-checked)
  `server/database_models/game.py`, `server/housekeeping/recovery.py`
- `revive`, `reload_history`, `Translator.hydrate`, `_resume_from_checkpoint`: **code**
- An open question raised inside an inner graph is visible in the top-level state: **measured**
  (re-run by me, same result)
- Tests of the recovery logic, all against stand-ins: `tests/server/test_durability.py`, whose
  header says the real Postgres path "is exercised by the manual restart smoke, not here".
  **test** (the 30 tests in the four files named in this appendix: run during the code read and
  again by me, all passed)
- The manual check: **doc** `frontend/docs/build_plan.md`, "restart smoke passed", August 2026

**The work that is done twice (3.6)**

- Cached nodes and their uncached human twins; the cache is an `InMemoryCache` on each inner
  graph; lifetime 6 hours. **code** (re-checked) `Agents/graphs/day.py`,
  `Agents/graphs/night/pack.py`, `Agents/config/langgraph.py`
- The cache key includes the game: **test** `test_key_separates_games` and two others (run,
  passed)
- The table of what is redone: **measured** with a stand-in graph on an in-memory saver and the
  blocking stream (run during the code read and again by me, same results). Not the Postgres
  saver and not the async stream. See the limits below. The scripts are kept in
  [measurements/](measurements/README.md).
- Send-once guards and their rebuild: `Translator._discuss`, `hydrate`. **code**
- Ballots held until collected: **test**
  `test_recovered_cached_votes_wait_for_collection_and_include_every_voter` (run, passed)
- The log and engine disagreeing after a re-run line: **code** reading only; **none** for a test
- Whether a re-run wolf kill that picks a different target is guarded: **none**

**The saver (3.7)**

**Its lock, corrected from U2.** U2's section 3.5 said a save holds the saver's single lock while
it waits for a worker thread. Reading the library again for this note:

| Operation | Holds the lock while waiting for a thread? |
|---|---|
| Saving a step's checkpoint | Yes |
| Reading a checkpoint | Yes |
| Saving one task's result | No. It prepares the data first and takes the lock after. |

So U2's statement holds for checkpoint saves and for reads, and not for the per-task saves. The
main point stands: one lock for all games, taken before a connection, so the pool of 4 works as 1.

**One saver per game is possible, with a catch.** U2 left this open. The library reads the saver
from a run's settings before it falls back to the one attached to the graph, so a game could be
given its own saver while one graph still serves all games. Several savers can share one
connection pool, each with its own lock. The catch: the setting is an internal one, not part of
the library's public interface, and one place in my server reads the graph's saver directly and
would have to change. None of this was tried. There is also a way that avoids the internal
setting: copy the compiled graph for each game with that game's saver, which costs 0.1 ms and
about 4 KiB per game (measured for U2 section 3.7, gap 1.2, on 2026-11-12).

**What can be read back.** The saver is told which of my classes it may rebuild when loading a
checkpoint. A class missing from that list is loaded as plain data with a warning. That happened
twice, and a test now checks the list against every type the engine's state can hold.

- One lock, taken before a connection: `self.lock = asyncio.Lock()`; `_cursor`. **library**
  (re-checked) `checkpoint/postgres/aio.py`
- `aput` and `aget_tuple` hop to a thread inside the lock; `aput_writes` prepares its data before
  taking it. **library** (re-checked)
- A saver read from the run's settings before the graph's own: **library**
  `langgraph/pregel/main.py` (`_defaults`; the key is `CONFIG_KEY_CHECKPOINTER`). Not tried.
- `_turn_payload` reads `self._graph.checkpointer` directly: **code**
- The allow-list of classes: `durable_serde()`. **code** `Agents/memory/checkpointer.py`; **test**
  `tests/engine/test_checkpoint_allowlist.py` (run, passed)

**Gaps (3.8)**

- Nothing deletes checkpoints, events or games: **code** (search for `delete_thread`, re-checked)
- Retention left out on purpose: **doc** `server_design_notes.md` section 8;
  `server_client_transport.md` section 4
- Size of one game's saved state: an estimate only. **doc**; measured: **none**

**Not established**

- That a kill on the real path (Postgres saver, async stream) behaves as the stand-in did. The
  resume logic is the library's shared code, but the real path was not run.
- The log and engine disagreement of 3.6, in a real game.
- Double counting in the lesson store on a re-run.
- A per-game saver, in practice.
- Why the library re-runs the finished tasks of an inner step in flight.

**Where a document and the code disagree**

- `server_encountered_challenges.md` section 8, `interview_prep/langgraph_langfuse_issues.md`
  section 6.4 and my own seed note say the checkpoint is written only when a whole step finishes.
  The library also saves each task's result as it finishes.
- The same section 8 says a repeated one-at-a-time turn's events "would be sent twice". For
  speech, wolf chat, memory and reads, the send-once guards drop them.
- `server_encountered_challenges.md` section 3 and my LangGraph issues note say an inner graph treats a
  fresh input as a new run. The stand-in graph resumed from its own last inner step.
- `build_plan.md` says games on a player's own key are dropped at restart. The code rebuilds them
  and waits for the key.
- `server_design_notes.md` section 8 says recovery covers waiting and running games. The code
  recovers running games only.
- U2 section 3.5: corrected in the saver reference above.

**Revision scope (2026-11-12)**

The concept explanation, comparisons and exercises were revised against the syllabus. Existing
implementation evidence and recorded test results above are retained from the original code
review; this editorial revision did not rerun those tests or the stand-in experiments. Proposed
fixes are hypotheses until their publication and persistence ordering is tested.

**Reading**

- [Microsoft Azure Architecture Center, Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
  "Solution" and the "Event ordering" and "Entity state re-creation" items under "Problems and
  considerations": authority, ordering and snapshots used to shorten replay. The delivery and
  chat scenarios here are worked design examples, not measurements of that platform.

- `frontend/docs/server_client_transport.md` section 4, "Where each truth lives"
- `frontend/docs/server_encountered_challenges.md` sections 3, 4, 5 and 8
- `interview_prep/langgraph_langfuse_issues.md` sections 6 and 7
