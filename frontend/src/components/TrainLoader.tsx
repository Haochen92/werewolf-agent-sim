/**
 * The house's loading picture (owner, 2026-10-16): the Ninth Express in cream silhouette, its
 * engine's wheels turning and steam blowing back, "The Ninth Express" under the rails, snow
 * falling past. Shown where a wait cannot be helped: a page of the site whose code is still on
 * its way (`(site)/loading.tsx`), the way into a replay (`ReplayCover`), a live departure's
 * platform whose pictures are not in yet, and the landing carriage's window (`FeaturedReplay`).
 *
 * It needs nothing to load: the train is drawn here and the snow is two small pictures inside
 * its stylesheet. It comes up only after 0.3 s, so a quick wait never shows it (`atOnce`: from
 * the first frame), and with `leaving` it fades off whatever it covered. Nothing here runs
 * script.
 *
 * Kept cheap to draw while the page under it loads: each snow layer is one tiled picture
 * sliding on its own layer (`will-change`), so the graphics chip moves it and nothing is
 * painted again; only the train's strip (the wheels, the rod, the steam, the rails) is redrawn.
 */
import classes from './TrainLoader.module.css';

const RAIL = 120;
/** The drawing's width: two cars, the engine and its tender. */
const W = 444;

function Wheel({ cx, cy, r }: { cx: number; cy: number; r: number }) {
  const s = Math.round(r * 8) / 10;
  const d = Math.round(s * 8.66) / 10;
  const e = s / 2;
  return (
    <g className={classes.wheel}>
      <circle className={classes.body} cx={cx} cy={cy} r={r} />
      <path
        className={classes.cut}
        d={`M${cx} ${cy - s}v${2 * s}M${cx - d} ${cy - e}l${2 * d} ${2 * e}M${cx - d} ${cy + e}l${2 * d} ${-2 * e}`}
      />
    </g>
  );
}

function Bogie({ cx }: { cx: number }) {
  return (
    <>
      <rect className={classes.body} x={cx - 12} y={102} width={24} height={5} rx={1.5} />
      <Wheel cx={cx - 6.5} cy={RAIL - 5} r={5} />
      <Wheel cx={cx + 6.5} cy={RAIL - 5} r={5} />
    </>
  );
}

/** One car as the platform's train has it: snow on the roof, trim, portholes, its windows. */
function Car({ x, w, dining = false }: { x: number; w: number; dining?: boolean }) {
  const y = 54;
  const h = 46;
  const panes = 5;
  const gap = 5;
  const pane = Math.round((w - 30 - gap * (panes - 1)) / panes);
  return (
    <g transform={`translate(${x} 0)`}>
      <path
        className={classes.body}
        d={`M0 ${y + 2}V${y - 4}q0-6 6-6h${w - 12}q6 0 6 6V${y + 2}z`}
      />
      <rect
        className={classes.snowcap}
        x={3}
        y={y - 12.5}
        width={w - 6}
        height={3.6}
        rx={1.8}
      />
      <rect className={classes.body} x={0} y={y} width={w} height={h} rx={2} />
      <rect className={classes.dark} x={2} y={y + 29} width={w - 4} height={1.2} />
      <circle className={classes.dark} cx={7} cy={y + 12} r={2.6} />
      <circle className={classes.dark} cx={w - 7} cy={y + 12} r={2.6} />
      {dining
        ? Array.from({ length: panes }, (_, i) => {
            const px = 15 + i * (pane + gap);
            return (
              <g key={i}>
                <rect
                  className={classes.lit}
                  x={px}
                  y={y + 7}
                  width={pane}
                  height={17}
                  rx={1.5}
                />
                {i < panes - 1 ? (
                  <circle
                    className={classes.sconce}
                    cx={px + pane + gap / 2}
                    cy={y + 12}
                    r={1.5}
                  />
                ) : null}
              </g>
            );
          })
        : [0, 1, 2].map((i) => (
            <rect
              key={i}
              className={classes.dark}
              x={Math.round(w * (0.24 + i * 0.26) - 6)}
              y={y + 7}
              width={12}
              height={17}
              rx={2.5}
            />
          ))}
      <rect className={classes.body} x={6} y={y + h} width={w - 12} height={4} />
      <Bogie cx={w * 0.2} />
      <Bogie cx={w * 0.8} />
    </g>
  );
}

/** The gangway's bellows between two cars. */
function Bellows({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} 0)`}>
      <rect className={classes.body} x={0} y={60} width={8} height={36} />
      <path className={classes.cut} strokeWidth={0.8} d="M2.7 62v32M5.3 62v32" />
    </g>
  );
}

/** A 1920s express engine facing right, its tender behind it; the rod goes round with the wheels. */
function Engine({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} 0)`}>
      <rect className={classes.body} x={0} y={64} width={40} height={34} rx={2} />
      <path className={classes.body} d="M2 64q8-9 18-8t18 8z" />
      <path className={classes.snowcap} d="M6 60q7-5 14-4.5t14 4.5q-14-2-28 0z" />
      <rect className={classes.dark} x={2} y={84} width={36} height={1.2} />
      <Wheel cx={11} cy={RAIL - 6} r={6} />
      <Wheel cx={29} cy={RAIL - 6} r={6} />
      <rect className={classes.body} x={40} y={86} width={6} height={4} />
      <rect className={classes.body} x={46} y={48} width={30} height={50} />
      <rect className={classes.body} x={43} y={44} width={36} height={5} rx={2} />
      <rect className={classes.snowcap} x={45} y={41} width={32} height={3.2} rx={1.6} />
      <rect className={classes.lit} x={53} y={55} width={16} height={13} rx={2} />
      <rect className={classes.body} x={76} y={62} width={78} height={30} rx={4} />
      <rect className={classes.dark} x={96} y={62} width={1.6} height={30} />
      <rect className={classes.dark} x={122} y={62} width={1.6} height={30} />
      <path className={classes.body} d="M100 62a9 8 0 0 1 18 0z" />
      <path className={classes.snowcap} d="M102.5 57.5a7 4.5 0 0 1 13 0z" />
      <path className={classes.body} d="M138 62l-1.5-13h11l-1.5 13z" />
      <rect className={classes.body} x={135} y={46} width={14} height={4} rx={1} />
      <rect className={classes.body} x={150} y={60} width={11} height={34} rx={3} />
      <circle className={classes.lit} cx={164} cy={68} r={3} />
      <rect className={classes.body} x={72} y={92} width={92} height={5} />
      <path className={classes.body} d="M158 95l14 16h-14z" />
      <Wheel cx={92} cy={RAIL - 10.5} r={10.5} />
      <Wheel cx={116} cy={RAIL - 10.5} r={10.5} />
      <Wheel cx={140} cy={RAIL - 10.5} r={10.5} />
      <Wheel cx={160} cy={RAIL - 5} r={5} />
      <g className={classes.rodX}>
        <g className={classes.rodY}>
          <rect
            className={classes.body}
            x={90}
            y={107.5}
            width={52}
            height={3.4}
            rx={1.7}
          />
        </g>
      </g>
    </g>
  );
}

/** The rail and its ties, the ties sliding back under the train. */
function Line() {
  let ties = '';
  for (let x = -24; x < W + 48; x += 24) ties += `M${x} ${RAIL + 3}h10v4h-10z`;
  return (
    <>
      <rect className={classes.body} x={-30} y={RAIL} width={W + 60} height={2.5} />
      <g className={classes.ties}>
        <path className={classes.body} d={ties} />
      </g>
    </>
  );
}

const PUFFS = [0, 1, 2, 3, 4];

/**
 * The train alone, running in place on its sliding ties. Also drawn small on the ticket
 * office's start plate while a key is checked (`tone="paper"`: ink on cream); still under
 * reduced motion wherever it is.
 */
export function TrainDrawing({ tone, className }: { tone?: 'paper'; className?: string }) {
  return (
    <svg
      viewBox={`0 4 ${W} 126`}
      aria-hidden="true"
      className={className ? `${classes.drawing} ${className}` : classes.drawing}
      data-tone={tone}
    >
      <Line />
      <g className={classes.bob}>
        <Car x={8} w={110} />
        <Bellows x={118} />
        <Car x={126} w={130} dining />
        <Bellows x={256} />
        <Engine x={264} />
      </g>
      {PUFFS.map((i) => (
        <circle
          key={i}
          className={classes.puff}
          style={{ animationDelay: `${-i * 0.28}s` }}
          cx={406}
          cy={40 + (i % 2) * 3}
          r={6}
        />
      ))}
    </svg>
  );
}

export function TrainLoader({
  leaving = false,
  atOnce = false,
  line = null,
}: {
  /** The wait is over: the picture fades off. */
  leaving?: boolean;
  /** Up from the first frame, not after 0.3 s. */
  atOnce?: boolean;
  /** What the wait is, when it is more than loading. */
  line?: string | null;
}) {
  return (
    <div className={classes.loader} role="status" data-at-once={atOnce || undefined}>
      <div className={classes.veil} data-leaving={leaving || undefined}>
        {line ? null : <span className={classes.sr}>Loading</span>}
        <div className={classes.snow} aria-hidden="true">
          <div className={classes.far} />
        </div>
        <div className={classes.lock}>
          <TrainDrawing />
          <span className={classes.caption} aria-hidden="true">
            The Ninth Express
          </span>
          {line ? <span className={classes.line}>{line}</span> : null}
        </div>
        <div className={classes.snow} aria-hidden="true">
          <div className={classes.near} />
        </div>
      </div>
    </div>
  );
}
