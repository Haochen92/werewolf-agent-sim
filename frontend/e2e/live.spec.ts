/**
 * The live game's page on the new stage, against the bundled fixture game served as if the
 * server were streaming it to seat 7 (the API is not running for these). The status poll and
 * the SSE stream are both mocked with `page.route`: the stream is one `text/event-stream` body
 * of `event: game` frames, the seat's entitled events only, with the catch-up boundary set by
 * the status's `last_seq` (at or below it is history, above it is news).
 *
 * Three pictures (mid-day catch-up at rest; seat 7's speaking turn with the dock; the curtain
 * after game over), and tests that are not pictures: a new game's deal plays from its first
 * beat; on the speaking turn the seat's agent drafts its line (steered or not, and with the
 * seat notebook when "Use my seat notes" is ticked) into the box to be edited, Send sends it,
 * and a line typed by hand sends as it is.
 *
 * The mocked stream ends when its body does, so the browser reads it as a dropped connection;
 * the theatre's "Reconnecting…" note is hidden in the pictures for that reason.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page, type Request, type Route } from '@playwright/test';

const GAME = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';
const ME = 'player_7';
const REPLAY = JSON.parse(
  readFileSync(join(__dirname, '../src/stage/fixtures/replay-9369a5c1.json'), 'utf8'),
) as { events: WireEvent[] };

interface WireEvent {
  seq: number;
  type: string;
  day: number;
  player?: string;
  [k: string]: unknown;
}

// the server's live entitlement for a seat that is not a wolf (server/game/entitlement.py)
const OBSERVER = new Set([
  'roles_assigned',
  'pass_marker',
  'firing_reason',
  'addressed_targets',
  'strategy_update',
  'memory_consulted',
  'memory_extracted',
  'player_reads',
  'day_summary_structured',
  'night_action',
]);
const FACTION = new Set([
  'pack_roster_update',
  'wolf_message',
  'wolf_vote',
  'wolf_kill_decided',
]);
const SEAT = new Set([
  'role_assigned',
  'input_request',
  'investigation_result',
  'vigilante_confirmation',
  'bullets_remaining',
]);
const seen = (e: WireEvent) =>
  !OBSERVER.has(e.type) && !FACTION.has(e.type) && (!SEAT.has(e.type) || e.player === ME);
const ALL = REPLAY.events;
const upTo = (seq: number) => ALL.filter((e) => e.seq <= seq && seen(e));

const T0 = Date.parse('2026-09-25T10:00:00Z');

/** The status poll's answer at the moment the page connects. */
function status(lastSeq: number, over: Record<string, unknown> = {}) {
  return {
    game_id: GAME,
    state: 'running',
    server_time: new Date(T0).toISOString(),
    players: [],
    max_seats: 9,
    name: 'fixture',
    locked: true,
    human_players: [ME],
    you: ME,
    pending_input: false,
    pending_seats: [],
    deadlines: {},
    game_over: false,
    last_seq: lastSeq,
    awaiting_key: false,
    winner: null,
    archived: false,
    error: null,
    ...over,
  };
}

const frame = (e: WireEvent) => `id: ${e.seq}\nevent: game\ndata: ${JSON.stringify(e)}\n\n`;

function cors(req: Request) {
  return {
    'access-control-allow-origin': req.headers()['origin'] ?? '*',
    'access-control-allow-credentials': 'true',
    'access-control-allow-headers': 'content-type',
    'access-control-allow-methods': 'GET, POST, OPTIONS',
  };
}

/** The API's own requests (not the page's document or its RSC fetches, which share the path). */
const isApi = (route: Route) => {
  const req = route.request();
  return req.resourceType() !== 'document' && !req.headers()['rsc'];
};

interface Mock {
  status: Record<string, unknown>;
  stream: WireEvent[];
  /** The bodies POSTed to /turns and /draft, as sent. */
  posted?: { path: string; body: unknown }[];
  draft?: Record<string, unknown>;
}

async function mockApi(page: Page, mock: Mock) {
  await page.route(`**/games/${GAME}`, async (route) => {
    if (!isApi(route)) return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: cors(route.request()),
      body: JSON.stringify(mock.status),
    });
  });
  await page.route(`**/games/${GAME}/events*`, async (route) => {
    // one body: a long retry keeps the browser from asking again while the test runs
    const body = `retry: 3600000\n\n${mock.stream.map(frame).join('')}`;
    await route.fulfill({
      status: 200,
      headers: { ...cors(route.request()), 'content-type': 'text/event-stream' },
      body,
    });
  });
  for (const path of ['turns', 'draft']) {
    await page.route(`**/games/${GAME}/${path}`, async (route) => {
      const req = route.request();
      if (req.method() === 'OPTIONS')
        return route.fulfill({ status: 204, headers: cors(req) });
      mock.posted?.push({ path, body: req.postDataJSON() });
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: cors(req),
        body: JSON.stringify(path === 'draft' ? mock.draft : { accepted: true }),
      });
    });
  }
}

/** Wait until the frame is still: sprites decoded, fonts in, the dev badge and the dropped-stream note hidden. */
async function settle(page: Page) {
  await page.addStyleTag({
    content:
      'nextjs-portal{display:none!important} [data-connection]{display:none!important}',
  });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [...document.images].map((img) =>
        img.complete ? null : img.decode().catch(() => null),
      ),
    );
  });
}

const theatre = (page: Page) => page.locator('[data-beat-index]');

/** Seat 7's discussion turn, asked just after the snapshot: news, with two minutes on the clock. */
const yourTurn = (seq: number): WireEvent => ({
  seq,
  day: 3,
  type: 'input_request',
  player: ME,
  action_kind: 'discuss',
  candidates: [],
  deadline: new Date(T0 + 120_000).toISOString(),
});

test('live: a refresh mid-day lands still on the latest beat', async ({ page }) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the fifth speech of day 3 (seat 8, seq 200), at rest: nothing played to get here
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
  await expect(page.locator('[data-line="say-200"]')).toBeVisible();
  await expect(theatre(page)).toHaveAttribute('data-holding', 'false');
  await settle(page);
  await expect(page).toHaveScreenshot('live-catch-up-d3.png');
});

test('live: a new game’s first connection plays the deal from its first beat', async ({
  page,
}) => {
  await page.clock.install({ time: T0 });
  // connected just after "the day begins": the deal is all history, and no turn yet
  await mockApi(page, { status: status(12), stream: upTo(12) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');
  await expect(theatre(page)).toHaveAttribute('data-holding', 'true');
  // played at normal speed, beat by beat: seat 7's own card comes third
  await page.clock.runFor(3100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.cards-dealt');
  await page.clock.runFor(3100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.your-card');
});

test('live: the waiting room’s platform departs into the deal on the same stage', async ({
  page,
}) => {
  test.setTimeout(60_000);
  await page.clock.install({ time: T0 });
  // a guest who boarded earlier: this device holds the seat's token (the cookie is the mock's)
  await page.addInitScript((game) => localStorage.setItem(`seat_${game}`, 'tok-7'), GAME);
  await page.route(`**/games/${GAME}/rejoin`, (route) =>
    route.request().method() === 'OPTIONS'
      ? route.fulfill({ status: 204, headers: cors(route.request()) })
      : route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: cors(route.request()),
          body: JSON.stringify({ token: 'tok-7' }),
        }),
  );
  const mock: Mock = {
    status: status(0, {
      state: 'waiting',
      players: ['mira', 'kei', 'sol'],
      host: 'mira',
      name: 'Night shift',
      locked: false,
      human_players: [],
      you: null,
    }),
    stream: [],
  };
  await mockApi(page, mock);
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the platform, with the three aboard standing on it, and no page-side lobby card
  await expect(theatre(page)).toHaveAttribute('data-platform', 'waiting');
  await expect(theatre(page)).toHaveAttribute('data-beat', 'station.waiting');
  await expect(page.locator('[data-aboard] img')).toHaveCount(3);
  await expect(page.locator('[data-ledge]')).toContainText(
    '3 of 9 aboard · waiting for the host',
  );
  const stage = await page.locator('[data-layer="paint"]').elementHandle();

  // the host departs: the next poll finds the game running, its deal already in the log
  mock.status = status(12);
  mock.stream = upTo(12);
  await page.clock.runFor(3100);
  await expect(theatre(page)).toHaveAttribute('data-platform', 'departing');
  await expect(theatre(page)).toHaveAttribute('data-beat', 'station.departing');
  await page.clock.runFor(7100); // the people board, the train pulls out
  await expect(theatre(page)).toHaveAttribute('data-platform', 'closing');
  await page.clock.runFor(1300); // the curtain is down: the game reaches the stage behind it
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');
  await expect(theatre(page)).toHaveAttribute('data-platform', 'opening');
  await page.clock.runFor(1100); // the curtain lifts off the deal
  await expect(theatre(page)).toHaveAttribute('data-platform', 'off');
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');

  // one stage throughout: the layer the platform was painted in is the deal's
  expect(await stage!.evaluate((el) => el.isConnected)).toBe(true);
  expect(
    await page
      .locator('[data-layer="paint"]')
      .evaluate((el, before) => el === before, stage),
  ).toBe(true);
  await expect(page.locator('[data-aboard] img')).toHaveCount(0);
  await expect(page.locator('[data-boarding-pass]')).toHaveCount(0);
  await expect(page.getByText('Waiting for the host to start…')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Start game' })).toHaveCount(0);
});

test('live: seat 7’s turn to speak, the dock at the foot', async ({ page }) => {
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.your-turn');
  await expect(theatre(page)).toHaveAttribute('data-open-prompt', '201');
  await expect(page.locator('[data-dock="discuss"]')).toBeVisible();
  // the drawer stops at the rail so the dock keeps the whole band; closed, the room is bench 72's
  await expect(page.locator('[data-drawer]')).toHaveAttribute('data-drawer', 'rail');
  await page.getByRole('button', { name: 'Transcript' }).click();
  await expect(page.locator('[data-drawer]')).toHaveCount(0);
  // stop the clock a few seconds in, then let the puppet’s rise and the dock’s fade-in finish
  // (the count reads off the page’s load time: 1:4x or 1:5x; the golden’s tolerance takes it)
  // (a slow first compile can take the page past ten seconds: then pause where it is)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 100));
  await page.clock.runFor(3000);
  await expect(
    page.locator('[data-dock="discuss"]').getByText(/^1:[3-5]\d$/),
  ).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('live-your-turn-d3.png');
});

test('live: a steered draft lands in the box; Send sends the line', async ({ page }) => {
  const posted: Mock['posted'] = [];
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
    draft: { draft: 'Seat 8 keeps dodging the question.', drafts_left: 2, deadline: null },
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // one flow: no hand-over on the speaking turn (the agent speaks only when the clock runs out)
  await expect(dock.getByRole('button', { name: /agent/i })).toHaveCount(0);
  await expect(dock.getByText('3 drafts left')).toBeVisible();
  // an empty notebook: no box to tick
  await expect(dock.getByLabel('Use my seat notes')).toHaveCount(0);
  await dock.getByLabel('Steer your agent').fill('8 dodging');
  await dock.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(dock.getByLabel('Your line')).toHaveValue(
    'Seat 8 keeps dodging the question.',
  );
  await expect(dock.getByText('2 drafts left')).toBeVisible();
  // the draft came back with no deadline (a solo game's): no count
  await expect(dock.getByText(/\d:\d\d/)).toHaveCount(0);
  await dock.getByRole('button', { name: 'Send' }).click();
  await expect(dock).toBeHidden();
  expect(posted).toEqual([
    { path: 'draft', body: { notes: '8 dodging', current: '' } },
    { path: 'turns', body: { message: 'Seat 8 keeps dodging the question.' } },
  ]);
});

test('live: with no steer the agent drafts its own line, which is edited before Send', async ({
  page,
}) => {
  const posted: Mock['posted'] = [];
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
    draft: {
      draft: 'Why did seat 5 vote before anyone spoke?',
      drafts_left: 2,
      deadline: null,
    },
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  const dock = page.locator('[data-dock="discuss"]');
  const line = dock.getByLabel('Your line');
  await expect(dock).toBeVisible();
  await expect(dock.getByRole('button', { name: 'Send' })).toBeDisabled();
  await dock.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(line).toHaveValue('Why did seat 5 vote before anyone spoke?');
  await line.fill('Why did seat 5 vote so fast?');
  await dock.getByRole('button', { name: 'Send' }).click();
  await expect(dock).toBeHidden();
  expect(posted).toEqual([
    { path: 'draft', body: { notes: '', current: '' } },
    { path: 'turns', body: { message: 'Why did seat 5 vote so fast?' } },
  ]);
});

test('live: the seat notes go with a draft while ticked; Redraft revises the line', async ({
  page,
}) => {
  const posted: Mock['posted'] = [];
  await page.addInitScript(
    (game) =>
      localStorage.setItem(
        `notes_${game}`,
        JSON.stringify({ notes: { 5: 'jumped on the slip fast', 8: 'quiet' }, suspect: 5 }),
      ),
    GAME,
  );
  const mock: Mock = {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
    draft: {
      draft: 'Seat 5 jumped on that slip awfully fast.',
      drafts_left: 2,
      deadline: null,
    },
  };
  await mockApi(page, mock);
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  const dock = page.locator('[data-dock="discuss"]');
  const share = dock.getByLabel('Use my seat notes');
  await expect(share).toBeChecked(); // ticked to start
  await dock.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(dock.getByLabel('Your line')).toHaveValue(
    'Seat 5 jumped on that slip awfully fast.',
  );
  // a line in the box: the same button redrafts, the steer revises it, and unticked the
  // notebook stays on the device
  mock.draft = {
    draft: 'Seat 5, why so quick on the slip?',
    drafts_left: 1,
    deadline: null,
  };
  await share.uncheck();
  await dock.getByLabel('Steer your agent').fill('softer');
  await dock.getByRole('button', { name: 'Redraft', exact: true }).click();
  await expect(dock.getByLabel('Your line')).toHaveValue(
    'Seat 5, why so quick on the slip?',
  );
  await expect(dock.getByText('1 draft left')).toBeVisible();
  expect(posted).toEqual([
    {
      path: 'draft',
      body: {
        notes: '',
        current: '',
        seat_notes: { player_5: 'jumped on the slip fast', player_8: 'quiet' },
        suspect: 'player_5',
      },
    },
    {
      path: 'draft',
      body: { notes: 'softer', current: 'Seat 5 jumped on that slip awfully fast.' },
    },
  ]);
});

test('live: a line typed by hand sends as it is, no draft asked for', async ({ page }) => {
  const posted: Mock['posted'] = [];
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  await dock.getByLabel('Your line').fill('I trust seat 4 today.');
  await dock.getByLabel('Your line').press('Control+Enter');
  await expect(dock).toBeHidden();
  expect(posted).toEqual([{ path: 'turns', body: { message: 'I trust seat 4 today.' } }]);
});

test('live: after game over the ending plays to its curtain', async ({ page }) => {
  test.setTimeout(90_000); // the whole ending plays, a beat at a time
  await page.clock.install({ time: T0 });
  const over = ALL.find((e) => e.type === 'game_over')!;
  const backlog = ALL.filter((e) => e.seq < over.seq && !seen(e));
  const taught = ALL.find((e) => e.type === 'memory_extracted')!;
  await mockApi(page, {
    status: status(405),
    // the morning as history; game over as news, then the withheld backlog and the memory
    stream: [...upTo(405), over, ...backlog, taught],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the ending plays beat by beat (fast: it is queued) until the epilogue's sheet waits
  for (let t = 0; t < 40; t++) {
    await page.clock.runFor(500);
    if ((await theatre(page).getAttribute('data-beat')) === 'over.epilogue') break;
  }
  await expect(theatre(page)).toHaveAttribute('data-beat', 'over.epilogue');
  await page.getByRole('button', { name: 'Close the sheet' }).click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'over.curtain');
  const replay = page.getByRole('link', { name: 'Watch the replay' });
  await expect(replay).toHaveAttribute('href', `/replays/${GAME}`);
  await expect(page.getByRole('link', { name: 'Back to the lobby' })).toHaveAttribute(
    'href',
    '/rooms',
  );
  await page.clock.runFor(5000);
  await settle(page);
  await expect(page).toHaveScreenshot('live-curtain.png');
});
