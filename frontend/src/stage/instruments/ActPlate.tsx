/**
 * The brass plate at the foot of the night room: it names the act ("Protect seat 1", "Check
 * seat 4", "Shoot seat 2", "Kill seat 5") once a doll is chosen, and pressing it confirms.
 * Before a choice it asks ("Choose a seat to protect") and cannot be pressed. The vigilante's
 * plate has a second button, "Hold fire", because not shooting is an act too.
 *
 * In the pack's room the plate sits at the left, because the wolves' chat has the right. On the
 * waiting room's ledge it is `inline`, in the ledge's row beside its notice ("Depart", "Lock").
 *
 * On a turn with a deadline the plate carries the countdown (the room has no clock): the time
 * left in digits before the act, and a thin bar along the plate's top edge that drains, red in
 * the last ten seconds. The bar eases between the container's ticks; arrived at, it is still.
 */
import { countLeft, countText, URGENT_MS } from '../countdown';
import styles from './NightRoom.module.css';

export interface ActPlateProps {
  /** What the plate says: the act and its seat, or the ask before a choice. */
  label: string;
  onConfirm?: () => void;
  /** Nothing chosen yet, or already sent. */
  disabled?: boolean;
  /** A second act beside it (the vigilante's "Hold fire"). */
  secondary?: { label: string; onClick?: () => void; disabled?: boolean };
  /** Centred on the stage, or at the room's left edge in units (the pack). */
  left?: number;
  /** Centred on this x in units instead (the shelf room: the room left of an open side slot). */
  centre?: number;
  /** The turn's real time left; null or absent = no deadline, no count. */
  clock?: { remainingMs: number; totalMs: number } | null;
  /** Placed by its parent's layout instead (the waiting room's ledge). */
  inline?: boolean;
}

export function ActPlate({
  label,
  onConfirm,
  disabled,
  secondary,
  left,
  centre,
  clock,
  inline,
}: ActPlateProps) {
  const place = inline ? styles.inline : left == null ? '' : styles.left;
  const f = countLeft(clock);
  const urgent = clock != null && f !== null && clock.remainingMs <= URGENT_MS;
  const x = left ?? centre;
  return (
    <div
      className={place ? `${styles.plate} ${place}` : styles.plate}
      style={x == null ? undefined : { left: x }}
      data-plate={label}
    >
      {clock && f !== null ? (
        <>
          <span
            className={styles.count}
            data-count={countText(clock.remainingMs)}
            data-urgent={urgent || undefined}
          >
            {countText(clock.remainingMs)}
          </span>
          <span className={styles.bar} data-urgent={urgent || undefined} aria-hidden="true">
            <i style={{ transform: `scaleX(${f.toFixed(4)})` }} />
          </span>
        </>
      ) : null}
      <button type="button" className={styles.pri} disabled={disabled} onClick={onConfirm}>
        {label}
      </button>
      {secondary ? (
        <button type="button" disabled={secondary.disabled} onClick={secondary.onClick}>
          {secondary.label}
        </button>
      ) : null}
    </div>
  );
}
