# U15 seed notes: capacity, and how far the server scales

Not a note yet. Points from the U2 walkthrough on 2026-11-12, kept so U15 covers them. No other
note is about scale: each has its own "what breaks" section, so the limits are scattered. U15
gathers them into one table and one argument I can defend. It was first placed in U14 and moved
out the same day: U14 already holds deployment, live configuration and cost control, and capacity
is a different question that draws on almost every note, so it is written last. U14 keeps the
house's spending limits; U15 treats money as one more row only where a budget stops games.

## The method

1. List every resource a running game uses.
2. For each, find what one game uses, the limit, and where the limit is set.
3. Divide the limit by the per-game use. That is the number of games at which the resource runs
   out.
4. The smallest of those numbers is the bottleneck. It is the basis for a cap on running games.
5. Say for each figure whether it is measured, arithmetic, or unknown.

Terms: capacity planning (the exercise), bottleneck (the limit reached first), load test (measuring
it instead of calculating it).

## The table as far as U2 and U3 fill it

| Resource | What one game uses | Limit, and where it is set | When it is used up | Status |
|---|---|---|---|---|
| Main-pool threads | 1 by day, up to 9 in a night step | 64, `server/app.py` | Work queues, no error, no time limit | Arithmetic: a night step in 7 games asks for 63 |
| Per-phase threads | One per seat in a day or pack phase, so up to 10 (changed from 8 on 2026-11-12, not deployed) | None across games; each phase's pool is separate from the 64 | Nothing refuses; the operating system's thread limit is far away (about 191,000 on the host, not read inside the container) | Measured for one phase, locally |
| Memory | Not known | No container limit; host 23 GB, about 12 GB available; about 256 MB idle | The process is killed, and every game with it | Idle figure measured; per-game not measured |
| Checkpoint connections | Shared | 4, behind one lock, so one save at a time | Saves queue; 30 s wait, then an error | Lock measured locally with a fake database |
| Lesson-store connections | Shared | 4, behind one lock held across the embedding call | Lookups queue; 30 s wait, then an error | Measured locally with a fake embedder |
| The server's own connections | Shared | 5, plus 10 under load | 30 s wait, then an error | Read in code |
| Browser connections | One per viewer, each with an unbounded queue | The operating system's open-file limit, not read | New connections refused; a slow viewer's queue grows in memory | Not measured |
| Model calls in flight | Up to 10 | The provider's rate limit, per key | 429 errors, then the stall and rescue path | Not measured against a limit |
| Processor time for Python code | Small per call (building prompts, parsing replies) | 4 processors, and one thread runs Python at a time | Everything slows together | Not measured |
| Games running at once | 1 | No limit | Nothing refuses a game | Read in code |

## What the table has to settle

- **The cap on running games.** Every row above is unbounded only because this one is. It cannot
  be chosen until memory per game is measured (one game, then several, watching the container).
- **The main pool's size follows from the cap, not the other way round.** 64 came from one
  incident. With a cap: cap x 9 for a night step, plus room for route jobs and checkpoint saves. A
  pool starts a thread only when work needs one, so a high maximum costs nothing while idle.
  Raising 64 without a cap only moves the queue to the provider's rate limit, the checkpoint lock
  or memory.
- **Which row is the bottleneck today.** My guess before measuring: the two locks or the provider's
  rate limit, well before threads. A guess, to be replaced by the division in step 3.
- **What a refused game is told**, and what a viewer sees.
- **The answer beyond one process**: where the design changes (workers, a shared channel for
  events), which is U5's seed notes and U2 section 3.8.

## An async engine, reconsidered (2026-11-12)

- U2 section 3.3 records why the engine stayed blocking code on threads in August: the size of the
  rewrite, the library's blocking calls not running an async graph, and the danger of a partial
  rewrite. The first reason has weakened (the rewrite is cheap to write) and the second is a
  contained change (one `asyncio.run` at each batch, command-line and test entry point).
- What it would buy: no thread budgets (the 64 and the per-phase pools go, replaced by a
  semaphore where a limit is wanted), no thread locks, and cancellation, which a turn deadline and
  a stalled model call both want.
- What it still costs: proving the engine behaves the same (about 1,400 engine tests, one of them
  already dependent on thread order), and finding every blocking call on the path, since one left
  behind freezes every game with no error. The two library locks are a separate fix either way.
- Not decided. The first step, if taken, is a count: which functions and which library calls
  would have to change, and which of those libraries have async versions. For a new project the
  answer is simpler: async from the start.

## The claim this supports

Today: "one process, a handful of games; the limits are known by arithmetic, not by a load test,
and nothing caps the number of games." After the measurement and the cap: "up to N games, with the
resource that sets N named and measured."
