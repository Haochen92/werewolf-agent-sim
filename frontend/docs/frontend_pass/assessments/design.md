# Assessment: design and art (area D)

Scanned 2026-10-26, read-only. Area D is index and playbook only: no chapter C story depends on
these documents, so currency was checked against the code only where a status line makes a claim
about what shipped, or where a living spec contradicts another living spec. The area's extra
output, the playbook's table of contents (brief §7), is in the area-level section.

## Summary table

| Document | Kind and status | Main issue | Feeds | Proposed action |
|---|---|---|---|---|
| `design_2026-09-25/HANDOFF.md` | Dated brief (the design handoff of 2026-09-25, amended in place 2026-09-29). Superseded as the spec by `beat_sheet.md` and `stage_architecture.md`, which say they win | Its header still says "This is the document the codebase build starts from". It describes nine seats, the vector shelf room with plush dolls, the film and the bundle's eleven figures, all replaced; only the 2026-09-29 changes are marked. §6 says queued beats drain at fast speed, which the 2026-10-01 ruling reversed. §11 lists bundle files that are not in this folder | playbook 1, 7; story 7 as history (§6) | Status line. One line in §11 saying where the bundle went |
| `design_2026-09-25/BUNDLE_README.md` | Dated brief, superseded with the handoff | Its paths (`benches/`, `sprites/`) and fixture file name resolve nowhere in the repo | playbook 1, 8 | Covered by the handoff's status line |
| `design_2026-09-25/landing-handoff-2026-09-22.md` | Dated brief, superseded by `pages_review.md` §F and `site_architecture.md` | "Nine LLM agents", the pre-merge palette and fonts | playbook 7 | Status line |
| `design_2026-09-25/kits/` (4 files) and `sprites-manifest.json` | Frozen artefacts of the benches, listed only | None as artefacts. The manifest describes the 600 px set that `stage_architecture.md` §4 "The cast" replaced on 2026-09-28 | none | Index entry only |
| `design_2026-09-26/pages_review.md` | Dated audit with owner rulings (2026-09-26, amended to 2026-09-29); executed | No as-built line. Its §F rulings are the one home for several site decisions, but nothing at the head says which were built | playbook 3, 6, 9 | Status line |
| `design_2026-09-28/scorecards_plan.md` | Dated plan, not built (checked 2026-10-26) | Its own status, "planned, nothing built", is still true | playbook 9 (the parity test idea) | Date the status line |
| `design_2026-09-28/landing_features.md` | Dated brief, built 2026-09-28 | "Why this wording" describes the lessons as "a snapshot from research runs"; served games now read the database's published store. The copy was written to survive that change, so only the explanation is dated | playbook 9 | Status line |
| `role_cards_brief.md` | Dated brief, shipped 2026-10-07 | Header says "DRAFT" while §6 says all eight shipped the same day. §4 repeats the card text whose home is `src/stage/card-text.ts` | playbook 2, 6 | Status line |
| `cast_expansion_brief.md` | Dated brief with its rounds (a journey log in miniature), shipped 2026-10-03 | The ruled template at the head supersedes "Process" and Prompts 1 to 4 below it, which still read as the method. Its last section, "The cast record", is a server and site design record (two tables, the picker, `resolveCast`) with no other home | playbook 2 | Section index and status line. A pointer to "The cast record" from `site_architecture.md` |
| `night_rooms_brief.md` | Dated brief, shipped 2026-10-07 | Header says "DRAFT"; §5 says all six shipped | playbook 2 | Status line |
| `music_brief.md` | Dated brief, delivered | No date and no status, so it reads as pending. `public/music` holds the four victory stings and two dawn files it asked for | playbook 2 | Status line with the date |
| `opening_round_brief.md` | Dated brief (2026-10-11), not built | No status. The painting was never made; the beat sheet's placard (§2 row 7, owner 2026-10-15) is what the stage shows | none | Status line |
| `typography.md` | Living spec (a ruling with its build) | "Status: built 2026-10-16, not yet deployed". The owner's records say it is deployed. `stage_architecture.md` §3 still names Young Serif, which this file retired | playbook 5 | Correct the status line. Light edit to `stage_architecture.md` §3 |
| `stage_architecture.md` §3 to §7, §12 | Living spec | Three plainly stale passages (named below). Otherwise current | playbook 1, 4, 8; learning `stage_motion`, `rendering_pipeline` (area C places them) | Index. Light edits |
| `beat_sheet.md` head and section list | Living spec | The head names one golden game; there are two. §15 lists two open items that are answered | playbook 1; story 6 (head, see the constraint check) | Index. Light edit to the head and §15 |

## Per document

### design_2026-09-25/
- **Documents:**
  - `HANDOFF.md`: about 7,100 words. The record of what the design chat decided, scene by scene (§4), with the replay container (§5), live pacing (§6), the tier table (§7), the kit changes (§8), the build list (§9) and the benches (§10).
  - `BUNDLE_README.md`: about 250 words, how to open the benches and render one headless.
  - `landing-handoff-2026-09-22.md`: about 1,100 words, the landing prototype's state for the next chat.
  - `kits/cast.js`, `puppet-kit.js`, `role-kit.js`, `stage-kit.js` (829 lines in all) and `sprites-manifest.json`: frozen copies from the benches. Listed only.
- **Kind and status:** dated brief, superseded as the spec. `stage_architecture.md`'s head says "Where this file and the handoff disagree, this file wins (§9 lists every such point)", and the beat sheet cites the handoff only as "the narrative behind each row".
- **Reader question:** what did the design chat agree for the live game and the replay, and why?
- **Currency:** not checked against code, dated record. Four points a reader would take as current:
  - The header calls it "the document the codebase build starts from", with no date of supersession.
  - It is marked superseded only where the 2026-09-29 pass changed it (the drape, the tabs, the skip speed). Later replacements are unmarked: the bundle's figures by the costumed cast (2026-09-28), the shelf room and plush dolls by the painted compartments (2026-09-28), the film by the case file (2026-09-29), nine seats by ten.
  - `stage_architecture.md` §9 claims to list "every such point", but it lists only seven early ones. The later departures are recorded as "As built" lines inside the beat sheet's sections, not in §9.
  - §6 says "Beats queued between the stage and the request drain at fast speed". The beat sheet §0 reverses this: "Live plays every beat at these holds at normal speed, in arrival order, however many are queued (§12, ruled 2026-10-01)". That reversal is the "read or jump, never hurry" rule of story 7, so the handoff's §6 is that story's before-picture. Area C should know it is here.
- **The bundle is split, and the handoff does not say so.** §11 lists `benches/`, `sprites/`, `production-log-rev-62.html`, `reference-events-schema.py` and `README.md`. In the repo, `README.md` is `BUNDLE_README.md`. The benches, sprites and production log are in `frontend/claude_artifacts/design/`, which `frontend/.gitignore` excludes (`stage_architecture.md` §1 ruling 5 records this). The reference schema is in neither place; `stage_architecture.md` §9 says it was byte-identical to `server/schemas/events.py`. Anyone cloning the repo cannot open a bench; the claude.ai links in §10 need a login.
- **One-home conflicts:**
  - §4.1, a human who leaves ("every turn delegates; ... whether a seat can be reclaimed is the server's call"), is the 2026-09-25 form of the AFK ruling. Home: `seat_continuity.md` §4, per area A. The handoff keeps its text under the status line.
  - §6, live pacing and reconnect ("history renders still at the latest state"). Home: beat sheet §12.
  - §7, the tier table. Home: beat sheet §13 for the stage and `server_client_transport.md` §5 for the wire.
- **Feeds:** playbook 1 (mock to spec), playbook 7 (the handoff between sessions), playbook 8 (the benches' controls and captions). Story 7, as history only.
- **Proposed action:**
  1. A status line on `HANDOFF.md`: "Dated record of the design chat's decisions, 2026-09-25 (amended 2026-09-29). The truth for what the stage shows is `beat_sheet.md`; for how it is built, `stage_architecture.md`. Later departures are their 'As built' lines, not marked here."
  2. One line in §11: the benches, sprites and production log are archived in `frontend/claude_artifacts/design/` (not in git), and `README.md` is `BUNDLE_README.md`.
  3. A one-line status on `landing-handoff-2026-09-22.md`: superseded by `design_2026-09-26/pages_review.md` §F and `site_architecture.md`.
- **Terms used before definition:** *the wing* (used in §1 and §2, never defined; it is the seat rail), *the dock* (§1, never defined; it is the human's turn panel), *beat* (used in §1, defined in §5), *the strip* ("the top strip", §2), *special* (the stage-lighting term, §4.4), *hub* and *spoke* (§4.9, defined there by use), *rev 62* and *bench 75* (revisions of the design chat's production log, explained only in §10).

### design_2026-09-26/pages_review.md
- **Documents:** about 6,200 words. §A, the five mocks' wire fields; §B, 17 conflicts with the rulings and the code; §C, the brief item by item; §D, the build order; §E, ten questions for the owner; §F, nine owner rulings with dated amendments.
- **Kind and status:** dated audit with rulings, 2026-09-26, amended to 2026-09-29. Executed: the site shell, archive, ticket office, platform scene and landing all exist (`frontend/src/app/(site)/`, `StationScene`). No line says so.
- **Reader question:** can these five mockups be built on the code and server as they stand, what conflicts, and what did the owner rule?
- **Currency:** not checked, dated record. Its anchors are line numbers "as of `13eb753`", which is correct for a dated audit.
- **One-home conflicts:**
  - The product name: F2 holds it, amended three times (Carriage Nine, then The Ninth Express, with the headlamp mark). This is its one detailed home; `site_architecture.md` should link here rather than restate it (area B to confirm).
  - The landing's mini replay: F7 (ruled 2026-09-26, amended 2026-09-27) is the decision; `stage_architecture.md` §8 describes the `mini` mode as built. `beat_sheet.md` §15 still lists "which beats it plays" as open, and `stage_architecture.md` §9 says "decided with the landing". Close both with a pointer to F7.
  - The waiting room's orientation: F1, already folded into `stage_architecture.md` §1 ruling 3 with a pointer back. Consistent.
  - Memory off by default and neutral copy: B12 and F6, consistent with the constraint.
- **Feeds:** playbook 3 (the exemplar), playbook 6 (§F is the rulings convention at its fullest), playbook 9 (B12, B14 and F9: copy checked against the server).
- **Proposed action:** a status line: "Executed 2026-09-26 to 2026-09-29; the rulings in §F are current except where `site_architecture.md` records a later change."
- **Terms used before definition:** *the carriage* (the landing's framed mini replay, used in §A and explained in B17), *slate* (the archive's game card), *hang tags*, *the platform*, *the ledge*, *Opus* and *the main loop* in §D (an Opus subagent and the main Claude session; a portfolio reader may take "main loop" for the owner).

### design_2026-09-28/
- **`scorecards_plan.md`** (about 1,000 words): a dated plan, "planned, nothing built". Still true: there is no `server/game/scorecard.py`, no `stats` route, and no `SeatScore` anywhere in `server/` or `frontend/src/` (checked 2026-10-26). Its numbers carry their N and date (N=180 on 2026-07-02, n=50 on 2026-06-11; 212 archived games). Proposed action: date the status ("not built as of 2026-10-26"). Feeds playbook 9 through one idea, the parity test ("the site's numbers and the eval's numbers can't drift apart"). Terms: *validated basket*, the ★ mark, *epoch-local*.
- **`landing_features.md`** (about 1,100 words): a dated brief, built 2026-09-28 (`Features.tsx` exists in `frontend/src/app/(site)/_components/landing/`). Card 3's second half waits on the scorecards, still true. "Why this wording" says served games "draw on a snapshot from research runs"; `server/game/run_config.py`'s docstring now says lessons are read from the database's published store. The card copy itself was written to stay true in either case. The exhibit's model (Gemini 3.5 Flash-Lite) is that game's, not the site default. Proposed action: a status line noting the lesson source changed on 2026-10-14 and the copy did not need to. Feeds playbook 9 (its "Why this wording" and "The drafted line is real" paragraphs are the exemplar). Terms: *the carriage*, *the loop strip*, *the served snapshot*.

### role_cards_brief.md
- **Documents:** about 5,100 words. §0 owner rulings (six), §1 house style read off the six existing figures, §2 lineup, §3 one entry per figure, §4 card text, §5 the prompt with its gate and the "habits seen" list, §6 shipping, §7 open.
- **Kind and status:** dated brief. Shipped 2026-10-07 (§6). The header still reads "Status: DRAFT, revised 2026-10-07 after review".
- **Reader question:** how were the eight new role figures specified, generated and shipped, and what does each card say?
- **Currency:** not checked, dated record. §7's one open item (the Fortune Teller's self-bet rule) belongs to the role sheet in `evidence/`, not here.
- **One-home conflicts:**
  - §4's card text. Home: `src/stage/card-text.ts`. The brief's block is what was proposed on 2026-10-07, and later engine rulings may have changed lines. The status line should say the code is the truth.
  - §6's shipping path. Home: `stage_architecture.md` §4 (the role sprites' location list). The brief states it in detail because the fit was "written down for the first time" there. Keep both, with the brief as the record of how.
  - Ruling 1 ("Town", not "Villagers") is a UI-wide naming rule recorded only here. Any later sweep of side names should cite it.
- **Feeds:** playbook 2 (§0, §1, §5 and §6 are the asset-brief exemplar), playbook 6 (§0).
- **Proposed action:** status line: "Shipped 2026-10-07 (§6). The card text in §4 is as proposed; `src/stage/card-text.ts` is the truth."
- **Terms used before definition:** *the six* (the existing figures), *level 2* (a role-sheet term), *the costume rule* (named in the intro, defined in `cast_expansion_brief.md`).

### cast_expansion_brief.md
- **Documents:** about 4,700 words. Sections in file order:
  - "Final template" (ruled 2026-10-03): what the rounds taught, the shared blocks, the steps, the gate, and the owner's state prompt.
  - The candidates ruled; the costume rule; free colour slots.
  - "Process" and Prompts 1 to 4: the first method.
  - Rounds 2, 3 and 4: the design journey, with the owner's words.
  - "The cast record": the database tables, the picker, the frontend fallback, and the deploy note.
- **Kind and status:** dated brief whose rounds form a journey log. Shipped 2026-10-03 (four characters: kitsune, mushroom, lionCub, automaton).
- **Reader question:** how were four new puppets designed to the house style without hinting at a role, and how does a game remember its cast?
- **Currency:** checked only "The cast record", because it describes server and site behaviour. `server/game/game_session.py::GameSession._deal_cast`, `frontend/src/stage/cast/castForGame.ts::resolveCast` and `LEGACY_CHARACTERS` exist as described.
- **Internal supersession:** the file's order inverts its history. The template at the head says the states come from one call returning four images ("Fallback: ... rerun that single state alone"). "Process" step 2, lower down, says "Six generations per character, one pose per image, no multi-pose sheets". A reader who starts at "Process" follows the superseded method. A line at the head of "Process" ("the first method; the template above replaced it on 2026-10-03") fixes it.
- **One-home conflicts:**
  - "The cast record" has no home outside this art brief. It is a design decision ("a game's cast is a fact about the game, stored in tables, not recomputed") with a schema and an API. Recommended home: a short section in `site_architecture.md` that summarises it and links here, or moves it (area B to decide).
  - The conversion recipe for the four: home `stage_architecture.md` §4 "The cast", "Four more". The brief points there. Consistent.
  - The costume rule (line 263: "no role props ..., no numerals, no dominant red / violet / cyan, equal mild expressions"). This is its one detailed home. It lists what is banned but never says why: a puppet is the face every viewer sees for a seat, so a costume that hinted at a role would leak hidden information. The playbook should carry the reason.
- **Feeds:** playbook 2 (the template is the strongest exemplar of "the spec aims past the goal", the cuteness pass and the measured gate).
- **Proposed action:**
  1. A section index at the head, in the form above.
  2. A status line: "Shipped 2026-10-03. The template at the head is the method; 'Process' and Prompts 1 to 4 are the first method it replaced."
  3. A pointer to "The cast record" from `site_architecture.md`.
- **Terms used before definition:** *the whale base* (the existing whale captain sprite used as the style anchor), *BODY and REACH* (defined in `stage_architecture.md` §4), *the eleven*.

### night_rooms_brief.md
- **Documents:** about 4,100 words. §1 which roles get a room, §2 the plan every room keeps, §3 the six rooms with a shape table, §4 the prompt (per room and all six in one call) and the gate, §5 shipping with the gate's measured results, §6 open (nothing).
- **Kind and status:** dated brief. Shipped 2026-10-07 (§5). The header says "Status: DRAFT".
- **Reader question:** how were six night rooms painted so that they differ in shape but keep every measure the code relies on?
- **Currency:** not checked, dated record.
- **One-home conflicts:** the shipping recipe. Home: `stage_architecture.md` §4 "The night rooms" ("Six more (2026-10-07, `docs/night_rooms_brief.md`)"). Consistent.
- **Feeds:** playbook 2. Two of its rules are distinctive:
  - §3: "a negative that names an object tends to summon it", so the negatives move from the prompt to the gate.
  - §4: one batch call for all six, with the per-room prompt kept for reruns.
- **Proposed action:** status line: "Shipped 2026-10-07 (§5). Nothing open."
- **Terms used before definition:** *the plan* (defined in §2 by its file), *the photo line*, *card spot*, *the five* (the earlier rooms).

### music_brief.md
- **Documents:** about 1,300 words. The existing score measured (key, tempo, RMS loudness per cue), what to make (four victory stings, a morning bed, two optional pieces), technical rules, and how each piece is placed.
- **Kind and status:** dated brief, delivered. The file has no date and no status; its modification date is 2026-10-15. `frontend/public/music/` holds `win-town`, `win-wolves`, `win-lone-killer`, `win-draw`, `dawn-loop` and `dawn-extended` (all `.v1.mp3`), which match the brief's cues. Neither optional piece (the deal one-shot, a second vote loop) is there. `stage_architecture.md` §12 (2026-10-15) uses the stings.
- **Reader question:** what music was still missing, and to what measured standard was it ordered?
- **Currency:** checked by listing `public/music` only.
- **One-home conflicts:** "How each piece is placed" repeats the scene holds and cue placement. Home: `stage_architecture.md` §12 and `src/music/cues.ts` for the cues, beat sheet §0 for the holds. The brief's table was a briefing aid for the composer and can stay as dated.
- **Internal inconsistency:** "Deliver MP3" against the naming rule's examples (`win_town_1.wav`). The shipped names follow neither (`win-town.v1.mp3`, versioned per §12). Leave it; it is a dated brief.
- **Feeds:** playbook 2. It extends the asset brief to audio: the house style read off the approved pieces becomes a measured table of key, tempo and loudness.
- **Proposed action:** a status line: "Written 2026-10-15. Delivered: the four victory stings and the morning loop (`public/music`, `stage_architecture.md` §12). Not made: the optional deal piece and second vote loop."
- **Terms used before definition:** *bed* and *sting* (clear from use; defined in `stage_architecture.md` §12), *the deal*.

### opening_round_brief.md
- **Documents:** about 560 words. What the screen is, the plan to paint on, how it ships, acceptance.
- **Kind and status:** dated brief, 2026-10-11, not built. There is no `opening.png` in `frontend/claude_artifacts/design/rasters/rooms/`, no `rooms.opening` in the code, and `DayScene.tsx` still writes "Everyone is writing their opening." on a placard. The beat sheet §2 row 7 records the placard as the owner's choice of 2026-10-15. The record does not say whether the painting was dropped or deferred.
- **Reader question:** what single painting would replace the opening round's notice?
- **Feeds:** none for the chapter. Its "Acceptance" section is a compact example for playbook 8 (acceptance written as workbench views plus a named test).
- **Proposed action:** status line: "Not built. The stage shows the placard of beat sheet §2 row 7 (owner, 2026-10-15)." The owner should say whether it is dropped or deferred.
- **Terms used before definition:** *the dock*, *composer*, *the sweep rounds*, *prepares beat*.

### typography.md
- **Documents:** about 800 words. The six faces (three voices, three props), the voice test, sizes and weights, numbers, the build.
- **Kind and status:** living spec, ruled 2026-10-16 with the owner on a mock with a switch per change. Header: "Status: built 2026-10-16 (the four steps at the end), not yet deployed". The owner's records outside this folder say the typography was ruled and deployed. The header should be corrected after the owner confirms the date.
- **Reader question:** which face sets which text, and how does a builder decide?
- **Currency:** checked only the cross-references. `stage_architecture.md` §5 matches it and says it "retired the 2026-09-29 Young Serif". But `stage_architecture.md` §3 "The HUD's look" still says "Two voices (§5): Young Serif for what is engraved or announced, Literata for what is said and read".
- **One-home conflicts:** fonts are stated in four places:
  - this file;
  - `stage_architecture.md` §5;
  - `stage_architecture.md` §3 (stale, as above);
  - `pages_review.md` B4 and F3 (Silkscreen dropped, dated).

  Home: this file. §5 already summarises and links; §3 should point to §5 instead of naming faces.
- **Feeds:** playbook 5 (the exemplar). Its voice test ("would this sentence make sense if the train were real?") is the best example in the folder of giving a builder a test instead of a list.
- **Proposed action:** correct the status line. Light edit to `stage_architecture.md` §3, "The HUD's look": replace the Young Serif sentence with "The faces: §5 and `typography.md`".
- **Terms used before definition:** *plate buttons*, *the case file*, *the strip*, *the reading room* (§ "The build", step 4).

### stage_architecture.md §3 to §7 and §12 (index only)
- **Kind and status:** living spec, the code shape of the stage. Header "Ruled 2026-09-25"; sections carry their own dated rulings up to 2026-10-19.
- **Reader question:** how is the stage laid out, what assets does it use and how are they made, how does it move, and how does a builder see it?
- **Plainly stale passages** (noted, not code-checked beyond the listed files):
  1. §3 "The HUD's look": Young Serif, as above.
  2. §4 "Rasters", the location list: `rooms/{healer,investigator,vigilante,serial_killer,wolf}.webp` and the line "Characters: cat hare owl ... shade" list the first five rooms and eleven characters. The same section adds six rooms (2026-10-07) and four characters (2026-10-03) further down. Add the new ids to the list.
  3. §9 "Deferred by decision" (outside the indexed range, but it bears on the same items): "whether a seat can be reclaimed (server's call)". The server has `POST /games/{id}/rejoin` (`server/routes/rooms.py::rejoin_game`), described in `server_client_transport.md` as the reclaim door. Area A should confirm whether that answers the item as meant (a seat reclaimed after leaving, not only a lost cookie).
- **Proposed index:**

| Section | Content | Feeds |
|---|---|---|
| §3 opening, the bleed, legibility | The 1600×900 unit box, one CSS scale, the bleed past 16:9, two legibility tiers for the phone | learning `rendering_pipeline` (area C) |
| §3 "Layers" | The nine stacked layers from paint to HUD | client design record (area B: the stage pipeline) |
| §3 HUD look, side slot, seat rail, transcript, atmosphere | The HUD as walnut furniture (three passes, 2026-09-29), the slot's reach, the rail, the drawer, the key light | none (design); the Young Serif sentence is stale |
| §4 "The rule", "Rasters" | WebP conversion, the sprite locations, then one entry per asset family: the felt props (2026-10-17), the cast (2026-09-28, with the four of 2026-10-03), the night rooms (2026-09-28, with the six of 2026-10-07), the seat rail (2026-10-18), the HUD kit (2026-10-19), "Never upscale" | playbook 2 (the shipping half of every asset brief); learning `memory_and_pictures` (area C) |
| §4 "Vector" | What stays vector: paint generators and instruments | none |
| §5 | Fonts and material tokens; Mantine kept out of the stage | playbook 5 (points to `typography.md`) |
| §6 opening | "Arrive still, play moving"; holds come from the beat sheet; selection never moves | learning `stage_motion` |
| §6 "GPU rules" to "Performance knobs not yet turned" | The phone rules ruled from A/B and census: no masks, baked set, nothing animates at rest, a mover rides its own box, the probes `?gpu=` and `?auto=`, the phone-rule gate, the set and body split, the knobs left (audit 2026-10-18) | playbook 4; story 10; learning `stage_motion`, `rendering_pipeline`, `performance_method` (area C places them) |
| §7 | The workbench route: the URL is the whole state, the registry shared with the player, phone frames, Playwright screenshots "for the agent to see the screen without the owner" | playbook 8 (the exemplar); learning `testing` (area B's walk) |
| §12 | Music: the cue sheet as a pure function of the beat, the Web Audio player, the first-press rule, the switch | none for the chapter; playbook 2 (the brief it came from) |

- **Terms used before definition** (in the indexed range): *the wing*, *the slot*, *the band*, *the strip* (the HUD's pieces, named in §3's layer list before any is described), *the car*, *at rest* (§6, clear from use), *census* (§6, from the build log).

### beat_sheet.md (head and section list, index only)
- **Kind and status:** living spec, "the source of truth, beat by beat", mirrored by `src/stage/beats/beatsFor` and pinned by goldens.
- **Reader question:** what does the stage show at each event, for each viewer, and for how long?
- **Plainly stale passages:**
  1. The head says the goldens are "on the fixture game (9369a5c1, memory on)". `src/stage/beats/__goldens__/` also holds `phase2.public.txt` and `phase2.xray.txt` (the game with rounds, beat sheet §2 rows 7 to 10, per `stage_architecture.md` §7). Add the second game to the head.
  2. §15 "Open": "The landing's miniature replay: which beats it plays" was ruled in `pages_review.md` F7. "Whether a seat can be reclaimed after leaving" may be answered by the rejoin door (area A to confirm). Close what is closed, with pointers.
- **Proposed index:**

| Section | Content | Feeds |
|---|---|---|
| Head | The table is mirrored by `beatsFor` and checked by goldens: "Change the table, change the code, regenerate the golden, in that order" | playbook 1 (its rule); story 6 |
| §0 Conventions | Columns (anchor, sees, stage, slot, hold), the holds with their dated history, speech paged at 150 characters, reading pace 2.4 words a second | story 7 (holds); playbook 6 (old values kept beside new ones) |
| §1, §1a | The deal; the platform (the waiting room, live only) | none |
| §2 | Day discussion, with the Phase 2 rounds (rows 7 to 10) | none (chapter C covers the wire, not the scene) |
| §3 to §8 | Vote, lynch, night lobby, acting seat, pack, morning | none |
| §9 | The replay's night: hub, spokes by actor's branch, the whole night (replay only) | none |
| §10 | Game over and the epilogue | story 3 (the X-ray at game over, stage side) |
| §11 | The replay's container: transport, chapters, the slot, the drawer, the case file | client design record (area B: live and replay on one renderer) |
| §12 | Live pacing: the queue, the dock, the turn jump, catch-up | stories 4 and 7 (area B and C read it) |
| §13 | Viewers and tiers, one table | story 3 (stage side) |
| §14, §15 | Polish list (none open); open items | none |

- **Terms used before definition:** *goldens* (in the head; the golden files of expected beat output), *bench*, *beat* (the head uses it; §0 defines the columns, not the word), *the dock* (used from §1, defined in §12).

## Area-level

### Overlaps, one home each

| Ruling or fact | Told in | Home | The others |
|---|---|---|---|
| Fonts | `typography.md`; `stage_architecture.md` §5, §3; `pages_review.md` B4, F3 | `typography.md` | §5 summarises and links (correct). §3 points to §5. `pages_review.md` stays dated |
| Role card text | `role_cards_brief.md` §4; `src/stage/card-text.ts` | the code | The brief's status line says so |
| Asset shipping recipes (cast, rooms, role figures) | the three briefs' shipping sections; `stage_architecture.md` §4 | `stage_architecture.md` §4 | Briefs keep their record of how, pointing there (they already do) |
| Music cues and placement | `music_brief.md` "How each piece is placed"; `stage_architecture.md` §12; `src/music/cues.ts` | §12 and the code | The brief stays dated |
| The landing's mini replay | `pages_review.md` F7; `stage_architecture.md` §8, §9; `beat_sheet.md` §15 | F7 for the decision, §8 for the code shape | Close §9's row and §15's item |
| A human who leaves; seat reclaim | `HANDOFF.md` §4.1; `stage_architecture.md` §9; `beat_sheet.md` §15 | `seat_continuity.md` §4 and transport §6b (area A) | The handoff stays dated; §9 and §15 point to area A's home once confirmed |
| Live pacing when the stage is behind | `HANDOFF.md` §6 ("drain at fast speed"); `beat_sheet.md` §0, §12 ("normal speed, however many are queued", 2026-10-01) | `beat_sheet.md` §12 | The handoff's version is the superseded one |
| The cast record (tables, picker) | `cast_expansion_brief.md` only | to be decided (area B): `site_architecture.md` or the brief with a pointer | none yet |
| The costume rule | `cast_expansion_brief.md` (rule); `role_cards_brief.md` intro (its opposite for role cards) | `cast_expansion_brief.md`, with its reason added in the playbook | none |
| Product name and mark | `pages_review.md` F2 (amended three times) | F2 | `site_architecture.md` links (area B to check) |

### Placement unclear
- **`design_2026-09-28/`** holds two unrelated documents, a built landing brief and an unbuilt feature plan. Each is self-contained, so a status line on each is enough; no move is needed.
- **`opening_round_brief.md`**: dropped or deferred is the owner's call. If dropped, it is a candidate for git history alone, since it shaped nothing that shipped. Under the style guide's rule (keep a finding only if it played a key role or shows a skill nothing else shows), it does neither.
- **The four briefs share one gap.** Their "Status" lines were written when the brief was drafted and not updated in the commit that shipped the assets (role cards and night rooms both say DRAFT after shipping; typography says "not yet deployed"). This is a process fault, not a document fault, and becomes one step in playbook 6.

### Constraint check (brief §8)
- **Persona voices: the brief's constraint looks wrong.** §8 says "Persona voices are OFF; the silence ruling stands (2026-10-18)". `server/game/run_config.py` sets `persona_voices=True` with the docstring "AI seats use their dealt puppet's speaking voice in served games". The latest commit on this branch (73aafcb9) is titled "docs(writeup): the proposal records voices as on in hosted games, not off". No document in area D mentions voices. The main session should correct the brief before the proposal relies on it.
- **No CI:** `stage_architecture.md` §7 says Playwright is "Not a CI gate until the scenes stop moving". It does not claim a CI runs, but it implies one exists to gate on. Suggested wording: "There is no CI; the suite runs by hand."
- **Authorship:**
  - `stage_architecture.md` §11 and `pages_review.md` §D assign work to "Opus" and "the main loop", meaning an Opus subagent and the main Claude session. A reader may take "main loop" for the owner. Wherever the write-up or the playbook quotes them, say "the main session" and state that the owner ruled and the agents built.
  - Story 6 lists "beat_sheet head" as a source for "the owner wrote the event schema and the beat sheet". The head carries no authorship statement, so that claim must come from the owner, not be cited to the document.
  - `HANDOFF.md` is "consolidated from the production log" of a design chat. Its "Agreed" marks are agreements between the owner and that chat.
- **Default seat model:** `landing_features.md` and `pages_review.md` B9 name Gemini 3.5 Flash-Lite as one game's model and as a display-name example. Both are dated and do not claim it is the default. No conflict.
- **Memory off by default:** `pages_review.md` B12 and F6, `landing_features.md`. Consistent.
- **Music deployed 2026-10-15:** consistent with `stage_architecture.md` §12 and `public/music`. `music_brief.md` reads as pending only because it lacks a status line.
- **Beat sheet and stage_architecture are the truth; goldens pin them:** consistent. Both say they win over the handoff. The head's golden list is incomplete, as noted.
- **General jump not built, stall watchdog not built, served-game fingerprints, one-game numbers:** none of the area's documents touch these.

### The playbook: table of contents (brief §7)

`frontend/docs/playbook.md`, about two pages. Each section gives when to use the method, the steps, the exemplar sections and the one rule it taught. One fact applies to every section and belongs in a two-line preface: the owner ruled, and AI agents built. The design benches and the generated masters live in `frontend/claude_artifacts/`, which is not in git, so every exemplar below is a document in the repo, not a bench.

The six candidates are confirmed. Three are added (7 to 9). Two were considered and not added.

**1. Mock to spec to code to golden.** *Confirmed.*
- *When:* a design made outside the repo (a design chat's benches) has to become code that agents build and keep correct.
- *Steps:*
  1. Design on benches, one per scene, each with controls (viewer, fixture, frame, motion) and a caption naming the wire event that drives the beat (`BUNDLE_README.md`; `HANDOFF.md` §10).
  2. Consolidate into a handoff that separates what was decided from how it was reached (playbook 7).
  3. Write the codebase's own "how" document, which wins over the handoff and lists where the build departs from it, with the reason for each (`stage_architecture.md` head, §1, §9).
  4. Make a beat table the truth, mirror it in one function (`beatsFor`), and pin it with goldens on a real archived game (`beat_sheet.md` head, §0).
  5. Order the work and say who does each step (`stage_architecture.md` §11).
  6. Tag the old version before deleting it (`stage_architecture.md` §1 ruling 6, §10, `theater-v1-baseline`).
- *Exemplars:* `HANDOFF.md` §1, §4, §9; `stage_architecture.md` §1, §2, §9, §11; `beat_sheet.md` head and §0.
- *Rule:* "Change the table, change the code, regenerate the golden, in that order" (`beat_sheet.md` head).
- *Gap to fix while writing it:* `stage_architecture.md` §9 stopped being updated after the early departures; the later ones are scattered "As built" lines. The step should say the departure list is kept current, or replaced by a pointer to the "As built" lines.

**2. The asset brief for image and audio generation.** *Confirmed, extended to audio.*
- *When:* a new picture or sound must match a set already shipped, and a generator does the making.
- *Steps:*
  1. The owner's rulings first (`role_cards_brief.md` §0).
  2. The house style read off the approved pieces, written as rules (`role_cards_brief.md` §1). For audio, the existing cues measured for key, tempo and loudness (`music_brief.md` "The existing score").
  3. What the asset must never carry. For puppets this is the costume rule, because a puppet is every viewer's face for a seat and a role prop would leak hidden information (`cast_expansion_brief.md`, the paragraph after the candidates). Role cards are the opposite case: the figure holds what its sigil shows (`role_cards_brief.md` intro).
  4. Shared blocks pasted into every step. A lineup sheet first, to judge colour and silhouette only. Then one item per call with the previous approval attached (`cast_expansion_brief.md` "Final template"; `role_cards_brief.md` §5).
  5. A spec that aims past the goal, because the model under-delivers on proportions (60 to 65% head, not 58%) (`cast_expansion_brief.md` "Final template", first paragraph).
  6. A negative that names an object tends to summon it, so the negatives move from the prompt to the gate (`night_rooms_brief.md` §3 last paragraph, §4 "Gate").
  7. A measured gate on the alpha box before the next step (`cast_expansion_brief.md` "GATE"; `role_cards_brief.md` §5 "GATE").
  8. Batch the call and keep a single-item prompt for reruns (`night_rooms_brief.md` §4).
  9. Record the first generation's bad habits and forbid them in the prompt (`role_cards_brief.md` §5, the paragraph after the block).
  10. The shipping checklist: master to the archive, fit script, manifest, code entry, gate results written down (`role_cards_brief.md` §6; `night_rooms_brief.md` §5; `stage_architecture.md` §4 "The cast").
- *Rule:* each step attaches the last approved picture, never the original anchor ("the approved base attached, never the whale", `cast_expansion_brief.md` "Process" step 2).

**3. Mock-against-repo review.** *Confirmed.*
- *When:* mockups arrive that must be built into an existing codebase and server.
- *Steps:*
  1. Work read-only.
  2. For each mock, list every field it reads or sends as one of three: exists today ("Ours"), derivable, or missing on the wire (§A).
  3. List the conflicts with the rulings and the built code, each with evidence and a recommended verdict (§B).
  4. Take the brief item by item: as written, differently, or skip, each with why (§C).
  5. Give a build order with size and who (§D).
  6. List the questions only the owner can answer (§E).
  7. Record the owner's rulings, with later amendments dated in place (§F).
- *Exemplar:* `design_2026-09-26/pages_review.md` §A to §F.
- *Rule:* check every claim a mock makes against the code before building it. B5 found that "no component imports `@mantine`" although the brief assumed Mantine. B11 found that the server refuses every join to a locked room, including by link, which the mock's copy promised.

**4. Measured performance work: audit, census, one batch, a gate.** *Confirmed. Area C reads the exemplars in depth; the sections are named here for the table of contents.*
- *When:* the browser crashes or stutters and fixes keep finding one more instance of the same cause.
- *Steps:*
  1. Audit on an isolated snapshot, stating what the host can and cannot show (software graphics is not an iPhone) (`rendering-audit-2026-10-02.md` "Scope and reproducibility", "What these results deprioritize or leave open").
  2. State the rule (`stage_architecture.md` §6 "GPU rules").
  3. Build probes that remove one kind of work each (`?gpu=`, `?auto=`, `stage_architecture.md` §6).
  4. Census every instance across every scene and beat.
  5. Fix the whole list in one batch.
  6. Make the rule a test (`build_log.md` §8.7; `e2e/phone-rule.spec.ts`).
  7. Measure before and after (`frontend-audit-2026-10-11.md` "Follow-up, 2026-10-15").
  8. List the knobs not yet turned (`stage_architecture.md` §6 "Performance knobs not yet turned").
- *Rule:* when the fourth fix of one rule follows the fourth crash, the rule becomes a test ("the owner called it whack-a-mole, rightly", `build_log.md` §8.7).

**5. Decision by a mock with a switch per change.** *Confirmed, with two more instances.*
- *When:* a visual decision has several independent parts and the owner must judge them in place.
- *Steps:*
  1. List the candidate changes.
  2. Build one mock with a toggle for each, so every change is compared against the same page.
  3. The owner rules switch by switch.
  4. Write the rule with a test a builder can apply.
  5. Record what was retired and why.
  6. List the build steps with their done date.
- *Exemplars:*
  - `typography.md`: the head, with the mock's link; "Which voice: the test"; the Young Serif retirement and its reason; "The build".
  - The logo, chosen on a bench over two alternatives (`pages_review.md` F2, second amendment of 2026-09-29).
  - The benches' own control strips (`BUNDLE_README.md`).
- *Rule:* give the builder a test, not a list ("would this sentence make sense if the train were real?").

**6. The rulings convention.** *Confirmed, with one step added from this scan.*
- *When:* any design document an agent will build from.
- *Steps:*
  1. "Rulings (owner, date)" first, numbered.
  2. Proposals below, marked as proposed.
  3. Amendments made in place, dated, with the reason and what they replaced.
  4. The old value kept beside the new one.
  5. "Open for the owner" at the foot, closed in place when ruled.
  6. The owner adjusts against the running app, not the mock (the holds raised on 2026-09-30 and 2026-10-01 after live play, `beat_sheet.md` §0).
  7. **Added:** the status line is updated in the same commit that ships. This scan found three documents whose status rotted: `role_cards_brief.md` and `night_rooms_brief.md` say DRAFT after shipping, and `typography.md` says "not yet deployed".
- *Exemplars:*
  - `role_cards_brief.md` §0 and §7.
  - `pages_review.md` §F.
  - `stage_architecture.md` §1, and §12 ("owner, 2026-10-15; they had alternated by day, and the masked accusations were too gloomy for a day 2").
  - `HANDOFF.md`'s Agreed, Proposed and Open marks.
  - `beat_sheet.md` §0's holds ("shutter 6.0 s (3.5 until 2026-10-01, 3.0 before 2026-09-30)").
- *Rule:* a superseded value stays on the page beside its replacement, with both dates.

**7. The handoff between sessions.** *Added. It may fold into section 1 if the page runs long.*
- *When:* work moves from one chat or agent to another (a design chat to the codebase, one design chat to the next).
- *Steps:*
  1. Say what the document is for and what it is not. The benches are the record of how decisions were reached; the handoff is the record of what was decided (`HANDOFF.md` second paragraph).
  2. State the scope and what is left for a later session (`HANDOFF.md` third paragraph, §9 last line).
  3. Give each item a status: Agreed, Proposed or Open.
  4. Record the principles that came out of the work (`HANDOFF.md` §1).
  5. Name the decisions that are expensive to retrofit, so they are settled before assembly (`HANDOFF.md` §9: names or seat numbers, the sprite canvas size, the mini replay).
  6. Give one link the next session can reopen and keep editing (`landing-handoff-2026-09-22.md` "The prototype").
  7. List the bundle's contents and where each file lives (`HANDOFF.md` §11, which this scan found out of step with the repo).
- *Rule:* settle the decisions that are expensive to retrofit before assembly starts.

**8. Give the builder eyes: the workbench.** *Added.*
- *When:* an agent builds a visual surface it cannot see, and the owner cannot review every step.
- *Steps:*
  1. One route mounts the real components on a bundled fixture game, never a copy of them.
  2. The URL holds the whole state, so any view can be named in text and reproduced.
  3. The captions and the beat stepper come from the same table as the real player.
  4. Phone frames are drawn on a desktop.
  5. Playwright takes a screenshot per named URL, "for the agent to see the screen without the owner".
  6. Acceptance criteria are written as workbench views plus a named test (`opening_round_brief.md` "Acceptance").
- *Exemplars:* `stage_architecture.md` §1 ruling 1 and §7; `BUNDLE_README.md` (rendering a bench headless to compare a beat); `stage_architecture.md` §12 (`/workbench/music` auditions sound against the beats).
- *Rule:* if a view cannot be named in a URL, an agent cannot check it.
- The owner's recorded rule "screenshot every visual change" belongs here when the main session folds the working rules in.

**9. Public copy that must stay true.** *Added.*
- *When:* site text makes a claim about the system (what an agent sees, what memory does, how a key is handled).
- *Steps:*
  1. Each claim names the code it rests on (`pages_review.md` F9 amendment: the API key line "checked against `game_session.py`"; B14 against the server's restart case).
  2. An exhibit is captured from a real run with its provenance, through the same function the server calls (`landing_features.md` card 2, "The drafted line is real").
  3. The wording is chosen to survive a change already expected (`landing_features.md` card 1, "Why this wording").
  4. A benefit claim matches the research verdict ("memory is shown as a mechanism, never as 'they play better'", `landing_features.md`; `pages_review.md` B12).
  5. Where site numbers restate eval numbers, a parity test ties them (`scorecards_plan.md` "One ruler", planned).
- *Rule:* copy describes the mechanism, never a benefit the evidence does not show.

**Considered, not added:**
- *The feature plan* (`scorecards_plan.md`). Its shape (the owner's goal, a status line, server layers mirroring the existing ones, parked limitations, a size in sessions) is good, but the feature is unbuilt and the form appears once. Its one reusable idea, the parity test, is step 5 of section 9.
- *The "who" column* (Opus or the main session; `stage_architecture.md` §11, `pages_review.md` §D). It appears in two plans as a step inside sections 1 and 3, not as a method of its own. It meets the owner's recorded rule on delegating to Opus, which the main session folds in.
