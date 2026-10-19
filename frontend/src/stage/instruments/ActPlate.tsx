/**
 * The brass plate at the foot of the night room: it names the act ("Protect seat 1", "Check
 * seat 4", "Shoot seat 2", "Kill seat 5") once a photo is chosen, and pressing it confirms.
 * Before a choice it asks ("Choose a seat to protect") and cannot be pressed; without a `label`
 * (the speculator's, whose sides hang on the line) it has no act until one is chosen. A request that
 * lists a no-action word has a second button in its words ("Hold fire", "Keep your checks",
 * "Stay put"), because not acting is an act too. A live turn ends the row with the hand-over,
 * in the same dress: "Let my agent choose".
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
import type { CSSProperties, ReactNode } from 'react';
import { useTimeLeft } from '@/hooks/useCountdown';
import { countLeft, countText, URGENT_MS, type TurnClock } from '../countdown';
import { KitIcon } from './KitIcon';
import styles from './NightRoom.module.css';

export interface ActPlateProps {
  /** What the plate says: the act and its seat, or the ask before a choice; null = no act yet. */
  label: string | null;
  onConfirm?: () => void;
  /** Nothing chosen yet, or already sent. */
  disabled?: boolean;
  /** A second act beside it (the request's no-action word: "Hold fire", "Keep your checks"). */
  secondary?: { label: string; onClick?: () => void; disabled?: boolean };
  /** The hand-over, last in the row in the second act's dress ("Let my agent choose"). */
  agent?: { label: string; onClick?: () => void; disabled?: boolean };
  /** Centred on the stage, or at the room's left edge in units (the pack). */
  left?: number;
  /** Centred on this x in units instead (the shelf room: the room left of an open side slot). */
  centre?: number;
  /** The room's width in units: a row wider than it wraps, the hand-over going under. */
  maxWidth?: number;
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
  /** Not drawn, and still mounted (`Presentation.footHidden`: the "You're back" notice stands here). */
  hidden?: boolean;
  /**
   * A row to choose from over the plate (`ChoicePlates`), hung from the plate's top so a plate
   * wrapped onto two rows (a phone beside the open transcript) lifts it rather than covers it.
   */
  over?: ReactNode;
}

export function ActPlate({
  label,
  onConfirm,
  disabled,
  secondary,
  agent,
  left,
  centre,
  maxWidth,
  clock,
  inline,
  note,
  error,
  sealed,
  hidden = false,
  over,
}: ActPlateProps) {
  const place = inline ? styles.inline : left == null ? '' : styles.left;
  const x = left ?? centre;
  const style: CSSProperties = {
    left: x,
    maxWidth,
    visibility: hidden ? 'hidden' : undefined,
  };
  if (sealed)
    return (
      <div
        className={place ? `${styles.plate} ${place}` : styles.plate}
        style={style}
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
      style={style}
      data-plate={label ?? undefined}
    >
      {over}
      {error ? (
        <p className={`${styles.note} ${styles.noteError}`} role="alert">
          {error}
        </p>
      ) : note ? (
        <p className={styles.note}>{note}</p>
      ) : null}
      {clock ? <PlateCount clock={clock} /> : null}
      {label !== null ? (
        <button
          type="button"
          className={styles.pri}
          disabled={disabled}
          onClick={onConfirm}
        >
          {label}
        </button>
      ) : null}
      {secondary ? (
        <button type="button" disabled={secondary.disabled} onClick={secondary.onClick}>
          <KitIcon name="pass" />
          {secondary.label}
        </button>
      ) : null}
      {agent ? (
        <button type="button" disabled={agent.disabled} onClick={agent.onClick}>
          <KitIcon name="agent" />
          {agent.label}
        </button>
      ) : null}
    </div>
  );
}

/** One plate in a `ChoicePlates` row: its word (or a sigil), and whether it is the chosen one. */
export interface PlateChoice {
  id: string;
  label: ReactNode;
  /** Its name in words, when the label is a picture (a role's sigil). */
  title?: string;
  on: boolean;
}

/**
 * A row of plates to choose from, over the plate (ten-seat pass §2): the fortune teller's roles
 * (as sigils, `sigils`). Tapping one lights it, tapping it again puts it out; the gold plate
 * under it still commits. A small sibling of the plate, in its style, handed to the plate as
 * its `over` and hung from its top edge.
 */
export function ChoicePlates({
  choices,
  onToggle,
  caption,
  sigils,
  disabled,
}: {
  choices: readonly PlateChoice[];
  onToggle: (id: string) => void;
  /** A quiet line over the row ("name a role for two points"). */
  caption?: string;
  /** The labels are pictures: square plates. */
  sigils?: boolean;
  disabled?: boolean;
}) {
  return (
    <div className={styles.choices} role="group" aria-label={caption}>
      {caption ? <p className={styles.choicesCaption}>{caption}</p> : null}
      <div className={styles.choicesRow}>
        {choices.map((c) => (
          <button
            key={c.id}
            type="button"
            className={sigils ? styles.sigil : undefined}
            data-choice={c.id}
            aria-pressed={c.on}
            aria-label={c.title}
            title={c.title}
            disabled={disabled}
            onClick={() => onToggle(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>
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
