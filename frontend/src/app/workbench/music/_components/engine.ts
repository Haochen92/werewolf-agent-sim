/**
 * The music bench's player: one AudioContext, made on the first press (a browser lets sound
 * start only after one), each file fetched and decoded once, and every sound a buffer source
 * scheduled on the audio clock. A loop is the buffer's own loop, exact to the sample, so the
 * bench hears the seam the game will; fades are gain ramps the audio thread runs.
 */
import { measure, type Measure } from './timelines';

export interface Voice {
  src: AudioBufferSourceNode;
  gain: GainNode;
  /** The audio clock's time at the file's position 0 (loops: of the first pass). */
  zero: number;
  /** The audio clock's time it starts sounding. */
  when: number;
  buffer: AudioBuffer;
  loop: boolean;
}

export interface PlayOpts {
  /** Seconds from now. */
  in?: number;
  /** Where in the file to start, seconds. */
  offset?: number;
  /** How long to play, seconds; a loop without it plays until stopped. */
  duration?: number;
  loop?: boolean;
  /** Fade in over this many seconds. */
  fadeIn?: number;
}

export class BenchPlayer {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private buffers = new Map<string, Promise<{ buffer: AudioBuffer; m: Measure }>>();
  private voices = new Set<Voice>();
  private volume = 0.8;

  /** The context, made and resumed inside a press. */
  audio(): AudioContext {
    if (!this.ctx) {
      this.ctx = new AudioContext();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') void this.ctx.resume();
    return this.ctx;
  }

  now(): number {
    return this.ctx?.currentTime ?? 0;
  }

  setVolume(v: number) {
    this.volume = v;
    if (this.master && this.ctx)
      this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  }

  load(url: string): Promise<{ buffer: AudioBuffer; m: Measure }> {
    let got = this.buffers.get(url);
    if (!got) {
      const ctx = this.audio();
      got = fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status} ${url}`);
          return r.arrayBuffer();
        })
        .then((bytes) => ctx.decodeAudioData(bytes))
        .then((buffer) => {
          const channels = Array.from({ length: buffer.numberOfChannels }, (_, i) =>
            buffer.getChannelData(i),
          );
          return { buffer, m: measure(channels, buffer.sampleRate) };
        });
      got.catch(() => this.buffers.delete(url));
      this.buffers.set(url, got);
    }
    return got;
  }

  play(buffer: AudioBuffer, opts: PlayOpts = {}): Voice {
    const ctx = this.audio();
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.loop = !!opts.loop;
    const gain = ctx.createGain();
    src.connect(gain).connect(this.master!);
    const when = ctx.currentTime + (opts.in ?? 0);
    const offset = opts.offset ?? 0;
    if (opts.fadeIn) {
      gain.gain.setValueAtTime(0, when);
      gain.gain.linearRampToValueAtTime(1, when + opts.fadeIn);
    }
    if (opts.duration !== undefined) src.start(when, offset, opts.duration);
    else src.start(when, offset);
    const voice: Voice = { src, gain, zero: when - offset, when, buffer, loop: src.loop };
    this.voices.add(voice);
    src.onended = () => this.voices.delete(voice);
    return voice;
  }

  /** Fade a voice out from `in` seconds from now, over `over` seconds, and stop it. */
  fadeOut(voice: Voice, over = 0.15, inS = 0) {
    if (!this.ctx) return;
    const at = this.ctx.currentTime + inS;
    voice.gain.gain.setValueAtTime(voice.gain.gain.value, at);
    voice.gain.gain.linearRampToValueAtTime(0, at + over);
    try {
      voice.src.stop(at + over + 0.02);
    } catch {
      // already stopped
    }
  }

  stopAll() {
    for (const v of this.voices) this.fadeOut(v);
    this.voices.clear();
  }

  /** Where a voice is in its file, seconds (a loop wraps), or null before it starts. */
  position(voice: Voice): number | null {
    if (this.now() < voice.when) return null;
    const t = this.now() - voice.zero;
    return voice.loop ? t % voice.buffer.duration : Math.min(t, voice.buffer.duration);
  }
}
