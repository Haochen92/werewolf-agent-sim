'use client';

/**
 * The two stops of a day where you act, working, in the guide: the vote's ballot row and the
 * night room's photo line with its plate, the live game's own instruments (`BallotRow`, `Photo`,
 * `Pin`, `ActPlate`) on a small stage each, cropped to them (owner, 2026-10-14: the pieces you
 * touch, never a whole scene). Nothing is sent: a confirmed ballot or act shows as the game shows
 * it, and the stop can be tried again.
 */
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react';
import { AnimatePresence } from 'motion/react';
import { CHARACTERS } from '@/assets/manifest';
import { Stage } from '@/stage/Stage';
import { stageFonts } from '@/stage/fonts';
import { ActPlate } from '@/stage/instruments/ActPlate';
import { BallotRow } from '@/stage/instruments/BallotRow';
import { MorningRoll } from '@/stage/instruments/MorningRoll';
import { Notice, NoticeZone } from '@/stage/instruments/Notice';
import { EndBox } from '@/stage/scenes/GameOverScene';
import { TransportBand } from '@/stage/containers/TransportBand';
import {
  jumpChapter,
  seekTo,
  stepBack,
  stepForward,
  still,
  transportLabel,
} from '@/stage/containers/transport';
import type { ChapterKind, SceneBeat } from '@/stage/beats/types';
import { SpeechBox } from '@/stage/instruments/SpeechBox';
import { TurnDock } from '@/stage/instruments/TurnDock';
import { vars } from '@/stage/paint/materials';
import type { DockInput, MotionSpeed } from '@/stage/scenes/types';
import { Photo } from '@/stage/instruments/Photo';
import { Pin, pinColour } from '@/stage/instruments/Pin';
import { PHOTO_H } from '@/stage/paint/compartment';
import classes from './Guide.module.css';

const CAST = CHARACTERS.slice(0, 10);
const ME = 'player_4';

/**
 * A small stage cropped to its top-left `w` × `h` units, framed. `fit`: no frame and no margin,
 * the crop as tall as the instrument and rounded as it is, so the instrument's own panel is the
 * frame (the ballot's glass box).
 */
function Crop({
  w,
  h,
  fit = false,
  children,
}: {
  w: number;
  h: number;
  fit?: boolean;
  children: ReactNode;
}) {
  const box = useRef<HTMLDivElement>(null);
  const crop = useRef<HTMLDivElement>(null);
  const [fitted, setFitted] = useState<{ h: number; r: number } | null>(null);
  useLayoutEffect(() => {
    const el = box.current?.firstElementChild as HTMLElement | null;
    const c = crop.current;
    if (!fit || !el || !c) return;
    // its height in units (the stage's scale is a transform: offsetHeight is unscaled), and its
    // corner (the ballot box's 14.4 units) at the crop's scale
    const set = () => setFitted({ h: el.offsetHeight, r: (14.4 * c.clientWidth) / w });
    set();
    const ro = new ResizeObserver(set);
    ro.observe(el);
    ro.observe(c);
    return () => ro.disconnect();
  }, [fit, w]);
  return (
    <div
      className={`${classes.stopDemo} ${fit ? classes.stopDemoFit : ''} ${stageFonts}`}
      style={{ '--sw': w, '--sh': fitted?.h ?? h } as CSSProperties}
    >
      <div
        ref={crop}
        className={classes.stopDemoCrop}
        style={fitted ? { borderRadius: fitted.r } : undefined}
      >
        <div className={classes.stopDemoWorld}>
          <Stage
            paint={<div className={classes.demoGround} />}
            hud={
              <div ref={box} className={classes.stopDemoBox}>
                {children}
              </div>
            }
          />
        </div>
      </div>
    </div>
  );
}

/** The vote: five seats and the empty plate; choose, confirm, and the ballot is in. */
export function VoteDemo() {
  const [chosen, setChosen] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  return (
    <div>
      <Crop w={600} h={250} fit>
        <BallotRow
          candidates={[
            'player_1',
            'player_2',
            'player_5',
            'player_7',
            'player_9',
            'abstain',
          ]}
          cast={CAST}
          chosen={chosen}
          onChoose={sent ? undefined : setChosen}
          onConfirm={() => setSent(true)}
          sent={sent}
          me={ME}
        />
      </Crop>
      {sent ? (
        <button
          type="button"
          className={classes.retry}
          onClick={() => {
            setSent(false);
            setChosen(null);
          }}
        >
          Vote again
        </button>
      ) : null}
    </div>
  );
}

const PHOTO_W = 112;
const NIGHT_SEATS = [1, 2, 3, 5, 6];

/** The healer's night: a line of photographs; tap one, the pin goes in, and the plate names it. */
export function NightDemo() {
  const [chosen, setChosen] = useState<number | null>(null);
  const [sent, setSent] = useState(false);
  const h = PHOTO_W * PHOTO_H;
  const pitch = PHOTO_W + 16;
  return (
    <div>
      <Crop w={700} h={330}>
        <svg className={classes.twine} viewBox="0 0 700 40" aria-hidden="true">
          <path d="M10,8 Q350,40 690,8" />
        </svg>
        {NIGHT_SEATS.map((s, i) => (
          <Photo
            key={s}
            character={CAST[s - 1]}
            seat={s}
            x={30 + PHOTO_W / 2 + pitch * i}
            top={16 + Math.sin((i / (NIGHT_SEATS.length - 1)) * Math.PI) * 14}
            w={PHOTO_W}
            h={h}
            drop={4}
            light={chosen === null ? undefined : chosen === s ? 'lit' : 'dim'}
            onChoose={sent ? undefined : () => setChosen(chosen === s ? null : s)}
          >
            <AnimatePresence initial={false}>
              {chosen === s ? <Pin key="pin" role="healer" w={PHOTO_W * 1.3} /> : null}
            </AnimatePresence>
          </Photo>
        ))}
        <ActPlate
          label={chosen ? `Protect seat ${chosen}` : 'Choose a photo'}
          disabled={!chosen}
          onConfirm={() => setSent(true)}
          note={chosen && !sent ? 'tap another photo to change' : undefined}
          sealed={
            sent && chosen
              ? { label: `Protecting seat ${chosen}`, colour: pinColour('healer') }
              : null
          }
        />
      </Crop>
      {sent ? (
        <button
          type="button"
          className={classes.retry}
          onClick={() => {
            setSent(false);
            setChosen(null);
          }}
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}

/**
 * A stage cropped to wherever an instrument places itself (`selector`), `pad` units round it:
 * the speech box and the notices stand at the foot of the stage, by the stage's own geometry.
 * Measured in units (a rect over the stage's scale), so the crop holds as the page resizes.
 */
export function Focus({
  selector,
  pad = 14,
  hud,
  band,
  also,
  children,
}: {
  selector: string;
  pad?: number;
  hud?: ReactNode;
  /** The replay band's longest, in units (TransportBand.module.css `--band-max`). */
  band?: number;
  /** Parts of the instrument that may stand out of its box, measured with it (a selector). */
  also?: string;
  /** Drawn inside the stage: an instrument that puts itself in a layer (`TransportBand`). */
  children?: ReactNode;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const [at, setAt] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  useLayoutEffect(() => {
    const root = wrap.current;
    if (!root) return;
    const measure = () => {
      const el = root.querySelector<HTMLElement>(selector);
      const box = [...root.querySelectorAll<HTMLElement>('div')].find((d) =>
        d.style.getPropertyValue('--stage-scale'),
      );
      const s = box ? parseFloat(box.style.getPropertyValue('--stage-scale')) : 0;
      if (!el || !box || !(s > 0)) return;
      // the instrument and, with `also`, its parts that stand out of it (a phone's band grows
      // its buttons past the band's top)
      const rs = [el, ...(also ? el.querySelectorAll<HTMLElement>(also) : [])].map((n) =>
        n.getBoundingClientRect(),
      );
      const top = Math.min(...rs.map((q) => q.top)),
        left = Math.min(...rs.map((q) => q.left));
      const r = {
        top,
        left,
        width: Math.max(...rs.map((q) => q.right)) - left,
        height: Math.max(...rs.map((q) => q.bottom)) - top,
      };
      const b = box.getBoundingClientRect();
      const next = {
        x: (r.left - b.left) / s - pad,
        y: (r.top - b.top) / s - pad,
        w: r.width / s + 2 * pad,
        h: r.height / s + 2 * pad,
      };
      setAt((cur) =>
        cur &&
        Math.abs(cur.x - next.x) < 0.5 &&
        Math.abs(cur.y - next.y) < 0.5 &&
        Math.abs(cur.w - next.w) < 0.5 &&
        Math.abs(cur.h - next.h) < 0.5
          ? cur
          : next,
      );
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(root);
    const el = root.querySelector(selector);
    if (el) ro.observe(el);
    return () => ro.disconnect();
  }, [selector, pad, also, children, hud]);
  return (
    <div
      ref={wrap}
      className={`${classes.stopDemo} ${stageFonts}`}
      style={
        {
          '--sw': at?.w ?? 1600,
          '--sh': at?.h ?? 900,
          '--sx': at?.x ?? 0,
          '--sy': at?.y ?? 0,
          '--band-max': band ? `${band}px` : undefined,
          // until it has been measured, the whole stage would show: nothing does
          visibility: at ? undefined : 'hidden',
        } as CSSProperties
      }
    >
      <div className={classes.stopDemoCrop}>
        <div className={`${classes.stopDemoWorld} ${classes.stopDemoShift}`}>
          <Stage paint={<div className={classes.demoGround} />} hud={hud}>
            {children}
          </Stage>
        </div>
      </div>
    </div>
  );
}

const LINES: { seat: number; line: string }[] = [
  { seat: 3, line: 'Seat 7, you voted against the healer’s claim yesterday. Why?' },
  {
    seat: 7,
    line: 'A real healer would have said who they protected. Seat 3, you’re dodging.',
  },
  { seat: 9, line: 'I’ve kept quiet, so here’s my read: seat 7 is pushing far too hard.' },
];

/** The discussion: three lines at the stand; a tap on the board moves on, as in the game. */
export function DiscussionDemo() {
  const [i, setI] = useState(0);
  const { seat, line } = LINES[i];
  return (
    <div>
      <Focus
        selector="[data-speech]"
        pad={28}
        hud={
          <SpeechBox
            hud="live"
            seat={seat}
            character={CAST[seat - 1]}
            line={line}
            onNext={() => setI((n) => (n + 1) % LINES.length)}
          />
        }
      />
      <p className={classes.tapCue}>
        Tap the board for the next line ({i + 1} of {LINES.length})
      </p>
    </div>
  );
}

/** The last word: the moderator's call, then the accused's answer. */
export function LastWordDemo() {
  const [answered, setAnswered] = useState(false);
  return (
    <div>
      <Focus
        selector="[data-speech]"
        pad={28}
        hud={
          <SpeechBox
            hud="live"
            seat={4}
            character={CAST[3]}
            line={
              answered
                ? 'I’m the investigator. I checked seat 7 last night: a wolf. Vote seat 7, not me.'
                : 'Before the vote: seat 4 has been accused by seat 2, seat 3 and seat 7. Seat 4 gets a last word.'
            }
            tag={answered ? undefined : { text: 'the moderator' }}
            onNext={() => setAnswered((a) => !a)}
          />
        }
      />
      <p className={classes.tapCue}>
        {answered
          ? 'Tap the board to hear the call again'
          : 'Tap the board for seat 4’s answer'}
      </p>
    </div>
  );
}

/** The morning: the real roll, two deaths and a save. */
export function MorningDemo() {
  return (
    <Crop w={720} h={300} fit>
      <Notice title="The morning roll" walnut>
        <MorningRoll
          rows={[
            { kind: 'death', player: 'player_6', role: 'sigilist', types: ['wolves'] },
            { kind: 'death', player: 'player_2', role: 'chanteuse', types: ['vigilante'] },
            { kind: 'save', player: 'player_9', types: ['serial_killer'] },
          ]}
          cast={CAST}
          me={ME}
        />
      </Notice>
    </Crop>
  );
}

/** The opening: the composer as the opening round asks for it; Send hands it in. */
export function OpeningDemo() {
  const [text, setText] = useState('');
  const [sent, setSent] = useState(false);
  const dock: DockInput = { text, onText: setText, round: 'opening' };
  return (
    <div className={`${classes.openingDemo} ${stageFonts}`} style={vars()}>
      {sent ? (
        <p className={classes.sentNote}>
          Your opening is in. Once every seat has written, they are read out in seat order.{' '}
          <button
            type="button"
            className={classes.retry}
            onClick={() => {
              setSent(false);
              setText('');
            }}
          >
            Write another
          </button>
        </p>
      ) : (
        <TurnDock
          dock={dock}
          clock={null}
          onSay={() => setSent(true)}
          onPass={() => setSent(true)}
          pinned
        />
      )}
    </div>
  );
}

/** The ending: the result box as a seated player sees it, a vigilante on the losing side. */
export function EndingDemo() {
  return (
    <Focus
      selector="[data-end-box]"
      pad={20}
      hud={
        <NoticeZone hud="live">
          {/* narrower than the band it stands in, so its words read at the column's size */}
          <div data-end-box style={{ width: 620 }}>
            <EndBox
              winner="wolves"
              neutral={null}
              won={false}
              winners={['player_2', 'player_8']}
              me={ME}
              myRole="vigilante"
              myDead={false}
              cast={CAST}
              truth
              way
              arrive={false}
            />
          </div>
        </NoticeZone>
      }
    />
  );
}

const CH: { kind: ChapterKind; n: number; labels: string[] }[] = [
  {
    kind: 'day',
    n: 1,
    labels: ['Everyone is writing their opening', 'Seat 3 speaks', 'Seat 7 speaks'],
  },
  {
    kind: 'night',
    n: 1,
    labels: ['Night falls', 'The wolves choose', 'The healer protects'],
  },
  { kind: 'morning', n: 1, labels: ['The morning roll'] },
  { kind: 'day', n: 2, labels: ['Seat 9 speaks', 'Seat 4 is called'] },
  {
    kind: 'vote',
    n: 2,
    labels: ['Voting opens', 'A chip is counted', 'Seat 7 is voted out'],
  },
  { kind: 'over', n: 0, labels: ['The town has won'] },
];
const BEATS = CH.flatMap((c) =>
  c.labels.map(
    (label, i) =>
      ({
        id: 'day.speech',
        scene: 'day',
        label,
        day: c.n,
        seq: 0,
        end: 0,
        sees: 'public',
        holdMs: 0,
        chapter: i === 0 ? { kind: c.kind, n: c.n } : undefined,
      }) as unknown as SceneBeat,
  ),
);

/** The replay's controls, working: chapters, a beat at a time, play, the seek bar and the speed. */
export function ReplayDemo() {
  const [cursor, setCursor] = useState(still(0));
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<MotionSpeed>('normal');
  useEffect(() => {
    if (!playing) return;
    const t = window.setTimeout(
      () => {
        if (cursor.index >= BEATS.length - 1) setPlaying(false);
        else setCursor((c) => stepForward(c, BEATS));
      },
      speed === 'fast' ? 600 : 1200,
    );
    return () => window.clearTimeout(t);
  }, [playing, cursor, speed]);
  const label = transportLabel(BEATS, cursor.index);
  return (
    <Focus selector="[data-transport]" also="button" pad={10} band={1300}>
      <TransportBand
        hud="replay"
        beats={BEATS}
        index={cursor.index}
        playing={playing}
        speed={speed}
        label={label}
        besideDrawer={false}
        onChapter={(dir) => setCursor((c) => jumpChapter(c, BEATS, dir))}
        onStep={(dir) =>
          setCursor((c) => (dir === 1 ? stepForward(c, BEATS) : stepBack(c)))
        }
        onTogglePlay={() => setPlaying((p) => !p)}
        onSeek={(i) => setCursor(seekTo(i, BEATS))}
        onSpeed={setSpeed}
      />
    </Focus>
  );
}
