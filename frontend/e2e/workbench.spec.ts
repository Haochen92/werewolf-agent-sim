/**
 * The day scene in the workbench, at rest, against its goldens, on the ten-seat game (the
 * workbench's default, `fixtures/replay-phase3.json`): the first speech (day 2, seq 128, seat
 * 3), a seated viewer's own line (seat 9's sweep line, day 2, seq 169), an X-ray pass (day 1,
 * seat 1, a turn that ended with no line), seat 10's line in the replay's frame (day 2, seq
 * 151), a public pass (day 2, seat 6), and a live game's thinking seat (seat 9 at the stand
 * before its line, `live=1`). The public indices count the rounds' notices, and a page per beat
 * for a speech told in pages. `strip=0` leaves the stage alone in a 1600×900 viewport, one unit
 * a pixel.
 */
import { expect, test, type Page } from '@playwright/test';

const SHOTS: [name: string, query: string][] = [
  ['day-speech-first', 'beat=3'],
  ['day-speech-seat9-own', 'beat=19&viewer=seat:player_9'],
  ['day-pass-xray', 'beat=1&viewer=xray'],
  ['day-speech-replay', 'beat=13&hud=replay'],
  ['day-pass-public', 'beat=11'],
  ['day-thinking-live-seat9', 'beat=27&viewer=seat:player_9&live=1'],
];

/**
 * The rounds (beat sheet §2 rows 7-10), on the Phase 2 game (`game=phase2`, goldens
 * `phase2.public.txt`): day 1's opening being written and nobody having anything to say, day
 * 2's seats that said nothing (seat 2 is the viewer: "you and seats…"), and the first accused
 * called to answer with the moderator's line in the box. No puppet stands at a notice, so these
 * settle on the wing.
 */
const ROUND_SHOTS: [name: string, query: string, figures: number][] = [
  // the day scene's own beat numbers (golden lines 3, 4, 14 and 35)
  ['phase2-opening-prepares-day1', 'beat=0&game=phase2', 0],
  ['phase2-round-passes-everyone', 'beat=1&game=phase2', 0],
  ['phase2-round-passes-seat2-you', 'beat=4&game=phase2&viewer=seat:player_2', 0],
  ['phase2-closing-called', 'beat=25&game=phase2', 1],
];

/** Wait until the frame is still: sprites decoded, fonts in, and Next's dev badge hidden. */
async function settle(page: Page) {
  await page.addStyleTag({ content: 'nextjs-portal{display:none!important}' });
  await page.evaluate(async () => {
    await document.fonts.ready;
    // only the images in the window: a lazy one scrolled out of a long drawer never loads
    const inView = (img: HTMLImageElement) => {
      const r = img.getBoundingClientRect();
      return r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth;
    };
    await Promise.all(
      [...document.images].map((img) =>
        img.complete || !inView(img) ? null : img.decode().catch(() => null),
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

for (const [name, query, figures] of ROUND_SHOTS) {
  test(`day, the rounds: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/day?${query}&animate=0&strip=0`, {
      waitUntil: 'networkidle',
    });
    await expect(page.locator('[data-layer="figures"] img')).toHaveCount(figures);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The flies scenes (the deal, the night lobby, the morning) at rest: nothing at the stand, so
 * they settle on the wing instead of a puppet. The chips' heads are SVG images, which
 * `networkidle` has already waited for. All ten-seat: the default game has no save, so the
 * saved chip is the other ten-seat game's (`game=phase3-necro`, seat 1 on morning 2).
 */
const FLIES: [name: string, path: string][] = [
  ['deal-cards-dealt', 'deal?beat=1'],
  ['deal-your-card-seat3', 'deal?beat=2&viewer=seat:player_3'],
  // the deal face up (the X-ray): each small card the role's figure under its name
  ['deal-face-up-figures', 'deal?beat=2&viewer=xray&hud=replay'],
  ['morning-chip-fell', 'morning?beat=2'],
  ['morning-chip-saved', 'morning?beat=11&game=phase3-necro'],
  // the roll after morning 3's report: its two deaths, a row each, roles told
  ['morning-roll-two-deaths', 'morning?beat=25'],
  ['night-hub', 'night?beat=0'],
];

for (const [name, path] of FLIES) {
  test(`flies: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(10);
    await settle(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}

/**
 * The platform (the waiting room) at rest, from its synthetic rooms (`?beat=N` indexes the
 * station's situations in registry.ts, the two ten-place rooms first): in rooms of nine places,
 * the host with three aboard, a guest in a locked room of five, someone watching a full room,
 * and a guest in an open room of four. Ready when every person on the platform is drawn.
 */
const STATION: [name: string, path: string, aboard: number][] = [
  ['station-host-3', 'station?beat=2', 3], // nine seats: the host, 3 aboard
  ['station-guest-locked', 'station?beat=3', 5], // nine seats: a guest, 5 aboard, locked
  ['station-spectator-full', 'station?beat=4', 9], // nine seats: watching, all 9 aboard
  ['station-guest-4', 'station?beat=7', 4], // nine seats: a guest, 4 aboard
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
  await page.getByRole('button', { name: '▶' }).click();
  await expect(
    page.getByText('day.pass · seq 35 · xray → player_1 · 4000 ms'),
  ).toBeVisible();
  // the ten-seat game's seats in the viewer control
  await page.getByLabel('viewer').selectOption('seat:player_10');
  await expect(page).toHaveURL(/beat=0&viewer=seat:player_10/);
});

/**
 * The night rooms, drawn from the workbench's synthetic situations (`?beat=N` indexes the
 * scene's situation list in registry.ts, the ten-seat ones first): on the nine-seat fixture,
 * the healer on night 2 at rest, with seat 1 chosen, and with the card open; the pack's vote on
 * night 2 with the packmate's tooth on seat 4. Ready when every photo on the line has its
 * portrait.
 */
const NIGHT_SHOTS: [name: string, path: string, photos: number][] = [
  ['room-healer-rest', 'room?beat=16', 8], // nine seats: healer, night 2
  ['room-healer-chosen', 'room?beat=17', 8], // nine seats: healer, night 2, seat 1 chosen
  ['room-healer-card', 'room?beat=18', 8], // nine seats: healer, night 2, the card open
  ['pack-vote-mate-tooth', 'pack?beat=8', 7], // nine seats: wolf, the vote, packmate voted
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
  // nine seats: healer, night 2, seat 1 chosen
  await page.goto('/workbench/room?beat=17&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await expect(pressed).toHaveCount(1);
  await page.mouse.click(300, 650);
  await expect(pressed).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Choose a seat to protect' }),
  ).toBeVisible();

  await page.goto('/workbench/room?beat=17&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await page.locator('button[data-card]').click();
  await page.getByRole('dialog').click(); // on the card: closes it, the choice stays
  await expect(card).toHaveCount(0);
  await expect(pressed).toHaveCount(1);
  await page.locator('button[data-card]').click();
  await page.mouse.click(1400, 450); // past the card
  await expect(card).toHaveCount(0);
  await expect(pressed).toHaveCount(0);

  // nine seats: healer, night 2, seat 1 protected (sent)
  await page.goto('/workbench/room?beat=24&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await page.locator('button[data-card]').click();
  await page.mouse.click(1400, 450);
  await expect(card).toHaveCount(0);
  await expect(page.getByText('Seat 1 is protected tonight')).toBeVisible();

  // nine seats: wolf, the vote, seat 4 chosen
  await page.goto('/workbench/pack?beat=9&animate=0&strip=0', { waitUntil: 'networkidle' });
  await expect(pressed).toHaveCount(1);
  await page.mouse.click(1000, 650);
  await expect(pressed).toHaveCount(0);
});

/**
 * The trap scenes at rest, on the ten-seat game: voting opens on day 3 (the table up, the jar
 * empty, the lid lifted), the fourth chip counted that day, the result (seat 10 voted out, 3 to
 * 2), the seated human's ballot (seat 9) with seat 6 chosen (the second of the vote's synthetic
 * situations, after the game's 24 vote beats), and the lynch's role card on the lift on day 3
 * (seat 10, the serial killer). Each waits for its own instrument, since the ballot row adds seat
 * chips to the HUD.
 */
const TRAP: [name: string, path: string, ready: string][] = [
  ['vote-opens-d3', 'vote?beat=13', '[data-vote-table]'],
  ['vote-chip-counted-4-d3', 'vote?beat=20', '[data-plate="player_10"]'],
  ['vote-result-d3', 'vote?beat=22', '[data-card="player_10"]'],
  ['vote-your-ballot-chosen', 'vote?beat=25', '[data-ballot="open"]'],
  ['lynch-card-up-d3', 'lynch?beat=9', '[data-lift-card]'],
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
 * so, on the ten-seat game: the X-ray night's spokes in the actor's own room (owner,
 * 2026-09-29), the investigator's check on night 1 (the pin through seat 6's photo, the lens on
 * it) and the pack's room on night 1 at its second line (the chat), and night 2 whole, all with
 * the file in the side slot; and the ending's verdict, the winners at the stand and, on the
 * nine-seat fixture (`game=9369a5c1`, the one game with memory on), the epilogue's sheet.
 */
const ENDING: [name: string, path: string, ready: string][] = [
  [
    'rnight-spoke-solo-d1',
    'rnight?beat=2&viewer=xray&hud=replay&slot=film',
    '[role="img"][aria-label="lens"]',
  ],
  [
    'rnight-spoke-pack-d1-line2',
    'rnight?beat=10&viewer=xray&hud=replay&slot=film',
    '[data-chat="pack"]',
  ],
  [
    'rnight-whole-d2',
    'rnight?beat=26&viewer=xray&hud=replay&slot=film',
    '[role="img"][aria-label="bite"]',
  ],
  // the photo wall at full width: the serial killer's scythe tacked on seat 2's print
  [
    'rnight-spoke-knife-d1',
    'rnight?beat=3&viewer=xray&hud=replay',
    '[role="img"][aria-label="knife"]',
  ],
  // the vigilante holding its fire on night 1: a room of its own, no mark; the other actors'
  // cards say "Visit ▸"
  [
    'rnight-spoke-held-d1',
    'rnight?beat=8&viewer=xray&hud=replay&slot=film',
    '[data-layer="hud"] [data-word="visit"]',
  ],
  // the night stop with its file up: "Visit a room" and "Tap a seat to open its file" head the
  // night's sheet, the wing's actors say "Visit ▸"
  [
    'rnight-hub-file',
    'rnight?beat=0&viewer=xray&hud=replay&slot=film',
    '[data-visit="pack"]',
  ],
  ['over-verdict', 'over?beat=2', '[data-verdict="villagers"]'],
  ['over-winners-stand', 'over?beat=3', '[data-layer="figures"] img'],
  ['over-epilogue', 'over?beat=5&game=9369a5c1', '[data-ledger]'],
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
 * The side slot open (beat sheet §12), on the ten-seat game unless a shot says otherwise: the
 * drawer at full height on a speech (seat 10 on day 2, in the replay's frame), the drawer on the
 * count with the day's vote as one line of chips, the drawer stopped at the rail on the seated
 * human's ballot; the case file on a turn (the speaker's notes; on the nine-seat fixture, the one
 * game with memory on, its precedents, opened, and the same turn in a memory-off game), with a
 * read card opened from the wing, the docket at the lynch's card ("who had them right"), and the
 * Record: at the morning's carried summary, with Reveal off on a day-3 turn of the second game
 * (its real ledger), the v4 redraw's synthetic ledger (every kind of line, the nine-seat
 * fixture's), the same without a ledger (an old archive), and the transcript's line pointing to
 * it (lit, at the carried summary's beat).
 */
const SLOT: [name: string, path: string, ready: string, click?: string][] = [
  ['slot-day-speech-drawer', 'day?beat=13&hud=replay&slot=drawer', '[data-line="say-151"]'],
  ['slot-vote-line-drawer', 'vote?beat=22&slot=drawer', '[data-line="votes-3"]'],
  ['slot-ballot-drawer-rail', 'vote?beat=25&slot=drawer', '[data-drawer="rail"]'],
  [
    'slot-day-speech-film',
    'day?beat=26&viewer=xray&hud=replay&slot=film',
    '[data-film="file"]',
  ],
  [
    'slot-day-file-precedents',
    'day?beat=16&viewer=xray&hud=replay&slot=film&game=9369a5c1',
    '[data-sheet="precedents"]',
    '[role="tab"]:has-text("Lessons")',
  ],
  [
    'slot-day-file-memory-off',
    'day?beat=16&viewer=xray&hud=replay&slot=film&memory=off',
    '[data-film="file"]',
  ],
  [
    'slot-day-read-card',
    'day?beat=26&viewer=xray&hud=replay&slot=film',
    '[data-read-card="player_1"]',
    '[data-layer="hud"] [data-seat="1"]',
  ],
  ['slot-lynch-card-up-film', 'lynch?beat=9&viewer=xray&slot=film', '[data-film="lynch"]'],
  [
    'slot-morning-carried-summary-film',
    'morning?beat=31&viewer=xray&slot=film',
    '[data-film="record"]',
  ],
  [
    'slot-record-reveal-off',
    'day?beat=120&hud=replay&slot=film&game=140610ad',
    '[data-film="record"] [data-claim="player_6"]',
  ],
  [
    'slot-record-v4-ledger',
    'day?beat=40&hud=replay&slot=film&summary=v4',
    '[data-film="record"] [data-claim="player_7"]',
  ],
  [
    'slot-record-no-ledger',
    'day?beat=40&hud=replay&slot=film&summary=v4&ledger=off',
    '[data-film="record"] [data-claim="player_5"]',
  ],
  [
    'slot-record-line-drawer',
    'morning?beat=31&viewer=xray&hud=replay&slot=drawer',
    '[data-line="record-2"]',
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
 * the game taught its role (the serial killer's nine observations, the first opened), on the
 * nine-seat fixture (the one game with memory on).
 */
test('slot: the case file’s findings at game over', async ({ page }) => {
  await page.goto(
    '/workbench/over?beat=6&viewer=xray&hud=replay&slot=film&game=9369a5c1&animate=0&strip=0',
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
    '/workbench/over?beat=6&viewer=xray&hud=replay&slot=film&game=9369a5c1&frame=iphone14&animate=0&strip=0',
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
  // without the X-ray the file opens on the Record alone (the X-ray is the viewer control here)
  await file.click();
  await expect(page).toHaveURL(/viewer=spect&motion=normal&slot=film/);
  await expect(page.locator('[data-film="record"]')).toBeVisible();
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

test('the transcript’s line to a day’s record opens the file on that day’s Record', async ({
  page,
}) => {
  await page.goto(
    '/workbench/day?beat=120&hud=replay&slot=drawer&game=140610ad&animate=0&strip=0',
    { waitUntil: 'networkidle' },
  );
  await page.locator('[data-line="record-1"] button').click();
  await expect(page).toHaveURL(/slot=film/);
  const record = page.locator('[data-sheet="record"]');
  await expect(record.getByText('Day 1’s record')).toBeVisible();
  // the pager goes on to day 2's (the stage is on day 3), never past it
  await record.getByRole('button', { name: 'Day 2 →' }).click();
  await expect(record.getByText('Day 2’s record')).toBeVisible();
  await expect(record.getByRole('button', { name: 'Day 2 →' })).toBeDisabled();
  // an accusation opens to its defence
  await record.getByRole('button', { name: 'Defence ▸' }).first().click();
  await expect(record.getByText('Defence:').first()).toBeVisible();
});

/**
 * `frame=iphone15max`: the stage in a 932×430 box, letterboxed as on the phone held sideways
 * (430 × 16/9 ≈ 764 wide), with the drawer closed as the phone opens it.
 */
test('the phone frame draws the stage at the phone’s size', async ({ page }) => {
  await page.goto('/workbench/vote?beat=17&viewer=seat:player_9&frame=iphone15max', {
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
 * The seat rail's notebook (beat sheet §0, HUD pass 2): a seated player (a live cut, seat 9 on
 * day 2 of the ten-seat game) taps another seat's card to write a note, guess its role (the
 * roles still possible, with how many are left) and mark a suspect; the note and the guess show
 * on the card, the suspect's head in the slot, and all come back after a reload (this device
 * only). A dead seat has no suspect toggle and no guess. The replay's cut shows the cards only.
 */
test('the seat rail: notes and a suspect for a seated player, none in a replay', async ({
  page,
}) => {
  const live = '/workbench/day?live=1&viewer=seat:player_9&animate=0&strip=0';
  await page.goto(`${live}&beat=7`, { waitUntil: 'networkidle' });
  const hint = page.getByText('Tap a card to write notes');
  await expect(hint).toBeVisible();
  // your own card is not a notebook page
  await expect(page.getByRole('button', { name: 'Seat 9, notes' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Seat 10, notes' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Seat 10');
  await expect(dialog).toContainText('Alive');
  await expect(hint).toHaveCount(0);
  await page.keyboard.type('Jumped on the slip');
  await dialog.getByRole('button', { name: 'Mark as suspect' }).click();
  // the role guess: only the roles that could still be alive (the night's three dead were told:
  // healer, chanteuse, investigator), with how many are left, "not sure" first, in a panel over
  // the notebook; the arrows move and Enter picks
  const guess = dialog.getByRole('button', { name: /I think they are…/ });
  await expect(guess).toHaveText('not sure');
  await guess.click();
  const menu = dialog.getByRole('listbox');
  await expect(menu).toBeFocused();
  await expect(menu.getByRole('option')).toHaveText([
    'not sure',
    // the pool's order (ten-seat pass §7)
    /^Sentinel\s*1 left$/,
    /^Trailseer\s*1 left$/,
    /^Vigilante\s*1 left$/,
    /^Sigilist\s*1 left$/,
    /^Illusionist\s*1 left$/,
    /^Serial killer\s*1 left$/,
    /^Fortune teller\s*1 left$/,
  ]);
  await expect(menu.getByRole('option', { selected: true })).toHaveText('not sure');
  for (let i = 0; i < 6; i++) await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(menu).toHaveCount(0);
  await expect(guess).toBeFocused();
  await expect(guess).toHaveText('Serial killer');
  await page.addStyleTag({ content: 'nextjs-portal{display:none!important}' });
  await expect(page).toHaveScreenshot('wing-notebook-guess.png');
  // open again: the guess is the selected row; Escape closes the panel, not the notebook
  await page.keyboard.press('ArrowDown');
  await expect(menu.getByRole('option', { selected: true })).toHaveText(/^Serial killer/);
  await expect(page).toHaveScreenshot('wing-notebook-menu.png');
  await page.keyboard.press('Escape');
  await expect(menu).toHaveCount(0);
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Done' }).click();
  await expect(dialog).toHaveCount(0);
  const card = page.locator('[data-layer="hud"] [data-seat="10"]');
  await expect(card).toContainText('Jumped on the slip');
  await expect(card.locator('[data-guess="serial_killer"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Suspect: seat 10, notes' })).toBeVisible();

  // kept on the device: a later beat still has it, and the hint stays dismissed
  await page.goto(`${live}&beat=14`, { waitUntil: 'networkidle' });
  await expect(card).toContainText('Jumped on the slip');
  await expect(card.locator('[data-guess="serial_killer"]')).toBeVisible();
  await expect(hint).toHaveCount(0);
  // a dead seat: its note may be written, it cannot be marked; Escape closes
  await page.getByRole('button', { name: 'Seat 5, notes' }).click();
  await expect(dialog).toContainText('Dead · Chanteuse');
  await expect(dialog.getByRole('button', { name: /suspect/ })).toHaveCount(0);
  await expect(dialog.getByRole('button', { name: /I think they are…/ })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Seat 5, notes' })).toBeFocused();

  // the replay's cut: the same seat, nothing to write on
  await page.goto('/workbench/day?beat=6&viewer=seat:player_9&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(10);
  await expect(page.getByRole('button', { name: /^Seat \d+, notes$/ })).toHaveCount(0);
  await expect(hint).toHaveCount(0);
});

/**
 * What a seat already knows shows on its wing, from its own view only: a wolf's pack mate
 * ("Your pack", day 1 of the ten-seat game), the seat its investigation read ("Seen · Villager":
 * the ten-seat game's investigator died on the night it checked, so the nine-seat fixture's day
 * 2), live and in a replay seen as that seat; a town seat and a spectator have nothing to band.
 */
test('the seat rail: a seat’s own knowledge bands its cards, and nobody else’s', async ({
  page,
}) => {
  const known = page.locator('[data-layer="hud"] [data-known]');
  const day = (viewer: string, more = '') =>
    page.goto(`/workbench/day?beat=1&viewer=${viewer}&animate=0&strip=0${more}`, {
      waitUntil: 'networkidle',
    });
  // the illusionist at seat 6, a wolf: its pack mate, seat 5
  await day('seat:player_6');
  await expect(known).toHaveCount(1);
  await expect(
    page.locator('[data-layer="hud"] [data-seat="5"] [data-known="pack"]'),
  ).toHaveText('Your pack');
  await expect(page.locator('[data-layer="hud"] [data-seat] img')).toHaveCount(10);
  await settle(page);
  await expect(page).toHaveScreenshot('wing-known-wolf-d1.png');
  for (const more of ['&live=1', '&hud=replay']) {
    await day('seat:player_6', more);
    await expect(known).toHaveCount(1);
  }
  // the nine-seat fixture's investigator at seat 4 read seat 1 on the first night
  await page.goto(
    '/workbench/day?beat=3&viewer=seat:player_4&game=9369a5c1&animate=0&strip=0',
    {
      waitUntil: 'networkidle',
    },
  );
  await expect(known).toHaveCount(1);
  await expect(
    page.locator('[data-layer="hud"] [data-seat="1"] [data-known="seen"]'),
  ).toHaveAttribute('title', 'Seen · Villager');
  // a town seat, a spectator and the X-ray's observer: nothing of their own to band
  for (const viewer of ['seat:player_9', 'spect', 'xray']) {
    await day(viewer);
    await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(10);
    await expect(known).toHaveCount(0);
  }
});

/**
 * Leaving the table (live only): the strip's door at its far right asks first, a walnut notice in
 * the foot's zone; Stay and Escape close it. The replay's HUD has no door.
 */
test('the strip’s door: live only, and it asks before leaving', async ({ page }) => {
  const door = page.getByRole('button', { name: 'Leave the table' });
  const confirm = page.locator('[data-leave-confirm]');
  await page.goto(
    '/workbench/day?beat=7&viewer=seat:player_9&hud=replay&animate=0&strip=0',
    {
      waitUntil: 'networkidle',
    },
  );
  await expect(page.getByRole('button', { name: 'Transcript', exact: true })).toBeVisible();
  await expect(door).toHaveCount(0);
  await page.goto('/workbench/day?live=1&beat=7&viewer=seat:player_9&animate=0&strip=0', {
    waitUntil: 'networkidle',
  });
  await door.click();
  await expect(confirm).toContainText('Leave the table?');
  await expect(confirm).toContainText(
    'Your seat’s agent plays on for you. You can come back to this game from the lobby while it lasts.',
  );
  await expect(confirm.getByRole('button', { name: 'Stay' })).toBeFocused();
  await expect(page.locator('[data-layer="figures"] img')).toHaveCount(1);
  await settle(page);
  await expect(page).toHaveScreenshot('leave-confirm-day.png');
  await page.keyboard.press('Escape');
  await expect(confirm).toHaveCount(0);
  await door.click();
  await confirm.getByRole('button', { name: 'Stay' }).click();
  await expect(confirm).toHaveCount(0);
});

/** The guess's panel on the smallest phone: every row on the stage, a finger's height, tappable. */
test('the seat rail: the role guess fits a small phone and takes a tap', async ({
  page,
}) => {
  await page.goto(
    '/workbench/day?live=1&viewer=seat:player_9&animate=0&strip=0&beat=7&frame=667x375',
    { waitUntil: 'networkidle' },
  );
  await page.getByRole('button', { name: 'Seat 10, notes' }).click();
  const dialog = page.getByRole('dialog');
  // opened from the keys, so no pointer rests on a row for the picture
  await dialog.getByRole('button', { name: /I think they are…/ }).focus();
  await page.keyboard.press('Enter');
  const options = dialog.getByRole('listbox').getByRole('option');
  await expect(options).toHaveCount(8);
  const stage = (await page.locator('[data-layer="hud"]').boundingBox())!;
  for (const box of await options.evaluateAll((els) =>
    els.map((el) => el.getBoundingClientRect().toJSON() as DOMRect),
  )) {
    expect(box.height).toBeGreaterThanOrEqual(37);
    expect(box.top).toBeGreaterThanOrEqual(stage.y);
    expect(box.bottom).toBeLessThanOrEqual(stage.y + stage.height);
  }
  await page.addStyleTag({ content: 'nextjs-portal{display:none!important}' });
  await expect(page).toHaveScreenshot('frame-667-notebook-menu.png');
  await options.filter({ hasText: 'Sigilist' }).click();
  await expect(dialog.getByRole('button', { name: /I think they are…/ })).toHaveText(
    'Sigilist',
  );
});

/**
 * The bleed (stage_architecture.md §3): on a phone held sideways (19.5:9) the picture carries
 * on past the 16:9 world's sides instead of leaving bars. The count's push-in in the car, with
 * the lantern's wall continuing on the right; the night lobby with the wing on the left. On the
 * ten-seat game, but the epilogue (the nine-seat fixture's: the one game with memory on).
 */
const FRAMES: [name: string, path: string][] = [
  ['frame-iphone14-vote', 'vote?beat=17&viewer=seat:player_9&frame=iphone14'],
  ['frame-iphone14-night', 'night?beat=0&viewer=seat:player_9&frame=iphone14'],
  // the case file on a phone: its cover and tabs in one row over the sheet
  ['frame-iphone14-file', 'day?beat=26&viewer=xray&hud=replay&slot=film&frame=iphone14'],
  // the stand's plate on a phone: pinned to the speech box's top edge, not at the chest
  ['frame-667-stand-plate', 'day?beat=26&viewer=xray&hud=replay&frame=667x375'],
  [
    'frame-568-stand-plate-file',
    'day?beat=26&viewer=xray&hud=replay&slot=film&frame=568x320',
  ],
  // the transcript on a phone: the pane grows out into the right bleed as the wing does left
  ['frame-iphone14-drawer', 'day?beat=13&hud=replay&slot=drawer&frame=iphone14'],
  // the epilogue's closing spread on a phone: the rows scroll in place
  ['frame-iphone14-epilogue', 'over?beat=5&game=9369a5c1&frame=iphone14'],
  // the morning roll on a small phone: a cause too long for its row goes under the name
  ['frame-667-morning-roll', 'morning?beat=10&frame=667x375'],
];

for (const [name, path] of FRAMES) {
  test(`bleed: ${name}`, async ({ page }) => {
    await page.goto(`/workbench/${path}&animate=0&strip=0`, { waitUntil: 'networkidle' });
    await expect(page.locator('[data-layer="hud"] [data-seat]')).toHaveCount(
      path.includes('game=9369a5c1') ? 9 : 10,
    );
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
  await page.goto('/workbench/vote?beat=17&viewer=seat:player_9&frame=iphone14&strip=0', {
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
  await page.goto('/workbench/day?beat=19&viewer=seat:player_9&frame=iphone14&strip=0', {
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

/**
 * A lesson read from its record's fields (`dimensions`, server 18ebf3e; the workbench's
 * `memory=fields` gives the nine-seat fixture's records synthetic ones, and draws that game): the form's Information and
 * Exposure ticked from the classifications, the consensus's direction under its words, the
 * tags under the action. And the form's labels never run into their boxes, on the desk or a
 * small phone (a label sits above its boxes there).
 */
test('slot: a lesson read from its record’s fields, the form’s labels clear of its boxes', async ({
  page,
}) => {
  for (const frame of ['', '&frame=667x375']) {
    await page.goto(
      `/workbench/day?beat=16&viewer=xray&hud=replay&slot=film&memory=fields${frame}&animate=0&strip=0`,
      { waitUntil: 'networkidle' },
    );
    await page.getByRole('tab', { name: /^Lessons/ }).click();
    const sheet = page.locator('[data-sheet="precedents"]');
    const toggle = sheet.getByRole('button', { name: /Situation on file/ });
    if ((await toggle.getAttribute('aria-expanded')) === 'false') await toggle.click();
    await expect(sheet.getByText('Exposure', { exact: true }).first()).toBeVisible();
    for (const row of await sheet.locator('[data-form-row]').all()) {
      const label = (await row.locator('[data-form-label]').boundingBox())!;
      const boxes = (await row.locator('[data-form-boxes]').boundingBox())!;
      const beside = label.y + label.height > boxes.y + 1;
      if (beside) expect(label.x + label.width).toBeLessThanOrEqual(boxes.x + 0.5);
    }
    if (!frame) {
      await expect(
        sheet.getByText(/^(defensive|offensive|positional) · (honest|deceptive)$/).first(),
      ).toBeVisible();
      await toggle.evaluate((el) => el.scrollIntoView({ block: 'start' }));
      await settle(page);
      await expect(page.locator('[data-film]')).toHaveScreenshot(
        'slot-day-file-lesson-fields.png',
      );
    }
  }
});
