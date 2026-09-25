'use client';

/**
 * Night, the acting seat (handoff §4.6, beat sheet §6): the healer, the investigator, the
 * vigilante or the serial killer, alone in their own room with the other seats hung as
 * plush dolls. Only the seats the server offered hang there (`pending.candidates` is the
 * only source of legal targets; the room never works out who may be chosen).
 *
 * - `room.opens`: the room, evenly lit; the clock runs on the request's time; the plate asks.
 * - choosing (tap a doll): the room below the shelf dims, one light finds the doll, the act's
 *   mark lands on it (plaster, lens, bullet, knife) and the plate names the act ("Protect
 *   seat 1"). The vigilante's plate also has "Hold fire"; the caps left sit under the popgun.
 * - confirming (tap the plate): the act goes out through `onAct`; the container takes the
 *   seat back to the lobby.
 * - the card (tap the frame): the full card over the room; a tap closes it.
 *
 * Arrived at, it is all simply there; played forward, the dolls fade in along the hooks.
 */
import { useState } from 'react';
import type { ActionKind } from '@/types/contracts';
import { SideSlot } from '../SideSlot';
import { ActMark, type ActKind } from '../instruments/ActMark';
import { ActPlate } from '../instruments/ActPlate';
import { Caps } from '../instruments/Notice';
import styles from '../instruments/NightRoom.module.css';
import { StageMotion } from '../motion';
import { seatNumber } from '../roles';
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

/** What the plate says: the ask before a choice, the act and its seat after one. */
export function plateLabel(kind: ActionKind | undefined, chosen: string | null): string {
  const verb = (kind && ACT_VERB[kind]) || 'Choose';
  if (!chosen)
    return verb === 'Choose' ? 'Choose a seat' : `Choose a seat to ${verb.toLowerCase()}`;
  return `${verb} seat ${seatNumber(chosen)}`;
}

/** The mark the act leaves on the chosen doll: the morning's marks, by role. */
const ACT_MARK: Partial<Record<string, ActKind>> = {
  healer: 'plaster',
  investigator: 'lens',
  vigilante: 'bullet',
  serial_killer: 'knife',
};

export function ShelfRoomScene(props: SceneProps) {
  const t = props.turn;
  return (
    <StageMotion speed={props.presentation.motion}>
      {/* a new request, or a new seeded choice, starts the room afresh */}
      <ShelfRoom
        key={`${props.beat.seq}:${props.me}:${t?.chosen ?? ''}:${t?.cardOpen ? 1 : 0}`}
        {...props}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function ShelfRoom(props: SceneProps) {
  const { view, onAct, turn } = props;
  const pending = view.me.pending;
  const kind = pending?.actionKind;
  const role = view.me.role?.role ?? (kind && ROLE_OF_KIND[kind]) ?? 'villager';
  const dolls = pending?.candidates ?? [];
  const [chosen, setChosen] = useState<string | null>(
    turn?.chosen && dolls.includes(turn.chosen) ? turn.chosen : null,
  );
  const [cardOpen, setCardOpen] = useState(!!turn?.cardOpen);
  const [sent, setSent] = useState(false);

  const mark = ACT_MARK[role];
  const bullets = role === 'vigilante' ? (view.me.role?.bullets ?? null) : null;

  const act = (target: string | null) => {
    if (sent) return;
    setSent(true);
    onAct?.(target);
  };

  return (
    <NightRoom
      {...props}
      role={role}
      dolls={dolls}
      lit={chosen}
      onChoose={sent ? undefined : (seat) => setChosen((c) => (c === seat ? null : seat))}
      marks={
        chosen && mark
          ? {
              [chosen]: (
                <span className={styles.actMark}>
                  {/* a seeded choice is at rest; a tapped one pops in */}
                  <ActMark
                    kind={mark}
                    x={0}
                    y={0}
                    k={26}
                    arrive={chosen === turn?.chosen ? false : 0}
                  />
                </span>
              ),
            }
          : undefined
      }
      kitNote={bullets !== null ? <Caps n={bullets} /> : undefined}
      clock={turn?.clock}
      cardOpen={cardOpen}
      onCard={setCardOpen}
    >
      {pending ? (
        <ActPlate
          label={plateLabel(kind, chosen)}
          disabled={!chosen || sent}
          onConfirm={() => act(chosen)}
          secondary={
            kind === 'vigilante_target'
              ? { label: 'Hold fire', disabled: sent, onClick: () => act(null) }
              : undefined
          }
        />
      ) : null}
    </NightRoom>
  );
}
