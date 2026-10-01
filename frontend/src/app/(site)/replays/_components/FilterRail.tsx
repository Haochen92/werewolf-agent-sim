'use client';
/**
 * The archive's filter rail (replays mockup `.rail`): an id search, "played on this device",
 * who won, where it ended, memory, who sat at the table, the model, and the finishing dates.
 * Sticky beside the results on a wide screen; on a narrow one it folds behind a "Filters" bar
 * so the games are not pushed a screen down.
 */
import { useId, useState } from 'react';
import { Chip, SegmentedControl, Select, Switch, TextInput } from '@mantine/core';
import type { Winner } from '@/types/contracts';
import { Icon } from '@/components/site';
import { Sigil } from '@/stage/instruments/Sigil';
import { NO_FILTERS, type ReplayFilters } from '@/lib/replay-filters';
import classes from './Archive.module.css';

/** The model dropdown's stand-ins: Mantine's Select has no empty-string or null option. */
const ANY_MODEL = '__any__';
const NO_MODEL = '__none__';

const WINNERS: { value: Winner; label: string; sigil: string; hue: string }[] = [
  { value: 'villagers', label: 'The village', sigil: 'villager', hue: 'var(--town)' },
  { value: 'wolves', label: 'The wolves', sigil: 'wolf', hue: 'var(--wolf)' },
  {
    value: 'serial_killer',
    label: 'The serial killer',
    sigil: 'serial_killer',
    hue: 'var(--sk)',
  },
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
        <button
          type="button"
          className={classes.railToggle}
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => setOpen((o) => !o)}
        >
          Filters
          {activeCount ? <span className={classes.railCount}>{activeCount}</span> : null}
          <Icon name={open ? 'i-minus' : 'i-plus'} size={16} />
        </button>
        {activeCount ? (
          <button
            type="button"
            className={classes.clearAll}
            onClick={() => onChange(NO_FILTERS)}
          >
            Clear all
          </button>
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
            onChange={(v) => set({ winners: v as Winner[] })}
          >
            <div className={classes.fchips}>
              {WINNERS.map((w) => (
                <Chip key={w.value} value={w.value}>
                  <Sigil
                    role={w.sigil}
                    className={classes.fchipSigil}
                    style={{ color: w.hue }}
                    strokeWidth={3.2}
                  />
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
