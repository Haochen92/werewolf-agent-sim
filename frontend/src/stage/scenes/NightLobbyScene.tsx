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
 * observer's knowledge, drawn from the roles it holds.
 *
 * Played forward, the chips come down one after another. After a day with no vote the window
 * goes from day to night first (the shutter stayed up all day, so it stays up). After a vote
 * or a lynch there is nothing to change: both of those end on this very picture, night in the
 * window and the shutter up, so the hub starts there rather than jumping back to dusk to fade
 * again.
 */
import type { GameView } from '@/game/types';
import { Atmosphere } from '../Atmosphere';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { CardButton, Notice, NoticeZone } from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { TopStrip } from '../instruments/TopStrip';
import { chipRow, rowX } from '../instruments/flies';
import { StageMotion } from '../motion';
import { CARD_TEXT } from '../card-text';
import { diningCarPlan } from '../paint/dining-car';
import { seatNumber } from '../roles';
import { bandNarrows, sideOpen, stripButtons } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { notebookGame } from '../notebook';
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

export function NightLobbyScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <LobbyBeat key={`${props.beat.id}:${props.beat.seq}`} {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function LobbyBeat({ view, beat, me, presentation, slot: slotInput, turn }: SceneProps) {
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
  const acted = Math.min(turn?.progress?.n ?? 0, units);

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
            lamp: (seat) => !!actors?.has(seat),
          }}
        />
        <TopStrip
          hud={hud}
          title={`Night ${beat.day}`}
          sub={`Night · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
          side={side}
          count={<CountPill hud={hud} label="Acted" n={acted} total={units} side={side} />}
        />
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
