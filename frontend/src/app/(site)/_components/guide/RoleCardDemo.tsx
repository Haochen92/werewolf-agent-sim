'use client';

/**
 * Your role card, working, in the guide (owner, 2026-10-16): the live game's own pieces on a
 * stage of their own. By day the card is the button at the foot of the stage; at night it
 * stands framed on your table; either opens the same full card, with what you do at night and
 * the uses you have left. The sigilist, so the uses line shows.
 */
import { useState, type CSSProperties } from 'react';
import { Stage } from '@/stage/Stage';
import { stageFonts } from '@/stage/fonts';
import { CardOverlay, FramedCard } from '@/stage/instruments/FramedCard';
import { CardButton } from '@/stage/instruments/Notice';
import { usesNote } from '@/stage/scenes/ShelfRoomScene';
import { geometry } from '@/stage/units';
import { useTabs } from './useTabs';
import classes from './Guide.module.css';
import own from './RoleCardDemo.module.css';

const ROLE = 'sigilist';
const SEAT = 4;
const NOTE = usesNote(ROLE, 2);

/** In world units: the crop, as tall as the opened card (taller on a phone, where the card is drawn larger). */
const CROP = { w: 760, h: 700, smallW: 760, smallH: 1100 };
/** The framed card on the night table, in world units (the night room's is 200 tall). */
const FRAMED_H = 400;

export function RoleCardDemo() {
  const t = useTabs(['day', 'night'] as const);
  // the card opened, by the side of the switch it was opened on: switching closes it
  const [opened, setOpened] = useState<'day' | 'night' | null>(null);
  const open = opened === t.at;
  const u = geometry('live').u;
  const crop = {
    '--crop-w': CROP.w,
    '--crop-h': CROP.h,
    '--crop-small-w': CROP.smallW,
    '--crop-small-h': CROP.smallH,
  } as CSSProperties;
  return (
    <div className={own.demo}>
      <div className={own.switch} role="tablist" aria-label="Day or night">
        <button {...t.tab('day')}>Day</button>
        <button {...t.tab('night')}>Night</button>
      </div>
      <div className={`${classes.demo} ${stageFonts}`} style={crop}>
        <div className={classes.demoCrop}>
          <div className={classes.demoWorld}>
            <Stage
              paint={<div className={classes.demoGround} />}
              hud={
                <div className={`${classes.demoBox} ${own.box}`} data-role-demo={t.at}>
                  {t.at === 'day' ? (
                    <div className={own.foot}>
                      <CardButton role={ROLE} onOpen={() => setOpened(t.at)} />
                    </div>
                  ) : (
                    <FramedCard
                      role={ROLE}
                      x={CROP.w / 2}
                      foot={CROP.h * 0.82}
                      height={FRAMED_H}
                      u={u * 0.95 * (FRAMED_H / 279)}
                      note={NOTE}
                      onOpen={() => setOpened(t.at)}
                    />
                  )}
                  {open ? (
                    <CardOverlay
                      role={ROLE}
                      seat={SEAT}
                      u={u * 1.6}
                      note={NOTE}
                      onClose={() => setOpened(null)}
                    />
                  ) : null}
                </div>
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}
