'use client';

/**
 * Your role card in the guide (owner, 2026-10-16): your night room, with the game's own card
 * standing on its table; select it and it opens full size, as in the game, with what you do at
 * night and the uses left (the sigilist's room and card, so the uses line shows). The room is
 * one picture baked from the game's (`scripts/bake-guide-room.mjs`): its painting, the night
 * behind the glass and the candle's light, for 34 KB and about 4 MB decoded, where the room as
 * the game draws it is three pictures and about 12 MB. Nothing is drawn until its tab is first
 * shown, and the box has its size before then, so the page does not move (lesson 27).
 */
import { useState, type CSSProperties } from 'react';
import Image from 'next/image';
import room from '@/assets/site/guide/sigilist-room.webp';
import { Stage } from '@/stage/Stage';
import { stageFonts } from '@/stage/fonts';
import { CardOverlay, FramedCard } from '@/stage/instruments/FramedCard';
import { usesNote } from '@/stage/scenes/ShelfRoomScene';
import { geometry } from '@/stage/units';
import classes from './Guide.module.css';
import own from './RoleCardDemo.module.css';

const ROLE = 'sigilist';
const SEAT = 4;
const NOTE = usesNote(ROLE, 2);

/** In stage units, the baked crop of the room (the bake script's `CROP`). */
const CROP = { x: 880, y: 120, w: 680, h: 700 };
/** Where the room plan stands the card in this room (`roomPlan` card, the replay's stage). */
const CARD = { x: 1116.7 - CROP.x, foot: 578.8 - CROP.y, h: 200 };

export function RoleCardDemo({ shown }: { shown: boolean }) {
  // drawn from the first time its tab is shown, then kept
  const [ever, setEver] = useState(shown);
  if (shown && !ever) setEver(true);
  const [open, setOpen] = useState(false);
  const u = geometry('replay').u;
  const crop = {
    '--crop-w': CROP.w,
    '--crop-h': CROP.h,
    '--crop-small-w': CROP.w,
    '--crop-small-h': CROP.h,
  } as CSSProperties;
  return (
    <div className={`${classes.demo} ${stageFonts}`} style={crop} data-role-demo>
      <div className={`${classes.demoCrop} ${own.crop}`}>
        <div className={classes.demoWorld}>
          {ever ? (
            <Stage
              paint={
                <Image
                  src={room}
                  alt=""
                  unoptimized
                  draggable={false}
                  className={own.room}
                />
              }
              hud={
                <div className={`${classes.demoBox} ${own.box}`}>
                  <FramedCard
                    role={ROLE}
                    x={CARD.x}
                    foot={CARD.foot}
                    height={CARD.h}
                    u={u * 0.95 * (CARD.h / 279)}
                    note={NOTE}
                    onOpen={() => setOpen(true)}
                  />
                  {open ? (
                    <CardOverlay
                      role={ROLE}
                      seat={SEAT}
                      u={u * 1.6}
                      note={NOTE}
                      onClose={() => setOpen(false)}
                    />
                  ) : null}
                </div>
              }
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
