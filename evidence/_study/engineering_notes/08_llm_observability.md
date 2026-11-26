# U8. Observability: finding out what happened in a run of model calls

**Reading time:** about 65 minutes for Parts 1 to 3 (estimate); Part 5, 5 minutes · **Builds on:** U3 (the event log), U4 (the turn cache), U5 (the human turn) · **Related:** U9 (provenance), U10 (keys and what must not be collected) · **Feeds write-up chapter:** 7

**The question:** something went wrong inside a run of hundreds of model calls. How do I find
out what happened, and why?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

**Reading path.** Part 1 explains the kinds of record and what each can prove. Part 2 separates
what the libraries do from what my code does. Part 3 is my system. Part 4 is three design choices.
Part 5 is the summary and the problems.

**Core and detail.** The core is four ideas: which record answers which question (1.1 and 1.2),
joining records by a shared id (1.3), what a missing record means (1.4), and recording errors
(1.6, with the design of the error itself in 1.6a). Counting usage (1.5) is short and specific to model applications. Section 1.8a says what a model
application adds to each idea, and 1.9 turns the core into seven questions to ask of a new design. Sections marked **Detail** can wait for a second read.

## The whole idea

```text
A run happens  →  it leaves records as it goes  →  later, someone asks "what happened?"
                  (logs, metrics, traces,           The answer can only come from
                   saved inputs and outputs)        records that were written.
```

Observability is being able to answer questions about a run from the records it left, without
running it again. For a model application that matters more than usual, because a run cannot be
repeated exactly: the model may answer differently the second time.

**Two kinds of trouble, read differently.** The note covers both, and they start from
different records.

| | Something failed | Nothing failed, but the result is wrong |
|---|---|---|
| Example | The search service timed out; the reply code crashed | A customer was told the wrong refund period |
| How it shows | An exception, a crash, a rising error rate | No error anywhere. A complaint, or a low score in an evaluation |
| The question | What broke, where, and how often? | What was the model given, and why did it answer that? |
| The record to open first | The error report or the log, then a count | The trace: the prompt as sent and the reply as returned |
| Found in | All software | Model applications above all |
| Sections | 1.6, 1.6a, 3.5, 3.5a | 1.2, 1.4, 1.8, 1.8a, 3.3, 3.4 |

The kinds of record (1.1), joining them by an id (1.3) and what must not be recorded (1.7)
serve both. A trace also answers a third question in any software: where did the time go (1.2)?

| Concept | The question it answers |
|---|---|
| Kinds of record | Which record answers which question? |
| Traces and spans | What happened inside one request, in what order, and how long did each part take? |
| Joining records | How do I find the same event in two different records? |
| A missing record | What can I conclude when a record is not there? |
| The design of an error | What must an error carry so that the code, and I, can act on it? |
| Collection limits | What must not be recorded, and what does recording cost the running system? |
| What a model application adds | What changes when a step can be wrong without failing? |
| Deciding what to record | What does a new design have to record, before any of it is built? |

---

# Part 1 — Fundamentals

The example throughout is a support assistant. A customer asks a question; the assistant
searches a help-centre index, calls a model with the results, and replies. Yesterday a customer
was told the wrong refund period.

## 1.1 Three kinds of record

| Record | What one entry is | Good for | Weak at |
|---|---|---|---|
| **Log** | A line of text written when something happens: `refund lookup failed for order 88` | Detail about one moment | Seeing a whole request, or a trend |
| **Metric** | A number counted over time: `failed lookups per minute = 3` | Trends, rates, alerts | Saying which request failed, or why |
| **Trace** | The record of one request from start to end, as a tree of timed steps | What one request did, in order, and where the time went | Trends across many requests |
| **Application record** | The application's own data: the reply it saved, an event history | What the application committed or produced | Says nothing of how the result was reached |

They answer different questions:

```text
"Is something wrong right now?"            → a metric
"Which request went wrong, and where?"     → a trace
"What exactly happened at that step?"      → a log line, or the data saved on the trace
"What did my server produce?"              → an application record
```

Three stages are easy to merge and should be kept apart: what the model returned, what the
server produced from it, and what the user's screen showed. A reply can be changed or lost
between any two of them, and each stage needs its own record.

A system with only logs can answer the third question and has to work hard for the first two.

## 1.2 Traces and spans

A **trace** is everything one request did. It is made of **spans**. A span is one timed step:
it has a name, a start, an end, a parent, and **attributes** (named values attached to it).

```text
Trace: "answer customer question"                        2.4 s
├─ span: search help centre         query="refund period"   0.3 s
├─ span: model call (decides to look up the policy)          1.0 s
├─ span: tool "lookup_policy"                                0.2 s
├─ span: model call (writes the answer)   1,850 tokens       1.0 s
└─ span: send reply                                           0.1 s
```

The tool runs after the model asks for it, so here the two model calls and the tool are
siblings. How spans are nested depends on how the code was instrumented.

Two things make this work.

- **Parent and child.** Each span records which span it was started inside. That is what turns
  a flat list of steps into a tree.
- **Context propagation.** A new span has to know its parent without every function passing it
  along by hand. Inside one process the tracing library keeps "the current span" in a context
  variable, and a new span reads it. Across two services, the current trace id is sent in a
  request header, and the receiving service continues the same trace.

For a model call, the span usually also carries the prompt, the reply, the model's name and the
token counts. That is the main addition a model application makes to ordinary tracing.

### Check

A trace shows a model call span of 9 seconds, followed by a tool span of 0.2 seconds.
What does the trace establish, and what does it not?

<details>
<summary>Answer</summary>

It establishes that the call happened, in what order, how long each step took, and (if captured)
what went in and came out. So the slow step was the model call, not the tool. It does not establish
that the model was computing for the rest: the span measures the time between sending the
request and getting the reply, which includes the network, waiting in the provider's queue and
any retry made inside the call. It also does not establish whether the answer was right. Those
need other evidence: the provider's status, a retry count, a check of the output.
</details>

## 1.3 Joining records

Each record is written by a different piece of code, into a different place. To follow one
event across them, they must share an identifier. This is a **correlation id** (the same idea
as U5's question id, used here for records instead of answers).

```text
log line:     2026-11-13 10:02:11 request=abc123 refund lookup failed
trace:        trace_id=abc123
database row: support_replies.request_id = abc123
```

With a shared id, "show me everything about that request" is one lookup in each store. Without
one, the records can only be matched by time and guesswork, and with several requests running
at once that often cannot be done.

The id has to be chosen at the right level, so there are usually two or three.

| Id level | Finds | Cannot pick out |
|---|---|---|
| Session (a conversation, a game) | Everything belonging to it | One call among fifty |
| Request or run | One execution | One step, when many run inside it |
| Step (a turn, a span) | One operation or decision | The session, unless it links back |

The ids need not be the same value in every store, as long as the mapping between them is
kept. My game has the session level in every record and no step id shared by all of them
(section 3.4).

## 1.4 A missing record

The most common mistake in reading records is treating "nothing was recorded" as "nothing
happened".

**A record's absence means something only if the record would have been written.** So the
first question about an empty result is: which code writes this record, and did that code run?

```text
The trace has no model call for step 3.

Possible meanings:
  - no model was called (a cached result, a default, a human's step)
  - a model was called by code the tracing does not cover
  - the call was recorded and the record was lost on the way to the store
```

All three look the same in the trace. Telling them apart needs a second, independent record:
the token usage, the saved output, a log line. When two independent records disagree, the
disagreement is the clue.

### Check

The support assistant's trace for yesterday's bad answer shows the search span and the reply,
and no model call. The usage count for that hour is one lower than the number of replies sent.
What are two explanations, and what would separate them?

<details>
<summary>Answer</summary>

One: the reply came from a cache of earlier answers, so no model was called. The usage count
agrees with this, since it is also one short. Two: a model was called by a code path with no
tracing and no usage counting. To separate them, look for a record that only one explanation
predicts: the provider's own billing for that hour (a real call appears there), or a cache-hit
record if the cache writes one. If the cache writes nothing when it is hit, that is itself the
gap to fix.
</details>

## 1.5 Counting usage, and pricing it later

A model call returns how many tokens it read and wrote. Adding those up is the one metric every
model application needs, because it is the bill.

```text
Stored:   2026-11-13 10:00 | model A | 412 calls | 3 failed | 1.9M tokens in | 0.2M out
Not stored: the cost
```

The counts are stored, and the cost is worked out when someone reads it: counts × the price
list. The reason is that prices are the part that turns out wrong. A price was entered wrongly,
or a cheaper rate for cached tokens was missed. If the cost had been stored, every old row would
hold the wrong figure. With counts stored, correcting the price list corrects every past figure.

One condition: a price that really changed must not be applied to older calls. So the price
list is dated ("this rate from this day"), and each count is priced at the rate in force when
the calls were made. That in turn needs the counts to be stored with their time.

Two choices decide what the counts can answer later:

- **What they are grouped by.** Per model per hour answers "what did model A cost yesterday?".
  It cannot answer "what did this one turn cost?".
- **What a failure records.** A failed call usually returns no token counts, so it can add to a
  "failed" count and nothing else.

## 1.6 Errors: handle it, then decide who hears about it

Handling an error and recording it are two separate decisions. Handling is what the system does
next: retry, fall back, use a default, refuse the request (U1). Recording is whether anyone
will ever find out. Every place the code catches an error makes both decisions, and the second
is often made by accident.

```python
try:
    answer = call_model(question)
except TimeoutError:
    answer = DEFAULT_REPLY        # handled well. Recorded nowhere.
```

That code behaves correctly and hides the failure completely. If the model times out on half
of all requests, nothing shows it. This is a **swallowed error**, and a fallback is the most
common place for one, because the fallback makes the symptom disappear.

**Expected and unexpected errors go to different places.**

| Kind | Example | Where it goes | Why |
|---|---|---|---|
| Unexpected: a bug, a crashed task | A `KeyError` in the reply code | An **error report**, one per occurrence, with the stack trace | Somebody has to look at it |
| Expected, and it matters in bulk | A model timeout that was retried | A **count** (a metric) | One is normal; a rising rate is the signal |
| Expected, and it is the user's to fix | A wrong API key, an invalid input | A clear message to the user; a log line at most | Reporting it would bury real errors in noise |

**What an error-reporting service adds to logs.** A log holds each error as a line among
thousands. An error reporter (Sentry is one) groups identical errors into one issue, and shows
how many times it happened, when it first appeared, and in which release. It can alert on a
new issue. So it answers "what is broken right now, and is it new?", which a log file does not.

**The rule for a fallback:** it may hide the failure from the user. It must not hide it from
me. A fallback needs at least a count.

### Check

The support assistant catches every exception from its search step and answers "I could not
find that" instead. Its error rate is zero and customers are complaining. What is wrong, and
what is the smallest fix?

<details>
<summary>Answer</summary>

The search errors are swallowed: handled, and recorded nowhere, so a broken search looks the
same as a question with no answer. The smallest fix is to record inside the `except`: a count
of search failures, and an error report for any exception that is not an expected kind (a
timeout is expected; an `AttributeError` is a bug). The reply to the customer can stay the same.
</details>

## 1.6a Designing the error: its type, its message, and where it is caught

Section 1.6 was about what happens after an error is caught. This section is about the error
itself: what type it is, what its message says, and which code catches it.

**1. The type is for the code.** The only thing an error's type does is let an `except` line
pick that error out from the others.

```python
try:
    answer_question()
except KeyRejected:
    ask_the_customer_to_check_the_key()     # this failure gets its own handling
except Exception:
    report_it()                             # everything else is a bug
```

The first branch can exist only because `KeyRejected` is a type of its own.

**2. A built-in type, or one of my own?** Built-in types are shared with Python itself and
with every library, so catching one catches more than was meant.

```python
raise ValueError("key rejected")
...
except ValueError:                          # meant for the rejected key
    ask_the_customer_to_check_the_key()     # also catches int("abc") from a bug elsewhere
```

That bug would be shown to the customer as a key problem and never reported. So the question at
the `raise` is whether some code will need to tell this failure apart from others.

```text
Yes → an own type. It can still be a kind of built-in one: class KeyRejected(ValueError).
No  → a built-in type (ValueError, RuntimeError) with a good message. The error ends the
      operation and a person reads it. An own type that no `except` names is only one more name.
```

An own type can be added later, the first time an `except` for that one case is wanted.

**3. Where an own error comes from.** The type only names the failure. Something still has to
notice it, and there are two ways.

```python
# My own check notices it.
if order_id not in orders:
    raise OrderNotFound(order_id)

# A library notices it, and its error is converted at the line that calls the library.
def call_model(question):
    try:
        return provider.complete(question)
    except provider.AuthError as e:
        raise KeyRejected("the provider refused the API key") from e
```

The second is **translating at the boundary**: the library's error comes in, and my type goes
out. `from e` keeps the original attached as the cause, so the stack trace still shows what the
provider said. Converting is worth it for three reasons:

| Reason | Without converting | With it |
|---|---|---|
| Several providers | Each has its own error class for a bad key, and every handler must know them all | Only the boundary knows them |
| Replacing a provider | Every handler that named its errors changes | One place changes |
| Meaning | "HTTP 401" says what the provider answered | "The assistant's key was refused" says what it means in this system, and so what to do next |

**4. The message is for the person.** It says what failed, for which thing, and why.

| Message | What is wrong with it |
|---|---|
| `"failed"` | Says nothing |
| `"search failed"` | Which search, for whom, and why? |
| `"search failed for conversation 4711: index 'help-centre' timed out after 5 s"` | Nothing: the operation, the id to join on (1.3), and the cause |

Two limits. A message must not contain a secret, and a provider's error sometimes repeats the
key it was sent (1.7). And a message for the user is not the message for me: "Check your API
key" for one, the provider's raw reply for the other. Often both are written, one shown and one
logged.

**5. Catch where something can be done. Everywhere else, let it rise.** The test for a `try`
is not "is this error expected?". It is "can this function do something about it?": retry,
fall back, answer the user, or record it and end cleanly. A timeout is expected, and a function
that can neither retry nor fall back still lets it rise to one that can. That leaves three
correct shapes.

```python
# A. No try/except. The function cannot act, so the error leaves by itself.
def search(question):
    return http_get(INDEX_URL, question)

# B. Catch only what can be acted on. Everything else still rises.
def search(question):
    try:
        return http_get(INDEX_URL, question)
    except TimeoutError:
        return http_get(INDEX_URL, question)      # one retry

# C. Do something on the way past, then re-raise the same error.
    except Exception:
        release_the_lock()
        raise
```

An `except` stops only the types it names. `except Exception` names every type, so nothing
rises past it unless the handler re-raises (shape C). Without a re-raise it belongs in two
places: the line that calls a library whose errors cannot be listed in advance, where the error
is sorted at once (point 3), and the **boundary of a unit of work**.

```text
the server process
 ├─ request 1                ← boundary: catch everything, record it, answer "500"
 ├─ request 2                ← its own boundary. Request 1's failure does not reach it
 └─ a worker, one message at a time
      ├─ message A           ← boundary: record it, set the message aside, take the next
      └─ message B
```

There is one boundary for each unit of work, not one for the program. A request, a background
task and one message from a queue are each a unit, and a failure in one must not end the
others. Anywhere deeper, a broad catch with no re-raise is the swallowed error of 1.6: the
function returns a default, and its caller cannot tell "it failed" from "there was nothing".

```text
The whole rule:  handle what can be acted on, where it can be acted on.
                 Let the rest rise.
                 At each unit's boundary, catch everything, record it, and end that unit cleanly.
```

**6. The type is also what gets counted.** Counting failures (1.6) needs something to group
by. Message text differs every time; the type does not.

```text
KeyRejected      3
SearchTimeout   41
everything else  2
```

That is a view of what is going wrong, and it exists only if the types mean something. One
catch-all type gives one row.

### Check

A function catches `Exception`, logs "something went wrong", and returns `None`. Its caller
treats `None` as "nothing found". What has been lost?

<details>
<summary>Answer</summary>

Three things. The type: the caller cannot tell a timeout from a bug. The cause: there is no
stack trace and no original error. And the failure itself: `None` now means both "nothing
found" and "it broke", which is the swallowed error of 1.6. The fix is to let the error rise,
or raise an own type `from` the original, and to catch it only where something can be done.
</details>

## 1.7 What recording costs, and what must not be recorded

Records are sent while the system runs, so recording has costs of its own.

| Concern | What goes wrong | Usual answer |
|---|---|---|
| Sending is slow | Each span sent as it ends would slow every request | Records are collected in memory and sent in batches. A **flush** sends what is waiting |
| The process dies | The batch in memory is lost | Flush at the end of each unit of work; accept that the last moments before a crash may be missing |
| The record store is down | The system fails because its monitoring failed | Recording must never raise into the work. Records are dropped instead |
| Volume | Every prompt repeats the whole conversation, so storage grows fast | Keep everything for a while, or record a share of requests (**sampling**) |
| Private data | Prompts, cookies and keys end up in a third party's store | Decide what is collected before turning it on. Leave out what is not needed; scrub what could slip in |

The last row is a design decision, not a setting to fix later. An error report that includes
local variables will include whatever those variables held.

## 1.8 Worked example: the wrong refund period

```text
1  A metric shows nothing unusual: replies per hour and error rate are normal.
   (A wrong answer is not an error. Metrics rarely catch it.)

2  The customer's conversation id finds the trace.
   The trace shows: search → model call → reply.

3  The search span's output holds two documents. One is the 2023 refund policy.
   So the model was given an outdated document.

4  The model call's saved prompt confirms the 2023 text was in it,
   and the saved reply quotes it.

5  What is established: outdated text reached the model, and the reply agrees with it.
   What is not: why the search returned it. The index may hold an old document, the
   ranking may prefer it, or the current policy may be missing. That needs the index's
   own records.

6  A check on the diagnosis itself: was that trace complete? If the search span had been
   missing, steps 3 to 5 could not have been done, and "no search span" would not have
   meant "no search" (1.4).
```

Each step used a different record. The metric said "no alarm", the id joined the complaint to
the trace, the span's saved data showed what the model saw, and the saved prompt confirmed it.
Without step 4, "the model made it up" and "the model was given bad input" could not be told
apart. Whether a customer's message may be kept in a trace at all is the collection question of
1.7, decided before any of this.

## 1.8a What a model application adds

Sections 1.1 to 1.7 hold for any software. A model application adds something to each, for one
reason: a model can return a wrong answer while every call succeeds.

| Section | The general idea | What a model application adds |
|---|---|---|
| 1.1 Kinds of record | Logs, metrics, traces, application records | The trace saves content, not only timings: the prompt as sent and the reply as returned. A fifth kind of record appears: a **score** attached to a trace |
| 1.2 Traces and spans | A tree of timed steps | The model call's span carries the model's name, its settings and the token counts. Retrieval and tool calls get spans of their own, holding what was retrieved and what the tool returned |
| 1.3 Joining records | A shared id | The id has to outlive the request, so a score or a user's feedback can find the reply later. Version stamps go with it (prompt version, model, release), so a fall in quality can be tied to a change |
| 1.4 A missing record | Absence means little unless the writing code ran | More paths skip the model: a cache hit, a fallback, a second model. Each records which path answered, and which model |
| 1.6 Errors | Unexpected; expected in bulk; the user's to fix | A fourth kind, the wrong answer with no error. And expected failures of the model's own: a refusal, a reply cut off at the length limit, structured output that does not parse |
| 1.7 Cost and limits | Volume and private data | Both are larger: each prompt repeats the conversation, and a prompt holds whatever the user typed |

**A wrong answer is found by other means, and the trace is their raw material.** Nothing
raises, so the program cannot catch it as it catches a timeout. It is found in layers, from
cheap and complete to costly and sampled.

| Layer | What it covers | Its limit |
|---|---|---|
| A check in code, on every output | Structure and hard rules: a valid format, an allowed value | Cannot judge meaning |
| A small model check in the request, at one known risk | One named failure, on every output | Adds time and cost, so only a few |
| A model as judge, afterwards, on a sample | Meaning and quality | A sample only, and the judge has to be checked itself |
| A person's review, and reference answers | The standard the judge is checked against | Slow, so small |
| User feedback | Real use | Sparse and late |

Tracing detects nothing by itself. It makes the layers possible: it saves the exact input and
output for a judge or a person to read, it gives each reply an id for a score or a complaint to
attach to, and it is what a sample is drawn from. How the layers are built and trusted is the
subject of evaluation, not of this note.

**The span that shows the wrong output is often not the span at fault.** In the worked example
(1.8) the model's reply was wrong, and the model call was faithful to what it was given. The
fault was in the search before it. So a trace is read backwards from the wrong output, with two
separate questions at each step:

```text
1. Was this step's input right?
      No  → the fault is upstream. Go to the step that produced the input and ask again.
2. Given its input, was its output right?
      No  → this is the step at fault.
```

This works only if each span saved its own input and output. In a chain of model calls the
effect compounds: a false statement written by an early step is input to every later one, and
each later step can look wrong while answering reasonably to what it was told.

It is also why a step is tested two ways. Replaying one step on its recorded input shows
whether that step is right given what it received. Running the whole chain shows whether
errors compound. A replay that keeps finding "the output is wrong, and so was the input" says
to stop changing that step and fix the one that feeds it.

### Check

The assistant's replies are replayed on 10 recorded conversations, and 8 are wrong. In 7 of
those 8, the recorded search result already held an outdated document. What is fixed first?

<details>
<summary>Answer</summary>

The search. In 7 cases the model answered faithfully to a wrong input, so changing the model's
prompt would be tuning the wrong step. One case remains where the input was right and the reply
wrong: that one is the model step's own, and it is looked at after the search is fixed, when
the replay is run again.
</details>

## 1.9 Deciding what to record, before building

The sections above read records that already exist. For a new system the same ideas become seven
questions, asked of the design before the code is written.

| Question | For the support assistant | What the answer decides |
|---|---|---|
| 1. What units of work will someone ask about? | "This conversation", "this reply", "this search" | The trace, and the named spans inside it (1.2) |
| 2. What id ties every record to that unit? | The conversation id | The id that goes on the trace, the log lines, the error reports and the database rows (1.3) |
| 3. Where can a step go wrong without raising an error? | The search returns nothing; a fallback reply is used; a call is retried | A record written at each of those places, because nothing else captures them (1.4, 1.6) |
| 4. For each setting, what number would show it is wrong? | The timeout assumes a normal call is much faster than the limit | A count or a timing kept for each setting: how long calls take, how often a retry succeeds |
| 5. What must never be recorded? | A card number in a customer's message; an API key | What is switched off or scrubbed before recording is turned on (1.7) |
| 6. What do I need to be told about, not only able to look up? | The search service is down; the error rate has doubled | The alerts. Everything else can wait in a record until someone asks |
| 7. How will I find out that an output was wrong, when nothing failed? | A sample of replies is scored each week; a "this was wrong" button sends the conversation id | The checks, the sample that is judged, and the id a score or a complaint attaches to (1.8a) |

A library answers part of questions 1 and 2: it records the calls that pass through it and nests
them. It cannot answer 3 and 4, because it does not know which fallbacks exist or which settings
were chosen from which numbers. Those two are where records go missing.

Part 3 gives my server's answers. Section 3.6 lists the places where the answer today is "not
recorded".

---

# Part 2 — What the libraries do, and what my application does

| Responsibility | The library | My application |
|---|---|---|
| Create the tracing client | Reads its keys and settings once, when the client is created | Decides when that is: a call at start-up, after the settings are loaded (Part 4) |
| Record each model call as a span, with prompt, reply and tokens | Langfuse's LangChain callback | Attaches the callback to the game's run |
| Know a span's parent | The tracing library's "current span" context | Opens the root span and the named spans around each decision |
| Send records | The SDK batches and sends in the background | Calls `flush()` when a game ends |
| Name things so they can be found | Nothing | Chooses the trace name, the session id, the span names |
| Count tokens for billing | The provider returns the counts | Adds them up per model per hour, and prices them when read |
| Catch unhandled errors | Sentry's SDK | Decides what is excluded, scrubs keys, tags the game |
| Save what each seat was shown | Nothing | The prompt capture and the events table |

The libraries record what passes through them. They cannot record a step that never reaches
them, and they do not know what a "game" or a "turn" is. Every name that makes a record
findable is my code's.

---

# Part 3 — My Werewolf server: what a game leaves behind

## 3.1 Why this matters: a failure with no failed call

On 2026-10-17, in a hosted game, the Serial Killer in seat 9 passed its turn with the reason
"generation failed". Three records were checked, and they disagreed:

| Record | What it said |
|---|---|
| The event log | Seat 9 passed: `generation_failed` |
| The usage count | 142 model calls, 0 failed |
| The prompt capture | Opening prompts for 8 of the 9 AI seats. None for seat 9 |

A failed generation with no failed call and no prompt is section 1.4's situation: the step
never reached the instrumented code. The cause was the turn cache. Its key did not include the
game's id, so seat 9 was handed a result from another game played nine minutes earlier, and
that result was a failure. A cache hit skips the turn's code, and nothing recorded that a cache
hit had happened. The cause was found only by putting the three records side by side (U4
section 3.2 has the key and the fix).

## 3.2 The records a game leaves

| Record | Where | Written when | Answers | If the process dies mid-game |
|---|---|---|---|---|
| **Trace** | Langfuse (self-hosted) | Spans are sent in batches; flushed when the game's task ends | What each model call was given and returned, in order, with timing | Spans not yet sent are lost |
| **Events** | The `events` table | After every chunk of engine output | What the server produced for each viewer, in order. Not whether a browser received or drew it | Kept up to the last chunk saved |
| **Usage** | `games.usage` | When a chunk arrives and 30 seconds have passed since the last save; and at the end | Calls, failures, tokens and seconds, per model per hour | Usually the last 30 seconds or less. More if the engine was silent or a save failed: a failed save is retried at the next chunk |
| **Prompt capture** | The `prompt_captures` table, gzip-compressed | Once, when the game is over | The inputs each seat's prompt was built from, and its private reads | Nothing is written. After a restart the capture is marked partial |
| **Server error report** | Sentry | When the game's task dies, or fails after the game is over | The exception, tagged with game, model and stage | Not sent if the process is killed |
| **Frontend error report** | Sentry | When the page crashes while rendering | The exception, with the stage's position (game, event number) | Does not apply |
| **Logs** | The container's log (stderr) | As things happen | Rescues, fallbacks, timeouts, recovery | Written lines survive the process. How long the container's log is kept is not established |

Three points about this table:

- **The events table is the most durable record and the trace is the most detailed.** They are
  written at different times by different code, which is what made the diagnosis in 3.1
  possible.
- **The prompt capture holds the inputs to the prompt template, not the final text sent and not
  the model's reply.** The reply is in the trace.
- **The prompt capture is written only at the end.** A game that is dropped mid-play leaves
  none.
- **The usage count is the one aggregate the server keeps.** It follows section 1.5: counts per
  model per hour are stored in the game's row, and `game_cost` applies the price list when the
  figure is read. The price list is dated: each model has rows "in force from this day", and a
  count is priced at the rate of its own hour, which is why the counts are kept per hour. A
  failed call adds 1 to `failed` and no tokens or time.

*Code:* [`GameSession._run`](../../../server/game/game_session.py) opens the trace;
[`prompt_captures.py`](../../../server/storage/prompt_captures.py);
[`UsageMeter` and `game_cost`](../../../server/game/usage.py);
[`error_reporting.py`](../../../server/error_reporting.py);
[`instrumentation-client.ts`](../../../frontend/src/instrumentation-client.ts).

## 3.3 What a hosted game's trace looks like

```text
Session: <game id>
└─ Trace "werewolf_game"          metadata: game_id, model, byok, recovered
   └─ span "werewolf-game"        output: running → success | interrupted | error
      ├─ span "agent_action_eval_player_3_day_1_round_0_vote"
      │   └─ model call (prompt, reply, tokens)        ← recorded by the callback
      ├─ span "day_resolution_day_1"
      ├─ span "night_resolution_day_1"
      ├─ span "day_summary_eval_<game>_day_1"
      └─ span "postgame_extraction_<game>"
```

- **One trace per run of the game's task.** A game that resumes after a restart gets a second
  trace in the same session, with `recovered` set.
- **One named span per decision**, with the player, day, round and phase in its name. The model
  call sits inside it.
- **A human's draft preview is a separate trace** (`draft_preview`) in the same session. A draft
  written from the player's notes has only the usage counter attached and is not traced.
- **Calls made directly through the Anthropic SDK** do not pass through LangChain, so they are
  logged as spans by my own code.
- **A human's turn has no model call.** An "empty" stretch of trace at a human seat is expected.
  On 2026-08-24 a game stuck at "player 2 is thinking" was first read as a stalled model. The
  trace was empty because seat 2 was the human, whose browser never received the prompt (a
  cookie scoped to the wrong path).

## 3.4 Following one turn across the records

The game id is the only id present in every record.

| Record | Holds the game id as | Can find one turn by |
|---|---|---|
| Trace | Session id and metadata | The span's name: player, day, round, phase |
| Prompt capture | `game_id` | Its entries' player, day, round and output key |
| Events | `game_id` | The payload's day and player; `seq` gives the order |
| Usage | The game's row | Not possible: counts are per model per hour |
| Server error report | A `game_id` tag | Not possible: game and time only |
| Frontend error report | The stage context | The event number (`seq`) the page had reached |

So to answer "why did seat 7 vote that way on day 2?":

```text
1  Events: find seat 7's vote on day 2. That is what the server sent to viewers.
2  Trace: open the game's session, find the span named for player_7, day 2, vote.
   Its model call holds the prompt as sent and the reply.
3  Prompt capture: seat 7's entry for day 2 holds the inputs the prompt was built from,
   and the seat's private reads.
4  If 2 has no model call, three explanations remain (1.4), and each needs its own check:
     - no model was called: a human seat (the game's row lists them), a turn-cache hit
       (no record of one exists, so this is reached by ruling out the others), or a
       safe default after a failure (a pass marker in the events; a log line)
     - a call was made by code the callback does not cover (a direct SDK call)
     - the span was recorded and lost before it reached Langfuse
   The usage count helps only at the level of the game: its totals cannot say whether
   one particular turn made a call.
```

No trace id is stored in the database, so step 2 is done by name, inside the game's session.
There is no single id for a turn that all the stores share.

**A failure that starts in the browser.** A player reports that the screen froze during the
vote.

```text
1  Frontend error report: is there a crash for that game? If so, its stage context gives
   the game id and the event number (seq) the page had reached.
2  Events: read the game's events around that seq. If the vote's events are there, the
   server produced them. That does not show the browser received them.
3  Server: error reports and log lines for that game id. A task that died shows here.
4  Trace: if the events stop before the vote, the game's trace shows which call was
   running last.
```

What this cannot settle: an event that was produced and saved but never reached the browser,
with no crash. No record is written when a browser receives or draws an event, so "the server
sent it" and "the player saw it" are separate claims, and only the first has a record. U6 covers
the connection in between.

## 3.5 Error reports: what is sent, and what is left out

**Which errors are reported** (section 1.6 applied):

| What happens | Handling | Recording |
|---|---|---|
| A game's task dies, or fails after the game is over | The game ends, or is archived without its extraction input | An error report, tagged with game, model and stage |
| The provider rejects a player's own key | The page asks for another key | No error report, on purpose: it is the player's to fix |
| The prompt capture cannot be saved | The game is unaffected | A log line |
| A model call stalls and the rescue model answers | The turn carries on | A log line, with no game id and no count |
| A turn falls back to a random legal target | The game carries on | A log line. Nothing in the events or the state |

The last two rows are swallowed errors in the sense of 1.6: handled correctly, and invisible in
bulk. Log lines are attached to an error report as context, and do not become reports
themselves.

**What is left out of each sink:**

| Sink | What is left out |
|---|---|
| Server error reports | Request bodies, headers, cookies, query parameters, local variables in stack frames, model inputs and outputs. Values of `api_key`, `seat_token`, `host_key` and `x_admin_token` are replaced at any depth. A player's own key is removed from every string |
| Frontend error reports | All default data collection is off. Typing in input boxes is not recorded. The stage context holds positions and ids, and no player text |
| Logs | A player's key is replaced with `***` in error text and tracebacks |
| Both error reporters | Off unless a DSN is set, so off in local and test runs |

These are safeguards that were built and tested. They do not prove that nothing sensitive can
ever appear, and the accurate wording is "these fields are excluded", not "error reports never
contain a key". U10 covers the key's whole lifetime.

*Tests (named, not run):* `tests/server/test_error_reporting.py`::`test_reporting_is_off_without_a_dsn`,
`test_a_game_failure_is_tagged_and_never_carries_the_keys`, `test_private_fields_are_dropped_at_any_depth`.

## 3.5a My error types: where each is raised, where it is caught, and who hears

My code defines ten error types (1.6a). Each row is one path from the line that raises to the
line that decides.

| Type | Raised when | Caught at | Who hears |
|---|---|---|---|
| `KeyRefused` | Before a game starts, the provider refuses the key or does not answer in time (`server/game/key_check.py`) | The route that creates a game or a room | The player: status 422 with the reason |
| `ProviderKeyRejected` | During a game, the provider refuses the game's key on the primary model (`Agents/turn/agent_player.py`) | The game's task (`game_session.py`, `_run`) | The player, in plain words on the page. The game is marked dropped and a line is logged. No Sentry report, on purpose |
| `ModelNeedsKey`, `HouseClosed` | The chosen model is not one the house pays for, or the house's games for today are spent (`server/house.py`) | `authorize_model` in `server/routes/_shared.py` | The player: 422, or 402 with a `Retry-After` header |
| `HumanTurnContractError` | A person's answer breaks the turn's rules, such as a pass where none is allowed (`Agents/turn/human_turn.py`) | The submit route. The command-line game catches it too and asks again | The player: 422 with a message written for them |
| `ReplayNotFound`, `IncompleteReplay`, `ReplayArchiveNotConfigured` | Reading a finished game (`server/storage/replay_service.py`) | The replay routes | The viewer: 404, 500 and 503 |
| `TranslationError` | The engine sends a chunk the translator has no entry for (`server/game/translate.py`) | Nothing catches it by name. It reaches the game's task | Me. It is a bug, so the generic path runs: logged, game dropped, Sentry report |
| `Contradiction` | The deduction solver finds a player with no possible role left | Inside the solver, whose entry function then returns `None` | Nobody. It is control flow inside one module and never leaves it |

**My units of work and their boundaries** (1.6a, point 5). An HTTP request: FastAPI answers
500 for an error no route caught, and Sentry's hook reports it. A game: the `except Exception`
in the game's task, which records the error on the game, marks it dropped and reports it. One
game's failure ends that game only.

**The table has three groups**, and they are the rows of 1.6's table:

```text
The player's to fix   KeyRefused, ProviderKeyRejected, ModelNeedsKey, HouseClosed,
                      HumanTurnContractError
                      → caught where the answer goes back to the player, turned into a status
                        code and a message, and not reported.
A bug                 TranslationError
                      → deliberately not caught by name, so it gets the full report.
Internal control      Contradiction
```

Every route converts with `raise HTTPException(...) from exc`, so the original error stays
attached. One error gains context on its way up: a refused backup key is re-raised as
`KeyRefused("Your backup key: ...")`, so the player knows which of two keys was refused.

**Translating at the boundary: the provider's errors.** One function is the only place that
reads a provider's error text.

```text
chain.invoke(...) raises whatever the provider's SDK raises
   │
   │  _generate() catches Exception and sorts it at once        (Agents/turn/agent_player.py)
   ├─ the key was refused  → returns _Rejected(reason)  → ProviderKeyRejected is raised
   ├─ slow or full         → returns _STALLED           → the rescue model takes the turn (U1)
   └─ anything else        → returns None               → the turn's retry and fallback (U1)
```

The sorting functions (`is_key_rejected_error` and `is_transient_provider_error`, in
`Agents/llm_factory/embeddings.py`) walk the error's chain of causes. They check the status
code first (401 or 403 for a refused key) and known phrases second, because the providers' SDKs
share no error types. Above `_generate`, no code reads a provider's message. Inside the turn
the three outcomes are return values, not exceptions. Only the key refusal becomes an
exception, because only it has to end the game.

**Two messages for one failure.** When the game's task dies, the text shown to viewers is the
error's own words for `ProviderKeyRejected` and its `repr` for anything else. Both pass through
a redaction step first, because a provider's error can repeat the key. The key check before a
game does the same: it replaces the key with `***` in the provider's reason before raising.

**Where this falls short**

| Gap | Consequence | Possible direction |
|---|---|---|
| Failures are counted in total, not by kind | `_generate` sorts every failure three ways and then only logs it. The usage count keeps one `failed` number per model per hour. "How many key refusals, stalls and other failures this week?" cannot be answered (improvements row 2). One kind is not told apart at all: a reply that broke the schema shares the outcome `None` with any other request error | Count the kinds where they are already sorted, by kind and model, saved with the game. Split the third kind by catching the parser's own error |
| An error's type is lost when it is saved as text | A dropped game stores its error as a string. To tell later that it died of a refused key, the server looks for a fixed phrase in that string (`error_kind` in `server/routes/_shared.py`). The phrase is one shared constant, so the two sides cannot drift, but it is still matching on text | Store the kind beside the message |
| The log lines written while sorting name the seat, not the game | The same as gap 3 of 3.6 | The game id on every engine log line |

Not checked: whether the 500 answered for an `IncompleteReplay` also reaches Sentry.

## 3.6 Known limitations

**A. Things that happen and leave no usable record**

| Gap | Consequence | Possible direction |
|---|---|---|
| 1. Nothing counts rescues, fallbacks or safe defaults | They exist only as log lines. "How often does a turn fall back?" cannot be answered (improvements row 2) | Counters saved with the game |
| 2. A random fallback vote or night action carries no marker | It looks like a chosen move in the events and the state. Only a technical pass is marked | Mark the event, as passes are |
| 3. The engine's log lines carry no game id | With several games running, a "rescued by the fallback model" line cannot be tied to its game | Put the game id on every engine log line |
| 4. A cache hit leaves no record | The 3.1 diagnosis had to be made by inference | Record the hit on the turn's span |
| 5. The prompt capture is written only at the end | A game that dies leaves none; a resumed game's is partial | Write it as the game goes |
| 6. No trace id is stored with the game, and events have no timestamp | A turn is joined by name, and "when was this sent?" cannot be answered from the events table | Store the trace id on the game's row; add a time column |
| 7. Evaluation cases from served games are not saved | They exist only as span outputs in Langfuse; batch runs write a file | Persist them, if served games are to be evaluated |

**B. Trouble the server cannot notice while it is happening**

| Gap | Consequence | Possible direction |
|---|---|---|
| 8. Nothing detects a game stuck in a model or engine call | The sweeper covers only games waiting on a person (improvements row 27) | A "no output for N minutes" check |
| 9. The health endpoint always answers "healthy" | It shows the process is up, not that the database or tracing is reachable | Check the dependencies it needs |
| 10. `flush()` runs on the event loop | Every viewer waits while it sends; worst when Langfuse is slow (improvements row 7) | Run it on a thread |

Group A is missing evidence: after the fact, a question has no record to answer it. Group B is
missing monitoring: nothing tells anyone at the time. **Recording is not alerting.**

**Detail: a store of failures is not seen until something counts it.** My dota2pred pipeline has
the same gap in another form. Its dead-letter queues hold every message that failed for good,
and there is a tool to read them, but no count and no alert, and I have never read them (U4
section 3.7). A record that nobody is told about works like no record.

Hosted traces carry the release "unknown", because the container has no git history and no
release variable is set. Checked in the trace store on 2026-11-16: of the 30 most recent game
traces, all 14 hosted ones say "unknown" and all 16 command-line and batch ones carry a commit
id. So a hosted trace cannot be tied to the code that produced it (improvements row 34). The
build now passes the commit id into the image, which takes effect at the next deploy. One
thing is still not read or tested: what the tracing SDK does when Langfuse is unreachable.
A full disk did drop
spans silently in July (`evidence/tracing/report.md`).

## 3.7 Questions earlier notes left for this one

Each is a question a number would answer. The table says whether an existing record holds that
number.

| Question | From | What exists today | What would have to be recorded |
|---|---|---|---|
| How often is a turn rescued, or given a safe default? | U1 3.3 gap 2 | Log lines, one per case, with no game id. A technical pass is also an event | A count per game, saved with the game's row |
| A call's first attempt times out and its second succeeds. What shows? | U1 3.3 gap 2 | Not established. I have not checked whether the failed attempt appears as its own span or adds to the `failed` count | Check one such call in a trace; then count attempts per call |
| How many model calls does a game make per minute? | U1 3.2 | The usage count gives calls per model per hour. The trace's span times give it per minute, by reading a game's trace | Nothing new for a rough figure |
| What is the stall rate on a normal day? | U1 3.2 | `failed` over `calls` in the usage count is close, if a timeout is counted as a failed call (not checked) | Confirm what `failed` includes |
| How long does a stall episode last? | U1 3.2 | Nothing built for it. It could be read from the times of failed spans across games | A record of each stall with its time, per model |
| How many threads of the main pool are busy, and how long does work wait for one? | U2 3.7 gap 2 | Nothing | A reading taken every few seconds of busy threads and queued work, and the time from submitting work to its start |
| How much memory does one running game use? | U2 3.7 gap 4; U15 | Nothing. About 256 MB idle is known | The container's memory read with one game running and with several, beside the count of running games |
| How long does the trace flush block the event loop? | U2 3.7 gap 3 | Nothing | Time the call |

The pattern across the rows: the traces can answer questions about one game after the fact.
Nothing answers a question about the server right now, or about many games over time. That is
the difference between a trace and a metric from section 1.1, and the server has the first and
not the second.

## 3.8 The whole system, layer by layer

The sections above follow a game. This one asks the same question of every layer the system
has: if it goes wrong here, what record would show it?

| Layer | What can go wrong | What records it today | What is missing |
|---|---|---|---|
| Browser | The page crashes; the stage draws the wrong thing; it is slow | A crash while rendering is reported, with the game and the event number reached | Any record of an event being received or drawn; anything on slowness |
| Connection (the event stream) | It drops; it stalls; events do not arrive | The server knows whether a seat is connected (the seat clocks use it). The page has its own check for a stalled stream (U6) | A saved record of connects, drops and stalls |
| Server process | A request fails; a game's task dies; the event loop is blocked | Error reports and log lines, tagged by game on the server side | Request counts and timings; thread-pool and event-loop measurements; a health check that checks anything |
| Engine and model calls | A call stalls or fails; a turn falls back; a wrong decision | The trace, the usage count, the prompt capture, pass markers in the events | Counts of rescues and fallbacks; a mark on a random fallback; a record of a cache hit |
| Database | A write fails; it is slow; it fills up | A failed event save is retried at the next chunk (U4); a failure is logged | Not established: I have not looked for anything that watches Postgres itself |
| Services it depends on | The model provider, the embedder or Langfuse is slow or down | Stalls are tracked per game in memory to choose the rescue model (U1); a game with memory is refused when the lesson store is not ready | A saved history of stalls; what happens when Langfuse is unreachable is not established |
| Host and container | Out of memory, disk full, CPU saturated, the container restarts | Docker's health check calls `/health`. A CPU alert on the host fired on 2026-10-21 (for another project's container) | Not established: what watches disk and memory. A full disk dropped spans silently in July |

Reading down the "missing" column gives the same finding as 3.7, from another side. The middle
of the system, the engine and its model calls, is well recorded. The two ends are not: what the
player's browser actually received, and what the machine underneath was doing. The two real
incidents that were hardest to see, the human's prompt that never arrived (3.3) and the full
disk, were both at the ends.

A general way to use this table for any system: list the layers a request passes through, and
for each ask "what would I look at?". A layer with no answer is where the next confusing
incident will come from.

### Check

A player says: "on day 2 the Seer voted for me for no reason." The trace has a span for that
vote with no model call inside it. The events show the vote, with no pass marker. The game's
usage count shows 0 failed calls. What is established, and what is the next check?

<details>
<summary>Answer</summary>

Established: the server recorded a vote for that seat, and no model call for it reached the
trace. Not established: why. The usage count does not help, since it is per game and cannot
say whether this turn made a call. The candidates are a human seat (check the game's row), a
random fallback after a failure (it carries no marker, so look for the log line near that
time), a turn-cache hit (no record exists), a call made outside the callback, or a lost span.
The next check is the cheapest one that rules something out: is the Seer's seat human? Then
the logs. The honest report, if those find nothing, is "no model call was recorded for this
vote, cause not determined", not "the cache did it".
</details>

---

# Part 4 — Design choices

**Where do the records live?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| A trace store only | Search and a viewer, with no code to write | A remote dependency that can lose or refuse data | No |
| Local records only (database, files) | Under my control, and joined to the game's own data | I build the tools to read them | No |
| Both, with one named as the record of truth for each question | Each covers the other's blind spots; a disagreement is a signal | Two things to keep in step | Yes. Events and usage in Postgres are the record; the trace is the detail |

**When is the prompt saved?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| With every call | Complete, and survives a crash up to the last batch that was sent | Large: each prompt repeats the conversation so far | The trace does this |
| Once at the end of the game | One compact, compressed row | Lost if the process dies first | The prompt capture does this |

**When is the tracing client created?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| When its module is imported: `client = get_client()` at the top level of a file | Nothing to call; any file imports the client | Import order decides when the client reads its settings. Settings loaded later are ignored | Until 2026-11-16 |
| By a call at start-up, with settings passed as arguments | The moment is written in one place, after the settings are loaded | Each entry point has to make the call | Yes: the server and the command-line game |
| On first use | Any script works with no start-up call | The moment is written nowhere; a wrong key shows at the first span, not at start-up | Yes, as the fallback for one-off scripts and tests |

**Detail: my first setup created the client at import, and that was a mistake.** The facts
behind it:

```text
1. The Langfuse client reads its keys from environment variables once, when it is created.
2. A file's top-level code runs when the file is first imported.
3. An entry point's imports run before its own code, so before its load_dotenv().
4. A client created without keys does not raise. It is disabled and drops every span.
```

Together: a game runs normally and leaves no trace, with no error. `Agents/tracing.py` had
`langfuse = get_client()` at the top level, and three workarounds grew around it:

| Workaround | What it made up for |
|---|---|
| The tracing module called `load_dotenv()` itself | The client was created before the entry point had loaded `.env` |
| The commit id was written into `os.environ` just before the client was created | A client created with no arguments can only be configured through the environment |
| The test suite sets `LANGFUSE_TRACING_ENABLED` before the module is imported | The same: the only moment to configure the client was before the import |

Each one worked. Each also needed a comment about import order, which is the sign that the
order was not written anywhere in the code.

Since 2026-11-16 importing the module creates nothing:

```python
init_tracing()     # builds the client once; the release is passed as an argument
get_langfuse()     # returns it; builds it on first use if no entry point called init_tracing()
```

The server calls `init_tracing()` in its lifespan and the command-line game calls it in
`main()`, both after their settings are loaded. The database engine in `server/db.py` was
already built this way (created in the lifespan, with its URL passed in), and it never needed a
comment about import order.

One trap is left, and the code guards it. The first Langfuse object created in a process fixes
the release for every later one, and the LangChain callback creates a default client if none
exists. A callback created first would leave every trace with no release. So
`create_langfuse_handler()` builds my client before the callback (run both orders on
2026-11-16 against the SDK: callback first gives release `None`, client first gives the
release that was passed in).

**The rule I take from it:** an object that reads its configuration once is created by a call
at start-up, never as a side effect of an import.

---

# Part 5 — Review

## In 30 seconds

Observability is answering questions about a run from the records it left. Logs give detail
about a moment, metrics give trends, and a trace gives one request as a tree of timed steps,
which for a model call includes the prompt and the reply. Records are only useful together if
they share an id. An empty record proves nothing until I know the code that writes it ran, so
independent records that disagree are the best clue. Token counts are stored and priced when
read, so a corrected price corrects the history. Recording has costs: it must never break
the work, and what is collected has to be decided on purpose.

## My Werewolf server in one paragraph

A hosted game leaves a Langfuse trace (one per run of the game's task, in a session named by
the game id, with a named span per decision), an event log in Postgres written after every
chunk, a usage count per model per hour, a compressed prompt capture written at the end, error
reports from the server and the browser with private fields excluded, and plain-text logs. The
game id joins them all; a single turn is found by player, day, round and phase. The usage count
is the only aggregate: nothing counts rescues or fallbacks, nothing measures the server while
it runs, and nothing notices a stuck game or raises an alert. The
clearest diagnosis so far came from three of these records disagreeing about one turn.

## Problems

Each is answered from memory first; my answers are in Appendix A.

**A. Transfer.** An agent gave a customer a wrong answer yesterday. There are traces, server
logs and the database. For each of "what did the model see?", "what did the user see?" and "was
a tool called?", which record answers it, and what follows if that record is missing?

**B. My system.** Name the records a hosted game leaves, when each is written, and which
survive the process dying mid-game.

**C. Evidence.** "Error reports can never contain a key" appears in a draft. What does the code
establish, and what is the accurate wording?

**D. The sharp question.** What does a trace establish about a failed model call that a log line
does not, and what can neither establish?

**E. Cost.** Why store token counts and not a cost? And why is it wrong to price last month's
calls at today's rate?

---

# Appendix A — Answers to the problems

**A.** *What the model saw:* the model call's span, if prompts are captured. If the span is
missing, three things are possible: no model was called, the call was made by code that is not
traced, or the span was lost on the way to the store. The provider's billing separates the first
from the other two; nothing in my own records separates the last two. *What the user saw:* the
application's own record of what it sent (a database row or an event log), not the trace,
because the reply can be changed after the model returns. That record shows what was sent, not
what the user's screen showed. *Was a tool called:* a child span of the model call. If it is
missing, the same three possibilities apply, and the tool's own logs are the second record.

**B.** The trace (sent in batches, flushed at the end; unsent spans are lost). The events (after
every chunk; kept up to the last chunk saved). The usage count (when a chunk arrives and 30
seconds have passed, and at the end; usually the last 30 seconds or less is lost). The prompt
capture (once at the end; nothing if the game dies, partial after a restart). Error reports (on
a failure; not sent if the process is killed). Logs (as things happen; written lines survive,
retention not established).

**C.** Established: request bodies, headers, cookies, stack-frame variables and model inputs and
outputs are not collected; four named private fields are replaced at any depth; a player's key
is removed from every string in a game-failure report; three tests pin this (named, not run).
Not established: that no other path can carry a key. Accurate wording: "error reports exclude
request data and model text, and scrub known key fields and the game's keys."

**D.** A trace establishes where in the request the failure happened, what the call was given,
how long it took, and what came before it. A log line establishes that one thing happened at
one time. Neither establishes why the model produced what it did, or that the output was
correct. Neither establishes anything about a step that never reached the recording code.

**E.** Counts are what was measured; a cost is a count times a price, and the price is the part
that gets corrected. With counts stored, a wrong rate or a missed discount can be fixed and
every past figure follows. But a rate that really changed applies only from its date, so each
count is priced at the rate in force when its calls were made. My server keeps dated prices
and hourly counts for that reason.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named; not
run), **inferred** (reasoned from code that was read), **doc** (a written record, not re-read in
the code). Read against the code on 2026-11-14. Paths are from the repository root.*

**Tracing (3.2, 3.3)**

- Self-hosted Langfuse, SDK `langfuse==3.14.6`; one client per process, built by
  `init_tracing()` (the server's lifespan, `Agents/main.py`::`main`) or on first use by
  `get_langfuse()`, never at import (changed 2026-11-16, Part 4); a LangChain `CallbackHandler`
  per run, `flush()`: **code** [`Agents/tracing.py`](../../../Agents/tracing.py), `server/app.py`::`lifespan`;
  **test** `tests/engine/test_tracing_setup.py` (four tests, run 2026-11-16)
- One trace per run of the game's task; root span `werewolf-game`, trace name `werewolf_game`,
  session id the game id; metadata `game_id`, `model`, `byok`, `recovered`; output `running`,
  then `success`, `interrupted` or `error`: **code** [`server/game/game_session.py`](../../../server/game/game_session.py)::`_run`;
  **test** `tests/server/test_game_session.py`::`test_server_session_opens_one_named_trace_in_the_games_session`
- Span names: **code** [`Agents/observability/span_names.py`](../../../Agents/observability/span_names.py),
  `Agents/turn/pipeline.py`, `Agents/nodes/orchestrator.py`, `Agents/nodes/night/resolution.py`,
  `Agents/nodes/day/flow.py`
- Draft preview is its own trace; a draft from notes has only the usage meter: **code**
  `game_session.py`::`_preview_line`, `_draft`
- Direct Anthropic SDK calls logged by `_trace`, which never raises: **code**
  `Agents/llm_factory/providers/anthropic.py`
- No tags and no run fingerprint on a server trace; the CLI attaches both a fingerprint and
  scores: **code** `Agents/main.py`, `Agents/config/langgraph.py`::`build_runnable_config`
- Hosted games trace: the Langfuse variables are defined for production and the server is on
  the Langfuse network: **code** `docker-compose.yml` (variable names checked, values not read)
- The release is "unknown" on hosted traces: **checked** in the trace store on 2026-11-16 (14 of
  14 hosted traces among the latest 30); cause **inferred** from the Dockerfile copying no `.git`
  and `Agents/run_fingerprint.py`::`git_revision`
- `flush()` is a synchronous call made from an async task: **inferred**

**Prompt captures (3.2)**

- What an entry holds (`player_id`, `player_role`, `output_key`, `day`, `round`, `prompt_input`,
  and the reads); per game through a context variable: **code** `Agents/turn/eval.py`; **test**
  `tests/server/test_leak_audit.py`::`test_concurrent_served_games_each_save_only_their_own_prompts`
- gzip of JSON; written once at game over with a 60-second limit; a failed save does not fail
  the game: **code** [`server/storage/prompt_captures.py`](../../../server/storage/prompt_captures.py),
  `game_session.py`::`_save_capture`; **test** `test_a_capture_round_trips_through_its_compressed_form`,
  `test_a_capture_that_cannot_be_saved_never_fails_the_game`
- Marked partial once a game resumes after a restart: **code** `game_session.py`

**Usage and cost (3.2)**

- Fields `calls`, `failed`, `input`, `cached`, `written`, `output`, `reasoning`, `seconds`, per
  model per UTC hour; a failed call adds only `failed`: **code** [`server/game/usage.py`](../../../server/game/usage.py)
- Saved to `games.usage` from `_persist_tail`, which runs after a chunk: when the count has
  changed and 30 seconds have passed since the last save, or the game is over. A failed save is
  retried at the next chunk. So the 30 seconds is a throttle, not a guaranteed interval. Reloaded
  on recovery; cost computed when read, from a dated price table (`Price(since, ...)`,
  `price_at(model, at)` in [`Agents/llm_factory/pricing.py`](../../../Agents/llm_factory/pricing.py);
  the `model_prices` table has a `since` column): **code** `game_session.py`, `usage.py`::`game_cost`; **test**
  `tests/server/test_usage.py` (five tests, among them
  `test_usage_is_saved_at_most_every_30_seconds_and_always_at_the_end`)

**Error reporting and logs (3.5)**

- Server: off without `SENTRY_DSN`; data collection off; `_drop_private`; `report_game_failure`
  tags `game_id`, `model`, `byok`, `stage` and is skipped for a rejected provider key; log lines
  become breadcrumbs, not events (`LoggingIntegration(event_level=None)`): **code**
  [`server/error_reporting.py`](../../../server/error_reporting.py)
- Frontend: `@sentry/browser`; off without `NEXT_PUBLIC_SENTRY_DSN`; input breadcrumbs dropped;
  `global-error.tsx` sends the stage context: **code**
  [`frontend/src/instrumentation-client.ts`](../../../frontend/src/instrumentation-client.ts),
  `frontend/src/app/global-error.tsx`, `frontend/src/stage/diagnostics.ts`

**Error types (3.5a)** *(read against the code on 2026-11-16; the named tests were run that day)*

- Ten own error types in `Agents/` and `server/`: **code**, a search for classes that derive from
  an exception type
- `KeyRefused` raised by the key check and answered as 422; a refused backup key says it was
  the backup: **code** `server/game/key_check.py`, `server/routes/games.py`, `server/routes/rooms.py`,
  `server/game/live_game_registry.py`; **test** `tests/server/test_http_api.py`::`test_a_refused_key_opens_no_game_and_no_room`,
  `test_a_refused_backup_key_opens_nothing_and_says_it_was_the_backup`
- A refused key on the primary ends the game, and on the rescue it does not; the three kinds
  of failure are told apart: **code** `Agents/turn/agent_player.py`::`_generate`,
  `Agents/llm_factory/embeddings.py`::`is_key_rejected_error`; **test** `tests/engine/test_model_fallback.py`::`test_a_refused_key_on_the_primary_ends_the_game`,
  `test_a_refused_rescue_key_falls_to_the_typed_fallback`, `test_key_refusals_are_told_apart_from_bad_requests_and_stalls`
- `ProviderKeyRejected` is shown in its own words and not sent to Sentry; other errors are:
  **code** `server/game/game_session.py`::`_run`
- `ModelNeedsKey` and `HouseClosed` answered as 422 and 402: **code** `server/routes/_shared.py`::`authorize_model`
- `HumanTurnContractError` answered as 422, and asked again on the command line: **code**
  `server/routes/games.py`::`submit_turn`, `Agents/driver/hitl_loop.py`
- Replay errors answered as 404, 500 and 503: **code** `server/routes/replays.py`; **test**
  `tests/server/test_replays.py`::`test_replays_answer_503_when_unconfigured`
- `TranslationError` is raised for an unknown chunk and caught by nothing by name: **code**
  `server/game/translate.py`, `game_session.py`::`_on_chunk` (called inside `_run`'s `try`);
  **test** `tests/server/test_translator.py`::`test_unknown_node_raises_not_skips`
- `Contradiction` is raised and caught inside the solver: **code** `Agents/deduction/candidates/solver.py`
- A stored game's refused key is recognised by a fixed phrase: **code** `server/routes/_shared.py`::`error_kind`;
  **test** `tests/server/test_http_api.py`::`test_a_game_whose_key_was_refused_says_so_in_its_status`
- One `failed` count per model per hour, not by kind: **code** `server/game/usage.py`
- Logs: plain text to stderr; the game id is written into server lines by hand; engine lines
  have none: **code** `server/app.py`::`_configure_logging`, `Agents/turn/agent_player.py`
- Key redaction in logs: **code** `game_session.py`::`_redact`; **test**
  `test_a_failure_after_game_over_never_logs_the_key`

**Events, cases, health (3.2, 3.6)**

- `events`: `game_id`, `seq`, `payload`; no time column; a pass carries
  `pass_reason="generation_failed"`: **code** `server/database_models/game.py`, `server/schemas/events.py`
- `freeze_case` stamps trace and span ids; batch runs write a file; a served game's cases are
  not persisted: **code** `Agents/observability/case_sink.py`, `scripts/run_batch.py`
- `/health` returns "healthy" unconditionally; no metrics endpoint: **code** `server/routes/system.py`

**Incidents on record**

- 2026-10-17, the cross-game cache hit (game `51226f24`), fixed 2026-10-26; spans dropped on a
  full disk in July: **doc** `evidence/tracing/report.md`
- 2026-08-24, the empty trace that was a human's turn: **doc**
  `frontend/docs/server_encountered_challenges.md` section 7

**Not established**

- What the Langfuse SDK does when the store is unreachable, and how long `flush()` can block.
- Whether a timed-out attempt inside a call appears as its own span, and whether it adds to the
  usage count's `failed`.
- Whether any direct Anthropic SDK call runs inside a served game. One would be missing from
  the usage count.
- Langfuse's retention and disk limits, and whether production logs are rotated or kept.
- Whether the frontend reports errors beyond render crashes and the SDK's default handlers.

**Reading** (titles only; no links, because I have not checked the addresses)

- OpenTelemetry's documentation, "Observability primer" and "Traces": the general terms of 1.1
  and 1.2.
- Langfuse's documentation on tracing and sessions: the trace store as this project uses it.
