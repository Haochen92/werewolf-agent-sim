'use client';
/**
 * The archive's list view (replays mockup `table`): one row per game for scanning many at once,
 * with the full id, and a "you" mark on the games this browser sat in.
 */
import Link from 'next/link';
import { Table } from '@mantine/core';
import type { ReplaySummary, Winner } from '@/types/contracts';
import { Button } from '@/components/site';
import { Sigil } from '@/stage/instruments/Sigil';
import { endedLabel, formatDate } from '@/lib/format';
import classes from './Archive.module.css';

const WON: Record<Winner, { name: string; sigil: string; hue: string }> = {
  villagers: { name: 'Villagers', sigil: 'villager', hue: 'var(--town)' },
  wolves: { name: 'Wolves', sigil: 'wolf', hue: 'var(--wolf)' },
  serial_killer: { name: 'Serial killer', sigil: 'serial_killer', hue: 'var(--sk)' },
};

function atTheTable(r: ReplaySummary): string {
  const humans = r.n_humans;
  if (humans === 0) return 'AI agents only';
  const seats = Object.values(r.cast_role_counts).reduce((a, b) => a + b, 0) || 9;
  return `${humans === 1 ? '1 human' : `${humans} humans`}, ${seats - humans} agents`;
}

export function ArchiveTable({
  rows,
  modelName,
  mine,
}: {
  rows: ReplaySummary[];
  modelName: (id: string) => string;
  mine: ReadonlySet<string>;
}) {
  return (
    <Table.ScrollContainer
      minWidth={860}
      className={classes.tablewrap}
      // in scroll-area mode Mantine leaves the root's overflow-x unset, which beside its
      // overflow-y: hidden resolves to auto: a native bar under the custom one
      styles={{ scrollContainer: { overflowX: 'hidden' } }}
    >
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Won by</Table.Th>
            <Table.Th>Ended</Table.Th>
            <Table.Th>Game</Table.Th>
            <Table.Th>Finished</Table.Th>
            <Table.Th>Model</Table.Th>
            <Table.Th>At the table</Table.Th>
            <Table.Th>Memory</Table.Th>
            <Table.Th>
              <span className={classes.sr}>Watch</span>
            </Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((r) => {
            const won = WON[r.winner];
            const ended = endedLabel(r.ended_phase, r.days);
            return (
              <Table.Tr key={r.game_id}>
                <Table.Td>
                  <span className={classes.won}>
                    <Sigil role={won.sigil} strokeWidth={3.2} style={{ color: won.hue }} />
                    {won.name}
                  </span>
                </Table.Td>
                <Table.Td className={ended ? undefined : classes.muted}>
                  {ended ?? 'Unrecorded'}
                </Table.Td>
                <Table.Td>
                  <span className={classes.gameId} title={r.game_id}>
                    {r.game_id.slice(0, 8)}
                  </span>
                  {mine.has(r.game_id) ? <span className={classes.here}>you</span> : null}
                </Table.Td>
                <Table.Td>{formatDate(r.finished_at)}</Table.Td>
                <Table.Td className={r.model ? undefined : classes.muted}>
                  {r.model ? modelName(r.model) : 'Unrecorded'}
                </Table.Td>
                <Table.Td>{atTheTable(r)}</Table.Td>
                <Table.Td>
                  {r.memory ? <span className={classes.memOn}>On</span> : 'Off'}
                </Table.Td>
                <Table.Td>
                  <Button component={Link} href={`/replays/${r.game_id}`} size="sm">
                    Watch
                  </Button>
                </Table.Td>
              </Table.Tr>
            );
          })}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}
