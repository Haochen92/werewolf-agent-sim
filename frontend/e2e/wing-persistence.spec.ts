import { expect, test } from '@playwright/test';

for (const hud of ['live', 'replay']) {
  test(`wing frame survives scene changes with ${hud} HUD`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto(`/workbench/station?animate=0&hud=${hud}`);
    const wing = page.getByRole('group', { name: 'The seats', exact: true });
    await expect(wing).toBeVisible();
    const original = await wing.elementHandle();
    const scenes = page.getByRole('group', { name: 'scene', exact: true });
    for (const scene of [
      'deal',
      'day',
      'vote',
      'lynch',
      'night',
      'room',
      'pack',
      'morning',
      'rnight',
      'over',
    ]) {
      await scenes.getByRole('button', { name: scene, exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`/workbench/${scene}\\?`));
      await expect(
        scenes.getByRole('button', { name: scene, exact: true }),
      ).toHaveAttribute('aria-pressed', 'true');
      await expect(wing).toBeVisible();
      expect(await wing.evaluate((node, kept) => node === kept, original), scene).toBe(
        true,
      );
    }
    // A non-game drawing must explicitly hide the retained rail.
    await scenes.getByRole('button', { name: 'paint', exact: true }).click();
    await expect(wing).toHaveCount(0);
    await scenes.getByRole('button', { name: 'day', exact: true }).click();
    await expect(wing).toBeVisible();
    await page.reload();
    await expect(wing).toBeVisible();
    await expect(scenes.getByRole('button', { name: 'day', exact: true })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });
}
