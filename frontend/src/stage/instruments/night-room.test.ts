import { describe, expect, it } from 'vitest';
import { countLeft, countText, URGENT_MS } from '../countdown';
import {
  betRoles,
  LONE_WOLF_SEALED,
  NO_ACTION_PLATE,
  plateLabel,
  sealedLabel,
  usesNote,
} from '../scenes/ShelfRoomScene';
import { packEntries } from '../scenes/PackScene';
import type { NightView } from '@/game/types';

describe('the countdown on the plate', () => {
  it('reads m:ss, rounding up, and -:-- with no deadline', () => {
    expect(countText(120_000)).toBe('2:00');
    expect(countText(74_000)).toBe('1:14');
    expect(countText(9_001)).toBe('0:10');
    expect(countText(500)).toBe('0:01');
    expect(countText(0)).toBe('0:00');
    expect(countText(null)).toBe('-:--');
  });

  it('drains the bar with the time left, and has none without a deadline', () => {
    expect(countLeft({ totalMs: 120_000 }, 120_000)).toBe(1);
    expect(countLeft({ totalMs: 120_000 }, 30_000)).toBe(0.25);
    expect(countLeft({ totalMs: 120_000 }, -5)).toBe(0);
    expect(countLeft({ totalMs: 120_000 }, 180_000)).toBe(1);
    expect(countLeft(null, 1000)).toBeNull();
    expect(countLeft({ totalMs: 120_000 }, null)).toBeNull();
    expect(countLeft({ totalMs: 0 }, 1000)).toBeNull();
    expect(URGENT_MS).toBe(10_000);
  });
});

describe('the plate', () => {
  it('asks, then names the act', () => {
    expect(plateLabel('healer_target', null)).toBe('Choose a seat to protect');
    expect(plateLabel('healer_target', 'player_1')).toBe('Protect seat 1');
    expect(plateLabel('investigator_target', 'player_4')).toBe('Check seat 4');
    expect(plateLabel('vigilante_target', 'player_2')).toBe('Shoot seat 2');
    expect(plateLabel('serial_killer_target', 'player_5')).toBe('Kill seat 5');
  });

  it('names every ten-seat act', () => {
    expect(plateLabel('sentinel_target', null)).toBe('Choose a seat to watch');
    expect(plateLabel('sentinel_target', 'player_3')).toBe('Watch seat 3');
    expect(plateLabel('trailseer_target', 'player_3')).toBe('Follow seat 3');
    expect(plateLabel('sigil_target', 'player_3')).toBe('Mark seat 3');
    expect(plateLabel('block_target', 'player_3')).toBe('Block seat 3');
    expect(plateLabel('conceal', null)).toBe('Hide the victim’s role');
    expect(plateLabel('speculator_pick', null)).toBe('Choose a side');
    expect(plateLabel('speculator_pick', 'town')).toBe('Pick the Town');
    expect(plateLabel('speculator_pick', 'lone_killer')).toBe('Pick the lone killer');
    expect(plateLabel('speculator_pick', 'self')).toBe('Pick yourself');
  });

  it('asks the necromancer for both a body and a seat', () => {
    expect(plateLabel('necromancer_target', null)).toBe('Choose a body and a seat');
    expect(plateLabel('necromancer_target', 'player_5')).toBe(
      'Choose a body to act through',
    );
    expect(plateLabel('necromancer_target', null, { body: 'player_3' })).toBe(
      'Through seat 3, choose a seat',
    );
    expect(plateLabel('necromancer_target', 'player_5', { body: 'player_3' })).toBe(
      'Through seat 3, act on seat 5',
    );
  });

  it('bets on a seat, on yourself, or on a seat as a role', () => {
    expect(plateLabel('bet_target', null)).toBe('Choose a seat to bet on');
    expect(plateLabel('bet_target', 'player_4', { me: 'player_8' })).toBe('Bet on seat 4');
    expect(plateLabel('bet_target', 'player_8', { me: 'player_8' })).toBe(
      'Bet on yourself',
    );
    expect(
      plateLabel('bet_target', 'player_4', { roleNamed: 'healer', me: 'player_8' }),
    ).toBe('Bet on seat 4 as Healer');
  });

  it('says each no-action word on the second button', () => {
    expect(NO_ACTION_PLATE).toEqual({
      hold_fire: 'Hold fire',
      no_check: 'Keep your checks',
      no_watch: 'Keep your watches',
      keep_sigil: 'Keep your sigils',
      no_conceal: 'Keep your conceals',
      stay_put: 'Stay put',
      not_yet: 'Not yet',
    });
  });
});

describe('the card’s count', () => {
  it('counts each limited ability in its own word', () => {
    expect(usesNote('investigator', 2)).toBe('2 checks left');
    expect(usesNote('investigator', 1)).toBe('your last check');
    expect(usesNote('sentinel', 2)).toBe('2 watches left');
    expect(usesNote('sigilist', 1)).toBe('your last sigil');
    expect(usesNote('illusionist', 2)).toBe('2 conceals left');
    expect(usesNote('fortune_teller', 2)).toBe('2 self-bets left');
    expect(usesNote('vigilante', 2)).toBe('2 caps left');
    // the nine-seat vigilante counts its bullets
    expect(usesNote('vigilante', null, 1)).toBe('your last cap');
    // none left, no count (the speculator's one pick), or no limit: no line
    expect(usesNote('sentinel', 0)).toBeUndefined();
    expect(usesNote('speculator', 1)).toBeUndefined();
    expect(usesNote('healer', null)).toBeUndefined();
  });
});

describe('the fortune teller’s roles', () => {
  it('names the pool of twelve, the dealt ones when the lineup is known, never its own', () => {
    const pool = betRoles([], 'fortune_teller');
    expect(pool).toHaveLength(11);
    expect(pool).not.toContain('villager');
    expect(pool).not.toContain('wolf');
    const lineup = [
      'healer',
      'investigator',
      'serial_killer',
      'fortune_teller',
      'chanteuse',
    ];
    expect(betRoles(lineup, 'fortune_teller')).toEqual([
      'healer',
      'investigator',
      'chanteuse',
      'serial_killer',
    ]);
  });
});

describe('the sealed plate', () => {
  it('says what was done tonight, one line per act', () => {
    expect(sealedLabel('healer_target', 'player_3')).toBe('Seat 3 is protected tonight');
    expect(sealedLabel('investigator_target', 'player_3')).toBe('You check seat 3 tonight');
    expect(sealedLabel('vigilante_target', 'player_3')).toBe('You shoot seat 3 tonight');
    expect(sealedLabel('vigilante_target', null)).toBe('You hold fire tonight');
    expect(sealedLabel('serial_killer_target', 'player_3')).toBe(
      'Seat 3 is marked tonight',
    );
    expect(sealedLabel('wolf_vote', 'player_4')).toBe('You vote seat 4 tonight');
    expect(LONE_WOLF_SEALED(4)).toBe('Seat 4 is your kill tonight');
    // a remount that lost the seat still says the act is in
    expect(sealedLabel('healer_target', undefined)).toBe('Your act is in');
  });

  it('seals every ten-seat act, and every no-action word', () => {
    expect(sealedLabel('sentinel_target', 'player_3')).toBe('You watch seat 3 tonight');
    expect(sealedLabel('trailseer_target', 'player_3')).toBe('You follow seat 3 tonight');
    expect(sealedLabel('sigil_target', 'player_3')).toBe('You mark seat 3 tonight');
    expect(sealedLabel('block_target', 'player_3')).toBe('Seat 3 is blocked tonight');
    expect(sealedLabel('carrier_kill', 'player_3')).toBe(
      'Seat 3 is the pack’s kill tonight',
    );
    expect(sealedLabel('conceal', 'conceal')).toBe('The victim’s role is hidden tonight');
    expect(sealedLabel('conceal', 'no_conceal')).toBe('You keep your conceals tonight');
    expect(sealedLabel('investigator_target', 'no_check')).toBe(
      'You keep your checks tonight',
    );
    expect(sealedLabel('sentinel_target', 'no_watch')).toBe(
      'You keep your watches tonight',
    );
    expect(sealedLabel('sigil_target', 'keep_sigil')).toBe('You keep your sigils tonight');
    expect(sealedLabel('necromancer_target', 'stay_put')).toBe('You stay put tonight');
    // the act that named no one, as only the kind knows it
    expect(sealedLabel('sentinel_target', null)).toBe('You keep your watches tonight');
    expect(sealedLabel('speculator_pick', 'town')).toBe('You pick the Town');
    expect(sealedLabel('speculator_pick', 'wolves')).toBe('You pick the Wolves');
    expect(sealedLabel('speculator_pick', 'self')).toBe('You pick yourself');
    expect(sealedLabel('speculator_pick', 'not_yet')).toBe(
      'You keep your pick for another night',
    );
    expect(sealedLabel('necromancer_target', 'player_5', { body: 'player_3' })).toBe(
      'Through seat 3, you act on seat 5 tonight',
    );
    expect(sealedLabel('bet_target', 'player_4')).toBe('You bet on seat 4');
    expect(sealedLabel('bet_target', 'player_4', { roleNamed: 'healer' })).toBe(
      'You bet on seat 4 as Healer',
    );
    expect(sealedLabel('bet_target', 'player_8', { me: 'player_8' })).toBe(
      'You bet on yourself',
    );
  });
});

describe('the pack chat', () => {
  it('orders talk, votes and the decision, with the morning note after', () => {
    const night = {
      wolfChannel: [
        { seq: 33, round: 1, wolf: 'player_3', message: 'a' },
        { seq: 271, round: 2, wolf: 'game_master', message: 'failed' },
      ],
      wolfVotes: [
        { seq: 55, wolf: 'player_8', votee: 'player_1' },
        { seq: 54, wolf: 'player_3', votee: 'player_1' },
      ],
      wolfKill: 'player_1',
    } as unknown as NightView;
    expect(packEntries(night).map((e) => e.kind)).toEqual([
      'line',
      'vote',
      'vote',
      'decided',
      'gm',
    ]);
    expect(packEntries(null)).toEqual([]);
  });

  it('keeps a passed round, and puts the carrier’s kill after the talk', () => {
    const night = {
      wolfChannel: [
        { seq: 63, round: 1, wolf: 'player_5', message: 'seat 7?', passed: false },
        { seq: 83, round: 2, wolf: 'player_6', message: '', passed: true },
      ],
      wolfVotes: [],
      wolfKill: 'player_7',
      carrier: 'player_5',
    } as unknown as NightView;
    const entries = packEntries(night);
    expect(entries.map((e) => e.kind)).toEqual(['line', 'line', 'decided']);
    expect(entries[1]).toMatchObject({ kind: 'line', passed: true });
    expect(entries[2]).toMatchObject({
      seq: 83.5,
      target: 'player_7',
      carrier: 'player_5',
    });
  });
});
