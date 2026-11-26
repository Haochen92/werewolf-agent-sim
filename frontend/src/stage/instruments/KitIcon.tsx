/**
 * The HUD's small icons, before a button's words (owner, 2026-10-19): one look for every input,
 * the icon saying what kind of press it is. Drawn in the button's ink (`currentColor`), an em
 * across, so they size with the words.
 */
import styles from './KitIcon.module.css';

export type KitIconName = 'send' | 'pass' | 'agent' | 'file' | 'transcript';

const PATHS: Record<KitIconName, string> = {
  // a paper plane
  send: 'M2.5 20.5 21.5 12 2.5 3.5v6.6l13 1.9-13 1.9z',
  // skip ahead
  pass: 'M4 5.5 11.5 12 4 18.5zM12.5 5.5 20 12l-7.5 6.5z',
  // the agent's spark
  agent: 'M12 2.5l2.4 7.1 7.1 2.4-7.1 2.4L12 21.5l-2.4-7.1L2.5 12l7.1-2.4z',
  // a folder
  file: 'M2.5 6A1.5 1.5 0 0 1 4 4.5h5.2l2 2H20A1.5 1.5 0 0 1 21.5 8v10.5A1.5 1.5 0 0 1 20 20H4a1.5 1.5 0 0 1-1.5-1.5z',
  // a page of lines
  transcript: 'M5.5 2.5h9l4 4v15h-13zM8.5 10h7v1.6h-7zm0 3.6h7v1.6h-7zm0 3.6h4.5v1.6H8.5z',
};

export function KitIcon({ name }: { name: KitIconName }) {
  return (
    <svg className={styles.icon} viewBox="0 0 24 24" aria-hidden="true">
      <path d={PATHS[name]} fillRule="evenodd" />
    </svg>
  );
}
