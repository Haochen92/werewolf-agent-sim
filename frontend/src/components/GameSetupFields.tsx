'use client';

/**
 * The fields every new game is configured with, whichever door it starts from: the model
 * the agents run on and the optional key that pays for it. `/play` and `/rooms/new` both
 * render this block; each adds its own field around it (the solo role picker, the room
 * name) and its own button. This mirrors the server, where both doors hand the registry
 * the same model + key and differ only in what surrounds them.
 */
import { useQuery } from '@tanstack/react-query';
import { getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ByokField } from '@/components/ByokField';
import classes from '@/components/Lobby.module.css';

export function GameSetupFields({
  model,
  onModelChange,
  apiKey,
  onApiKeyChange,
}: {
  model: string;
  onModelChange: (model: string) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
}) {
  const { data: models } = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: Infinity, // the menu is static for the process's lifetime
  });

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
          {/* First entry of the menu is the default for a bare key — say so plainly. */}
          <option value="">House default</option>
          {models?.models.map((row) => (
            <option key={row.model} value={row.model}>
              {row.label}
            </option>
          ))}
        </select>
      </div>

      <ByokField value={apiKey} onChange={onApiKeyChange} />
    </>
  );
}
