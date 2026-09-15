'use client';

/**
 * D3 — the solo door. One centred card, three groups top-down: role picker, then the
 * shared setup fields (model select, BYOK). One primary button.
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
import { useMutation } from '@tanstack/react-query';
import { createGame } from '@/lib/api';
import { seatToken } from '@/lib/storage';
import { humanise } from '@/lib/format';
import { RoleIcon } from '@/components/RoleIcon';
import { GameSetupFields } from '@/components/GameSetupFields';
import type { Role } from '@/types/contracts';
import classes from '@/components/Lobby.module.css';

/** The castable roles. Fixed 9-player 3-faction casting is a server ruling, not a choice. */
const ROLES: Role[] = ['villager', 'wolf', 'healer', 'investigator', 'vigilante', 'serial_killer'];

export function PlayClient() {
  const router = useRouter();
  const [role, setRole] = useState<Role | null>(null);
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [needsKey, setNeedsKey] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

        <GameSetupFields
          model={model}
          onModelChange={setModel}
          apiKey={apiKey}
          onApiKeyChange={setApiKey}
          onNeedsKeyChange={setNeedsKey}
        />

        <button
          type="button"
          className={classes.primary}
          onClick={() => create.mutate()}
          disabled={create.isPending || (needsKey && !apiKey.trim())}
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
