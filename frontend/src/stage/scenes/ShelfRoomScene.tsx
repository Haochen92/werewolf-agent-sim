'use client';

/**
 * Night, the acting seat (handoff §4.6, beat sheet §6): the healer, the investigator, the
 * vigilante or the serial killer, alone in their own painted compartment with the other seats
 * hung as photographs on a line. Only the seats the server offered hang there
 * (`pending.candidates` is the only source of legal targets; the room never works out who may
 * be chosen).
 *
 * - `room.opens`: the room dark but for the candle's pool on the photos; the plate asks, and
 *   carries the countdown on the request's time.
 * - choosing (tap a photo): the wall goes darker, one light finds the photo, a pin goes
 *   through it and the plate names the act ("Protect seat 1"). Tapping it again draws the pin
 *   out. The vigilante's plate also has "Hold fire"; the caps left are on the card, under
 *   its night line. Until the plate is pressed a line over it says another photo can still be
 *   tapped. A tap on the empty room draws the pin out too, and closes the card.
 * - confirming (tap the plate): the act goes out through `onAct`. The server takes one answer
 *   per seat, so the pin goes fully home and the plate seals ("Seat 1 is protected tonight");
 *   the room stays so until the stage moves on. A failed send reopens the plate with its words.
 * - the card (tap the frame): the full card over the room; a tap closes it (past the card, it
 *   also clears the choice, as a tap on the empty room does; once the act is in, it only
 *   closes).
 *
 * Arrived at, it is all simply there; played forward, the photos fade in along the line.
 */
import { useCallback, useState, type SetStateAction } from 'react';
import type { ActionKind } from '@/types/contracts';
import { SideSlot } from '../SideSlot';
import { ActPlate } from '../instruments/ActPlate';
import { CountPill } from '../instruments/CountPill';
import { pinColour } from '../instruments/Pin';
import { StageMotion } from '../motion';
import { seatNumber } from '../roles';
import { sideOpen } from '../slot';
import { geometry } from '../units';
import { nightUnits } from './NightLobbyScene';
import { NightRoom } from './NightRoom';
import type { SceneProps } from './types';

/** The act a request asks for, as the plate names it. */
export const ACT_VERB: Partial<Record<ActionKind, string>> = {
  healer_target: 'Protect',
  investigator_target: 'Check',
  vigilante_target: 'Shoot',
  serial_killer_target: 'Kill',
};

const ROLE_OF_KIND: Partial<Record<ActionKind, string>> = {
  healer_target: 'healer',
  investigator_target: 'investigator',
  vigilante_target: 'vigilante',
  serial_killer_target: 'serial_killer',
};

/** What the sealed plate says once the act is in: one line, by act. */
export const ACT_SEALED: Partial<Record<ActionKind, (seat: number) => string>> = {
  healer_target: (n) => `Seat ${n} is protected tonight`,
  investigator_target: (n) => `You check seat ${n} tonight`,
  vigilante_target: (n) => `You shoot seat ${n} tonight`,
  serial_killer_target: (n) => `Seat ${n} is marked tonight`,
  wolf_vote: (n) => `You vote seat ${n} tonight`,
};

/** A lone wolf's sealed plate: its vote is the kill. */
export const LONE_WOLF_SEALED = (n: number) => `Seat ${n} is your kill tonight`;

/** The sealed plate's words: the act and its seat; null = no one (the vigilante held fire). */
export function sealedLabel(
  kind: ActionKind | undefined,
  target: string | null | undefined,
): string {
  if (target === null && kind === 'vigilante_target') return 'You hold fire tonight';
  const say = kind && ACT_SEALED[kind];
  // a remount that lost which seat was pressed still knows the act is in
  return target && say ? say(seatNumber(target)) : 'Your act is in';
}

/** Under-the-plate words while a choice can still change. */
export const CHANGE_NOTE = 'tap another photo to change';

/** The vigilante's caps left, on the card under its night line (no caps, no line: no request comes). */
export function capsNote(bullets: number | null): string | undefined {
  if (bullets === null || bullets < 1) return undefined;
  return bullets === 1 ? 'your last cap' : `${bullets} caps left`;
}

/** The sealed plate when the seat's agent answered, or the server already had an answer. */
export const AGENT_SEALED = 'Your seat’s agent acted for you';

/** What the plate says: the ask before a choice, the act and its seat after one. */
export function plateLabel(kind: ActionKind | undefined, chosen: string | null): string {
  const verb = (kind && ACT_VERB[kind]) || 'Choose';
  if (!chosen)
    return verb === 'Choose' ? 'Choose a seat' : `Choose a seat to ${verb.toLowerCase()}`;
  return `${verb} seat ${seatNumber(chosen)}`;
}

/**
 * State that belongs to one request and its seeded choice: it starts over from `init` when
 * `seed` changes (a new beat, another viewer, a choice or an open card handed in), while the
 * room around it stays up. The rooms used to be keyed whole on the seed, and every beat rebuilt
 * the painting, the light, the photos and the wing with it (build log §8.9).
 */
export function useSeeded<T>(
  seed: string,
  init: () => T,
): [T, (next: SetStateAction<T>) => void] {
  const [state, setState] = useState(() => ({ seed, value: init() }));
  let current = state;
  if (state.seed !== seed) {
    current = { seed, value: init() };
    setState(current);
  }
  const set = useCallback(
    (next: SetStateAction<T>) =>
      setState((s) => ({
        seed: s.seed,
        value: typeof next === 'function' ? (next as (prev: T) => T)(s.value) : next,
      })),
    [],
  );
  return [current.value, set];
}

export function ShelfRoomScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <ShelfRoom {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function ShelfRoom(props: SceneProps) {
  const { view, beat, me, onAct, turn } = props;
  const pending = view.me.pending;
  const kind = pending?.actionKind;
  const role = view.me.role?.role ?? (kind && ROLE_OF_KIND[kind]) ?? 'villager';
  const photos = pending?.candidates ?? [];
  // a new request, another viewer or a new seeded choice starts the choice afresh; the room
  // itself stays up
  const seed = `${beat.seq}:${me}:${turn?.chosen ?? ''}:${turn?.cardOpen ? 1 : 0}`;
  const [chosen, setChosen] = useSeeded<string | null>(seed, () =>
    turn?.chosen && photos.includes(turn.chosen) ? turn.chosen : null,
  );
  const [cardOpen, setCardOpen] = useSeeded(seed, () => !!turn?.cardOpen);
  // what this room sent: a seat, or null (hold fire); undefined = nothing yet, or not known
  const [pressed, setPressed] = useSeeded<string | null | undefined>(seed, () =>
    turn?.sent === 'you' && turn.chosen !== undefined ? turn.chosen : undefined,
  );

  const bullets = role === 'vigilante' ? (view.me.role?.bullets ?? null) : null;
  // the server takes one answer: in once pressed (or answered elsewhere), open again on a failure
  const failed = !!turn?.sendError && !turn.sent;
  const elsewhere = turn?.sent === 'agent' || turn?.sent === 'closed';
  const isIn = !failed && (elsewhere || pressed !== undefined || turn?.sent === 'you');
  const target = isIn ? (elsewhere ? null : pressed) : chosen;

  const act = (seat: string | null) => {
    if (isIn) return;
    setPressed(seat);
    onAct?.(seat);
  };

  return (
    <NightRoom
      {...props}
      role={role}
      photos={photos}
      lit={target ?? null}
      pin={target ?? null}
      pinHome={isIn}
      seed={seed}
      onChoose={isIn ? undefined : (seat) => setChosen((c) => (c === seat ? null : seat))}
      cardOpen={cardOpen}
      onCard={setCardOpen}
      cardNote={capsNote(bullets)}
      onEmpty={() => {
        setCardOpen(false);
        if (!isIn) setChosen(null);
      }}
    >
      {/* once the act is in, the lobby's count: the others acting, until the morning */}
      {isIn ? <NightCount {...props} /> : null}
      {pending ? (
        <ActPlate
          label={plateLabel(kind, chosen)}
          // centred in the room, left of an open side slot, so the drawer can run full height
          centre={geometry(props.presentation.hud, sideOpen(props.presentation)).cx}
          clock={isIn ? null : turn?.clock}
          disabled={!chosen || isIn}
          onConfirm={() => act(chosen)}
          secondary={
            kind === 'vigilante_target'
              ? { label: 'Hold fire', disabled: isIn, onClick: () => act(null) }
              : undefined
          }
          note={chosen ? CHANGE_NOTE : undefined}
          error={failed ? turn?.sendError : null}
          sealed={
            isIn
              ? {
                  label: elsewhere ? AGENT_SEALED : sealedLabel(kind, pressed),
                  colour: pinColour(role),
                }
              : null
          }
        />
      ) : null}
    </NightRoom>
  );
}

/** The night lobby's pill ("Acted 3 of 5"), from the same census and the same live count. */
export function NightCount({ view, presentation, turn }: SceneProps) {
  const units = nightUnits(view);
  const acted = Math.min(turn?.progress?.n ?? 0, units);
  return (
    <CountPill
      hud={presentation.hud}
      label="Acted"
      n={acted}
      total={units}
      side={sideOpen(presentation)}
    />
  );
}
