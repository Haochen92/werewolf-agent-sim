/**
 * The live game's page on the new stage, against the bundled fixture game served as if the
 * server were streaming it to seat 7 (the API is not running for these). The status poll and
 * the SSE stream are both mocked with `page.route`: the stream is one `text/event-stream` body
 * of `event: game` frames, the seat's entitled events only, with the catch-up boundary set by
 * the status's `last_seq` (at or below it is history, above it is news).
 *
 * Pictures (mid-day catch-up at rest; seat 7's speaking turn with the dock, and with the
 * seat's card opened over it; the curtain after game over), and tests that are not pictures: a
 * new game's deal plays from its first beat; "your card" opens and closes, and stays open as
 * the beats go by; on the speaking turn the dock is three plaques (2026-10-01), Write your line,
 * Send (greyed until there is a line, live as soon as the composer's box holds one) and Pass,
 * the line previewed under the head once written (a picture; a refused line's words under it);
 * all the writing is in the full-screen composer (a picture), where the seat's agent drafts its
 * line (steered or not, and with the seat notebook when "Use my seat notes" is ticked) into the
 * box to be edited, Send sends it, and a line typed by hand sends as it is; on a phone the
 * plaques keep a thumb's size (a picture), a tap on the preview opens the composer and it keeps
 * above the soft keyboard; while the status is on its way the page is the empty platform (a
 * picture). The pace
 * (2026-10-01): a departed game plays its deal and the turns after it from the first beat,
 * however much the log held; a queue of beats plays at its normal holds; Reveal and File wait
 * for the stage's ending.
 * A seat's notes stay open (words, caret, the role list) while the beats and scenes go by, and
 * close when the seat dies (2026-10-01). The curtain waits for the replay to be filed: a plaque
 * until the archive answers for it (a picture), then the link in its place.
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
  /** The archive answers for the game's replay (filed when the run ends); a 404 until then. */
  filed?: boolean;
}

/** Each page's mock, so a wait for the stage can be sized to the stream it is served. */
const mocks = new WeakMap<Page, Mock>();

async function mockApi(page: Page, mock: Mock) {
  mocks.set(page, mock);
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
  await page.route(`**/replays/${GAME}*`, async (route) => {
    if (!isApi(route)) return route.fallback();
    await route.fulfill({
      status: mock.filed ? 200 : 404,
      contentType: 'application/json',
      headers: cors(route.request()),
      body: JSON.stringify(mock.filed ? REPLAY : { detail: 'unknown replay' }),
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

/**
 * Wait until the frame is still: sprites decoded, fonts in, the dev badge and the dropped-stream
 * note hidden. Only pictures in the window are waited for: a lazy picture scrolled out of view
 * (the transcript's chips far up the drawer, which now stays mounted from scene to scene) never
 * loads, and its `decode()` never settles.
 */
async function settle(page: Page) {
  await page.addStyleTag({
    content:
      'nextjs-portal{display:none!important} [data-connection]{display:none!important}',
  });
  await page.evaluate(async () => {
    await document.fonts.ready;
    const inWindow = (img: HTMLImageElement) => {
      const r = img.getBoundingClientRect();
      return r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
    };
    await Promise.all(
      [...document.images].map((img) =>
        img.complete || !inWindow(img) ? null : img.decode().catch(() => null),
      ),
    );
  });
}

const theatre = (page: Page) => page.locator('[data-beat-index]');

/**
 * The stage on `beat` once the page has read its stream. The page reads the frames back to back,
 * a render each (about 85 ms a frame in the dev build alone, more under the suite's three
 * workers), and answers nothing, not even a read of an attribute, until the last is in: the
 * default five seconds is less than day 3's 47-frame catch-up under load, and thirty less than
 * game over's 406. So the wait is sized to the stream: ten seconds and 200 ms a frame.
 */
const foldTime = (page: Page) => 10_000 + (mocks.get(page)?.stream.length ?? 0) * 200;
async function landsOn(page: Page, beat: string | RegExp) {
  await expect(theatre(page)).toHaveAttribute('data-beat', beat, { timeout: foldTime(page) });
}

/**
 * The waiting room's clock, taken from the page while the platform stands idle. A flowing clock
 * carried the curtain's short phases (1.2 s falling, 1 s lifting) past while a page under three
 * workers was busy reading the deal's frames; paused, each phase waits for the test. (Paused
 * later, in the departure, the pause itself landed in the past.)
 */
async function pausePlatform(page: Page) {
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(now + 1000);
}

/**
 * Run the paused clock on in 100 ms steps until the platform reads `phase`, for at most `ms`.
 * Steps, not one run: the status poll's news travels on a timer after its answer comes, which
 * the next step fires.
 */
async function stepsTo(page: Page, phase: string, ms: number) {
  for (let ran = 0; ran < ms; ran += 100) {
    if ((await theatre(page).getAttribute('data-platform')) === phase) break;
    await page.clock.runFor(100);
  }
  await expect(theatre(page)).toHaveAttribute('data-platform', phase);
}

/**
 * Hold the stream back until the page's clock is paused, so every hold after it is the test's
 * to run: until then the installed clock flows with real time, and a page load can outlast a
 * hold. Returns the release, which waits for the stream to be asked for (the status is in by
 * then: its query's news travels on a timer, which a paused clock would keep), pauses the clock
 * and lets the stream through.
 */
async function pausedStream(page: Page) {
  let release = () => {};
  let asked = () => {};
  const held = new Promise<void>((r) => (release = r));
  const requested = new Promise<void>((r) => (asked = r));
  await page.route(`**/games/${GAME}/events*`, async (route) => {
    asked();
    await held;
    await route.fallback();
  });
  return async () => {
    await requested;
    const now = await page.evaluate(() => Date.now());
    await page.clock.pauseAt(now + 500);
    release();
  };
}

/**
 * The stage plays these beats in turn, each for its whole hold: the paused clock runs on in
 * 200 ms steps until the beat moves on, and the time that took is its hold, give or take a step
 * or two (a timer set mid-step, a render read a step late). Fast would be half. The first beat
 * must have just come on.
 */
async function holdsEach(page: Page, steps: readonly (readonly [string, number])[]) {
  for (const [id, hold] of steps) {
    await expect(theatre(page)).toHaveAttribute('data-beat', id);
    await expect(theatre(page)).toHaveAttribute('data-holding', 'true');
    const at = await theatre(page).getAttribute('data-beat-index');
    let ran = 0;
    while (ran < hold + 2000) {
      await page.clock.runFor(200);
      ran += 200;
      if ((await theatre(page).getAttribute('data-beat-index')) !== at) break;
    }
    expect(ran, `${id}'s hold`).toBeGreaterThanOrEqual(hold - 400);
    expect(ran, `${id}'s hold`).toBeLessThanOrEqual(hold + 600);
  }
}

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

/**
 * Open the full-screen composer from the dock's brass plaque ("Write your line", or "Edit your
 * line" once there is one), where all the writing is done.
 */
async function openComposer(page: Page) {
  await page
    .locator('[data-dock="discuss"]')
    .getByRole('button', { name: /^(Write|Edit) your line$/ })
    .click();
  const composer = page.locator('[data-composer]');
  await expect(composer).toBeVisible();
  return composer;
}

test('live: a refresh mid-day lands still on the latest beat', async ({ page }) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the fifth speech of day 3 (seat 8, seq 200), at rest: nothing played to get here
  await landsOn(page, 'day.speech');
  await expect(page.locator('[data-line="say-200"]')).toBeVisible();
  await expect(theatre(page)).toHaveAttribute('data-holding', 'false');
  // Reveal is locked until the game ends
  const reveal = page.getByRole('button', { name: 'Reveal', exact: true });
  await expect(reveal).toBeDisabled();
  await expect(reveal).toHaveAttribute('aria-pressed', 'false');
  await expect(reveal).toHaveAttribute('title', 'Revealed after the game');
  await settle(page);
  await expect(page).toHaveScreenshot('live-catch-up-d3.png');
});

test('live: while the status is on its way the page is the empty platform, then the stage', async ({
  page,
}) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  // hold the status poll until the picture is taken
  let release = () => {};
  const held = new Promise<void>((r) => (release = r));
  await page.route(`**/games/${GAME}`, async (route) => {
    if (!isApi(route)) return route.fallback();
    await held;
    await route.fallback();
  });
  await page.goto(`/games/${GAME}`);
  const still = page.locator('[data-loading="game"]');
  await expect(still).toBeVisible();
  await expect(still.getByRole('status')).toHaveText('Boarding…');
  // nobody on it: no people, no chips, no plates, no ledge buttons
  await expect(still.locator('[data-aboard], [data-tag], [data-ledge]')).toHaveCount(0);
  await expect(still.locator('[data-layer="hud"] img')).toHaveCount(0);
  await settle(page);
  await expect(page).toHaveScreenshot('loading-game.png');
  release();
  await landsOn(page, 'day.speech');
  await expect(still).toHaveCount(0);
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
  await page.clock.runFor(6100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.cards-dealt');
  await page.clock.runFor(6100);
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
  await pausePlatform(page);

  // the host departs: the next poll finds the game running, its deal already in the log
  mock.status = status(12);
  mock.stream = upTo(12);
  await stepsTo(page, 'departing', 6000);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'station.departing');
  await stepsTo(page, 'closing', 7600); // the people board, the train pulls out
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

test('live: a departed game plays its deal and the turns after it, however much the log held', async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.clock.install({ time: T0 });
  await page.addInitScript((game) => localStorage.setItem(`seat_${game}`, 'tok-7'), GAME);
  const mock: Mock = {
    status: status(0, {
      state: 'waiting',
      players: ['mira'],
      host: 'mira',
      name: 'Solo',
      locked: false,
      human_players: [],
      you: null,
    }),
    stream: [],
  };
  await mockApi(page, mock);
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-platform', 'waiting');
  await pausePlatform(page);

  // a solo game: by the time the train has left, the agents have taken day 1's first turns
  const said = (seq: number, player: string): WireEvent => ({
    seq,
    day: 1,
    type: 'speech',
    player,
    channel_seq: seq,
    message: 'Nothing to go on yet; I will watch the vote.',
  });
  const turn = (seq: number) => ALL.find((e) => e.seq === seq)!;
  mock.status = status(24);
  mock.stream = [
    ...upTo(12),
    turn(13),
    said(14, 'player_1'),
    turn(18),
    said(19, 'player_5'),
    turn(23),
    said(24, 'player_4'),
  ];
  expect(mock.stream.filter((e) => e.type === 'turn_started')).toHaveLength(3);
  await stepsTo(page, 'departing', 6000);
  await stepsTo(page, 'closing', 7600);
  await page.clock.runFor(1300);
  // the curtain is down: the deal's first beat, not the latest turn
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');
  await expect(theatre(page)).toHaveAttribute('data-holding', 'true');
  await page.clock.runFor(1100);
  await expect(theatre(page)).toHaveAttribute('data-platform', 'off');
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');
  // from here the clock is the test's: the rest of the table's hold, then each beat in turn
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(now + 50);
  for (let t = 0; t < 40; t++) {
    if ((await theatre(page).getAttribute('data-beat')) === 'deal.cards-dealt') break;
    await page.clock.runFor(200);
  }
  await holdsEach(page, [
    ['deal.cards-dealt', 6000],
    ['deal.your-card', 8000],
    ['deal.day-begins', 6000],
    ['day.turn-thinking', 2000],
    ['day.speech', 5000],
    ['day.turn-thinking', 2000],
    ['day.speech', 5000],
    ['day.turn-thinking', 2000],
  ]);
  // the last line, the latest beat: it plays, and the stage rests there
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
  await expect(theatre(page)).toHaveAttribute('data-holding', 'true');
  await expect(page.locator('[data-line="say-24"]')).toBeVisible();
});

test('live: a queue of beats plays at its normal holds, one after another', async ({
  page,
}) => {
  test.setTimeout(60_000);
  await page.clock.install({ time: T0 });
  // a refresh at day 2's vote: the ballots, the count and the verdict come as news behind it,
  // fourteen beats queued (they drained at half their holds until 2026-10-01)
  await mockApi(page, { status: status(81), stream: upTo(119) });
  const go = await pausedStream(page);
  await page.goto(`/games/${GAME}`);
  await expect(theatre(page)).toBeAttached();
  await go();
  await holdsEach(page, [
    ['vote.ballots-drop', 2500],
    ['vote.closes', 2500],
    ['vote.count-begins', 2000],
    ['vote.chip-counted', 2500],
    ['vote.chip-counted', 2500],
    ['vote.chip-counted', 2500],
  ]);
});

test('live: game over in the night keeps Reveal and File shut until the stage reaches the ending', async ({
  page,
}) => {
  test.setTimeout(150_000); // the stream's fold (landsOn), then the night and the ending
  await page.clock.install({ time: T0 });
  const over = ALL.find((e) => e.type === 'game_over')!;
  const backlog = ALL.filter((e) => e.seq < over.seq && !seen(e));
  // the stage on day 4's lynch; night 4, its morning and game over arrive as news
  await mockApi(page, { status: status(386), stream: [...upTo(405), over, ...backlog] });
  const go = await pausedStream(page);
  await page.goto(`/games/${GAME}`);
  await expect(theatre(page)).toBeAttached();
  await go();
  // four hundred frames, a render each, in a dev build: give them time
  await landsOn(page, 'night.hub');
  const reveal = page.getByRole('button', { name: 'Reveal', exact: true });
  const file = page.getByRole('button', { name: 'File', exact: true });
  // the log holds the game's end, the stage is still in the night: nothing unlocks
  const before: string[] = [];
  for (let t = 0; t < 60; t++) {
    const beat = (await theatre(page).getAttribute('data-beat'))!;
    if (beat.startsWith('over.')) break;
    if (!before.includes(beat)) before.push(beat);
    await expect(reveal).toHaveAttribute('data-reveal', 'locked');
    await expect(file).toBeDisabled();
    await page.clock.runFor(1000);
  }
  expect(before).toEqual(expect.arrayContaining(['night.hub', 'morning.shutter-down']));
  // the ending: Reveal is on and the File tab opens, for good
  await expect(theatre(page)).toHaveAttribute('data-beat', 'over.where-it-ended');
  await expect(reveal).toHaveAttribute('data-reveal', 'on');
  await expect(file).toBeEnabled();
  for (let t = 0; t < 30; t++) {
    if ((await theatre(page).getAttribute('data-beat')) === 'over.verdict') break;
    await page.clock.runFor(1000);
  }
  await expect(theatre(page)).toHaveAttribute('data-beat', 'over.verdict');
  await expect(reveal).toHaveAttribute('data-reveal', 'on');
  await expect(file).toBeEnabled();
});

test('live: seat 7’s turn to speak, the dock at the foot', async ({ page }) => {
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  await expect(theatre(page)).toHaveAttribute('data-open-prompt', '201');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // three plaques and no boxes (2026-10-01): Send greyed until there is a line
  await expect(dock.getByRole('textbox')).toHaveCount(0);
  await expect(dock.getByRole('button', { name: 'Write your line' })).toBeEnabled();
  await expect(dock.getByRole('button', { name: 'Send', exact: true })).toBeDisabled();
  await expect(dock.getByRole('button', { name: 'Pass', exact: true })).toBeEnabled();
  // the drawer stops at the rail so the dock keeps the whole band; closed, the room is bench 72's
  await expect(page.locator('[data-drawer]')).toHaveAttribute('data-drawer', 'rail');
  await page.getByRole('button', { name: 'Transcript', exact: true }).click();
  await expect(page.locator('[data-drawer]')).toHaveCount(0);
  // stop the clock a few seconds in, then let the puppet’s rise and the dock’s fade-in finish
  // (the count reads off the page’s load time: 1:4x or 1:5x; the golden’s tolerance takes it)
  // (a slow first compile can take the page past ten seconds: then pause where it is; the
  // clock keeps running between the read and the pause, so leave it a wide margin — under a
  // parallel run 100 ms was not enough and the pause landed in the past)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 1500));
  await page.clock.runFor(3000);
  await expect(dock.getByText(/^1:[3-5]\d$/)).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('live-your-turn-d3.png');
});

test('live: “your card” opens the seat’s card over the stage; a tap or Esc closes it', async ({
  page,
}) => {
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  // as the turn's golden: stop the clock a few seconds in (a wide margin: see above)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 3000));
  const card = page.locator('[data-overlay="card"]');
  const yours = page.getByRole('button', { name: 'Your card: Vigilante' });
  await yours.click();
  await expect(card.getByRole('dialog', { name: 'Vigilante' })).toBeVisible();
  // let the dock and the card settle
  await page.clock.runFor(3000);
  await settle(page);
  await expect(page).toHaveScreenshot('live-your-card-d3.png');
  // a tap anywhere closes it; so does Esc
  await page.mouse.click(1400, 450);
  await expect(card).toHaveCount(0);
  await yours.click();
  await expect(card).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(card).toHaveCount(0);
});

test('live: the card stays open while the beats go by', async ({ page }) => {
  await page.clock.install({ time: T0 });
  // a new game's deal, played from its first beat: seat 7's card is the third
  await mockApi(page, { status: status(12), stream: upTo(12) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.table-seated');
  await page.clock.runFor(6100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.cards-dealt');
  await page.clock.runFor(6100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.your-card');
  await page.getByRole('button', { name: 'Your card: Vigilante' }).click();
  const card = page.locator('[data-overlay="card"]');
  await expect(card).toBeVisible();
  // the deal plays on under it, into the day: the card is still open
  await page.clock.runFor(8100);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'deal.day-begins');
  await expect(card).toBeVisible();
});

test('live: a steered draft lands in the composer’s box; the dock’s Send sends the line', async ({
  page,
}) => {
  const posted: Mock['posted'] = [];
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
    draft: { draft: 'Seat 8 keeps dodging the question.', drafts_left: 2, deadline: null },
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // one flow: no hand-over on the speaking turn (the agent speaks only when the clock runs out)
  await expect(dock.getByRole('button', { name: /agent/i })).toHaveCount(0);
  // the dock holds no boxes: the steer, Draft and the line are the composer's
  await expect(dock.getByRole('textbox')).toHaveCount(0);
  const composer = await openComposer(page);
  await expect(composer.getByText('3 drafts left')).toBeVisible();
  // an empty notebook: no box to tick
  await expect(composer.getByLabel('Use my seat notes')).toHaveCount(0);
  await composer.getByLabel('Steer your agent').fill('8 dodging');
  await composer.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(composer.getByLabel('Your line')).toHaveValue(
    'Seat 8 keeps dodging the question.',
  );
  await expect(composer.getByText('2 drafts left')).toBeVisible();
  // the draft came back with no deadline (a solo game's): no count
  await expect(composer.getByText(/\d:\d\d/)).toHaveCount(0);
  // closed, the dock previews the line, and its own Send sends it
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  await expect(dock.locator('[data-dock-preview]')).toContainText(
    'Seat 8 keeps dodging the question.',
  );
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
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  await expect(dock.getByRole('button', { name: 'Send' })).toBeDisabled();
  const composer = await openComposer(page);
  const line = composer.getByLabel('Your line');
  await expect(composer.getByRole('button', { name: 'Send' })).toBeDisabled();
  await composer.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(line).toHaveValue('Why did seat 5 vote before anyone spoke?');
  await line.fill('Why did seat 5 vote so fast?');
  await composer.getByRole('button', { name: 'Send' }).click();
  await expect(dock).toBeHidden();
  expect(posted).toEqual([
    { path: 'draft', body: { notes: '', current: '' } },
    { path: 'turns', body: { message: 'Why did seat 5 vote so fast?' } },
  ]);
});

test('live: the seat notes go with a draft while ticked; Redraft this revises the line', async ({
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
  const composer = await openComposer(page);
  const share = composer.getByLabel('Use my seat notes');
  await expect(share).toBeChecked(); // ticked to start
  await composer.getByRole('button', { name: 'Draft', exact: true }).click();
  await expect(composer.getByLabel('Your line')).toHaveValue(
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
  await composer.getByLabel('Steer your agent').fill('softer');
  await composer.getByRole('button', { name: 'Redraft this', exact: true }).click();
  await expect(composer.getByLabel('Your line')).toHaveValue(
    'Seat 5, why so quick on the slip?',
  );
  await expect(composer.getByText('1 draft left')).toBeVisible();
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

test('live: a line typed by hand in the composer sends as it is, no draft asked for', async ({
  page,
}) => {
  const posted: Mock['posted'] = [];
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  const composer = await openComposer(page);
  await composer.getByLabel('Your line').fill('I trust seat 4 today.');
  // Ctrl/⌘+Enter sends from the composer
  await composer.getByLabel('Your line').press('Control+Enter');
  await expect(composer).toHaveCount(0);
  await expect(dock).toBeHidden();
  expect(posted).toEqual([{ path: 'turns', body: { message: 'I trust seat 4 today.' } }]);
});

test('live: a long line counts near the cap in the composer and stops at 700; a pending draft says it is working', async ({
  page,
}) => {
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  // a draft that never comes back, so the button stays on its words
  await page.unroute(`**/games/${GAME}/draft`);
  await page.route(`**/games/${GAME}/draft`, async (route) => {
    const req = route.request();
    if (req.method() === 'OPTIONS')
      return route.fulfill({ status: 204, headers: cors(req) });
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  const composer = await openComposer(page);
  const box = composer.getByLabel('Your line');
  const count = composer.locator('[data-line-count]');
  await box.fill('a'.repeat(599));
  await expect(count).toHaveCount(0);
  await box.press('b');
  await expect(count).toHaveText('600 / 700');
  // typing stops at the cap
  await page.keyboard.insertText('c'.repeat(110));
  await expect(box).toHaveValue(/^a{599}bc{100}$/);
  await expect(count).toHaveText('700 / 700');
  await composer.getByRole('button', { name: 'Redraft this', exact: true }).click();
  // the newest word (the one fading out stays in the page while it goes)
  const words = composer.locator('[data-draft-word]').last();
  await expect(words).toHaveText('Drafting…');
  await expect(words).toHaveText('Weighing the table…', { timeout: 4000 });
  await expect(words).toHaveText('Finding the words…', { timeout: 4000 });
});

test('live: the brass plaque opens the full-screen composer, which keeps the line when closed', async ({
  page,
}) => {
  test.setTimeout(90_000);
  const posted: Mock['posted'] = [];
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
  });
  // a draft held until the button has turned through its words
  let release = () => {};
  const held = new Promise<void>((r) => (release = r));
  await page.unroute(`**/games/${GAME}/draft`);
  await page.route(`**/games/${GAME}/draft`, async (route) => {
    const req = route.request();
    if (req.method() === 'OPTIONS')
      return route.fulfill({ status: 204, headers: cors(req) });
    posted.push({ path: 'draft', body: req.postDataJSON() });
    await held;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: cors(req),
      body: JSON.stringify({
        draft: 'Seat 8 keeps dodging the question.',
        drafts_left: 2,
        deadline: new Date(T0 + 120_000).toISOString(),
      }),
    });
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // as the turn's golden: stop the clock a few seconds in (a wide margin: see above)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 1500));
  await page.clock.runFor(3000);
  const composer = await openComposer(page);
  const big = composer.getByLabel('Your line');
  await expect(big).toBeFocused();
  await expect(composer.getByRole('button', { name: 'Draft', exact: true })).toBeVisible();
  await page.keyboard.type('I trust seat 4 today, and');
  // closed, the line stays; Edit your line opens it again with the caret at its end, so the
  // writing goes on where it was
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  await expect(dock.locator('[data-dock-preview]')).toContainText(
    'I trust seat 4 today, and',
  );
  await dock.getByRole('button', { name: 'Edit your line' }).click();
  await expect(big).toHaveValue('I trust seat 4 today, and');
  await expect(big).toBeFocused();
  await page.keyboard.type(' not seat 5.');
  await expect(big).toHaveValue('I trust seat 4 today, and not seat 5.');
  // with text in the box the one button revises it
  await expect(
    composer.getByRole('button', { name: 'Redraft this', exact: true }),
  ).toBeVisible();
  await expect(composer.locator('[data-word-count]')).toHaveText('9 words');
  await expect(composer.locator('[data-composer-clock]')).toHaveText(/^1:[3-5]\d$/);
  await expect(composer.locator('[data-line-count]')).toHaveCount(0);
  await expect(composer.getByText('3 drafts left')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('composer-day.png');

  // near the cap the count comes, as in the box
  await big.fill('ab '.repeat(204));
  await expect(composer.locator('[data-line-count]')).toHaveText('612 / 700');
  await expect(composer.locator('[data-word-count]')).toHaveText('204 words');
  await big.fill('I trust seat 4 today.');

  // Draft: the same button, its words turning while the draft is on its way
  await composer.getByLabel('Steer your agent').fill('8 dodging');
  await composer.getByRole('button', { name: 'Redraft this', exact: true }).click();
  const words = composer.locator('[data-draft-word]').last();
  await expect(words).toHaveText('Drafting…');
  await page.clock.runFor(1700);
  await expect(words).toHaveText('Weighing the table…');
  release();
  await expect(big).toHaveValue('Seat 8 keeps dodging the question.');
  await expect(composer.getByText('2 drafts left')).toBeVisible();

  // closed (Esc), the dock previews the drafted line; the X closes too
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  await expect(dock.locator('[data-dock-preview]')).toContainText(
    'Seat 8 keeps dodging the question.',
  );
  await dock.getByRole('button', { name: 'Edit your line' }).click();
  await composer.getByRole('button', { name: 'Close', exact: true }).click();
  await expect(composer).toHaveCount(0);

  // Send from the composer posts what the dock's Send would
  await dock.getByRole('button', { name: 'Edit your line' }).click();
  await composer.getByRole('button', { name: 'Send' }).click();
  await expect(composer).toHaveCount(0);
  await expect(dock).toBeHidden();
  expect(posted).toEqual([
    { path: 'draft', body: { notes: '8 dodging', current: 'I trust seat 4 today.' } },
    { path: 'turns', body: { message: 'Seat 8 keeps dodging the question.' } },
  ]);
});

test('live: the dock’s plaques: Send waits for a line and is live once the composer holds one; the dock previews it, and a refused line says why under it', async ({
  page,
}) => {
  const posted: Mock['posted'] = [];
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
    posted,
  });
  // the engine refuses the line, in its own words
  await page.unroute(`**/games/${GAME}/turns`);
  await page.route(`**/games/${GAME}/turns`, async (route) => {
    const req = route.request();
    if (req.method() === 'OPTIONS')
      return route.fulfill({ status: 204, headers: cors(req) });
    posted.push({ path: 'turns', body: req.postDataJSON() });
    await route.fulfill({
      status: 422,
      contentType: 'application/json',
      headers: cors(req),
      body: JSON.stringify({ detail: 'That line names a seat that is not at the table.' }),
    });
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // the drawer shut, as in the turn's picture
  await page.getByRole('button', { name: 'Transcript', exact: true }).click();
  await expect(page.locator('[data-drawer]')).toHaveCount(0);
  // as the turn's golden: stop the clock a few seconds in (a wide margin: see above)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 1500));
  await page.clock.runFor(3000);
  // three plaques and no boxes; Send greyed with no line
  const send = dock.getByRole('button', { name: 'Send', exact: true });
  await expect(dock.getByRole('button', { name: 'Write your line' })).toBeEnabled();
  await expect(send).toBeDisabled();
  await expect(dock.getByRole('button', { name: 'Pass', exact: true })).toBeEnabled();
  await expect(dock.locator('[data-dock-preview]')).toHaveCount(0);
  // a letter in the composer's box and the dock's Send is live, with the composer still open
  const composer = await openComposer(page);
  await page.keyboard.type('S');
  await expect(send).toBeEnabled();
  await expect(composer).toBeVisible();
  await page.keyboard.press('Backspace');
  await expect(send).toBeDisabled();
  const line =
    'Seat 9 says seat 2 was home all night, but nobody saw the lamp lit after the second bell, and that is the third time seat 9 has vouched for the same seat.';
  await composer.getByLabel('Your line').fill(line);
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  // closed: the line previewed on one row cut with an ellipsis, its words at the end, Send live
  // and the plaque reading Edit your line
  const preview = dock.locator('[data-dock-preview]');
  await expect(preview.locator('[data-preview-words]')).toHaveText('33 words');
  await expect(send).toBeEnabled();
  await expect(dock.getByRole('button', { name: 'Edit your line' })).toBeVisible();
  const shown = await preview
    .locator('span')
    .first()
    .evaluate((el) => ({
      text: el.textContent ?? '',
      clipped: el.scrollWidth > el.clientWidth,
      ellipsis: getComputedStyle(el).textOverflow,
      oneLine:
        el.getBoundingClientRect().height < 2 * parseFloat(getComputedStyle(el).fontSize),
    }));
  expect(shown.ellipsis).toBe('ellipsis');
  expect(shown.oneLine).toBe(true);
  expect(shown.clipped || shown.text.endsWith('…')).toBe(true);
  // on a desktop the preview is only a preview: the plaque is the way in
  await preview.click();
  await expect(composer).toHaveCount(0);
  await settle(page);
  await expect(page).toHaveScreenshot('dock-preview-d3.png');
  // refused: the server's words under the preview, over the plaques; the line stays
  await send.click();
  const error = dock.getByRole('alert');
  await expect(error).toHaveText('That line names a seat that is not at the table.');
  await expect(preview).toContainText('Seat 9 says seat 2');
  const [p, e, w] = await Promise.all(
    [preview, error, dock.getByRole('button', { name: 'Edit your line' })].map(
      async (el) => (await el.boundingBox())!,
    ),
  );
  expect(e.y).toBeGreaterThanOrEqual(p.y + p.height - 0.5);
  expect(w.y).toBeGreaterThanOrEqual(e.y + e.height - 0.5);
  expect(posted).toEqual([{ path: 'turns', body: { message: line } }]);
});

test('live: on a phone a tap on the preview opens the composer, fitted above the soft keyboard', async ({
  page,
}) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 667, height: 375 });
  // the soft keyboard up: the browser says only the top 200 px of the page are visible
  await page.addInitScript(() => {
    const area = Object.assign(new EventTarget(), {
      width: 667,
      height: 200,
      offsetLeft: 0,
      offsetTop: 0,
      pageLeft: 0,
      pageTop: 0,
      scale: 1,
    });
    Object.defineProperty(window, 'visualViewport', { get: () => area });
  });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // no line yet, no preview: the plaque opens the composer
  const preview = dock.locator('[data-dock-preview]');
  await expect(preview).toHaveCount(0);
  const composer = await openComposer(page);
  await page.keyboard.type('Seat 5 was quick.');
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  // the preview is a way back in on a phone, the writing going on where it was
  await expect(preview).toContainText('Seat 5 was quick.');
  await preview.click();
  await expect(composer).toBeVisible();
  const big = composer.getByLabel('Your line');
  await expect(big).toBeFocused();
  await page.keyboard.type(' Too quick.');
  await expect(big).toHaveValue('Seat 5 was quick. Too quick.');
  const send = composer.getByRole('button', { name: 'Send' });
  await expect(send).toBeEnabled();
  const frame = (await composer.boundingBox())!;
  expect(frame.y).toBeGreaterThanOrEqual(0);
  expect(frame.y + frame.height).toBeLessThanOrEqual(200.5);
  for (const el of [big, send]) {
    const b = (await el.boundingBox())!;
    expect(b.height).toBeGreaterThan(16);
    expect(b.y).toBeGreaterThanOrEqual(0);
    expect(b.y + b.height).toBeLessThanOrEqual(200);
  }
  // the box keeps room for more than a line
  expect((await big.boundingBox())!.height).toBeGreaterThanOrEqual(30);
});

test('live: on a phone the three plaques sit in a row under the head, with the drawer shut or open', async ({
  page,
}) => {
  await page.setViewportSize({ width: 667, height: 375 });
  await page.clock.install({ time: T0 });
  await mockApi(page, {
    status: status(200, { pending_seats: [ME], pending_input: true }),
    stream: [...upTo(200), yourTurn(201)],
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await landsOn(page, 'day.your-turn');
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // as the turn's golden: stop the clock a few seconds in (a wide margin: see above)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 1500));
  await page.clock.runFor(3000);
  const plaques = ['Write your line', 'Send', 'Pass'].map((name) =>
    dock.getByRole('button', { name, exact: true }),
  );
  await expect(plaques[1]).toBeDisabled();
  const clock = dock.getByText(/^1:[3-5]\d$/);
  const heading = dock.getByText('Your turn to speak');
  const hint = dock.getByText(/^Nothing is said until you send it\./);
  // each a thumb's size, in one row in order under the head, nothing past the dock
  const fits = async () => {
    const [d, c, t, h, ...ps] = await Promise.all(
      [dock, clock, heading, hint, ...plaques].map(async (el) => (await el.boundingBox())!),
    );
    for (const p of ps) {
      // 44 css px, give or take the stage's scale rounding
      expect(p.height).toBeGreaterThanOrEqual(43.9);
      expect(Math.abs(p.y - ps[0].y)).toBeLessThan(1);
      expect(p.x).toBeGreaterThanOrEqual(d.x);
      expect(p.x + p.width).toBeLessThanOrEqual(d.x + d.width);
      expect(p.y + p.height).toBeLessThanOrEqual(d.y + d.height);
    }
    expect(ps[0].x + ps[0].width).toBeLessThanOrEqual(ps[1].x);
    expect(ps[1].x + ps[1].width).toBeLessThanOrEqual(ps[2].x);
    // the clock at the head's right end, above the row
    expect(c.x + c.width).toBeLessThanOrEqual(d.x + d.width);
    expect(c.y + c.height).toBeLessThanOrEqual(ps[0].y);
    expect(h.y + h.height).toBeLessThanOrEqual(ps[0].y);
    return { t, h };
  };
  await fits();
  await settle(page);
  await expect(page).toHaveScreenshot('dock-plaque-phone.png');
  // the drawer open (the side slot): the dock narrows, the hint drops under the heading and the
  // plaques keep their size
  await page.getByRole('button', { name: 'Transcript', exact: true }).click();
  await expect(page.locator('[data-drawer]')).toBeVisible();
  const { t, h } = await fits();
  expect(h.y).toBeGreaterThanOrEqual(t.y + t.height - 0.5);
  // the composer opens from it
  await plaques[0].click();
  await expect(page.locator('[data-composer]')).toBeVisible();
});

test('live: the strip’s door asks, and Leave goes to the lobby', async ({ page }) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-beat-index', /\d+/);
  await page.getByRole('button', { name: 'Leave the table' }).click();
  const confirm = page.getByRole('alertdialog', { name: 'Leave the table?' });
  await expect(confirm).toBeVisible();
  await confirm.getByRole('button', { name: 'Leave' }).click();
  // the address changes once the lobby's page has come from the dev server: 4.8 s of it under
  // three workers (2026-10-02), past the default five
  await expect(page).toHaveURL(/\/rooms$/, { timeout: 20_000 });
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
    // the run has ended: the replay is filed
    filed: true,
  });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the ending plays beat by beat, each at its normal hold, until the epilogue's sheet waits
  for (let t = 0; t < 120; t++) {
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
  // the game's end is the switch: Reveal is on, with nothing to press
  const reveal = page.getByRole('button', { name: 'Reveal', exact: true });
  await expect(reveal).toHaveAttribute('aria-pressed', 'true');
  await expect(reveal).toHaveText('Revealed');
  await page.clock.runFor(5000);
  await settle(page);
  await expect(page).toHaveScreenshot('live-curtain.png');
});

test('live: a seat’s notes stay open while the beats and scenes go by, until the seat dies', async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.clock.install({ time: T0 });
  // the stage at day 3's vote; the count, the lynch, the night, and the morning that tells
  // seat 5's death, as news
  await mockApi(page, { status: status(244), stream: upTo(280) });
  const go = await pausedStream(page);
  await page.goto(`/games/${GAME}`);
  await expect(theatre(page)).toBeAttached();
  await go();
  await landsOn(page, /^vote\./);
  await page.getByRole('button', { name: 'Seat 5, notes' }).click();
  const editor = page.getByRole('dialog', { name: 'Seat 5' });
  const paper = editor.getByRole('textbox', { name: 'Your notes on seat 5' });
  await expect(paper).toBeFocused();
  await page.keyboard.type('quiet on day 3');
  // the beats go by under it, into the night: still open, the words and the caret kept
  const seen: string[] = [(await theatre(page).getAttribute('data-beat'))!];
  const step = async () => {
    await page.clock.runFor(1000);
    const beat = (await theatre(page).getAttribute('data-beat'))!;
    if (seen.at(-1) !== beat) seen.push(beat);
    return beat;
  };
  while (!(await step()).startsWith('night.')) await expect(editor).toBeVisible();
  expect(seen.length).toBeGreaterThanOrEqual(3);
  await expect(editor).toBeVisible();
  await expect(paper).toBeFocused();
  await page.keyboard.type(', voted 6');
  await expect(paper).toHaveValue('quiet on day 3, voted 6');
  // the guess's listbox, opened, stays open across a beat and still picks
  await editor.getByRole('button', { name: /I think they are/ }).click();
  const list = editor.getByRole('listbox');
  await expect(list).toBeVisible();
  const at = seen.length;
  while (seen.length === at) await step();
  await expect(list).toBeVisible();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(list).toHaveCount(0);
  await expect(editor.locator('[data-seat-guess="5"]')).toContainText('Villager');
  // and the suspect mark, after another beat
  const at2 = seen.length;
  while (seen.length === at2) await step();
  await editor.getByRole('button', { name: 'Mark as suspect' }).click();
  await expect(editor.getByRole('button', { name: 'Marked as suspect' })).toBeVisible();
  // the morning tells seat 5's death: the notes close; what was written is on its card
  for (let t = 0; t < 120 && (await editor.count()) > 0; t++) await step();
  await expect(editor).toHaveCount(0);
  expect(seen.at(-1)).toMatch(/^morning\./);
  expect(seen.some((b) => b.startsWith('night.'))).toBe(true);
  await expect(page.locator('[data-layer="hud"] [data-seat="5"]')).toContainText(
    'quiet on day 3, voted 6',
  );
});

test('live: the curtain waits for the replay to be filed, then the link comes in its place', async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.clock.install({ time: T0 });
  const over = ALL.find((e) => e.type === 'game_over')!;
  const backlog = ALL.filter((e) => e.seq < over.seq && !seen(e));
  // the game is over; its run is not (the lessons are still being written): no replay yet
  const mock: Mock = {
    status: status(405),
    stream: [...upTo(405), over, ...backlog],
    filed: false,
  };
  await mockApi(page, mock);
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  for (let t = 0; t < 120; t++) {
    await page.clock.runFor(500);
    if ((await theatre(page).getAttribute('data-beat')) === 'over.curtain') break;
  }
  await expect(theatre(page)).toHaveAttribute('data-beat', 'over.curtain');
  const plaque = page.getByRole('status').filter({ hasText: 'Winding the reels' });
  await expect(plaque).toHaveText(
    /Winding the reels… come back in a few minutes\s*Your seat’s lessons are being written\./,
  );
  await expect(page.getByRole('link', { name: 'Watch the replay' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Back to the lobby' })).toBeVisible();
  await page.clock.runFor(5000);
  await settle(page);
  await expect(page).toHaveScreenshot('curtain-winding.png');
  // the run ends and the replay is filed: the next ask finds it, and the link comes in
  const lobby = page.getByRole('link', { name: 'Back to the lobby' });
  const before = (await lobby.boundingBox())!;
  const held = (await plaque.boundingBox())!;
  mock.filed = true;
  await page.clock.runFor(5500);
  const replay = page.getByRole('link', { name: 'Watch the replay' });
  await expect(replay).toHaveAttribute('href', `/replays/${GAME}`);
  await expect(plaque).toBeHidden();
  // in the plaque's place, against the lobby's button, which has not moved along the row
  const after = (await lobby.boundingBox())!;
  const link = (await replay.boundingBox())!;
  expect(Math.abs(after.x - before.x)).toBeLessThan(1);
  expect(Math.abs(link.x + link.width - (held.x + held.width))).toBeLessThan(1);
});
