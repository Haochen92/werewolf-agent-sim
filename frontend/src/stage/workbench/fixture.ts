/**
 * The workbench draws the ten-seat game (`PHASE3_GAME`, below) unless the URL names another.
 *
 * The fixture: the bundled replay of 9369a5c1 (nine seats, memory on, `game=9369a5c1`), the
 * workbench's default until the ten-seat pass (ruling 2026-10-11) and still the game the beat
 * goldens and most stage tests are cut from, so a beat number in the workbench on
 * `game=9369a5c1` and a line in its golden are the same beat.
 *
 * And a second game, for the case file's Record (`game=140610ad`): a DeepSeek game with long
 * day summaries (2026-10-03), with the claim ledger the server answered for it
 * (`GET /games/{id}/ledger`), so the Record is drawn from real claims and checks without a server.
 */
import type { DurableGameEvent, LedgerDay } from '@/types/contracts';
import fixture from '../fixtures/replay-9369a5c1.json';
import ledgerGame from '../fixtures/replay-140610ad.json';
import ledger from '../fixtures/ledger-140610ad.json';
import phase2Game from '../fixtures/replay-phase2.json';
import phase3Game from '../fixtures/replay-phase3.json';
import phase3NecroGame from '../fixtures/replay-phase3-necro.json';
import { castForGame, resolveCast, rosterSize } from '../cast/castForGame';

export const FIXTURE_GAME_ID: string = fixture.game_id;
export const FIXTURE_EVENTS = fixture.events as unknown as readonly DurableGameEvent[];
/** The benches pass the full uuid: the 8-character prefix would give a different cast. */
export const FIXTURE_CAST = castForGame(fixture.game_id, rosterSize(FIXTURE_EVENTS));

/** The second game (`game=140610ad`), its recorded cast, and its ledger. */
const ledgerEvents = ledgerGame.events as unknown as readonly DurableGameEvent[];

export const LEDGER_GAME = {
  id: ledgerGame.game_id,
  events: ledgerEvents,
  cast: resolveCast(ledgerGame.cast, ledgerGame.game_id, rosterSize(ledgerEvents)),
  ledger: ledger as unknown as readonly LedgerDay[],
};

/**
 * The third game (`game=phase2`): the 2026-10-07 game of the day with rounds (Phase 2 of the
 * discussion work), the translator's own golden for its captured stream turned into a replay.
 * AI-only, memory off, no ledger. The round beats (`day.opening-prepares`, `day.round-passes`,
 * `day.closing-called`) are drawn and golden-tested from it; its cast is derived from the id.
 */
const phase2Events = phase2Game.events as unknown as readonly DurableGameEvent[];

export const PHASE2_GAME = {
  id: phase2Game.game_id,
  events: phase2Events,
  cast: castForGame(phase2Game.game_id, rosterSize(phase2Events)),
};

const phase3Events = phase3Game.events as unknown as readonly DurableGameEvent[];
const phase3NecroEvents = phase3NecroGame.events as unknown as readonly DurableGameEvent[];

/**
 * The ten-seat games (Phase 3). The default (no `game=`, or `game=phase3`): the translator's golden for the captured
 * 2026-10 game (serial killer and fortune teller drawn; a sigil kill, a concealed body, the
 * fortune teller's win at game over). `game=phase3-necro`: batch game e04 of
 * evidence/game_play_enhancement/data/phase3_balance_4 through the translator (necromancer and
 * speculator drawn; the necromancer acts through a body, the speculator picks the wolves, a
 * save). Both built by `scripts/export_replay_fixture.py`; AI-only, memory off, no ledger.
 */
export const PHASE3_GAME = {
  id: phase3Game.game_id,
  events: phase3Events,
  cast: castForGame(phase3Game.game_id, rosterSize(phase3Events)),
};

export const PHASE3_NECRO_GAME = {
  id: phase3NecroGame.game_id,
  events: phase3NecroEvents,
  cast: castForGame(phase3NecroGame.game_id, rosterSize(phase3NecroEvents)),
};
