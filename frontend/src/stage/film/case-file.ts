/**
 * The case file, as data: what the X-ray's pane holds for one seat at a beat (owner,
 * 2026-09-29, from the case-file bench). A manila folder per seat, its divider tabs:
 *
 * - Notes: one typed page per `strategy_update` the seat wrote up to the playhead, each with a
 *   pencil line in the margin saying how it came from the page before (`marginNote`);
 * - Reads: the seat's latest `player_reads`, one row per seat read, against the truth;
 * - Precedents, shown as "Lessons" (memory-on games): the seat's latest `memory_consulted`,
 *   each lesson with the agent's verdict and why, the situation it was written for parsed into
 *   its facets;
 * - Findings (memory-on games, after the game): what the game taught this seat's ROLE
 *   (`memory_extracted`: its observations, and any strategy points; the extractor files them
 *   by role, not seat). Served games extract observations only (owner, 2026-09-29).
 *
 * All of it is read from the view folded at the beat, so the file only ever holds what had
 * been written by the moment on stage. Which seat's file is open is `fileFocus` + `shownSeat`;
 * a beat with no seat in focus shows the docket (film-model.ts `docketFor`).
 */
import type { GameView } from '@/game/types';
import type { MemoryConsulted, MemoryExtracted } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';
import { nightBranchesOf } from '../scenes/replay-night';
import { seatNumber, seatify } from '../roles';
import { lessonsOf, readMark, type FilmLesson, type ReadMark } from './film-model';

export type FileTab = 'notes' | 'reads' | 'precedents' | 'findings';
export type ExtractedLesson = MemoryExtracted['strategy_points'][number];
export type ExtractedObservation = MemoryExtracted['observations'][number];
type ActionPhase = MemoryConsulted['action_phase'];

// ---- which seat's file ----------------------------------------------------------------

/**
 * The seat a beat brings into focus, and a key for that moment: a day turn's speaker (keyed by
 * the turn), a night spoke's actor (keyed by the spoke; the pack's spoke has both wolves, the
 * first opened). Null for the beats with no seat in focus: they show the docket.
 */
export interface FileFocus {
  seats: string[];
  key: string;
}

export function fileFocus(view: GameView, beat: SceneBeat): FileFocus | null {
  if ((beat.id === 'day.speech' || beat.id === 'day.pass') && beat.subject)
    return { seats: [beat.subject], key: `turn:${beat.seq}` };
  if (beat.id === 'rnight.spoke' && beat.spoke) {
    const cur = nightBranchesOf(view, beat.day)[beat.spoke.rank];
    if (!cur) return null;
    return {
      seats: cur.actor === 'pack' ? cur.seats : [cur.actor],
      key: `night:${beat.day}:${cur.actor}`,
    };
  }
  return null;
}

/**
 * The viewer's own pick from the chooser: a seat, or the docket (null), or the Record, and the
 * focus it was made under. It holds until a beat brings a different seat into focus.
 */
export interface FileChoice {
  seat: string | null;
  key: string | null;
  /** The Record's tab (`seat` is then null). */
  record?: boolean;
}

/**
 * The seat whose file is open (null: the docket). The viewer's pick holds while the beats keep
 * the focus it was made under, or have none (the count, the lynch, the morning, the ending);
 * the next beat that brings a seat into focus (another turn, another spoke) opens that seat's.
 */
export function shownSeat(
  focus: FileFocus | null,
  choice: FileChoice | null,
): string | null {
  if (choice && (focus === null || focus.key === choice.key)) return choice.seat;
  return focus ? focus.seats[0] : null;
}

/** The viewer picked the Record, and the pick still holds, as a seat's would (`shownSeat`). */
export function recordPicked(focus: FileFocus | null, choice: FileChoice | null): boolean {
  return !!choice?.record && (focus === null || focus.key === choice.key);
}

/** "Day 3 · discussion", "Night 2", "Dawn 3" (the report of night 2), "Game over": where the playhead is. */
export function asOf(beat: Pick<SceneBeat, 'id' | 'scene' | 'day'>): string {
  const d = beat.day;
  switch (beat.scene) {
    case 'station':
      return 'Before the game';
    case 'deal':
      return beat.id === 'deal.day-begins' ? `Day ${d} · discussion` : 'The deal';
    case 'day':
      return `Day ${d} · discussion`;
    case 'vote':
    case 'lynch':
      return `Day ${d} · vote`;
    case 'morning':
      return beat.id === 'morning.day-begins' ? `Day ${d} · discussion` : `Dawn ${d + 1}`;
    case 'over':
      return 'Game over';
    default:
      return `Night ${d}`;
  }
}

const PHASE_WORD: Record<string, string> = {
  day: 'discussion',
  voting: 'vote',
  day_discussion: 'discussion',
  day_vote: 'vote',
};

/** "Day 2 · discussion", "Day 3 · vote", or "Night 2": a day and a phase, as the file writes them. */
export function when(day: number, phase: string): string {
  return phase === 'night' || phase === 'night_action'
    ? `Night ${day}`
    : `Day ${day} · ${PHASE_WORD[phase] ?? phase}`;
}

// ---- the notes ------------------------------------------------------------------------

export interface NotePage {
  seq: number;
  day: number;
  /** The phase it was written in, from the timeline: `day`, `voting` or `night`. */
  phase: string;
  text: string;
}

/** Every note the seat has written by the view's end, oldest first. */
export function notePages(view: GameView, seat: string): NotePage[] {
  return (view.xray.agents[seat]?.strategy ?? []).map((s) => ({
    seq: s.seq,
    day: s.day,
    phase: view.timeline.filter((t) => t.seq < s.seq).at(-1)?.phase ?? 'day',
    text: s.text,
  }));
}

/**
 * A word diff (longest common subsequence over whitespace-split words): the edit script from
 * `a` to `b`, and the share of `a`'s words that `b` kept.
 */
export function wordDiff(a: string, b: string) {
  const A = a.trim().split(/\s+/).filter(Boolean);
  const B = b.trim().split(/\s+/).filter(Boolean);
  const n = A.length,
    m = B.length;
  const L = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const ops: ['=' | '-' | '+', string][] = [];
  let i = 0,
    j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) {
      ops.push(['=', B[j]]);
      i++;
      j++;
    } else if (L[i + 1][j] >= L[i][j + 1]) ops.push(['-', A[i++]]);
    else ops.push(['+', B[j++]]);
  }
  while (i < n) ops.push(['-', A[i++]]);
  while (j < m) ops.push(['+', B[j++]]);
  return { ops, kept: n ? L[0][0] / n : 0 };
}

/**
 * The pencil line in page `k`'s margin: "first page"; "rewritten from scratch" when it kept
 * under half the previous page's words; else `edited from p. N, added: "…"` quoting the longest
 * run of words it added (at most nine), or `edited from p. N` when it only cut.
 */
export function marginNote(pages: readonly { text: string }[], k: number): string {
  if (k <= 0) return 'first page';
  const d = wordDiff(seatify(pages[k - 1].text), seatify(pages[k].text));
  if (d.kept < 0.5) return 'rewritten from scratch';
  if (d.ops.every(([op]) => op === '=')) return `unchanged from p. ${k}`;
  const runs: string[][] = [];
  let run: string[] = [];
  for (const [op, w] of d.ops) {
    if (op === '+') run.push(w);
    else if (op === '=' && run.length) {
      runs.push(run);
      run = [];
    }
  }
  if (run.length) runs.push(run);
  const bare = (w: string) => w.replace(/[^\w']/g, '').toLowerCase();
  const cut = new Set(d.ops.filter(([op]) => op === '-').map(([, w]) => bare(w)));
  // the longest run (the first of equals); a word that only moved in from the cut is not new
  const longest = [
    ...(runs.reduce<string[] | null>((a, r) => (a && a.length >= r.length ? a : r), null) ??
      []),
  ];
  if (longest.length > 1 && cut.has(bare(longest[0]))) longest.shift();
  if (!longest.length) return `edited from p. ${k}`;
  const words = longest.slice(0, 9).join(' ') + (longest.length > 9 ? '…' : '');
  return `edited from p. ${k}, added: “${words}”`;
}

// ---- the situation a lesson was written for ------------------------------------------

export type FacetKey =
  | 'information'
  | 'stakes'
  | 'consensus'
  | 'position'
  | 'heat'
  | 'exposure'
  | 'targets'
  | 'public'
  | 'phase';

/**
 * The labels `compose_situation_embed` (Agents/schemas/memory.py) writes between a
 * situation's facets, and the older stores' set (Game phase, Consensus texture, Agent
 * exposure). Longer labels first, so "Consensus texture:" is never read as "Consensus:".
 */
const LABELS: readonly [label: string, key: FacetKey, name: string][] = [
  ['Information landscape', 'information', 'Information'],
  ['Consensus texture', 'consensus', 'Consensus'],
  ['Consensus', 'consensus', 'Consensus'],
  ['Stakes', 'stakes', 'Stakes'],
  ['My position', 'position', 'Position'],
  ['Heat', 'heat', 'Heat'],
  ['Forward exposure', 'exposure', 'Exposure'],
  ['Agent exposure', 'exposure', 'Exposure'],
  ['Target landscape', 'targets', 'Targets'],
  ['Public vs private', 'public', 'Public vs private'],
  ['Game phase', 'phase', 'Phase'],
];
const LABEL_RE = new RegExp(`(?:^|\\s)(${LABELS.map(([l]) => l).join('|')}):`, 'g');

export interface Facet {
  key: FacetKey;
  /** The file's short name for it: "Information", "Position". */
  name: string;
  value: string;
}

/** A situation split at its labels: the lead (no label), then each facet; no labels, all lead. */
export function parseSituation(text: string): { lead: string; facets: Facet[] } {
  const hits = [...text.matchAll(LABEL_RE)].map((m) => {
    const [, key, name] = LABELS.find(([l]) => l === m[1])!;
    const at = m.index + m[0].length - m[1].length - 1;
    return { at, end: m.index + m[0].length, key, name };
  });
  if (!hits.length) return { lead: text.trim(), facets: [] };
  return {
    lead: text.slice(0, hits[0].at).trim(),
    facets: hits.map((h, k) => ({
      key: h.key,
      name: h.name,
      value: text.slice(h.end, k + 1 < hits.length ? hits[k + 1].at : text.length).trim(),
    })),
  };
}

/**
 * A memory record's structured situation, as the wire carries it since server 18ebf3e
 * (`dimensions` on WireLesson, WireObservation and the extracted ones): the store's fields
 * verbatim; null for a legacy record, whose situation is only the composed string.
 */
export type Dimensions = { [key: string]: unknown } | null | undefined;

/** The record's text facets, by their keys, in the order `compose_situation_embed` writes them. */
export const DIM_FACETS: readonly [dim: string, key: FacetKey, name: string][] = [
  ['information_landscape', 'information', 'Information'],
  ['criticality_stakes', 'stakes', 'Stakes'],
  ['consensus_text', 'consensus', 'Consensus'],
  ['my_position', 'position', 'Position'],
  ['heat_now', 'heat', 'Heat'],
  ['forward_exposure', 'exposure', 'Exposure'],
  ['target_landscape', 'targets', 'Targets'],
  ['public_private_text', 'public', 'Public vs private'],
];

const CONSENSUS_NOTE: Record<string, string> = {
  aligns_with_my_read: 'aligns with my read',
  opposes_my_read: 'opposes my read',
  no_clear_direction: 'no clear direction',
};

export interface SituationRead {
  lead: string;
  facets: Facet[];
  /**
   * Boxes ticked exactly from the record's classifications (Information from
   * `info_landscape_class`, Exposure from `exposure_class`); a row absent here ticks by the
   * leading-word rule on its text (`tickOf`), and Exposure is then not a row at all.
   */
  exact: Partial<Record<FormKey, string | null>>;
  /** A small typed note under a facet: the consensus's direction. */
  notes: Partial<Record<FacetKey, string>>;
  /** One quiet typed line of the record's numbers: "9 alive · a swing vote". */
  count: string | null;
}

const text = (v: unknown) => (typeof v === 'string' ? v.trim() : '');

/**
 * A situation as the file sets it. With the record's `dimensions` (owner, 2026-09-30) its
 * facets are read from the named fields, the string never parsed, and the Information and
 * Exposure boxes are ticked from the classifications exactly; without them (an old replay) the
 * composed string is split at its labels, as before.
 */
export function situationOf(situation: string, dims?: Dimensions): SituationRead {
  if (!dims) return { ...parseSituation(situation), exact: {}, notes: {}, count: null };
  const facets = DIM_FACETS.flatMap(([dim, key, name]) =>
    text(dims[dim]) ? [{ key, name, value: text(dims[dim]) }] : [],
  );
  const exact: SituationRead['exact'] = {};
  const info = dims.info_landscape_class;
  if (info === 'info_starved' || info === 'info_rich')
    exact.information = info === 'info_starved' ? 'Starved' : 'Rich';
  const exp = dims.exposure_class;
  if (exp === 'safe' || exp === 'exposed')
    exact.exposure = exp === 'safe' ? 'Safe' : 'Exposed';
  const notes: SituationRead['notes'] = {};
  const dir = CONSENSUS_NOTE[text(dims.consensus_direction)];
  if (dir && facets.some((f) => f.key === 'consensus')) notes.consensus = dir;
  const alive =
    typeof dims.players_alive === 'number' ? `${dims.players_alive} alive` : null;
  const swing = dims.is_swing === true ? 'a swing vote' : null;
  const count = [alive, swing].filter(Boolean).join(' · ') || null;
  return { lead: text(dims.situation), facets, exact, notes, count };
}

/** A record's tags, "defensive · honest", from its `direction` and `honesty`; null without them. */
export function tagsOf(dims?: Dimensions): string | null {
  if (!dims) return null;
  const t = [text(dims.direction), text(dims.honesty)].filter(Boolean).join(' · ');
  return t || null;
}

/** A facet's first sentence (the whole of it when it has one). */
export function firstSentence(s: string): string {
  const m = s.match(/^(.+?[.!?])(\s|$)/);
  return m ? m[1] : s;
}

/** A value's short form: up to its first `;` or `.`, underscores as spaces. */
export function shortForm(v: string): string {
  return v.split(/[;.]/)[0].replace(/_/g, ' ').trim();
}

export type FormKey = 'heat' | 'position' | 'information' | 'exposure';

/**
 * The form's rows and their boxes, in the order they are printed. Exposure is a row only when
 * the record classifies it (`exposure_class`); its text has no closed words to tick by.
 */
export const FORM: readonly {
  key: FormKey;
  name: string;
  boxes: readonly (readonly [word: string, box: string])[];
}[] = [
  {
    key: 'heat',
    name: 'Heat',
    boxes: [
      ['none', 'None'],
      ['low', 'Low'],
      ['moderate', 'Moderate'],
      ['high', 'High'],
      ['max', 'Max'],
    ],
  },
  {
    key: 'position',
    name: 'Position',
    boxes: [
      ['driving', 'Driving'],
      ['with majority', 'With majority'],
      ['holding out', 'Holding out'],
    ],
  },
  {
    key: 'information',
    name: 'Information',
    boxes: [
      ['information-starved', 'Starved'],
      ['information-rich', 'Rich'],
    ],
  },
  {
    key: 'exposure',
    name: 'Exposure',
    boxes: [
      ['safe', 'Safe'],
      ['exposed', 'Exposed'],
    ],
  },
];

/**
 * The box a facet's value ticks, or null (owner, 2026-09-29: a wrong tick misstates what the
 * agent believed). Ticked only when the value, lower-cased with `_` as a space, STARTS WITH one
 * of the row's closed words, as a whole word ("maximum" is not "max"), and its short form names
 * no other box of the row: "Moderate to high" is a range, not Moderate. Anything else ticks
 * nothing and is written in pencil instead.
 */
export function tickOf(key: FormKey, value: string): string | null {
  const v = value.trim().toLowerCase().replace(/_/g, ' ');
  const short = shortForm(v);
  const row = FORM.find((r) => r.key === key)!;
  const names = (word: string) =>
    new RegExp(`(^|[^a-z0-9])${word}($|[^a-z0-9])`).test(short);
  for (const [word, box] of row.boxes)
    if (
      v.startsWith(word) &&
      !/[a-z0-9]/.test(v.charAt(word.length)) &&
      !row.boxes.some(([w]) => w !== word && names(w))
    )
      return box;
  return null;
}

// ---- one seat's file ------------------------------------------------------------------

export interface ReadRow {
  seat: string;
  suspected: string;
  sure: boolean;
  why: string;
  /** The seat's real role, when the viewer holds it, and how near the read came. */
  truth: string | null;
  mark: ReadMark | null;
}

export interface SeatFile {
  seat: string;
  role: string | null;
  pages: NotePage[];
  reads: { day: number; phase: ActionPhase; rows: ReadRow[] } | null;
  consult: { day: number; phase: ActionPhase; lessons: FilmLesson[] } | null;
  /** A memory-on game: the file has a Precedents tab (empty until the seat consults). */
  memory: boolean;
  /** After the game, in a memory-on game: what it taught this seat's role; null before. */
  findings: {
    role: string;
    observations: ExtractedObservation[];
    lessons: ExtractedLesson[];
  } | null;
}

/**
 * Whether the game was played with memory: anyone consulted, or the game's lessons came in.
 * Read from the view ahead where there is one (the replay's whole log), so day 1, before the
 * first consult, already knows.
 */
export function memoryOn(view: GameView): boolean {
  return (
    !!view.xray.extracted ||
    Object.values(view.xray.agents).some((a) => a.consulted.length > 0)
  );
}

/**
 * At a vote or the lynch after it, where the ballots are in: the day's first ballot. A voter's
 * file there is what it voted on, its reads and its consult as they stood when the ballots were
 * released (owner, 2026-09-29). Null elsewhere: the file reads to the playhead.
 */
export function ballotCut(
  view: GameView,
  beat: Pick<SceneBeat, 'scene' | 'day'>,
): number | null {
  if (beat.scene !== 'vote' && beat.scene !== 'lynch') return null;
  return view.days[beat.day]?.vote.ballots[0]?.seq ?? null;
}

/** One seat's file at the view's end (its reads and consult before `cut`, when given: `ballotCut`); `ahead` (the log past the beat) only says whether memory was on and brings the game's lessons once it is over. */
export function seatFile(
  view: GameView,
  seat: string,
  ahead?: GameView | null,
  cut: number | null = null,
): SeatFile {
  const agent = view.xray.agents[seat];
  const role = view.xray.roles[seat] ?? null;
  const later = ahead ?? view;
  const memory = memoryOn(later) || memoryOn(view);
  const before = <T extends { seq: number }>(list: readonly T[] | undefined) =>
    (list ?? []).filter((e) => cut === null || e.seq < cut).at(-1);
  const r = before(agent?.reads);
  const c = before(agent?.consulted);
  const extracted = view.over ? (later.xray.extracted ?? view.xray.extracted) : null;
  return {
    seat,
    role,
    pages: notePages(view, seat),
    reads: r
      ? {
          day: r.day,
          phase: r.action_phase,
          rows: [...r.reads]
            .sort((a, b) => seatNumber(a.player) - seatNumber(b.player))
            .map((x) => {
              const truth = view.xray.roles[x.player] ?? null;
              return {
                seat: x.player,
                suspected: x.suspected_role,
                sure: x.confidence === 'high',
                why: x.why,
                truth,
                mark: truth ? readMark(x.suspected_role, truth) : null,
              };
            }),
        }
      : null,
    consult: c ? { day: c.day, phase: c.action_phase, lessons: lessonsOf(c) } : null,
    memory,
    findings:
      memory && extracted && role
        ? {
            role,
            observations: extracted.observations.filter((o) => o.perspective === role),
            lessons: extracted.strategy_points.filter((p) => p.perspective === role),
          }
        : null,
  };
}

export interface TabState {
  id: FileTab;
  label: string;
  count: number | null;
  /** Greyed: the tab exists in this game but holds nothing yet. */
  enabled: boolean;
}

/** The file's divider tabs: Notes and Reads always, Precedents and Findings only when they can exist. */
export function fileTabs(f: SeatFile): TabState[] {
  const tabs: TabState[] = [
    {
      id: 'notes',
      label: 'Notes',
      count: f.pages.length || null,
      enabled: f.pages.length > 0,
    },
    {
      id: 'reads',
      label: 'Reads',
      count: f.reads?.rows.length || null,
      enabled: !!f.reads?.rows.length,
    },
  ];
  if (f.memory)
    tabs.push({
      id: 'precedents',
      // the viewer's word for the agents' precedents (owner, 2026-09-30); the id stays
      label: 'Lessons',
      count: f.consult?.lessons.length || null,
      enabled: !!f.consult?.lessons.length,
    });
  if (f.findings)
    tabs.push({
      id: 'findings',
      label: 'Findings',
      count: f.findings.observations.length + f.findings.lessons.length || null,
      enabled: f.findings.observations.length + f.findings.lessons.length > 0,
    });
  return tabs;
}

/** The tab to open: the viewer's, when this file has it; otherwise the notes. */
export function openTab(tabs: readonly TabState[], want: string | undefined): FileTab {
  return tabs.find((t) => t.id === want && t.enabled)?.id ?? 'notes';
}

/** "serial killers", "wolves": a role's plural, for "What this game taught …" (the twelve and the nine-seat two). */
export { ROLE_PLURAL } from '../roles';
