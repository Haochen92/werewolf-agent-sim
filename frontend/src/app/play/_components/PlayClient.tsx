'use client';

/**
 * D3 — the solo door. One centred card, three groups top-down: role picker, model select,
 * BYOK field. One primary button.
 *
 * Solo games auto-start, so submitting redirects straight to `/games/[id]`, which opens in
 * `running` — the player's first screen is the role reveal (D8).
 *
 * Role choice is solo-only by server ruling: rooms always deal random seats, so this picker
 * exists on this page and nowhere else.
 */
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createGame, getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { seatToken } from '@/lib/storage';
import { humanise } from '@/lib/format';
import { RoleIcon } from '@/components/RoleIcon';
import { ByokField } from '@/components/ByokField';
import classes from '@/components/Lobby.module.css';

/** The castable roles. Fixed 9-player 3-faction casting is a server ruling, not a choice. */
const ROLES = ['villager', 'wolf', 'healer', 'investigator', 'vigilante', 'serial_killer'];

export function PlayClient() {
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data: models } = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: Infinity, // the menu is static for the process's lifetime
  });

  const create = useMutation({
    mutationFn: () =>
      createGame({
        human: true,
        human_role: role,
        api_key: apiKey,
        model,
      }),
    onSuccess: (game) => {
      // The seat token comes back exactly once — stash it before navigating, or a cookie
      // loss later has nothing to rejoin with.
      if (game.seat_token) seatToken.set(game.game_id, game.seat_token);
      router.push(`/games/${game.game_id}`);
    },
    onError: (err) =>
      setError(err instanceof Error ? err.message : 'Could not start a game.'),
  });

  return (
    <div className={classes.wrap}>
      <div className={classes.card}>
        <div className={classes.head}>
          <h1 className={classes.name}>Take a seat</h1>
          <Link href="/" className={classes.inlineLink}>
            ← home
          </Link>
        </div>

        <div className={classes.group}>
          <span className={classes.label}>Your role</span>
          <div className={classes.roleGrid}>
            <button
              type="button"
              className={`${classes.roleOption} ${role === null ? classes.rolePicked : ''}`}
              onClick={() => setRole(null)}
            >
              Random
            </button>
            {ROLES.map((option) => (
              <button
                key={option}
                type="button"
                className={`${classes.roleOption} ${role === option ? classes.rolePicked : ''}`}
                onClick={() => setRole(option)}
              >
                <RoleIcon role={option} />
                {humanise(option)}
              </button>
            ))}
          </div>
        </div>

        <div className={classes.group}>
          <label className={classes.label} htmlFor="model">
            Model
          </label>
          <select
            id="model"
            className={classes.select}
            value={model}
            onChange={(e) => setModel(e.target.value)}
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

        <ByokField value={apiKey} onChange={setApiKey} />

        <button
          type="button"
          className={classes.primary}
          onClick={() => create.mutate()}
          disabled={create.isPending}
        >
          {create.isPending ? 'Dealing…' : 'Take your seat'}
        </button>

        {error ? (
          <p className={classes.error} role="alert">
            {error}
          </p>
        ) : null}

        <p className={classes.fine}>
          Eight agents will fill the rest of the table. The game starts the moment you sit
          down.
        </p>
      </div>
    </div>
  );
}
