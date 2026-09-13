# The server, as I would tell it in an interview

One page. Each answer is a decision, the reason, and what it cost or ruled out. Rehearse
these out loud; open the file only for the one you stall on.

## "Walk me through a player submitting a turn."

The browser posts to `/turns` with a seat cookie. The route turns the cookie's token into a
seat name and hands the answer to the session. The session keeps three dicts keyed by seat:
the question the engine asked, the engine's own id for that question, and an empty Future.
The answer is checked against the question's rules (same rules as the CLI game), the seat is
crossed off, and the Future is set. The game task has been asleep on `gather` over every
seat's Future; the last answer wakes it, and it resumes the engine once with the whole batch.

Why a Future per seat: the engine asks several humans at once in a night step and wants one
resume with all the answers. Why cross the seat off first: a second click from another tab
must fail on the missing question, never reach a Future that only takes one value.

## "What happens when the server restarts mid-game?"

Three records survive, each the authority on one thing: the game row (identity, seats,
status), the events table (everything the players were sent), and LangGraph's checkpoint
(where the engine actually is, including open questions). On boot the registry rebuilds
each running row into a session, re-parks any open question from the checkpoint, and either
starts the task or, for a game that ran on a player's key, waits. Keys are never stored, so
any seat holder resubmits it on the page, the server tries it on the provider, and the game
continues from its checkpoint.

The cost: a step in flight at the crash re-runs, so one turn's wording can differ from what
a viewer briefly saw. Accepted; the record stays self-consistent.

## "Why don't waiting rooms survive a restart?"

Because a matchmaking lobby closes when its server goes away, and players expect that. A
room lives in memory; its database row is born when the game starts. That also means the
row exists only for games that consumed a model call, which keeps the funding count honest.

## "How do you stop a villager seeing wolf chat on a live stream?"

Every event carries a tier: public, wolves only, one seat, or observer. The session fans
every event into every viewer's queue without looking. The stream route checks the tier
against the viewer's seat per event, at send time, because a seat can be dealt after the
stream opens. At game over the rule flips and the held-back events flush to everyone.
Progress bars are the same idea one level up: the tracker counts finished night roles and
cast ballots privately and publishes only the running total, with padded completions so a
role that did nothing is indistinguishable from a slow one.

## "What about a player who walks away?"

Two clocks per waiting seat: 120 seconds to think, cut to 30 once their last stream drops.
When it runs out and another human is connected, that one turn is played by the seat's own
agent and the game moves on. If nobody is connected the game parks: nothing runs, nothing
is billed, and the first player back restarts the clocks. A parked game has a shelf life,
an hour solo and a day for a table, after which a sweeper drops it.

## "How do you keep the demo from bankrupting you?"

The house pays for games up to a daily cap, counted from the games table itself rather than
a counter that could drift. The cap, the default model and an off switch are live settings
behind an admin endpoint, so they change on the day, not on the next deploy. A player who
brings a key runs any model and is never counted. The credits behind the house end on
2026-10-27; the switch is what makes that date survivable.

## The failure story

I believed for a day that the engine's checkpoint always led the events table, so a crash
could only lose events, never duplicate them. Reading the LangGraph loop showed the reverse:
a task's output streams the moment it finishes, and the step's checkpoint is written after
every task in the step, in the background. The events table leads by up to one step. What
saves it is that committed work comes back on resume tagged as cached and is dropped, and
the vote nodes are cached so a re-run returns its recorded result. The remaining window is
one database write wide and needs a hard crash. I recorded the ordering in the translator's
docstring and pinned the cached-drop with a test over every part of a real game, and chose
not to add a blanket dedup, because two event types legitimately repeat with identical
fields and a key would swallow a real turn.

## "What would you change?"

A stall watchdog: a provider that hangs leaves a frozen board and keep-alives, and nothing
notices. The delivery and presence code could be its own object beside the clocks and the
pacing tracker; the session file is the one place that keeps absorbing things. And the
storage layer is tested only through fakes; a container-backed test would catch the
migration mistakes the fakes cannot.

## "How much of this did you write?"

I designed it, directed the build, and reviewed it line by line until I could defend any
part of it. Several things I found in that review were wrong and got fixed. For the three
core files I can draw the design and explain any method; for the rest I own the contract
and the tests, and I would open the file.
