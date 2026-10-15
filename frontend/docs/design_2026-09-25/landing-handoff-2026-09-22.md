# Werewolf landing page — handoff

## What this is
Landing page for **wolf.liuhaochen.com**, a multi-agent LLM werewolf game.
Nine LLM agents play social deduction; every private deliberation is recorded and
opened when the game ends ("the X-ray"). Finished games are archived as replays.

**Audience, in priority order:** (1) interviewers in AI engineering / agentic AI
evaluating this as a portfolio project; (2) laypeople who want to play the game.

## The prototype
**https://claude.ai/artifact/CcqMvd52peTym5r7EFjPPu**
Everything decided is in here. Paste the link in a new chat and Claude can read the file back
into the workspace and keep editing in place (the same link stays valid, it does not create a copy).

## Design system
- **paper vs glass** — anything inside the game fiction (role cards, seats, tickets, slates) is
  parchment printed in faction ink; the instrument that looks at it (theater, X-ray, card frames)
  is glossy dark.
- Palette: warm black `#0c0a07`, panel `#17130e`, panel-2 `#211b14`, amber `#e0a63a` primary,
  factions town amber / wolves red `#e3503f` / evil-neutral violet `#9d7cff`, paper `#ecdfc3`,
  paper-dk `#cbb992`. Dark faction inks: town `#4a2e0a`, wolf `#4a120c`, killer `#241548`.
- Type: **Outfit** on dark surfaces; **IM Fell English** only on paper.
- Radius 12 / 20 / 28, deep soft shadows. Ink-wobble SVG filter applies to printed text and rules,
  never to sprites.
- Pixel art: 12×12 three-tone sprites in faction ink — placeholders for real HD-pixel portraits.

## Page order and what's settled
1. **Hero** — two hung paper seat tags ("Play solo" / "Play with others") on a faint rail, tilted,
   punched holes. Mobile: tags lie flat, no rail or thread, hole in the top-left corner.
   Labels beat "Play with friends" (overpromises — the lobby has public rooms) and "Solo/Multiplayer"
   (flat). Room count shown by default.
2. **Replay theater** — stage and transcript side by side, controls on a glass bar over the stage.
   Seat cards are number-first: large Fell numeral, role sigil reversed out of a faction-ink band at
   the foot. The same card appears at 28×36px as the speaker chip on every transcript line.
   Transcript column warm ink `#120d07`. Row height pinned with `clamp(400px, 34vw, 520px)`.
   Mobile: square stage, smaller lens, tighter seat ring, controls in normal flow below the scene.
   **Decided but provisional — see below.**
3. **The roles** — six parchment role cards, click to flip. Unchanged throughout.
4. **One turn, three layers** — three-card carousel in an instrument-rack frame. **Unresolved.**
5. **Latest games** — the slate: clapperboard in the ticket's materials, faction-ink stripe band,
   ruled fields (Record / Days / Ended / Model), faction sigil as a 5.5% watermark bleeding off the
   corner, "REPLAY" plaque in the band, clapper snaps on hover, instruction line above the grid.
   Card border tinted 12% with faction ink.
6. **Footer** — centred sign-off: heading, ongoing-project paragraph, API-key panel, four underlined
   text links, centred meta line. No buttons, since both play actions live in the hero and nav.

## Open items

### 1. The explainer section — the main open item
Two separate questions, both prototyped:

**Layout** — https://claude.ai/artifact/8aEMGinDkkjB27jUsD2Rde
Five patterns: alternating rows, sticky pin, bento, numbered ledger, tabs. Recommendation was
alternating rows, since the page already has two card grids. If the claims end up without visuals,
the numbered ledger is the better fit.

**Visuals** — decided against screenshots (duplicates the theater), icons (filler) and generated
images (collides with the pixel art). Two sets built:
- Dual-audience: https://claude.ai/artifact/DumuPSWxbkCBZqNpugRGSS
  said/thought flip, **spot the wolf** interactive, memory-between-games animation.
  Suggested mapping: flip → the X-ray, spot the wolf → the game, memory → the research.
- Research-facing: https://claude.ai/artifact/DxSNtmVUiD5s5aLyKfrzoU
  live novelty-gate widget, turn-pipeline SVG diagram, archive chart. Judged too technical for the
  player audience but a good fit for a separate portfolio write-up. **The chart's numbers are invented.**

Also unresolved: the heading still says "One turn, three layers" but the cards are now three
*mechanisms*, and the first card holds two layers.

### 2. The replay screen — deliberately deferred
The full-screen replay theater **does not exist yet**. Decision: build that first, then design the
landing demo as a reduction of it. The demo may end up deliberately different — it has ~5 seconds to
land one idea, while the real theater serves someone who already committed. Three decisions worth
settling early because they are expensive to retrofit:
- **names or seat numbers** — everything is currently built around numbers
- **the sprite canvas size** — one number everything else scales from
- whether the landing demo is the same component in reduced mode, or a separate cut-down build

### 3. Content placeholders
- **The memory claim** (carousel card 3, memory visual) says agents accumulate memory across games.
  **Unverified.** Must not ship as an unqualified claim; a clearly scoped negative result is worth more.
- **The API-key wording** ("used for that game only, discarded when the game ends, never written to the
  archive") is a security promise and must be checked against the implementation. Also belongs at the
  key input, not only in the footer.
- "Spot the wolf" needs real quotes from real games — invented ones are the same problem as the chart.
- "game 0412" in the theater and X-ray headers is invented.
- Footer meta: `[your name]`, `[N] games archived`, `[year]`. Privacy needs a real page.

## Data contract (Latest games)
`GET /replays?limit=6` → `ReplayBase[]`, newest first:
`game_id` (uuid), `winner` ("villagers" | "wolves" | "serial_killer"), `days` (int, 4–5 observed),
`n_humans` (int), `n_events` (int), `cast_role_counts` (currently invariant: 3 villager, 2 wolf,
healer, vigilante, investigator, serial killer), `model` (string, `""` on ~1/3 of rows),
`finished_at` (ISO-8601 | null).

Not rendered by choice: `n_events` (developer metric) and `cast_role_counts` (invariant).
`model` is the only field that meaningfully varies; empty renders as "Unrecorded — column added later".

**Wanted but not yet provided:** `final_seats` (role + alive per seat), per-day event data,
`ended_at` phase (day/night).

## Traps when editing the prototype
- The string `/* ---------- latest games: the slate ---------- */` appears **twice**, once in
  `<style>` and once in `<script>`. A naive replace-before-anchor lands CSS inside the script block
  and silently breaks all JS. This happened twice.
- Control styles are scoped to their container (`.overbar`, `.side .foot`). Moving a control without
  re-scoping leaves it unstyled.
- Desktop overrides added late in the stylesheet beat the earlier mobile media queries. Mobile rules
  must come after.
- Flex children default to `min-height: auto`. A grid row with no definite height gets driven by the
  transcript's content, and the stage resizes during playback.