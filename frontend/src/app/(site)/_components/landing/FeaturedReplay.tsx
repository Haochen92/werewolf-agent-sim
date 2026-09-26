'use client';

/**
 * The carriage on the landing (review §F7, B17): a game from the archive playing in the dining
 * car's own walnut and brass, under a marquee that says what is showing. It is the replay
 * theatre itself in its mini mode (no HUD, no slot, no transport), playing one window of the
 * public cut round and round: day 3's vote through the lynched seat's card going to the wing
 * (`featuredWindow`). No second engine.
 *
 * The game is `SITE.featuredReplay`; if the archive no longer has it, the newest game plays
 * instead, with its own window. It plays only while it is on screen and the window is at
 * least 700px wide. On an upright phone (the stage would be a quarter of its size) it rests on
 * the window's first beat as a poster, with a way into the whole replay; so does it for a
 * viewer who asked for reduced motion, and with `?still=1` (the goldens).
 */
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useMediaQuery } from '@mantine/hooks';
import { SPRITES } from '@/assets/manifest';
import { Button } from '@/components/site';
import { useModelLabels } from '@/hooks/useModelLabels';
import { getReplay, listReplaysWithTotal } from '@/lib/api';
import { featuredWindow } from '@/lib/featured-window';
import { formatDate } from '@/lib/format';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { SITE } from '@/lib/site';
import { beatsFor } from '@/stage/beats/beatsFor';
import { ReplayTheatre } from '@/stage/containers/ReplayTheatre';
import { stageFonts } from '@/stage/fonts';
import type { DurableGameEvent, ReplayGame, Winner } from '@/types/contracts';
import classes from './Carriage.module.css';

const WON: Record<Winner, string> = {
  villagers: 'Villagers won',
  wolves: 'Wolves won',
  serial_killer: 'Serial killer won',
};

/** The marquee's tiles: the game's facts, as the archive's slates say them. */
function tilesOf(game: ReplayGame, modelName: (id: string) => string): string[] {
  const humans = game.n_humans;
  return [
    game.model ? modelName(game.model) : 'Model unrecorded',
    game.memory ? 'Memory on' : 'Memory off',
    humans ? `${humans} human${humans > 1 ? 's' : ''} at the table` : 'All agents',
    `${game.days} ${game.days === 1 ? 'day' : 'days'}`,
    WON[game.winner],
    formatDate(game.finished_at),
  ].filter(Boolean);
}

/** The featured game, or the newest one when the archive no longer has it. */
function useShownGame() {
  const featured = useQuery({
    queryKey: queryKeys.replays.detail(SITE.featuredReplay),
    queryFn: () => getReplay(SITE.featuredReplay),
    staleTime: Infinity, // a finished replay is immutable
    retry: false,
  });
  const gone = featured.error instanceof ApiError && featured.error.status === 404;
  // the footer asks the same one-row page for the archive's total: one request serves both
  const newest = useQuery({
    queryKey: queryKeys.replays.total(),
    queryFn: () => listReplaysWithTotal({ limit: 1 }),
    staleTime: 60_000,
    retry: false,
    enabled: gone,
  });
  const newestId = newest.data?.replays[0]?.game_id ?? null;
  const fallback = useQuery({
    queryKey: queryKeys.replays.detail(newestId ?? ''),
    queryFn: () => getReplay(newestId!),
    staleTime: Infinity,
    retry: false,
    enabled: gone && newestId !== null,
  });

  if (!gone) return { game: featured.data ?? null, failed: featured.isError };
  return {
    game: fallback.data ?? null,
    failed: newest.isError || fallback.isError || (newest.isSuccess && newestId === null),
  };
}

/** True while the element is at least partly on screen. */
function useOnScreen<T extends Element>() {
  const ref = useRef<T>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setOn(entry.isIntersecting), {
      threshold: 0.25,
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return [ref, on] as const;
}

/** Bogie: the carriage's wheels, drawn once (the mockup's `frames` script). */
function Bogie({ className }: { className: string }) {
  const spokes = [0, 45, 90, 135].map((a) => {
    const dx = (14 * Math.cos((a * Math.PI) / 180)).toFixed(1);
    const dy = (14 * Math.sin((a * Math.PI) / 180)).toFixed(1);
    return { a, dx, dy };
  });
  return (
    <svg className={className} viewBox="0 0 150 46" aria-hidden="true">
      <rect x="10" y="4" width="130" height="12" rx="3" fill="#1c1510" />
      <rect x="18" y="0" width="114" height="6" rx="2" fill="#2e241c" />
      {[38, 112].map((cx) => (
        <g key={cx}>
          <circle cx={cx} cy="28" r="17" fill="#15100c" stroke="#6b5a3e" strokeWidth="3" />
          <circle cx={cx} cy="28" r="4" fill="#8a7a66" />
          {spokes.map(({ a, dx, dy }) => (
            <path
              key={a}
              d={`M${cx},28 l${dx},${dy} M${cx},28 l${-dx},${-dy}`}
              stroke="#4a3d30"
              strokeWidth="2"
            />
          ))}
        </g>
      ))}
      <rect x="56" y="18" width="38" height="8" rx="2" fill="#2e241c" />
    </svg>
  );
}

export function FeaturedReplay() {
  const still = useSearchParams().get('still') === '1';
  const { game, failed } = useShownGame();
  const modelName = useModelLabels();
  const wide = useMediaQuery('(min-width: 700px)');
  const [screenRef, onScreen] = useOnScreen<HTMLDivElement>();

  const events = game?.events as readonly DurableGameEvent[] | undefined;
  const cut = useMemo(
    () => (events ? featuredWindow(beatsFor(events, { xray: false })) : null),
    [events],
  );

  const id = game?.game_id ?? null;
  const record = id ? id.slice(0, 7).toUpperCase() : '';
  const href = id ? `/replays/${id}` : '/replays';
  const what = cut?.day != null ? `Day ${cut.day}` : 'The opening';

  return (
    <figure className={classes.figure}>
      <div
        className={classes.carriage}
        data-frame="carriage"
        style={{ '--wood': `url(${SPRITES.wood.src})` } as CSSProperties}
      >
        <span className={classes.roof} aria-hidden="true" />
        <div className={classes.marquee}>
          <span className={classes.bulbs} aria-hidden="true" />
          <div className={classes.mqRow}>
            <span className={classes.nowShowing}>Now showing</span>
            {game ? (
              <ul className={classes.tiles} aria-label="About this game">
                {tilesOf(game, modelName).map((t) => (
                  <li key={t} className={classes.tile}>
                    {t}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <span className={`${classes.bulbs} ${classes.bulbsLow}`} aria-hidden="true" />
        </div>
        <div ref={screenRef} className={`${classes.screen} ${stageFonts}`}>
          {game && cut ? (
            <ReplayTheatre
              key={game.game_id}
              game={game}
              mini={{
                from: cut.from,
                to: cut.to,
                autoplay: wide && onScreen && !still,
              }}
            />
          ) : (
            <p className={classes.wait}>
              {failed ? 'The archive is resting; the replays are a click away.' : ' '}
            </p>
          )}
          {game ? (
            <div className={classes.poster}>
              <Button component={Link} href={href} variant="primary" size="md">
                Watch the replay
              </Button>
            </div>
          ) : null}
        </div>
        <span className={classes.chassis} aria-hidden="true">
          <Bogie className={`${classes.bogie} ${classes.bogieL}`} />
          <Bogie className={`${classes.bogie} ${classes.bogieR}`} />
          <span className={classes.rails} />
        </span>
      </div>
      {game ? (
        <figcaption className={classes.caption}>
          <Link href={href}>
            {what} of game {record} &middot; watch it whole &rarr;
          </Link>
        </figcaption>
      ) : null}
    </figure>
  );
}
