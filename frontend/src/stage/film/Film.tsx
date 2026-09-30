'use client';

/**
 * The case file: the side slot's other occupant, beside the transcript drawer, and the X-ray's
 * own pane (the strip's File tab). It holds *this beat, inside*: what the agents were working
 * from at the moment on stage, which live nobody sees. The material is a manila folder of typed
 * pages (owner, 2026-09-29, the case-file bench; it replaced the blue-black X-ray film).
 *
 * A seat's file: the cover (its face, "Seat 2 ▾", "As of Day 3 · discussion", its role stamped
 * on) and divider tabs, Notes · Reads · Lessons · Findings, as case-file.ts works them out;
 * the open tab is held by whoever mounts the stage, so it stays put as the viewer steps
 * through the turns, and falls back to Notes where a file does not have it. A beat with no seat
 * in focus shows the docket instead, one sheet in the same paper (film-model.ts `docketFor`),
 * titled by what it holds ("The vote", "Day 2's brief"; `docketTitle`), never "the docket".
 *
 * Whose file: the seat the beat brings into focus (a turn's speaker, a night spoke's actor; the
 * pack's spoke flips between its wolves). The name on the cover is also a chooser that opens
 * any seat's file (or the docket) at the playhead; the pick holds until a beat brings a
 * different seat into focus (`shownSeat`).
 *
 * The file stops above the rail: nothing in it repeats the speech, so the box below keeps the
 * whole band. On a phone the cover and the tabs share one row, and the long parts fold behind
 * a toggle. Long text is Literata and upright; only the stamps and the ticks sit crooked.
 */
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react';
import Link from 'next/link';
import { SPRITES, type Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { SceneBeat } from '../beats/types';
import { ChipSprite } from '../cast/ChipSprite';
import { Sigil } from '../instruments/Sigil';
import {
  PHASE_NAME,
  PHASE_ORDER,
  stripVerdict,
  verdictKind,
  type VerdictKind,
} from '../instruments/ledger';
import { PHASE_ICON } from '../instruments/Ledger';
import { VerdictMark } from '../instruments/VerdictMark';
import { ACT_VERB } from '../drawer/drawer-lines';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { ROLE_NAME, factionOf, seatNumber, seatify } from '../roles';
import { sideSlot, type Hud } from '../units';
import {
  FORM,
  ROLE_PLURAL,
  asOf,
  ballotCut,
  fileFocus,
  fileTabs,
  firstSentence,
  marginNote,
  openTab,
  parseSituation,
  seatFile,
  shortForm,
  shownSeat,
  tickOf,
  when,
  type FileChoice,
  type SeatFile,
} from './case-file';
import {
  MARK,
  docketFor,
  docketTitle,
  type DocketModel,
  type FilmNote,
  type Verdict,
} from './film-model';
import styles from './Film.module.css';

// the viewer reads the agents' precedents as Lessons (owner, 2026-09-30): these are its stamps
const VWORD: Record<Verdict, string> = {
  follow: 'Followed',
  override: 'Overrode',
  not_relevant: 'Doesn’t apply',
};
const PIP: Record<Verdict, string> = { follow: 'F', override: 'O', not_relevant: '–' };
const INK_TEX = { '--ink-tex': `url(${SPRITES.textures.ink.src})` } as CSSProperties;

export interface FilmProps {
  view: GameView;
  beat: SceneBeat;
  hud: Hud;
  cast: readonly Character[];
  /** The view a little past the beat: whether memory was on, and the game's lessons at the end. */
  ahead?: GameView | null;
  /** The open tab (`notes`, `reads`, `precedents`, `findings`); one a file lacks opens Notes. */
  tab?: string;
  onTab?: (tab: string) => void;
  /**
   * The viewer's pick from the chooser, held by whoever mounts the stage so it outlives the
   * beat. Without `onSeat` the file keeps its own.
   */
  seat?: FileChoice | null;
  onSeat?: (choice: FileChoice | null) => void;
  /**
   * Live only: the finished game's replay. The closed file (after `game_over`) says at its top
   * that this is how each file ended, and points there for the thinking turn by turn.
   */
  replay?: string;
  /** A tap on a seat on the rail opens its file at this beat: the docket says so. */
  seatTaps?: boolean;
}

export function Film({
  view,
  beat,
  hud,
  cast,
  ahead,
  tab = 'notes',
  onTab,
  seat,
  onSeat,
  replay,
  seatTaps = false,
}: FilmProps) {
  const [ownSeat, setOwnSeat] = useState<FileChoice | null>(null);
  const box = useRef<HTMLElement>(null);
  const wide = useWideSlot(box);
  const choice = onSeat ? (seat ?? null) : ownSeat;
  const choose = onSeat ?? setOwnSeat;
  if (beat.id === 'over.epilogue') return null;
  const focus = fileFocus(view, beat);
  const shown = shownSeat(focus, choice);
  // the beat's own docket (a beat with no seat in focus), titled by what it holds
  const own = focus ? null : docketFor(view, beat);
  const docket = shown ? null : (own ?? docketFor(view, beat));
  if (!shown && !docket) return null;
  const title = docket ? docketTitle(docket) : null;
  const ownTitle = own ? docketTitle(own) : null;
  const r = sideSlot(hud);
  const pick = (s: string | null) => choose({ seat: s, key: focus?.key ?? null });
  const chip = (s: string, cls = styles.face) => {
    const c = cast[seatNumber(s) - 1];
    return <span className={cls}>{c ? <ChipSprite character={c} /> : null}</span>;
  };
  // the pack's spoke holds both wolves: the other one, a tap away
  const other =
    shown && focus && focus.seats.length > 1 && focus.seats.includes(shown)
      ? focus.seats.find((s) => s !== shown)!
      : null;
  const file = shown ? seatFile(view, shown, ahead, ballotCut(view, beat)) : null;
  const nudge =
    replay && view.winner ? (
      <p className={styles.nudge} data-nudge>
        This is how each file ended. To see what each seat was thinking turn by turn,{' '}
        <Link href={replay}>watch the replay →</Link>
      </p>
    ) : null;
  return (
    <aside
      ref={box}
      className={styles.folder}
      style={{ left: r.x, top: r.y, width: r.w, height: r.h, ...INK_TEX }}
      data-film={file ? 'file' : docket!.kind}
      data-file-seat={shown ?? undefined}
      data-wide={wide || undefined}
      aria-label={shown ? `Case file, seat ${seatNumber(shown)}` : `Case file, ${title}`}
    >
      {wide ? (
        <SeatTabs
          seats={view.seats}
          alive={view.alive}
          shown={shown}
          docket={ownTitle}
          cast={cast}
          onPick={pick}
        />
      ) : null}
      <div className={styles.fold}>
        {file ? (
          <SeatFileView
            key={shown!}
            file={file}
            asOf={asOf(beat)}
            chip={chip}
            tab={tab}
            onTab={onTab}
            nudge={nudge}
            chooser={
              <Chooser
                wide={wide}
                label={`Seat ${seatNumber(shown!)}`}
                seats={view.seats}
                shown={shown}
                docket={ownTitle}
                chip={chip}
                onPick={pick}
              />
            }
            flip={
              other ? (
                <button
                  type="button"
                  className={styles.flip}
                  onClick={() => pick(other)}
                  title="The pack's other wolf"
                >
                  ⇄ Seat {seatNumber(other)}
                </button>
              ) : null
            }
          />
        ) : (
          <>
            <div className={styles.head}>
              <div className={styles.cover}>
                <span className={`${styles.face} ${styles.docketFace}`} aria-hidden="true">
                  <DocketGlyph />
                </span>
                <div className={styles.who}>
                  <Chooser
                    wide={wide}
                    label={title!}
                    seats={view.seats}
                    shown={null}
                    docket={title}
                    chip={chip}
                    onPick={pick}
                  />
                  <span className={styles.when}>As of {asOf(beat)}</span>
                </div>
              </div>
            </div>
            <div className={`${styles.sheet} ${styles.docket}`}>
              {nudge}
              {seatTaps ? (
                <p className={styles.tapHint} data-tap-hint>
                  <KeyholeGlyph /> Tap a seat to open its file
                </p>
              ) : null}
              <Docket model={docket!} chip={chip} onSeat={pick} />
            </div>
          </>
        )}
      </div>
    </aside>
  );
}

// ---- the cover's chooser --------------------------------------------------------------

/**
 * The cover's name. Where the slot is wide the chip tabs along the folder's top do the
 * choosing, so it is only a title; on a phone (no width for nine tabs) it is a bordered
 * button, "Seat 5 · change ▾", that opens a small grid of every seat's face (and the docket).
 */
function Chooser({
  wide,
  label,
  seats,
  shown,
  docket,
  chip,
  onPick,
}: {
  wide: boolean;
  label: string;
  seats: readonly string[];
  shown: string | null;
  /** The beat's docket to go back to, by its title ("The vote"); null: none. */
  docket: string | null;
  chip: (seat: string, cls?: string) => ReactNode;
  onPick: (seat: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (!open) return;
    const away = (e: PointerEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('pointerdown', away);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('pointerdown', away);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);
  const go = (s: string | null) => {
    setOpen(false);
    onPick(s);
  };
  if (wide) return <span className={styles.nameText}>{label}</span>;
  return (
    <span ref={box} className={styles.choose}>
      <button
        type="button"
        className={styles.name}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {label}
        <small>· change</small>
        <i aria-hidden="true">▾</i>
      </button>
      {open ? (
        <span className={styles.chooser} role="dialog" aria-label="Open a file">
          {seats.map((s) => (
            <button
              key={s}
              type="button"
              className={styles.pick}
              aria-pressed={s === shown}
              onClick={() => go(s)}
            >
              {chip(s)}
              {seatNumber(s)}
            </button>
          ))}
          {docket ? (
            <button
              type="button"
              className={`${styles.pick} ${styles.pickDocket}`}
              aria-pressed={shown === null}
              onClick={() => go(null)}
            >
              {docket}
            </button>
          ) : null}
        </span>
      ) : null}
    </span>
  );
}

/**
 * Where the slot is wide: every seat's face on a small tab standing up off the folder's top
 * edge, like the tabs in a filing drawer; the open file's tab raised, the dead greyed (still
 * openable), and the docket's own tab first when the beat has one.
 */
function SeatTabs({
  seats,
  alive,
  shown,
  docket,
  cast,
  onPick,
}: {
  seats: readonly string[];
  alive: readonly string[];
  shown: string | null;
  /** The beat's docket, by its title: its tab is the folder glyph, first. */
  docket: string | null;
  cast: readonly Character[];
  onPick: (seat: string | null) => void;
}) {
  return (
    <div className={styles.drawer} role="tablist" aria-label="Seats' files">
      {docket ? (
        <button
          type="button"
          role="tab"
          className={`${styles.stab} ${styles.dtab}`}
          aria-selected={shown === null}
          aria-label={docket}
          title={docket}
          onClick={() => onPick(null)}
        >
          <DocketGlyph />
        </button>
      ) : null}
      {seats.map((s) => {
        const c = cast[seatNumber(s) - 1];
        const dead = !alive.includes(s);
        return (
          <button
            key={s}
            type="button"
            role="tab"
            className={dead ? `${styles.stab} ${styles.dead}` : styles.stab}
            aria-selected={s === shown}
            aria-label={`Seat ${seatNumber(s)}’s file${dead ? ' (out)' : ''}`}
            title={`Seat ${seatNumber(s)}${dead ? ' · out' : ''}`}
            onClick={() => onPick(s)}
          >
            <span className={styles.tface}>{c ? <ChipSprite character={c} /> : null}</span>
            <b>{seatNumber(s)}</b>
          </button>
        );
      })}
    </div>
  );
}

/** The Reveal switch's keyhole: the docket's hint that a seat on the rail opens its file. */
function KeyholeGlyph() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={styles.keyhole}>
      <path d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z" />
    </svg>
  );
}

function DocketGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6}>
      <path d="M3 7h6l2 2h10v10H3z" strokeLinejoin="round" />
      <path d="M7 13h10M7 16h7" strokeLinecap="round" />
    </svg>
  );
}

/** A role stamped on: its name in capitals, in the faction's ink. */
function Stamp({ role, className }: { role: string; className?: string }) {
  const f = factionOf(role);
  return (
    <span
      className={`${styles.stamp} ${f ? styles[`s-${f}`] : ''} ${className ?? ''}`}
      aria-label={`Role: ${ROLE_NAME[role] ?? role}`}
    >
      {ROLE_NAME[role] ?? role}
    </span>
  );
}

// ---- one seat's file ------------------------------------------------------------------

function SeatFileView({
  file,
  asOf: now,
  chip,
  tab,
  onTab,
  chooser,
  flip,
  nudge,
}: {
  file: SeatFile;
  asOf: string;
  chip: (seat: string, cls?: string) => ReactNode;
  tab: string;
  onTab?: (tab: string) => void;
  chooser: ReactNode;
  flip: ReactNode;
  nudge: ReactNode;
}) {
  const tabs = fileTabs(file);
  const open = openTab(tabs, tab);
  const n = seatNumber(file.seat);
  return (
    <>
      <div className={styles.head}>
        <div className={styles.cover}>
          {chip(file.seat)}
          <div className={styles.who}>
            <span className={styles.nameRow}>
              {chooser}
              {flip}
            </span>
            <span className={styles.when}>As of {now}</span>
          </div>
          {file.role ? <Stamp role={file.role} className={styles.coverStamp} /> : null}
        </div>
        <div className={styles.dividers} role="tablist" aria-label="File sections">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              className={styles.tab}
              aria-selected={t.id === open}
              disabled={!t.enabled}
              title={t.enabled ? undefined : 'Nothing here yet'}
              onClick={() => onTab?.(t.id)}
            >
              {t.label}
              {t.count ? <small>{t.count}</small> : null}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.sheet} role="tabpanel" data-sheet={open}>
        {nudge}
        {open === 'notes' ? (
          <Notes key={file.pages.length} file={file} />
        ) : open === 'reads' ? (
          <Reads file={file} chip={chip} />
        ) : open === 'precedents' ? (
          <Precedents
            key={file.consult?.lessons.map((l) => l.situation).join()}
            file={file}
            n={n}
          />
        ) : (
          <Findings file={file} />
        )}
      </div>
    </>
  );
}

/** Notes: a typed page per strategy note, newest first opened, the margin's pencil line. */
function Notes({ file }: { file: SeatFile }) {
  const pages = file.pages;
  const [k, setK] = useState(pages.length - 1);
  if (!pages.length)
    return (
      <>
        <div className={styles.shHead}>
          <span className={styles.title}>Strategy note</span>
        </div>
        <p className={styles.empty}>No note written yet.</p>
      </>
    );
  const cur = pages[Math.min(k, pages.length - 1)];
  const at = pages.indexOf(cur);
  return (
    <>
      <div className={styles.shHead}>
        <span className={styles.title}>Strategy note</span>
        <span className={styles.typed}>
          Page {at + 1} of {pages.length}
        </span>
      </div>
      <p className={styles.typed}>Written {when(cur.day, cur.phase)}</p>
      <p className={styles.body}>{seatify(cur.text)}</p>
      <p className={styles.margin}>{marginNote(pages, at)}</p>
      {pages.length > 1 ? (
        <div className={styles.pager}>
          <button
            type="button"
            className={styles.pbtn}
            disabled={at === 0}
            onClick={() => setK(at - 1)}
          >
            ← p. {Math.max(at, 1)}
          </button>
          <span className={styles.dots}>
            {pages.map((p, i) => (
              <button
                key={p.seq}
                type="button"
                aria-label={`Page ${i + 1}`}
                aria-current={i === at ? 'page' : undefined}
                onClick={() => setK(i)}
              >
                <i />
              </button>
            ))}
          </span>
          <button
            type="button"
            className={styles.pbtn}
            disabled={at === pages.length - 1}
            onClick={() => setK(at + 1)}
          >
            p. {Math.min(at + 2, pages.length)} →
          </button>
        </div>
      ) : null}
    </>
  );
}

/** Reads: the seat's latest suspicions, one row per seat read, against the truth. */
function Reads({
  file,
  chip,
}: {
  file: SeatFile;
  chip: (seat: string, cls?: string) => ReactNode;
}) {
  const reads = file.reads!;
  return (
    <>
      <div className={styles.shHead}>
        <span className={styles.title}>Reads</span>
        <span className={styles.typed}>Read {when(reads.day, reads.phase)}</span>
      </div>
      <div className={styles.rows}>
        {reads.rows.map((r) => (
          <div key={r.seat} className={styles.read}>
            {chip(r.seat, `${styles.face} ${styles.sm}`)}
            <span className={styles.guess}>
              <small>Seat {seatNumber(r.seat)}</small>
              <b>
                {r.suspected === 'unclear'
                  ? 'unclear'
                  : (ROLE_NAME[r.suspected] ?? r.suspected).toLowerCase()}
              </b>
              <small>{r.sure ? 'sure' : 'not sure'}</small>
            </span>
            {r.mark ? (
              <span
                className={`${styles.mk} ${styles[`m-${r.mark}`]}`}
                title={r.truth ? `truly ${ROLE_ARTICLE[r.truth] ?? r.truth}` : undefined}
              >
                {MARK[r.mark]}
              </span>
            ) : (
              <span />
            )}
            <p className={styles.why}>{seatify(r.why)}</p>
          </div>
        ))}
      </div>
      <p className={styles.legend}>● had the role · ◐ had the side · ○ unclear or wrong</p>
    </>
  );
}

/**
 * Precedents, as the viewer reads them: Lessons, advice from past games (owner, 2026-09-30).
 * The lessons the seat last weighed, the chosen one opened.
 */
function Precedents({ file, n }: { file: SeatFile; n: number }) {
  const consult = file.consult!;
  const [i, setI] = useState(0);
  const l = consult.lessons[Math.min(i, consult.lessons.length - 1)];
  return (
    <>
      <div className={styles.shHead}>
        <span className={styles.title}>
          Lessons <small className={styles.sub}>advice from past games</small>
        </span>
        <span className={styles.typed}>Consulted {when(consult.day, consult.phase)}</span>
      </div>
      <div className={styles.pidx} role="tablist" aria-label="Lessons">
        {consult.lessons.map((x, k) => (
          <button
            key={x.n}
            type="button"
            role="tab"
            aria-selected={x === l}
            onClick={() => setI(k)}
          >
            <i className={x.verdict ? styles[`bg-${x.verdict}`] : undefined} />
            No. {x.n} · {x.verdict ? VWORD[x.verdict] : 'No verdict'}
          </button>
        ))}
      </div>
      <div className={styles.reason}>
        <Clip />
        {l.verdict ? (
          <span className={`${styles.stamp} ${styles.vstamp} ${styles[`v-${l.verdict}`]}`}>
            {VWORD[l.verdict]}
          </span>
        ) : null}
        <p className={styles.cap}>Seat {n}’s reasoning</p>
        <p className={styles.said}>{l.why ? cap(seatify(l.why)) : 'No reason given.'}</p>
      </div>
      <div className={`${styles.prec} ${l.verdict === 'not_relevant' ? styles.dim : ''}`}>
        <p className={styles.cap}>The lesson, from a past game</p>
        <p>{seatify(l.action)}</p>
      </div>
      <Situation key={l.n} text={l.situation} label="Written for" />
    </>
  );
}

/**
 * A situation as the file sets it: its lead under `label`, the "Situation on file" form (a box
 * ticked only by the owner's rule, else the value in pencil), then the other facets one
 * sentence each, "Show the full wording". The form folds by default on a phone, or wherever
 * `folded` asks (a finding, one of many).
 */
function Situation({
  text,
  label,
  folded = false,
}: {
  text: string;
  label: string;
  folded?: boolean;
}) {
  const [full, setFull] = useState(false);
  const [form, setForm] = useState<boolean | null>(null);
  const small = useSmall();
  const sit = parseSituation(seatify(text));
  const rows = FORM.flatMap((row) => {
    const f = sit.facets.find((x) => x.key === row.key);
    if (!f) return [];
    const tick = tickOf(row.key, f.value);
    // the full wording, when it says more than the ticked word or the pencilled short form
    const said = tick ? row.boxes.find(([, b]) => b === tick)![0] : shortForm(f.value);
    const more = bare(f.value) !== bare(said);
    return [{ ...row, value: f.value, tick, more }];
  });
  const rest = sit.facets.filter((f) => !FORM.some((r) => r.key === f.key));
  const formOpen = form ?? !(small.small || folded);
  return (
    <div ref={small.ref}>
      {sit.lead ? (
        <>
          <p className={styles.cap}>{label}</p>
          <p className={styles.for}>{sit.lead}</p>
        </>
      ) : null}
      {rows.length ? (
        <div className={styles.form}>
          <button
            type="button"
            className={styles.formT}
            aria-expanded={formOpen}
            onClick={() => setForm(!formOpen)}
          >
            <span>Situation on file</span>
            <i aria-hidden="true">{formOpen ? '▾' : '▸'}</i>
          </button>
          {formOpen
            ? rows.map((row) => (
                <div key={row.key} className={styles.frow}>
                  <span className={styles.fl}>{row.name}</span>
                  <span className={styles.boxes}>
                    {row.boxes.map(([, box]) => (
                      <span
                        key={box}
                        className={`${styles.bx} ${row.tick === box ? styles.on : ''}`}
                      >
                        <span className={styles.b}>
                          {row.tick === box ? <Tick /> : null}
                        </span>
                        {box}
                      </span>
                    ))}
                    {row.tick ? null : (
                      <span className={styles.pword}>{shortForm(row.value)}</span>
                    )}
                  </span>
                  {full && row.more ? (
                    <span className={styles.fullv}>{row.value}</span>
                  ) : null}
                </div>
              ))
            : null}
        </div>
      ) : null}
      {rest.length ? (
        <dl className={styles.fields}>
          {rest.map((f, k) => (
            <div key={k}>
              <dt>{f.name}</dt>
              <dd>{full ? f.value : firstSentence(f.value)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {sit.facets.length ? (
        <button type="button" className={styles.more} onClick={() => setFull((x) => !x)}>
          {full ? 'Show less' : 'Show the full wording'}
        </button>
      ) : null}
    </div>
  );
}

/** How a finding turned out, as `net_verdict` says it: a word for the stamp, a calm ink. */
const NET: Record<VerdictKind, string> = {
  worked: 'Positive',
  cost: 'Negative',
  mixed: 'Mixed',
  unclear: 'Unclear',
};

const PHASE_SHORT: Record<string, string> = {
  day_discussion: 'Discussion',
  day_vote: 'Vote',
  night_action: 'Night',
};

/**
 * Findings: what the finished game taught this seat's role, from every seat that held it (the
 * wire files them by role). The index groups its numbers under the phase they came from, with
 * the ledger's phase icons (one row that wraps; a third row of tabs would not fit a phone), each
 * number with its verdict's mark (✓ ✗ ± ?, never colour alone); the chosen one opens below: its
 * situation, what was done, how it went, the verdict stamped on. Then any lessons kept.
 */
function Findings({ file }: { file: SeatFile }) {
  const f = file.findings!;
  const [i, setI] = useState(0);
  const plural = ROLE_PLURAL[f.role] ?? f.role;
  const one = (ROLE_NAME[f.role] ?? f.role).toLowerCase();
  // numbered in the game's order of phases, so the groups read 1 2 3 · 4 5 · 6 7 8 9
  const obs = PHASE_ORDER.flatMap((ph) =>
    f.observations.filter((o) => o.action_phase === ph),
  );
  const items = [
    ...obs.map((o) => ({ kind: 'obs' as const, o, phase: o.action_phase })),
    ...f.lessons.map((l) => ({ kind: 'lesson' as const, l, phase: l.action_phase })),
  ];
  const k = Math.min(i, items.length - 1);
  const cur = items[k];
  const label = (n: number) =>
    n < obs.length ? `No. ${n + 1}` : `Lesson ${n + 1 - obs.length}`;
  const groups = [
    ...PHASE_ORDER.map((ph) => ({
      key: ph as string,
      head: (
        <>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            {PHASE_ICON[ph]}
          </svg>
          {PHASE_SHORT[ph]}
        </>
      ),
      at: items.flatMap((x, n) => (x.kind === 'obs' && x.phase === ph ? [n] : [])),
    })),
    {
      key: 'kept',
      head: <>Kept</>,
      at: items.flatMap((x, n) => (x.kind === 'lesson' ? [n] : [])),
    },
  ].filter((g) => g.at.length);
  return (
    <>
      <div className={styles.shHead}>
        <span className={styles.title}>Findings</span>
        <span className={styles.typed}>after the game</span>
      </div>
      <p className={styles.cap}>
        What this game taught {plural}: filed by role, not seat, so from every {one} seat
      </p>
      <div className={styles.fidx} role="tablist" aria-label="Findings">
        {groups.map((g) => (
          <span key={g.key} className={styles.fgroup}>
            <span className={styles.fhead}>{g.head}</span>
            {g.at.map((n) => {
              const x = items[n];
              const v = x.kind === 'obs' ? verdictKind(x.o.net_verdict) : null;
              return (
                <button
                  key={n}
                  type="button"
                  role="tab"
                  aria-selected={n === k}
                  aria-label={`${label(n)}${v ? `, ${NET[v].toLowerCase()}` : ', a lesson kept'}`}
                  onClick={() => setI(n)}
                >
                  {v ? (
                    <VerdictMark
                      kind={v}
                      className={`${styles.fmark} ${styles[`t-${v}`]}`}
                    />
                  ) : null}
                  {n < obs.length ? n + 1 : `L${n + 1 - obs.length}`}
                </button>
              );
            })}
          </span>
        ))}
      </div>
      {cur.kind === 'obs' ? (
        <div key={k} className={styles.finding}>
          <p className={styles.cap}>
            {label(k)} · {PHASE_NAME[cur.phase] ?? cur.phase}
          </p>
          <Situation text={cur.o.situation} label="The situation" folded />
          <div className={styles.reason}>
            <span
              className={`${styles.stamp} ${styles.vstamp} ${styles[`t-${verdictKind(cur.o.net_verdict)}`]}`}
            >
              <VerdictMark kind={verdictKind(cur.o.net_verdict)} className={styles.smark} />
              {NET[verdictKind(cur.o.net_verdict)]}
            </span>
            <p className={styles.cap}>What was done</p>
            <p className={styles.fbody}>{cap(seatify(cur.o.approach))}</p>
            <p className={`${styles.cap} ${styles.gap}`}>How it turned out</p>
            <p className={styles.fbody}>{cap(seatify(stripVerdict(cur.o.outcome)))}</p>
          </div>
        </div>
      ) : (
        <div key={k} className={styles.finding}>
          <p className={styles.cap}>
            {label(k)} · {PHASE_NAME[cur.phase] ?? cur.phase}
          </p>
          <div className={styles.prec}>
            <p className={styles.cap}>The lesson kept</p>
            <p>{seatify(cur.l.action)}</p>
          </div>
          <Situation text={cur.l.situation} label="Written for" folded />
        </div>
      )}
    </>
  );
}

const cap = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const bare = (s: string) =>
  s
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/[\s.;,]+$/, '')
    .trim();

function Tick() {
  return (
    <svg viewBox="0 0 22 20" aria-hidden="true">
      <path
        d="M2 11.5c2 1.2 3.6 3 4.8 5.6C9.5 10 13.5 5 20 1.5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
      />
    </svg>
  );
}

function Clip() {
  return (
    <svg className={styles.clip} viewBox="0 0 18 40" aria-hidden="true">
      <path
        d="M6 30V8a3 3 0 0 1 6 0v24a5 5 0 0 1-10 0V6a7 7 0 0 1 14 0v22"
        fill="none"
        stroke="#8a8f94"
        strokeWidth={2}
        strokeLinecap="round"
      />
    </svg>
  );
}

/**
 * Whether the side slot is drawn wide enough for a tab per seat (424 css px, three-quarters of
 * its full size, which is also where the stage turns `data-small`): measured on the slot itself,
 * after the stage has scaled, and again when the window or the stage's size class changes.
 */
function useWideSlot(ref: React.RefObject<HTMLElement | null>) {
  const [wide, setWide] = useState(true);
  useLayoutEffect(() => {
    const check = () => {
      const w = ref.current?.getBoundingClientRect().width ?? 0;
      if (w > 0) setWide(w >= 424);
    };
    check();
    const raf = requestAnimationFrame(check);
    window.addEventListener('resize', check);
    const mo = new MutationObserver(check);
    mo.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-small'],
      subtree: true,
    });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', check);
      mo.disconnect();
    };
  }, [ref]);
  return wide;
}

/**
 * Whether the stage is drawn phone-small (Stage.tsx sets `data-small` on the stage's box), for
 * what folds by default there. Watched, as the stage toggles it on a resize.
 */
function useSmall() {
  const ref = useRef<HTMLDivElement>(null);
  const [small, setSmall] = useState(false);
  useLayoutEffect(() => {
    const check = () => setSmall(!!ref.current?.closest('[data-small]'));
    check();
    const mo = new MutationObserver(check);
    mo.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-small'],
      subtree: true,
    });
    return () => mo.disconnect();
  }, []);
  return { ref, small };
}

// ---- the docket -----------------------------------------------------------------------

function Docket({
  model,
  chip,
  onSeat,
}: {
  model: DocketModel;
  chip: (seat: string, cls?: string) => ReactNode;
  onSeat: (seat: string) => void;
}) {
  const sm = `${styles.face} ${styles.sm}`;
  const role = (r: string | null) =>
    r ? <i className={styles.role}>{(ROLE_NAME[r] ?? r).toLowerCase()}</i> : null;
  const head = (title: string, typed: string) => (
    <div className={styles.shHead}>
      <span className={styles.title}>{title}</span>
      <span className={styles.typed}>{typed}</span>
    </div>
  );

  switch (model.kind) {
    case 'night':
      return (
        <>
          {head('The night, inside', `Night ${model.day} · what each did`)}
          <div className={styles.rows}>
            {/* an actor's row opens its file (the pack's, the first wolf's) */}
            {model.rows.map((b) => (
              <button
                key={b.actor}
                type="button"
                className={styles.row}
                onClick={() => onSeat(b.seats[0] ?? b.actor)}
                title={`Open seat ${seatNumber(b.seats[0] ?? b.actor)}’s file`}
              >
                <span className={styles.faces}>
                  {b.seats.map((s) => (
                    <span key={s}>{chip(s, sm)}</span>
                  ))}
                </span>
                <span className={styles.nm}>
                  {b.actor === 'pack' ? (
                    <>
                      The pack{' '}
                      <small>
                        {b.seats.map((s) => `seat ${seatNumber(s)}`).join(' and ')}
                      </small>
                    </>
                  ) : (
                    <>
                      Seat {seatNumber(b.actor)} {role(b.role)}
                    </>
                  )}
                </span>
                <span className={styles.pair}>
                  {b.target ? (
                    <>
                      {ACT_VERB[b.role] ?? 'acts on'} {chip(b.target, sm)}
                    </>
                  ) : (
                    'holds'
                  )}
                </span>
              </button>
            ))}
          </div>
          <p className={styles.legend}>
            In the order the log finished them. Live, nobody sees any of this.
          </p>
        </>
      );

    case 'vote':
      return (
        <>
          {head('Inside the vote', `Day ${model.day} · what each voter weighed`)}
          <div className={styles.rows}>
            {/* a voter's row opens its file: the reads and the lessons it voted on */}
            {model.rows.map((v) => (
              <button
                key={v.voter}
                type="button"
                className={styles.row}
                onClick={() => onSeat(v.voter)}
                title={`Open seat ${seatNumber(v.voter)}’s file`}
              >
                {chip(v.voter, sm)}
                <span className={styles.nm}>
                  Seat {seatNumber(v.voter)} {role(v.role)}
                  <small>
                    {v.votee === 'abstain'
                      ? 'abstains'
                      : `votes seat ${seatNumber(v.votee)}`}
                  </small>
                </span>
                <span className={styles.vd} aria-label="the lessons it weighed">
                  {v.verdicts.length ? (
                    v.verdicts.map((x, i) => (
                      <span
                        key={i}
                        className={x ? styles[`bg-${x}`] : undefined}
                        title={x ? VWORD[x] : ''}
                      >
                        {x ? PIP[x] : '·'}
                      </span>
                    ))
                  ) : (
                    <small>none</small>
                  )}
                </span>
              </button>
            ))}
          </div>
          <p className={styles.legend}>
            The lessons each voter weighed before its ballot, No. 1 to 3: F followed, O
            overrode, – doesn’t apply. Tap a voter for its file.
          </p>
        </>
      );

    case 'lynch': {
      const had = model.rows;
      return (
        <>
          {head(
            'Who had them right',
            `Seat ${seatNumber(model.seat)} was ${ROLE_ARTICLE[model.role] ?? model.role}`,
          )}
          <div className={styles.rows}>
            {had.map((r) => (
              <div key={r.voter} className={styles.read}>
                {chip(r.voter, sm)}
                <span className={styles.guess}>
                  <small>
                    Seat {seatNumber(r.voter)} {role(r.role)}
                  </small>
                  <b>
                    {r.suspected
                      ? r.suspected === 'unclear'
                        ? 'unclear'
                        : (ROLE_NAME[r.suspected] ?? r.suspected).toLowerCase()
                      : 'no read'}
                  </b>
                  {r.confidence ? (
                    <small>{r.confidence === 'high' ? 'sure' : 'not sure'}</small>
                  ) : null}
                </span>
                <span className={`${styles.mk} ${styles[`m-${r.mark}`]}`} title={r.mark}>
                  {MARK[r.mark]}
                </span>
                {r.why ? <p className={styles.why}>{seatify(r.why)}</p> : null}
              </div>
            ))}
          </div>
          <p className={styles.legend}>
            ● had the role · ◐ had the side · ○ no read or wrong.{' '}
            {had.filter((h) => h.mark === 'role').length} of {had.length} had the role;{' '}
            {had.filter((h) => h.mark === 'side').length} more had the side.
          </p>
          {model.note ? (
            <LastNote
              label={`Seat ${seatNumber(model.seat)}’s last note before the vote`}
              note={model.note}
            />
          ) : null}
        </>
      );
    }

    case 'brief':
      return <Brief model={model} chip={(s) => chip(s, sm)} />;

    case 'deal':
      return (
        <>
          {model.truth
            ? head('The case, closed', 'the deal, and how each seat went')
            : head('The deal', 'every seat, face up')}
          <div className={styles.rows}>
            {model.rows.map((s) => {
              const f = factionOf(s.role);
              return (
                <button
                  key={s.seat}
                  type="button"
                  className={`${styles.row} ${styles.open}`}
                  onClick={() => onSeat(s.seat)}
                  title={`Open seat ${seatNumber(s.seat)}’s file`}
                >
                  {chip(s.seat, sm)}
                  <span className={styles.nm}>
                    Seat {seatNumber(s.seat)}{' '}
                    {s.role ? (
                      <span className={f ? styles[`s-${f}`] : undefined}>
                        <Sigil role={s.role} className={styles.sigil} /> {role(s.role)}
                      </span>
                    ) : (
                      <i className={styles.role}>unknown</i>
                    )}
                  </span>
                  <span className={styles.pair}>{s.fate ?? ''}</span>
                </button>
              );
            })}
          </div>
          <p className={styles.legend}>
            {model.truth
              ? 'Withheld all game; every viewer holds it once the game is over. Tap a seat for its whole file.'
              : 'Face up once revealed; the table knows only the cast. Tap a seat for its file.'}
          </p>
        </>
      );

    case 'notes':
      return (
        <>
          {head('The winners’ last notes', 'the last note each wrote')}
          {model.rows.map(({ seat, role: r, note }) =>
            note ? (
              <LastNote
                key={seat}
                label={`Seat ${seatNumber(seat)}${r ? `, ${(ROLE_NAME[r] ?? r).toLowerCase()}` : ''}`}
                note={note}
              />
            ) : null,
          )}
        </>
      );

    case 'empty':
      return (
        <>
          {head(docketTitle(model), model.label)}
          <p className={styles.empty}>
            Nothing on file at this beat. A turn and a night act open that seat’s file; this
            sheet holds the count, the lynch’s card, a morning’s brief, the night whole, the
            deal and the ending. Any seat’s file is a tap away, on the name above.
          </p>
        </>
      );
  }
}

function LastNote({ label, note }: { label: string; note: FilmNote }) {
  return (
    <div className={styles.lastNote}>
      <p className={styles.cap}>{label}</p>
      <p>{seatify(note.text)}</p>
    </div>
  );
}

function Brief({
  model,
  chip,
}: {
  model: Extract<DocketModel, { kind: 'brief' }>;
  chip: (seat: string) => ReactNode;
}) {
  const s = model.summary;
  const seats = (list: readonly string[]) =>
    list.map((p) => <span key={p}>{chip(p)}</span>);
  return (
    <>
      <div className={styles.shHead}>
        <span className={styles.title}>What day {model.day} taught</span>
        <span className={styles.typed}>the brief carried into day {model.day + 1}</span>
      </div>
      {!s ? (
        <p className={styles.empty}>No summary was carried from this day.</p>
      ) : (
        <>
          <p className={styles.sect}>Accusations</p>
          {s.accusations.length ? (
            s.accusations.map((a, i) => (
              <div key={i} className={styles.acc}>
                <header>
                  {seats(a.accusers)}
                  <span aria-hidden="true">→</span>
                  {chip(a.target)}
                  <span>
                    {a.accusers.map((p) => `Seat ${seatNumber(p)}`).join(', ')} → Seat{' '}
                    {seatNumber(a.target)}
                  </span>
                  <span className={styles.tag}>{a.evidenceType.replace(/_/g, ' ')}</span>
                </header>
                <p>{seatify(a.reasoning)}</p>
                {a.defense ? (
                  <p className={styles.def}>
                    <b>Defence:</b> {seatify(a.defense)}
                  </p>
                ) : null}
              </div>
            ))
          ) : (
            <p className={styles.none}>No accusations that day.</p>
          )}
          <p className={styles.sect}>Claims</p>
          {s.roleClaims.length ? (
            s.roleClaims.map((c, i) => (
              <div key={i} className={styles.acc}>
                <header>
                  {chip(c.player)} Seat {seatNumber(c.player)} claims <b>{c.claimedRole}</b>
                </header>
                {c.evidence ? <p className={styles.def}>{seatify(c.evidence)}</p> : null}
              </div>
            ))
          ) : (
            <p className={styles.none}>None.</p>
          )}
          <p className={styles.sect}>Blocs</p>
          {s.blocs.length ? (
            s.blocs.map((b, i) => (
              <div key={i} className={styles.acc}>
                <header>{seats(b.players)}</header>
                <p className={styles.def}>{seatify(b.basis)}</p>
              </div>
            ))
          ) : (
            <p className={styles.none}>None.</p>
          )}
          <p className={styles.sect}>Mood</p>
          <div className={styles.acc}>
            {[s.dynamics.landscape, s.dynamics.consensus, s.dynamics.drivers]
              .filter(Boolean)
              .map((t, i) => (
                <p key={i}>{seatify(t)}</p>
              ))}
          </div>
        </>
      )}
    </>
  );
}
