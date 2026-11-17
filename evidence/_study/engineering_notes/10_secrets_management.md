# U10. Secrets: a key's whole lifetime in a model application

**Reading time:** about 25 minutes for Parts 1 to 3 (estimate); Part 5, 5 minutes · **Builds on:** U8 (what gets recorded, and what must not be) · **Related:** U7 (who may read which record), U11 (what a prompt holds) · **Feeds write-up chapter:** 7

**The question:** a person hands my application their own model API key. Between the moment
they paste it and the moment the game ends, where can it end up, and what stops it going there?

**First answer, before reading on:** where does my server keep a player’s key, and what is
the cost of that choice? A rough answer is enough; Part 5 is the stopping check.

U8 ended on what must never be recorded. This note follows one secret from end to end, and
then lists the server's own.

**Reading path.** Part 1 is the idea: a lifetime with five stages, and the list of places a
secret can leak to. Part 3 is my system and its gaps. Part 4 is two design choices. Part 5 is
the summary. This note is short on purpose.

**Enough for this pass (2026-11-16).** Explain my system without notes: what it does, why, one
trade-off and one gap. Read Parts 1, 3 and 5; Parts 2 and 4 answer follow-up questions, and
Appendix B holds the evidence. The [syllabus](../../../writeup/_planning/ch7_ch8_syllabus.md#u10-secrets-management-in-llm-applications-60-min--categories-1-and-2--explain)
keeps the deeper scope for later; completing it is not required for this pass.

**Core and detail.** The core is three ideas: a secret has a lifetime and each stage has its
own question (1.2), a secret leaks through the places text is written (1.3), and a key has to
be checked twice: that it works, and that it is the one being used (1.4).

## The whole idea

```text
receive  →  hold  →  use  →  drop                (replace or revoke when needed)
              │        │
              │        └─ sent to exactly one company: the one it belongs to
              └─ held only as long as the work needs it; persistence is a choice

At every stage the same question: where is text written from here?
   logs · traces · error reports · the database · an exception's message · a URL
```

A secret is a value that lets its holder act as someone else. A model API key lets its holder
spend the owner's money. So handling one is two jobs: keep it out of every place where text is
written, and make sure it pays only for what its owner agreed to.

| Concept | The question it answers |
|---|---|
| The lifetime | At each stage, what is the least I can do with the secret? |
| The sinks | Which places could it be written to, and what guards each one? |
| Verify and attribute | Does the key work, and is it the key each call is using? |
| My own secrets | Where do the server's keys live, and what keeps them out of git and the image? |

---

# Part 1 — Fundamentals

The example is the support assistant from U8 and U9. It calls a model provider with the
company's own key. A large customer asks to use their own key instead, so that their usage is
on their bill. That arrangement is called **bring your own key** (BYOK).

## 1.1 Two kinds of secret

| Kind | Example | Who is harmed if it leaks |
|---|---|---|
| My own | The company's provider key, the database password | Me: someone spends my money or reads my data |
| Entrusted to me | The customer's provider key | Someone else, who trusted me with it |

Both need protection; the difference is who can respond. The service can replace its own key.
For a customer's key, it usually needs the owner to revoke it at the provider and supply a
replacement. Deleting the service's copy does not revoke a stolen copy.

## 1.2 The lifetime

| Stage | The question | A bounded design |
|---|---|---|
| Receive | How does it reach the server? | In a request body over HTTPS. Never in a URL, because URLs are written to access logs and browser history |
| Hold | Where does it live, and for how long? | In memory, for the length of the work. Storing it is a decision with a cost (Part 4) |
| Use: where it is sent | Which company's servers may receive it? | Only the company that issued it. An application often calls several providers, and a key attached to the wrong request has been handed to a company with no business seeing it |
| Use: what it pays for | Which work may be charged to it? | Only the work its owner asked for. Never another customer's work, and never a background job of mine |
| Drop | When is the last reference released? | When the work ends, including the clients that were built with it |
| Replace or revoke | What happens when access ends or a key may have leaked? | Stop using the old key and release its clients and copies. Then revoke it at the provider: the service does this for its own key. For a customer's key only the customer can, so the service's part is to tell them |

"The least I can do" is the rule at each stage: the shortest hold, the fewest calls, the
fewest copies. Releasing references is not proof that memory has been securely erased.

## 1.3 The sinks

A secret does not leak because someone prints it on purpose. It leaks because it was inside
something else that got written.

| Sink | How a key gets there |
|---|---|
| A log line | An exception from the provider is logged with its message; the object holding the key is logged whole |
| A trace | The request's settings or its error output are recorded with the span |
| An error report | The reporting tool may capture local variables, request bodies or headers, depending on its configuration |
| The database | The request that carried the key is saved as a row; a state snapshot includes the object |
| An object's printed form | `repr()` of a settings object shows every field unless told not to |
| A URL | A token passed as a query parameter is written by every server and proxy on the way |

There are two ways to scrub, and they miss different things.

| Method | How it works | What it misses |
|---|---|---|
| By known value | Replace the exact key string wherever it appears | A key that was changed on the way: cut short, encoded, or shown in part by the provider |
| By pattern | Replace anything that looks like a key (`sk-…`, a field named `api_key`) | A key in an unexpected shape or under an unexpected name. It also hides things that were not keys |

Scrubbing is the second line. The first is that the key is not in the thing being written at
all: it is not in the configuration object, not in the saved state, not in the request that
gets logged.

One place cannot be kept clean that way: the call that uses the key. The key has to be in
that request, so anything that comes back from it, such as the provider's error message, may
contain it. That is where scrubbing is needed however carefully the key was carried.

**How to know whether a key reached a sink: plant one.** Reading the code shows only the
paths someone thought to read. The direct check is a test with a planted key, often called a
canary.

```text
1. Make up a key that cannot be mistaken for anything else:  sk-CANARY-7f3a91c2
2. Run the work with it through every path, the failing ones included:
   a refused key, a call that errors midway, a crash, a restart.
3. Search every sink for that exact string:
   the log output, each database table, the saved state, the trace, the error report.
4. Any hit is a leak, and it names the path.
```

The key is fake, so the provider is replaced in the test by a stand-in: a fake object that
returns answers the test scripted, in place of the provider's client. No real call is made
and nothing leaves the machine. The key still travels the real route through my code, which
is what is being tested. For the failing paths the stand-in raises an error whose message contains the key.
That is the worst case a real provider could produce, and it is what proves the scrubbing
works.

In production the complement is a periodic search of logs and tables for key-shaped strings.

## 1.4 Verify, and attribute

**Verify.** A key can be mistyped, expired or out of credit. A cheap call before the work
starts (one word, a short time limit) turns "the conversation fails at its first reply" into
"this key was refused, and here is why".

**Attribute.** Passing that check does not show that the customer's key is the one in use.
If one code path still builds its client from the server's own key, the check passes with any
key at all, the work succeeds, and the bill goes to the wrong party. Nothing fails. This is
checked with tests that assert which key each provider’s client receives, including fallback
paths. Provider-side usage records can corroborate who paid. A successful response alone cannot.

The probe itself costs a call and only establishes access at that moment; failing on first
use avoids that extra call but discovers problems later.

**What to log when a key is refused.** The log line is built from things I control: the
provider's name, the request identifier the provider returned for that call, and an error
category from a fixed list of my own (for example `invalid_key`, `out_of_credit`,
`rate_limited`, `timeout`). It leaves out the submitted key and the provider's raw error text. That text was
written by someone else, so I do not control what is in it, and some providers put part of the
key there (3.6). A category cannot contain a key, which makes this stronger than scrubbing.

### Check

The support assistant accepts a customer's key, runs one test call that succeeds, and the
customer's conversations work all month. What does that establish about whose key paid?

<details>
<summary>Answer</summary>

Nothing, yet. A successful test call shows that some key worked for that call. It does not show
which key the client was built with. If the client took the server's key from the environment,
every step above looks the same. The evidence would be the customer's own usage page showing
the calls, or a test that builds the client for that provider and asserts the key it holds.
</details>

## 1.5 Deciding it for a new system

| Question | What the answer decides |
|---|---|
| 1. Which secrets are mine, and which are entrusted to me? | The bar for each (1.1) |
| 2. Does an entrusted secret need to outlive one piece of work? | Hold in memory, or store (Part 4) |
| 3. Where is text written in this system? | The list of sinks to guard, and a test for each |
| 4. Which calls may carry each secret? | The routing rule, and the test that asserts it |
| 5. How is each secret replaced or revoked, and by whom? | One place to change it; nothing baked into an image or committed |

---

# Part 2 — What the libraries do, and what my application does

| Responsibility | The library | My application |
|---|---|---|
| Keep a key out of a client object's printed form | The model client libraries hold it in a masked type | Keeps it out of my own objects' printed form |
| Keep request data out of error reports | Collection depends on the SDK and settings | Turns each of those off, and scrubs the key's value from what is sent (U8, 3.7) |
| Keep the key out of traces | Langfuse records what passes through it; it masks nothing unless given a masking function | Keeps the key out of configuration; error and other text paths need their own controls |
| Send the key to the right company | Sends whatever key the client was built with | Decides which client gets which key |
| Load the server's own secrets | `pydantic-settings` reads them from the environment | Decides which file supplies them and keeps that file out of git |

---

# Part 3 — My Werewolf system: a player's key, and the server's own

A visitor can play on the house's keys, within a daily limit, or bring their own key for one of
the model companies on the menu.

## 3.1 The player's key, start to finish

```text
Browser   A password field. Kept in the page's memory.
          Saved in the browser's local storage only if the player ticks "remember on this
          device" (off by default), one slot per company, as plain text.
   │
   │  POST /games (or /rooms), in the JSON body, over HTTPS. Never in a URL.
   ▼
Server    1. Probe: one call, "Reply with the single word OK", 20-second limit.
             A refusal goes back as a 422 with the provider's reason.
          2. Held in the game's session object, in memory.
          3. Set on a context variable inside the game's own task, so every model call
             in that game receives that selection. This is task scoping, not a security
             barrier against other code in the same process.
          4. Clients built with it are cached with the game, not in the process-wide cache.
   │
   ▼
Provider  Sent only to the company the game's model belongs to.
   │
   ▼
Game ends The session clears both keys and rebuilds its selection without the key
          or its clients.
```

The key rides a context variable and not the run's configuration for one reason: the
configuration is recorded by those paths. Keeping the key out closes that route into saved
records; it does not prove absence from all records, since errors and other objects can carry it.

**Code:** `server/game/key_check.py::check_key`; `server/game/game_session.py` (`_api_key`,
`_llm_selection`, `_end`); `Agents/llm_factory/chat.py` (`GameLLM`, `GAME_LLM`).

## 3.2 Which recording paths are guarded

Each row is a place where the server saves something about a game. The key was part of that
game, so the question for each place is what gets saved there in its place, and how I know.

| Where something is saved | What is saved about the key | How I know |
|---|---|---|
| The game's row in the database | Only whether the game used a player's key: a true-or-false column, `byok`. Recovery needs that fact after a restart (3.4) | By reading the code that writes the row |
| The trace sent to Langfuse | The same true or false, in the trace's metadata | By reading the code that builds the metadata |
| The run's configuration, which is copied into checkpoints and run records | Nothing. The key is never put in it; it travels on the context variable | By the design |
| The error text and traceback of a game that died | The text with each key replaced by `***` | A test, for the key and for the backup key |
| The crash report sent to Sentry | Bodies, headers and local variables are off; the key's value is replaced | A test |
| The log of a failure after the game is over | The traceback with the key replaced | A test |

Three of these rest on reading the code, not on a test. No test asserts that the key is absent
from the database, the events or the trace. A planted-key test (1.3) would settle those three.

## 3.3 Which company can receive it

```text
key for the game's model   →  sent only when the call's model is from the same company
backup key                 →  sent only when the rescue model is from its company
any other call             →  the server's own credentials
```

A game also makes calls outside its main model, such as the rescue model when a turn stalls.
The rule reads the model's name, takes the company from its prefix, and hands over the
player's key only on a match. So a player's Anthropic key is never sent to another provider.

The player cannot redirect it either. Each provider's address is a constant in the code, and
the model must be a row in the server's catalogue. No request carries a URL.

The backup key is the player's second key, for a different company. With it, that company's
model becomes the rescue. It must be for a company other than the game model's.

This rule has tests because of the fault in 1.4, which happened here: four provider branches
built their clients from the server's environment and ignored the player's key. A player's game
would have been billed to the house, and any string passed the key check.

**Code:** `Agents/llm_factory/chat.py::_game_key_for`, `_provider_family`;
`server/game/model_catalog.py`. **Tests:** `tests/server/test_byok.py`.

## 3.4 After a restart

The key was only in memory, so a restart loses it. The game's row says `byok` is true, so
recovery rebuilds the session in a waiting state and starts nothing. A seat holder supplies the
key again through `POST /games/{id}/key`; it is probed, and the game resumes from its
checkpoint. The backup key is not asked for again.

This is the cost of not storing the key: the player has to act for the game to continue.

## 3.5 The server's own secrets

| Question | My system |
|---|---|
| Which are they? | The database address, four model-provider keys, the Langfuse keys, the Sentry address, and the path to the Google credentials file |
| How are they loaded? | `pydantic-settings` reads the environment; in production Docker Compose supplies it from one file, `.env.production` |
| Are they in git? | No. `.env`, `.env.bak` and `.env.production` are ignored. The two tracked frontend files hold only the public API address |
| Are they in the image? | No. The Dockerfile copies the code folders only; the Google credentials file is mounted read-only at run time |
| What limits spending on the house's keys? | A daily cap on house-funded games, 10 by default. A player who brings a key is not counted |

The admin page needs a token that is not set in production, so it answers "not found".

## 3.6 Known limitations

| Gap | Consequence | Possible direction |
|---|---|---|
| 1. A failed model call logs the provider's exception as it is | Whatever the provider says about the key reaches the container's log. Today none of the five echoes a refused key in full; two show part of it (below). Only a dead game's text is redacted | Log the error's category and the request identifier in place of the exception's text (1.4). The code already sorts a failed call into three kinds before logging: the key was rejected (a refused key and an empty account together), the provider stalled (rate limit, timeout, server error), or anything else. Each log line names its kind in a fixed phrase and then prints the exception's text |
| 2. Redaction is by exact value only | A key shown in part by a provider passes. OpenAI and DeepSeek do show part | Add a pattern for the known key shapes |
| 3. The host's key for a room travels in the URL | Access logs on the way may hold it. It controls one room for its life, not money | Move it to a header or the body |
| 4. Seat tokens are stored as plain text, in the database and in the browser | Anyone who can read the table can act as a seat in a live game | Store a hash; accepted today because a token is worth one seat for one day |
| 5. The files with secrets are sent to the image build | There is no `.dockerignore`, so they are in the build context, though not copied into the image | Add the file |
| 6. Nothing scans for a committed secret, and no rotation procedure is written | A key committed by mistake would be found by eye or not at all | A scanning hook; a short rotation page |
| 7. A player with no backup key may have a rescue on the house | When the rescue model is from another company, the call uses the server's credentials. Not checked against the catalogue | Check which rescues cross companies, then decide |
| 8. A player cannot be told that their key may have leaked | There are no accounts and no contact details, so only the player can revoke the key, and only if they think to | Advise, where the key is entered, a key made for this purpose with a spending limit, revoked after playing |

**What a provider's refusal says about the key.** A stand-in in a test shows that my code
scrubs a key if the provider echoes it. It cannot show whether a real provider does. That is
a separate question, answered only by a real call, so I sent a made-up key to one model of
each company on the menu and searched the error for it.

| Company | The refused key in the error text |
|---|---|
| Anthropic | Not shown |
| Google | Not shown |
| OpenRouter | Not shown |
| OpenAI | Shown in part: the first eight characters and the last four, the rest as `*` |
| DeepSeek | Shown in part: the last four characters |

So no provider echoed the whole key, and the unredacted log line (gap 1) would hold at most
those fragments. A provider can change its wording at any time, so the scrubbing is still
written for the worst case, and this check is worth repeating when a provider is added.

---

# Part 4 — Design choices

**Where does an entrusted key live?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| In memory, for one game | No intentional server-side key storage at rest; fewer retained copies | A restart loses it and the player must supply it again | Yes |
| Stored, encrypted | Survives a restart; the player types it once | A stored secret needs an encryption key of its own, a deletion path, and an answer for a breach | No |

**How is a key kept out of what is written?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Keep it out of the written object | Closes that object’s route to each sink | Needs a separate channel to carry the key | Yes: the context variable |
| Scrub by exact value | Exact, no false matches | Misses a changed form of the key | Yes, for error text and reports |
| Scrub by pattern | Catches keys nobody registered | False matches; misses new shapes | No |

**How does a value reach the code that uses it?** *(Detail)*

The key has to travel from the session that holds it to the function, many calls deeper, that
builds a provider's client. There are three ways for a value to make that trip.

```python
# Explicit: the value is handed in.
def call_model(key): ...

# Global: one shared value, read where it is needed.
current_key = ""
def call_model(): use(current_key)

# Ambient: read where it is needed, like a global, but each task has its own value.
current_key = ContextVar("current_key", default="")
def call_model(): use(current_key.get())
```

| Style | Visible where it is used? | A separate value for each game running at once? |
|---|---|---|
| Explicit | Yes, in the function's parameters | Yes |
| Global | No | No: one value for the whole process |
| Ambient | No | Yes |

**The ambient style is a context variable.** It is declared once at module level, which
Python requires, so in the source it looks like a global. The value is not global: every
asyncio task carries its own table of context-variable values. `set` writes into the table of
the task that is running, and `get` reads from it. A new task copies its parent's table. A new
thread does not, so whatever starts the thread must copy it; LangGraph does this for the
threads that run its nodes.

```python
token = current_key.set("abc")   # write, for the current task only
current_key.get()                # read
current_key.reset(token)         # put the previous value back
```

It is part of Python's standard library (`contextvars`). The older tool was thread-local
storage, one value per thread, which stopped being enough once many tasks shared one thread.

**Why a plain global cannot carry a per-game value.** Two games run at once; each stores its
key both ways, then a function deeper in reads both after a short wait.

```text
game A: global sees 'key-B', context variable sees 'key-A'
game B: global sees 'key-B', context variable sees 'key-B'
```

Game B overwrote the global while game A was waiting, so A read B's key. The context variable
kept them apart.

**Which to use.** The first question is whether there is one value for the process or one per
piece of work. The second is whether the code depends on the value to do its job.

| What is carried | Style | Why |
|---|---|---|
| One shared resource for the process: a connection pool, a logger, a tracing client | Global, behind one accessor | Every caller is meant to share it |
| Something the code needs to do its job, different per piece of work: a client, a repository | Explicit | The dependency shows in the signature, and a test passes a fake as an argument |
| Side information that every layer may want and none should have to pass on: the current trace span, a request id for log lines | Ambient | The code is still correct without it, and threading it through every call would touch everything |

The test for the last row is "would the program still be correct without this value?". A log
line without a request id is a working program. A model call without its client is not.

**In my system.**

| Value | Style | Fits the table? |
|---|---|---|
| The Langfuse client | Global, behind `get_langfuse()` | Yes: one for the process |
| The current span, inside the tracing library | Ambient | Yes: side information |
| The Langfuse callback, the metrics object, the evaluation sink | Explicit: the run's configuration and LangGraph's `context` | Yes |
| The prompt capture (`TURN_CAPTURE`) | Ambient | Borderline: a recording, but the leak audit depends on it |
| The model selection, the key and the clients (`GAME_LLM`) | Ambient | No. It is a core dependency, and nothing in `get_llm()` shows that its result depends on a value set in the session's task |

The last row is the one I would do differently. The context variable was correct for keeping
games apart, and it kept the key out of the saved configuration. The cost is the hidden
dependency, and tests that must set and reset the variable around each case. The explicit
form would pass one object, the models for this game, through LangGraph's `context`. It cannot
be fixed in a constructor, because the server compiles the graph once and shares it across
games, so a per-game value has to arrive with each call. The reason it was not built that way
is the order of the work: the engine came first, for batch runs, with accessors that read the
environment, and a context variable added a player's key without changing every model call.

---

# Part 5 — Review

## In 30 seconds

A secret has a lifetime: receive, hold, use, drop, and replace or revoke when needed. At each stage
the aim is the least: the shortest hold, the fewest calls, the fewest copies. Releasing references is not proof that memory has been securely erased. It leaks through
the places text is written: logs, traces, error reports, the database, a printed object, a
URL. The first defence is that the key is never in the thing being written; scrubbing is the
second. A key is checked twice: that it works, and that it is the key each call is built
with. Routing tests and provider usage records address the second question; a successful
call does not, because nothing fails when the wrong party pays.

## My Werewolf system in one paragraph

A player's key arrives in a request body, is probed with one call, and is held in memory on a
context variable inside that game's task. It is kept out of the run's configuration, closing
that route into saved records; the games table records BYOK as true or false. This does not
establish absence from every log or trace. It is sent only to the company the model belongs to, the rule a past fault made me
test. It is cleared when the game ends, and a restart means the player supplies it again. The
server's own keys come from one ignored file through the environment. The weak points: a
failed call's log line is not redacted, redaction matches the exact value only, the room host's
key travels in the URL, and nothing scans for a committed secret.

## Stopping check

In two minutes, without the note: explain how the key reaches a model call, why it travels
outside configuration, what a restart costs, and one recording path that is not guarded.
If those connect, this pass is done. The two problems below are optional follow-ups.

## Problems

**Problem A.** A document-summary service lets each user connect their own cloud-storage
token so that it can read their files overnight, while they are away. It must continue after
a restart without asking them again. Which stage differs from my system, and what does that force?

**Problem B.** A draft sentence for the write-up: "The player's key is never logged or
stored." What is supported, what is not, and what is the accurate wording?

---

# Appendix A — Answers to the problems

**Problem A.** The hold. The restart requirement means some credential must be durably
available, either the token or a credential that can obtain a new one. Overnight work alone
could use memory if losing it on restart were acceptable. Durable storage adds:
encryption at rest with a key kept elsewhere, a way for the user to revoke and delete it, a
scope limited to reading, and a plan for a breach. A restart can no longer be answered by
asking the user again.

**Problem B.** Supported: the games table stores only true or false; the key is not in the
run's configuration; a dead game's error and traceback, and the Sentry report, are redacted,
each with a test. Not supported: "never logged", since a failed call's log line carries the
provider's exception without redaction (gap 1), and no test asserts the key's absence from the
database, the events or the trace. Also the browser stores it when the player asks. Accurate
wording: "The server holds a player’s key in memory rather than deliberately persisting it
in the game row or run configuration. Named tests cover redaction in game-failure text and
Sentry reports. Model-call exception logs remain an unguarded path if a provider echoes a key;
absence from every stored record has not been demonstrated."

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named, and
run on 2026-11-16), **doc** (a written record, not re-read in the code). Read against the code
on 2026-11-16. Paths are from the repository root.*

**The player's key (3.1, 3.2)**

- The password field and the opt-in local storage, one slot per company: **code**
  `frontend/src/app/(site)/_components/ticket/KeyRow.tsx`, `frontend/src/hooks/useRememberedKey.ts`,
  `frontend/src/lib/storage.ts`
- The key in the JSON body of `POST /games`, `POST /rooms` and `POST /games/{id}/key`: **code**
  `frontend/src/lib/api.ts`, `server/schemas/requests.py` (`NewSoloGame`, `BackupKey`, `FundGame`)
- The probe, its 20-second limit, and the key replaced in the refusal text: **code**
  `server/game/key_check.py::check_key`
- Held on the session and set on the context variable in the game's task: **code**
  `server/game/game_session.py`; **test** `tests/server/test_byok.py`
  (`test_session_sets_the_selection_inside_its_own_task_only`)
- Clients cached with the game: **test** `test_a_players_key_is_cached_with_its_game_not_the_process`
- Cleared at the end: **code** `game_session.py::_end`; **test** `tests/server/test_game_session.py`
- The games row and the trace metadata hold a true-or-false value: **code**
  `server/database_models/game.py`, `game_session.py`
- Redaction of a dead game's text: **code** `game_session.py::_redact`; **test**
  `test_dead_game_error_never_echoes_the_key`, `test_dead_game_error_never_echoes_the_backup_key`
- The Sentry report: **code** `server/error_reporting.py`; **test**
  `tests/server/test_error_reporting.py`
- No test for absence from the database, events or trace: **code**, a search of `tests/server/`

**Routing (3.3)**

- The company rule and the backup rule: **code** `Agents/llm_factory/chat.py::_game_key_for`;
  **test** `test_off_family_models_never_receive_the_game_key`,
  `test_the_backup_key_goes_to_the_rescues_company_only`
- Provider addresses are constants; the model must be a catalogue row: **code**
  `Agents/llm_factory/providers/openai_compat.py`, `server/house.py`
- The four branches that used the server's key: **doc** commit `8cd83ba7`

**Restart (3.4)**

- Recovery waits for the key; the key endpoint: **code** `server/game/live_game_registry.py`,
  `server/routes/games.py`; **test** `tests/server/test_durability.py`

**The server's secrets (3.5)**

- Variable names in `.env.production` (names only were read); `env_file` in
  `docker-compose.yml`; ignored files in `.gitignore`; what the `Dockerfile` copies: **code**
- The daily cap: **code** `server/config.py` (`HOUSE_GAMES_PER_DAY`), `server/house.py`

**The gaps (3.6)**

- Gap 1: **code** `Agents/turn/agent_player.py` (the three log lines in the model-call wrapper)
- The three styles (Part 4): the two-games output is a **run** on 2026-11-16 of a 20-line script,
  two tasks under `asyncio.gather`; the graph compiled once and shared: **code**
  `server/graph_runtime.py`; nodes reading LangGraph's context: **code** `Agents/graphs/parent.py`,
  `Agents/nodes/orchestrator.py`; the two context variables: **code** `Agents/llm_factory/chat.py`
  (`GAME_LLM`), `Agents/turn/eval.py` (`TURN_CAPTURE`)
- The model client libraries hold the key in a masked type (Part 2): **run** on 2026-11-16. A
  client was built for each of the five companies with a made-up key; the key field is a
  `SecretStr` in each, and the key is absent from the client's printed form, its field dump
  and its LangChain serialisation. My own `GameLLM` hides both keys from its printed form:
  **code** `Agents/llm_factory/chat.py`; **test**
  `test_neither_key_shows_in_the_selections_printed_form`
- Gap 3: **code** `frontend/src/lib/api.ts` (`host_key` as a query parameter)
- Gap 4: **code** `server/routes/games.py`, `server/database_models/game.py`
- Gaps 5 and 6: **code**, searches for `.dockerignore`, CI workflows, hooks and "rotat"
- Gap 7: not checked against the catalogue
- What a refusal says about the key: **run** on 2026-11-16, a made-up key sent once to one
  model of each company on the menu, the error text searched for it (result under 3.6). One
  kind of error only; other errors were not tried
- Not checked: what the production
  access logs contain

**Further reading, only when needed:** [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html),
sections 2.5 (memory) and 2.7 (lifecycle), for release versus erasure and replacement versus revocation.
