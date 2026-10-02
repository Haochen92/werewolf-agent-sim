/**
 * The replay's transport, along the foot of the stage (bench 73's band, beat sheet §11): the
 * five buttons (previous chapter, back a beat, play or pause, forward a beat, next chapter),
 * the seek bar with a mark per chapter, where we are in words ("Vote 3 · A chip is counted"),
 * and the speed as one toggle (Normal or Fast) (owner, 2026-09-29: three speeds and a count did
 * not fit a small phone on its side). The X-ray's switch, Reveal, is the top strip's now.
 *
 * It only draws and reports presses; the replay theatre holds the state. It sits in the HUD,
 * in stage units, so it shrinks with the picture on a small screen like everything else. When
 * the transcript drawer runs to the foot of the stage, the band stops short of it.
 */
import type { MouseEvent } from 'react';
import { Layer } from '../Stage';
import { chapterMarks } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import type { MotionSpeed } from '../scenes/types';
import { bandFoot, geometry, type Hud } from '../units';
import styles from './TransportBand.module.css';

export interface TransportBandProps {
  hud: Hud;
  beats: readonly SceneBeat[];
  index: number;
  playing: boolean;
  speed: MotionSpeed;
  /** "Vote 3 · A chip is counted" (transportLabel). */
  label: string;
  /** The drawer is open at full height: the band ends at its edge. */
  besideDrawer: boolean;
  onChapter: (dir: 1 | -1) => void;
  onStep: (dir: 1 | -1) => void;
  onTogglePlay: () => void;
  onSeek: (index: number) => void;
  onSpeed: (speed: MotionSpeed) => void;
}

// bench 73's glyphs, drawn in a 16×16 box; pause is ours (the bench only drew play)
const ICON = {
  prevChapter: 'M4 3h2v10H4zm3 5 8-5v10z',
  back: 'M11 3 3 8l8 5z',
  play: 'M5 3l9 5-9 5z',
  pause: 'M4 3h3v10H4zm5 0h3v10H9z',
  forward: 'M5 3l8 5-8 5z',
  nextChapter: 'M10 3h2v10h-2zM1 3l8 5-8 5z',
};

function Glyph({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden>
      <path d={d} />
    </svg>
  );
}

const CHAPTER_NAME = { day: 'Day', vote: 'Vote', night: 'Night', morning: 'Morning' };

function chapterName(beat: SceneBeat): string {
  const c = beat.chapter;
  if (!c) return '';
  return c.kind === 'over' ? 'Game over' : `${CHAPTER_NAME[c.kind]} ${c.n}`;
}

export function TransportBand({
  hud,
  beats,
  index,
  playing,
  speed,
  label,
  besideDrawer,
  onChapter,
  onStep,
  onTogglePlay,
  onSeek,
  onSpeed,
}: TransportBandProps) {
  const fast = speed === 'fast';
  const g = geometry(hud, besideDrawer);
  const last = Math.max(1, beats.length - 1);
  const at = (i: number) => `${(i / last) * 100}%`;

  // a click lands on the nearest beat; the bar is the whole log, one step per beat
  const seek = (e: MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (r.width <= 0) return;
    onSeek(Math.round(((e.clientX - r.left) / r.width) * last));
  };

  return (
    <Layer name="hud">
      <div
        className={styles.band}
        data-transport
        style={{
          height: bandFoot(hud, 0),
          left: g.wingN + 22.4,
          right: besideDrawer ? g.slotW + 12.8 : 22.4,
        }}
      >
        <div className={styles.buttons}>
          <button type="button" aria-label="Previous chapter" onClick={() => onChapter(-1)}>
            <Glyph d={ICON.prevChapter} />
          </button>
          <button type="button" aria-label="Back a beat" onClick={() => onStep(-1)}>
            <Glyph d={ICON.back} />
          </button>
          <button
            type="button"
            aria-label={playing ? 'Pause' : 'Play'}
            aria-pressed={playing}
            onClick={onTogglePlay}
          >
            <Glyph d={playing ? ICON.pause : ICON.play} />
          </button>
          <button type="button" aria-label="Forward a beat" onClick={() => onStep(1)}>
            <Glyph d={ICON.forward} />
          </button>
          <button type="button" aria-label="Next chapter" onClick={() => onChapter(1)}>
            <Glyph d={ICON.nextChapter} />
          </button>
        </div>

        <div className={styles.where}>
          <div className={styles.caption}>
            <span className={styles.label}>{label}</span>
          </div>
          <div
            className={styles.seek}
            role="slider"
            aria-label="Seek"
            aria-valuemin={1}
            aria-valuemax={beats.length}
            aria-valuenow={index + 1}
            aria-valuetext={label}
            onClick={seek}
          >
            <div className={styles.track}>
              <i style={{ width: at(index) }} />
              {chapterMarks(beats).map(({ index: i, beat }) => (
                <b
                  key={i}
                  className={i <= index ? styles.passed : undefined}
                  style={{ left: at(i) }}
                  title={chapterName(beat)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* one toggle: it says the speed it plays at, and a press switches to the other */}
        <button
          type="button"
          className={styles.speed}
          data-speed={speed}
          title={fast ? 'Playing fast: tap for normal speed' : 'Tap to play fast'}
          onClick={() => onSpeed(fast ? 'normal' : 'fast')}
        >
          {fast ? 'Fast' : 'Normal'}
        </button>
      </div>
    </Layer>
  );
}
