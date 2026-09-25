/**
 * The count pill: how many are in, and never who. "Acted 2 of 5" through the night (the pack
 * counts as one, and seats with nothing to do are padded in, so the count leaks nobody);
 * "Ballots in, 4 of 7" through the vote. A dot per unit, filled as they come in; the viewer's
 * own, if it has one, in amber. It sits at the top centre of the room, clear of the wing.
 */
import { geometry, type Hud } from '../units';
import styles from './CountPill.module.css';

export interface CountPillProps {
  hud: Hud;
  /** "Acted", "Ballots in". */
  label: string;
  n: number;
  total: number;
  /** Which dot is the viewer's own (0-based), if one is in. */
  mine?: number | null;
  /** The side slot is open: centred on the narrower room. */
  side?: boolean;
}

export function CountPill({ hud, label, n, total, mine, side = false }: CountPillProps) {
  const g = geometry(hud, side);
  return (
    <div className={styles.pill} style={{ left: g.wingN + g.room / 2 }} role="status">
      <span>{label}</span>
      <b>
        {n} of {total}
      </b>
      <span className={styles.dots} aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <i key={i} className={i === mine ? styles.mine : i < n ? styles.in : undefined} />
        ))}
      </span>
    </div>
  );
}
