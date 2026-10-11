'use client';

/**
 * A scene's baked backdrop: the car's paint and haze as one picture (`src/assets/sets`, made by
 * `scripts/bake-sets.mjs` from the bake bench), where the live scene drew five sheets. Same
 * drawing; one bitmap for the browser to hold instead of a stack of full-stage layers, which is
 * what a phone's memory cap catches (build log §8.3).
 *
 * The picture covers the world and the bleed (2200×900 units) and comes at 1×, 1.5× and 2×
 * (2200, 3300 and 4400 pixels wide). Which one is picked by the pixels the stage is actually
 * drawn at (`pickScale`): its measured width times the screen's density times the camera's
 * closest push-in, so the landing's small carriage on a phone takes the 1× sheet where a
 * landscape theatre on the same phone takes the 1.5×. A small stage stays capped at 1.5, where
 * a 2× sheet would decode to 32 MB. No sheet is drawn until the Stage has measured itself, so
 * a page never asks for one sheet and then another for the same screen; a golden at 1× is
 * exact.
 *
 * Played from another hour (`from`), the old hour's picture fades off over the new one, as the
 * car's live paint did.
 *
 * A scene mounts `Backdrop`, which only describes the sheet to the Stage (set.ts); the Stage
 * draws `BackdropSheet` once, at the foot of the paint layer, and keeps it across the scene's
 * beats and from one scene to the next. The picture's `<img>` is therefore never remounted by
 * a beat, which on iPhone Safari showed the house's dark for a frame while a fresh image
 * decoded, every beat of a scene keyed whole (build log §8.8). A change of hour changes only the
 * `src`, and the browser keeps the old picture until the new one is ready.
 */
import { useContext, useEffect, useLayoutEffect, useState } from 'react';
import Image from 'next/image';
import { motion } from 'motion/react';
import { SETS, type SetScale } from '@/assets/sets';
import { useMotionScale } from '../motion';
import { BackdropContext, useSmall, useStageWidth, type BackdropSpec } from '../set';
import type { Phase } from '../paint/materials';
import { BLEED, CAMERA_ZOOM_MAX, STAGE_H, STAGE_W, type Hud } from '../units';

const SCALES: readonly SetScale[] = ['1', '1.5', '2'];
/** The 1× sheet's width in pixels: one pixel per unit across the world and both bleeds. */
const SHEET_W = STAGE_W + 2 * BLEED;
/** How far under a smaller sheet's size the need must fall before the sheet is traded down. */
const SLACK = 0.1;

/**
 * The sheet for a stage drawn `stageW` css px wide on a screen of density `dpr`: the smallest
 * whose width in pixels is at least the stage's width in physical pixels at the camera's
 * closest (`stageW × dpr × CAMERA_ZOOM_MAX`), within `cap`. Given the sheet already shown
 * (`prev`), a larger one is kept until the need is `SLACK` under the smaller one's size, so a
 * stage resized back and forth across a boundary does not trade sheets on every pixel.
 */
export function pickScale(
  stageW: number,
  dpr: number,
  cap: number,
  prev?: SetScale,
): SetScale {
  const want = Math.min((stageW * dpr * CAMERA_ZOOM_MAX) / SHEET_W, cap);
  const fresh = SCALES.find((s) => Number(s) >= want) ?? SCALES[SCALES.length - 1];
  const keep =
    prev !== undefined &&
    Number(prev) > Number(fresh) &&
    Number(prev) <= cap &&
    want > Number(fresh) * (1 - SLACK);
  return keep ? prev : fresh;
}

/**
 * The sheet for this stage (null until the Stage has measured it), and whether the stage is
 * drawn small (a phone's: `useSmall`). The pick is made in render from the measured width, so
 * the first sheet asked for is already the right one; the last pick is kept in state for
 * `pickScale`'s slack.
 */
function useScreen(): { scale: SetScale | null; narrow: boolean } {
  const narrow = useSmall();
  const width = useStageWidth();
  const [shown, setShown] = useState<SetScale | null>(null);
  const scale =
    width > 0
      ? pickScale(width, window.devicePixelRatio || 1, narrow ? 1.5 : 2, shown ?? undefined)
      : shown;
  if (scale !== shown) setShown(scale);
  return { scale, narrow };
}

/**
 * The hour's change on a phone: a cut at the fade's start instead of a crossfade. Two sheets
 * and a full-stage fading layer at once is the heaviest moment on the stage, and it falls on
 * "the day begins", together with the shutter's and the stand's rise; a phone's cap caught
 * exactly that beat (build log §8.3). The shutter is rising over the window as it cuts.
 */
function useCut(from: Phase | null | undefined, phase: Phase, after: number): Phase {
  const [shown, setShown] = useState<Phase>(from && from !== phase ? from : phase);
  useEffect(() => {
    if (!from || from === phase) return setShown(phase);
    setShown(from);
    const t = setTimeout(() => setShown(phase), after * 1000);
    return () => clearTimeout(t);
  }, [from, phase, after]);
  return shown;
}

export function Backdrop({
  phase,
  hud,
  side = false,
  from,
  fadeDelay = 1.2,
}: {
  phase: Phase;
  hud: Hud;
  /** The side slot is open: the room is moved left. */
  side?: boolean;
  /** Played: the hour the car was at before this beat. */
  from?: Phase | null;
  fadeDelay?: number;
}) {
  const set = useContext(BackdropContext);
  const k = useMotionScale();
  // the description's JSON is its identity: a new-but-equal one changes nothing
  const key = JSON.stringify({ phase, hud, side, from: from ?? null, fadeDelay, k });
  useLayoutEffect(() => {
    if (!set) return;
    set(JSON.parse(key) as BackdropSpec);
    // the next description lands in the same commit as this one's clearing (the next beat's,
    // or the next scene's), so the Stage never draws the gap between them
    return () => set(null);
  }, [set, key]);
  return null;
}

/** The sheet itself, drawn by the Stage from the scene's description. */
export function BackdropSheet({ phase, hud, side, from, fadeDelay, k }: BackdropSpec) {
  const { scale, narrow } = useScreen();
  const cut = useCut(narrow ? from : null, phase, fadeDelay * k);
  // the bench's "no HUD" draws the car as the live HUD does (geometry(hud) treats them alike)
  const h = hud === 'replay' ? 'replay' : 'live';
  if (!scale) return null;
  const at = (p: Phase) => SETS.car[p][h][side ? 'side' : 'full'][scale];
  const sheet = {
    position: 'absolute',
    top: 0,
    left: -BLEED,
    width: STAGE_W + 2 * BLEED,
    height: STAGE_H,
    display: 'block',
  } as const;
  return (
    <div
      data-backdrop={phase}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    >
      <Image
        src={at(narrow ? cut : phase)}
        alt=""
        unoptimized
        priority
        draggable={false}
        style={sheet}
      />
      {!narrow && from && from !== phase ? (
        <motion.div
          key={from}
          style={{ position: 'absolute', inset: 0 }}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ duration: 1.2 * k, delay: fadeDelay * k, ease: 'easeInOut' }}
        >
          <Image src={at(from)} alt="" unoptimized draggable={false} style={sheet} />
        </motion.div>
      ) : null}
    </div>
  );
}
