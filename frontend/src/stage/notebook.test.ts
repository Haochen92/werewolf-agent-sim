import { describe, expect, it } from 'vitest';
import { nightWords, parseNotebook } from './notebook';

describe('the player’s file on a seat (2026-10-18)', () => {
  it('reads back claims, nights and lines, and drops what is not one', () => {
    const book = parseNotebook({
      claims: { 3: 'trailseer', 4: 'nonsense' },
      nights: { 3: { 1: { target: 5, seen: [7, 'x', 1], none: 'yes', result: 9 } }, x: {} },
      lines: { 3: { 2: 'first to name seat 5' }, 0: { 1: 'no seat' } },
    });
    expect(book.claims).toEqual({ 3: 'trailseer' });
    expect(book.nights).toEqual({ 3: { 1: { target: 5, seen: [7, 1] } } });
    expect(book.lines).toEqual({ 3: { 2: 'first to name seat 5' } });
  });

  it('a note kept before the files is the seat’s lines on day 1, never over a line there', () => {
    expect(parseNotebook({ notes: { 5: 'quiet' } }).lines).toEqual({ 5: { 1: 'quiet' } });
    expect(
      parseNotebook({ notes: { 5: 'old' }, lines: { 5: { 1: 'new' } } }).lines,
    ).toEqual({ 5: { 1: 'new' } });
  });

  it('says a night as the claimed role does it', () => {
    expect(nightWords('investigator', { target: 7, result: 'suspicious' })).toBe(
      'checked player_7; reads Suspicious',
    );
    expect(nightWords('sentinel', { target: 2, none: true })).toBe(
      'watched player_2; saw no one',
    );
    expect(nightWords(undefined, { target: 2 })).toBe('acted on player_2');
  });
});
