'use client';

/**
 * The music's one switch: a speaker, with its waves when the music is on and struck through when
 * it is off. The choice is the viewer's and kept on this device. On a stage the music is on
 * until they turn it off; on the guide (`optIn`) it is off until they turn it on. A browser
 * starts sound only after a press on the page, so before one the label says so.
 */
import type { ReactNode } from 'react';
import { musicOn, useMusicState } from './music';

export function SoundButton({
  optIn = false,
  className,
  children,
}: {
  optIn?: boolean;
  className?: string;
  /** A word beside the speaker (the guide's); the stage's is the speaker alone. */
  children?: ReactNode;
}) {
  const pref = useMusicState((s) => s.pref);
  const pressed = useMusicState((s) => s.pressed);
  const choose = useMusicState((s) => s.choose);
  const on = musicOn(pref, optIn);
  const label = !on
    ? 'Music off'
    : pressed
      ? 'Music on'
      : 'Music on: it starts at your first tap';
  return (
    <button
      type="button"
      className={className}
      aria-pressed={on}
      aria-label={children ? undefined : label}
      title={label}
      onClick={() => choose(on ? 'off' : 'on')}
    >
      <SpeakerGlyph on={on} />
      {children}
    </button>
  );
}

function SpeakerGlyph({ on }: { on: boolean }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth={1.2}
        strokeLinejoin="round"
      />
      {on ? (
        <path
          d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.8 7.8 0 0 1 0 11"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.6}
          strokeLinecap="round"
        />
      ) : (
        <path
          d="M16 9.5l5 5m0-5-5 5"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.6}
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}
