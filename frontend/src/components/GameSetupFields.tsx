'use client';

/**
 * The fields every new game is configured with, whichever door it starts from: the model
 * the agents run on and the optional key that pays for it. `/play` and `/rooms/new` both
 * render this block; each adds its own field around it (the solo role picker, the room
 * name) and its own button. This mirrors the server, where both doors hand the registry
 * the same model + key and differ only in what surrounds them.
 *
 * Who pays is said before the submit, not after it fails. Each row is tagged "house pays"
 * or "your key", the status line under the select says what the house will do right now
 * (how many games are left today, or when it reopens), and the parent learns through
 * `onNeedsKeyChange` whether the chosen row needs the player's key so it can hold the
 * submit until one is typed. A player may always bring a key, even for a house row.
 */
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import type { ModelsMenu } from '@/types/contracts';
import { ByokField } from '@/components/ByokField';
import classes from '@/components/Lobby.module.css';

/** Whether the chosen row needs the player's key right now. The server says; the door applies the same rule. */
export function needsKey(menu: ModelsMenu | undefined, model: string): boolean {
  if (!menu) return false;
  const row = menu.models.find((r) => r.model === model) ?? menu.models.find((r) => r.is_default);
  return row?.needs_key ?? false;
}

function houseLine(menu: ModelsMenu, model: string): string {
  const row = menu.models.find((r) => r.model === model);
  if (!row) return '';
  if (!row.house_funded) return 'This model runs on your own key.';
  const { enabled, remaining, games_per_day, reset_at } = menu.house;
  if (!enabled) return 'House funding is switched off for now. Enter your key to play.';
  if (remaining <= 0) {
    const at = new Date(reset_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `The house has funded its ${games_per_day} games for today (more at ${at}). Enter your key to play now.`;
  }
  return `The house pays for this model: ${remaining} of ${games_per_day} games left today. Your own key is optional.`;
}

export function GameSetupFields({
  model,
  onModelChange,
  apiKey,
  onApiKeyChange,
  onNeedsKeyChange,
}: {
  model: string;
  onModelChange: (model: string) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  onNeedsKeyChange?: (needsKey: boolean) => void;
}) {
  const { data: menu } = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: 30_000, // the purse changes as games start; the menu itself is static
  });

  // The default is a live server setting: preselect it once the menu arrives, so the
  // select never shows a blank and the status line always describes a real row.
  useEffect(() => {
    if (!menu || model) return;
    const row = menu.models.find((r) => r.is_default) ?? menu.models[0];
    if (row) onModelChange(row.model);
  }, [menu, model, onModelChange]);

  const required = needsKey(menu, model);
  useEffect(() => {
    onNeedsKeyChange?.(required);
  }, [required, onNeedsKeyChange]);

  return (
    <>
      <div className={classes.group}>
        <label className={classes.label} htmlFor="model">
          Model for the agents
        </label>
        <select
          id="model"
          className={classes.select}
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
        >
          {menu?.models.map((row) => (
            <option key={row.model} value={row.model}>
              {row.label}
              {row.is_default ? ' · default' : ''}
              {row.house_funded ? ' · house pays' : ' · your key'}
            </option>
          ))}
        </select>
        {menu ? <p className={classes.fine}>{houseLine(menu, model)}</p> : null}
      </div>

      <ByokField value={apiKey} onChange={onApiKeyChange} />
    </>
  );
}
