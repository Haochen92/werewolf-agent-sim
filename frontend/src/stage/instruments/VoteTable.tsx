'use client';

/**
 * The vote's table: what the lift brings up through the trap. A painted walnut table with a
 * linen cloth hanging from its front edge, a lace hem and turned legs; on it the glass jar. For the count the jar is tipped over at the back
 * rail and a row of plates stands along the front edge, one per seat that got a vote and an
 * upturned saucer at the right for abstain, each with a place card on the cloth below it (the
 * candidate's head, the seat, the running number). The counted chips stack on the plates face
 * up, in towers of four, so the table can be read at a glance.
 *
 * Props describe the state; `play` names what moves in this beat. Nothing here says who
 * chose what beyond what the count has already put on the table. Drawn after the vote bench
 * (rev 64 `tableSVG`, `plateSVG`, `cardSVG`, `arcChip`).
 */
import { useId, type CSSProperties, type ReactNode } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import type { Ballot } from '@/game/types';
import { K2 } from '../paint/materials';
import { seatNumber } from '../roles';
import { STAGE_H, STAGE_W } from '../units';
import { Jar, JarLid, JarShadow, type LidState } from './Jar';
import { Tween, about, lerp } from './Tween';
import { ChipBack, ChipFace, FlatChip } from './VoteChip';
import {
  TOWER_CAP,
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

/**
 * The table picture (SPRITES.props.voteTable) in its file's pixels: its top's back and front
 * lines, the front corners, and the depth of cloth the vector `drop` stands for.
 */
const TABLE_PX = {
  W: 1536,
  H: 295,
  back: 9,
  front: 88,
  left: 21,
  right: 1518.5,
  drop: 138,
};

/**
 * The painted table in two strips that meet at the top's front line: the top stretched to
 * the vote's own depth, so the plates and the jar stand where they did; the cloth and legs
 * below it scaled to `drop`, so the place cards hang on the cloth.
 */
function TablePicture({ v }: { v: VoteGeometry }) {
  const { cx, topY, depth, tw, drop } = v,
    P = TABLE_PX;
  const s = tw / (P.right - P.left),
    sT = depth / (P.front - P.back),
    sF = drop / P.drop;
  const strip = (top: number, height: number, sy: number, y0: number): CSSProperties => ({
    position: 'absolute',
    left: cx - ((P.left + P.right) / 2) * s,
    top,
    width: P.W * s,
    height,
    backgroundImage: `url(${SPRITES.props.voteTable.src})`,
    backgroundRepeat: 'no-repeat',
    backgroundSize: `${P.W * s}px ${P.H * sy}px`,
    backgroundPosition: `0 ${-y0 * sy}px`,
  });
  return (
    <div aria-hidden="true">
      <div style={strip(topY, (P.H - P.front) * sF, sF, P.front)} />
      {/* a unit past the line, over the cloth's strip, so no seam shows between them */}
      <div style={strip(topY - P.front * sT, P.front * sT + 1, sT, 0)} />
    </div>
  );
}

/**
 * A soft shadow's fill (the rooms' atmosphere): dark at the middle, gone at the rim, so a plain
 * ellipse reads as a shadow without a blur.
 */
export function SoftShadow({ id, a = 0.5 }: { id: string; a?: number }) {
  return (
    <radialGradient id={id}>
      <stop offset="0" stopColor="#0c0704" stopOpacity={a} />
      <stop offset=".55" stopColor="#0c0704" stopOpacity={a * 0.6} />
      <stop offset="1" stopColor="#0c0704" stopOpacity={0} />
    </radialGradient>
  );
}

/** Behind the table: its soft shadow on the lift, to the right with the key light. */
function TableBack({ v, shade }: { v: VoteGeometry; shade: string }) {
  const { cx, tw, footY, floorH } = v;
  return (
    <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
      <defs>
        <SoftShadow id={shade} a={0.62} />
      </defs>
      <ellipse
        cx={cx + tw * 0.035}
        cy={footY + floorH * 0.06}
        rx={tw * 0.58}
        ry={floorH * 0.5}
        fill={`url(#${shade})`}
      />
    </svg>
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
  /** The soft shadow's fill (VoteTable's `SoftShadow`), for the plate's and its towers' shadows. */
  shade: string;
}

/** A plate on the table's top, or the upturned saucer for abstain, with its chips in towers. */
export function Plate({
  v,
  p,
  voters,
  cast,
  me,
  lit,
  landing,
  lighting,
  shade,
}: PlateProps) {
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
        cx={p.x + p.rx * 0.1}
        cy={p.y + p.ry * 0.45}
        rx={p.rx * 1.14}
        ry={p.ry * 1.5}
        fill={`url(#${shade})`}
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
        if (i % TOWER_CAP) return null;
        // each tower's shadow on the plate, longer for a taller tower
        const [x, y, rr] = stackPos(v, p, i),
          levels = Math.min(TOWER_CAP, voters.length - i);
        const s = (
          <ellipse
            key={`s${voter}`}
            cx={x + rr * (0.35 + 0.06 * levels)}
            cy={y + rr * TOWER_STEP + rr * 0.12}
            rx={rr * (1.12 + 0.08 * levels)}
            ry={rr * 0.52}
            fill={`url(#${shade})`}
          />
        );
        return landing && i === voters.length - 1 ? (
          <Tween
            key={`s${voter}`}
            play
            delay={0.84}
            duration={0.15}
            ease="easeOut"
            opacity={(q) => q}
          >
            {s}
          </Tween>
        ) : (
          s
        );
      })}
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
  // the rooms' atmosphere: soft shadows under the table, the jar, the plates and the towers
  const ids = 'vt' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const shade = ids + 's';
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
          shade={shade}
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
      <TableBack v={v} shade={ids + 'b'} />
      <TablePicture v={v} />
      <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
        <defs>
          <SoftShadow id={shade} />
        </defs>
        <JarShadow v={v} tipped={tipped} tipping={play.tipping} shade={shade} />
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
