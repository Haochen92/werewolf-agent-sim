'use client';

/**
 * `/games/[gameId]` — ONE route, three states (build_plan §5).
 *
 *   waiting  → the lobby card
 *   running  → the live table: the SAME transcript components the replay theater uses,
 *              fed by the SSE store instead of a fetched log, plus the turn dock
 *   finished → the theater, X-ray unlocked
 *
 * The client never re-routes across those transitions; the page morphs, mirroring the
 * server's own registry swap where a room URL becomes a game URL.
 *
 * Beats fire on LIVE arrival only. Every takeover below is gated on `isLive(seq)` from the
 * store, which is false for anything folded during catch-up — so a refresh mid-game lands
 * silently on the newest day instead of replaying an hour of drama (ux_journeys §0, D23).
 */
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { useGameStream } from '@/hooks/useGameStream';
import { useGameSession } from '@/game/store';
import { queryKeys } from '@/lib/queryKeys';
import { rejoinGame } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { seatToken } from '@/lib/storage';
import { DayTranscript } from '@/components/DayTranscript';
import { GhostBar, PacingStrip, ThinkingRow, TurnDock } from '@/components/TurnDock';
import { RoleChip, RoleReveal, WinnerTakeover } from '@/components/Beats';
import { LobbyCard, TerminalError } from '@/components/LobbyCard';
import {
  AgentInspector,
  DayScrubber,
  RosterRail,
  VoteMatrix,
  WinnerChip,
  XrayToggle,
} from '@/components/theater-parts';
import theater from '@/components/Theater.module.css';

export function GameClient({ gameId }: { gameId: string }) {
  const queryClient = useQueryClient();
  const { status, state, error, statusError, isPending } = useGameStream(gameId);

  const view = useGameSession((s) => s.view);
  const isLive = useGameSession((s) => s.isLive);
  const connection = useGameSession((s) => s.connection);
  const pacing = useGameSession((s) => s.pacing);
  const clearPending = useGameSession((s) => s.clearPending);

  const [xray, setXray] = useState(false);
  const [inspecting, setInspecting] = useState<string | null>(null);
  const [revealSeen, setRevealSeen] = useState(false);
  const [overSeen, setOverSeen] = useState(false);
  const [reopenRole, setReopenRole] = useState(false);
  const [day, setDay] = useState<number | null>(null);

  /**
   * Seat recovery (D23). The trigger is NOT a failed request: a lost cookie does not make
   * `GET /games/{id}` fail — it succeeds and simply reports `you: null`, because that call
   * is public. So the real signal is "this device holds a seat token for this game, yet the
   * server says we are nobody", which means the HttpOnly cookie is gone (cleared data, new
   * browser session) while its localStorage backup survived. One attempt, then we stay a
   * spectator: cross-device rejoin is deliberately v1-out.
   */
  const [rejoinTried, setRejoinTried] = useState(false);
  const [rejoining, setRejoining] = useState(false);
  useEffect(() => {
    setRejoinTried(false);
    setRejoining(false);
  }, [gameId]);

  useEffect(() => {
    const seatMissing = Boolean(status && !status.you);
    const seatRejected = statusError instanceof ApiError && statusError.isSeatLost;
    if (rejoinTried || (!seatMissing && !seatRejected)) return;
    const token = seatToken.get(gameId);
    if (!token) return;
    setRejoinTried(true);
    setRejoining(true);
    rejoinGame(gameId, token)
      .then(() =>
        queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) }),
      )
      .catch(() => {
        // The token no longer resolves (game gone, or a different device's seat).
        seatToken.clear(gameId);
      })
      .finally(() => setRejoining(false));
  }, [gameId, status, statusError, rejoinTried, queryClient]);

  const days = useMemo(
    () => Object.values(view.days).sort((a, b) => a.day - b.day),
    [view.days],
  );

  if (isPending || rejoining) {
    return (
      <p className={theater.meta}>{rejoining ? 'Reclaiming your seat…' : 'Joining…'}</p>
    );
  }

  if (statusError) {
    const missing = statusError instanceof ApiError && statusError.status === 404;
    return (
      <div className={theater.shell}>
        <p role="alert" className={theater.meta}>
          {missing ? 'This live game is no longer in the registry.' : statusError.message}
        </p>
        <p className={theater.meta}>
          {missing ? (
            <Link href={`/replays/${gameId}`}>Open its replay if it was archived →</Link>
          ) : (
            <Link href="/">Back to the start →</Link>
          )}
        </p>
      </div>
    );
  }

  // D23: the game task died. The stream cannot tell us this — only the poll's error field
  // can, because heartbeats keep flowing and `state` stays "running".
  if (error) return <TerminalError message={error} byok={status?.name?.includes('byok')} />;

  if (state === 'waiting' && status) return <LobbyCard gameId={gameId} status={status} />;

  const current = day !== null ? view.days[day] : days[days.length - 1];
  const previous = current ? view.days[current.day - 1] : undefined;
  const deadByNow = new Set(
    view.dead
      .filter((death) => death.day <= (current?.day ?? view.day))
      .map((d) => d.player),
  );
  const finished = state === 'finished' || view.winner !== null;

  // The two takeovers: rendered only if their event arrived LIVE and has not been dismissed.
  // "We have a role now" is also true after a refresh, so the question is whether the seq
  // that carried it arrived LIVE. The store is the only thing that knows.
  const showReveal =
    !revealSeen &&
    view.me.role !== null &&
    view.me.seat !== null &&
    view.me.roleSeq !== null &&
    isLive(view.me.roleSeq);
  const showWinner =
    !overSeen && view.winner !== null && view.winnerSeq !== null && isLive(view.winnerSeq);

  const activeStage =
    view.phase === 'night' ? 'night' : view.phase === 'voting' ? 'day_vote' : null;
  const activePacing = activeStage
    ? pacing[`${current?.day ?? view.day}:${activeStage}`]
    : undefined;
  const myTurnIsActive = Boolean(
    view.me.pending &&
    view.me.seat &&
    ((status?.pending_seats ?? []).includes(view.me.seat) ||
      view.me.pending.seq > (status?.last_seq ?? 0)),
  );

  return (
    <div className={theater.shell}>
      {showReveal && view.me.role && view.me.seat ? (
        <RoleReveal
          seat={view.me.seat}
          card={view.me.role}
          onDismiss={() => setRevealSeen(true)}
        />
      ) : null}

      {reopenRole && view.me.role && view.me.seat ? (
        <RoleReveal
          seat={view.me.seat}
          card={view.me.role}
          onDismiss={() => setReopenRole(false)}
        />
      ) : null}

      {showWinner && view.winner ? (
        <WinnerTakeover
          winner={view.winner}
          onDismiss={() => {
            setOverSeen(true);
            // The reveal is the point: land them in the X-ray they were just promised.
            setXray(true);
            setDay(days[0]?.day ?? null);
          }}
        />
      ) : null}

      <header className={theater.header}>
        <div className={theater.headerTop}>
          <Link href="/" className={theater.back}>
            ← home
          </Link>
          <h1 className={theater.title}>{current ? `Day ${current.day}` : 'The table'}</h1>
          {view.winner ? <WinnerChip winner={view.winner} /> : null}
          {view.me.role ? (
            <RoleChip card={view.me.role} onOpen={() => setReopenRole(true)} />
          ) : null}
          <span className={theater.spacer} />
          {!view.me.seat && !finished ? (
            <span className={theater.hint}>watching live</span>
          ) : null}
          {view.xray.available ? (
            <XrayToggle
              on={xray}
              available
              showHint={!xray}
              onToggle={() => setXray((v) => !v)}
            />
          ) : null}
        </div>

        {connection === 'reconnecting' ? (
          <div className={theater.meta}>reconnecting…</div>
        ) : null}

        {/* The scrubber unlocks only once the game is over — mid-game there is nothing to
            scrub to but the present, and offering it would imply otherwise. */}
        {finished && days.length > 1 ? (
          <DayScrubber
            days={days}
            current={current?.day ?? days[0].day}
            onSelect={setDay}
          />
        ) : null}
      </header>

      <div className={theater.body}>
        <aside className={theater.rail}>
          <RosterRail
            view={view}
            xray={xray}
            upToDay={current?.day ?? 99}
            onInspect={xray ? setInspecting : undefined}
          />
        </aside>

        <div className={theater.center}>
          {current ? (
            <DayTranscript
              day={current}
              previousDay={previous}
              roles={view.xray.roles}
              xray={xray}
              mySeat={view.me.seat}
              deadSeats={deadByNow}
              // Live: the recap IS a morning briefing after a night away (D13).
              expandRecap={!finished}
              privateResults={view.me.privateResults}
              showEntitledMachine={!finished}
              onInspect={xray ? setInspecting : undefined}
            />
          ) : (
            <p className={theater.meta}>Waiting for the table to wake…</p>
          )}

          {/* D12: only meaningful live, and only at the tail. */}
          {!finished && view.thinking ? (
            <ThinkingRow player={view.thinking.player} />
          ) : null}
        </div>

        <aside className={theater.inspector}>
          {inspecting ? (
            <AgentInspector
              seat={inspecting}
              view={view}
              onClose={() => setInspecting(null)}
            />
          ) : null}
          {current ? <VoteMatrix view={view} day={current} /> : null}
        </aside>
      </div>

      {activePacing && !finished ? (
        <PacingStrip
          stage={activePacing.stage}
          done={activePacing.done}
          total={activePacing.total}
        />
      ) : null}

      {/* The dock, the ghost bar, or nothing at all for a spectator. */}
      {view.me.pending && myTurnIsActive && view.me.alive && !finished ? (
        <TurnDock
          gameId={gameId}
          pending={view.me.pending}
          seats={view.seats}
          onSubmitted={() => {
            clearPending();
            queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
          }}
        />
      ) : view.me.seat && !view.me.alive ? (
        <GhostBar />
      ) : null}
    </div>
  );
}
