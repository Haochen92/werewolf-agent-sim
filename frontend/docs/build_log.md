# Frontend v1 — build log: decisions, failures, and what they cost

> Written 2026-08-21, at the end of the P0→P3 build (branch `feature-frontend-v1`, 24 commits,
> tag `frontend-v1-headless` at the pre-visual fork point). Deployed at
> **wolf.liuhaochen.com**.
>
> **Purpose: review.** This is the honest record of what was decided, what broke, and why —
> organised by *kind of problem* rather than chronologically, because the categories are what
> generalise. Every claim here was verified against a running system; where something is
> unverified it says so.
>
> The specs are [`build_plan.md`](build_plan.md) (architecture), [`ux_baseline.md`](ux_baseline.md)
> (visual), [`ux_journeys.md`](ux_journeys.md) (screen-by-screen). This document does not repeat
> them — it records where reality disagreed with them.

---

## 0. How to read this

Each entry follows the same shape:

- **What happened** — in plain terms.
- **Why it happened** — the actual mechanism, named precisely.
- **What it cost / would have cost** — the real consequence, not a hypothetical.
- **How it was settled.**

Severity is marked where it matters:
**🔴 would have shipped broken** · **🟠 caught late, cheap to fix** · **🟡 friction only**

---

## 1. Infrastructure and environment

### 1.1 🟡 Port 8000 was already taken — by a different project

**What happened.** The build plan says the API runs on `localhost:8000`. It answered, and it
answered with a valid OpenAPI document — so it looked correct. It was a *different
application*: another project's `api-service` container, running since July, whose paths were
`/inference/predict` and `/heroes/get_image_urls`.

**Why.** Docker port bindings are first-come on a shared host. Nothing warns you that the
service answering is not the service you meant.

**Cost.** Would have generated the entire TypeScript client from the wrong OpenAPI schema.
Caught in the first five minutes only because the route list was checked rather than assumed.

**Settled.** The werewolf server runs on **8001** in dev; `NEXT_PUBLIC_API_BASE_URL` points
there. The server's CORS default already allowed `localhost:3000`, so nothing else moved.
The other project's container was not touched.

**Generalises to:** a health check that returns 200 proves *something* is listening, not that
it is yours. Check an identifying route.

### 1.2 🟠 The credential the app needs is not the credential you expect

**What happened.** The containerised server crashed on boot with
`DefaultCredentialsError`, even though the only thing it was being asked to do was serve
finished games out of a database.

**Why.** The game engine's embeddings factory (`Agents/llm_factory/embeddings.py`) builds its
client **eagerly at import time**, not lazily on first use. Importing `server.app` therefore
requires Google credentials, regardless of what the process will go on to do.

**Cost.** Roughly an hour of deploy time, and a genuinely confusing failure — "why does the
replay archive need an LLM key?"

**Settled.** Application Default Credentials are mounted read-only into the container rather
than baked into the image. A convenient accident made this clean: the container user is uid
1001, which is also the host `ubuntu` user's uid, so the credential's `0600` permissions carry
over unchanged and nothing had to be loosened.

### 1.3 🔴 The container was missing data the engine reads at game creation

**What happened.** `POST /games` returned **500** in production while working perfectly in
dev. Traceback ended at
`FileNotFoundError: '/app/memory_stores/v6_1/observations.json'`.

**Why.** A served game is created with `memory_persistence={"dump_enabled": False}` — so
nothing is ever *written back* to the memory store. But the engine still **seeds retrieval**
from that store when the game is constructed. "Dump disabled" and "memory off" are not the
same thing, and the deployment assumed they were.

**Cost.** Live play was completely broken in production while every local test passed. This is
the classic works-on-my-machine failure: the code was identical, the *data* was not.

**Settled.** `memory_stores/` is mounted read-only. Not copied into the image: it is 37 MB and
**not tracked in git**, so a `COPY` would have worked on this machine and failed on any clean
checkout — a latent trap rather than a fix. Read-only so a container can never corrupt the
store it reads.

**Generalises to:** an image built from a git checkout only contains what git tracks. Anything
the app reads from disk that is *not* in git must be mounted, and its absence must be a loud
failure rather than a silent degradation.

### 1.4 🔴 Cloudflare silently buffered the live event stream

**The most consequential issue in the build.**

**What happened.** After deploying, live play appeared to hang forever. The browser would
connect and then receive nothing — no events, no errors. Meanwhile the game was running
perfectly behind it: the server's own status endpoint showed the game advancing normally.

**Why.** The app pushes live updates using **Server-Sent Events** — one long-lived HTTP
response that stays open and dribbles out events as they happen. Any proxy in the path that
decides to *buffer* that response, waiting for it to "finish" before passing it on, converts a
live stream into a response that arrives when the game ends. Cloudflare was doing exactly
that.

What made it hard: **everything else was already correct.**

- The origin sent `content-type: text/event-stream`, `cache-control: no-cache`, and
  `x-accel-buffering: no`.
- Caddy had `flush_interval -1` set — and this was confirmed *in its running configuration*
  via the admin API, not merely in the file on disk.

**How it was isolated.** Three measurements, narrowing the path each time:

| Path | Result |
|---|---|
| Direct from the server container (`localhost:8000`) | frames immediately |
| Through Caddy, bypassing Cloudflare (`curl --resolve` to the origin IP) | headers + first frame in ~20 ms |
| Through Cloudflare (the public URL) | **not even the response headers within 25 s** |

That middle row is what identified the culprit: it proves Caddy is innocent, because the only
difference between rows two and three is Cloudflare.

**Settled.** `header_down Cache-Control "no-cache, no-transform"` on the `/api` block.
`no-transform` is the documented instruction to Cloudflare to leave a response alone — no
compression, no optimisation — and *transforming is what its buffering hangs off*. After the
change: **first frame at 0.02 s**, and a complete game's ~400 events streamed live.

**Cost.** Would have shipped a multiplayer game that looked permanently frozen to every user,
with no error anywhere and a perfectly healthy backend. Nothing in the application would have
indicated a fault.

**Generalises to:** streaming responses have a *path*, not just an endpoint. Every hop can
buffer. Test through the real public URL, never only against the origin — and when it fails,
bisect the path rather than guessing at the code.

### 1.5 🟡 The project's compose file did not contain the deployment

**What happened.** The instruction was "everything you need to host should be on the docker
compose file in this project." It wasn't: `docker-compose.yml` held only the Langfuse
observability stack (Postgres, ClickHouse, Redis, MinIO). No web server, no app, no reverse
proxy.

**Why.** The reverse proxy is a *separate project* (`~/projects/caddy`) that owns a shared
Docker network (`shared-caddy-network`) and the Cloudflare origin certificates, and fronts six
other domains. Services join that network and Caddy addresses them by container name.

**Settled.** The app services were added to this project's compose (where they were expected),
joined to both a private network and the shared one — copying the pattern of the sibling
project, whose `dota.liuhaochen.com` block is structurally identical to what this app needed.

### 1.6 🟠 A database that must never be recreated

**What happened.** The replay archive and memory store live in a standalone `ww-postgres`
container that predates this work and holds real data.

**Why it mattered.** Declaring it in the compose file would have been tidier and would have
meant `docker compose up` could recreate it — destroying data.

**Settled.** Deliberately **not** in the compose file; attached to the app network
out-of-band with `docker network connect werewolf ww-postgres`. This is written into the
compose file as a comment, because it is exactly the kind of invisible dependency that breaks
six months later. **If that container is ever recreated, the connect command must be re-run.**

### 1.7 🟡 Shell and tooling friction (grouped — no lasting impact)

| Issue | Mechanism | Resolution |
|---|---|---|
| A test fixture landed in the repo root instead of `frontend/` | the shell's working directory had drifted between commands; relative paths resolved elsewhere | moved; later commands used absolute paths |
| `pkill -f "next start"` killed its own shell | the pattern matched the command string of the very process running it | killed by PID, identified via the port it held |
| Wrong server kept serving an old build | several `next-server` processes on the host from other projects; the one restarted was not the one on port 3000 | identified the owner of port 3000 explicitly; left the others alone |
| A verification "hang" that wasn't | Python's `requests.iter_lines` buffers to 512 bytes before yielding, so a slow stream looks stalled | re-verified with `curl -N`, which does not buffer |
| A spurious `403` while testing | each `curl` invocation is a fresh session, so the seat cookie was lost between calls | used a cookie jar; the 403 was correct behaviour |
| `.env` templates refused by git | the repo root ignores `.env.*` (correct for the Python side) | a scoped un-ignore in `frontend/.gitignore` for the two files that hold only a public URL |

**Generalises to:** most "the system is broken" moments during verification were *the
measuring instrument* being broken. Confirm the tool before believing the reading.

---

## 2. Server contract: what the wire actually said

None of these are server bugs. They are places where **the documentation and the data
disagreed**, and the data won. All were found by inspecting a real 593-event archived game
before writing the code that depended on them.

### 2.1 🔴 The transcript is a shared slot counter, not a list of speeches

**What the docs implied.** Observer-tier annotations ("why did this agent speak?", "who were
they addressing?") join to a speech via `about_channel_seq`.

**What the data showed.** `channel_seq` is a single per-day counter shared by **three**
different event types: speeches, passes, and narrator lines. It is dense (0…N, no gaps, no
duplicates). So a day's transcript is a list of **slots**, each occupied by one of the three,
and an annotation attaches to *whatever occupied that slot*.

**Why this matters enormously.** Of the seeded game's 149 annotations, **18 attach to passes,
not speeches**. A data model built around "annotations decorate speeches" would have silently
dropped every explanation of *why an agent chose not to speak* — which is precisely the
content that makes the X-ray feature worth building.

**Settled.** `GameView` models a day as ordered slots; annotations live in a side map keyed by
`channel_seq`, which also makes the join order-independent by construction.

### 2.2 🟠 Nights belong to the day before them

`night_result` for night N is tagged `day: N`, and the narrator's description of that night's
deaths occupies a slot in **day N's** channel.

The two design documents disagree about where this renders: `ux_journeys` D19 puts the night
section on the current day's page; D20 says the night *result* opens the *next* day's page.
The data settles it — splitting them would place a day-5 narrator line on a day-6 page that
does not exist.

**Settled.** Night N renders at the bottom of day N. The one thing that *does* cross the day
boundary is `day_summary`, because the wire's own docstring says "shown next morning."

### 2.3 🟠 Not every day has every phase

Day 1 of the seeded game goes **day → night** with no voting phase at all: three agents
passed, nobody spoke, and the day ended with `no_vote`.

**Cost avoided.** A scrubber built as "days × 3 phases" would have shown a phase that never
happened. The timeline is built from the `phase_change` events that actually occurred.

**Side effect worth knowing:** the seeded game's day 1 legitimately looks almost empty with
the X-ray off. That is the real game, not a rendering bug.

### 2.4 🟠 A field the UI spec assumed is not on the wire

`ux_baseline` specifies a pass button "where `can_pass`". `InputRequest` carries no `can_pass`
field — only `action_kind`, `candidates`, and `deadline`.

**Settled.** Pass is offered on every discussion turn and **the server decides**: on a turn
that must be answered it returns `422` with its own wording ("You must respond on this
reactive turn."), which the dock renders verbatim. An honest rejection beats a button hidden
on a client-side guess.

**Flagged for review:** this is the one place the client cannot pre-validate what the server
will accept. Adding `can_pass` to the wire would close it.

### 2.5 🟡 The turn endpoint has no schema

`POST /turns` accepts an untyped dictionary; validation is delegated to the engine's
`validate_human_response`. So the accepted shapes are **not** discoverable from the API
schema.

**Settled.** The four payload shapes were read out of the engine source and written down at
the client's call site: `{delegate: true}` alone (legal in every phase); `{message}` or
`{pass_turn: true}` for discussion; `{message}` only for wolf talk; `{target}` for everything
else, drawn from the server's own candidate list.

### 2.6 🟡 Smaller contract facts, each of which would have caused a bug

| Fact | Consequence if missed |
|---|---|
| `host_key` is a **query parameter** on `/start` and `/lock`, not a body field | host actions silently unauthorised |
| `GameStatus.state` is a bare string, not an enum | no compile-time safety on the three-state route |
| `PhaseProgress` never appears in the API schema (it is stream-only) | the pacing type had to be hand-transcribed from the server source, and is marked as such |
| `day_summary_structured` exists in the schema but is never emitted | building the inspector on it would have produced a permanently empty panel — `build_plan` warns about this and `ux_journeys` §8 still lists it; the warning was followed |
| Stream frames are named `game` and `pacing`, with the event id carrying the sequence number | wrong listener names receive nothing, with no error |

---

## 3. Client bugs I introduced and caught

Recorded because they are the honest part: several of these were caught only by testing
against real data or a running system, not by types or review.

### 3.1 🔴 Seat recovery would never have fired

**What happened.** If a player's session cookie is lost (cleared data, new browser session),
the app is supposed to silently reclaim their seat using a token kept in local storage. I
wired that recovery to trigger *when the status request failed*.

**Why it was wrong.** `GET /games/{id}` is a **public** endpoint. A lost cookie does not make
it fail — it succeeds and simply reports `you: null`. The trigger condition would never have
been true.

**Cost.** Seat loss would have been permanently unrecoverable, and it would have looked like a
rare, unreproducible bug.

**Settled.** The real signal is "this device holds a seat token for this game, yet the server
says we are nobody." Verified end-to-end against a live game: rejoin returns 200 and the next
status comes back with the seat resolved.

### 3.2 🔴 Every refresh would have replayed the whole game's drama

**What happened.** The design has exactly two full-screen moments — the role reveal and the
game-over banner — and both must fire **only when the event arrives live**.

The problem: the stream *replays history* before going live. On a first connection it replays
from sequence zero, so an hour-old role deal and a finished game's ending arrive through the
same channel as genuine news.

**Settled.** The status snapshot taken at connect time provides `last_seq`. Everything at or
below it is history; everything above is news. The store records which sequence numbers
arrived live, and the beat layer asks it before firing.

This also required adding two fields to the view model (`me.roleSeq`, `winnerSeq`), because
"we have a role now" is *also* true after a reload — the question is which event carried it.

**Generalises to:** "is this new?" is not answerable from state. It needs a boundary recorded
at connect time.

### 3.3 🟠 A test that was wrong in a useful way

A test asserted that 149 annotations would produce 149 annotated slots. It produced 85.

The test was wrong, not the code: all 85 turns carry a firing reason, and 64 of those *also*
carry addressing tags — two annotation types landing on one slot. Fixing the assertion forced
the actual invariant to be stated properly.

A second test failure was more valuable: a "public tier only" filter didn't exclude
`role_assigned`, which exposed a real design muddle — I had been filing every seat's private
role card into the observer-tier role map. For a live player that would have produced a
one-entry "X-ray" containing only their own card. Now the observer map comes solely from
observer-tier data, and your own role lives on your own view.

### 3.4 🟠 Container reported unhealthy while serving perfectly

**What happened.** The frontend container showed `(unhealthy)` in Docker while responding
correctly to every request.

**Why.** The health check used `localhost:3000`. Inside that image `localhost` resolves to the
IPv6 loopback `::1` first, and Next's standalone server binds **IPv4 only** — so the check got
"connection refused" from a healthy application.

**Cost.** Cosmetic today, but `depends_on: service_healthy` would have blocked anything placed
behind the frontend later, and a permanently-unhealthy container is exactly the sort of thing
that gets believed during a real outage.

### 3.5 🟠 A white flash on a dark-only app

Mantine's SSR helper hard-codes `data-mantine-color-scheme="light"` and relies on the client
to correct it after hydration. That default assumes an app with both schemes; this one has
only the dark palette, so every first paint flashed white — worst on the replay theater, the
page people are sent links to.

**Caught by** reading the served HTML, not by reasoning. The build, the type checker and the
component render tests were all perfectly happy with it.

### 3.6 🟠 A visual feature that shipped as nothing

The day/night shift — which `ux_baseline` calls "the single most atmospheric thing tokens can
do" — was implemented as a class that re-points colour variables. It was invisible.

**Why.** The class re-pointed the general surface variables, but every element inside the
night section reached for *explicit* night-specific colours instead. The re-pointing had
nothing to act on, and the section had no surface of its own to tint.

**Caught by** grepping the *built* CSS and reasoning about what actually consumed those
variables. The rule was present and correct in both source and output — and still did nothing.

**Generalises to:** "the CSS is in the bundle" is not "the CSS has an effect."

### 3.7 🟡 Self-inflicted, quick to fix

- A CSS comment containing `--night-*/--wolf-*` — the `*/` **closed the comment early**, and
  the formatter then mangled the rest of the file into nonsense.
- Referenced two view-model fields that didn't exist yet; the type checker caught it, and the
  right fix was to add them to the reducer properly rather than fake them at the call site.
- A leftover no-op expression (`className={classes.nightPhase ? '' : ''}`) from an edit.
- The Docker build failed on a missing `public/` directory — reserved by the layout for later
  share-card work, never created.
- `@eslint/eslintrc` was needed for the flat ESLint config and wasn't installed.

---

## 4. Design decisions and where the specs collided

These are judgement calls, recorded so they can be overruled knowingly.

### 4.1 The reducer knows nothing about time

One pure function folds the event log into a view model, and it serves **all three** surfaces:
replay (fold once), live (fold incrementally), and the post-game reveal (the same fold
absorbing the withheld backlog).

It deliberately does **not** know whether an event is live or historical. That belongs to the
store. Keeping the reducer ignorant is what lets replay-scrubbing and refresh-mid-game share
one code path instead of two that drift apart.

### 4.2 "Who am I?" is passed in, never inferred

A replay contains **every** seat's private role card. Inferring "my role" from those events
would have made the viewer whichever seat happened to be dealt last. The seat identity comes
from the server's status response, and when it arrives late the log is re-folded rather than
patched — because several fields derive from it.

### 4.3 The X-ray is arrangement, never permission

The client never hides data it received. Tier filtering is the server's job, and withheld
events simply never arrive. The toggle decides what is shown *at once*; it disables itself
when a log carries no observer data, because there would be nothing behind it — never because
the client decided to withhold.

### 4.4 Two takeovers, and no more

Full-screen moments are reserved for the role reveal and the game-over banner. Deaths — the
obvious third candidate — stay in the transcript flow as full-width banners. Overlay inflation
is how game interfaces become noisy, and the scarcity is what makes the two that remain land.

The replay's ending is therefore a *card at the foot of the final day*, not a takeover: a
replay viewer is by definition arriving at history.

### 4.5 Documented deviations

| Spec | What was built | Why |
|---|---|---|
| D20: night results open the next day's page | night renders at the foot of its own day | the data groups them that way (§2.2) |
| §8 row 6: turn markers visible in X-ray | not built | every speech already shows *why* the turn fired; a marker per turn was pure noise |
| §8 row 14: structured summaries in the inspector | not built | the engine never emits them (§2.6) |
| §6: micro-animation is parked | built, on request | the delivered replay read as static; motion is tied to reader actions only, never to game events, so the "render settled during catch-up" rule holds |

### 4.6 🟠 Two scope items I missed and later closed

- **The Dockerfile was in P0's scope** and I did not build it in the first pass. Closed during
  deployment.
- **Role icons were specified** in `ux_baseline` and never implemented; roles rendered as bare
  text until the visual pass.

Both were found by re-reading the spec against what existed, not by noticing during the build.

---

## 5. Blocked, and why

### 5.1 Portrait generation — external access, not code

The asset task called for generating ~24 seat portraits with Imagen. The script is written,
two-phase (generate candidates → owner curates → post-process picks), with a single fixed
style prompt so the set coheres.

It cannot run here. Credentials authenticate and resolve the project correctly, but **no image
model is reachable on it**:

| Model | Result |
|---|---|
| `imagen-4.0-generate-001`, `imagen-4.0-fast-generate-001` | 404 — "project does not have access" |
| `imagen-3.0-generate-002`, `imagen-3.0-fast-generate-001` | 404 |
| `imagegeneration@006` | 404 |
| `gemini-2.5-flash-image` | 400 FAILED_PRECONDITION via the Vertex predict path |

**Impact contained by design.** The asset manifest ships an empty portrait list and every seat
falls back to initials on a deterministic per-seat colour — the degradation `ux_baseline`
asked to be designed in. Enabling Imagen on the project is the only step needed; no component
changes.

---

## 6. What verification actually caught

Worth reviewing, because the *cheap* checks caught almost nothing.

| Method | What it caught |
|---|---|
| TypeScript / ESLint / build | the two invented field names — and **nothing else** in this list |
| Reducer tests against a **real** archived game | the annotation-join model, the shared slot counter, the missing voting phase, the observer-map muddle |
| Rendering components through `react-dom/server` with real data | that every day and both X-ray modes render without throwing |
| **Reading the served HTML and built CSS** | the white flash, the invisible night tint — both invisible to every check above |
| **Driving the real API** (create, stream, submit, rejoin, spectate) | the seat-recovery logic error, confirmation of 409/403 handling |
| **Testing through the public URL** | the Cloudflare buffering — invisible from every other vantage point |

The pattern is stark: **the further the check was from the real running system, the less it
found.** The build's most serious defects were all invisible to the type checker and the test
suite, and were caught by looking at bytes actually served over the wire.

### Standing gap

No browser exists in this environment, so **nobody has visually confirmed the rendered
pages.** Layout, spacing, contrast and the story/machine-world separation are unverified by
eye. Component *structure* is verified; component *appearance* is not. That review is
outstanding, and `ux_journeys` §0 reserves it for the owner against the running app anyway.

---

## 7. If someone picks this up next

1. **The Cloudflare `no-transform` rule is load-bearing.** Any future subdomain that streams
   needs it, and the failure mode is silent.
2. **`docker network connect werewolf ww-postgres`** must be re-run if that container is ever
   recreated.
3. **The reducer is the thing to protect.** Every visual component is a function of its output;
   if it is right, the visual layer is thin and low-risk. Its test suite doubles as a tripwire
   on server event semantics — if the server changes how the day channel is numbered, those
   tests fail before any user sees a misplaced annotation.
4. **`can_pass` on the wire** would remove the one place the client cannot pre-validate.
5. **Portraits** are one credential away from landing with zero code changes.
