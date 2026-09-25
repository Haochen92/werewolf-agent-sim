/**
 * Which component draws each scene. The replay, the live game and the workbench all look a
 * scene up here, so a scene is written once and mounted everywhere. `null` is a scene the beat
 * sheet names but nobody has built yet (every scene is built today; the type keeps the door).
 */
import type { ComponentType } from 'react';
import type { SceneId } from '../beats/types';
import { DayScene } from './DayScene';
import { DealScene } from './DealScene';
import { GameOverScene } from './GameOverScene';
import { LynchScene } from './LynchScene';
import { MorningScene } from './MorningScene';
import { NightLobbyScene } from './NightLobbyScene';
import { PackScene } from './PackScene';
import { ReplayNightScene } from './ReplayNightScene';
import { ShelfRoomScene } from './ShelfRoomScene';
import { VoteScene } from './VoteScene';
import type { SceneProps } from './types';

export const SCENES: Record<SceneId, ComponentType<SceneProps> | null> = {
  deal: DealScene,
  day: DayScene,
  vote: VoteScene,
  lynch: LynchScene,
  night: NightLobbyScene,
  room: ShelfRoomScene,
  pack: PackScene,
  morning: MorningScene,
  rnight: ReplayNightScene,
  over: GameOverScene,
};
