/**
 * The game every workbench view is drawn from: the bundled replay of 9369a5c1 (memory on),
 * the same file the beat goldens are cut from, so a beat number in the workbench and a line in
 * the golden are the same beat.
 */
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '../fixtures/replay-9369a5c1.json';
import { castForGame } from '../cast/castForGame';

export const FIXTURE_GAME_ID: string = fixture.game_id;
export const FIXTURE_EVENTS = fixture.events as unknown as readonly DurableGameEvent[];
/** The benches pass the full uuid: the 8-character prefix would give a different cast. */
export const FIXTURE_CAST = castForGame(fixture.game_id);
