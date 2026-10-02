'use client';

/**
 * A scene's baked backdrop: the car's paint and haze as one picture (`src/assets/sets`, made by
 * `scripts/bake-sets.mjs` from the bake bench), where the live scene drew five sheets. Same
 * drawing; one bitmap for the browser to hold instead of a stack of full-stage layers, which is
 * what a phone's memory cap catches (build log §8.3).
 *
 * The picture covers the world and the bleed (2200×900 units) and comes at 1×, 1.5× and 2×.
 * Which one is picked by the screen: its pixel density, capped at 2 on a desktop and at 1.5 on
 * a phone, where a 2× sheet would decode to 32 MB for a 900 px wide stage. The server renders
 * 1× and the browser upgrades once it knows its screen, so a golden at 1× is exact.
 *
 * Played from another hour (`from`), the old hour's picture fades off over the new one, as the
 * car's live paint did.
 */
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { motion } from 'motion/react';
import { SETS, type SetScale } from '@/assets/sets';
import { useMotionScale } from '../motion';
import type { Phase } from '../paint/materials';
import { NARROW_PX } from '../screen';
import { BLEED, STAGE_H, STAGE_W, type Hud } from '../units';

const SCALES: readonly SetScale[] = ['1', '1.5', '2'];

/** The sheet for this screen: the smallest at or above its density, within the cap. */
export function pickScale(dpr: number, cap: number): SetScale {
  const want = Math.min(dpr, cap);
  return SCALES.find((s) => Number(s) >= want) ?? SCALES[SCALES.length - 1];
}

/** The sheet for this screen, and whether the screen is a phone's (a narrow window). */
function useScreen(): { scale: SetScale; narrow: boolean } {
  const [screen, setScreen] = useState<{ scale: SetScale; narrow: boolean }>({
    scale: '1',
    narrow: false,
  });
  useEffect(() => {
    const narrow = window.innerWidth < NARROW_PX;
    setScreen({ scale: pickScale(window.devicePixelRatio || 1, narrow ? 1.5 : 2), narrow });
  }, []);
  return screen;
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
  const k = useMotionScale();
  const { scale, narrow } = useScreen();
  const cut = useCut(narrow ? from : null, phase, fadeDelay * k);
  // the bench's "no HUD" draws the car as the live HUD does (geometry(hud) treats them alike)
  const h = hud === 'replay' ? 'replay' : 'live';
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
