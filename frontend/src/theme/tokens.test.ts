/**
 * The site's tokens against the theatre's: wherever the two share a CSS name, the theatre's
 * value is the one the site uses, in the TS table (which the Mantine theme reads) and in
 * `styles/tokens.css` (which the CSS modules read) alike.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { vars } from '@/stage/paint/materials';
import { SITE_TOKENS, THEATRE_ALIASES, TOKENS } from './tokens';

const CSS = readFileSync(join(__dirname, '../styles/tokens.css'), 'utf8');

/** Every `--name: value;` declared in a `:root { … }` block of tokens.css. */
function rootDeclarations(css: string): Map<string, string[]> {
  const found = new Map<string, string[]>();
  const bare = css.replace(/\/\*[\s\S]*?\*\//g, '');
  for (const block of bare.matchAll(/:root\s*\{([^}]*)\}/g)) {
    for (const [, name, value] of block[1].matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
      found.set(name, [...(found.get(name) ?? []), value.trim()]);
    }
  }
  return found;
}

const norm = (v: string) => v.replace(/\s+/g, '').toLowerCase();
const declared = rootDeclarations(CSS);
const stage = vars();

describe('site tokens', () => {
  it('take the theatre value on every name the theatre also defines', () => {
    for (const [name, value] of Object.entries(THEATRE_ALIASES)) {
      expect(value, name).toBe(stage[name as keyof typeof stage]);
    }
    for (const name of Object.keys(SITE_TOKENS)) {
      expect(
        name in stage,
        `${name} is a theatre name, so it belongs in THEATRE_NAMES`,
      ).toBe(false);
    }
  });

  it('are declared in tokens.css once, with the same value as the TS table', () => {
    for (const [name, value] of Object.entries(TOKENS)) {
      const css = declared.get(name);
      expect(css, `${name} missing from tokens.css`).toBeDefined();
      expect(css!.length, `${name} declared twice in tokens.css`).toBe(1);
      expect(norm(css![0]), name).toBe(norm(value));
    }
  });

  it('never let a tokens.css :root value shadow a theatre value', () => {
    for (const [name, values] of declared) {
      if (!(name in stage)) continue;
      for (const v of values)
        expect(norm(v), name).toBe(norm(stage[name as `--${string}`]));
    }
  });

  it('drop the mockups’ duplicate names for theatre materials', () => {
    for (const gone of [
      '--killer',
      '--panel2',
      '--paperdk',
      '--inkTown',
      '--inkWolf',
      '--inkSk',
      '--aqua',
    ]) {
      expect(declared.has(gone), gone).toBe(false);
    }
  });
});
