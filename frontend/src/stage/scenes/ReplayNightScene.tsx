'use client';

/**
 * The replay's night with the X-ray on (handoff §4.9, beat sheet §9, bench 67): the night's
 * acts ran at the same time, and live nobody saw any of them. The replay tells them one actor
 * at a time, then all at once.
 *
 * - `rnight.hub`: the lobby, with the wing's lamp lit on every seat that acts tonight. It is
 *   the lobby itself (NightLobbyScene) that draws it; a lit card there jumps to that night.
 * - `rnight.spoke`: one actor's night, told in its own painted room, the one a seated player
 *   of that role sits in live (NightRoom; owner, 2026-09-29, replacing the actor at the day's
 *   stand): its card on the table, the seats it may choose hanging on the line as photographs,
 *   and its choice landing as the live room shows one, the light finding the photo and the pin
 *   going through it, then the act's mark on the print. The pack's spoke is the wolves' room:
 *   its chat a line at a time, then the votes and the kill decided, both teeth landing on the
 *   photo with the pin. The actor's lamp in the wing goes dark as its spoke ends. The case file
 *   beside it holds the actor's file.
 * - `rnight.whole`: back in the car, nobody at the stand, the living hung across the room and
 *   every mark on them at once: the picture the parallel night never shows anyone live.
 *
 * Arrived at, everything is where it ends up. Played, a new actor's room fades in, its photos
 * one after another, the choice lands and the mark pops in while the lamp goes out; the pack's
 * newest line fades into the chat, the room around it at rest.
 */
import { useEffect, useState, type ReactNode } from 'react';
import { Atmosphere } from '../Atmosphere';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { ActMark } from '../instruments/ActMark';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { Notice, NoticeButton, NoticeZone } from '../instruments/Notice';
import { PackChat, type PackEntry } from '../instruments/PackChat';
import { Shutter } from '../instruments/Shutter';
import { Tooth } from '../instruments/Tooth';
import { TopStrip } from '../instruments/TopStrip';
import { chipRow, rowX } from '../instruments/flies';
import { StageMotion, useMotionScale } from '../motion';
import { roomPlan } from '../paint/compartment';
import { diningCarPlan } from '../paint/dining-car';
import { ROLE_NAME, seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen, stripButtons } from '../slot';
import { HUD_CHROME, STAGE_H, STAGE_W, geometry } from '../units';
import { CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { NightLobbyScene, nightUnits, spokeOf } from './NightLobbyScene';
import { NightRoom, ROOM_OF } from './NightRoom';
import { packEntries } from './PackScene';
import {
  ACT_MARK,
  actedAt,
  actedTonight,
  endsBranch,
  isHeld,
  isMarkStep,
  marksAt,
  nightBranchesOf,
  type NightBranch,
  type RowMark,
} from './replay-night';
import { notebookGame } from '../notebook';
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
/** A seat that chose no one: what the box says (the vigilante holding its fire). */
const HOLDS: Record<string, string> = { vigilante: 'holds its fire.' };
/** When, after the beat starts, the choice lands, its mark follows, and the actor's lamp goes out (seconds). */
const MARK_AT = 0.9;
const STAMP_AT = 1.4;
const LAMP_OUT = 1.6;

export function ReplayNightScene(props: SceneProps) {
  // the actor whose card is open on the table (night and actor, so it outlives the room's
  // steps but not the room): the play goes on under it, untouched
  const [cardOf, setCardOf] = useState<string | null>(null);
  const actor =
    props.beat.id === 'rnight.spoke' && props.beat.spoke
      ? `${props.beat.day}:${props.beat.spoke.actor}`
      : null;
  if (cardOf !== null && cardOf !== actor) setCardOf(null);
  if (props.beat.id === 'rnight.hub') return <NightLobbyScene {...props} />;
  return (
    <StageMotion speed={props.presentation.motion}>
      {props.beat.id === 'rnight.whole' ? (
        <NightWhole key={`${props.beat.id}:${props.beat.seq}`} {...props} />
      ) : (
        <SpokeRoom
          key={`${props.beat.id}:${props.beat.seq}:${props.beat.spoke?.step ?? ''}`}
          {...props}
          cardOpen={actor !== null && cardOf === actor}
          onCard={(open) => setCardOf(open ? actor : null)}
        />
      )}
      <SideSlot {...props} />
    </StageMotion>
  );
}

/** "Seat 4", "The pack", or the lone wolf's "Seat 8": who the spoke is about. */
function actorWord(cur: NightBranch | undefined): string {
  if (cur?.actor !== 'pack') return `Seat ${seatNumber(cur?.actor ?? '')}`;
  return cur.seats.length > 1 ? 'The pack' : `Seat ${seatNumber(cur.seats[0] ?? '')}`;
}

/** Plays a moment `at` seconds into a beat played forward; already there when arrived at. */
function useAfter(at: number, animate: boolean): boolean {
  const k = useMotionScale();
  const [done, setDone] = useState(!animate);
  useEffect(() => {
    if (done) return;
    const t = setTimeout(() => setDone(true), at * k * 1000);
    return () => clearTimeout(t);
  }, [done, at, k]);
  return done;
}

/**
 * One actor's spoke, in its own room (NightRoom): the seats it could choose on the line (the
 * living but itself; for the pack, the living who are not wolves), its card on the table, and
 * at the mark step the choice: the light and the pin on the target's photo, then the act's
 * mark (the pack's: both teeth). The pack's line steps are the same room at rest with the next
 * line arriving in the chat.
 */
function SpokeRoom({
  cardOpen,
  onCard,
  ...props
}: SceneProps & { cardOpen: boolean; onCard: (open: boolean) => void }) {
  const { view, beat, presentation, stop, slot: slotInput, onSeek } = props;
  const { hud, animate, cast } = presentation;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const day = beat.day;
  const night = view.days[day]?.night ?? null;
  const branches = nightBranchesOf(view, day);
  const spoke = beat.spoke ?? null;
  const cur: NightBranch | undefined = spoke ? branches[spoke.rank] : undefined;
  const markStep = !!spoke && isMarkStep(spoke, cur);
  const held = isHeld(cur);
  const ends = !!spoke && endsBranch(spoke, cur);
  const total = nightUnits(view);
  const acted = actedAt(branches, spoke, total);
  const pack = cur?.actor === 'pack';
  const role = cur?.role ?? 'villager';
  const seats = cur?.seats ?? [];
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const wolves = new Set(alive.filter((s) => view.xray.roles[s] === 'wolf'));
  const photos = pack
    ? alive.filter((s) => !wolves.has(s))
    : alive.filter((s) => s !== cur?.actor || s === cur?.target);
  const target = markStep ? (cur?.target ?? null) : null;

  // played: the room arrives on the spoke's first step only; the choice lands, then its mark
  const landed = useAfter(MARK_AT, animate);
  const stamped = useAfter(STAMP_AT, animate);
  const lampOut = useAfter(LAMP_OUT, animate);
  const lampOn = (seat: string) =>
    branches.some(
      (b, rank) =>
        b.seats.includes(seat) &&
        (rank > (spoke?.rank ?? Infinity) || (rank === spoke?.rank && !(ends && lampOut))),
    );
  // the wing (2026-09-30): another actor's card goes straight to its room, "Visit ▸" on it
  // ("Seen" once visited), this actor's plays its room again, anyone else's opens a file
  const actors = actedTonight(view, view, day);
  const open = fileTap(presentation, slotInput, true);
  const visit = (seat: string) => {
    const into = spokeOf(view, day, seat);
    if (!(stop ? stop.onVisit(into) : onSeek?.(into))) open?.(seat);
  };
  const tap = stop || onSeek ? (s: string) => (actors.has(s) ? visit : open)?.(s) : open;
  const word = (s: string) => {
    const a = actors.get(s);
    if (!a || seats.includes(s)) return undefined;
    return stop?.visited.includes(a) ? 'seen' : 'visit';
  };

  const plan = roomPlan({ room: ROOM_OF[role] ?? 'healer', hud, side, n: photos.length });
  const marks: Partial<Record<string, ReactNode>> = {};
  if (target && pack) {
    // each wolf's vote a tooth on the photo it chose, the first wolf's on the left, as the live
    // pack room draws them: two on one photo read as the bite, apart as a split
    for (const v of night?.wolfVotes ?? []) {
      const i = seats.indexOf(v.wolf);
      if (i < 0) continue;
      marks[v.votee] = (
        <>
          {marks[v.votee]}
          <Tooth
            key={v.wolf}
            side={seats.length > 1 && i === 0 ? 'left' : 'right'}
            land={animate ? MARK_AT : false}
          />
        </>
      );
    }
  } else if (target && stamped && ACT_MARK[role]) {
    // the act's mark on the print, low on its left, clear of the pin (in the photo's mark box)
    marks[target] = (
      <span className={styles.stamp}>
        <ActMark
          kind={ACT_MARK[role]}
          x={0}
          y={0}
          k={plan.photo.w * 0.3}
          arrive={animate ? 0 : false}
        />
      </span>
    );
  }
  const lit = target && landed ? target : null;
  // the replay's stop: from any room, back to the night's hub
  const back = stop ? (
    <NoticeButton onPress={stop.onBack}>← Back to the night</NoticeButton>
  ) : null;

  return (
    <NightRoom
      {...props}
      // the pack's line steps keep the room still: only the chat moves
      presentation={{ ...presentation, animate: animate && (spoke?.step ?? 0) === 0 }}
      role={role}
      alone={pack && seats.length < 2}
      photos={photos}
      lit={lit}
      pin={lit}
      pinHome
      marks={marks}
      pack={pack ? seats : []}
      // the actor's card opens as a seated player's does, the play going on under it
      cardOpen={cardOpen}
      onCard={onCard}
      cardOwner={
        pack && seats.length > 1
          ? `Seats ${seats.map(seatNumber).join(' and ')}`
          : `Seat ${seatNumber(seats[0] ?? cur?.actor ?? '')}`
      }
      sub={`${beat.label} · ${actorWord(cur)}`}
      count={<CountPill hud={hud} label="Acted" n={acted} total={total} side={side} />}
      wing={{
        lit: (s) => seats.includes(s),
        lamp: lampOn,
        word,
        tap,
        tapLabel: (s) =>
          actors.has(s)
            ? seats.includes(s)
              ? `Seat ${seatNumber(s)}’s night, again`
              : `Seat ${seatNumber(s)}’s night`
            : `Open seat ${seatNumber(s)}’s file`,
      }}
    >
      {cur && !pack ? (
        <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
          <Notice
            chip={cast[seatNumber(cur.actor) - 1]}
            title={actorWord(cur)}
            aqua={(ROLE_NAME[cur.role] ?? cur.role).toLowerCase()}
            arrive={animate}
            delay={0.7}
            walnut={!!back}
            actions={back}
          >
            {held
              ? (HOLDS[cur.role] ?? 'does not act.')
              : `${VERB[cur.role] ?? 'acts on'} seat ${seatNumber(cur.target ?? '')}.`}
          </Notice>
        </NoticeZone>
      ) : null}
      {pack && spoke ? (
        <div
          className={styles.chatBand}
          style={{
            left: g.wingN,
            bottom: HUD_CHROME.band[hud],
            right: STAGE_W - g.wingN - g.room,
          }}
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
            action={back}
          />
        </div>
      ) : null}
    </NightRoom>
  );
}

/**
 * The night whole, in the car: nobody at the stand, the living hung across the room, and every
 * spoke's mark beneath its target at once. With the X-ray on a card opens its seat's file.
 */
function NightWhole({ view, beat, me, presentation, slot: slotInput }: SceneProps) {
  const { hud, xray, cast } = presentation;
  // the room is laid out beside the side slot when it is open (bench 67 drew the film up)
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase: 'night', hud, side });
  const row = chipRow(g, plan, 'low');
  const day = beat.day;
  const branches = nightBranchesOf(view, day);
  const marks = marksAt(branches, null);
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const total = nightUnits(view);

  const byChip = new Map<string, RowMark[]>();
  for (const m of marks) byChip.set(m.seat, [...(byChip.get(m.seat) ?? []), m]);
  const chipAt = (seat: string) => rowX(row, alive.indexOf(seat), alive.length);
  const mk = row.cr * 0.6;
  const H = STAGE_H;
  const pool = {
    x: row.x0 + row.span / 2,
    y: row.rowY - 0.06 * H,
    rx: row.span * 0.56,
    ry: 0.3 * H,
  };

  return (
    <>
      <Atmosphere room="car" phase="night" hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint phase="night" hud={hud} side={side} />
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
            />
          );
        })}
      </Layer>

      <Layer name="instruments">
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
            />
          ));
        })}
      </Layer>

      <Layer name="light">
        <HouseLights phase="night" hud={hud} pool={pool} dark={46} side={side} />
      </Layer>

      <Layer name="hud">
        <TableWing
          view={view}
          cast={cast}
          me={me}
          hud={hud}
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          edit={slotInput?.notebook}
          opts={{
            truth: (s) => (xray ? (view.xray.roles[s] ?? null) : null),
            // nobody speaks here: a card opens its seat's file
            file: fileTap(presentation, slotInput, true),
          }}
        />
        <TopStrip
          hud={hud}
          title={`Night ${day}`}
          sub={beat.label}
          {...stripButtons(presentation, slotInput)}
          side={side}
          count={<CountPill hud={hud} label="Acted" n={total} total={total} side={side} />}
        />
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
