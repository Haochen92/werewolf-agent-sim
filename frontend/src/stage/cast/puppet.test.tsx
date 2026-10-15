import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { SPRITES, type Character, type DayState } from '@/assets/manifest';
import { geometry } from '../units';
import { Puppet, puppetBox } from './Puppet';
import { ChipSprite } from './ChipSprite';

// The four added 2026-10-03: no workbench bench casts an arbitrary character (the benches draw
// the fixture's legacy cast), so this is their check that they stand and show their faces.
const ADDED: Character[] = ['kitsune', 'mushroom', 'lionCub', 'automaton'];
const STATES: DayState[] = ['base', 'talking', 'thinking', 'out'];

describe('the four added puppets', () => {
  it.each(ADDED)('%s stands in every state with its own sprite and shadow', (character) => {
    const g = geometry('live');
    for (const state of STATES) {
      const out = renderToStaticMarkup(
        <Puppet g={g} character={character} seat={3} state={state} shadow />,
      );
      expect(out).toContain(`sprites/day/${character}/${state}.webp`);
      expect(SPRITES.shadow.day[character][state].src).toContain(
        `sprites/shadow/day/${character}/${state}.webp`,
      );
      // one body height on the stage, the figure's box inside the stage
      const box = puppetBox(g, character, state);
      expect(box.w).toBeGreaterThan(0);
      expect(box.top).toBeGreaterThanOrEqual(0);
    }
  });

  it.each(ADDED)('%s shows its head portrait in a chip', (character) => {
    expect(renderToStaticMarkup(<ChipSprite character={character} />)).toContain(
      `sprites/day/${character}/head.webp`,
    );
  });
});
