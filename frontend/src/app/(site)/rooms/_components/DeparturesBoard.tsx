'use client';
/**
 * The departures board (rooms mockup, review §A3): every room still waiting for players, one row
 * each, read from `GET /rooms` and read again every ten seconds, because rooms fill while you
 * look at them. Rows, not cards: a list of rooms is scanned, and rows still work when there are
 * many.
 *
 * Only the Boarding list ships. The mockup's "Under way" tab, room codes, watchers and the
 * model and memory terms have nothing on the wire yet (review §F8), so they are left out rather
 * than drawn empty.
 *
 * States: loading (skeleton rows), the board could not be read (an alert with a retry), no
 * rooms open, and the rows; each row carries its own boarding, joining and refused states.
 */
import type { CSSProperties } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Alert, Skeleton } from '@mantine/core';
import { listRooms } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { SPRITES } from '@/assets/manifest';
import { Button, Flapword, Icon } from '@/components/site';
import { BoardRow } from './BoardRow';
import classes from './Departures.module.css';

const REFRESH_MS = 10_000;

export function DeparturesBoard() {
  const rooms = useQuery({
    queryKey: queryKeys.rooms.list(),
    queryFn: listRooms,
    refetchInterval: REFRESH_MS, // rooms fill up while you look at them
  });
  const rows = rooms.data;

  let face;
  if (rooms.isPending) {
    face = (
      <>
        <ColHead />
        <ul className={classes.rows} aria-label="Loading rooms">
          {[0, 1, 2].map((i) => (
            <li key={i} className={classes.row}>
              <div className={classes.st}>
                <Skeleton height={22} width={112} radius={3} />
              </div>
              <div className={classes.rm}>
                <Skeleton height={16} width="55%" radius="sm" />
                <Skeleton height={12} width="35%" radius="sm" mt={10} />
              </div>
              <div className={classes.seats}>
                <Skeleton height={19} width={190} radius="xl" />
              </div>
              <div className={classes.act}>
                <Skeleton height={36} width={96} radius="xl" />
              </div>
            </li>
          ))}
        </ul>
      </>
    );
  } else if (!rows) {
    face = (
      <div className={classes.failed}>
        <Alert
          title="The board could not be read"
          icon={<Icon name="i-x" size={16} />}
          role="alert"
        >
          The server said: {rooms.error?.message || 'nothing at all.'}
        </Alert>
        <Button onClick={() => rooms.refetch()} loading={rooms.isFetching}>
          Try again
        </Button>
      </div>
    );
  } else if (rows.length === 0) {
    face = (
      <div className={classes.empty}>
        <Flapword text="NO DEPARTURES" tone="dim" className={classes.emptyFlap} />
        <p>
          No tables open right now. Open one and send the link to your friends, or play a
          solo game while you wait.
        </p>
        <div className={classes.emptyDoors}>
          <Button component={Link} href="/rooms/new" variant="primary">
            Open a table
          </Button>
          <Button component={Link} href="/play">
            Play solo
          </Button>
        </div>
      </div>
    );
  } else {
    face = (
      <>
        <ColHead />
        <ul className={classes.rows} aria-label="Rooms boarding">
          {rows.map((room) => (
            <BoardRow key={room.game_id} room={room} />
          ))}
        </ul>
      </>
    );
  }

  return (
    <section
      className={classes.board}
      aria-labelledby="departures"
      style={{ '--wood': `url(${SPRITES.wood.src})` } as CSSProperties}
    >
      <div className={classes.bezel}>
        <h2 className={classes.plate} id="departures">
          Departures
        </h2>
        <span className={classes.count}>
          Boarding <span className={classes.n}>{rows ? rows.length : '·'}</span>
        </span>
      </div>
      <div className={classes.face} aria-busy={rooms.isPending}>
        {face}
      </div>
      <div className={classes.bfoot}>
        <span>
          A locked room stays on the board, but admits nobody until its host unlocks it.
        </span>
        <span aria-live="polite">
          {rows && rooms.isError
            ? 'Could not refresh; trying again'
            : 'Updated every 10 seconds'}
        </span>
      </div>
    </section>
  );
}

function ColHead() {
  return (
    <div className={classes.colhead} aria-hidden="true">
      <span>Status</span>
      <span>Room</span>
      <span>Aboard</span>
      <span />
    </div>
  );
}
