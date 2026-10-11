# The ten-seat pass — wiring the frontend to the Phase 3 cast

Started 2026-10-10. The engine deals ten seats from a twelve-role pool (the role sheet,
`evidence/game_play_enhancement/role_sheet.md`); the wire changed on 2026-10-09 and 2026-10-10
(`event_derivation.md`, night sections). This document is the pass's plan and its rulings; the
beat sheet stays the source of truth for what a scene shows and the agents doing a slice change
its rows first. The census of every nine-seat assumption is
`evidence/game_play_enhancement/phase3_wiring_census.md` §7.

Goal: landing, ticket, live and replays show the full cast, a human can complete every turn the
engine can ask of it, and an archived nine-seat replay still plays. Then user testing.

## 1. Rulings for this pass

Owner's, before the pass: the side is **Town**, not Villagers, UI-wide (2026-10-07); the
reanimated attacker kinds use the body kind's icon, no new icons (2026-10-10); memory stays
off for the ten-seat game until a store exists for it (the seeding runs in parallel,
`evidence/memory_system/ten_seat_seeding/plan.md`); no balance dials in this pass.

Mine, flagged for the owner (change here first if overruled):

- **A null winner is a draw** (`game_over.winner: null`; engine: no side alive, or a day-cap
  tie). The UI says "Draw"; a draw has no side colour. The neutral's result
  (`game_over.neutral_result`) is a second line on the game over, never the winner.
- **The necromancer wins under the lone killer's colour** (the serial killer's violet): one of
  the two is dealt, and both play for themselves. Named "Necromancer" where the winner is named.
- **The pack is a role set, not a role**: `wolf`, `chanteuse`, `illusionist`. Everything that
  tested `role === 'wolf'` tests membership. A pack mate's role is not on the wire (the deal's
  `pack` lists seats), so the wing's band says "Your pack", not a role.
- **Seat count comes from the roster** (`game_started.seats`), never a constant: the stage lays
  out nine or ten from the game it is showing. The platform (the waiting room) shows the room's
  size from the lobby.
- **The selectable cast is the pool** (twelve roles); villager and wolf exist only to render
  archived games. Old event kinds (`wolf_vote`, `investigation_result`,
  `vigilante_confirmation`, `bullets_remaining`) keep their handlers for those games.
- **A concealed body stays concealed everywhere** the viewer is not the X-ray: morning roll,
  roster, notebook, ledger, record, public replay show "role hidden" (the wire sends `role: ""`
  and `concealed: true`). The X-ray (replay, observer tier) may show the role from
  `roles_assigned`.
- **A no-action answer is the server's word**, never derived: the candidate in the request that
  is one of `hold_fire`, `no_check`, `no_watch`, `keep_sigil`, `no_conceal`, `stay_put`,
  `not_yet`, `abstain`. If none is listed, the turn has no "no one".
- **The human claim selector is deferred**: the turn's POST body has no claim field
  (`HumanTurnResponse`, extra fields forbidden), and this pass makes no wire change. The
  summariser's fallback covers a human's spoken claim. Queue it for the next wire epoch.
- **The sigilist's death glyph** is new pixel art (a ward mark); it awaits the owner's eye.

## 2. The human turn, every shape the engine asks

`input_request.action_kind` → what the room shows and what the POST carries. The POST body
(`TurnPayload`) grows `body` and `role_named`; everything else is `{target}` from `candidates`.

| Kind | Who | Room | Control | POST |
|---|---|---|---|---|
| `discuss` | all, by round | day dock | text, pass where allowed | `{message}` / `{pass_turn}` |
| `vote` | all | vote table | a seat, abstain when listed | `{target}` |
| `wolf_discuss` | pack, up to 3 rounds | pack room, chat | text, or **pass** (new: the engine ends the chat once every wolf passed a round) | `{message}` / `{pass_turn}` |
| `carrier_kill` | the carrier wolf only | pack room, the plate | a seat ("Kill seat N") | `{target}` |
| `block_target` | chanteuse | pack room | a seat ("Block seat N") | `{target}` |
| `conceal` | illusionist | pack room | two plates: "Hide the victim's role" / "Keep your conceals" (no photos; `candidates` = `conceal`, `no_conceal`) | `{target: word}` |
| `healer_target` | healer | own room | a seat | `{target}` |
| `investigator_target` | investigator | own room | a seat, "Keep your checks" | `{target}` |
| `sentinel_target` | sentinel | own room | a seat ("Watch"), "Keep your watches" | `{target}` |
| `trailseer_target` | trailseer | own room | a seat ("Follow") | `{target}` |
| `vigilante_target` | vigilante | own room | a seat ("Shoot"), "Hold fire" | `{target}` |
| `sigil_target` | sigilist | own room | a seat ("Mark"), "Keep your sigils" | `{target}` |
| `serial_killer_target` | serial killer | own room | a seat ("Kill") | `{target}` |
| `necromancer_target` | necromancer, from night 2 | own room | **two photo lines**: the bodies (`bodies`, "act through") above the targets; "Stay put" | `{target, body}` |
| `speculator_pick` | speculator, until picked | own room | side plates from `candidates`: `town` → "Town", `wolves` → "Wolves", `lone_killer` → "The lone killer", `self` → "Yourself", `not_yet` → "Not yet" | `{target: word}` |
| `bet_target` | fortune teller | own room | a seat ("Bet on"), the own seat when listed ("Bet on yourself"), and an optional role (a row of the twelve sigils, "name a role for two points") | `{target, role_named?}` |

Sealed plates follow the beat sheet's pattern ("You watch seat N tonight", "Seat N is blocked
tonight", "The victim's role is hidden tonight", "Through seat 3, you act on seat 5", "You pick
the Town", "You bet on seat N as Healer"). The card note generalises the caps: `uses_remaining`
counts checks, watches, caps, sigils, conceals, self-bets, the pick, in each role's word.

Rooms: every solo role has a painting (`SPRITES.rooms`); the chanteuse and the illusionist use
the pack's. A role with nothing to do tonight (the necromancer on night 1, a spent vigilante)
gets no request and sleeps in the lobby.

Everything above is one request at a time, so refresh and reconnect work as today: the pending
request is refolded from the log, and a sent answer seals on the server's 409.

## 3. What the fold must carry (new wire)

- `input_request.bodies` → `me.pending.bodies`.
- `night_record` → a private result `{kind: 'night_record', actor, action, target, result,
  outcome, seen}`; the morning's dashed "Only you" line and the Record tab read it. The pack's
  kill record arrives at every wolf with `actor: "wolves"`.
- `uses_remaining` → `me.role.uses` (replaces `bullets` for the card chip; `bullets_remaining`
  still writes it for old games) and the X-ray's per-seat results.
- `night_result.deaths[].concealed`, `saves[]` (every save; `save` keeps the first), `pick`
  (the side a speculator picked, announced at dawn).
- `wolf_message.passed`, `wolf_kill_decided.carrier`.
- `game_over.neutral_result`; `game_started.lineup`.
- `role_assigned.uses`; `speech.claim` (the claim ledger reads it server-side; the stage may show
  it in the Record tab later, not in this pass).

## 4. Slices and order

1. **Compile** (done first): winners, Town, attacker kinds, the ticket's pool roles.
2. **Mappings and fold**: pack-role set, lone-killer set, roster-derived seats, the night
   census mirroring `server/game/pacing.py` (superseded by §10: one unit per living seat),
   the fold's new fields and handlers, view types, tests on a ten-seat fixture.
3. **Human inputs**: `Answer`/`payloadFor`/`TurnPayload`, the rooms by kind (§2), the pack room's
   pass/carrier/skills, the beat sheet's §6 and §7 rows.
4. **Morning, roster, record, game over**: the roll's new rows and concealed bodies, the roster
   and notebook, the Record tab's night records, four winners and a draw with the neutral line.
5. **Landing and ticket**: the twelve cards with "eight fixed roles and two drawn seats", Town,
   the memory toggle disabled with its note, the landing's role hand on the pool.
6. **Acceptance** (§5).

Fixtures: `tests/fixtures/translator_golden.jsonl` is a full ten-seat game (serial killer +
fortune teller lineup, a sigil kill, a concealed body, a neutral result) → wrap it as
`frontend/src/stage/fixtures/replay-phase3.json` the way `replay-phase2.json` wraps the Phase 2
golden. A necromancer + speculator game comes from a batch capture
(`evidence/game_play_enhancement/data/phase3_balance_4/e0N.chunks.jsonl` through the
translator, `tests/fixtures/stream.py`). The nine-seat fixtures stay as the regression.

## 5. Ready for user testing

P0 (before the first tester): typecheck, lint and unit tests green; a ten-seat replay plays
start to end in both lineups; the nine-seat fixtures still play; every kind in §2 answerable in
the workbench with the server's words; a concealed body hidden on every public surface; the
game over for each of the four winners, a draw, and a neutral result.
P1 (first week): the ticket's twelve cards readable on a phone; the landing on the pool; the
X-ray night for the new roles; keyboard access to the cards.
P2: screen-size sweep, replay seeking across the new night beats, the hallucination screen's
Record tab on ten-seat games.

## 6. Known gaps found during the pass (not fixed here)

- **Drawn games are not archived.** `server/storage/replay_service.py` keeps only rows with a
  winner and `ReplayBase.winner` is non-null, so the archive's Draw chip matches nothing until
  the server archives draws. That is a wire change (a nullable winner on the replay row), so it
  waits for the next wire epoch, after the memory seeding's no-wire-change window.
- **The human claim selector** (§1): same reason.

## 7. Follow-ups queued inside the pass (from the slice reports) — all done 2026-10-10

- `beatsFor.ts`: a `morning.only-you` beat for a `night_record` (seen by the record's seat,
  subject = its target, one beat for the pack's kill at the lowest seq); the save chips for
  every save in `saves`, not the first; the roll's hold counts the pick row.
- `drawer-lines.ts`: the X-ray drawer shows the pack's kill record once, not once per wolf;
  the dawn line's seat filter counts every save.
- Beat sheet §1 row 4 (`deal.your-pack`: the pack card, not "turns to the wolf"); §11 names the
  Record's night section.
- Wording: invented neutral lines use `ROLE_NAME` casing ("The fortune teller won, with 2
  points"); the engine's own lines (the pick) stay as the engine writes them.
- X-ray night: the carrier's kill and its skill both arrive as `night_action` for the carrier's
  seat, so `nightBranchesOf` makes a seat branch beside the pack's with the target overwritten
  by the skill (P1: the X-ray night for the new roles).
- Nine-seat archives now get the pool's plate and notebook order (healer after vigilante).

## 8. Acceptance, 2026-10-10 (uncommitted, P0 met)

Typecheck 0 errors, lint clean, vitest 56 files / 1397 tests, Playwright 13 baselines regenerated
and checked by eye (ticket at 390 and 1440, rooms, landing, replays slate, game-over, record
tabs, notebook order); every §2 ask kind rendered in the workbench's ten-seat situations; both
ten-seat fixtures and two nine-seat ones stepped through every public and X-ray beat with no page
error. Shots were reviewed for the concealed-body morning, the speculator's side plates and the
necromancer's two photo lines.

Fixed during acceptance: a ten-place platform situation in the workbench; the phone wrap of the
bet's role row and the side plates; the pack chat's Pass overlapping the panel; "Your pack" in
the pack room's rail; the fortune teller / sigilist / chanteuse cards overflowing; "Necromancer"
and "Fortune teller" clipped on rail bands.

For the owner to rule (not changed):
- The necromancer win and the draw game-over were verified by unit test only: no fixture holds
  either, and the workbench loads fixtures from a fixed list.
- No fixture has a reanimated attacker type, so that roll row is unit-tested only.
- On the phone the chosen bet photo partly covers "name a role for two points".
- The speculator's X-ray spoke hangs seat photos it does not use.
- The deal from a pack seat shows two "Your pack" beats (seq 6 and 7).
- Prettier: `foldEvents.ts`, `GameEndedCard.tsx`, `night-lobby.test.ts` carry pre-pass
  formatting debt the pass did not clear (whole-file reformat would hide the diff).
- The sigilist's pixel death glyph (§1) still awaits your eye.

## 9. Review batch, 2026-10-11 (uncommitted)

Six review findings fixed and the two stale landing tests rewritten: the pack chat's send state
now comes from the container (reopens on a 422, browser-tested); nine-seat replays read a frozen
`LEGACY_CARD_TEXT` chosen by `isNineSeat(view)` (no lineup on the wire); the night lobby's link
reaches a wolf's own skill room and then the pack's (`actedTonight` returns each seat's rooms in
play order); the Record tab gets a final page for the last night at game over, records only;
the shared side label is "Lone killer" (winners keep their role names); a draw says "No side
has won". tsc 0, lint clean, vitest 1413, Playwright 160 green, one baseline regenerated
(`replay-room-card.png`: the old investigator words). Archive compatibility is now complete for
card text.

## 10. Ruling 2026-10-11: the night bar's total is the living seats

Owner: the lobby's "N acted" counting rooms is correct. The LIVE progress bar must not leak which
roles have uses left, so its total is the number of publicly alive players, one unit per living
seat every night, whether or not that seat acts; padding timers fill the units that never tick.
In a replay a seat with no night action has no room to click, which is fine. Implemented in
`server/game/pacing.py` (the vote bar's total moves to the same alive count, fixing an overcount
after a concealed death) and mirrored in `nightUnits`.
