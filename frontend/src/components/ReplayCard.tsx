'use client';

import Link from 'next/link';
import type { ReplaySummary, Winner } from '@/types/contracts';
import { timeAgo } from '@/lib/format';
import classes from './ReplayCard.module.css';

const FACTION_CLASS: Record<Winner, string> = {
  villagers: classes.villagers,
  wolves: classes.wolves,
  serial_killer: classes.serialKiller,
};

const FACTION_LABEL: Record<Winner, string> = {
  villagers: 'Villagers win',
  wolves: 'Wolves win',
  serial_killer: 'Serial killer wins',
};

/** Who won, in the winning side's colour: the first thing a card says. */
function WinnerChip({ winner }: { winner: Winner }) {
  return (
    <span className={`${classes.winnerChip} ${FACTION_CLASS[winner]}`}>
      {FACTION_LABEL[winner]}
    </span>
  );
}

export function ReplayCard({ replay }: { replay: ReplaySummary }) {
  const seats = Object.values(replay.cast_role_counts).reduce((a, b) => a + b, 0);

  return (
    <Link href={`/replays/${replay.game_id}`} className={classes.card}>
      {/* Chips first, meta second: one row of variable-width chips wrapping against a
          fixed meta line is stable at every width, where one mixed row wrapped or not
          depending on how long the winner's name happened to be. */}
      <div className={classes.chips}>
        <WinnerChip winner={replay.winner} />
        {replay.n_humans > 0 ? (
          <span className={classes.humans}>
            {replay.n_humans} human{replay.n_humans > 1 ? 's' : ''}
          </span>
        ) : null}
      </div>
      <div className={classes.meta}>
        {replay.days} days · {seats} seats
      </div>
      <div className={classes.foot}>
        {/* The cast is the same nine roles in every game, so it says nothing here and
            lives in the theater header instead. The model does vary, and which model
            played a game is the most interesting thing a browsing visitor can compare
            across the rail. Empty for games archived before the column existed. */}
        <span className={classes.model}>{replay.model}</span>
        <span>{timeAgo(replay.finished_at)}</span>
      </div>
    </Link>
  );
}

export function ReplayGrid({ replays }: { replays: ReplaySummary[] }) {
  return (
    <div className={classes.grid}>
      {replays.map((replay) => (
        <ReplayCard key={replay.game_id} replay={replay} />
      ))}
    </div>
  );
}
