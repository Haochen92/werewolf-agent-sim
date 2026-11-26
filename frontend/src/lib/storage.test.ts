import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { byokKeys } from './storage';

// node has no localStorage: a Map stands in for the browser's
beforeEach(() => {
  const store = new Map<string, string>();
  vi.stubGlobal('window', {
    localStorage: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    },
  });
});
afterEach(() => vi.unstubAllGlobals());

describe('byokKeys', () => {
  it('keeps one key per company, each deleted on its own', () => {
    byokKeys.set('anthropic', 'sk-ant-aaaa1111');
    byokKeys.set('google', 'AIzaBBBB2222');
    expect(byokKeys.all()).toEqual([
      { provider: 'anthropic', key: 'sk-ant-aaaa1111' },
      { provider: 'google', key: 'AIzaBBBB2222' },
    ]);
    byokKeys.clear('anthropic');
    expect(byokKeys.all()).toEqual([{ provider: 'google', key: 'AIzaBBBB2222' }]);
  });

  it("moves the old single slot's key to the company its prefix names", () => {
    window.localStorage.setItem('byok_key', 'sk-ant-old');
    byokKeys.migrate('google');
    expect(byokKeys.get('anthropic')).toBe('sk-ant-old');
    expect(window.localStorage.getItem('byok_key')).toBeNull();
  });

  it("files a prefix that names no company under the model's, and waits when there is no model", () => {
    window.localStorage.setItem('byok_key', 'sk-plain');
    byokKeys.migrate(null);
    expect(window.localStorage.getItem('byok_key')).toBe('sk-plain');
    byokKeys.migrate('deepseek');
    expect(byokKeys.get('deepseek')).toBe('sk-plain');
    expect(window.localStorage.getItem('byok_key')).toBeNull();
  });
});
