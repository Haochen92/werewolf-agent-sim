import { expect, test } from '@playwright/test';

for (const slot of ['drawer', 'film']) {
  test(`open ${slot} survives room changes and closes normally`, async ({ page }) => {
    await page.goto(`/workbench/day?animate=0&slot=${slot}`);
    const panel = page.locator(slot === 'drawer' ? '[data-drawer]' : '[data-film]');
    await expect(panel).toBeVisible();
    const original = await panel.elementHandle();
    for (const scene of ['vote', 'room', 'pack', 'day']) {
      await page
        .getByRole('group', { name: 'scene', exact: true })
        .getByRole('button', { name: scene, exact: true })
        .click();
      await expect(panel).toBeVisible();
      expect(await panel.evaluate((node, kept) => node === kept, original), scene).toBe(
        true,
      );
      await expect(panel).toHaveCount(1);
    }
    const controls = page.getByRole('group', { name: 'slot', exact: true });
    await controls.getByRole('button', { name: 'none', exact: true }).click();
    await expect(panel).toHaveCount(0);
    await controls.getByRole('button', { name: slot, exact: true }).click();
    await expect(panel).toBeVisible();
  });
}

test('portrait survives becoming read-only and clickable again', async ({ page }) => {
  await page.goto('/workbench/day?live=1&viewer=seat:player_9&beat=7&animate=0');
  const portrait = page.locator('[data-wing-host] [data-seat="10"] img');
  await expect(portrait).toBeVisible();
  const original = await portrait.elementHandle();
  const button = page.getByRole('button', { name: 'Seat 10’s file', exact: true });
  await button.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-player-file="10"]')).toBeVisible();
  const hud = page.getByRole('group', { name: 'hud', exact: true });
  await hud.getByRole('button', { name: 'replay', exact: true }).click();
  await expect(button).toHaveCount(0);
  expect(await portrait.evaluate((node, kept) => node === kept, original)).toBe(true);
  await hud.getByRole('button', { name: 'live', exact: true }).click();
  await expect(button).toBeVisible();
  expect(await portrait.evaluate((node, kept) => node === kept, original)).toBe(true);
  await page
    .getByRole('group', { name: 'slot', exact: true })
    .getByRole('button', { name: 'none', exact: true })
    .click();
  await button.focus();
  await page.keyboard.press('Space');
  await expect(page.locator('[data-player-file="10"]')).toBeVisible();
});
