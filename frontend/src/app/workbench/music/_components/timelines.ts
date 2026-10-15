/**
 * The scenes the music bench plays music against: each scene's beats with their holds at normal
 * speed, as `beatsFor` gives them in the carriage's game (68c26e83). A replay on Fast halves
 * every hold; the music itself never changes speed.
 */

export interface BenchBeat {
  id: string;
  label: string;
  /** The hold at normal speed, in seconds. */
  s: number;
}

export interface TimedBeat extends BenchBeat {
  /** When the beat starts and ends, in seconds from the scene's start, at the chosen speed. */
  at: number;
  end: number;
}

export const LYNCH: BenchBeat[] = [
  { id: 'stand-returns', label: 'The stand returns', s: 6 },
  { id: 'named', label: 'Voted out', s: 2 },
  { id: 'drop', label: 'The drop', s: 2 },
  { id: 'card-up', label: 'The card comes up', s: 4 },
  { id: 'truth', label: 'The truth', s: 4 },
  { id: 'card-to-wing', label: 'The card goes to the wing', s: 6 },
];

/** A morning with one death; `MORNING_TWO` has a second attack, saved. */
export const MORNING_ONE: BenchBeat[] = [
  { id: 'shutter-down', label: 'The shutter', s: 6 },
  { id: 'chip-attacked', label: 'Attacked', s: 2.5 },
  { id: 'chip-fell', label: 'Fell', s: 2.5 },
  { id: 'card-down', label: 'The card comes down', s: 4 },
  { id: 'roll', label: 'The roll', s: 8 },
  { id: 'day-begins', label: 'The day begins', s: 6 },
];

export const MORNING_TWO: BenchBeat[] = [
  { id: 'shutter-down', label: 'The shutter', s: 6 },
  { id: 'chip-attacked', label: 'Attacked', s: 2.5 },
  { id: 'chip-fell', label: 'Fell', s: 2.5 },
  { id: 'card-down', label: 'The card comes down', s: 4 },
  { id: 'chip-attacked-2', label: 'Attacked', s: 2.5 },
  { id: 'chip-saved', label: 'Saved', s: 4 },
  { id: 'roll', label: 'The roll', s: 12 },
  { id: 'day-begins', label: 'The day begins', s: 6 },
];

/** The curtain stays up until the viewer leaves; the bench shows 20 s of it. */
export const ENDING: BenchBeat[] = [
  { id: 'where-it-ended', label: 'Where it ended', s: 8 },
  { id: 'winners-hour', label: "The winners' hour", s: 6 },
  { id: 'verdict', label: 'The verdict', s: 6 },
  { id: 'winners-stand', label: 'The winners stand', s: 6 },
  { id: 'truth', label: 'The truth', s: 4 },
  { id: 'curtain', label: 'The curtain (stays up)', s: 20 },
];

export type Speed = 'normal' | 'fast';

/** The beats laid end to end at a speed: when each starts and ends. */
export function timeline(beats: readonly BenchBeat[], speed: Speed): TimedBeat[] {
  const k = speed === 'fast' ? 0.5 : 1;
  let at = 0;
  return beats.map((b) => {
    const t = { ...b, at, end: at + b.s * k };
    at = t.end;
    return t;
  });
}

/** When a beat starts in a laid-out timeline (the first with that id). */
export function startOf(line: readonly TimedBeat[], id: string): number {
  const beat = line.find((b) => b.id === id);
  if (!beat) throw new Error(`no beat ${id}`);
  return beat.at;
}

/** The beat playing at a time, or null before the start and after the end. */
export function beatAt(line: readonly TimedBeat[], t: number): TimedBeat | null {
  return line.find((b) => t >= b.at && t < b.end) ?? null;
}

export interface Measure {
  /** Length in seconds. */
  duration: number;
  /** Mean loudness of the mono mix, dBFS. */
  rms: number;
  /** Highest sample, dBFS. */
  peak: number;
  /** Silence at the end (below −50 dBFS in 50 ms windows), seconds. */
  silentTail: number;
}

const db = (v: number) => 20 * Math.log10(Math.max(v, 1e-9));

/** A track's length, loudness and silent tail, from its channels' samples. */
export function measure(channels: readonly Float32Array[], sampleRate: number): Measure {
  const n = channels[0]?.length ?? 0;
  let sum = 0;
  let peak = 0;
  const w = Math.max(1, Math.round(sampleRate * 0.05));
  const windows: number[] = [];
  let acc = 0;
  for (let i = 0; i < n; i++) {
    let m = 0;
    for (const c of channels) {
      const v = c[i];
      m += v;
      const a = Math.abs(v);
      if (a > peak) peak = a;
    }
    m /= channels.length;
    sum += m * m;
    acc += m * m;
    if ((i + 1) % w === 0) {
      windows.push(Math.sqrt(acc / w));
      acc = 0;
    }
  }
  let quiet = 0;
  for (let i = windows.length - 1; i >= 0 && db(windows[i]) < -50; i--) quiet++;
  return {
    duration: n / sampleRate,
    rms: db(Math.sqrt(sum / Math.max(1, n))),
    peak: db(peak),
    silentTail: quiet * (w / sampleRate),
  };
}

/** A track built to loop has no silent tail; a one-shot ends in silence. */
export const isLoop = (m: Measure) => m.silentTail < 0.3;
