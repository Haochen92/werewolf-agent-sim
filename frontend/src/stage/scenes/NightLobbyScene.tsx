'use client';

/**
 * Night, the lobby (handoff §4.5, beat sheet §5, bench 67): where everyone who is not acting
 * spends the night, and the villager's whole night. The dining car in the dark, the shutter
 * up on the night window, the living seats hung from the flies as chips in a row (the table
 * asleep) and the count pill ("Acted 0 of 5").
 *
 * Nothing here says who is awake: the pill counts the night's units (the special roles the
 * public census says are alive, the pack as one), never names them. The X-ray's hub is the
 * same room with a lamp lit in the wing on every seat that acts tonight; that is the
 * observer's knowledge, drawn from the roles it holds. There a lit card is a way in: a tap jumps
 * to that actor's night (its first spoke; a wolf's, the pack's), and any other card opens that
 * seat's case file (owner, 2026-09-29). The play still runs the spokes in the log's order.
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
import { Atmosphere } from '../Atmosphere';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { CardButton, Notice, NoticeButton, NoticeZone } from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { TopStrip } from '../instruments/TopStrip';
import { chipRow, rowX } from '../instruments/flies';
import { StageMotion } from '../motion';
import { CARD_TEXT } from '../card-text';
import { diningCarPlan } from '../paint/dining-car';
import { seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen, stripButtons } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { notebookGame } from '../notebook';
import { actedTonight } from './replay-night';
import type { SceneProps } from './types';

/** The roles with a night of their own; the pack is one more unit. */
const NIGHT_ROLES = ['healer', 'investigator', 'serial_killer', 'vigilante'];

/**
 * The pill's total, as the server paces it (server/game/pacing.py): one per special role the
 * public census says is alive (the cast, minus the roles deaths revealed), plus the pack.
 */
export function nightUnits(view: GameView): number {
  const alive: Record<string, number> = { ...view.castRoleCounts };
  for (const d of view.dead)
    if (d.role) alive[d.role] = Math.max(0, (alive[d.role] ?? 0) - 1);
  return (
    NIGHT_ROLES.filter((r) => (alive[r] ?? 0) > 0).length + ((alive.wolf ?? 0) > 0 ? 1 : 0)
  );
}

/**
 * Who acts tonight, as the X-ray knows it: every living seat with a night role (a vigilante
 * only while it has a bullet), every living wolf, and anyone the log already shows acting.
 */
export function actorsTonight(view: GameView, day: number): Set<string> {
  const out = new Set<string>();
  for (const seat of view.alive) {
    const role = view.xray.roles[seat];
    if (!role) continue;
    if (role === 'vigilante') {
      const left = (view.xray.privateResults[seat] ?? [])
        .filter((p) => p.kind === 'bullets')
        .at(-1);
      if (left?.kind === 'bullets' && left.count <= 0) continue;
    }
    if (role === 'wolf' || NIGHT_ROLES.includes(role)) out.add(seat);
  }
  for (const a of view.days[day]?.night?.actions ?? []) out.add(a.actor);
  return out;
}


/**
 * The X-ray hub's way into a seat's night: its first spoke that night (a wolf's is the pack's).
 * A seat whose night left nothing to tell (a vigilante holding fire) has none.
 */
export function spokeOf(view: GameView, day: number, seat: string) {
  const actor = view.xray.roles[seat] === 'wolf' ? 'pack' : seat;
  return (b: SceneBeat) =>
    b.id === 'rnight.spoke' && b.day === day && b.spoke?.actor === actor;
}

export function NightLobbyScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <LobbyBeat key={`${props.beat.id}:${props.beat.seq}`} {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
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
  const row = chipRow(g, plan, 'low');
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const phases = view.days[beat.day]?.phases ?? [];
  const voted = phases.includes('voting');
  const actors = xray ? actorsTonight(view, beat.day) : null;
  const myRole = me ? (view.me.role?.role ?? null) : null;
  const H = STAGE_H;
  // live, the acts come in as the night runs (`phase_progress`): the count
  const units = nightUnits(view);
  const actedN = Math.min(turn?.progress?.n ?? 0, units);
  // the hub's cards: an actor's jumps to its night, anyone else's opens its file
  const open = fileTap(presentation, slotInput, true);
  const hub = beat.id === 'rnight.hub';
  // the replay's stop: who acted (from the log ahead), and whose rooms have been seen
  const atStop = hub && stop ? stop : null;
  const acted = atStop ? actedTonight(view, slotInput?.ahead ?? view, beat.day) : null;
  const seen = (seat: string) => {
    const actor = acted?.get(seat);
    return !!actor && !!atStop?.visited.includes(actor);
  };
  // a tap goes into the seat's night where it has one (at the stop: where it acted)
  const goesIn = (seat: string) => !!(acted ? acted.has(seat) : actors?.has(seat));
  const toNight = (seat: string) => {
    // a seat whose night left nothing to tell (a vigilante holding fire): its file
    const into = spokeOf(view, beat.day, seat);
    if (!(atStop ? atStop.onVisit(into) : onSeek?.(into))) open?.(seat);
  };

  return (
    <>
      <Atmosphere room="car" phase="night" hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint
          phase="night"
          from={animate && !voted ? 'day' : null}
          hud={hud}
          fadeDelay={0.1}
          side={side}
        />
        {/* up: the day never brought it down, and a vote's or a lynch's night gathered it already */}
        <Shutter g={g} state="open" />
      </Layer>

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

      <Layer name="light">
        <HouseLights
          phase="night"
          hud={hud}
          pool={{
            x: row.x0 + row.span / 2,
            y: row.rowY - 0.06 * H,
            rx: row.span * 0.56,
            ry: 0.3 * H,
          }}
          dark={46}
          side={side}
        />
      </Layer>

      <Layer name="hud">
        <TableWing
          view={view}
          cast={cast}
          me={me}
          hud={hud}
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          opts={{
            truth: (seat) => (xray ? (view.xray.roles[seat] ?? null) : null),
            lamp: (seat) => !!actors?.has(seat) && !seen(seat),
            glow: (seat) =>
              acted?.has(seat) ? (seen(seat) ? 'visited' : 'acted') : undefined,
            // the word on the card says it: the glow alone did not read as lit (2026-09-30)
            word: (seat) =>
              acted?.has(seat) ? (seen(seat) ? 'seen' : 'visit') : undefined,
            file: open && hub ? (seat) => (goesIn(seat) ? toNight : open)(seat) : open,
            fileLabel: (seat) =>
              hub && goesIn(seat)
                ? `Seat ${seatNumber(seat)}’s night`
                : `Open seat ${seatNumber(seat)}’s file`,
          }}
        />
        <TopStrip
          hud={hud}
          title={`Night ${beat.day}`}
          sub={`Night · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
          side={side}
          count={<CountPill hud={hud} label="Acted" n={actedN} total={units} side={side} />}
        />
        {atStop && acted?.size ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            <Notice
              walnut
              // rooms, as the pill counts them (the pack's two wolves are one)
              title={`Night ${beat.day} · ${new Set(acted.values()).size} acted.`}
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
            <CardButton role={myRole} />
            <Notice
              title={myRole === 'villager' ? 'You sleep' : 'Night falls'}
              arrive={animate}
              delay={1.2}
            >
              {myRole === 'wolf' && (view.packRoster.length || 0) < 2
                ? CARD_TEXT.wolf.nightAlone
                : CARD_TEXT[myRole]?.night}
            </Notice>
          </NoticeZone>
        ) : null}
      </Layer>
    </>
  );
}
