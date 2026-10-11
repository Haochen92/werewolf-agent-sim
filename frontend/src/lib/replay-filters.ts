/**
 * The archive's filters and sort (review §F6: they run in the browser, over the one fetch of
 * `GET /replays`). Pure functions over `ReplaySummary` rows, so the page only holds state and
 * these decide what it shows.
 */
import type { ReplaySummary } from '@/types/contracts';
import { winnerKey, type WinnerKey } from '@/stage/roles';

export type EndedPhase = NonNullable<ReplaySummary['ended_phase']>;

export interface ReplayFilters {
  /** Part of a game id, any case. */
  q: string;
  /** Only games this browser holds a seat in. */
  mine: boolean;
  /** Won by any of these (`draw`: no one); empty = any winner. */
  winners: WinnerKey[];
  memory: 'any' | 'on' | 'off';
  /** `people`: at least one human seat; `agents`: agents in every seat. */
  table: 'any' | 'people' | 'agents';
  ended: 'any' | EndedPhase;
  /** A model id; `''` = games whose model was not recorded; null = any model. */
  model: string | null;
  /** Finished on or after / on or before this day (`YYYY-MM-DD`, UTC); '' = open. */
  from: string;
  to: string;
}

export type ReplaySort = 'new' | 'old' | 'long' | 'short';

export const NO_FILTERS: ReplayFilters = {
  q: '',
  mine: false,
  winners: [],
  memory: 'any',
  table: 'any',
  ended: 'any',
  model: null,
  from: '',
  to: '',
};

export function matchesReplay(
  r: ReplaySummary,
  f: ReplayFilters,
  mine: ReadonlySet<string>,
): boolean {
  const q = f.q.trim().toLowerCase();
  if (q && !r.game_id.toLowerCase().includes(q)) return false;
  if (f.mine && !mine.has(r.game_id)) return false;
  if (f.winners.length && !f.winners.includes(winnerKey(r.winner))) return false;
  if (f.memory === 'on' && !r.memory) return false;
  if (f.memory === 'off' && r.memory) return false;
  if (f.table === 'people' && r.n_humans === 0) return false;
  if (f.table === 'agents' && r.n_humans > 0) return false;
  if (f.ended !== 'any' && r.ended_phase !== f.ended) return false;
  if (f.model !== null && (r.model ?? '') !== f.model) return false;
  if (f.from || f.to) {
    const day = r.finished_at?.slice(0, 10);
    if (!day) return false;
    if (f.from && day < f.from) return false;
    if (f.to && day > f.to) return false;
  }
  return true;
}

/** Newest first when two rows tie on the sort key; games with no date go last. */
function byNewest(a: ReplaySummary, b: ReplaySummary): number {
  const ta = a.finished_at ?? '';
  const tb = b.finished_at ?? '';
  if (ta !== tb) return tb.localeCompare(ta);
  return a.game_id.localeCompare(b.game_id);
}

export function sortReplays(
  rows: readonly ReplaySummary[],
  sort: ReplaySort,
): ReplaySummary[] {
  const out = rows.slice();
  switch (sort) {
    case 'new':
      return out.sort(byNewest);
    case 'old':
      return out.sort((a, b) => {
        if (!a.finished_at !== !b.finished_at) return a.finished_at ? -1 : 1;
        return -byNewest(a, b);
      });
    case 'long':
      return out.sort((a, b) => b.days - a.days || byNewest(a, b));
    case 'short':
      return out.sort((a, b) => a.days - b.days || byNewest(a, b));
  }
}

export function applyFilters(
  rows: readonly ReplaySummary[],
  f: ReplayFilters,
  sort: ReplaySort,
  mine: ReadonlySet<string>,
): ReplaySummary[] {
  return sortReplays(
    rows.filter((r) => matchesReplay(r, f, mine)),
    sort,
  );
}

/** The model ids in the fetched rows, for the model dropdown; `''` (unrecorded) last. */
export function distinctModels(rows: readonly ReplaySummary[]): string[] {
  const ids = new Set(rows.map((r) => r.model ?? ''));
  const named = [...ids].filter(Boolean).sort();
  return ids.has('') ? [...named, ''] : named;
}

export const WINNER_NAME: Record<WinnerKey, string> = {
  villagers: 'the town',
  wolves: 'the wolves',
  serial_killer: 'the serial killer',
  necromancer: 'the necromancer',
  draw: 'no one',
};

const ENDED_NAME: Record<EndedPhase, string> = {
  day: 'in the day',
  voting: 'at the vote',
  night: 'at night',
};

export interface ActiveFilter {
  key: string;
  label: string;
  /** The filters with this one taken off. */
  without: ReplayFilters;
}

/** The filters in force, as removable chips above the results. */
export function activeFilters(
  f: ReplayFilters,
  modelName: (id: string) => string,
): ActiveFilter[] {
  const out: ActiveFilter[] = [];
  const q = f.q.trim();
  if (q) out.push({ key: 'q', label: `Game ${q}`, without: { ...f, q: '' } });
  if (f.mine)
    out.push({ key: 'mine', label: 'On this device', without: { ...f, mine: false } });
  for (const w of f.winners) {
    out.push({
      key: `win:${w}`,
      label: `Won by ${WINNER_NAME[w]}`,
      without: { ...f, winners: f.winners.filter((x) => x !== w) },
    });
  }
  if (f.ended !== 'any') {
    out.push({
      key: 'ended',
      label: `Ended ${ENDED_NAME[f.ended]}`,
      without: { ...f, ended: 'any' },
    });
  }
  if (f.memory !== 'any') {
    out.push({
      key: 'memory',
      label: `Memory ${f.memory}`,
      without: { ...f, memory: 'any' },
    });
  }
  if (f.table !== 'any') {
    out.push({
      key: 'table',
      label: f.table === 'agents' ? 'AI agents only' : 'With human players',
      without: { ...f, table: 'any' },
    });
  }
  if (f.model !== null) {
    out.push({
      key: 'model',
      label: f.model ? modelName(f.model) : 'Model not recorded',
      without: { ...f, model: null },
    });
  }
  if (f.from)
    out.push({ key: 'from', label: `From ${f.from}`, without: { ...f, from: '' } });
  if (f.to) out.push({ key: 'to', label: `To ${f.to}`, without: { ...f, to: '' } });
  return out;
}
