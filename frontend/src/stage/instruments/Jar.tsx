'use client';

/**
 * The ballot jar: a footed glass sweet jar on the vote's table (the felt set, 2026-10-17), with a
 * domed glass lid hung on its own string.
 * In the centre while the ballots come in, the chips lying in a pile at the bottom, backs up, so
 * the glass shows how many and never whose (the seated human's own chip lies face up, on their
 * screen only). For the count it stands at the back of the table, to the right, and the chips
 * are lifted out of its mouth one by one (it was tipped onto its side until 2026-10-17).
 *
 * The lid is its own piece: it comes down on its string as the table arrives and lifts off
 * (`up`), goes back on when voting closes (`down`), and flies out of the frame when the count
 * begins (`gone`). The glass and the lid are painted pictures (SPRITES.props); the chips are
 * drawn under the glass. Drawn after the vote bench (rev 64 `jar`, `lidGroup`, `pileSVG`).
 * The glass sits in an HTML box of its own, its own small drawing inside (see `Jar`).
 */
import type { CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { rnd } from '../paint/draw';
import { useSmall } from '../set';
import { STAGE_H } from '../units';
import { Tween, about, lerp } from './Tween';
import { ChipBack, ChipFace, FlatChip, type ChipFaceProps } from './VoteChip';
import {
  GLASS_PX,
  LID_PX,
  jarGeometry,
  pileSpots,
  type VoteGeometry,
} from './vote-geometry';

type Face = Omit<ChipFaceProps, 'x' | 'y' | 'r' | 'sw'>;

export interface JarProps {
  v: VoteGeometry;
  /** Chips in the jar. */
  n: number;
  /** Which chip is the viewer's own, shown face up, and its face. */
  mine?: { index: number; face: Face } | null;
  /** Standing at the back of the table, for the count. */
  counting?: boolean;
  /** Played: the count begins, and the jar fades from the centre to the back. */
  countBegins?: boolean;
  /** Chips that drop in this beat, in the order they fall, and when the first starts. */
  falling?: number[];
  fallDelay?: number;
}

const FALL = [0.45, 0, 0.85, 0.7] as [number, number, number, number];

/** When each falling chip starts: `fallDelay`, then 0.09 s apart in the order they fall. */
function fallTimes(falling: number[] | undefined, fallDelay: number) {
  const order = new Map((falling ?? []).map((i, k) => [i, k]));
  return { order, at: (i: number) => fallDelay + (order.get(i) ?? 0) * 0.09 };
}

/* the glass box's own drawing fills the box; its viewBox is the box, in the stage's units */
const SHEET: CSSProperties = {
  position: 'absolute',
  inset: 0,
  width: '100%',
  height: '100%',
  overflow: 'visible',
};

/**
 * The glass with the chips in it: an HTML box over the table, the glass picture's size, with
 * its own small drawing inside. It never moves (owner 2026-10-17: the sweet jar is not tipped
 * out): it stands in the centre while the ballots come in and at the back of the table, to the
 * right and smaller, for the count. When the count begins the one fades out and the other in,
 * an opacity on a group inside each box's drawing (`Tween`, driven in JavaScript), so no layer is
 * made for the fade. The chips dropping in are drawn over the glass by `JarFallers`, in the
 * table's drawing; the counted ones leave by the back jar's mouth (`VoteTable`'s `ArcChip`).
 */
export function Jar({
  v,
  n,
  mine,
  counting = false,
  countBegins = false,
  falling,
  fallDelay = 0,
}: JarProps) {
  // a phone draws the glass far under its file's size: its copy
  const glass = useSmall() ? SPRITES.small.props.jarGlass : SPRITES.props.jarGlass;
  const J = jarGeometry(v),
    { cx, base, r } = v,
    { w, h } = J;
  const { order, at } = fallTimes(falling, fallDelay);

  const pile = pileSpots(v, n).map(([x, y], i) => {
    const chip = (
      <FlatChip key={i} x={x} y={y} r={r} face={mine?.index === i ? mine.face : null} />
    );
    // a falling chip's place in the pile fills as it arrives
    return order.has(i) ? (
      <Tween
        key={i}
        play
        delay={at(i) + 0.72}
        duration={0.15}
        ease="easeOut"
        opacity={(p) => p}
      >
        {chip}
      </Tween>
    ) : (
      chip
    );
  });

  // the picture's file over the painted glass's height: the box the glass is drawn in
  const s = h / GLASS_PX.h;
  const box = {
    x: cx - w / 2 - GLASS_PX.x * s,
    y: base - h - GLASS_PX.y * s,
    w: GLASS_PX.W * s,
    h: GLASS_PX.H * s,
  };
  // the same box at the back: scaled about the base's centre and set down there
  const A = J.aside;
  const back = {
    x: A.x + (box.x - cx) * A.sc,
    y: A.y + (box.y - base) * A.sc,
    w: box.w * A.sc,
    h: box.h * A.sc,
  };
  // the painted glass over its chips, so they take its mist and highlights
  const glassOver = (
    <>
      {pile}
      <image
        href={glass.src}
        x={box.x}
        y={box.y}
        width={box.w}
        height={box.h}
        preserveAspectRatio="none"
      />
    </>
  );
  const sheet = (where: typeof box, fade?: 'out' | 'in') => (
    <div
      style={{
        position: 'absolute',
        left: where.x,
        top: where.y,
        width: where.w,
        height: where.h,
      }}
    >
      <svg viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`} style={SHEET} aria-hidden="true">
        {fade ? (
          <Tween
            play
            delay={fade === 'out' ? 0.9 : 1.05}
            duration={0.35}
            ease="linear"
            opacity={(p) => (fade === 'out' ? 1 - p : p)}
          >
            {glassOver}
          </Tween>
        ) : (
          glassOver
        )}
      </svg>
    </div>
  );
  if (!counting) return sheet(box);
  if (!countBegins) return sheet(back);
  return (
    <>
      {sheet(box, 'out')}
      {sheet(back, 'in')}
    </>
  );
}

/** The chips dropping into the jar's mouth this beat, drawn over the glass in the table's drawing. */
export function JarFallers({
  v,
  mine,
  falling,
  fallDelay = 0,
}: Pick<JarProps, 'v' | 'mine' | 'falling' | 'fallDelay'>) {
  const J = jarGeometry(v),
    { cx, r } = v,
    { yR } = J;
  const { at } = fallTimes(falling, fallDelay);
  return (
    <>
      {(falling ?? []).map((i) => {
        const jx = (rnd(i, 501) - 0.5) * r * 1.6,
          y0 = yR - r * 0.6,
          fy = -(yR + 3 * r);
        const face = mine?.index === i ? mine.face : null;
        return (
          <Tween
            key={`f${i}`}
            play
            delay={at(i)}
            duration={0.75}
            ease={FALL}
            transform={(p) => `translate(0 ${lerp(fy, 0, p)})`}
            opacity={(p) => (p < 0.86 ? 1 : 1 - (p - 0.86) / 0.14)}
          >
            {face ? (
              <ChipFace x={cx + jx} y={y0} r={r} {...face} />
            ) : (
              <ChipBack x={cx + jx} y={y0} r={r} />
            )}
          </Tween>
        );
      })}
    </>
  );
}

/**
 * The jar's shadow on the table (the rooms' atmosphere), to the right of its foot, lighter than
 * a solid thing's for the glass. For the count it lies under the jar at the back; played, the
 * one fades into the other with the jar.
 */
export function JarShadow({
  v,
  counting,
  countBegins = false,
  shade,
}: {
  v: VoteGeometry;
  counting: boolean;
  countBegins?: boolean;
  /** The soft shadow's fill (VoteTable's `SoftShadow`). */
  shade: string;
}) {
  const J = jarGeometry(v),
    { cx, base } = v,
    A = J.aside;
  const at = (x: number, y: number, k: number) => (
    <ellipse
      cx={x + J.w * 0.16 * k}
      cy={y - v.depth * 0.02 * k}
      rx={J.w * 0.64 * k}
      ry={v.depth * 0.26 * k}
      fill={`url(#${shade})`}
      opacity={0.7}
    />
  );
  const front = at(cx, base, 1),
    back = at(A.x, A.y, A.sc);
  if (!counting) return front;
  if (!countBegins) return back;
  return (
    <>
      <Tween play delay={0.9} duration={0.35} ease="linear" opacity={(p) => 1 - p}>
        {front}
      </Tween>
      <Tween play delay={1.05} duration={0.35} ease="linear" opacity={(p) => p}>
        {back}
      </Tween>
    </>
  );
}

export type LidState = 'up' | 'down' | 'gone';

export interface JarLidProps {
  v: VoteGeometry;
  state: LidState;
  /** Played: the lid moves here from this state. */
  from?: LidState | null;
  delay?: number;
  /** Played at "voting opens": the lid's string comes down first, then the lid lifts. */
  arriving?: boolean;
}

const LID_EASE = [0.3, 0.8, 0.4, 1] as [number, number, number, number];

/** The glass lid on its string, tied round the neck of its knob. */
export function JarLid({ v, state, from, delay, arriving = false }: JarLidProps) {
  const pic = useSmall() ? SPRITES.small.props.jarLid : SPRITES.props.jarLid;
  const J = jarGeometry(v),
    { lw, ly, ks, knob, cx, cy } = J.lid;
  const pose = (s: LidState) =>
    s === 'up'
      ? J.lidUp
      : s === 'gone'
        ? { x: 0, y: -1.2 * STAGE_H, rot: 0 }
        : { x: 0, y: 0, rot: 0 };
  const a = pose(from ?? state),
    b = pose(state);
  const at = (p: number) =>
    about(cx, cy, {
      dx: lerp(a.x, b.x, p),
      dy: lerp(a.y, b.y, p),
      rot: lerp(a.rot, b.rot, p),
    });
  const string = (
    <g>
      <line
        x1={cx}
        y1={-2 * STAGE_H}
        x2={cx}
        y2={knob}
        stroke="#24180c"
        strokeOpacity={0.8}
        strokeWidth={3}
      />
      <line
        x1={cx}
        y1={-2 * STAGE_H}
        x2={cx}
        y2={knob}
        stroke="#d9c9a0"
        strokeWidth={1.4}
      />
    </g>
  );
  const lid = (
    <g>
      {arriving ? (
        <Tween play delay={1.9} duration={0.3} ease="linear" opacity={(p) => p}>
          {string}
        </Tween>
      ) : (
        string
      )}
      <image
        href={pic.src}
        x={cx - lw / 2 - LID_PX.x * ks}
        y={ly - LID_PX.y * ks}
        width={LID_PX.W * ks}
        height={LID_PX.H * ks}
        preserveAspectRatio="none"
      />
    </g>
  );
  if (!from || from === state) return <g transform={at(1)}>{lid}</g>;
  const ld = delay ?? (arriving ? 2.1 : 0.25);
  return (
    <Tween
      play
      delay={ld}
      duration={state === 'down' ? 0.6 : 0.7}
      ease={state === 'down' ? 'easeIn' : LID_EASE}
      transform={at}
    >
      {lid}
    </Tween>
  );
}
