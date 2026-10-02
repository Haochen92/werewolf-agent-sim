/**
 * Which component draws each scene. The replay, the live game and the workbench all look a
 * scene up here, so a scene is written once and mounted everywhere. `null` is a scene the beat
 * sheet names but nobody has built yet (every scene is built today; the type keeps the door).
 */
import type { ComponentType } from 'react';
import type { SceneId } from '../beats/types';
import { carScene } from './CarScene';
import { DayBody } from './DayScene';
import { DealBody } from './DealScene';
import { OverBody } from './GameOverScene';
import { LynchBody } from './LynchScene';
import { MorningBody } from './MorningScene';
import { LobbyBody } from './NightLobbyScene';
import { PackScene } from './PackScene';
import { ReplayNightBody } from './ReplayNightScene';
import { ShelfRoomScene } from './ShelfRoomScene';
import { StationScene } from './StationScene';
import { VoteBody } from './VoteScene';
import type { SceneProps } from './types';

/**
 * Every scene played in the dining car is a body of one host, so the car's set stays up from
 * scene to scene (CarScene.tsx). The platform and the live night rooms are places of their own.
 */
export const CarScene = carScene({
  deal: DealBody,
  day: DayBody,
  vote: VoteBody,
  lynch: LynchBody,
  night: LobbyBody,
  morning: MorningBody,
  rnight: ReplayNightBody,
  over: OverBody,
});

export const SCENES: Record<SceneId, ComponentType<SceneProps> | null> = {
  station: StationScene,
  deal: CarScene,
  day: CarScene,
  vote: CarScene,
  lynch: CarScene,
  night: CarScene,
  room: ShelfRoomScene,
  pack: PackScene,
  morning: CarScene,
  rnight: CarScene,
  over: CarScene,
};
