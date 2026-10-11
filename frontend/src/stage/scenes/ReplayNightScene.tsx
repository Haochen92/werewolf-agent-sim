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
import { Layer } from '../Stage';
import { ActMark } from '../instruments/ActMark';
import { Chip } from '../instruments/Chip';
import { CountPill } from '../instruments/CountPill';
import { Notice, NoticeButton, NoticeZone } from '../instruments/Notice';
import { PackChat, type PackEntry } from '../instruments/PackChat';
import { Tooth } from '../instruments/Tooth';
import { chipRow, rowX } from '../instruments/flies';
import { useMotionScale } from '../motion';
import { roomPlan } from '../paint/compartment';
import { diningCarPlan } from '../paint/dining-car';
import { ROLE_NAME, isPackRole, seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen } from '../slot';
import { bandFoot, STAGE_H, STAGE_W, geometry } from '../units';
import { CarSetSpec } from './CarScene';
import { LobbyBody, nightUnits, roomsToTry, spokeOf } from './NightLobbyScene';
import { NightRoom, ROOM_OF } from './NightRoom';
import { packEntries } from './PackScene';
import {
  ACT_MARK,
  actedAt,
  actLine,
  actedTonight,
  endsBranch,
  isMarkStep,
  marksAt,
  nightBranchesOf,
  type NightBranch,
  type RowMark,
} from './replay-night';
import type { SceneProps } from './types';
import styles from './ReplayNight.module.css';

/** When, after the beat starts, the choice lands, its mark follows, and the actor's lamp goes out (seconds). */
const MARK_AT = 0.9;
const STAMP_AT = 1.4;
const LAMP_OUT = 1.6;

/**
 * The replay's night under the car's host (CarScene.tsx): the hub and the night whole are
 * played in the car and describe its set; a spoke's room describes none, so the car's set
 * comes down while the room is up and returns with the next hub.
 */
export function ReplayNightBody(props: SceneProps) {
  // the actor whose card is open on the table (night and actor, so it outlives the room's
  // steps but not the room): the play goes on under it, untouched
  const [cardOf, setCardOf] = useState<string | null>(null);
  const actor =
    props.beat.id === 'rnight.spoke' && props.beat.spoke
      ? `${props.beat.day}:${props.beat.spoke.actor}`
      : null;
  if (cardOf !== null && cardOf !== actor) setCardOf(null);
  if (props.beat.id === 'rnight.hub') return <LobbyBody {...props} />;
  if (props.beat.id === 'rnight.whole')
    return <NightWhole key={`${props.beat.id}:${props.beat.seq}`} {...props} />;
  return (
    <SpokeRoom
      // the room stays up for the spoke's steps (the pack's chat a line at a time) and the
      // beat moves what moves; each line rebuilt the room's picture (build log §8.9)
      key={actor ?? `${props.beat.id}:${props.beat.seq}`}
      {...props}
      cardOpen={actor !== null && cardOf === actor}
      onCard={(open) => setCardOf(open ? actor : null)}
    />
  );
}

/** "Seat 4", "The pack", or the lone wolf's "Seat 8": who the spoke is about. */
function actorWord(cur: NightBranch | undefined): string {
  if (cur?.actor !== 'pack') return `Seat ${seatNumber(cur?.actor ?? '')}`;
  return cur.seats.length > 1 ? 'The pack' : `Seat ${seatNumber(cur.seats[0] ?? '')}`;
}

/**
 * Plays a moment `at` seconds into a beat played forward; already there when arrived at. The
 * wait starts over with each beat (`seq`): the room stays mounted across a spoke's steps.
 */
function useAfter(at: number, animate: boolean, seq: number): boolean {
  const k = useMotionScale();
  const [state, setState] = useState({ seq, done: !animate });
  if (state.seq !== seq) setState({ seq, done: !animate });
  useEffect(() => {
    if (!animate) return;
    const t = setTimeout(() => setState({ seq, done: true }), at * k * 1000);
    return () => clearTimeout(t);
  }, [seq, animate, at, k]);
  return state.seq === seq && state.done;
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
  const ends = !!spoke && endsBranch(spoke, cur);
  const total = nightUnits(view);
  const acted = actedAt(branches, spoke, total);
  const pack = cur?.actor === 'pack';
  const role = cur?.role ?? 'villager';
  const seats = cur?.seats ?? [];
  const alive = view.seats.filter((s) => view.alive.includes(s));
  const wolves = new Set(alive.filter((s) => isPackRole(view.xray.roles[s])));
  const photos = pack
    ? alive.filter((s) => !wolves.has(s))
    : alive.filter((s) => s !== cur?.actor || s === cur?.target);
  const target = markStep ? (cur?.target ?? null) : null;

  // played: the room arrives on the spoke's first step only; the choice lands, then its mark
  const landed = useAfter(MARK_AT, animate, beat.seq);
  const stamped = useAfter(STAMP_AT, animate, beat.seq);
  const lampOut = useAfter(LAMP_OUT, animate, beat.seq);
  const lampOn = (seat: string) =>
    branches.some(
      (b, rank) =>
        b.seats.includes(seat) &&
        (rank > (spoke?.rank ?? Infinity) || (rank === spoke?.rank && !(ends && lampOut))),
    );
  // the wing (2026-09-30): another actor's card goes straight to its room, "Visit ▸" on it
  // ("Seen" once visited); anyone else's opens a file, and so does a card of the actor whose
  // room this is (until 2026-10-02 it replayed the room, which in the pack's room, every wolf's
  // card, read as a card that would not open; owner)
  const actors = actedTonight(view, view, day);
  const open = fileTap(presentation, slotInput, true);
  // the rooms another actor's card leads to (a wolf's: its skill's, the pack's); this room's
  // own actors' cards open their files
  const elsewhere = (s: string) =>
    seats.includes(s) ? [] : (actors.get(s) ?? []).filter((a) => a !== cur?.actor);
  const visit = (seat: string) => {
    for (const actor of roomsToTry(view, seat, elsewhere(seat), stop?.visited)) {
      const into = spokeOf(day, actor);
      if (stop ? stop.onVisit(into) : onSeek?.(into)) return;
    }
    open?.(seat);
  };
  const tap =
    stop || onSeek ? (s: string) => (elsewhere(s).length ? visit : open)?.(s) : open;
  const word = (s: string) => {
    const rooms = elsewhere(s);
    if (!rooms.length) return undefined;
    return rooms.every((a) => stop?.visited.includes(a)) ? 'seen' : 'visit';
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
            {actLine(cur.role, cur.target)}
          </Notice>
        </NoticeZone>
      ) : null}
      {pack && spoke ? (
        <div
          className={styles.chatBand}
          style={{
            left: g.wingN,
            bottom: bandFoot(hud, 0),
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
  const row = chipRow(g, plan, 'low', view.seats.length);
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
      <CarSetSpec
        phase="night"
        shutter={{ state: 'open' }}
        light={{ pool, dark: 46 }}
        wing={{
          truth: (s) => (xray ? (view.xray.roles[s] ?? null) : null),
          // nobody speaks here: a card opens its seat's file
          file: fileTap(presentation, slotInput, true),
        }}
        strip={{
          title: `Night ${day}`,
          sub: beat.label,
          side,
          count: <CountPill hud={hud} label="Acted" n={total} total={total} side={side} />,
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
