'use client';

/**
 * The loading still (beat sheet §1a): the empty platform at night, shown while a theatre route
 * waits for its game or its replay. The same paint as the waiting room's first frame (the
 * country and the moon, the train at the platform with the dining car's long window, the lamps,
 * the beam, the station sign, the empty seat rail, the snow), with nobody on it, no plates and
 * no chips, and a notice on the ledge saying what the wait is: "Boarding…", "Reclaiming your
 * seat…", "Rewinding the reels…".
 *
 * It takes no game and fetches nothing, so a route's `loading.tsx` can show it at once. The
 * picture is there from the first frame; only the ledge fades in, after a moment, so a page that
 * mounts quickly swaps in without the still ever looking different from the platform it
 * becomes. The snow falls (still for reduced motion). Landscape only, like every stage.
 */
import Image from 'next/image';
import { SPRITES } from '@/assets/manifest';
import { OrientationGuard } from '../OrientationGuard';
import { Layer, Paint, Stage } from '../Stage';
import { Bleed } from '../instruments/Bleed';
import { Wing } from '../instruments/Wing';
import { stationBack, stationFront, stationPlan } from '../paint/station';
import { STAGE_H, geometry, type Hud } from '../units';
import { Snow } from './StationScene';
import styles from './Station.module.css';
import own from './StationStill.module.css';

/** The rail's empty cards: the seats are not known yet, so nine, as the platform has. */
const SEATS = Array.from({ length: 9 }, (_, i) => ({ seat: i + 1 }));

export function StationStill({
  line,
  hud = 'live',
  what,
}: {
  /** The ledge's words: what the wait is. */
  line: string;
  /** Whose stage this stands in for: the rail and the room are laid out as its. */
  hud?: Exclude<Hud, 'none'>;
  /** For tests and styles: which route is loading. */
  what: 'game' | 'replay';
}) {
  const S = stationPlan(hud);
  const g = geometry(hud);
  return (
    <OrientationGuard>
      <main className={own.page} data-loading={what}>
        <Stage fit="contain">
          <Layer name="paint">
            <Bleed room="station" />
            <Paint of={stationBack} opts={{ hud, sky: SPRITES.station.sky.src }} />
            <div className={styles.world}>
              <div
                className={styles.train}
                style={{
                  left: S.train.x,
                  top: S.train.y,
                  width: S.train.w,
                  height: S.train.h,
                }}
              >
                <Image
                  decoding="sync"
                  src={SPRITES.station.train}
                  alt=""
                  unoptimized
                  priority
                  draggable={false}
                  className={styles.fill}
                />
              </div>
            </div>
            <div
              className={styles.paving}
              style={{ top: S.floorY, height: STAGE_H - S.floorY }}
            >
              <div
                className={styles.tile}
                style={{ backgroundImage: `url(${SPRITES.station.floor.src})` }}
              />
            </div>
            <Paint
              of={stationFront}
              opts={{
                hud,
                post: SPRITES.station.post.src,
                lamp: SPRITES.station.lamp.src,
                wood: SPRITES.wood.src,
                stone: SPRITES.station.floor.src,
              }}
            />
          </Layer>
          <Layer name="instruments">
            <div className={styles.sign} style={{ left: S.cx }}>
              <span className={styles.chains} aria-hidden="true">
                <i />
                <i />
              </span>
              <span className={styles.board}>
                <b>The Ninth Express</b>
              </span>
            </div>
          </Layer>
          <Layer name="light">
            <Snow still={false} />
          </Layer>
          <Layer name="hud">
            <Wing width={g.wingN} tiles={SEATS} />
            <div
              className={`${styles.ledge} ${own.arrive}`}
              style={{
                left: S.cx,
                translate: '-50% 0',
                backgroundImage: `linear-gradient(rgba(60,30,12,.25),rgba(20,10,4,.55)),url(${SPRITES.wood.src})`,
              }}
            >
              <div className={styles.notice} role="status">
                <b>{line}</b>
              </div>
            </div>
          </Layer>
        </Stage>
      </main>
    </OrientationGuard>
  );
}
