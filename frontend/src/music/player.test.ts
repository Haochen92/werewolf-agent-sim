import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MusicPlayer } from './player';

/** Just enough of an AudioContext for the player's wake, rebuild and visibility paths. */
class FakeContext {
  static made: FakeContext[] = [];
  state: string = 'suspended';
  currentTime = 0;
  destination = {};
  resumes = 0;
  closed = false;
  constructor() {
    FakeContext.made.push(this);
  }
  createGain() {
    const param = {
      value: 0,
      setValueAtTime() {},
      linearRampToValueAtTime() {},
      cancelScheduledValues() {},
    };
    return { gain: param, connect: () => ({}) };
  }
  resume() {
    this.resumes++;
    // Safari refuses to restart an interrupted context
    if (this.state === 'interrupted') return Promise.reject(new Error('not allowed'));
    this.state = 'running';
    return Promise.resolve();
  }
  suspend() {
    this.state = 'suspended';
    return Promise.resolve();
  }
  close() {
    this.closed = true;
    return Promise.resolve();
  }
}

describe('MusicPlayer and a context the phone took away', () => {
  let player: MusicPlayer;

  beforeEach(() => {
    FakeContext.made = [];
    vi.stubGlobal('window', {});
    vi.stubGlobal('document', { visibilityState: 'visible' });
    vi.stubGlobal('AudioContext', FakeContext);
    player = new MusicPlayer();
    player.enter();
  });

  afterEach(() => {
    player.dispose();
    vi.unstubAllGlobals();
  });

  it('makes the context on the first press and resumes it', () => {
    player.unlock();
    expect(FakeContext.made).toHaveLength(1);
    expect(FakeContext.made[0].resumes).toBe(1);
  });

  it('a press after an interruption makes a new context, and the old one is closed', () => {
    player.unlock();
    const first = FakeContext.made[0];
    first.state = 'interrupted';
    player.unlock();
    expect(FakeContext.made).toHaveLength(2);
    expect(first.closed).toBe(true);
    expect(FakeContext.made[1].resumes).toBe(1);
  });

  it('a press on a merely suspended context resumes it without making another', () => {
    player.unlock();
    FakeContext.made[0].state = 'suspended';
    player.unlock();
    expect(FakeContext.made).toHaveLength(1);
    expect(FakeContext.made[0].resumes).toBe(2);
  });

  it('the page shown again only tries a resume: a refused one waits for the next press', async () => {
    player.unlock();
    const first = FakeContext.made[0];
    first.state = 'interrupted';
    player.setVisible(true);
    await Promise.resolve();
    expect(FakeContext.made).toHaveLength(1);
    expect(first.resumes).toBe(2);
  });
});
