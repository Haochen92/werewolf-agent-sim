/**
 * The replay page on the new stage, against the bundled fixture game served as if the API
 * sent it (the API is not running for these): the first beat, two chapter jumps, the transport
 * band beside the open drawer, and the X-ray's file on a day-3 speech. Then tests that are not
 * pictures: played fast, the cursor runs on at twice the pace; the drawer stays where a reader
 * scrolled it; the band fits a small phone on its side.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page } from '@playwright/test';

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
  await seek(page, 48);
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  await expect(page.locator('[data-line="say-200"]')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-band-drawer.png', {
    clip: { x: 0, y: 820, width: 1600, height: 80 },
  });
});

test('replay: the X-ray on a day-3 speech, the file in the slot', async ({ page }) => {
  await open(page);
  await seek(page, 48); // seat 8's speech (seq 200), its first page
  // the File tab is the X-ray's pane: greyed until the band's switch turns the X-ray on
  const file = page.getByRole('button', { name: 'File', exact: true });
  await expect(file).toBeDisabled();
  await band(page).getByRole('button', { name: 'X-ray', exact: true }).click();
  await expect(file).toBeEnabled();
  // the switch leaves the pane as it was (the transcript), now with the X-ray's lines
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  await file.click();
  await expect(page.locator('[data-film="file"]')).toBeVisible();
  // the X-ray re-cut the beats; the cursor stayed on the same speech
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
  await expect(band(page).getByText('X-ray on')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-xray-film-d3.png');
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
  // 16 s at fast reaches the night (beat 6, 10.5 s of holds, each new hold set at the end of a
  // step); at normal it would still be on day 1's passes (17 s of holds to beat 5)
  for (let t = 0; t < 32; t++) await page.clock.runFor(500);
  expect(Number(await theatre(page).getAttribute('data-beat-index'))).toBeGreaterThan(5);
});

test('replay: the transcript follows only while the reader is at now', async ({ page }) => {
  await open(page);
  await seek(page, 48);
  const lines = page.locator('[data-drawer] [data-line]').first().locator('xpath=..');
  const back = page.getByRole('button', { name: /Back to now/ });
  await expect(back).toHaveCount(0);
  // the reader scrolls up to read back: the next beat leaves them there, with the pill
  await lines.evaluate((el) => el.scrollTo({ top: 0 }));
  await expect(back).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '49');
  expect(await lines.evaluate((el) => el.scrollTop)).toBe(0);
  // the pill takes them back to the beat's line, and the drawer follows again
  await back.click();
  await expect(back).toHaveCount(0);
  await expect(page.locator('[data-drawer] [data-line="say-200"]')).toBeInViewport();
});

test('replay: the band fits a small phone on its side', async ({ page }) => {
  await page.setViewportSize({ width: 667, height: 375 });
  await open(page);
  const vw = 667;
  const boxes = await band(page)
    .locator(':scope > *')
    .evaluateAll((els) => els.map((e) => e.getBoundingClientRect().toJSON()));
  // four pieces (the buttons, where we are, the speed, the X-ray), in a row, none past the edge
  expect(boxes).toHaveLength(4);
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
  await seek(page, 38); // day 3's first speech, seat 2: its first page, a 7.3 s hold
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await page.locator('[data-speech]').hover();
  for (let t = 0; t < 20; t++) await page.clock.runFor(1000);
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '38');
  await page.mouse.move(5, 5);
  for (let t = 0; t < 12; t++) await page.clock.runFor(1000);
  await expect(theatre(page)).toHaveAttribute('data-beat-index', '39');
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
