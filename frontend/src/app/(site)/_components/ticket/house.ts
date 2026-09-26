/**
 * Who pays for a new game, read from `GET /models`: the house (a fixed number of free games a
 * day, `server/house.py`) or the player's own key. The server decides per row (`needs_key`);
 * the ticket office only applies its answer, so the key field appears exactly when the server
 * would refuse the game without one. A player may always bring a key, even for a house row.
 *
 * Moved here from `GameSetupFields` (the August setup form) with its copy unchanged.
 */
import type { ModelRow, ModelsMenu } from '@/types/contracts';

/** The row a blank or unknown choice falls back to: the server's live default. */
export function defaultRow(menu: ModelsMenu): ModelRow | undefined {
  return menu.models.find((r) => r.is_default) ?? menu.models[0];
}

/** Whether the chosen row needs the player's key right now. The server says; the door applies the same rule. */
export function needsKey(menu: ModelsMenu | undefined, model: string): boolean {
  if (!menu) return false;
  const row =
    menu.models.find((r) => r.model === model) ?? menu.models.find((r) => r.is_default);
  return row?.needs_key ?? false;
}

/** The status line for the chosen row: what the house will do right now. */
export function houseLine(menu: ModelsMenu, model: string): string {
  const row = menu.models.find((r) => r.model === model);
  if (!row) return '';
  if (!row.house_funded) return 'This model runs on your own key.';
  const { enabled, remaining, games_per_day, reset_at } = menu.house;
  if (!enabled) return 'House funding is switched off for now. Enter your key to play.';
  if (remaining <= 0) {
    const at = new Date(reset_at).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    return `The house has funded its ${games_per_day} games for today (more at ${at}). Enter your key to play now.`;
  }
  return `The house pays for this model: ${remaining} of ${games_per_day} games left today. Your own key is optional.`;
}
