'use client';

/**
 * D6/D7 — the lobby, `/games/[id]` in its `waiting` state. Driven entirely by the status
 * poll, since a lobby has no event stream worth speaking of.
 *
 * The share link is the host's PRIMARY action, in the top slot: an empty room is a dead
 * room. A joiner's lobby differs only in what is absent (start and lock), never in layout.
 * There is no lobby chat — no backend carries it, and faking an affordance is worse than
 * omitting one.
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { joinGame, lockRoom, startGame } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { queryKeys } from '@/lib/queryKeys';
import { hostKey as hostKeyStore, seatToken } from '@/lib/storage';
import type { GameStatus } from '@/types/contracts';
import { SeatChip } from './SeatChip';
import classes from './Lobby.module.css';

export function LobbyCard({ gameId, status }: { gameId: string; status: GameStatus }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const storedHostKey = hostKeyStore.get(gameId);
  const isHost = Boolean(storedHostKey);
  const seated = Boolean(status.you) || Boolean(seatToken.get(gameId));
  const players = status.players ?? [];
  const full = status.max_seats > 0 && players.length >= status.max_seats;

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });

  const join = useMutation({
    mutationFn: () => joinGame(gameId, name.trim() || 'human'),
    onSuccess: (seat) => {
      // The token comes back exactly once; stash it as the cookie's backup immediately.
      seatToken.set(gameId, seat.token);
      setError(null);
      refresh();
    },
    onError: (err) => setError(err instanceof Error ? err.message : 'Could not join.'),
  });

  const start = useMutation({
    mutationFn: () => startGame(gameId, storedHostKey),
    onSuccess: () => {
      // host_key has exactly one use and it is spent; keeping it invites confusion later.
      hostKeyStore.clear(gameId);
      refresh();
    },
    onError: (err) => setError(err instanceof Error ? err.message : 'Could not start.'),
  });

  const lock = useMutation({
    mutationFn: () => lockRoom(gameId, !status.locked, storedHostKey ?? ''),
    onSuccess: refresh,
    onError: (err) =>
      setError(err instanceof Error ? err.message : 'Could not change the lock.'),
  });

  const shareLink =
    typeof window === 'undefined' ? '' : `${window.location.origin}/games/${gameId}`;

  return (
    <div className={classes.wrap}>
      <div className={classes.card}>
        <div className={classes.head}>
          <h1 className={classes.name}>{status.name || 'Unnamed table'}</h1>
          <span className={classes.count}>
            {players.length}/{status.max_seats || '?'}
          </span>
          {status.locked ? (
            <span className={classes.lockChip} title="Locked — no new players">
              locked
            </span>
          ) : null}
        </div>

        <div className={classes.shareRow}>
          <input className={classes.shareInput} readOnly value={shareLink} />
          <button
            type="button"
            className={classes.copyButton}
            onClick={() => {
              void navigator.clipboard?.writeText(shareLink);
              setCopied(true);
              setTimeout(() => setCopied(false), 1600);
            }}
          >
            {copied ? 'copied' : 'copy'}
          </button>
        </div>

        <ul className={classes.roster}>
          {players.map((player) => (
            <li key={player}>
              <SeatChip seat={player} isSelf={player === status.you} />
            </li>
          ))}
          {/* Capacity shown as empty seats, so a half-full room reads as one. */}
          {Array.from({ length: Math.max(0, status.max_seats - players.length) }).map(
            (_, i) => (
              <li key={`empty-${i}`} className={classes.empty}>
                ○ empty
              </li>
            ),
          )}
        </ul>

        {!seated && !full && !status.locked ? (
          <div className={classes.joinRow}>
            <input
              className={classes.nameInput}
              placeholder="your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={24}
            />
            <button
              type="button"
              className={classes.primary}
              onClick={() => join.mutate()}
              disabled={join.isPending}
            >
              Take a seat
            </button>
          </div>
        ) : null}

        {!seated && (full || status.locked) ? (
          <p className={classes.note}>
            {status.locked ? 'This table is locked.' : 'This table is full.'} You can still{' '}
            <Link href={`/games/${gameId}`} className={classes.inlineLink}>
              watch
            </Link>
            .
          </p>
        ) : null}

        <div className={classes.actions}>
          {isHost ? (
            <>
              <button
                type="button"
                className={classes.primary}
                onClick={() => start.mutate()}
                disabled={start.isPending || players.length < 1}
              >
                Start game
              </button>
              <button
                type="button"
                className={classes.secondary}
                onClick={() => lock.mutate()}
                disabled={lock.isPending}
              >
                {status.locked ? 'Unlock' : 'Lock'}
              </button>
            </>
          ) : (
            <p className={classes.note}>Waiting for the host to start…</p>
          )}
        </div>

        {error ? (
          <p className={classes.error} role="alert">
            {error}
          </p>
        ) : null}
      </div>

      <p className={classes.spectate}>
        Not playing? This page becomes the table when the game starts — just leave it open.
      </p>
    </div>
  );
}

/** D23: the game task died. No retry affordance — the server holds no way back. */
export function TerminalError({ message, byok }: { message: string; byok?: boolean }) {
  return (
    <div className={classes.wrap}>
      <div className={`${classes.card} ${classes.terminal}`}>
        <h1 className={classes.name}>This game has ended unexpectedly</h1>
        <p className={classes.note}>{message}</p>
        {byok ? (
          <p className={classes.note}>
            Games started with your own API key don’t survive a server restart — the key is
            never stored, which is exactly why.
          </p>
        ) : null}
        <Link href="/" className={classes.primary}>
          Back to the start
        </Link>
      </div>
    </div>
  );
}

export { ApiError };
