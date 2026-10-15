# Multiplayer audit — 2026-10-15

What can go wrong when several friends play one game: what one of them can learn that their
seat should not know, how one can hold up or abuse the table, and how a friend's screen can
fall out of step. Two read-only scans, one of the server (`server/`) and one of the page
(`frontend/`), with the main claims checked in the code. Nothing was run on a device or in a
real four-human game.

Each fix below follows one form: **what we found**, **why it was like that** (the gap, and
the reason it made sense when it was built), **the fix**, and **how it is now**.

## What is solid

- **Who sees which event** is decided per event, per viewer, when it is sent
  (`server/game/entitlement.py`), and tested for every tier. The page receives only what its
  seat may see. Reveal's lock on the page guards against spoilers only: the observer events
  reach a browser only after game over, when everyone may see them.
- **The status** gives a seat its own pending turn and deadline, and nobody else's.
- **Replays** are served for finished games only. **The ledger** reads public events only.
  **The draft prompt** is built from the seat's own turn.
- **Seat cookies** are per game, HttpOnly and random; a forged or foreign token gets 403.
- **A submit racing the turn's clock:** nothing is awaited between the check and the
  handover, and a second answer gets 409. Several tabs on one seat count as present while any
  of them is open.

## Fixed

### The status counted private events (finding 1, status half)

- **What we found.** `GET /games/{id}` returned `last_seq`, the seq of the log's newest event,
  and anyone could poll it, spectators included. The log holds private events too: at night
  each role's action is written as it finishes. Polling once a second therefore ticked once per
  night action. It showed how many night actors were left, how long the pack chat ran, and
  whether a human held a night action; with two humans at the table, that names the other one.
  This undid the padding the night's progress bar exists for.
- **Why it was like that.** `last_seq` was added as the page's catch-up line: at connect,
  everything at or below it is history and lands still. The log's own newest seq was the
  simplest correct line, and the per-viewer filtering was applied to the events and the
  pending seats, not to this number.
- **The fix.** The status reports the newest event this viewer may see (the same entitlement
  rule as the stream). The page needs nothing more: it never receives the others.
- **How it is now.** A viewer's `last_seq` moves only with events they receive; at game over,
  when everything unlocks, it is the log's. Commit `cc0325c2`, test
  `test_status_last_seq_counts_only_what_the_viewer_may_see`. **Still open:** the stream's
  `id:` lines carry the global seq, so the gaps between the ids a viewer receives show how
  many hidden events fell between them. That is held (owner): reconnects resume from those ids.

### The refusal of a turn named whether another seat owed one (finding 2)

- **What we found.** A turn posted by a seat that owed none was refused with "no pending
  input_request for this game" when nobody owed anything, and "...for seat 'P4'" when someone
  did. A villager posting `{}` at night learned that a human night actor was choosing, and by
  posting again, when they answered.
- **Why it was like that.** The two messages were written for debugging: they told "the game is
  not waiting" from "it is not your turn".
- **The fix.** One message, naming the caller's own seat, whatever the others owe.
- **How it is now.** The answer is identical in both cases (tested). Commit `0082952b`.

### Drafts sent together got past the cap (finding 4)

- **What we found.** A draft checked "fewer than 3 used", then asked the model (seconds),
  and only then counted itself. Drafts sent at once all passed the check. Each was a paid model
  call, paid by the host's key or the house, and each added up to 20 s to the seat's clock, so
  one friend could hold the table.
- **Why it was like that.** Counting after the answer meant a failed draft was not charged,
  and in the page's own flow the button is disabled while a draft is on its way, so one seat
  never raced itself.
- **The fix.** The draft is counted before the model is asked and given back if the call
  fails; a seat drafts one at a time (409 "a draft is already on its way"). The wait is
  credited only to the question it was drafted for, not to one asked meanwhile.
- **How it is now.** Two at once: one runs, the other is refused, and only the one that ran is
  counted (tested); a failed draft leaves the count where it was (tested). Commit `7ed36d7e`.

### A friend who left held every one of their turns (finding 5)

- **What we found.** A seat with no connection gets 30 s per question before its agent plays
  it. A friend who had gone for good cost the table 30 s on every one of their turns, for the
  rest of the game.
- **Why it was like that.** The 30 s is for a dropped connection, long enough to come back
  from. Leaving for good was not modelled, because a running game has no way to leave.
- **The fix.** After two turns in a row played by its agent while the seat had no
  connection, the seat is taken to have left: its next questions go to its agent at once. It
  connecting again ends that (`seat_clocks.py` `GONE_AFTER_TURNS`).
- **How it is now.** Two turns wait the 30 s; the third goes at once; a reconnect brings the
  30 s back (tested). Commit `ff1368f5`.

### A dead stream went unnoticed (finding 7)

- **What we found.** Two ways a friend's stream could die without the page noticing:
  - The browser closed it for good after a failed reopen (a 502 during a deploy, a 403 after a
    restart). It never retries that, and the page reopened only when the tab was hidden and
    shown again.
  - A phone kept a dead connection open through its sleep. The server's heartbeat was an SSE
    comment, which no script sees, so a silent stream looked the same as a quiet game.

  Either way the stage froze, the friend's turns never showed, and their agent played them
  unseen.
- **Why it was like that.** An SSE comment is the usual keep-alive, and it was there to keep
  proxies from closing an idle connection, not to tell the page anything. The page relied on
  the browser's own reconnect, plus a reopen on coming back to the tab or the network
  (2026-10-11). Neither covers a closed stream on a visible page, or a half-open one.
- **The fix.** The server's heartbeat is a named `ping` event, sent as a stream opens and
  every quiet 15 s. The page notes when it last heard anything. It reopens a stream silent for
  more than 40 s, and retries a closed one every 10 s, never while hidden (`streamStalled`).
- **How it is now.** A dead stream is reopened within about 45 s; a reopen is a catch-up,
  with the "You're back" notice for what went by. Server commit `f44028d8`; page `a0fa2e44`. Deploy both together: a new page on an old server would take a quiet game
  for a dead stream and reopen it every 40 s, harmlessly.

### An older status gave a new turn the old turn's deadline (finding 8)

- **What we found.** The page learns a turn's deadline from the stream (with the question)
  and from the 12 s status poll. A status asked for before the new question existed, and
  answered after it arrived, copied the previous turn's passed deadline onto the new one. The
  dock then called the turn expired and locked, while the server still waited, and the seat's
  agent answered at the real deadline. Back-to-back pack lines make this likely.
- **Why it was like that.** The guard against an older status (`snapshotLastSeq`) was added
  where the race was first seen: a stale status clearing a newer request. The other branch
  only refreshes a deadline, and was taken to be safe.
- **The fix.** A status whose `last_seq` is below the pending request's seq cannot have seen
  that request, so it moves nothing about it (`store.ts` `syncPending`).
- **How it is now.** Tested both ways: an older status leaves the deadline, a newer one moves
  it. This relies on the status counting the viewer's own events (finding 1), and a seat's own
  request is always one of them. Commit `53e7b0be`.

### Opening a game's page again used a cached status (finding 9)

- **What we found.** The page draws the line between history and news from the first status
  it holds, and reads the server's clock from it. The query cache keeps a status for 30 s, so
  a friend who left the table and came back within that window used the old one. Everything
  since then played as news, at reading pace, with no "You're back", and the clock read late.
- **Why it was like that.** The 30 s freshness is the app's default for every query, to avoid
  refetching on every mount, and the stream reads the status once, as a snapshot. A snapshot
  served from a cache is a snapshot of an earlier moment.
- **The fix.** The game's status is always asked for again when the page mounts
  (`refetchOnMount: 'always'`), and not used until this visit's answer is in
  (`isFetchedAfterMount`).
- **How it is now.** Coming back to a game shows the loading platform for one status round
  trip, then lands as a first visit does. Commit `bb15b5cd`.

### A friend's clock ran out while their stage read toward the turn (finding 10)

- **What we found.** On a room's clock the turn's 120 s run from when the server asks. A
  stage behind the table (a phone back from a pocket, a long run of agent lines) read every
  beat at its normal hold before reaching the turn. The friend could lose the turn before it
  was ever on the screen.
- **Why it was like that.** The owner's ruling (2026-10-01) is that the stage never hurries:
  trimmed holds flicker, and the general "jump" (ruling 3) was left for a real four-human game
  to settle. Only the beat on the stage was cut short once.
- **The fix.** For the seat's own turn only: when more than 30 s of reading is queued before
  it, the stage lands still just before the turn, and the turn plays (`live-state.ts`
  `TURN_JUMP_MS`). The skipped lines are in the transcript. Under 30 s, the old cut stays.
- **How it is now.** Tested both ways. No notice is shown for the jump yet. The general jump
  (any queue past about 45 s, with the "Caught up to the table" strip) is still unbuilt
  (`live_timing_sheet.md` ruling 3). Commit `e27497bd`.

### A network blip during a rejoin cost the seat (finding 11)

- **What we found.** The page keeps a copy of the seat's key in case the cookie is lost. A
  rejoin that failed for any reason deleted the copy, including no network or a server
  restarting. The friend was then a spectator for the rest of the game.
- **Why it was like that.** The only failure considered was a key that no longer resolves
  (the game gone, or another device's seat), where deleting it is right.
- **The fix.** The key is deleted only when the server refuses it (403, 404, 410:
  `ApiError.refusesToken`). On anything else it is kept, and the game page tries again after
  5 s.
- **How it is now.** Tested on the rule. Commit `5b4186d2`.

## Accepted or left

| # | Finding | Decision |
| --- | --- | --- |
| 1 | The stream's ids carry the global seq, so their gaps count hidden events. | Held (owner): reconnects resume from them. |
| 3 | The night's length shows a human night actor: the bar fills in 20–30 s, then waits for the human, up to 120 s. | Accepted (owner): not a big issue. |
| 6 | No rate limits; stream queues unbounded; the host's key travels in the URL (proxy logs). | Left (owner). |
| 12 | A restart can reuse event seqs (events are sent before they are saved), and a vote answered just before a restart is asked again. | Accepted (owner): a question asked again is answered again. |
| — | The store is not reset after leaving a game; two tabs joining at the same instant take two seats; a submit does not say which request it answers; friends see a death a few seconds apart (by design). | Left. |
