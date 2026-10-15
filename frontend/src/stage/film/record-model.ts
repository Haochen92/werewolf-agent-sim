/**
 * The case file's Record, as data: what the table had on record each morning (owner,
 * 2026-10-04). Every morning after a summarised day the agents read the day summary's
 * accusations and the claim ledger: every role claim and claimed night action, checked by code
 * against the game master's record (`GET /games/{id}/ledger`). All of it is public, so the
 * Record opens without the X-ray, live and in the replay.
 *
 * A page is one morning: the ledger read that morning and the accusations of the day before.
 * The pages are the mornings the view has reached (never one past the stage); the latest is
 * open unless the viewer paged back. A game that ended at dawn adds one page at game over: the
 * last night's records alone, which no morning carried. A game whose ledger is missing (an old
 * archive, or a failed fetch) shows each summary's own claims instead, with no checks.
 */
import type {
  CarriedSummary,
  GameView,
  PrivateResult,
  SummaryAccusation,
  SummaryNightAction,
} from '@/game/types';
import type { LedgerDay, LedgerEntry, LedgerPlayer } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';

export interface RecordPage {
  /** The morning it was read on. */
  morning: number;
  /** The day it carries from (`morning - 1`): its accusations. */
  day: number;
  accusations: SummaryAccusation[];
  players: LedgerPlayer[];
  /** The claims are the ledger's, checked by code; false: the summary's own, unchecked. */
  checked: boolean;
  /**
   * The night before this morning as the engine recorded it for each seat (`night_record`): the
   * viewer's own seat, or every seat in the X-ray; `[]` for a nine-seat game and for a viewer
   * who holds none.
   */
  nights: NightRecordLine[];
  /** The game over's last page (`finalMorning`): the night's records alone, no claims or accusations. */
  final?: boolean;
}

/** Who is looking: their seat's own night records, or every seat's with the X-ray. */
export interface RecordViewer {
  me: string | null;
  xray: boolean;
}

/** One seat's record of its night, in the engine's words; the pack's kill is one line for the pack. */
export interface NightRecordLine {
  /** The seat it was sent to, or `wolves` for the pack's kill. */
  seat: string;
  night: number;
  outcome: string;
  /** The viewer's own (a pack line: the viewer is in the pack). */
  mine: boolean;
}

/**
 * The viewer's page: a morning, and the latest morning there was when they chose it. A new
 * morning reached (or the stage stepped back past it) drops the pick, and the latest opens.
 */
export interface RecordPick {
  morning: number;
  latest: number;
}

/** The beat whose sheet is the Record: the X-ray's carried summary, a day's record before its morning. */
export function recordBeat(beat: Pick<SceneBeat, 'id'>): boolean {
  return beat.id === 'morning.carried-summary';
}

type RecordView = Pick<GameView, 'days' | 'timeline'> &
  Partial<Pick<GameView, 'over' | 'me' | 'xray'>>;

/**
 * The mornings whose record the view has reached, oldest first: morning N once day N-1's
 * summary is in and day N has begun, or while the X-ray's carried-summary beat for day N-1 is
 * on stage. The summary of the day the game ended on is never read: no morning follows it.
 * Given who is looking (`seen`), a game over at dawn adds the last night's page (`finalMorning`).
 */
export function recordMornings(
  view: RecordView,
  beat: Pick<SceneBeat, 'id' | 'day'>,
  seen?: RecordViewer,
): number[] {
  const out = Object.values(view.days)
    .filter(
      (d) =>
        (d.summary || d.summaryStructured) &&
        (view.timeline.some((t) => t.day === d.day + 1 && t.phase === 'day') ||
          (recordBeat(beat) && beat.day === d.day)),
    )
    .map((d) => d.day + 1)
    .sort((a, b) => a - b);
  const last = finalMorning(view, seen);
  return last !== null && !out.includes(last) ? [...out, last] : out;
}

/**
 * The game over's last page, as a morning number: a night's records are complete once it
 * resolves, so the last night the viewer holds records for gets a page when the game ended at
 * its dawn (no day followed to carry them; a summary is read only on a morning that comes). Null
 * before game over, for a game that ended at a lynch (its last night is that day's morning page),
 * and for a viewer who holds no record of it.
 */
export function finalMorning(view: RecordView, seen?: RecordViewer): number | null {
  if (!view.over || !seen) return null;
  const nights = Object.values(view.days)
    .map((d) => d.day)
    .filter((d) => nightRecords(view, d, seen.me, seen.xray).length > 0);
  if (!nights.length) return null;
  const morning = Math.max(...nights) + 1;
  return view.timeline.some((t) => t.day === morning && t.phase === 'day') ? null : morning;
}

/** The morning to open: the viewer's pick while it still holds, else the latest; null: none yet. */
export function shownMorning(
  mornings: readonly number[],
  pick: RecordPick | null | undefined,
): number | null {
  const latest = mornings.at(-1);
  if (latest === undefined) return null;
  return pick && pick.latest === latest && mornings.includes(pick.morning)
    ? pick.morning
    : latest;
}

/**
 * One morning's page: the ledger's claims when it has any, else the summary's own; and, given
 * who is looking (`seen`), the night records of the night before it.
 */
export function recordPage(
  view: Pick<GameView, 'days'> &
    Partial<Pick<GameView, 'timeline' | 'over' | 'me' | 'xray'>>,
  morning: number,
  ledger: readonly LedgerDay[] | null | undefined,
  seen?: RecordViewer,
): RecordPage {
  // the game over's last page: the night alone (the day before it was read by no morning)
  if (view.timeline && morning === finalMorning({ ...view, timeline: view.timeline }, seen))
    return {
      morning,
      day: morning - 1,
      accusations: [],
      players: [],
      checked: false,
      nights: nightRecords(view, morning - 1, seen!.me, seen!.xray),
      final: true,
    };
  const summary = view.days[morning - 1]?.summaryStructured ?? null;
  const filed = ledger?.find((d) => d.day === morning)?.players ?? [];
  return {
    morning,
    day: morning - 1,
    accusations: summary?.accusations ?? [],
    players: filed.length ? filed : summaryClaims(summary, morning - 1),
    checked: filed.length > 0,
    nights: seen ? nightRecords(view, morning - 1, seen.me, seen.xray) : [],
  };
}

/**
 * A night's records as this viewer holds them, in the log's order: a seat its own; the X-ray
 * every seat's. They are private, so a viewer with neither (a spectator, the replay without the
 * X-ray) has none. The pack's kill reaches every wolf: it is one line, the pack's.
 */
export function nightRecords(
  view: Partial<Pick<GameView, 'me' | 'xray'>>,
  night: number,
  me: string | null,
  xray: boolean,
): NightRecordLine[] {
  const held: readonly PrivateResult[] = xray
    ? Object.values(view.xray?.privateResults ?? {}).flat()
    : me
      ? (view.me?.privateResults ?? []).filter((p) => p.player === me)
      : [];
  const out: NightRecordLine[] = [];
  for (const p of [...held].sort((a, b) => a.seq - b.seq)) {
    if (p.kind !== 'night_record' || p.day !== night) continue;
    const pack = p.actor === 'wolves';
    if (pack && out.some((l) => l.seat === 'wolves')) continue;
    out.push({
      seat: pack ? 'wolves' : p.player,
      night,
      outcome: p.outcome,
      mine: pack ? !!me && !!view.me?.role?.pack?.includes(me) : p.player === me,
    });
  }
  return out;
}

/**
 * A summary's own claims in the ledger's shape, unchecked (an old archive, or no ledger): the
 * claims made that one day, each night action a reported line. Before v4 the summarizer wrote
 * its own verdict on a claim (`evidence`): kept as a plain note, since it is what agents read.
 */
export function summaryClaims(summary: CarriedSummary | null, day: number): LedgerPlayer[] {
  return (summary?.roleClaims ?? []).map((c) => ({
    player: c.player,
    history: '',
    roles: c.claimedRole
      ? [{ day, role: c.claimedRole, kind: c.retracted ? 'retracted' : 'claimed' }]
      : [],
    checks: c.evidence ? [{ text: c.evidence, fits: null }] : [],
    entries: c.nightActions.map((n): LedgerEntry => ({
      night: n.night,
      action: n.action,
      target: n.target,
      result: n.result,
      said_on_day: day,
      reported: true,
      earlier: [],
      also: [],
      planned: null,
      reason: '',
      text: claimedActionText(n),
      checks: [],
    })),
  }));
}

/** What a claimed action did, as the Record says it: "investigated", "protected". */
export const CLAIM_VERB: Record<string, string> = {
  investigate: 'investigated',
  protect: 'protected',
  shoot: 'shot',
  kill: 'attacked',
};
/** A plan, as the Record says it: "planned to protect". */
export const PLAN_VERB: Record<string, string> = {
  investigate: 'investigate',
  protect: 'protect',
  shoot: 'shoot',
  kill: 'attack',
};
const CLAIM_SAYS: Record<string, string> = {
  saved_from_attack: 'saved them from an attack',
  no_attack: 'no attack came',
  died: 'they died',
  survived: 'they survived',
  not_a_wolf: 'not a wolf',
};

/** "Night 2", or "Night not stated" when the player did not say which. */
export const nightName = (night: number) => (night ? `Night ${night}` : 'Night not stated');

/** The result the player gave, in words ("wolf", "saved them from an attack"); '' for none. */
export function resultWords(result: string): string {
  if (!result || result === 'not_said') return '';
  return CLAIM_SAYS[result] ?? result.replace(/_/g, ' ');
}

/**
 * A claimed night action in one line: "Night 1: investigated player_7 — wolf". A v3 summary's
 * free-text result reads as it was written; a result the player never gave is left off.
 */
export function claimedActionText(n: SummaryNightAction): string {
  const night = nightName(n.night);
  if (!n.action) return `${night}: ${n.target} ${n.result}`.trim();
  const result = resultWords(n.result);
  return `${night}: ${CLAIM_VERB[n.action] ?? n.action} ${n.target}${result ? ` — ${result}` : ''}`;
}

/** The player's claimed role now (their last claim), and whether they withdrew it. */
export function currentClaim(p: LedgerPlayer): { role: string; retracted: boolean } | null {
  const last = p.roles.at(-1);
  return last ? { role: last.role, retracted: last.kind === 'retracted' } : null;
}

/**
 * How an entry's plan reads beside it: none; `as-planned` (they did what they said they
 * would); `changed` (they said they would act on someone else, `planned`); `only` (a plan they
 * never reported on: the plan is the whole line).
 */
export function planKind(e: LedgerEntry): 'none' | 'as-planned' | 'changed' | 'only' {
  if (!e.reported) return 'only';
  if (!e.planned) return 'none';
  return e.planned === e.target ? 'as-planned' : 'changed';
}
