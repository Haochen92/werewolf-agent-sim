'use client';
/**
 * The archive's filter rail (replays mockup `.rail`): an id search, "played on this device",
 * who won (a side by its mark, a lone killer or a neutral by its role's sigil), where it ended, memory, who sat at the table, the model, and the finishing dates.
 * Sticky beside the results on a wide screen; on a narrow one it folds behind a "Filters" bar
 * so the games are not pushed a screen down.
 */
import { useId, useState } from 'react';
import { Chip, SegmentedControl, Select, Switch, TextInput } from '@mantine/core';
import { Button, Icon } from '@/components/site';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import { NO_FILTERS, type ReplayFilters, type WonBy } from '@/lib/replay-filters';
import classes from './Archive.module.css';

/** The model dropdown's stand-ins: Mantine's Select has no empty-string or null option. */
const ANY_MODEL = '__any__';
const NO_MODEL = '__none__';

/** Each chip's mark: a side's (`side`), or a role's sigil (`role`); a draw has none. */
const WINNERS: {
  value: WonBy;
  label: string;
  hue: string;
  side?: 'villagers' | 'wolves';
  role?: string;
}[] = [
  { value: 'villagers', label: 'The town', hue: 'var(--town)', side: 'villagers' },
  { value: 'wolves', label: 'The wolves', hue: 'var(--wolf)', side: 'wolves' },
  {
    value: 'serial_killer',
    label: 'The serial killer',
    hue: 'var(--sk)',
    role: 'serial_killer',
  },
  { value: 'necromancer', label: 'The necromancer', hue: 'var(--sk)', role: 'necromancer' },
  {
    value: 'speculator',
    label: 'The speculator',
    hue: 'var(--benign)',
    role: 'speculator',
  },
  {
    value: 'fortune_teller',
    label: 'The fortune teller',
    hue: 'var(--benign)',
    role: 'fortune_teller',
  },
  { value: 'draw', label: 'A draw', hue: 'var(--muted)' },
];

export function FilterRail({
  filters,
  onChange,
  models,
  modelName,
  activeCount,
}: {
  filters: ReplayFilters;
  onChange: (next: ReplayFilters) => void;
  /** The model ids in the archive (`''` = unrecorded), from `distinctModels`. */
  models: string[];
  modelName: (id: string) => string;
  activeCount: number;
}) {
  const [open, setOpen] = useState(false);
  const bodyId = useId();
  const set = (patch: Partial<ReplayFilters>) => onChange({ ...filters, ...patch });

  const modelValue =
    filters.model === null ? ANY_MODEL : filters.model === '' ? NO_MODEL : filters.model;
  const modelData = [
    { value: ANY_MODEL, label: 'Any model' },
    ...models.map((id) => ({
      value: id || NO_MODEL,
      label: id ? modelName(id) : 'Not recorded',
    })),
  ];

  return (
    <aside className={classes.rail} aria-label="Filters" data-open={open || undefined}>
      <div className={classes.railHead}>
        <h2 className={classes.railTitle}>Filters</h2>
        <Button
          type="button"
          size="sm"
          className={classes.railToggle}
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => setOpen((o) => !o)}
          rightSection={<Icon name={open ? 'i-minus' : 'i-plus'} size={16} />}
        >
          Filters
          {activeCount ? <span className={classes.railCount}>{activeCount}</span> : null}
        </Button>
        {activeCount ? (
          <Button
            type="button"
            variant="text"
            size="sm"
            onClick={() => onChange(NO_FILTERS)}
          >
            Clear all
          </Button>
        ) : null}
      </div>

      <div className={classes.railBody} id={bodyId}>
        <div className={classes.fs} data-first>
          <TextInput
            aria-label="Game id"
            placeholder="Game id, e.g. 9369a5c1"
            autoComplete="off"
            leftSection={<Icon name="i-search" />}
            value={filters.q}
            onChange={(e) => set({ q: e.currentTarget.value })}
          />
        </div>

        <div className={classes.fs}>
          <Switch
            label="Played on this device"
            description="Games you sat in, remembered by this browser."
            checked={filters.mine}
            onChange={(e) => set({ mine: e.currentTarget.checked })}
          />
        </div>

        <fieldset className={classes.fs}>
          <legend className={classes.legend}>Won by</legend>
          <Chip.Group
            multiple
            value={filters.winners}
            onChange={(v) => set({ winners: v as WonBy[] })}
          >
            <div className={classes.fchips}>
              {WINNERS.map((w) => (
                <Chip key={w.value} value={w.value}>
                  {w.side ? (
                    <FactionMark
                      faction={w.side}
                      format="mark"
                      variant="stamp"
                      small
                      className={classes.fchipSigil}
                      style={{ color: w.hue }}
                    />
                  ) : w.role ? (
                    <Sigil
                      role={w.role}
                      small
                      className={classes.fchipSigil}
                      style={{ color: w.hue }}
                    />
                  ) : null}
                  {w.label}
                </Chip>
              ))}
            </div>
          </Chip.Group>
        </fieldset>

        <fieldset className={classes.fs}>
          <legend className={classes.legend}>Ended in</legend>
          <SegmentedControl
            fullWidth
            aria-label="Ended in"
            value={filters.ended}
            onChange={(v) => set({ ended: v as ReplayFilters['ended'] })}
            data={[
              { value: 'any', label: 'Any' },
              { value: 'day', label: 'Day' },
              { value: 'voting', label: 'Vote' },
              { value: 'night', label: 'Night' },
            ]}
          />
        </fieldset>

        <fieldset className={classes.fs}>
          <legend className={classes.legend}>Agents&rsquo; memory</legend>
          <SegmentedControl
            fullWidth
            aria-label="Agents' memory"
            value={filters.memory}
            onChange={(v) => set({ memory: v as ReplayFilters['memory'] })}
            data={[
              { value: 'any', label: 'Any' },
              { value: 'on', label: 'On' },
              { value: 'off', label: 'Off' },
            ]}
          />
        </fieldset>

        <fieldset className={classes.fs}>
          <legend className={classes.legend}>At the table</legend>
          <SegmentedControl
            fullWidth
            orientation="vertical"
            aria-label="At the table"
            value={filters.table}
            onChange={(v) => set({ table: v as ReplayFilters['table'] })}
            data={[
              { value: 'any', label: 'Any' },
              { value: 'people', label: 'With human players' },
              { value: 'agents', label: 'AI agents only' },
            ]}
          />
        </fieldset>

        <div className={classes.fs}>
          <Select
            label="Model"
            data={modelData}
            value={modelValue}
            allowDeselect={false}
            onChange={(v) =>
              set({ model: !v || v === ANY_MODEL ? null : v === NO_MODEL ? '' : v })
            }
          />
        </div>

        <fieldset className={classes.fs}>
          <legend className={classes.legend}>Finished</legend>
          <div className={classes.dates}>
            <TextInput
              type="date"
              label="From"
              size="sm"
              classNames={{ input: classes.dateInput }}
              value={filters.from}
              max={filters.to || undefined}
              onChange={(e) => set({ from: e.currentTarget.value })}
            />
            <TextInput
              type="date"
              label="To"
              size="sm"
              classNames={{ input: classes.dateInput }}
              value={filters.to}
              min={filters.from || undefined}
              onChange={(e) => set({ to: e.currentTarget.value })}
            />
          </div>
        </fieldset>
      </div>
    </aside>
  );
}
