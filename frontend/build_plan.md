# Frontend build plan — `webapp/`

> Decision record + implementation plan, ruled 2026-08-20. Supersedes the stale
> `BUILD_BRIEF.md` (2026-07-17, lived in the abandoned `ww-frontend-app` worktree) — that brief
> assumed "build against mocks, backend staged last"; the backend has since been fully built and
> live-smoke-tested (SSE server, rooms, seat tokens, AFK delegation, replay archive, live-session
> durability with restart recovery; 947 tests green). The idea source remains [`design_log.md`](design_log.md); the wire contract lives in
> [`server_client_transport.md`](server_client_transport.md) + [`event_derivation.md`](event_derivation.md)
> and `server/schemas/events.py`.
>
> **Scope note: this document covers architecture, stack, and build phasing only. Visual / UX
> design (layout, table view, séance-noir styling, mobile ergonomics) is deliberately NOT covered
> — it is the next design discussion. The theme-slice structure below is where that pass will
> plug in without touching app code.**

---

## 1. Rulings (owner, 2026-08-20)

| # | Question | Ruling |
|---|---|---|
| 1 | Where the app lives | `webapp/` in the main repo (name chosen over `frontend_app/` to avoid clashing with the existing `frontend/` docs dir). **No new branch / worktree** — build directly on the active branch; the app is a disjoint folder, commit hygiene by folder-scoped commits. |
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
- **WebSocket anything** — SSE is the wire contract.

## 3. Repo layout

```
webapp/
├── Dockerfile  next.config.mjs  postcss.config.cjs  tsconfig.json  vitest.config.ts
├── .env.local.dev (→ cp to .env.local)  .env.production
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
    ├── components/                         # cross-route: table view, transcript, xray, forms
    ├── game/                               # THE core: reducer + store (pure TS, vitest home)
    │   ├── foldEvents.ts                   # (GameView, DurableGameEvent) → GameView
    │   ├── types.ts                        # GameView + derived shapes (types/domain material)
    │   └── store.ts                        # zustand session store (§4)
    ├── hooks/                              # useGameStream, useCountdown, useFilterState, …
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

BYOK-remember explicitly needs ZERO server support: the key's only wire appearance is the
create-request body; remember/mask/clear are local operations (ruled 2026-08-20).

**One route, three states**: `/games/[gameId]` renders by `GameStatus.state` — `waiting` →
lobby (roster poll, share link, start button iff `host_key` held), `running` → live table,
`finished` → post-game X-ray. This mirrors the server's registry swap (room URL = game URL);
the client never re-routes across the transition.

**Turn submission**: `POST /games/{gameId}/turns` body by `action_kind`: `discuss` → `{message}` or
`{pass_turn: true}`; `wolf_discuss` → `{message}`; every vote/night kind → `{target}` from
`candidates`; `{delegate: true}` legal everywhere (the AFK button). 422 message renders as-is;
409 = someone (or the AFK timer) already answered — clear the form and re-sync via status.

## 6. Server tweaks shipping with P0 (ruling 5)

1. `server/replays.py`: `ReplayGame.events: list[DurableGameEvent]` (currently `list[dict]`) —
   the event union, the most important type in the frontend, currently never appears in
   `/openapi.json`. One annotation fixes codegen + docs. Verify the discriminated union
   round-trips through OpenAPI cleanly (pydantic emits `oneOf` + discriminator).
2. `server/config.py` + `app.py`/`dependencies.py`: env-driven `SEAT_COOKIE_SECURE` (default
   false for dev) applied everywhere the seat cookie is set.

## 7. Phases (each ends deployable)

**P0 — scaffold + contracts.** The two server tweaks · Next 15 + Mantine 8 scaffold · theme
slices skeleton · `lib/{config,request,queryKeys}` · codegen wired · Providers/AppShell ·
Prettier + Vitest config · Dockerfile (4-stage, standalone, `NEXT_PUBLIC_*` build arg) ·
**archive seeding**: serve ~5–10 cheap LLM-only games through the real server (`POST /games`,
house key, flash-lite) — fills `/replays` AND doubles as another live soak (ruling 6).
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
key). **BYOK key handling (ruled 2026-08-20)**: the server never stores keys (by design
— BYOK games even die on restart for exactly this reason), so remembering is purely
client-side. One shared `ByokField` component (used by `/play` and `/rooms/new`): key
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

**P4 — deploy + polish.** Caddy site (same-origin `/api`), HTTPS + `Secure` cookie flag on ·
production compose (Postgres + `alembic upgrade head` before first boot; one `WW_POSTGRES_DSN`
powers both the replay archive and live-session durability) · landing page · README 60-s replay-theater GIF (survives credit expiry;
recruiters watch GIFs, not links).

**Later (each needs new backend, separately scoped):** ghost-guess persistence endpoint →
daily puzzle (curation/publish) → MVP score/autopsy endpoint → memory-showcase mode 2 (store
read-path + changelog explorer) → accounts/OAuth/stats → room row GC (listing shipped
slice 7; the TTL hides stale rooms from browse, but dead rows still accumulate in the
sessions table) → kick-player (deferred 2026-08-20).
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
| Ghost guesses (§9), daily puzzle (§7), MVP score (§6.4), accounts (§6.1) | ❌ none | localStorage ghost v1 now; rest = "later" list |
| Session durability | ✅ full (2026-08-20, post-draft) | Postgres checkpointer + sessions/events tables + boot recovery; a server restart re-parks pending turns and games resume (restart smoke passed). BYOK games are the one exception: the key dies with the process, so they revive dead with a clear `GameStatus.error`. Unset `WW_POSTGRES_DSN` degrades gracefully to RAM-only. |

## 9. Testing & quality line (ruling 8)

Vitest on `src/game/` only (fold correctness: full-game fixture folds, R7-unlock fold,
pacing monotonic-max, tier-absent robustness). Prettier everywhere. ESLint = `next/core-web-vitals`
flat config. No component tests, no E2E for now. All-TS — zero `.js` files, no `any` at view-prop
boundaries (dota2pred's `historyData: any[]` mistake is the named anti-pattern).
