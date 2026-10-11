import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { CARD_TEXT, LEGACY_CARD_TEXT, cardTextFor, isNineSeat } from '../card-text';
import { FACTION_NAME, WINNER_NAME } from '../roles';
import { PHASE2_GAME, PHASE3_GAME } from '../workbench/fixture';
import { RoleCard } from './Card';
import { CardOverlay, FramedCard } from './FramedCard';

/** An investigator's card in the game shown: opened, framed and full face. */
const investigator = (events: typeof PHASE2_GAME.events) => {
  const legacy = isNineSeat(foldEvents(events));
  return [
    <CardOverlay key="o" role="investigator" seat={4} u={1} legacy={legacy} />,
    <FramedCard
      key="f"
      role="investigator"
      x={0}
      foot={0}
      height={200}
      u={1}
      legacy={legacy}
    />,
    <RoleCard key="r" role="investigator" seat={4} w={340} legacy={legacy} />,
  ].map((el) => renderToStaticMarkup(el).replace(/&#x27;/g, "'"));
};

describe('card words by the game’s rules', () => {
  it('an archived nine-seat game’s investigator learns an exact role every night', () => {
    const [overlay, framed, face] = investigator(PHASE2_GAME.events);
    for (const out of [overlay, framed]) {
      expect(out).toContain("Learn one player's exact role. Only you see the result.");
      expect(out).not.toContain('Suspicious');
      expect(out).not.toContain('two checks');
    }
    expect(face).toContain('Peeks inside one glove each night.');
  });

  it('a ten-seat game’s investigator has two checks, Suspicious or Not suspicious', () => {
    const [overlay, framed, face] = investigator(PHASE3_GAME.events);
    for (const out of [overlay, framed]) {
      expect(out).toContain('two checks in the game');
      expect(out).toContain('Not suspicious');
      expect(out).not.toContain('exact role');
    }
    expect(face).toContain('when it counts.');
  });

  it('keeps the names, so a name read from the pool reads right in any game', () => {
    for (const [role, text] of Object.entries(LEGACY_CARD_TEXT))
      expect(text.name).toBe(CARD_TEXT[role].name);
  });

  it('falls back to the pool for a role the nine-seat game never dealt', () => {
    expect(cardTextFor('sentinel', true)).toBe(CARD_TEXT.sentinel);
    expect(cardTextFor('investigator', false)).toBe(CARD_TEXT.investigator);
  });
});

describe('the side under a card', () => {
  it('names the lone killer’s side, not a role, under the necromancer and the serial killer', () => {
    for (const role of ['necromancer', 'serial_killer']) {
      const out = renderToStaticMarkup(<RoleCard role={role} seat={9} w={340} />);
      expect(out).toMatch(/aria-label="Lone killer"[\s\S]*<\/svg>Lone killer<\/span>/);
    }
    expect(FACTION_NAME.serial_killer).toBe('Lone killer');
  });

  it('keeps a winner’s role name: a serial killer’s win is the serial killer’s', () => {
    expect(WINNER_NAME.serial_killer).toBe('Serial killer');
    expect(WINNER_NAME.necromancer).toBe('Necromancer');
  });
});
