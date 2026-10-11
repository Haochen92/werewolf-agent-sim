/**
 * The workbench's table of scenes: which component draws each one (kept with the scenes, in
 * `scenes/index.ts`, so the live and replay theatres never depend on the workbench), the beats
 * each has, and the live-only situations the fixture cannot give. A scene the workbench cannot
 * draw yet is `null` there: the workbench says so instead of failing.
 */
import type { SceneBeat, SceneId } from '../beats/types';
import { SCENES } from '../scenes';
import type { RoomSituation, Situation } from './synthetic';

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

/** The situations a scene's stepper can hold: the platform's are rooms, every other a moment of the fixture. */
type Situations = {
  [K in SceneId]?: K extends 'station' ? readonly RoomSituation[] : readonly Situation[];
};

/** The platform's people: the host boards first, the rest in the order they joined. */
const ABOARD = ['mira', 'kei', 'sol', 'ada', 'bo', 'ines', 'tomas', 'yuki', 'noor'];

/**
 * Scenes whose beats exist only in a live game (a prompt to a seated human, or the waiting
 * room before the game), so the fixture never yields them: the workbench draws each from a
 * situation instead (see synthetic.ts), and its stepper steps through these in place of the
 * fixture's beats (or, for the scenes in `SYNTHETIC_AFTER`, after them).
 */
export const SYNTHETIC: Situations = {
  station: [
    {
      label: 'the host, 3 aboard',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: ABOARD.slice(0, 3),
        places: 9,
        host: 'mira',
        locked: false,
        isHost: true,
        seated: true,
        you: 0,
      },
    },
    {
      label: 'a guest, 5 aboard, locked',
      beat: 'station.locked',
      room: {
        name: 'Night shift',
        aboard: ABOARD.slice(0, 5),
        places: 9,
        host: 'mira',
        locked: true,
        isHost: false,
        seated: true,
        you: 2,
      },
    },
    {
      label: 'watching, all 9 aboard',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: ABOARD,
        places: 9,
        host: 'mira',
        locked: false,
        isHost: false,
        seated: false,
        you: null,
      },
    },
    {
      label: 'departing, 3 aboard',
      beat: 'station.departing',
      room: {
        name: 'Night shift',
        aboard: ABOARD.slice(0, 3),
        places: 9,
        host: 'mira',
        locked: false,
        isHost: true,
        seated: true,
        you: 0,
      },
    },
    {
      label: 'the host, nobody aboard yet',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: [],
        places: 9,
        host: null,
        locked: false,
        isHost: true,
        seated: false,
        you: null,
      },
    },
    {
      label: 'a guest, 4 aboard',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: ABOARD.slice(0, 4),
        places: 9,
        host: 'mira',
        locked: false,
        isHost: false,
        seated: true,
        you: 3,
      },
    },
    // the ten-seat room (ten-seat pass §1: the platform's size comes from the lobby)
    {
      label: 'ten places: a guest, 4 aboard',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: ABOARD.slice(0, 4),
        places: 10,
        host: 'mira',
        locked: false,
        isHost: false,
        seated: true,
        you: 3,
      },
    },
    {
      label: 'ten places: watching, all 10 aboard',
      beat: 'station.waiting',
      room: {
        name: 'Night shift',
        aboard: [...ABOARD, 'pim'],
        places: 10,
        host: 'mira',
        locked: false,
        isHost: false,
        seated: false,
        you: null,
      },
    },
  ],
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
    {
      label: 'healer, night 2, seat 1 chosen, 7 seconds left',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      left: 7,
    },
    // the plate as the commit: chosen and not sent, sent (sealed), and a send that failed
    {
      label: 'healer, night 2, seat 1 protected (sent)',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sent: true,
      acted: 1,
    },
    {
      label: 'healer, night 2, seat 1 chosen, the send failed',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sendError: 'Could not reach the table. Try again.',
    },
    {
      label: 'vigilante, night 4, seat 9 chosen',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      chosen: 'player_9',
    },
    {
      label: 'vigilante, night 4, seat 9 shot (sent)',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      chosen: 'player_9',
      sent: true,
      acted: 1,
    },
    {
      label: 'vigilante, night 4, held fire (sent)',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      sent: true,
      acted: 1,
    },
    {
      label: 'investigator, night 1, seat 2 checked (sent)',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
      chosen: 'player_2',
      sent: true,
      acted: 1,
    },
    {
      label: 'serial killer, night 3, seat 7 marked (sent)',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
      chosen: 'player_7',
      sent: true,
      acted: 1,
    },
    {
      label: 'healer, night 2, seat 1 protected (sent), three acted',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sent: true,
      acted: 3,
    }, // chosen, for the rooms the list above only shows at rest and sealed
    {
      label: 'investigator, night 1, seat 2 chosen',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
      chosen: 'player_2',
    },
    {
      label: 'serial killer, night 3, seat 7 chosen',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
      chosen: 'player_7',
    },
    // the ten-seat kinds (ten-seat pass §2), each drawn from a ten-seat game
    {
      label: 'ten seats: sentinel, night 1',
      game: 'phase3',
      me: 'player_9',
      day: 1,
      actionKind: 'sentinel_target',
    },
    {
      label: 'ten seats: trailseer, night 1, seat 5 chosen',
      game: 'phase3',
      me: 'player_3',
      day: 1,
      actionKind: 'trailseer_target',
      chosen: 'player_5',
    },
    {
      label: 'ten seats: sigilist, night 1, seat 5 chosen',
      game: 'phase3',
      me: 'player_4',
      day: 1,
      actionKind: 'sigil_target',
      chosen: 'player_5',
    },
    {
      label: 'ten seats: investigator, night 1, checks kept (sent)',
      game: 'phase3',
      me: 'player_7',
      day: 1,
      actionKind: 'investigator_target',
      sent: true,
      acted: 2,
    },
    {
      label: 'ten seats: vigilante, night 2, seat 10 chosen',
      game: 'phase3',
      me: 'player_1',
      day: 2,
      actionKind: 'vigilante_target',
      chosen: 'player_10',
    },
    {
      label: 'ten seats: chanteuse’s block, night 1, seat 1 chosen',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'block_target',
      chosen: 'player_1',
    },
    {
      label: 'ten seats: illusionist’s conceal, night 2',
      game: 'phase3',
      me: 'player_6',
      day: 2,
      actionKind: 'conceal',
    },
    {
      label: 'ten seats: illusionist, the victim hidden (sent)',
      game: 'phase3',
      me: 'player_6',
      day: 2,
      actionKind: 'conceal',
      chosen: 'conceal',
      sent: true,
      acted: 3,
    },
    {
      label: 'ten seats: fortune teller, night 1, seat 10 as serial killer',
      game: 'phase3',
      me: 'player_8',
      day: 1,
      actionKind: 'bet_target',
      chosen: 'player_10',
      roleNamed: 'serial_killer',
    },
    {
      label: 'ten seats: fortune teller, night 1, a self-bet chosen',
      game: 'phase3',
      me: 'player_8',
      day: 1,
      actionKind: 'bet_target',
      chosen: 'player_8',
    },
    {
      label: 'ten seats: fortune teller, seat 10 as serial killer (sent)',
      game: 'phase3',
      me: 'player_8',
      day: 1,
      actionKind: 'bet_target',
      chosen: 'player_10',
      roleNamed: 'serial_killer',
      sent: true,
      acted: 4,
    },
    {
      label: 'ten seats: speculator, night 1, the wolves chosen',
      game: 'phase3-necro',
      me: 'player_7',
      day: 1,
      actionKind: 'speculator_pick',
      chosen: 'wolves',
    },
    {
      label: 'ten seats: speculator, the town picked (sent)',
      game: 'phase3-necro',
      me: 'player_7',
      day: 1,
      actionKind: 'speculator_pick',
      chosen: 'town',
      sent: true,
      acted: 2,
    },
    {
      label: 'ten seats: necromancer, night 2',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
    },
    {
      label: 'ten seats: necromancer, through seat 4 on seat 1',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
      chosen: 'player_1',
      body: 'player_4',
    },
    {
      label: 'ten seats: necromancer, through seat 4 on seat 1 (sent)',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
      chosen: 'player_1',
      body: 'player_4',
      sent: true,
      acted: 3,
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
      acted: 1,
    },
    { label: 'lone wolf, night 3', me: 'player_8', day: 3, actionKind: 'wolf_vote' },
    {
      label: 'lone wolf, the kill decided',
      me: 'player_8',
      day: 3,
      actionKind: null,
      at: 264,
      beat: 'pack.decided',
      acted: 1,
    },
    {
      label: 'wolf, the vote, seat 4 voted (sent)',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
      sent: true,
      acted: 1,
    },
    {
      label: 'wolf, the vote, seat 4 chosen, the send failed',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
      sendError: 'Could not reach the table. Try again.',
    },
    // the ten-seat pack: up to three rounds (a wolf may pass), the carrier names the kill
    {
      label: 'ten seats: chat, round 1 to open',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'wolf_discuss',
    },
    {
      label: 'ten seats: chat, the packmate passed, round 3',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'wolf_discuss',
      at: 83,
    },
    {
      label: 'ten seats: the carrier names the kill, seat 7 chosen',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'carrier_kill',
      at: 88,
      chosen: 'player_7',
    },
    {
      label: 'ten seats: the kill named (sent)',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'carrier_kill',
      at: 88,
      chosen: 'player_7',
      sent: true,
      acted: 2,
    },
    {
      label: 'ten seats: the kill decided, seen by the packmate',
      game: 'phase3',
      me: 'player_6',
      day: 1,
      actionKind: null,
      at: 90,
      beat: 'pack.decided',
      acted: 2,
    },
  ],
};

/**
 * Scenes that are mostly the fixture's own beats with a live-only prompt among them (the vote
 * and its ballot): the stepper runs through the fixture's beats first, then the situations.
 */
export const SYNTHETIC_AFTER: ReadonlySet<SceneId> = new Set<SceneId>(['vote']);
