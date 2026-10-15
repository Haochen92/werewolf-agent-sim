'use client';

/**
 * The seat cards, working, in the guide: one of the live game's own cards (`Wing`), wide, on a
 * stage of its own, its notes pinned open beside it (owner, 2026-10-14: the card and its notes,
 * no room, no empty bars, on a phone too). The rail lays its card out to the box it stands in,
 * and the notes centre on the same box; the frame is cropped to the two.
 * Its notebook is a game of its own (`notes_guide` on this device), so what a reader writes here
 * stays here, as a player's notes do.
 */
import type { CSSProperties } from 'react';
import { CHARACTERS } from '@/assets/manifest';
import { Stage } from '@/stage/Stage';
import { stageFonts } from '@/stage/fonts';
import { Wing, type WingTileProps } from '@/stage/instruments/Wing';
import classes from './Guide.module.css';

const TILES: WingTileProps[] = [{ seat: 2, character: CHARACTERS[1] }];

/** The ten-seat cast, one of each role: what the guess offers. */
const CAST: Record<string, number> = {
  investigator: 1,
  sentinel: 1,
  trailseer: 1,
  vigilante: 1,
  sigilist: 1,
  healer: 1,
  chanteuse: 1,
  illusionist: 1,
  serial_killer: 1,
  fortune_teller: 1,
};

/**
 * In world units: the rail's width, and the crop (the card and its notes). Drawn small (a crop
 * under 0.75 of its width in css px) the stage's type grows, and the notes with it, so the small
 * crop is larger.
 */
const RAIL_W = 300;
const CROP = { w: 730, h: 480, smallW: 850, smallH: 640 };
/** The writing paper's height, in the note's lines: the notes about 3/4 of the card's height. */
const PAPER = { wide: '12em', small: '9.5em' };

export function SeatCardsDemo() {
  const crop = {
    '--crop-w': CROP.w,
    '--crop-h': CROP.h,
    '--crop-small-w': CROP.smallW,
    '--crop-small-h': CROP.smallH,
    '--paper-h': PAPER.wide,
    '--paper-small-h': PAPER.small,
  } as CSSProperties;
  return (
    <div className={`${classes.demo} ${stageFonts}`} style={crop}>
      <div className={classes.demoCrop}>
        <div className={classes.demoWorld}>
          <Stage
            paint={<div className={classes.demoGround} />}
            hud={
              <div className={classes.demoBox}>
                <Wing
                  width={RAIL_W}
                  tiles={TILES}
                  notes="guide"
                  castCounts={CAST}
                  pinned={2}
                />
              </div>
            }
          />
        </div>
      </div>
    </div>
  );
}
