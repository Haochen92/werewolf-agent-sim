'use client';

/**
 * The pieces the dining car's scenes without a puppet share (the deal, the night lobby, the
 * morning): the backdrop at an hour, crossfading from the last hour when a beat plays the
 * change; the house lights (with the visible cones of the beat's specials); the wing of seats; and the empty stand that comes back up when
 * the day begins. Each scene says what is different about it and leaves the rest to these.
 */
import { motion } from 'motion/react';
import { useEffect } from 'react';
import { SPRITES, type Character, type DayState } from '@/assets/manifest';
import type { GameView, SpeechSlot, PassSlot } from '@/game/types';
import { Layer, Paint } from '../Stage';
import { Puppet } from '../cast/Puppet';
import { PaintedBleed } from '../instruments/Bleed';
import { CarBackdrop } from '../instruments/CarBackdrop';
import { FeltWindow } from '../instruments/FeltWindow';
import { SpeechBox } from '../instruments/SpeechBox';
import { Plaque, Stand } from '../instruments/Stand';
import { Wing } from '../instruments/Wing';
import { useMotionScale } from '../motion';
import { beam, type Special } from '../paint/draw';
import { diningCarPlan } from '../paint/dining-car';
import { drape } from '../paint/drape';
import { light, type Pool } from '../paint/light';
import type { Phase } from '../paint/materials';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { BLEED, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';

/**
 * The car at an hour; played from another hour, the old hour's picture fades off over the new
 * (the night picture comes in over the day's). Its sides sink into the house's dark past the
 * painting's edges, for a screen wider than 16:9. Over it, the felt country in its glass,
 * changing hour with it.
 */
export function CarPaint({
  phase,
  from,
  hud,
  fadeDelay = 1.2,
  side,
}: {
  phase: Phase;
  /** Played: the hour the car was at before this beat. */
  from?: Phase | null;
  hud: Hud;
  fadeDelay?: number;
  /** The side slot is open: the room is moved left (the X-ray's film is up). */
  side?: boolean;
}) {
  const k = useMotionScale();
  const fade = { duration: 1.2 * k, delay: fadeDelay * k, ease: 'easeInOut' } as const;
  const plan = diningCarPlan({ phase, hud, side });
  // both pictures ready before an hour's change needs the other one
  useEffect(() => {
    for (const p of Object.values(SPRITES.car)) new window.Image().src = p.src;
  }, []);
  return (
    <>
      <CarBackdrop phase={phase} hud={hud} side={side} />
      {from && from !== phase ? (
        <motion.div
          style={{ position: 'absolute', inset: 0 }}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={fade}
        >
          <CarBackdrop phase={from} hud={hud} side={side} />
        </motion.div>
      ) : null}
      <PaintedBleed x={plan.picture.x} w={STAGE_W} outside />
      <FeltWindow phase={phase} from={from} fade={fade} hud={hud} side={side} />
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
          lamps: plan.lamps,
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
  /** The replay's night stop: a seat that acted glows, a visited one keeps a steady mark. */
  glow?: (seat: string) => 'acted' | 'visited' | undefined;
  pack?: (seat: string) => boolean;
  /**
   * A tap on a seat's card opens its case file (`fileTap` in slot.ts), or, at the night hub,
   * whatever the hub makes of it; null or absent: the cards are only shown.
   */
  file?: ((seat: string) => void) | null;
  /** What a card's tap says, when it is not "Open seat N's file". */
  fileLabel?: (seat: string) => string;
}

/** The wing, with the replay's drape above it when the HUD is the replay's. */
export function TableWing({
  view,
  cast,
  me,
  hud,
  width,
  notes = null,
  opts = {},
}: {
  view: GameView;
  cast: readonly Character[];
  me: string | null;
  hud: Hud;
  width: number;
  /** The game whose notebook the seated player keeps (`notebookGame`); null: none. */
  notes?: string | null;
  opts?: WingSeatOptions;
}) {
  const deadBySeat = new Map(view.dead.map((d) => [d.player, d]));
  return (
    <>
      {hud === 'replay' ? (
        <Paint of={drape} opts={{ bleed: BLEED, src: SPRITES.props.valance.src }} />
      ) : null}
      <Wing
        width={width}
        notes={notes}
        castCounts={view.castRoleCounts}
        tiles={view.seats.map((seat, i) => {
          const d = opts.untold?.has(seat) ? undefined : deadBySeat.get(seat);
          return {
            seat: seatNumber(seat),
            character: cast[i],
            dead: d ? { role: d.role } : undefined,
            truth: opts.truth?.(seat) ?? null,
            lit: opts.lit?.(seat),
            dim: opts.dim?.(seat),
            lamp: opts.lamp?.(seat),
            glow: opts.glow?.(seat),
            pack: opts.pack?.(seat),
            you: seat === me,
            file: opts.file
              ? {
                  onTap: () => opts.file!(seat),
                  label: opts.fileLabel?.(seat) ?? `Open seat ${seatNumber(seat)}’s file`,
                }
              : undefined,
          };
        })}
      />
    </>
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
            shadow
            glass
            character={character}
            // the stand's plate names the seat: no numeral on the belly
            seat={null}
            state={state}
            arrive={animate ? delay : false}
          />
        ) : null}
      </Layer>
      <Layer name="stand">
        <motion.div style={{ position: 'absolute', inset: 0 }} {...fade}>
          <Stand g={g} speech={!!(character && slot)}>
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
          />
        </Layer>
      ) : null}
    </>
  );
}
