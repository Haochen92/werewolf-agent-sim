import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '@/assets/manifest';
import { ActPlate } from './ActPlate';
import { BallotRow } from './BallotRow';
import { SayLine } from './PackChat';

const html = (el: React.ReactElement) => renderToStaticMarkup(el);
const cast = CHARACTERS.slice(0, 9);
const noop = () => {};

describe('the hand-over is each plate’s own (owner, 2026-10-17)', () => {
  it('ends the ballot’s row with "Let my agent vote", only when the container offers it', () => {
    const row = (onAgent?: () => void) =>
      html(
        <BallotRow
          candidates={['player_2', 'abstain']}
          cast={cast}
          chosen={null}
          me="player_1"
          onAgent={onAgent}
        />,
      );
    expect(row(noop)).toContain('Let my agent vote');
    expect(row()).not.toContain('Let my agent vote');
  });

  it('says the agent has the ballot, naming no seat, once handed over', () => {
    const out = html(
      <BallotRow
        candidates={['player_2']}
        cast={cast}
        chosen={null}
        me="player_1"
        sent
        byAgent
      />,
    );
    expect(out).toContain('Your agent has your ballot');
    expect(out).toContain('data-ballot="agent"');
    expect(out).not.toContain('Abstain');
  });

  it('says "Sending…" with the chips shut on the choice and no plate, until the server has it (2026-10-17)', () => {
    const out = html(
      <BallotRow
        candidates={['player_2', 'player_4', 'abstain']}
        cast={cast}
        chosen="player_4"
        me="player_1"
        onAgent={noop}
        sending
      />,
    );
    expect(out).toContain('data-ballot="sending"');
    expect(out).toContain('Sending…');
    expect(out).not.toContain('Your ballot is in');
    expect(out).not.toContain('Vote seat 4');
    expect(out).not.toContain('Let my agent vote');
    // every chip is shut, the chosen one still lit
    const chips = [...out.matchAll(/<button[^>]*role="radio"[^>]*>/g)].map((m) => m[0]);
    expect(chips).toHaveLength(3);
    expect(chips.every((c) => c.includes('disabled'))).toBe(true);
    expect(chips.filter((c) => c.includes('aria-checked="true"'))).toHaveLength(1);
  });

  it('puts the plate’s hand-over last, in the second button’s dress', () => {
    const out = html(
      <ActPlate
        label="Protect seat 3"
        secondary={{ label: 'Hold fire' }}
        agent={{ label: 'Let my agent choose', onClick: noop }}
      />,
    );
    const buttons = [...out.matchAll(/<button[^>]*>([^<]*)<\/button>/g)];
    expect(buttons.map((b) => b[1])).toEqual([
      'Protect seat 3',
      'Hold fire',
      'Let my agent choose',
    ]);
    // only the act itself is the gold plate
    expect(buttons[2][0]).not.toMatch(/class=/);
  });

  it('gives the pack’s chat round "Let my agent talk" beside Say it and Pass', () => {
    const out = html(
      <SayLine draft="" left={0} onSay={noop} onPass={noop} onAgent={noop} />,
    );
    expect(out).toMatch(/Say it.*Pass.*Let my agent talk/s);
  });
});
