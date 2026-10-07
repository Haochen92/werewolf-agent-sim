/**
 * The dock's head names the turn the human is on (beat sheet §2 row 11): a wrong label asks for
 * the wrong kind of line, and the opening's hint is the only place the human reads the round's rules.
 */
import { describe, expect, it } from 'vitest';
import { dockHeading } from './TurnDock';

describe('the dock’s heading, by the ask’s round', () => {
  it('names the opening and lists what an opening may hold', () => {
    expect(dockHeading('opening')).toEqual({
      title: 'Your opening',
      hint: 'A role claim, something from last night, or a challenge. Or pass.',
    });
  });

  it('names the open floor', () => {
    expect(dockHeading('proactive')).toEqual({
      title: 'The floor is yours',
      hint: 'One or two useful points, or pass.',
    });
  });

  it('names the last word', () => {
    expect(dockHeading('closing')).toEqual({
      title: 'Your last word',
      hint: 'The village has its eye on you.',
    });
  });

  it('keeps the ordinary heading for a discussion turn and for an ask with no round', () => {
    const ordinary = {
      title: 'Your turn to speak',
      hint: 'Nothing is said until you send it.',
    };
    expect(dockHeading('discussion')).toEqual(ordinary);
    expect(dockHeading(null)).toEqual(ordinary);
    expect(dockHeading(undefined)).toEqual(ordinary);
  });
});
