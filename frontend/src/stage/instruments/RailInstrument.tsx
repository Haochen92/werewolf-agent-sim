'use client';

/**
 * The actor's instrument, laid on the stand's rail beside it in the X-ray replay's night:
 * the healer's box of plasters, the investigator's lens, the vigilante's popgun (with a red
 * cap for each shot left), the serial killer's sickle. It says what this seat does at night
 * before the mark lands, without a word. The wolves have no instrument of their own; their
 * kit (mask, bone, red hood) stands on the rail instead.
 *
 * Vector for the four (bench 67 `instrument()`, drawn about the centre at size `k`), the kit
 * sprite for the pack. Played, it fades in with the actor.
 */
import Image from 'next/image';
import { motion } from 'motion/react';
import { SPRITES } from '@/assets/manifest';
import { useMotionScale } from '../motion';
import { CAR, K2 } from '../paint/materials';

const ink = (d: string, fill: string, w: number) => (
  <path d={d} fill={fill} stroke={K2} strokeWidth={w} strokeLinejoin="round" />
);

function Drawing({ role, k, bullets }: { role: string; k: number; bullets: number }) {
  switch (role) {
    case 'healer':
      return (
        <>
          {ink(`M${-k},${-k * 0.5} h${2 * k} v${k * 0.9} h${-2 * k}Z`, '#efe4cb', 2)}
          <path d={`M${-k},${-k * 0.5} h${2 * k}`} stroke="#cbb992" strokeWidth={6} />
          <path
            d={`M${-k * 0.22},${-k * 0.05} h${k * 0.44} M0,${-k * 0.27} v${k * 0.44}`}
            stroke="#e3503f"
            strokeWidth={k * 0.14}
          />
          {ink(
            `M${-k * 0.2},${-k * 0.5} v${-k * 0.18} h${k * 0.4} v${k * 0.18}Z`,
            '#cbb992',
            1.4,
          )}
        </>
      );
    case 'investigator':
      return (
        <>
          <circle
            cx={-k * 0.3}
            cy={0}
            r={k * 0.55}
            fill="#d6ecec"
            fillOpacity={0.2}
            stroke={CAR.brass}
            strokeWidth={4}
          />
          <circle
            cx={-k * 0.3}
            cy={0}
            r={k * 0.55 + 4}
            fill="none"
            stroke={K2}
            strokeWidth={1.4}
          />
          <path
            d={`M${k * 0.1},${k * 0.4} l${k * 0.9},${k * 0.6}`}
            stroke={K2}
            strokeWidth={9}
            strokeLinecap="round"
          />
          <path
            d={`M${k * 0.1},${k * 0.4} l${k * 0.9},${k * 0.6}`}
            stroke="#5a3418"
            strokeWidth={6}
            strokeLinecap="round"
          />
        </>
      );
    case 'vigilante':
      return (
        <>
          {ink(
            `M${-k * 1.1},${-k * 0.15} h${k * 1.7} v${k * 0.3} h${-k * 0.9} l${-k * 0.1},${k * 0.55} h${-k * 0.4} l${k * 0.1},${-k * 0.55} h${-k * 0.4}Z`,
            '#3f6b4a',
            2,
          )}
          <circle
            cx={k * 0.75}
            cy={0}
            r={k * 0.12}
            fill="#e3503f"
            stroke={K2}
            strokeWidth={1.2}
          />
          {Array.from({ length: bullets }, (_, i) => (
            <g key={i}>
              {ink(
                `M${k * 1.0 + i * k * 0.3},${-k * 0.1} h${k * 0.16} v${k * 0.35} h${-k * 0.16}Z`,
                '#e3503f',
                1.4,
              )}
            </g>
          ))}
        </>
      );
    case 'serial_killer':
      return (
        <>
          <path
            d={`M${-k * 1.2},${k * 0.7} L${k * 0.5},${-k * 0.5}`}
            stroke={K2}
            strokeWidth={7}
            strokeLinecap="round"
          />
          <path
            d={`M${-k * 1.2},${k * 0.7} L${k * 0.5},${-k * 0.5}`}
            stroke="#5a3418"
            strokeWidth={4.5}
            strokeLinecap="round"
          />
          {ink(
            `M${k * 0.5},${-k * 0.5} c${k * 0.5},${-k * 0.5} ${k * 1.2},${-k * 0.3} ${k * 1.3},${k * 0.05} c${-k * 0.6},${-k * 0.15} ${-k * 1.0},${k * 0.05} ${-k * 1.3},${-k * 0.05}Z`,
            '#cfd3d6',
            1.8,
          )}
        </>
      );
    default:
      return null;
  }
}

export interface RailInstrumentProps {
  /** The acting role (`wolf` for the pack). */
  role: string;
  /** Its centre on the rail, in units, and its size (the bench's 0.14 of a puppet width). */
  x: number;
  y: number;
  k: number;
  /** The vigilante's caps left. */
  bullets?: number;
  /** Fade in after this many seconds (played); false = at rest. */
  arrive?: number | false;
}

export function RailInstrument({
  role,
  x,
  y,
  k,
  bullets = 0,
  arrive = false,
}: RailInstrumentProps) {
  const m = useMotionScale();
  const motionProps = {
    initial: arrive === false ? false : { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 * m, delay: (arrive || 0) * m },
  } as const;
  if (role === 'wolf') {
    const img = SPRITES.kits.wolf;
    const h = k * 2.2,
      w = (h * img.width) / img.height;
    return (
      <motion.div
        data-instrument="wolf"
        style={{
          position: 'absolute',
          left: x - w / 2,
          top: y + k * 0.7 - h,
          width: w,
          height: h,
        }}
        {...motionProps}
      >
        <Image
          decoding="sync"
          src={img}
          alt=""
          unoptimized
          draggable={false}
          style={{
            width: '100%',
            height: '100%',
            filter: 'drop-shadow(0 6px 8px rgba(0,0,0,.5))',
          }}
        />
      </motion.div>
    );
  }
  const half = k * 1.6;
  return (
    <motion.svg
      data-instrument={role}
      viewBox={`${-half} ${-half} ${2 * half} ${2 * half}`}
      style={{
        position: 'absolute',
        left: x - half,
        top: y - half,
        width: 2 * half,
        height: 2 * half,
        overflow: 'visible',
        filter: 'drop-shadow(0 4px 5px rgba(0,0,0,.45))',
      }}
      aria-hidden="true"
      {...motionProps}
    >
      <Drawing role={role} k={k} bullets={bullets} />
    </motion.svg>
  );
}
