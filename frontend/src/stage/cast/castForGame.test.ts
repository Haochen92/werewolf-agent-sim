import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { describe, expect, it } from 'vitest';
import { SPRITES } from '@/assets/manifest';
import {
  LEGACY_CHARACTERS,
  castForGame,
  castForRoom,
  liveCastSize,
  resolveCast,
} from './castForGame';

// The benches pass the full uuid (`DATA.game_id`), not the 8-char prefix.
const FIXTURE_GAME_ID = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';

describe('live cast size during departure', () => {
  it('keeps every platform seat drawable when running status beats the roster stream', () => {
    const gameId = '2b29bfe8-714d-4aa8-a4c2-f92b08d02aa5';
    for (const places of [9, 10]) {
      for (const status of [
        { max_seats: places, cast: [] },
        { max_seats: 0, cast: [] },
        { max_seats: 0, cast: castForGame(gameId, places) },
      ]) {
        const size = liveCastSize(0, status, places);
        expect(size).toBe(places);
        const cast = resolveCast(status.cast, gameId, size);
        for (let i = 0; i < places; i++) {
          expect(SPRITES.day[cast[i]].base.src).toBeTruthy();
          expect(SPRITES.small.day[cast[i]].base.src).toBeTruthy();
        }
      }
    }
  });

  it('uses the recorded cast before the roster arrives on a running game', () => {
    expect(liveCastSize(0, { max_seats: 0, cast: castForGame(FIXTURE_GAME_ID, 10) })).toBe(
      10,
    );
  });

  it('prefers the dealt roster and keeps the legacy default when nothing is known', () => {
    expect(liveCastSize(9, { max_seats: 10, cast: [] }, 10)).toBe(9);
    expect(liveCastSize(0, undefined)).toBe(9);
    expect(liveCastSize(0, { max_seats: 0, cast: [] })).toBe(9);
  });
});

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

describe('resolveCast', () => {
  const stored = [
    'whale',
    'cat',
    'owl',
    'hare',
    'badger',
    'onion',
    'shade',
    'dragon',
    'cyclops',
  ];

  it('takes the cast the server recorded, in seat order', () => {
    expect(resolveCast(stored, FIXTURE_GAME_ID)).toEqual(stored);
  });

  it('falls back to the legacy hash for a game recorded before casts were stored', () => {
    expect(resolveCast([], FIXTURE_GAME_ID)).toEqual(castForGame(FIXTURE_GAME_ID));
    expect(resolveCast(undefined, FIXTURE_GAME_ID)).toEqual(castForGame(FIXTURE_GAME_ID));
  });

  it('falls back when the record is short or names a character this build cannot show', () => {
    expect(resolveCast(stored.slice(0, 8), FIXTURE_GAME_ID)).toEqual(
      castForGame(FIXTURE_GAME_ID),
    );
    expect(resolveCast([...stored.slice(0, 8), 'griffon'], FIXTURE_GAME_ID)).toEqual(
      castForGame(FIXTURE_GAME_ID),
    );
  });

  it('shuffles the frozen eleven, never the manifest, so old games keep their cast', () => {
    expect(LEGACY_CHARACTERS).toHaveLength(11);
    expect(LEGACY_CHARACTERS[0]).toBe('owl');
    expect(LEGACY_CHARACTERS[10]).toBe('shade');
  });
});

describe('castForRoom', () => {
  const hashed = castForGame(FIXTURE_GAME_ID);

  it('is the hash while nobody has picked', () => {
    expect(castForRoom([], FIXTURE_GAME_ID)).toEqual(hashed);
    expect(castForRoom([null, null], FIXTURE_GAME_ID)).toEqual(hashed);
  });

  it('dresses each picker in their pick and keeps everyone else in their place', () => {
    // the third place picks the second place's hashed puppet: only the second has to change
    const cast = castForRoom([null, null, hashed[1]], FIXTURE_GAME_ID);
    expect(cast[2]).toBe(hashed[1]);
    expect(cast[0]).toBe(hashed[0]);
    expect(cast[1]).not.toBe(hashed[1]);
    expect(cast.slice(3)).toEqual(hashed.slice(3));
    expect(new Set(cast).size).toBe(9);
  });

  it('ignores a pick this build has no sprites for', () => {
    expect(castForRoom(['griffon'], FIXTURE_GAME_ID)).toEqual(hashed);
  });
});
