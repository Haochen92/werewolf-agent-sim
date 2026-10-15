/**
 * The clock, as an enamel station sign under the day's line: rooms give every turn two minutes,
 * shown by a brass pocket watch with its last two minutes in red (the second hand ticks round).
 */
import classes from './ClockSign.module.css';

/** The hour ticks: long at the quarters. */
const TICKS = Array.from({ length: 12 }, (_, i) => {
  const a = (i * Math.PI) / 6;
  const long = i % 3 === 0;
  const r1 = 30;
  const r2 = long ? 25 : 27.5;
  const at = (r: number) =>
    [50 + r * Math.sin(a), 56 - r * Math.cos(a)].map((v) => +v.toFixed(1));
  const [x1, y1] = at(r1);
  const [x2, y2] = at(r2);
  return { x1, y1, x2, y2, w: long ? 2.4 : 1.2 };
});

function Watch() {
  return (
    <svg className={classes.watch} viewBox="0 0 100 112" aria-hidden="true">
      <defs>
        <radialGradient id="clock-case" cx="38%" cy="30%" r="75%">
          <stop offset="0" stopColor="#fff3c8" />
          <stop offset=".35" stopColor="#e6c47a" />
          <stop offset=".7" stopColor="#b8893a" />
          <stop offset="1" stopColor="#6b4a1c" />
        </radialGradient>
        <radialGradient id="clock-face" cx="45%" cy="40%" r="70%">
          <stop offset="0" stopColor="#fbf3df" />
          <stop offset="1" stopColor="#e3d3ae" />
        </radialGradient>
      </defs>
      {/* the bow, the stem and the case */}
      <path d="M44 6h12v6H44z" fill="url(#clock-case)" stroke="#4a3210" strokeWidth="1" />
      <circle cx="50" cy="5" r="4.5" fill="none" stroke="#c9a04e" strokeWidth="2.4" />
      <rect
        x="41"
        y="10"
        width="18"
        height="7"
        rx="2"
        fill="url(#clock-case)"
        stroke="#4a3210"
        strokeWidth="1"
      />
      <circle
        cx="50"
        cy="56"
        r="41"
        fill="url(#clock-case)"
        stroke="#4a3210"
        strokeWidth="1.4"
      />
      <circle
        cx="50"
        cy="56"
        r="35"
        fill="url(#clock-face)"
        stroke="#7d5f2e"
        strokeWidth="1.6"
      />
      {/* the last two minutes, in red */}
      <path d="M50 56 L24.0 41.0 A30 30 0 0 1 50.0 26.0 Z" fill="#c8392b" opacity=".22" />
      <path
        d="M22.7 40.2 A31.5 31.5 0 0 1 50.0 24.5"
        fill="none"
        stroke="#c8392b"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <g stroke="#2a1a08" strokeLinecap="round">
        {TICKS.map((t, i) => (
          <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} strokeWidth={t.w} />
        ))}
      </g>
      <text x="50" y="35" textAnchor="middle" className={classes.twelve}>
        XII
      </text>
      <line
        x1="50"
        y1="56"
        x2="50"
        y2="33"
        stroke="#2a1a08"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <line
        x1="50"
        y1="56"
        x2="40.5"
        y2="39.5"
        stroke="#2a1a08"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <line
        className={classes.second}
        x1="50"
        y1="62"
        x2="50"
        y2="30"
        stroke="#c8392b"
        strokeWidth="1.1"
        strokeLinecap="round"
      />
      <circle cx="50" cy="56" r="2.6" fill="#c8392b" stroke="#2a1a08" strokeWidth=".8" />
    </svg>
  );
}

export function ClockSign() {
  return (
    <aside className={classes.sign} role="note">
      <Watch />
      <div>
        <h3>Rooms run on a clock</h3>
        <p>
          With other people at the table, every turn has <b>two minutes</b>. If yours runs
          out, <b>your agent speaks or votes for you</b>.
        </p>
        <p className={classes.solo}>Solo games have no clock: take as long as you like.</p>
      </div>
    </aside>
  );
}
