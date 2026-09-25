'use client';

/**
 * The carriage clock at the centre of the shelf: the acting seat's two minutes. Drawn in
 * vector after the generated clock (bench 70): an arched brass case with a leather handle,
 * columns and ball feet, a felt dial with a stitched ring and sixty ticks and no numerals,
 * one red hand, a red arc behind it for the time that is left, and a split-flap counter in
 * the base. It is drawn rather than a sprite because the hand and the counter are state.
 *
 * The hand reads as the day's wall clock does on a turn: at a full two minutes it points
 * straight up with the whole ring red; as time runs out it sweeps back round to the top and
 * the ring drains behind it. The clock keeps no time of its own: whoever mounts the room
 * feeds it the real time left on the request (`remainingMs`), so the countdown never waits
 * for the stage. No time (a game with no deadline) shows no ring, no hand, blank flaps.
 */
import { useId } from 'react';
import { K2, brass } from '../paint/draw';
import styles from './NightRoom.module.css';

const RED = '#e3503f';
const BONE = '#efe4cb';

/** How much of the turn is left (0–1), and the hand's angle clockwise from twelve. */
export function clockHand(
  remainingMs: number | null | undefined,
  totalMs: number | null | undefined,
): { f: number; deg: number } | null {
  if (remainingMs == null || totalMs == null || !(totalMs > 0)) return null;
  const f = Math.max(0, Math.min(1, remainingMs / totalMs));
  return { f, deg: 360 * f };
}

/** The counter's reading, `m:ss`, rounded up so it shows 0:00 only when time is up. */
export function flapText(remainingMs: number | null | undefined): string {
  if (remainingMs == null) return '-:--';
  const s = Math.max(0, Math.ceil(remainingMs / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

export interface CarriageClockProps {
  /** Centre x and the shelf's top face it stands on, in units. */
  x: number;
  foot: number;
  /** The case's height in units (bench 70: 0.27 of the stage's height). */
  height: number;
  /** Real time left on the request, and the whole allowance; null = no ring (solo game). */
  remainingMs?: number | null;
  totalMs?: number | null;
}

const f1 = (n: number) => n.toFixed(1);

function Flaps({ x, y, text, h }: { x: number; y: number; text: string; h: number }) {
  const w = h * 0.68,
    gap = h * 0.08,
    x0 = x - ((text.length - 1) * (w + gap)) / 2;
  return (
    <>
      {[...text].map((ch, i) => {
        const cx = x0 + i * (w + gap);
        if (ch === ':')
          return (
            <g key={i}>
              <circle cx={cx} cy={y - h * 0.2} r={h * 0.09} fill={BONE} />
              <circle cx={cx} cy={y + h * 0.2} r={h * 0.09} fill={BONE} />
            </g>
          );
        return (
          <g key={i}>
            <rect
              x={cx - w / 2}
              y={y - h / 2}
              width={w}
              height={h}
              rx={h * 0.08}
              fill="#111"
              stroke={K2}
              strokeWidth={1.4}
            />
            <rect
              x={cx - w / 2}
              y={y - h / 2}
              width={w}
              height={h / 2}
              rx={h * 0.08}
              fill="#1c1c1c"
            />
            <text
              className={styles.flap}
              x={cx}
              y={y + h * 0.33}
              textAnchor="middle"
              fontSize={f1(h * 0.92)}
              fill={BONE}
            >
              {ch}
            </text>
            <path d={`M${cx - w / 2},${y} H${cx + w / 2}`} stroke="#000" strokeWidth={2} />
          </g>
        );
      })}
    </>
  );
}

export function CarriageClock({
  x: cx,
  foot,
  height: chh,
  remainingMs,
  totalMs,
}: CarriageClockProps) {
  const id = 'cc' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const cw = chh * 0.72,
    y1 = foot,
    y0 = y1 - chh,
    r = cw * 0.34,
    dy = y0 + chh * 0.44;
  const hand = clockHand(remainingMs, totalMs);
  const ink = (d: string, fill: string, w: number) => (
    <path
      d={d}
      fill={fill}
      stroke={K2}
      strokeWidth={w}
      strokeLinejoin="round"
      strokeLinecap="round"
    />
  );
  const sr = r * 0.9;

  let arc = null;
  let handLine = null;
  if (hand) {
    const a = -Math.PI / 2 + (2 * Math.PI * hand.deg) / 360,
      ra = r * 0.84;
    if (hand.f >= 0.9995)
      arc = (
        <circle
          cx={cx}
          cy={dy}
          r={ra}
          fill="none"
          stroke={RED}
          strokeWidth={4}
          strokeOpacity={0.9}
        />
      );
    else if (hand.f > 0)
      arc = (
        <path
          d={`M${cx},${dy - ra} A${ra},${ra} 0 ${hand.f > 0.5 ? 1 : 0} 1 ${f1(cx + Math.cos(a) * ra)},${f1(dy + Math.sin(a) * ra)}`}
          fill="none"
          stroke={RED}
          strokeWidth={4}
          strokeOpacity={0.9}
        />
      );
    handLine = (
      <path
        data-hand={hand.deg.toFixed(1)}
        d={`M${cx},${dy} l${f1(Math.cos(a) * r * 0.72)},${f1(Math.sin(a) * r * 0.72)}`}
        stroke={RED}
        strokeWidth={2.6}
        strokeLinecap="round"
      />
    );
  }

  return (
    <svg className={styles.clock} viewBox="0 0 1600 900" aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-case`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#3a2416" />
          <stop offset=".5" stopColor="#5a3a24" />
          <stop offset="1" stopColor="#2e1a10" />
        </linearGradient>
        <radialGradient id={`${id}-dial`} cx="45%" cy="40%" r="65%">
          <stop offset="0" stopColor="#f4ead2" />
          <stop offset="1" stopColor="#e2cfab" />
        </radialGradient>
      </defs>
      {/* ball feet */}
      {[cx - cw * 0.36, cx + cw * 0.36].map((fx) => (
        <circle
          key={fx}
          cx={fx}
          cy={y1}
          r={cw * 0.05}
          fill={brass}
          stroke={K2}
          strokeWidth={1.4}
        />
      ))}
      {/* the case, arched */}
      {ink(
        `M${cx - cw / 2},${y1 - cw * 0.05} v${-(chh - cw * 0.05 - cw * 0.3)} q0,${-cw * 0.3} ${cw * 0.5},${-cw * 0.3} q${cw * 0.5},0 ${cw * 0.5},${cw * 0.3} v${chh - cw * 0.05 - cw * 0.3}Z`,
        `url(#${id}-case)`,
        2.6,
      )}
      {/* the brass band at the base */}
      {ink(
        `M${cx - cw / 2 - 5},${y1 - cw * 0.05} h${cw + 10} v-9 h${-cw - 10}Z`,
        brass,
        1.8,
      )}
      {/* the columns */}
      {[cx - cw / 2 + 5, cx + cw / 2 - 5].map((x) => (
        <g key={x}>
          <path
            d={`M${x},${y0 + cw * 0.34} V${y1 - cw * 0.06}`}
            stroke={brass}
            strokeWidth={3}
          />
          <circle
            cx={x}
            cy={y0 + cw * 0.3}
            r={cw * 0.04}
            fill={brass}
            stroke={K2}
            strokeWidth={1.2}
          />
        </g>
      ))}
      {/* the handle, leather-wrapped */}
      <path
        d={`M${cx - cw * 0.22},${y0 + cw * 0.02} q0,${-cw * 0.22} ${cw * 0.22},${-cw * 0.22} q${cw * 0.22},0 ${cw * 0.22},${cw * 0.22}`}
        fill="none"
        stroke={K2}
        strokeWidth={7}
        strokeLinecap="round"
      />
      <path
        d={`M${cx - cw * 0.22},${y0 + cw * 0.02} q0,${-cw * 0.22} ${cw * 0.22},${-cw * 0.22} q${cw * 0.22},0 ${cw * 0.22},${cw * 0.22}`}
        fill="none"
        stroke={brass}
        strokeWidth={4}
        strokeLinecap="round"
      />
      <rect
        x={cx - cw * 0.12}
        y={y0 - cw * 0.26}
        width={cw * 0.24}
        height={cw * 0.09}
        rx={cw * 0.04}
        fill="#4a2c18"
        stroke={K2}
        strokeWidth={1.4}
      />
      {/* the dial: brass bezel, felt face, a stitched ring, sixty ticks */}
      <circle cx={cx} cy={dy} r={r + 4} fill={brass} stroke={K2} strokeWidth={2} />
      <circle
        cx={cx}
        cy={dy}
        r={r}
        fill={`url(#${id}-dial)`}
        stroke={K2}
        strokeWidth={1.6}
      />
      <path
        d={`M${cx - sr},${dy} a${sr},${sr} 0 1 0 ${2 * sr},0 a${sr},${sr} 0 1 0 ${-2 * sr},0`}
        fill="none"
        stroke="#a67c52"
        strokeWidth={1.1}
        strokeDasharray={`${1.1 * 2.4} ${1.1 * 2.4}`}
        strokeLinecap="round"
        opacity={0.9}
      />
      {Array.from({ length: 60 }, (_, i) => {
        const t = (i / 60) * 2 * Math.PI - Math.PI / 2,
          L = i % 5 ? 0.05 : 0.12;
        return (
          <path
            key={i}
            d={`M${f1(cx + Math.cos(t) * r * 0.8)},${f1(dy + Math.sin(t) * r * 0.8)} L${f1(cx + Math.cos(t) * r * (0.8 - L))},${f1(dy + Math.sin(t) * r * (0.8 - L))}`}
            stroke="#5a3418"
            strokeWidth={i % 5 ? 1.1 : 2.4}
            strokeLinecap="round"
          />
        );
      })}
      {arc}
      {handLine}
      <circle cx={cx} cy={dy} r={3} fill={brass} stroke={K2} strokeWidth={1.2} />
      {/* the split-flap counter in the base */}
      <rect
        x={cx - cw * 0.34}
        y={y1 - chh * 0.2}
        width={cw * 0.68}
        height={chh * 0.13}
        rx={3}
        fill="#1a1512"
        stroke={K2}
        strokeWidth={1.4}
      />
      <g data-counter={flapText(hand ? remainingMs : null)}>
        <Flaps
          x={cx}
          y={y1 - chh * 0.135}
          text={flapText(hand ? remainingMs : null)}
          h={chh * 0.095}
        />
      </g>
    </svg>
  );
}
