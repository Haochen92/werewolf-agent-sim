'use client';

/**
 * After the game, working, in the guide: three of the replay's own panels fed from real
 * recorded games (the workbench's fixtures, so the guide loads this module lazily): the
 * transcript (`Drawer`), the case file with Reveal on (`Film`), and a memory-on game's case
 * file open on its Lessons. Each panel stands on a small stage cropped to it (`Focus`), its
 * height capped (`--side-max`) so it reads at the column's size.
 */
import { useMemo, useState } from 'react';
import type { DurableGameEvent } from '@/types/contracts';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '@/stage/beats/beatsFor';
import { castForGame, rosterSize } from '@/stage/cast/castForGame';
import { Drawer } from '@/stage/drawer/Drawer';
import { DEFAULT_FILTERS, type DrawerFilters } from '@/stage/drawer/drawer-lines';
import { Film } from '@/stage/film/Film';
import type { FileChoice } from '@/stage/film/case-file';
import tenSeat from '@/stage/fixtures/replay-phase3.json';
import memoryGame from '@/stage/fixtures/replay-9369a5c1.json';
import { Focus } from './StopDemos';
import classes from './Guide.module.css';

/** A recorded game at one beat: its view there, the whole game's, and its cast. */
function useGameAt(
  game: { game_id: string; events: unknown },
  /** A day (its middle beat, or its `last`), or `end`: the game's last beat, every file closed. */
  pick: { xray: boolean; day?: number; last?: boolean; end?: boolean },
) {
  return useMemo(() => {
    const events = game.events as readonly DurableGameEvent[];
    const beats = beatsFor(events, { xray: pick.xray, me: null });
    const onDay = beats.filter((b) => b.day === pick.day);
    const beat =
      (pick.end
        ? beats.at(-1)
        : pick.last
          ? onDay.at(-1)
          : onDay[Math.floor(onDay.length / 2)]) ?? beats[0];
    return {
      beat,
      view: foldEvents(events.slice(0, beat.end), { mySeat: null }),
      ahead: foldEvents(events, { mySeat: null }),
      cast: castForGame(game.game_id, rosterSize(events)),
    };
  }, [game, pick.xray, pick.day, pick.last, pick.end]);
}

/** The transcript of a ten-seat game at the end of day 2: filter it by day, by seat. */
export function TranscriptDemo() {
  const g = useGameAt(tenSeat, { xray: false, day: 2, last: true });
  const [filters, setFilters] = useState<DrawerFilters>(DEFAULT_FILTERS);
  return (
    <div className={classes.sidePanel}>
      <Focus selector="[data-drawer]" pad={0}>
        <Drawer
          view={g.view}
          beat={g.beat}
          me={null}
          xray={false}
          hud="replay"
          cast={g.cast}
          filters={filters}
          onFilters={setFilters}
        />
      </Focus>
    </div>
  );
}

/** The case file with Reveal on, a ten-seat game at its end: pick a seat, Notes and Reads. */
export function RevealDemo() {
  const g = useGameAt(tenSeat, { xray: true, end: true });
  const [tab, setTab] = useState('notes');
  // open on a seat's file: its Notes first, its Reads a tab away
  const [seat, setSeat] = useState<FileChoice | null>({ seat: 'player_6', key: null });
  return (
    <div className={classes.sidePanel}>
      <Focus selector="[data-film]" pad={0}>
        <Film
          view={g.view}
          beat={g.beat}
          hud="replay"
          cast={g.cast}
          ahead={g.ahead}
          tab={tab}
          onTab={setTab}
          seat={seat}
          onSeat={setSeat}
          xray
        />
      </Focus>
    </div>
  );
}

/** A memory-on game's case file at its end, open on a seat's Lessons (its Findings a tab away). */
export function MemoryDemo() {
  const g = useGameAt(memoryGame, { xray: true, end: true });
  const [tab, setTab] = useState('precedents');
  const [seat, setSeat] = useState<FileChoice | null>({ seat: 'player_8', key: null });
  return (
    <div className={classes.sidePanel}>
      <Focus selector="[data-film]" pad={0}>
        <Film
          view={g.view}
          beat={g.beat}
          hud="replay"
          cast={g.cast}
          ahead={g.ahead}
          tab={tab}
          onTab={setTab}
          seat={seat}
          onSeat={setSeat}
          xray
        />
      </Focus>
    </div>
  );
}
