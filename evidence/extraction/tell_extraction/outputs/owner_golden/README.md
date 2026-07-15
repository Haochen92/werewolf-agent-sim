# Owner golden — adjudication protocol (the certifying gate)

This is the detector-blind golden that certifies the tell detector before its counts may feed
lift or credit. You are grading a **stored cached k=2 run** (the standing config) on 6 held-out
games nobody mined from. Until you finish, every detector accuracy number in the repo is
temp-golden grade.

**Blindness rules (the whole point):**

- Do NOT open `SEALED_do_not_open/` until phase 1 is committed — it contains the detector's
  answers and the game records with true roles.
- You judge role-blind, from the public transcript only, exactly the record the detector saw.
- The question per finding is always factual: *did this player exhibit this checklist behavior
  on this day, as shown by a quotable line?* — never "does this feel wolfy."

## Phase 1 — blind read (~30–40 min per game; games are independent, stop anywhere)

For each cell in `answer_sheet.md` (2 focus players × 2 channels per game):

1. Skim the whole game transcript once for orientation (who died when, how votes went).
2. **Vote cell** (fast, ~5 min): walk day by day. For each day look at the focus player's vote
   line, their stated reason, and how their vote sits against the room (early/late, with/against
   the pile, target voiced or not). Then sweep `checklist_vote.md` top to bottom and record every
   `(tell, day)` you can anchor with a quote (a vote line counts as a quote).
3. **Discussion cell** (slower, ~10–15 min): read only the focus player's messages, day by day.
   After each day, sweep `checklist_discussion.md` in blocks and ask "did any line this day do
   this?" Record `(tell, day, quote)`.
4. Only claim what you can quote. If genuinely unsure, keep it with a `?` suffix on the tell id —
   it will be scored both ways rather than silently dropped.
5. A `(none found)` cell is a real, valuable answer — don't force findings.

**On recall:** phase 1 is NOT expected to be exhaustive — no human free-read is. Do an honest
sweep, don't grind. Exhaustiveness comes from phase 2's pooling.

**Commit before phase 2:** when done (even partially), say so / `git add answer_sheet.md`. The
sheet must be frozen before you see any machine answer.

## Phase 2 — pooled adjudication (~30–45 min total)

Open `SEALED_do_not_open/phase2_sheet.md`. It lists every candidate any instrument proposed for
your cells (detector passes + strong-model prelabels), **shuffled and source-blind** — you cannot
tell whether a row came from one instrument or three, so agreement can't anchor you. For each
claimed `(tell, day)`: mark `[y]`/`[n]` after checking the record (the printed quote is a
pointer, not proof), and add `+d` for days a candidate missed.

Your phase-1 findings ∪ your `[y]` verdicts = the golden. Scoring (done for you afterwards):

- **Precision** — detector rows judged against your ratified set.
- **Recall** — your ratified set recovered by the detector, *bounded by the pool*: a tell no
  instrument and no blind read surfaced stays invisible, and the report will say so.
- Your phase-1-only finds (things every instrument missed) are the recall ceiling's honest error
  bar — that's why phase 1 exists at all.

## What this unlocks

Certified precision/recall → the k=2 vs k=1 decision (half cost if one view suffices) → the
held-out lift table graduates from PROVISIONAL → credit wiring may consume tell counts.
