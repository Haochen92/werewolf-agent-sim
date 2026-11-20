'use client';
/**
 * One room on the departures board: its status on split-flap tiles, the room's name and host,
 * how many are aboard (a pip per place), and the Board button.
 *
 * Board goes to the room (`/games/[id]`), whose boarding pass takes the name and the puppet: the
 * pass is the one form every human in a room fills in, so the board has no join of its own. A
 * locked or full room keeps its row, with the button off and the reason next to it.
 *
 * A room this device is already in (it holds the seat token, or the host key of the room it
 * opened) offers the way back instead of Board, full or locked alike: boarding again would
 * only put a second name on the manifest.
 */
import { useId } from 'react';
import Link from 'next/link';
import { Anchor } from '@mantine/core';
import { hostKey, seatToken } from '@/lib/storage';
import { timeAgo } from '@/lib/format';
import { Button, Flapword, Icon } from '@/components/site';
import type { RoomSummary } from '@/types/contracts';
import { aboardLine, hostName, rowFace } from './boarding';
import classes from './Departures.module.css';

export function BoardRow({ room }: { room: RoomSummary }) {
  const ids = useId();
  const face = rowFace(room);
  const opened = timeAgo(room.created_at);
  // rows render only after the client fetch, so reading this device's storage here is safe
  const seated = Boolean(seatToken.get(room.game_id));
  const mine = seated || Boolean(hostKey.get(room.game_id));

  const watch = (
    <Anchor component={Link} href={`/games/${room.game_id}`} className={classes.watch}>
      Watch instead
    </Anchor>
  );

  return (
    <li className={classes.row} data-room={room.game_id} data-state={face.state}>
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
            variant="plate"
            size="sm"
          >
            {seated ? 'Return to your seat' : 'Return to your room'}
          </Button>
        ) : face.joinable ? (
          <Button component={Link} href={`/games/${room.game_id}`} size="sm">
            Board
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
    </li>
  );
}
