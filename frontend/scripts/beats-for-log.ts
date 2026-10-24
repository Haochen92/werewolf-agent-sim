/**
 * Cut a served game's event log into the beats its seated human's live stage would play, with the
 * stage's own cutter (`beatsFor`: xray off, `me` the human, live on), and write each beat's id, scene,
 * day, the log prefix it needs (`end`) and its hold. Used by `evaluation/experiments/stage_fit.py`
 * to ask whether the stage would have waited for the model.
 *
 *   ./node_modules/.bin/vite-node --config vitest.config.ts scripts/beats-for-log.ts -- <game.json> <beats.json> [player_n]
 *
 * `game.json` holds `{ "events": [...] }`, the game's durable events in seq order.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { beatsFor } from '@/stage/beats/beatsFor';

const [input, output, me] = process.argv.slice(2);
const game = JSON.parse(readFileSync(input, 'utf8'));
const beats = beatsFor(game.events, { xray: false, me: me || null, live: true });
const rows = beats.map((beat) => ({
  id: beat.id,
  scene: beat.scene,
  day: beat.day,
  seq: beat.seq,
  end: beat.end,
  holdMs: beat.holdMs,
  subject: beat.subject ?? null,
  liveOnly: !!beat.liveOnly,
}));
writeFileSync(output, JSON.stringify(rows));
console.log(`${rows.length} beats`);
