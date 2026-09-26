'use client';

/**
 * The acting seat's room at night, as both night rooms share it (handoff §2, beat sheet §6
 * and §7): bare walnut panelling, the shelf across the upper half with your framed card at
 * the left, the carriage clock at the centre and your role's kit at the right, and below it
 * one plush doll per seat you may choose, each on its hook. There is no avatar of you: you
 * are the one sitting in the chair.
 *
 * Choosing is light. Before a choice the room is evenly lit; once a doll is chosen the room
 * below the shelf dims and one light finds that doll, while the shelf stays lit. Nothing
 * moves to say "chosen". The shelf room and the pack's room differ only in what sits over
 * this (the plate, the chat, the teeth), so they pass that in.
 */
import { AnimatePresence, motion } from 'motion/react';
import type { ReactNode } from 'react';
import { SPRITES } from '@/assets/manifest';
import { Layer, Paint } from '../Stage';
import { Bleed } from '../instruments/Bleed';
import { CarriageClock } from '../instruments/CarriageClock';
import { CardOverlay, FramedCard } from '../instruments/FramedCard';
import { Kit } from '../instruments/Kit';
import { DOLL_BODY_PER_WIDTH, Plush } from '../instruments/Plush';
import { TopStrip } from '../instruments/TopStrip';
import { Wing, WingTile } from '../instruments/Wing';
import { useMotionScale } from '../motion';
import { shelfLight, shelfPlan, shelfRoom } from '../paint/shelf-room';
import { seatNumber } from '../roles';
import { sideOpen, stripButtons } from '../slot';
import { BLEED, STAGE_H, geometry } from '../units';
import type { SceneProps, TurnInput } from './types';
import styles from '../instruments/NightRoom.module.css';

/** The light finding a chosen doll, and the room dimming around it (seconds). */
const LIGHT_FADE = 0.6;
/** Arriving in the room: each doll fades in a beat after the one before it (seconds). */
const DOLL_STAGGER = 0.08;

export interface NightRoomProps extends Pick<
  SceneProps,
  'view' | 'beat' | 'me' | 'presentation' | 'slot'
> {
  /** Your role: its card in the frame, its kit on the shelf. */
  role: string;
  /** A lone wolf's card reads "You hunt alone now". */
  alone?: boolean;
  /** The seats hung on the hooks, in seat order. */
  dolls: readonly string[];
  /** The doll the light finds; null = the room evenly lit. */
  lit: string | null;
  /** Tapping a doll; without it the dolls are only shown. */
  onChoose?: (seat: string) => void;
  /** Marks drawn over a doll (the teeth), by seat. */
  marks?: Partial<Record<string, ReactNode>>;
  /** Seats the wing marks as the pack's (red edge). */
  pack?: readonly string[];
  /** Under the kit on the shelf's edge: the vigilante's caps left. */
  kitNote?: ReactNode;
  clock?: TurnInput['clock'];
  cardOpen: boolean;
  onCard: (open: boolean) => void;
  /** The plate, the chat: whatever the room adds at its foot. */
  children?: ReactNode;
}

export function NightRoom({
  view,
  beat,
  me,
  presentation,
  slot: slotInput,
  role,
  alone,
  dolls,
  lit,
  onChoose,
  marks,
  pack = [],
  kitNote,
  clock,
  cardOpen,
  onCard,
  children,
}: NightRoomProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  // the side slot open: the shelf and its hooks keep to the room left of it
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const n = Math.max(1, dolls.length);
  const plan = shelfPlan({ hud, hooks: n, side });
  const body = plan.dollW * DOLL_BODY_PER_WIDTH;
  const chosenIndex = lit ? dolls.indexOf(lit) : -1;
  const deadBySeat = new Map(view.dead.map((d) => [d.player, d]));
  const myRole = view.me.role?.role ?? role;

  return (
    <>
      <Layer name="paint">
        <Bleed room="shelf" hud={hud} />
        <Paint of={shelfRoom} opts={{ hud, hooks: n, side, wood: SPRITES.wood.src }} />
      </Layer>

      <Layer name="figures">
        {dolls.map((seat, i) => {
          const s = seatNumber(seat);
          const character = cast[s - 1];
          const hook = plan.hooks[i];
          if (!character || !hook) return null;
          return (
            <Plush
              key={seat}
              character={character}
              seat={s}
              x={hook.x}
              hangY={hook.end + 2}
              body={body}
              light={chosenIndex < 0 ? undefined : i === chosenIndex ? 'lit' : 'dim'}
              onChoose={onChoose ? () => onChoose(seat) : undefined}
              arrive={animate ? 0.1 + i * DOLL_STAGGER : false}
            >
              {marks?.[seat]}
            </Plush>
          );
        })}
      </Layer>

      <Layer name="instruments">
        <FramedCard
          role={role}
          x={plan.cardX}
          foot={plan.foot}
          height={0.31 * STAGE_H}
          u={g.u * 0.95}
          alone={alone}
          onOpen={() => onCard(true)}
        />
        <CarriageClock
          x={plan.clockX}
          foot={plan.foot}
          height={0.27 * STAGE_H}
          remainingMs={clock?.remainingMs ?? null}
          totalMs={clock?.totalMs ?? null}
        />
        <Kit role={role} x={plan.kitX} foot={plan.foot} height={0.19 * STAGE_H} />
        {kitNote ? (
          <div className={styles.kitNote} style={{ left: plan.kitX, top: plan.foot + 8 }}>
            {kitNote}
          </div>
        ) : null}
      </Layer>

      <Layer name="light">
        <AnimatePresence initial={false}>
          <motion.div
            key={chosenIndex}
            style={{ position: 'absolute', inset: 0 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: LIGHT_FADE * k }}
          >
            <Paint
              of={shelfLight}
              opts={{
                hud,
                hooks: n,
                side,
                chosen: chosenIndex < 0 ? undefined : chosenIndex,
                bleed: BLEED,
              }}
            />
          </motion.div>
        </AnimatePresence>
      </Layer>

      <Layer name="hud">
        <Wing width={g.wingN}>
          {view.seats.map((seat, i) => {
            const d = deadBySeat.get(seat);
            const truth = xray
              ? (view.xray.roles[seat] ?? null)
              : seat === me
                ? myRole
                : pack.includes(seat)
                  ? 'wolf'
                  : null;
            return (
              <WingTile
                key={seat}
                seat={seatNumber(seat)}
                character={cast[i]}
                dead={d ? { role: d.role } : undefined}
                truth={truth}
                you={seat === me}
                pack={seat !== me && pack.includes(seat)}
              />
            );
          })}
        </Wing>
        <TopStrip
          hud={hud}
          title={`Night ${beat.day}`}
          sub={`Night · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
        />
        {children}
        {cardOpen && me ? (
          <CardOverlay
            role={role}
            seat={seatNumber(me)}
            u={g.u * 1.6}
            alone={alone}
            onClose={() => onCard(false)}
          />
        ) : null}
      </Layer>
    </>
  );
}
