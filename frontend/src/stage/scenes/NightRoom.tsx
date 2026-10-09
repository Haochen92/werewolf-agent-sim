'use client';

/**
 * The acting seat's room at night, as both night rooms share it (handoff §2, beat sheet §6
 * and §7): the role's painted sleeping compartment (paint/compartment.ts), the night going by
 * behind its window, a line of photographs under the brass rack, one per seat you may choose,
 * and your framed card standing on the table by the candle. There is no avatar of you: you are
 * the one sitting in the chair. The turn's countdown is on the plate, not in the room. The
 * replay's night tells each actor's act in this same room, the actor's (ReplayNightScene).
 *
 * It is dark but for the painted candle: its warm pool falls on the photos and the card.
 * Choosing is light and a pin. Once a photo is chosen the wall goes darker, one light finds
 * that photo, and a pin in the acting side's colour goes through it. The acting seat's room and
 * the pack's differ only in what sits over this (the plate, the chat, the teeth), so they pass
 * that in.
 *
 * A tap on the empty room (not a photo, the card, the plate or the HUD) resets it: `onEmpty`,
 * which closes the card and clears a choice not yet sent. With the card open, a tap past the
 * card does the same.
 */
import { AnimatePresence, motion } from 'motion/react';
import type { ReactNode } from 'react';
import type { RoomPicture } from '@/assets/manifest';
import { Atmosphere } from '../Atmosphere';
import { Layer, Paint } from '../Stage';
import { Compartment } from '../instruments/Compartment';
import { CardOverlay, FramedCard } from '../instruments/FramedCard';
import { Photo } from '../instruments/Photo';
import { Pin } from '../instruments/Pin';
import { TopStrip } from '../instruments/TopStrip';
import { Wing } from '../instruments/Wing';
import { useMotionScale } from '../motion';
import { useSmall } from '../set';
import { notebookGame } from '../notebook';
import { photoTwine, roomChoice, roomLight, roomPlan } from '../paint/compartment';
import { knownRoles, seatNumber } from '../roles';
import { sideOpen, stripButtons } from '../slot';
import { BLEED, geometry } from '../units';
import type { SceneProps } from './types';
import styles from '../instruments/NightRoom.module.css';

/** The light finding a chosen photo, and the room dimming around it (seconds). */
const LIGHT_FADE = 0.6;
/** Arriving in the room: each photo fades in a beat after the one before it (seconds). */
const PHOTO_STAGGER = 0.08;

/** Each role's painted room; a role with none of its own (a villager, in the workbench) gets the healer's. */
export const ROOM_OF: Record<string, RoomPicture> = {
  healer: 'healer',
  investigator: 'investigator',
  vigilante: 'vigilante',
  serial_killer: 'serial_killer',
  wolf: 'wolf',
  // the two wolf skills play in the pack's room (owner, 2026-10-07)
  chanteuse: 'wolf',
  illusionist: 'wolf',
  sentinel: 'sentinel',
  trailseer: 'trailseer',
  sigilist: 'sigilist',
  speculator: 'speculator',
  necromancer: 'necromancer',
  fortune_teller: 'fortune_teller',
};

export interface NightRoomProps extends Pick<
  SceneProps,
  'view' | 'beat' | 'me' | 'presentation' | 'slot'
> {
  /** Your role: its card in the frame, its painted room. */
  role: string;
  /** A lone wolf's card reads "You hunt alone now". */
  alone?: boolean;
  /** The seats whose photos hang on the line, in seat order. */
  photos: readonly string[];
  /** The photo the light finds; null = only the candle's pool. */
  lit: string | null;
  /** The photo with the pin through it (the choice); null = none. */
  pin?: string | null;
  /** The act is sent: the pin goes fully home. */
  pinHome?: boolean;
  /**
   * The choice as handed in (the beat, the viewer, a seeded choice): when it changes, the pin
   * and the choice's darkness are simply there, as on arriving in the room, which stays up.
   */
  seed?: string;
  /** Tapping a photo; without it the photos are only shown. */
  onChoose?: (seat: string) => void;
  /** Marks drawn over a photo (the teeth), by seat. */
  marks?: Partial<Record<string, ReactNode>>;
  /** Seats the wing marks as the pack's (red edge). */
  pack?: readonly string[];
  cardOpen: boolean;
  onCard: (open: boolean) => void;
  /** A quiet line on the card under the night text (the vigilante's caps left). */
  cardNote?: string;
  /**
   * The replay's rooms: the card is the actor's, not yours ("Seat 4", "Seats 3 and 8"); it
   * opens all the same, with no seat of yours needed.
   */
  cardOwner?: string;
  /** A tap on the empty room, or past the open card: back to the room at rest. */
  onEmpty?: () => void;
  /** The plate, the chat: whatever the room adds at its foot. */
  children?: ReactNode;
  /** The strip's small line, in place of "Night · <beat>" (the replay names the actor). */
  sub?: string;
  /** The count pill, handed to the strip (the replay's row keeps it by its plaques). */
  count?: ReactNode;
  /**
   * The replay's night: the wing's lit card (the actor), its lamps (those still to act), and
   * (2026-09-30) its taps and words: another actor's card visits that room, "Visit ▸" or "Seen"
   * on it, anyone else's opens a file.
   */
  wing?: {
    lit?: (seat: string) => boolean;
    lamp?: (seat: string) => boolean;
    word?: (seat: string) => 'visit' | 'seen' | undefined;
    tap?: ((seat: string) => void) | null;
    tapLabel?: (seat: string) => string;
  };
}

export function NightRoom({
  view,
  beat,
  me,
  presentation,
  slot: slotInput,
  role,
  alone,
  photos,
  lit,
  pin = null,
  pinHome = false,
  seed,
  onChoose,
  marks,
  pack = [],
  cardOpen,
  onCard,
  cardNote,
  cardOwner,
  onEmpty,
  children,
  sub,
  count,
  wing,
}: NightRoomProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  // on a phone the choice's darkness cuts in: a full-stage fade is a GPU layer for its length,
  // and every layer drawn over it (stage_architecture.md §6)
  const small = useSmall();
  const fade = small ? { duration: 0 } : { duration: LIGHT_FADE * k };
  // the side slot open: the painting slides left, so its window and its wall stay in view
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const room = ROOM_OF[role] ?? 'healer';
  const n = Math.max(1, photos.length);
  const plan = roomPlan({ room, hud, side, n });
  const chosenIndex = lit ? photos.indexOf(lit) : -1;
  const deadBySeat = new Map(view.dead.map((d) => [d.player, d]));
  const known = knownRoles(me, view.me);
  const myRole = view.me.role?.role ?? role;

  return (
    <>
      <Atmosphere room="compartment" phase="night" hud={hud} side={side} />
      <Layer name="paint">
        <Compartment room={room} hud={hud} side={side} />
      </Layer>

      {onEmpty ? (
        <Layer name="floor">
          <div
            className={styles.emptyTap}
            data-empty="room"
            aria-hidden
            onClick={onEmpty}
          />
        </Layer>
      ) : null}

      <Layer name="figures">
        {/* the line is paint: a tap through it lands on the empty room */}
        <div style={{ pointerEvents: 'none' }}>
          <Paint of={photoTwine} opts={{ room, hud, side, n }} />
        </div>
        {photos.map((seat, i) => {
          const s = seatNumber(seat);
          const character = cast[s - 1];
          const at = plan.photos[i];
          if (!character || !at) return null;
          return (
            <Photo
              key={seat}
              character={character}
              seat={s}
              x={at.x}
              top={at.top}
              w={plan.photo.w}
              h={plan.photo.h}
              drop={at.drop}
              light={chosenIndex < 0 ? undefined : i === chosenIndex ? 'lit' : 'dim'}
              onChoose={onChoose ? () => onChoose(seat) : undefined}
              arrive={animate ? 0.1 + i * PHOTO_STAGGER : false}
            >
              <span className={styles.bite}>{marks?.[seat]}</span>
              {/* starts still: only a pin put in or drawn out in the room plays */}
              <AnimatePresence key={seed} initial={false}>
                {pin === seat ? (
                  <Pin key="pin" role={role} w={plan.photo.w * 1.3} home={pinHome} />
                ) : null}
              </AnimatePresence>
            </Photo>
          );
        })}
      </Layer>

      <Layer name="instruments">
        <FramedCard
          role={role}
          x={plan.card.x}
          foot={plan.card.foot}
          height={plan.card.h}
          u={g.u * 0.95 * (plan.card.h / 279)}
          alone={alone}
          note={cardNote}
          owner={cardOwner}
          onOpen={me || cardOwner ? () => onCard(true) : undefined}
        />
      </Layer>

      <Layer name="light">
        {/* the candle's room stays still; only the choice's darkness fades in and out over it */}
        <Paint of={roomLight} opts={{ room, hud, side, n, bleed: BLEED }} />
        <AnimatePresence key={seed} initial={false}>
          {chosenIndex < 0 ? null : (
            <motion.div
              key={chosenIndex}
              style={{ position: 'absolute', inset: 0 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={fade}
            >
              <Paint
                of={roomChoice}
                opts={{ room, hud, side, n, chosen: chosenIndex, bleed: BLEED }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </Layer>

      <Layer name="hud">
        <Wing
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          edit={slotInput?.notebook}
          castCounts={view.castRoleCounts}
          tiles={view.seats.map((seat, i) => {
            const d = deadBySeat.get(seat);
            const truth = xray
              ? (view.xray.roles[seat] ?? null)
              : seat === me
                ? myRole
                : pack.includes(seat)
                  ? 'wolf'
                  : null;
            return {
              seat: seatNumber(seat),
              character: cast[i],
              dead: d ? { role: d.role } : undefined,
              truth,
              you: seat === me,
              pack: seat !== me && pack.includes(seat),
              known: known.get(seat),
              lit: wing?.lit?.(seat),
              lamp: wing?.lamp?.(seat),
              word: wing?.word?.(seat),
              file: wing?.tap
                ? {
                    onTap: () => wing.tap!(seat),
                    label: wing.tapLabel?.(seat) ?? `Open seat ${seatNumber(seat)}’s file`,
                  }
                : undefined,
            };
          })}
        />
        <TopStrip
          hud={hud}
          title={`Night ${beat.day}`}
          sub={sub ?? `Night · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
          side={side}
          count={count}
        />
        {children}
        {cardOpen && (me || cardOwner) ? (
          <CardOverlay
            role={role}
            seat={me ? seatNumber(me) : undefined}
            owner={cardOwner}
            u={g.u * 1.6}
            alone={alone}
            note={cardNote}
            onClose={() => onCard(false)}
            onOutside={onEmpty}
          />
        ) : null}
      </Layer>
    </>
  );
}
