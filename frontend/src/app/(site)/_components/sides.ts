/**
 * The deal's pool of twelve, grouped by side as the site shows it: the town's six, the pack's
 * two, then the lone killer's pair and the neutral's pair (a game deals one of each pair; the
 * site never says so, the guide's subheads aside). The landing, the guide and the ticket all
 * draw their pickers from this one list.
 */
import type { Faction } from '@/stage/roles';
import type { PoolRole } from '@/types/contracts';

export const SIDES: readonly { faction: Faction; roles: readonly PoolRole[] }[] = [
  {
    faction: 'villagers',
    roles: ['investigator', 'sentinel', 'trailseer', 'vigilante', 'sigilist', 'healer'],
  },
  { faction: 'wolves', roles: ['chanteuse', 'illusionist'] },
  { faction: 'serial_killer', roles: ['serial_killer', 'necromancer'] },
  { faction: 'neutral_benign', roles: ['speculator', 'fortune_teller'] },
];

/** The pool in picker order: the arrow keys walk it. */
export const ROLES: readonly PoolRole[] = SIDES.flatMap((s) => s.roles);

/** The arrow keys' step through a radio group of roles. */
export const ARROW_STEP: Record<string, number> = {
  ArrowRight: 1,
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowUp: -1,
};
