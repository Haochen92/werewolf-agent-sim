/**
 * The day scene in the workbench, at rest, against its goldens: a first speech (day 3, seq
 * 163), the bench's own line (seat 7, day 4, seq 356, seated at 7 as bench 72 is), an X-ray
 * pass, the replay's frame, a public pass (day 1's first turn, which ended with no line), and
 * a live game's thinking seat (seat 7 at the stand before that line, `live=1`). The public
 * indices count day 1 and 2's passes, and a page per beat for a speech told in pages. `strip=0` leaves the stage alone in a 1600×900
 * viewport, one unit a pixel.
 */
import { expect, test, type Page } from '@playwright/test';

const SHOTS: [name: string, query: string][] = [
  ['day-speech-first', 'beat=6'],
  ['day-speech-seat7-bench72', 'beat=55&viewer=seat:player_7'],
  ['day-pass-xray', 'beat=0&viewer=xray'],
  ['day-speech-replay', 'beat=55&hud=replay'],
  ['day-pass-public', 'beat=0'],
  ['day-thinking-live-seat7', 'beat=86&viewer=seat:player_7&live=1'],
];

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

for (const [name, query] of SHOTS) {
  test(`day: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/day?${query}&animate=0&strip=0`, {
      waitUntil: 'networkidle',
    });
    await expect(page.locator('[data-layer="figures"] img')).toHaveCount(1);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The flies scenes (the deal, the night lobby, the morning) at rest: nothing at the stand, so
 * they settle on the wing instead of a puppet. The chips' heads are SVG images, which
 * `networkidle` has already waited for.
 */
const FLIES: [name: string, path: string][] = [
  ['deal-cards-dealt', 'deal?beat=1'],
  ['deal-your-card-seat3', 'deal?beat=2&viewer=seat:player_3'],
  ['morning-chip-fell', 'morning?beat=6'],
  ['morning-chip-saved', 'morning?beat=2'],
  ['night-hub', 'night?beat=0'],
];

for (const [name, path] of FLIES) {
  test(`flies: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(9);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The platform (the waiting room) at rest, from its synthetic rooms (`?beat=N` indexes the
 * station's situations in registry.ts): the host with three aboard, a guest in a locked room
 * of five, someone watching a full room, and a guest in an open room of four. Ready when every
 * person on the platform is drawn.
 */
const STATION: [name: string, path: string, aboard: number][] = [
  ['station-host-3', 'station?beat=0', 3],
  ['station-guest-locked', 'station?beat=1', 5],
  ['station-spectator-full', 'station?beat=2', 9],
  ['station-guest-4', 'station?beat=5', 4],
];

for (const [name, path, aboard] of STATION) {
  test(`platform: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-aboard] img')).toHaveCount(aboard);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

test('the control strip writes the URL', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto('/workbench/day?beat=3', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: '▶' }).click();
  await expect(page).toHaveURL(/beat=4&viewer=spect&motion=normal/);
  await page.getByLabel('viewer').selectOption('xray');
  await expect(page).toHaveURL(/beat=0&viewer=xray/);
  await expect(
    page.getByText('day.pass · seq 15 · xray → player_1 · 4000 ms'),
  ).toBeVisible();
});

/**
 * The night rooms, drawn from the workbench's synthetic situations (`?beat=N` indexes the
 * scene's situation list in registry.ts): the healer on night 2 at rest, with seat 1 chosen,
 * and with the card open; the pack's vote on night 2 with the packmate's tooth on seat 4.
 * Ready when every photo on the line has its portrait.
 */
const NIGHT_SHOTS: [name: string, path: string, photos: number][] = [
  ['room-healer-rest', 'room?beat=0', 8],
  ['room-healer-chosen', 'room?beat=1', 8],
  ['room-healer-card', 'room?beat=2', 8],
  ['pack-vote-mate-tooth', 'pack?beat=3', 7],
];

for (const [name, path, photos] of NIGHT_SHOTS) {
  test(`night: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="figures"] [data-seat] img')).toHaveCount(
      photos,
    );
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * A tap on the empty room resets it (beat sheet §6, ruled 2026-09-28): it draws the pin out of
 * an unsent choice and closes the card; a tap past the open card does the same; once the act
 * is in, a tap only closes the card.
 */
test('night: a tap on the empty room clears an unsent choice and closes the card', async ({
  page,
}) => {
  const pressed = page.locator('[data-seat][aria-pressed="true"]');
  const card = page.locator('[data-overlay="card"]');
  await page.goto('/workbench/room?beat=1&animate=0&strip=0', { waitUntil: 'networkidle' });
  await expect(pressed).toHaveCount(1);
  await page.mouse.click(300, 650);
  await expect(pressed).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Choose a seat to protect' }),
  ).toBeVisible();

  await page.goto('/workbench/room?beat=1&animate=0&strip=0', { waitUntil: 'networkidle' });
  await page.locator('button[data-card]').click();
  await page.getByRole('dialog').click(); // on the card: closes it, the choice stays
  await expect(card).toHaveCount(0);
  await expect(pressed).toHaveCount(1);
  await page.locator('button[data-card]').click();
  await page.mouse.click(1400, 450); // past the card
  await expect(card).toHaveCount(0);
  await expect(pressed).toHaveCount(0);

  await page.goto('/workbench/room?beat=8&animate=0&strip=0', { waitUntil: 'networkidle' });
  await page.locator('button[data-card]').click();
  await page.mouse.click(1400, 450);
  await expect(card).toHaveCount(0);
  await expect(page.getByText('Seat 1 is protected tonight')).toBeVisible();

  await page.goto('/workbench/pack?beat=4&animate=0&strip=0', { waitUntil: 'networkidle' });
  await expect(pressed).toHaveCount(1);
  await page.mouse.click(1000, 650);
  await expect(pressed).toHaveCount(0);
});

/**
 * The trap scenes at rest: voting opens on day 3 (the table up, the jar empty, the lid lifted),
 * the fourth chip counted that day, the result (seat 6 voted out, 6 to 1), the seated human's
 * ballot with seat 6 chosen (the second of the vote's synthetic situations, after the fixture's
 * 39 vote beats), and the lynch's role card on the lift on day 4 (seat 2, the serial killer).
 * Each waits for its own instrument, since the ballot row adds seat chips to the HUD.
 */
const TRAP: [name: string, path: string, ready: string][] = [
  ['vote-opens-d3', 'vote?beat=15', '[data-vote-table]'],
  ['vote-chip-counted-4-d3', 'vote?beat=22', '[data-plate="player_6"]'],
  ['vote-result-d3', 'vote?beat=26', '[data-card="player_6"]'],
  ['vote-your-ballot-chosen', 'vote?beat=40', '[data-ballot="open"]'],
  ['lynch-card-up-d4', 'lynch?beat=9', '[data-lift-card]'],
];

for (const [name, path, ready] of TRAP) {
  test(`trap: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator(ready).first()).toBeAttached();
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The last two scenes at rest, in the replay's frame (the top drape) where the bench drew them
 * so: the X-ray night's pack spoke on night 2 at its second line (the chat, the marks of the
 * three spokes before it) and the night whole, both with the film in the side slot as bench 67
 * drew them; and the ending's verdict, the winner at the stand and the epilogue's sheet.
 */
const ENDING: [name: string, path: string, ready: string][] = [
  [
    'rnight-spoke-pack-d2-line2',
    'rnight?beat=15&viewer=xray&hud=replay&slot=film',
    '[data-chat="pack"]',
  ],
  [
    'rnight-whole-d2',
    'rnight?beat=19&viewer=xray&hud=replay&slot=film',
    '[role="img"][aria-label="bite"]',
  ],
  ['over-verdict', 'over?beat=2', '[data-verdict="wolves"]'],
  ['over-winners-stand', 'over?beat=3', '[data-layer="figures"] img'],
  ['over-epilogue', 'over?beat=5', '[data-ledger]'],
];

for (const [name, path, ready] of ENDING) {
  test(`ending: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator(ready).first()).toBeAttached();
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The side slot open (beat sheet §12): the drawer at full height on a speech (bench 74's
 * moment, seat 8 on day 3, in the replay's frame), the drawer on the count with the day's vote
 * as one line of chips, the drawer stopped at the rail on the seated human's ballot; the case
 * file on a turn (the speaker's notes; its precedents, opened; the same turn in a memory-off
 * game), with a read card opened from the wing, and the docket at the lynch's card ("who had them
 * right") and at the morning's carried brief.
 */
const SLOT: [name: string, path: string, ready: string, click?: string][] = [
  ['slot-day-speech-drawer', 'day?beat=16&hud=replay&slot=drawer', '[data-line="say-200"]'],
  ['slot-vote-line-drawer', 'vote?beat=26&slot=drawer', '[data-line="votes-3"]'],
  ['slot-ballot-drawer-rail', 'vote?beat=40&slot=drawer', '[data-drawer="rail"]'],
  [
    'slot-day-speech-film',
    'day?beat=16&viewer=xray&hud=replay&slot=film',
    '[data-film="file"]',
  ],
  [
    'slot-day-file-precedents',
    'day?beat=16&viewer=xray&hud=replay&slot=film',
    '[data-sheet="precedents"]',
    '[role="tab"]:has-text("Precedents")',
  ],
  [
    'slot-day-file-memory-off',
    'day?beat=16&viewer=xray&hud=replay&slot=film&memory=off',
    '[data-film="file"]',
  ],
  [
    'slot-day-read-card',
    'day?beat=16&viewer=xray&hud=replay&slot=film',
    '[data-read-card="player_1"]',
    '[data-layer="hud"] [data-seat="1"]',
  ],
  ['slot-lynch-card-up-film', 'lynch?beat=9&viewer=xray&slot=film', '[data-film="lynch"]'],
  [
    'slot-morning-carried-summary-film',
    'morning?beat=20&viewer=xray&slot=film',
    '[data-film="brief"]',
  ],
];

for (const [name, path, ready, click] of SLOT) {
  test(`slot: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="hud"] [data-seat="9"]').first()).toBeVisible();
    if (click) await page.locator(click).click();
    await expect(page.locator(ready).first()).toBeVisible();
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The closed case at the curtain: a seat opened from the docket's rows, and its Findings, what
 * the game taught its role (the serial killer's nine observations, the first opened).
 */
test('slot: the case file’s findings at game over', async ({ page }) => {
  await page.goto(
    '/workbench/over?beat=6&viewer=xray&hud=replay&slot=film&animate=0&strip=0',
    {
      waitUntil: 'networkidle',
    },
  );
  await page.locator('[data-film="deal"] button[title^="Open seat 2"]').click();
  await page.getByRole('tab', { name: /^Findings/ }).click();
  await expect(page.locator('[data-sheet="findings"]')).toBeVisible();
  await settle(page);
  await expect(page).toHaveScreenshot('slot-over-file-findings.png');
});

/** The same findings on a phone: the index's numbers grouped by phase, wrapping. */
test('bleed: frame-iphone14-findings', async ({ page }) => {
  await page.goto(
    '/workbench/over?beat=6&viewer=xray&hud=replay&slot=film&frame=iphone14&animate=0&strip=0',
    { waitUntil: 'networkidle' },
  );
  await page.locator('[data-film="deal"] button[title^="Open seat 3"]').click();
  await page.getByRole('tab', { name: /^Findings/ }).click();
  await expect(page.locator('[data-sheet="findings"]')).toBeVisible();
  await settle(page);
  await expect(page.locator('[data-frame]')).toHaveScreenshot(
    'frame-iphone14-findings.png',
  );
});

test('the stage’s File and Transcript tabs write the slot into the URL', async ({
  page,
}) => {
  await page.goto('/workbench/day?beat=16&strip=0', { waitUntil: 'networkidle' });
  const file = page.getByRole('button', { name: 'File', exact: true });
  await page.getByRole('button', { name: 'Transcript' }).click();
  await expect(page).toHaveURL(/viewer=spect&motion=normal&slot=drawer/);
  await expect(page.locator('[data-drawer="full"]')).toBeVisible();
  // the file is the X-ray's pane: greyed without it (the X-ray is the viewer control here)
  await expect(file).toBeDisabled();
  await page.goto('/workbench/day?beat=16&viewer=xray&slot=drawer&strip=0', {
    waitUntil: 'networkidle',
  });
  await file.click();
  await expect(page).toHaveURL(/beat=16&viewer=xray&motion=normal&slot=film/);
  await expect(page.locator('[data-film="file"]')).toBeVisible();
  // Transcript swaps the drawer in; the X-ray stays on
  await page.getByRole('button', { name: 'Transcript' }).click();
  await expect(page).toHaveURL(/viewer=xray&motion=normal&slot=drawer/);
  // File brings the film back; again, and the slot closes
  await file.click();
  await expect(page).toHaveURL(/viewer=xray&motion=normal&slot=film/);
  await file.click();
  await expect(page).toHaveURL(/viewer=xray&motion=normal&slot=none/);
});

/**
 * `frame=iphone15max`: the stage in a 932×430 box, letterboxed as on the phone held sideways
 * (430 × 16/9 ≈ 764 wide), with the drawer closed as the phone opens it.
 */
test('the phone frame draws the stage at the phone’s size', async ({ page }) => {
  await page.goto('/workbench/vote?beat=32&viewer=seat:player_7&frame=iphone15max', {
    waitUntil: 'networkidle',
  });
  // the stage box: the world's parent, the HUD layer's grandparent
  const box = await page.locator('[data-layer="hud"]').locator('xpath=../..').boundingBox();
  expect(Math.abs((box?.width ?? 0) - 764)).toBeLessThanOrEqual(2);
  expect(Math.abs((box?.height ?? 0) - 430)).toBeLessThanOrEqual(2);
  await expect(page.locator('[data-drawer]')).toHaveCount(0);
  await expect(page.getByText('iPhone 15 Pro Max · 932×430 css px')).toBeVisible();
});

/**
 * The seat rail's notebook (beat sheet §0, HUD pass 2): a seated player (a live cut) taps another
 * seat's card to write a note and mark a suspect; the note shows on the card, the suspect's head
 * in the slot, and both come back after a reload (this device only). A dead seat has no suspect
 * toggle. The replay's cut shows the cards only.
 */
test('the seat rail: notes and a suspect for a seated player, none in a replay', async ({
  page,
}) => {
  const live = '/workbench/day?live=1&viewer=seat:player_7&animate=0&strip=0';
  await page.goto(`${live}&beat=6`, { waitUntil: 'networkidle' });
  const hint = page.getByText('Tap a card to write notes');
  await expect(hint).toBeVisible();
  // your own card is not a notebook page
  await expect(page.getByRole('button', { name: 'Seat 7, notes' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Seat 5, notes' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Seat 5');
  await expect(dialog).toContainText('Alive');
  await expect(hint).toHaveCount(0);
  await page.keyboard.type('Jumped on the slip');
  await dialog.getByRole('button', { name: 'Mark as suspect' }).click();
  await dialog.getByRole('button', { name: 'Done' }).click();
  await expect(dialog).toHaveCount(0);
  const card = page.locator('[data-layer="hud"] [data-seat="5"]');
  await expect(card).toContainText('Jumped on the slip');
  await expect(page.getByRole('button', { name: 'Suspect: seat 5, notes' })).toBeVisible();

  // kept on the device: a later beat still has it, and the hint stays dismissed
  await page.goto(`${live}&beat=14`, { waitUntil: 'networkidle' });
  await expect(card).toContainText('Jumped on the slip');
  await expect(hint).toHaveCount(0);
  // a dead seat: its note may be written, it cannot be marked; Escape closes
  await page.getByRole('button', { name: 'Seat 3, notes' }).click();
  await expect(dialog).toContainText('Dead · Wolf');
  await expect(dialog.getByRole('button', { name: /suspect/ })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Seat 3, notes' })).toBeFocused();

  // the replay's cut: the same seat, nothing to write on
  await page.goto('/workbench/day?beat=6&viewer=seat:player_7&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(9);
  await expect(page.getByRole('button', { name: /^Seat \d, notes$/ })).toHaveCount(0);
  await expect(hint).toHaveCount(0);
});

/**
 * The bleed (stage_architecture.md §3): on a phone held sideways (19.5:9) the picture carries
 * on past the 16:9 world's sides instead of leaving bars. The count's push-in in the car, with
 * the lantern's wall continuing on the right; the night lobby with the wing on the left.
 */
const FRAMES: [name: string, path: string][] = [
  ['frame-iphone14-vote', 'vote?beat=32&viewer=seat:player_7&frame=iphone14'],
  ['frame-iphone14-night', 'night?beat=0&viewer=seat:player_7&frame=iphone14'],
  // the case file on a phone: its cover and tabs in one row over the sheet
  ['frame-iphone14-file', 'day?beat=16&viewer=xray&hud=replay&slot=film&frame=iphone14'],
];

for (const [name, path] of FRAMES) {
  test(`bleed: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(9);
    await settle(page);
    await expect(page.locator('[data-frame]')).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * Legibility (stage_architecture.md §3): drawn at a phone's scale (~0.43 on an iPhone 14), the
 * HUD grows in two tiers: labels and buttons by `--legible-ui` (capped at 1.3), so a top-strip
 * button still reads and taps; the words people read by `--legible`, so a speech reads at a
 * phone's body size. Sizes are as drawn on the screen: the computed size times the stage's scale.
 */
test('the phone frame: the top strip’s buttons are drawn large enough to read and tap', async ({
  page,
}) => {
  await page.goto('/workbench/vote?beat=32&viewer=seat:player_7&frame=iphone14&strip=0', {
    waitUntil: 'networkidle',
  });
  const button = page
    .locator('[data-layer="hud"]')
    .getByRole('button', { name: 'Transcript' });
  const drawn = await button.evaluate((el: HTMLElement) => {
    const scale = el.getBoundingClientRect().width / el.offsetWidth;
    return {
      font: parseFloat(getComputedStyle(el).fontSize) * scale,
      height: el.getBoundingClientRect().height,
    };
  });
  expect(drawn.font).toBeGreaterThanOrEqual(9);
  expect(drawn.height).toBeGreaterThanOrEqual(22);
});

test('the phone frame: a speech is drawn at a phone’s body size', async ({ page }) => {
  await page.goto('/workbench/day?beat=55&viewer=seat:player_7&frame=iphone14&strip=0', {
    waitUntil: 'networkidle',
  });
  // the speech box's line: the div after its head
  const body = page.locator('[data-speech] > header + div');
  const font = await body.evaluate((el: HTMLElement) => {
    const scale = el.getBoundingClientRect().width / el.offsetWidth;
    return parseFloat(getComputedStyle(el).fontSize) * scale;
  });
  expect(font).toBeGreaterThanOrEqual(16);
});
