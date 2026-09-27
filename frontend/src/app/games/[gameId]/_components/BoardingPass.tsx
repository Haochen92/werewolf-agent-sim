'use client';

/**
 * The boarding pass: the name a newcomer puts on the platform before they step onto it. The
 * one step on `/games/[id]` that is allowed upright (review 2026-09-26 §F1), because an invite
 * link is usually opened on a phone held upright; the platform itself is on the stage, sideways.
 *
 * Shown to a viewer with no seat while the room is open and has a place left. Boarding joins
 * the room there and then (the seat token comes back once and is kept on this device); "Just
 * watch" goes to the platform without a seat. A full or locked room skips this step.
 */
import { useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TextInput } from '@mantine/core';
import { Button, Paper } from '@/components/site';
import { joinGame } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { seatToken } from '@/lib/storage';
import type { GameStatus } from '@/types/contracts';
import classes from './BoardingPass.module.css';

export function BoardingPass({
  gameId,
  status,
  onBoarded,
  onWatch,
}: {
  gameId: string;
  status: GameStatus;
  /** Joined: this device now holds a seat. */
  onBoarded: () => void;
  onWatch: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const aboard = status.players?.length ?? 0;
  const places = status.max_seats || 9;

  const join = useMutation({
    mutationFn: (as: string) => joinGame(gameId, as),
    onSuccess: (seat) => {
      // The token comes back exactly once; stash it as the cookie's backup immediately.
      seatToken.set(gameId, seat.token);
      onBoarded();
      void queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
    },
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!join.isPending) join.mutate(name.trim() || 'human');
  };

  return (
    <main className={classes.wrap}>
      <Paper component="form" className={classes.pass} onSubmit={submit} data-boarding-pass>
        <span className={classes.kind}>Boarding pass</span>
        <h1 className={classes.title}>{status.name || 'Unnamed table'}</h1>
        <p className={classes.sub}>
          hosted by {status.host?.trim() || '—'}, {aboard} of {places} on the platform
        </p>
        <TextInput
          label="Your name on the platform"
          placeholder="your name"
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
          maxLength={24}
          autoComplete="nickname"
          classNames={{ label: classes.label, input: classes.input }}
        />
        <div className={classes.actions}>
          <Button type="submit" variant="brass" loading={join.isPending}>
            Step onto the platform
          </Button>
          <Button type="button" variant="ghost" onClick={onWatch}>
            Just watch
          </Button>
        </div>
        {join.error ? (
          <p className={classes.error} role="alert">
            {join.error instanceof Error ? join.error.message : 'Could not board.'}
          </p>
        ) : null}
        <p className={classes.fine}>
          Seats and roles are dealt when the train departs; agents take the empty places.
        </p>
      </Paper>
    </main>
  );
}
