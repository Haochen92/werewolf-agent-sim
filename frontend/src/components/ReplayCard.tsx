'use client';

import Link from 'next/link';
import type { ReplaySummary, Winner } from '@/types/contracts';
import { describeCast, timeAgo } from '@/lib/format';
import { WinnerChip } from './theater-parts';
import classes from './ReplayCard.module.css';

const FACTIONS = new Set<string>(['villagers', 'wolves', 'serial_killer']);

export function ReplayCard({ replay }: { replay: ReplaySummary }) {
  const seats = Object.values(replay.cast_role_counts).reduce((a, b) => a + b, 0);

  return (
    <Link href={`/replays/${replay.game_id}`} className={classes.card}>
      <div className={classes.cardTop}>
        {/* `winner` is a bare string on the wire; only render a faction chip for a value
            we actually have a colour for, rather than inventing one. */}
        {FACTIONS.has(replay.winner) ? (
          <WinnerChip winner={replay.winner as Winner} />
        ) : null}
        <span className={classes.days}>
          {replay.days} days · {seats} seats
        </span>
        {replay.n_humans > 0 ? (
          <span className={classes.humans}>
            {replay.n_humans} human{replay.n_humans > 1 ? 's' : ''}
          </span>
        ) : null}
      </div>
      <div className={classes.cast}>{describeCast(replay.cast_role_counts)}</div>
      <div className={classes.foot}>
        <span>{replay.n_events} events</span>
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
