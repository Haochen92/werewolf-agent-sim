# U10. Secrets: a key's whole lifetime in a model application

**Reading time:** about 25 minutes for Parts 1 to 3 (estimate); Part 5, 5 minutes · **Builds on:** U8 (what gets recorded, and what must not be) · **Related:** U7 (who may read which record), U11 (what a prompt holds) · **Feeds write-up chapter:** 7

**The question:** a person hands my application their own model API key. Between the moment
they paste it and the moment the game ends, where can it end up, and what stops it going there?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

U8 ended on what must never be recorded. This note follows one secret from end to end, and
then lists the server's own.

**Reading path.** Part 1 is the idea: a lifetime with five stages, and the list of places a
secret can leak to. Part 3 is my system and its gaps. Part 4 is two design choices. Part 5 is
the summary. This note is short on purpose.

**Core and detail.** The core is three ideas: a secret has a lifetime and each stage has its
own question (1.2), a secret leaks through the places text is written (1.3), and a key has to
be checked twice: that it works, and that it is the one being used (1.4).

## The whole idea

```text
receive  →  hold  →  use  →  drop                (and, for my own keys: rotate)
              │        │
              │        └─ sent to exactly one company: the one it belongs to
              └─ in memory only, for as long as the work needs it

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

The second kind sets the higher bar. I can rotate my own key the moment I suspect a leak. I
cannot rotate someone else's, and I may not even learn that it leaked.

## 1.2 The lifetime

| Stage | The question | The safest answer |
|---|---|---|
| Receive | How does it reach the server? | In a request body over HTTPS. Never in a URL, because URLs are written to access logs and browser history |
| Hold | Where does it live, and for how long? | In memory, for the length of the work. Storing it is a decision with a cost (Part 4) |
| Use | Which calls may carry it? | Only calls to the company it belongs to, for the work its owner asked for |
| Drop | When is the last reference released? | When the work ends, including the clients that were built with it |
| Rotate | How is it replaced? | For my own keys: a written procedure, and no place that needs a code change |

"The least I can do" is the rule at each stage: the shortest hold, the fewest calls, the
fewest copies.

## 1.3 The sinks

A secret does not leak because someone prints it on purpose. It leaks because it was inside
something else that got written.

| Sink | How a key gets there |
|---|---|
| A log line | An exception from the provider is logged with its message; the object holding the key is logged whole |
| A trace | The request's settings or its error output are recorded with the span |
| An error report | The reporting tool captures local variables, request bodies and headers by default |
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

## 1.4 Verify, and attribute

**Verify.** A key can be mistyped, expired or out of credit. A cheap call before the work
starts (one word, a short time limit) turns "the conversation fails at its first reply" into
"this key was refused, and here is why".

**Attribute.** Passing that check does not show that the customer's key is the one in use.
If one code path still builds its client from the server's own key, the check passes with any
key at all, the work succeeds, and the bill goes to the wrong party. Nothing fails. This is
found only by a test that asserts which key each provider's client was built with.

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
| 5. How does each of my own secrets get replaced? | One place to change it; nothing baked into an image or committed |

---

# Part 2 — What the libraries do, and what my application does

| Responsibility | The library | My application |
|---|---|---|
| Keep a key out of a client object's printed form | The model client libraries hold it in a masked type | Keeps it out of my own objects' printed form |
| Keep request data out of error reports | Sentry collects bodies, headers and local variables unless told not to | Turns each of those off, and scrubs the key's value from what is sent (U8, 3.7) |
| Keep the key out of traces | Langfuse records what passes through it; it masks nothing unless given a masking function | Keeps the key out of the run's configuration, so it never passes through |
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
             in that game can read it and no other game can.
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
configuration is saved into checkpoints, traces and run records. A value that is never in it
cannot be written by any of them.

**Code:** `server/game/key_check.py::check_key`; `server/game/game_session.py` (`_api_key`,
`_llm_selection`, `_end`); `Agents/llm_factory/chat.py` (`GameLLM`, `GAME_LLM`).

## 3.2 Where the key is not written

| Sink | What is written instead | Support |
|---|---|---|
| The games table | A true-or-false column, `byok` | The code that writes the row |
| The trace | `byok` as true or false in the metadata | The code that builds the metadata |
| The run's configuration and fingerprint | Nothing: the key is on the context variable | By design |
| A dead game's error text and traceback | The text with each key replaced by `***` | A test, for the key and for the backup key |
| A Sentry report | Bodies, headers and local variables are off; the key's value is scrubbed | A test |
| A failure after the game is over | The traceback with the key replaced | A test |

Three of these rest on reading the code, not on a test. No test asserts that the key is absent
from the database, the events or the trace.

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
| 1. A failed model call logs the provider's exception as it is | If a provider ever echoed the key in its error message, it would reach the container's log. Only a dead game's text is redacted | Redact in the turn's log lines too, from the same context variable |
| 2. The selection object's printed form shows the main key | The backup key is hidden from `repr()`; the main key is not. Nothing prints the object today | Mark the field the same way |
| 3. Redaction is by exact value only | A key shown in part by a provider would pass | Add a pattern for the known key shapes |
| 4. The host's key for a room travels in the URL | Access logs on the way may hold it. It controls one room for its life, not money | Move it to a header or the body |
| 5. Seat tokens are stored as plain text, in the database and in the browser | Anyone who can read the table can act as a seat in a live game | Store a hash; accepted today because a token is worth one seat for one day |
| 6. The files with secrets are sent to the image build | There is no `.dockerignore`, so they are in the build context, though not copied into the image | Add the file |
| 7. Nothing scans for a committed secret, and no rotation procedure is written | A key committed by mistake would be found by eye or not at all | A scanning hook; a short rotation page |
| 8. A player with no backup key may have a rescue on the house | When the rescue model is from another company, the call uses the server's credentials. Not checked against the catalogue | Check which rescues cross companies, then decide |

---

# Part 4 — Design choices

**Where does an entrusted key live?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| In memory, for one game | Nothing to steal from the database; nothing to rotate | A restart loses it and the player must supply it again | Yes |
| Stored, encrypted | Survives a restart; the player types it once | A stored secret needs an encryption key of its own, a deletion path, and an answer for a breach | No |

**How is a key kept out of what is written?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Keep it out of the written object | Holds for every sink at once | Needs a separate channel to carry the key | Yes: the context variable |
| Scrub by exact value | Exact, no false matches | Misses a changed form of the key | Yes, for error text and reports |
| Scrub by pattern | Catches keys nobody registered | False matches; misses new shapes | No |

---

# Part 5 — Review

## In 30 seconds

A secret has a lifetime: receive, hold, use, drop, and for my own keys rotate. At each stage
the aim is the least: the shortest hold, the fewest calls, the fewest copies. It leaks through
the places text is written: logs, traces, error reports, the database, a printed object, a
URL. The first defence is that the key is never in the thing being written; scrubbing is the
second. A key is checked twice: that it works, and that it is the key each call is built
with. The second check needs a test, because nothing fails when the wrong party pays.

## My Werewolf system in one paragraph

A player's key arrives in a request body, is probed with one call, and is held in memory on a
context variable inside that game's task. It is never in the run's configuration, so
checkpoints, traces and run records cannot contain it; the games table stores only true or
false. It is sent only to the company the model belongs to, the rule a past fault made me
test. It is cleared when the game ends, and a restart means the player supplies it again. The
server's own keys come from one ignored file through the environment. The weak points: a
failed call's log line is not redacted, redaction matches the exact value only, the room host's
key travels in the URL, and nothing scans for a committed secret.

## Problems

**Problem A.** A document-summary service lets each user connect their own cloud-storage
token so that it can read their files overnight, while they are away. Which stage of the
lifetime differs from my system, and what does that force?

**Problem B.** A draft sentence for the write-up: "The player's key is never logged or
stored." What is supported, what is not, and what is the accurate wording?

---

# Appendix A — Answers to the problems

**Problem A.** The hold. The work runs when the user is not there, so the token must outlive
the request that delivered it: it has to be stored. That forces what my system avoids:
encryption at rest with a key kept elsewhere, a way for the user to revoke and delete it, a
scope limited to reading, and a plan for a breach. A restart can no longer be answered by
asking the user again.

**Problem B.** Supported: the games table stores only true or false; the key is not in the
run's configuration; a dead game's error and traceback, and the Sentry report, are redacted,
each with a test. Not supported: "never logged", since a failed call's log line carries the
provider's exception without redaction (gap 1), and no test asserts the key's absence from the
database, the events or the trace. Also the browser stores it when the player asks. Accurate
wording: "The server holds a player's key in memory for the length of the game and never in
the run's configuration or the database. Error text and crash reports are redacted, with
tests. One log line is not, and would matter only if a provider echoed the key."

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
- Gap 2: **code** `Agents/llm_factory/chat.py` (`GameLLM.api_key` has no `repr=False`)
- Gap 4: **code** `frontend/src/lib/api.ts` (`host_key` as a query parameter)
- Gap 5: **code** `server/routes/games.py`, `server/database_models/game.py`
- Gaps 6 and 7: **code**, searches for `.dockerignore`, CI workflows, hooks and "rotat"
- Gap 8: not checked against the catalogue
- Not checked: what the provider libraries put in an exception's text; what the production
  access logs contain
