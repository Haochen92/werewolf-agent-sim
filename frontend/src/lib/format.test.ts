import { describe, expect, it } from 'vitest';
import { formatCallSeconds, formatCost } from './format';

describe('formatCost', () => {
  it('shows dollars to the cent, a sliver as under a cent, and nothing when unknown', () => {
    expect(formatCost(0.2671)).toBe('$0.27');
    expect(formatCost(1.2)).toBe('$1.20');
    expect(formatCost(0.004)).toBe('<$0.01');
    expect(formatCost(null)).toBe('');
    expect(formatCost(undefined)).toBe('');
  });
});

describe('formatCallSeconds', () => {
  it('keeps a decimal under ten seconds and rounds above', () => {
    expect(formatCallSeconds(4.06)).toBe('4.1 s');
    expect(formatCallSeconds(19.7)).toBe('20 s');
    expect(formatCallSeconds(null)).toBe('');
  });
});
