# Pages review: five mockups against the repo (2026-09-26)

Read-only verification of `frontend/claude_artifacts/design/pages/{landing,rooms,waiting-room,replays,ticket-office}.html`
(`M/` below) and the pasted build brief, against `src/`, `../server/` (`S/`) and the ruled docs. Line numbers are
from the files as of `13eb753` + working tree. "Ours" = a name that exists today in `src/types/contracts` /
`src/lib/api.ts` / `S/schemas`. Base64 payloads were not opened; sprite facts come from CSS and our WebP headers.

## A. The five pages

| Mock | What it is | Route | States (`[data-when]` / `data-*` on `<body>`) |
|---|---|---|---|
| `landing.html` (3206 l.) | Hero with two hung tags, a "carriage"-framed mini replay theatre (own JS engine, l.2321–3060), "What's under the table", role cards, latest games (slates), footer | replaces `/` (`src/app/page.tsx`) | no `.mock` panel, no toggler; mini replay modes `featured`/`whole`, `narrow` on phones |
| `replays.html` | "The archive": filter rail + cards/list | replaces `/replays` (`ReplayListClient`, `components/ReplayCard.tsx`) | `view=cards\|list`, `frame=desk\|phone` (l.239) |
| `rooms.html` | "The departures hall": split-flap board, Boarding / Under way tabs, code ticket, two hang tags | replaces `/rooms` (`RoomsClient`) | `tab=boarding\|underway`, `view=busy\|empty`, `hidefull`, `frame` (l.204) |
| `ticket-office.html` | One form for **both** doors: "Admit one" (solo) and "Admit a party" (open a room) | replaces `/play` (`PlayClient`) **and** `/rooms/new` (`NewRoomClient`). It is the create flow only: it calls `createGame` / `createRoom`. It does **not** touch `fundGame` (`POST /games/{id}/key`, restart recovery, `KeyNeededCard`) or `/admin/house`; the house purse reaches it only through `GET /models`.`house`, which the mock never shows (see B13) | `kind=solo\|party` (l.484) |
| `waiting-room.html` | "The platform": a 16:9 painted station scene (`.stage{aspect-ratio:16/9;container-type:size}`, all `cqw`, l.104), train with the dining car, sign, Invite/Ticket tags, boarding-pass sheet, walnut ledge with brass plates, Depart animation → "fades to the deal" | replaces `LobbyCard` = `/games/[id]` while `state==="waiting"` (`GameClient.tsx:114`) | `state=waiting\|departing`, `role=host\|guest`, `pop=inv\|tk\|tag`, `locked`, `sheet=pass`, `passmode=join\|change`, `drawer` (l.304) |

### A1. Landing: wire fields (no Notes panel; read from `GAMES` l.2542, `tagsOf` l.2897, `drawArchive` l.2991)

| Field | Ours | Derivable | Missing on the wire |
|---|---|---|---|
| `game_id`, `finished_at`, `winner`, `days`, `n_humans`, `model`, `memory` | `ReplaySummary` (= `S/schemas/replays.py` `ReplayBase`) | | |
| `events` (mini replay) | `getReplay()` → `ReplayGame.events` | | |
| `short` (record id) | | `game_id.slice(0,8)` | |
| model display name (`MODELS`, l.2534) | `ModelsMenu.models[].label` via `getModels()` | id→label map; fall back to raw id for retired ids | |
| `ended` (day/night the game ended in) | | only from the full log | `ReplayBase.ended_phase` (the 09-22 landing handoff also asked for it, and `final_seats`) |
| "4 open" on the party tag | `listRooms()` | count of unlocked, not-full rows | |
| footer "[N] games archived" (l.1413) | | | a total: `GET /replays` returns a bare `list[ReplayBase]` (`S/routes/replays.py:16`) with no count |
| "[your name]", "[year]" | | static | |

**As built (2026-09-26, step 6).** `/` is `app/(site)/page.tsx` over `_components/landing/`. Hero: the mockup's
kicker, headline and lede, then the old landing's research line kept verbatim, two `HangTag`s from a rail (`SeatTags`:
"Play solo" → `/play`, "Open a table" → `/rooms/new`, its foot "N tables boarding" = `listRooms()` rows `rowFace` calls
joinable) and `HouseDoorNote` under them (B13). The carriage (`FeaturedReplay`, `data-frame="carriage"`, B17): walnut
from `SPRITES.wood`, roof, brass rule, rivets, bogies and rails; under the roof a "Now showing" marquee whose tiles are
the game's model label, memory, humans, days, winner and date. Inside it is `ReplayTheatre` with `mini` (F7): the game is
`SITE.featuredReplay`, or on a 404 the newest from `listReplaysWithTotal({limit: 1})`; the window is
`lib/featured-window.ts` (day 3's `vote.opens` through its `lynch.card-to-wing`, found by id and day: 48..66 on the
fixture; else the first vote through its lynch or `vote.table-down`; else beats 0..30). It autoplays at `fast` while on
screen and at least 700px wide; below that, with reduced motion, or with `?still=1`, it rests on the first beat, and
under 700px a "Watch the replay" button sits over it. The caption under the frame links the whole game ("Day 3 of game
9369A5C · watch it whole →"). *(The play, the poster and the caption were replaced on 2026-09-27: see ruling F7's
amendment.)* "What's under the table" (`UnderTable`, bench 77: notes, reads, gate; plates become tabs
under 640px of bench) is fixed to game 9369a5c1: its words and counts were re-checked against the fixture
(`under-table.ts` names the seqs). "Who's at the table": `RoleHand` (six sigils pick one card that turns to its briefing;
`CARD_TEXT` gained the kit's `day` and `win`) beside `GameLoop` (the four steps, walking while on screen), then "Take a
seat" with the tags again (as ticket stubs since 2026-09-27, owner: the full tags a screen apart read as a duplicate); "Latest games" is `ReplayListClient limit={6}` and "All replays →". The footer's
"N games archived" is live (`GamesArchived`, the one-row page's `X-Total-Count`); `site.ts` lost `gamesArchived`. Left
out: the mockup's own footer block ("Built in the open", its lede and the API-key line: the site footer stands, and the
research line moved to the hero), the pictures in "How a game goes" (the mockup draws four scenes with its own kit; no
second engine), the mockup's "whole game" mode inside the carriage (the caption links the real replay instead), the
sideways swipes on the role and workshop cards (tabs and the sigil row do the same), and the drape.

### A2. Replays (Notes l.317: "Wire fields this page reads (GET /replays)")

| Field / query | Ours | Derivable | Missing (schema) |
|---|---|---|---|
| `game_id` `winner` `days` `n_humans` `model` (""=unrecorded) `finished_at` `memory` | all in `ReplayBase`; `memory: bool` **is** there (the note's "check it" resolves yes) | | |
| phase the game ended in | | | `ReplayBase.ended_phase` |
| `winner[]` `memory` `humans` `model` `q` `sort`, date From/To (l.277) | | client-side over a full fetch while the archive is small | server filters: `list_replays` takes only `limit`, `offset` (`S/routes/replays.py:22-26`) |
| `ids[]` "played on this device" | | enumerate `seat_*` keys (`lib/storage.ts` `KEYS.seat`; needs a `seatToken.all()` accessor). Only games this browser *sat in*; solo and joined rooms both write it | |
| `limit`/`cursor` | `limit`/`offset` | | cursor (offset is enough) |
| total, distinct models | | distinct models from the fetched rows | `total` (response envelope or header) |

**As built (2026-09-26, step 2).** `/replays` is `ArchiveClient`. It makes one fetch, `listReplaysWithTotal({limit: 500})`,
which returns the rows plus `X-Total-Count`, and runs every filter and the sort in the browser (`lib/replay-filters.ts`).
Field mapping: `winner` sets the slate's colour (`--town/--wolf/--sk`), its inks (`--*-ink`) and the `Sigil` watermark.
`game_id` gives the record (the first 7 characters), the link to `/replays/[id]` and the nine chips (`castForGame` on the
full id). `days` and `ended_phase` give "Days" and "Ended" ("Night 4", "Day 3 vote"; "Unrecorded" when null). `model`
shows its `getModels()` label with the raw id and the `finished_at` date underneath ("Unrecorded" when `""`).
`n_humans` and `memory` are the stamps. `seatToken.all()` gives a "You played" stamp and the "Played on this device"
filter. The rail has search by id, played on this device, won by, **ended in** (not in the mock), memory, at the table,
model and the From/To dates. It folds behind a "Filters" bar below 900px. The toolbar has the count, removable chips for
active filters, sort, and cards/list. "Show more games" pages 12 at a time on the client. `Slate` (`components/site`)
replaces `ReplayCard`, which is deleted, and the landing's latest-games rail uses it too. Left out: search by seat name
(there are no names on `ReplayBase`) and the footer's "[N] games archived" (`site.ts` has only a static
`gamesArchived`, with no slot a page can fill).

### A3. Rooms (Notes: "Needs from the server")

| Field | Ours (`RoomSummary`, `S/schemas/requests.py`) | Derivable | Missing (schema) |
|---|---|---|---|
| name | `name` | | |
| locked | `locked` | | semantics differ (B11) |
| people aboard (of nine) | `players: list[str]`, `max_seats` (= 9: `MAX_HUMAN_SEATS = len(initial_roles)`, `S/game/lobby.py:32`) | | |
| host name ("hosted by mira") | | | `RoomSummary.host` (the server never marks which joiner is the host; the host key is only in the creator's `localStorage`) |
| code (unlocked only) `HX4R` | | | 4-char room code + a lookup route; today the id is the UUID `game_id` |
| each person's puppet (pips) | | | per-player character (B7) |
| status boarding / full | | `players.length >= max_seats` | |
| status day/night N, phase, alive count (Under way tab) | | | the whole tab: `GET /rooms` lists only lobbies (`S/routes/rooms.py:55-71`); a running game exposes only `GameStatus.alive_role_counts`, per game, with no day/phase |
| memory, model, turn clock | | | `RoomSummary.memory`, `.model` (known to the lobby: `open_room(model=, memory=)`), `.turn_seconds` (no such setting, B15) |
| watchers allowed | | | `NewRoom.watchers_allowed` + enforcement (the stream and `GET /games/{id}` are public today) |
| "manifest name once" | | device-local name key (not in `lib/storage.ts` yet) | |

**As built (2026-09-26, step 4).** `/rooms` is the lobby: an ordinary responsive page with no `OrientationGuard`.
It holds the head ("The departures hall"), `DeparturesBoard` and two hung doors under it: "Open a table" (`/rooms/new`)
and "Play solo" (`/play`). The board reads `listRooms()` through TanStack Query and refetches every 10 s, as
`RoomsClient` did. Its plate says "Departures" beside a Boarding count; Boarding is the only list. Field mapping,
one row per `RoomSummary`: `locked` and `players.length >= max_seats` give the status tiles (`Flapword`: BOARDING
amber, LOCKED or FULL dimmed; locked wins, because the server checks the lock first). `name` gives the title ("Unnamed
table" when blank), with `i-lock` when locked. `host` gives "hosted by …" ("—" while the room is empty). `created_at`
gives "opened … ago". `players` and `max_seats` give nine pips (a paper chip with the initial for each person
aboard, a dashed ring for each open place) and "3 of 9 aboard, 6 places open". `boarding.ts` (with vitest) holds
that logic. Board opens a strip under the row with "Your name on the manifest" and Join. The join is the old flow
unchanged: `joinGame(id, name.trim() || 'human')`, `seatToken.set`, then `/games/[id]`. Join is busy while it posts,
and a refusal shows the server's words in a themed `Alert` in the strip. A locked or full row keeps its place, with
the button off and the reason beside it ("Locked — ask the host to unlock it.", "Full — every place at this table is
taken."). The old "Watch instead" link to `/games/[id]` stays with that reason and with a refusal. Board states:
skeleton rows while loading, an `Alert` with "Try again" when the list cannot be read, "NO DEPARTURES" with Open a
table and Play solo when it is empty, and a footer line that says so when a background refresh fails. `RoomsClient`
is deleted. `components/Lobby.module.css` stays, because `LobbyCard`, `KeyNeededCard`, `ByokField` and
`GameEndedCard` still use it. Left out, with no placeholder: the Under way tab, codes and the code ticket, watchers,
the model and memory terms (`RoomSummary` carries neither), the turn clock, puppet pips (§F5), and the mockup's
search and "Hide full rooms" filters.

### A4. Ticket office (Notes: "Wire fields this page sends and reads")

| Field | Ours | Derivable | Missing (schema) |
|---|---|---|---|
| reads: model list | `getModels()` → `ModelRow{model,label,house_funded,is_default,needs_key}` + `house` | | |
| reads: clock range/step | | constant client-side (120–300 s / 15, l.407) | server setting if it should be server-owned |
| solo: role or random | `NewSoloGame.human_role` (+ `human: true`) | | |
| solo: puppet or any | | | `NewSoloGame.character` + seat→character on the wire (B7) |
| solo: `turn_seconds` or none | | | solo games have **no** clock (`S/game/seat_clocks.py:13,47`); needs `NewSoloGame.turn_seconds` + clocks enabled for solo |
| memory, model, key | `NewSoloGame`/`NewRoom`.`memory`, `.model`, `.api_key` | | |
| party: room name | `NewRoom.name` (max 40) | | |
| party: `turn_seconds` | | | `NewRoom.turn_seconds`; today `AFK_TIMEOUT_SECONDS = 120.0` constant (`seat_clocks.py:31`), which is the mock's 2:00 default |
| party: locked | `lockRoom()` after create | two calls | `NewRoom.locked` (optional convenience) |
| party: `watchers_allowed` | | | `NewRoom.watchers_allowed` |
| replay: role chosen vs dealt | | | `ReplayBase`/`game_started` flag; `human_role` is not persisted anywhere on the replay |

**As built (2026-09-26, step 3).** Both pages mount one `TicketOffice` (`app/(site)/_components/ticket/`) with
`kind: 'solo' | 'room'`: `/play` is solo, `/rooms/new` is the room. The two hung tags are links between the two pages,
and the current one is ringed (`HangTag current`). The submit flows are the old clients' flows. Solo calls `createGame`,
keeps `seat_token` in `seatToken` and goes to `/games/[id]`. Room calls `createRoom`, keeps `host_key` in `hostKey` and
goes to `/games/[id]`. `PlayClient`, `NewRoomClient` and `GameSetupFields` are deleted. Field mapping: the role cards →
`NewSoloGame.human_role` (`null` = the face-down "dealt at random" card; each face is `roleFigure` + `Sigil` +
`CARD_TEXT.night` in the note). Room name → `NewRoom.name` (max 40, "Unnamed table" when blank). The memory Switch →
`memory`, off by default, with neutral copy. The model Select → `model` (the `getModels()` label, with the raw id
underneath and in each option). The key → `api_key`. `house.ts` (`needsKey`, `houseLine`, moved from `GameSetupFields`
with their copy unchanged, now with vitest) decides the key row. While the house covers the model, the row shows the
house line and hides the field behind "Use my own key instead". Otherwise the field is open, and a submit without a key
is held with a field error. The mockup's always-required key is not used. A key remembered on this device opens the field
(`useRememberedKey`, now shared with `ByokField`). The key copy says a key is lost only on a server restart, after which
the game waits for a player to enter one (B14). The room's "The room" row replaces the lock radio with the server's
meaning (B11, §F6): the room opens unlocked, can be locked from the room, and a locked room admits nobody, link or not.
A lock at creation would lock the host out too, since the host joins after creating. Server refusals show in a themed
Mantine `Alert` on the stub. Left out, with no placeholder: the puppet rail and the stub's puppet (§F5), the turn clock
(§F8), watchers (§F8), and the seat name (neither request has one; the host names themselves in the room, as before).

### A5. Waiting room (Notes are design-only; fields read from the markup, l.328–377)

| Field | Ours (`GameStatus`) | Derivable | Missing (schema) |
|---|---|---|---|
| room name, locked, players, capacity | `name`, `locked`, `players`, `max_seats` | | |
| host vs guest | | host = `hostKey.get(id)` present (`LobbyCard.tsx:29`) | host's *name* for guests (`GameStatus.host`) |
| code on the sign / Invite | | link = URL | code (A3) |
| puppets per person, "Change puppet", pass rail with taken puppets | | | `JoinGame.character`; a change-character route; `GameStatus.characters` |
| Ticket popover: "Agents run on your key / mira's key", clock, memory, watchers | | | `GameStatus.model`, `.memory`, `.turn_seconds`, `.watchers_allowed`, `.funded_by` (house vs host key: the copy ignores the house) |
| "Change the terms" (host) | | | a PATCH room route |
| Lock / Depart | `lockRoom()`, `startGame(hostKey)` | | |
| Leave (guest), remove a passenger (host tag) | | | leave and kick routes (`S/routes/rooms.py` has create/list/lock/join/rejoin/start only) |

As built 2026-09-26 (step D5): `stage/scenes/StationScene.tsx` + `paint/station.ts` + the seven
station WebPs (`SPRITES.station.*`), mounted by `GameClient` in the waiting state inside the same
`OrientationGuard` and `LiveTheatre` as the game; beats `station.waiting` / `.locked` /
`.departing` (beat_sheet §1a); the ledge is walnut with a paper notice ("3 of 9 aboard · waiting
for the host") and, for the host, `ActPlate` (new `inline` prop) with Depart and Lock/Unlock;
Invite (the link, Copy) and Ticket (places, the 2:00 clock, host, open/locked) are the hung tags
and their paper panels; the boarding pass is `BoardingPass.tsx`, a page before the guard. The
states map: `state=waiting|departing` → the beats, `role=host|guest` → `RoomInput.isHost/seated`,
`locked` → `station.locked`, `pop=inv|tk` → the tags' panels, `sheet=pass` → the boarding pass
page. Depart → the train leaves → a curtain → deal beat 0, one stage (no remount). Derived, not on
the wire: "you" (the name this device boarded with, in memory: a reload forgets it, the waiting
status has no `you`); the host's name is `GameStatus.host`. Skipped for want of wire: the code,
puppet choice / Change puppet (the platform wears `castForGame` by join order, which the dealt
seats do not keep), Leave, remove a passenger, Change the terms, the Ticket's model / memory /
funded-by lines. The mockup's `pop=tag` and `passmode=change` have no counterpart.

## B. Conflicts with the rulings and the built code

| # | Conflict | Evidence | Verdict to rule on |
|---|---|---|---|
| B1 | **Waiting room orientation.** Brief 6 says recompose for portrait. Ruling 3 makes "everything inside a game room (`/games/[id]` …)" landscape but says "the lobby/rooms stay responsive"; the built code reads "lobby" as the *waiting* lobby: `GameClient.tsx:18` "The waiting lobby stays an ordinary responsive page", and `ux_journeys` D6 names `/games/[id]`·waiting "The lobby". The mock is a fixed 16:9 `cqw` stage with no portrait layout | `stage_architecture.md:15-17`; `M/waiting-room.html:104` | **Recommend: the platform is a stage scene, landscape only; amend ruling 3 to name the waiting state.** Keep the boarding pass (name + puppet) as a responsive page step *before* the scene, so an invite link opened upright still works. Skip brief 6's portrait recomposition |
| B2 | **Page or scene?** The mock's Depart "fades to the deal in the dining car"; HANDOFF l.75 says the boarding variant was built on the deal's bench (75) "for the rooms' waiting lobby"; beat_sheet §1 says the same; §8 already lists a `station` paint generator; HANDOFF l.218 keeps "the station cloth … for the rooms" | `src/stage/paint/` has no station yet; `ActPlate.tsx` already is the brass confirm plate | **Recommend: `src/stage/scenes/StationScene.tsx` + `paint/station.ts`, 1600×900 units, mounted by `GameClient` in the waiting state inside the same `OrientationGuard`**, so Depart → deal beat 0 is one stage box with no route change. It is compatible with beat_sheet §12's "deal on first connection" rule (the stream opens at `running` with only deal events in history, so the deal plays from beat 0). Guests see Depart on the 3 s waiting poll (`useGameStream.ts:68`) |
| B3 | **Tokens.** Inner pages define both vocabularies at `:root` (l.11–14): `--town`/`--amber` #e0a63a, `--text`/`--bone` #f1e8d6 (but `--bone` becomes #efe4cb in the two dark blocks), `--muted`/`--bone2` #a3947c, `--panel-2`/`--panel2`, `--paper-dk`/`--paperdk`, `--killer`/`--sk` #9d7cff. Against the theatre (`materials.ts` `vars()`): `--bone2` #cdbb93 ≠ #a3947c, `--bone3` #8d7a55 ≠ #7f735f; `--inkTown/--inkWolf/--inkSk` = our `--town-ink/--wolf-ink/--sk-ink`; `--aqua` = our `--sure`/`--film-ink`; `--brass` #c9a25e and `--red` #c8392b have no theatre token. Against `src/styles/tokens.css` (the live site): `--amber` #e0a33f ≠ #e0a63a, `--text` #e9dfd4 ≠ #f1e8d6, `--faction-villagers` verdigris #7d9e83 vs town amber, `--radius` 2px vs 12/20/28. The landing slate overrides `--ink` and `--sk` locally with faction colours (l.2997), the same names the stage uses for paper ink and the killer | | **Theatre wins on shared names.** One site token file: site-only roles keep landing names (`--bg --panel --panel-2 --line --text --muted --paper-dk --r-s/m/l --shadow`); shared materials take the theatre's names **and values** (`--town --wolf --sk --paper --ink --amber`); drop `--killer`, `--bone*`, `--panel2`, `--paperdk`, `--inkTown…`, `--aqua` from pages. Rename the slate's local vars. The old `tokens.css` palette goes when its 7 consumers go (`page.module.css`, `Lobby.module.css`, `ReplayCard.module.css`, `SeatChip.module.css`, `GameClient.module.css`, `TheaterClient.module.css`, `RoomsClient.tsx`) |
| B4 | **Fonts.** Mocks: Outfit 300–800 + IM Fell English (+ Patrick Hand on the landing) from Google CSS. Theatre: `stage/fonts.ts` Outfit 400/500/600/**700**, Fell, Patrick Hand via `next/font`, applied only by the `/games/[id]`, `/replays/[id]` and `/workbench` layouts. Site: `layout.tsx` loads **Silkscreen** as `--font-display`, which no mock uses; Mantine `theme/typography.ts` sets the sans | mock titles use weight 800 (`.ttl`, hero h1) | Hoist `stageFonts` to the root layout (add 800), drop Silkscreen. Same families, so there is no conflict beyond one weight |
| B5 | **Mantine.** The prompt assumed Mantine in the rooms pages. It is not: **no component imports `@mantine`**; only `layout.tsx` (`ColorSchemeScript`, `mantineHtmlProps`), `Providers.tsx` (`MantineProvider`, an unused `<Notifications/>`) and `src/theme/*` do. Rooms/play/lobby are CSS modules over `tokens.css` | `grep "@mantine" src` | Dropping Mantine loses only its global reset (`@mantine/core/styles.css`), the forced-dark provider and the theme; replace with a 20-line reset in the site CSS. `stage_architecture.md` §5 ("Mantine stays for the rooms, the landing and forms") needs a one-line amendment |
| B6 | **Sprites.** Inner mocks inline two 11-frame strips: `.ch` (round chip) and `.fg` (figure, fixed `aspect-ratio:360/480`), frame order **cat, hare, owl, badger…** (`.fg-cat 0%` …). Ours: per-character WebP `SPRITES.day[c].{base,talking,thinking,out,chip}`, base 430×600 / 372×600 / 413×600 (variable width, `BODY` crop fractions), chip 200×200, order **owl, hare, cat…** (`manifest.ts:157`). The landing's `DAYCAST` (l.2329) matches our manifest exactly (same sizes) | | Same characters, different crops for `.fg` (0.75 fixed vs 0.62–0.72 variable). Build with `ChipSprite` and `SPRITES.day[c].base` + `BODY`; never ship the strips. Waiting-room rasters (sky, canopy, fringe, posts, lamps, floor tile, cars, blinds: 10 data URIs) have **no masters** in `claude_artifacts/design/sprites/`; extract them once to WebP under `src/assets/sprites/station/` via `manifest.ts` (ruling 5), or ask the design chat for masters |
| B7 | **Puppet choice vs `castForGame`.** Ticket office (solo), boarding pass and rooms pips let a person *choose* a puppet. `castForGame(gameId)` derives all nine from a hash of the id "so … nothing has to be added to the wire" (`cast/castForGame.ts:1-5`, and the kit's own comment at `M/landing.html:1676`). Humans are dealt random seats at start, so a chosen puppet cannot survive the hash | | **Needs a ruling.** Either (a) keep the hash: remove choice (rooms pips show initials or plain chips), or (b) add `seat→character` to the frozen contract (`game_started`, `S/schemas/events.py:64`) plus `JoinGame.character`/`NewSoloGame.character`, with `castForGame` filling the unchosen seats and serving old games. (b) changes `events.py`, which "changes only by ruling" |
| B8 | **Landing mini replay is not ReplayTheatre.** The mock ships its own engine (`buildBeats` l.2551, `render` l.2665, `film` l.2751). The memory note says it should be "ReplayTheatre in a reduced frame"; `stage_architecture.md` §9 and beat_sheet §15 leave "which beats it plays" open. `ReplayTheatre` takes only `{ game }` (`ReplayTheatre.tsx:42`) and lives under `OrientationGuard` at route level; the landing is responsive, and the mock has a portrait `narrow` mode with the pane under the stage | | Build it as `ReplayTheatre` + new props (beat window for "featured", autoplay, `hud`, compact slot) inside the carriage frame. Treat the mock's engine as a spec for the featured cut only. Owner rules on portrait: a 16:9 box at 390 px is scale ≈0.24, below the legibility floor (§3) |
| B9 | **Model display names.** `GET /models` carries them (`ModelRow.label` ← `model_catalog.py` `display_name`), e.g. "Gemini 3.5 Flash-**L**ite" with a hyphen. Mocks hardcode "Gemini 3.5 Flash Lite" (landing l.2534, replays l.275), yet rooms rows (l.241) and the ticket-office select (l.430) show the raw id. `ReplayBase.model` is the id only; `ReplayCard.tsx:53` shows the raw id today | | Labels come from `getModels()` everywhere (server spelling wins); raw id as secondary mono text only where the mock shows both (the slate) |
| B10 | **Product name.** `layout.tsx:24` "Werewolf — agent sim"; routes "X — Werewolf"; workbench "Workbench · Werewolf Playhouse"; mocks: landing `<title>` "Werewolf — nine agents, one table", inner "X · Werewolf Playhouse", nav brand "Werewolf" everywhere; separator — vs · | | Owner picks (E2). Note the brand mark is the **wolf sigil's crescent** (same path as `Sigil.tsx` `wolf`) |
| B11 | **Lock semantics.** Mock: locked rooms stay listed and "only the code or your invite link lets people in" (ticket l.447, waiting l.336). Server: locked refuses **every** join, link included (`lobby.py:94` "room is locked — ask the host to unlock it") | | Either change the server (a locked room admits by code/link) or change the copy to "the host must unlock it". This decides whether "Use a code" can exist |
| B12 | **Memory default.** Ticket office pre-checks "On" (l.423). Server default `memory=False`; `PlayClient`/`NewRoomClient` default false; the demo toggle ships off by default | | Keep off by default; the copy describes, it must not promise benefit (the research result is negative) |
| B13 | **House purse missing.** No mock shows "free right now · n of N left" / "bring a key"; the key field reads as required. Built: `HouseDoorNote.tsx` (landing doors), `GameSetupFields.tsx` `needsKey`/`houseLine` hold the submit per row | | Keep the built logic under the new skin. It is a regression if dropped |
| B14 | **Key copy.** Ticket (party, l.437): "If you drop off mid-game, anyone aboard can put in theirs to carry on." Server: the key lives in session memory for the run; only a **server restart** loses it (`awaiting_key` → `fundGame`, `KeyNeededCard`). Leaving does not stop the game. Also `ByokField` has an opt-in "remember on this device" the mock drops | | Reword to the restart case; keep "remember" (it is why "never stored" says *on our side*) |
| B15 | **Turn clock.** 2:00–5:00 slider (party) and "Give myself a clock" (solo) assume a per-game setting; the server has one constant (120 s) and **no clocks in solo** | | Server work (`NewRoom`/`NewSoloGame.turn_seconds`, `SeatClocks` per game) or ship the mock with a fixed 2:00 label and no solo clock |
| B16 | **Global class soup.** Collisions already inside the mocks: `.mark` = brand badge (nav) **and** platform mark (`M/waiting-room.html:147`); `.ttl` = page title and ticket stub title; `.btn` inverted between landing and inner pages (B-brief 3) | | CSS modules per component (the theatre's convention); no global component classes |
| B17 | **"Strip `data-frame`"** is only half right: `body[data-frame=phone]` is the harness in `rooms.html:104-105` and `replays.html:104-105`, but the landing's `data-frame="carriage"` (l.1288–1356) is the **real** theatre frame | | Strip the harness; keep the carriage frame as a design |

## C. The brief, item by item

| # | Brief says | Do | Why |
|---|---|---|---|
| 1 | one tokens.css, keep landing names, map browns | **Differently** | Theatre names/values win where they overlap (B3); landing names only for site-only roles. Hardcoded browns: map to `--panel/--panel-2/--line` as said, but put stage-material browns (walnut `#3a2212`…) in `materials.ts`, not the site file |
| 2 | shared components copied verbatim | **As written, with a correction** | Verbatim among the four inner pages (identical `.hang/.flap/.slate` CSS hash); the landing's `.hang` is an `<a>` variant (l.60 vs rooms l.49). Build once as CSS-module components; `.ch/.fg` → `ChipSprite`/`SPRITES`, never the strips (B6) |
| 3 | unify on the landing's `.btn` API; keep `.brass` | **As written** | Confirmed inverted (`.btn` = amber in inner pages, ghost = `.btn.ghost`). `.brass` in the waiting room = `ActPlate.tsx` (the stage's existing brass plate) once it is a scene |
| 4 | one `<symbol>` sprite; add `i-lock-open`, `i-ticket` | **Half** | `sg-*` paths are byte-identical to `stage/instruments/Sigil.tsx`: reuse `Sigil`, don't add a second copy. `i-*` (13 icons, all 24-grid strokes) → one small `Icon` component; add the two |
| 5 | radii 28/20; display names; product name; GitHub icon | **As written, but names from the server** | `--r-*` are declared but barely used (landing 9 uses, rooms/ticket 0); labels from `ModelRow.label` (B9); product name is E2 |
| 6 | waiting room portrait recomposition | **Skip** | B1/B2: make it a landscape stage scene; portrait only for the boarding pass step. It has no site nav today, and should not get one |
| 7 | strip scaffolding | **As written, except** keep `data-frame="carriage"` (B17) and the `[data-when]` states become component props/state, not attributes |
| 8 | wire the data; fill placeholders | **As written, where the wire exists** | `GAMES`→`listReplays`/`getReplay`; `G`→`listReplays`; rows→`listRooms`. "[N] games" needs a server total; "Under way", codes, host, puppets, clock, watchers need server work (A3–A5) |

## D. Build order

| # | Step | Replaces / extends | Size | Who |
|---|---|---|---|---|
| 1 | **Site shell.** `app/(site)/layout.tsx` route group (nav + footer) for `/`, `/replays`, `/rooms`, `/play`; theatre routes stay outside. One site token file per B3; fonts hoisted (B4); Mantine removed (B5); leaf components as CSS modules: `Button`, `HangTag`, `Paper`, `Flapword`, `Icon`, `Slate` (reusing `Sigil`, `ChipSprite`) | `layout.tsx`, `Providers.tsx`, `src/theme/*`, `styles/tokens.css`, `app/page.module.css`, `components/Lobby.module.css` | M | Opus, after E1–E3 |
| 2 | **Archive + latest games.** `Slate` replaces `ReplayCard`; filter rail + cards/list over one `listReplays({limit: 500})` fetch, filtered client-side; "played on this device" via a new `seatToken.all()`; model labels from `getModels()` | `app/replays/*`, `components/ReplayCard.*`, `ReplayListClient.tsx`, `lib/storage.ts` | M | Opus (mechanical once E4 rules client vs server filtering) |
| 3 | **Ticket office.** One `TicketOffice` component, mounted by `/play` (solo) and `/rooms/new` (party), or one route with `?kind=`; keeps `GameSetupFields` `needsKey`/house logic and `ByokField`; role cards from `paint/role-kit.ts` + `card-text.ts`. Puppet/clock/watchers fields ship only after E5/E6 | `PlayClient.tsx`, `NewRoomClient.tsx`, `GameSetupFields.tsx` (reskin) | M (L with the server fields) | Opus for the form; the main loop for server DTOs |
| 4 | **Departures board.** Boarding tab over `listRooms()` (name, players/9, locked, full, created-ago); join inline as today. Under way tab, codes, host names, terms need server work | `RoomsClient.tsx` | M | Opus for Boarding; Under way waits on E7 |
| 5 | **The platform as a scene.** `stage/scenes/StationScene.tsx` + `paint/station.ts` + station WebPs in `manifest.ts`; ledge = `ActPlate`; Invite/Ticket as in-box panels; the boarding pass as a responsive page step; `GameClient` mounts it in the waiting state under `OrientationGuard`; Depart hands off to `DealScene` beat 0; a workbench entry `/workbench/station` | `components/LobbyCard.tsx` (retired), `GameClient.tsx`, `stage/scenes/index.ts`, `workbench/registry.ts` | L | Assets + paint port: Opus. Scene contract + hand-off: main loop, after E1/E5 |
| 6 | **Landing.** New `/` with the hero tags (room count from `listRooms`), `ReplayTheatre` in a mini mode in the carriage frame, under-the-table, role cards, latest slates (step 2), footer with real values | `app/page.tsx`, `page.module.css`, `HouseDoorNote.tsx` (kept), `stage/containers/ReplayTheatre.tsx` (new props) | L | Main loop for the `ReplayTheatre` props (E8); Opus for the sections |

Server track (parallel, main loop): `ReplayBase.ended_phase` + a total; `RoomSummary`/`GameStatus` `host`, `model`, `memory`; then, only if ruled, `turn_seconds`, `watchers_allowed`, codes, leave/kick/terms, characters (`events.py`).

## E. Questions only the owner can answer

1. **Is the waiting room a stage scene (landscape, `src/stage`, ruling 3 amended) or a responsive page?** (B1/B2.) Is the boarding pass allowed upright?
2. **Product name:** "Werewolf" or "Werewolf Playhouse", and the title separator (— or ·)?
3. **Drop Mantine entirely?** (It is only a provider and a reset today.) And retire the Silkscreen display face?
4. **Archive filters:** client-side over one fetch (how many archived games, and is that expected to pass ~500?), or server query params?
5. **Puppet choice:** keep `castForGame` (no choice), or put `seat→character` on the frozen wire? (B7.)
6. **Turn clock and watchers:** worth server work now (per-game `turn_seconds`, a solo clock, `watchers_allowed`), or ship fixed 2:00 / always watchable?
7. **Rooms scope:** build "Under way" (a listing of running games), 4-char codes, host names, leave/kick/change-terms? And lock semantics: code/link admits, or nobody? (B11.)
8. **Landing mini replay:** which beats does the featured cut play, and what does it do on an upright phone?
9. **Footer:** name as shown, and should "[N] games archived" be live? Where do "How it's built", Privacy and Contact point (no routes exist)?
10. **Memory on the ticket:** default off (as built) and neutral copy, agreed?

## F. Rulings (owner, 2026-09-26)

1. **Waiting room = a stage scene** (`StationScene`, landscape only, under `OrientationGuard`,
   Depart hands to deal beat 0). The boarding pass (name, later the puppet) is an upright-friendly
   page step. Brief item 6 dropped. Terminology: the **lobby** is the list of rooms (`/rooms`,
   responsive); the **waiting room** is inside a room before the start (landscape).
2. **Name: "Carriage Nine"** (tentative; the logo mark follows it, generated later).
   *Amended 2026-09-28 (owner):* kept, with the nine as the carriage's number, not the table's
   size (the table will not always seat nine). The mark is a brass escutcheon whose keyhole is
   a 9, the night and its moon seen through it, drawn by `scripts/brand-mark.mjs` at three
   levels of detail (≥48px, the nav's 24–40px, the favicon's 16–20px) and an X-ray state (the
   keyhole cut through to the film's cyan grid) that the nav shows while the brand is pointed
   at. It replaces the wolf's crescent on a paper disc.
   *Amended 2026-09-29 (owner):* the 9 is redrawn as a heavy geometric one (the family of the
   site's headings), and the moon sits where its counter would be. The mark is lit from the
   upper left: polished brass against a true night blue, a raised bevel with a seam in place
   of the rim ring, and, at 48px and up only, a bevelled edge on the cut (smaller, it read as a
   smudge). The hover is no longer the X-ray (its cyan fought the brass): a lamp comes on in
   the carriage and the keyhole glows amber (`mark-lamp*.svg`).
   *Amended again 2026-09-29 (owner):* **the name is now The Ninth Express** (no tagline; "the
   ninth passenger" was dropped). The mark is the train's headlamp, from the owner's bench
   (`claude_artifacts/design/logo/ninth-express-marks.html`, chosen over the coin and the
   number plate): an iron housing and a brass bezel round a lit lens, the keyhole 9 dark in
   the glass (the round bowl and round-ended tail) with the moon as its light. The number plate
   and its seat badges are left to the HUD (the stage's work). Hover turns the lamp up: the
   lens burns whiter, the moon's glow spreads, the housing warms.
3. **Mantine stays** and is the site chrome's component library (the owner's stack across projects):
   the site pages use Mantine components themed from the landing's tokens; the theatre stays CSS
   modules and never imports Mantine. The Silkscreen pixel face goes (the August art ruling is
   superseded by the playhouse; the mockups define the site's faces).
4. **Solo and room creation stay two pages** (`/play`, `/rooms/new`), both restyled from the
   ticket-office mockup; the server's create endpoints hold as they are.
5. **Puppet choice: later, as its own step** (join carries a character next to the name; the
   game-started event carries the seat→character map; `castForGame` is the fallback).
6. **Lock** = the server's meaning (a locked room admits nobody); the mockups' copy is corrected.
   **Memory** defaults off, neutral copy. **Replay filters** run in the browser over one fetch.
7. **Landing mini replay** = the same `ReplayTheatre`, `hud: 'none'`, a featured window, autoplay,
   in the carriage frame; on an upright phone a poster still with a play link. No second engine.
   **Amended 2026-09-27 (owner):** the carriage has the replay's controls, as the mockup's featured
   mode did (the E8 question never asked about them). At 700px and up, the strip's X-ray and
   Transcript, the side slot and the band sit on the stage, the band over the window only. On an
   upright phone they sit under the stage at reading size (`CarriageUnder`): a bar, a Transcript /
   X-ray switch, and one pane. The transcript takes its lines from `drawerLines`, so nothing arrives
   earlier than in the drawer; the X-ray pane is the stage's own `Film`, drawn by a small stage
   cropped to the film. The poster is gone. The marquee names the window ("Day 3 of game 9369A5C")
   and carries **Watch the whole game** → `/replays/{id}` (no whole-game mode on the landing). Its
   facts are small brass plates, not cream tiles; below 960px the date goes, and a phone shows only
   the first two (model, memory). The button is a ruled amber sign button, not the page's filled pill.
8. **Server track now:** `ended_phase` + a total on the replay list; the host's name on a room row.
   Everything else the mockups want from the wire is derived or skipped (codes, watchers, under-way
   list, leave/kick/terms, per-game clock).
   **Amended 2026-09-27 (owner):** leave and close are in. A guest's ledge has **Leave**
   (`POST /games/{id}/leave`: the place opens again); the host's has **Close room**, two presses
   (`POST /games/{id}/close`: the room's URL answers 410 with the reason); a room nobody departed
   within `ROOM_LIST_TTL_SECONDS` is closed by the sweeper. The host is the seat that boarded with
   the host key (no longer "whoever boarded first"), and cannot leave, only close. Kick and terms
   stay skipped.
9. **Footer:** name "Liu Haochen", GitHub `https://github.com/Haochen92/werewolf-agent-sim`; other
   links live in one `site.ts` config with TODOs the owner fills.
   **Amended 2026-09-27 (owner):** the footer is one row under one rule: the plain credit line
   ("Built by Liu Haochen · N games archived · 2026") at the left, the links (GitHub, for now) at
   the right; stacked on a phone. A brass maker's plate for the credit was tried and dropped. The landing ends on the
   mockup's closing block, cut down: "Built in the open, and still being built.", one sentence (the
   research line stays the hero's), and the API key line, checked against `game_session.py` (the key
   is session memory only, scrubbed from error reports, never in `RunConfig` or the archive). The
   latest games are four (two on a phone, where the slates stack), not six; "Take a seat" ends on
   ticket stubs rather than a second pair of hang tags.
