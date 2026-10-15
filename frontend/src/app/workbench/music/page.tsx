/**
 * The music bench (`/workbench/music`): every candidate in `public/game_music`, one folder per
 * cue, to audition side by side, hear each loop's seam, and play the lynch, the morning and the
 * ending against their beats. The folder is read on each request, so a new candidate shows on a
 * reload; a build without the folder shows the bench empty.
 */
import { readdir } from 'node:fs/promises';
import path from 'node:path';
import { MusicBench, type Cue } from './_components/MusicBench';

export const dynamic = 'force-dynamic';

const ROOT = path.join(process.cwd(), 'public', 'game_music');

/** The cues in the order the game reaches them; a folder matches the first key its name holds. */
const ORDER: [key: string, name: string][] = [
  ['lobby', 'Lobby'],
  ['discussion', 'Discussion'],
  ['vote', 'Vote'],
  ['lynch', 'Lynch'],
  ['night', 'Night'],
  ['morning', 'Morning'],
  ['victory', 'Victory'],
];

async function cues(): Promise<Cue[]> {
  let dirs: string[];
  try {
    dirs = (await readdir(ROOT, { withFileTypes: true }))
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch {
    return [];
  }
  const found = await Promise.all(
    dirs.map(async (dir) => {
      const files = (await readdir(path.join(ROOT, dir)))
        .filter((f) => /\.(mp3|m4a|ogg|wav)$/i.test(f))
        .sort();
      const rank = ORDER.findIndex(([key]) => dir.toLowerCase().includes(key));
      return {
        id: ORDER[rank]?.[0] ?? dir.trim(),
        name: ORDER[rank]?.[1] ?? dir.trim(),
        rank: rank === -1 ? ORDER.length : rank,
        files: files.map((f) => ({
          name: f.replace(/\.[^.]+$/, ''),
          url: `/game_music/${encodeURIComponent(dir)}/${encodeURIComponent(f)}`,
        })),
      };
    }),
  );
  return found
    .filter((c) => c.files.length > 0)
    .sort((a, b) => a.rank - b.rank)
    .map(({ id, name, files }) => ({ id, name, files }));
}

export default async function MusicBenchPage() {
  return <MusicBench cues={await cues()} />;
}
