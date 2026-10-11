# Frontend owner’s guide

Next.js App Router, React, TypeScript, Mantine, TanStack Query, Zustand and Motion. The game
picture is a scaled DOM/SVG stage with WebP artwork. Live games, archived replays and the
landing preview share that renderer.

## Where to start reading

1. [Game types](src/game/types.ts) and [event folding](src/game/foldEvents.ts): turn the wire log into a view of the game.
2. [Beat generation](src/stage/beats/beatsFor.ts): turn events into the sequence the audience sees.
3. [Replay controller](src/stage/containers/ReplayTheatre.tsx) and [replay reducer](src/stage/containers/replay-state.ts): transport, seeking and the selected view.
4. [Live controller](src/stage/containers/LiveTheatre.tsx), [live reducer](src/stage/containers/live-state.ts), [stream hook](src/hooks/useGameStream.ts) and [session store](src/game/store.ts): incoming events, catch-up and human turns.
5. [Scene registry](src/stage/scenes/index.ts), [shared car](src/stage/scenes/CarScene.tsx) and [day scene](src/stage/scenes/DayScene.tsx): compose a picture from those inputs.
6. [Stage](src/stage/Stage.tsx), [coordinates](src/stage/units.ts) and [motion policy](src/stage/motion.tsx): scaling, portals, layer order and animation.

## Where an edit belongs

| Change                                            | Location                                       |
| ------------------------------------------------- | ---------------------------------------------- |
| Route, loading state, page-specific composition   | `src/app/`; route-local `_components/`         |
| Shared site navigation, buttons and paper styling | `src/components/site/`                         |
| HTTP endpoint, query key, persistence helper      | `src/lib/`                                     |
| Stream/query lifecycle                            | `src/hooks/`                                   |
| Game event semantics and session state            | `src/game/`                                    |
| What happens in the presentation, and when        | `src/stage/beats/`, `src/stage/containers/`    |
| Stage composition                                 | `src/stage/scenes/`                            |
| Reusable stage objects and animation wrappers     | `src/stage/instruments/`, `src/stage/cast/`    |
| Generated lighting and geometry                   | `src/stage/paint/`                             |
| Transcript and case file                          | `src/stage/drawer/`, `src/stage/film/`         |
| Artwork and import handles                        | `src/assets/`; conversion/baking in `scripts/` |
| Pure behavioral regression                        | Colocated `*.test.ts` / `*.test.tsx`           |
| Browser behavior and visual regression            | `e2e/`                                         |

`src/types/contracts/api.ts` is generated. Update the server contract and run
`npm run generate-api-types` rather than editing it by hand.

## Invariants worth protecting

- Catch-up history must not replay as newly arrived action. Preserve seat entitlement and
  the special out-of-order reveal backlog when changing event ingestion.
- The live human deadline remains authoritative even when presentation lags the server.
- Seeking and playback have different animation behavior. Reusing a scene must still reset
  its transient input/animation state correctly.
- The car set and backdrop persist across beats. A new React key can defeat that lifetime.
- `Layer` portals and shared transforms are intentional: changing their nesting can change
  both lighting/blending and compositing cost.
- A component being retained, memoized or visually static does not guarantee that the browser
  avoids painting or holds its decoded image. Check the target browser.

## Commands

Run from `frontend/` after `npm ci`:

```sh
npm run dev -- -p 3117
npm test
npm run typecheck
npm run lint
npm run build
WORKBENCH_URL=http://localhost:3117 npm run e2e
```

Playwright does not start the server. Its committed configuration currently uses Chromium
only. Screenshot tests and phone-rule checks have different purposes; neither certifies
physical iPhone memory or frame rate. `next lint` works with the installed Next 15 version
but is deprecated; migrate the script to the ESLint CLI when maintaining tooling.

For performance, use a separate checkout/build directory so `next build` does not overwrite
an active dev server’s `.next`. Serve that production build, then run:

```sh
node scripts/profile-theatre.mjs http://localhost:3137 chromium /tmp/chromium-profile.json
node scripts/profile-theatre.mjs http://localhost:3137 webkit /tmp/webkit-profile.json
```

This diagnostic script expects the API base to be the default same-origin `/api`; it mocks
those reads with a bundled replay. It does not start a real game. It is a census, not a
pass/fail performance gate. Missing animation/layer samples and software rendering must not
be interpreted as a fast renderer. Use a physical iPhone for final performance acceptance.

Pin the fixture explicitly in reproducible workbench URLs, for example:
`/workbench/vote?game=9369a5c1&beat=0&animate=1&frame=iphone14&hud=replay`.
The default fixture can change independently of that historical replay’s beat numbers.

## Documentation

- [Performance and ownership audit, 2026-10-11](docs/frontend-audit-2026-10-11.md): current findings, priorities and proposed tests.
- [Stage architecture](docs/stage_architecture.md): detailed renderer and design contracts.
- [Site architecture](docs/site_architecture.md): routes, site components and styling.
- [Transport](docs/server_client_transport.md): server/client event behavior.
- [Build log](docs/build_log.md) and [phone lessons](docs/phone_lessons.md): historical decisions and device observations. Treat historical explanations as evidence for their recorded conditions, not universal browser guarantees.
