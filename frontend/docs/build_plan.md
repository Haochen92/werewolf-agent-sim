# Frontend build plan — `frontend/`

> Decision record + implementation plan, ruled 2026-08-20. Supersedes the stale
> `BUILD_BRIEF.md` (2026-07-17, lived in the abandoned `ww-frontend-app` worktree) — that brief
> assumed "build against mocks, backend staged last"; the backend has since been fully built and
> live-smoke-tested (SSE server, rooms, seat tokens, AFK delegation, replay archive, live-session
> durability with restart recovery; 947 tests green). The idea source remains [`design_log.md`](design_log.md); the wire contract lives in
> [`server_client_transport.md`](server_client_transport.md) + [`event_derivation.md`](event_derivation.md)
> and `server/schemas/events.py`.
>
> **Scope note: this document covers architecture, stack, and build phasing only. Visual / UX
> design lives in [`ux_baseline.md`](ux_baseline.md) (ruled 2026-08-20) — the v1 UX spec, the
> token-level aesthetic baseline (art-direction pick deliberately deferred), and the future
> parking lot. The two documents together are the complete implementation handoff. The
> theme-slice structure below is where the later styling pass plugs in without touching app
> code.**

---

## 1. Rulings (owner, 2026-08-20)

| # | Question | Ruling |
|---|---|---|
| 1 | Where the app lives | **`frontend/` in the main repo IS the app root** (re-ruled 2026-08-20, superseding the earlier `webapp/` pick); the design/decision docs moved to `frontend/docs/`. **No worktree.** ~~No new branch~~ → **re-ruled 2026-08-21: build on `feature-frontend-v1`** (cut from `feature-dimension-schema` at `563c7d7`, so it carries the §6 server tweaks). The original "no branch" call was about app *location*, not isolation; a branch costs nothing and buys the thing the build actually wants — the headless core (wire + reducer + tests + walking skeleton) lands as one commit that visual variants fork from. Commit hygiene stays folder-scoped. |
| 2 | Mantine major | **v8** (current major; dota2pred is on v7 but its patterns port unchanged; greenfield shouldn't inherit a dated major). All `@mantine/*` pinned to the same major. |
| 3 | Tailwind | **Dropped** from the old locked stack. Mantine props + CSS Modules + `postcss-preset-mantine` only — one styling system. |
| 4 | Data fetching | **TanStack Query only** (deviation from dota2pred's SWR-primary split-brain; our API is write-heavy — join/start/rejoin/turns — so mutations + invalidation are core). |
| 5 | Pre-scaffold server tweaks | **Approved**: (a) type `ReplayGame.events` as `list[DurableGameEvent]` so the event union reaches `/openapi.json` and TS codegen; (b) env-driven `Secure` flag on the seat cookie for HTTPS deploy. |
| 6 | Replay content bootstrap | **Serve cheap self-play games through the real server** to fill the archive (doubles as live soak). No backfill exporter for now. |
| 7 | Ghost-mode guesses | **localStorage-only v1** — no backend endpoint yet. |
| 8 | Testing | **Vitest for the event reducer only.** Plus Prettier (dota2pred's missing formatter shows as indentation drift). |

## 2. Stack

Pattern donor: `~/projects/dota2pred/frontend` (studied 2026-08-20). Adopt its architecture;
fix its five known warts (dual fetch libs, base-URL copy-pasted ×8, no formatter, mixed
`.js`/`.tsx`, zero tests).

### Dependencies

| Package | Role | Note |
|---|---|---|
| `next` (15.x, App Router) | framework | `output: 'standalone'`, `optimizePackageImports` for Mantine/icons |
| `react` / `react-dom` 19 | | |
| `@mantine/core` `@mantine/hooks` `@mantine/notifications` (v8, same major) | UI | notifications = error toasts (turn rejected, reconnect, game error) |
| `@tanstack/react-query` v5 | ALL server reads + mutations | client created in a `useState` initializer inside the provider (App Router pattern) |
| `zustand` v5 | the ONE client-side store: the live game session (see §4) | per-slice selectors; NOT for server request/response data |
| `@tabler/icons-react` | icons | |
| `typescript` (strict), `openapi-typescript`, `prettier`, `vitest`, `postcss` + `postcss-preset-mantine` + `postcss-simple-vars` | dev | |

### Explicitly skipped (add only when a need materializes)

- **`@mantine/form`** — our forms are trivial (message textarea, target radio group, name field,
  API key + model select); controlled `useState` suffices. (Also the source of dota2pred's
  cross-major version mismatch.)
- **`@mantine/charts` / recharts** — no charts in P0–P4. The vote matrix is a grid, not a chart.
  Eval dashboard is a "later" feature.
- **`@mantine/dates` / dayjs / date-fns** — no date pickers; timestamp formatting = native
  `Intl.DateTimeFormat`; AFK countdown = a small `useCountdown` hook off `deadline`.
- **zod** — server-side pydantic already validates everything; generated types suffice (same
  call dota2pred made).
- **SWR** — replaced by TanStack Query (ruling 4).
- **Ladle / Storybook, Playwright** — dota2pred barely used them; revisit at the styling pass.
- **WebSocket anything** — not a dota2pred carry-over (dota2pred is SSE-only too); listed
  because `design_log.md` §8 floated "WebSocket is a fine later swap." Pinning here: SSE + POST
  is the shipped wire contract, and the traffic pattern (server→client dominates; client acts
  only on its turn) never needs a socket. Don't add one.

## 3. Repo layout

```
frontend/
├── docs/                                   # design + decision records (this file, ux_baseline.md,
│                                           #  design_log.md, the wire-contract docs) — NOT app code
├── Dockerfile  next.config.mjs  postcss.config.cjs  tsconfig.json  vitest.config.ts
├── .env.local.dev (→ cp to .env.local)  .env.production
├── public/
│   └── og/                                 # OG share cards ONLY (need stable URLs; P4) — nothing else
└── src/
    ├── app/
    │   ├── layout.tsx  page.tsx            # landing: replays · quick play · create room
    │   ├── Providers.tsx                   # QueryProvider > MantineProvider > AppShell
    │   ├── replays/{page.tsx, _components/}
    │   ├── replays/[gameId]/{page.tsx, _components/}   # replay theater
    │   ├── play/{page.tsx, _components/}   # solo quick-play door (role + model + BYOK)
    │   ├── rooms/{page.tsx, _components/}  # public room browser (GET /rooms, slice 7)
    │   ├── rooms/new/{page.tsx, _components/}
    │   └── games/[gameId]/{page.tsx, _components/}     # ONE route, three states (§5)
    ├── assets/                             # imported art: portraits/ glyphs/ backgrounds/
    │   └── manifest.ts                     # the ONE import site → typed handles (no paths in components)
    ├── components/                         # cross-route: seat chip, replay card, lobby cards, forms
    ├── stage/                              # the theatre, replay and live (stage_architecture.md §8)
    ├── game/                               # THE core: reducer + store (pure TS, vitest home)
    │   ├── foldEvents.ts                   # (GameView, DurableGameEvent) → GameView
    │   ├── types.ts                        # GameView + derived shapes (types/domain material)
    │   └── store.ts                        # zustand session store (§4)
    ├── hooks/                              # useGameStream (+ catch-up-boundary), useCountdown
    ├── lib/
    │   ├── config.ts                       # API_BASE_URL — the ONE definition
    │   ├── request.ts                      # request<T>(): error discrimination (§6)
    │   └── queryKeys.ts                    # key factory (dota2pred lacked one, paid for it)
    ├── theme/                              # 4-slice mergeThemeOverrides (colors/typography/
    │   └── components/...                  #  per-component overrides + colocated CSS modules)
    ├── types/
    │   ├── contracts/{api.ts, index.ts}    # generated ← /openapi.json + hand façade
    │   └── domain/                         # hand-written view-model types
    └── styles/                             # shared design-layer CSS module (styling pass)
```

Conventions (dota2pred, kept): route-private components in `_components/`; server `page.tsx` =
metadata + `<Suspense fallback={<Skeleton/>}>` + `<XClient/>`; container/presenter split
(`XClient` fetches → typed props → pure `XView`); skeletons are first-class; `kebab-case.ts`
non-components, `PascalCase.tsx` components; responsive via `visibleFrom`/`hiddenFrom`; Next 15
`error.tsx` per route group (not a hand-rolled ErrorBoundary).

Type codegen: `"generate-api-types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/contracts/api.ts"`
— committed output; the façade `contracts/index.ts` renames generated types so app code never
imports `api.ts` directly (regeneration can't ripple).

**Image assets (ruled 2026-08-21; direction = `ux_baseline.md` §1).** Art ships via static
imports + `next/image` — content-hashed URLs (regenerated art can never get stuck behind a
browser's cached copy), inferred dimensions (no layout shift), automatic optimization. NOT
`public/`: it serves verbatim with none of that; `public/og/` is the sole exception (share
cards need stable URLs for `generateMetadata`; favicons use Next's `app/icon.png` file
convention, not `public/`). `src/assets/manifest.ts` is the only file that imports image
files; it exports typed handles (`PORTRAITS: StaticImageData[]`, `KILL_GLYPHS:
Record<AttackerType, …>`) so components never hold path strings — `SeatChip` picks
`PORTRAITS[hash(seat) % len]` and falls back to the initials `Avatar` while `portraits/` is
empty, so the build never blocks on art and an art swap is files + manifest, zero component
edits. Generated assets land as WebP at ~2× display size (portraits are chip/card scale, so
~512px square — never raw multi-MB gen output), one palette, one canvas ratio.

### Rendering model (Next.js specifics — ruled 2026-08-20)

- **`/games/[gameId]` and `/replays/[gameId]` are dynamic route segments** (App Router `[param]`
  folders), rendered on demand — nothing is statically generated at build time except the truly
  static shells (landing, `/play`, `/rooms/new` forms).
- **Game surfaces are client-rendered.** The `page.tsx` files stay server components (metadata +
  Suspense + skeleton, the dota2pred pattern), but everything below the boundary is
  `'use client'`: the live game depends on `EventSource` (browser-only API) and the HttpOnly
  seat cookie, and the replay theater is interaction-bound (scrubber). Server-side data fetching
  would add complexity for zero paint benefit — the skeleton IS the first paint.
- **No parallel/intercepting routes** (dota2pred's `@modal` slot): no modal-over-route use case
  yet — the X-ray is an in-page pane, not an overlay route. Revisit only if the UX pass creates
  one.
- **No PPR / streaming SSR**: the app is interaction-bound, not TTFB-bound.
- **The one server-rendering win, slotted P4**: `generateMetadata` on `/replays/[gameId]` doing
  a server-side fetch of the replay summary (public GET, no cookie needed) to emit OG share-card
  tags ("Wolves won in 5 days · 9 seats") so pasted replay links unfurl. Pure additive polish;
  nothing else moves server-side for it.

## 4. State model — the load-bearing design decision

Three state planes, three tools, no overlap:

1. **Server request/response data** (replay list, replay detail, models menu, game status
   snapshots) → **TanStack Query**, keys from `lib/queryKeys.ts`. Models menu: `staleTime:
   Infinity`. GameStatus: polled (§5) — it is also the dead-game detector.
2. **The live game session** → **one Zustand store per open game**: append-only durable event
   log + the folded `GameView` + connection state + pending `input_request` + ephemeral pacing
   (monotonic-max, never persisted). Fed exclusively by the SSE hook. Zustand (not Context +
   useReducer) because every SSE event updates the store while dozens of components subscribe —
   per-slice selectors prevent the re-render storm, and the store is trivially testable without
   React.
3. **URL search params** as the single source of truth for browse/scrub state (`useFilterState`
   pattern): replay-list pagination, replay-theater scrubber position (`?day=3&seq=214`) —
   shareable deep links ("play of the game" wants this later).

**`foldEvents` is the heart of the app**: one pure function folding `DurableGameEvent[]` into
`GameView`. Replay = fetch `/replays/{id}.events` → fold once. Live = SSE → fold incrementally.
Post-game R7 flush = the same fold absorbing the withheld observer backlog. The play UI is the
replay UI + input affordances — one reducer serves all three, which is exactly what the backend
was shaped for (`ReplayGame.events` is the same durable log the SSE stream carries).

`GameView` sketch (refine while implementing):

```ts
{
  seats: string[]; castRoleCounts: Record<string, number>;   // game_started
  day: number; phase: 'day' | 'voting' | 'night';
  winner: Winner | null;                                      // game_over
  roster: { alive: string[]; dead: DeathRecord[] };           // roster_update, player deaths
  transcript: Record<day, TranscriptEntry[]>;                 // speech·gm_message·turn_started
                                                              //  (+pass_marker in x-ray view)
  votes: Record<day, { ballots: VoteCast[]; result: LynchResult | null }>;
  nights: Record<day, { deaths: NightDeath[]; save: NightSave | null }>;
  me: { seat: string | null; role: RoleCard | null;           // role_assigned (pack, bullets)
        pending: InputRequest | null;                         // + deadline countdown source
        privateResults: PrivateEvent[] };                     // investigation·vigilante·bullets
  wolfChannel: WolfEntry[];                                   // faction tier (or post-game)
  xray: Record<player, { role?: string; strategy: string[];   // observer tier: roles_assigned,
        firingReasons: FiringReason[]; addressed: ...;        //  strategy_update, firing_reason,
        nightActions: NightAction[]; gatedPasses: ... }>;     //  addressed_targets, night_action,
  xrayUnlocked: boolean;                                      //  pass_marker(gated_candidate)
}
```

Tier filtering is server-side — the client folds whatever arrives and renders what exists;
`xrayUnlocked` flips on `game_over`. Never gate client-side on information the server withheld
(there is nothing to gate — it never arrives pre-unlock). `day_summary_structured` never fires
(schema-only, provisional) — do not build on it.

## 5. Wire integration

**Base URL / env**: `NEXT_PUBLIC_API_BASE_URL ?? '/api'` defined once in `lib/config.ts`.
Dev: `http://localhost:8000` (server's CORS default already allows `localhost:3000`).
Prod: same-origin `/api` behind Caddy — **required, not optional**: the seat cookie is
`HttpOnly; SameSite=Lax; Path=/games/{id}` with no `domain`, so the frontend must be same-site
with the API. Every fetch: `credentials: 'include'`; EventSource: `withCredentials: true`.

**`request<T>()` (`lib/request.ts`)** — one helper discriminating the two error `detail` shapes
(FastAPI string vs 422 validation array) into a typed `ApiError { status, message }`, plus the
status codes that drive flow: `403 unknown seat token` → run the rejoin flow; `409` → state
conflict (already started / not started / no pending request — double-submit bounce); `422` →
human-readable contract message, render verbatim in the turn form; `503` on `/replays` → archive
not configured.

**`useGameStream(gameId)`** — dota2pred's snapshot-then-stream shape, adapted:
1. `GET /games/{id}` → seed status (`last_seq`, `state`, `you`, `pending_seats`, `deadlines`).
2. `EventSource(/games/{id}/events?last_seq=N)`. Browser auto-reconnect sends `Last-Event-ID`
   (server honors it over the fossil query cursor). Two event names: `game` (durable, fold it)
   and `pacing` (ephemeral snapshot, monotonic-max into the store).
3. `onerror`: ignore when `document.hidden`; log on `CONNECTING`; close + surface otherwise.
4. **Status poll fallback** (~10–15 s, TanStack `refetchInterval` while state === 'running'):
   a dead game task emits NO stream signal (heartbeats keep flowing, `state` stays `"running"`,
   only `GameStatus.error` fills) — the poll is the only detector. It also refreshes
   `pending_seats`/`deadlines` for lobby-ish UI.

**Seat identity flow**: solo create / room join returns the token in the body once → stash in
`localStorage[seat_{gameId}]` as the cookie's backup; cookie loss (`403` anywhere) → `POST
/rejoin {token}` → cookie restored. Room creator additionally stashes `host_key` (returned only
by `POST /rooms`). Mid-game refresh survives via this pair.

**Client-side persistence inventory** (the complete list — all device-local, the server
never reads any of it; one `lib/storage.ts` module owns the key names):

| Key | Content | Written | Cleared |
|---|---|---|---|
| `seat_{gameId}` | seat-token backup (cookie's second copy) | join / solo create / rejoin | lazily, when status says `finished` or the game 404s |
| `host_{gameId}` | room creator's host_key | `POST /rooms` | after `/start` succeeds (its only use) |
| `byok_key` | remembered API key — **opt-in only** | "remember on this device" checked | the "clear saved key" button; also never written unless opted in |
| `ghost_{gameId}` | ghost-mode guesses keyed by phase | guess widget (ruling 7) | never (it's the user's history) |
| `notes_{gameId}` | the seated player's file on each seat: the claim, the guess, each night's claim, each day's lines | the case file's player files (2026-10-18; the rail's note editor before) | never (it's the user's own record) |
| `music` | `on` or `off`, the viewer's last choice of music; absent = never chosen (the game plays it, the guide does not) | the sound button (the stage's strip, the guide) | never |
| `depart_{gameId}` (**sessionStorage**) | a game for one's departure: the ticket's puppet and when it was bought | the ticket office's solo create | once its train has left (the curtain falls); not read after 60 s; with the tab |
| `told_{gameId}_{seat}` (**sessionStorage**) | the seat has been told of its own death that came in while the page was away, or watched it live | the live theatre's "While you were away" notice, dismissed; a live `night_result`/`lynch_result` naming the seat (2026-10-11) | with the tab |

BYOK-remember explicitly needs ZERO additional server support: the key's only wire appearance
is the create-request body; the server retains it only in the live game object's memory, while
remember/mask/clear are local operations (ruled 2026-08-20). Restart recovery by resubmitting a
key is a recorded future design, not part of v1.

**One route, three states**: `/games/[gameId]` renders by `GameStatus.state` — `waiting` →
lobby (roster poll, share link, start button iff `host_key` held), `running` → live table,
`finished` → post-game X-ray. This mirrors the server's registry swap (room URL = game URL);
the client never re-routes across the transition.

**Turn submission**: `POST /games/{gameId}/turns` body by `action_kind`: `discuss` → `{message}` or
`{pass_turn: true}`; `wolf_discuss` → `{message}`; every vote/night kind → `{target}` from
`candidates`; `{delegate: true}` legal everywhere (the AFK button). 422 message renders as-is;
409 = someone (or the AFK timer) already answered — clear the form and re-sync via status.

**Drafting a line from notes** (server landed 2026-09-17, UI pending — spec in ux_journeys D25):
`POST /games/{gameId}/draft` `{notes}` → `{draft, drafts_left, deadline}` for `discuss` /
`wolf_discuss` turns only. A read-only helper: the draft goes into the textarea and is sent
through `/turns` like any typed line. Three drafts per turn, server-enforced; the wait is
credited back to the seat's clock and the returned `deadline` is the new countdown. 409 =
no turn / no drafts left; 503 = model failure, "type it instead".

## 6. Server tweaks shipping with P0 (ruling 5) — ⭐BOTH LANDED 2026-08-21

1. ✅ `server/schemas/replays.py`: `ReplayGame.events: list[DurableGameEvent]` (the table's JSONB
   column stays `list[dict]`; only the wire model is typed). Verified: the 27-member
   discriminated union now renders in `/openapi.json` as `oneOf` refs — the frontend TS
   event types generate from it. Side effect (deliberate): stored rows re-validate on the
   way out, so archive drift 500s loudly instead of shipping mystery dicts.
2. ✅ `server/config.py` + `app.py`: `SEAT_COOKIE_SECURE` env knob (default false for
   plain-HTTP dev; the TLS deploy sets it). `_set_seat_cookie` is the single set-site, so
   one line covers all three doors (solo create / join / rejoin).

Three regression tests added (Secure-flag knob · typed-event parsing incl. drift rejection ·
union-reaches-OpenAPI member count). 954 green.

## 7. Phases (each ends deployable)

**P0 — scaffold + contracts.** The two server tweaks · Next 15 + Mantine 8 scaffold · theme
slices skeleton · `lib/{config,request,queryKeys}` · codegen wired · Providers/AppShell ·
Prettier + Vitest config · Dockerfile (4-stage, standalone, `NEXT_PUBLIC_*` build arg) ·
**archive seeding**: ✅ SEEDED 2026-08-21 at $0 — the recorded fixture game
(`chunk_catalogue.jsonl`, a real served flash-lite game) replayed through
`GameSession(FakeGraph)` with the live DSN; row `seed-chunk-catalogue` (wolves, 5 days,
593 events) verified through both `/replays` endpoints incl. the typed-union parse
(one-shot script, deleted after per ruling). More rows arrive organically: every cleanly
finished served game auto-archives. Optionally serve a few cheap real games later for
browse variety (ruling 6).
*Done when*: `/replays` renders real rows from the archive in the browser.

**P1 — event reducer + replay theater (the portfolio centerpiece).** `foldEvents` +
`GameView` + Vitest suite (fixtures = real archived-game JSON dumped from P0's seeding; the
server's `notebooks/fixtures/chunk_catalogue.jsonl` lineage stays server-side) · `/replays`
browser (pagination via `useFilterState`) · `/replays/[gameId]` theater: day/phase scrubber
(URL-addressed), table + transcript, vote reveal + lynch results, night results ·
**X-ray toggle**: roles, night actions, wolf channel, firing reasons (reactive/proactive +
owes), novelty-gated passes w/ `gated_candidate` (the vetoed speech!), strategy timeline, vote
matrix (derived), dramatic-irony affordances (spectator knows roles) · ghost-mode v1: guess
widget at day boundaries, localStorage-keyed `(game_id, phase)` (ruling 7).
*Done when*: a stranger can replay a real game end-to-end and flip the X-ray.

**P2 — live game + solo play.** `useGameStream` + game store feeding the SAME reducer/UI ·
`/play` solo door (role picker from cast, model menu from `GET /models`, optional BYOK
key). **BYOK key handling (ruled 2026-08-20)**: the server holds a key only in the live
game object's process memory and never persists it (BYOK games currently die on restart for
exactly this reason), so remembering is purely client-side. One shared `ByokField` component
(used by `/play` and `/rooms/new`): key
input + an OPT-IN "remember on this device" checkbox → `localStorage`; when a saved key
loads it renders masked with a "clear saved key" button right there in the field. Off
by default; the key travels only in the create-request body; say all of this in the UI. · turn forms per `action_kind` + AFK
`deadline` countdown + delegate button · pacing progress rendering · rejoin flow + 403/409
handling · post-game: the R7 unlock re-fold ("the SK was WHO?") on the live route.
*Done when*: a solo human plays a full game in the browser, survives a mid-game refresh, and
gets the X-ray reveal at game over.

**P3 — rooms.** `/rooms` public browser (GET /rooms: name, roster, locked, created-ago;
TTL-filtered server-side — slice 7, 2026-08-20) · `/rooms/new` (create + optional room
name → host_key stash → share link) · lobby state of `/games/[id]` (roster poll, join
form, start button, spectate link; host additionally sees the lock toggle → `POST
/games/{id}/lock`; locked rooms render joinless, not hidden) · multi-seat pending
indicators (`pending_seats`, per-seat deadlines). Kick-player deliberately deferred
(lock covers pre-start griefing; AFK delegate absorbs post-start deserters).
*Done when*: two browsers play one game found via the public browser OR a shared link.

### Deploy notes (as-built, 2026-08-21 — wolf.liuhaochen.com)

Three things the deploy surfaced that no amount of local testing would have:

1. **Cloudflare buffers SSE unless told not to.** The origin already sent
   `cache-control: no-cache`, `x-accel-buffering: no` and `content-type: text/event-stream`,
   and Caddy had `flush_interval -1` — verified present in its *running* config. Bypassing
   Cloudflare (`--resolve` straight to the origin) the first frame landed in ~20 ms; through
   Cloudflare not even the response headers arrived within 25 s. The fix is
   `header_down Cache-Control "no-cache, no-transform"` on the `/api` block: `no-transform`
   is the documented way to tell Cloudflare to leave a response alone, and transforming is
   what its buffering hangs off. After it, first frame ≈ 0.02 s and a full game's ~400
   events stream live. **Any future subdomain serving SSE needs this too.**
2. **The server cannot start without Google credentials, even for replay-only.** The
   engine's embeddings factory initialises eagerly at import. ADC is mounted read-only.
3. **`memory_stores/` must be mounted.** A served game runs with `dump_enabled: false`, but
   the engine still SEEDS retrieval from `memory_stores/v6_1` at game creation, so a missing
   store is a 500 on `POST /games`. It is 37 MB and not in git, hence a mount, not a COPY.

Caddy lives in `~/projects/caddy` (its own compose, owns `shared-caddy-network`, holds the
Cloudflare origin certs) and fronts six other domains — validate before every reload.

**Deploy record.** 2026-08-21 first deploy · 2026-08-24 rebuild at `8efbc32` · 2026-09-10
server-only rebuild · **2026-09-15 both containers rebuilt at `db6628c`** (branch
`feature-frontend-v1`, pushed): the site now matches the branch, so the D1–D24 ruling pass
runs against current code. Rollback = the `:prev` image tags left on the host. Smoke: health,
model menu with `needs_key`, replay list carrying `model`, one house-funded AI game
streaming, the replay page chunk carrying the new player. Not set: `ADMIN_TOKEN` (the house
runs on process defaults; set it before the demo URL goes into applications) and the
Langfuse keys (production has never traced; the server logs the disabled-client warning at boot).
· **2026-09-17 both containers rebuilt at `223fc9b`** (the AI-memory switch + the three X-ray
events; built from a clean detached worktree so uncommitted work stayed out). Order that
mattered: `alembic upgrade head` (0006, `games.memory`) ran first, from inside the NEW server
image on the `werewolf` network — the host cannot resolve the DSN's `ww-postgres` name, and
the old image lacks the migration file. Then `.env.production` gained
`WW_MEMORY_STORE_DIR=/app/memory_stores/demo_snapshots/demo_gen1` (absolute: the server's cwd
is `/app`; the snapshot's `indexed_cache.pkl` was built on the host first, the mount is ro).
Pre-flight in the slim image before the switch: the memory-on import closure resolves and the
snapshot loads from cache with no embedding call (the Dockerfile's "memory back on" warning did
not bite — nothing on the retrieval path imports the filtered ML stack). Smoke: as before, plus
the OpenAPI carries `memory` on both doors and the three event types, and one house-funded
memory-on game (`9369a5c1`, wolves, 407 events: 53 `memory_consulted`, 52 `player_reads`, one
`memory_extracted` with 51 observations; the store loaded from cache, 723 vectors; the observer
backlog flushed over the public stream at game over). Same day, server-only rebuild: served
games retrieve **strategy points only** (`run_config.py`, owner's ruling — the town half of the
store never had observations, so both factions now get the same kind of memory). That one change
is applied on top of `223fc9b` in the image; commit pending (landed later in `c8a41e6`).
· **2026-09-28 both containers rebuilt at `447d8d4`** (the Playhouse redesign: the stage and its
scenes, the five site pages, the waiting room, the painted set and the atmosphere pass; built with
`docker build` from a clean detached worktree, then `compose up -d --no-build`). No migration step:
the shared `ww-postgres` was already at `0007` (applied 2026-09-26 for the local server; the old
image ran on it unharmed, the migration only adds a column). Rollback = the `:prev` tags (the
2026-09-17 images). Smoke: every site route and `/api` health, replays (with `X-Total-Count`),
rooms, models; a live replay rendered in headless Chromium loading the painted window, textures
and lantern.
· **2026-10-01, later: frontend only, `946c898` → `314b7cc` → `d6a19fe` → `a40f011`** (the GPU
probe; no SVG mask on the stage; no CSS mask either; the pace probe), each a frontend image
built from a detached worktree and `compose up -d --no-build wolf-frontend`; the server stayed at
`a651988`. The iPhone Safari crash on every stage page (build log §8.1) ended at `d6a19fe`; the
pace probe went up alone so the phone's floor could be read before the scene split (`196ebee`,
build log §8.3) went up after it; then `200ffed` (the split, the history-API steps), `8f29e70`
(the `noclip` probe word), `49c58c9` (the baked backdrop for the day and the morning), `3a5aa83`
(the phone's cut and the probe's loop range) and, on 2026-10-02, `7fadcd4` (every car scene on
the backdrop, the camera off its layer on phones, the tappable transport band) and `7f9cadf`
(safe areas, no pinch-zoom, no pull-to-refresh on the theatre pages), `8b71e4b` (the morning
roll after the chips, the drawer's dawn line held until it) `f33c89a` (the jar's tip and the
shutter's slide on HTML boxes, the Home Screen manifest and the iPhone's line for it) ,
`86955eb` (on a phone the camera cuts and the figures cast no filtered shadow) `d924ea0`
(on a phone nothing animates at rest: the night room's felt row, the wing's glows, the
station's snow) and `9cfe8d4` (the phone rule as a gate and its sweep fixed in one batch: the
kit's idle life, the lift's layer, the train, the ledger, one phone flag; the wolf card) and `ddacb4e`
(a fast second tap on a control is the control's, not a double-tap zoom) and `a9a066c` (the
same for a tap anywhere in the theatre: the viewport's no-zoom flags, which iOS honours for the
double tap, and the rule on every element) and `fbaef8c` (the backdrop belongs to the Stage,
kept across beats and scenes; every stage picture decodes synchronously) and `a3d6404` (the
phone's frame time, one batch: the car's set under one host and kept from scene to scene, the
vote, the lynch, the lobby and the night rooms playing by their props; moves stepped at 24 fps
on a phone; the light's screened sheets boxed, its drawings remembered; the grade's grain off
and a room's choice cut on a phone; 55 phone-size picture copies; the next speaker decoded a
turn ahead; the gate's remount check — build log §8.9: the vote's raster 67 s → 23 s over its
41 steps) and `a07067e` (the box, not the figure: every mover's box cut to its load, the ending
held still on a phone, the epilogue's sheet with a close, the live night rooms kept across beats,
the live countdown ticking in its own leaf, the live suite's waits sized to their streams — build
log §8.10; rollback = `:prev` = `a3d6404`), each frontend only.
· **2026-10-01 both containers rebuilt at `a651988`** (branch pushed first; built with
`docker build` from a clean detached worktree, then `compose up -d --no-build`). Server: the
request budget and stall rescue (30 s, two attempts, two stalls → the rescue model for five
minutes), the 700-character line cap and the 20 s draft-credit cap, the draft endpoint. Frontend:
the live pass — the morning roll, the once-only beats, the card in every scene, the known-role
bands, the role-guess listbox, the drawer's foot, the leave door, the loading platform, the
composer and the three-plaque dock, reading-pace holds with no fast backlog, the deal after a
departure, Reveal and File on the stage's clock, the notebook across beats, the curtain's wait
for the filed replay. No migration (the DB was at 0007). Rollback = the `:prev` tags (the
2026-09-28 images). Smoke: `/api` health, models, replays with `X-Total-Count` 11, the five site
routes and a replay page all 200; headless Chromium loaded a replay to `deal.table-seated` with
the Reveal switch and no page errors.
· **2026-10-03 both containers rebuilt at `9ae5056`** (built with `docker build` from a clean
detached worktree, then `compose up -d --no-build`; branch not pushed). Server: the
discussion-evidence prompt pass, switched on by `WW_DISCUSSION_PROMPT=v2` added to
`.env.production` (evidence/game_play_enhancement/discussion_evidence.md), and the human line cap
700 → 500. Frontend: the composer's cap 700 → 500. Pre-flight in the new server image with the
production env: the switch reads on, the rules carry the turn-order line, the wolf has the
claiming option, the cap is 500, the summary uses its v2 format. No migration. Rollback = the
`:prev` tags (server `a651988`, frontend `a07067e`); to keep the new images but the old prompts,
drop the env line and recreate the server. Smoke: `/api` health, models, replays, `/`, `/play`,
`/rooms`, `/replays` all 200.
· **2026-10-04 both containers rebuilt at `60c7cc0b`** (branch pushed first; built with
`docker build` from a clean detached worktree, then `compose up -d --no-build`). Server: the
information-fidelity pass (private night records, the game master's record shown apart from
claims), day summary v4 with the code-checked claim ledger, memory instructions only with
memories, and thinking per game model (3.5 flash-lite medium, 3.1 flash-lite low; rescues get
their own model's level), all in evidence/game_play_enhancement/discussion_evidence.md §6.4–6.7;
plus the cast record and the four new puppets. Frontend: the cast picker and new puppets, and
the v4 summary in the X-ray brief and the drawer. No migration step: the shared `ww-postgres` was
already at `0009` (applied for the local server). The images running before this deploy, 16
hours old and newer than the `9ae5056` tags, are kept as `:prev`. Pre-flight in the new server
image: the thinking levels and the rescue table resolve. Smoke: `/api` health, models,
replays, characters, `/`, `/play`, `/rooms`, `/replays` and an old replay page all 200.
· **2026-10-04 both containers rebuilt at `2d8bab5e`** (branch pushed first; clean detached
worktree, `docker build`, `compose up -d --no-build`). Server: day summary v4.1 (a plan for
tonight is recorded apart from actions already taken, with the player's reason when they differ;
a vague result is "not stated"; accusation fields at most 30 words), the claim ledger's same-night
double claims and plans, `GET /games/{id}/ledger`, and `day_summary_structured` made public; plus
the per-game usage record (`games.usage`), dated price table, calling modes per model and the
model menu's mean game cost. Frontend: the File's Record tab (opens without Reveal), the
transcript's one-line pointer to it, and the replay slate's cost line and grouped model menu.
Migration `0010` was already applied to the shared `ww-postgres` (nullable column, so the old
server ran fine on it). The `60c7cc0b` images are kept as `:prev`. Smoke: `/api` health, models,
replays, characters, `/`, `/play`, `/rooms`, `/replays`, an old replay page and the ledger
endpoint (game 140610ad: mornings 2 and 3) all 200; the Record tab renders the real ledger.
· **2026-10-04 server hotfix at `ae64e8ed`** (server image only). The private night record
(`NightActionRecord`, in state since the fidelity pass, deployed at `60c7cc0b`) was missing from the
checkpoint serializer's allowlist, so a human turn after a night resumed it as a plain dict and the
game died ("'dict' object has no attribute 'day'"; game 6ad64e96). Games whose human died on night 1
never resumed after a night, which is why the earlier game did not hit it. A new test walks every
graph state's models against the allowlist. `:prev` for the server is now `2d8bab5e`.
· **2026-10-04 server at `5441a564`** (server image only; prompt change = new epoch). The rules
now say day 1 has no vote, and day 1's moderator line reads "There is no vote on day 1, so no one
voted and no one is eliminated" instead of a "vote result" with no votes: agents in game 48e56d44
cited a day-1 abstention that never happened. `:prev` for the server is now `ae64e8ed`.
· **2026-10-04 server at `1964f993`** (server image only; branch pushed first; clean detached
worktree). Two player-key rows join the model menu after admission and the hallucination bench:
GPT-6 Luna (medium reasoning, json_schema output; 6% bad bench samples against 3.5 flash-lite
medium's 9%) and GLM-5.3 Flash (no thinking, json_mode; 32%, a cheap option). Shipped with the
fix they depend on: OpenAI, OpenRouter, xAI and NVIDIA models had ignored a player's own key and
used the server's, so a player's game would have billed the server and any key passed the check
(`8cd83ba7`; never exploitable before, since no such row was on the menu). No migration. Pre-flight
in the new image: both rows, their calling modes, thinking levels and prices resolve, and a
player's OpenRouter key reaches the client. Smoke: `/api` health, models (both rows, `needs_key`
true), replays, characters, `/`, `/play`, `/rooms`, `/replays` and an old replay page all 200; the
replay API carries `cost_usd` 0.5151 and `avg_call_seconds` 5.13 for game 48e56d44. `:prev` for
the server is now `5441a564`.
· **2026-10-11 both containers rebuilt at `74d8206b`** (branch pushed first; `docker build` from a clean detached worktree, then `compose up -d --no-build`; `:prev` = the 2026-10-04 images, rollback). The ten-seat cast: the Phase 3 engine and its balance and hallucination fixes (72 commits since the last deploy), the frontend pass (`docs/ten_seat_pass.md`), the night bar's total as the living seats, the workbench on the ten-seat game, the backdrop density and preview lifecycle. No migration step: the shared `ww-postgres` was already at `0010`. Memory stays off (the ticket's switch disabled until a ten-seat store ships). Smoke: `/api/health`, the OpenAPI carrying the ten-seat ask kinds and the night record events, replays with the archive's nine-seat game parsing and its page serving, the landing saying four sides and ten seats, `/play`, the model menu. Not yet run on this build: a live ten-seat game through the server (the owner's user testing is the first).
· **2026-10-14 both containers rebuilt at `d41b1c0c`** (branch and the `prompt-layout-baseline` tag pushed first; `docker build` from a clean detached worktree, then `compose up -d --no-build`; `:prev` = the images that ran before: server `837b9b6d`, frontend `3c4b8bee`). The branch tip, 145 commits past the frontend's base: the shared-prefix prompt layout as the only layout (every seat turn and lookup opens with the rules and the public record, the cache boundary; a new prompt epoch, `evidence/caching/experiment_log.md` §13-15), reads-first seat schemas, OpenAI explicit cache breakpoints, Claude's unenforced schema mode, cache writes priced at their premium; and the other sessions' work since `837b9b6d`: the v8 memory pipeline (credit, stage filter, synthesis), served games saving their extraction input instead of extracting, the model catalogue in the database, the Qwen embedder via OpenRouter. Migration `0012` and `OPENROUTER_API_KEY` applied by the owner before the swap. Pre-flight in the new server image: imports, the layout and the embedder resolve. Smoke: `/api` health, models (all ten menu rows), replays, characters, `/`, `/play`, `/rooms`, `/replays` all 200, no errors in the server log. Not yet run on this build: a live game (the owner's next).
· **2026-10-14 server only rebuilt at `7f508c4d`** (branch pushed first; same clean-worktree build; `:prev` = server `d41b1c0c`; frontend unchanged). A json_mode seat (Haiku, Luna) whose reply breaks the schema is asked again with the schema enforced, so the turn stays on its own model instead of going to the rescue; and `run_batch --stage-filter`. Pre-flight in the image: the retry's code imports with the server's environment. Smoke: `/api/health`, `/api/models`, `/api/replays`, `/` all 200, no errors in the server log.
· **2026-10-14 server only rebuilt at `68cef8b0`** (same procedure; `:prev` = server `7f508c4d`). The enforced retry extended to the lookup's situation summary and the day summary, after a demo game's lookup fell back to a generic query on a broken json_mode reply. Haiku accepted both schemas enforced (one probe call each). Same smoke, all 200, no errors.
· **2026-10-14 server only rebuilt at `a1e47ad6`** (same procedure; `:prev` = server `68cef8b0`). A prompt change: a turn shown no lessons gets no verdict field and no verdict example (Haiku had copied the example's lesson-1 verdict onto 426 turns with no lessons in the v8 demo games); after the cache boundary, so the cached prefix is unchanged. One real Haiku discussion turn checked before the swap (no verdicts, parsed). Same smoke, all 200, no errors.
· **2026-10-14 both containers rebuilt at `344b9e58`** (same procedure; `:prev` = server `a1e47ad6`, frontend `d41b1c0c`). The outage first: since the `d41b1c0c` deploy every POST /games had died with a 500, because the session seeded the file store on every game, memory on or off, the Qwen embedder switch had made `demo_gen1`'s `indexed_cache.pkl` stale, and the rewrite hit the read-only mount (each attempt also re-embedded 723 records through OpenRouter for nothing). The fix is the store swap ruled in July: the graph is compiled over LangGraph's Postgres store on `ww-postgres` (records and vectors in the database; the tick publishes into it after each pass, `tick publish` by hand), nothing is seeded into the process, `WW_MEMORY_STORE_DIR` and the `memory_stores` mount are gone. `GET /models` now carries `memory_available`, the ticket's switch follows it (default still off), and a memory-on request is refused with 409 while the store is unpublished or embedded by another model. Before the swap the owner resized the leftover empty `store_vectors` column (an earlier experiment had created it at 8 dimensions) to 1536. Order: compose up (memory-off games back at once; `/models` said memory unavailable, "no lessons published"), then the publish from the host (2,498 records, 490 strategy points, 3 min 15 s through OpenRouter), after which `/models` flipped to available with no restart. Smoke: health, models (ten rows), the 409 before the publish, a vector search through the server's own store, one house-funded memory-on Haiku game `2f19d908` (the first memory-on game served on the ten-seat cast).
· **2026-10-15 both containers rebuilt at `2482f370`** (branch pushed first; `docker build` from a clean detached worktree, then `compose up -d --no-build`; `:prev` = server and frontend `344b9e58`). 91 commits: the landing reworked (the hero's new words and the guide's sign, a ten-seat game in the carriage, three cards from real games, the replay section, the closing with its case-study plate), the guide rebuilt (introduction, live demos, the sides' rooms, "The end of the line"), the controls kit (cream and brass plates, wells, text buttons, links, plate tabs); and the other session's batch: a finished game keeps its prompts for the nightly leak audit, the replay list carries how the neutral fared, the slates show the roles dealt. Migrations `0013` (prompt captures) and `0014` (`games.neutral_result`, filled for finished games) applied by the owner before the swap. Smoke: `/api` health, models, replays (`neutral_result` filled), characters, `/`, `/play`, `/rooms`, `/replays`, `/guide` and the carriage's replay page all 200; the new image is the running one; no errors in the server log.
· **2026-10-15 frontend only rebuilt at `d4295e49`** (branch pushed first; `docker build` from a clean detached worktree, then `compose up -d --no-build --no-deps wolf-frontend`; `:prev` = frontend `2482f370`, the server unchanged at `2482f370`). The guide's role cards at reading size: two to a page on a desktop (417 px at 1440, from 270), 85% of the row on a phone; and the music bench (`/workbench/music`), whose files are not in git, so on the site it lists no candidates. Smoke: `/`, `/guide`, `/replays`, `/rooms`, `/play`, an old replay page and `/api` health, models and replays all 200; the guide's chunk carries the new width; no errors in the frontend log.
· **2026-10-16 frontend only rebuilt at `87499f98`** (not pushed; `docker build` from a clean detached worktree, then `compose up -d --no-build --no-deps wolf-frontend`; `:prev` = the frontend image that ran before; no rooms waiting and no game traffic in the 20 minutes before). The typography review (`docs/typography.md`): Young Serif retired from the theatre (Garamond 600 for its signs, scaled by `--display-scale`; Literata 600 for its small text and controls; even digits on signs and controls); the site's titles in Garamond; speech in Literata, typed notes in Courier Prime, one style for the small labels; the landing's hero as a poster (the game's name as the sign, the hook in a lamplit Garamond 500, the lamps hung from the name's position) and its story moved into the reading room under one light by "What makes it different". Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays` and `/api` health, models and replays all 200; the landing's HTML carries the new name, hook and story; no errors in the frontend log. Disk after the build: 9.7 GB free (94%).
· **2026-10-16 frontend only rebuilt at `91216f7f`** (not pushed; same procedure; `:prev` = frontend `87499f98`). The landing's hero on a phone darker (the doors' light under the tags and smaller, the candle glow at half, the wall's tiles a shade darker; the desktop unchanged), and the music back on an iPhone after another app or a call (an `interrupted` AudioContext is closed and remade on the next press). No rooms waiting and no game traffic before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays` and `/api` health, models and replays all 200; no errors in the frontend log. Disk after the build: 8.1 GB free (95%).
· **2026-10-16 frontend only rebuilt at `1a04c23d`** (not pushed; same procedure; `:prev` = frontend `91216f7f`). The replay's night counts seats, not rooms: the night stop's notice says the seats that acted (a ten-seat wolf with its own room and the pack's is one; it had read "11 acted" beside "Acted 10 of 10"), and the pill inside the rooms reaches full on the last room (`ten_seat_pass.md` §11). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; the live chunk counts `acted.size`; no errors in the frontend log. Disk after the build: 39 GB free (72% of `/home`, where Docker keeps its data).
· **2026-10-16 frontend only rebuilt at `79a7c802`** (not pushed; same procedure; `:prev` = frontend `1a04c23d`). The replay's opening stop: with Reveal on the play pauses on the opening, a seat's card opens its file led by what it wrote (its line, or its pass with the reason and what it held back), Play the opening ▶ or Skip the opening →, and a round's passes are one placard (beat sheet §2); and the next speaker's rest pose decoded ahead of a pass (`81ca9b13`): on the old build each pass's pose was first fetched 1.4 s into its beat, as the puppet changed into it, on this one 4 to 6 s before. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; the live chunk carries the stop; no errors in the frontend log. Disk after the build: 39 GB free (73% of `/home`).
· **2026-10-16 frontend only rebuilt at `34230767`** (not pushed; same procedure; `:prev` = frontend `79a7c802`). At the opening's stop a seat's file reads as of the round's end (its notes, reads and lessons written with its opening; at the round's start they were empty), the stage and the transcript staying at its start. The first `docker build` failed and its output was not kept (`-q`); the rebuild from the same worktree passed with no errors, and nothing was swapped in between. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; no errors in the frontend log. Disk after the build: 38 GB free (74% of `/home`).
· **2026-10-16 frontend only rebuilt at `399d48fa`** (not pushed; same procedure; `:prev` = frontend `34230767`). The game's card says what you do at night in short (nine roles; the sigilist's and chanteuse's in the owner's words), its count only in the uses line, which is now the standard on every card the game shows (the deal's box too; the vigilante counts bullets); the replay's rooms show what the actor had left that night; the guide's Tools gain Your card (a Day | Night demo of the role card). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; the guide's HTML names three aids; no errors in the frontend log. Disk after the build: 36 GB free (75% of `/home`).
· **2026-10-16 frontend only rebuilt at `b4d10bce`** (not pushed; same procedure; `:prev` = frontend `399d48fa`; another session's uncommitted morning-roll and contract edits stayed out, the build being a clean checkout). The guide's Your card is now the sigilist's night room (one baked picture, `scripts/bake-guide-room.mjs`, 34 KB, drawn only once its tab is shown) with the game's card on the table, opening full size on a tap; the opened card's phone growth became a knob (`--card-max`, the game's value by default). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; the guide's role-card and tab-height tests pass against the live site; no errors in the frontend log. Disk after the build: 36 GB free (75% of `/home`).
· **2026-10-16 frontend only rebuilt at `aceaf93f`** (not pushed; same procedure; `:prev` = frontend `b4d10bce`). The landing carriage waits under the house's loading picture (`TrainLoader`) in place of "Rewinding the reels…", up from when the carriage comes near until the stage's pictures are in, then faded off; the archive's failure keeps its line. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay page and `/api` health, models and replays all 200; on the live landing, with the pictures held back, the train is in the window and gone once they are drawn; no errors in the frontend log. Disk after the build: 35 GB free (76% of `/home`).
· **2026-10-17 both containers rebuilt at `c00ec36c`** (not pushed; same procedure, from a clean detached worktree, so another session's uncommitted engine work stayed out; `:prev` = server `676d89ba` (the 2026-10-15 image), frontend `aceaf93f`). Server: the whole pack learns the role the illusionist hid (a new prompt epoch: one sentence of the rules), and the deduction engine's slices 1–2 (`9c7f37b6`, `deduction_mode` full by default, the human seat off), whose built image `9ca84fc4` had never been swapped in. Frontend: the wolves' night in the transcript (a Wolf filter; live, a wolf's transcript opens on it for the night and closes at dawn; the chat box left the pack's room), the pack's dawn record told only when it says something new, a wolf's wing showing the concealed role it was told, the transcript's "acts on seat 0" fixed, and the landing's closing section (owner). Full e2e on a scratch build first: 173 of 175, the two failures a flaky guide test (passed on rerun) and a workbench beat index my change shifted (renumbered); goldens kept only where the change explains them. No rooms waiting and no games running before the swap. Pre-flight in the server image: the record and deduction modules import, the rules say every wolf. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, replay 645228e7 and `/api` health, models and replays all 200; the landing serves the new question; no errors in either log. Disk after the builds: 34 GB free (76% of `/home`).
· **2026-10-17 both containers rebuilt at `ea1c3176`** (not pushed; same procedure, from a clean detached worktree; `:prev` = server and frontend `c00ec36c`). Server: a human wolf's skill turn (block, conceal) is announced before the pack's parallel skill step ends (`2814776d`), and the other session's committed fortune-teller self-bet announcement and ledger fix (`06f21018`, `cedfcdea`). Frontend: a tappable seat card keeps its photo on iPadOS 18 (`ea1c3176`; full e2e 175/175 on a scratch build, no golden explained by it), and the self-bet morning lines. Held while a human game was running; swapped once it had finished, with no rooms or games live. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, replay 645228e7 and `/api` health, models and replays all 200; the live server's `pack_fan_out_skills` announces; no errors in either log. Disk after the builds: 33 GB free (77% of `/home`).
· **2026-10-17 both containers rebuilt at `9c87b441`** (not pushed; same procedure, from a clean detached worktree; `:prev` = server and frontend `ea1c3176`). Mine: each prompt's plate holds its own "Let my agent …" button (vote, choose, talk) in the plate's second-button dress, the top plaque gone, and a night plate that wraps within the room (`9c87b441`). The other session's, deployed at the owner's word: day 1 not counting toward the forced vote (`095c9d94`), the pack chat as a conversation with a voluntary pass shown (`c30af7ba`), the wolves knowing each other's roles (`3e2f6c1b`) and a human wolf told its packmate's role at the deal (`6b9fe05c`), the night-1 lot suggested as the AI wolf's own pick (`3222638c`). Python suite 1701 passed and full e2e 175/175 on a clean build of this HEAD before the build. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, replay 645228e7 and `/api` health, models and replays all 200; the live server builds `pack_roles`, the live frontend carries "Let my agent vote"; no errors in either log. Disk after the builds: 32 GB free (78% of `/home`).
· **2026-10-17 both containers rebuilt at `ac7acec7`** (not pushed; same procedure, from a clean detached worktree; `:prev` = server and frontend `9c87b441`). The owner's live bug report of the day: a draw no longer drops a finished game (`ae5bfe7d`); a player's key is tried on the provider before a game or room opens, and a key refused mid-game ends the game with "Your key stopped working" instead of a game of technical passes (`34cefb05`, `c018f6a5`, `6962f065`); every send is retried and says "Sending…" until the server has it, the ballot reopening on a failure (`205813bb`); a packmate's line no longer holds a human wolf's prompt (`3a7fea5c`); one house loader for every wait on `/games/[id]` (StationStill gone), the connection pill, a drop under 20 s is a blip (`5d11f5b1`); 64 graph threads (`3b9a7326`); Sentry on both sides, one project, every data category off and the model-provider integrations off (`bbd708bc`, `22bc79cf`, `ac7acec7`; server DSN in `.env.production`, the browser's as a build arg). Python suite 1711 passed on the clean worktree (one environment-only failure: the untracked `memory_stores`), full e2e 183/183 on `5d11f5b1` (only `loading-game.png` regenerated). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay, a game page and `/api` health, models and replays all 200; OpenAPI carries `error_kind`; the server logs "error reporting on"; on the live `/play` the browser SDK is loaded, an OpenAI-style key with Haiku gets the hint, no console errors. Draw game `f2e944a3` (dropped by the post-game crash) restored by the owner from its 525 stored events (`complete_game`, as a normal finish).
· **2026-10-17 server rebuilt at `cca44ed8`** (frontend unchanged at `ac7acec7`; server `:prev` = `ac7acec7`). The restored draw answered 404: the replay list and lookup required a winner, so no draw could ever be watched (`cca44ed8`: the winner is not a listing condition; the replay's winner is None for a draw). Server suite 296 passed. Smoke: replay `f2e944a3` 200 (winner none, the fortune teller "won (2 points)", 525 events), first in `/replays` as "Draw", its page plays with no console errors; `/`, `/replays`, `/api/health` 200.
· **2026-10-17 frontend rebuilt at `8ae65f36`** (not pushed; same procedure, from a clean detached worktree; server unchanged at `cca44ed8`; frontend `:prev` = `ac7acec7`). The felt set (owner): every vote and day prop the owner's felt picture (`530bfcdd`), the jar standing at the table's end for the count instead of tipping, the place cards as paper tacked to the felt (`72b8e836`), the landing's carriage in cream felt, a phone's its own mini carriage (`0c9d462b`); the character sprites under `sprites/characters` and the unused portraits gone (`ba1c7e7c`). The other session's, deployed at the owner's word: a game no side won is the neutral's when it won it (`3612fa1b`), the speculator's sides as pennants (`7211ec9d`), the fortune teller's roles hung from the plate's top (`1f629b69`). Full e2e 183/183 on a clean build of this HEAD (70 goldens redrawn, each checked against its old one); unit 1635 passed. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays`, a replay and `/api` health and replays all 200; on the live landing the desktop draws `frame-felt` and a phone only `frame-felt-phone`, no console errors.
· **2026-10-17 frontend rebuilt at `340872dc`** (not pushed; same procedure, from a fresh detached worktree; server unchanged at `cca44ed8`; frontend `:prev` = `8ae65f36`). The station in felt (owner): the train joined from the owner's felt pieces, five windows on the dining car with the felt night country through them, the walnut felt beam and ledge, the platform's stone softened and warmed (`c99dd0f4`); each window its own glass, the places seated in the nearest window, an agent's curtain inside the glass with the agent's head and shoulders cast on it (`7844fcfb`). Full e2e 183/183 on a clean build of this HEAD (four station goldens redrawn, checked by eye). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/play`, `/rooms`, `/replays` and `/api/health` 200; the live station draws the felt train; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `f7f91bd8`** (not pushed; same procedure, from a fresh detached worktree; server unchanged at `cca44ed8`; frontend `:prev` = `340872dc`). The platform's ledge carries the music's speaker, so music turned off on a site page can be turned back on in the waiting room (`e05d2e95`); the guide's introduction shows six of the cast before the felt train (`f7f91bd8`). Full e2e 183/183 on a build of this HEAD (four platform and two guide goldens redrawn, checked by eye). One room waiting during the swap (the server's, untouched by a frontend swap). Smoke: `/`, `/guide`, `/rooms`, `/replays` and `/api/health` 200 (origin certificate needs `-k` from the box); the live guide serves the new picture; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `6fc5706c`** (not pushed; same procedure, from a fresh detached worktree; server unchanged at `cca44ed8`; frontend `:prev` = `f7f91bd8`). The wooden toy (owner): the landing carriage, desktop and phone, re-cut and re-measured (`83bb3488`); the station's train joined from the owner's new pieces, the guide's platform picture re-baked (`6fc5706c`), plus the bake script (`07393835`). A picture swap, so per the owner's ruling only the specs that show the pictures ran: the landing, platform and guide goldens redrawn (checked by eye), the landing behaviour tests, the live waiting-room and departure tests, the station and manifest unit tests; the departure checked by eye mid-pull. The first image build exited 1 with no output under `-q`; the same worktree built clean on the next try. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays` and `/api/health` 200; the live train file matches the committed one; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `b0c89858`** (not pushed; same procedure; server unchanged at `cca44ed8`; frontend `:prev` = `6fc5706c`). The guide's platform picture stands the kitsune and the automaton in the owl's and the hare's places (owner). A picture swap: only the guide goldens redrawn (checked by eye; guide-390's top is the known capture-timing change of the section bar behind the nav). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays` and `/api/health` 200; the live guide serves the new picture; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `3e16dc9f`** (not pushed; same procedure; server unchanged at `cca44ed8`; frontend `:prev` = `b0c89858`). The guide drops "A claim isn't proof" under the day's line (owner: it restated the Vote and Morning stops). Guide tests 8/8 after the guide goldens were redrawn (only the box gone and the page below it moved up). No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays` and `/api/health` 200; the live guide has no claims box; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `195e0710`** (not pushed; from a fresh detached worktree at the live `3e16dc9f` with the hero's two commits cherry-picked, `318b90ae` → `4277bacb` and `2d8eeaa7` → `195e0710`, so the other session's frontend commits `c957fdb5` (contract types) and `d1f343c1` (the departures board's Board goes to the room) are NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `3e16dc9f`). The landing's hero is the night platform as a handmade set, its words and two paper tickets on the sky (owner). site.spec + phone-rule 54/56 then the landing goldens redrawn (checked by eye), landing tests 7/7. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays` and `/api/health` 200; the live landing serves both hero files; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `20ccf759`** (not pushed; from a fresh detached worktree at the live `195e0710` with `152f20ee` → `2f828779`, `8dfa71df` → `cb0a1f09` and `b01a6efa` → `20ccf759` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `195e0710`). The mark is a gold 9 badge (nav, hero rule, favicon, home-screen icons); the hero's tickets print bolder, their rule ends in the arrow, and the tables boarding are the nav's Rooms door's alone (owner). site.spec + phone-rule 55/56 (the landing-390 golden, expected), then every site golden force-redrawn and diffed (the nav's mark only, the landing's hero, rooms-390 losing a dev badge); the landing's clock test failed once in the redraw run and passed alone. No rooms waiting and no games running before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/api/health`, `/icon.svg`, `/icons/icon-512.png` 200; the live icons match the committed ones; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `6a4c62d4`** (not pushed; from a fresh detached worktree at the live `20ccf759` with `0cdff3e1` → `fcf30d13` and `d4daadc7` → `6a4c62d4` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `20ccf759`). On a phone the hero's purse and guide sign stand at the screen's foot with the passengers clear above them, and the carriage's section starts below the first screen (owner); the landing goldens leave out the pinned strip, as the rooms' do. Full e2e 181/182 (the landing-390 golden, expected), landing goldens redrawn and diffed (1440: 74 px of the strip's edge). The image build failed once inside `npm run build` and passed on the rerun with a clean log, as before. Rooms and games were not checked before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/api/health` 200; the live landing carries the hero's foot; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `f398ac5b`** (not pushed; from a fresh detached worktree at the live `6a4c62d4` with `716eb24f` → `a739bfc0`, `f666b2dd` → `fa197683`, `ca08f124` → `eb7bd575` and `a63360ab` → `f398ac5b` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live, so the live board rows keep their in-row join strip and its styles; server unchanged at `cca44ed8`; frontend `:prev` = `6a4c62d4`). The departures hall on the night platform (owner's mock and raster kit): the wall as one picture, the board's case in pictures with a live plate and plaque, the passenger beside the board on a wide screen and after it on a narrower one; on a phone a larger title, no lede, stub tickets; the ticket's stub now at 860px and under (the landing's tablets too); PlatformBackdrop removed. Full e2e 181/182 (the guide's case-file test timed out once, passed twice alone); rooms goldens redrawn, stable over three reruns. No rooms open before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/play`, `/api/health` 200; the hall's pictures and all six board pieces served; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `c908a226`** (not pushed; from a fresh detached worktree at the live `f398ac5b` with `73f8230e`, `30506ee2`, `81c4f95a`, `4a875458`, `c3b76b82`, `79799021`, `0fb239ce`, `a971c7ef`, `4a253736`, `8445b1bd`, `26a305d6` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `f398ac5b`). The hall's footer close; the carriage in a night gradient with falling snow, its phone gap a quarter less; the station's walls as pictures (the landing's navy wall behind the story to the latest games, the guide, the ticket office, the archive); the story's title over the gold rule; the research as the owner's two-column mock (a shorter phone version), the case study a link, the footer close; the guide's side nav at the screen's middle; the ticket office on the landing's paper tickets; the room form at `/play/room` (`/rooms/new` redirects 308). site.spec + phone-rule 57/57 after every site golden was redrawn (the guide's case-file test, which flaked twice beside the whole suite, given 15 s). No rooms open before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/play`, `/play/room`, `/api/health` 200; `/rooms/new` 308 to `/play/room`; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `4464cd68`** (not pushed; from a fresh detached worktree at the live `c908a226` with `7ab819c1`, `1afc2313`, `7a15f511`, `268d7582` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `c908a226`). The guide's wall is its green alone; the navy wall's lamp hangs just above "What makes it different" and the features board runs close into the replay; the archive keeps its drawn tile room under the pendant (owner preferred it; pixel-identical to before the walls round). site.spec + phone-rule 57/57, the ticket office's goldens unchanged. No rooms open before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/play`, `/play/room`, `/api/health` 200; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `b203158e`** (not pushed; from a fresh detached worktree at the live `4464cd68` with `66b00bc3`, `c59ad4a3`, `860c3b8a` cherry-picked; the other session's `c957fdb5` and `d1f343c1` still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `4464cd68`). The guide's role rooms fade to clear into its green wall; on a desktop its nav names the section 40% down the screen. site.spec + phone-rule 57/57 under the whole suite's load (the case-file test now clicks its tabs until selected). **The image build failed twice in `next/font`** (`TypeError: Cannot read properties of null (reading '1')` on the Outfit font): Next fetches the Google Fonts CSS at build time and got an answer with no font links (a throttled or error reply); the same request answered normally minutes later and the third build passed. This is the likely cause of the earlier silent one-off build failures too: on a build failure, read the log for `next/font` before anything else, and retry. No rooms open before the swap. Smoke: `/`, `/guide`, `/rooms`, `/replays`, `/play`, `/play/room`, `/api/health` 200; the fonts preloaded from `/_next/static/media`; no errors in the frontend log.
· **2026-10-18 frontend rebuilt at `1290eddb`** (not pushed; from a fresh detached worktree at the live `b203158e` with `b1f065c3`, `04a61006`, `dd70680d` cherry-picked; the other session's `c957fdb5`, `d1f343c1` and later stage commits still NOT live; server unchanged at `cca44ed8`; frontend `:prev` = `b203158e`). Every site page comes up whole behind the train loader (`PageGate`: the first screen's pictures and fonts, waited for from an inline script, 8 s cap), and the landing carriage's whole scene comes up at once, asked for once the hero is up (10 s cap). site.spec + phone-rule 57/57 (the preview test now expects the carriage loaded without a scroll). Smoke: `/`, `/rooms`, `/replays`, `/guide`, `/play`, `/play/room` 200 with the gate's script; on the live site each page opened 160–430 ms after the request on a first visit from this host and the carriage was ready without scrolling, no page errors (a reload, which revalidates every file, opened in 0.3–1 s).
· **2026-10-18 frontend rebuilt at `20934225`** (live `1290eddb` + `bbe553f3`; `:prev` = `1290eddb`): the page loader, once up, stays 1.5 s, and a page ready before 0.3 s appears with no fade (owner: the train blinked on fast loads). Timing only, so no e2e run (owner). Smoke: all six site pages 200, no log errors; on the live site a first visit to `/` showed the loader and held it to 1.96 s, every other first visit and every cached one came up with no loader (186–412 ms from the request).
· **2026-10-18 frontend rebuilt at `9d8f80b9`** (live `20934225` + `7c2e4d76`; `:prev` = `20934225`): the page loader comes up after 1 s (was 0.3 s) and, once up, stays 2 s (was 1.5 s); owner: 1.5 s too short to see it, and under a second needs no sign. Timing only, no e2e (owner). Smoke: all six site pages 200, no log errors.
· **2026-10-18 frontend rebuilt at `ac97363c`** (live `9d8f80b9` + `74153ef5`; `:prev` = `9d8f80b9`): one train from the click (owner saw a blink of the site loader's train, dark, then the gate's): the site loader also waits 1 s; a page's gate counts its second from the click and carries on a train already up; the shared state is on the window because the build gave the loader and the pages separate copies of PageGate's module. Checked locally on delayed client-side clicks (train ~1 s after the click, held 2 s, no blink; a fast click shows none); no e2e (owner: timing). Smoke: all six site pages 200, no log errors.
· **2026-10-18 frontend rebuilt at `af939f3c`** (live `ac97363c` + `8e6611df`; `:prev` = `ac97363c`): "What makes it different" in the owner's material kit (walnut board + brass rim, card paper, cream slips, brass plates as a 9-slice, paperclip, worn-ink stamp; copy unchanged). Tests: the two landing goldens only (no other test shows the board), redrawn on HEAD + the change in a worktree because the main tree's build carried the other session's uncommitted seat rail into the carriage. Smoke: pages 200, the walnut in the landing's CSS, no log errors.
· **2026-10-18 frontend rebuilt at `62ed9007`** (live `af939f3c` + `f4a1160b`; `:prev` = `af939f3c`): "At the end of the line" as a case file in the material kit (walnut, brass plate, kraft folder + tab, card under a red ribbon, brass pin, clipped ruled note with "Do not disclose:" marked, outcome on the kraft; copy unchanged). Tests: the two landing goldens only, redrawn on HEAD + the change in a worktree. Smoke: pages 200, the folder tab in the landing's CSS, no log errors.
· **2026-10-18 frontend rebuilt at `d4b5b5f7`** (live `62ed9007` + `4ece428d`; `:prev` = `62ed9007`): the replay section's one way on is "Watch all replays" (brass plate button) under "Watch latest games"; "Explore this replay" removed (owner). Landing goldens only. Smoke: pages 200, the new words served, no log errors.
· **2026-10-18 frontend rebuilt at `4f753583`** (live `d4b5b5f7` + `88880f85`; `:prev` = `d4b5b5f7`): the carriage's game-ID board is the owner's walnut sign (9-slice) and the carriage stands on the owner's railway (repeating strip; platform edge moved below the track). Landing goldens only. Smoke: pages 200, rail + sign in the landing's CSS, no log errors.
· **2026-10-18 frontend rebuilt at `9bcee9da`** (live `4f753583` + `f39ba9ad`): the guide's "The end of the line" in the material kit (kraft folder + tabs on walnut in a brass rim, walnut mounts, brass clip, cream index cards with a red double-rule border, worn-ink stamp; copy unchanged). Tests: the guide goldens + the case-file test, on HEAD + the change. Smoke: pages 200, no log errors.
· **2026-10-18 frontend rebuilt at `f5331623`** (live `9bcee9da` + `8f5c0eab`, `b684a83d`, `cfc99daa`; `:prev` = `9bcee9da`): the guide's tools board in the kit (walnut, brass-plate tabs, card paper, brass discs), the role cards on card paper under the kit's frame (no tray), the slates on card paper. ToolsTray.tsx differs from the main tree only by the other session's uncommitted NotesDemo work (not live). Tests: guide/landing/archive/ticket goldens + the guide's tests, on HEAD + the changes. Smoke: pages 200, no log errors.
· **2026-10-19 server rebuilt at `334a56e1`** (not pushed; from a clean detached worktree; frontend unchanged at `f5331623`; server `:prev` = `cca44ed8`). The reasoning work since 2026-10-17, at the owner's word: the deduction engine's slices 3–15 (public block and seat block, `deduction_mode` "full" by default; the claims checked against the record and each other, the conditionals, the explanations, implied role claims, E18), the evil cards that claim instead of deny with their covers (R11), the open floor speaking by default with the echo gate holding restatements, the rules clauses (a roleblock notice, the morning naming no visitors), speech events carrying their claimed night actions, the difficulty levels per side (config only, not in rooms). Persona voices stay off. No migration (no alembic change in the range). Python 2272 passed in the clean worktree (1 env-only fail: the untracked memory store dir). No room waiting before the swap. Smoke: `/`, `/play`, `/replays`, a replay page and `/api` health, models, rooms and replays all 200; container healthy. Not yet run on this build: a live game.
· **2026-10-19 frontend rebuilt at `62dcf7af`** (not pushed; from a fresh detached worktree at the live `f5331623` with `11b60671`, `1a1f2f97`, `b280e34e`, `004f1c3f`, `8599d673`, `334a56e1`, `cba985ea`, `01f9f5e2`, `b880b789`, `cca3015b`, `89d7525d`, `b294a5e6` cherry-picked (docs conflicts taken as the incoming side; the docs-only `47519b46` skipped) and the open slot's unused sheets removed as on the branch; the other session's `c957fdb5` (contract types) and `d1f343c1` (the rooms' Board) still NOT live; server unchanged at `334a56e1`; frontend `:prev` = `f5331623`). The live-game revamp, all at the owner's word: the seat rail drawn once a game in the owner's materials, the notes moved into the case file (a file on every seat, full height on a phone), the navy jar chip, the maple ring and the pewter plate, the owner's car at four hours with its country painted in, the whole table standing on the floor and no trap, the HUD's bronze kit (dark bronze panels, one light bronze button, cream for the act and the written, icons, a blank white chip to abstain, a smaller phone ballot) and the transcript full height whenever it is open. Full e2e on HEAD + the HUD work 182/183, the one failure (the speaking dock not narrowing beside the full-height drawer, so the drawer covered Send) fixed and live.spec 31/31; 77 goldens redrawn, each checked by eye; unit 1637. The image build failed once in `next/font` (the throttled Google Fonts reply) and passed on the retry. No rooms open and no game traffic in the half hour before the swap. Smoke: `/`, `/guide`, `/play`, `/play/room`, `/rooms`, `/replays`, a replay page and `/api/health` 200; the live CSS carries the kit; the guide says "blank chip"; a live replay draws with no page errors; no errors in the frontend log.

**P4 — deploy + polish.** Caddy site (same-origin `/api`), HTTPS + `Secure` cookie flag on ·
production compose (Postgres + `alembic upgrade head` before first boot; one `WW_POSTGRES_DSN`
powers both the replay archive and live-session durability) · landing page · README 60-s replay-theater GIF (survives credit expiry;
recruiters watch GIFs, not links).

**Later (each needs new backend, separately scoped):** ghost-guess persistence endpoint →
daily puzzle (curation/publish) → MVP score/autopsy endpoint → memory-showcase mode 2 (store
read-path + changelog explorer) → BYOK restart recovery by original-host key resubmission
(`server_design_notes` §6 implementation packet) → accounts/OAuth/stats → room row GC (listing shipped
slice 7; the TTL hides stale rooms from browse, but dead rows still accumulate in the
`games` table) → kick-player (deferred 2026-08-20).
~~live-session durability~~ — built 2026-08-20, no longer pending (see §8). **The deep memory X-ray** (retrieval→decision inspector for v7 memory-on
replays, demo mode 3's enhancement) reads eval-case dumps = a static-export pipeline, NOT this
server — schedule as its own slice when the memory-showcase mode is taken up.

## 8. Backend readiness matrix (as of 2026-08-20)

| Feature (design_log §) | Backend | Notes |
|---|---|---|
| Replay theater + X-ray (§2 T1, §4) | ✅ full | `GET /replays/{id}` = complete durable log, ALL tiers; archive starts EMPTY → P0 seeding |
| Live spectating (§2 T2) | ✅ full | public tier, no seat needed; pacing channel |
| Solo play w/ role choice (§2 T3) | ✅ full | `POST /games`; role choice is solo-only by server ruling |
| Multiplayer rooms (§13) | ✅ full | create/join/start/rejoin, host_key, AFK delegate ladder; slice 7 (2026-08-20): `GET /rooms` public browser + room names + host lock + listing TTL (kick deferred) |
| Post-game reveal (§6.3) | ✅ full | R7 flush is server-implemented; client just re-folds |
| BYOK + model picker (§10) | ✅ full | `GET /models` render-ready; 422 rules mirrored client-side |
| Vote matrix / mention graph (§7) | ✅ derivable | `vote_cast` + `addressed_targets` (observer) |
| Dramatic irony live (§2 T1) | ❌ by design | roles are observer-tier until game_over; replay-only |
| Memory X-ray / said-vs-thought (§2 T1) | ⚠️ partial | live is memory-OFF (research closure); wire x-ray = scheduler/roles/strategy/gated passes; deep memory inspector = static eval-case export, later |
| Draft a line from notes (ux_journeys D25) | ✅ server (2026-09-17), ❌ UI | `POST /games/{id}/draft`; 3 per turn, clock credited; discussion turns only |
| Ghost guesses (§9), daily puzzle (§7), MVP score (§6.4), accounts (§6.1) | ❌ none | localStorage ghost v1 now; rest = "later" list |
| Session durability | ✅ full (2026-08-20, normalized 2026-08-22) | Postgres checkpointer + unified games/events tables + boot recovery; a server restart re-parks pending turns and games resume (restart smoke passed). Completed `GameRow`s and their existing `EventRow`s are the replay—there is no copied replay blob. BYOK games are the one exception: the key dies with the process, so they become dropped with a clear `GameStatus.error`. Unset `WW_POSTGRES_DSN` degrades gracefully to RAM-only. |

## 9. Testing & quality line (ruling 8)

Vitest on `src/game/` only (fold correctness: full-game fixture folds, R7-unlock fold,
pacing monotonic-max, tier-absent robustness). Prettier everywhere. ESLint = `next/core-web-vitals`
flat config. No component tests, no E2E for now. All-TS — zero `.js` files, no `any` at view-prop
boundaries (dota2pred's `historyData: any[]` mistake is the named anti-pattern).
