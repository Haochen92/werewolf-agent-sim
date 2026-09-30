import { describe, expect, it } from 'vitest';
import { PHONE_QUERY, composerBox, composerShown, wordCount, wordsText } from './composer';

describe('wordCount', () => {
  it('counts runs of anything but white space', () => {
    expect(wordCount('')).toBe(0);
    expect(wordCount('   \n ')).toBe(0);
    expect(wordCount('Seat 5, why so quick?')).toBe(5);
    expect(wordCount('  one\ttwo\n\nthree  ')).toBe(3);
    expect(wordCount('—')).toBe(1);
  });
  it('says one word, or so many words', () => {
    expect(wordsText(0)).toBe('0 words');
    expect(wordsText(1)).toBe('1 word');
    expect(wordsText(42)).toBe('42 words');
  });
});

describe('composerShown', () => {
  it('shows while opened and the turn is still open', () => {
    expect(composerShown(true, {})).toBe(true);
    expect(composerShown(true, { closed: false })).toBe(true);
  });
  it('shuts once the turn is closed, and never shows unopened', () => {
    expect(composerShown(true, { closed: true })).toBe(false);
    expect(composerShown(false, { closed: false })).toBe(false);
  });
});

describe('composerBox', () => {
  it('fills the whole frame when the browser says nothing of what is visible', () => {
    expect(composerBox(null)).toBeNull();
    expect(composerBox(undefined)).toBeNull();
    expect(composerBox({ width: 0, height: 0, offsetLeft: 0, offsetTop: 0 })).toBeNull();
  });
  it('keeps to the visible part: a soft keyboard up leaves the top 200 px', () => {
    expect(
      composerBox({ width: 667, height: 200.4, offsetLeft: 0, offsetTop: 12.2 }),
    ).toEqual({ left: 0, top: 12, width: 667, height: 200 });
  });
});

describe('PHONE_QUERY', () => {
  it('is the phone frame: 900 css px wide or narrower', () => {
    expect(PHONE_QUERY).toBe('(max-width: 900px)');
  });
});
