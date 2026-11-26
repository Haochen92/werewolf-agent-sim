# U4. Delivery and repeated work: the concepts, and a review of my systems

**Reading time:** about 90 minutes for a first read of the core path (estimate); the summary in Part 6, 5 minutes · **Builds on:** U1, U3 · **Feeds write-up chapter:** 7

**The question these notes answer:** the same message or job arrives twice. How is its effect
made to happen once?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

U3 ended on work that runs twice: resuming from a save repeats the step that was in flight. This
note is about making a repeat harmless, and about two records that have to change together.

## What these notes cover

1. Why a sender often cannot tell whether its work happened, and the choice that forces.
2. What makes a repeated action harmless, and what does not.
3. Two records that must change together when no single save covers both.
4. Why retrying needs an end.
5. A review of where work repeats in my Werewolf server and in my dota2pred pipeline, and what
   each does about it.

**Core and detail.** The core is four things: the unknown outcome, the harmless repeat, the two
records, and the end of retrying. Sections and paragraphs marked **Detail** go further into how
it is built and can wait for a second read.

**Covered in other notes:** when to retry a call and for how long (U1), what a restart re-runs
(U3), a claim on a job that expires (U5), and a browser receiving the same event twice (U6).

---

# Part 1 — Doing something once when it may be asked twice

A task that crosses a network or survives a crash can be attempted more than once. This part is
about making the result the same as if it had been attempted once. It answers four questions:

1. **Did it happen?** (the unknown outcome)
2. **What if it is done again?** (a harmless repeat)
3. **What if two records must both change?** (the dual write)
4. **When does retrying stop?** (the poison message)

The example is a ticket shop. A customer buys a ticket. The shop saves the order in its database,
charges the card through a payment provider, and emails the ticket through an email provider. The
charge and the email are done by a worker that takes jobs from a queue.

## 1.1 Did it happen?

The worker sends "charge order 88, 40 euros" to the payment provider and waits. No answer comes
back before the timeout. Three different things could have happened:

| What happened | Was the card charged? |
|---|---|
| The request never arrived | No |
| The provider received it and failed | No |
| The provider charged the card, and the reply was lost | Yes |

From the worker's side all three look the same: silence. This is the **unknown outcome**. It is
not a bug in either program. It is what any two programs face when one waits on the other and
either side, or the network between them, can fail.

A crash gives the same result without a network. The worker charges the card, then dies before
writing "charged" in the database. The new worker finds an order that is not marked charged, and
cannot tell whether the charge was made.

So the worker has to decide what to do without knowing, and there are only two choices.

| Choice | Called | What can go wrong |
|---|---|---|
| Do not try again | **At-most-once** | The work may never happen: the customer has no ticket |
| Try again | **At-least-once** | The work may happen twice: the customer is charged twice |

There is no third choice that delivers a message exactly once across a failure. What can be had
is the *effect* happening once: retry, and make sure a second attempt changes nothing. That is
the rest of this part.

**At-least-once delivery, plus work that is safe to repeat, gives a result that happens once.**

Delivery is not completion: a message can be delivered many times and never succeed, which is
section 1.4. And "safe to repeat" has conditions of its own, which section 1.2 sets out.

### Check

A worker sends an email through a provider and the call times out. The team decides "we never
retry emails, so nobody gets two". What have they chosen, and what does a customer see when it
goes wrong?

<details>
<summary>Answer</summary>

At-most-once. When the request was lost or the provider failed, no email is ever sent, and
nothing in the system knows. The customer has paid and has no ticket. Whether that is better than
a rare second email depends on the cost of each: for an email, a duplicate is usually the cheaper
failure.
</details>

## 1.2 What if it is done again?

An action is **idempotent** when doing it twice leaves the same result as doing it once. Some
actions are like that by nature, and some are not.

| Action | Done twice |
|---|---|
| Set order 88's status to "paid" | Still "paid". Harmless. |
| Save the ticket for order 88, replacing any earlier copy | One ticket. Harmless. |
| Add 1 to "tickets sold" | Counts 2. Wrong. |
| Charge the card 40 euros | 80 euros taken. Wrong. |
| Send the ticket email | Two emails. Annoying, not costly. |

The first two say what the end state is. The others say what to change, and a change applied
twice lands twice. So the first tool is to write the action as "make it so" where that is
possible: set a value instead of adding to it, and save a record under its own identity so a
second save replaces the first.

A charge cannot be written that way. For those, the sender gives each action a name. An
**idempotency key** is an identifier the sender attaches to a request, the same on every attempt
at the same action. The receiver remembers the keys it has acted on. A second request with a key
it knows is not carried out again; the receiver returns the first result.

```text
attempt 1:  charge 40 euros, key = "charge-order-88"   -> charged, reply lost
attempt 2:  charge 40 euros, key = "charge-order-88"   -> "already done", same receipt
```

Two things have to be right for this to work: the key itself, and the receiver's record of
keys.

**Choosing the key.** The key has to identify exactly one action: the same on every attempt at
that action, and different for every other action. It can miss in two directions.

| The key is made from | Example | What goes wrong |
|---|---|---|
| The attempt (too narrow) | A random id made fresh for each send | Every retry has a new key, so the receiver never recognises a repeat. It protects nothing. |
| The action (right) | "charge-order-88" | A retry matches, and a different order does not |
| Something wider than the action (too broad) | "charge-customer-7" | That customer's second order matches the first and is refused. A real action is swallowed. |

**Looking after the record.** The receiver recognises a repeat only through its record of keys.
There are four ways that record can fail, each with its fix.

| Take care of | What goes wrong otherwise | What to do |
|---|---|---|
| **Saving the key with the effect** | The receiver charges the card and crashes before recording the key. The retry is charged again. | Record the key and do the work as one step that succeeds or fails together (atomicity, U3). One database transaction gives this when the work is in the same database; when the work is outside it, see section 1.3 |
| **How long a key is kept** | The record is cleared after a day, and a retry arrives after two. It looks new and is carried out again. | Keep keys at least as long as the sender can still retry |
| **Where the record is stored** | The record is in memory, and the receiver restarts. Every key is forgotten. | Store it where it survives the failures that cause retries, usually the database |
| **Two attempts at the same moment** | Two copies arrive together. Both check, both find "not done yet", both act. This is a race (U2). | Make the check and the save one step: a unique constraint on the key, inside the transaction that does the work |

**A duplicate is not a race.** The two are easy to confuse, and each fix does nothing for the
other.

| Problem | What it is | Fix |
|---|---|---|
| A race | Two different updates at the same moment; one overwrites the other | Update only if the value is unchanged since it was read, or a lock (U2) |
| A duplicate | The same update arriving twice, at any time | A key, or stating the end result |

"Update only if unchanged" does not stop a duplicate: a second copy that arrives later reads
the new value, and its check passes.

A key only helps where the receiver supports it. Payment providers nearly always do.

**Asking instead of repeating.** The other way to settle an unknown outcome is to ask the
receiver: "does a charge for order 88 exist?" If it does, record it and move on. If it does
not, send it. This needs two things from the receiver: a way to look an action up, and a
reference the sender chose (the order number) to look it up by. It has one weakness. The answer
"not found" can come back while the first request is still on its way, and then both land. So
asking narrows the window and a key closes it. The strongest design uses both: ask first to
avoid needless repeats, and send the key anyway.

Where the receiver offers neither, what is left is weaker. The shop can check its own record
before calling, but the crash that caused the doubt can be the reason that record is missing.
Or it can accept a rare duplicate when one is cheap.

A repeat can be harmless and still not identical. Saving a ticket twice is safe. Asking a pricing
service twice may return a different price the second time. If the first answer was already shown
to someone, the second one replaces it underneath them. **Safe to repeat** means the repeat does
no damage; it does not mean the repeat gives the same answer. Where the answer must not change,
the first result has to be saved and reused.

### Check

A worker handles "order 88 paid" by running `UPDATE stats SET tickets_sold = tickets_sold + 1`.
The queue delivers the message twice. What goes wrong, and what are two ways to fix it?

<details>
<summary>Answer</summary>

The count goes up by 2 for one order. One fix is to make the action state its end result: count
the paid orders instead of keeping a running total, or record "order 88 counted" and add only if
that record is new. The other is a key: store the message's id in the same transaction as the
update, and skip a message whose id is already stored.
</details>

## 1.3 What if two records must both change?

Sometimes one operation needs to update two systems. For example, placing an order requires:

1. Saving the order in the **database**.
2. Publishing a job to the **queue** so a worker can charge it and email the ticket.

Each system can guarantee its own write, but not both together. If the application crashes
between the writes, one succeeds while the other never happens. This is the **dual-write
problem**.

The central rule is: **prefer a failure that causes work to be repeated over one that causes
work to disappear.** Repeated work can be made harmless through idempotency (section 1.2),
provided something remembers to retry it.

### A. Where the failures happen

Consider order 88. The database stores its details and payment status. The queue stores a job
telling a worker to charge it and email the ticket. The job carries only the order number, so the worker reads the
amount and the card from the database.

There are two places where the application must update separate systems.

**1. Creating the job: database + queue**

The shop saves the order, then publishes its job.

```text
1. Save order 88 in database.       ✓
   -- crash --
2. Publish "charge+email 88".       ✗
```

The database has the order, but the queue has no job. **Nothing will process the order**,
because nothing remembers that the job still needs to be published.

Reversing the writes doesn't solve it. Publishing first could leave a job for an order that
doesn't exist: the worker looks up order 88 and finds no row.

**2. Completing the job: database + queue acknowledgement**

After processing the job, the worker must save the result and acknowledge the queue message. An
**acknowledgement** (ACK) tells the queue that the job is finished and no longer needs delivery.

The write order determines what happens after a crash:

| Write order | Crash leaves | Consequence |
|---|---|---|
| ACK → Save result | Job gone, result missing | **Lost work** |
| Save result → ACK | Result saved, job still pending | **Repeated work** |

The second order is safer. If the worker crashes before acknowledging, the queue delivers the
job again.

This is the **acknowledge-last rule**: finish and save the work before marking its message as
done.

The two problems differ in one way:

- **Creating work:** the job may never reach the queue. There is nothing to retry.
- **Completing work:** the job is already in the queue. Delaying the acknowledgement preserves
  its ability to be retried.

### B. How to solve them

**1. Acknowledge last: make completion retryable**

The worker saves the result before acknowledging the job.

```text
1. Worker receives "charge+email 88".
2. Charge card using key "charge-order-88".
3. Save order 88 as "paid".
   -- crash --
4. Acknowledge job.                  ✗

Queue redelivers the unacknowledged job.

5. Retry charge using the same key.
   → Provider returns the original charge.
6. Save "paid" again.
7. Acknowledge successfully.
```

The work is attempted twice, but produces the same final result. (The email half of the job
is left out here; section 1.5 follows it.)

This requires two things:

- **A retry mechanism:** something delivers the work again. Here it is the queue. A program
  that polls a source has the same thing: the next poll offers the item again, as long as it is
  not yet marked done.
- **Idempotency:** repeating the operations doesn't duplicate their effects (section 1.2).

Acknowledge-last is simple, but **cannot fix a job that was never published**.

**2. Transactional outbox: make job creation reliable**

When two facts fit in one database, one transaction covers both and there is no gap. A queue
cannot join the database's transaction, so the shop cannot save an order and publish a message
as one step. Instead, it stores both the order and the *intention to publish* in the same
database.

```text
SHOP (one DB transaction)
  ├─ Save order 88
  └─ Save outbox row: "charge+email 88"
                ↓
RELAY (runs repeatedly)
  ├─ Read unsent outbox rows
  ├─ Publish jobs to queue
  └─ Mark rows as sent
                ↓
QUEUE → WORKER
```

Now the order and its outbox row either both exist or neither exists. An order cannot be
committed without a record of its pending job.

The relay still has two writes: publish the job and mark the row sent. It therefore **marks the
row sent last**.

If it crashes after publishing, the row remains unsent and the relay publishes it again. The
result is a duplicate job rather than a permanently missing one.

The worker must therefore be idempotent.

Each step in this chain writes down what is still owed before the next step starts, and
removes that mark last. The outbox row is owed until the relay marks it sent; the job is owed
until the worker acknowledges it. A crash anywhere leaves a mark that something will pick up.

*Cost:* an outbox table, a relay process, and a small publication delay.

**3. Reconciliation: detect and repair missed work**

An alternative or additional safeguard is to periodically compare the expected state with the
actual state.

```text
12:00  Order 88 saved as "new".
       Crash before publishing job.

12:10  Reconciliation scans orders still "new".
       Finds order 88.
       Publishes a replacement job.
```

This repairs missing jobs, but introduces a delay. It needs a rule for which record is right:
here the database is, so the queue is the one corrected. It may also publish a duplicate if the
original job is merely waiting or taking longer than expected.

Reconciliation therefore still requires idempotency.

*Cost:* a scheduled check, repair logic, and a period where the systems can disagree.

### C. Putting it together

The mechanisms solve different parts of the problem:

| Mechanism | What it protects against |
|---|---|
| **Acknowledge last** | Losing work already delivered to a worker |
| **Transactional outbox** | Losing work before it reaches the queue |
| **Reconciliation** | Inconsistencies that need detecting and repairing |
| **Idempotency (1.2)** | Duplicate effects when any work is retried |

They are complementary, not mutually exclusive.

**The goal is not to prevent every duplicate. It is to ensure work is not silently lost, and
that retries are safe.**

### Check

A worker polls a ticket site for new events. For each event it:

1. Adds its ID to a `seen` set.
2. Saves the event.
3. Publishes it to the next stage.

It crashes after step 1.

What happens on the next poll? Why is this the same failure as acknowledging a queue message
too early?

<details>
<summary>Answer</summary>

The event is skipped because its ID is already marked `seen`, even though processing never
completed. The worker marked the work done before completing it. It should record completion
only after the necessary work succeeds, with retries made safe through idempotency.
</details>

## 1.4 When does retrying stop?

At-least-once means a job that fails is tried again. Most failures pass: the provider was down
for a minute. Some never will. An order's email address is malformed, and the email provider
rejects it every time. A job that can never succeed is a **poison message**.

Retried forever, it costs twice. It uses the worker's time and the provider's rate limit on work
that cannot finish, and a growing pile of such jobs crowds out the ones that could.

So retrying needs an end, in three parts:

- **A limit.** A count of attempts, or an age, after which the job stops being retried.
- **A place to put it.** A **dead-letter queue** holds jobs that reached the limit, so they are
  out of the way and still visible. It is an end point for automatic retrying: nothing sends a
  job back from it by itself. A person can send one back after fixing its cause (a corrected
  address, a bug fixed in the worker). A sweep that feeds jobs back automatically turns the
  dead-letter queue into one more retry loop, and the limit no longer ends anything.
- **A way to tell the two failures apart.** "The provider is down" deserves another try.
  "This job is invalid" does not, and should be set aside at once.

## 1.5 One order, one crash, start to finish

The shop saves the order and the job in one transaction, using an outbox. The worker charges
with an idempotency key and acknowledges last.

```text
 1  Save order 88 and outbox job "charge+email 88" in one transaction.
 2  Relay publishes the job to the queue, marks the outbox row sent.
 3  Worker takes the job. Marks order 88 "charging".
 4  Worker sends: charge 40 euros, key "charge-order-88".
 5  Provider charges the card. The reply is lost. The worker dies.

 6  The job was never acknowledged, so the queue delivers it again.
 7  New worker takes it. Order 88 says "charging": the uncertain case, visible in the data.
 8  It sends the same charge with the same key.
 9  Provider knows the key: no second charge, returns the first receipt.
10  Worker marks order 88 "paid", sends the email, records "emailed", acknowledges.
```

Each step that kept this correct is one idea from above. Step 1 removes the lost job (1.3).
Step 6 is at-least-once delivery (1.1). Steps 8 and 9 are the idempotency key (1.2). Step 10
acknowledges last (1.3).

One repeat is still possible. If the worker dies after sending the email and before recording
"emailed", the next worker sends it again. The shop accepts that, because a second email is
cheap, or uses a key if the email provider supports one. Naming which repeats are accepted is
part of the design.

The fourth idea needs a job that cannot succeed. Order 91 has a malformed email address.

```text
 1  Worker takes "email 91". The provider rejects the address: a permanent error.
 2  A permanent error is not retried. The job goes to the dead-letter queue and is acknowledged.
 3  Order 91 is marked "email failed", where support staff can see it.
```

Had the provider timed out instead, the job would be retried up to its limit and only then set
aside. Telling the two apart is what keeps a bad address from being retried forever (1.4).

---

# Part 2 — The choices

This part restates Part 1 as tables, with my systems placed in each. On a first read it can be
skimmed for the last column. "Werewolf" is the game server; "dota2pred" is my queued prediction
pipeline.

**Which way to fail when the outcome is unknown?**

| Design | What it buys | What it costs | Fits when | In my systems |
|---|---|---|---|---|
| Do not try again (at-most-once) | No duplicates | Work can be lost with nobody knowing | A repeat is worse than a loss | Werewolf: a human's answer lost in a restart is not replayed; the seat is asked again |
| Try again (at-least-once) | Work is not lost | Work can happen twice | A repeat can be made harmless | Werewolf: the step in flight is re-run after a pause or a restart. dota2pred: every stage that reads from a stream |

**How is a repeat made harmless?**

| Design | What it buys | What it costs | Fits when | In my systems |
|---|---|---|---|---|
| State the end result (set, replace, upsert) | Nothing extra to store | Not every action can be written this way | The action is a save | Werewolf: event rows, usage counts, the prompt capture, a game's lessons. dota2pred: features, predictions, odds |
| Dedupe by a key at the receiver. The record of the key can also hold the first result, so a repeat returns the same answer | Works for any action; with the result kept, the repeat is identical | The key must name exactly one action and be saved with the effect, in storage that survives the failure and for long enough | The action has an effect outside the store, or its answer must not change | Werewolf: the cache on AI turns (key and first result, in memory, six hours); the send-once guards (key only, rebuilt from the log) |
| Accept the repeat | Nothing to build | The repeat's cost | A repeat is cheap and rare | Werewolf: model calls after a restart. dota2pred: a prediction made twice |

**How are two records kept together?**

| Design | What it buys | What it costs | Fits when | In my systems |
|---|---|---|---|---|
| One store, one transaction | The two facts change as one | Both facts must live in one database | They can | Werewolf: event rows with the game's "updated" time; a game's lessons with its "extracted" mark |
| Order the writes so a crash repeats, not loses | No lost work | The work must be safe to repeat | Two stores, and a queue that redelivers | dota2pred: Postgres first, then the Redis step that acknowledges |
| Outbox and relay | No lost message | A table and a relay to run | Two stores, and a loss is unacceptable | Not used |
| Reconcile afterwards | Repairs what slipped through | A job to write, and a rule for who is right | A gap is accepted | Not used |

**What gives retrying an end?** These three are parts of one design and are used together.
They are not alternatives.

| Part | What it does | What it costs | In my systems |
|---|---|---|---|
| A limit on attempts | Gives a known worst case | A passing fault can use the attempts up | Werewolf: two attempts on the main model, then one on the rescue model, then a safe default (U1). dota2pred: a limit of 3 |
| A dead-letter queue as an end point | Keeps failed jobs out of the way and visible | Someone has to look at it | dota2pred: used, with a retry sweep that feeds jobs back |
| Telling a permanent error from a passing one | Stops wasted calls at once | The error has to be recognisable | dota2pred: a match the data provider answers "not found" for is discarded for good |

In the first three tables no row is the better design. Each is right for one cost of failure: what a loss costs, what a
repeat costs, and how much a changed answer matters.

---

# Part 3 — My two systems

Werewolf has no queue: the engine runs inside the server process. So it meets repeated work in
two forms only, a step that is re-run and a request that is sent twice. dota2pred is a pipeline
of queued stages, and it meets the rest.

## 3.1 Where work repeats: the map

Work repeats in my server in three ways. Each has its own section; this table is the index.

**A step that runs again** (section 3.2)

| What repeats | Why | What makes it harmless | What is left |
|---|---|---|---|
| The AI turns of a step | A human answers a paused step | The turn cache and the "cached" label | Nothing, within one process and six hours |
| The step in flight | The server restarts | For viewers, the send-once guards. For the model calls, nothing | Calls are billed again and can answer differently |

**A request that arrives twice** (section 3.3)

| What repeats | Why | What makes it harmless | What is left |
|---|---|---|---|
| A human's answer | The browser retries a lost send | The seat is crossed off first | An answer carries no question id (gap 1) |
| "Start the game" | A double click | The room is replaced by the game first | Nothing |
| A player's own key, supplied again | A double click | The game is claimed first | Nothing |
| "Create a game" | A double click, or a second press after a lost reply | Only the browser's disabled button | Two requests make two games (gap 2) |

**A write that is made again** (section 3.5)

| What repeats | Why | What makes it harmless | What is left |
|---|---|---|---|
| An event write | A failed save is sent again with the next one | The row's key is the game and the event number | Nothing |
| A game's completion | A restart between the engine's last save and the row update | Recovery makes the same write, late | The finish time, and the extraction input |
| Lesson extraction for a game | The offline run is started again | It skips games marked extracted, and saves one row per game | Nothing |
| The lesson counters | A turn that is not cached runs again | Nothing: read, add one, write | A counter can be one too high (U3 gap 5) |
| An event reaching a browser | A reconnect or a page load | The browser drops an event number it has (U6) | Nothing |

## 3.2 A step that runs again

**The situation.** A step that paused is not continued from its middle. When a human answers,
or the game resumes after a restart, the engine runs the unfinished step again from its start.
In my engine the day and the wolves' night each run as a smaller graph called from inside one
step of the main graph, so the whole of that call runs again, and every seat's result in it is
reported in the stream again (U5 has the cause).

**The failure point.** A vote with one human seat and nine AI seats:

```text
1  The nine AI seats vote. Each one calls the model.
2  The human has not voted, so the step cannot finish. The game pauses.
3  The human votes. The engine runs the vote step again from its start.
4  With nothing in place: nine model calls are paid for a second time,
   and nine results are reported again, to be sent to viewers again.
```

The event number cannot catch the second report. It comes from a counter in the translator:
each event made gets the next number. A second report of the same speech would get a new
number, and the database and the browser would both take it as a new event. A counter is a key
made from the attempt, the "too narrow" row of section 1.2. So the repeat has to be stopped
before an event is made.

**What the code does.** Three layers, each covering what the one before cannot.

| Layer | What it stops | How | After a restart |
|---|---|---|---|
| The turn cache | A second model call | The engine finds the seat's recorded answer under the turn's key and reuses it | Empty: it is in the process's memory |
| The cached label | A second event for a reused result | The engine reports a reused result labelled "cached". My server checks each report for the label first and makes no event from one that has it | The label also comes on any result the engine had saved for that step |
| The send-once guards | A second event for a result that was produced again | The translator remembers each thing it has sent by its identity in the game, and makes no event for one it remembers | Rebuilt from the saved events when the game is loaded |

When a human answers, the first two work as a pair: the cache spares the model call, and the
label stops the reused result being sent again. After a restart the cache is empty, the seats
run again, their results carry no label, and the guards are what is left.

**The turn cache's key.** Section 1.2 asked that a key identify exactly one action. The key is
built from the values of the turn's input, written out in a fixed order, with the game's id
included.

- *Why the game's id.* The engine's graph is built once and every game runs through it, so one
  cache serves every game. A day-1 opening turn has almost no input of its own: a seat, a role,
  a line-up, and nothing said yet. Two games dealt the same way would produce the same key, and
  the second would be handed the first game's answer. A test deals two games alike and checks
  that their keys differ. This is the "too broad" row of section 1.2.
- *Why values and not the objects.* An object read back from a checkpoint is not byte-for-byte
  the object that was saved, and a key made from the object never matched.

Two limits come with the cache. A human turn is never cached: a cached human answer would be
played back in place of asking the person, and the library also fails when a cached step pauses
for input. And nothing outside the input is in the key, so a game that switches to its rescue
model in the middle would still be given an answer recorded from the main model. Entries last
six hours.

**The guards' keys.** Each is made from facts about the game, so a result produced again has
the same key as the first time.

| Event | Key |
|---|---|
| A speech or a pass | The day and the line's position in the day's conversation |
| A wolf's night message | The day, the round and the wolf |
| A seat's reads, and its memory lookup | The seat, the day, the round and the phase |
| A strategy note | The seat and the note's text: an unchanged note is not sent again |

The position is the one to remember. Each line in the day's conversation holds its own
position, worked out from how many lines the day already has, and the engine saves it with the
game's state. The speech event carries a copy. After a restart the state is restored, the count
is the same, and the seat's line gets the same position again, so the guard matches it. The
guards need no game id, because each game has its own translator.

Ballots need no guard. They are held back until the whole vote is in, so a ballot cast again in
a re-run replaces the first, and nothing was shown before.

One guard keyed on an event's content, or on the day and the player, would be simpler. It would
also drop real events, because two event types (`turn_started` and `input_request`) repeat
within a day with identical fields. So each guard is keyed for its own event type.

**What is left.**

- After a restart the AI seats of the step in flight are billed again (U3 gap 3).
- A seat that runs again may say something different, and the guard keeps the line viewers were
  already shown. The engine then holds the new line and the viewers' record the old one (U3
  gap 2).

*Code:* [`turn_cache_key`](../../../Agents/config/langgraph.py) builds the key;
[`is_cached` and `Translator.hydrate`](../../../server/game/translate.py) are the label check
and the rebuilding of the guards. A test replays every state-update chunk of a recorded game
with the label on it and checks that nothing is sent or numbered.

## 3.3 A request that arrives twice

**The situation.** A browser can send the same request twice: a double click, or a retry after
a reply the network lost. For a turn, the browser itself retries after 2, 5 and 10 seconds. No
request to my server carries an idempotency key.

**The failure point.** A request checks something, then acts on it. If the server waits on
anything between the two, a second copy of the request can pass the same check. Supplying a key
for a game that lost its own in a restart shows it:

```text
Check the key first, then claim the game:
  Request 1:  the game is waiting for a key -> OK. Checks the key with the provider...  (waits)
  Request 2:  the game is waiting for a key -> OK. Checks the key with the provider...  (waits)
  Both keys are accepted. The game is resumed twice.

Claim the game first, then check the key (what the code does):
  Request 1:  the game is waiting for a key -> OK. Clears the flag. Checks the key...
  Request 2:  the flag is cleared -> refused.
```

**What the code does.** Three of the four requests are safe without a key, because the server
changes its own state before anything waits, and the second copy finds nothing left to do.

| Request | What the server does first | The second copy | Technique |
|---|---|---|---|
| A human's answer | Looks the seat up among the seats that owe an answer and crosses it off, then hands the answer to the game | Gets "nothing owed". The browser treats that as "already answered" | No wait |
| "Start the game" | The registry keeps one entry per game id, a waiting room or a running game. Starting replaces the room with the game under the same id | Looks for a waiting room, finds a running game, and is refused | No wait |
| A player's own key | Clears the game's "waiting for a key" flag before checking the key with the provider. Sets it again if the provider rejects the key | Finds the flag cleared, and is refused | A reservation first |
| "Create a game" | Nothing. The browser disables the button while the request is out | Makes a second game | None |

This is the check-then-act race of
[U2 section 1.6](02_concurrency_models.md#16-what-if-two-of-them-change-the-same-thing), and
the two techniques are from
[U2 section 3.6](02_concurrency_models.md#36-when-two-requests-change-the-same-thing).

- **No wait between the check and the act.** The server switches to another request only when
  the current one waits. With no wait in the gap, nothing can run in between.
- **A reservation first.** When a slow step has to sit in the gap, the claim is made before it
  and given back if the step fails. The second request is turned away at once; a lock would
  make it wait instead.

Both are kept in the one process's memory and rely on its single event loop. Neither would hold
across two server processes.

**What is left.**

- *A human's answer is matched to the seat, not to the question* (gap 1). A retry that arrives
  after the seat has been asked something new would be checked against the new question.
- *"Create a game" is protected in the browser only* (gap 2). A reply that is lost, followed by
  a second press, makes two games. The other three could be checked against state the server
  already had. Here it has nothing to compare: each request rightly asks for a new game, so the
  browser would have to send a key.

*Code:* [`GameSession.submit_turn`](../../../server/game/game_session.py);
[`LiveGameRegistry.start` and `resume_with_key`](../../../server/game/live_game_registry.py).

## 3.4 The unknown outcome, on a model call

A model call has a time limit of 30 seconds. When it passes, the provider's client sends the
request once more by itself; after that the turn goes to the rescue model, and after that to a
safe default (U1).

A call that the provider finished after the client gave up is the unknown outcome of section
1.1. My code does nothing about it. No key is sent with a model call, and the usage meter
records a timed-out call as failed with zero tokens. If the provider bills such a call, the
game's shown cost is lower than the real one. I have not checked whether providers bill it.

This is accepted. A second model call has no effect outside the game except its price.

## 3.5 Two records, and a write made again

**The situation.** One game is recorded in several places: the engine's checkpoint, the events
table, the game's row, and the lesson store. Inside Postgres, facts that must change together
share a transaction: a batch of event rows with the game's "updated" time, and a game's
extracted lessons with the mark that says they were extracted. Across the records there is no
shared transaction, so each pair is a dual write (section 1.3).

**The failure points.** Two of them, with the same shape as the shop's.

```text
Saving events
1  The translator makes events 210 to 212. They are sent to the browsers.
2  The save to the events table fails.
   Viewers have seen three events the database does not hold.

Finishing a game
1  The engine plays the last step and saves its final checkpoint.
   -- the server restarts --
2  The game's row is marked "completed".                    never happens
   The checkpoint says the game is over. The row says "running".
```

**What the code does.** The server has no outbox. It uses the third way of section 1.3, repair
afterwards, with the checkpoint as the authority, and it makes its saves safe to repeat.

| The two records | A failure between them leaves | What settles it | What is left |
|---|---|---|---|
| The events in memory, and the events table | Events sent to browsers and not saved | The save is made again with the next one | A viewer can see an event that is then lost, if the server stops first (U3 gap 7) |
| The checkpoint, and the events table | After a restart, the step in flight runs again | The send-once guards (section 3.2) | The two can disagree on one line (U3 gap 2) |
| The checkpoint, and the game's row | A finished game whose row says "running" | Recovery completes the row | The finish time, and the extraction input |
| The checkpoint, and the lesson counters | A turn that runs again adds to its counter again | Nothing | A counter can be one too high (U3 gap 5) |

*Saving events.* The game's events are one list in memory, with a bookmark for "saved up to
here". Each save writes everything after the bookmark, and the bookmark moves only when the
database confirms the write. A failed save leaves it where it was, so the next save sends those
events again with the new ones, and one more attempt is made when the game ends. If the first
save did reach the database, the rows are sent twice. That is harmless: a row's key is the game
and the event number, and a row that exists is left alone.

*Finishing a game.* At start-up, recovery loads every row that says "running" and asks the
checkpoint what step comes next. For a finished game the answer is none, so recovery completes
the row instead of resuming. Completion reads the winner, the day count and the event count out
of the event log and sets them in one update, so the late write sets the same values the first
would have. This is reconciliation in a small form: two records disagree, and one is corrected
from the other. Two things differ in a row completed this way. The finish time is the
recovery's. And the extraction input, which was held in memory until completion, is gone
(improvements, row 24).

*Lesson extraction.* When the offline run is started again, it skips games already marked
extracted and saves one row per game, replacing any earlier one.

*Code:* [`GameSession._persist_tail`](../../../server/game/game_session.py);
[`complete_game`](../../../server/storage/game_repository.py);
[`_resume_from_checkpoint`](../../../server/game/live_game_registry.py).

## 3.6 dota2pred: a queued pipeline

dota2pred predicts match results. Its live pipeline is a chain of stages joined by Redis
streams: a new match is found, features are built, a prediction is made, odds are captured, and
the match is completed when it ends. Every stage writes to Postgres and to Redis, which is a
dual write at every stage.

The stages that read from a stream do it the same way: commit to Postgres first, then one Redis
transaction that acknowledges the input. For feature engineering and prediction that same
transaction also records the status and publishes to the next stream. That is acknowledge last. A crash between the two leaves the input unacknowledged, so it is delivered
again.

| Stage | A crash between the two writes | On a repeat |
|---|---|---|
| Feature engineering | Delivered again, features rebuilt | Features are saved by key, replacing the earlier ones |
| Prediction | Delivered again, model called again | The earlier prediction and its date are overwritten |
| Odds | Delivered again, odds captured again | The earlier capture is overwritten with later market prices |
| Completion | Delivered again; the outcome may be saved without the history | The outcome is kept: a second save is ignored. The history update: not verified |
| New match | **The match is lost** | Nothing is delivered again |

No stage that reads from a stream loses work. Whether a repeat is acceptable is a separate
question. Prediction and odds are the case from the end of section 1.2: the second run replaces
the first with a later answer. That is fine if only the latest value is ever used, and not if
the first was already shown or acted on. I have not checked which holds, so the table says what
happens and not that it is safe.

**The new-match stage breaks the rule.** It starts from a poll, not from a stream, so there is
no input to deliver again. It updates the "seen" set first, then saves to Postgres, then
publishes. A crash, or a failed save, after the set update means the next poll treats the match
as seen, and it never gets a prediction. This is the check at the end of section 1.3.

Two more faults sit beside it. A failed publish in that stage returns "false", the caller ignores
it and counts a success. And the prediction save catches its own database error without raising
it, so a publish may follow a failed save; I have not verified that last step.

**Retrying without an end.** The completion stream once held 69,227 entries while about 8
matches were live, with some entries delivered 61 times. The dead-letter sweep was the cause:
it reset each job's retry count to zero when it fed the job back, so the limit of 3 never
applied, and jobs that could never succeed were re-sent every two minutes. Each one spent a
call to the data provider, which reached about 7,200 calls a day against an allowance of about
2,000. A match whose data will never exist is now discarded for good when the provider answers
"not found".

That is all three parts of section 1.4: a limit that did not count, a dead-letter queue used as
a loop, and no way to tell a permanent failure from a passing one.

## 3.7 Gaps

The Werewolf gaps are also rows 20 to 23 of [improvements.md](improvements.md). Each is read in
the code and not reproduced unless it says otherwise.

**1. A human's answer carries no question id.** The server matches an answer to the seat it
came from, not to the question it answers. So an answer that arrives late can be taken as the
answer to a different question.

```text
1  Seat 4 is asked to speak. The player types "I think it's seat 7" and the browser sends it.
2  The server receives it, crosses seat 4 off, and replies "accepted".
3  That reply is lost on the way back. The browser cannot tell whether its message arrived,
   so it will send it again (after 2, 5 and 10 seconds).
4  Before the retry lands, seat 4 is asked to speak again.
5  The retry arrives. It is from seat 4, seat 4 owes an answer, and it is a legal message:
   it is accepted as the answer to the new question.
```

*The fix.* The browser sends back which question it is answering, and the server refuses an
answer that names a question other than the seat's open one.

*What names a question.* The number of the "your turn" event that asked it. Every event in a
game has its own number, and the browser already receives it, so nothing new has to be made.
The day, phase and round do not work as the name: the round is a label (opening, proactive,
discussion, closing), and a seat can be asked to speak several times in one discussion round.

A question keeps one event number across a normal restart. The one exception is in
[U5 section 3.5](05_durable_execution_and_human_in_the_loop.md#35-restart-recovery-the-actual-sequence).

**2. "Create a game" has no key.** Two requests make two games, and both count against the
house's daily limit, which is a count of game rows.

**3. A failed save of a new game's row does not stop the game.** The save reports failure and
the game starts anyway; its later writes would then fail.

**4. A guard that nothing sets.** The lesson write-back skips a game whose lessons are marked
as already folded into the store, so they are not counted twice. No code sets that mark.

**dota2pred.** The three faults in 3.6 are open. I am fixing them by hand.

**dota2pred: nobody reads the dead-letter queue.** Failed jobs are kept, one Redis hash per
stream, each with its payload and failure time, and an interactive command-line tool can list
them, send one back or delete one. I have never used it to read them: it shows one queue at a
time and has to be run by hand. Nothing counts the entries and nothing alerts on them, so the
only reader has been the retry sweep. A count per queue, logged or exported on a schedule,
would make a growing queue visible without opening the tool (U8).

### Check

In the Werewolf server a browser sends a vote, the network drops the reply, and the browser
sends it again five seconds later. What does the server do with each, and what would change if
the server ran as two processes?

<details>
<summary>Answer</summary>

The first is validated, the seat is crossed off the list of open questions, and the answer is
handed to the game. The second finds nothing owed for that seat and is refused, and the browser
reads that refusal as "already answered". With two processes, each would hold its own list of
open questions, so the check would have to move to something they share, such as a row in the
database written with a condition, and the answer would need the question's id.
</details>

---

# Part 4 — What would change at a larger scale?

- **Two server processes.** "Change my own state first" stops working as a guard, because the
  state is no longer in one place. Each guard in section 3.3 that relies on it would need a key
  stored in the database.
- **A durable turn cache.** With many games, a restart re-bills a step in every one of them. The
  cache would move to storage that survives a restart (U3).
- **A queue between the server and the engine.** If games ran on separate workers, everything in
  Part 1 would apply to Werewolf as it does to dota2pred: acknowledgement, redelivery, and a
  claim on a game that expires (U5).
- **Money.** If a game took a payment, "create a game" could not rely on a disabled button. It
  would need an idempotency key from the browser.

---

# Part 5 — Worked problems

Each is answered from memory first; my answers are in Appendix A.

## Problem A: The same concepts in another system

A payment provider tells a shop about each payment by calling the shop's webhook. Under load it
delivers the same notice twice. Make the handler safe, and say what its idempotency key must
and must not include.

## Problem B: My systems, without Part 3 open

1. A human answers a vote in Werewolf and the step is re-run. Why is no AI seat billed twice?
2. Why does the same re-run bill them after a restart?
3. Which dota2pred stage can lose a match, and what is the one-sentence reason?

## Problem C: Three claims, and what supports each

Three statements about a restart of the Werewolf server:

1. Work that was already saved sends nothing when it comes back.
2. The events table can be one step ahead of the checkpoint.
3. A restart is safe.

For each: what supports it, and how should it be worded on a portfolio page?

## Problem D: The sharp question

What does at-least-once delivery oblige the receiver to do?

---

# Part 6 — Summary

Four things to keep, each with my systems' answer.

**1. After a failure, the sender often cannot tell whether the work happened.** A lost request
and a lost reply look the same. The only choices are not to try again, and risk the work never
happening, or to try again, and risk it happening twice. Most systems try again.
*My systems:* both retry. Werewolf re-runs the step in flight; dota2pred redelivers a message
that was not acknowledged.

**2. A repeat is made harmless by what the action is, or by a key.** An action that states its
end result can be done twice. One that cannot needs a key that names the intent, saved together
with the effect. Harmless does not mean identical: where the answer must not change, the first
result has to be saved and reused.
*My systems:* Werewolf saves by key where it can and caches AI turns by their input and game
id, in memory. dota2pred saves by key, and a repeated prediction overwrites the first.

**3. Two records in two stores cannot change as one.** The choices are to put both facts in one
store, to order the writes so a crash causes a repeat and not a loss, or to accept the gap and
repair it. Marking work done before it is done turns a crash into a loss.
*My systems:* Werewolf uses one transaction where both facts are in Postgres, and accepts the
gap between events and checkpoints. dota2pred acknowledges last in four stages, so they do not
lose work, and marks "seen" first in the fifth, which can lose a match.

**4. Retrying needs an end.** A job that can never succeed must stop being retried, be set
aside where it can be seen, and be told apart from one that failed for a passing reason.
*My systems:* a Werewolf turn has a fixed number of attempts and then a safe default.
dota2pred's dead-letter sweep once retried without limit; a match that will never have data is
now discarded.

### My systems in one paragraph

The Werewolf server has no queue, so its repeats are a re-run step and a request sent twice. A
re-run step returns its AI turns from a cache keyed by the turn's input and the game's id, which
covers a human's pause and not a restart. What viewers see is protected by guards and by an
events table keyed on the event number. Requests sent twice are refused because the server
changes its own state first, which holds for one process. There are two exceptions: creating a
game, and an answer that arrives after the seat's next question has opened. My dota2pred
pipeline is the queued case. Four stages do not lose work, because an unacknowledged message is
delivered again and the saves replace by key. A repeated prediction or odds capture overwrites
the earlier one, and the completion stage's history update is not verified as safe to repeat.
The new-match stage can lose a match, because it marks the match seen before handing it on.

U5 takes up the next step: a workflow that waits for a person, across a pause and a restart.

---

# Appendix A — Answers to the problems

## Problem A: The webhook

The handler records the provider's event id and applies the effect (mark the order paid) in one
database transaction, with a unique constraint on the id. A second delivery finds the id and
returns success without doing anything. The constraint also covers two deliveries arriving
together: one insert wins and the other is refused. The ids are kept at least as long as the
provider keeps retrying.

The key must include what identifies one logical event: the provider's event id. It must not
include anything that changes between deliveries, such as a delivery time or an attempt number,
or every delivery looks new. It must not be broader than the event either. The order id alone
would treat a payment and a later refund of the same order as one event and drop the second.

If the handler also does something outside its database, such as sending an email, that action
has its own unknown outcome. Recording "sent" afterwards does not close it, because the crash
can land between sending and recording. It needs the email provider's own key, a way to ask the
provider what was sent, or an accepted rare duplicate.

## Problem B: My systems

1. The AI turns are cached by their input and the game's id. The re-run finds each one in the
   cache and returns the recorded answer without calling the model.
2. The cache is in the process's memory, and a restart empties it.
3. The new-match stage. It marks the match as seen before it saves and publishes it, and it has
   no input message to be delivered again, so a crash in between leaves a match the next poll
   skips.

## Problem C: Three claims

1. **Supported by a named test.** The test replays every state-update chunk of a recorded game
   marked as cached and checks that nothing is sent or numbered. I did not run it for this note.
   Wording: "a test checks that work already saved produces no events when it is streamed again."
2. **Supported by reading the code, with no test.** Events are written and waited for; the
   checkpoint is saved in the background (U3 section 3.4). Wording: "by design, the event log
   can be one step ahead of the engine's checkpoint", with no word such as "tested".
3. **Not established.** The first two facts do not add up to it. The recovery logic is tested
   against stand-ins, a real kill and restart was checked once by hand, and U3 lists what a
   restart does not promise. Wording: "a running game continues after a restart; the step in
   flight is repeated, and its wording can differ from what a viewer briefly saw."

## Problem D: The sharp question

To make its work safe to repeat, since the same message can arrive more than once. In practice:
do the work, record the result, and acknowledge last; write the work so a second run changes
nothing, by stating the end result or by remembering a key saved with the effect; and stop
retrying a message that can never succeed.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named; not
run unless stated), **incident** (a dated record), **doc** (a written record, not re-read in the
code), **inferred** (reasoned from code that was read). Read against the code on 2026-11-13.
Werewolf paths are from the repository root; dota2pred paths are in its own repository.*

**The turn cache (3.2)**

- Key built from the payload's values as ordered JSON, with the game id required:
  **code** [`Agents/config/langgraph.py`](../../../Agents/config/langgraph.py)::`turn_cache_key`; entries last
  `TURN_CACHE_TTL_SECONDS = 6 * 3600`
- Cached nodes `round_turn`, `vote`, `CARRIER_KILL`, `PACK_SKILL`; uncached human twins; one
  `InMemoryCache` per compiled graph, at module level: **code** [`Agents/graphs/day.py`](../../../Agents/graphs/day.py),
  [`Agents/graphs/night/pack.py`](../../../Agents/graphs/night/pack.py)
- Two games dealt alike never share a key: **test**
  `test_two_games_never_share_a_day_one_opening_key`
- The rescue model is not in the key: **doc** `interview_prep/langgraph_langfuse_issues.md` 7.4

**Where work repeats (3.1, 3.3, 3.5)**

- Events: primary key (game_id, seq); `on_conflict_do_nothing`; same transaction as
  `updated_at`: **code** [`server/storage/game_repository.py`](../../../server/storage/game_repository.py)::`record_events`
- A human's answer: looked up by seat, crossed off, then the future is set, with nothing waited
  on in between: **code** [`server/game/game_session.py`](../../../server/game/game_session.py)::`submit_turn`; the route answers 409
- The browser's retry (2, 5, 10 s; 15 s per try; never after a server answer): **code**
  [`frontend/src/stage/containers/LiveTheatre.tsx`](../../../frontend/src/stage/containers/LiveTheatre.tsx)::`postTurn`
- A second start is refused: **code** [`server/game/live_game_registry.py`](../../../server/game/live_game_registry.py); two starts passing
  the daily-limit check together: **inferred**
- A second key is refused: **code** `live_game_registry.py`::`resume_with_key`
- Creating a game has no key: **code** [`server/routes/games.py`](../../../server/routes/games.py); the daily limit is a count of
  rows: **code** [`server/storage/game_repository.py`](../../../server/storage/game_repository.py), [`server/house.py`](../../../server/house.py) (its docstring says
  concurrent starts can exceed the limit)
- Completion is a plain update with no check on status: **code**
  `game_repository.py`::`complete_game`
- Extraction skips games with `lessons_extracted_at` set and upserts one row per game in one
  transaction: **code** [`Agents/memory/extraction/served_games.py`](../../../Agents/memory/extraction/served_games.py)
- Lesson counters are read, add, write: **code** [`Agents/turn/adoption.py`](../../../Agents/turn/adoption.py)

- Cached chunks send nothing: **code** [`server/game/translate.py`](../../../server/game/translate.py)::`is_cached`; **test**
  [`tests/server/test_translator.py`](../../../tests/server/test_translator.py)::`test_every_real_chunk_re_delivered_as_cached_sends_nothing`
  (not run for this note)
- The blanket dedup left out, and the two event types that repeat: **doc**
  [`frontend/docs/server_encountered_challenges.md`](../../../frontend/docs/server_encountered_challenges.md) section 8

**The unknown outcome (3.4)**

- 30 s limit and two attempts; the provider's client re-sends once: **code**
  [`Agents/llm_factory/accessors.py`](../../../Agents/llm_factory/accessors.py), `chat.py`
- Rescue on a stall: **code** [`Agents/turn/agent_player.py`](../../../Agents/turn/agent_player.py)::`run_agent`
- A timed-out call recorded as failed with zero tokens: **code**
  [`server/game/usage.py`](../../../server/game/usage.py)::`on_llm_error`

**Gaps (3.7)**

- No question id on an answer: **code** `submit_turn`, [`frontend/src/lib/api.ts`](../../../frontend/src/lib/api.ts) (payload
  shapes); the late retry being accepted for a new question: **inferred**. The seat clocks do
  compare the question: **code** [`server/game/seat_clocks.py`](../../../server/game/seat_clocks.py)
- A failed `create_game` is ignored by `_launch`: **code** `live_game_registry.py`
- `folded_in_gen` is read by the write-back and set by no code: **code** (repository search)

**dota2pred (3.6)**

- Stage table and the three faults: **code**, re-read 2026-11-13; no commits to that repository
  since 2026-11-11. Detail and line references: [working/u04_seed_notes.md](working/u04_seed_notes.md)
- The history update being safe to repeat, and whether a publish follows the swallowed
  prediction error: **not verified**

**Incidents on record**

- 2026-08-19: a human's answer re-ran the AI votes and some changed; the cache was added, and
  at first never matched because the key was made from the objects. `langgraph_langfuse_issues.md`
  5.2, 7.1, 7.2
- 2026-10-26: two games shared a cached opening answer; one game replayed another's failed
  turn nine minutes later. In an offline check, 7 of 66 pairs among 12 dealt games shared a key.
  `langgraph_langfuse_issues.md` 7.3
- 2026-10-17: a vote lost on bad wifi was never sent again; the browser's retry was added.
  Comment at `postTurn`
- dota2pred, 2026-06-07: the completion backlog and the dead-letter churn.
  `dota2pred/docs/2026-06-07-pending-completion-backlog.md`,
  `2026-06-07-dlq-churn-and-opendota-cost.md`

**Not established**

- Whether a provider bills a call the client abandoned at its time limit.
- Whether a late retried answer is in fact accepted for a seat's next question.
- Whether one game can be counted twice in a credit window that reads both files and the
  database.

**Reading**

- Stripe, "Idempotent requests" (API reference): how a provider implements the key in 1.2.
- microservices.io, "Transactional outbox": the pattern in 1.3, with its relay.
- AWS Builders' Library, "Making retries safe with idempotent APIs": the receiver's side.
