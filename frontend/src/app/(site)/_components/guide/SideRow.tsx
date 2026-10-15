'use client';

/**
 * One side's row in the guide: its badge and name, a Briefings switch that turns the whole row,
 * and its cards in a carousel that pages (three to a page on a desktop, two on a tablet, one on a
 * phone with its neighbours peeking, centred). The pages move by transform; cards off the page
 * are inert, so the keyboard never reaches a card nobody can see. A swipe pages on touch.
 */
import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { FACTION_NAME, type Faction } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import type { PoolRole } from '@/types/contracts';
import { BriefingsSwitch } from '../BriefingsSwitch';
import { RoleCard } from '../RoleCard';
import classes from './Guide.module.css';

const GAP = 24;
const SWIPE_PX = 40;
/** ms between cards when the switch turns a whole row. */
const STAGGER_MS = 60;

/** Cards to a page for the row's width, and each card's width (a phone's leaves room to peek). */
function layout(width: number) {
  if (width >= 760) return { per: 3, card: (width - 2 * GAP) / 3 };
  if (width >= 480) return { per: 2, card: (width - GAP) / 2 };
  return { per: 1, card: width * 0.8 };
}

export function SideRow({
  faction,
  roles,
}: {
  faction: Faction;
  roles: readonly PoolRole[];
}) {
  const view = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [page, setPage] = useState(0);
  const [turned, setTurned] = useState<Partial<Record<PoolRole, boolean>>>({});
  const [allTurned, setAllTurned] = useState(false);
  const [stagger, setStagger] = useState(false);
  const swipeFrom = useRef<number | null>(null);
  const swiped = useRef(false);

  useEffect(() => {
    const el = view.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { per, card } = layout(width || 1);
  const pages = Math.ceil(roles.length / per);
  const at = Math.min(page, pages - 1);
  // a single card centres in the row; a full page starts at the row's edge
  const offset = per === 1 ? (width - card) / 2 : 0;
  const shift = offset - at * per * (card + GAP);
  const name = FACTION_NAME[faction];

  const turnAll = (on: boolean) => {
    setAllTurned(on);
    setStagger(true);
    setTurned(Object.fromEntries(roles.map((r) => [r, on])));
  };

  return (
    <section
      className={classes.side}
      id={`side-${faction}`}
      data-faction={faction}
      aria-labelledby={`side-${faction}-head`}
    >
      <div className={classes.sideHead}>
        <FactionMark faction={faction} format="badge" className={classes.badge} />
        <h3 id={`side-${faction}-head`}>{name}</h3>
        <BriefingsSwitch
          checked={allTurned}
          onChange={turnAll}
          ariaLabel={`${name}: show the briefings`}
        />
      </div>

      {pages > 1 ? (
        <div className={classes.pager}>
          <button
            type="button"
            className={classes.arrow}
            aria-label={`Earlier ${name.toLowerCase()} cards`}
            disabled={at === 0}
            onClick={() => setPage(at - 1)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M15 5l-7 7 7 7" />
            </svg>
          </button>
          <span className={classes.dots}>
            {Array.from({ length: pages }, (_, i) => (
              <button
                key={i}
                type="button"
                className={classes.dot}
                aria-label={`Page ${i + 1} of ${pages}`}
                aria-current={i === at}
                onClick={() => setPage(i)}
              />
            ))}
          </span>
          <button
            type="button"
            className={classes.arrow}
            aria-label={`Later ${name.toLowerCase()} cards`}
            disabled={at === pages - 1}
            onClick={() => setPage(at + 1)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      ) : null}

      <div
        ref={view}
        className={classes.view}
        onPointerDown={(e) => {
          swipeFrom.current = e.clientX;
        }}
        onPointerUp={(e) => {
          const from = swipeFrom.current;
          swipeFrom.current = null;
          if (from === null || Math.abs(e.clientX - from) < SWIPE_PX) return;
          swiped.current = true;
          setPage(Math.max(0, Math.min(pages - 1, at + (e.clientX < from ? 1 : -1))));
        }}
        onClickCapture={(e) => {
          // a swipe that ends on a card pages the row; it must not also turn the card
          if (!swiped.current) return;
          swiped.current = false;
          e.stopPropagation();
        }}
      >
        <div
          className={classes.track}
          style={{ transform: `translateX(${shift}px)`, gap: GAP } as CSSProperties}
        >
          {roles.map((r, i) => (
            <div
              key={r}
              className={classes.slot}
              style={{ flexBasis: card }}
              inert={i < at * per || i >= (at + 1) * per}
            >
              <RoleCard
                role={r}
                turned={turned[r] ?? false}
                delay={stagger ? Math.max(0, i - at * per) * STAGGER_MS : 0}
                onTurn={(on) => {
                  setStagger(false);
                  setTurned((t) => ({ ...t, [r]: on }));
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
