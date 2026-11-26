# Assessment: area A, the server side

Scanned 2026-10-26 against the code at `9f350ea5` (the last commit touching `server/`, 2026-10-21) and
LangGraph 1.1.10 / langgraph-checkpoint 4.2.0 (`poetry.lock`). Code was read, never run. Nine documents,
about 28,800 words.

## Summary table

| Document | Kind and status | Main issue | Feeds | Proposed action |
|---|---|---|---|---|
| `frontend/docs/server_client_transport.md` (~7,300 words) | Design record. Status line frozen at 2026-07-28 ("server app + frontend not yet built") | The mechanisms hold, but ten passages describe the July plan where the build departed: route names, the EventBus, the phase marker table (superseded 2026-08-08 by NIGHT_START), the exhaustiveness alarms, where `turn_started` is written, the replay route, the cookie path, the room TTL, checkpoint deletion | 1, 3, 4, 6, 8 (the spine's main source) | Status line, plus dated as-built notes on the ten passages named below. Not a rewrite |
| `frontend/docs/server_design_notes.md` (~6,900) | Design record kept as a dated parking doc, 2026-08-08 to 2026-09-12 | Several eras on one page with no map: §6 holds eight rulings of five dates, one of them (the BYOK restart packet, host-key only) reversed by §13 with no pointer. §3 names translator internals that a rewrite removed | 2, 5, 9; learning (the code-walk rulings) | Status line and a section index (below). Four-line superseded card on the §6 BYOK packet. Dated notes on §3, §5c, §6 (registry, stalls), §10, §13 |
| `frontend/docs/seat_continuity.md` (~2,500) | Design record, the lifecycle map. Status "ruled 2026-09-09, building" | Two later rulings on absence are told nowhere in it: a solo game suspends while its player is away (2026-10-11, told only in the code and one beat-sheet aside), and a seat with two absent turns in a row is taken to have left (2026-10-15, told in the audit). §7's waiting-room row is stale since 2026-09-27 | 4, 5, 8 | Status line ("built; amended to 2026-10-15"). Light edit: §4, §5, §7, §9, §10 as named below. It becomes the one home for absence |
| `frontend/docs/server_encountered_challenges.md` (~2,200) | Journey log (debugging records), 2026-08-19, §7 added 2026-08-24 undated | All of §1 to §5 checked and current. Entries carry no dates and the LangGraph behaviour they rest on has no version pin. The talking points' failure story (events table leads the checkpoint) has no detailed home anywhere | 2, 5, 8; learning | Dates per entry, a version pin on §1, §3, §4. New entry §8 for the failure story (its one home) |
| `frontend/docs/event_derivation.md` (~3,400) | Living spec, mirrored by `server/game/translate.py` and pinned by the goldens. Status line correct | One section contradicts its own 2026-10-11 ruling: the pacing channel's opening lines and the "Derived (night)" row still give the night denominator as the role census, and the stage list lacks the rounds | 1, 3, 6 | Light edit of those two passages only |
| `frontend/docs/multiplayer-audit-2026-10-15.md` (~2,200) | Dated audit | Already in the plain form. No deploy status | 3, 4, 5, 7, 8, 9; learning (realtime_and_sync); playbook | Status line naming the deploy. Index entry |
| `interview_prep/server_talking_points.md` (~1,000) | Interview prep, 2026-09-13, current in most answers | The "walks away" answer omits the solo suspension and the "gone" rule. The funding answer leans on the Vertex credit date. "How much of this did you write?" does not state the authorship as §8 requires | 2, 3, 4, 5, 6, 9 | Light edit of three answers |
| `server/README.md` (~1,600) | Living map of `server/` | The layout table misses six modules and four tables added since 2026-09-15. "~170 tests" is stale (274 test functions on 2026-10-26). The "When the engine changes" table is the only correct account of the coupling alarms | 6; playbook | Light edit of the layout table; drop the test count; note the cron status |
| `docs/agentic_ai_encountered_issues.md` (~1,700) | Journey log, production model issues, 2026-10-01 with dated updates 2026-10-22 | Entry 3 is headed "OPEN" and ends "Next: write the timing sheet". The sheet was written and the seat's-own-turn jump built; the general jump was not | 5, 7 | Dated status note on entry 3 |

## Per document

### server_client_transport.md

- **Kind and status:** design record, the decision record for the wire. Its status line (2026-07-28)
  says the server and frontend are not built. Sections §6b and §6c (2026-08-20), §6d (2026-09-09), §8b
  (2026-10-06, extended 2026-10-17) and the §10 correction (2026-10-22) were added later, so the page
  holds four eras under one July status line.
- **Reader question:** how does a LangGraph game reach a browser, who may see what, and how does a
  client stay in step?
- **Against the §4 standard:** this is the strongest record in the area. Each section states the
  problem, the design, the rejected alternatives and the accepted trade-off. §2 (the upstream rule),
  §3 (the four sync patterns and the history test), §4 (wire format vs persistence) and §8b (three
  options, one built and reverted) meet the standard as written. What it lacks is the dated note where
  the build departed, which §4 of the brief asks for. Its prose carries about 109 em-dashes and
  check/cross icons in two tables; the style guide caps em-dashes and the brief asks for no
  colour marks. Neither blocks its use as a source.
- **Currency (checked by reading the code):**
  - Holds: SSE + POST (`server/routes/games.py::event_stream`, `::submit_turn`). Whole-event
    filtering per viewer at send time (`server/game/entitlement.py::entitled`, called per event in
    `server/routes/games.py::_sse`). The tier is never a wire field (`server/schemas/events.py::EVENT_TIERS`,
    with an import-time check that every union member has an entry). The X-ray is one boolean
    (`entitled(..., game_over)`). Suffix replay by `seq`, `Last-Event-ID` winning over `?last_seq`
    (`_sse`, `event_stream`). Commit-point emission (`server/game/game_session.py::GameSession._drive_graph`
    streams `["updates", "custom"]`, `subgraphs=True`). The §8b announcement (`fan_out_vote`,
    `fan_out_round` in `Agents/nodes/day/flow.py`, `route_night_actors` in `Agents/nodes/orchestrator.py`,
    `pack_fan_out_skills` in `Agents/nodes/night/pack.py`, all writing through
    `Agents/turn/human_turn.py::announce_human_turn`; adopted in `GameSession::announce` and `::park`).
  - Departed from, needing a dated note each:
    1. §1: the routes are `GET /games/{id}/events` and `POST /games/{id}/turns`, not `/stream` and
       `/action`. The table also omits `/draft`, `/key`, `/rejoin`, `/ledger`.
    2. §2: there is no `EventBus` class. `GameSession._deliver` puts each event into every
       subscriber's `asyncio.Queue` directly. The single-process argument holds.
    3. §4: the "M2 rule" (finished game, checkpoint thread deleted) was never built. Design notes §8
       records retention as unruled, and nothing in `server/` calls `adelete_thread`.
    4. §5: "~12 small classes" is now 33 tiered durable event types plus the ephemeral
       `PhaseProgress` (2026-10-26). The trade-off paragraph ("fine at 12 to 20") should state the
       count. The tier examples use nine-seat names (`strategy_note`, `investigation_result`,
       `shot_result`); the wire now sends `strategy_update`, `pass_marker`, `night_record`,
       `uses_remaining`, and observer events added in September (`player_reads`, `memory_consulted`,
       `day_summary_structured`).
    5. §5 "three sources" and §8 "the marker table": both still say `DAY_RESOLUTION` announces the
       night and disambiguate by the winner in its delta. The owner replaced that on 2026-08-08 with a
       `NIGHT_START` marker node (design notes §4; `server/game/translate.py`, the `NIGHT_START` entry).
       The conditional-edge rule is therefore history.
    6. §6: the named standing test `check_event_stream_isolation` in `tests/leak_test.py` does not
       exist. The tier boundary is pinned by `tests/server/test_game_session.py`
       (`test_faction_reaches_wolves_only`, `test_seat_reaches_the_named_recipient_only`,
       `test_observer_reaches_nobody_live_and_everybody_after_game_over`),
       `tests/server/test_translator.py::test_every_emitted_type_is_tier_registered` and the
       import-time check. The multiplayer audit (2026-10-15) later found two side channels these
       event-level tests could not see (findings 1 and 2); §6 should link them.
    7. §6b: the cookie path now carries the browser-visible prefix (`server/routes/_shared.py::set_seat_cookie`,
       `SEAT_COOKIE_PATH_PREFIX`, fixed 2026-08-24, challenges §7). "Status doubles as the auth probe:
       the poll hitting 403 is the trigger for rejoin" is contradicted by seat_continuity §2, which says
       the trigger is the mismatch between a stored token and a status that names nobody. The orphaned
       seat's remedy is the delegate (design notes §7), not "the AFK timer's deterministic defaults
       (slice 4)". The local copy is now kept unless the server definitely refuses it (multiplayer
       finding 11).
    8. §6c: the listing TTL is no longer only a browse filter. Since 2026-09-27 the sweeper closes a
       room that has not departed within `ROOM_LIST_TTL_SECONDS`, and its URL answers 410 with the
       reason (`server/game/live_game_registry.py::LiveGameRegistry.expire_rooms`, `::closed_reason`).
       A guest can leave and the host can close (`::leave`, `::close`).
    9. §8: the alarms as built differ from the two asserted-set tests the section describes. Each
       translator node entry declares its `writes`, and the first chunk carrying an undeclared node or
       field raises `TranslationError` at runtime (`server/game/translate.py::node`, `::silent_node`).
       `tests/server/test_engine_sync.py` compares the declared fields with the engine's state schemas;
       no test covers the node axis (`server/README.md` says so). "The novelty gate" is now the echo
       gate on sweep turns and the opening filter (2026-10-07); the commit-point argument holds with
       them, since a held line becomes a `pass_marker` with `gated_candidate`.
    10. §9: `turn_started` is written from the `route_speaker` edge (`Agents/nodes/day/flow.py`), not
        "at the top of each turn node", so it cannot double-fire on a resume (event_derivation, the
        `route_speaker` entry). §10: the union no longer enters the OpenAPI document through
        `GET /games/{id}/events -> list[GameEvent]`; that path is the SSE route. It enters through
        `GET /replays/{game_id}` (`server/schemas/replays.py::ReplayGame.events`).
- **One-home conflicts:** the reconnect rulings of 2026-08-18 (three lifetimes, two cursor channels,
  the tier-aware cursor) live in design notes §6 while §7 here is the reconnect section. Recommended
  home: §7 here, with the two rulings summarised and the design-notes bullets kept as the dated
  originals. §6b vs seat_continuity §2 (above): the design stays here, the lifecycle there.
- **Feeds:** story 1 (§2, §3, §8, §9), 3 (§5, §6), 4 (§7), 6 (§8, §10), 8 (§6b), 2 (§8b).
- **Proposed action:** a status line ("ruled 2026-07-28; built 2026-08; sections §6b to §8b added to
  2026-10-17; dated notes mark where the build departed"), then the ten dated notes above. Keep every
  mechanism as ruled.
- **Terms used before definition:** tier and X-ray (used in §3, defined in §5), "ghost mode" (status
  line), M2 (§4), "slice 4" (§6b), "the novelty gate" (§4, §8, §9, never defined), beat (§9), "the
  jar" and "the composer" (§8b), HITL (§8b), park (§6d heading).

### server_design_notes.md

- **Kind and status:** design record in the form of a parking doc ("write-up seeds, NOT polished
  prose"), 13 dated sections from 2026-08-08 to 2026-09-12. The README already treats it as "server
  rulings, dated", which is what it is now; the header should say so.
- **Reader question:** why is the server shaped as it is, ruling by ruling?
- **Against the §4 standard:** §5 (concurrency: three options, the arithmetic of async being viral,
  a parity check before migrating), §10 to §12 (the owner's code walks, each ending in a ruling with
  rejected alternatives) and §13 (funding) meet the standard. §6 does not: it is a bullet list in
  which a built feature, a deferred build packet, a registry policy and a stall fix share one
  heading, and its first BYOK-restart bullet was reversed by §13 without a pointer.
- **Currency:**
  - Holds: §1 and §2, the translator never calls `get_state` and keeps its own shadow
    (`server/game/translate.py` module docstring). §4, `NIGHT_START` (registered in the translator).
    §5, `astream` on the loop with sync nodes in LangGraph's executor (`server/game/game_session.py`
    module docstring). §7, the delegate answer and the 120 s clock, armed only with two or more human
    seats (`GameSession.__init__`, `SeatClocks(enabled=len(self._seat_tokens) > 1)`). §11, the
    fall-through to the row for ended games (`server/routes/games.py::game_status`,
    `::_archived_status`). §12, rooms born at start (`LiveGameRegistry::_launch`, `::revive`). §13, the
    purse (`server/house.py::HousePolicy`), the count from the games table, the admin knobs behind
    `ADMIN_TOKEN` with 404 when unset (`server/routes/admin.py`), resuming a key-funded game
    (`LiveGameRegistry::resume_with_key`, `server/routes/games.py::fund_game`).
  - Departed from:
    - §3: `_h_<node>` handlers, `_FOLDS` and `_h_collect_wolf_votes` are gone. The translator is a
      registry of `@node(name, writes=...)` entries, and Phase 3 removed the pack vote. The principle
      (one entry per node, arrival is not release for ballots) holds.
    - §5c mode 1 still lists "honour Last-Event-ID" as an open ruling; it was ruled the next day
      (§6, 2026-08-18). Mode 2 gained two changes: a refused key is now caught at the door
      (`LiveGameRegistry::_try_key`, 2026-10-17), and a failure after `game_over` archives the game
      instead of dropping it (`GameSession._drive_graph`, 2026-10-17).
    - §6, the BYOK restart packet (2026-08-22) ruled "only the original host_key may restore
      funding" and a `POST /credential` route. Neither was built. §13 (2026-09-12) built `POST /key`
      for any seat holder and lists host-only as rejected.
    - §6, "BYOK v1.5": `SUPPORTED_GAME_MODELS` in code is gone. The catalogue lives in the `models`
      and `model_prices` tables, re-read live (`server/game/model_catalog.py` docstring,
      `server/housekeeping/catalog_refresh.py`). The Gemini default of 2026-08-12 is history: the site
      default is Claude Haiku 5.5 since 2026-10-15. A player's backup key for another company
      (`BACKUP_MODELS`, 2026-10-21) has no design record in this folder.
    - §6, "Stalls (2026-09-30)": a full copy of `docs/agentic_ai_encountered_issues.md` §1.
    - §10: the registry's transitions grew (`leave`, `close`, `choose_character`, `expire_rooms`,
      `resume_with_key`). The registry docstring has the current state diagram.
    - §13 "Still open": the default model paragraph (3.5 Flash-Lite against 3.1) predates the switch
      to Haiku 5.5. `server/house.py` says "concurrent starts can all take the last slot"; §13 says
      "may exceed the cap by one". One of the two should be corrected after a look at
      `HousePolicy.authorize`.
- **One-home conflicts:** §5c (fault model) vs seat_continuity §1: home seat_continuity §1; §5c keeps
  its dated text and gets a one-line pointer (mode 5 already has one). §7 (AFK) vs seat_continuity
  §4 and §5: home seat_continuity; §7 keeps the original ruling and its existing banner. §6 stalls vs
  agentic issues §1: home agentic §1; §6 keeps one sentence and a link. §6 BYOK packet vs §13: home
  §13.
- **Feeds:** story 2 (§1, §2), 5 (§5c, §8, §11, §12), 9 (§13), 1 (§5); learning (§10 to §12 are the
  owner re-owning the code, the use the brief names in §1.2).
- **Proposed action:** status line; this section index as a header block; a four-line card on the §6
  BYOK packet ("question: who may restore a key-funded game after a restart; ruled 2026-08-22 host
  only, not built; reversed 2026-09-12, any seat holder; see §13"); dated notes on §3, §5c, §6 v1.5,
  §6 stalls (cut to a pointer), §10, §13.

  | § | Date | Ruling | Status 2026-10-26 | Detailed home |
  |---|---|---|---|---|
  | 1, 2 | 08-08 | The translator keeps its own shadow and never calls `get_state` | holds | here |
  | 3 | 08-08 | One handler per node; ballots arrive and are released apart | holds; names predate the registry rewrite and Phase 3 | here, dated note |
  | 4 | 08-08 | `NIGHT_START` marker node, the owner's reversal | built | here |
  | 5 | 08-08 | `astream` on the loop, sync nodes in the executor | built | here |
  | 5b | 08-12 | The live-machine dict and the two scaling steps | durability done (§8); distribution not built | here |
  | 5c | 08-17 | Fault model, five modes | statuses superseded 2026-09-09 | seat_continuity §1 |
  | 6 | 08-08 to 09-30 | Slim `input_request`; day summary text; annotation join; reconnect lifetimes and cursors (08-18); BYOK built (08-12); BYOK restart packet (08-22); model registry (08-12); stalls (09-30) | packet reversed by §13; registry moved to the database; stalls told twice | reconnect: transport §7; stalls: agentic §1; the rest here |
  | 7 | 08-20 | AFK: delegate the turn to the seat's own agent | extended 2026-09-09 and 2026-10-15 | seat_continuity §4, §5 |
  | 8 | 08-22 | One game identity, one event log; retention unruled | built; retention still unruled | here |
  | 9 | 08-22 | Routers expose resources, never own them | built (`admin`, `characters` routers added) | here |
  | 10 | 09-10 | Three nested lifecycles; `LiveGameRegistry` | built; transitions grew | here |
  | 11 | 09-11 | The registry holds only live games | built | here |
  | 12 | 09-12 | Rooms are not persisted | built; amended 2026-09-27 (leave, close, rooms expire) | here, dated note |
  | 13 | 09-12 | Funding: purse, menu, key resubmission | built; default model and catalogue moved on | here, dated note |

- **Terms used before definition:** "the spike" and "the kernel cross-check" (§1), `_FOLDS` (§3), R7
  (§6, the reveal backlog), M2 (§5b), "the three doors" (§10), epitaph (§11), "the purse" (§13 title,
  defined in its first bullet).

### seat_continuity.md

- **Kind and status:** design record, the lifecycle map of a human seat that stops answering. Status
  line "ruled 2026-09-09 (owner), building". It was built; §6, §7 and §9 were amended on 2026-09-11,
  2026-09-12 and 2026-09-17.
- **Reader question:** when a human seat goes silent, from a blip to an empty table, what does the
  system do at each layer, and why?
- **Against the §4 standard:** close to the exemplar. It asks the question (why is the seat
  silent), draws the distinction that answers it (presence is a snapshot; blip and close are
  identical at the instant the socket dies), states the mechanism, gives the one measurement that
  pinned a number (the 30 s grace: drops seen after 1.0 s once and 10.1 s twice, through Cloudflare
  and Caddy, 2026-09-09; N=3), and lists rejected alternatives (§8). What it lacks is the October
  record.
- **Currency (checked):**
  - Holds: §3, presence resolved per subscriber token (`GameSession.connected_seats`, `::subscribe`,
    `::unsubscribe`). §4, the two clocks in one deadline, the deadline absolute from the ask, the
    clock tied to the question by identity (`server/game/seat_clocks.py::SeatClocks.reschedule`,
    `::_expire`). §5, delegate when anyone is connected, park when nobody is, only human seats count
    (`::_expire`, `GameSession.humans_present`). §6, three authorities on boot
    (`LiveGameRegistry::revive`, `::_resume_from_checkpoint`). §7, the sweeper and its two shelf
    lives (`server/housekeeping/sweeper.py::_shelf_life`, `::is_expired`). §9.5, no stall watchdog
    (nothing in `server/` detects a stream that produces no chunk).
  - Missing or departed:
    - A solo game suspends while its living player has no stream open (ruling 2026-10-11, commit
      `9f4c21a7`; `GameSession::_wait_for_absent_player`, `::_absent_solo_seat`). The engine stops at
      the end of the step it is in; a dead player is not waited for; the sweeper drops a suspended
      game after the solo hour ("suspended with its player away"). This reverses §4's "a solo game
      may wait forever" for every turn but the human's own, and it is the reason given in the
      commit: a human was killed during a two-minute phone sleep. No design record states it. The
      only prose is an aside in `beat_sheet.md` (the door's words, 2026-10-11).
    - A seat with two turns in a row played by its agent while unconnected is taken to have left;
      its next questions go to the agent at once until it reconnects (`seat_clocks.py::GONE_AFTER_TURNS`,
      2026-10-15, multiplayer finding 5).
    - §4's draft credit: the credit is capped at 20 s (`game_session.py::DRAFT_CREDIT_CAP_S`,
      2026-09-30), and a draft is counted before the model is asked, one at a time per seat
      (multiplayer finding 4).
    - §7's waiting-room row: rooms are now closed by the sweeper after `ROOM_LIST_TTL_SECONDS`, and
      their URL answers 410 with the reason (2026-09-27).
    - §3: the heartbeat is a named `ping` event, not an SSE comment, and the page reopens a stream
      silent for 40 s (multiplayer finding 7, 2026-10-15). The 15 s detection bound is unchanged.
- **One-home conflicts:** this is the recommended single home for absence and recovery: the fault
  model (design notes §5c), the AFK clocks (design notes §7, transport §6d, multiplayer finding 5,
  talking points), the solo suspension (code only) and retention. Each other place keeps its dated
  original and a pointer here.
- **Feeds:** story 5 (§1, §4 to §7, the spine's main source), 4 (§2, §3), 8 (§2).
- **Proposed action:** status line ("ruled 2026-09-09; built; amended 2026-09-12 to 2026-10-15").
  Light edit: §4 gains the gone-after-two-turns rule and the draft cap; a new §5b "A solo table
  suspends" with the 2026-10-11 ruling and its reason; §7's table gains the suspended row and the
  corrected room row; §9.2 stays open (no "your seats" strip or join code exists in `frontend/src`);
  §10 lists multiplayer findings 4, 5, 7, 11 and commit `9f4c21a7`.
- **Terms used before definition:** "the dock" (§5), epitaph (§7), "the sweeper" (§6, defined in §7),
  "strip" (§9.2, a home-page list, a different object from the stage's strip).

### server_encountered_challenges.md

- **Kind and status:** journey log of seven debugging records, each told as story, fix, "what to
  know". Written 2026-08-19; §7 dates from 2026-08-24 (seat_continuity §10) but carries no date.
- **Reader question:** what broke while making the server host real humans, and what was it?
- **Against the standard:** the plain-language form already meets the brief's prose rules (written
  to be read cold, mechanisms named, the wrong first diagnosis in §2 kept). Two gaps against the
  style guide: no entry has a date, and the LangGraph behaviour each rests on has no version pin
  (§4 says "on our pinned LangGraph version").
- **Currency (checked, story 2):** all current. §1, only root-level interrupts are parked
  (`GameSession::_on_chunk`, `"__interrupt__" in data and not ns`). §2, last write per voter wins
  (`Translator._day_ballots`; `tests/server/test_translator.py::test_reexecuted_ballots_overwrite_the_aborted_ones`)
  and the tally cross-check raises on a mismatch (`translate.py`, "kernel/delta mismatch"). §4, cached
  and uncached twins (`tests/engine/test_human_seat.py::test_day_vote_fanout_routes_humans_to_the_uncached_twin`
  and the pack twins), TTL six hours (`Agents/config/langgraph.py::TURN_CACHE_TTL_SECONDS`). §5, the
  canonical-JSON key (`Agents/config/langgraph.py::turn_cache_key`, `tests/engine/test_turn_cache_key.py`).
  §6, the allowlist test exists (`tests/engine/test_checkpoint_allowlist.py`). §7, the prefix
  (`server/config.py::SEAT_COOKIE_PATH_PREFIX`).
- **One-home conflicts:** the stream behaviours are summarised in event_derivation ("Stream
  behaviours the translator guards") with links here, which is the right split. Two findings of the
  same family live elsewhere: the nested-parallel interrupt latency (transport §8b, measured
  2026-10-17) and the failure story in the talking points (the events table leads the checkpoint by
  up to one step; the cached drop pinned by
  `tests/server/test_translator.py::test_every_real_chunk_re_delivered_as_cached_sends_nothing`).
  Recommended: §8b keeps its finding (it is a design decision); the failure story gets its detailed
  home here as a new §8, and the talking points keep the summary.
- **Feeds:** story 2 (§1 to §5), 5 (the new §8), 8 (§7); learning (each "what to know" is a lesson,
  see the area-level section).
- **Proposed action:** a date on each entry; "LangGraph 1.1.10" on §1, §3, §4; new §8 "The events
  table leads the checkpoint" in the same form.
- **Terms used before definition:** none of note; the file defines interrupt, root mirror and cached
  door as it goes.

### event_derivation.md

- **Kind and status:** living spec, the companion of `server/game/translate.py` by node name. Its
  status line ("nothing checks it against the code; when the two disagree, the goldens are right")
  is accurate and should stay.
- **Reader question:** what does each graph node send, and to whom?
- **Currency (plainly stale passages only):** the "Ephemeral pacing channel" opening says the night
  denominator is the "padded alive-role census" and names two stages; the "Derived (night)" table
  says the same. Both contradict the section's own ruling bullet (2026-10-11: one padded unit per
  living seat, from the roster), `server/game/pacing.py` (module docstring) and
  `server/schemas/events.py::PhaseProgress` (`stage` is `night`, `day_vote`, `opening`, `closing`). The
  rest was not checked, as a spec the goldens pin.
- **One-home conflicts:** none. It is the one home for per-node emission; transport §5 and §8 should
  point at it for the current marker nodes.
- **Feeds:** story 1 (commit-point emission per node, `turn_started` from the edge), 3 (tiers per
  node, silent whiffs, the pacing denominator as a side channel closed), 6 (the companion of the
  goldens).
- **Proposed action:** light edit of the two passages above.
- **Terms used before definition:** the twelve role names, carrier, pack, sweep, proactive, "the
  stage" (defined in the role sheet and beat sheet; a link at the head is enough).

### multiplayer-audit-2026-10-15.md

- **Kind and status:** dated audit, two read-only scans (server and page), claims checked in code,
  nothing run on a device or in a four-human game. Each fix in one form: what we found, why it was
  like that, the fix, how it is now.
- **Reader question:** what can go wrong when several friends play one game?
- **Currency (checked, stories 3, 4, 8, 9):** finding 1, the status's `last_seq` is the newest event
  this viewer may see (`server/routes/_shared.py::live_status`). Finding 2, one refusal message naming
  the caller's seat (`GameSession::submit_turn`). Finding 4, counted before the model call, one draft
  at a time (`GameSession::draft_line`). Finding 5, `GONE_AFTER_TURNS`. Finding 7, the named `ping`
  (`server/routes/games.py::_PING`). Finding 9, `refetchOnMount: 'always'`
  (`frontend/src/hooks/useGameStream.ts`). Finding 10, `TURN_JUMP_MS = 30_000`
  (`frontend/src/stage/containers/live-state.ts`). Finding 11, `ApiError.refusesToken`
  (`frontend/src/lib/request.ts`). `syncPending` (finding 8) is in `frontend/src/game/store.ts`, not
  read. All match.
- **One-home conflicts:** finding 11 corrects `build_log.md` §3.11's last sentence ("failed tokens are
  cleared"), which area B should mark. Finding 5 belongs in seat_continuity §4 as the rule, with the
  audit as its evidence. Finding 10 is the as-built half of live_timing_sheet ruling 3 (area C).
- **Feeds:** story 3 (findings 1 to 3), 4 (7 to 9), 5 (5, 12), 7 (10), 8 (11), 9 (4); learning
  (realtime_and_sync, below); playbook (the audit form, below).
- **Proposed action:** status line naming whether the commits it lists are deployed (not checked
  here). Index entry.
- **Terms used before definition:** "Reveal's lock" (What is solid), "the ledger", "the dock" (8),
  "hold" and "the stage" (10), "the bar" (finding 3).

### interview_prep/server_talking_points.md

- **Kind and status:** interview prep, one page of decision, reason and cost, 2026-09-13. Not a
  frontend doc, but the brief names it as a source for stories 2 and 5.
- **Reader question:** how would the owner tell the server in an interview?
- **Currency (checked):** the turn walk (three dicts keyed by seat, a Future each, `gather`, cross the
  seat off first: `GameSession::park`, `::submit_turn`, `::_collect_answers`), the restart answer, the
  rooms answer and the wolf-chat answer all match the code. Three answers need a light edit:
  - "A player who walks away": add the solo suspension (2026-10-11) and the gone-after-two-turns rule
    (2026-10-15). As written it implies a solo game runs on with its player away.
  - "Bankrupting": the credit date (2026-10-27, Vertex) predates the 2026-10-15 switch of the site
    default to Claude Haiku 5.5. The mechanism (cap from the games table, live settings, kill switch)
    stands; the reason should be stated in present terms.
  - "How much of this did you write?": it does not say that the owner wrote the event schema and
    co-wrote the beat sheet, or that the rest, tests included, was AI-written to those specs.
    "I own the contract and the tests" can be heard as "I wrote the tests". Rephrase to the §8
    constraint; this answer is story 6's honest half.
- **One-home conflicts:** the failure story's only full telling is here (recommended home:
  challenges §8). "What would you change" repeats seat_continuity §9.5; consistent.
- **Feeds:** 2, 3, 4, 5, 6, 9.
- **Proposed action:** light edit of the three answers named.
- **Terms used before definition:** none; written for a cold listener.

### server/README.md

- **Kind and status:** living map of `server/`: reading order, layout table, "When the engine
  changes", how to run it.
- **Reader question:** where is each part of the server, and which record explains it?
- **Currency:** the three-lifecycle diagram and the "When the engine changes" table match the code
  (`test_engine_sync.py` sees fields, not nodes; a new node is caught by `TranslationError` at
  runtime). Gaps in the layout table: `game/cast.py`, `game/ledger.py`, `game/usage.py`,
  `housekeeping/catalog_refresh.py`, `routes/characters.py`, the rooms' `leave` and `close`, and
  `database_models/` (which also maps `prompt_captures`, `models`, `model_prices`, `characters`,
  `game_cast`, not only `games`, `events`, `settings`). The `game_session.py` row should name the
  solo suspension. "~170 tests" is stale: `tests/server/` holds 274 test functions on 2026-10-26,
  before parametrisation; per the evidence-pass rule, drop the count. The leak-audit paragraph
  ("Nightly, from `crontab -e`") reads as running; the owner's hardening list records the cron as not
  yet installed (not checked on the host).
- **One-home conflicts:** none; it points rather than repeats, as it says.
- **Feeds:** story 6 (the coupling table is the correct as-built account of the alarms; transport §8
  should link it); playbook ("reading order for a newcomer", "re-entering after months").
- **Proposed action:** light edit of the layout table, the count and the cron sentence.

### docs/agentic_ai_encountered_issues.md

- **Kind and status:** journey log of the production pass for the models, 2026-10-01, with dated
  updates of 2026-10-22 on entries 1 and 2.
- **Reader question:** what went wrong with the models while real people played, and how was it
  settled?
- **Currency:** entry 1 (the request budget, `Agents/llm_factory/health.py::ModelHealth`) carries its
  dated update to Haiku 5.5 with Sonnet 5.5 as the rescue. Entry 3 is headed "OPEN" and ends with the
  timing sheet as the next step. Since then the sheet was written (2026-10-01), the seat's-own-turn
  jump was built (2026-10-15, multiplayer finding 10), and the general jump was not. "The worst
  honest turn measured before the change was 11 s" needs its N (how many games or turns).
- **One-home conflicts:** entry 1 is the recommended home for the stall rescue; design notes §6
  "Stalls" points here. Entry 3's ruling is restated at the head of `live_timing_sheet.md` (area C),
  which should be its home; entry 3 keeps the owner's explanation and links.
- **Feeds:** story 7 (entries 1 to 3), 5 (the stall gap: the budget narrows it, the watchdog is still
  missing).
- **Proposed action:** a dated status note on entry 3; the N on the 11 s figure.
- **Terms used before definition:** beat, hold, "the strip notice", "the drawer", "the mark beat"
  (entry 3).

## Area-level

### Overlaps, one home each

| Ruling or finding | Told in | Recommended home | The others |
|---|---|---|---|
| Fault model, five modes | design notes §5c; seat_continuity §1; talking points | seat_continuity §1 | §5c keeps its 2026-08-17 text with a pointer; mode 1's open line gets a dated note |
| AFK clocks, delegate or park | design notes §7; seat_continuity §4, §5; transport §6d (already a stub); multiplayer finding 5; talking points; `seat_clocks.py` docstring | seat_continuity §4, §5, amended | §7 keeps the original ruling; finding 5 is the evidence for the "gone" rule |
| A solo table suspends (2026-10-11) | code and commit only; one aside in `beat_sheet.md` | seat_continuity, new §5b | talking points summarise |
| Retention and the sweeper | seat_continuity §7; design notes §8 (deletion unruled); transport §4 (M2) | seat_continuity §7 | transport §4 gets a dated note |
| Reconnect cursors (header vs query, tier-aware) | design notes §6 (2026-08-18); transport §7 | transport §7 | design notes keeps the dated originals |
| Seat identity, cookie path, reclaim door | transport §6b; seat_continuity §2; challenges §7; multiplayer 11; build_log §3.1, §3.11 (area B) | transport §6b, with dated notes | challenges §7 tells the bug; the audit tells the fix |
| Rooms: not persisted, TTL, leave, close | design notes §12; transport §6c; seat_continuity §6, §7; registry docstring | design notes §12, with a dated note for 2026-09-27 | transport §6c and seat_continuity §7 summarise |
| BYOK restart | design notes §6 (2026-08-22 packet), §13 (2026-09-12); seat_continuity §6, §9.6 | design notes §13 | §6 gets the four-line superseded card |
| Stall rescue and request budget | agentic issues §1; design notes §6 "Stalls" | agentic issues §1 | design notes §6 cut to a pointer |
| Coupling alarms | transport §8 (as planned); README "When the engine changes" (as built); `events.py` import-time check | README table | transport §8 keeps the policy and links the table |
| Phase markers | transport §5, §8 (DAY_RESOLUTION, July); design notes §4 (NIGHT_START, 2026-08-08); event_derivation | event_derivation (per node), design notes §4 (the reversal) | transport gets a dated note |
| `turn_started` placement | transport §9 (node top, double-fires); event_derivation (edge, cannot) | event_derivation | transport §9 dated note |
| Events table leads the checkpoint | talking points; `translate.py` docstring | challenges, new §8 | talking points summarise |

### Story coverage from this area

- **Story 1:** transport §2, §3, §8, §9 hold as design; the as-built anchors are
  `GameSession._drive_graph`, `::_on_chunk`, `::_deliver` and `routes/games.py::_sse`. The dated notes
  above are needed before the chapter quotes route names or the marker table.
- **Story 2:** challenges §1 to §5 and transport §8b, all checked; the talking points' turn walk.
  Nothing missing.
- **Story 3:** transport §5, §6; multiplayer findings 1 to 3; event_derivation's silent whiffs and
  pacing denominator; `entitlement.py` (28 lines, worth quoting whole). The named leak test in §6
  must be replaced by the real tests before the chapter cites it.
- **Story 4:** transport §7 plus design notes §6 (the cursor rulings), seat_continuity §2, §3,
  multiplayer 7 to 9. The client half (membership dedupe, the history line, `syncPending`) is area B's.
- **Story 5:** seat_continuity is the spine, but it lacks the two October rulings, and the failure
  story has no detailed home. Both gaps should be closed before chapter C is drafted.
- **Story 6:** README's coupling table, transport §10, `test_engine_sync.py`, `test_openapi_snapshot.py`,
  the goldens; the authorship answer in the talking points needs the §8 wording.
- **Story 8:** transport §6b (with notes), challenges §7, multiplayer 11.
- **Story 9:** design notes §13, multiplayer 4, `house.py`. The backup key (2026-10-21) has no record
  here.

### Placement unclear

- **The backup key and the database model catalogue** (2026-10-21 and earlier): code only
  (`server/game/model_catalog.py`, `server/housekeeping/catalog_refresh.py`). Proposed home: a dated
  amendment to design notes §13, since both change who pays and what the menu offers.
- **`docs/agentic_ai_encountered_issues.md`** sits in `docs/` while its two companion logs sit in
  `frontend/docs/`. It is the production record for the models, not the frontend; keep it where it
  is and index it from the folder's index.
- **Server lessons in the learning hierarchy.** The brief's §6 topics are browser and sync topics.
  The challenges' "what to know" lines (root is authoritative; a stream can retract; cache keys from
  values; an allowlist warning is a to-do; a proxy's upstream path is not the browser's) have no
  topic. Either `realtime_and_sync.md` takes §2, §5 and §7, or the challenges file is itself the
  server's lesson doc and `principles.md` cites it. The second costs nothing.
- **The talking points** live in `writeup/`, which fits interview prep; the chapter should cite the
  records behind them, not the page.

### Constraint check (§8)

- **General jump not built:** multiplayer finding 10 says so. Agentic issues entry 3 states the
  ruling with no build status; add it.
- **Stall watchdog not built:** consistent in all four places (design notes §5c, seat_continuity §9.5,
  agentic §1, talking points), and nothing in `server/` detects a silent stream.
- **Served games carry no runtime fingerprint:** no document contradicts it. Design notes §6 and the
  `GameSession` docstring say "RunConfig is fingerprinted and recorded" as the reason a key stays off
  it; a reader may infer served games are fingerprinted. Add "in batch records" when §6 is touched.
- **No CI:** the only mention is the 2026-10-22 correction in transport §10.
- **Persona voices OFF:** the code contradicts this constraint. `server/game/run_config.py::game_run_config`
  sets `persona_voices=True` ("AI seats use their dealt puppet's speaking voice in served games"),
  and commit `73aafcb9` (2026-10-26) corrected the evidence-pass proposal to "voices on in hosted
  games". No area A document states the voices setting, so nothing here changes, but the brief's
  constraint should be corrected before the proposal is written.
- **Music deployed:** not in this area.
- **Beat sheet and stage_architecture are the truth for the stage:** not contradicted; event_derivation
  defers to the goldens for the wire.
- **Haiku 5.5 default since 2026-10-15:** design notes §6 (Gemini 3.1 Flash-Lite default) and §13
  ("3.5 Flash-Lite thinks by default") and the talking points' credit date read as current. Agentic
  §1 already carries the dated update. Dated notes needed on the other three.
- **Memory off by default in served games:** consistent (`server/schemas/requests.py`, `memory: bool =
  False`; README's `WW_MEMORY_ENABLED` paragraph).
- **Authorship:** the talking points' last answer must be rephrased (above). No other area document
  claims authorship.
- **One game's numbers:** the grace measurement (seat_continuity §4) is three drops on 2026-09-09 and
  says so; agentic entry 3's "20 to 40 s behind" is an estimate and the 11 s worst turn lacks its N.

### Contributions to §6 and §7 (not assigned; offered for areas C and D)

- **realtime_and_sync.md** would draw on the multiplayer audit as its richest single source. Lessons
  that generalise, by finding: 1 (a number on a public endpoint is an information channel; filter it
  like an event), 2 (an error message is a side channel), 4 (a check and an act across an await are
  not atomic; take the slot first, give it back on failure), 5 (a dropped connection and a departed
  player need different rules), 7 (a heartbeat a script cannot hear does not prove liveness), 8 (a
  snapshot may only speak about what it could have seen; guard every branch by seq), 9 (a cached
  snapshot is an earlier moment), 11 (destroy a credential only on a definite refusal). From the
  challenges: §2 (a stream can retract; converge on last values) and §7 (the proxy namespace).
- **Playbook items with exemplars in this area:**
  1. *The read-only audit.* Exemplar: the multiplayer audit. Steps: scope the threat in one sentence;
     two scans (server, page) with every main claim checked in code; each fix written as found, why,
     fix, now, with commit and test; an "accepted or left" table carrying the owner's decision per
     item. Rule it taught: say what was not run (here, no device and no four-human game).
  2. *The owner's code walk and the invariant question.* Exemplars: design notes §10, §11, §12 and §4.
     Steps: read one module a day after it is written; ask which module owns a lifecycle or what the
     table's invariant is; record the answer as a dated ruling with rejected alternatives; delete the
     backstop that would hide a broken invariant (§11's `release_idle`). Rule: naming a layer does
     not make anyone ask what it guarantees.
  3. *Coupling alarms when the engine changes.* Exemplar: README "When the engine changes" with
     transport §8's policy. Steps: name each copied fact; give it one place and an alarm; keep a table
     of change, update, caught by; regenerate a golden only for a deliberate wire change and review its
     diff. This is the server twin of the brief's item 1.
  4. *The plain-language challenge record.* Exemplar: server_encountered_challenges §2. Steps: the
     story with the wrong first diagnosis kept, the decisive evidence, the fix with its pinning test,
     "what to know". Rule: written to be read cold, without the chat or the code.
  5. *Measure before pinning a number.* Exemplar: seat_continuity §4, the 30 s grace measured through
     the real proxy chain with a scripted client before it was fixed in code.
