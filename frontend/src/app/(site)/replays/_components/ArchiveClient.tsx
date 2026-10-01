'use client';
/**
 * The archive (`/replays`, replays mockup): one fetch of the newest 500 finished games, then
 * every filter and the sort run here in the browser (review §F6). The total in the count comes
 * from the list's `X-Total-Count` header, so the page can say when the archive holds more games
 * than it loaded.
 *
 * States: loading (skeleton slates), error, an empty archive, nothing matching the filters, and
 * the results as slates or as a table.
 */
import { useMemo, useState } from 'react';
import Link from 'next/link';
import { SegmentedControl, Select, Skeleton } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { listReplaysWithTotal } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { queryKeys } from '@/lib/queryKeys';
import {
  NO_FILTERS,
  activeFilters,
  applyFilters,
  distinctModels,
  type ReplayFilters,
  type ReplaySort,
} from '@/lib/replay-filters';
import { useModelLabels } from '@/hooks/useModelLabels';
import { usePlayedHere } from '@/hooks/usePlayedHere';
import { Button, Icon, Slate, SlateGrid } from '@/components/site';
import type { ReplaySummary } from '@/types/contracts';
import { FilterRail } from './FilterRail';
import { ArchiveTable } from './ArchiveTable';
import classes from './Archive.module.css';

/** The one fetch. Past this, the count says only the newest are loaded (review §E4). */
const LIMIT = 500;
/** Slates (or rows) shown before "Show more games". */
const PAGE = 12;
const NONE: ReplaySummary[] = [];

const SORTS: { value: ReplaySort; label: string }[] = [
  { value: 'new', label: 'Newest first' },
  { value: 'old', label: 'Oldest first' },
  { value: 'long', label: 'Longest first' },
  { value: 'short', label: 'Shortest first' },
];

export function ArchiveClient() {
  const archive = useQuery({
    queryKey: queryKeys.replays.archive(LIMIT),
    queryFn: () => listReplaysWithTotal({ limit: LIMIT }),
  });
  const modelName = useModelLabels();
  const mine = usePlayedHere();

  const [filters, setFilters] = useState<ReplayFilters>(NO_FILTERS);
  const [sort, setSort] = useState<ReplaySort>('new');
  const [view, setView] = useState<'cards' | 'list'>('cards');
  const [shown, setShown] = useState(PAGE);

  const rows = archive.data?.replays ?? NONE;
  const results = useMemo(
    () => applyFilters(rows, filters, sort, mine),
    [rows, filters, sort, mine],
  );
  const models = useMemo(() => distinctModels(rows), [rows]);
  const active = activeFilters(filters, modelName);

  const refilter = (next: ReplayFilters) => {
    setFilters(next);
    setShown(PAGE);
  };

  if (archive.error) {
    // 503 is "the archive isn't configured": an operator problem, worth its own words
    const unavailable = archive.error instanceof ApiError && archive.error.isUnavailable;
    return (
      <div className={classes.empty} role="alert">
        <h3 className={classes.emptyTitle}>The archive could not be opened</h3>
        <p className={classes.emptyText}>
          {unavailable
            ? 'The replay archive is not configured on this server.'
            : `The server said: ${archive.error.message}`}
        </p>
        <Button onClick={() => archive.refetch()} loading={archive.isFetching}>
          Try again
        </Button>
      </div>
    );
  }

  if (archive.data && rows.length === 0) {
    return (
      <div className={classes.empty}>
        <h3 className={classes.emptyTitle}>Nothing in the archive yet</h3>
        <p className={classes.emptyText}>
          Every game that finishes lands here, with the X-ray open. Play one and it will be
          the first.
        </p>
        <Button component={Link} href="/play" variant="primary">
          Take a seat
        </Button>
      </div>
    );
  }

  const total = archive.data?.total ?? 0;
  const page = results.slice(0, shown);

  return (
    <div className={classes.grid}>
      <FilterRail
        filters={filters}
        onChange={refilter}
        models={models}
        modelName={modelName}
        activeCount={active.length}
      />

      <section aria-label="Games" className={classes.results} aria-busy={archive.isPending}>
        <div className={classes.bar}>
          <span className={classes.count} aria-live="polite">
            {archive.isPending ? (
              'Opening the archive…'
            ) : (
              <>
                Showing <b>{results.length}</b> of {total} {total === 1 ? 'game' : 'games'}
                {total > rows.length ? ` (the newest ${rows.length} are loaded)` : ''}
              </>
            )}
          </span>
          {active.length ? (
            <div className={classes.active}>
              {active.map((a) => (
                <button
                  key={a.key}
                  type="button"
                  className={classes.activeChip}
                  onClick={() => refilter(a.without)}
                >
                  {a.label}
                  <Icon name="i-x" size={14} />
                  <span className={classes.sr}> (remove)</span>
                </button>
              ))}
            </div>
          ) : null}
          <span className={classes.spacer} />
          <div className={classes.sort}>
            <label htmlFor="archive-sort">Sort</label>
            <Select
              id="archive-sort"
              data={SORTS}
              value={sort}
              allowDeselect={false}
              onChange={(v) => v && setSort(v as ReplaySort)}
              w={156}
            />
          </div>
          <SegmentedControl
            aria-label="View"
            className={classes.viewToggle}
            classNames={{ label: classes.viewToggleLabel }}
            value={view}
            onChange={(v) => setView(v as 'cards' | 'list')}
            data={[
              { value: 'cards', label: <Icon name="i-grid" label="Cards" /> },
              { value: 'list', label: <Icon name="i-list" label="List" /> },
            ]}
          />
        </div>

        {archive.isPending ? (
          <SlateGrid className={classes.games}>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={262} radius="md" className={classes.skeleton} />
            ))}
          </SlateGrid>
        ) : results.length === 0 ? (
          <div className={classes.empty}>
            <h3 className={classes.emptyTitle}>No game matches these filters</h3>
            <p className={classes.emptyText}>
              Loosen one of them, or clear them all to see the whole archive.
            </p>
            <Button variant="primary" onClick={() => refilter(NO_FILTERS)}>
              Clear filters
            </Button>
          </div>
        ) : view === 'cards' ? (
          <>
            <p className={classes.instruct}>
              <span className={classes.instructIcon}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M5 3 L21 12 L5 21 Z" />
                </svg>
              </span>
              Click any record to watch the replay.
            </p>
            <SlateGrid className={classes.games}>
              {page.map((r) => (
                <Slate
                  key={r.game_id}
                  replay={r}
                  modelLabel={r.model ? modelName(r.model) : undefined}
                  mine={mine.has(r.game_id)}
                />
              ))}
            </SlateGrid>
          </>
        ) : (
          <ArchiveTable rows={page} modelName={modelName} mine={mine} />
        )}

        {results.length > shown ? (
          <div className={classes.more}>
            <Button onClick={() => setShown((n) => n + PAGE)}>Show more games</Button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
