/**
 * The workbench's table of scenes: which component draws each one (kept with the scenes, in
 * `scenes/index.ts`, so the live and replay theatres never depend on the workbench), the beats
 * each has, and the live-only situations the fixture cannot give. A scene the workbench cannot
 * draw yet is `null` there: the workbench says so instead of failing.
 */
import type { SceneBeat, SceneId } from '../beats/types';
import { SCENES } from '../scenes';
import type { Situation } from './synthetic';

export { SCENES };

/** Every scene, in the order a game plays them. */
export const SCENE_IDS = Object.keys(SCENES) as SceneId[];

export function isSceneId(s: string): s is SceneId {
  return Object.prototype.hasOwnProperty.call(SCENES, s);
}

/** The beats of one scene, in play order. */
export function sceneBeats(beats: readonly SceneBeat[], scene: SceneId): SceneBeat[] {
  return beats.filter((b) => b.scene === scene);
}

/**
 * Scenes whose beats exist only in a live game (a prompt to a seated human), so the fixture
 * never yields them: the workbench draws each from a situation instead (see synthetic.ts),
 * and its stepper steps through these in place of the fixture's beats (or, for the scenes in
 * `SYNTHETIC_AFTER`, after them).
 */
export const SYNTHETIC: Partial<Record<SceneId, readonly Situation[]>> = {
  vote: [
    { label: 'your ballot, day 3', me: 'player_7', day: 3, actionKind: 'vote' },
    {
      label: 'your ballot, day 3, seat 6 chosen',
      me: 'player_7',
      day: 3,
      actionKind: 'vote',
      chosen: 'player_6',
    },
    {
      label: 'your ballot, day 3, abstain chosen',
      me: 'player_7',
      day: 3,
      actionKind: 'vote',
      chosen: 'abstain',
    },
  ],
  room: [
    { label: 'healer, night 2', me: 'player_9', day: 2, actionKind: 'healer_target' },
    {
      label: 'healer, night 2, seat 1 chosen',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
    },
    {
      label: 'healer, night 2, the card open',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      card: true,
    },
    {
      label: 'investigator, night 1',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
    },
    { label: 'vigilante, night 4', me: 'player_7', day: 4, actionKind: 'vigilante_target' },
    {
      label: 'serial killer, night 3',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
    },
    {
      label: 'healer, night 3, no deadline (solo game)',
      me: 'player_9',
      day: 3,
      actionKind: 'healer_target',
      left: null,
    },
  ],
  pack: [
    { label: 'wolf, round 1 to open', me: 'player_3', day: 1, actionKind: 'wolf_discuss' },
    {
      label: 'wolf, the packmate’s line arrives',
      me: 'player_3',
      day: 1,
      actionKind: null,
      at: 46,
      beat: 'pack.line',
    },
    {
      label: 'wolf, round 2 to answer',
      me: 'player_3',
      day: 1,
      actionKind: 'wolf_discuss',
      at: 46,
    },
    {
      label: 'wolf, the vote, packmate voted',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
    },
    {
      label: 'wolf, the vote, seat 4 chosen',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
    },
    {
      label: 'wolf, the kill decided',
      me: 'player_8',
      day: 2,
      actionKind: null,
      at: 154,
      beat: 'pack.decided',
    },
    { label: 'lone wolf, night 3', me: 'player_8', day: 3, actionKind: 'wolf_vote' },
    {
      label: 'lone wolf, the kill decided',
      me: 'player_8',
      day: 3,
      actionKind: null,
      at: 264,
      beat: 'pack.decided',
    },
  ],
};

/**
 * Scenes that are mostly the fixture's own beats with a live-only prompt among them (the vote
 * and its ballot): the stepper runs through the fixture's beats first, then the situations.
 */
export const SYNTHETIC_AFTER: ReadonlySet<SceneId> = new Set<SceneId>(['vote']);
