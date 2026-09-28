import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import {
  carryAcross,
  holdFor,
  jumpChapter,
  seekTo,
  stepBack,
  stepForward,
  still,
  transportLabel,
} from './transport';
import { catchUpIndex, nextLiveStep } from './live-queue';

const events = fixture.events as unknown as DurableGameEvent[];
const pub = beatsFor(events, { xray: false });
const xray = beatsFor(events, { xray: true });

describe('the transport', () => {
  it('only a forward step animates; everything else arrives still', () => {
    expect(stepForward(still(3), pub)).toEqual({ index: 4, animate: true });
    expect(stepBack({ index: 4, animate: true })).toEqual(still(3));
    expect(seekTo(40, pub)).toEqual(still(40));
    expect(seekTo(-5, pub)).toEqual(still(0));
    expect(seekTo(9999, pub)).toEqual(still(pub.length - 1));
    expect(stepForward(still(pub.length - 1), pub).index).toBe(pub.length - 1);
  });

  it('chapter jumps land on chapter marks, still', () => {
    const vote2 = pub.findIndex((b) => b.chapter?.kind === 'vote' && b.chapter.n === 2);
    const night2 = pub.findIndex((b) => b.chapter?.kind === 'night' && b.chapter.n === 2);
    expect(jumpChapter(still(vote2 + 3), pub, 1)).toEqual(still(night2));
    // Back from inside a chapter goes to its start; back from the start goes one chapter up.
    expect(jumpChapter(still(vote2 + 3), pub, -1)).toEqual(still(vote2));
    const day2 = pub.findIndex((b) => b.chapter?.kind === 'day' && b.chapter.n === 2);
    expect(jumpChapter(still(vote2), pub, -1)).toEqual(still(day2));
    expect(jumpChapter(still(0), pub, -1)).toEqual(still(0));
    expect(jumpChapter(still(pub.length - 1), pub, 1)).toEqual(still(pub.length - 1));
  });

  it('holds scale with speed and a 0 hold waits for the viewer', () => {
    const chip = pub.find((b) => b.id === 'vote.chip-counted')!;
    expect(holdFor(chip, 'normal')).toBe(2000);
    expect(holdFor(chip, 'fast')).toBe(1000);
    expect(holdFor(chip, 'skip')).toBe(250);
    const curtain = pub.find((b) => b.id === 'over.curtain')!;
    expect(holdFor(curtain, 'normal')).toBeNull();
  });

  it('carries the cursor across an X-ray toggle by the beat it was on', () => {
    const chip4 = pub.findIndex(
      (b) => b.id === 'vote.chip-counted' && b.ordinal === 4 && b.day === 3,
    );
    const across = carryAcross(still(chip4), pub, xray);
    expect(xray[across.index]).toMatchObject({
      id: 'vote.chip-counted',
      ordinal: 4,
      day: 3,
    });
    expect(across.animate).toBe(false);
    // An X-ray-only beat has no twin: land on the next public beat at or after its seq.
    const spoke = xray.findIndex((b) => b.id === 'rnight.spoke' && b.day === 2);
    const back = carryAcross(still(spoke), xray, pub);
    expect(pub[back.index].seq).toBeGreaterThanOrEqual(xray[spoke].seq);
    expect(pub[back.index].id).toBe('morning.shutter-down');
  });

  it('labels a beat with its chapter', () => {
    const chip = pub.findIndex((b) => b.id === 'vote.chip-counted' && b.day === 3);
    expect(transportLabel(pub, chip)).toBe('Vote 3 · A chip is counted');
    expect(transportLabel(pub, pub.length - 1)).toBe('Game over · Curtain');
  });
});

describe('the live queue', () => {
  const live = beatsFor(events, { xray: false, me: 'player_7', live: true });
  const ctx = { me: 'player_7', rolesLanded: false };

  it('plays one or two queued beats at normal speed and a backlog of three at fast', () => {
    const last = live.length - 1;
    expect(nextLiveStep(live, last - 1, ctx)).toEqual({ index: last, speed: 'normal' });
    expect(nextLiveStep(live, last - 2, ctx)).toEqual({ index: last - 1, speed: 'normal' });
    expect(nextLiveStep(live, last - 3, ctx)).toEqual({ index: last - 2, speed: 'fast' });
    expect(nextLiveStep(live, last - 5, ctx)).toEqual({ index: last - 4, speed: 'fast' });
    expect(nextLiveStep(live, last, ctx)).toBeNull();
  });

  it('plays the deal at normal speed even behind a backlog or a pending prompt', () => {
    const card = live.findIndex((b) => b.id === 'deal.your-card');
    expect(card).toBeGreaterThan(0);
    expect(live.length - 1 - (card - 1)).toBeGreaterThanOrEqual(3);
    expect(nextLiveStep(live, card - 1, ctx)).toEqual({ index: card, speed: 'normal' });
    const prompt = {
      ...live[card],
      id: 'day.your-turn' as const,
      liveOnly: true,
      sees: 'seat' as const,
      seat: 'player_7',
      holdMs: 0,
    };
    const staged = [...live.slice(0, card + 2), prompt, ...live.slice(card + 2)];
    expect(nextLiveStep(staged, card - 1, ctx)).toEqual({ index: card, speed: 'normal' });
  });

  it('holds the winners’ stand until the roles have landed', () => {
    const stand = live.findIndex((b) => b.id === 'over.winners-stand');
    expect(nextLiveStep(live, stand - 1, ctx)).toBeNull();
    // Released once the roles land (the speed is the backlog's business).
    expect(nextLiveStep(live, stand - 1, { ...ctx, rolesLanded: true })).toMatchObject({
      index: stand,
    });
  });

  it('drains fast toward a prompt for the seated human', () => {
    // The fixture has no human prompts; stage one after a speech beat.
    const at = live.findIndex((b) => b.id === 'day.speech' && b.day === 3);
    const prompt = {
      ...live[at + 1],
      id: 'day.your-turn' as const,
      liveOnly: true,
      sees: 'seat' as const,
      seat: 'player_7',
      holdMs: 0,
    };
    const staged = [...live.slice(0, at + 1), prompt, ...live.slice(at + 1)];
    expect(nextLiveStep(staged, at - 1, ctx)).toEqual({ index: at, speed: 'fast' });
    expect(nextLiveStep(staged, at, ctx)).toEqual({ index: at + 1, speed: 'fast' });
  });

  it('a catch-up lands on the latest beat', () => {
    expect(catchUpIndex(live)).toBe(live.length - 1);
    expect(catchUpIndex([])).toBe(0);
  });
});
