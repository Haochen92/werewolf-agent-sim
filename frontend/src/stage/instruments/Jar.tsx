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
 * begins (`gone`). Drawn after the vote bench (rev 64 `jar`, `lidGroup`, `pileSVG`).
 */
import type { ReactNode } from 'react';
import { rnd } from '../paint/draw';
import { CAR, K2 } from '../paint/materials';
import { STAGE_H } from '../units';
import { Tween, about, lerp } from './Tween';
import { ChipBack, ChipFace, FlatChip, type ChipFaceProps } from './VoteChip';
import { jarGeometry, pileSpots, type VoteGeometry } from './vote-geometry';

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

/** The glass's outline, as one path. */
function bodyPath(v: VoteGeometry) {
  const { cx, base } = v,
    J = jarGeometry(v),
    { w, wN, yS, yN, yR, rb } = J;
  return `M${cx - w / 2},${base - rb} Q${cx - w / 2},${base} ${cx - w / 2 + rb},${base} H${cx + w / 2 - rb} Q${cx + w / 2},${base} ${cx + w / 2},${base - rb} V${yS} C${cx + w / 2},${yS - (yS - yN) * 0.7} ${cx + wN / 2},${yN + (yS - yN) * 0.35} ${cx + wN / 2},${yN} V${yR} H${cx - wN / 2} V${yN} C${cx - wN / 2},${yN + (yS - yN) * 0.35} ${cx - w / 2},${yS - (yS - yN) * 0.7} ${cx - w / 2},${yS}Z`;
}

/** Where the chips lie once the jar is on its side, in the jar's own (upright) drawing. */
function lyingSpots(v: VoteGeometry, n: number): [number, number][] {
  const J = jarGeometry(v),
    { r } = v;
  return Array.from({ length: n }, (_, i) => [
    v.cx + (i % 2 ? 0.6 : -0.6) * r + (rnd(i, 601) - 0.5) * r * 0.5,
    Math.min(J.yR + r * 1.1 + Math.floor(i / 2) * r * 1.25, v.base - r * 1.1),
  ]);
}

const FALL = [0.45, 0, 0.85, 0.7] as [number, number, number, number];
const TIP = [0.4, 0.6, 0.35, 1] as [number, number, number, number];

export function Jar({
  v,
  n,
  mine,
  tipped = false,
  tipping = false,
  falling,
  fallDelay = 0,
}: JarProps) {
  const J = jarGeometry(v),
    { cx, base, r } = v,
    { w, h, wN, yR, rb } = J,
    d = bodyPath(v);
  const order = new Map((falling ?? []).map((i, k) => [i, k]));
  const at = (i: number) => fallDelay + (order.get(i) ?? 0) * 0.09;

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

  const glass = (pile: ReactNode) => (
    <g>
      <path d={d} fill="#1b2a2c" fillOpacity={0.38} />
      <ellipse
        cx={cx}
        cy={yR}
        rx={wN / 2}
        ry={wN * 0.13}
        fill="#0c0a07"
        fillOpacity={0.35}
        stroke={K2}
        strokeWidth={1.4}
      />
      {pile}
      <path d={d} fill="#d6ecec" fillOpacity={0.13} stroke={K2} strokeWidth={2.2} />
      <path
        d={`M${cx - w * 0.36},${base - h * 0.1} V${J.yS + h * 0.02}`}
        stroke="#fff"
        strokeOpacity={0.55}
        strokeWidth={5}
        strokeLinecap="round"
      />
      <path
        d={`M${cx + w * 0.34},${base - h * 0.14} V${base - h * 0.3}`}
        stroke="#fff"
        strokeOpacity={0.38}
        strokeWidth={3}
        strokeLinecap="round"
      />
      <path
        d={`M${cx - w / 2 + rb},${base - 3} H${cx + w / 2 - rb}`}
        stroke="#fff"
        strokeOpacity={0.3}
        strokeWidth={3}
      />
      <path
        d={`M${cx - wN / 2},${yR} a${wN / 2},${wN * 0.13} 0 0 0 ${wN},0`}
        fill="none"
        stroke={K2}
        strokeWidth={1.6}
      />
    </g>
  );

  const fallers = (falling ?? []).map((i) => {
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
  });

  if (!tipped) {
    return (
      <g>
        {glass(upright)}
        {fallers}
      </g>
    );
  }
  const T = J.tip;
  const pose = (p: number) =>
    about(T.ox, T.oy, { dx: T.dx * p, dy: T.dy * p, rot: T.ang * p, sx: lerp(1, T.sc, p) });
  if (!tipping) return <g transform={pose(1)}>{glass(lying)}</g>;
  return (
    <Tween play delay={0.9} duration={0.8} ease={TIP} transform={pose}>
      {glass(
        <>
          <Tween play delay={1.25} duration={0.25} ease="linear" opacity={(p) => 1 - p}>
            {upright}
          </Tween>
          <Tween play delay={1.3} duration={0.25} ease="linear" opacity={(p) => p}>
            {lying}
          </Tween>
        </>,
      )}
    </Tween>
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

/** The brass lid on its string: a band with two ridges, a low dome, a knob. */
export function JarLid({ v, state, from, delay, arriving = false }: JarLidProps) {
  const J = jarGeometry(v),
    { lh, lw, ly, knob, cx, cy } = J.lid,
    h = J.h;
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
  const brass = CAR.brass;
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
      <rect
        x={cx - lw / 2}
        y={ly}
        width={lw}
        height={lh}
        rx={3}
        fill={brass}
        stroke={K2}
        strokeWidth={2}
      />
      <path
        d={`M${cx - lw / 2 + 3},${ly + lh * 0.38} H${cx + lw / 2 - 3} M${cx - lw / 2 + 3},${ly + lh * 0.7} H${cx + lw / 2 - 3}`}
        stroke="#7a5a2a"
        strokeWidth={1.2}
      />
      <path
        d={`M${cx - lw / 2 + 2},${ly} C${cx - lw * 0.4},${ly - h * 0.1} ${cx + lw * 0.4},${ly - h * 0.1} ${cx + lw / 2 - 2},${ly}Z`}
        fill="#c9a25e"
        stroke={K2}
        strokeWidth={1.8}
        strokeLinejoin="round"
      />
      <path
        d={`M${cx - lw * 0.28},${ly - h * 0.035} Q${cx - lw * 0.1},${ly - h * 0.07} ${cx + lw * 0.05},${ly - h * 0.072}`}
        fill="none"
        stroke="#f1dca6"
        strokeWidth={2.4}
        strokeLinecap="round"
      />
      <rect
        x={cx - 4}
        y={ly - h * 0.1}
        width={8}
        height={h * 0.035}
        fill={brass}
        stroke={K2}
        strokeWidth={1.2}
      />
      <circle
        cx={cx}
        cy={ly - h * 0.105}
        r={7}
        fill={brass}
        stroke={K2}
        strokeWidth={1.6}
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
