'use client';

/**
 * The stage floor in front of the back wall: the apron (the boards running on to the frame's
 * edge below the rail) and the trap, the two-leaf door in it that the vote's table rises
 * through and the voted-out puppet drops through. By day both sit under the stand, the trap
 * shut; they are drawn anyway so that the stand can go and the floor is already there.
 *
 * Played (`animate`), the trap opens (the leaves fold down flat into the floor's edge, then
 * stand up either side of the hole) or shuts (the standing leaves fold down, then the flat
 * ones lay back over the hole), at the vote bench's timings (rev 64 `.leaf-*`). The numbers
 * are the deal bench's (rev 75, `VG`, `apronSVG`, `trapSVG`).
 */
import { useId, type ReactNode } from 'react';
import { Tween, about } from './Tween';
import { BOARD, BOARD2, K2 } from '../paint/materials';
import { carLines } from '../paint/window';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';

/** The trap's geometry, in units: a tenth wider than the vote's table, centred on the stand. */
export function trapGeometry(g: StageGeometry) {
  const H = STAGE_H,
    { floorY, floorH, B } = carLines(g);
  const tw = Math.min((g.side ? 0.76 : 0.6) * g.room, 2.1 * g.pwid);
  const trapW = tw * 1.1,
    footY = B + 0.012 * H;
  const holeTop = floorY + floorH * 0.25,
    holeBot = footY + 0.045 * H;
  return {
    x0: g.cx - trapW / 2,
    x1: g.cx + trapW / 2,
    cx: g.cx,
    trapW,
    holeTop,
    holeBot,
    leafH: trapW * 0.085,
    leafT: trapW * 0.028,
  };
}

const svgProps = {
  viewBox: `0 0 ${STAGE_W} ${STAGE_H}`,
  xmlns: 'http://www.w3.org/2000/svg',
  style: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    overflow: 'visible',
  },
} as const;

/** The boards from the rail to the frame's foot, faded into the dark at both ends. */
export function Apron({ g }: { g: StageGeometry }) {
  const fade = 'ap' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const B = g.railY,
    H = STAGE_H,
    W = STAGE_W;
  const seams: number[] = [];
  for (let y = B + 0.045 * H; y < H; y += 0.05 * H) seams.push(y);
  const rect = { x: 0, y: B - 2, width: W, height: H - B + 2 };
  return (
    <svg {...svgProps} aria-hidden="true">
      <defs>
        <linearGradient id={fade} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#0c0a07" stopOpacity=".95" />
          <stop offset=".12" stopColor="#0c0a07" stopOpacity="0" />
          <stop offset=".88" stopColor="#0c0a07" stopOpacity="0" />
          <stop offset="1" stopColor="#0c0a07" stopOpacity=".95" />
        </linearGradient>
      </defs>
      <rect {...rect} fill={BOARD} />
      {seams.map((y) => (
        <path
          key={y}
          d={`M0,${y.toFixed(0)} H${W}`}
          stroke={BOARD2}
          strokeWidth={1.6}
          opacity={0.7}
        />
      ))}
      <rect {...rect} fill={`url(#${fade})`} />
      <rect {...rect} fill="#0c0a07" opacity={0.18} />
    </svg>
  );
}

export type TrapState = 'closed' | 'open';

/**
 * The trap: shut (two leaves flat in the floor) or open (the leaves standing either side of
 * the hole). `animate` plays the move into `state` from the other one.
 */
export function Trap({
  g,
  state,
  animate = false,
}: {
  g: StageGeometry;
  state: TrapState;
  animate?: boolean;
}) {
  const t = trapGeometry(g),
    h = t.holeBot - t.holeTop;
  const ink = { stroke: K2, strokeLinejoin: 'round', strokeLinecap: 'round' } as const;
  // a flat leaf folds about the trap's outer edge; a standing leaf rises from the hole's foot
  const flatMove = (x: number, node: ReactNode) =>
    !animate ? (
      node
    ) : (
      <Tween
        key={x}
        play
        {...(state === 'open'
          ? { delay: 0.3, duration: 0.5, ease: 'easeIn' as const }
          : { delay: 2.4, duration: 0.5, ease: 'easeOut' as const })}
        transform={(p) =>
          about(x < t.cx ? t.x0 : t.x1, t.holeTop, {
            sx: state === 'open' ? 1 - 0.92 * p : 0.08 + 0.92 * p,
            sy: 1,
          })
        }
      >
        {node}
      </Tween>
    );
  const standMove = (x: number, node: ReactNode) =>
    !animate ? (
      node
    ) : (
      <Tween
        key={x}
        play
        {...(state === 'open'
          ? {
              delay: 0.7,
              duration: 0.45,
              ease: [0.3, 0.8, 0.4, 1] as [number, number, number, number],
            }
          : { delay: 2.0, duration: 0.45, ease: 'easeIn' as const })}
        transform={(p) => {
          const q = state === 'open' ? p : 1 - p;
          return about(0, t.holeBot, { sx: 1, sy: 0.06 + 0.94 * q });
        }}
        opacity={(p) => 0.4 + 0.6 * (state === 'open' ? p : 1 - p)}
      >
        {node}
      </Tween>
    );
  const flat = [t.x0, t.cx].map((x) => {
    const w = t.trapW / 2;
    return flatMove(
      x,
      <g key={x}>
        <path
          d={`M${x},${t.holeTop} h${w} v${h} h${-w}Z`}
          fill={BOARD}
          strokeWidth={2}
          {...ink}
        />
        <path
          d={`M${x + 6},${t.holeTop + h * 0.5} H${x + w - 6}`}
          stroke={BOARD2}
          strokeWidth={1.4}
          opacity={0.7}
        />
        <path
          d={`M${x + 8},${t.holeTop + 7} H${x + w - 8}`}
          stroke="#2a1a0c"
          strokeWidth={2}
        />
      </g>,
    );
  });
  if (state === 'closed' && !animate) {
    return (
      <svg {...svgProps} aria-hidden="true">
        {flat}
      </svg>
    );
  }
  return (
    <svg {...svgProps} aria-hidden="true">
      <rect x={t.x0} y={t.holeTop} width={t.trapW} height={h} fill="#050403" />
      <rect
        x={t.x0}
        y={t.holeTop}
        width={t.trapW}
        height={h * 0.35}
        fill="#000"
        opacity={0.5}
      />
      <rect
        x={t.x0}
        y={t.holeTop}
        width={t.trapW}
        height={h}
        fill="none"
        stroke="#2a1a0c"
        strokeWidth={2.4}
      />
      {animate ? flat : null}
      {[t.x0 - t.leafT, t.x1].map((x) =>
        standMove(
          x,
          <g key={x}>
            <path
              d={`M${x},${t.holeTop - t.leafH} h${t.leafT} v${h + t.leafH} h${-t.leafT}Z`}
              fill="#3e2a16"
              strokeWidth={2}
              {...ink}
            />
            <path
              d={`M${x + t.leafT / 2},${t.holeTop - t.leafH + 6} V${t.holeBot - 6}`}
              stroke="#2a1a0c"
              strokeWidth={1.4}
              opacity={0.8}
            />
            <path
              d={`M${x - 3},${t.holeBot - 4} h${t.leafT + 6} v8 h${-t.leafT - 6}Z`}
              fill="#2a1a0c"
              strokeWidth={1.2}
              {...ink}
            />
          </g>,
        ),
      )}
    </svg>
  );
}
