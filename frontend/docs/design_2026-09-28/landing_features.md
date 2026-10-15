# The landing's middle section: three features (draft for the owner, 2026-09-28)

Replaces "What's under the table" (`UnderTable.tsx`, three cards about one agent in one game:
the private note, the reads, the lines held back). The owner's brief: lead with what makes
the game fun, and give the mechanism as support. A player reads the headline; an interviewer
reads the line under it. The depth goes to the "How it's built" write-up, which each card
links to once it is published.

Status: **built 2026-09-28** (`Features.tsx`, `features.ts`, `Features.module.css`, on the
same walnut bench as before). Cards 1 and 2 describe features that are live today; card 3's
second half ("see who played best") waits on the scorecards (`scorecards_plan.md`). As built,
card 3's *How* line is the live table (every seat sees only its own side; a quiet seat's agent
takes the turn when its clock runs out), card 1's *How* line is shortened because the loop
strip above it carries the steps, and on a phone each card takes its own height (the lessons
card is far the longest). The "How it's built" links wait for the write-up's URL.

## Section head

> **What makes it different**
> You can read the agents' minds, borrow one when you're stuck, and bring friends to beat
> them.

## Card 1: read their minds, then watch them learn

> **Read their minds, then watch them learn.**
> The X-ray shows each agent's private reasoning beside what it said out loud: its notes, its
> read on every seat, the lessons it weighed before speaking, and what the game taught it
> afterwards.
> *How:* after a game, each agent writes down what worked and what didn't. The lessons are
> merged with earlier ones and handed to the agents in later games. With memory on, the
> agents draw on lessons from past games. Whether they win more because of it is the open
> research question.
>
> (Owner, 2026-09-28, option A: the card says "merged", not "scored". The wolf and killer
> lessons in the served snapshot were merged without being scored, so scoring is left to the
> write-up.)

- **Exhibit:** from game 9369A5C (the carriage's game, played with memory on), one lesson a
  wolf weighed before the day 2 vote (`memory_consulted`, seat 8, seq 100) next to one line
  of what the game taught (`memory_extracted`, seq 407). Seat 8's private note on each day
  (today's card 1, with its day tabs) can stay as the "reasoning" half.
- **Why this wording:** it stays true whichever games the lessons come from. Today, this
  site's games don't write lessons back (`run_config.py` sets `dump_enabled: False`), and the
  agents draw on a snapshot from research runs. That's temporary and may change at any time
  (owner, 2026-09-28), so the copy names neither case: no "from your game", and no "from our
  research runs only". The benefit wording follows the 2026-09-17 ruling: memory is shown as
  a mechanism, never as "they play better".

## Card 2: stuck on your turn? let your agent draft it

> **Stuck on your turn? Let your agent draft it.**
> Jot rough notes and your seat's own agent turns them into a line, or hand it the whole
> turn: the vote, or the night's move.
> *How:* your agent sees only what your seat is allowed to know: your role, your own
> results, the public talk, and the wolves' channel only if you're a wolf. That wall is
> built where each agent's prompt is put together, not by asking the model to keep a
> secret, and every agent at the table stands behind the same one.

- **Exhibit:** the turn dock as a paper card: the rough notes below
  → "Draft from notes" → the drafted line. Beside it, two short lists: *your agent sees* /
  *it never sees*.
- **The drafted line is real (captured 2026-09-28).** The turn was seat 6's day 3
  discussion turn in game 9369A5C, rebuilt from the log at the moment the seat passed (after
  player 8's second line). Seat 6 is a villager and was lynched that day; seat 8 is a wolf.
  The same `draft_from_notes` the server calls drafted it, on the game's own model (Gemini
  3.5 Flash-Lite). Nothing was sent or archived.
  - notes: `8 changed tack the second 5 pushed back. that's what a wolf does. push on 8`
  - draft (verbatim, the second of two): *"Player 8 instantly flipped their stance the moment
    player_5 pushed back on them, which is classic wolf behavior, so we need to put pressure
    on player_8 right now."*
  - Caption: "A real draft, from day 3 of the game above. Seat 8 was a wolf."
- Live today: "Draft from notes" (three a turn, the wait given back to the clock) and
  "Let my agent speak" / "Let my agent play this turn" in the turn dock.

## Card 3: bring your friends, beat the machines

> **Bring your friends. Beat the machines.**
> Open a room, send the link, and your friends take seats at a table of agents.
> *(once the scorecards ship:)* When the game ends, every seat is scored, human or agent, and
> you can see who played best.
> *How (once the scorecards ship):* scores come from what each seat actually did, its votes,
> saves, finds and kills, checked against the true roles, not from an AI's opinion.

- **Exhibit now:** a room's roster (a few named paper chips among the agents' puppets) with
  the invite link, and the "Open a table" stub.
- **Exhibit later:** a scorecard, one line per seat (see `scorecards_plan.md`).

## What leaves the landing

The reads waffle and the lines held back (today's cards 2 and 3) go. Both still live in the
replay's X-ray. The scheduler ("every line says why the agent spoke") is a candidate for the
write-up, not the landing.

## Open

- The "How it's built" link: the portfolio write-up's URL, when there is one.
- The layout (proposed, Claude): keep the walnut bench and its brass plates, with three new
  cards on it. The bench already matches the carriage, and its phone tabs and fixed card
  height carry over unchanged.
- Card 1's loop (proposed, Claude): a four-step strip under the exhibit, in plain words, no
  pipeline names: **Reflect** (after a game, each agent writes down what worked and what
  didn't) → **Distill** (lessons are merged with earlier ones) → **Recall**
  (next game, it pulls the lessons that fit its situation) → **Weigh** (it decides whether
  each one applies; the X-ray shows the verdict). The full pipeline goes in the write-up.
