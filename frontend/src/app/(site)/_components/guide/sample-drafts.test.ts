import { describe, expect, it } from 'vitest';
import { sampleDraft } from './sample-drafts';

const ask = { steer: '', current: '', book: null, taken: 0 };

describe('the guide’s sample drafts', () => {
  it('opens with a plain line, a different one each draft', () => {
    const lines = [0, 1, 2].map((taken) => sampleDraft({ ...ask, taken }));
    expect(new Set(lines).size).toBe(3);
  });

  it('follows a steer: the seat it names, in the tone it asks for', () => {
    expect(sampleDraft({ ...ask, steer: 'softer, seat 6' })).toMatch(
      /seat 6 has me uneasy/,
    );
    expect(sampleDraft({ ...ask, steer: 'push on seat 3' })).toMatch(
      /^Seat 3, that is twice/,
    );
    expect(sampleDraft({ ...ask, steer: 'short' })).toBe(
      'Seat 5: who did you vote for, and why?',
    );
  });

  it('reads the shared notes: a guess first, else the note, cut short', () => {
    const book = { notes: { 2: 'Defended seat 5 too fast' }, guesses: {} };
    expect(sampleDraft({ ...ask, book })).toContain(
      'My note on them: "Defended seat 5 too fast".',
    );
    const guessed = { notes: { 2: 'quiet' }, guesses: { 2: 'serial_killer' } };
    expect(sampleDraft({ ...ask, book: guessed })).toMatch(
      /^I think seat 2 could be the serial killer/,
    );
    const long = { notes: { 2: 'x'.repeat(90) } };
    expect(sampleDraft({ ...ask, book: long })).toContain(`"${'x'.repeat(57)}…"`);
  });

  it('a redraft revises about the noted seat', () => {
    const book = { notes: { 2: 'quiet' } };
    expect(sampleDraft({ ...ask, current: 'Hello.', book })).toMatch(
      /^Put another way: seat 2/,
    );
  });
});
