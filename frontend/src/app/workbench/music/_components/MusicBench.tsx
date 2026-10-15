'use client';

/**
 * The music bench's page: the candidates by cue, and three scene runs (the lynch, the morning,
 * the ending) that play the chosen files against the scene's beats as the stage holds them.
 * Each file is measured once it has been played (length, loudness, whether it loops). The
 * "Keep" marks are kept on this device and listed at the foot, to copy back.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { BenchPlayer, type Voice } from './engine';
import {
  ENDING,
  LYNCH,
  MORNING_ONE,
  MORNING_TWO,
  beatAt,
  isLoop,
  startOf,
  timeline,
  type Measure,
  type Speed,
  type TimedBeat,
} from './timelines';
import styles from './MusicBench.module.css';

export interface Track {
  name: string;
  url: string;
}
export interface Cue {
  id: string;
  name: string;
  files: Track[];
}

/** One sound in a scene run: where it sits on the scene's clock, for its lane. */
interface Lane {
  name: string;
  from: number;
  to: number;
}

interface Run {
  scene: string;
  line: TimedBeat[];
  /** The audio clock's time at the scene's start. */
  t0: number;
  end: number;
  lanes: Lane[];
  voices: Voice[];
}

const KEEP_KEY = 'music-bench-keep';
const fmt = (s: number) => `${s.toFixed(1)} s`;

export function MusicBench({ cues }: { cues: Cue[] }) {
  const [player] = useState(() => new BenchPlayer());

  const [measures, setMeasures] = useState<Record<string, Measure>>({});
  const [playing, setPlaying] = useState<{
    url: string;
    voice: Voice;
    seam: boolean;
  } | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [now, setNow] = useState(0);
  const [speed, setSpeed] = useState<Speed>('normal');
  const [volume, setVolume] = useState(0.8);
  const [keep, setKeep] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const byCue = useMemo(() => Object.fromEntries(cues.map((c) => [c.id, c.files])), [cues]);

  useEffect(() => {
    try {
      setKeep(JSON.parse(localStorage.getItem(KEEP_KEY) ?? '{}'));
    } catch {
      // a private window: the marks last for the visit
    }
  }, []);
  const toggleKeep = (url: string) =>
    setKeep((k) => {
      const next = { ...k, [url]: !k[url] };
      try {
        localStorage.setItem(KEEP_KEY, JSON.stringify(next));
      } catch {
        // as above
      }
      return next;
    });

  // the clock for the progress bars and the runs' playhead, only while something sounds
  useEffect(() => {
    if (!playing && !run) return;
    let frame = 0;
    const tick = () => {
      setNow(player.now());
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [player, playing, run]);

  // a run ends by itself at its scene's end
  useEffect(() => {
    if (run && now > run.t0 + run.end + 0.5) {
      player.stopAll();
      setRun(null);
    }
  }, [player, run, now]);

  const load = useCallback(
    async (url: string) => {
      const got = await player.load(url);
      setMeasures((m) => (m[url] ? m : { ...m, [url]: got.m }));
      return got;
    },
    [player],
  );

  const stop = () => {
    player.stopAll();
    setPlaying(null);
    setRun(null);
  };

  const play = async (url: string, seam: boolean) => {
    stop();
    setError(null);
    try {
      const { buffer, m } = await load(url);
      const loop = isLoop(m);
      // the seam: the last 4 s running on into the first 4, through the buffer's own loop
      const voice = seam
        ? player.play(buffer, { offset: buffer.duration - 4, loop: true, duration: 8 })
        : player.play(buffer, { loop });
      setPlaying({ url, voice, seam });
    } catch (e) {
      setError(String(e));
    }
  };

  const startRun = async (scene: string, build: () => Promise<Omit<Run, 'scene'>>) => {
    stop();
    setError(null);
    try {
      setRun({ scene, ...(await build()) });
    } catch (e) {
      setError(String(e));
    }
  };

  const setVol = (v: number) => {
    setVolume(v);
    player.setVolume(v);
  };

  const kept = cues.flatMap((c) =>
    c.files.filter((f) => keep[f.url]).map((f) => `${c.name}: ${f.name}`),
  );
  const dropped = cues.flatMap((c) =>
    c.files.filter((f) => !keep[f.url]).map((f) => `${c.name}: ${f.name}`),
  );
  const summary = `Keep:\n${kept.join('\n') || '(none)'}\n\nDrop:\n${dropped.join('\n') || '(none)'}`;

  return (
    <main className={styles.page}>
      <header className={styles.head}>
        <h1>Music bench</h1>
        <p>
          Nothing plays until you press. Loops play exactly as the game will loop them;{' '}
          <b>Seam</b> plays a loop&rsquo;s last 4 s into its first 4. A file is measured
          once it has been played.
        </p>
        <div className={styles.controls}>
          <label>
            Volume{' '}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={(e) => setVol(Number(e.target.value))}
            />
          </label>
          <button type="button" onClick={stop}>
            Stop all
          </button>
        </div>
        {error && <p className={styles.error}>{error}</p>}
        {cues.length === 0 && (
          <p className={styles.error}>No music in public/game_music.</p>
        )}
      </header>

      <section className={styles.runs}>
        <div className={styles.runsHead}>
          <h2>Against the stage</h2>
          <div className={styles.speed} role="radiogroup" aria-label="Replay speed">
            {(['normal', 'fast'] as const).map((s) => (
              <button
                key={s}
                type="button"
                role="radio"
                aria-checked={speed === s}
                onClick={() => setSpeed(s)}
              >
                {s === 'normal' ? 'Normal' : 'Fast (replay)'}
              </button>
            ))}
          </div>
        </div>
        <LynchRun
          files={byCue.lynch ?? []}
          speed={speed}
          load={load}
          start={startRun}
          player={player}
        />
        <MorningRun
          files={byCue.morning ?? []}
          day={byCue.discussion ?? []}
          speed={speed}
          load={load}
          start={startRun}
          player={player}
        />
        <EndingRun
          stings={byCue.victory ?? []}
          loops={[...(byCue.lobby ?? []), ...(byCue.discussion ?? [])]}
          speed={speed}
          load={load}
          start={startRun}
          player={player}
        />
        {run && <RunView run={run} at={now - run.t0} onStop={stop} />}
      </section>

      {cues.map((cue) => (
        <section key={cue.id} className={styles.cue}>
          <h2>{cue.name}</h2>
          <ul className={styles.rows}>
            {cue.files.map((f) => {
              const m = measures[f.url];
              const on = playing?.url === f.url ? playing : null;
              const pos = on ? player.position(on.voice) : null;
              const len = on?.seam ? 8 : m?.duration;
              const shown = on?.seam && on ? Math.max(0, now - on.voice.when) : pos;
              return (
                <li key={f.url} className={styles.row} data-on={!!on || undefined}>
                  <label className={styles.keep}>
                    <input
                      type="checkbox"
                      checked={!!keep[f.url]}
                      onChange={() => toggleKeep(f.url)}
                    />
                    Keep
                  </label>
                  <span className={styles.name}>{f.name}</span>
                  <span className={styles.meta}>
                    {m
                      ? `${fmt(m.duration)} · ${m.rms.toFixed(1)} dB · ${isLoop(m) ? 'loop' : 'one-shot'}`
                      : '—'}
                  </span>
                  <span className={styles.buttons}>
                    <button
                      type="button"
                      onClick={() => (on && !on.seam ? stop() : play(f.url, false))}
                    >
                      {on && !on.seam ? 'Stop' : 'Play'}
                    </button>
                    {(!m || isLoop(m)) && (
                      <button
                        type="button"
                        onClick={() => (on?.seam ? stop() : play(f.url, true))}
                      >
                        {on?.seam ? 'Stop' : 'Seam'}
                      </button>
                    )}
                  </span>
                  <span className={styles.bar}>
                    {on && len && shown !== null && (
                      <i style={{ width: `${Math.min(100, (shown / len) * 100)}%` }} />
                    )}
                    {on?.seam && <b className={styles.seamMark} />}
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      ))}

      <section className={styles.cue}>
        <h2>Your picks</h2>
        <pre className={styles.summary}>{summary}</pre>
        <button
          type="button"
          onClick={() => {
            void navigator.clipboard?.writeText(summary).catch(() => undefined);
          }}
        >
          Copy
        </button>
      </section>
    </main>
  );
}

type Loader = (url: string) => Promise<{ buffer: AudioBuffer; m: Measure }>;
type Starter = (scene: string, build: () => Promise<Omit<Run, 'scene'>>) => void;

interface RunProps {
  speed: Speed;
  load: Loader;
  start: Starter;
  player: BenchPlayer;
}

/** Every sound of a run is scheduled from one instant, once its files have loaded. */
const LEAD = 0.15;

function Pick({
  label,
  files,
  value,
  onChange,
  none = false,
}: {
  label: string;
  files: Track[];
  value: string;
  onChange: (v: string) => void;
  none?: boolean;
}) {
  return (
    <label className={styles.pick}>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {none && <option value="">None</option>}
        {files.map((f) => (
          <option key={f.url} value={f.url}>
            {f.name}
          </option>
        ))}
      </select>
    </label>
  );
}

const first = (files: Track[], hint: string) =>
  (files.find((f) => f.name.includes(hint)) ?? files[0])?.url ?? '';

/** The lynch: a piece from the scene's start, a sting on "Voted out", or both. */
function LynchRun({ files, speed, load, start, player }: RunProps & { files: Track[] }) {
  const [whole, setWhole] = useState(() => first(files, 'psalm'));
  const [sting, setSting] = useState('');
  const go = () =>
    start('The lynch', async () => {
      const line = timeline(LYNCH, speed);
      const cues = [
        [whole, 0],
        [sting, startOf(line, 'named')],
      ] as const;
      const loaded = await Promise.all(cues.map(([url]) => (url ? load(url) : null)));
      const t0 = player.now() + LEAD;
      const lanes: Lane[] = [];
      const voices: Voice[] = [];
      cues.forEach(([url, at], i) => {
        const got = loaded[i];
        if (!got) return;
        voices.push(player.play(got.buffer, { in: LEAD + at }));
        lanes.push({ name: nameOf(files, url), from: at, to: at + got.buffer.duration });
      });
      return { t0, line, end: line.at(-1)!.end, lanes, voices };
    });
  return (
    <div className={styles.run}>
      <h3>The lynch</h3>
      <Pick
        label="From the scene's start"
        files={files}
        value={whole}
        onChange={setWhole}
        none
      />
      <Pick label='On "Voted out"' files={files} value={sting} onChange={setSting} none />
      <button type="button" onClick={go}>
        Run
      </button>
    </div>
  );
}

/** The morning: its music from the shutter, the day's coming in at "The day begins". */
function MorningRun({
  files,
  day,
  speed,
  load,
  start,
  player,
}: RunProps & { files: Track[]; day: Track[] }) {
  const [music, setMusic] = useState(() => first(files, 'extended'));
  const [then, setThen] = useState(() => first(day, ''));
  const [deaths, setDeaths] = useState<'one' | 'two'>('one');
  const go = () =>
    start('The morning', async () => {
      const line = timeline(deaths === 'one' ? MORNING_ONE : MORNING_TWO, speed);
      const dayAt = startOf(line, 'day-begins');
      const end = line.at(-1)!.end + 4;
      const [a, b] = await Promise.all([
        music ? load(music) : null,
        then ? load(then) : null,
      ]);
      const t0 = player.now() + LEAD;
      const lanes: Lane[] = [];
      const voices: Voice[] = [];
      if (a) {
        const loop = isLoop(a.m);
        const v = player.play(a.buffer, { in: LEAD, loop });
        // the morning's music gives way to the day's over 3 s
        player.fadeOut(v, 3, LEAD + dayAt);
        voices.push(v);
        lanes.push({
          name: nameOf(files, music),
          from: 0,
          to: Math.min(dayAt + 3, loop ? Infinity : a.buffer.duration),
        });
      }
      if (b) {
        voices.push(player.play(b.buffer, { in: LEAD + dayAt, loop: true, fadeIn: 3 }));
        lanes.push({ name: nameOf(day, then), from: dayAt, to: end });
      }
      return { t0, line, end, lanes, voices };
    });
  return (
    <div className={styles.run}>
      <h3>The morning</h3>
      <Pick label="From the shutter" files={files} value={music} onChange={setMusic} none />
      <Pick label='At "The day begins"' files={day} value={then} onChange={setThen} none />
      <label className={styles.pick}>
        Deaths
        <select value={deaths} onChange={(e) => setDeaths(e.target.value as 'one' | 'two')}>
          <option value="one">One (29 s)</option>
          <option value="two">One, and one saved (39.5 s)</option>
        </select>
      </label>
      <button type="button" onClick={go}>
        Run
      </button>
    </div>
  );
}

/** The ending: the winner's sting on their hour, then the ending loop through the curtain. */
function EndingRun({
  stings,
  loops,
  speed,
  load,
  start,
  player,
}: RunProps & { stings: Track[]; loops: Track[] }) {
  const [sting, setSting] = useState(() => first(stings, 'town'));
  const [loop, setLoop] = useState(() => first(loops, 'lobby'));
  const [hand, setHand] = useState<'after' | 'overlap'>('after');
  const go = () =>
    start('The ending', async () => {
      const line = timeline(ENDING, speed);
      const hour = startOf(line, 'winners-hour');
      const end = line.at(-1)!.end;
      const [a, b] = await Promise.all([
        sting ? load(sting) : null,
        loop ? load(loop) : null,
      ]);
      const t0 = player.now() + LEAD;
      const lanes: Lane[] = [];
      const voices: Voice[] = [];
      let loopAt = hour;
      if (a) {
        voices.push(player.play(a.buffer, { in: LEAD + hour }));
        lanes.push({
          name: nameOf(stings, sting),
          from: hour,
          to: hour + a.buffer.duration,
        });
        // after: once the sting has gone quiet; overlap: under it from 4 s
        loopAt = hand === 'after' ? hour + a.buffer.duration - a.m.silentTail : hour + 4;
      }
      if (b) {
        const fadeIn = hand === 'after' ? 2 : 4;
        voices.push(player.play(b.buffer, { in: LEAD + loopAt, loop: true, fadeIn }));
        lanes.push({ name: nameOf(loops, loop), from: loopAt, to: end });
      }
      return { t0, line, end, lanes, voices };
    });
  return (
    <div className={styles.run}>
      <h3>The ending</h3>
      <Pick
        label="The winner's sting"
        files={stings}
        value={sting}
        onChange={setSting}
        none
      />
      <Pick
        label="Then the ending loop"
        files={loops}
        value={loop}
        onChange={setLoop}
        none
      />
      <label className={styles.pick}>
        Hand-over
        <select
          value={hand}
          onChange={(e) => setHand(e.target.value as 'after' | 'overlap')}
        >
          <option value="after">After the sting</option>
          <option value="overlap">Under the sting from 4 s</option>
        </select>
      </label>
      <button type="button" onClick={go}>
        Run
      </button>
    </div>
  );
}

const nameOf = (files: Track[], url: string) =>
  files.find((f) => f.url === url)?.name ?? url;

/** The running scene: its beats along the top, the music's lanes under them, a playhead. */
function RunView({ run, at, onStop }: { run: Run; at: number; onStop: () => void }) {
  const pct = (t: number) => `${(Math.min(Math.max(t, 0), run.end) / run.end) * 100}%`;
  const current = beatAt(run.line, at);
  return (
    <div className={styles.view}>
      <div className={styles.viewHead}>
        <b>{run.scene}</b> · {fmt(Math.max(0, at))} · {current?.label ?? '—'}
        <button type="button" onClick={onStop}>
          Stop
        </button>
      </div>
      <div className={styles.track}>
        {run.line.map((b) => (
          <span
            key={`${b.id}-${b.at}`}
            className={styles.beat}
            data-on={current === b || undefined}
            style={{ left: pct(b.at), width: `calc(${pct(b.end)} - ${pct(b.at)})` }}
            title={`${b.label}: ${fmt(b.end - b.at)}`}
          >
            {b.label}
          </span>
        ))}
        {run.lanes.map((l, i) => (
          <span
            key={`${l.name}-${i}`}
            className={styles.lane}
            style={{
              top: `${36 + i * 26}px`,
              left: pct(l.from),
              width: `calc(${pct(l.to)} - ${pct(l.from)})`,
            }}
          >
            {l.name}
          </span>
        ))}
        <i className={styles.playhead} style={{ left: pct(at) }} />
      </div>
    </div>
  );
}
