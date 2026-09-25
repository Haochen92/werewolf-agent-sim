import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { filmFor, lessonsOf, turnReads, type FilmModel } from './film-model';

const beats = beatsFor(FIXTURE_EVENTS, { xray: true });
const whole = foldEvents(FIXTURE_EVENTS);

function film(id: SceneBeat['id'], pick: (b: SceneBeat) => boolean, ahead = true) {
  const beat = beats.find((b) => b.id === id && pick(b))!;
  const view = foldEvents(FIXTURE_EVENTS.slice(0, beat.end));
  return filmFor(view, beat, ahead ? whole : null);
}
function as<K extends NonNullable<FilmModel>['kind']>(m: FilmModel | null, kind: K) {
  expect(m?.kind).toBe(kind);
  return m as Extract<FilmModel, { kind: K }>;
}

describe('the film at a turn', () => {
  it('holds the note written after the turn and the lessons weighed before it', () => {
    const m = as(
      film('day.speech', (b) => b.seq === 200),
      'inside',
    );
    expect(m).toMatchObject({ seat: 'player_8', role: 'wolf', when: 'turn' });
    expect(m.note?.seq).toBe(203);
    expect(m.consultSeq).toBe(174);
    expect(m.readsSeq).toBe(175);
    // seat 8 spoke at 176 after that consult: the lessons were carried over to this turn
    expect(m.carried).toBe(true);
    expect(m.lessons.map((l) => [l.n, l.verdict])).toEqual([
      [1, 'follow'],
      [2, 'follow'],
      [3, 'not_relevant'],
    ]);
  });

  it('has no note yet without the view ahead: the note lands after the turn’s beat', () => {
    expect(
      as(
        film('day.speech', (b) => b.seq === 200, false),
        'inside',
      ).note,
    ).toBeNull();
  });

  it('holds a pass’s note and lessons too, and none on day 1 (no memory yet)', () => {
    expect(
      as(
        film('day.pass', (b) => b.seq === 183),
        'inside',
      ).note?.seq,
    ).toBe(185);
    const d1 = as(
      film('day.pass', (b) => b.seq === 15),
      'inside',
    );
    expect(d1.lessons).toEqual([]);
    expect(d1.consultSeq).toBeNull();
  });

  it('puts the speaker’s reads on the wing, not in the film', () => {
    const beat = beats.find((b) => b.id === 'day.speech' && b.seq === 200)!;
    const reads = turnReads(foldEvents(FIXTURE_EVENTS.slice(0, beat.end)), beat);
    expect(reads?.seq).toBe(175);
    expect(reads?.reads.find((r) => r.player === 'player_1')).toMatchObject({
      suspected_role: 'villager',
      confidence: 'high',
    });
  });
});

describe('the film elsewhere', () => {
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

  it('holds an actor’s consult and note at its spoke, the pack’s two notes at the pack’s', () => {
    const spoke = as(
      film('rnight.spoke', (b) => b.day === 2 && b.seq === 126),
      'inside',
    );
    expect(spoke).toMatchObject({ seat: 'player_4', role: 'investigator', when: 'night' });
    expect(spoke.lessons).toHaveLength(3);
    const pack = as(
      film('rnight.spoke', (b) => b.day === 2 && b.seq === 140),
      'pack',
    );
    expect(pack.seats).toEqual(['player_3', 'player_8']);
    // the note that night, never a later one
    expect(pack.notes.every((n) => n.note === null || n.note.seq < 159)).toBe(true);
    expect(pack.lines).toBe(4);
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
  });

  it('gives the epilogue to the ledger, and says so when a beat has nothing inside', () => {
    expect(film('over.epilogue', () => true)).toBeNull();
    expect(film('rnight.hub', () => true)?.kind).toBe('empty');
  });

  it('reads a consult’s lessons with the verdict on each', () => {
    expect(lessonsOf(undefined)).toEqual([]);
  });
});
