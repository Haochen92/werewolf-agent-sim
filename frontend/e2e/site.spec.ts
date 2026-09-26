/**
 * The site shell (app/(site)/layout.tsx): every site page wears the top nav with the product
 * name and the footer with the GitHub link, and the theatre's routes wear neither. No API is
 * running for these; the pages' own data may fail to load, the chrome must not care.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page, type Route } from '@playwright/test';

const GITHUB = 'https://github.com/Haochen92/werewolf-agent-sim';

for (const path of ['/', '/replays', '/rooms', '/play']) {
  test(`site shell: ${path}`, async ({ page }) => {
    await page.goto(path);
    await expect(page).toHaveTitle(/^Carriage Nine/);

    const nav = page.getByRole('navigation', { name: 'Site' });
    await expect(nav.getByRole('link', { name: 'Carriage Nine' })).toBeVisible();
    for (const door of ['Play', 'Rooms', 'Replays']) {
      await expect(nav.getByRole('link', { name: door, exact: true })).toBeVisible();
    }

    const footer = page.getByRole('contentinfo');
    await expect(footer.getByRole('link', { name: 'GitHub', exact: true })).toHaveAttribute(
      'href',
      GITHUB,
    );
    await expect(footer).toContainText('Liu Haochen');
  });
}

test('the theatre wears no site chrome: /workbench/day', async ({ page }) => {
  await page.goto('/workbench/day?beat=6&animate=0&strip=0', { waitUntil: 'networkidle' });
  // the stage rendered (the speaker's figure is up), and around it there is no nav or footer
  await expect(page.locator('[data-layer="figures"] img')).toHaveCount(1);
  await expect(page.getByRole('navigation', { name: 'Site' })).toHaveCount(0);
  await expect(page.getByText('Carriage Nine', { exact: true })).toHaveCount(0);
  await expect(page.locator(`a[href="${GITHUB}"]`)).toHaveCount(0);
});

/**
 * The archive (`/replays`) over a mocked `GET /replays`: the bundled fixture game's summary plus
 * three invented rows, and a `GET /models` menu for the display names. One of the invented games
 * holds a seat token, so its slate carries the "you played" stamp.
 */
const GAME = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';
const MINE = 'c41e07b2-5a3f-4d1e-9b7a-2f6c8e0d1a34';
const FIXTURE = JSON.parse(
  readFileSync(join(__dirname, '../src/stage/fixtures/replay-9369a5c1.json'), 'utf8'),
) as Record<string, unknown>;
const summary = (over: Record<string, unknown>) => ({
  n_events: 380,
  cast_role_counts: FIXTURE.cast_role_counts,
  ...over,
});
const REPLAYS = [
  // the fixture's own summary fields (its log ends on night 4), then three invented rows
  summary({
    game_id: FIXTURE.game_id,
    finished_at: FIXTURE.finished_at,
    winner: FIXTURE.winner,
    days: FIXTURE.days,
    ended_phase: 'night',
    n_events: FIXTURE.n_events,
    n_humans: FIXTURE.n_humans,
    model: FIXTURE.model,
    memory: FIXTURE.memory,
  }),
  summary({
    game_id: MINE,
    finished_at: '2026-09-24T19:02:11Z',
    winner: 'villagers',
    days: 3,
    ended_phase: 'voting',
    n_humans: 1,
    model: 'gemini-3.6-flash',
    memory: false,
  }),
  summary({
    game_id: '7f2a9d10-8c4b-4e2f-a1d3-6b5e9f0c2d87',
    finished_at: '2026-09-23T11:40:00Z',
    winner: 'serial_killer',
    days: 5,
    ended_phase: 'night',
    n_humans: 3,
    model: 'gemini-3.6-flash',
    memory: false,
  }),
  summary({
    game_id: 'seed-chunk-catalogue',
    finished_at: '2026-08-21T09:15:00Z',
    winner: 'wolves',
    days: 5,
    ended_phase: null,
    n_humans: 0,
    model: '',
    memory: false,
  }),
];
const MODELS = {
  models: [
    {
      model: 'gemini-3.5-flash-lite',
      label: 'Gemini 3.5 Flash-Lite',
      rescue_model: null,
      house_funded: true,
      is_default: true,
      needs_key: false,
    },
    {
      model: 'gemini-3.6-flash',
      label: 'Gemini 3.6 Flash',
      rescue_model: null,
      house_funded: true,
      is_default: false,
      needs_key: false,
    },
  ],
  house: {
    enabled: true,
    games_per_day: 20,
    remaining: 12,
    reset_at: '2026-09-27T00:00:00Z',
  },
};

/** The API's own requests (not the page's document or its RSC fetches, which share the path). */
function api(body: unknown, headers: Record<string, string> = {}) {
  return async (route: Route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: {
        'access-control-allow-origin': req.headers()['origin'] ?? '*',
        'access-control-allow-credentials': 'true',
        'access-control-expose-headers': 'X-Total-Count',
        ...headers,
      },
      body: JSON.stringify(body),
    });
  };
}

async function openArchive(page: Page) {
  await page.addInitScript((id) => localStorage.setItem(`seat_${id}`, 'tok'), MINE);
  await page.route('**/replays*', api(REPLAYS, { 'X-Total-Count': '212' }));
  await page.route('**/models', api(MODELS));
  await page.goto('/replays', { waitUntil: 'networkidle' });
  await expect(page.locator('[data-game]')).toHaveCount(4);
}

/** Fonts in and the visible chips decoded, so the picture is the settled page. */
async function settle(page: Page) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [...document.images].map((img) =>
        img.complete ? img.decode().catch(() => null) : null,
      ),
    );
  });
}

test('archive: slates say the model by name and where the game ended', async ({ page }) => {
  await openArchive(page);
  await expect(page.getByRole('heading', { name: 'The archive' })).toBeVisible();
  await expect(page.getByText('Showing 4 of 212 games')).toBeVisible();

  const fixture = page.locator(`[data-game="${GAME}"]`);
  await expect(fixture).toHaveAttribute('href', `/replays/${GAME}`);
  await expect(fixture).toContainText('Wolves');
  await expect(fixture).toContainText('Gemini 3.5 Flash-Lite');
  await expect(fixture).toContainText('gemini-3.5-flash-lite');
  await expect(fixture).toContainText('Night 4');
  await expect(fixture).toHaveAttribute('aria-label', /ended night 4/);
  await expect(fixture.locator('img')).toHaveCount(9);

  await expect(page.locator(`[data-game="${MINE}"]`)).toContainText('Day 3 vote');
  await expect(page.locator(`[data-game="${MINE}"]`)).toContainText('played');
  await expect(page.locator('[data-game="seed-chunk-catalogue"]')).toContainText(
    'Unrecorded',
  );
});

test('archive: a filter narrows the list, and its chip takes it off', async ({ page }) => {
  await openArchive(page);
  const rail = page.getByRole('complementary', { name: 'Filters' });

  await rail.getByText('The wolves').click();
  await expect(page.locator('[data-game]')).toHaveCount(2);
  await expect(page.getByText('Showing 2 of 212 games')).toBeVisible();

  await rail.getByText('Night', { exact: true }).click();
  await expect(page.locator('[data-game]')).toHaveCount(1);
  await expect(page.locator(`[data-game="${GAME}"]`)).toBeVisible();

  await rail.getByRole('switch', { name: 'Played on this device' }).click();
  await expect(page.getByText('No game matches these filters')).toBeVisible();

  await page.getByRole('button', { name: 'Clear filters' }).click();
  await expect(page.locator('[data-game]')).toHaveCount(4);

  await rail.getByRole('switch', { name: 'Played on this device' }).click();
  await expect(page.locator('[data-game]')).toHaveCount(1);
  await page.getByRole('button', { name: /On this device/ }).click();
  await expect(page.locator('[data-game]')).toHaveCount(4);
});

for (const [name, viewport] of [
  ['replays-1440', { width: 1440, height: 900 }],
  ['replays-390', { width: 390, height: 844 }],
] as const) {
  test(`archive: ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await openArchive(page);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}
