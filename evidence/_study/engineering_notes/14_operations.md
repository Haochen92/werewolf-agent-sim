# U14. Operations: releasing safely, changing settings live, limiting spend

**Reading time:** about 25 minutes for Parts 1 and 3 (estimate); Part 5, 5 minutes · **Builds on:** U1 (time and attempt limits on a call), U2 (race conditions), U10 (the server's own keys) · **Related:** U15 (capacity) · **Feeds write-up chapter:** 7

**The question:** my demo is public, and every game played on the house's keys costs me money.
What stops a bad release from breaking it? What can I change without making a release? What
stops the bill from growing while I am not watching?

**First answer, before reading on:** two or three sentences, with an example that is not from
this project.

**Suggested read.** Part 1 has the general ideas. Part 3 is how my system does each one, and
what is missing. Part 4 compares the design choices. Part 5 is the summary. Part 2 and
Appendix B are reference. This note is short on purpose.

## The core idea

Running a system safely comes down to three separate jobs:

```text
Releasing    build → check the new image → change the database → swap → smoke test
             (the previous image is kept, so the release can be undone)

Settings     read once at start-up (changing it needs a restart)
             or stored and re-read while running (changing it needs no restart)

Spending     count what has been used, from the database's own records
             → compare with the limit → refuse, and tell the caller when to come back
```

| Topic | The question it answers |
|---|---|
| Release safety | Is this the code I meant to release? Does it start? Can I undo it? Who is interrupted during the change? |
| Database changes | Can the previous version of the code still run after the database has changed? |
| Run-time settings | Which values must I be able to change quickly, without a release? |
| Spending limit | What is counted, where does the count come from, and how exact is the limit? |

---

# Part 1 — Fundamentals

The example is the support assistant from U8 to U11. It runs as one container, and each
conversation makes model calls that the company pays for.

## 1.1 Four questions for a release

A **release** is replacing the version of the software that users are running with a newer
one. Three related words: a **commit** saves a change in git, a **build** packages the code
into an image that can run, and a **deploy** puts that image on the server and starts it. Only
the deploy changes what users get. In a small system such as mine, deploying and releasing are
the same event, so this note uses "release" for the whole procedure. In larger systems they
can be separate: new code is deployed switched off, and released later by switching it on.

A release is safe when each of these four questions has an answer.

| Question | How to answer it |
|---|---|
| 1. Is this the code I meant to release? | Build the image from a clean checkout of one commit, never from a working folder that has uncommitted edits. Record the commit id inside the image |
| 2. Does it start with production's settings? | Run a check inside the new image before it receives traffic. Tests that passed on my own machine used my machine's settings, not production's |
| 3. Can I undo it? | Keep the image that was running. Undoing the release (a **rollback**) is starting that image again |
| 4. Who is interrupted during the change? | Know what a restart does to work that is in progress, and choose when to do it |

After the new version is running, a **smoke test** sends it a few real requests: does the home
page load, does the health-check address answer, does one real request work from start to
finish. It is kept short. Its purpose is to detect that the system is not serving at all. It
is not a second run of the full test suite.

These steps can be run automatically by a pipeline on every merge. This is called continuous
integration and continuous delivery (CI/CD). They can also be run by a person following a
written procedure. A pipeline guarantees that no step is skipped. A written procedure is the
minimum: without one, each release depends on what the person remembers.

## 1.2 Database changes need their own rollback plan

Code can be rolled back in seconds by starting the previous image. Data cannot. So when a
release changes the structure of the database (a **migration**), "can I undo it?" has to be
answered separately for the database.

| Kind of change | Examples | Can the previous code still run? | What a rollback needs |
|---|---|---|---|
| **Additive** (backward-compatible) | Add a new table; add a column that is allowed to be empty | Yes. The previous code never reads the new table or column | Nothing in the database. Start the previous image |
| **Destructive** | Remove or rename a column; change a column's type | No. The previous code fails on the changed structure | The database has to be changed back as well, and data may be lost |

The usual practice has three parts:

- make changes additive wherever possible;
- apply the migration before the new code starts;
- take a backup before any change that is not additive.

A migration tool keeps a record of which migrations have been applied, and can run each one
forwards or backwards.

**How deleted data is recovered.** Running a migration backwards restores the structure, not
the data that was in it. Recovering data needs one of these, and a company usually uses
several, because each covers a different kind of mistake:

| Method | How it works | What it recovers | Storage cost |
|---|---|---|---|
| **Backups** | A full copy of the database on a schedule, kept for some days | The database as it was at the time of the backup. Later writes are lost | One copy per backup kept; less with compression and incremental backups |
| **Point-in-time recovery** | A backup, plus a continuous archive of the database's change log. Restore the backup, then replay the log up to the moment before the mistake | The database at any moment in the retention period | Grows with the amount of change, not with the size of the database |
| **Soft delete** | The application sets a `deleted_at` column and never deletes the row | A row deleted by mistake | Deleted rows stay in the table |
| **History tables** | For important tables, each change writes the old version of the row to a second table | Any earlier version of a row | Grows with every change, so used selectively |
| **Expand, then contract** | Stop the code using a column first; drop the column in a much later release | Nothing needs recovering while the column still exists | None |

Two things that are not recovery. A **replica** is a live copy kept so the service survives a
machine failing; a deletion is copied to it within a second. **Data lineage** records which
source and which processing step produced a value, and is used in analytics.

How much to keep is set by two targets: the **recovery point objective** (RPO), how much
recent data may be lost, and the **recovery time objective** (RTO), how long the service may
be down during a restore. A nightly backup means an RPO of up to 24 hours. Managed databases
provide backups and point-in-time recovery as a setting.

## 1.3 Two kinds of setting

| Kind | When it is read | How it is changed | What it suits |
|---|---|---|---|
| **Deploy-time** | Once, when the process starts | Restart the process, or make a release | Addresses, credentials, anything the code is built around |
| **Run-time** | From a store such as a database, re-read every few seconds | Write the new value to the store. No restart | Limits, on/off switches, which model is the default |

To decide which kind a setting should be, ask: *would I ever need to change this quickly,
while the system is running, with no time to make a release?* A daily spending limit: yes. A
database address: no.

A run-time setting needs three things besides somewhere to be stored:

- **a short cache**, so the store is not queried on every request;
- **a default value**, used when the store has no value;
- **a controlled way to change it**, with a record of who changed it and when.

An on/off switch of this kind is often called a **feature flag**.

## 1.4 Limiting spend

A spending limit compares a count of what has been used with a maximum. Three design
decisions follow.

**Decision 1: where does the count come from?**

| Design | How it works | What goes wrong |
|---|---|---|
| A separate counter | Add one each time work starts; reset it at midnight | The counter can become wrong. A crash between doing the work and adding one loses a count. A restart loses a counter held in memory. Two servers each have their own counter |
| Count the records | Each time, ask the database how many records of that kind were created since midnight | It costs one query per check. It cannot disagree with what happened, because it is computed from the records of what happened |

The records are the **source of truth**. A count computed from them is correct after a
restart and with several servers.

**Decision 2: best-effort or exact?** Checking the count and starting the work are two
separate steps. Between them, another request can pass the same check. This is the race
condition from U2.

| Design | What happens | Cost |
|---|---|---|
| **Best-effort** | Several requests that arrive at the same moment can all pass the check and all take the last place | Simple. The limit can be exceeded by a few |
| **Reserve, then release** | A place is claimed in one atomic database operation before the work starts, and given back if the work fails | Exact. It needs a transaction or a lock, and a rule for places that were claimed and never used |

Best-effort is acceptable when exceeding the limit by a few costs little. It is not acceptable
when each unit is expensive, or when someone is deliberately trying to exceed the limit.

**Decision 3: what does a refused caller see?** The response should say why the request was
refused and when to try again.

**A daily limit is not the only limit needed.** It restricts how many pieces of work start.
Each piece of work also needs its own limits: a time limit and a retry limit on each model
call, and a maximum length for the whole piece of work.

### Check your understanding

The support assistant allows 500 free conversations a day. The count is a counter held in the
server's memory. On Tuesday the server restarts at noon. What happens to the limit, and what
is the smallest change that fixes it?

<details>
<summary>Answer</summary>

The counter is lost when the process stops, so it starts again from zero at noon. Up to 500
more conversations are allowed that afternoon, so the real limit for the day became up to
1,000.

The smallest fix is to stop keeping a counter. On each check, count that day's conversation
records in the database. The count is then correct after a restart, and correct with more
than one server. The limit is still best-effort: two requests arriving at the same moment can
both take the last place.
</details>

## 1.5 A checklist for a new system

| Question | What it establishes |
|---|---|
| 1. What are the steps of a release, and which of them are automated? | The procedure, and where a step could be skipped |
| 2. What is kept so that a release can be undone, for the code and for the data? | The previous image, additive migrations, backups |
| 3. What does a restart do to work in progress? | When a release may happen, and what a user sees |
| 4. Which settings would I need to change in a hurry? | The run-time settings, where they are stored, and who may change them |
| 5. What costs money each time it is used, and what limits it? | The spending limit, what it counts from, and the limits on each call and each job |
| 6. What runs on a schedule, and how do I know it ran? | The scheduled jobs, and a check that each one is installed |

---

# Part 2 — What the tools do, and what my application does

| Responsibility | The tool | My application |
|---|---|---|
| Package the code with its dependencies | Docker builds an image from the Dockerfile | Chooses what is copied in, and records the commit id in the image |
| Start, restart and health-check the containers | Docker Compose, from one file | Provides the health-check address; decides what a restart does to games in progress |
| Apply and record database changes | Alembic runs each migration and records which have run | Writes each migration, forwards and backwards, and decides when to apply it |
| Hold run-time settings | Postgres stores the rows | Reads them through a short cache, with default values |
| Count what was spent | No tool does this | Counts game records, and refuses new games when the limit is reached |

---

# Part 3 — How my Werewolf system does it

One host runs everything with Docker Compose: the server, the frontend and the tracing
services. The game database is a separate container that Compose does not manage. This is
deliberate: starting or rebuilding the Compose services can then never recreate the database.
A web server in front of everything (Caddy) is a separate project.

## 3.1 How a release is done

Every step is done by hand. The procedure was never written as a document of its own. It
developed over many entries in a deploy log, and the log's summary states it:

```text
1  Build the image from a clean checkout of the commit being released,
   so that uncommitted work is not included.
2  Keep the image that is currently running, tagged ":prev".
3  If the release has a migration, apply it first, from inside the new image.
4  Run a start-up check inside the new image with production's settings.
5  Swap to the new image only when no room is waiting and no game is in progress.
6  Smoke test: the site's pages, the API's health check, the model list and the replays,
   and one game or replay through the browser.
7  Write a log entry: date, containers, commit, what changed, migration, tests,
   and the checks above.
```

**Steps 3 and 4 both use a temporary container.** While the old server keeps serving users, a
second, short-lived container is started from the new image. It runs one command and exits,
and it never receives traffic. The general form is
`docker run --rm --network werewolf --env-file .env.production <new image> <command>`.

*Step 3, the migration.* The command is `alembic upgrade head`.

| Question | Answer |
|---|---|
| Why from the new image? | The migration is a file in the code. The old image was built before that file existed |
| Why from a container, not from the host? | The database's address is a name, `ww-postgres`, that exists only on Docker's internal network. The host cannot resolve it |
| Why before the swap? | The new code expects the new column or table. Started first, it would fail on its first query that uses it |
| Is the old server harmed meanwhile? | No. Every migration so far only added things, and the old code never reads them |

*Step 4, the start-up check.* The command is a short piece of Python that loads the
application and checks what this release changed. Two examples from the log: for the release
that switched AI memory on, that the memory code imports in the slimmed-down image and the
saved snapshot loads; for a release that changed the rules, that the switch reads "on" and the
rules contain the new sentence. The check catches faults that cannot appear on my own machine:
a library left out of the image, a setting missing from production's file, a path that is
valid on the host but not inside the container. If it fails, nothing has been swapped. The log
records that these checks were done, not the exact commands.

Step 5 is how my system answers "who is interrupted?". A restart has these effects:

| What is in progress | What a restart does to it |
|---|---|
| A room waiting for players | It is ended |
| A game paid for by a player's key | It returns in a state where it waits for the key to be entered again (U10) |
| A game paid for by the house | It resumes from its saved checkpoint (U3, U5) |

Waiting until nothing is in progress avoids all three. That is possible only because the site
has little traffic.

The server's README gives one build command. The other steps are only in the log.

**Record:** `frontend/docs/deploy_log.md`; `server/README.md`; `Dockerfile`.

## 3.2 How a release is undone

| What | How it can be undone | What is missing |
|---|---|---|
| The code | The previous image is kept as `:prev`. A rollback is starting that image | The command for doing so is not written down |
| The database's structure | Every migration has a working backward step. They have not been needed so far: every migration only added tables or columns that may be empty, so the previous image kept working on the new structure | Nothing |
| The data | Not covered | No backup is taken before a migration as a written step, and no backup runs on a schedule |

Migrations are applied by hand before the swap. The server does not check the database's
version when it starts. If it were started against a database missing a migration, it would
run normally until the first query that needs the missing table or column, and fail there.

## 3.3 What can be changed without a release

Two sets of values are stored in Postgres and re-read every 10 seconds.

| Store | What it holds | How it is changed |
|---|---|---|
| The house's settings | Three values: whether the house pays for games at all, the default model, and how many house-paid games are allowed per day | Two admin endpoints, protected by a token |
| The model catalogue | One row per model: whether the house pays for it, its rescue model, its prices | A command-line script that writes the rows |

**The admin endpoints cannot be used in production.** The admin token is not set there, so
the endpoints answer "not found" (404) to everyone. The settings table is empty, and the three
values come from their defaults. In practice, the only one of the two that I have used to
change behaviour is the model catalogue.

**An example of it working.** The Gemini credits that paid for house games ran out. I marked
the Gemini rows in the catalogue as "paid for by the player", which left one Claude model as
the only model the house pays for. The server chooses the default model in this order:

1. the stored default-model setting, if that model is still one the house pays for;
2. the default given at start-up;
3. the first model in the catalogue that the house pays for.

The first two were empty, so the default became that Claude model within 10 seconds. There was
no release and no restart.

**Everything else is deploy-time.** Addresses, cookie settings, how long idle games are kept,
and the log level are read once from environment variables at start-up. Changing any of them
needs a restart.

**Code:** `server/house.py::HousePolicy`; `server/routes/admin.py`;
`server/housekeeping/catalog_refresh.py`; `scripts/model_catalog.py`; `server/config.py`.

## 3.4 The limit on house-paid games

```text
A visitor asks for a game paid for by the house
   │
   ├─ count the game records with byok = false created since midnight UTC
   ├─ compare the count with the limit (10 by default)
   │
   ├─ below the limit → the game starts
   └─ at the limit    → the request is refused with status 402, the reason,
                        and a Retry-After header giving the next midnight UTC
```

The three decisions from 1.4, as my system makes them:

| Decision | My system |
|---|---|
| Where the count comes from | The game records. There is no counter. Every started game has a record that says whether a player's key paid for it (`byok`, "bring your own key"), so the count is correct after a restart |
| Best-effort or exact | Best-effort. The check and the start are separate steps, so games requested at the same moment can all take the last place. The code's own comments say so |
| What a refused visitor sees | Status 402 with the reason, and the time when house games become available again |

A player who brings their own key is never counted and never refused by this limit.

**The limit outside my code: the prepaid balance.** I pay each model provider in advance and
do not let the balance refill automatically. When the balance reaches zero, the provider
refuses further calls. So the most I can lose in a month is the amount I chose to add. This
limit is exact, and it holds even if my own daily limit has a fault, because the provider
enforces it and my code does not. For that reason I have not built a monthly limit. The cost
of relying on it is how it fails: house-paid games stop working for everyone until I add
credit, where the daily limit refuses politely and says when to come back.

**The limits on one game, once it has started:**

| What is limited | Value |
|---|---|
| One model call | 30 seconds and 2 attempts. The day's summary call gets 90 seconds |
| A seat whose calls keep timing out | After 2 timeouts, its turns go to the rescue model for 5 minutes |
| A person's turn | 120 seconds, after which the game continues without their answer |
| The game's length | 12 days, then the game is declared a draw |
| A game nobody is using | Removed after 1 hour for a single-player game, 1 day when several people are in it |

There is no limit on how many games run at the same time (U15).

**Code:** `server/house.py::authorize`; `server/storage/game_repository.py`;
`server/routes/_shared.py`.

## 3.5 Known limitations and possible improvements

| Gap | Why it matters | Possible improvement |
|---|---|---|
| 1. Every release step is done by hand, and nothing runs the tests before a release | A skipped step would not be detected. The log shows the steps were followed, but nothing enforces them | One script for the steps; run the tests automatically on every push |
| 2. No backup before a migration, and none on a schedule | A faulty migration or a lost disk would lose the games and the lessons | A database dump before each migration; a nightly dump |
| 3. The server does not check the database's version at start-up | Started against a database missing a migration, it fails later, on the first query that needs it | Compare versions at start-up and refuse to start on a mismatch |
| 4. The admin endpoints are disabled in production | The three house settings can be changed only by writing to the database by hand. The catalogue script handles the one case that has occurred | Set the token, or give the settings a script like the catalogue's |
| 5. The daily limit is best-effort, and nothing limits how many games run at once | Requests arriving together can exceed the limit, and each game makes many model calls | Reserve a place atomically; limit the number of games in progress (U15) |
| 6. The nightly leak audit is documented but not installed | The prompts of hosted games are not being checked for leaked private information | Add the scheduled job; then check that it ran |
| 7. The running server is older than the repository, and one migration has not been applied | Fixes made since the last release are not live, including the tracing and fingerprint changes | One release that includes them |

**Two written records are wrong.** A design note says the default model was changed through
the stored setting; the code and the database show it was the catalogue. A plan counts 72
releases; the log's table has 76.

---

# Part 4 — Design choices

**Who runs the release steps?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| A person, following a written procedure and logging each release | No infrastructure to build. Every release has a record with its reasons | A step can be skipped, and nothing runs the tests first | Yes |
| A pipeline that runs on every merge | Every step runs every time | The pipeline has to be built and maintained | No |

**Where does the spending count come from?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Count the records in the games table | Always matches what happened; correct after a restart | One query per check | Yes |
| A separate counter | No query | Can become wrong, and is lost on a restart unless it is stored | No |

**How exact is the limit?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Best-effort | Simple | Requests arriving together can exceed it | Yes |
| Reserve, then release | Exact | A transaction, and a rule for reservations that are never used | No |

**Where does the system run?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| One host, Docker Compose | One file describes everything. It is cheap. A release is two commands | Only one machine: every release needs a restart, and if the host fails there is no replacement | Yes |
| Several hosts behind a load balancer, or a managed platform | A release without interruption. One host can fail | More cost and more parts to operate. Games are currently held in one process's memory and would have to be moved out of it (U5, U15) | No |

---

# Part 5 — Review

## In 30 seconds: five ideas

1. **A release is safe when four questions have answers.** Is it the code I meant? Does it
   start with production's settings? Can I undo it? Who is interrupted during the change?
2. **The database needs its own rollback plan.** Additive migrations let the previous code
   keep running. A backup covers the changes that are not additive.
3. **A setting is either deploy-time or run-time.** Run-time settings are for the values I may
   need to change quickly, without a release.
4. **Count spending from the records, not from a separate counter.** A counter can become
   wrong; a count over the records cannot. The limit is then either best-effort or an exact
   reservation.
5. **A daily limit is not enough alone.** Each piece of work also needs limits on its time,
   its retries and its length.

## My Werewolf system in one paragraph

Everything runs on one host under Docker Compose, with the game database kept outside Compose.
A release is done by hand, following a procedure that developed over the entries of a deploy
log: build from a clean checkout, keep the previous image, apply any migration first, check
inside the new image, swap when no game is in progress, smoke test, and write a log entry. The
model catalogue and three house settings are stored in Postgres and re-read every 10 seconds.
The catalogue is the one I have actually used: it moved the default model away from a provider
whose credits had run out, with no release. House-paid games are limited per day by counting
game records since midnight UTC. The limit is best-effort, and a refused visitor gets status
402 and a time to come back. The weak points: no step is automated and no tests run before a
release, there are no backups, the admin endpoints are disabled, the leak audit is not
scheduled, and the running server is older than the repository.

## Stopping check

Without looking back at the note, explain:

- the four questions for a release, and my system's answer to each;
- why the daily limit counts game records and does not keep a counter;
- what "best-effort" means for that limit, and when that would not be acceptable.

Then answer Problem B. That is enough for this pass.

## Problems

**Problem A: transfer to another application.** A public demo of a model application is
shared widely at 2 a.m. Which settings must be changeable without a release? How is spending
limited so that the count can be trusted? What should have been recorded by morning?

**Problem B: my own system.** Describe a release of my server in four steps, and name what is
missing.

---

# Appendix A — Answers to the problems

**Problem A.** *Changeable without a release:* the switch that turns free use on or off, the
daily limit, and which model is the default, because switching to a cheaper model is the
fastest way to reduce cost.

*A count that can be trusted:* the limit counts the day's records in the database, not a
separate counter, so that a restart or a second server cannot reset it. If exceeding the limit
is expensive, a place is reserved atomically before the work starts. Each piece of work keeps
its own limits: time and retries per call, and a maximum length.

*Recorded by morning:* how many requests were served and how many refused, by hour; the cost
by model; the error rate; and whether any limit was exceeded.

*In my system:* the first two settings exist but can be changed only by writing to the
database by hand, the third is changed through the catalogue, and the count is best-effort.

**Problem B.** The four steps:

1. Build the image from a clean checkout of the commit, and keep the previous image.
2. Apply any migration, then run a start-up check inside the new image.
3. Swap when no game is in progress.
4. Smoke test, and write the log entry.

Missing: nothing runs the tests automatically, no step is scripted, there is no backup before
the migration, the rollback command is not written down, and the server does not check that
the database matches the code.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **run** (executed
for this note), **doc** (a written record, not re-read in the code). Read against the code and
the host on 2026-11-16. Paths are from the repository root.*

**The release (3.1)**

- The procedure and the form of an entry: **doc** `frontend/docs/deploy_log.md` (its summary
  of the procedure, and the table of entries, 76 in all, the last dated 2026-10-26)
- The one build command: **doc** `server/README.md`; **code** `Dockerfile`
- No script, Makefile, CI workflow or active git hook: **code**, a search
- What a restart does to rooms and to games on a player's key: **doc**
  `frontend/docs/seat_continuity.md`; **code** `server/game/live_game_registry.py`
- How long a swap interrupts a game in progress, and what a player sees: not measured

**Rollback (3.2)**

- Images tagged `:prev` and by commit exist on the host: **run** (`docker images`)
- Fifteen migrations, each with a backward step: **code** `alembic/versions/`
- Migrations applied by hand, not at start-up: **code** `Dockerfile` (the start command),
  `server/app.py` (the lifespan)
- The previous image ran on the new structure: **doc** the deploy log
- No backup step or scheduled backup: **code** and **doc**, a search; **run** (`crontab -l`).
  One dump taken by hand before a migration exists on the host, dated 2026-10-15

**Run-time settings (3.3)**

- The three settings, their store, the 10-second cache and the defaults: **code**
  `server/house.py`, `server/storage/settings_repository.py`, `server/config.py`
- The admin endpoints answer 404 without a token; the token is not among production's
  variable names: **code** `server/routes/admin.py`; **run** (names only)
- The settings table is empty and one model row is house-paid: **run**, a read-only query
- The order in which the default model is chosen: **code** `house.py::_default_model`
- The catalogue's refresh and its script: **code** `server/housekeeping/catalog_refresh.py`,
  `scripts/model_catalog.py`
- That the Gemini rows were changed with that script: **doc**, my own record of the day; the
  database's present state agrees, and there is no audit trail

**The limit (3.4)**

- The count, the day window, the check, the 402 and `Retry-After`: **code**
  `server/storage/game_repository.py`, `server/house.py::authorize`, `server/routes/_shared.py`
- Best-effort: **code** `server/house.py` (the module's and the method's own text)
- The limits on a call, a stalling seat, a turn, the game's length and idle games: **code**
  `Agents/llm_factory/accessors.py`, `Agents/llm_factory/health.py`,
  `server/game/seat_clocks.py`, `Agents/config/game.py`, `server/config.py`
- No limit on games in progress: **code**, a search

**The gaps (3.5)**

- Gap 6: **doc** `server/README.md` (the scheduled line); **run** (`crontab -l` has no such
  line)
- Gap 7: **run**, the server container started 2026-10-26 from the image tagged `2ecec0cc`;
  the database is at migration 0014 of 15
- The two records that are wrong: **doc** `frontend/docs/server_design_notes.md` (how the
  default changed), `frontend/docs/build_plan.md` (the count of releases)
