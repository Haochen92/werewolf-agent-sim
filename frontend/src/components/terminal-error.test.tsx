import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { MantineProvider } from '@mantine/core';
import type { GameStatus } from '@/types/contracts';
import { GameEndedCard } from './GameEndedCard';
import { TerminalError } from './TerminalError';

const REFUSED = 'Anthropic refused this game’s API key: 401, invalid x-api-key.';

const html = (node: React.ReactNode) =>
  renderToStaticMarkup(<MantineProvider>{node}</MantineProvider>);

describe('TerminalError', () => {
  it('says a refused key stopped the game, and leads to a new one without the restart note', () => {
    const out = html(<TerminalError message={REFUSED} byok kind="key_rejected" />);
    expect(out).toContain('Your key stopped working');
    expect(out).toContain(`${REFUSED} The agents can’t play without it`);
    expect(out).toContain('Common causes:');
    expect(out).toMatch(/href="\/play"[^>]*>.*Start a new game/);
    expect(out).toContain('Back to the start');
    expect(out).not.toContain('server restart');
  });

  it('keeps the plain card, restart note included, for any other end', () => {
    const out = html(<TerminalError message="boom" byok />);
    expect(out).toContain('This game has ended unexpectedly');
    expect(out).toContain('server restart');
    expect(out).not.toContain('Your key stopped working');
  });
});

describe('GameEndedCard', () => {
  const status = (over: Partial<GameStatus>): GameStatus =>
    ({ state: 'dropped', archived: true, you: 'mira', ...over }) as GameStatus;

  it('gives an archived game dropped on a refused key the same words', () => {
    const out = html(
      <GameEndedCard
        gameId="g1"
        status={status({ error: REFUSED, error_kind: 'key_rejected' })}
      />,
    );
    expect(out).toContain('Your key stopped working');
    expect(out).toContain('You played as Mira.');
    expect(out).not.toContain('This game was dropped');
  });

  it('keeps "dropped" for any other error', () => {
    const out = html(
      <GameEndedCard gameId="g1" status={status({ error: 'nobody came' })} />,
    );
    expect(out).toContain('This game was dropped');
    expect(out).toContain('nobody came');
  });
});
