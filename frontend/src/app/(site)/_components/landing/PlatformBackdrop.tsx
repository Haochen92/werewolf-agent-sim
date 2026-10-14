/**
 * The landing's setting (redesign handoff 2026-10-14 §2): a night platform behind the hero. A
 * glazed-tile wall shown only where light falls on it, two wall lamps just outside the content
 * column, faint iron roof trusses, a vignette. All of it is still: drawn once at load, nothing
 * animates, no filters or blends, and the box is capped to the hero's height rather than the
 * page's (phone_lessons 1–3).
 *
 * It sits under everything in the landing's stacking context (z-index -1) and spans the
 * viewport from the very top, behind the nav's board. Its light follows the lamps through three
 * variables set on the landing (`.scene` in the module): `--lx`/`--rx` for the lamps' x and
 * `--ly` for their glass; the carriage's platform reads the same three.
 */
import classes from './PlatformBackdrop.module.css';

function Lamp({ side }: { side: 'l' | 'r' }) {
  const glow = `lampGlow-${side}`;
  const iron = `lampIron-${side}`;
  return (
    <svg className={`${classes.lamp} ${classes[side]}`} viewBox="0 0 84 150" aria-hidden="true">
      <defs>
        <radialGradient id={glow}>
          <stop offset="0" stopColor="#fff3d2" />
          <stop offset=".55" stopColor="#ffbf5e" />
          <stop offset="1" stopColor="#ffbf5e" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={iron} x1="0" x2="1">
          <stop offset="0" stopColor="#22180b" />
          <stop offset=".5" stopColor="#8a6630" />
          <stop offset="1" stopColor="#22180b" />
        </linearGradient>
      </defs>
      <path d="M4 20 V60" stroke={`url(#${iron})`} strokeWidth="6" strokeLinecap="round" />
      <path d="M4 30 H52 M4 30 Q30 30 30 52" fill="none" stroke={`url(#${iron})`} strokeWidth="3" />
      <circle cx="18" cy="38" r="5" fill="none" stroke="#8a6630" strokeWidth="2" />
      <path d="M52 30 V42" stroke={`url(#${iron})`} strokeWidth="3" />
      <path d="M38 42 h28 l-4 10 h-20 z" fill={`url(#${iron})`} />
      <rect
        x="40"
        y="52"
        width="24"
        height="48"
        rx="2"
        fill="#ffcf7a"
        fillOpacity=".22"
        stroke={`url(#${iron})`}
        strokeWidth="2.5"
      />
      <line x1="52" y1="52" x2="52" y2="100" stroke="#5a4320" strokeWidth="1.2" />
      <ellipse cx="52" cy="76" rx="10" ry="16" fill={`url(#${glow})`} />
      <path d="M38 100 h28 l-5 8 h-18 z" fill={`url(#${iron})`} />
      <path d="M52 108 v14" stroke={`url(#${iron})`} strokeWidth="3" />
    </svg>
  );
}

export function PlatformBackdrop() {
  return (
    <div className={classes.backdrop} aria-hidden="true">
      <div className={classes.tiles} />
      <div className={classes.light} />
      <svg
        className={classes.roof}
        viewBox="0 0 1440 300"
        preserveAspectRatio="xMidYMin slice"
      >
        <g fill="none" stroke="#cbb992" strokeOpacity=".07" strokeWidth="2">
          <path d="M-40 300 Q720 -120 1480 300" />
          <path d="M-40 270 Q720 -150 1480 270" strokeOpacity=".05" />
          <g strokeWidth="1.2">
            <path d="M60 238 L180 158 L300 104 L420 66 L540 42 L660 30 L780 30 L900 42 L1020 66 L1140 104 L1260 158 L1380 238" />
            <path d="M60 238 L120 194 M180 158 L240 131 M300 104 L360 85 M420 66 L480 54 M540 42 L600 36 M660 30 L720 30 M780 30 L840 36 M900 42 L960 54 M1020 66 L1080 85 M1140 104 L1200 131 M1260 158 L1320 194" />
          </g>
        </g>
      </svg>
      <Lamp side="l" />
      <Lamp side="r" />
    </div>
  );
}
