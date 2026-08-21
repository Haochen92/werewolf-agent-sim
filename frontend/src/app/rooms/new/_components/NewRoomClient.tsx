'use client';

/**
 * D4 — create a room. Same card pattern as the solo door, minus the role picker: rooms deal
 * random seats by server ruling, so the concept is unrepresentable here rather than guarded.
 *
 * On success the host_key is stashed before navigating. It is returned exactly once, it is
 * the only proof of hosting, and its single use is the start button.
 */
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createRoom, getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { hostKey } from '@/lib/storage';
import { ByokField } from '@/components/ByokField';
import classes from '@/components/Lobby.module.css';

export function NewRoomClient() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data: models } = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: Infinity,
  });

  const create = useMutation({
    mutationFn: () => createRoom({ name: name.trim(), model, api_key: apiKey }),
    onSuccess: (room) => {
      hostKey.set(room.game_id, room.host_key);
      router.push(`/games/${room.game_id}`);
    },
    onError: (err) =>
      setError(err instanceof Error ? err.message : 'Could not open a room.'),
  });

  return (
    <div className={classes.wrap}>
      <div className={classes.card}>
        <div className={classes.head}>
          <h1 className={classes.name}>Open a table</h1>
          <Link href="/rooms" className={classes.inlineLink}>
            ← rooms
          </Link>
        </div>

        <div className={classes.group}>
          <label className={classes.label} htmlFor="room-name">
            Table name
          </label>
          <input
            id="room-name"
            className={classes.textInput}
            style={{ width: '100%' }}
            placeholder="Unnamed table"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={40}
          />
        </div>

        <div className={classes.group}>
          <label className={classes.label} htmlFor="room-model">
            Model for the agents
          </label>
          <select
            id="room-model"
            className={classes.select}
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="">House default</option>
            {models?.models.map((row) => (
              <option key={row.model} value={row.model}>
                {row.label}
              </option>
            ))}
          </select>
        </div>

        <ByokField value={apiKey} onChange={setApiKey} />

        <button
          type="button"
          className={classes.primary}
          onClick={() => create.mutate()}
          disabled={create.isPending}
        >
          {create.isPending ? 'Opening…' : 'Open the room'}
        </button>

        {error ? (
          <p className={classes.error} role="alert">
            {error}
          </p>
        ) : null}

        <p className={classes.fine}>
          You’ll get a share link on the next screen. Agents fill any seats nobody takes.
        </p>
      </div>
    </div>
  );
}
