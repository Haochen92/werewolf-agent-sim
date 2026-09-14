'use client';

/**
 * The replay theater — the portfolio centerpiece (build_plan P1).
 *
 * Two ways to read a finished game. Opened cold, the whole log is folded once and the
 * scrubber selects a page out of the result, so `?day=` is cheap and the X-ray is there
 * from the first paint. Pressed play, the log is revealed beat by beat at reading pace and
 * the fold runs on the visible prefix instead: the page follows the cursor's day, the
 * scrubber jumps the cursor, and "show all" returns to the first mode. The player owns the
 * cursor and the timer (useReplayPlayer); the beats are cut in game/replayPlayer.
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
import { useReplayPlayer } from '@/hooks/useReplayPlayer';
import { ReplayControls } from '@/components/ReplayControls';
import { ghostGuesses } from '@/lib/storage';
import { DayTranscript } from '@/components/DayTranscript';
import { WinnerCard } from '@/components/transcript-parts';
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

const EMPTY: DurableGameEvent[] = [];

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

  const events = useMemo(
    () => (data ? (data.events as DurableGameEvent[]) : EMPTY),
    [data],
  );
  const player = useReplayPlayer(events);
  const view = useMemo(
    () => (data ? foldEvents(player.visibleEvents) : null),
    [data, player.visibleEvents],
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
  // While the player runs, the page is the cursor's day; the URL's day is for a cold open.
  const shownDay = player.active && player.currentDay !== null ? player.currentDay : day;
  const current = view.days[shownDay] ?? days[days.length - 1];
  if (!current) {
    // Play from start, before the first beat lands: nothing to fold yet.
    return (
      <div className={classes.shell}>
        <header className={classes.header}>
          <ReplayControls player={player} />
        </header>
      </div>
    );
  }
  const selectDay = (target: number) => {
    setDay(target);
    if (player.active) player.jumpToDay(target);
  };
  const previous = view.days[current.day - 1];
  const next = view.days[current.day + 1];
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
        <DayScrubber days={days} current={current.day} onSelect={selectDay} />
        <ReplayControls player={player} />
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
            nextDay={next}
            roles={view.xray.roles}
            xray={xray}
            deadSeats={deadByNow}
            onInspect={xray ? setInspecting : undefined}
          />
          {/* The ending belongs at the foot of the LAST day, where the reader arrives at
              it — not in the header, where it would spoil every earlier day it sits above. */}
          {view.winner && current.day === days[days.length - 1].day ? (
            <WinnerCard winner={view.winner} days={days.length} survivors={view.alive} />
          ) : null}
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
