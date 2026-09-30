/**
 * Everything the workbench needs to draw one URL: the scene's beats for this viewer, the one
 * the URL points at, the log folded up to it, and the presentation. A pure function of the
 * URL (and the fixture), so what the workbench shows and what a test checks cannot drift.
 */
import type { Character } from '@/assets/manifest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { DurableGameEvent } from '@/types/contracts';
import { beatsFor } from '../beats/beatsFor';
import { DIM_FACETS, parseSituation } from '../film/case-file';
import type { SceneBeat, SceneId } from '../beats/types';
import type { Presentation, RoomInput, TurnInput } from '../scenes/types';
import { FIXTURE_CAST, FIXTURE_EVENTS } from './fixture';
import { SYNTHETIC, SYNTHETIC_AFTER, sceneBeats } from './registry';
import { synthesiseAll, type AnySituation } from './synthetic';
import type { WorkbenchQuery } from './url';

const MEMORY_EVENTS = new Set(['memory_consulted', 'memory_extracted']);

/** The workbench's one game, for the notebook a seated viewer keeps (notebook.ts). */
export const WORKBENCH_GAME = 'workbench';

export interface WorkbenchFrame {
  beats: SceneBeat[];
  /** The URL's beat, clamped into the scene's range. */
  index: number;
  beat: SceneBeat | null;
  view: GameView | null;
  me: string | null;
  presentation: Presentation;
  /** A live-only scene: the situation this frame was drawn from, and its prompt's live side. */
  situation?: AnySituation;
  turn?: TurnInput;
  /** The platform's waiting room. */
  room?: RoomInput;
  /**
   * The whole log folded, for the case file: whether memory was on, and what the game taught
   * (see `SlotInput.ahead`). A replay has the whole log, so the workbench hands it all over.
   */
  ahead?: GameView | null;
}

export function workbenchFrame(
  scene: SceneId,
  q: WorkbenchQuery,
  events: readonly DurableGameEvent[] = FIXTURE_EVENTS,
  cast: readonly Character[] = FIXTURE_CAST,
): WorkbenchFrame {
  // a memory-off game: the same log without what memory adds
  if (q.memoryOff) events = events.filter((e) => !MEMORY_EVENTS.has(e.type));
  else if (q.memoryFields) events = withFields(events);
  const situations = SYNTHETIC[scene];
  if (situations && !SYNTHETIC_AFTER.has(scene))
    return syntheticFrame(situations, q, events, cast);
  const me = q.viewer.kind === 'seat' ? q.viewer.seat : null;
  const xray = q.viewer.kind === 'xray';
  const beats = sceneBeats(beatsFor(events, { xray, me, live: q.live }), scene);
  // a live-only prompt among the fixture's beats: its situations follow them in the stepper
  if (situations && q.beat >= beats.length)
    return syntheticFrame(
      situations,
      { ...q, beat: q.beat - beats.length },
      events,
      cast,
      beats,
    );
  const index = Math.max(0, Math.min(q.beat, beats.length - 1));
  const beat = beats[index] ?? null;
  const view = beat ? foldEvents(events.slice(0, beat.end), { mySeat: me }) : null;
  const ahead = beat && xray ? foldEvents(events, { mySeat: me }) : null;
  return {
    beats: situations
      ? [...beats, ...synthesiseAll(situations, events).map((f) => f.beat)]
      : beats,
    index,
    beat,
    view,
    me,
    ahead,
    presentation: {
      xray,
      slot: q.slot === 'none' ? null : q.slot,
      motion: q.motion,
      hud: q.hud,
      animate: q.animate,
      cast,
      // a live cut keeps a seated viewer's notebook, as a live game would
      game: q.live ? WORKBENCH_GAME : undefined,
    },
  };
}

/** The beat's anchor, in one line: "day.speech · seq 163 · public → player_2 · 11250 ms". */
export function anchorLine(b: SceneBeat): string {
  const tier = b.seat ? `${b.sees}@${b.seat}` : b.sees;
  const about = b.subject ? ` → ${b.subject}` : '';
  const nth = b.ordinal ? ` #${b.ordinal}` : '';
  return `${b.id} · seq ${b.seq} · ${tier}${about}${nth} · ${b.holdMs} ms`;
}

/**
 * A live-only scene's frame: `?beat=N` picks the Nth situation, the seat comes from the
 * situation (the viewer control does not apply), and the X-ray is off (a prompt is seat tier).
 * `before` are the fixture's own beats that come first in the stepper, if any.
 */
function syntheticFrame(
  situations: readonly AnySituation[],
  q: WorkbenchQuery,
  events: readonly DurableGameEvent[],
  cast: readonly Character[],
  before: readonly SceneBeat[] = [],
): WorkbenchFrame {
  const frames = synthesiseAll(situations, events);
  const index = Math.max(0, Math.min(q.beat, frames.length - 1));
  const f = frames[index];
  return {
    beats: [...before, ...frames.map((x) => x.beat)],
    index: before.length + index,
    beat: f?.beat ?? null,
    view: f?.view ?? null,
    me: f?.me ?? null,
    presentation: {
      xray: false,
      slot: q.slot === 'none' ? null : q.slot,
      motion: q.motion,
      hud: q.hud,
      animate: q.animate,
      cast,
      // a live-only prompt is a seated player's: their notebook is kept
      game: WORKBENCH_GAME,
    },
    situation: situations[index],
    turn: f?.turn,
    room: f?.room,
  };
}

/**
 * The fixture's memory records with a small synthetic `dimensions` each (the fixture predates
 * them, server 18ebf3e): the composed situation split back into its fields, and made-up but
 * plausible classifications and tags, so the case file's field-reading path can be drawn.
 */
function withFields(events: readonly DurableGameEvent[]): DurableGameEvent[] {
  const dims = (situation: string, i: number) => {
    const s = parseSituation(situation);
    const out: Record<string, unknown> = { situation: s.lead };
    for (const f of s.facets) {
      const dim = DIM_FACETS.find(([, key]) => key === f.key)?.[0];
      if (dim) out[dim] = f.value;
    }
    out.info_landscape_class = /rich/i.test(String(out.information_landscape ?? ''))
      ? 'info_rich'
      : 'info_starved';
    out.exposure_class = i % 2 ? 'exposed' : 'safe';
    out.consensus_direction = [
      'aligns_with_my_read',
      'opposes_my_read',
      'no_clear_direction',
    ][i % 3];
    out.direction = ['defensive', 'offensive', 'positional'][i % 3];
    out.honesty = i % 2 ? 'deceptive' : 'honest';
    out.players_alive = 9 - (i % 4);
    return out;
  };
  return events.map((e) =>
    e.type === 'memory_consulted'
      ? {
          ...e,
          lessons: e.lessons.map((l, i) => ({ ...l, dimensions: dims(l.situation, i) })),
        }
      : e.type === 'memory_extracted'
        ? {
            ...e,
            observations: e.observations.map((o, i) => ({
              ...o,
              dimensions: dims(o.situation, i),
            })),
            strategy_points: e.strategy_points.map((l, i) => ({
              ...l,
              dimensions: dims(l.situation, i),
            })),
          }
        : e,
  );
}
