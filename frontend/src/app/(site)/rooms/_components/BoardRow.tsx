'use client';
/**
 * One room on the departures board: its status on split-flap tiles, the room's name and host,
 * how many are aboard (a pip per place), and the Board button.
 *
 * Board opens a strip under the row that asks for the name to put on the manifest, then joins
 * the room there and then. The seat token that comes back is kept on this device, and the page
 * goes to the room (`/games/[id]`). A locked or full room keeps its row, with the button off and
 * the reason next to it. When the server refuses a join (the room filled or locked while the
 * strip was open, or the game started), its words show in the strip.
 *
 * A room this device is already in (it holds the seat token, or the host key of the room it
 * opened) offers the way back instead of Board, full or locked alike: boarding again would
 * only put a second name on the manifest.
 */
import { useId, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { Alert, TextInput } from '@mantine/core';
import { joinGame } from '@/lib/api';
import { MAX_NAME, nameProblem, tidyName } from '@/lib/names';
import { hostKey, seatToken } from '@/lib/storage';
import { timeAgo } from '@/lib/format';
import { Button, Flapword, Icon } from '@/components/site';
import type { RoomSummary } from '@/types/contracts';
import { aboardLine, hostName, rowFace } from './boarding';
import classes from './Departures.module.css';

export function BoardRow({ room }: { room: RoomSummary }) {
  const router = useRouter();
  const ids = useId();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const face = rowFace(room);
  const opened = timeAgo(room.created_at);
  // rows render only after the client fetch, so reading this device's storage here is safe
  const seated = Boolean(seatToken.get(room.game_id));
  const mine = seated || Boolean(hostKey.get(room.game_id));

  const join = useMutation({
    mutationFn: () => joinGame(room.game_id, tidyName(name)),
    onSuccess: (seat) => {
      seatToken.set(room.game_id, seat.token);
      router.push(`/games/${room.game_id}`);
    },
  });

  const problem = nameProblem(name);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!join.isPending && face.joinable && !problem) join.mutate();
  };

  const watch = (
    <Link href={`/games/${room.game_id}`} className={classes.watch}>
      Watch instead
    </Link>
  );

  return (
    <li
      className={classes.row}
      data-room={room.game_id}
      data-state={face.state}
      aria-busy={join.isPending}
    >
      <div className={classes.st}>
        <Flapword text={face.flap} tone={face.tone} className={classes.flap} />
      </div>

      <div className={classes.rm}>
        <div className={classes.nm}>
          {room.name || 'Unnamed table'}
          {room.locked ? <Icon name="i-lock" size={16} label="Locked" /> : null}
        </div>
        <div className={classes.sub}>
          <span>hosted by {hostName(room)}</span>
          {opened ? <span>opened {opened}</span> : null}
        </div>
        {face.reason && !mine ? (
          <p className={classes.reason} id={`${ids}-why`}>
            {face.reason} {watch}
          </p>
        ) : null}
      </div>

      <div className={classes.seats}>
        <div className={classes.pips} aria-hidden="true">
          {Array.from({ length: room.max_seats }, (_, i) => {
            const player = room.players[i];
            return player ? (
              <i key={i} className={classes.aboard}>
                {[...player.trim()][0]?.toUpperCase() ?? '?'}
              </i>
            ) : (
              <i key={i} className={classes.open} />
            );
          })}
        </div>
        <div className={classes.cap}>{aboardLine(room.players.length, room.max_seats)}</div>
      </div>

      <div className={classes.act}>
        {mine ? (
          <Button
            component={Link}
            href={`/games/${room.game_id}`}
            variant="primary"
            size="sm"
          >
            {seated ? 'Return to your seat' : 'Return to your room'}
          </Button>
        ) : face.joinable ? (
          <Button
            variant={open ? 'ghost' : 'primary'}
            size="sm"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls={`${ids}-pass`}
          >
            {open ? 'Cancel' : 'Board'}
          </Button>
        ) : (
          <Button
            size="sm"
            disabled
            aria-describedby={`${ids}-why`}
            leftSection={face.state === 'locked' ? <Icon name="i-lock" size={15} /> : null}
          >
            {face.state === 'locked' ? 'Locked' : 'Full'}
          </Button>
        )}
      </div>

      {open && !mine && (face.joinable || join.error) ? (
        <form
          id={`${ids}-pass`}
          className={classes.pass}
          onSubmit={submit}
          aria-label={`Board ${room.name || 'Unnamed table'}`}
        >
          <TextInput
            label="Your name on the manifest"
            placeholder="your name"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            maxLength={MAX_NAME}
            autoComplete="nickname"
            description={`${[...tidyName(name)].length} of ${MAX_NAME}`}
            error={name.trim() ? problem : null}
            autoFocus
            disabled={join.isPending}
            className={classes.passName}
          />
          <Button
            type="submit"
            variant="primary"
            size="sm"
            loading={join.isPending}
            disabled={!face.joinable || Boolean(problem)}
          >
            Join
          </Button>
          {join.error ? (
            <Alert
              title="You could not board"
              icon={<Icon name="i-x" size={16} />}
              className={classes.passAlert}
              role="alert"
            >
              {join.error.message || 'Could not join.'} {watch}
            </Alert>
          ) : null}
        </form>
      ) : null}
    </li>
  );
}
