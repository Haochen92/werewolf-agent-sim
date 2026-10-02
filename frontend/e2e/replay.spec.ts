/**
 * The replay page on the new stage, against the bundled fixture game served as if the API
 * sent it (the API is not running for these): the first beat, two chapter jumps, the transport
 * band beside the open drawer, the X-ray's file on a day-3 speech (turned on by the strip's
 * Reveal), the X-ray's night stop (the hub paused with its notice, a lit card playing that
 * actor's room and coming back, "Back to the night"), a voter's file opened from the wing at the
 * count, the vote's stop with the ballots in, and the strip with Reveal on a small phone. Then tests
 * that are not pictures: played fast, the cursor runs on at twice the pace; the drawer stays
 * where a reader scrolled it; the band fits a small phone on its side. A game over but not yet
 * filed winds its reels until the replay comes; a dropped game says so, an unknown id has none.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page, type Request } from '@playwright/test';

const GAME = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';
const REPLAY = readFileSync(join(__dirname, '../src/stage/fixtures/replay-9369a5c1.json'));

/**
 * Serve the fixture for the API's `GET /replays/{id}` (same-origin `/api` or the dev server's
 * absolute API origin alike). The page itself has the same path: its own load goes through.
 */
async function mockApi(page: Page) {
  await page.route(`**/replays/${GAME}*`, async (route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: {
        'access-control-allow-origin': req.headers()['origin'] ?? '*',
        'access-control-allow-credentials': 'true',
      },
      body: REPLAY,
    });
  });
}

/** Wait until the frame is still: sprites decoded, fonts in, and Next's dev badge hidden. */
async function settle(page: Page) {
  await page.addStyleTag({ content: 'nextjs-portal{display:none!important}' });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [...document.images].map((img) =>
        img.complete ? null : img.decode().catch(() => null),
      ),
    );
  });
}

async function open(page: Page) {
  await mockApi(page);
  await page.goto(`/replays/${GAME}`, { waitUntil: 'networkidle' });
  await expect(page.locator('[data-transport]')).toBeVisible();
  await expect(page.locator('[data-beat-index="0"]')).toBeAttached();
}

const theatre = (page: Page) => page.locator('[data-beat-index]');
const band = (page: Page) => page.locator('[data-transport]');
const reveal = (page: Page) => page.getByRole('button', { name: 'Reveal', exact: true });
/** A seat's card on the wing. */
const card = (page: Page, n: number) =>
  page.locator(`[data-layer="hud"] button[data-seat="${n}"]`);

/** Click the seek bar where beat `i` sits (the bar is the whole list, one step per beat). */
async function seek(page: Page, i: number) {
  const bar = page.getByRole('slider', { name: 'Seek' });
  const n = Number(await bar.getAttribute('aria-valuemax'));
  const box = (await bar.boundingBox())!;
  await page.mouse.click(box.x + (i / (n - 1)) * box.width, box.y + box.height / 2);
  // a beat is under 2 px of the bar: a click can land a beat off, so the keys finish the step
  const at = Number(await theatre(page).getAttribute('data-beat-index'));
  for (let k = at; k < i; k++) await page.keyboard.press('ArrowRight');
  for (let k = at; k > i; k--) await page.keyboard.press('ArrowLeft');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', String(i));
}

test('replay: while the log is on its way the page is the empty platform, then the stage', async ({
  page,
}) => {
  await mockApi(page);
  // hold the log until the picture is taken
  let release = () => {};
  const held = new Promise<void>((r) => (release = r));
  await page.route(`**/replays/${GAME}*`, async (route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    await held;
    await route.fallback();
  });
  await page.goto(`/replays/${GAME}`);
  const still = page.locator('[data-loading="replay"]');
  await expect(still).toBeVisible();
  await expect(still.getByRole('status')).toHaveText('Rewinding the reels…');
  await settle(page);
  await expect(page).toHaveScreenshot('loading-replay.png');
  release();
  await expect(page.locator('[data-transport]')).toBeVisible();
  await expect(still).toHaveCount(0);
});

test('replay: the first beat', async ({ page }) => {
  await open(page);
  await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(9);
  // nothing is said at the deal yet; the way back to the list sits at the strip's left
  await expect(page.locator('[data-drawer]').getByText('Nothing said yet.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Replays' })).toHaveAttribute(
    'href',
    '/replays',
  );
  await settle(page);
  await expect(page).toHaveScreenshot('replay-first-beat.png');
});

test('replay: two chapters on', async ({ page }) => {
  await open(page);
  const next = page.getByRole('button', { name: 'Next chapter' });
  await next.click();
  await next.click();
  // Day 1, then Night 1 (no one is voted out on day 1)
  await expect(theatre(page)).toHaveAttribute('data-beat', 'night.hub');
  await expect(band(page).getByText('Night 1 · Night falls')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-chapter-night-1.png');
});

test('replay: the transport band beside the open drawer', async ({ page }) => {
  await open(page);
  // the fifth speech of day 3 (seat 8, seq 200), its first page, seeked to, so it lands still
  await seek(page, 50);
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  await expect(page.locator('[data-line="say-200"]')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-band-drawer.png', {
    clip: { x: 0, y: 820, width: 1600, height: 80 },
  });
});

test('replay: the X-ray on a day-3 speech, the file in the slot', async ({ page }) => {
  await open(page);
  await seek(page, 50); // seat 8's speech (seq 200), its first page
  // the File tab is the X-ray's pane: greyed until the strip's Reveal turns the X-ray on
  const file = page.getByRole('button', { name: 'File', exact: true });
  await expect(file).toBeDisabled();
  await expect(reveal(page)).toHaveAttribute('aria-pressed', 'false');
  await expect(reveal(page)).toHaveText('Reveal');
  await reveal(page).click();
  await expect(file).toBeEnabled();
  // the switch leaves the pane as it was (the transcript), now with the X-ray's lines
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  await file.click();
  await expect(page.locator('[data-film="file"]')).toBeVisible();
  // the X-ray re-cut the beats; the cursor stayed on the same speech
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
  await expect(reveal(page)).toHaveAttribute('aria-pressed', 'true');
  await expect(reveal(page)).toHaveText('Revealed');
  // the band keeps the transport only: the switch is the strip's
  await expect(band(page).getByRole('button', { name: /X-ray|Reveal/ })).toHaveCount(0);
  await settle(page);
  await expect(page).toHaveScreenshot('replay-xray-film-d3.png');
});

test('replay: the night stops at its hub; a lit card plays that actor’s room and rests there', async ({
  page,
}) => {
  // the room's hold is the page's clock: run on only when asked
  await page.clock.install();
  await open(page);
  await reveal(page).click();
  const next = page.getByRole('button', { name: 'Next chapter' });
  await next.click();
  await next.click();
  // the stop: arrived at, paused, the actors lit, the notice with the ways on
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.hub');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
  // five rooms (the vigilante's held fire is one; the pack's two wolves are one), six seats lit
  await expect(page.getByText('Night 1 · 5 acted.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Watch them all ▶' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'End the night →' })).toBeVisible();
  await expect(page.locator('[data-glow="acted"]')).toHaveCount(6);
  await expect(page.locator('[data-layer="hud"] [data-word="visit"]')).toHaveCount(6);
  await settle(page);
  await expect(page).toHaveScreenshot('replay-night-hub-reveal.png');
  // the investigator's card (lit): its room plays, its file beside it
  await expect(card(page, 4)).toHaveAttribute('aria-label', 'Seat 4’s night');
  await card(page, 4).click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.spoke');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  await expect(page.getByText('In the night · Seat 4')).toBeVisible();
  await page.getByRole('button', { name: 'File', exact: true }).click();
  await expect(page.locator('[data-film="file"]')).toHaveAttribute(
    'data-file-seat',
    'player_4',
  );
  // its last step played (the mark's 4 s), it rests there (no return by itself)
  await page.clock.runFor(4500);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.spoke');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
  await expect(page.getByText('In the night · Seat 4')).toBeVisible();
  // from inside the room, another actor's card goes straight to its room: the vigilante's,
  // who held its fire
  await expect(card(page, 7)).toHaveAttribute('data-word', 'visit');
  await card(page, 7).click();
  await expect(page.getByText('In the night · Seat 7')).toBeVisible();
  await expect(page.getByText('holds its fire.')).toBeVisible();
  await expect(card(page, 4)).toHaveAttribute('data-word', 'seen');
  // "Back to the night": the hub, paused, the rooms seen a steady mark and "Seen"
  await page.getByRole('button', { name: '← Back to the night' }).click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.hub');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
  await expect(card(page, 4)).toHaveAttribute('data-glow', 'visited');
  await expect(card(page, 7)).toHaveAttribute('data-word', 'seen');
  // the file's sheet offers the rooms too: the pack's, from there
  await page.locator('[data-visit="pack"]').click();
  await expect(page.getByText('In the night · The pack')).toBeVisible();
  await page.getByRole('button', { name: '← Back to the night' }).click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.hub');
  await expect(card(page, 8)).toHaveAttribute('data-glow', 'visited');
  // a seat that does not act opens its own file
  await card(page, 5).click();
  await expect(page.locator('[data-film="file"]')).toHaveAttribute(
    'data-file-seat',
    'player_5',
  );
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.hub');
});

test('replay: in an actor’s room the card on the table opens, and the play goes on under it', async ({
  page,
}) => {
  await page.clock.install();
  await open(page);
  await reveal(page).click();
  const next = page.getByRole('button', { name: 'Next chapter' });
  await next.click();
  await next.click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.hub');
  await card(page, 4).click();
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  const at = await theatre(page).getAttribute('data-beat-index');
  // opened while playing: nothing seeks, nothing pauses
  const table = page.getByRole('button', {
    name: 'Seat 4’s card: Investigator. Tap to read',
  });
  await table.click();
  const overlay = page.locator('[data-overlay="card"]');
  await expect(overlay).toBeVisible();
  await expect(overlay.getByText('Seat 4 · tap anywhere to close')).toBeVisible();
  await expect(theatre(page)).toHaveAttribute('data-beat-index', at!);
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  // the room plays out and rests on its last step (the mark's 4 s), the card still open over it
  await page.clock.runFor(4500);
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
  await expect(overlay).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-room-card.png');
  // a tap closes it, as live; the room stays where it is
  await overlay.click();
  await expect(overlay).toHaveCount(0);
  await expect(theatre(page)).toHaveAttribute('data-beat', 'rnight.spoke');
  await expect(page.getByText('In the night · Seat 4')).toBeVisible();
  // stepped on to the next actor's room, open or not, the card is that room's and shut
  await table.click();
  await expect(overlay).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByText('In the night · Seat 2')).toBeVisible();
  await expect(overlay).toHaveCount(0);
});

test('replay: at the count, a voter’s card opens what it voted on', async ({ page }) => {
  test.setTimeout(90_000);
  await open(page);
  await reveal(page).click();
  // on to day 3's vote, then its first chip
  for (let i = 0; i < 12; i++) {
    if ((await band(page).textContent())?.includes('Vote 3')) break;
    await page.keyboard.press(']');
  }
  for (let i = 0; i < 12; i++) {
    if ((await band(page).textContent())?.includes('A chip is counted')) break;
    await page.keyboard.press('ArrowRight');
  }
  await expect(theatre(page)).toHaveAttribute('data-beat', 'vote.chip-counted');
  // the pane is the transcript (or closed); a tap on seat 8 brings its file
  await card(page, 8).click();
  const film = page.locator('[data-film="file"]');
  await expect(film).toHaveAttribute('data-file-seat', 'player_8');
  await page.getByRole('tab', { name: /Lessons/ }).click();
  await expect(film.getByText('Consulted Day 3 · vote')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-vote-voter-file.png');
  // the count's sheet (titled by what it holds) opens a voter's file from its rows too
  await page.getByRole('tab', { name: 'The vote' }).click();
  await page.locator('[data-film="vote"] button', { hasText: 'Seat 5' }).click();
  await expect(film).toHaveAttribute('data-file-seat', 'player_5');
});

test('replay: the vote stops with the ballots in, and counts on', async ({ page }) => {
  test.setTimeout(90_000);
  await open(page);
  await reveal(page).click();
  for (let i = 0; i < 12; i++) {
    if ((await band(page).textContent())?.includes('Vote 3')) break;
    await page.keyboard.press(']');
  }
  // the drop, the lid down (the stop), the count; back a beat lands on the stop at rest
  for (const beat of ['vote.ballots-drop', 'vote.closes', 'vote.count-begins']) {
    await page.keyboard.press('ArrowRight');
    await expect(theatre(page)).toHaveAttribute('data-beat', beat);
  }
  await page.keyboard.press('ArrowLeft');
  await expect(theatre(page)).toHaveAttribute('data-beat', 'vote.closes');
  await expect(page.getByText('7 ballots in.')).toBeVisible();
  await expect(page.getByText('Tap a seat to read what it voted on.')).toBeVisible();
  await expect(card(page, 6)).toHaveAttribute('aria-label', 'Open seat 6’s file');
  await settle(page);
  await expect(page).toHaveScreenshot('replay-vote-stop.png');
  await page.getByRole('button', { name: 'Count the votes ▶' }).click();
  await expect(theatre(page)).toHaveAttribute('data-beat', 'vote.count-begins');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
});

test('replay: the strip fits a small phone with Reveal on', async ({ page }) => {
  test.setTimeout(90_000);
  for (const [w, h] of [
    [667, 375],
    [568, 320],
  ]) {
    await page.setViewportSize({ width: w, height: h });
    await open(page);
    await reveal(page).click();
    // Day 1's vote-less night, then day 2's vote: the ballots drop, with the pill in the row
    for (let i = 0; i < 12; i++) {
      if ((await band(page).textContent())?.includes('Vote 2')) break;
      await page.keyboard.press(']');
    }
    await page.keyboard.press('ArrowRight');
    await expect(theatre(page)).toHaveAttribute('data-beat', 'vote.ballots-drop');
    for (const file of [false, true]) {
      if (file) await page.getByRole('button', { name: 'File', exact: true }).click();
      const dock = (await reveal(page).locator('xpath=..').boundingBox())!;
      expect(dock.x + dock.width).toBeLessThanOrEqual(w);
      // the left row's pieces that share the dock's line end before it
      const left = await page
        .locator('a[href="/replays"]')
        .locator('xpath=..')
        .locator(':scope > *')
        .evaluateAll((els) => els.map((e) => e.getBoundingClientRect().toJSON()));
      for (const b of left)
        if (b.top < dock.y + dock.height && b.bottom > dock.y)
          expect(b.right).toBeLessThanOrEqual(dock.x);
      // nothing in the dock is cut short
      for (const b of await reveal(page).locator('xpath=..').locator('button').all())
        expect(await b.evaluate((el) => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
    }
    if (w === 568) {
      await settle(page);
      await expect(page).toHaveScreenshot('replay-strip-reveal-568.png', {
        clip: { x: 0, y: 0, width: w, height: 60 },
      });
    }
  }
});

test('replay: played fast, the cursor runs on at twice the pace', async ({ page }) => {
  test.setTimeout(60_000);
  await page.clock.install();
  await open(page);
  // one toggle: it says the speed it plays at
  await band(page).getByRole('button', { name: 'Normal' }).click();
  await expect(band(page).getByRole('button', { name: 'Fast' })).toBeVisible();
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  // 20 s at fast reaches the night (beat 6, 15 s of holds, each new hold set at the end of a
  // step); at normal it would still be on day 1's first pass (26 s of holds to beat 5)
  for (let t = 0; t < 40; t++) await page.clock.runFor(500);
  expect(Number(await theatre(page).getAttribute('data-beat-index'))).toBeGreaterThan(5);
});

test('replay: the transcript follows only while the reader is at now', async ({ page }) => {
  await open(page);
  await seek(page, 50);
  const lines = page.locator('[data-drawer] [data-line]').first().locator('xpath=..');
  const back = page.getByRole('button', { name: /Back to now/ });
  await expect(back).toHaveCount(0);
  // the reader scrolls up to read back: the next beat leaves them there, with the pill
  await lines.evaluate((el) => el.scrollTo({ top: 0 }));
  await expect(back).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '51');
  expect(await lines.evaluate((el) => el.scrollTop)).toBe(0);
  // the pill takes them back to the beat's line, and the drawer follows again
  await back.click();
  await expect(back).toHaveCount(0);
  await expect(page.locator('[data-drawer] [data-line="say-200"]')).toBeInViewport();
});

test('replay: the transcript follows again once the reader scrolls to its foot', async ({
  page,
}) => {
  await open(page);
  await seek(page, 50);
  const lines = page.locator('[data-drawer] [data-line]').first().locator('xpath=..');
  const back = page.getByRole('button', { name: /Back to now/ });
  const gap = () =>
    lines.evaluate((el) => el.scrollHeight - el.scrollTop - el.clientHeight);
  await lines.evaluate((el) => el.scrollTo({ top: 0 }));
  await expect(back).toBeVisible();
  // down to the very foot: caught up, it follows on its own and the pill goes
  await lines.evaluate((el) => el.scrollTo({ top: el.scrollHeight }));
  await expect(back).toHaveCount(0);
  // the beats go on: held at the foot, the newest line showing
  for (const i of [49, 50, 51]) {
    await page.keyboard.press('ArrowRight');
    await expect(theatre(page)).toHaveAttribute('data-beat-index', String(i));
    await expect.poll(gap).toBeLessThanOrEqual(4);
    await expect(page.locator('[data-drawer] [data-line]').last()).toBeInViewport();
  }
  await expect(back).toHaveCount(0);
  // scrolled up again, it stops: the next beat leaves the reader where they are
  await lines.evaluate((el) => el.scrollTo({ top: 0 }));
  await expect(back).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '52');
  expect(await lines.evaluate((el) => el.scrollTop)).toBe(0);
});

test('replay: the band fits a small phone on its side', async ({ page }) => {
  await page.setViewportSize({ width: 667, height: 375 });
  await open(page);
  const vw = 667;
  const boxes = await band(page)
    .locator(':scope > *')
    .evaluateAll((els) => els.map((e) => e.getBoundingClientRect().toJSON()));
  // three pieces (the buttons, where we are, the speed), in a row, none past the edge
  expect(boxes).toHaveLength(3);
  for (const b of boxes) {
    expect(b.left).toBeGreaterThanOrEqual(0);
    expect(b.right).toBeLessThanOrEqual(vw);
  }
  for (let i = 1; i < boxes.length; i++)
    expect(boxes[i].left).toBeGreaterThanOrEqual(boxes[i - 1].right - 0.5);
  // the words where we are are not squeezed to nothing
  expect(boxes[1].width).toBeGreaterThan(60);
});

test('replay: a speech holds while the pointer rests on it', async ({ page }) => {
  await page.clock.install();
  await open(page);
  await seek(page, 40); // day 3’s first speech, seat 2: its first page, a 7.3 s hold
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await page.locator('[data-speech]').hover();
  for (let t = 0; t < 20; t++) await page.clock.runFor(1000);
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '40');
  await page.mouse.move(5, 5);
  for (let t = 0; t < 12; t++) await page.clock.runFor(1000);
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '41');
});

test('replay: the keys step, jump chapters and play', async ({ page }) => {
  await open(page);
  await page.keyboard.press('ArrowRight');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '1');
  await page.keyboard.press(']');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '2');
  await page.keyboard.press('ArrowLeft');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '1');
  await page.keyboard.press(' ');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  await page.keyboard.press(' ');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
  // with the play button focused, the space still toggles once, not twice
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  await page.keyboard.press(' ');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
});

/**
 * The replay of a game whose run has not ended: the archive 404s until `filed()` says so, and
 * the game's status answers as `status` (null: a 404, a game nobody knows).
 */
async function mockUnfiled(
  page: Page,
  filed: () => boolean,
  status: Record<string, unknown> | null,
) {
  const headers = (req: Request) => ({
    'access-control-allow-origin': req.headers()['origin'] ?? '*',
    'access-control-allow-credentials': 'true',
  });
  await page.route(`**/replays/${GAME}*`, async (route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    await route.fulfill(
      filed()
        ? {
            status: 200,
            contentType: 'application/json',
            headers: headers(req),
            body: REPLAY,
          }
        : {
            status: 404,
            contentType: 'application/json',
            headers: headers(req),
            body: JSON.stringify({ detail: 'unknown replay' }),
          },
    );
  });
  await page.route(`**/games/${GAME}`, async (route) => {
    const req = route.request();
    if (req.resourceType() === 'document' || req.headers()['rsc']) return route.fallback();
    await route.fulfill({
      status: status ? 200 : 404,
      contentType: 'application/json',
      headers: headers(req),
      body: JSON.stringify(status ?? { detail: 'unknown game' }),
    });
  });
}

const OVER = {
  game_id: GAME,
  state: 'finished',
  server_time: '2026-10-01T10:00:00Z',
  players: [],
  human_players: ['player_7'],
  you: null,
  game_over: true,
  last_seq: 407,
  archived: false,
  winner: null,
  error: null,
};

test('replay: a game over but not yet filed winds its reels, then plays', async ({
  page,
}) => {
  let filed = false;
  await mockUnfiled(page, () => filed, OVER);
  await page.goto(`/replays/${GAME}`);
  const still = page.locator('[data-loading="replay"]');
  await expect(still.getByRole('status')).toHaveText(
    'Winding the reels… come back in a few minutes',
  );
  await expect(page.getByText('No such replay.')).toHaveCount(0);
  // the run ends: the next ask (every five seconds) finds the replay
  filed = true;
  await expect(page.locator('[data-transport]')).toBeVisible({ timeout: 12_000 });
  await expect(still).toHaveCount(0);
});

test('replay: a dropped game says so; an id nobody knows has no replay', async ({
  page,
}) => {
  await mockUnfiled(page, () => false, {
    ...OVER,
    state: 'dropped',
    game_over: false,
    archived: true,
    error: 'nobody came back',
  });
  await page.goto(`/replays/${GAME}`);
  await expect(page.getByText('This game was dropped.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Back to the lobby' })).toHaveAttribute(
    'href',
    '/rooms',
  );
  await page.unrouteAll();
  await mockUnfiled(page, () => false, null);
  await page.goto(`/replays/${GAME}`);
  await expect(page.getByText('No such replay.')).toBeVisible();
});
