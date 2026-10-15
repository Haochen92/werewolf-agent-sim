/**
 * The epilogue's sheet, as data (handoff §4.10): what the finished game taught, arranged the
 * way the ledger shows it. The wire keys each observation by the ROLE it was made from, not
 * the seat, so the sheet has one tab per role (with the seats that held it), a tally of the
 * verdicts, and the rows grouped under the phase they came from.
 */
import type { MemoryExtracted } from '@/types/contracts';

export type Observation = MemoryExtracted['observations'][number];
export type Lesson = MemoryExtracted['strategy_points'][number];
export type VerdictKind = 'worked' | 'cost' | 'mixed' | 'unclear';
export type ActionPhase = Observation['action_phase'];

/** The extractor's `net_verdict`, as the patch names it. */
export function verdictKind(net: string): VerdictKind {
  const v = net.trim().toLowerCase();
  return v === 'positive'
    ? 'worked'
    : v === 'negative'
      ? 'cost'
      : v === 'mixed'
        ? 'mixed'
        : 'unclear';
}

/** The order the tally reads in: what worked, then what was mixed, what cost, what is unclear. */
export const VERDICT_ORDER: readonly VerdictKind[] = ['worked', 'mixed', 'cost', 'unclear'];
export const ROLE_ORDER = [
  'villager',
  'healer',
  'investigator',
  'vigilante',
  'wolf',
  'serial_killer',
] as const;
export const PHASE_ORDER: readonly ActionPhase[] = [
  'day_discussion',
  'day_vote',
  'night_action',
];
export const PHASE_NAME: Record<ActionPhase, string> = {
  day_discussion: 'The discussion',
  day_vote: 'The vote',
  night_action: 'The night',
};

export interface LedgerRow {
  /** Its place in the extraction, a stable key. */
  index: number;
  obs: Observation;
  verdict: VerdictKind;
}

export interface LedgerTab {
  role: string;
  /** The seats that held this role, in seat order. */
  seats: string[];
  rows: LedgerRow[];
  tally: Record<VerdictKind, number>;
  /** One pip per observation, grouped by verdict in `VERDICT_ORDER`. */
  pips: VerdictKind[];
}

/** One tab per role that has observations, in the cast's order; `roles` is seat → role. */
export function ledgerTabs(
  extracted: MemoryExtracted,
  roles: Record<string, string>,
): LedgerTab[] {
  const known = [
    ...ROLE_ORDER,
    ...extracted.observations
      .map((o) => o.perspective)
      .filter((p) => !(ROLE_ORDER as readonly string[]).includes(p)),
  ];
  return [...new Set(known)].flatMap((role) => {
    const rows = extracted.observations
      .map((obs, index) => ({ index, obs, verdict: verdictKind(obs.net_verdict) }))
      .filter((r) => r.obs.perspective === role);
    if (!rows.length) return [];
    const tally = { worked: 0, cost: 0, mixed: 0, unclear: 0 };
    for (const r of rows) tally[r.verdict]++;
    const seats = Object.keys(roles)
      .filter((s) => roles[s] === role)
      .sort((a, b) => Number(a.replace(/\D/g, '')) - Number(b.replace(/\D/g, '')));
    return [
      {
        role,
        seats,
        rows,
        tally,
        pips: VERDICT_ORDER.flatMap((v) => Array<VerdictKind>(tally[v]).fill(v)),
      },
    ];
  });
}

/** A tab's rows under the phase they came from, in the game's order of phases; empty ones dropped. */
export function byPhase(rows: readonly LedgerRow[]) {
  return PHASE_ORDER.map((phase) => ({
    phase,
    rows: rows.filter((r) => r.obs.action_phase === phase),
  })).filter((g) => g.rows.length > 0);
}

/** The outcome text opens with the verdict ("Negative. …"); the patch says it already. */
export function stripVerdict(text: string): string {
  return text.replace(/^(negative|positive|mixed|unclear)[.:]?\s*/i, '');
}
