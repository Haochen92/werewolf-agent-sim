# Phase 3 wiring: the plan and the census (2026-10-09)

## The plan (agreed 2026-10-09, after an external review)

**Status, end of 2026-10-09:** steps 1 to 8 built and run (the frontend pass of step 6 excepted; its starting list is in section 7 below): the suite is green (1394 passed), three live games are read in `data/phase3_games/README.md`, the switch is done (the nine-seat prompts, schemas, rules and core strategy are deleted; the tag goes on the commit before). An external review (2026-10-09) found six gaps the suite missed; all six are fixed with regression tests (the role sheet's change log has the list; the wire gained `input_request.bodies` and `speech.claim`, both additive). Nothing is committed.

The wiring is graph wiring and the completion of the runtime rules, not only connecting the
settled prompts. Each slice lands with its tests; full AI games are the final acceptance check.

**Decisions taken (owner):** named graph nodes per role, sharing one implementation; structured
choices, not one target string; memory off for the ten-seat game at first; the solo role picker
offers all twelve roles and picking a drawn role forces that draw, rooms deal at random; the
winner stays a side, with a separate neutral result (a side draw with a neutral winner is
possible; living neutrals count in the parity numbers); the translator consumes the night's
authoritative outcome instead of reconstructing it; resources are spent in the resolution, once
per night, never in a turn node, so a human resume cannot spend one twice; tag the nine-seat game
before deleting it; archived replays keep validating; deploy only once the frontend understands
the new events.

1. **Role registry and the contracts.** `ROLE_SPECS` grows to the twelve roles and four sides,
   with explicit rules per role: what it does at night, from which night, its uses, whether it can
   be blocked or killed at night, whether it visits, and where its result goes (its own record,
   the morning report, the wire). Every `role == "wolf"` check and the two survivor buckets become
   side-based. The night choice (`Agents/schemas/night.py`) gains the structured fields the new
   roles need: the body a necromancer acts through, the role a fortune teller names, the side a
   speculator picks. One `night_choices` map on the orchestrator state, keyed by role, with a
   merge reducer so parallel branches keep every choice; the per-role target fields retire.
   Tests: the registry against the cards and the lineups; the reducer under concurrent writes.
2. **The deal and day participation.** Ten seats from the fixed eight plus the two seeded draws;
   the human's choice forces a draw. The day flow seats every dealt role: discussion and vote
   templates and schemas from the lineup, private context lines per card, the `claim` field into
   the claim ledger, the ledger's verbs extended. At this point a ten-seat game runs day-only
   with the new roles as plain seats. Tests: the deal (seeds, the forced draw), every role
   speaking and voting, the claim recorded.
3. **The solo night turns and the resolution.** One shared implementation behind the named
   nodes (`HEALER_NIGHT`, `SENTINEL_NIGHT`, ...): payload, turn, choice written to the map; the
   gates in the night router from the registry (alive, uses left, the one-time pick, the
   necromancer from night 2); the no-action words accepted by the resolver; private results
   delivered from the night record to the next day's prompt and the human seat. The resolution
   layer completed: borrowed-body visits and traces, the self-bet's protection, bets and the pick
   settled, uses spent, the Speculator's pick announced. Collect all choices, resolve once,
   deliver public and private results. Tests: each role's night on the real graph with scripted
   players; a human resume that repeats no AI turn and spends nothing twice.
4. **The pack night.** Chat (up to three rounds, carrier first, a pass, ends on a full round of
   passes), the carrier's kill, then each wolf's skill turn; the vote nodes removed. Tests: the
   rounds and the cap, the carrier rotation and the survivor, the block and the conceal through
   the resolution.
5. **The win.** Four sides in the counts; the lone killer may be the necromancer; the neutral
   result beside the side winner; the max-days winner and the messages. Tests: every ending in
   `test_determine_winner`, including a side draw with a neutral winner.
6. **Server and frontend.** The translator: the new nodes registered, the vote handlers replaced
   by the carrier's kill, the outcome consumed, the concealed role never published, the faction
   tier by side; pacing's night units; private seat events for the new results; the wire enums
   extended with the old values kept; the OpenAPI contract and the translator goldens
   regenerated. The frontend pass from the census (section 7), as beat-sheet rows first.
7. **The switch and cleanup.** Annotated tag of the nine-seat game; the old templates, rules,
   preamble, core strategy, output classes and enums deleted in one commit; the memory, leak and
   batch role sets updated; extraction gated or extended for the new roles.
8. **Full games.** A few AI-only games read in full, as Phase 2 step 8 did.


Every place the code assumes the nine-seat game: its six roles (villager, wolf, investigator,
healer, serial killer, vigilante), its three sides, nine seats and the pack vote. Taken before the
wiring, on the uncommitted Phase 3 tree, by a read-only sweep (Agents/prompts excluded, already
rebuilt from the role cards). Line numbers are as of that tree. The plan that works from it is in
the role sheet's change log and `discussion_evidence.md` §8.1.

Already in place but not connected: the pool and the draw tables (`Agents/schemas/roles.py`), the
ten-seat output schemas (`Agents/schemas/lineup_output.py`), the night layer with block, sigil,
conceal, watch, follow and the carrier (`Agents/rules/night.py`, `night_record.py`), the role
cards and the ten-seat templates (`Agents/prompts/`), and on the frontend the role names, sigils,
card text and night rooms.

## 1. The deal

- `Agents/config/game.py:17-31` — `initial_roles` is the nine-seat list. Becomes the ten-seat lineup with the two draws.
- `Agents/config/game.py:74-86` — the validator requires `wolf`, a healer, an investigator. Rewrite for the pool.
- `Agents/config/game.py:37` — `vigilante_bullets` is the only per-role setting; sigils and other uses need fields.
- `Agents/nodes/orchestrator.py:80-93` — the seeded deal; the two draws join this rng sequence (old seeds stop reproducing; `tests/engine/test_seedability.py:32,38` pins nine).
- `Agents/nodes/orchestrator.py:106-116` — the solo human-role swap; choosing a drawn role must force the draw.
- `Agents/nodes/orchestrator.py:122-125, 141-145` and `Agents/state/orchestrator.py:52-73, 97-100, 110-125` — one marker and one target field per old role; the new roles need theirs (or one generic map).
- `Agents/nodes/orchestrator.py:131-138` — `surviving_wolves` / `surviving_villagers` split on `role == "wolf"`; must split by side.
- `Agents/main.py:46-48, 194, 200-201` — legacy memory role keys, the CLI's human role, the bucket prints.
- `server/game/lobby.py:38` (`MAX_HUMAN_SEATS`) and `server/game/run_config.py:13,36` follow the config.
- Human role choice today: solo only — `server/schemas/requests.py:98`, `server/routes/games.py:50-53`, `frontend/.../ticket/RoleCards.tsx:19-26`; rooms deal at random (`server/game/lobby.py:8-12, 177`).

## 2. The night

- `Agents/graphs/parent.py:19-45, 108-325, 348-386` — five hard-wired night phases, one wrapper per role reading `*_player` and writing `*_target`; `:126` assumes the pack actor via role `wolf`.
- `Agents/graphs/night/*`, `Agents/nodes/night/*`, `Agents/state/night/*` — one subgraph, act node and state per role, bound to the old output classes.
- `Agents/graphs/night/wolf.py:28-57`, `Agents/nodes/night/wolf.py:53-54, 67, 97, 127-142, 185`, `Agents/state/night/wolf.py:11-47` — talk, then the plurality vote. Becomes chat, carrier, skills.
- `Agents/nodes/orchestrator.py:422-446` (`route_night_actors`) — phase list gated on markers and bullets; new gates (uses left, the one-time pick, the necromancer from night 2).
- `Agents/nodes/orchestrator.py:449-473` — `_SOLO_NIGHT_ROLES` and the human night announcement; the no-action words.
- `Agents/nodes/orchestrator.py:157-178, 310-322, 244-249` — clearing markers, resetting targets, removing the dead from the buckets.
- `Agents/nodes/night/resolution.py:65-96` — the five targets into `choices_from_targets`; `:37-42` `_ATTACK_FLAVOR` lacks the necromancer; `:102-126` the metric's old fields; `:136-178` hand-written private results; `:154-178` an immune target "confirms the serial killer" (wrong when the necromancer is dealt).
- `Agents/rules/night.py:53-94` (`choices_from_targets`, five roles, the pack choice with role `wolf`), `:172` (conceal keys off role `wolf`), `:37`.
- `Agents/schemas/night.py:18, 25-33` — `AttackerType` / `ATTACKER_TYPE_OF_ROLE` and the side constants.
- `Agents/rules/night_record.py:23-28, 72, 178, 194` — the pack record's actor keyed on role `wolf`.
- `Agents/turn/action_space.py:25-58`, `Agents/schemas/turn.py:18-28`, `Agents/turn/resolve.py:39-44, 184-206, 272-275`, `Agents/turn/agent_player.py:~150-210` — output keys, no-action words, turn kinds, resolved types; two-field outputs (`body`, `bet_role`).
- `Agents/turn/human_turn.py:120, 147-152`, `Agents/schemas/human_player.py:~41-49`, `Agents/driver/hitl_loop.py:67, 88-90` — human instructions and the fixed private fields (no `night_actions`).

## 3. The win

- `Agents/nodes/orchestrator.py:327-373` — `_faction_counts`, `determine_winner`, `_max_days_winner`, `_WINNER_MESSAGE`: three sides.
- `Agents/rules/board_clocks.py:30, 50-78`, `Agents/memory/consolidation/decision_scoring.py:115-148` — the three-side clocks.
- `Agents/schemas/roles.py:66, 73-80` — `RoleSpec.faction` vocabulary; `ROLE_SPECS` drives `side_of`, `can_be_blocked`, the threat brief.
- Winner storage is a free string (`Agents/state/orchestrator.py:106`, `Agents/schemas/metrics.py:94, 245`, `server/database_models/game.py:100`).

## 4. The day

- `Agents/nodes/day/actors.py:9-32, 64-80, 96, 132, 191` — templates keyed by the six roles; the old output classes.
- `Agents/nodes/day/flow.py:195-202, 249` — `_DAY_ACTING_ROLES`: **a new role is silently skipped** (never speaks or votes).
- `Agents/nodes/day/flow.py:167-183, 255-267, 191, 119-123` — pack info and results by role name; `_NIGHT_RECORD_ROLES` silently omits new roles.
- `Agents/state/day.py:74-77, 96-221` — per-role payload states.
- `Agents/schemas/roles.py:12, 37-43, 85-91` — the six-role enums and action phases.
- `Agents/schemas/output.py:343, 364`, `Agents/rules/claim_ledger.py:23, 29-31, 167, 251` — claimed actions and the ledger know only investigate, protect, shoot, kill.

## 5. Memory (where a new role breaks or is silently skipped)

- `Agents/memory/extraction/extraction_agent.py:42-49, 317`, `cell_units.py:16-23` — fixed six roles; new roles never extracted.
- `Agents/schemas/memory.py:528-546, 614-632, 755-773` — cell registries cover six roles.
- `Agents/memory/retrieval/situation_agent.py:42-49, 104-107, 206-221` — **falls back to the villager situation prompt** for a role without a cell.
- `Agents/config/run.py:27-45`, `retrieval/plan_gating.py:111-141` — memory defaults; a new role is silently memory-off.
- `consolidation/credit_rules.py:33-34, 93-121`, `decision_scoring.py:23-39`, `credit.py:32` — role sets for credit and scoring.
- Namespaces follow `roles`; the old wolf and villager stores are orphaned.
- `Agents/memory/tell_book.py:47-61` — old-role tells drop out.
- `Agents/compute_metrics.py:15-18, 152-430`, `Agents/schemas/metrics.py:38-55, 97-145` — role sets and per-role metrics.

## 6. Server

- `server/schemas/events.py:28-29` — wire `Role` and `Winner`; **keep the old values or archived replays stop validating** (`replays.py:19`, `requests.py:17, 98, 312`).
- `server/schemas/events.py:305-314, 78-82, 412-425, 432-438, 453-473, 557-559` — action kinds, starting uses, `WolfVote`, attacker types, a concealed death, private seat events.
- `server/game/translate.py:101-117, 213, 280-291, 414-426, 595-651, 716-719` — node registry (**an unregistered node raises**), the pack by role `wolf`, the vote handlers.
- `server/game/translate.py:653-714` — recomputes the night with the five-role call; **`:682` publishes `self.roles[t]`, which would leak a concealed role**.
- `server/game/pacing.py:32-40, 99-103, 147` — night units, the census by revealed role, the pack unit from `alive["wolf"]`.
- `server/game/entitlement.py:25` — **the faction tier checks role `wolf`: the chanteuse and illusionist would never see the pack chat**.
- `server/game/game_session.py:525-529, 592, 825` — the human turn request, drafting, the census.
- OpenAPI: `frontend/src/types/contracts/openapi.json`, `api.ts`; regenerate with `python -m server.openapi` (`tests/server/test_openapi_snapshot.py`).

## 7. Frontend (`frontend/src`)

After the wire change of 2026-10-09 (the contract regenerated), `tsc --noEmit` fails in exactly
these places, which is where the frontend pass starts: `replays/_components/FilterRail.tsx:105-112`
and `lib/replay-filters.ts:113,145` and `components/site/Slate.tsx:51,112` (the `Winner` union
gained `necromancer` and `null`), `assets/glyphs/PixelGlyph.tsx:97,104`, `stage/instruments/
ActMark.tsx:24` and `MorningRoll.tsx:29-40` (the attacker type gained `sigilist`). Everything
below compiles but assumes the old game at runtime. Since then (2026-10-10) the attacker type also gained `reanimated_wolves`,
`reanimated_vigilante` and `reanimated_sigilist`, which take the body kind's icon (no new icons, owner), and
`input_request` gained `bodies` and `speech` a `claim`.

- `stage/roles.ts:18, 38-60, 106` — the `Faction` union and the pack label.
- `scenes/game-over.ts:21-60`, `GameOverScene.tsx:101`, `FramedCard.tsx:57,138`, `Pin.tsx:34`, `RoleHand.tsx:35`, `replays/_components/FilterRail.tsx:21-23` — winners, one winning side assumed.
- `game/foldEvents.ts:315-330, 357, 611-622`, `beats/beatsFor.ts:98-103, 353, 430`, `containers/LiveTheatre.tsx:545, 661`, `scenes/PackScene.tsx:96-233`, `workbench/*` — `wolf_vote` and `role === 'wolf'`.
- `scenes/NightLobbyScene.tsx:44-86, 220-224`, `replay-night.ts`, `ReplayNightScene.tsx`, `DealScene.tsx:81`, `drawer-lines.ts:184`, `ShelfRoomScene.tsx:48-61, 138, 152` — night roles, the pack, "you sleep" for villagers.
- Old-role tables: `NightRoom.tsx:49-60` (new rooms already there), `RailInstrument.tsx:25-163`, `MorningRoll.tsx:29-40`, `ActMark.tsx:32-36`, `Notice.tsx:197-212`, `ledger.ts:28-35`, `case-file.ts:575-581`, `notebook.ts:66-73`, `IconSprite.tsx:84-89`, `RoleCards.tsx:19-26`, `assets/manifest.ts:383-390`.
- Nine seats: `cast/castForGame.ts:41, 57, 74`, `StationStill.tsx:29`, `DealScene.tsx:275`, `MorningScene.tsx:55`, `paint/station.ts:7, 65`, `units.ts:148`.

## 8. Leak checks and evaluation

- `tests/leak_test.py:27-137` (run live from `scripts/run_batch.py:489, 587`) — keyed on role `wolf`, `wolf_vote`, the investigator and vigilante.
- `scripts/run_batch.py:26, 48-58, 412-421, 618-622`, `build_nethorizon_store.py:41-46`, `analyze_batch.py:78, 160-163` — role sets and winners.
- `evaluation/src/replay/*`, `model_admission/seat_schemas.py`, `hallucination_bench.py:88-109` — per-role specs and the five-role night call.
- Study code with role-set constants (`loop/`, `audits/`, `studies/`, `instrument_validation/`, `diagnosis/`) — dated records of the nine-seat game; update only what a ten-seat run uses.
- Tests that pin role lists: `tests/server/test_engine_sync.py:50-96` (the checklist once `ROLE_SPECS` grows), `test_seedability.py`, `test_determine_winner.py`, `test_v6_cells.py:95-147`, `test_translator.py:57` and the translator goldens, `test_openapi_snapshot.py`.
