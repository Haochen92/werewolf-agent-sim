import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { foldEvents } from '@/game/foldEvents';
import fixture from '@/game/__fixtures__/seed-chunk-catalogue.json';
import { DayTranscript } from './DayTranscript';
import { AgentInspector } from './theater-parts';

const replay = fixture as unknown as ReplayGame;
const view = foldEvents(replay.events as DurableGameEvent[]);

describe('entitled machine-world rendering', () => {
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
