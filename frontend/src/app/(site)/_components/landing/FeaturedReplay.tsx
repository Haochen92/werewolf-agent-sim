'use client';

/**
 * The carriage on the landing (redesign handoff 2026-10-14 §3): a game from the archive
 * playing in the big window of a railway carriage standing at the platform. It is the replay
 * theatre itself in its mini mode, playing one window round and round: day 3's vote through the
 * lynched seat's card going to the wing (`featuredWindow`). No second engine.
 *
 * On a desktop (over 860px) the whole carriage stands centred, both ends in view: end, door,
 * the game's window, door, end, under a roof board that names the game (its ID in split-flap
 * tiles) and its model, and the replay's own controls sit on the stage. On a phone the window
 * runs edge to edge and the controls leave the stage for the platform under it, at reading size
 * (`CarriageUnder`). Below the platform: the game's details and the way to the whole game.
 * Nothing on the carriage's body is interactive.
 *
 * The carriage is drawn in CSS as a stand-in (Carriage.module.css); each of its parts takes its
 * picture from a CSS variable, so the painted pieces can drop in later without new markup.
 *
 * The game is `SITE.featuredReplay`; if the archive no longer has it, the newest game plays
 * instead, with its own window. It plays while it is on screen; it rests on the window's first
 * beat for a viewer who asked for reduced motion, and with `?still=1` (the goldens).
 *
 * The carriage sits below the fold, so nothing of the preview is fetched at load (audit
 * 2026-10-11 §2): the carriage is drawn at its full size, the board's tiles and the details
 * held empty, and the theatre's code (a chunk of its own), the replay and the stage's pictures
 * come only once the window is on screen, or within a screen of it after the visitor has
 * scrolled (`useNear`). Once up it stays up; scrolled away it pauses, and so does a hidden page
 * (the theatre's own clock).
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type RefObject,
} from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useMediaQuery } from '@mantine/hooks';
import { useModelLabels } from '@/hooks/useModelLabels';
import { getReplay, listReplaysWithTotal } from '@/lib/api';
import { featuredWindow } from '@/lib/featured-window';
import { formatDate } from '@/lib/format';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { SITE } from '@/lib/site';
import { beatsFor } from '@/stage/beats/beatsFor';
import type { MiniUnder } from '@/stage/containers/ReplayTheatre';
import { stageFonts } from '@/stage/fonts';
import { winnerKey, type WinnerKey } from '@/stage/roles';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import classes from './Carriage.module.css';

// the stage and the controls under it load when the carriage comes near (`useNear`), not with
// the landing: they are the whole theatre, and most of the page's script
const ReplayTheatre = dynamic(
  () => import('@/stage/containers/ReplayTheatre').then((m) => m.ReplayTheatre),
  { ssr: false },
);
const CarriageUnder = dynamic(
  () => import('./CarriageUnder').then((m) => m.CarriageUnder),
  { ssr: false },
);

const WON: Record<WinnerKey, string> = {
  villagers: 'Town won',
  wolves: 'Wolves won',
  serial_killer: 'Serial killer won',
  necromancer: 'Necromancer won',
  draw: 'A draw',
};

/** The game's details under the platform, as the archive's slates say them (the model is on the roof board). */
function detailsOf(game: ReplayGame): string[] {
  const humans = game.n_humans;
  return [
    game.memory ? 'Memory on' : 'Memory off',
    humans ? `${humans} human${humans > 1 ? 's' : ''} at the table` : 'All agents',
    `${game.days} ${game.days === 1 ? 'day' : 'days'}`,
    WON[winnerKey(game.winner)],
    formatDate(game.finished_at),
  ].filter(Boolean);
}

/** The featured game, or the newest one when the archive no longer has it; asked once `wanted`. */
function useShownGame(wanted: boolean) {
  const featured = useQuery({
    queryKey: queryKeys.replays.detail(SITE.featuredReplay),
    queryFn: () => getReplay(SITE.featuredReplay),
    staleTime: Infinity, // a finished replay is immutable
    retry: false,
    enabled: wanted,
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

/**
 * True once the element is on screen, or within a screen of it after the visitor has scrolled
 * at all: the preview's code, replay and pictures are fetched from then. Not at load for a
 * carriage just under the fold, so a visitor who never scrolls never pays for it; and a
 * screen ahead once they do, so it is usually up before it is seen. It stays true.
 */
function useNear(ref: RefObject<Element | null>) {
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    let seen = false;
    let reach = false;
    let moved = window.scrollY > 0;
    const check = () => {
      if (seen || (reach && moved)) setNear(true);
    };
    const onScroll = () => {
      moved = true;
      check();
    };
    const look = new IntersectionObserver(([entry]) => {
      seen = entry.isIntersecting;
      check();
    });
    const ahead = new IntersectionObserver(
      ([entry]) => {
        reach = entry.isIntersecting;
        check();
      },
      { rootMargin: '100% 0px' },
    );
    look.observe(el);
    ahead.observe(el);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      look.disconnect();
      ahead.disconnect();
      window.removeEventListener('scroll', onScroll);
    };
  }, [ref, near]);
  return near;
}

export function FeaturedReplay() {
  const still = useSearchParams().get('still') === '1';
  const modelName = useModelLabels();
  const wide = useMediaQuery('(min-width: 861px)');
  const [screenRef, onScreen] = useOnScreen<HTMLDivElement>();
  const near = useNear(screenRef);
  const { game, failed } = useShownGame(near);
  const [underEl, setUnderEl] = useState<HTMLDivElement | null>(null);
  const under = useCallback((u: MiniUnder) => <CarriageUnder {...u} />, []);

  const events = game?.events as readonly DurableGameEvent[] | undefined;
  const cut = useMemo(
    () => (events ? featuredWindow(beatsFor(events, { xray: false })) : null),
    [events],
  );

  const id = game?.game_id ?? null;
  const record = id ? id.slice(0, 7).toUpperCase() : '';
  // the theatre's way out comes back here (`from=home`, TheaterClient)
  const href = id ? `/replays/${id}?from=home` : '/replays';
  const what = cut?.day != null ? `Day ${cut.day}` : 'The opening';

  const model = game ? (game.model ? modelName(game.model) : 'Model unrecorded') : null;
  // the ID's tiles, held blank until the game arrives so nothing on the board moves
  const tiles = record || '       ';

  return (
    <figure
      className={classes.depot}
      data-frame="carriage"
      aria-label={game ? `Replay of ${what.toLowerCase()} of game ${record}` : undefined}
    >
      <div className={classes.car}>
        <div className={classes.rbwrap}>
          <div className={classes.rboard}>
            <div className={classes.field}>
              <span className={classes.lab}>Game ID</span>
              <span
                className={classes.flaps}
                role={game ? 'img' : undefined}
                aria-label={game ? record : undefined}
                aria-hidden={game ? undefined : true}
              >
                {[...tiles].map((c, i) => (
                  <span key={i} className={classes.t}>
                    {c}
                  </span>
                ))}
              </span>
            </div>
            <div className={`${classes.field} ${classes.fieldModel}`}>
              <span className={classes.lab}>Model</span>
              <span className={classes.mdv}>{model ?? '\u00a0'}</span>
            </div>
          </div>
        </div>
        <div className={classes.roof} aria-hidden="true" />
        <div className={classes.body}>
          <span className={`${classes.gang} ${classes.gangL}`} aria-hidden="true" />
          <span className={`${classes.gang} ${classes.gangR}`} aria-hidden="true" />
          <div className={classes.cantrail} aria-hidden="true" />
          <div className={classes.band}>
            <div className={classes.gwin}>
              <div className={classes.lights} aria-hidden="true">
                {Array.from({ length: 7 }, (_, i) => (
                  <i key={i} />
                ))}
              </div>
              <div className={classes.glass}>
                <div ref={screenRef} className={`${classes.screen} ${stageFonts}`}>
                  {game && cut ? (
                    <ReplayTheatre
                      key={game.game_id}
                      game={game}
                      mini={{
                        from: cut.from,
                        to: cut.to,
                        autoplay: onScreen && !still,
                        controls: wide ? 'stage' : 'under',
                        under,
                        underEl,
                      }}
                    />
                  ) : (
                    <p className={classes.wait}>
                      {failed ? 'The archive is resting; the replays are a click away.' : ' '}
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div aria-hidden="true">
              {(['L', 'R'] as const).map((side) => (
                <div key={side} className={`${classes.door} ${classes[`door${side}`]}`}>
                  <span className={classes.drop} />
                  <span className={classes.strap} />
                  <span className={classes.handle} />
                  <span className={classes.crest}>9</span>
                  <span className={classes.step} />
                </div>
              ))}
              {(['L1', 'L2', 'R1', 'R2'] as const).map((g) => (
                <span key={g} className={`${classes.grab} ${classes[`grab${g}`]}`} />
              ))}
            </div>
          </div>
          <div className={classes.lower} aria-hidden="true" />
        </div>
        <div className={classes.under} aria-hidden="true">
          <svg viewBox="0 0 1280 46" preserveAspectRatio="none">
            <g fill="none" stroke="#3a2c1e" strokeWidth="3">
              <path d="M150 4 L420 36 H860 L1130 4" />
            </g>
            <g fill="#2a2016">
              <rect x="440" y="30" width="16" height="10" />
              <rect x="824" y="30" width="16" height="10" />
            </g>
            <rect x="540" y="4" width="200" height="26" rx="2" fill="#1d160f" stroke="#3a2c1e" />
          </svg>
          <span className={`${classes.buf} ${classes.bufL}`} />
          <span className={`${classes.buf} ${classes.bufR}`} />
          <span className={`${classes.bogie} ${classes.bogieL}`}>
            <i />
            <i />
          </span>
          <span className={`${classes.bogie} ${classes.bogieR}`}>
            <i />
            <i />
          </span>
        </div>
      </div>
      <div className={classes.platform} aria-hidden="true" />
      {wide ? null : (
        <div
          ref={setUnderEl}
          className={failed ? `${stageFonts} ${classes.mui}` : `${stageFonts} ${classes.mui} ${classes.underHold}`}
        />
      )}
      <div className={classes.below}>
        <p className={classes.meta}>
          {game ? (
            <span className={classes.in}>
              {detailsOf(game).map((t) => (
                <span key={t}>{t}</span>
              ))}
            </span>
          ) : (
            '\u00a0'
          )}
        </p>
        <Link href={href} className={classes.go}>
          Watch the whole game <span aria-hidden="true">&rarr;</span>
        </Link>
      </div>
    </figure>
  );
}
