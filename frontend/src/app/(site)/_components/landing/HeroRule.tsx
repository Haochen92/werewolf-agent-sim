/**
 * The gold rule between the game's name and its hook (owner's mock, 2026-10-18): a fine line
 * either side, a bead and a ring at its inner end, and the brand's 9 in the middle. Vector, so
 * it stays sharp at any width; the 9 is the nav's own mark.
 */
import Image from 'next/image';
import mark from '@/assets/brand/mark-md.svg';
import classes from './Landing.module.css';

/** One side, drawn for the left; the right is the same mirrored. */
function Side({ flip = false }: { flip?: boolean }) {
  return (
    <svg
      className={classes.ruleSide}
      viewBox="0 0 200 20"
      preserveAspectRatio="xMaxYMid meet"
      style={flip ? { transform: 'scaleX(-1)' } : undefined}
      aria-hidden="true"
    >
      <defs>
        {/* in the line's own units: a flat line has no height to stretch a gradient over */}
        <linearGradient
          id={`rule-${flip ? 'r' : 'l'}`}
          gradientUnits="userSpaceOnUse"
          x1="0"
          x2="156"
        >
          <stop offset="0" stopColor="currentColor" stopOpacity="0" />
          <stop offset=".4" stopColor="currentColor" stopOpacity=".8" />
          <stop offset="1" stopColor="currentColor" />
        </linearGradient>
      </defs>
      <path d="M0 10 H156" stroke={`url(#rule-${flip ? 'r' : 'l'})`} strokeWidth="1.4" />
      <circle cx="162" cy="10" r="2.2" fill="currentColor" />
      <circle cx="176" cy="10" r="5" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="176" cy="10" r="1.6" fill="currentColor" />
      <path d="M183 10 H196" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

export function HeroRule() {
  return (
    <div className={classes.rule} aria-hidden="true">
      <Side />
      <Image src={mark} alt="" width={38} height={38} className={classes.ruleMark} />
      <Side flip />
    </div>
  );
}
