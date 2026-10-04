'use client';

/**
 * The right side of the stage: the transcript drawer or the case file, one at a time, or
 * nothing (beat sheet §0 "The right slot", §12 "The slot"). Every scene mounts this once, in
 * the HUD, and lays its own room out narrower while it holds something (see slot.ts).
 *
 * What must outlive a beat (the drawer's filters, the file's open tab, chosen seat and the
 * Record's page) comes from whoever mounts the stage, through `SceneProps.slot`; without it the
 * slot keeps its own, so a scene still draws a working slot on its own. The transcript's
 * pointer to a day's record opens the file on the Record at that morning, through here.
 */
import { useState } from 'react';
import { Layer } from './Stage';
import { Drawer } from './drawer/Drawer';
import { useDrawerFilters } from './drawer/use-drawer-filters';
import { Film } from './film/Film';
import { fileFocus, type FileChoice } from './film/case-file';
import { recordMornings, type RecordPick } from './film/record-model';
import type { SceneProps } from './scenes/types';
import { atRail, railHolds, slotOf, tapsOpenFiles } from './slot';
import { actedTonight } from './scenes/replay-night';

export function SideSlot({ view, beat, me, presentation, slot, stop }: SceneProps) {
  const own = useDrawerFilters();
  const [ownTab, setOwnTab] = useState('notes');
  const [ownSeat, setOwnSeat] = useState<FileChoice | null>(null);
  const [ownPick, setOwnPick] = useState<RecordPick | null>(null);
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
  const pickSeat = slot?.onFileSeat ?? setOwnSeat;
  const pickPage = slot?.onRecordPick ?? setOwnPick;
  // the transcript's pointer: the file on the Record, at the morning the day's record was read
  const showRecord = slot?.onShowRecord;
  const openRecord = showRecord
    ? (morning: number) => {
        pickPage({ morning, latest: recordMornings(view, beat).at(-1) ?? morning });
        pickSeat({ seat: null, key: fileFocus(view, beat)?.key ?? null, record: true });
        showRecord();
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
          onRecord={openRecord}
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
          onSeat={pickSeat}
          replay={slot?.replayHref}
          seatTaps={!!slot?.onOpenFile && tapsOpenFiles(beat)}
          visit={visit}
          xray={xray}
          ledger={slot?.ledger ?? null}
          recordPick={slot?.onRecordPick ? (slot.recordPick ?? null) : ownPick}
          onRecordPick={pickPage}
        />
      )}
    </Layer>
  );
}
