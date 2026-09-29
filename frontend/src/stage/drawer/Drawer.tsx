'use client';

/**
 * The transcript drawer: the game's record down the right side of the stage, the side slot's
 * other occupant beside the X-ray film (handoff §2 "The transcript"). It is history: every
 * line the viewer holds up to the beat on stage, the beat's own line lit and scrolled to.
 * What the lines are, and who has which, is drawer-lines.ts; this draws them.
 *
 * It follows the beat only while the reader is at it: scrolled away to read back, the lines
 * stay put as new ones arrive, and a "Back to now" pill at the foot returns (owner,
 * 2026-09-29). Where they were, and whether they follow, outlives the scene (`scroll`).
 *
 * Full height under the top strip, because it is a long scroll; the room lays itself out
 * beside it and the box at the foot moves in under the puppet. On the seated human's own
 * turn it stops at the rail, so the prompt keeps the whole width.
 *
 * The filters are the container's (they have to outlive a beat): the days as tabs along the
 * foot; the seats as their chips at the head (the dead dimmed, still selectable, since their
 * lines are history); and Show, one toggle per tier this viewer has.
 *
 * Set like a page of a book rather than a list of cards (HUD pass 3a, owner 2026-09-29): the
 * chapters as headings (the day large, in the display face), the speeches as a small head and
 * a name over the words, a run of passes as one quiet line, the vote as a tally of faces per
 * seat voted for with the sentence under it, the game master's reports as short sentences with
 * the dead in terracotta. One column, the phone's width and the desktop's alike. What only the
 * X-ray shows is in its verdigris, so hidden information never reads as public talk.
 */
import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react';
import type { Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { SceneBeat } from '../beats/types';
import { ChipSprite } from '../cast/ChipSprite';
import { Sigil } from '../instruments/Sigil';
import { factionOf, seatNumber, seatify, ROLE_NAME } from '../roles';
import { STAGE_H, STAGE_W, geometry, type Hud } from '../units';
import {
  ACT_VERB,
  briefRows,
  drawerDays,
  drawerLines,
  filterLines,
  groupPasses,
  litKey,
  passSentence,
  passWhy,
  reportParts,
  shownKeys,
  showRow,
  voteSentence,
  voteTally,
  WINNER_TEXT,
  type DrawerFilters,
  type DrawerLine,
  type LineTier,
  type ShownLine,
} from './drawer-lines';
import type { DrawerScroll } from './use-drawer-filters';
import styles from './Drawer.module.css';

const TIER_NAME: Record<LineTier, string> = {
  public: 'Public',
  private: 'Private',
  xray: 'X-ray',
};

export interface DrawerProps {
  view: GameView;
  beat: SceneBeat;
  me: string | null;
  xray: boolean;
  hud: Hud;
  cast: readonly Character[];
  filters: DrawerFilters;
  onFilters?: (next: DrawerFilters) => void;
  /** The seated human is answering a prompt: stop at the rail. */
  rail?: boolean;
  /** The rail stop holds on a phone too (their own room); else the drawer runs full there. */
  railHolds?: boolean;
  /** Played forward: scroll to the new line smoothly; at rest it is simply there. */
  animate?: boolean;
  /** Where the reader was and whether they follow the beat, kept across scenes by the container. */
  scroll?: DrawerScroll;
}

export function Drawer({
  view,
  beat,
  me,
  xray,
  hud,
  cast,
  filters,
  onFilters,
  rail = false,
  railHolds = false,
  animate = false,
  scroll: kept,
}: DrawerProps) {
  const g = geometry(hud, true);
  const lines = useMemo(
    () => drawerLines(view, { me, xray, beat }),
    [view, me, xray, beat],
  );
  const shown = useMemo(() => groupPasses(filterLines(lines, filters)), [lines, filters]);
  // the days whose votes line tells the ballots, so the game master's line need not
  const told = useMemo(
    () => new Set(lines.flatMap((l) => (l.kind === 'votes' ? [l.day] : []))),
    [lines],
  );
  const lit = litKey(lines, beat);
  const days = drawerDays(lines);
  const tiers = showRow(me, xray);
  const dead = new Set(view.dead.map((d) => d.player));
  const [open, setOpen] = useState<ReadonlySet<string>>(new Set());

  // Following, the beat's line is scrolled into view, a little below the middle (bench 74);
  // none: the end. Scrolled away by the reader, it stays where they left it.
  const scroller = useRef<HTMLDivElement>(null);
  const [own] = useState<DrawerScroll>(() => ({ following: true, top: 0 }));
  const memo = kept ?? own;
  const [following, setFollowing] = useState(memo.following);
  // our own scrolling (a smooth scroll fires many scroll events) is not the reader's
  const ours = useRef(false);
  const settle = useRef<ReturnType<typeof setTimeout>>(undefined);
  const goTo = (behavior: ScrollBehavior) => {
    const el = scroller.current;
    if (!el) return;
    const now = lit ? el.querySelector<HTMLElement>(`[data-line="${lit}"]`) : null;
    const top = now ? Math.max(0, now.offsetTop - el.clientHeight * 0.6) : el.scrollHeight;
    if (Math.abs(el.scrollTop - Math.min(top, el.scrollHeight - el.clientHeight)) < 1)
      return;
    ours.current = true;
    el.scrollTo({ top, behavior });
  };
  // at now: the beat's line in view, or the foot when there is none
  const atNow = () => {
    const el = scroller.current;
    if (!el) return true;
    const now = lit ? el.querySelector<HTMLElement>(`[data-line="${lit}"]`) : null;
    if (!now) return el.scrollHeight - el.scrollTop - el.clientHeight < 32;
    const y = now.offsetTop - el.scrollTop;
    return y + now.offsetHeight > 0 && y < el.clientHeight;
  };
  const follow = (on: boolean) => {
    memo.following = on;
    setFollowing(on);
  };
  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    if (memo.following) goTo(animate ? 'smooth' : 'auto');
    // a new drawer (another scene) opens where the reader left the last one
    else if (Math.abs(el.scrollTop - memo.top) > 1) {
      ours.current = true;
      el.scrollTop = memo.top;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lit, shown, animate]);
  useEffect(() => () => clearTimeout(settle.current), []);
  const onScroll = () => {
    const el = scroller.current;
    if (!el) return;
    memo.top = el.scrollTop;
    clearTimeout(settle.current);
    // ours: wait for it to come to rest, then read where it stopped
    if (ours.current) {
      settle.current = setTimeout(() => {
        ours.current = false;
        const at = atNow();
        if (at !== memo.following) follow(at);
      }, 160);
      return;
    }
    const at = atNow();
    if (at !== memo.following) follow(at);
  };
  // a wheel, a finger or a key on the lines is the reader taking over from our scroll
  const reader = () => {
    ours.current = false;
  };
  const backToNow = () => {
    follow(true);
    goTo('smooth');
  };

  const set = (next: Partial<DrawerFilters>) => onFilters?.({ ...filters, ...next });
  const chip = (seat: string, cls = '') => {
    const c = cast[seatNumber(seat) - 1];
    return (
      <span className={`${styles.hchip} ${cls}`}>
        {c ? <ChipSprite character={c} /> : null}
      </span>
    );
  };
  const roleTag = (seat: string) => {
    const r = xray ? view.xray.roles[seat] : null;
    if (!r) return null;
    const f = factionOf(r);
    return (
      <span className={`${styles.rt} ${f ? styles[`c-${f}`] : ''}`}>
        {(ROLE_NAME[r] ?? r).toLowerCase()}
      </span>
    );
  };
  const you = (seat: string) => (seat === me ? ' (you)' : '');

  return (
    <aside
      className={styles.drawer}
      style={
        {
          left: STAGE_W - g.slotW,
          width: g.slotW,
          '--drawer-h': `${rail ? g.railY : STAGE_H}px`,
        } as CSSProperties
      }
      data-drawer={rail ? 'rail' : 'full'}
      data-rail={rail ? (railHolds ? 'holds' : 'soft') : undefined}
      aria-label="Transcript"
    >
      <header>
        <div className={styles.ttl}>
          Transcript
          <small>
            {xray
              ? 'with the X-ray’s lines'
              : me
                ? 'and your own lines'
                : 'the public record'}
          </small>
        </div>
        <div className={styles.filters}>
          <div className={styles.fg} role="group" aria-label="Seat">
            <span>Seat</span>
            <button
              type="button"
              className={styles.pill}
              aria-pressed={filters.seat === null}
              onClick={() => set({ seat: null })}
            >
              All
            </button>
            {view.seats.map((s) => {
              const c = cast[seatNumber(s) - 1];
              return (
                <button
                  key={s}
                  type="button"
                  className={`${styles.pill} ${styles.seatp} ${dead.has(s) ? styles.dead : ''}`}
                  aria-pressed={filters.seat === s}
                  title={`Seat ${seatNumber(s)}`}
                  onClick={() => set({ seat: filters.seat === s ? null : s })}
                >
                  {c ? <ChipSprite character={c} /> : seatNumber(s)}
                </button>
              );
            })}
          </div>
          {tiers.length ? (
            <div className={styles.fg} role="group" aria-label="Show">
              <span>Show</span>
              {tiers.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`${styles.pill} ${styles.show} ${styles[t]}`}
                  aria-pressed={filters.show[t]}
                  onClick={() => set({ show: { ...filters.show, [t]: !filters.show[t] } })}
                >
                  <i>{filters.show[t] ? '✓' : ''}</i>
                  {TIER_NAME[t]}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </header>

      <div className={styles.page}>
        <div
          className={styles.lines}
          ref={scroller}
          onScroll={onScroll}
          onWheel={reader}
          onTouchStart={reader}
          onPointerDown={reader}
          onKeyDown={reader}
        >
          {shown.length ? (
            shown.map((l) => (
              <Line
                key={l.key}
                line={l}
                lit={lit}
                ballotsTold={told.has(l.day)}
                open={open.has(l.key)}
                onToggle={() =>
                  setOpen((o) => {
                    const n = new Set(o);
                    if (n.has(l.key)) n.delete(l.key);
                    else n.add(l.key);
                    return n;
                  })
                }
                chip={chip}
                roleTag={roleTag}
                you={you}
              />
            ))
          ) : (
            <div className={styles.empty}>
              {/* before the first line (the deal) there is nothing to filter yet */}
              {lines.some((l) => l.kind !== 'rule')
                ? 'Nothing here under these filters.'
                : 'Nothing said yet.'}
            </div>
          )}
        </div>

        {following ? null : (
          <button type="button" className={styles.backnow} onClick={backToNow}>
            <span aria-hidden="true">↓</span> Back to now
          </button>
        )}
      </div>

      <nav className={styles.daytabs} aria-label="Days">
        <button
          type="button"
          aria-pressed={filters.day === 'all'}
          onClick={() => set({ day: 'all' })}
        >
          All days
        </button>
        {days.map((d) => (
          <button
            key={d}
            type="button"
            aria-pressed={filters.day === d}
            onClick={() => set({ day: d })}
          >
            Day {d}
          </button>
        ))}
      </nav>
    </aside>
  );
}

function Line({
  line: l,
  lit: litKey,
  ballotsTold,
  open,
  onToggle,
  chip,
  roleTag,
  you,
}: {
  line: ShownLine;
  /** The beat's line: this one, or one of a run's passes. */
  lit: string | null;
  ballotsTold: boolean;
  open: boolean;
  onToggle: () => void;
  chip: (seat: string, cls?: string) => ReactNode;
  roleTag: (seat: string) => ReactNode;
  you: (seat: string) => string;
}) {
  const lit = litKey !== null && shownKeys(l).includes(litKey);
  const cls = (...k: string[]) =>
    [styles.tl, ...k.map((x) => styles[x]), lit ? styles.now : '']
      .filter(Boolean)
      .join(' ');
  const blank = chip('', styles.blank);
  const at = { 'data-line': l.key, 'data-kind': l.kind };
  const sigil = (r: string) => {
    const f = factionOf(r);
    return (
      <span className={`${styles.sg} ${f ? styles[`c-${f}`] : ''}`} title={r}>
        <Sigil role={r} />
      </span>
    );
  };
  // a report's seat names in the display face: the dead in terracotta, the living in brass
  const named = (text: string, dead: ReadonlySet<string>) =>
    text.split(/(\b[Ss]eat \d+)/).map((t, i) => {
      const m = /^[Ss]eat (\d+)$/.exec(t);
      if (!m) return t;
      return (
        <span key={i} className={dead.has(`player_${m[1]}`) ? styles.dead : styles.nm}>
          {t}
        </span>
      );
    });
  const only = (t: DrawerLine & { kind: 'only' }) =>
    typeof t.text === 'string' ? (
      seatify(t.text)
    ) : (
      <>
        {t.text.lead}
        {t.text.chip ? chip(t.text.chip, styles.sm) : null}
        {t.text.rest}
      </>
    );

  switch (l.kind) {
    case 'rule':
      // the day is the chapter heading; the vote, the night, the morning and the end are its
      // sections, each under a hairline
      return l.chapter === 'day' ? (
        <h3 className={styles.day} {...at}>
          Day {l.day}
          <small>Discussion</small>
        </h3>
      ) : (
        <h4 className={`${styles.sect} ${styles[`s-${l.chapter}`]}`} {...at}>
          {l.chapter === 'night' ? <Moon /> : null}
          {l.chapter === 'vote' ? 'Vote' : l.text}
        </h4>
      );
    case 'speech':
      return (
        <div className={cls('say')} {...at}>
          {chip(l.player)}
          <div className={styles.who}>
            <span className={styles.nm}>Seat {seatNumber(l.player)}</span>
            {you(l.player)}
            {roleTag(l.player)}
          </div>
          <div className={styles.txt}>{seatify(l.text)}</div>
        </div>
      );
    case 'pass':
      // folded into a run by groupPasses; a lone one is drawn as a run of one
      return null;
    case 'passes':
      return (
        <div className={cls('passes')} {...at}>
          <p className={styles.ps}>
            {l.passes.map((p, i) => {
              const why = passWhy(p);
              return (
                <span key={p.key} data-line={p.key}>
                  {i ? ' ' : ''}
                  {passSentence(p)}
                  {why ? <span className={styles.why}>, {why}</span> : null}.
                </span>
              );
            })}
          </p>
          {l.passes.map((p) =>
            p.draft ? (
              <div key={p.key} className={styles.draft}>
                <small>Seat {seatNumber(p.player)} held back</small>
                {seatify(p.draft)}
              </div>
            ) : null,
          )}
        </div>
      );
    case 'gm': {
      const dead = new Set(l.seats.slice(0, l.roles.length));
      return (
        <div className={cls('report')} {...at}>
          {reportParts(l, ballotsTold).map((p, i) => (
            <p key={i}>
              {named(p.text, dead)}
              {p.role ? sigil(p.role) : null}
            </p>
          ))}
        </div>
      );
    }
    case 'votes': {
      // a tally per seat voted for: the voters' faces are its marks (big enough to tell apart
      // on a phone, about 24 css px), the count at the right, the sentence under it
      const rows = voteTally(l.pairs);
      return (
        <div className={cls('votes')} {...at}>
          {rows.map((r) => (
            <div key={r.votee} className={styles.trow}>
              <span className={styles.tn}>
                {r.votee === 'abstain' ? 'Abstain' : `Seat ${seatNumber(r.votee)}`}
              </span>
              <span className={styles.marks}>
                {r.voters.map((v) => (
                  <span key={v} title={`Seat ${seatNumber(v)}`}>
                    {chip(v)}
                  </span>
                ))}
              </span>
              <span className={styles.tc}>{r.voters.length}</span>
            </div>
          ))}
          <p className={styles.vs}>{voteSentence(rows)}</p>
        </div>
      );
    }
    case 'act':
      return (
        <div className={cls('xr')} {...at}>
          {chip(l.actor)}
          <div className={styles.who}>
            Seat {seatNumber(l.actor)} {ACT_VERB[l.role] ?? 'acts on'} seat{' '}
            {seatNumber(l.target)}
            {roleTag(l.actor)}
          </div>
        </div>
      );
    case 'pack':
      return (
        <div className={l.mine ? cls('pack') : cls('xr', 'pack')} {...at}>
          {chip(l.wolf)}
          <div className={styles.who}>
            <span className={styles.pk}>Pack</span>Seat {seatNumber(l.wolf)}
            {you(l.wolf)} <i>round {l.round}</i>
          </div>
          <div className={styles.txt}>{seatify(l.text)}</div>
        </div>
      );
    case 'kill':
      return (
        <div className={l.mine ? cls('pack') : cls('xr')} {...at}>
          {blank}
          <div className={styles.who}>
            {l.mine ? <span className={styles.pk}>The pack</span> : 'The pack'} chooses seat{' '}
            {seatNumber(l.target)}
            {chip(l.target, styles.sm)}
          </div>
        </div>
      );
    case 'only':
      return (
        <div className={l.mine ? cls('only') : cls('only', 'theirs')} {...at}>
          {blank}
          <div className={styles.who}>
            <span className={styles.oy}>{l.who}</span>
            {l.about}
          </div>
          <div className={styles.txt}>{only(l)}</div>
        </div>
      );
    case 'brief':
      return (
        <div
          className={cls('brief', ...(open ? ['open'] : []))}
          {...at}
          role="button"
          tabIndex={0}
          aria-expanded={open}
          onClick={onToggle}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ' ? onToggle() : undefined)}
        >
          {blank}
          <div className={styles.who}>
            The day’s brief, day {l.day} <i>what the agents carry from here</i>
            <span className={styles['open-tag']}>{open ? 'close' : 'open'}</span>
          </div>
          <Brief text={l.text} />
        </div>
      );
    case 'over':
      return (
        <div className={cls('report')} {...at}>
          <p>{WINNER_TEXT[l.winner] ?? l.winner}</p>
        </div>
      );
  }
}

/**
 * The day's brief: a labelled row per section (the label a small heading over its words), the
 * sections with nothing in them one quiet line; as it came when it does not split.
 */
function Brief({ text }: { text: string }) {
  const rows = briefRows(text);
  if (!rows) return <div className={styles.txt}>{seatify(text)}</div>;
  return (
    <div className={`${styles.txt} ${styles.rows}`}>
      {rows.map((r, i) =>
        r.kind === 'none' ? (
          <p key={i} className={styles.bnone}>
            {r.text}
          </p>
        ) : (
          <section key={i} className={styles.brow}>
            <h5>{r.label}</h5>
            {r.items.map((t, j) => (
              <p key={j}>{seatify(t)}</p>
            ))}
          </section>
        ),
      )}
    </div>
  );
}

/** The night heading's crescent, the day plaque's moon in line (TopStrip's Disc). */
function Moon() {
  return (
    <svg
      className={styles.moon}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      aria-hidden="true"
    >
      <path d="M15.6 5.2a7 7 0 1 0 3.2 11.7A6 6 0 0 1 15.6 5.2Z" strokeLinejoin="round" />
    </svg>
  );
}
