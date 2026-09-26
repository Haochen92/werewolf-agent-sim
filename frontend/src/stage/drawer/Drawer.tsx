'use client';

/**
 * The transcript drawer: the game's record down the right side of the stage, the side slot's
 * other occupant beside the X-ray film (handoff §2 "The transcript"). It is history: every
 * line the viewer holds up to the beat on stage, the beat's own line lit and scrolled to.
 * What the lines are, and who has which, is drawer-lines.ts; this draws them.
 *
 * Full height under the top strip, because it is a long scroll; the room lays itself out
 * beside it and the box at the foot moves in under the puppet. On the seated human's own
 * turn it stops at the rail, so the prompt keeps the whole width.
 *
 * The filters are the container's (they have to outlive a beat): the days as tabs along the
 * foot; the seats as their chips at the head (the dead dimmed, still selectable, since their
 * lines are history); and Show, one toggle per tier this viewer has.
 */
import {
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
  drawerDays,
  drawerLines,
  filterLines,
  litKey,
  showRow,
  WINNER_TEXT,
  type DrawerFilters,
  type DrawerLine,
  type LineTier,
} from './drawer-lines';
import styles from './Drawer.module.css';

const PASS_REASON: Record<string, string> = {
  voluntary: 'chose to pass',
  novelty_gated: 'held back: nothing new to say',
  generation_failed: 'no line came',
};
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
}: DrawerProps) {
  const g = geometry(hud, true);
  const lines = useMemo(
    () => drawerLines(view, { me, xray, beat }),
    [view, me, xray, beat],
  );
  const shown = useMemo(() => filterLines(lines, filters), [lines, filters]);
  const lit = litKey(lines, beat);
  const days = drawerDays(lines);
  const tiers = showRow(me, xray);
  const dead = new Set(view.dead.map((d) => d.player));
  const [open, setOpen] = useState<ReadonlySet<string>>(new Set());

  // the beat's line scrolled into view, a little above the middle (bench 74); none: the end
  const scroller = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const now = lit ? el.querySelector<HTMLElement>(`[data-line="${lit}"]`) : null;
    const top = now ? Math.max(0, now.offsetTop - el.clientHeight * 0.6) : el.scrollHeight;
    el.scrollTo({ top, behavior: animate ? 'smooth' : 'auto' });
  }, [lit, shown, animate]);

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

      <div className={styles.lines} ref={scroller}>
        {shown.length ? (
          shown.map((l) => (
            <Line
              key={l.key}
              line={l}
              lit={l.key === lit}
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
  lit,
  open,
  onToggle,
  chip,
  roleTag,
  you,
}: {
  line: DrawerLine;
  lit: boolean;
  open: boolean;
  onToggle: () => void;
  chip: (seat: string, cls?: string) => ReactNode;
  roleTag: (seat: string) => ReactNode;
  you: (seat: string) => string;
}) {
  const cls = (...k: string[]) =>
    [styles.tl, ...k.map((x) => styles[x]), lit ? styles.now : '']
      .filter(Boolean)
      .join(' ');
  const blank = chip('', styles.blank);
  const at = { 'data-line': l.key, 'data-kind': l.kind };
  const sigils = (roles: string[]) =>
    roles.map((r, i) => {
      const f = factionOf(r);
      return (
        <span key={i} className={`${styles.sg} ${f ? styles[`c-${f}`] : ''}`} title={r}>
          <Sigil role={r} />
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
      return (
        <div className={styles.rule} {...at}>
          {l.text}
          <i />
        </div>
      );
    case 'speech':
      return (
        <div className={cls('say')} {...at}>
          {chip(l.player)}
          <div className={styles.who}>
            Seat {seatNumber(l.player)}
            {you(l.player)}
            {roleTag(l.player)}
          </div>
          <div className={styles.txt}>{seatify(l.text)}</div>
        </div>
      );
    case 'pass':
      return (
        <div className={cls('xr')} {...at}>
          {chip(l.player)}
          <div className={styles.who}>
            Seat {seatNumber(l.player)}
            {you(l.player)} passes
            {roleTag(l.player)}
            <i>{l.reason ? (PASS_REASON[l.reason] ?? l.reason) : 'chose to pass'}</i>
          </div>
          {l.draft ? (
            <div className={styles.txt}>
              <span className={styles.draft}>{seatify(l.draft)}</span>
            </div>
          ) : null}
        </div>
      );
    case 'gm':
      return (
        <div className={cls('sys', 'gm')} {...at}>
          <div className={styles.txt}>
            {seatify(l.text)}
            {sigils(l.roles)}
          </div>
        </div>
      );
    case 'votes':
      return (
        <div className={cls('sys')} {...at}>
          <div className={styles.txt}>
            The table votes, {l.pairs.length} ballot{l.pairs.length === 1 ? '' : 's'} at the
            count
            <div className={styles.pairs}>
              {l.pairs.map((p) => (
                <span
                  key={p.voter}
                  className={styles.pair}
                  title={`Seat ${seatNumber(p.voter)}`}
                >
                  {chip(p.voter)}
                  <span>→</span>
                  {p.votee === 'abstain' ? (
                    <span className={styles.ab} title="abstains" />
                  ) : (
                    chip(p.votee)
                  )}
                </span>
              ))}
            </div>
          </div>
        </div>
      );
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
          className={cls('xr', 'brief', ...(open ? ['open'] : []))}
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
          <div className={styles.txt}>{seatify(l.text)}</div>
        </div>
      );
    case 'over':
      return (
        <div className={cls('sys')} {...at}>
          <div className={styles.txt}>{WINNER_TEXT[l.winner] ?? l.winner}</div>
        </div>
      );
  }
}
