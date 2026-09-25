'use client';

/**
 * The backdrop bench: the paint generators on their own, with no scene over them. The dining
 * car at each hour, the shelf room, the shutter open or closed, the replay's drape, under
 * each HUD mode, and guide lines for the frozen HUD geometry, to check the numbers against a
 * bench by eye. Every option is in the URL:
 *
 *   /workbench/paint?phase=day|dusk|night|dawn&room=car|shelf&shutter=open|closed
 *                   &drape=0|1&hud=none|live|replay&guides=0|1&chosen=0..7&strip=0
 */
import { Layer, Paint } from '@/stage/Stage';
import { diningCar, diningCarPlan } from '@/stage/paint/dining-car';
import { drape } from '@/stage/paint/drape';
import { light } from '@/stage/paint/light';
import { PHASES_IN_ORDER, type Phase } from '@/stage/paint/materials';
import { shelfLight, shelfRoom } from '@/stage/paint/shelf-room';
import { shutter, type ShutterState } from '@/stage/paint/window';
import { geometry, HUD_CHROME, sideSlot, STAGE_W, type Hud } from '@/stage/units';
import { Seg } from '@/stage/workbench/ControlStrip';
import { SPRITES } from '@/assets/manifest';

const pick = <T extends string>(v: string | null, all: readonly T[], dflt: T): T =>
  all.includes(v as T) ? (v as T) : dflt;

function readPaint(params: URLSearchParams) {
  const chosenRaw = params.get('chosen');
  return {
    phase: pick<Phase>(params.get('phase'), PHASES_IN_ORDER, 'day'),
    room: pick(params.get('room'), ['car', 'shelf'] as const, 'car'),
    shutter: pick<ShutterState>(params.get('shutter'), ['open', 'closed'], 'open'),
    hud: pick<Hud>(params.get('hud'), ['none', 'live', 'replay'], 'live'),
    drape: params.get('drape') === '1',
    guides: params.get('guides') === '1',
    chosen: chosenRaw == null ? undefined : Number(chosenRaw),
  };
}

/** Outlines of the frozen HUD geometry. */
function Guides({ hud }: { hud: Hud }) {
  const g = geometry(hud),
    slot = sideSlot(hud);
  const line = '1px dashed rgba(127,220,242,.8)';
  const box = (style: React.CSSProperties) => (
    <div style={{ position: 'absolute', pointerEvents: 'none', ...style }} />
  );
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {box({ left: 0, top: 0, width: g.wingN, height: 900, borderRight: line })}
      {box({
        left: g.wingN,
        top: 0,
        width: STAGE_W - g.wingN,
        height: HUD_CHROME.topStrip,
        borderBottom: line,
      })}
      {box({ left: 0, top: g.railY, width: STAGE_W, borderTop: line })}
      {box({ left: g.left, top: g.top, width: g.pwid, height: g.ph, border: line })}
      {box({
        left: slot.x,
        top: slot.y,
        width: slot.w,
        height: slot.h,
        border: '1px dotted rgba(127,220,242,.6)',
      })}
    </div>
  );
}

export function PaintBench({ params }: { params: URLSearchParams }) {
  const o = readPaint(params);
  const plan = diningCarPlan({ phase: o.phase, hud: o.hud });
  return (
    <>
      <Layer name="paint">
        {o.room === 'car' ? (
          <>
            <Paint of={diningCar} opts={{ phase: o.phase, hud: o.hud }} />
            <Paint of={shutter} opts={{ hud: o.hud, state: o.shutter }} />
          </>
        ) : (
          <Paint of={shelfRoom} opts={{ hud: o.hud, wood: SPRITES.wood.src }} />
        )}
      </Layer>
      <Layer name="light">
        {o.room === 'car' ? (
          <Paint
            of={light}
            opts={{
              hud: o.hud,
              from: 'over',
              scene: { glows: plan.glows, specials: plan.specials },
            }}
          />
        ) : (
          <Paint of={shelfLight} opts={{ hud: o.hud, chosen: o.chosen }} />
        )}
      </Layer>
      <Layer name="hud">
        {o.drape ? <Paint of={drape} opts={{}} /> : null}
        {o.guides ? <Guides hud={o.hud} /> : null}
      </Layer>
    </>
  );
}

export function PaintControls({
  params,
  set,
}: {
  params: URLSearchParams;
  set: (k: string, v: string) => void;
}) {
  const o = readPaint(params);
  return (
    <>
      <Seg
        label="phase"
        options={PHASES_IN_ORDER}
        value={o.phase}
        onChange={(v) => set('phase', v)}
      />
      <Seg
        label="room"
        options={['car', 'shelf'] as const}
        value={o.room}
        onChange={(v) => set('room', v)}
      />
      <Seg
        label="shutter"
        options={['open', 'closed'] as const}
        value={o.shutter}
        onChange={(v) => set('shutter', v)}
      />
      <Seg
        label="hud"
        options={['none', 'live', 'replay'] as const}
        value={o.hud}
        onChange={(v) => set('hud', v)}
      />
      <Seg
        label="drape"
        options={['0', '1'] as const}
        value={o.drape ? '1' : '0'}
        onChange={(v) => set('drape', v)}
      />
      <Seg
        label="guides"
        options={['0', '1'] as const}
        value={o.guides ? '1' : '0'}
        onChange={(v) => set('guides', v)}
      />
    </>
  );
}
