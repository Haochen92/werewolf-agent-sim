/**
 * The brass plate at the foot of the night room: it names the act ("Protect seat 1", "Check
 * seat 4", "Shoot seat 2", "Kill seat 5") once a photo is chosen, and pressing it confirms.
 * Before a choice it asks ("Choose a seat to protect") and cannot be pressed. The vigilante's
 * plate has a second button, "Hold fire", because not shooting is an act too.
 *
 * In the pack's room the plate sits at the left, because the wolves' chat has the right. On the
 * waiting room's ledge it is `inline`, in the ledge's row beside its notice ("Depart", "Lock").
 *
 * On a turn with a deadline the plate carries the countdown (the room has no clock): the time
 * left in digits before the act, and a thin bar along the plate's top edge that drains, red in
 * the last ten seconds. The bar eases between the count's ticks; arrived at, it is still. Only
 * the count and the bar tick (`PlateCount`), not the plate, nor the room around it.
 *
 * Pressing it is the commit: the server takes one answer per seat and refuses a second. So
 * once a photo is chosen a quiet line over it says the choice can still change, and once the
 * act is in the plate is `sealed`: a label saying what was done, with nothing left to press.
 * A send that failed says why in that line, and the plate can be pressed again.
 */
import { useTimeLeft } from '@/hooks/useCountdown';
import { countLeft, countText, URGENT_MS, type TurnClock } from '../countdown';
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
  clock?: TurnClock | null;
  /** Placed by its parent's layout instead (the waiting room's ledge). */
  inline?: boolean;
  /** A quiet line over the plate ("tap another photo to change"). */
  note?: string;
  /** What went wrong with the last press, over the plate in place of the note. */
  error?: string | null;
  /** The act is in: the plate is this label, sealed in the acting side's colour. */
  sealed?: { label: string; colour: string } | null;
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
  note,
  error,
  sealed,
}: ActPlateProps) {
  const place = inline ? styles.inline : left == null ? '' : styles.left;
  const x = left ?? centre;
  if (sealed)
    return (
      <div
        className={place ? `${styles.plate} ${place}` : styles.plate}
        style={x == null ? undefined : { left: x }}
        data-plate={sealed.label}
        data-sealed
      >
        {error ? (
          <p className={`${styles.note} ${styles.noteError}`} role="alert">
            {error}
          </p>
        ) : null}
        <p className={styles.sealed} role="status">
          <i style={{ background: sealed.colour }} aria-hidden="true" />
          {sealed.label}
        </p>
      </div>
    );
  return (
    <div
      className={place ? `${styles.plate} ${place}` : styles.plate}
      style={x == null ? undefined : { left: x }}
      data-plate={label}
    >
      {error ? (
        <p className={`${styles.note} ${styles.noteError}`} role="alert">
          {error}
        </p>
      ) : note ? (
        <p className={styles.note}>{note}</p>
      ) : null}
      {clock ? <PlateCount clock={clock} /> : null}
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

/** The plate's count and its draining bar, ticking on their own. */
function PlateCount({ clock }: { clock: TurnClock }) {
  const remainingMs = useTimeLeft(clock.deadline, clock.at);
  const f = countLeft(clock, remainingMs);
  if (remainingMs === null || f === null) return null;
  const urgent = remainingMs <= URGENT_MS;
  return (
    <>
      <span
        className={styles.count}
        data-count={countText(remainingMs)}
        data-urgent={urgent || undefined}
      >
        {countText(remainingMs)}
      </span>
      <span className={styles.bar} data-urgent={urgent || undefined} aria-hidden="true">
        <i style={{ transform: `scaleX(${f.toFixed(4)})` }} />
      </span>
    </>
  );
}
