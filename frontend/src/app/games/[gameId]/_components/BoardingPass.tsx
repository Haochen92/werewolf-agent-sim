'use client';

/**
 * The boarding pass: the name a newcomer puts on the platform before they step onto it. The
 * one step on `/games/[id]` that is allowed upright (review 2026-09-26 §F1), because an invite
 * link is usually opened on a phone held upright; the platform itself is on the stage, sideways.
 *
 * The newcomer may pick their puppet here too, beside the name: the pass is the one form every
 * human in a room fills in (the host included), while the platform is a scene with no form on
 * it. A pick needs a seat, so it is held on the pass and sent right after the join; puppets the
 * others already hold are out of reach, and the roster shows who stands as what.
 *
 * Shown to a viewer with no seat while the room is open and has a place left. Boarding joins
 * the room there and then (the seat token comes back once and is kept on this device); "Just
 * watch" goes to the platform without a seat. A full or locked room skips this step.
 */
import { useId, useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TextInput } from '@mantine/core';
import { Button, Paper } from '@/components/site';
import { PickedRoster, PuppetPicker, roomPicks } from '@/components/PuppetPicker';
import { useCharacters } from '@/hooks/useCharacters';
import { chooseCharacter, joinGame } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { MAX_NAME, nameProblem, tidyName } from '@/lib/names';
import { hostKey, seatToken } from '@/lib/storage';
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
  const pickerId = useId();
  const [name, setName] = useState('');
  const [choice, setChoice] = useState<string | null>(null);
  const cards = useCharacters();
  const players = status.players ?? [];
  const aboard = players.length;
  const places = status.max_seats || 9;
  const { held } = roomPicks(status);
  // someone else may take it while this pass is open: the poll says so, and the pick lapses
  const pick = choice && !held.has(choice) ? choice : null;

  const join = useMutation({
    mutationFn: async (as: string) => {
      // the creator boards with the host key, so the room knows which seat is its host's
      const seat = await joinGame(gameId, as, hostKey.get(gameId));
      // The token comes back exactly once; stash it as the cookie's backup immediately.
      seatToken.set(gameId, seat.token);
      // aboard either way: a pick lost to a faster tap leaves the house to draw this seat's
      if (pick) await chooseCharacter(gameId, pick).catch(() => null);
    },
    onSuccess: () => {
      onBoarded();
      void queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
    },
  });

  // said once something is typed; an empty box only keeps the button off
  const problem = nameProblem(name);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!join.isPending && !problem) join.mutate(tidyName(name));
  };

  return (
    <main className={classes.wrap}>
      <Paper component="form" className={classes.pass} onSubmit={submit} data-boarding-pass>
        <span className={classes.kind}>Boarding pass</span>
        <h1 className={classes.title}>{status.name || 'Unnamed table'}</h1>
        <p className={classes.sub}>
          hosted by {status.host?.trim() || '—'}, {aboard} of {places} on the platform
        </p>
        {aboard > 0 && cards.length > 0 ? (
          <PickedRoster players={players} picks={status.characters ?? []} cards={cards} />
        ) : null}
        <TextInput
          label="Your name on the platform"
          placeholder="your name"
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
          maxLength={MAX_NAME}
          autoComplete="nickname"
          description={`${[...tidyName(name)].length} of ${MAX_NAME}`}
          error={name.trim() ? problem : null}
          classNames={{ label: classes.label, input: classes.input }}
        />
        {cards.length > 0 ? (
          <div className={classes.puppets}>
            <span className={classes.label} id={pickerId}>
              The puppet you stand as
            </span>
            <PuppetPicker
              cards={cards}
              value={pick}
              held={held}
              onChange={setChoice}
              disabled={join.isPending}
              labelledBy={pickerId}
            />
          </div>
        ) : null}
        <div className={classes.actions}>
          <Button
            type="submit"
            variant="brass"
            loading={join.isPending}
            disabled={Boolean(problem)}
          >
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
