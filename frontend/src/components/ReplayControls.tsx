'use client';

/**
 * The transport bar for a replay: play the log beat by beat, or show it all at once.
 *
 * Idle, it is one button, "play from start", and the theater behaves exactly as it did
 * before the player existed. Active, it is pause or resume, one beat forward, skip to the
 * next phase change, a speed, a progress count, and "show all" to leave. Text glyphs, no
 * icon font: the theater is set in a display face and these sit inside its scrubber row.
 */
import { SPEEDS, type ReplayPlayer, type Speed } from '@/hooks/useReplayPlayer';
import classes from './Theater.module.css';

export function ReplayControls({ player }: { player: ReplayPlayer }) {
  const { active, playing, atEnd, cursor, beats, speed } = player;

  if (!active) {
    return (
      <div className={classes.player}>
        <button
          type="button"
          className={classes.playButton}
          onClick={player.playFromStart}
          disabled={beats.length === 0}
        >
          ▶ Play from start
        </button>
        <span className={classes.playerHint}>
          reveals the game beat by beat, at reading pace
        </span>
      </div>
    );
  }

  return (
    <div className={classes.player} role="group" aria-label="Replay playback">
      <button
        type="button"
        className={classes.playButton}
        onClick={playing ? player.pause : player.play}
        aria-label={playing ? 'Pause' : 'Play'}
      >
        {playing ? '❚❚' : '▶'}
      </button>
      <button
        type="button"
        className={classes.arrowButton}
        onClick={player.step}
        disabled={atEnd}
        aria-label="Next beat"
        title="Next beat"
      >
        ▶|
      </button>
      <button
        type="button"
        className={classes.arrowButton}
        onClick={player.skipPhase}
        disabled={atEnd}
        aria-label="Skip to the next phase"
        title="Skip to the next phase"
      >
        ▶▶
      </button>
      <span className={classes.speeds} role="radiogroup" aria-label="Speed">
        {SPEEDS.map((option: Speed) => (
          <button
            key={option}
            type="button"
            className={`${classes.step} ${option === speed ? classes.stepActive : ''}`}
            onClick={() => player.setSpeed(option)}
            role="radio"
            aria-checked={option === speed}
          >
            {option}×
          </button>
        ))}
      </span>
      <span className={classes.playerProgress}>
        beat {cursor} / {beats.length}
      </span>
      <span className={classes.spacer} />
      <button type="button" className={classes.arrowButton} onClick={player.showAll}>
        show all
      </button>
    </div>
  );
}
