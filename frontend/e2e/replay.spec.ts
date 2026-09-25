/**
 * The replay page on the new stage, against the bundled fixture game served as if the API
 * sent it (the API is not running for these): the first beat, two chapter jumps, the transport
 * band beside the open drawer, and the X-ray's film on a day-3 speech. Then one test that is
 * not a picture: played at "skip", the cursor runs well into the game within a few seconds.
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
  // the fifth speech of day 3 (seat 8, seq 200), seeked to, so it lands still
  await seek(page, 44);
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  await expect(page.locator('[data-line="say-200"]')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-band-drawer.png', {
    clip: { x: 0, y: 820, width: 1600, height: 80 },
  });
});

test('replay: the X-ray on a day-3 speech, the film in the slot', async ({ page }) => {
  await open(page);
  await seek(page, 44);
  await page.getByRole('button', { name: 'X-ray', exact: true }).click();
  await expect(page.locator('[data-film="inside"]')).toBeVisible();
  // the X-ray re-cut the beats; the cursor stayed on the same speech
  await expect(theatre(page)).toHaveAttribute('data-beat', 'day.speech');
  await expect(band(page).getByText('X-ray on')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('replay-xray-film-d3.png');
});

test('replay: played at skip, the cursor runs on', async ({ page }) => {
  await page.clock.install();
  await open(page);
  await page.getByRole('button', { name: 'Skip' }).click();
  await page.getByRole('button', { name: 'Play' }).click();
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  // each beat holds 250 ms at skip; step the clock a beat at a time so each new hold is set
  for (let t = 0; t < 16; t++) await page.clock.runFor(250);
  expect(Number(await theatre(page).getAttribute('data-beat-index'))).toBeGreaterThan(10);
});

test('replay: a speech holds while the pointer rests on it', async ({ page }) => {
  await page.clock.install();
  await open(page);
  await seek(page, 38); // day 3's first speech, seat 2: an 11.25 s hold
  await page.getByRole('button', { name: 'Play' }).click();
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
  await page.getByRole('button', { name: 'Play' }).click();
  await expect(theatre(page)).toHaveAttribute('data-playing', 'true');
  await page.keyboard.press(' ');
  await expect(theatre(page)).toHaveAttribute('data-playing', 'false');
});
