/**
 * The X-ray's one switch, Reveal (TopStrip's, on its own plaque at the strip's right): in a
 * file of its own, with no hooks, so a page outside the stage can show it too (`RevealSign`).
 * Its look is the strip's (TopStrip.module.css).
 */
import styles from './TopStrip.module.css';

export interface RevealProps {
  on: boolean;
  onPress?: () => void;
  locked?: boolean;
}

/**
 * The Reveal switch: a brass escutcheon with a keyhole cut through it, riding a dark slot, and
 * the word. Off, it sits at the slot's left, the keyhole dark; on, it has slid right and the
 * keyhole glows verdigris. A switch, not a third tab: its own plaque, and it never reads as a
 * pane. Without `onPress` it cannot be pressed: locked (live, until the game ends), or on.
 */
export function Reveal({ on, onPress, locked = false }: RevealProps) {
  return (
    <button
      type="button"
      className={styles.reveal}
      aria-pressed={on}
      aria-label="Reveal"
      data-reveal={locked ? 'locked' : on ? 'on' : 'off'}
      disabled={!onPress}
      title={
        locked
          ? 'Revealed after the game'
          : !onPress
            ? 'Revealed: the game is over'
            : on
              ? 'Hide the roles and the thinking'
              : 'Reveal the roles and the thinking'
      }
      onClick={onPress}
    >
      <span className={styles.slot} aria-hidden="true">
        <span className={styles.knob}>
          <svg viewBox="0 0 16 16">
            <path
              className={styles.hole}
              d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z"
            />
            {/* the light behind the keyhole: faded in, never a colour change */}
            <path
              className={styles.lit}
              d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z"
            />
          </svg>
        </span>
      </span>
      <span className={styles.word}>{on && !locked ? 'Revealed' : 'Reveal'}</span>
    </button>
  );
}
