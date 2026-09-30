'use client';

/**
 * The verdict: a walnut board the flies lower on two strings at the end of the game, large
 * and centred, in the morning card's grammar. The winning side's colour runs along its top
 * and bottom edges, the side's sigil sits on a paper plate at its left, and the result is
 * printed in the card's old serif ("The wolves have won"), with where the game stopped
 * beneath it ("Day 4 · at the morning"). It is read, then drawn up out of the frame as the
 * next beat begins.
 *
 * Vector, not a sprite: it is a sign, and it carries state (the side, the words). The
 * measures are bench 73's `signSVG`: 1.5 puppet widths wide (at most 0.52 of the stage),
 * 0.17 of the stage tall, centred at 0.36 of the height; down 1.1 s after 0.4 s, up 0.8 s
 * after 0.1 s.
 */
import { CAR, MATERIALS } from '../paint/materials';
import { WINNER_LINE, WINNER_SIGIL, type EndedAt } from '../scenes/game-over';
import type { Faction } from '../roles';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';
import { Sigil } from './Sigil';
import { StringDrop, Twine } from './StringDrop';

const WAL = '#4a2c18',
  WAL_HI = '#6a4a2a',
  INK = MATERIALS.ink;

const EDGE: Record<Faction, string> = {
  villagers: MATERIALS.town,
  wolves: MATERIALS.wolf,
  serial_killer: MATERIALS.sk,
};

/** Where the board hangs, in units. */
export function verdictBoardBox(g: StageGeometry) {
  const w = Math.min(0.52 * STAGE_W, g.pwid * 1.5),
    h = 0.17 * STAGE_H;
  return { x: g.cx - w / 2, y: 0.36 * STAGE_H - h / 2, w, h };
}

export interface VerdictBoardProps {
  g: StageGeometry;
  winner: Faction;
  /** The day the game ended on. */
  day: number;
  endedAt: EndedAt;
  /** Played: lowered from the flies, or drawn back up out of the frame. */
  move?: 'lower' | 'raise' | null;
}

export function VerdictBoard({ g, winner, day, endedAt, move }: VerdictBoardProps) {
  const { x, y, w, h } = verdictBoardBox(g);
  const col = EDGE[winner];
  const band = h * 0.085;
  const pr = h * 0.24,
    px = w * 0.16,
    py = h / 2;
  const tx = w * 0.63;
  return (
    <StringDrop
      x={x + w / 2}
      y={y}
      w={w}
      h={h}
      bare
      move={move}
      delay={move === 'raise' ? 0.1 : 0.4}
      duration={move === 'raise' ? 0.8 : 1.1}
    >
      <div data-verdict={winner} style={{ position: 'absolute', inset: 0 }}>
        {[0.1, 0.9].map((f) => (
          <Twine key={f} x={w * f} y0={-y - 40} y1={-6} />
        ))}
        <svg
          viewBox={`0 0 ${w} ${h}`}
          style={{
            position: 'absolute',
            inset: 0,
            width: w,
            height: h,
            overflow: 'visible',
          }}
          role="img"
          aria-label={`${WINNER_LINE[winner]} · Day ${day} · at the ${endedAt === 'lynch' ? 'vote' : 'morning'}`}
        >
          {[0.1, 0.9].map((f) => (
            <circle
              key={f}
              cx={w * f}
              cy={-6}
              r={5}
              fill="none"
              stroke={CAR.brass}
              strokeWidth={2}
            />
          ))}
          <rect x={6} y={10} width={w} height={h} rx={8} fill="#000" opacity={0.45} />
          <rect
            x={0}
            y={0}
            width={w}
            height={h}
            fill={WAL}
            stroke={INK}
            strokeWidth={3}
            strokeLinejoin="round"
          />
          <rect
            x={4}
            y={4}
            width={w - 8}
            height={h - 8}
            rx={5}
            fill="none"
            stroke={WAL_HI}
            strokeWidth={2}
          />
          {[8, h - 8 - band].map((by) => (
            <g key={by}>
              <rect x={8} y={by} width={w - 16} height={band} fill={col} />
              <path
                d={`M14,${by + band / 2} H${w - 14}`}
                stroke={INK}
                strokeWidth={1.6}
                strokeDasharray="3.84 3.84"
                strokeLinecap="round"
                opacity={0.5}
              />
            </g>
          ))}
          <circle
            cx={px}
            cy={py}
            r={pr}
            fill={MATERIALS.paper}
            stroke={INK}
            strokeWidth={2.2}
          />
          <circle
            cx={px}
            cy={py}
            r={pr * 0.82}
            fill="none"
            stroke="#cbb992"
            strokeWidth={1.6}
          />
          <Sigil
            role={WINNER_SIGIL[winner]}
            x={px - pr * 0.6}
            y={py - pr * 0.6}
            width={pr * 1.2}
            height={pr * 1.2}
            variant="felt"
          />
          <text
            x={tx}
            y={h * 0.5}
            textAnchor="middle"
            fontFamily="var(--font-stage-serif, 'IM Fell English'), Georgia, serif"
            fontSize={h * 0.3}
            fill={MATERIALS.bone}
          >
            {WINNER_LINE[winner]}
          </text>
          <text
            x={tx}
            y={h * 0.7}
            textAnchor="middle"
            fontFamily="var(--font-stage-sans, Outfit), system-ui, sans-serif"
            fontSize={h * 0.11}
            letterSpacing={1.5}
            fill={MATERIALS.bone2}
          >
            {`DAY ${day} · AT THE ${endedAt === 'lynch' ? 'VOTE' : 'MORNING'}`}
          </text>
        </svg>
      </div>
    </StringDrop>
  );
}
