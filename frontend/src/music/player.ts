/**
 * The score's player: one per page, on the Web Audio clock. Each track is fetched and decoded
 * once (a few at a time are kept: an 87 s track decoded is about 30 MB) and played from a buffer,
 * so a loop is exact to the sample, and every fade is a gain ramp the audio thread runs: no
 * JavaScript per frame, and an iPhone, which ignores a media element's volume, fades too.
 *
 * Browsers start sound only after the viewer has pressed something on the page, so the context
 * is made in `unlock`, which the director calls from the first press; until then a bed is only
 * remembered. A hidden page suspends the context, which stops its clock too, so a playlist's
 * schedule (read off that clock once a second) picks up where it was.
 */
import type { Bed } from './cues';

/** A bed's change of music, and a playlist's turn from one track to the next, in seconds. */
const XFADE = 1.5;
/** How long before a playlist's track ends its next one is fetched. */
const PRELOAD = 20;
/** Decoded tracks kept beyond those playing. */
const KEEP = 4;
/** The music sits under reading: the master level. */
const LEVEL = 0.55;
/** A bed starts once the stage has stayed on it this long: a scrub or a run of chapter jumps
 *  passes through beds without fetching each one (a beat holds 2 s at the least). */
const SETTLE_MS = 400;

interface Voice {
  src: AudioBufferSourceNode;
  gain: GainNode;
  /** The context time it starts, and when its buffer runs out (a loop: never). */
  at: number;
  ends: number;
}

interface Lane {
  bed: Bed;
  /** The track playing now, as an index into `bed.tracks`. */
  index: number;
  voice: Voice | null;
  /** The next track has been scheduled to come in. */
  queued: boolean;
}

export class MusicPlayer {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private buffers = new Map<string, Promise<AudioBuffer>>();
  private lane: Lane | null = null;
  /** The bed asked for; it plays once sound is unlocked and the viewer allows it. */
  private wanted: Bed | null = null;
  /** The viewer's choice: `on`, `off`, or null for never chosen (see `allows`). */
  private pref: 'on' | 'off' | null = null;
  /** When the last sting goes quiet: a bed waits for it. */
  private stingEnds = 0;
  private stings = new Set<Voice>();
  private ticker: ReturnType<typeof setInterval> | null = null;
  /** The viewer has pressed something on this page: the browser lets sound start. */
  private pressed = false;
  /** Seconds of the context's clock with nothing playing; past a few, it is suspended. */
  private idle = 0;
  /** Pages with music mounted (`enter`): only there does a press open the sound device. */
  private pages = 0;
  private settle: ReturnType<typeof setTimeout> | null = null;

  /**
   * The viewer pressed something. On a page with music the context is made (or woken, if a
   * phone suspended it) inside the press, which Safari needs; elsewhere nothing opens the sound
   * device, which an open context keeps awake.
   */
  unlock() {
    this.pressed = true;
    this.wake();
  }

  /** A page with music is mounted; the returned call is its leaving. */
  enter(): () => void {
    this.pages++;
    return () => {
      this.pages--;
    };
  }

  /** Make the context on a music page once the viewer has pressed, and resume it. */
  private wake() {
    if (typeof window === 'undefined' || typeof AudioContext === 'undefined') return;
    if (!this.pressed || this.pages === 0) {
      this.apply();
      return;
    }
    if (!this.ctx) {
      this.ctx = new AudioContext();
      this.master = this.ctx.createGain();
      this.master.gain.value = LEVEL;
      this.master.connect(this.ctx.destination);
      this.ticker = setInterval(() => this.tick(), 1000);
    }
    if (this.ctx.state === 'suspended' && document.visibilityState === 'visible')
      void this.ctx.resume();
    this.idle = 0;
    this.apply();
  }

  /** The viewer's choice of music; turning it off fades out what plays. */
  setPref(pref: 'on' | 'off' | null) {
    if (pref === this.pref) return;
    this.pref = pref;
    if (pref === 'off') {
      for (const s of this.stings) this.fade(s, 0.4);
      this.stings.clear();
      this.stingEnds = 0;
    }
    this.wake();
  }

  /** The game plays unless the viewer said off; an opt-in bed (the guide) only if they said on. */
  allows(bed: Pick<Bed, 'optIn'>): boolean {
    return bed.optIn ? this.pref === 'on' : this.pref !== 'off';
  }

  /** The bed for what the stage shows now; the same key again changes nothing. */
  setBed(bed: Bed | null) {
    if (bed?.key === this.wanted?.key) return;
    this.wanted = bed;
    if (this.settle) clearTimeout(this.settle);
    this.settle = setTimeout(() => {
      this.settle = null;
      this.wake();
    }, SETTLE_MS);
  }

  /** A one-shot on a moment. Dropped while sound is off or locked. */
  sting(url: string) {
    if (!this.ctx || !this.allows({})) return;
    const ctx = this.ctx;
    // a bed asked for while the sting loads waits for it too
    this.stingEnds = Infinity;
    // a bed already playing makes way for it
    this.release();
    void this.load(url)
      .then((buffer) => {
        if (!this.allows({}) || this.ctx !== ctx) {
          this.stingEnds = 0;
          return;
        }
        const voice = this.start(buffer, ctx.currentTime, { loop: false, fadeIn: 0 });
        this.stings.add(voice);
        voice.src.onended = () => this.stings.delete(voice);
        this.stingEnds = voice.ends;
      })
      .catch(() => {
        this.stingEnds = 0;
      })
      .finally(() => {
        // a bed that waited for the sting starts over now that its time is known
        if (this.lane && !this.lane.voice) this.lane = null;
        this.apply();
      });
  }

  /** The stage jumped: a one-shot still sounding belonged to where it was. */
  cutStings() {
    if (this.stings.size === 0 && this.stingEnds === 0) return;
    for (const s of this.stings) this.fade(s, 0.6);
    this.stings.clear();
    this.stingEnds = 0;
    // a bed waiting on the cut sting starts over, now
    if (this.lane && !this.lane.voice) this.lane = null;
    this.apply();
  }

  /** The page is hidden or shown: the clock stops with it. */
  setVisible(visible: boolean) {
    if (!this.ctx) return;
    if (visible) void this.ctx.resume();
    else void this.ctx.suspend();
  }

  dispose() {
    if (this.ticker) clearInterval(this.ticker);
    void this.ctx?.close();
    this.ctx = null;
    this.lane = null;
  }

  // ---------------------------------------------------------------------------------

  /** Bring what plays in line with what is wanted. */
  private apply() {
    const ctx = this.ctx;
    if (!ctx) return;
    const want = this.wanted && this.allows(this.wanted) ? this.wanted : null;
    if (this.lane && this.lane.bed.key === want?.key) return;
    this.release();
    if (!want) return;
    const lane: Lane = { bed: want, index: want.start ?? 0, voice: null, queued: false };
    this.lane = lane;
    void this.load(want.tracks[lane.index]).then((buffer) => {
      if (this.lane !== lane || this.ctx !== ctx) return;
      // a sting still loading: the bed waits for it (`sting` starts it again)
      if (this.stingEnds === Infinity) return;
      // after a sting, the bed comes in as it goes quiet
      const at = Math.max(ctx.currentTime, this.stingEnds - 0.5);
      lane.voice = this.start(buffer, at, { loop: this.loops(lane), fadeIn: XFADE });
    });
  }

  /** Fade out the bed that plays. */
  private release() {
    if (this.lane?.voice) this.fade(this.lane.voice, XFADE);
    this.lane = null;
  }

  /** Whether the lane's current track loops on itself. */
  private loops(lane: Lane): boolean {
    const { mode, tracks } = lane.bed;
    return mode === 'loop' || (mode === 'sequence' && lane.index === tracks.length - 1);
  }

  /**
   * Once a second: a playlist's next track, fetched ahead and brought in as this one ends; and
   * a context left with nothing to play is suspended after a few seconds (its fades done).
   */
  private tick() {
    const ctx = this.ctx;
    const lane = this.lane;
    if (ctx && !lane && this.stings.size === 0 && ctx.state === 'running') {
      if (++this.idle >= 4) void ctx.suspend();
    }
    if (!ctx || !lane?.voice || lane.queued || this.loops(lane)) return;
    const next = (lane.index + 1) % lane.bed.tracks.length;
    const left = lane.voice.ends - ctx.currentTime;
    if (left > PRELOAD) return;
    lane.queued = true;
    const current = lane.voice;
    void this.load(lane.bed.tracks[next]).then((buffer) => {
      if (this.lane !== lane || this.ctx !== ctx) return;
      const at = Math.max(ctx.currentTime, current.ends - XFADE);
      lane.index = next;
      lane.queued = false;
      lane.voice = this.start(buffer, at, { loop: this.loops(lane), fadeIn: XFADE });
      this.fade(current, XFADE, at - ctx.currentTime);
    });
  }

  private start(
    buffer: AudioBuffer,
    at: number,
    o: { loop: boolean; fadeIn: number },
  ): Voice {
    const ctx = this.ctx!;
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.loop = o.loop;
    const gain = ctx.createGain();
    src.connect(gain).connect(this.master!);
    if (o.fadeIn > 0) {
      gain.gain.setValueAtTime(0, at);
      gain.gain.linearRampToValueAtTime(1, at + o.fadeIn);
    }
    src.start(at);
    return { src, gain, at, ends: o.loop ? Infinity : at + buffer.duration };
  }

  /** Fade a voice out over `over` seconds, starting `after` seconds from now, and stop it. */
  private fade(voice: Voice, over: number, after = 0) {
    const ctx = this.ctx;
    if (!ctx) return;
    // still waiting for its start (behind a sting): it never sounds
    if (after === 0 && voice.at > ctx.currentTime) {
      try {
        voice.src.stop();
      } catch {
        // already stopped
      }
      return;
    }
    const from = Math.max(ctx.currentTime + after, voice.at);
    voice.gain.gain.cancelScheduledValues(from);
    voice.gain.gain.setValueAtTime(voice.gain.gain.value, from);
    voice.gain.gain.linearRampToValueAtTime(0, from + over);
    try {
      voice.src.stop(from + over + 0.05);
    } catch {
      // never started, or already stopped
    }
  }

  private load(url: string): Promise<AudioBuffer> {
    const ctx = this.ctx!;
    let got = this.buffers.get(url);
    if (got) {
      // most recently used last, so the oldest go first
      this.buffers.delete(url);
      this.buffers.set(url, got);
      return got;
    }
    got = fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${url}`);
        return r.arrayBuffer();
      })
      .then((bytes) => ctx.decodeAudioData(bytes));
    got.catch(() => this.buffers.delete(url));
    this.buffers.set(url, got);
    while (this.buffers.size > KEEP + 2) {
      const oldest = this.buffers.keys().next().value as string;
      this.buffers.delete(oldest);
    }
    return got;
  }
}
