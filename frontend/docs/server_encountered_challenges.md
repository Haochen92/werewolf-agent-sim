# Server: encountered challenges

> Plain-language records of the hard problems we hit while making the game server able to
> host real human players, what each one turned out to be, and how it was solved. Written to
> be read cold, without the chat history or the code open. Each entry: the story, the fix,
> and what you need to remember. (Written 2026-08-19, during the multi-human build.)

---

## 1) Every interrupt arrived twice (and, nested deeper, three times)

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
