import { isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { MantineProvider } from '@mantine/core';
import type { CharacterCard, GameStatus } from '@/types/contracts';
import { PickedRoster, PuppetPicker, roomPicks } from './PuppetPicker';

const CARDS: CharacterCard[] = [
  { id: 'owl', display_name: 'Owl', retired: false },
  { id: 'hare', display_name: 'Hare', retired: false },
  { id: 'shade', display_name: 'Songbird', retired: false },
  // in the catalogue ahead of its sprites
  { id: 'lantern', display_name: 'Paper lantern', retired: false },
];

type Props = Parameters<typeof PuppetPicker>[0];

/** The picker's buttons, from the element tree it returns (it has no hooks, so it can be called). */
function buttons(props: Props): ReactElement<{
  'data-puppet': string;
  disabled: boolean;
  onClick?: () => void;
}>[] {
  const found: ReactElement[] = [];
  const walk = (node: ReactNode) => {
    if (Array.isArray(node)) return node.forEach(walk);
    if (!isValidElement(node)) return;
    if (node.type === 'button') found.push(node);
    walk((node.props as { children?: ReactNode }).children);
  };
  walk(PuppetPicker(props));
  return found as ReturnType<typeof buttons>;
}

const tap = (props: Props, id: string) =>
  buttons(props).find((b) => b.props['data-puppet'] === id)!.props.onClick!();

/** One chip's markup, by its puppet id. */
function chip(html: string, id: string): string {
  const m = html.match(new RegExp(`<button[^>]*data-puppet="${id}"[^>]*>.*?</button>`));
  return m?.[0] ?? '';
}

describe('the puppet picker', () => {
  const held = new Map([['hare', 'Ada']]);

  it('dims a puppet another player holds, with their name, and keeps it from a tap', () => {
    const html = renderToStaticMarkup(
      <PuppetPicker cards={CARDS} value="owl" held={held} onChange={() => {}} />,
    );
    const hare = chip(html, 'hare');
    expect(hare).toContain('data-held="true"');
    expect(hare).toContain('disabled=""');
    expect(hare).toContain('Ada');
    expect(hare).toContain('aria-label="Hare, taken by Ada"');
  });

  it('presses your own, and leaves a free one open', () => {
    const html = renderToStaticMarkup(
      <PuppetPicker cards={CARDS} value="owl" held={held} onChange={() => {}} />,
    );
    expect(chip(html, 'owl')).toContain('aria-pressed="true"');
    expect(chip(html, 'owl')).not.toContain('disabled');
    const free = chip(html, 'shade');
    expect(free).toContain('aria-pressed="false"');
    expect(free).not.toContain('disabled');
    expect(free).not.toContain('data-held');
    expect(html).toContain('You stand as the Owl');
  });

  it('tapping a free puppet picks it; tapping your own gives it up', () => {
    const onChange = vi.fn();
    const props = { cards: CARDS, value: 'owl', held, onChange };
    tap(props, 'shade');
    expect(onChange).toHaveBeenLastCalledWith('shade');
    tap(props, 'owl');
    expect(onChange).toHaveBeenLastCalledWith(null);
  });

  it('without onChange (a spectator) every chip is shown but none can be tapped', () => {
    const shown = buttons({ cards: CARDS, value: null, held });
    expect(shown).toHaveLength(CARDS.length);
    expect(shown.every((b) => b.props.disabled && !b.props.onClick)).toBe(true);
    const html = renderToStaticMarkup(
      <PuppetPicker cards={CARDS} value={null} held={held} />,
    );
    expect(html).not.toContain('house draws');
  });

  it('holds every chip still while a press is on its way', () => {
    const shown = buttons({
      cards: CARDS,
      value: null,
      onChange: () => {},
      disabled: true,
    });
    expect(shown.every((b) => b.props.disabled)).toBe(true);
  });

  it('draws a puppet the build has no sprites for as its initials', () => {
    const html = renderToStaticMarkup(<PuppetPicker cards={CARDS} value={null} />);
    expect(chip(html, 'lantern')).toContain('>PL<');
    expect(chip(html, 'owl')).toContain('<img');
  });
});

describe('the picks in a room', () => {
  const status = {
    state: 'waiting',
    players: ['Ada', 'Bo', 'Cy'],
    characters: ['hare', null, 'owl'],
    you_aboard: 2,
  } as GameStatus;

  it('holds the others’ picks by name and finds yours by your place', () => {
    const { held, mine } = roomPicks(status);
    expect([...held]).toEqual([['hare', 'Ada']]);
    expect(mine).toBe('owl');
  });

  it('a viewer without a seat holds nothing of their own', () => {
    const { held, mine } = roomPicks({ ...status, you_aboard: null });
    expect(held.get('owl')).toBe('Cy');
    expect(mine).toBeNull();
  });

  it('the roster puts each name beside its puppet, an empty ring where none is picked', () => {
    const html = renderToStaticMarkup(
      <MantineProvider>
        <PickedRoster players={status.players!} picks={status.characters!} cards={CARDS} />
      </MantineProvider>,
    );
    expect(html.match(/<li/g)).toHaveLength(3);
    expect(html).toContain('data-empty');
    expect(html).toContain(', as the Hare');
  });
});
