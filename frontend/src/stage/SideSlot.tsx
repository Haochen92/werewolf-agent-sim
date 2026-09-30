'use client';

/**
 * The right side of the stage: the transcript drawer or the X-ray's case file, one at a time,
 * or nothing (beat sheet §0 "The right slot", §12 "The slot"). Every scene mounts this once, in
 * the HUD, and lays its own room out narrower while it holds something (see slot.ts).
 *
 * What must outlive a beat (the drawer's filters, the file's open tab and chosen seat) comes
 * from whoever mounts the stage, through `SceneProps.slot`; without it the slot keeps its own,
 * so a scene still draws a working slot on its own.
 */
import { useState } from 'react';
import { Layer } from './Stage';
import { Drawer } from './drawer/Drawer';
import { useDrawerFilters } from './drawer/use-drawer-filters';
import { Film } from './film/Film';
import type { FileChoice } from './film/case-file';
import type { SceneProps } from './scenes/types';
import { atRail, railHolds, slotOf, tapsOpenFiles } from './slot';
import { actedTonight } from './scenes/replay-night';

export function SideSlot({ view, beat, me, presentation, slot, stop }: SceneProps) {
  const own = useDrawerFilters();
  const [ownTab, setOwnTab] = useState('notes');
  const [ownSeat, setOwnSeat] = useState<FileChoice | null>(null);
  const occupant = slotOf(presentation);
  // the epilogue is the ledger come down over the whole stage: nothing sits beside it
  if (!occupant || beat.id === 'over.epilogue') return null;
  const { hud, xray, cast, animate } = presentation;
  // the night stop: the rooms the file's sheet offers to visit, each actor once (the pack's
  // wolves together), as the wing's lit cards do
  const rooms: { actor: string; seats: string[]; seen: boolean }[] = [];
  if (stop && beat.id === 'rnight.hub')
    for (const [seat, actor] of actedTonight(view, slot?.ahead ?? view, beat.day)) {
      const r = rooms.find((x) => x.actor === actor);
      if (r) r.seats.push(seat);
      else rooms.push({ actor, seats: [seat], seen: stop.visited.includes(actor) });
    }
  const visit = rooms.length
    ? {
        rooms,
        onVisit: (actor: string) =>
          stop!.onVisit(
            (b) =>
              b.id === 'rnight.spoke' && b.day === beat.day && b.spoke?.actor === actor,
          ),
      }
    : undefined;
  return (
    <Layer name="hud">
      {occupant === 'drawer' ? (
        <Drawer
          view={view}
          beat={beat}
          me={me}
          xray={xray}
          hud={hud}
          cast={cast}
          filters={slot?.filters ?? own.filters}
          onFilters={slot?.onFilters ?? own.setFilters}
          rail={atRail(beat)}
          railHolds={railHolds(beat)}
          animate={animate}
          scroll={slot?.drawerScroll ?? own.scroll}
        />
      ) : (
        <Film
          view={view}
          beat={beat}
          hud={hud}
          cast={cast}
          ahead={slot?.ahead}
          tab={slot?.filmTab ?? ownTab}
          onTab={slot?.onFilmTab ?? setOwnTab}
          seat={slot?.onFileSeat ? (slot.fileSeat ?? null) : ownSeat}
          onSeat={slot?.onFileSeat ?? setOwnSeat}
          replay={slot?.replayHref}
          seatTaps={!!slot?.onOpenFile && tapsOpenFiles(beat)}
          visit={visit}
        />
      )}
    </Layer>
  );
}
