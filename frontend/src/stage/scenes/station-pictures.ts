'use client';

/**
 * The station's train at the density the stage is drawn at (frontend lesson 22): one pixel per
 * unit where that covers the screen's pixels, else the master as shipped (about 1.5). A desktop
 * at 1× and most 2× phones take the lighter copy. The platform's picture has one size.
 *
 * Upright, the stage stands behind the card that asks to turn the phone (OrientationGuard), at
 * the upright width; picked from that, a phone would take the light pair and then, turned, the
 * sharp one. So upright the pick is made for the stage the turned screen will draw. A pick is
 * traded up and never down: a lighter copy after a sharper one is a second download for nothing.
 */
import { useEffect, useState } from 'react';
import type { StaticImageData } from 'next/image';
import { SPRITES } from '@/assets/manifest';
import { useStageWidth } from '../set';
import { STAGE_W } from '../units';

type Density = 1 | 1.5;
type StationPictures = { train: StaticImageData };

const SHARP: StationPictures = { train: SPRITES.station.train };

/** The copy for a stage drawn `stageW` css px wide on a screen of density `dpr`. */
export function stationDensity(stageW: number, dpr: number): Density {
  return (stageW * dpr) / STAGE_W > 1 ? 1.5 : 1;
}

/** The stage's width once the phone is turned, if it is held upright (16:9, fit inside). */
function turnedWidth(stageW: number): number {
  const { innerWidth: w, innerHeight: h } = window;
  if (h <= w) return stageW;
  return Math.max(stageW, Math.min(h, (w * 16) / 9));
}

/** How long a departure waits for its pictures before it leaves without them. */
const READY_CAP_MS = 6000;

/**
 * Says once the train and the platform this stage draws are loaded and decoded (or after
 * `READY_CAP_MS`), so a departure never pulls out before its train is there: on a page opened
 * for the departure, a game for one's, the platform is new. Mounted inside the
 * Stage, beside the platform, for its measured pick.
 */
export function StationReady({ onReady }: { onReady: () => void }) {
  const { train } = useStationPictures();
  // the platform's two pictures as well (owner, 2026-10-19: the page comes up whole)
  const { platform, platformFront, beam } = SPRITES.station;
  useEffect(() => {
    let live = true;
    const done = () => {
      if (live) onReady();
    };
    const cap = setTimeout(done, READY_CAP_MS);
    void Promise.all(
      [train.src, platform.src, platformFront.src, beam.src].map((src) => {
        const img = new Image();
        img.src = src;
        return img.decode().catch(() => {});
      }),
    ).then(done);
    return () => {
      live = false;
      clearTimeout(cap);
    };
  }, [train.src, platform.src, platformFront.src, beam.src, onReady]);
  return null;
}

export function useStationPictures(): StationPictures {
  const width = useStageWidth();
  const [shown, setShown] = useState<Density | null>(null);
  const want =
    width > 0 ? stationDensity(turnedWidth(width), window.devicePixelRatio || 1) : null;
  const pick = want === null || (shown !== null && shown > want) ? shown : want;
  if (pick !== shown) setShown(pick);
  return pick === 1 ? SPRITES.stationAt1x : SHARP;
}
