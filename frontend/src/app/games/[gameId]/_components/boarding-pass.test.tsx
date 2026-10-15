import { renderToStaticMarkup } from 'react-dom/server';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MantineProvider } from '@mantine/core';
import { chooseCharacter } from '@/lib/api';
import { ApiError } from '@/lib/request';
import type { RoomInput } from '@/stage/scenes/types';
import type { CharacterCard, GameStatus } from '@/types/contracts';
import { leavesPass, PassPuppets, passIsUp, sendPick, type LostPick } from './BoardingPass';

vi.mock('@/lib/api', () => ({ chooseCharacter: vi.fn(), joinGame: vi.fn() }));
const choose = vi.mocked(chooseCharacter);

const CARDS: CharacterCard[] = [
  { id: 'owl', display_name: 'Owl', retired: false },
  { id: 'hare', display_name: 'Hare', retired: false },
];

/** What a sent pick comes to (the server refuses with `refusal`, or takes it), and whether it lets the player off the pass. */
async function send(id: string | null, refusal?: Error) {
  if (refusal) choose.mockRejectedValueOnce(refusal);
  else choose.mockResolvedValueOnce({} as GameStatus);
  const outcome = await sendPick('g1', id);
  return { outcome, leaves: leavesPass(outcome, id) };
}

const puppets = (lost: LostPick | null) =>
  renderToStaticMarkup(
    <MantineProvider>
      <PassPuppets
        cards={CARDS}
        value={null}
        held={new Map([['owl', 'Ada']])}
        lost={lost}
        busy={false}
        onPick={() => {}}
        onHouseDraws={() => {}}
      />
    </MantineProvider>,
  );

const room = (over: Partial<RoomInput>) =>
  ({
    aboard: ['Ada', 'Bo'],
    places: 9,
    locked: false,
    seated: false,
    ...over,
  }) as RoomInput;

describe('a pick lost on the boarding pass', () => {
  beforeEach(() => choose.mockReset());

  it('lost after the join: the pass stays up and names the puppet, with the house draw beside it', async () => {
    const sent = await send('owl', new ApiError(409, 'someone already stands as the owl'));
    expect(sent).toEqual({ outcome: 'taken', leaves: false });
    // the seat is held and its pick is open, so the room keeps the pass up for it
    expect(passIsUp(room({ seated: true }), true)).toBe(true);
    expect(passIsUp(room({ seated: true, aboard: Array(9).fill('x') }), true)).toBe(true);

    const html = puppets({ id: 'owl', taken: true });
    expect(html).toContain('Someone took the Owl. Choose another puppet.');
    expect(html).toContain('Let the house draw');
    // nothing says the house draws until the player asks it to
    expect(html).not.toContain('the house draws your puppet');
  });

  it('a send that never arrived keeps the pass up too, saying so', async () => {
    const sent = await send('owl', new TypeError('Failed to fetch'));
    expect(sent).toEqual({ outcome: 'failed', leaves: false });
    expect(puppets({ id: 'owl', taken: false })).toContain(
      'The Owl did not reach the platform',
    );
  });

  it('"Let the house draw" sends null and lets the player go', async () => {
    const sent = await send(null);
    expect(choose).toHaveBeenCalledWith('g1', null);
    expect(sent).toEqual({ outcome: 'landed', leaves: true });
    // the player asked for the draw: even a failed send does not hold them
    expect((await send(null, new Error('down'))).leaves).toBe(true);
  });

  it('a game that has already started lets the player go; the house draw stands', async () => {
    const sent = await send('hare', new ApiError(409, 'game already started'));
    expect(sent).toEqual({ outcome: 'started', leaves: true });
    expect((await send('hare', new ApiError(410, 'ended'))).leaves).toBe(true);
  });

  it('a pick that lands lets the player go, and a settled seat no longer gets the pass', async () => {
    expect(await send('hare')).toEqual({
      outcome: 'landed',
      leaves: true,
    });
    expect(passIsUp(room({ seated: true }), false)).toBe(false);
    expect(passIsUp(room({}), false)).toBe(true);
    expect(passIsUp(room({ locked: true }), false)).toBe(false);
  });

  it('with no pick lost the picker says the house draws, and offers no separate button', () => {
    const html = puppets(null);
    expect(html).toContain('None picked: the house draws your puppet.');
    expect(html).not.toContain('Let the house draw');
    expect(html).not.toContain('role="alert"');
  });
});
