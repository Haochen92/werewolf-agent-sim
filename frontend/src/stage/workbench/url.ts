/**
 * The workbench's URL contract: the URL is the whole state, so any view of any scene can be
 * named in a line of text, pasted, and reproduced exactly (by a person, or by Playwright).
 *
 *   /workbench/<scene>?beat=N&viewer=spect|xray|seat:player_7&motion=normal|fast|skip
 *                     &slot=drawer|film|none&hud=live|replay|none&animate=0|1
 *
 * `beat` counts the scene's own beats from 0. Parsing is forgiving (a missing or bad value is
 * the default; `seat:7` means `seat:player_7`; `motion=1|0` mean normal|skip, the spelling in
 * stage_architecture.md §7), and writing is canonical: all six keys, always in this order.
 * `slot=none` (the default) is the side slot closed; the Transcript and X-ray buttons on the
 * stage write `slot` and `viewer=xray` here, as the replay's own container would hold them.
 * `live=1`, written only when on, cuts the beats as a game in play would (the thinking seat
 * at the stand between turns), for any viewer; without it the beats are the replay's.
 */
import type { MotionSpeed } from '../scenes/types';
import type { Hud } from '../units';

export type Viewer = { kind: 'spect' } | { kind: 'xray' } | { kind: 'seat'; seat: string };

export interface WorkbenchQuery {
  beat: number;
  viewer: Viewer;
  motion: MotionSpeed;
  slot: 'drawer' | 'film' | 'none';
  hud: Hud;
  animate: boolean;
  /** Cut the beats as a live game would; absent = the replay's cut. */
  live?: boolean;
}

export const DEFAULT_QUERY: WorkbenchQuery = {
  beat: 0,
  viewer: { kind: 'spect' },
  motion: 'normal',
  slot: 'none',
  hud: 'live',
  animate: false,
};

/** The keys this contract owns, in the order they are written. Other keys are left alone. */
export const QUERY_KEYS = [
  'beat',
  'viewer',
  'motion',
  'slot',
  'hud',
  'animate',
  'live',
] as const;

const pick = <T extends string>(v: string | null, all: readonly T[], dflt: T): T =>
  all.includes(v as T) ? (v as T) : dflt;

export function parseViewer(v: string | null): Viewer {
  if (v === 'xray') return { kind: 'xray' };
  const m = v?.match(/^seat:(?:player_)?(\d+)$/);
  if (m) return { kind: 'seat', seat: `player_${Number(m[1])}` };
  return { kind: 'spect' };
}

export function viewerParam(v: Viewer): string {
  return v.kind === 'seat' ? `seat:${v.seat}` : v.kind;
}

export function parseQuery(params: URLSearchParams): WorkbenchQuery {
  const beat = Number(params.get('beat'));
  const motionRaw = params.get('motion');
  const motion =
    motionRaw === '1'
      ? 'normal'
      : motionRaw === '0'
        ? 'skip'
        : pick<MotionSpeed>(motionRaw, ['normal', 'fast', 'skip'], DEFAULT_QUERY.motion);
  return {
    beat: Number.isInteger(beat) && beat >= 0 ? beat : DEFAULT_QUERY.beat,
    viewer: parseViewer(params.get('viewer')),
    motion,
    slot: pick(params.get('slot'), ['drawer', 'film', 'none'] as const, DEFAULT_QUERY.slot),
    hud: pick<Hud>(params.get('hud'), ['live', 'replay', 'none'], DEFAULT_QUERY.hud),
    animate: params.get('animate') === '1',
    ...(params.get('live') === '1' ? { live: true } : {}),
  };
}

/**
 * The query string for `q`: the six keys in canonical form, then any other keys `rest`
 * carries (the paint bench's options, `strip=0`), untouched and in their own order.
 */
export function writeQuery(q: WorkbenchQuery, rest?: URLSearchParams): string {
  const out = new URLSearchParams();
  out.set('beat', String(q.beat));
  out.set('viewer', viewerParam(q.viewer));
  out.set('motion', q.motion);
  out.set('slot', q.slot);
  out.set('hud', q.hud);
  out.set('animate', q.animate ? '1' : '0');
  if (q.live) out.set('live', '1');
  rest?.forEach((v, k) => {
    if (!(QUERY_KEYS as readonly string[]).includes(k)) out.append(k, v);
  });
  // `:` is safe in a query; keeping it literal keeps the URL readable
  return out.toString().replace(/%3A/g, ':');
}
