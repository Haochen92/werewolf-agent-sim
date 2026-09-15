import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { emptyDay, foldEvents } from '@/game/foldEvents';
import fixture from '@/game/__fixtures__/seed-chunk-catalogue.json';
import { DayTranscript } from './DayTranscript';
import { AgentInspector } from './theater-parts';

const replay = fixture as unknown as ReplayGame;
const view = foldEvents(replay.events as DurableGameEvent[]);

describe('entitled machine-world rendering', () => {
  it('moves a settled night result to dawn of the following day', () => {
    const day1AtNight = renderToStaticMarkup(
      <DayTranscript day={view.days[1]} roles={view.xray.roles} xray={false} />,
    );
    const day1AfterDay2Exists = renderToStaticMarkup(
      <DayTranscript
        day={view.days[1]}
        nextDay={view.days[2]}
        roles={view.xray.roles}
        xray={false}
      />,
    );
    const day2 = renderToStaticMarkup(
      <DayTranscript
        day={view.days[2]}
        previousDay={view.days[1]}
        nextDay={view.days[3]}
        roles={view.xray.roles}
        xray={false}
      />,
    );

    expect(day1AtNight).toContain('Someone was attacked in the night — and survived.');
    expect(day1AfterDay2Exists).not.toContain(
      'Someone was attacked in the night — and survived.',
    );
    expect(day2).toContain('Dawn of Day 2');
    expect(day2).toContain('Someone was attacked in the night — and survived.');
  });

  it('keeps faction data behind X-ray in replay but shows it on an entitled live surface', () => {
    const day = view.days[3];
    const hidden = renderToStaticMarkup(
      <DayTranscript day={day} roles={view.xray.roles} xray={false} />,
    );
    const live = renderToStaticMarkup(
      <DayTranscript
        day={day}
        roles={view.xray.roles}
        xray={false}
        showEntitledMachine
        privateResults={view.xray.privateResults['player_1']}
      />,
    );

    expect(hidden).not.toContain('pack votes');
    expect(live).toContain('pack votes');
    expect(live).toContain('survived the shot');
    expect(live).toContain('bullet remaining');
  });

  it('renders archived seat-private results in that agent’s inspector', () => {
    const inspector = renderToStaticMarkup(
      <AgentInspector seat="player_3" view={view} onClose={() => undefined} />,
    );
    expect(inspector).toContain('private results');
    expect(inspector).toContain('investigation');
    expect(inspector).toContain('player_1 is Vigilante');
  });
});

describe('the carried summary (D13)', () => {
  const day1 = {
    ...emptyDay(1),
    summary: 'Key accusations and defenses: None.',
    summaryStructured: {
      accusations: [
        {
          accusers: ['player_1', 'player_3'],
          target: 'player_4',
          reasoning: 'player_1 and player_3 accuse player_4 of hypocrisy.',
          evidenceType: 'voting_record',
          defense: 'player_4 calls it self-preservation.',
        },
      ],
      roleClaims: [],
      blocs: [
        { players: ['player_1', 'player_3'], basis: 'Joint defense of their votes.' },
      ],
      dynamics: {
        landscape: 'Information-rich.',
        consensus: 'Split into camps.',
        drivers: 'player_4 drives.',
      },
    },
  };
  const day2 = emptyDay(2);

  it('stays off the story surface', () => {
    const html = renderToStaticMarkup(
      <DayTranscript day={day2} previousDay={day1} roles={{}} xray={false} />,
    );
    expect(html).not.toContain('carry from day 1');
    expect(html).not.toContain('hypocrisy');
    expect(html).not.toContain('Key accusations');
  });

  it('renders the typed form as sections under X-ray: the parties, then the sentence on its own', () => {
    const html = renderToStaticMarkup(
      <DayTranscript day={day2} previousDay={day1} roles={{}} xray={true} />,
    );
    expect(html).toContain('What the agents carry from day 1');
    expect(html).toContain('Split into camps.');
    expect(html).toContain('player_1, player_3 → player_4');
    expect(html).toContain('accuse player_4 of hypocrisy.');
    expect(html).toContain('Defense: player_4 calls it self-preservation.');
    expect(html).toContain('Joint defense of their votes.');
    expect(html).not.toContain('Key accusations');
  });

  it('falls back to the flattened text when the typed form has not arrived', () => {
    const html = renderToStaticMarkup(
      <DayTranscript
        day={day2}
        previousDay={{ ...day1, summaryStructured: null }}
        roles={{}}
        xray={true}
      />,
    );
    expect(html).toContain('Key accusations and defenses: None.');
  });
});
