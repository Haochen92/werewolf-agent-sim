'use client';

/**
 * The trap in the stage floor: the two-leaf door the vote's table rises through and the
 * voted-out puppet drops through. The floor itself is the car's painting (CarBackdrop), so a
 * shut trap at rest draws nothing: the painted floor is its leaves.
 *
 * Played (`animate`), the trap opens (the leaves fold down flat into the floor's edge, then
 * stand up either side of the hole) or shuts (the standing leaves fold down, then the flat
 * ones lay back over the hole), at the vote bench's timings (rev 64 `.leaf-*`). The numbers
 * are the deal bench's (rev 75, `VG`, `trapSVG`). The flat leaves are cut from the painting
 * itself at the car's hour, so they are the floor they fold out of and lie back into.
 */
import { useId, type ReactNode } from 'react';
import { SPRITES } from '@/assets/manifest';
import { Tween, about } from './Tween';
import { CAR_TINT } from './CarBackdrop';
import { diningCarPlan } from '../paint/dining-car';
import { K2, type Phase } from '../paint/materials';
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

export type TrapState = 'closed' | 'open';

/**
 * The trap: shut (two leaves flat in the floor) or open (the leaves standing either side of
 * the hole). `animate` plays the move into `state` from the other one.
 */
export function Trap({
  g,
  state,
  animate = false,
  phase = 'dusk',
}: {
  g: StageGeometry;
  state: TrapState;
  animate?: boolean;
  /** The car's hour, whose painted floor the flat leaves are cut from. */
  phase?: Phase;
}) {
  const t = trapGeometry(g),
    h = t.holeBot - t.holeTop;
  // the leaves' face: the car's painted floor where they lie, at the car's hour
  const tex = 'tr' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const at = diningCarPlan({ phase, hud: g.hud, side: g.side }).picture,
    tint = CAR_TINT[phase];
  const defs = (
    <defs>
      <pattern
        id={tex}
        patternUnits="userSpaceOnUse"
        x={at.x}
        y={at.y}
        width={STAGE_W}
        height={STAGE_H}
      >
        <image
          href={SPRITES.car[phase === 'night' ? 'night' : 'day'].src}
          width={STAGE_W}
          height={STAGE_H}
        />
        {tint ? <rect width={STAGE_W} height={STAGE_H} fill={tint} /> : null}
      </pattern>
    </defs>
  );
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
      <path
        key={x}
        d={`M${x},${t.holeTop} h${w} v${h} h${-w}Z`}
        fill={`url(#${tex})`}
        strokeWidth={1.6}
        {...ink}
      />,
    );
  });
  // shut and still: the painted floor is the trap
  if (state === 'closed' && !animate) return null;
  return (
    <svg {...svgProps} aria-hidden="true">
      {defs}
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
