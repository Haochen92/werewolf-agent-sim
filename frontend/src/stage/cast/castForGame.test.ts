import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { describe, expect, it } from 'vitest';
import { castForGame } from './castForGame';

// The benches pass the full uuid (`DATA.game_id`), not the 8-char prefix.
const FIXTURE_GAME_ID = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';

function kitCast(gameId: string): string[] {
  const kit = readFileSync(
    new URL('../../../docs/design_2026-09-25/kits/puppet-kit.js', import.meta.url),
    'utf8',
  );
  const sandbox: { PuppetKit?: { castForGame: (id: string) => string[] } } = {};
  runInNewContext(`${kit};this.PuppetKit = PuppetKit;`, sandbox);
  return [...sandbox.PuppetKit!.castForGame(gameId)];
}

describe('castForGame', () => {
  it('casts the fixture game as the benches do', () => {
    expect(castForGame(FIXTURE_GAME_ID)).toEqual([
      'cat',
      'threeEyes',
      'owl',
      'shade',
      'whale',
      'polarBear',
      'onion',
      'cyclops',
      'hare',
    ]);
  });

  it('is deterministic and gives nine distinct characters', () => {
    const cast = castForGame(FIXTURE_GAME_ID);
    expect(castForGame(FIXTURE_GAME_ID)).toEqual(cast);
    expect(cast).toHaveLength(9);
    expect(new Set(cast).size).toBe(9);
  });

  it('matches the puppet kit for any id', () => {
    for (const id of [FIXTURE_GAME_ID, '9369a5c1', '', 'seed-chunk-catalogue', 'ü-ñ']) {
      expect(castForGame(id)).toEqual(kitCast(id));
    }
  });
});
