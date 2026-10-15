'use client';

/**
 * The replay's way in (owner, 2026-10-15): the train leaves the platform, every place in its
 * window an agent's, the blinds down with their shadows on them; the curtain falls; and it holds,
 * saying what the wait is, until the page has the replay. The train leaves once its picture is
 * there (`StationReady`), and the departure is the whole of `DEPART`, so the page is never
 * shorter than that; the replay is fetched, and its theatre mounted out of sight to fetch its
 * pictures, while it plays (TheaterClient). Then the page lifts the curtain by fading this
 * whole platform off the theatre under it (`lifting`): the theatre's stage is laid out apart
 * (its rail, its drawer), so a curtain on it would neither cover the same screen nor say its
 * words in the same place.
 *
 * The same platform as the room's departure (`StationScene`, `station.departing`), with no
 * room behind it (`RoomInput.bare`): the sign is the line's, nobody is on the platform, and
 * the cast is the one the game's id draws (`castForGame`), the replay's own not being known yet.
 * A viewer who asked for less motion gets the departure's moment (`departMs`).
 */
import { useCallback, useEffect, useMemo, useState, type CSSProperties } from 'react';
import { foldEvents } from '@/game/foldEvents';
import { Stage } from '../Stage';
import { castForGame } from '../cast/castForGame';
import type { Presentation } from './types';
import { StationScene } from './StationScene';
import { CURTAIN, departMs, stationBeat } from './station';
import { StationReady } from './station-pictures';
import own from './StationStill.module.css';

const EMPTY_VIEW = foldEvents([]);
const BOARDING = stationBeat('station.waiting');
const DEPARTING = stationBeat('station.departing');
/** A game's places: ten since the ten-seat cast (the replay's own count is not known yet). */
const PLACES = 10;

/** Still on the platform until its train is there (`StationReady`), then the departure. */
type Phase = 'boarding' | 'departing' | 'closing' | 'down';

/** The curtain lifting: the platform, curtain and all, fades off the theatre under it. */
const LIFT: CSSProperties = {
  opacity: 0,
  transition: `opacity ${CURTAIN.open}s ease-in-out`,
  pointerEvents: 'none',
};

export function StationDeparture({
  gameId,
  line,
  onDown,
  lifting = false,
}: {
  gameId: string;
  /** What the wait is, shown under the curtain while it holds. */
  line: string;
  /** The curtain is down: the page may hand over to the theatre. */
  onDown: () => void;
  /** The theatre is up under the platform: the whole of it fades off, as the curtain lifts. */
  lifting?: boolean;
}) {
  const [phase, setPhase] = useState<Phase>('boarding');
  const onReady = useCallback(
    () => setPhase((p) => (p === 'boarding' ? 'departing' : p)),
    [],
  );
  useEffect(() => {
    if (phase === 'boarding') return;
    const after = (ms: number, then: () => void) => {
      const t = setTimeout(then, ms);
      return () => clearTimeout(t);
    };
    if (phase === 'departing') return after(departMs(), () => setPhase('closing'));
    if (phase === 'closing') return after(CURTAIN.close * 1000, () => setPhase('down'));
    onDown();
  }, [phase, onDown]);

  const presentation = useMemo(
    (): Presentation => ({
      xray: false,
      slot: null,
      motion: 'normal',
      hud: 'replay',
      cast: castForGame(gameId, PLACES),
      animate: phase !== 'boarding',
    }),
    [gameId, phase],
  );
  return (
    <main
      className={own.page}
      data-loading="replay"
      data-departure={lifting ? 'lifting' : phase}
      style={lifting ? LIFT : undefined}
    >
      <Stage fit="contain">
        <StationScene
          view={EMPTY_VIEW}
          beat={phase === 'boarding' ? BOARDING : DEPARTING}
          me={null}
          presentation={presentation}
          room={{
            name: '',
            aboard: [],
            places: PLACES,
            host: null,
            locked: false,
            isHost: false,
            seated: false,
            you: null,
            minAboard: 1,
            link: '',
            bare: true,
            curtain: phase === 'closing' || phase === 'down' ? 'closing' : null,
            curtainLine: phase === 'down' ? line : null,
          }}
        />
        <StationReady onReady={onReady} />
      </Stage>
    </main>
  );
}
