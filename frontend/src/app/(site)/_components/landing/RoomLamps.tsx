/**
 * The two lamps of the landing's rooms (Rooms.module.css): the reading room's banker's lamp on
 * its wall shelf, and the pendant hung over the latest games. Plain SVG, still; their light is
 * the room's own gradient, not part of the drawing. Decoration only, so hidden from readers.
 */
import classes from './Rooms.module.css';

/** A green-shaded banker's lamp standing on a small wall shelf. */
export function BankerLamp() {
  return (
    <svg className={classes.banker} viewBox="0 0 128 132" aria-hidden="true">
      <defs>
        <linearGradient id="bk-brass" x1="0" x2="1">
          <stop offset="0" stopColor="#4e340e" />
          <stop offset=".5" stopColor="#e0b45e" />
          <stop offset="1" stopColor="#4e340e" />
        </linearGradient>
        <linearGradient id="bk-glass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3f8a5a" />
          <stop offset=".55" stopColor="#245a38" />
          <stop offset="1" stopColor="#173a24" />
        </linearGradient>
        <radialGradient id="bk-glow">
          <stop offset="0" stopColor="#fff1cc" />
          <stop offset=".6" stopColor="#ffcc78" stopOpacity=".7" />
          <stop offset="1" stopColor="#ffcc78" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="bk-shelf" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5a3d22" />
          <stop offset="1" stopColor="#2a1a0e" />
        </linearGradient>
      </defs>
      <g transform="translate(18 0)">
        <ellipse cx="46" cy="92" rx="26" ry="4" fill="url(#bk-brass)" />
        <rect x="43" y="40" width="5" height="52" fill="url(#bk-brass)" />
        <path d="M44 44 Q30 40 24 36" stroke="url(#bk-brass)" strokeWidth="3" fill="none" />
        <path d="M48 44 Q62 40 68 36" stroke="url(#bk-brass)" strokeWidth="3" fill="none" />
        <ellipse cx="46" cy="40" rx="34" ry="9" fill="url(#bk-glow)" />
        <path d="M10 36 Q12 14 46 12 Q80 14 82 36 Z" fill="url(#bk-glass)" />
        <path
          d="M16 30 Q22 18 46 16"
          stroke="#9fe0b4"
          strokeOpacity=".45"
          strokeWidth="2"
          fill="none"
        />
        <path d="M10 36 H82" stroke="url(#bk-brass)" strokeWidth="2.5" />
        <line x1="70" y1="38" x2="70" y2="56" stroke="#8a6630" strokeWidth="1" />
        <circle cx="70" cy="58" r="2" fill="#d9a64a" />
      </g>
      {/* the shelf and its two brackets */}
      <rect x="0" y="94" width="128" height="10" rx="2" fill="url(#bk-shelf)" />
      <rect x="0" y="94" width="128" height="1" fill="#ffdcaa" fillOpacity=".25" />
      <path d="M16 104 h7 l-11 26 h-4 Z M112 104 h-7 l11 26 h4 Z" fill="#3a2812" />
    </svg>
  );
}

/** A brass pendant shade on its cord, hung from the top of the room. */
export function Pendant() {
  return (
    <svg className={classes.pendant} viewBox="0 0 60 96" aria-hidden="true">
      <defs>
        <radialGradient id="pd-glow">
          <stop offset="0" stopColor="#fff2cf" />
          <stop offset=".6" stopColor="#ffc56a" />
          <stop offset="1" stopColor="#ffc56a" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="pd-brass" x1="0" x2="1">
          <stop offset="0" stopColor="#4e340e" />
          <stop offset=".5" stopColor="#d9a64a" />
          <stop offset="1" stopColor="#4e340e" />
        </linearGradient>
      </defs>
      <line x1="30" y1="0" x2="30" y2="60" stroke="#3a2a14" strokeWidth="2" />
      <path d="M14 78 Q16 62 30 60 Q44 62 46 78 Z" fill="url(#pd-brass)" />
      <ellipse cx="30" cy="82" rx="18" ry="10" fill="url(#pd-glow)" />
    </svg>
  );
}
