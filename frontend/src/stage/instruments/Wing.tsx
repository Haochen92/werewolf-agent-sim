/**
 * The wing: the nine seats down the left edge of the stage, one tile each, so the whole table
 * is always in view while one seat has the stand. A tile is the seat's chip and numeral; the
 * seat on the stand is lit; a dead seat turns to its role's sigil on paper (deaths reveal the
 * role on the wire, so everyone may see it); with the X-ray on, a living seat also wears its
 * faction's strip and a sigil badge, which is the truth only the observer tier holds.
 *
 * Lit and dimmed are light only (border and background, opacity), never a move or a resize.
 */
import type { CSSProperties, ReactNode } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { factionOf } from '../roles';
import { Sigil } from './Sigil';
import styles from './Wing.module.css';

export function Wing({ width, children }: { width: number; children: ReactNode }) {
  if (width <= 0) return null;
  return (
    <div className={styles.wing} style={{ width } as CSSProperties}>
      {children}
    </div>
  );
}

export interface WingTileProps {
  /** The numeral, 1–9. */
  seat: number;
  character: Character;
  /** Dead: the tile shows this role's sigil (null if the role is somehow unknown). */
  dead?: { role: string | null };
  /** The role this viewer is entitled to see on a living seat (the X-ray's truth). */
  truth?: string | null;
  /** On the stand now. */
  lit?: boolean;
  /** Dimmed: out of the scene's focus (the losers at the end, say). */
  dim?: boolean;
  /** This viewer's own seat. */
  you?: boolean;
  /** A packmate, as a wolf sees it: the red edge. */
  pack?: boolean;
  /** The X-ray night's lamp: this seat acts tonight. */
  lamp?: boolean;
  /**
   * The X-ray's read on this seat by the seat at the stand: a blue edge, brighter for a sure
   * read. `onRead` makes the tile a button that opens the read card (handing over the tile, so
   * the card can sit level with it); `open` while its card is out.
   */
  read?: { sure: boolean; open?: boolean; onRead?: (tile: HTMLElement) => void };
}

export function WingTile({
  seat,
  character,
  dead,
  truth,
  lit,
  dim,
  you,
  pack,
  lamp,
  read,
}: WingTileProps) {
  const role = dead ? dead.role : (truth ?? null);
  const faction = factionOf(role);
  const cls = [
    styles.tile,
    faction ? styles[`c-${faction}`] : '',
    dead ? styles.dead : '',
    lit ? styles.lit : '',
    dim ? styles.dim : '',
    pack ? styles.pack : '',
    read ? styles.read : '',
    read?.sure ? styles.sure : '',
    read?.open ? styles.open : '',
  ]
    .filter(Boolean)
    .join(' ');
  const tap = read?.onRead;
  return (
    <div
      className={cls}
      data-seat={seat}
      {...(tap
        ? {
            role: 'button',
            tabIndex: 0,
            'aria-label': `The speaker's read of seat ${seat}`,
            'aria-expanded': !!read?.open,
            onClick: (e: React.MouseEvent<HTMLElement>) => tap(e.currentTarget),
            onKeyDown: (e: React.KeyboardEvent<HTMLElement>) => {
              if (e.key === 'Enter' || e.key === ' ') tap(e.currentTarget);
            },
          }
        : {})}
    >
      <span className={you ? `${styles.face} ${styles.you}` : styles.face}>
        <b className={styles.num}>{seat}</b>
        {dead ? (
          role ? (
            <Sigil role={role} className={styles.sigil} />
          ) : null
        ) : (
          <>
            <ChipSprite character={character} />
            {faction ? <span className={styles.strip} /> : null}
            {truth ? (
              <span className={styles.badge}>
                <Sigil role={truth} />
              </span>
            ) : null}
          </>
        )}
        {lamp ? <span className={styles.lamp} /> : null}
      </span>
    </div>
  );
}
