'use client';

/**
 * The pieces the dining car's scenes without a puppet share (the deal, the night lobby, the
 * morning): the backdrop at an hour, crossfading from the last hour when a beat plays the
 * change; the house lights (with the visible cones of the beat's specials); the wing of seats; and the empty stand that comes back up when
 * the day begins. Each scene says what is different about it and leaves the rest to these.
 */
import { motion } from 'motion/react';
import type { Character, DayState } from '@/assets/manifest';
import type { GameView, SpeechSlot, PassSlot } from '@/game/types';
import { Layer, Paint, PaintPicture } from '../Stage';
import { Puppet } from '../cast/Puppet';
import { Bleed } from '../instruments/Bleed';
import { Apron, Trap } from '../instruments/Floor';
import { SpeechBox } from '../instruments/SpeechBox';
import { Plaque, Stand } from '../instruments/Stand';
import { Wing, WingTile } from '../instruments/Wing';
import { useMotionScale } from '../motion';
import { beam, type Special } from '../paint/draw';
import { diningCar, diningCarPlan } from '../paint/dining-car';
import { drape } from '../paint/drape';
import { light, type Pool } from '../paint/light';
import type { Phase } from '../paint/materials';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { BLEED, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';

/**
 * The car at an hour; played from another hour, the old paint fades off over the new. Under
 * both, the bleed past the stage's sides, on the new hour at once.
 */
export function CarPaint({
  phase,
  from,
  hud,
  wallClock = true,
  fadeDelay = 1.2,
  side,
}: {
  phase: Phase;
  /** Played: the hour the car was at before this beat. */
  from?: Phase | null;
  hud: Hud;
  wallClock?: boolean;
  fadeDelay?: number;
  /** The side slot is open: the room is drawn narrower, moved left (the X-ray's film is up). */
  side?: boolean;
}) {
  const k = useMotionScale();
  return (
    <>
      <Bleed room="car" phase={phase} hud={hud} />
      <Paint of={diningCar} opts={{ phase, hud, wallClock, side }} />
      {from && from !== phase ? (
        <motion.div
          style={{ position: 'absolute', inset: 0 }}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ duration: 1.2 * k, delay: fadeDelay * k, ease: 'easeInOut' }}
        >
          <PaintPicture of={diningCar} opts={{ phase: from, hud, wallClock, side }} />
        </motion.div>
      ) : null}
    </>
  );
}

/** The house lights for a beat: the car's own glows, a pool where the action is, and specials. */
export function HouseLights({
  phase,
  hud,
  pool,
  specials = [],
  quiet = [],
  dark,
  side,
}: {
  phase: Phase;
  hud: Hud;
  pool: Pool;
  specials?: Special[];
  /** Specials that light a patch without a visible cone (the lynch's standing leaves). */
  quiet?: Special[];
  dark: number;
  /** The side slot is open (as for `CarPaint`). */
  side?: boolean;
}) {
  const plan = diningCarPlan({ phase, hud, side });
  return (
    <>
      {specials.length ? <Paint of={beams} opts={{ specials }} /> : null}
      <Paint
        of={light}
        opts={{
          hud,
          side,
          pool,
          dark,
          specials: [...specials, ...quiet],
          scene: { glows: plan.glows, specials: plan.specials },
          bleed: BLEED,
        }}
      />
    </>
  );
}

/* the visible cones of this beat's own specials, as the car draws its own (draw.ts `beam`) */
const beams = ({ specials }: { id: string; specials: Special[] }) =>
  `<svg viewBox="0 0 ${STAGE_W} ${STAGE_H}" xmlns="http://www.w3.org/2000/svg">${specials
    .map(([x, y0, y1, rx]) => beam(x, y0, y1, rx, 70))
    .join('')}</svg>`;

export interface WingSeatOptions {
  /** Seats whose death this beat has not told yet: still shown alive. */
  untold?: ReadonlySet<string>;
  /** Roles this viewer may see on living seats (the X-ray's truth, a wolf's packmate). */
  truth?: (seat: string) => string | null;
  lit?: (seat: string) => boolean;
  /** Out of the scene's focus: the losers at the end. */
  dim?: (seat: string) => boolean;
  lamp?: (seat: string) => boolean;
  pack?: (seat: string) => boolean;
}

/** The wing, with the replay's drape above it when the HUD is the replay's. */
export function TableWing({
  view,
  cast,
  me,
  hud,
  width,
  opts = {},
}: {
  view: GameView;
  cast: readonly Character[];
  me: string | null;
  hud: Hud;
  width: number;
  opts?: WingSeatOptions;
}) {
  const deadBySeat = new Map(view.dead.map((d) => [d.player, d]));
  return (
    <>
      {hud === 'replay' ? <Paint of={drape} opts={{ bleed: BLEED }} /> : null}
      <Wing width={width}>
        {view.seats.map((seat, i) => {
          const d = opts.untold?.has(seat) ? undefined : deadBySeat.get(seat);
          return (
            <WingTile
              key={seat}
              seat={seatNumber(seat)}
              character={cast[i]}
              dead={d ? { role: d.role } : undefined}
              truth={opts.truth?.(seat) ?? null}
              lit={opts.lit?.(seat)}
              dim={opts.dim?.(seat)}
              lamp={opts.lamp?.(seat)}
              pack={opts.pack?.(seat)}
              you={seat === me}
            />
          );
        })}
      </Wing>
    </>
  );
}

/** The floor in front of the wall: the boards, the trap shut. */
export function CarFloor({ g }: { g: StageGeometry }) {
  return (
    <Layer name="floor">
      <Apron g={g} />
      <Trap g={g} state="closed" />
    </Layer>
  );
}

/**
 * "The day begins": the stand comes back up, lit, with the day's first speaker in it if the
 * view already holds that turn; otherwise empty, waiting for it. Played, it fades in after
 * `delay` and the puppet rises.
 */
export function StandReturns({
  g,
  view,
  day,
  hud,
  cast,
  xray,
  animate,
  delay,
  narrow = false,
  aside = false,
}: {
  g: StageGeometry;
  view: GameView;
  day: number;
  hud: Hud;
  cast: readonly Character[];
  xray: boolean;
  animate: boolean;
  delay: number;
  /** The drawer is open at full height: the box narrows under the puppet. */
  narrow?: boolean;
  /** The side slot is open: on a phone the box stops short of it (SpeechBox's `aside`). */
  aside?: boolean;
}) {
  const k = useMotionScale();
  const slot = view.days[day]?.slots.find((s) => s.kind !== 'gm') as
    SpeechSlot | PassSlot | undefined;
  const n = slot ? seatNumber(slot.player) : 0;
  const character = n ? cast[n - 1] : null;
  const role = slot ? view.xray.roles[slot.player] : undefined;
  const state: DayState = slot?.kind === 'speech' ? 'talking' : 'base';
  const fade = {
    initial: animate ? { opacity: 0 } : false,
    animate: { opacity: 1 },
    transition: { duration: 0.5 * k, delay: delay * k },
  } as const;
  return (
    <>
      <Layer name="figures">
        {character ? (
          <Puppet
            g={g}
            character={character}
            seat={n}
            state={state}
            arrive={animate ? delay : false}
          />
        ) : null}
      </Layer>
      <Layer name="stand">
        <motion.div style={{ position: 'absolute', inset: 0 }} {...fade}>
          <Stand g={g}>
            {n ? (
              <Plaque
                seat={n}
                tag={xray && role ? ROLE_NAME[role] : undefined}
                tone={xray && role ? (factionOf(role) ?? undefined) : undefined}
              />
            ) : null}
          </Stand>
        </motion.div>
      </Layer>
      {character && slot ? (
        <Layer name="hud">
          <SpeechBox
            hud={hud}
            seat={n}
            character={character}
            line={slot.kind === 'speech' ? slot.message : null}
            arrive={animate}
            side={narrow}
            aside={aside}
          />
        </Layer>
      ) : null}
    </>
  );
}
