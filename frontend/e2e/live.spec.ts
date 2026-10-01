/**
 * The live game's page on the new stage, against the bundled fixture game served as if the
 * server were streaming it to seat 7 (the API is not running for these). The status poll and
 * the SSE stream are both mocked with `page.route`: the stream is one `text/event-stream` body
 * of `event: game` frames, the seat's entitled events only, with the catch-up boundary set by
 * the status's `last_seq` (at or below it is history, above it is news).
 *
 * Four pictures (mid-day catch-up at rest; seat 7's speaking turn with the dock, and with the
 * seat's card opened over it; the curtain after game over), and tests that are not pictures: a
 * new game's deal plays from its first beat; "your card" opens and closes, and stays open as
 * the beats go by; on the speaking turn the seat's agent drafts its line (steered or not, and
 * with the seat notebook when "Use my seat notes" is ticked) into the box to be edited, Send
 * sends it, and a line typed by hand sends as it is; the full-screen composer holds the same
 * line (a picture of it, and on a phone it keeps above the soft keyboard); while the status is
 * on its way the page is the empty platform (a picture). The pace (2026-10-01): a departed
 * game plays its deal and the turns after it from the first beat, however much the log held;
 * a queue of beats plays at its normal holds; Reveal and File wait for the stage's ending.
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

test('live: a refresh mid-day lands still on the latest beat', async ({ page }) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  // the fifth speech of day 3 (seat 8, seq 200), at rest: nothing played to get here
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
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
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
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
  await page.clock.runFor(3100);
  await expect(theatre(page)).toHaveAttribute('data-platform', 'departing');
  await page.clock.runFor(7100);
  await expect(theatre(page)).toHaveAttribute('data-platform', 'closing');
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
  test.setTimeout(90_000);
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
  await expect(theatre(page)).toHaveAttribute('data-beat', 'night.hub', {
    timeout: 30_000,
  });
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
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.your-turn');
  await expect(theatre(page)).toHaveAttribute('data-open-prompt', '201');
  await expect(page.locator('[data-dock="discuss"]')).toBeVisible();
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
  await expect(
    page.locator('[data-dock="discuss"]').getByText(/^1:[3-5]\d$/),
  ).toBeVisible();
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
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.your-turn');
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

test('live: a long line counts near the cap and stops at 700; a pending draft says it is working', async ({
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
  const dock = page.locator('[data-dock="discuss"]');
  const box = dock.getByLabel('Your line');
  const count = dock.locator('[data-line-count]');
  await box.fill('a'.repeat(599));
  await expect(count).toHaveCount(0);
  await box.press('b');
  await expect(count).toHaveText('600 / 700');
  // typing stops at the cap
  await page.keyboard.insertText('c'.repeat(110));
  await expect(box).toHaveValue(/^a{599}bc{100}$/);
  await expect(count).toHaveText('700 / 700');
  await dock.getByRole('button', { name: 'Redraft', exact: true }).click();
  // the newest word (the one fading out stays in the page while it goes)
  const words = dock.locator('[data-draft-word]').last();
  await expect(words).toHaveText('Drafting…');
  await expect(words).toHaveText('Weighing the table…', { timeout: 4000 });
  await expect(words).toHaveText('Finding the words…', { timeout: 4000 });
});

test('live: the keyboard button opens the full-screen composer, the same line as the box', async ({
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
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  // as the turn's golden: stop the clock a few seconds in (a wide margin: see above)
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(Math.max(T0 + 10_000, now + 1500));
  await page.clock.runFor(3000);
  await dock.getByLabel('Your line').fill('I trust seat 4 today, and');
  await dock.getByRole('button', { name: 'Write full screen' }).click();
  const composer = page.locator('[data-composer]');
  await expect(composer).toBeVisible();
  const big = composer.getByLabel('Your line');
  // the same line, the caret at its end: the writing goes on where it was
  await expect(big).toHaveValue('I trust seat 4 today, and');
  await expect(big).toBeFocused();
  await page.keyboard.type(' not seat 5.');
  await expect(dock.getByLabel('Your line')).toHaveValue(
    'I trust seat 4 today, and not seat 5.',
  );
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
  await composer.getByRole('button', { name: 'Redraft', exact: true }).click();
  const words = composer.locator('[data-draft-word]').last();
  await expect(words).toHaveText('Drafting…');
  await page.clock.runFor(1700);
  await expect(words).toHaveText('Weighing the table…');
  release();
  await expect(big).toHaveValue('Seat 8 keeps dodging the question.');
  await expect(composer.getByText('2 drafts left')).toBeVisible();

  // closed (Esc), the line stays in the box; the X closes too
  await page.keyboard.press('Escape');
  await expect(composer).toHaveCount(0);
  await expect(dock.getByLabel('Your line')).toHaveValue(
    'Seat 8 keeps dodging the question.',
  );
  await dock.getByRole('button', { name: 'Write full screen' }).click();
  await composer.getByRole('button', { name: 'Close', exact: true }).click();
  await expect(composer).toHaveCount(0);

  // Send from the composer posts what the box's Send would
  await dock.getByRole('button', { name: 'Write full screen' }).click();
  await composer.getByRole('button', { name: 'Send' }).click();
  await expect(composer).toHaveCount(0);
  await expect(dock).toBeHidden();
  expect(posted).toEqual([
    { path: 'draft', body: { notes: '8 dodging', current: 'I trust seat 4 today.' } },
    { path: 'turns', body: { message: 'Seat 8 keeps dodging the question.' } },
  ]);
});

test('live: on a phone a tap on the box opens the composer, fitted above the soft keyboard', async ({
  page,
}) => {
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
  const dock = page.locator('[data-dock="discuss"]');
  await expect(dock).toBeVisible();
  const small = dock.getByLabel('Your line');
  // the small box is the preview here: it takes no typing of its own
  await expect(small).toHaveAttribute('readonly', '');
  await small.click();
  const composer = page.locator('[data-composer]');
  await expect(composer).toBeVisible();
  const big = composer.getByLabel('Your line');
  await expect(big).toBeFocused();
  await page.keyboard.type('Seat 5 was quick.');
  await expect(small).toHaveValue('Seat 5 was quick.');
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

test('live: the strip’s door asks, and Leave goes to the lobby', async ({ page }) => {
  await mockApi(page, { status: status(200), stream: upTo(200) });
  await page.goto(`/games/${GAME}`, { waitUntil: 'networkidle' });
  await expect(theatre(page)).toHaveAttribute('data-beat-index', /\d+/);
  await page.getByRole('button', { name: 'Leave the table' }).click();
  const confirm = page.getByRole('alertdialog', { name: 'Leave the table?' });
  await expect(confirm).toBeVisible();
  await confirm.getByRole('button', { name: 'Leave' }).click();
  await expect(page).toHaveURL(/\/rooms$/);
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
  await expect(theatre(page)).toHaveAttribute('data-beat', /^vote\./);
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
