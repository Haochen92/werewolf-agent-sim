'use client';

/**
 * The replay's night with the X-ray on (handoff §4.9, beat sheet §9, bench 67): the night's
 * acts ran at the same time, and live nobody saw any of them. The replay tells them one actor
 * at a time, then all at once.
 *
 * - `rnight.hub`: the lobby, with the wing's lamp lit on every seat that acts tonight. It is
 *   the lobby itself (NightLobbyScene) that draws it.
 * - `rnight.spoke`: one actor's night seen from the house. Its puppet stands at the stand (the
 *   pack as its two wolves side by side, or the lone wolf), its instrument lies on the rail,
 *   and the living hang as chips in a row at the window's height. The marks the earlier
 *   spokes left are already on the row; this spoke's mark lands on its target. The pack's
 *   spoke is told a line at a time in its chat, then the kill decided and the bite landing.
 *   The actor's lamp in the wing goes dark as its spoke ends. The film, when it has the side
 *   slot, holds what the actor weighed from past games and the note it wrote.
 * - `rnight.whole`: nobody at the stand, the row across the room, and every mark on it at
 *   once: the picture the parallel night never shows anyone live.
 *
 * Arrived at, everything is where it ends up. Played, a new actor rises into the stand with
 * its instrument, the pack's newest line fades into the chat, and the mark pops in on its
 * chip while the lamp goes out.
 */
import { useEffect, useState } from 'react';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { Puppet } from '../cast/Puppet';
import { ActMark } from '../instruments/ActMark';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { Notice, NoticeZone } from '../instruments/Notice';
import { PackChat, type PackEntry } from '../instruments/PackChat';
import { RailInstrument } from '../instruments/RailInstrument';
import { Shutter } from '../instruments/Shutter';
import { Plaque, Stand } from '../instruments/Stand';
import { TopStrip } from '../instruments/TopStrip';
import { WallClock } from '../instruments/WallClock';
import { chipRow, rowX } from '../instruments/flies';
import { StageMotion, useMotionScale } from '../motion';
import { diningCarPlan } from '../paint/dining-car';
import type { Special } from '../paint/draw';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { bandNarrows, sideOpen, stripButtons } from '../slot';
import { HUD_CHROME, STAGE_H, STAGE_W, geometry, standBox } from '../units';
import { CarFloor, CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { NightLobbyScene, nightUnits } from './NightLobbyScene';
import { packEntries } from './PackScene';
import { standSet } from './game-over';
import {
  actedAt,
  isMarkStep,
  marksAt,
  nightBranchesOf,
  type NightBranch,
  type RowMark,
} from './replay-night';
import type { SceneProps } from './types';
import styles from './ReplayNight.module.css';

/** What each act does, as the box says it (bench 67 `VERB`). */
const VERB: Record<string, string> = {
  healer: 'protects',
  investigator: 'checks',
  vigilante: 'shoots',
  serial_killer: 'marks',
  wolf: 'chooses',
};
/** When, after the beat starts, the mark lands and the actor's lamp goes out (seconds). */
const MARK_AT = 0.9;
const LAMP_OUT = 1.6;

export function ReplayNightScene(props: SceneProps) {
  if (props.beat.id === 'rnight.hub') return <NightLobbyScene {...props} />;
  return (
    <StageMotion speed={props.presentation.motion}>
      <NightSpoke
        key={`${props.beat.id}:${props.beat.seq}:${props.beat.spoke?.step ?? ''}`}
        {...props}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function NightSpoke({ view, beat, me, presentation, slot: slotInput }: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  // the room is laid out beside the side slot when it is open (bench 67 drew the film up)
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase: 'night', hud, side });
  const whole = beat.id === 'rnight.whole';
  const row = chipRow(g, plan, whole ? 'low' : 'high');
  const day = beat.day;
  const night = view.days[day]?.night ?? null;
  const branches = nightBranchesOf(view, day);
  const spoke = whole ? null : (beat.spoke ?? null);
  const cur: NightBranch | undefined = spoke ? branches[spoke.rank] : undefined;
  const markStep = !!spoke && isMarkStep(spoke, cur);
  const marks = marksAt(branches, spoke);
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const total = nightUnits(view);
  const acted = actedAt(branches, spoke, total);

  // the actor's lamp stays lit through its spoke and goes out as the mark lands
  const [out, setOut] = useState(!animate);
  useEffect(() => {
    if (out) return;
    const t = setTimeout(() => setOut(true), LAMP_OUT * k * 1000);
    return () => clearTimeout(t);
  }, [out, k]);
  const lampOn = (seat: string) =>
    !whole &&
    branches.some(
      (b, rank) =>
        b.seats.includes(seat) &&
        (rank > (spoke?.rank ?? Infinity) || (rank === spoke?.rank && !(markStep && out))),
    );

  // the figures at the stand, and the stand widened for two
  const seats = cur?.seats ?? [];
  const set = standSet(seats.length);
  const stand = standBox(g);
  const rising = animate && spoke?.step === 0;
  const instrumentK = 0.14 * g.pwid;

  const byChip = new Map<string, RowMark[]>();
  for (const m of marks) byChip.set(m.seat, [...(byChip.get(m.seat) ?? []), m]);
  const chipAt = (seat: string) => rowX(row, alive.indexOf(seat), alive.length);
  const mk = row.cr * (whole ? 0.6 : 0.55);

  const target = markStep ? (cur?.target ?? null) : null;
  // the instrument on the rail, with a patch of light on it so it reads in the dark
  const tool = {
    x: g.cx + (stand.w / 2) * set.widen * 0.72,
    y: g.railY - instrumentK * 0.5,
  };
  const toolLight: Special[] = cur
    ? [[tool.x, tool.y - instrumentK * 1.4, g.railY, instrumentK * 1.5, 0.8]]
    : [];
  const specials: Special[] =
    target && alive.includes(target)
      ? [[chipAt(target), 0, row.rowY + row.cr, row.cr * 1.6, 0.9]]
      : [];
  const H = STAGE_H;
  const pool = whole
    ? { x: row.x0 + row.span / 2, y: row.rowY - 0.06 * H, rx: row.span * 0.56, ry: 0.3 * H }
    : {
        x: g.cx,
        y: g.railY - g.pwid * 0.9,
        rx: g.pwid * 0.55 * set.widen,
        ry: g.pwid * 0.95,
      };

  const actorWord =
    cur?.actor === 'pack'
      ? seats.length > 1
        ? 'The pack'
        : `Seat ${seatNumber(seats[0] ?? '')}`
      : `Seat ${seatNumber(cur?.actor ?? '')}`;
  const bullets =
    cur?.role === 'vigilante'
      ? ((
          (view.xray.privateResults[cur.actor] ?? [])
            .filter((p) => p.kind === 'bullets')
            .at(-1) as { count: number } | undefined
        )?.count ?? 2)
      : 0;

  return (
    <>
      <Layer name="paint">
        <CarPaint phase="night" hud={hud} wallClock={false} side={side} />
        {plan.clock ? (
          <WallClock
            x={plan.clock.x}
            y={plan.clock.y}
            r={plan.clock.r}
            time={(6 * acted) / Math.max(1, total)}
            from={animate && markStep ? (6 * (acted - 1)) / Math.max(1, total) : null}
            phase="night"
          />
        ) : null}
        <Shutter g={g} state="open" />
      </Layer>
      <CarFloor g={g} />

      <Layer name="figures">
        {seats.map((seat, i) => {
          const n = seatNumber(seat);
          return (
            <Puppet
              key={seat}
              g={g}
              character={cast[n - 1]}
              seat={n}
              state="base"
              dx={set.offsets[i] * g.pwid}
              scale={set.scale}
              arrive={rising ? 0.2 + i * 0.22 : false}
            />
          );
        })}
        {alive.map((seat, i) => {
          const n = seatNumber(seat);
          return (
            <Chip
              key={seat}
              x={rowX(row, i, alive.length)}
              y={row.rowY}
              r={row.cr}
              seat={n}
              character={cast[n - 1]}
              you={seat === me}
              edge={seat === target ? 'lit' : null}
            />
          );
        })}
      </Layer>

      {seats.length ? (
        <Layer name="stand">
          <Stand g={g} widen={set.widen}>
            <Plaque
              seat={seats.map(seatNumber)}
              tag={cur?.actor === 'pack' ? 'Wolves' : ROLE_NAME[cur?.role ?? '']}
              tone={factionOf(cur?.role) ?? undefined}
            />
          </Stand>
        </Layer>
      ) : null}

      <Layer name="instruments">
        {cur ? (
          <RailInstrument
            role={cur.role}
            x={tool.x}
            y={tool.y}
            k={instrumentK}
            bullets={bullets}
            arrive={rising ? 0.6 : false}
          />
        ) : null}
        {[...byChip].flatMap(([seat, list]) => {
          const x = chipAt(seat);
          if (!alive.includes(seat)) return [];
          const cols = Math.min(2, list.length);
          return list.map((m, i) => (
            <ActMark
              key={`${seat}-${m.rank}`}
              kind={m.kind}
              x={x + ((i % 2) - (cols - 1) / 2) * mk * 2.3}
              y={row.rowY + row.cr + mk * 1.2 + Math.floor(i / 2) * mk * 2.4}
              k={mk}
              arrive={m.landing && animate ? MARK_AT : false}
            />
          ));
        })}
      </Layer>

      <Layer name="light">
        <HouseLights
          phase="night"
          hud={hud}
          pool={pool}
          specials={specials}
          quiet={toolLight}
          dark={whole ? 66 : 62}
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
          opts={{
            truth: (s) => (xray ? (view.xray.roles[s] ?? null) : null),
            lit: (s) => seats.includes(s),
            lamp: lampOn,
          }}
        />
        <TopStrip
          hud={hud}
          title={`Night ${day}`}
          sub={whole ? beat.label : `${beat.label} · ${actorWord}`}
          {...stripButtons(presentation, slotInput)}
        />
        <CountPill hud={hud} label="Acted" n={acted} total={total} side={side} />
        {cur && cur.actor !== 'pack' ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            <Notice
              chip={cast[seatNumber(cur.actor) - 1]}
              title={actorWord}
              aqua={(ROLE_NAME[cur.role] ?? cur.role).toLowerCase()}
              arrive={animate}
              delay={0.7}
            >
              {VERB[cur.role] ?? 'acts on'} seat {seatNumber(cur.target ?? '')}.
            </Notice>
          </NoticeZone>
        ) : null}
        {cur?.actor === 'pack' && spoke ? (
          <div
            className={styles.chatBand}
            style={{ bottom: HUD_CHROME.band[hud], right: STAGE_W - g.wingN - g.room }}
          >
            <PackChat
              entries={chatAt(packEntries(night), spoke.step, markStep)}
              you=""
              mate={seats.length > 1 ? seats[1] : null}
              cast={cast}
              heading={
                seats.length > 1
                  ? `The pack · seats ${seats.map(seatNumber).join(' and ')}`
                  : `Seat ${seatNumber(seats[0] ?? '')} hunts alone`
              }
              arriving={markStep ? decidedSeq(night) : beat.seq}
              arrive={animate}
            />
          </div>
        ) : null}
      </Layer>
    </>
  );
}

/** The chat at a pack step: its lines up to this one; at the mark, the votes and the kill too. */
function chatAt(all: PackEntry[], step: number, mark: boolean): PackEntry[] {
  const talk = all.filter((e) => e.kind !== 'gm');
  if (mark) return talk;
  const lines = talk.filter((e) => e.kind === 'line');
  return lines.slice(0, step + 1);
}

function decidedSeq(night: Parameters<typeof packEntries>[0]): number | undefined {
  return packEntries(night).find((e) => e.kind === 'decided')?.seq;
}
