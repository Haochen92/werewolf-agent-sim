'use client';

/**
 * The vote's table: what the lift brings up through the trap. A painted table, a baize top, a
 * cream felt cloth hanging from its front edge, a stitched scalloped hem and turned legs (the
 * felt set, 2026-10-17); on it the glass jar. For the count the jar stands at the back of the
 * table, to the right, and a row of plates stands along the front edge, one per seat that got
 * a vote and one more at the right for abstain (an ordinary empty plate, owner 2026-09-30; it
 * was an upturned saucer), each with a place card on the cloth below it (the candidate's head
 * and seat, or "Abstain", and the running number). The counted chips stack on the plates face
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
import { useSmall } from '../set';
import { STAGE_H, STAGE_W } from '../units';
import { Jar, JarFallers, JarLid, JarShadow, type LidState } from './Jar';
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
 * The table picture (SPRITES.props.voteTable, the felt set of 2026-10-17: a green baize top, a
 * cream felt cloth with a stitched scalloped hem) in its file's pixels: its top's back and front
 * lines, the front corners, and the depth of cloth the vector `drop` stands for (to the hem's
 * cusps, so the place cards hang on the plain felt above the scallops).
 */
const TABLE_PX = {
  W: 1412,
  H: 321,
  back: 5.5,
  front: 47.9,
  left: 8.9,
  right: 1402.6,
  drop: 177.9,
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

/** A plate on the table's top (abstain's is the same plate), with its chips in towers. */
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
  // a phone's plate is a few dozen pixels wide: its copy
  const plate = useSmall() ? SPRITES.small.props.plate : SPRITES.props.plate;
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
      {/* the painted plate (2026-09-30), the same for abstain: already squashed to the table's
          perspective (ry = 0.3 rx), so it fills the spot's box exactly */}
      <image
        href={plate.src}
        x={p.x - p.rx}
        y={p.y - p.ry}
        width={p.rx * 2}
        height={p.ry * 2}
        preserveAspectRatio="none"
      />
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

/** The paper's face: the stage's display serif with lining figures (Notice.module.css `.head strong`). */
const SERIF: CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontVariantNumeric: 'lining-nums tabular-nums',
};

/**
 * The place card on the cloth under a plate: the candidate's head, "Seat 2", the count. A
 * printed paper label tacked to the felt (2026-10-17; it was a tent card, which could stand on a
 * table but not hang on a cloth).
 */
export function PlaceCard({ v, p, nCands, n, cast, lit, hit, lighting }: PlaceCardProps) {
  const b = placeCardBox(v, p, nCands),
    { x, y, w: cw, h: ch } = b,
    r = ch * 0.34;
  const cy = y + ch * 0.6,
    hx = x + r * 1.35;
  const ab = p.c === 'abstain';
  const label = ab ? 'Abstain' : `Seat ${seatNumber(p.c)}`;
  // the label's top (where the tent card's fold was), its tacks' size, its paper's gradient
  const y0 = y + ch * 0.12,
    tack = Math.max(2, ch * 0.045),
    paper = `place-card-paper-${p.c}`;
  const fs = Math.max(9, ch * 0.3),
    nfs = Math.max(13, ch * 0.62);
  const nx = x + cw - 10;
  // abstain's card has no head: its word starts where the head would, so it always fits
  const tx = ab ? x + r * 0.5 : hx + r * 1.3;
  const fits = ab || tx + fs * 0.56 * label.length < nx - nfs * 0.75;
  const num = (k: number) => (
    <text
      x={nx}
      y={cy + nfs * 0.36}
      textAnchor="end"
      style={SERIF}
      fontWeight={700}
      fontSize={nfs}
      fill={lit ? '#9a6a12' : K2}
    >
      {k}
    </text>
  );
  const frame = lit ? (
    <path
      d={`M${x + 3},${y0 + 3} v${y + ch - y0 - 6} h${cw - 6} v${-(y + ch - y0 - 6)}Z`}
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
      {/* printed paper (the house's facts are paper, as the vote's result is): the notice's
          cream, lit from the top left, a soft edge, no ink outline */}
      <defs>
        <linearGradient id={paper} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={lit ? '#fbf3dc' : '#f5ebd4'} />
          <stop offset="0.55" stopColor={lit ? '#f4e8c8' : '#efe3c8'} />
          <stop offset="1" stopColor={lit ? '#e9d8ad' : '#e2d2ae'} />
        </linearGradient>
      </defs>
      <rect
        x={x}
        y={y0}
        width={cw}
        height={y + ch - y0}
        rx={2.5}
        fill={`url(#${paper})`}
        stroke="#b79d6c"
        strokeWidth={1.2}
      />
      {/* tacked to the felt at its top corners, brass, as the placards' paper is held */}
      {[x + tack * 1.6, x + cw - tack * 1.6].map((tx0) => (
        <g key={tx0}>
          <circle
            cx={tx0}
            cy={y0 + tack * 1.6}
            r={tack}
            fill="#b8893a"
            stroke="#6b4a1c"
            strokeWidth={0.8}
          />
          <circle
            cx={tx0 - tack * 0.3}
            cy={y0 + tack * 1.3}
            r={tack * 0.35}
            fill="#f1d58e"
          />
        </g>
      ))}
      {frame && lighting ? (
        <Tween play delay={0.2} duration={0.7} ease="easeOut" opacity={(q) => q}>
          {frame}
        </Tween>
      ) : (
        frame
      )}
      {ab ? null : (
        <ChipFace
          x={hx}
          y={cy}
          r={r}
          seat={seatNumber(p.c)}
          character={cast[seatNumber(p.c) - 1]}
        />
      )}
      {fits ? (
        <text
          x={tx}
          y={cy + fs * 0.36}
          style={SERIF}
          fontWeight={600}
          fontSize={fs}
          fill="#2a1d11"
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

/** A chip leaving the jar's mouth: it arcs over, turns face up on the way, and lands. */
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
  /** The count: the jar at the back, the plates and the cards out. */
  counting: boolean;
  /** How many chips of `order` have landed on their plates. */
  counted: number;
  /** The ballots in the order they are counted. */
  order: readonly Ballot[];
  /** The plates, left to right; `abstain` for abstain's plate. */
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
    /** The count begins: the jar fades from the centre to the back. */
    countBegins?: boolean;
    /** The plates and cards come out onto the table. */
    platesIn?: boolean;
    /** The last counted chip is lifted out of the jar onto its plate. */
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
  counting,
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
  const ps = counting ? plateSpots(v, candidates, counts) : [];
  const onPlate: Record<string, string[]> = {};
  order.slice(0, counted).forEach((b) => (onPlate[b.votee] ??= []).push(b.voter));
  const newest = play.landing && counted > 0 ? order[counted - 1] : null;
  const myFace = me
    ? { seat: seatNumber(me), character: cast[seatNumber(me) - 1], you: true }
    : null;
  const own = !counting && mine != null && myFace ? { index: mine, face: myFace } : null;

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
      {/* the jar's shadow under it, the jar as its own box (see `Jar`), then what is drawn
          over the glass: the chips dropping in, the lid, the plates */}
      <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
        <defs>
          <SoftShadow id={shade} />
        </defs>
        <JarShadow v={v} counting={counting} countBegins={play.countBegins} shade={shade} />
      </svg>
      <Jar
        v={v}
        n={counting ? ballotsIn - counted : ballotsIn}
        mine={own}
        counting={counting}
        countBegins={play.countBegins}
        falling={play.falling}
      />
      <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={svgFill} aria-hidden="true">
        <JarFallers v={v} mine={own} falling={play.falling} />
        {!counting || play.lidFrom ? (
          <JarLid v={v} state={lid} from={play.lidFrom} arriving={play.arriving} />
        ) : null}
        {plates}
        {arc}
      </svg>
    </div>
  );
}
