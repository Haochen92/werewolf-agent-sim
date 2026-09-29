import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import {
  docketFor,
  freshReads,
  lessonsOf,
  turnReads,
  type DocketModel,
} from './film-model';

const beats = beatsFor(FIXTURE_EVENTS, { xray: true });

function film(id: SceneBeat['id'], pick: (b: SceneBeat) => boolean) {
  const beat = beats.find((b) => b.id === id && pick(b))!;
  return docketFor(foldEvents(FIXTURE_EVENTS.slice(0, beat.end)), beat);
}
function as<K extends NonNullable<DocketModel>['kind']>(m: DocketModel | null, kind: K) {
  expect(m?.kind).toBe(kind);
  return m as Extract<DocketModel, { kind: K }>;
}

describe('the reads a turn was made from', () => {
  it('puts the speaker’s reads on the wing, not in the film', () => {
    const beat = beats.find((b) => b.id === 'day.speech' && b.seq === 200)!;
    const reads = turnReads(foldEvents(FIXTURE_EVENTS.slice(0, beat.end)), beat);
    expect(reads?.seq).toBe(175);
    expect(reads?.reads.find((r) => r.player === 'player_1')).toMatchObject({
      suspected_role: 'villager',
      confidence: 'high',
    });
  });

  it('marks the reads that are new or changed since the speaker’s previous ones', () => {
    const beat = beats.find((b) => b.id === 'day.speech' && b.seq === 200)!;
    const view = foldEvents(FIXTURE_EVENTS.slice(0, beat.end));
    // seat 8 at seq 175 against its day-2 vote reads (seq 101): seat 1 grew sure, seat 2 went
    // from unclear to villager; the rest held
    expect(freshReads(view, turnReads(view, beat))).toEqual(
      new Set(['player_1', 'player_2']),
    );
    expect(freshReads(view, null)).toEqual(new Set());
  });
});

describe('the docket', () => {
  it('lists what each voter weighed at the count, an override among them', () => {
    const m = as(
      film('vote.chip-counted', (b) => b.day === 3),
      'vote',
    );
    expect(m.rows.map((r) => r.voter)).toEqual([
      'player_1',
      'player_2',
      'player_5',
      'player_6',
      'player_7',
      'player_8',
      'player_9',
    ]);
    expect(m.rows[1].verdicts).toEqual(['override', 'override', 'not_relevant']);
  });

  it('says who had the voted-out seat right at the lynch’s card', () => {
    const m = as(
      film('lynch.card-up', (b) => b.day === 4),
      'lynch',
    );
    expect(m).toMatchObject({ seat: 'player_2', role: 'serial_killer' });
    expect(Object.fromEntries(m.rows.map((r) => [r.voter, r.mark]))).toEqual({
      player_1: 'side',
      player_7: 'side',
      player_8: 'role',
      player_9: 'side',
    });
    expect(m.note!.seq).toBeLessThan(378);
    // before the card, the film is the vote's
    expect(film('lynch.named', (b) => b.day === 4)?.kind).toBe('vote');
  });

  it('carries the typed brief at the morning', () => {
    const m = as(
      film('morning.carried-summary', (b) => b.day === 3),
      'brief',
    );
    expect(m.day).toBe(3);
    expect(m.summary?.dynamics.landscape).toMatch(/information-starved/);
  });

  it('lists what each actor did at the night whole', () => {
    const all = as(
      film('rnight.whole', (b) => b.day === 2),
      'night',
    );
    expect(all.rows.map((r) => r.actor)).toEqual([
      'player_4',
      'player_9',
      'player_2',
      'pack',
    ]);
  });

  it('lists the deal face up, and at the end how each seat went', () => {
    const dealt = as(
      film('deal.face-up', () => true),
      'deal',
    );
    expect(dealt.rows.map((r) => r.role)).toEqual([
      'villager',
      'serial_killer',
      'wolf',
      'investigator',
      'villager',
      'villager',
      'vigilante',
      'wolf',
      'healer',
    ]);
    expect(dealt.rows.every((r) => r.fate === null)).toBe(true);
    const truth = as(
      film('over.truth', () => true),
      'deal',
    );
    expect(truth.rows[7].fate).toBe('survived');
    expect(truth.rows[1].fate).toBe('day 4, voted out');
    // the curtain, where a live game rests: the case, closed
    expect(
      as(
        film('over.curtain', () => true),
        'deal',
      ).truth,
    ).toBe(true);
    expect(film('over.winners-stand', () => true)?.kind).toBe('notes');
  });

  it('gives the epilogue to the ledger, and says so when a beat has nothing on the docket', () => {
    expect(film('over.epilogue', () => true)).toBeNull();
    expect(film('rnight.hub', () => true)?.kind).toBe('empty');
  });

  it('reads a consult’s lessons with the verdict on each', () => {
    expect(lessonsOf(undefined)).toEqual([]);
  });
});
