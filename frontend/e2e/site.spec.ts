/**
 * The site shell (app/(site)/layout.tsx): every site page wears the top nav with the product
 * name and the footer with the GitHub link, and the theatre's routes wear neither. No API is
 * running for these; the pages' own data may fail to load, the chrome must not care.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page, type Route } from '@playwright/test';

const GITHUB = 'https://github.com/Haochen92/werewolf-agent-sim';

for (const path of ['/', '/replays', '/rooms', '/play', '/rooms/new']) {
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

/**
 * The ticket office (`/play`, `/rooms/new`) over a mocked `GET /models`. Whether the key field
 * shows is the house's call: a purse that covers the default model folds it away, a spent purse
 * (the server flips `needs_key`) opens it and holds the ticket until a key is typed.
 */
const menuWithPurse = (remaining: number) => ({
  models: MODELS.models.map((row) => ({
    ...row,
    needs_key: remaining <= 0,
  })),
  house: { enabled: true, games_per_day: 20, remaining, reset_at: '2026-09-27T00:00:00Z' },
});

async function openTicket(page: Page, path: string, remaining: number) {
  await page.route('**/models', api(menuWithPurse(remaining)));
  await page.goto(path, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'The ticket office' })).toBeVisible();
  // the default model is preselected: its display name in the select, the raw id underneath
  await expect(page.getByLabel('Model', { exact: true })).toHaveValue(
    'Gemini 3.5 Flash-Lite',
  );
  await expect(page.getByRole('code')).toHaveText('gemini-3.5-flash-lite');
}

test('ticket: the house pays, so /play asks for no key', async ({ page }) => {
  await openTicket(page, '/play', 3);
  await expect(
    page.getByText('The house pays for this model: 3 of 20 games left today.'),
  ).toBeVisible();
  await expect(page.getByLabel('Your key')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Use my own key instead' })).toBeVisible();
  await expect(page.getByRole('switch', { name: 'Agents’ memory' })).not.toBeChecked();

  // the role cards: one chosen at a time, and the stub says which
  await page.getByRole('button', { name: 'Wolf' }).click();
  await expect(page.getByRole('button', { name: 'Wolf' })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  await expect(page.getByText('Wolf, chosen')).toBeVisible();
});

test('ticket: a spent purse opens the key field and holds the ticket', async ({ page }) => {
  let posted = false;
  await page.route('**/games', async (route) => {
    posted = true;
    await route.abort();
  });
  await openTicket(page, '/play', 0);
  await expect(page.getByText(/The house has funded its 20 games for today/)).toBeVisible();
  const key = page.getByLabel('Your key');
  await expect(key).toBeVisible();

  await page.getByRole('button', { name: 'Start the game' }).click();
  await expect(page.getByText('Paste an API key: the house is not paying')).toBeVisible();
  await expect(key).toBeFocused();
  expect(posted).toBe(false);
});

test('ticket: /rooms/new opens a room and goes to it', async ({ page }) => {
  const ROOM = 'b7d1c0de-0000-4000-8000-00000000abcd';
  let sent: Record<string, unknown> | null = null;
  await page.route('**/rooms', async (route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    const cors = {
      'access-control-allow-origin': req.headers()['origin'] ?? '*',
      'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
    };
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
    sent = req.postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: cors,
      body: JSON.stringify({ game_id: ROOM, host_key: 'hk-1' }),
    });
  });
  await openTicket(page, '/rooms/new', 3);

  await page.getByLabel('Room name').fill('Night shift');
  await expect(page.getByText('Night shift', { exact: true })).toBeVisible(); // the stub
  await page.getByRole('button', { name: 'Open the room' }).click();

  await page.waitForURL(`**/games/${ROOM}`);
  expect(sent).toEqual({
    name: 'Night shift',
    model: 'gemini-3.5-flash-lite',
    api_key: '',
    memory: false,
  });
  expect(await page.evaluate((id) => localStorage.getItem(`host_${id}`), ROOM)).toBe(
    'hk-1',
  );
});

for (const [name, path, viewport] of [
  ['play-1440', '/play', { width: 1440, height: 900 }],
  ['play-390', '/play', { width: 390, height: 844 }],
  ['rooms-new-1440', '/rooms/new', { width: 1440, height: 900 }],
] as const) {
  test(`ticket: ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await openTicket(page, path, 3);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}

/**
 * The departures board (`/rooms`) over a mocked `GET /rooms`: one room boarding, one locked and
 * one full. The clock is pinned so "opened … ago" is the same on every run. Board opens the
 * strip; Join posts the name and goes to the room with the seat token kept on this device.
 */
const NOW = new Date('2026-09-26T12:00:00Z');
const BOARDING = 'a1b2c3d4-0000-4000-8000-000000000001';
const LOCKED = 'a1b2c3d4-0000-4000-8000-000000000002';
const FULL = 'a1b2c3d4-0000-4000-8000-000000000003';
const ROOMS = [
  {
    game_id: BOARDING,
    name: 'Night shift',
    players: ['mira', 'sol', 'ana'],
    host: 'mira',
    max_seats: 9,
    locked: false,
    created_at: '2026-09-26T11:56:00Z',
  },
  {
    game_id: LOCKED,
    name: 'Seminar room B',
    players: ['prof_lee', 'kei'],
    host: 'prof_lee',
    max_seats: 9,
    locked: true,
    created_at: '2026-09-26T11:48:00Z',
  },
  {
    game_id: FULL,
    name: 'Full cast',
    players: ['june', 'oskar', 'tomas', 'ana', 'ivy', 'bo', 'cy', 'dee', 'eli'],
    host: 'june',
    max_seats: 9,
    locked: false,
    created_at: '2026-09-26T11:20:00Z',
  },
];

async function openBoard(page: Page, rooms: unknown[] = ROOMS) {
  await page.clock.setFixedTime(NOW);
  await page.route('**/rooms', api(rooms));
  await page.goto('/rooms', { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'The departures hall' })).toBeVisible();
}

/** `POST /games/{id}/join` answered with `status` and `body`, preflight included. */
async function mockJoin(page: Page, status: number, body: unknown) {
  const sent: { url: string; body: unknown }[] = [];
  await page.route('**/games/*/join', async (route) => {
    const req = route.request();
    const cors = {
      'access-control-allow-origin': req.headers()['origin'] ?? '*',
      'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
    };
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
    sent.push({ url: req.url(), body: req.postDataJSON() });
    await route.fulfill({
      status,
      contentType: 'application/json',
      headers: cors,
      body: JSON.stringify(body),
    });
  });
  return sent;
}

test('rooms: the board says boarding, locked and full, and why', async ({ page }) => {
  await openBoard(page);
  await expect(page.locator('[data-room]')).toHaveCount(3);

  const boarding = page.locator(`[data-room="${BOARDING}"]`);
  await expect(boarding).toHaveAttribute('data-state', 'boarding');
  await expect(boarding).toContainText('BOARDING');
  await expect(boarding).toContainText('Night shift');
  await expect(boarding).toContainText('hosted by mira');
  await expect(boarding).toContainText('opened 4 minutes ago');
  await expect(boarding).toContainText('3 of 9 aboard, 6 places open');
  await expect(boarding.getByRole('button', { name: 'Board' })).toBeEnabled();

  const locked = page.locator(`[data-room="${LOCKED}"]`);
  await expect(locked).toContainText('LOCKED');
  await expect(locked.getByRole('img', { name: 'Locked' })).toBeVisible();
  const lockedButton = locked.getByRole('button', { name: 'Locked' });
  await expect(lockedButton).toBeDisabled();
  await expect(lockedButton).toHaveAccessibleDescription(
    /Locked — ask the host to unlock it\./,
  );

  const full = page.locator(`[data-room="${FULL}"]`);
  await expect(full).toContainText('FULL');
  await expect(full).toContainText('9 of 9 aboard');
  const fullButton = full.getByRole('button', { name: 'Full' });
  await expect(fullButton).toBeDisabled();
  await expect(fullButton).toHaveAccessibleDescription(
    /every place at this table is taken/,
  );

  await expect(page.getByRole('link', { name: /Open a table/ })).toHaveAttribute(
    'href',
    '/rooms/new',
  );
});

test('rooms: Join posts the name and goes to the room', async ({ page }) => {
  const sent = await mockJoin(page, 200, { token: 'seat-tok-1' });
  await openBoard(page);

  const row = page.locator(`[data-room="${BOARDING}"]`);
  await row.getByRole('button', { name: 'Board' }).click();
  await row.getByLabel('Your name on the manifest').fill('sol');
  await row.getByRole('button', { name: 'Join' }).click();

  await page.waitForURL(`**/games/${BOARDING}`);
  expect(sent).toHaveLength(1);
  expect(sent[0].url).toMatch(new RegExp(`/games/${BOARDING}/join$`));
  expect(sent[0].body).toEqual({ name: 'sol' });
  expect(await page.evaluate((id) => localStorage.getItem(`seat_${id}`), BOARDING)).toBe(
    'seat-tok-1',
  );
});

test('rooms: a refused join says the server’s words in the row', async ({ page }) => {
  await mockJoin(page, 409, { detail: 'room is locked — ask the host to unlock it' });
  await openBoard(page);

  const row = page.locator(`[data-room="${BOARDING}"]`);
  await row.getByRole('button', { name: 'Board' }).click();
  await row.getByRole('button', { name: 'Join' }).click();
  await expect(row.getByRole('alert')).toContainText(
    'room is locked — ask the host to unlock it',
  );
  await expect(page).toHaveURL(/\/rooms$/);
});

test('rooms: an empty board offers to open a table', async ({ page }) => {
  await openBoard(page, []);
  await expect(page.getByText('NO DEPARTURES')).toBeVisible();
  await expect(page.getByText('No tables open right now.', { exact: false })).toBeVisible();
  await expect(
    page
      .getByRole('region', { name: 'Departures' })
      .getByRole('link', { name: 'Open a table' }),
  ).toHaveAttribute('href', '/rooms/new');
});

for (const [name, viewport] of [
  ['rooms-1440', { width: 1440, height: 900 }],
  ['rooms-390', { width: 390, height: 844 }],
] as const) {
  test(`rooms: ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await openBoard(page);
    await expect(page.locator('[data-room]')).toHaveCount(3);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}
