# Explanation prototype: Frontend (chapter 8)

Pages: `writeup/frontend/frontend.md` (Level 1) and three Level 2 pages:
`event_stream_and_sync/`, `viewer_authorization/`, `rendering/` · Date: 2026-11-22
Checkpoint: waived. The owner asked on 2026-11-22 for "the same treatment for chapter 8 as chapter
7 today": a full draft first, a different model reviews and revises it, the owner then reads the
revised version; Level 2 pages wherever the Level 1 page would otherwise be too long.

Authoring material, not page copy.

## Reader and explanation

- **Reader outcome:** the reader can say what the browser receives from a running game and why it
  is events, how the server keeps each viewer to the events they may have, how a page recovers
  from a dropped connection, and why the stage once rebuilt itself on every step.
- **Starting knowledge:** chapters 1 to 7 supply the game, the engine, the human turn and the
  server's two saved records. New here: the event stream as the browser uses it, the per-viewer
  check, side channels, and React's identity rules.
- **Concept order:** events against state and tokens → the view computed from the log → catch-up
  and duplicates → a dead connection → the per-viewer check and where it runs → side channels →
  identity, remount and re-render → where state lives → cache keys.
- **Likely confusion:** that hiding in the page protects hidden information; that a viewer holding
  event 50 holds everything before it.
- **Treatment-map stories used:** S1 and S4 (event stream page), S3 and S8 (authorization page),
  S10 in its React part only (rendering page), S6 (one paragraph on generated types). S2, S5, S7
  and S9 are links to chapters 1, 7 and 6.

## Rulings carried over from chapter 7 (owner, 2026-11-22)

No first-person pronoun; technical headings; no development or deploy status; no gathered list of
limitations at the end of a page, with each limit beside the claim it bounds; tools named but not
their wiring; "viewers" and "players", never "the table"; diagrams vertical. "One level deeper" is
a guide for leaving overly complex material off, not a gate.

## Evidence

No chapter 8 report was written (agreed 2026-11-22). Each page's sources comment cites code, tests
and the dated frontend records directly: `frontend/docs/server_client_transport.md`,
`frontend/docs/multiplayer-audit-2026-10-15.md`, `frontend/docs/learning/react_identity/` and
`realtime_and_sync/`. The notes `evidence/_study/engineering_notes/` 06, 07 and 12 are the index
to those sources and hold the next level of detail. Code was read on 2026-11-19 (U6) and
2026-11-22 (U7, U12). Measurements are quoted with their conditions and were not repeated.

## Questions closed by the owner (2026-11-22)

1. **Authorship.** The pages do not say who designed or wrote the frontend. The neutral voice stays.
2. **The rendering page.** Kept as a Level 2 page, limited to React's identity rules, with the phone
   mentioned only as where the fault showed.
3. **Accessibility.** No line on the pages for now.

## Trial record

- 2026-11-22: first full drafts of all four pages by Claude. No editorial or claims reviewer run.
  Word counts of page copy at first draft are in the hand-over message.
- 2026-11-26: the owner renamed the chapter to "Client-server architecture" (the title on the Level 1 page and in the
  Level 2 pages' top lines). The folder and file names stay `frontend/`. The Level 1 page was
  restructured the same day after another model's rewrite, and the night's progress bar was added
  to its side-channel section at the owner's request.
