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

/** The situations a scene's stepper can hold: the platform's are rooms, every other a moment of a bundled game. */
type Situations = {
  [K in SceneId]?: K extends 'station' ? readonly RoomSituation[] : readonly Situation[];
};

/** The platform's people: the host boards first, the rest in the order they joined. */
const ABOARD = ['mira', 'kei', 'sol', 'ada', 'bo', 'ines', 'tomas', 'yuki', 'noor'];

/**
 * Scenes whose beats exist only in a live game (a prompt to a seated human, or the waiting
 * room before the game), so the fixture never yields them: the workbench draws each from a
 * situation instead (see synthetic.ts), and its stepper steps through these in place of the
 * fixture's beats (or, for the scenes in `SYNTHETIC_AFTER`, after them). The ten-seat game is
 * the default, so the ten-seat situations come first; the nine-seat ones follow, each label
 * marked "nine seats: " and each drawn from the nine-seat fixture (9369a5c1).
 */
export const SYNTHETIC: Situations = {
  station: [
    // the ten-seat room (ten-seat pass §1: the platform's size comes from the lobby)
    {
      label: 'a guest, 4 aboard',
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
      label: 'watching, all 10 aboard',
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
    // nine places, the platform before the ten-seat pass
    {
      label: 'nine seats: the host, 3 aboard',
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
      label: 'nine seats: a guest, 5 aboard, locked',
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
      label: 'nine seats: watching, all 9 aboard',
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
      label: 'nine seats: departing, 3 aboard',
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
      label: 'nine seats: the host, nobody aboard yet',
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
      label: 'nine seats: a guest, 4 aboard',
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
  ],
  // the game the workbench draws (seat 9 and seat 6 live to day 3's vote in the ten-seat game
  // and in the nine-seat fixture), its candidates from that game's roster
  vote: [
    { label: 'your ballot, day 3', me: 'player_9', day: 3, actionKind: 'vote' },
    {
      label: 'your ballot, day 3, seat 6 chosen',
      me: 'player_9',
      day: 3,
      actionKind: 'vote',
      chosen: 'player_6',
    },
    {
      label: 'your ballot, day 3, abstain chosen',
      me: 'player_9',
      day: 3,
      actionKind: 'vote',
      chosen: 'abstain',
    },
  ],
  room: [
    // the ten-seat kinds (ten-seat pass §2), each drawn from a ten-seat game
    {
      label: 'sentinel, night 1',
      game: 'phase3',
      me: 'player_9',
      day: 1,
      actionKind: 'sentinel_target',
    },
    {
      label: 'trailseer, night 1, seat 5 chosen',
      game: 'phase3',
      me: 'player_3',
      day: 1,
      actionKind: 'trailseer_target',
      chosen: 'player_5',
    },
    {
      label: 'sigilist, night 1, seat 5 chosen',
      game: 'phase3',
      me: 'player_4',
      day: 1,
      actionKind: 'sigil_target',
      chosen: 'player_5',
    },
    {
      label: 'investigator, night 1, checks kept (sent)',
      game: 'phase3',
      me: 'player_7',
      day: 1,
      actionKind: 'investigator_target',
      sent: true,
      acted: 2,
    },
    {
      label: 'vigilante, night 2, seat 10 chosen',
      game: 'phase3',
      me: 'player_1',
      day: 2,
      actionKind: 'vigilante_target',
      chosen: 'player_10',
    },
    {
      label: 'chanteuse’s block, night 1, seat 1 chosen',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'block_target',
      chosen: 'player_1',
    },
    {
      label: 'illusionist’s conceal, night 2',
      game: 'phase3',
      me: 'player_6',
      day: 2,
      actionKind: 'conceal',
    },
    {
      label: 'illusionist, the victim hidden (sent)',
      game: 'phase3',
      me: 'player_6',
      day: 2,
      actionKind: 'conceal',
      chosen: 'conceal',
      sent: true,
      acted: 3,
    },
    {
      label: 'fortune teller, night 1, seat 10 as serial killer',
      game: 'phase3',
      me: 'player_8',
      day: 1,
      actionKind: 'bet_target',
      chosen: 'player_10',
      roleNamed: 'serial_killer',
    },
    {
      label: 'fortune teller, night 1, a self-bet chosen',
      game: 'phase3',
      me: 'player_8',
      day: 1,
      actionKind: 'bet_target',
      chosen: 'player_8',
    },
    {
      label: 'fortune teller, seat 10 as serial killer (sent)',
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
      label: 'speculator, night 1, the wolves chosen',
      game: 'phase3-necro',
      me: 'player_7',
      day: 1,
      actionKind: 'speculator_pick',
      chosen: 'wolves',
    },
    {
      label: 'speculator, the town picked (sent)',
      game: 'phase3-necro',
      me: 'player_7',
      day: 1,
      actionKind: 'speculator_pick',
      chosen: 'town',
      sent: true,
      acted: 2,
    },
    {
      label: 'necromancer, night 2',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
    },
    {
      label: 'necromancer, through seat 4 on seat 1',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
      chosen: 'player_1',
      body: 'player_4',
    },
    {
      label: 'necromancer, through seat 4 on seat 1 (sent)',
      game: 'phase3-necro',
      me: 'player_9',
      day: 2,
      actionKind: 'necromancer_target',
      chosen: 'player_1',
      body: 'player_4',
      sent: true,
      acted: 3,
    },
    // the nine-seat kinds, drawn from the nine-seat fixture (9369a5c1)
    {
      label: 'nine seats: healer, night 2',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
    },
    {
      label: 'nine seats: healer, night 2, seat 1 chosen',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
    },
    {
      label: 'nine seats: healer, night 2, the card open',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      card: true,
    },
    {
      label: 'nine seats: investigator, night 1',
      game: '9369a5c1',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
    },
    {
      label: 'nine seats: vigilante, night 4',
      game: '9369a5c1',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
    },
    {
      label: 'nine seats: serial killer, night 3',
      game: '9369a5c1',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
    },
    {
      label: 'nine seats: healer, night 3, no deadline (solo game)',
      game: '9369a5c1',
      me: 'player_9',
      day: 3,
      actionKind: 'healer_target',
      left: null,
    },
    {
      label: 'nine seats: healer, night 2, seat 1 chosen, 7 seconds left',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      left: 7,
    },
    // the plate as the commit: chosen and not sent, sent (sealed), and a send that failed
    {
      label: 'nine seats: healer, night 2, seat 1 protected (sent)',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: healer, night 2, seat 1 chosen, the send failed',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sendError: 'Could not reach the table. Try again.',
    },
    {
      label: 'nine seats: vigilante, night 4, seat 9 chosen',
      game: '9369a5c1',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      chosen: 'player_9',
    },
    {
      label: 'nine seats: vigilante, night 4, seat 9 shot (sent)',
      game: '9369a5c1',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      chosen: 'player_9',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: vigilante, night 4, held fire (sent)',
      game: '9369a5c1',
      me: 'player_7',
      day: 4,
      actionKind: 'vigilante_target',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: investigator, night 1, seat 2 checked (sent)',
      game: '9369a5c1',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
      chosen: 'player_2',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: serial killer, night 3, seat 7 marked (sent)',
      game: '9369a5c1',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
      chosen: 'player_7',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: healer, night 2, seat 1 protected (sent), three acted',
      game: '9369a5c1',
      me: 'player_9',
      day: 2,
      actionKind: 'healer_target',
      chosen: 'player_1',
      sent: true,
      acted: 3,
    }, // chosen, for the rooms the list above only shows at rest and sealed
    {
      label: 'nine seats: investigator, night 1, seat 2 chosen',
      game: '9369a5c1',
      me: 'player_4',
      day: 1,
      actionKind: 'investigator_target',
      chosen: 'player_2',
    },
    {
      label: 'nine seats: serial killer, night 3, seat 7 chosen',
      game: '9369a5c1',
      me: 'player_2',
      day: 3,
      actionKind: 'serial_killer_target',
      chosen: 'player_7',
    },
  ],
  pack: [
    // the ten-seat pack: up to three rounds (a wolf may pass), the carrier names the kill
    {
      label: 'chat, round 1 to open',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'wolf_discuss',
    },
    {
      label: 'chat, the packmate passed, round 3',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'wolf_discuss',
      at: 83,
    },
    {
      label: 'the carrier names the kill, seat 7 chosen',
      game: 'phase3',
      me: 'player_5',
      day: 1,
      actionKind: 'carrier_kill',
      at: 88,
      chosen: 'player_7',
    },
    {
      label: 'the kill named (sent)',
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
      label: 'the kill decided, seen by the packmate',
      game: 'phase3',
      me: 'player_6',
      day: 1,
      actionKind: null,
      at: 90,
      beat: 'pack.decided',
      acted: 2,
    },
    // the nine-seat pack (9369a5c1): two rounds, then every wolf votes the kill
    {
      label: 'nine seats: wolf, round 1 to open',
      game: '9369a5c1',
      me: 'player_3',
      day: 1,
      actionKind: 'wolf_discuss',
    },
    {
      label: 'nine seats: wolf, the packmate’s line arrives',
      game: '9369a5c1',
      me: 'player_3',
      day: 1,
      actionKind: null,
      at: 46,
      beat: 'pack.line',
    },
    {
      label: 'nine seats: wolf, round 2 to answer',
      game: '9369a5c1',
      me: 'player_3',
      day: 1,
      actionKind: 'wolf_discuss',
      at: 46,
    },
    {
      label: 'nine seats: wolf, the vote, packmate voted',
      game: '9369a5c1',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
    },
    {
      label: 'nine seats: wolf, the vote, seat 4 chosen',
      game: '9369a5c1',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
    },
    {
      label: 'nine seats: wolf, the kill decided',
      game: '9369a5c1',
      me: 'player_8',
      day: 2,
      actionKind: null,
      at: 154,
      beat: 'pack.decided',
      acted: 1,
    },
    {
      label: 'nine seats: lone wolf, night 3',
      game: '9369a5c1',
      me: 'player_8',
      day: 3,
      actionKind: 'wolf_vote',
    },
    {
      label: 'nine seats: lone wolf, the kill decided',
      game: '9369a5c1',
      me: 'player_8',
      day: 3,
      actionKind: null,
      at: 264,
      beat: 'pack.decided',
      acted: 1,
    },
    {
      label: 'nine seats: wolf, the vote, seat 4 voted (sent)',
      game: '9369a5c1',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
      sent: true,
      acted: 1,
    },
    {
      label: 'nine seats: wolf, the vote, seat 4 chosen, the send failed',
      game: '9369a5c1',
      me: 'player_8',
      day: 2,
      actionKind: 'wolf_vote',
      at: 152,
      chosen: 'player_4',
      sendError: 'Could not reach the table. Try again.',
    },
  ],
};

/**
 * Scenes that are mostly the fixture's own beats with a live-only prompt among them (the vote
 * and its ballot): the stepper runs through the fixture's beats first, then the situations.
 */
export const SYNTHETIC_AFTER: ReadonlySet<SceneId> = new Set<SceneId>(['vote']);
