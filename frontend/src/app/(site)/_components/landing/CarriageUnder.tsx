'use client';

/**
 * The carriage's controls on a phone (redesign handoff 2026-10-14 §4): there the stage is a
 * quarter of its size, so its controls leave it for the platform under the carriage, at reading
 * size. One board: the play plate, the step's caption and the window's steps as a stretch of line
 * (a sleeper per step, brass rails behind you, a cream marker where you are; each sleeper seeks).
 *
 * The preview stops there on a phone (owner, 2026-10-14): the transcript and the Reveal pane did
 * not fit a phone's screen beside the carriage, and the Reveal pane drew a second stage. The
 * stage's own speech box carries the words; the transcript and Reveal are the whole replay's, a
 * tap away, and the gameplay guide explains them.
 */
import type { CSSProperties } from 'react';
import type { MiniUnder } from '@/stage/containers/ReplayTheatre';
import classes from './CarriageUnder.module.css';

export function CarriageUnder(u: MiniUnder) {
  const n = u.beats.length;
  // the marker and the rails behind it sit at the middle of the current step's sleeper
  const at = n ? `${((u.index + 0.5) / n) * 100}%` : '0%';
  return (
    <div className={classes.ctrl}>
      <button
        type="button"
        className={classes.play}
        aria-label={u.playing ? 'Pause' : 'Play'}
        aria-pressed={u.playing}
        onClick={u.onTogglePlay}
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d={u.playing ? 'M4 3h3v10H4zm5 0h3v10H9z' : 'M5 3l9 5-9 5z'} />
        </svg>
      </button>
      <div className={classes.ctrlText}>
        {/* the step's own name: the window already shows which day and vote this is */}
        <span className={classes.cap} title={u.label}>
          {u.beat.label}
        </span>
        <div
          className={classes.track}
          role="group"
          aria-label="Beats"
          style={{ '--at': at } as CSSProperties}
        >
          <span className={classes.done} aria-hidden="true" />
          <span className={classes.pos} aria-hidden="true" />
          {u.beats.map((b, i) => (
            <button
              key={i}
              type="button"
              aria-label={`Step ${i + 1} of ${n}: ${b.label}`}
              aria-current={i === u.index ? 'step' : undefined}
              onClick={() => u.onSeek(i)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
