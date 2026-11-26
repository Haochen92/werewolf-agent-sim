# Server: encountered challenges

Status (2026-10-26): Journey log, kept as written. §1 to §6 were written 2026-08-19, §7 on
2026-08-24, and §8 on 2026-10-26 from a finding of 2026-09-12. The LangGraph behaviour they rest
on was observed on LangGraph 1.1.10 with langgraph-checkpoint 4.2.0, still the pinned versions on
2026-10-26, and every fix is still in the code.

| § | Date | What broke |
|---|---|---|
| 1 | 2026-08-19 | Every interrupt arrived once per nesting level |
| 2 | 2026-08-19 | The server's vote tally disagreed with the engine's |
| 3 | 2026-08-19 | Why the engine re-runs the AI votes after a human answers |
| 4 | 2026-08-19 | Caching the re-run, and why a human turn must never be cached |
| 5 | 2026-08-19 | The cache key that missed exactly when it was needed |
| 6 | 2026-08-19 | A class missing from the checkpoint allowlist |
| 7 | 2026-08-24 | A seat cookie the browser never sent back behind the proxy |
| 8 | 2026-09-12 | The events table runs ahead of the checkpoint |

> Plain-language records of the hard problems we hit while making the game server able to
> host real human players, what each one turned out to be, and how it was solved. Written to
> be read cold, without the chat history or the code open. Each entry: the story, the fix,
> and what you need to remember. (Written 2026-08-19, during the multi-human build.)

---

## 1) Every interrupt arrived twice (and, nested deeper, three times)

*2026-08-19, LangGraph 1.1.10 (commit `e4fbcfd1`).*

**The story.** When a game needs a human's input, the engine "interrupts" — it pauses and
surfaces a request that the server turns into an `input_request` event for the browser. While
testing, we discovered that LangGraph delivers every interrupt to us **twice**: once labelled
with the subgraph it came from (the "child" copy), and once again at the top level of the
stream (the "root mirror"). Both copies are identical, same ID. Had this gone live, every
"it's your turn" prompt would have appeared twice on every player's screen. We then asked:
what happens if the interrupt comes from a subgraph *inside* a subgraph? A quick experiment
showed it arrives **three** times — once per nesting level. The rule is: an interrupt echoes
at every level it bubbles through on its way up.

**The solution.** The server listens for interrupts **only at the root level** and ignores
every other copy. This is the only correct choice, not just a preference: an interrupt raised
directly in the top-level graph has *no* child copy at all, so filtering for "child copies
only" would miss it entirely, while the root copy always exists, exactly once, at any depth.

**What to know.** The root of the stream is the graph's official public surface — the child
copies are internal plumbing that the "show me subgraph details" streaming mode happens to
expose. When in doubt about which copy of anything is authoritative: root.

---

## 2) The vote count that wouldn't add up

*2026-08-19 (commit `e4fbcfd1`).*

**The story.** In our first real two-human test game, the server crashed at a day resolution
with a self-protection error: the server's own tally of the votes said "player_5 was lynched"
while the engine said "nobody was lynched". (The server keeps its own running copy of the
vote count so it can double-check everything it broadcasts — that cross-check refusing to
ship a wrong result is what "crashed" here, and it did exactly its job.)

Our first diagnosis was wrong. A small experiment suggested votes were being **delivered
twice** and counted twice, so we deduplicated: keep only the *first* ballot per voter. The
next test game crashed in the opposite direction. So we captured a full tape of every message
the engine streamed during a failing game and read it line by line. The tape told a
completely different story: when the human's vote pauses the game, the engine **throws away**
the votes the AI players had already cast in that round, and when the human answers, it asks
every AI player to **vote again from scratch** — and some of them change their minds the
second time. The engine only keeps the second round. Our tally had counted the first round —
votes that, from the engine's point of view, never happened. The decisive proof came from the
engine itself: its game-master recap message lists exactly the ballots it counted, and they
were the *second* set. Our "keep the first ballot" fix had been keeping precisely the ballots
the engine discarded.

**The solution.** The server's tally is now **last-write-wins per voter**: whatever a voter's
most recent streamed ballot says is what counts. However many times the engine re-runs the
round, the tally converges to exactly the set the engine keeps. Unit tests replay the real
tape's scenario (including the two AI players who changed their votes) so this can't quietly
regress.

**What to know.** The deep lesson: anything streamed *before* a human-caused pause in the
same voting round is provisional — "retracted truth" — until the round completes. The wire
layer must treat the stream as something that can re-deliver and even *contradict* itself,
and converge on final values rather than trust first sight. Also: the crash was the
safety-check working. Without it we'd have silently broadcast a wrong lynch.

---

## 3) Why the engine redoes work after a human answers

*2026-08-19, LangGraph 1.1.10.*

**The story.** Issue 2 raised the obvious question: *why* does the engine discard and redo
the AI votes at all? The documentation — and our own earlier experiments — said the opposite:
when a round pauses, finished players' work is saved, and on resume only the paused player
continues. Both are true. The difference is a wiring choice made long before humans existed.

There are two ways to attach a sub-game (like "the day phase") to the main game. One is to
hand the whole subgraph to the framework as a node — the framework then *knows* it's a graph
and can resume it surgically. The other is to call the subgraph like an ordinary function
from inside your own node — the framework sees only a black box. Our engine uses the second
style everywhere, for a good reason: the calling code hand-builds each subgraph's input,
and that hand-building is our **privacy boundary** (the wolf subgraph only ever receives what
wolves may know). The cost, invisible until now: when a pause happens inside a black-box
node, the framework's only move on resume is to **re-run the whole node from the top** —
which re-runs the sub-game's in-flight round, AI calls included.

We even checked whether the finished players' work was being saved: it **is** — byte-for-byte
identical to the surgical-resume case. The saved work just can't be *redeemed*, because our
re-run node calls the subgraph with a fresh input, and to the subgraph a fresh input means "a
new run", which supersedes the paused one. Saved, never spent.

**The solution (for the wire).** None needed beyond issue 2's fix — the server now handles
re-runs correctly. The engine-side waste is addressed in issue 4.

**What to know.** This behavior affects *solo* human games too and always has: every human
vote quietly re-billed ~8 AI vote calls, unobservable from the CLI. Also: completed *earlier*
rounds never re-run in either style (that guarantee held all along) — only the round the
pause lands in is affected. If we ever restructure, converting the day/wolf phases to
framework-managed subgraph nodes would make resumes surgical, at the cost of redesigning how
the privacy boundary is enforced. We chose a cheaper route instead — see issue 4.

---

## 4) Making the redone work free (caching), and why humans must never be cached

*2026-08-19, LangGraph 1.1.10, the "pinned version" below (commit `d06d7179`).*

**The story.** If the engine insists on re-running the AI voters after every human answer,
the next best thing is making the re-run cost nothing. LangGraph has a per-node result cache:
if a node runs again with the same input, the recorded result is replayed instead of calling
the LLM. The AI voters are perfect for this — same context in, same vote out. Two traps,
though. First, on our pinned LangGraph version, putting the cache on a node that can pause
for a human **crashes the game on resume** (the interrupted attempt leaves a malformed cache
entry). Second — and true on *any* version — caching a human turn is semantically wrong: a
cache assumes a node's output is determined by its input, and a human's answer is determined
by the *human*. Identical situation twice? A cache would silently replay their old answer
instead of asking.

**The solution.** Each parallel voting node now has an **uncached twin**: same code
registered under two names ("vote" with a cache, "vote_human" without), and the dispatcher —
which already knows which seats are human — routes each player to the right door. AI seats go
through the cached door; humans through the uncached one. Cache lifetime is six hours (it
must outlive a slow human's thinking time) and it doubles as the memory bound on a
long-running server.

**What to know.** The twin split looks redundant in the graph diagram; it is load-bearing.
The mental model: the cached door is for seats whose answer is a *function of their context*;
the uncached door is for the seat whose answer comes from a person.

---

## 5) The cache that never hit

*2026-08-19 (commit `d06d7179`).*

**The story.** With the cache wired, we ran a verification game — and the cache achieved
**zero hits**. The game stayed correct (issue 2's fix absorbed the re-runs, exactly as
designed), but every AI vote was still re-billed. The cause took an offline experiment to
isolate: the cache's default "same input?" check hashes the input with **pickle**, which is
sensitive to an object's internal bookkeeping, not just its values. And the re-run's inputs
are never the original objects — they're reconstructed from the checkpoint (saved and
reloaded), and a reconstructed object carries slightly different bookkeeping (pydantic
records *which fields were set explicitly*: four on the original, all ten on the
reconstruction). Same values, different bytes, different key. The default key therefore
misses in **precisely and only** the situation the cache exists for. A lab-bench test proved
it: original payload and its checkpoint round-trip compare equal (`==`), yet produce
different default cache keys.

**The solution.** A custom key function that hashes the payload's canonical JSON — its
*values*, sorted, with pydantic objects reduced to their field data — so any two payloads
that mean the same thing key the same. A unit test round-trips a realistic payload through
the real checkpoint serializer and asserts key equality, pinning the exact failure mode.

**What to know.** Classic systems lesson in local costume: cache keys must be built from
*values*, never from object *representations*, whenever inputs can be serialized and
reconstructed between attempts. If the cache ever misses again, the degradation is safe —
it's just issue-3 behavior (re-run, re-billed) with issue-2's fix keeping everything correct.

*Live confirmation (same day):* the verification game — which happened to deal a **human
wolf**, exercising the wolf-side twin for the first time — replayed **20 ballots from cache**
(17 day votes + 3 wolf kill votes) across its resumes, every one byte-identical to its live
original, and completed cleanly. The re-billing is gone.

---

## 6) A warning in the logs: "Blocked deserialization of DiscussionPassReason"

*2026-08-19 (commit `e382d5b2`).*

**The story.** During the first two-human game, the log showed LangGraph refusing to
reconstruct one of our own classes when reloading a checkpoint. Background: reconstructing
arbitrary classes named inside stored data is a code-execution risk (the same reason unpickling
untrusted data is dangerous), so our checkpointer was built with an explicit **allowlist** of
the classes that ride game state. The rule was documented in that very file: "a new model
class added to graph state must be added here too." `DiscussionPassReason` (a small label
enum on pass-turn markers) was added to the state later and never registered. The game
survived anyway by luck of nesting: the blocked value degrades to its raw string, and its
parent object — which *is* allowlisted — re-validates the string back into the enum on load.

**The solution.** One line: register the class. The allowlist now covers all nine state
classes.

**What to know.** The warning only fires on the resume path, so purely-AI games never show
it. If it ever appears again, it means a new class started riding game state without being
registered — harmless while nested inside an allowlisted parent, silently wrong if a blocked
class ever sits directly in state. Treat the warning as a to-do, not noise.

---

## 7) The human turn that looked like an AI thinking forever

*2026-08-24 (commit `81c6bb0a`).*

**The story.** The first production game served through Caddy stopped at "player_2 is
thinking." Langfuse showed no model trace, which initially made the new model selection look
suspect. The server told a different story: player_2 was the human seat, and the engine was
correctly waiting for that person's input. The browser had silently become a spectator, so
it rendered the public thinking marker but never received the private `input_request` that
opens the turn controls.

The lost identity came from two different views of the same URL. The browser calls
`/api/games/{id}`, while Caddy's `handle_path /api/*` strips the prefix and sends
`/games/{id}` to FastAPI. FastAPI therefore issued the seat cookie with
`Path=/games/{id}`. `handle_path` rewrites the incoming request only; it does not rewrite the
`Set-Cookie` response header. Browsers compare cookie paths against the URL *they* see, so a
cookie scoped to `/games/{id}` is never attached to `/api/games/{id}`. Rejoining appeared to
succeed and set the same unusable cookie again.

**The solution.** Cookie paths now include a configurable browser-visible prefix.
`SEAT_COOKIE_PATH_PREFIX` is empty by default for direct local FastAPI calls and is `/api` in
production. The cookie is consequently scoped to `/games/{id}` in development and
`/api/games/{id}` behind Caddy. An HTTP regression test pins the production header, including
normalisation of a trailing slash, while the original test continues to pin the development
path.

**What to know.** A reverse proxy's upstream path and a browser's public path are different
namespaces. Any browser-interpreted response metadata—cookie paths, redirects, generated
links—must describe the public namespace unless the proxy explicitly rewrites that metadata
on the way back. Here the application owns the cookie policy, so the deployment supplies its
public mount prefix and Caddy remains responsible only for routing.

---

## 8) The events table runs ahead of the checkpoint

*2026-09-12, read in LangGraph 1.1.10's source; recorded in the translator on 2026-09-13 (commit
`889a1371`) and written up here on 2026-10-26.*

**The story.** A running game is written down in two places. Each event the server sends is
appended to the events table as soon as its chunk is translated (`GameSession._persist_tail`,
called after every chunk), and LangGraph writes its own checkpoint of the game state. After a
restart the game resumes from the checkpoint, and browsers replay the events table. For a day we
believed the checkpoint always led, so a crash could only lose events the engine would produce
again, never send one twice. Reading LangGraph's loop showed the reverse. A task's output is
streamed the moment that task finishes, while the step's checkpoint is written only after every
task in the step has finished, and in the background. So the events table can lead the
checkpoint by up to one step: a crash in that window restarts the engine from a checkpoint that
does not yet hold work whose events were already sent and saved.

**The solution.** Mostly machinery that already existed. On the next boot the step re-runs from
its last checkpoint, as after a human's answer (issue 3): work that was committed comes back on
the stream tagged `cached`, and the translator drops it whole, for every kind of event
(`server/game/translate.py::is_cached`; cached ballots only refill the vote buffers). The step
in progress re-executes, and the vote cache (issue 4), the ballot buffers and the guards that
stop a line being sent twice absorb it as they do in a running process; at boot those guards are
rebuilt from the saved events (`Translator.hydrate`). A test re-delivers every state-update chunk of a
real recorded game as cached and checks that nothing is sent or even numbered
(`tests/server/test_translator.py::test_every_real_chunk_re_delivered_as_cached_sends_nothing`).
What none of this covers, as recorded on 2026-09-12, is a re-executed sequential node whose
events had already been written: they would be sent twice.

A blanket dedup was left out on purpose. A key on an event's content, or on (day, player), would
catch that last case and also drop real turns, because `turn_started` and `input_request`
legitimately repeat within a day with identical fields. The remaining window is one database
write wide and needs a hard crash, so it was accepted.

**What to know.** Two records of the same game do not agree just because both are "the state":
LangGraph's stream runs ahead of its checkpoint. It is the same fact that makes the translator
keep its own copy of the state instead of asking the graph (design notes §1). Before trusting an
ordering between two stores, read where each one is written. And before adding a dedup key,
check it against the events that legitimately repeat.
