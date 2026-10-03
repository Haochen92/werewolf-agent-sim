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
 * The house never draws for a player who picked: a pick lost to someone else, before the join or
 * after it, keeps the pass up with a line naming the puppet, until another pick lands or the
 * player presses "Let the house draw". Only a game that has already begun lets them go without.
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
import { ApiError } from '@/lib/request';
import { MAX_NAME, nameProblem, tidyName } from '@/lib/names';
import { hostKey, seatToken } from '@/lib/storage';
import type { RoomInput } from '@/stage/scenes/types';
import type { CharacterCard, GameStatus } from '@/types/contracts';
import classes from './BoardingPass.module.css';

/** How a sent pick ended: it landed, another seat holds it, the game began, or it never arrived. */
export type PickOutcome = 'landed' | 'taken' | 'started' | 'failed';

/** Send this seat's pick (null: the house draws); a refusal comes back as an outcome, not a throw. */
export async function sendPick(gameId: string, id: string | null): Promise<PickOutcome> {
  try {
    await chooseCharacter(gameId, id);
    return 'landed';
  } catch (err) {
    if (!(err instanceof ApiError)) return 'failed';
    // 409 "already stands" = another seat has it; "already started" (or 410, ended) = too late
    if (err.isConflict && /already stands/i.test(err.message)) return 'taken';
    if ((err.isConflict && /started/i.test(err.message)) || err.status === 410)
      return 'started';
    return 'failed';
  }
}

/** A pick that landed, a game already under way, or the house's draw lets the player off the pass. */
export const leavesPass = (outcome: PickOutcome, id: string | null): boolean =>
  id === null || outcome === 'landed' || outcome === 'started';

/** The pass is up for a newcomer to an open room, and for a seat whose lost pick is unsettled. */
export function passIsUp(room: RoomInput, repicking: boolean): boolean {
  return repicking || (!room.seated && !room.locked && room.aboard.length < room.places);
}

/** A pick that got away: another seat holds it (`taken`), or the send never arrived. */
export interface LostPick {
  id: string;
  taken: boolean;
}

/** The pass's puppet block: the picker, and once a pick is lost, the line saying so and the house's draw. */
export function PassPuppets({
  cards,
  value,
  held,
  lost,
  busy,
  onPick,
  onHouseDraws,
}: {
  cards: readonly CharacterCard[];
  value: string | null;
  held: ReadonlyMap<string, string>;
  lost: LostPick | null;
  busy: boolean;
  onPick: (id: string | null) => void;
  onHouseDraws: () => void;
}) {
  const pickerId = useId();
  const name = lost ? (cards.find((c) => c.id === lost.id)?.display_name ?? lost.id) : '';
  return (
    <div className={classes.puppets}>
      <span className={classes.label} id={pickerId}>
        The puppet you stand as
      </span>
      {lost ? (
        <p className={classes.lost} role="alert">
          {lost.taken
            ? `Someone took the ${name}. Choose another puppet.`
            : `The ${name} did not reach the platform. Choose again.`}
        </p>
      ) : null}
      <PuppetPicker
        cards={cards}
        value={value}
        held={held}
        onChange={onPick}
        disabled={busy}
        labelledBy={pickerId}
        quiet={lost !== null}
      />
      {lost ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className={classes.house}
          disabled={busy}
          onClick={onHouseDraws}
        >
          Let the house draw
        </Button>
      ) : null}
    </div>
  );
}

export function BoardingPass({
  gameId,
  status,
  onBoarded,
  onWatch,
}: {
  gameId: string;
  status: GameStatus;
  /**
   * Joined: this device now holds a seat. `pickOpen` = its pick was lost, so the pass stays up;
   * called again with false once a pick lands or the house draws.
   */
  onBoarded: (pickOpen: boolean) => void;
  onWatch: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [choice, setChoice] = useState<string | null>(null);
  const [lost, setLost] = useState<LostPick | null>(null);
  // aboard with the pick lost after the join: from here a tap sends the pick straight away
  const [seated, setSeated] = useState(false);
  const cards = useCharacters();
  const players = status.players ?? [];
  const aboard = players.length;
  const places = status.max_seats || 9;
  const { held } = roomPicks(status);
  // someone else took it while this pass was open: the poll says so, the pick lapses, the pass says so
  if (choice && held.has(choice)) {
    setLost({ id: choice, taken: true });
    setChoice(null);
  }

  const settle = (outcome: PickOutcome, id: string | null) => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
    if (id && !leavesPass(outcome, id)) {
      setSeated(true);
      setLost({ id, taken: outcome === 'taken' });
      setChoice(null);
      onBoarded(true);
    } else onBoarded(false);
  };

  const join = useMutation({
    mutationFn: async ({ as, pick }: { as: string; pick: string | null }) => {
      // the creator boards with the host key, so the room knows which seat is its host's
      const seat = await joinGame(gameId, as, hostKey.get(gameId));
      // The token comes back exactly once; stash it as the cookie's backup immediately.
      seatToken.set(gameId, seat.token);
      if (!pick) return 'landed' as const;
      // aboard now: hold the pass up until the pick settles (the next poll would take it down)
      onBoarded(true);
      return sendPick(gameId, pick);
    },
    onSuccess: (outcome, { pick }) => settle(outcome, pick),
  });
  // after a lost pick: another puppet, or null for the house's draw
  const repick = useMutation({
    mutationFn: (id: string | null) => sendPick(gameId, id),
    onSuccess: settle,
  });
  const busy = join.isPending || repick.isPending;

  const onPick = (id: string | null) => {
    if (!seated) {
      setChoice(id);
      setLost(null);
    } else if (id) {
      // the line stays until this one lands or is lost too
      setChoice(id);
      repick.mutate(id);
    }
  };
  const onHouseDraws = () => {
    if (seated) repick.mutate(null);
    else setLost(null);
  };

  // said once something is typed; an empty box only keeps the button off
  const problem = nameProblem(name);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!busy && !seated && !problem && !lost)
      join.mutate({ as: tidyName(name), pick: choice });
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
          readOnly={seated}
          classNames={{ label: classes.label, input: classes.input }}
        />
        {cards.length > 0 ? (
          <PassPuppets
            cards={cards}
            value={choice}
            held={held}
            lost={lost}
            busy={busy}
            onPick={onPick}
            onHouseDraws={onHouseDraws}
          />
        ) : null}
        {seated ? null : (
          <div className={classes.actions}>
            <Button
              type="submit"
              variant="brass"
              loading={join.isPending}
              disabled={Boolean(problem) || lost !== null}
            >
              Step onto the platform
            </Button>
            <Button type="button" variant="ghost" onClick={onWatch}>
              Just watch
            </Button>
          </div>
        )}
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
