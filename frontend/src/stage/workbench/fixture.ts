/**
 * The game every workbench view is drawn from: the bundled replay of 9369a5c1 (memory on),
 * the same file the beat goldens are cut from, so a beat number in the workbench and a line in
 * the golden are the same beat.
 *
 * And a second game, for the case file's Record (`game=140610ad`): a DeepSeek game with long
 * day summaries (2026-10-03), with the claim ledger the server answered for it
 * (`GET /games/{id}/ledger`), so the Record is drawn from real claims and checks without a server.
 */
import type { DurableGameEvent, LedgerDay } from '@/types/contracts';
import fixture from '../fixtures/replay-9369a5c1.json';
import ledgerGame from '../fixtures/replay-140610ad.json';
import ledger from '../fixtures/ledger-140610ad.json';
import { castForGame, resolveCast } from '../cast/castForGame';

export const FIXTURE_GAME_ID: string = fixture.game_id;
export const FIXTURE_EVENTS = fixture.events as unknown as readonly DurableGameEvent[];
/** The benches pass the full uuid: the 8-character prefix would give a different cast. */
export const FIXTURE_CAST = castForGame(fixture.game_id);

/** The second game (`game=140610ad`), its recorded cast, and its ledger. */
export const LEDGER_GAME = {
  id: ledgerGame.game_id,
  events: ledgerGame.events as unknown as readonly DurableGameEvent[],
  cast: resolveCast(ledgerGame.cast, ledgerGame.game_id),
  ledger: ledger as unknown as readonly LedgerDay[],
};
