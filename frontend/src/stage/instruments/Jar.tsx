'use client';

/**
 * The ballot jar: clear glass on the vote's table, with a brass lid hung on its own string.
 * Upright while the ballots come in, the chips lying in a pile at the bottom, backs up, so the
 * glass shows how many and never whose (the seated human's own chip lies face up, on their
 * screen only). For the count it is tipped over onto its side at the back rail and the chips
 * roll out of its mouth one by one.
 *
 * The lid is its own piece: it comes down on its string as the table arrives and lifts off
 * (`up`), goes back on when voting closes (`down`), and flies out of the frame when the count
 * begins (`gone`). The glass and the lid are painted pictures (SPRITES.props); the chips are
 * drawn under the glass. Drawn after the vote bench (rev 64 `jar`, `lidGroup`, `pileSVG`).
 * The glass rides an HTML box of its own so its tip is a CSS transform (see `Jar`).
 */
import { motion } from 'motion/react';
import type { CSSProperties, ReactNode } from 'react';
import { SPRITES } from '@/assets/manifest';
import { useMotionScale, useSteps } from '../motion';
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
  /** On its side at the back rail, for the count. */
  tipped?: boolean;
  /** Play the tip over (the count begins). */
  tipping?: boolean;
  /** Chips that drop in this beat, in the order they fall, and when the first starts. */
  falling?: number[];
  fallDelay?: number;
}

/** Where the chips lie once the jar is on its side, in the jar's own (upright) drawing. */
function lyingSpots(v: VoteGeometry, n: number): [number, number][] {
  const J = jarGeometry(v),
    { r } = v;
  return Array.from({ length: n }, (_, i) => [
    v.cx + (i % 2 ? 0.6 : -0.6) * r + (rnd(i, 601) - 0.5) * r * 0.5,
    Math.min(J.yR + r * 1.1 + Math.floor(i / 2) * r * 1.25, J.floor - r * 1.1),
  ]);
}

const FALL = [0.45, 0, 0.85, 0.7] as [number, number, number, number];
const TIP = [0.4, 0.6, 0.35, 1] as [number, number, number, number];

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
 * its own small drawing inside. The tip is a CSS transform on that box (motion's `x`, `y`,
 * `rotate` and `scale`, about the base's centre), so the browser repaints one finished picture
 * through a transform each frame; the same move as an SVG `transform` on a group inside the
 * table's drawing relaid out the drawing every frame and stuttered on a phone (build log
 * §8.4). The chips dropping in are drawn over the glass by `JarFallers`, in the table's drawing.
 */
export function Jar({
  v,
  n,
  mine,
  tipped = false,
  tipping = false,
  falling,
  fallDelay = 0,
}: JarProps) {
  const k = useMotionScale();
  const step = useSteps();
  // a phone draws the glass far under its file's size: its copy
  const glass = useSmall() ? SPRITES.small.props.jarGlass : SPRITES.props.jarGlass;
  const J = jarGeometry(v),
    { cx, base, r } = v,
    { w, h } = J;
  const { order, at } = fallTimes(falling, fallDelay);

  const upright = pileSpots(v, n).map(([x, y], i) => {
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
  const lying = lyingSpots(v, n).map(([x, y], i) => <ChipBack key={i} x={x} y={y} r={r} />);

  // the picture's file over the painted glass's height: the box the glass is drawn in
  const s = h / GLASS_PX.h;
  const box = {
    x: cx - w / 2 - GLASS_PX.x * s,
    y: base - h - GLASS_PX.y * s,
    w: GLASS_PX.W * s,
    h: GLASS_PX.H * s,
  };
  // the painted glass over its chips, so they take its mist and highlights
  const sheet = (pile: ReactNode) => (
    <svg viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`} style={SHEET} aria-hidden="true">
      {pile}
      <image
        href={glass.src}
        x={box.x}
        y={box.y}
        width={box.w}
        height={box.h}
        preserveAspectRatio="none"
      />
    </svg>
  );

  const pile = !tipped ? (
    upright
  ) : !tipping ? (
    lying
  ) : (
    <>
      <Tween play delay={1.25} duration={0.25} ease="linear" opacity={(p) => 1 - p}>
        {upright}
      </Tween>
      <Tween play delay={1.3} duration={0.25} ease="linear" opacity={(p) => p}>
        {lying}
      </Tween>
    </>
  );
  const T = J.tip;
  const standing = { x: 0, y: 0, rotate: 0, scale: 1 };
  const over = { x: T.dx, y: T.dy, rotate: T.ang, scale: T.sc };
  return (
    <motion.div
      data-moves=""
      style={{
        position: 'absolute',
        left: box.x,
        top: box.y,
        width: box.w,
        height: box.h,
        transformOrigin: `${T.ox - box.x}px ${T.oy - box.y}px`,
      }}
      initial={tipping ? standing : false}
      animate={tipped ? over : standing}
      // not played: at rest in its state at once, also when the state changes under it
      transition={
        tipping ? step({ duration: 0.8 * k, delay: 0.9 * k, ease: TIP }) : { duration: 0 }
      }
    >
      {sheet(pile)}
    </motion.div>
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
 * a solid thing's for the glass. Tipped, it lies along the jar at the back rail; played, the
 * one fades into the other as the jar goes over.
 */
export function JarShadow({
  v,
  tipped,
  tipping = false,
  shade,
}: {
  v: VoteGeometry;
  tipped: boolean;
  tipping?: boolean;
  /** The soft shadow's fill (VoteTable's `SoftShadow`). */
  shade: string;
}) {
  const J = jarGeometry(v),
    { cx, base } = v,
    T = J.tip;
  const up = (
    <ellipse
      cx={cx + J.w * 0.16}
      cy={base - v.depth * 0.02}
      rx={J.w * 0.64}
      ry={v.depth * 0.26}
      fill={`url(#${shade})`}
      opacity={0.7}
    />
  );
  // lying: its length along the rail, its near side on the table's back line
  const len = J.h * T.sc,
    x = cx + T.dx + len * 0.06,
    y = v.topY - v.depth * 1.05 + J.w * T.sc * 0.02;
  const down = (
    <ellipse
      cx={x}
      cy={y}
      rx={len * 0.56}
      ry={v.depth * 0.22}
      fill={`url(#${shade})`}
      opacity={0.7}
    />
  );
  if (!tipped) return up;
  if (!tipping) return down;
  return (
    <>
      <Tween play delay={1.1} duration={0.5} ease="linear" opacity={(p) => 1 - p}>
        {up}
      </Tween>
      <Tween play delay={1.3} duration={0.5} ease="linear" opacity={(p) => p}>
        {down}
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

/** The brass lid on its string, tied round the ring on its top. */
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
