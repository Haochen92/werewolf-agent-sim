'use client';

/**
 * Night, the lobby (handoff §4.5, beat sheet §5, bench 67): where everyone who is not acting
 * spends the night, and the villager's whole night. The dining car in the dark, the shutter
 * up on the night window, the living seats hung from the flies as chips in a row (the table
 * asleep) and the count pill ("Acted 0 of 5").
 *
 * Nothing here says who is awake: the pill counts the night's units (one per living seat,
 * acting tonight or not), never names them. The X-ray's hub is the
 * same room with a lamp lit in the wing on every seat that acts tonight; that is the
 * observer's knowledge, drawn from the roles it holds. There a lit card is a way in: a tap jumps
 * to that actor's night (its first spoke; a wolf's, its own skill's if it has one tonight, else
 * the pack's, and the other once the first is seen), and any other card opens that seat's case
 * file (owner, 2026-09-29). The play still runs the spokes in the log's order.
 *
 * The replay's hub is a stop (owner, 2026-09-30; containers/stops.ts): the play waits here. The
 * seats that acted glow on the wing, the ones whose rooms have been visited keep a steady mark,
 * and the notice at the foot says how many acted and offers the ways on: watch them all, or end
 * the night. A lit seat's room plays, and its end comes back here.
 *
 * Played forward, the chips come down one after another. After a day with no vote the window
 * goes from day to night first (the shutter stayed up all day, so it stays up). After a vote
 * or a lynch there is nothing to change: both of those end on this very picture, night in the
 * window and the shutter up, so the hub starts there rather than jumping back to dusk to fade
 * again.
 */
import type { GameView } from '@/game/types';
import type { SceneBeat } from '../beats/types';
import { Layer } from '../Stage';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { CardButton, Notice, NoticeButton, NoticeZone } from '../instruments/Notice';
import { chipRow, rowX } from '../instruments/flies';
import { cardTextFor, isNineSeat } from '../card-text';
import { diningCarPlan } from '../paint/dining-car';
import { isPackRole, isSoloNightRole, seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarSetSpec } from './CarScene';
import { actedTonight } from './replay-night';
import type { SceneProps } from './types';

/**
 * The pill's total, as the server paces it (server/game/pacing.py): one unit per publicly alive
 * player, whether or not that seat acts tonight, so the total says nothing of which roles still
 * have uses left. Live, the `phase_progress` frame's own total is the word (`progress`); with no
 * frame (a replay, or before the first one lands) it is the living seats, so the two agree.
 */
export function nightUnits(view: GameView, progress?: { total: number }): number {
  return progress?.total ?? view.alive.length;
}

/**
 * Who acts tonight, as the X-ray knows it: every living seat with a night role (a vigilante
 * only while it has a bullet, a speculator until it has picked, a necromancer from night 2),
 * every living pack role, and anyone the log already shows acting.
 */
export function actorsTonight(view: GameView, day: number): Set<string> {
  const out = new Set<string>();
  for (const seat of view.alive) {
    const role = view.xray.roles[seat];
    if (!role) continue;
    if (role === 'vigilante' || role === 'speculator') {
      // nine-seat games count a vigilante's `bullets`; ten-seat ones send `uses`
      const left = (view.xray.privateResults[seat] ?? [])
        .filter((p) => p.kind === 'bullets' || (p.kind === 'uses' && p.role === role))
        .at(-1);
      if (left && 'count' in left && left.count <= 0) continue;
    }
    // the necromancer has no body to act through on night 1, and is asked nothing
    if (role === 'necromancer' && day === 1) continue;
    if (isPackRole(role) || isSoloNightRole(role)) out.add(seat);
  }
  for (const a of view.days[day]?.night?.actions ?? []) out.add(a.actor);
  return out;
}

/** The way into an actor's room on night `day` (a seat, or `pack`): its first spoke. */
export function spokeOf(day: number, actor: string) {
  return (b: SceneBeat) =>
    b.id === 'rnight.spoke' && b.day === day && b.spoke?.actor === actor;
}

/**
 * The rooms a tap on a seat tries, in order (it opens the first that has a spoke): the seat's
 * own (a wolf's skill, a block or a conceal, is its own), then a wolf's pack's; of those, the
 * ones not yet `visited` first. `rooms` are the seat's from `actedTonight` when the log ahead is
 * known; without it a wolf may have either. A seat whose night left nothing to tell (a
 * vigilante holding fire) has no spoke at all.
 */
export function roomsToTry(
  view: GameView,
  seat: string,
  rooms?: readonly string[],
  visited: readonly string[] = [],
): string[] {
  const all = rooms
    ? [...rooms.filter((a) => a !== 'pack'), ...rooms.filter((a) => a === 'pack')]
    : isPackRole(view.xray.roles[seat])
      ? [seat, 'pack']
      : [seat];
  return [
    ...all.filter((a) => !visited.includes(a)),
    ...all.filter((a) => visited.includes(a)),
  ];
}

/** The lobby's body under the car's host (CarScene.tsx): up across its beats, playing by its props. */
export function LobbyBody(props: SceneProps) {
  return <LobbyBeat {...props} />;
}

function LobbyBeat({
  view,
  beat,
  me,
  presentation,
  slot: slotInput,
  turn,
  onSeek,
  stop,
}: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase: 'night', hud, side });
  const row = chipRow(g, plan, 'low', view.seats.length);
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const phases = view.days[beat.day]?.phases ?? [];
  const voted = phases.includes('voting');
  const actors = xray ? actorsTonight(view, beat.day) : null;
  const myRole = me ? (view.me.role?.role ?? null) : null;
  const H = STAGE_H;
  // live, the acts come in as the night runs (`phase_progress`): the count
  const units = nightUnits(view, turn?.progress);
  const actedN = Math.min(turn?.progress?.n ?? 0, units);
  // the hub's cards: an actor's jumps to its night, anyone else's opens its file
  const open = fileTap(presentation, slotInput, true);
  const hub = beat.id === 'rnight.hub';
  // the replay's stop: who acted (from the log ahead), and whose rooms have been seen
  const atStop = hub && stop ? stop : null;
  const acted = atStop ? actedTonight(view, slotInput?.ahead ?? view, beat.day) : null;
  // seen once every room of the seat's has been (a wolf with a skill of its own: both)
  const seen = (seat: string) => {
    const rooms = acted?.get(seat);
    return !!rooms && rooms.every((a) => !!atStop?.visited.includes(a));
  };
  // a tap goes into the seat's night where it has one (at the stop: where it acted)
  const goesIn = (seat: string) => !!(acted ? acted.has(seat) : actors?.has(seat));
  const toNight = (seat: string) => {
    for (const actor of roomsToTry(view, seat, acted?.get(seat), atStop?.visited)) {
      const into = spokeOf(beat.day, actor);
      if (atStop ? atStop.onVisit(into) : onSeek?.(into)) return;
    }
    // a seat whose night left nothing to tell (a vigilante holding fire): its file
    open?.(seat);
  };

  return (
    <>
      <CarSetSpec
        phase="night"
        backdrop={{ from: animate && !voted ? 'day' : null, fadeDelay: 0.1 }}
        // up: the day never brought it down, and a vote's or a lynch's night gathered it already
        shutter={{ state: 'open' }}
        light={{
          pool: {
            x: row.x0 + row.span / 2,
            y: row.rowY - 0.06 * H,
            rx: row.span * 0.56,
            ry: 0.3 * H,
          },
          dark: 46,
        }}
        wing={{
          truth: (seat) => (xray ? (view.xray.roles[seat] ?? null) : null),
          lamp: (seat) => !!actors?.has(seat) && !seen(seat),
          glow: (seat) =>
            acted?.has(seat) ? (seen(seat) ? 'visited' : 'acted') : undefined,
          // the word on the card says it: the glow alone did not read as lit (2026-09-30)
          word: (seat) => (acted?.has(seat) ? (seen(seat) ? 'seen' : 'visit') : undefined),
          file: open && hub ? (seat) => (goesIn(seat) ? toNight : open)(seat) : open,
          fileLabel: (seat) =>
            hub && goesIn(seat)
              ? `Seat ${seatNumber(seat)}’s night`
              : `Open seat ${seatNumber(seat)}’s file`,
        }}
        strip={{
          title: `Night ${beat.day}`,
          sub: `Night · ${beat.label}`,
          side,
          count: <CountPill hud={hud} label="Acted" n={actedN} total={units} side={side} />,
        }}
      />

      <Layer name="figures">
        {alive.map((seat, i) => {
          const n = seatNumber(seat);
          return (
            <Chip
              key={seat}
              glass={g}
              x={rowX(row, i, alive.length)}
              y={row.rowY}
              r={row.cr}
              seat={n}
              character={cast[n - 1]}
              you={seat === me}
              move={animate ? 'lower' : null}
              delay={0.6 + i * 0.06}
            />
          );
        })}
      </Layer>

      <Layer name="hud">
        {atStop && acted?.size ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            <Notice
              walnut
              // rooms, as the pill counts them (the pack's two wolves are one)
              title={`Night ${beat.day} · ${new Set([...acted.values()].flat()).size} acted.`}
              arrive={animate}
              delay={1.2}
              actions={
                <>
                  <NoticeButton lead onPress={atStop.onPlay}>
                    Watch them all ▶
                  </NoticeButton>
                  <NoticeButton onPress={atStop.onEndNight}>End the night →</NoticeButton>
                </>
              }
            >
              Tap a lit seat to visit its room.
            </Notice>
          </NoticeZone>
        ) : null}
        {myRole ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            <CardButton role={myRole} onOpen={turn?.onCard} />
            <Notice
              title={myRole === 'villager' ? 'You sleep' : 'Night falls'}
              arrive={animate}
              delay={1.2}
            >
              {isPackRole(myRole) && (view.packRoster.length || 0) < 2
                ? (cardTextFor(myRole, isNineSeat(view))?.nightAlone ??
                  cardTextFor(myRole, isNineSeat(view))?.night)
                : cardTextFor(myRole, isNineSeat(view))?.night}
            </Notice>
          </NoticeZone>
        ) : null}
      </Layer>
    </>
  );
}
