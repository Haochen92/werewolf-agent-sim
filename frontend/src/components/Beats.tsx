'use client';

/**
 * The two earned takeovers, and the role chip that outlives the first one.
 *
 * ux_journeys §0 is binding here: full-screen moments are reserved for exactly two beats —
 * the role reveal (D8) and the game over banner (D22) — and both fire on LIVE ARRIVAL only.
 * Every caller therefore checks the store's live-seq flag before rendering these; during a
 * catch-up fold they must not appear at all, which is the rule that makes refreshing
 * mid-game safe rather than a re-run of the whole game's drama.
 */
import { hueFor, initialsFor } from '@/assets/manifest';
import { humanise } from '@/lib/format';
import { RoleIcon } from './RoleIcon';
import type { RoleCard } from '@/game/types';
import type { Winner } from '@/types/contracts';
import classes from './Beats.module.css';

const ABILITY: Record<string, string> = {
  wolf: 'Each night, your pack chooses someone to kill. By day, blend in.',
  villager: 'No night power — only your read on the table.',
  healer: 'Each night, choose one player to protect from attack.',
  investigator: 'Each night, learn one player’s true role.',
  vigilante: 'You carry bullets. Each night you may shoot — or hold your fire.',
  serial_killer: 'You kill alone, and you win alone.',
};

function factionClass(role: string): string {
  if (role === 'wolf') return classes.wolf;
  if (role === 'serial_killer') return classes.sk;
  return classes.village;
}

/** The role-conditional third line, straight from the seat's own card (D8). */
function detailFor(card: RoleCard): string | null {
  if (card.role === 'wolf') {
    return card.pack && card.pack.length > 0
      ? `Your pack: ${card.pack.join(', ')}`
      : 'You hunt alone tonight.';
  }
  if (card.role === 'vigilante' && card.bullets !== null) {
    return `${card.bullets} bullet${card.bullets === 1 ? '' : 's'}`;
  }
  if (card.role === 'serial_killer') {
    return 'Immune to night attacks. Your kills are silent.';
  }
  return null;
}

export function RoleReveal({
  seat,
  card,
  onDismiss,
}: {
  seat: string;
  card: RoleCard;
  onDismiss: () => void;
}) {
  return (
    <div className={classes.takeover} role="dialog" aria-modal="true">
      <div className={`${classes.card} ${factionClass(card.role)}`}>
        {/* The portraits' moment, when they exist; initials until then. */}
        <div
          className={classes.portrait}
          style={{ background: `hsl(${hueFor(seat)} 38% 62%)` }}
        >
          {initialsFor(seat)}
        </div>
        <h2 className={classes.roleName}>
          <RoleIcon role={card.role} size={18} /> {humanise(card.role)}
        </h2>
        <p className={classes.ability}>{ABILITY[card.role] ?? ''}</p>
        {detailFor(card) ? <p className={classes.detail}>{detailFor(card)}</p> : null}
        <button type="button" className={classes.dismiss} onClick={onDismiss} autoFocus>
          Take your seat
        </button>
      </div>
    </div>
  );
}

const WINNER_CLASS: Record<Winner, string> = {
  villagers: classes.winnerVillagers,
  wolves: classes.winnerWolves,
  serial_killer: classes.winnerSerialKiller,
};

const WINNER_LINE: Record<Winner, string> = {
  villagers: 'The Villagers win',
  wolves: 'The Wolves win',
  serial_killer: 'The Serial Killer wins',
};

/**
 * D22. While this sits on screen the R7 backlog is streaming in behind it and re-folding,
 * so dismissing it lands the player in the full theater with the X-ray unlocked — the
 * "the SK was WHO?" moment. No re-route: the live route morphs.
 */
export function WinnerTakeover({
  winner,
  onDismiss,
}: {
  winner: Winner;
  onDismiss: () => void;
}) {
  return (
    <div className={classes.takeover} role="dialog" aria-modal="true">
      <div className={classes.winner}>
        <h2 className={`${classes.winnerHeadline} ${WINNER_CLASS[winner]}`}>
          {WINNER_LINE[winner]}
        </h2>
        <p className={classes.winnerSub}>Every private thought is now on the record.</p>
        <button type="button" className={classes.dismiss} onClick={onDismiss} autoFocus>
          See what really happened
        </button>
      </div>
    </div>
  );
}

/**
 * D9. After dismissal the role lives here — the answer to "which seat am I?" is always one
 * glance away. Tapping re-opens the card as a memory aid, never as a takeover again.
 */
export function RoleChip({ card, onOpen }: { card: RoleCard; onOpen: () => void }) {
  return (
    <button type="button" className={classes.roleChip} onClick={onOpen}>
      <RoleIcon role={card.role} />
      {humanise(card.role)}
      {card.bullets !== null ? ` · ${card.bullets}` : ''}
    </button>
  );
}
