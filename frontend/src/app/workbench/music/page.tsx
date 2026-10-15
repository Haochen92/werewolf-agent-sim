/**
 * The music bench (`/workbench/music`): the score's tracks in `public/music`, by cue, to audition
 * side by side, hear each loop's seam, and play the lynch, the morning and the ending against
 * their beats. A file's cue is the start of its name (`night-…`, `win-…`); the folder is read on
 * each request, so a candidate dropped in shows on a reload.
 */
import { readdir } from 'node:fs/promises';
import path from 'node:path';
import { MusicBench, type Cue } from './_components/MusicBench';

export const dynamic = 'force-dynamic';

const ROOT = path.join(process.cwd(), 'public', 'music');

/** The cues in the order the game reaches them, with the name prefix that files them. */
const ORDER: [id: string, prefix: string, name: string][] = [
  ['lobby', 'lobby', 'Lobby'],
  ['discussion', 'day', 'Discussion'],
  ['vote', 'vote', 'Vote'],
  ['lynch', 'lynch', 'Lynch'],
  ['night', 'night', 'Night'],
  ['morning', 'dawn', 'Morning'],
  ['victory', 'win', 'Victory'],
  ['ending', 'elders', 'Guide and ending'],
];

async function cues(): Promise<Cue[]> {
  let files: string[];
  try {
    files = (await readdir(ROOT)).filter((f) => /\.(mp3|m4a|ogg|wav)$/i.test(f)).sort();
  } catch {
    return [];
  }
  return ORDER.map(([id, prefix, name]) => ({
    id,
    name,
    files: files
      .filter((f) => f.startsWith(`${prefix}-`))
      .map((f) => ({
        name: f.replace(/\.[^.]+$/, ''),
        url: `/music/${encodeURIComponent(f)}`,
      })),
  })).filter((c) => c.files.length > 0);
}

export default async function MusicBenchPage() {
  return <MusicBench cues={await cues()} />;
}
