import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import type { Ballot, DayVote } from '@/game/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import {
  candidatesOf,
  landOrder,
  lastLine,
  litPlates,
  resultWords,
  score,
  tally,
} from './vote-count';
import { readMark, whoHadThemRight } from '../film/film-model';

const b = (seq: number, voter: number, votee: number | 'abstain'): Ballot => ({
  seq,
  voter: `player_${voter}`,
  votee: votee === 'abstain' ? 'abstain' : `player_${votee}`,
});

const vote = (o: Partial<DayVote>): DayVote => ({
  ballots: [],
  outcome: null,
  lynched: null,
  lynchedRole: null,
  voteCounts: {},
  noLynchStreak: 0,
  ...o,
});

const view = foldEvents(FIXTURE_EVENTS);

describe('the count', () => {
  it('lays the plates out in seat order with the abstain saucer last', () => {
    expect(candidatesOf([b(1, 1, 'abstain'), b(2, 2, 7), b(3, 3, 2)])).toEqual([
      'player_2',
      'player_7',
      'abstain',
    ]);
  });

  it('lands the chip that settles the winner last (day 4: seat 8’s ballot for seat 2)', () => {
    const ballots = view.days[4].vote.ballots;
    const order = landOrder(ballots);
    expect(order).toHaveLength(ballots.length);
    expect(order.at(-1)).toMatchObject({ voter: 'player_8', votee: 'player_2' });
    // the others keep the log's order
    expect(order.slice(0, -1).map((x) => x.seq)).toEqual([378, 379, 380, 381]);
  });

  it('holds back the winner’s last chip even when it came early (day 3: 6 to 1)', () => {
    const order = landOrder(view.days[3].vote.ballots);
    expect(order.at(-1)?.votee).toBe('player_6');
    expect(order.at(-1)?.seq).toBe(248);
  });

  it('keeps the log’s order on a tie: nothing settles it', () => {
    const ballots = [b(1, 1, 2), b(2, 2, 1), b(3, 3, 2), b(4, 4, 1)];
    expect(landOrder(ballots)).toEqual(ballots);
  });

  it('reads the score out largest first, a single plate against nothing', () => {
    expect(score({ player_7: 2, player_2: 3 })).toBe('3 to 2');
    expect(score({ abstain: 9 })).toBe('9 to 0');
    expect(score(tally(view.days[3].vote.ballots))).toBe('6 to 1');
  });
});

describe('the result', () => {
  it('names the voted-out seat and the score', () => {
    expect(resultWords(view.days[4].vote)).toEqual({
      title: 'Seat 2',
      body: 'Voted out, 3 to 2.',
    });
    expect(litPlates(view.days[4].vote)).toEqual(['player_2']);
  });

  it('says the table abstains, and lights the saucer', () => {
    expect(resultWords(view.days[2].vote)).toEqual({
      title: 'The table abstains',
      body: '9 to 0. No one is voted out.',
    });
    expect(litPlates(view.days[2].vote)).toEqual(['abstain']);
  });

  it('says a tie, lights the tied plates equally, and gives the game master’s line', () => {
    const tie = vote({
      ballots: [b(1, 1, 2), b(2, 2, 1), b(3, 3, 2), b(4, 4, 1), b(5, 5, 'abstain')],
      outcome: 'tie',
      voteCounts: { player_2: 2, player_1: 2, abstain: 1 },
    });
    expect(resultWords(tie, 'A tie: no one is voted out.')).toEqual({
      title: 'A tie, 2 to 2 to 1',
      body: 'A tie: no one is voted out.',
    });
    expect(resultWords(tie)?.body).toBe('No one is voted out.');
    expect(litPlates(tie)).toEqual(['player_1', 'player_2']);
  });

  it('takes the last line of the game master’s tally', () => {
    expect(
      lastLine('\nHere is the vote:\n  a\nPlayer player_2 has been voted out.\n'),
    ).toBe('Player player_2 has been voted out.');
    expect(lastLine('')).toBeNull();
  });
});

describe('who had them right', () => {
  it('marks the role, the side (wolves and the killer together), or nothing', () => {
    expect(readMark('serial_killer', 'serial_killer')).toBe('role');
    expect(readMark('wolf', 'serial_killer')).toBe('side');
    expect(readMark('healer', 'villager')).toBe('side');
    expect(readMark('wolf', 'villager')).toBe('none');
    expect(readMark('unclear', 'villager')).toBe('none');
    expect(readMark(null, 'villager')).toBe('none');
  });

  it('reads each voter’s last read before the ballots (day 4, seat 2): bench 65’s table', () => {
    const rows = whoHadThemRight(view, 4, 'player_2', 'serial_killer');
    expect(rows.map((r) => [r.voter, r.suspected, r.mark])).toEqual([
      ['player_1', 'wolf', 'side'],
      ['player_9', 'wolf', 'side'],
      ['player_7', 'wolf', 'side'],
      ['player_8', 'serial_killer', 'role'],
    ]);
  });
});
