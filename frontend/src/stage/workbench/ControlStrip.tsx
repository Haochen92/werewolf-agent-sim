'use client';

/**
 * The workbench's controls, as small plain pieces the page lines up in a strip above the
 * stage: a segmented choice, a select, the beat stepper with its caption, and the URL. They
 * hold no state of their own; each reports a change and the page writes it into the URL,
 * which is the workbench's only state.
 */
import type { ReactNode } from 'react';
import styles from './ControlStrip.module.css';

export function ControlStrip({ children }: { children: ReactNode }) {
  return (
    <nav className={styles.strip} aria-label="Workbench controls">
      {children}
    </nav>
  );
}

export function Group({
  label,
  wide,
  children,
}: {
  label: string;
  /** Take the rest of the row (the URL). */
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={wide ? `${styles.group} ${styles.wide}` : styles.group}>
      <span className={styles.label}>{label}</span>
      {children}
    </div>
  );
}

export interface SegOption<T extends string> {
  value: T;
  label?: string;
  /** Drawn quieter: a scene that is not built yet. */
  muted?: boolean;
}

export function Seg<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly (T | SegOption<T>)[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <Group label={label}>
      <div className={styles.seg} role="group" aria-label={label}>
        {options.map((o) => {
          const opt: SegOption<T> = typeof o === 'string' ? { value: o } : o;
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={opt.value === value}
              className={opt.muted ? styles.unbuilt : undefined}
              onClick={() => onChange(opt.value)}
            >
              {opt.label ?? opt.value}
            </button>
          );
        })}
      </div>
    </Group>
  );
}

export function Select({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <Group label={label}>
      <select
        className={styles.select}
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </Group>
  );
}

export function BeatStepper({
  index,
  count,
  label,
  anchor,
  onChange,
}: {
  index: number;
  count: number;
  /** The beat's name, "Speaks". */
  label: string;
  /** The beat's anchor line, "day.speech · seq 163 · public → player_2 · 11250 ms". */
  anchor: string;
  onChange: (i: number) => void;
}) {
  const go = (i: number) => onChange(Math.max(0, Math.min(count - 1, i)));
  return (
    <Group label="beat">
      <div className={styles.stepper}>
        <button type="button" onClick={() => go(index - 1)} disabled={index <= 0}>
          ◀
        </button>
        <input
          className={styles.num}
          type="number"
          aria-label="beat number"
          min={0}
          max={Math.max(0, count - 1)}
          value={index}
          onChange={(e) => go(Number(e.target.value) || 0)}
        />
        <button type="button" onClick={() => go(index + 1)} disabled={index >= count - 1}>
          ▶
        </button>
        <span className={styles.of}>of {count}</span>
        <span className={styles.caption}>
          <b>{label}</b>
          <span className={styles.anchor}>{anchor}</span>
        </span>
      </div>
    </Group>
  );
}

export function UrlReadout({ url }: { url: string }) {
  return (
    <Group label="url" wide>
      <output className={styles.url} aria-label="workbench URL">
        {url}
      </output>
    </Group>
  );
}
