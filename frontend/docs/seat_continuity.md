# Seat continuity — absence, disconnection, and recovery (design record)

> **What this is:** the one place that tells the whole story of a human seat that stops
> answering — from a network blip to a closed tab to a table everyone has left — and what
> the system does about it at each layer. The individual rulings were made on different
> dates in different documents (the transport record, the server design notes, the frontend
> build log); each is summarised here in lifecycle order and cited at the end. **The dated
> originals stay where they are** — this document is the map, not a replacement.
>
> Status: ruled 2026-09-09 (owner), building. Open rulings are listed in §9.

## 1. The fault model — five ways a game stops moving

| # | What happens | Layer that heals it | Status (2026-09-09) |
|---|---|---|---|
| 1 | The viewer's side dies (closed tab, back button, blip) | client: reconnect + replay the log | solved by architecture (§3, §6) |
| 2 | One game crashes (engine exception, dead BYOK key) | game: surfaced, redacted, other games untouched | resumption possible, deliberately unwired |
| 3 | The server process dies (crash, container rebuild, deploy) | process: continuous persistence + boot recovery | built 2026-08-20 (§6) |
| 4 | A game hangs (provider outage; nothing fails, nothing moves) | — | **undetected**; needs a stall watchdog (§9) |
| 5 | A human stops answering | table: the two clocks + presence (§4–§5) | **ruled here**, replacing "policy undecided" |

The layering is the write-up's one-liner: the client heals by replay, the game by
checkpoint, the process by persistence — and the two liveness gaps (stall, absence) are
*detection* problems, not recovery problems. This document closes the second gap.

## 2. Identity — a seat is a token, and the token has two copies

There are no accounts. A seat is a random token minted at join (or at the solo door), and
proving the seat means presenting that token. It travels in an **HttpOnly cookie** scoped to
the game's URL (24 h lifetime; `Secure` behind TLS; Path carries the browser-visible `/api`
prefix because the reverse proxy strips it upstream and browsers match cookie paths against
the URL *they* see), and it is handed to the page **once in the join body** so the client can
keep a second copy in local storage — a different lifecycle from cookies, so one copy usually
survives what kills the other.

Recovery is a **reclaim door, not re-verification**: `POST /games/{id}/rejoin {token}`
re-proves ownership and re-sets the cookie, in the waiting room or mid-game. The client's
trigger is not a failed request — `GET /games/{id}` is public and never fails on a lost
cookie — but the mismatch "this device holds a token for this game, yet status says we are
nobody". Rejoin also has to *re-open the stream*, because an in-flight SSE request keeps the
credential it began with; the stream's lifetime is keyed to seat identity, not only game
identity. Both copies gone (a genuinely new device) → the seat is orphaned, and an orphaned
seat is handled exactly like an absent one (§5). That convergence is why the demo gets away
with no accounts.

## 3. Disconnection — what the server actually sees

Every viewer holds one long-lived SSE connection per game tab. The server sees it as a
subscribe when the tab opens and an unsubscribe when the socket closes, and it notices a
silently dead socket within one heartbeat (15 s) because the heartbeat write fails; behind
the proxy it is usually faster.

A network blip and a closed tab are **identical at the instant the socket dies.** The tab
sends no other signal. The difference is what follows: an open tab's `EventSource` retries
on its own within seconds, carrying `Last-Event-ID` and the cookie, and the server resumes
that seat's filtered log from the cursor — identity and position both survive with zero
client code. A closed tab never retries.

So **presence** is a snapshot question — *does any open stream resolve to this seat right
now?* — and a timer is the waiting period that lets blip and close diverge. To answer it
the session keeps the seat resolver next to each subscriber queue (the route already resolved
the seat per event; the session's set was previously seat-blind).

## 4. The two clocks, one deadline

The AFK fail-safe (design notes §7) hands a silent human's turn to the seat's own AI —
"delegate" is a legal answer for every kind of turn, so no scripted defaults and no canned
words in an absent wolf's mouth. It arms in rooms with two or more human seats; a solo game
may wait forever. What it never asked was *why* the seat was silent. Now it does:

- **Thinking time, 120 s** — the seat is connected and simply has not answered. Unchanged.
- **Absence grace, ~30 s** — the seat has no open stream. Measured from the ask, or from the
  moment its stream dropped mid-turn, whichever is later. Long enough for a browser retry, a
  phone changing networks and the heartbeat lag; short enough that one closed tab does not
  cost the rest of the table two minutes on *every* one of that seat's turns. Reconnecting
  cancels the grace. **Pinned at 30 s after measuring** (2026-09-09, through Cloudflare +
  Caddy, a scripted client killed mid-stream): the server saw the drop after 1.0 s once and
  10.1 s twice — the slow cases landed exactly on the next 15 s heartbeat write, so the
  detection bound is the heartbeat. Worst case ≈ 15 s detection + ~5 s browser retry + TLS,
  leaving ~10 s margin inside 30. Tightening the heartbeat would let the grace shrink.
- **The deadline is absolute from the ask and absence never extends it.** Back at 29 s means
  91 s left; a fresh 120 s is granted only after a park (§5), because nobody waited during
  it. Pausing the clock for the absentee would favour the one person who is not there over
  everyone who is.
- **The wire carries the effective deadline** — the earlier of the two clocks — so the
  countdown the table sees is the truth. (`deadline` is a moment, not a duration.)

Two existing details keep the stopwatch honest and are unchanged: it is tied to the *exact
question* it started for (answer at 119 s, get asked again at 119.5 s → the old clock dies
quietly, the new question gets its full window), and a real answer racing the expiry bounces
off the same guard that ignores a double-click.

## 5. At expiry, the table decides — delegate or park

When either clock fires, the server runs the presence test over **every human seat**:

- **Someone is connected → delegate this one turn** to the seat's agent. Delegated turns are
  indistinguishable from AI play to the rest of the table, by design. The cost of a closed
  tab is one turn, never the seat.
- **Nobody is connected → park.** The delegate is simply *not submitted*; the question stays
  waiting, exactly as a solo game waits today. The graph is not running, no tokens burn, the
  row stays `running`, and restart recovery (§6) already knows how to revive a game parked on
  a human question. There is **no pause state, no pause status, no resume button**: the first
  human stream to subscribe again re-arms the pending clocks and play continues from that
  turn. If the returning person owns the parked seat, their dock is already showing.

A parked question *is* the pause. Durability already persists it.

Two boundaries of the test. **Only human seats count** — an open spectator tab, or a host
watching after their own seat was orphaned, does not keep the table running. And **presence
is read at the moment of expiry, not accumulated over the window** — a seat that reconnects
at 25 s and drops again at 29 s is absent at 30 s; the question is whether anyone is there to
play *now*. In practice a park can only ever come from the grace path, because a seat whose
120 s thinking clock fires is itself a connected human; the rule is still written as "either
clock" so there is one expiry handler with one test, not two that can drift apart.

## 6. Restart recovery — a park is restart-shaped

Persistence is continuous, not save-on-crash: each graph superstep commits to the Postgres
checkpointer and each durable event is appended to the event log as it is born. On boot the
registry is rebuilt from three separate authorities — the game row (identity, lifecycle,
seats, room settings), the ordered event rows (the replay source and the translator's
sequence shadow), the LangGraph checkpoint (executable state, pending tasks, interrupts).
A game parked at a human question is re-parked at that question; waiting rooms come back
with their name, lock and creation time. BYOK games are the exception: their key lives only
in process memory, so recovery marks them dropped.

This is why parking needs no machinery of its own: a parked game and a game that just
survived a restart are the same state.

## 7. Retention — nothing waits forever

Recovery revives every `waiting` and `running` row on each boot, so abandoned games would
otherwise accumulate (eleven did, in the first three weeks). A small idempotent sweeper
marks them **`dropped`** — the existing status, reused rather than adding a fifth — with the
reason in the row's error field:

| Row | Swept when |
|---|---|
| solo game parked on a human question, nobody connected | parked longer than **1 hour** |
| multi-human game parked, nobody connected | parked longer than **1 day** |
| waiting room | (open — the 2 h listing filter hides it; direct URL still resolves) |

"Parked" is measured from the ask (`parked_since`, restored from the row's `updated_at`
across a restart so a reboot does not make an old park newborn), and "nobody connected" is
the same presence test as §5 — a solo player sitting on an open tab is never swept out from
under them. Knobs: `SOLO_PARK_TTL_SECONDS`, `MULTI_PARK_TTL_SECONDS`, `SWEEP_INTERVAL_SECONDS`;
the sweep lives in `server/sweeper.py` and the epitaph reads `abandoned: parked on a human
turn with nobody connected for N min`.

Dropped games never enter the replay list and are never revived. Deleting dropped rows and
their checkpoints is a separate, later ruling.

## 8. Considered and rejected

- **A whole round of delegations before parking.** Turns are sequential, so an empty table
  would burn every other seat's turn first; and a present-but-slow player would count towards
  parking a game that still has a human in it. Presence fires at the first empty expiry and
  never while anyone is connected.
- **Delegating the instant the socket drops.** Every blip would cost a turn.
- **Wall-clock idleness ("no human for an hour").** Most games last ten minutes and four to
  five rounds; the rule would never fire before the game finished itself.
- **A host with special standing.** The host is a lobby role (lock, start). Making the game
  depend on them reintroduces "host left, table dead", which the fail-safe exists to prevent.
- **A `paused` status.** Redundant — see §5.
- **Pausing the clock during absence.** See §4.
- **Scripted per-turn defaults** (the AFK design discarded first): wolf night-talk cannot be
  passed under the game's own rules, so the table would have had to weaken the rule or put
  words in an absent wolf's mouth. Delegation needed neither.

## 9. Open rulings

1. ~~The grace number~~ — measured and pinned at 30 s (§4).
2. **Resume UX** (parked 2026-09-09): a "your seats" strip on the home page from the device's
   stored tokens; a copyable seat code on the role card for the cleared-everything case.
   Today the only way back into a game is its URL.
3. **Identity mechanics** (parked 2026-09-09): cookie lifetime, the local-storage copy,
   cross-device — currently "same browser or nothing", by ruling.
4. **Waiting-room retention** — no sweep yet.
5. **Stall watchdog** (fault mode 4) — a hang is still invisible; a "no part for N minutes"
   timeout would convert it into mode 2.
6. **BYOK credential resubmission** after a restart — recorded, not built.

## 10. Source records (dated originals)

- Fault model — `server_design_notes.md` §5c (2026-08-17)
- AFK delegate ruling and mechanics — `server_design_notes.md` §7 (2026-08-20)
- Seat token, two copies, reclaim door — `server_client_transport.md` §6b (2026-08-20)
- Reconnect and catch-up — `server_client_transport.md` §7
- Presence / two clocks / park — this document (2026-09-09; superseded a short-lived §6d in
  the transport record the same day)
- Client bugs on the recovery path — `build_log.md` §3.1, §3.11 (2026-08-21)
- The cookie-path-behind-a-proxy bug — `server_encountered_challenges.md` §7 (2026-08-24)
- Persistence and recovery on boot — `server_design_notes.md` §5c mode 3, §8 (2026-08-22)
