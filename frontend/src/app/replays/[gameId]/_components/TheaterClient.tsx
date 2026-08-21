'use client';

/**
 * The replay theater — the portfolio centerpiece (build_plan P1).
 *
 * The fold happens ONCE for the whole log; the scrubber selects a page out of the result
 * rather than re-folding to a position. That is what makes `?day=` cheap, and why the X-ray
 * is available from the first paint of a finished game instead of only after the scrubber
 * reaches `game_over`.
 *
 * Nothing here gates on entitlement. The archive serves every tier for a finished game, so
 * the X-ray toggle is an ARRANGEMENT control — it decides what is shown at once, never what
 * the viewer is allowed to know. If a log carried no observer data the toggle disables
 * itself, because there would be nothing behind it (never because we decided to withhold).
 */
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { foldEvents } from '@/game/foldEvents';
import { useNumberFilter } from '@/hooks/useFilterState';
import { ghostGuesses } from '@/lib/storage';
import { DayTranscript } from '@/components/DayTranscript';
import {
  AgentInspector,
  DayScrubber,
  GhostGuess,
  RosterRail,
  VoteMatrix,
  WinnerChip,
  XrayToggle,
} from '@/components/theater-parts';
import { describeCast, timeAgo } from '@/lib/format';
import type { DurableGameEvent } from '@/types/contracts';
import classes from '@/components/Theater.module.css';

export function TheaterClient({ gameId }: { gameId: string }) {
  const [day, setDay] = useNumberFilter('day', 1);
  const [xray, setXray] = useState(false);
  const [inspecting, setInspecting] = useState<string | null>(null);
  const [guesses, setGuesses] = useState<Record<string, string>>({});

  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.replays.detail(gameId),
    queryFn: () => getReplay(gameId),
    staleTime: Infinity, // a finished replay is immutable
  });

  const view = useMemo(
    () => (data ? foldEvents(data.events as DurableGameEvent[]) : null),
    [data],
  );

  // localStorage is client-only; read it after mount so the markup matches on hydration.
  useEffect(() => setGuesses(ghostGuesses.get(gameId)), [gameId]);

  if (isPending) return <p className={classes.meta}>Loading replay…</p>;
  if (error) {
    const missing = error instanceof ApiError && error.status === 404;
    return (
      <p role="alert" className={classes.meta}>
        {missing ? 'No such replay.' : `Could not load this replay: ${error.message}`}
      </p>
    );
  }
  if (!view || !data) return null;

  const days = Object.values(view.days).sort((a, b) => a.day - b.day);
  const current = view.days[day] ?? days[0];
  const previous = view.days[current.day - 1];
  const deadByNow = new Set(
    view.dead.filter((d) => d.day <= current.day).map((d) => d.player),
  );

  const recordGuess = (seat: string) => {
    const next = { ...guesses, [`day-${current.day}`]: seat };
    setGuesses(next);
    ghostGuesses.set(gameId, next);
  };

  return (
    <div className={classes.shell}>
      <header className={classes.header}>
        <div className={classes.headerTop}>
          <Link href="/replays" className={classes.back}>
            ← replays
          </Link>
          <h1 className={classes.title}>Day {current.day}</h1>
          {view.winner ? <WinnerChip winner={view.winner} /> : null}
          <span className={classes.spacer} />
          <XrayToggle
            on={xray}
            available={view.xray.available}
            showHint={!xray}
            onToggle={() => setXray((v) => !v)}
          />
        </div>
        <div className={classes.meta}>
          <span>{data.days} days</span>
          <span>{view.seats.length} seats</span>
          <span>{describeCast(data.cast_role_counts)}</span>
          {data.finished_at ? <span>{timeAgo(data.finished_at)}</span> : null}
        </div>
        <DayScrubber days={days} current={current.day} onSelect={setDay} />
      </header>

      <div className={classes.body}>
        <aside className={classes.rail}>
          <RosterRail
            view={view}
            xray={xray}
            upToDay={current.day}
            onInspect={xray ? setInspecting : undefined}
          />
        </aside>

        <div className={classes.center}>
          <DayTranscript
            day={current}
            previousDay={previous}
            roles={view.xray.roles}
            xray={xray}
            deadSeats={deadByNow}
            onInspect={xray ? setInspecting : undefined}
          />
        </div>

        <aside className={classes.inspector}>
          <GhostGuess
            day={current.day}
            seats={view.seats}
            deadSeats={deadByNow}
            guess={guesses[`day-${current.day}`]}
            truth={view.xray.roles}
            revealed={view.winner !== null}
            onGuess={recordGuess}
          />
          {inspecting ? (
            <AgentInspector
              seat={inspecting}
              view={view}
              onClose={() => setInspecting(null)}
            />
          ) : null}
          <VoteMatrix view={view} day={current} />
        </aside>
      </div>
    </div>
  );
}
