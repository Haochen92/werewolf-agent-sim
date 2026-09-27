import { describe, expect, it } from 'vitest';
import { MAX_NAME, nameProblem, tidyName } from './names';

describe('a player name', () => {
  it('is tidied the way the server tidies it', () => {
    expect(tidyName('  kei   mori ')).toBe('kei mori');
  });

  it('takes letters in any script, digits and the marks names use', () => {
    for (const ok of [
      'Liu Haochen',
      '刘浩晨',
      'Zoë',
      "O'Brien",
      'J.-P. 2',
      'a'.repeat(MAX_NAME),
    ])
      expect(nameProblem(ok)).toBeNull();
  });

  it('says why it cannot board', () => {
    expect(nameProblem('   ')).toBe('A name is needed.');
    expect(nameProblem('a'.repeat(MAX_NAME + 1))).toBe('At most 12 characters.');
    expect(nameProblem('hao🐺')).toMatch(/not 🐺/);
    expect(nameProblem('<b>')).toMatch(/not < >/);
  });
});
