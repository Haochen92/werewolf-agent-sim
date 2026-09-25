/**
 * The brass plate at the foot of the night room: it names the act ("Protect seat 1", "Check
 * seat 4", "Shoot seat 2", "Kill seat 5") once a doll is chosen, and pressing it confirms.
 * Before a choice it asks ("Choose a seat to protect") and cannot be pressed. The vigilante's
 * plate has a second button, "Hold fire", because not shooting is an act too.
 *
 * In the pack's room the plate sits at the left, because the wolves' chat has the right.
 */
import styles from './NightRoom.module.css';

export interface ActPlateProps {
  /** What the plate says: the act and its seat, or the ask before a choice. */
  label: string;
  onConfirm?: () => void;
  /** Nothing chosen yet, or already sent. */
  disabled?: boolean;
  /** A second act beside it (the vigilante's "Hold fire"). */
  secondary?: { label: string; onClick?: () => void; disabled?: boolean };
  /** Centred on the stage (the shelf room), or at the room's left edge in units (the pack). */
  left?: number;
}

export function ActPlate({ label, onConfirm, disabled, secondary, left }: ActPlateProps) {
  return (
    <div
      className={left == null ? styles.plate : `${styles.plate} ${styles.left}`}
      style={left == null ? undefined : { left }}
      data-plate={label}
    >
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
