'use client';

/**
 * Night, the acting seat (handoff §4.6, beat sheet §6): every role with a night of its own,
 * alone in its own painted compartment with the other seats hung as photographs on a line (the
 * chanteuse and the illusionist in the pack's, for their own skill). Only the seats the server
 * offered hang there (`pending.candidates` is the only source of legal targets; the room never
 * works out who may be chosen), and the server's other words are plates: its no-action word
 * the plate's second button, the speculator's sides a row of plates, the illusionist's conceal
 * the plate itself. A necromancer's bodies hang on a line of their own over the seats, a
 * fortune teller may name a role on its bet from a row of sigils (ten-seat pass §2).
 *
 * - `room.opens`: the room dark but for the candle's pool on the photos; the plate asks, and
 *   carries the countdown on the request's time.
 * - choosing (tap a photo): the wall goes darker, one light finds the photo, a pin goes
 *   through it and the plate names the act ("Protect seat 1"). Tapping it again draws the pin
 *   out. A request with a no-action word has it beside the plate ("Hold fire", "Keep your
 *   checks"); what is left of a limited ability is on the card, under its night line. Until the plate is pressed a line over it says another photo can still be
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
import { noActionWord } from '@/game/turn-words';
import type { ActionKind } from '@/types/contracts';
import { SideSlot } from '../SideSlot';
import { ActPlate, ChoicePlates } from '../instruments/ActPlate';
import { CountPill } from '../instruments/CountPill';
import { pinColour } from '../instruments/Pin';
import { Sigil } from '../instruments/Sigil';
import { StageMotion } from '../motion';
import { isPackRole, ROLE_NAME, seatNumber } from '../roles';
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
  sentinel_target: 'Watch',
  trailseer_target: 'Follow',
  sigil_target: 'Mark',
  block_target: 'Block',
  necromancer_target: 'Act on',
  bet_target: 'Bet on',
};

const ROLE_OF_KIND: Partial<Record<ActionKind, string>> = {
  healer_target: 'healer',
  investigator_target: 'investigator',
  vigilante_target: 'vigilante',
  serial_killer_target: 'serial_killer',
  sentinel_target: 'sentinel',
  trailseer_target: 'trailseer',
  sigil_target: 'sigilist',
  block_target: 'chanteuse',
  conceal: 'illusionist',
  necromancer_target: 'necromancer',
  speculator_pick: 'speculator',
  bet_target: 'fortune_teller',
};

/** What the sealed plate says once the act is in: one line, by act. */
export const ACT_SEALED: Partial<Record<ActionKind, (seat: number) => string>> = {
  healer_target: (n) => `Seat ${n} is protected tonight`,
  investigator_target: (n) => `You check seat ${n} tonight`,
  vigilante_target: (n) => `You shoot seat ${n} tonight`,
  serial_killer_target: (n) => `Seat ${n} is marked tonight`,
  sentinel_target: (n) => `You watch seat ${n} tonight`,
  trailseer_target: (n) => `You follow seat ${n} tonight`,
  sigil_target: (n) => `You mark seat ${n} tonight`,
  block_target: (n) => `Seat ${n} is blocked tonight`,
  // a remount that lost the body still says what was done
  necromancer_target: (n) => `You act on seat ${n} tonight`,
  bet_target: (n) => `You bet on seat ${n}`,
  wolf_vote: (n) => `You vote seat ${n} tonight`,
  carrier_kill: (n) => `Seat ${n} is the pack’s kill tonight`,
};

/**
 * The server's no-action words (ten-seat pass §1), as the plate's second button says them and
 * as its seal says them once pressed. Shown only when the request lists the word.
 */
export const NO_ACTION_PLATE: Record<string, string> = {
  hold_fire: 'Hold fire',
  no_check: 'Keep your checks',
  no_watch: 'Keep your watches',
  keep_sigil: 'Keep your sigils',
  no_conceal: 'Keep your conceals',
  stay_put: 'Stay put',
  not_yet: 'Not yet',
};

export const NO_ACTION_SEALED: Record<string, string> = {
  hold_fire: 'You hold fire tonight',
  no_check: 'You keep your checks tonight',
  no_watch: 'You keep your watches tonight',
  keep_sigil: 'You keep your sigils tonight',
  no_conceal: 'You keep your conceals tonight',
  stay_put: 'You stay put tonight',
  not_yet: 'You keep your pick for another night',
};

/** Each kind's no-action word, for a seal that only knows the act named no one (null). */
const NO_ACTION_OF_KIND: Partial<Record<ActionKind, string>> = {
  investigator_target: 'no_check',
  sentinel_target: 'no_watch',
  vigilante_target: 'hold_fire',
  sigil_target: 'keep_sigil',
  conceal: 'no_conceal',
  necromancer_target: 'stay_put',
  speculator_pick: 'not_yet',
};

/** The speculator's sides, as their plates say them and as "You pick …" says them. */
export const SIDE_PLATE: Record<string, string> = {
  town: 'Town',
  wolves: 'Wolves',
  lone_killer: 'The lone killer',
  self: 'Yourself',
};
const SIDE_PICKED: Record<string, string> = {
  town: 'the Town',
  wolves: 'the Wolves',
  lone_killer: 'the lone killer',
  self: 'yourself',
};

/** The illusionist's plate (its request's word `conceal`), and its seal. */
export const CONCEAL_PLATE = 'Hide the victim’s role';
export const CONCEAL_SEALED = 'The victim’s role is hidden tonight';

/** A lone wolf's sealed plate: its vote is the kill. */
export const LONE_WOLF_SEALED = (n: number) => `Seat ${n} is your kill tonight`;

/** What an act carries besides its target, for the plate's words. */
export interface PlateMore {
  /** A necromancer's body. */
  body?: string | null;
  /** A fortune teller's named role. */
  roleNamed?: string | null;
  /** The acting seat: a fortune teller's bet on it is "yourself". */
  me?: string | null;
}

/**
 * The sealed plate's words: the act and its target; a no-action word (or null, the act that
 * named no one) says what was kept.
 */
export function sealedLabel(
  kind: ActionKind | undefined,
  target: string | null | undefined,
  more: PlateMore = {},
): string {
  const word = target === null ? kind && NO_ACTION_OF_KIND[kind] : target;
  if (word && NO_ACTION_SEALED[word]) return NO_ACTION_SEALED[word];
  if (kind === 'conceal' && target === 'conceal') return CONCEAL_SEALED;
  if (kind === 'speculator_pick' && target && SIDE_PICKED[target])
    return `You pick ${SIDE_PICKED[target]}`;
  if (kind === 'bet_target' && target) {
    if (target === more.me) return 'You bet on yourself';
    if (more.roleNamed)
      return `You bet on seat ${seatNumber(target)} as ${ROLE_NAME[more.roleNamed] ?? more.roleNamed}`;
  }
  if (kind === 'necromancer_target' && target && more.body)
    return `Through seat ${seatNumber(more.body)}, you act on seat ${seatNumber(target)} tonight`;
  const say = kind && ACT_SEALED[kind];
  // a remount that lost which seat was pressed still knows the act is in
  return target && say ? say(seatNumber(target)) : 'Your act is in';
}

/** Under-the-plate words while a choice can still change. */
export const CHANGE_NOTE = 'tap another photo to change';
export const SIDE_CHANGE_NOTE = 'tap another side to change';

/** What each limited ability is counted in, on the card under its night line: one, and more. */
const USE_WORDS: Record<string, [string, string]> = {
  investigator: ['check', 'checks'],
  sentinel: ['watch', 'watches'],
  vigilante: ['cap', 'caps'],
  sigilist: ['sigil', 'sigils'],
  illusionist: ['conceal', 'conceals'],
  fortune_teller: ['self-bet', 'self-bets'],
};

/**
 * What is left of the role's limited ability, on the card under its night line: "2 checks
 * left", "your last check". From `uses` (the ten-seat game); a nine-seat vigilante counts
 * `bullets`. None left, or a role without a count (the speculator's one pick): no line.
 */
export function usesNote(
  role: string | null | undefined,
  uses: number | null,
  bullets: number | null = null,
): string | undefined {
  const words = role ? USE_WORDS[role] : undefined;
  const left = uses ?? (role === 'vigilante' ? bullets : null);
  if (!words || left === null || left < 1) return undefined;
  return left === 1 ? `your last ${words[0]}` : `${left} ${words[1]} left`;
}

/** The sealed plate when the seat's agent answered, or the server already had an answer. */
export const AGENT_SEALED = 'Your seat’s agent acted for you';

/** What the plate says: the ask before a choice, the act and its target after one. */
export function plateLabel(
  kind: ActionKind | undefined,
  chosen: string | null,
  more: PlateMore = {},
): string {
  if (kind === 'conceal') return CONCEAL_PLATE;
  if (kind === 'speculator_pick')
    return chosen && SIDE_PICKED[chosen] ? `Pick ${SIDE_PICKED[chosen]}` : 'Choose a side';
  if (kind === 'necromancer_target') {
    if (more.body && chosen)
      return `Through seat ${seatNumber(more.body)}, act on seat ${seatNumber(chosen)}`;
    if (more.body) return `Through seat ${seatNumber(more.body)}, choose a seat`;
    return chosen ? 'Choose a body to act through' : 'Choose a body and a seat';
  }
  if (kind === 'bet_target' && chosen) {
    if (chosen === more.me) return 'Bet on yourself';
    if (more.roleNamed)
      return `Bet on seat ${seatNumber(chosen)} as ${ROLE_NAME[more.roleNamed] ?? more.roleNamed}`;
  }
  const verb = (kind && ACT_VERB[kind]) || 'Choose';
  if (!chosen)
    return verb === 'Choose' ? 'Choose a seat' : `Choose a seat to ${verb.toLowerCase()}`;
  return `${verb} seat ${seatNumber(chosen)}`;
}

/** A seat on the wire (`player_N`), as against the server's other words (a side, a no-action). */
export const isSeat = (c: string) => /^player_\d+$/.test(c);

/**
 * The roles a fortune teller may name on a bet: the deal's pool of twelve (the roles the stage
 * names, less the nine-seat villager and wolf), only those dealt when the game says its lineup,
 * never its own.
 */
export function betRoles(
  lineup: readonly string[],
  own: string | null | undefined,
): string[] {
  return Object.keys(ROLE_NAME).filter(
    (r) =>
      r !== 'villager' &&
      r !== 'wolf' &&
      r !== own &&
      (lineup.length === 0 || lineup.includes(r)),
  );
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
  const candidates = pending?.candidates ?? [];
  // the seats hang on the line; the server's other words are plates (a side, conceal, no one)
  const photos = candidates.filter(isSeat);
  const none = noActionWord(candidates);
  const sides = kind === 'speculator_pick' ? candidates.filter((c) => c in SIDE_PLATE) : [];
  const bodies =
    kind === 'necromancer_target' ? (pending?.bodies ?? []).filter(isSeat) : [];
  // a new request, another viewer or a new seeded choice starts the choice afresh; the room
  // itself stays up
  const seed = `${beat.seq}:${me}:${turn?.chosen ?? ''}:${turn?.body ?? ''}:${turn?.roleNamed ?? ''}:${turn?.cardOpen ? 1 : 0}`;
  const [chosen, setChosen] = useSeeded<string | null>(seed, () =>
    turn?.chosen && candidates.includes(turn.chosen) && turn.chosen !== none
      ? turn.chosen
      : null,
  );
  const [body, setBody] = useSeeded<string | null>(seed, () =>
    turn?.body && bodies.includes(turn.body) ? turn.body : null,
  );
  const [roleNamed, setRoleNamed] = useSeeded<string | null>(
    seed,
    () => turn?.roleNamed ?? null,
  );
  const [cardOpen, setCardOpen] = useSeeded(seed, () => !!turn?.cardOpen);
  // what this room sent: a target, or the no-action word; undefined = nothing yet, or not known
  const [pressed, setPressed] = useSeeded<string | null | undefined>(seed, () =>
    turn?.sent === 'you' && turn.chosen !== undefined ? (turn.chosen ?? none) : undefined,
  );

  // the server takes one answer: in once pressed (or answered elsewhere), open again on a failure
  const failed = !!turn?.sendError && !turn.sent;
  const elsewhere = turn?.sent === 'agent' || turn?.sent === 'closed';
  const isIn = !failed && (elsewhere || pressed !== undefined || turn?.sent === 'you');
  const target = isIn ? (elsewhere ? null : pressed) : chosen;
  // only a seat is lit and pinned (a side or a no-action word hangs nowhere)
  const seat = target && isSeat(target) ? target : null;
  const bet = kind === 'bet_target';
  // a role is named on a bet on someone else, never on yourself
  const naming = bet && roleNamed && chosen !== me ? roleNamed : null;
  const more = { body, roleNamed: naming, me };
  const ready =
    kind === 'conceal'
      ? candidates.includes('conceal')
      : kind === 'necromancer_target'
        ? !!chosen && !!body
        : !!chosen;

  const act = (to: string | null) => {
    if (isIn) return;
    setPressed(to ?? none);
    const extra =
      to && kind === 'necromancer_target' && body
        ? { body }
        : to && naming
          ? { roleNamed: naming }
          : undefined;
    onAct?.(to, extra);
  };
  const choose = (c: string) => setChosen((was) => (was === c ? null : c));
  const centre = geometry(props.presentation.hud, sideOpen(props.presentation)).cx;

  return (
    <NightRoom
      {...props}
      role={role}
      photos={photos}
      lit={seat}
      pin={seat}
      pinHome={isIn}
      seed={seed}
      onChoose={isIn ? undefined : choose}
      captions={bet && me && photos.includes(me) ? { [me]: 'yourself' } : undefined}
      bodies={
        kind === 'necromancer_target'
          ? {
              seats: bodies,
              chosen: body,
              onChoose: isIn ? undefined : (b) => setBody((was) => (was === b ? null : b)),
              tag: 'act through',
            }
          : undefined
      }
      pack={isPackRole(role) ? view.packRoster : undefined}
      cardOpen={cardOpen}
      onCard={setCardOpen}
      cardNote={usesNote(role, view.me.role?.uses ?? null, view.me.role?.bullets ?? null)}
      onEmpty={() => {
        setCardOpen(false);
        if (!isIn) {
          setChosen(null);
          setBody(null);
        }
      }}
    >
      {/* once the act is in, the lobby's count: the others acting, until the morning */}
      {isIn ? <NightCount {...props} /> : null}
      {pending && !isIn && sides.length ? (
        <ChoicePlates
          centre={centre}
          choices={sides.map((c) => ({ id: c, label: SIDE_PLATE[c], on: c === chosen }))}
          onToggle={choose}
        />
      ) : null}
      {pending && !isIn && bet && chosen !== me ? (
        <ChoicePlates
          centre={centre}
          caption="name a role for two points"
          sigils
          choices={betRoles(view.lineup, role).map((r) => ({
            id: r,
            label: <Sigil role={r} variant="felt" />,
            title: ROLE_NAME[r],
            on: r === roleNamed,
          }))}
          onToggle={(r) => setRoleNamed((was) => (was === r ? null : r))}
        />
      ) : null}
      {pending ? (
        <ActPlate
          label={plateLabel(kind, chosen, more)}
          // centred in the room, left of an open side slot, so the drawer can run full height
          centre={centre}
          clock={isIn ? null : turn?.clock}
          disabled={!ready || isIn}
          onConfirm={() => act(kind === 'conceal' ? 'conceal' : chosen)}
          secondary={
            none && NO_ACTION_PLATE[none]
              ? { label: NO_ACTION_PLATE[none], disabled: isIn, onClick: () => act(null) }
              : undefined
          }
          note={chosen ? (sides.length ? SIDE_CHANGE_NOTE : CHANGE_NOTE) : undefined}
          error={failed ? turn?.sendError : null}
          sealed={
            isIn
              ? {
                  label: elsewhere ? AGENT_SEALED : sealedLabel(kind, pressed, more),
                  colour: pinColour(role),
                }
              : null
          }
        />
      ) : null}
    </NightRoom>
  );
}

/** The night lobby's pill ("Acted 3 of 9"), from the same total and the same live count. */
export function NightCount({ view, presentation, turn }: SceneProps) {
  const units = nightUnits(view, turn?.progress);
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
