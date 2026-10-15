import { describe, expect, it } from 'vitest';
import { editorStays } from './notebook';

describe('the note editor stays open while the beats go by', () => {
  const alive = {};
  const dead = { dead: { role: 'villager' } };

  it('stays on a living seat that can be written on, whatever the beat', () => {
    expect(editorStays({ seat: 5, dead: false }, alive, true)).toBe(true);
  });

  it('closes when its seat dies', () => {
    expect(editorStays({ seat: 5, dead: false }, dead, true)).toBe(false);
  });

  it('stays on a seat that was already dead when its notes were opened', () => {
    expect(editorStays({ seat: 5, dead: true }, dead, true)).toBe(true);
  });

  it('closes when the seat can no longer be written on, or is not on the rail', () => {
    expect(editorStays({ seat: 5, dead: false }, alive, false)).toBe(false);
    expect(editorStays({ seat: 5, dead: false }, undefined, true)).toBe(false);
  });

  it('nothing open stays nothing', () => {
    expect(editorStays(null, alive, true)).toBe(false);
  });
});
