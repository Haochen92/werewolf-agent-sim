'use client';

/**
 * A live game that lost its funding in a server restart: it ran on a player's key, which
 * the server never stores, so it was rebuilt idle and waits for a seat holder to enter the
 * key again. Any seat holder may (funding is a favour, not a privilege); spectators only
 * see why the game is paused. The key is tried on the provider before the game moves, so a
 * refused key is reported here rather than killing the game on its next turn.
 */
import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fundGame } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import type { GameStatus } from '@/types/contracts';
import { ByokField } from './ByokField';
import classes from './Lobby.module.css';

export function KeyNeededCard({ gameId, status }: { gameId: string; status: GameStatus }) {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const seated = Boolean(status.you);

  const fund = useMutation({
    mutationFn: () => fundGame(gameId, apiKey),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
    },
    onError: (err) => setError(err instanceof Error ? err.message : 'The key was refused.'),
  });

  return (
    <div className={classes.wrap}>
      <div className={classes.card}>
        <h1 className={classes.name}>This game is waiting for its key</h1>
        <p className={classes.note}>
          It was started with a player’s own API key. The server never stores keys, so after
          a restart the game can’t continue until one of its players enters the key again.
        </p>
        {seated ? (
          <>
            <ByokField value={apiKey} onChange={setApiKey} />
            <button
              type="button"
              className={classes.primary}
              onClick={() => fund.mutate()}
              disabled={fund.isPending || !apiKey.trim()}
            >
              {fund.isPending ? 'Checking the key…' : 'Resume with this key'}
            </button>
            {error ? (
              <p className={classes.error} role="alert">
                {error}
              </p>
            ) : null}
          </>
        ) : (
          <p className={classes.note}>
            You’re watching. One of the players can resume it from their seat.
          </p>
        )}
        <Link href="/" className={classes.inlineLink}>
          Back to the start
        </Link>
      </div>
    </div>
  );
}
