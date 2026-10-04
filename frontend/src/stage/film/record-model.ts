/**
 * The case file's Record, as data: what the table had on record each morning (owner,
 * 2026-10-04). Every morning after a summarised day the agents read the day summary's
 * accusations and the claim ledger: every role claim and claimed night action, checked by code
 * against the game master's record (`GET /games/{id}/ledger`). All of it is public, so the
 * Record opens without the X-ray, live and in the replay.
 *
 * A page is one morning: the ledger read that morning and the accusations of the day before.
 * The pages are the mornings the view has reached (never one past the stage); the latest is
 * open unless the viewer paged back. A game whose ledger is missing (an old archive, or a
 * failed fetch) shows each summary's own claims instead, with no checks.
 */
import type {
  CarriedSummary,
  GameView,
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

/**
 * The mornings whose record the view has reached, oldest first: morning N once day N-1's
 * summary is in and day N has begun, or while the X-ray's carried-summary beat for day N-1 is
 * on stage. The summary of the day the game ended on is never read: no morning follows it.
 */
export function recordMornings(
  view: Pick<GameView, 'days' | 'timeline'>,
  beat: Pick<SceneBeat, 'id' | 'day'>,
): number[] {
  return Object.values(view.days)
    .filter(
      (d) =>
        (d.summary || d.summaryStructured) &&
        (view.timeline.some((t) => t.day === d.day + 1 && t.phase === 'day') ||
          (recordBeat(beat) && beat.day === d.day)),
    )
    .map((d) => d.day + 1)
    .sort((a, b) => a - b);
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

/** One morning's page: the ledger's claims when it has any, else the summary's own. */
export function recordPage(
  view: Pick<GameView, 'days'>,
  morning: number,
  ledger: readonly LedgerDay[] | null | undefined,
): RecordPage {
  const summary = view.days[morning - 1]?.summaryStructured ?? null;
  const filed = ledger?.find((d) => d.day === morning)?.players ?? [];
  return {
    morning,
    day: morning - 1,
    accusations: summary?.accusations ?? [],
    players: filed.length ? filed : summaryClaims(summary, morning - 1),
    checked: filed.length > 0,
  };
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
