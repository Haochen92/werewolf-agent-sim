'use client';

/**
 * The vote's table: what the lift brings up through the trap. A walnut top (the generated wood
 * tile, laid on in perspective), a white cloth hanging from its front edge with a lace hem,
 * turned walnut legs; on it the glass jar. For the count the jar is tipped over at the back
 * rail and a row of plates stands along the front edge, one per seat that got a vote and an
 * upturned saucer at the right for abstain, each with a place card on the cloth below it (the
 * candidate's head, the seat, the running number). The counted chips stack on the plates face
 * up, in towers of four, so the table can be read at a glance.
 *
 * Props describe the state; `play` names what moves in this beat. Nothing here says who
 * chose what beyond what the count has already put on the table. Drawn after the vote bench
 * (rev 64 `tableSVG`, `plateSVG`, `cardSVG`, `arcChip`).
 */
import type { CSSProperties, ReactNode } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import type { Ballot } from '@/game/types';
import { stitch } from '../paint/draw';
import { K2 } from '../paint/materials';
import { seatNumber } from '../roles';
import { STAGE_H, STAGE_W } from '../units';
import { homography, type Pt } from './homography';
import { Jar, JarLid, type LidState } from './Jar';
import { Tween, about, lerp } from './Tween';
import { ChipBack, ChipFace, FlatChip } from './VoteChip';
import {
  TOWER_STEP,
  jarGeometry,
  placeCardBox,
  plateSpots,
  stackPos,
  type PlateSpot,
  type VoteGeometry,
} from './vote-geometry';

const svgFill: CSSProperties = {
  position: 'absolute',
  inset: 0,
  width: '100%',
  height: '100%',
  overflow: 'visible',
};
const WAL = '#4a2c18';

/** The stage units the wood's true depth is laid out in before the perspective squashes it. */
const WOOD_DEPTH = 320;
const WOOD_TILE = 440;

/** A leg: walnut, turned, from y0 down to y1. */
function Leg({ x, y0, y1, w }: { x: number; y0: number; y1: number; w: number }) {
  const h = y1 - y0;
  return (
    <path
      d={`M${x - w / 2},${y0} h${w} l${-w * 0.12},${h * 0.28} q${w * 0.3},${h * 0.08} 0,${h * 0.16} L${x + w * 0.2},${y1} h${-w * 0.4} L${x - w * 0.38},${y0 + h * 0.44} q${-w * 0.3},${-h * 0.08} 0,${-h * 0.16}Z`}
      fill={WAL}
      stroke={K2}
      strokeWidth={1.8}
      strokeLinejoin="round"
    />
  );
}

/** The walnut top: the tile's planks run along the table, narrowing toward the back. */
function WoodTop({ v }: { v: VoteGeometry }) {
  const { cx, topY, depth, tw, bw } = v;
  // the box's width runs from the back edge to the front, its height from left to right
  const to: [Pt, Pt, Pt, Pt] = [
    [cx - bw / 2, topY - depth],
    [cx - tw / 2, topY],
    [cx + tw / 2, topY],
    [cx + bw / 2, topY - depth],
  ];
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: WOOD_DEPTH,
        height: tw,
        transformOrigin: '0 0',
        transform: homography(WOOD_DEPTH, tw, to),
        backgroundImage: `linear-gradient(90deg, rgba(12,8,4,.45), rgba(12,8,4,0) 70%), url(${SPRITES.wood.src})`,
        backgroundSize: `100% 100%, ${WOOD_TILE}px ${WOOD_TILE}px`,
      }}
    />
  );
}

/** Everything behind the top: the shadow on the lift, the back legs. */
function TableBack({ v }: { v: VoteGeometry }) {
  const { cx, topY, depth, tw, bw, footY, g, slabTop, floorH } = v,
    legW = 0.032 * g.pwid;
  return (
    <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
      <ellipse
        cx={cx}
        cy={footY}
        rx={tw * 0.52}
        ry={floorH * 0.3}
        fill="#000"
        opacity={0.3}
      />
      <Leg x={cx - bw * 0.44} y0={topY - depth} y1={slabTop + 0.02 * STAGE_H} w={legW} />
      <Leg x={cx + bw * 0.44} y0={topY - depth} y1={slabTop + 0.02 * STAGE_H} w={legW} />
    </svg>
  );
}

/** In front of the top: its edge, the cloth and its hem, the front legs. */
function TableFront({ v }: { v: VoteGeometry }) {
  const { cx, topY, depth, tw, bw, drop, footY, g } = v,
    legW = 0.032 * g.pwid;
  const n = Math.max(8, Math.round(tw / (0.075 * g.pwid))),
    sw = tw / n;
  let hem = '';
  for (let i = 0; i < n; i++) hem += ` q${-sw / 2},${0.22 * drop} ${-sw},0`;
  return (
    <>
      <path
        d={`M${cx - tw / 2},${topY} L${cx - bw / 2},${topY - depth} H${cx + bw / 2} L${cx + tw / 2},${topY}Z`}
        fill="none"
        stroke={K2}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <path
        d={`M${cx - tw / 2},${topY} H${cx + tw / 2} V${topY + drop}${hem} Z`}
        fill="#e3d5b4"
        stroke={K2}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <rect
        x={cx - tw / 2}
        y={topY}
        width={tw}
        height={drop * 0.14}
        fill="#000"
        opacity={0.08}
      />
      <g
        dangerouslySetInnerHTML={{
          __html: stitch(
            `M${cx - tw / 2 + 6},${topY + drop * 0.8} H${cx + tw / 2 - 6}`,
            '#b4a07c',
            1.3,
            0.9,
          ),
        }}
      />
      <Leg x={cx - tw * 0.44} y0={topY + drop} y1={footY} w={legW} />
      <Leg x={cx + tw * 0.44} y0={topY + drop} y1={footY} w={legW} />
    </>
  );
}

export interface PlateProps {
  v: VoteGeometry;
  p: PlateSpot;
  /** The voters whose chips are on it, in the order they landed. */
  voters: string[];
  cast: readonly Character[];
  /** The viewer's own seat: its chip keeps the amber rim. */
  me?: string | null;
  /** The winner's plate (or a tied one): lit from above. */
  lit?: boolean;
  /** Played: the top chip lands this beat; the light comes up. */
  landing?: boolean;
  lighting?: boolean;
}

/** A plate on the table's top, or the upturned saucer for abstain, with its chips in towers. */
export function Plate({ v, p, voters, cast, me, lit, landing, lighting }: PlateProps) {
  const face = (seat: string) => ({
    seat: seatNumber(seat),
    character: cast[seatNumber(seat) - 1],
    you: seat === me,
  });
  const glow = lit ? (
    <ellipse
      cx={p.x}
      cy={p.y}
      rx={p.rx * 1.7}
      ry={p.ry * 2.4}
      fill="#ffd9a0"
      opacity={0.42}
    />
  ) : null;
  return (
    <g data-plate={p.c}>
      {glow && lighting ? (
        <Tween play delay={0.2} duration={0.7} ease="easeOut" opacity={(q) => q}>
          {glow}
        </Tween>
      ) : (
        glow
      )}
      <ellipse
        cx={p.x}
        cy={p.y + p.ry * 0.25}
        rx={p.rx}
        ry={p.ry}
        fill="#000"
        opacity={0.22}
      />
      {p.c === 'abstain' ? (
        <>
          <ellipse
            cx={p.x}
            cy={p.y}
            rx={p.rx}
            ry={p.ry}
            fill="#e6dcc4"
            stroke={K2}
            strokeWidth={1.8}
          />
          <path
            d={`M${p.x - p.rx * 0.9},${p.y - p.ry * 0.1} Q${p.x},${p.y - p.ry * 3} ${p.x + p.rx * 0.9},${p.y - p.ry * 0.1}`}
            fill="#f4ecd9"
            stroke={K2}
            strokeWidth={1.8}
          />
          <ellipse
            cx={p.x}
            cy={p.y - p.ry * 1.3}
            rx={p.rx * 0.5}
            ry={p.ry * 0.5}
            fill="#e6dcc4"
            stroke="#c9a25e"
            strokeWidth={1.6}
          />
        </>
      ) : (
        <>
          <ellipse
            cx={p.x}
            cy={p.y}
            rx={p.rx}
            ry={p.ry}
            fill="#f4ecd9"
            stroke={K2}
            strokeWidth={1.8}
          />
          <ellipse
            cx={p.x}
            cy={p.y}
            rx={p.rx * 0.7}
            ry={p.ry * 0.7}
            fill="#ece2cb"
            stroke="#c9a25e"
            strokeWidth={1.6}
          />
        </>
      )}
      {voters.map((voter, i) => {
        const [x, y, rr] = stackPos(v, p, i);
        const chip = (
          <FlatChip key={voter} x={x} y={y} r={rr} face={face(voter)} t={TOWER_STEP} />
        );
        return landing && i === voters.length - 1 ? (
          <Tween
            key={voter}
            play
            delay={0.84}
            duration={0.15}
            ease="easeOut"
            opacity={(q) => q}
          >
            {chip}
          </Tween>
        ) : (
          chip
        );
      })}
    </g>
  );
}

export interface PlaceCardProps {
  v: VoteGeometry;
  p: PlateSpot;
  nCands: number;
  /** The running number. */
  n: number;
  cast: readonly Character[];
  lit?: boolean;
  /** Played: the number ticks up from n − 1; the light comes up. */
  hit?: boolean;
  lighting?: boolean;
}

/** The place card on the cloth under a plate: the candidate's head, "Seat 2", the count. */
export function PlaceCard({ v, p, nCands, n, cast, lit, hit, lighting }: PlaceCardProps) {
  const b = placeCardBox(v, p, nCands),
    { x, y, w: cw, h: ch } = b,
    r = ch * 0.34;
  const cy = y + ch * 0.6,
    hx = x + r * 1.35;
  const ab = p.c === 'abstain';
  const label = ab ? 'Abstain' : `Seat ${seatNumber(p.c)}`;
  const fs = Math.max(9, ch * 0.3),
    nfs = Math.max(13, ch * 0.62);
  const nx = x + cw - 10;
  const fits = hx + r * 1.3 + fs * 0.56 * label.length < nx - nfs * 0.75;
  const num = (k: number) => (
    <text
      x={nx}
      y={cy + nfs * 0.36}
      textAnchor="end"
      fontFamily="var(--font-stage-sans, Outfit), system-ui, sans-serif"
      fontWeight={700}
      fontSize={nfs}
      fill={lit ? '#9a6a12' : K2}
    >
      {k}
    </text>
  );
  const frame = lit ? (
    <path
      d={`M${x + 3},${y + ch * 0.12 + 3} v${ch * 0.88 - 6} h${cw - 6} v${-(ch * 0.88 - 6)}`}
      fill="none"
      stroke="#e0a63a"
      strokeWidth={2.2}
    />
  ) : null;
  const ox = nx - nfs * 0.3;
  return (
    <g data-card={p.c}>
      <path
        d={`M${x + 2},${y + ch + 2} h${cw} v${-ch * 0.3}`}
        fill="none"
        stroke="#000"
        strokeOpacity={0.18}
        strokeWidth={4}
      />
      <path
        d={`M${x},${y + ch * 0.12} l${cw * 0.5},${-ch * 0.12} l${cw * 0.5},${ch * 0.12} v${ch * 0.88} h${-cw}Z`}
        fill={lit ? '#f7edd0' : '#f4ecd9'}
        stroke={K2}
        strokeWidth={1.8}
        strokeLinejoin="round"
      />
      <path
        d={`M${x},${y + ch * 0.12} l${cw * 0.5},${-ch * 0.12} l${cw * 0.5},${ch * 0.12}`}
        fill="#e3d5b4"
        stroke={K2}
        strokeWidth={1.4}
      />
      {frame && lighting ? (
        <Tween play delay={0.2} duration={0.7} ease="easeOut" opacity={(q) => q}>
          {frame}
        </Tween>
      ) : (
        frame
      )}
      <ChipFace
        x={hx}
        y={cy}
        r={r}
        seat={ab ? null : seatNumber(p.c)}
        character={ab ? undefined : cast[seatNumber(p.c) - 1]}
      />
      {fits ? (
        <text
          x={hx + r * 1.3}
          y={cy + fs * 0.36}
          fontFamily="var(--font-stage-sans, Outfit), system-ui, sans-serif"
          fontWeight={500}
          fontSize={fs}
          fill="#4a3320"
        >
          {label}
        </text>
      ) : null}
      {hit ? (
        <>
          <Tween play delay={0.8} duration={0.1} ease="linear" opacity={(q) => 1 - q}>
            {num(n - 1)}
          </Tween>
          <Tween
            play
            delay={0.82}
            duration={0.4}
            ease={[0.3, 1.6, 0.5, 1]}
            transform={(q) => about(ox, cy, { sx: lerp(0.3, 1, q) })}
            opacity={(q) => Math.min(1, q * 3)}
          >
            {num(n)}
          </Tween>
        </>
      ) : (
        num(n)
      )}
    </g>
  );
}

/** A chip leaving the tipped jar's mouth: it arcs over, turns face up on the way, and lands. */
function ArcChip({
  from,
  to,
  r,
  face,
}: {
  from: { x: number; y: number };
  to: { x: number; y: number };
  r: number;
  face: Parameters<typeof ChipFace>[0];
}) {
  const ax = from.x - to.x,
    ay = from.y - to.y,
    lift = 0.14 * STAGE_H;
  const easeIO = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
  const dy = (p: number) =>
    p < 0.45
      ? lerp(ay, ay * 0.3 - lift, easeIO(p / 0.45))
      : lerp(ay * 0.3 - lift, 0, easeIO((p - 0.45) / 0.55));
  const sx = (p: number) => Math.max(0.05, Math.abs(Math.cos(Math.PI * p)));
  return (
    <Tween
      play
      duration={0.85}
      ease="linear"
      transform={(p) =>
        about(to.x, to.y, { dx: ax * (1 - p), dy: dy(p), sx: sx(p), sy: 1 })
      }
      opacity={(p) => (p < 0.976 ? 1 : 0)}
    >
      <Tween play duration={0.85} ease="linear" opacity={(p) => (p < 0.5 ? 1 : 0)}>
        <ChipBack x={to.x} y={to.y} r={r} />
      </Tween>
      <Tween play duration={0.85} ease="linear" opacity={(p) => (p < 0.5 ? 0 : 1)}>
        <ChipFace {...face} x={to.x} y={to.y} r={r} />
      </Tween>
    </Tween>
  );
}

export interface VoteTableProps {
  v: VoteGeometry;
  cast: readonly Character[];
  /** The viewer's seat, for the amber rim on its own chip. */
  me?: string | null;
  /** Chips in the upright jar, backs up. */
  ballotsIn: number;
  /** Which chip in the upright jar is the viewer's own (face up, on their screen only). */
  mine?: number | null;
  lid: LidState;
  /** The jar on its side for the count, the plates and the cards out. */
  tipped: boolean;
  /** How many chips of `order` have landed on their plates. */
  counted: number;
  /** The ballots in the order they are counted. */
  order: readonly Ballot[];
  /** The plates, left to right; `abstain` for the saucer. */
  candidates: readonly string[];
  /** The full tally, which sizes the towers before the chips arrive. */
  counts: Record<string, number>;
  /** The plates lit at the result. */
  winner?: readonly string[] | null;
  /** What moves in this beat. */
  play?: {
    lidFrom?: LidState;
    /** The table has just come up: the lid's string comes down and the lid lifts. */
    arriving?: boolean;
    /** Chips in the jar that drop in now, in the order they fall. */
    falling?: number[];
    tipping?: boolean;
    /** The plates and cards come out onto the table. */
    platesIn?: boolean;
    /** The last counted chip rolls out of the jar onto its plate. */
    landing?: boolean;
    /** The winner's light comes up. */
    lighting?: boolean;
  };
}

export function VoteTable({
  v,
  cast,
  me,
  ballotsIn,
  mine,
  lid,
  tipped,
  counted,
  order,
  candidates,
  counts,
  winner,
  play = {},
}: VoteTableProps) {
  const J = jarGeometry(v);
  const ps = tipped ? plateSpots(v, candidates, counts) : [];
  const onPlate: Record<string, string[]> = {};
  order.slice(0, counted).forEach((b) => (onPlate[b.votee] ??= []).push(b.voter));
  const newest = play.landing && counted > 0 ? order[counted - 1] : null;
  const myFace = me
    ? { seat: seatNumber(me), character: cast[seatNumber(me) - 1], you: true }
    : null;

  const plates: ReactNode[] = ps.map((p, i) => {
    const lit = !!winner?.includes(p.c);
    const got = onPlate[p.c] ?? [];
    const hit = !!newest && newest.votee === p.c;
    const inner = (
      <g key={p.c}>
        <Plate
          v={v}
          p={p}
          voters={got}
          cast={cast}
          me={me}
          lit={lit}
          landing={hit}
          lighting={play.lighting}
        />
        <PlaceCard
          v={v}
          p={p}
          nCands={ps.length}
          n={got.length}
          cast={cast}
          lit={lit}
          hit={hit}
          lighting={play.lighting}
        />
      </g>
    );
    return play.platesIn ? (
      <Tween
        key={p.c}
        play
        delay={1.5 + i * 0.16}
        duration={0.55}
        ease={[0.3, 0.8, 0.4, 1]}
        transform={(q) => `translate(0 ${lerp(-0.05 * STAGE_H, 0, q)})`}
        opacity={(q) => q}
      >
        {inner}
      </Tween>
    ) : (
      inner
    );
  });

  let arc: ReactNode = null;
  if (newest) {
    const p = ps.find((q) => q.c === newest.votee);
    if (p) {
      const [fx, fy, rr] = stackPos(v, p, (onPlate[p.c]?.length ?? 1) - 1);
      arc = (
        <ArcChip
          from={J.mouth}
          to={{ x: fx, y: fy - rr * 0.2 }}
          r={rr}
          face={{
            x: 0,
            y: 0,
            r: rr,
            seat: seatNumber(newest.voter),
            character: cast[seatNumber(newest.voter) - 1],
            you: newest.voter === me,
          }}
        />
      );
    }
  }

  return (
    <div style={{ position: 'absolute', inset: 0 }} data-vote-table="">
      <TableBack v={v} />
      <WoodTop v={v} />
      <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
        <TableFront v={v} />
        <Jar
          v={v}
          n={tipped ? ballotsIn - counted : ballotsIn}
          mine={!tipped && mine != null && myFace ? { index: mine, face: myFace } : null}
          tipped={tipped}
          tipping={play.tipping}
          falling={play.falling}
        />
        {!tipped || play.lidFrom ? (
          <JarLid v={v} state={lid} from={play.lidFrom} arriving={play.arriving} />
        ) : null}
        {plates}
        {arc}
      </svg>
    </div>
  );
}
