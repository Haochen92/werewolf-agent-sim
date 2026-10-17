/**
 * The ONE import site for art (build_plan §3). Components never hold path strings — they
 * ask this module for a typed handle, so swapping the asset set is files + this file, with
 * zero component edits.
 *
 * Static imports (not `public/`) buy content-hashed URLs — regenerated art can never get
 * stuck behind a cached copy — plus inferred dimensions, so no layout shift.
 */
import type { StaticImageData } from 'next/image';
import owlBase from './sprites/characters/owl/base.webp';
import owlTalking from './sprites/characters/owl/talking.webp';
import owlThinking from './sprites/characters/owl/thinking.webp';
import owlOut from './sprites/characters/owl/out.webp';
import owlHead from './sprites/characters/owl/head.webp';
import hareBase from './sprites/characters/hare/base.webp';
import hareTalking from './sprites/characters/hare/talking.webp';
import hareThinking from './sprites/characters/hare/thinking.webp';
import hareOut from './sprites/characters/hare/out.webp';
import hareHead from './sprites/characters/hare/head.webp';
import catBase from './sprites/characters/cat/base.webp';
import catTalking from './sprites/characters/cat/talking.webp';
import catThinking from './sprites/characters/cat/thinking.webp';
import catOut from './sprites/characters/cat/out.webp';
import catHead from './sprites/characters/cat/head.webp';
import badgerBase from './sprites/characters/badger/base.webp';
import badgerTalking from './sprites/characters/badger/talking.webp';
import badgerThinking from './sprites/characters/badger/thinking.webp';
import badgerOut from './sprites/characters/badger/out.webp';
import badgerHead from './sprites/characters/badger/head.webp';
import cyclopsBase from './sprites/characters/cyclops/base.webp';
import cyclopsTalking from './sprites/characters/cyclops/talking.webp';
import cyclopsThinking from './sprites/characters/cyclops/thinking.webp';
import cyclopsOut from './sprites/characters/cyclops/out.webp';
import cyclopsHead from './sprites/characters/cyclops/head.webp';
import threeEyesBase from './sprites/characters/threeEyes/base.webp';
import threeEyesTalking from './sprites/characters/threeEyes/talking.webp';
import threeEyesThinking from './sprites/characters/threeEyes/thinking.webp';
import threeEyesOut from './sprites/characters/threeEyes/out.webp';
import threeEyesHead from './sprites/characters/threeEyes/head.webp';
import dragonBase from './sprites/characters/dragon/base.webp';
import dragonTalking from './sprites/characters/dragon/talking.webp';
import dragonThinking from './sprites/characters/dragon/thinking.webp';
import dragonOut from './sprites/characters/dragon/out.webp';
import dragonHead from './sprites/characters/dragon/head.webp';
import onionBase from './sprites/characters/onion/base.webp';
import onionTalking from './sprites/characters/onion/talking.webp';
import onionThinking from './sprites/characters/onion/thinking.webp';
import onionOut from './sprites/characters/onion/out.webp';
import onionHead from './sprites/characters/onion/head.webp';
import whaleBase from './sprites/characters/whale/base.webp';
import whaleTalking from './sprites/characters/whale/talking.webp';
import whaleThinking from './sprites/characters/whale/thinking.webp';
import whaleOut from './sprites/characters/whale/out.webp';
import whaleHead from './sprites/characters/whale/head.webp';
import polarBearBase from './sprites/characters/polarBear/base.webp';
import polarBearTalking from './sprites/characters/polarBear/talking.webp';
import polarBearThinking from './sprites/characters/polarBear/thinking.webp';
import polarBearOut from './sprites/characters/polarBear/out.webp';
import polarBearHead from './sprites/characters/polarBear/head.webp';
import shadeBase from './sprites/characters/shade/base.webp';
import shadeTalking from './sprites/characters/shade/talking.webp';
import shadeThinking from './sprites/characters/shade/thinking.webp';
import shadeOut from './sprites/characters/shade/out.webp';
import shadeHead from './sprites/characters/shade/head.webp';
import kitsuneBase from './sprites/characters/kitsune/base.webp';
import kitsuneTalking from './sprites/characters/kitsune/talking.webp';
import kitsuneThinking from './sprites/characters/kitsune/thinking.webp';
import kitsuneOut from './sprites/characters/kitsune/out.webp';
import kitsuneHead from './sprites/characters/kitsune/head.webp';
import mushroomBase from './sprites/characters/mushroom/base.webp';
import mushroomTalking from './sprites/characters/mushroom/talking.webp';
import mushroomThinking from './sprites/characters/mushroom/thinking.webp';
import mushroomOut from './sprites/characters/mushroom/out.webp';
import mushroomHead from './sprites/characters/mushroom/head.webp';
import lionCubBase from './sprites/characters/lionCub/base.webp';
import lionCubTalking from './sprites/characters/lionCub/talking.webp';
import lionCubThinking from './sprites/characters/lionCub/thinking.webp';
import lionCubOut from './sprites/characters/lionCub/out.webp';
import lionCubHead from './sprites/characters/lionCub/head.webp';
import automatonBase from './sprites/characters/automaton/base.webp';
import automatonTalking from './sprites/characters/automaton/talking.webp';
import automatonThinking from './sprites/characters/automaton/thinking.webp';
import automatonOut from './sprites/characters/automaton/out.webp';
import automatonHead from './sprites/characters/automaton/head.webp';
import healerKit from './sprites/kits/healer.webp';
import investigatorKit from './sprites/kits/investigator.webp';
import vigilanteKit from './sprites/kits/vigilante.webp';
import serialKillerKit from './sprites/kits/serial_killer.webp';
import wolfKit from './sprites/kits/wolf.webp';
import villagerKit from './sprites/kits/villager.webp';
import clockKit from './sprites/kits/clock.webp';
import lampKit from './sprites/kits/lamp.webp';
import walnut from './sprites/wood/walnut.webp';
import stationSky from './sprites/station/sky.webp';
import stationFloor from './sprites/station/floor.webp';
import stationPost from './sprites/station/post.webp';
import stationLampLit from './sprites/station/lamp-lit.webp';
import stationTrain from './sprites/station/train.webp';
import stationSky1x from './sprites/station/sky@1x.webp';
import stationTrain1x from './sprites/station/train@1x.webp';
import stationBlind from './sprites/station/blind.webp';
import carriageRoof from './sprites/carriage/roof.webp';
import carriageRail from './sprites/carriage/rail.webp';
import carriageTeak from './sprites/carriage/teak.webp';
import carriageFrame from './sprites/carriage/frame.webp';
import carriageBogie from './sprites/carriage/bogie.webp';
import carriageSolebar from './sprites/carriage/solebar.webp';
import carriageBellows from './sprites/carriage/bellows.webp';
import windowDayFar from './sprites/window/day-far.webp';
import windowDayNear from './sprites/window/day-near.webp';
import windowDuskFar from './sprites/window/dusk-far.webp';
import windowDuskNear from './sprites/window/dusk-near.webp';
import windowNightFar from './sprites/window/night-far.webp';
import windowNightNear from './sprites/window/night-near.webp';
import windowDawnFar from './sprites/window/dawn-far.webp';
import windowDawnNear from './sprites/window/dawn-near.webp';
import propJarGlass from './sprites/props/jar-glass.webp';
import propJarLid from './sprites/props/jar-lid.webp';
import propPlate from './sprites/props/plate.webp';
import propShutter from './sprites/props/shutter.webp';
import propStand from './sprites/props/stand-front.webp';
import propVoteTable from './sprites/props/vote-table.webp';
import carDay from './sprites/car/day.webp';
import carNight from './sprites/car/night.webp';
import roomHealer from './sprites/rooms/healer.webp';
import roomInvestigator from './sprites/rooms/investigator.webp';
import roomVigilante from './sprites/rooms/vigilante.webp';
import roomSerialKiller from './sprites/rooms/serial_killer.webp';
import roomWolf from './sprites/rooms/wolf.webp';
import roomSentinel from './sprites/rooms/sentinel.webp';
import roomTrailseer from './sprites/rooms/trailseer.webp';
import roomSigilist from './sprites/rooms/sigilist.webp';
import roomSpeculator from './sprites/rooms/speculator.webp';
import roomNecromancer from './sprites/rooms/necromancer.webp';
import roomFortuneTeller from './sprites/rooms/fortune_teller.webp';
import roleVillager from './sprites/roles/villager.webp';
import roleWolf from './sprites/roles/wolf.webp';
import roleInvestigator from './sprites/roles/investigator.webp';
import roleVigilante from './sprites/roles/vigilante.webp';
import roleHealer from './sprites/roles/healer.webp';
import roleSerialKiller from './sprites/roles/serial_killer.webp';
import roleSentinel from './sprites/roles/sentinel.webp';
import roleTrailseer from './sprites/roles/trailseer.webp';
import roleSigilist from './sprites/roles/sigilist.webp';
import roleChanteuse from './sprites/roles/chanteuse.webp';
import roleIllusionist from './sprites/roles/illusionist.webp';
import roleNecromancer from './sprites/roles/necromancer.webp';
import roleSpeculator from './sprites/roles/speculator.webp';
import roleFortuneTeller from './sprites/roles/fortune_teller.webp';
import owlBaseShadow from './sprites/shadow/characters/owl/base.webp';
import owlTalkingShadow from './sprites/shadow/characters/owl/talking.webp';
import owlThinkingShadow from './sprites/shadow/characters/owl/thinking.webp';
import owlOutShadow from './sprites/shadow/characters/owl/out.webp';
import hareBaseShadow from './sprites/shadow/characters/hare/base.webp';
import hareTalkingShadow from './sprites/shadow/characters/hare/talking.webp';
import hareThinkingShadow from './sprites/shadow/characters/hare/thinking.webp';
import hareOutShadow from './sprites/shadow/characters/hare/out.webp';
import catBaseShadow from './sprites/shadow/characters/cat/base.webp';
import catTalkingShadow from './sprites/shadow/characters/cat/talking.webp';
import catThinkingShadow from './sprites/shadow/characters/cat/thinking.webp';
import catOutShadow from './sprites/shadow/characters/cat/out.webp';
import badgerBaseShadow from './sprites/shadow/characters/badger/base.webp';
import badgerTalkingShadow from './sprites/shadow/characters/badger/talking.webp';
import badgerThinkingShadow from './sprites/shadow/characters/badger/thinking.webp';
import badgerOutShadow from './sprites/shadow/characters/badger/out.webp';
import cyclopsBaseShadow from './sprites/shadow/characters/cyclops/base.webp';
import cyclopsTalkingShadow from './sprites/shadow/characters/cyclops/talking.webp';
import cyclopsThinkingShadow from './sprites/shadow/characters/cyclops/thinking.webp';
import cyclopsOutShadow from './sprites/shadow/characters/cyclops/out.webp';
import threeEyesBaseShadow from './sprites/shadow/characters/threeEyes/base.webp';
import threeEyesTalkingShadow from './sprites/shadow/characters/threeEyes/talking.webp';
import threeEyesThinkingShadow from './sprites/shadow/characters/threeEyes/thinking.webp';
import threeEyesOutShadow from './sprites/shadow/characters/threeEyes/out.webp';
import dragonBaseShadow from './sprites/shadow/characters/dragon/base.webp';
import dragonTalkingShadow from './sprites/shadow/characters/dragon/talking.webp';
import dragonThinkingShadow from './sprites/shadow/characters/dragon/thinking.webp';
import dragonOutShadow from './sprites/shadow/characters/dragon/out.webp';
import onionBaseShadow from './sprites/shadow/characters/onion/base.webp';
import onionTalkingShadow from './sprites/shadow/characters/onion/talking.webp';
import onionThinkingShadow from './sprites/shadow/characters/onion/thinking.webp';
import onionOutShadow from './sprites/shadow/characters/onion/out.webp';
import whaleBaseShadow from './sprites/shadow/characters/whale/base.webp';
import whaleTalkingShadow from './sprites/shadow/characters/whale/talking.webp';
import whaleThinkingShadow from './sprites/shadow/characters/whale/thinking.webp';
import whaleOutShadow from './sprites/shadow/characters/whale/out.webp';
import polarBearBaseShadow from './sprites/shadow/characters/polarBear/base.webp';
import polarBearTalkingShadow from './sprites/shadow/characters/polarBear/talking.webp';
import polarBearThinkingShadow from './sprites/shadow/characters/polarBear/thinking.webp';
import polarBearOutShadow from './sprites/shadow/characters/polarBear/out.webp';
import shadeBaseShadow from './sprites/shadow/characters/shade/base.webp';
import shadeTalkingShadow from './sprites/shadow/characters/shade/talking.webp';
import shadeThinkingShadow from './sprites/shadow/characters/shade/thinking.webp';
import shadeOutShadow from './sprites/shadow/characters/shade/out.webp';
import kitsuneBaseShadow from './sprites/shadow/characters/kitsune/base.webp';
import kitsuneTalkingShadow from './sprites/shadow/characters/kitsune/talking.webp';
import kitsuneThinkingShadow from './sprites/shadow/characters/kitsune/thinking.webp';
import kitsuneOutShadow from './sprites/shadow/characters/kitsune/out.webp';
import mushroomBaseShadow from './sprites/shadow/characters/mushroom/base.webp';
import mushroomTalkingShadow from './sprites/shadow/characters/mushroom/talking.webp';
import mushroomThinkingShadow from './sprites/shadow/characters/mushroom/thinking.webp';
import mushroomOutShadow from './sprites/shadow/characters/mushroom/out.webp';
import lionCubBaseShadow from './sprites/shadow/characters/lionCub/base.webp';
import lionCubTalkingShadow from './sprites/shadow/characters/lionCub/talking.webp';
import lionCubThinkingShadow from './sprites/shadow/characters/lionCub/thinking.webp';
import lionCubOutShadow from './sprites/shadow/characters/lionCub/out.webp';
import automatonBaseShadow from './sprites/shadow/characters/automaton/base.webp';
import automatonTalkingShadow from './sprites/shadow/characters/automaton/talking.webp';
import automatonThinkingShadow from './sprites/shadow/characters/automaton/thinking.webp';
import automatonOutShadow from './sprites/shadow/characters/automaton/out.webp';
import grain from './sprites/atmosphere/grain.webp';
import textureWalnut from './sprites/textures/walnut.webp';
import textureBoards from './sprites/textures/boards.webp';
import textureVelvet from './sprites/textures/velvet.webp';
import textureCork from './sprites/textures/cork.webp';
import textureInk from './sprites/textures/ink.webp';
import owlBaseSmall from './sprites/characters/owl/base@small.webp';
import owlTalkingSmall from './sprites/characters/owl/talking@small.webp';
import owlThinkingSmall from './sprites/characters/owl/thinking@small.webp';
import owlOutSmall from './sprites/characters/owl/out@small.webp';
import hareBaseSmall from './sprites/characters/hare/base@small.webp';
import hareTalkingSmall from './sprites/characters/hare/talking@small.webp';
import hareThinkingSmall from './sprites/characters/hare/thinking@small.webp';
import hareOutSmall from './sprites/characters/hare/out@small.webp';
import catBaseSmall from './sprites/characters/cat/base@small.webp';
import catTalkingSmall from './sprites/characters/cat/talking@small.webp';
import catThinkingSmall from './sprites/characters/cat/thinking@small.webp';
import catOutSmall from './sprites/characters/cat/out@small.webp';
import badgerBaseSmall from './sprites/characters/badger/base@small.webp';
import badgerTalkingSmall from './sprites/characters/badger/talking@small.webp';
import badgerThinkingSmall from './sprites/characters/badger/thinking@small.webp';
import badgerOutSmall from './sprites/characters/badger/out@small.webp';
import cyclopsBaseSmall from './sprites/characters/cyclops/base@small.webp';
import cyclopsTalkingSmall from './sprites/characters/cyclops/talking@small.webp';
import cyclopsThinkingSmall from './sprites/characters/cyclops/thinking@small.webp';
import cyclopsOutSmall from './sprites/characters/cyclops/out@small.webp';
import threeEyesBaseSmall from './sprites/characters/threeEyes/base@small.webp';
import threeEyesTalkingSmall from './sprites/characters/threeEyes/talking@small.webp';
import threeEyesThinkingSmall from './sprites/characters/threeEyes/thinking@small.webp';
import threeEyesOutSmall from './sprites/characters/threeEyes/out@small.webp';
import dragonBaseSmall from './sprites/characters/dragon/base@small.webp';
import dragonTalkingSmall from './sprites/characters/dragon/talking@small.webp';
import dragonThinkingSmall from './sprites/characters/dragon/thinking@small.webp';
import dragonOutSmall from './sprites/characters/dragon/out@small.webp';
import onionBaseSmall from './sprites/characters/onion/base@small.webp';
import onionTalkingSmall from './sprites/characters/onion/talking@small.webp';
import onionThinkingSmall from './sprites/characters/onion/thinking@small.webp';
import onionOutSmall from './sprites/characters/onion/out@small.webp';
import whaleBaseSmall from './sprites/characters/whale/base@small.webp';
import whaleTalkingSmall from './sprites/characters/whale/talking@small.webp';
import whaleThinkingSmall from './sprites/characters/whale/thinking@small.webp';
import whaleOutSmall from './sprites/characters/whale/out@small.webp';
import polarBearBaseSmall from './sprites/characters/polarBear/base@small.webp';
import polarBearTalkingSmall from './sprites/characters/polarBear/talking@small.webp';
import polarBearThinkingSmall from './sprites/characters/polarBear/thinking@small.webp';
import polarBearOutSmall from './sprites/characters/polarBear/out@small.webp';
import shadeBaseSmall from './sprites/characters/shade/base@small.webp';
import shadeTalkingSmall from './sprites/characters/shade/talking@small.webp';
import shadeThinkingSmall from './sprites/characters/shade/thinking@small.webp';
import shadeOutSmall from './sprites/characters/shade/out@small.webp';
import kitsuneBaseSmall from './sprites/characters/kitsune/base@small.webp';
import kitsuneTalkingSmall from './sprites/characters/kitsune/talking@small.webp';
import kitsuneThinkingSmall from './sprites/characters/kitsune/thinking@small.webp';
import kitsuneOutSmall from './sprites/characters/kitsune/out@small.webp';
import mushroomBaseSmall from './sprites/characters/mushroom/base@small.webp';
import mushroomTalkingSmall from './sprites/characters/mushroom/talking@small.webp';
import mushroomThinkingSmall from './sprites/characters/mushroom/thinking@small.webp';
import mushroomOutSmall from './sprites/characters/mushroom/out@small.webp';
import lionCubBaseSmall from './sprites/characters/lionCub/base@small.webp';
import lionCubTalkingSmall from './sprites/characters/lionCub/talking@small.webp';
import lionCubThinkingSmall from './sprites/characters/lionCub/thinking@small.webp';
import lionCubOutSmall from './sprites/characters/lionCub/out@small.webp';
import automatonBaseSmall from './sprites/characters/automaton/base@small.webp';
import automatonTalkingSmall from './sprites/characters/automaton/talking@small.webp';
import automatonThinkingSmall from './sprites/characters/automaton/thinking@small.webp';
import automatonOutSmall from './sprites/characters/automaton/out@small.webp';
import owlHeadSmall from './sprites/characters/owl/head@small.webp';
import hareHeadSmall from './sprites/characters/hare/head@small.webp';
import catHeadSmall from './sprites/characters/cat/head@small.webp';
import badgerHeadSmall from './sprites/characters/badger/head@small.webp';
import cyclopsHeadSmall from './sprites/characters/cyclops/head@small.webp';
import threeEyesHeadSmall from './sprites/characters/threeEyes/head@small.webp';
import dragonHeadSmall from './sprites/characters/dragon/head@small.webp';
import onionHeadSmall from './sprites/characters/onion/head@small.webp';
import whaleHeadSmall from './sprites/characters/whale/head@small.webp';
import polarBearHeadSmall from './sprites/characters/polarBear/head@small.webp';
import shadeHeadSmall from './sprites/characters/shade/head@small.webp';
import kitsuneHeadSmall from './sprites/characters/kitsune/head@small.webp';
import mushroomHeadSmall from './sprites/characters/mushroom/head@small.webp';
import lionCubHeadSmall from './sprites/characters/lionCub/head@small.webp';
import automatonHeadSmall from './sprites/characters/automaton/head@small.webp';
import propJarGlassSmall from './sprites/props/jar-glass@small.webp';
import propJarLidSmall from './sprites/props/jar-lid@small.webp';
import propPlateSmall from './sprites/props/plate@small.webp';
import propStandSmall from './sprites/props/stand-front@small.webp';
import roleVillagerTile from './sprites/roles/villager@small.webp';
import roleWolfTile from './sprites/roles/wolf@small.webp';
import roleInvestigatorTile from './sprites/roles/investigator@small.webp';
import roleVigilanteTile from './sprites/roles/vigilante@small.webp';
import roleHealerTile from './sprites/roles/healer@small.webp';
import roleSerialKillerTile from './sprites/roles/serial_killer@small.webp';
import roleSentinelTile from './sprites/roles/sentinel@small.webp';
import roleTrailseerTile from './sprites/roles/trailseer@small.webp';
import roleSigilistTile from './sprites/roles/sigilist@small.webp';
import roleChanteuseTile from './sprites/roles/chanteuse@small.webp';
import roleIllusionistTile from './sprites/roles/illusionist@small.webp';
import roleNecromancerTile from './sprites/roles/necromancer@small.webp';
import roleSpeculatorTile from './sprites/roles/speculator@small.webp';
import roleFortuneTellerTile from './sprites/roles/fortune_teller@small.webp';
import windowNightFarSmall from './sprites/window/night-far@small.webp';
import windowNightNearSmall from './sprites/window/night-near@small.webp';

export function initialsFor(seat: string): string {
  const parts = seat.split(/[_\s-]+/).filter(Boolean);
  if (parts.length === 0) return '??';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  // "player_5" → "P5", which keeps a nine-seat table distinguishable at chip size.
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * The stage's cast (stage_architecture.md §4): every character this build has sprites for.
 * The server records which of them stand in each game; games recorded before that are cast
 * from the frozen LEGACY_CHARACTERS in castForGame.ts, not from this list, so this one may
 * grow.
 */
export const CHARACTERS = [
  'owl',
  'hare',
  'cat',
  'badger',
  'cyclops',
  'threeEyes',
  'dragon',
  'onion',
  'whale',
  'polarBear',
  'shade',
  'kitsune',
  'mushroom',
  'lionCub',
  'automaton',
] as const;

export type Character = (typeof CHARACTERS)[number];

export type DayState = 'base' | 'talking' | 'thinking' | 'out';

export type KitName =
  | 'healer'
  | 'investigator'
  | 'vigilante'
  | 'serial_killer'
  | 'wolf'
  | 'villager'
  | 'clock'
  | 'lamp';

/**
 * The waiting room's pictures (the platform, the train, its lamps), extracted once from the
 * waiting-room mockup (scripts/extract-station-sprites.mjs; no masters exist in the bundle).
 */
export type StationPicture = 'sky' | 'floor' | 'post' | 'lamp' | 'train' | 'blind';

/**
 * The landing carriage's pieces, cut from the waiting room's train (scripts/cut-carriage.mjs),
 * each at the painting's own pixels and shown at half size: the roof's bay, the brass rail, a
 * seamless teak tile, the window's brass rim (a 9-slice), a bogie, the solebar and the bellows.
 */
export type CarriagePicture =
  | 'roof'
  | 'rail'
  | 'teak'
  | 'frame'
  | 'bogie'
  | 'solebar'
  | 'bellows';

/**
 * The country behind the dining car's window (FeltWindow): per hour, the far sky and hills, and
 * the near row of pines, fence and pole that scrolls past (alpha). Recipe: stage_architecture §4.
 */
export type WindowHour = 'day' | 'dusk' | 'night' | 'dawn';
export type WindowPicture = 'far' | 'near';

/**
 * The painted props (alpha): the ballot jar's glass and its lid, the stand's front (drawn as a
 * 9-slice), the vote's table with its cloth, the count's plate (already squashed to the table's
 * perspective, ry = 0.3 rx) and the window's three-leaf shutter. Recipe: stage_architecture §4.
 */
export type PropPicture =
  'jarGlass' | 'jarLid' | 'stand' | 'voteTable' | 'plate' | 'shutter';

/**
 * The dining car (opaque but for the window's glass): its walls, window frame, lamps and floor,
 * painted once by day and relit for the night, both fitted to the stage. Recipe:
 * stage_architecture §4 "The dining car".
 */
export type CarPicture = 'day' | 'night';

/**
 * The night rooms (opaque but for the window's glass): the acting seat's sleeping compartment by
 * role, and the pack's. Cropped to the stage's band, the glass cleared. Recipe: stage_architecture §4.
 */
export type RoomPicture =
  | 'healer'
  | 'investigator'
  | 'vigilante'
  | 'serial_killer'
  | 'wolf'
  | 'sentinel'
  | 'trailseer'
  | 'sigilist'
  | 'speculator'
  | 'necromancer'
  | 'fortune_teller';

/**
 * The role figures (alpha): each role's felt doll, 720×960, scaled to the full height, centred,
 * feet on the bottom edge. Drawn on the role cards through `roleFigure` (paint/role-kit.ts).
 */
export type RoleSprite =
  | 'villager'
  | 'wolf'
  | 'investigator'
  | 'vigilante'
  | 'healer'
  | 'serial_killer'
  | 'sentinel'
  | 'trailseer'
  | 'sigilist'
  | 'chanteuse'
  | 'illusionist'
  | 'necromancer'
  | 'speculator'
  | 'fortune_teller';

/*
 * The atmosphere's pictures (stage_architecture §4 "Atmosphere"): each day figure's cast
 * shadow, its silhouette baked small and soft (a 12 px margin round 128 px tall), and the film
 * grain, a 160 px tile of noise.
 */

/**
 * The room's surfaces (seamless tiles, opaque): the walls' walnut veneer, the floor's boards and
 * the replay valance's velvet, each tinted to the flat colour it fills. Recipe: stage_architecture §4.
 * Also the case file's stamp ink (`ink`, scripts/make-stamp-ink.mjs): a white tile whose alpha is
 * the ink's coverage, a mask for the stamps.
 */
export type TexturePicture = 'walnut' | 'boards' | 'velvet' | 'cork' | 'ink';

/**
 * The phone's copies (scripts/small-sprites.mjs, each beside its source) of the pictures a small
 * stage (`useSmall`) draws far under their files' size, so a phone does not decode pixels it
 * never shows. Each is its full picture scaled, same aspect. `roleTiles` is for the deal's small
 * cards only; `window` holds only the night, the one hour drawn live (a night room's glass).
 */
export interface SmallSprites {
  day: Record<Character, Record<DayState | 'head', StaticImageData>>;
  props: Record<'jarGlass' | 'jarLid' | 'plate' | 'stand', StaticImageData>;
  roleTiles: Record<RoleSprite, StaticImageData>;
  window: { night: Record<WindowPicture, StaticImageData> };
}

export const SPRITES: {
  day: Record<Character, Record<DayState | 'head', StaticImageData>>;
  kits: Record<KitName, StaticImageData>;
  wood: StaticImageData;
  station: Record<StationPicture, StaticImageData>;
  /** The train and the country at one pixel per unit; `station`'s are about 1.5 (scenes/station-pictures.ts). */
  stationAt1x: Record<'sky' | 'train', StaticImageData>;
  carriage: Record<CarriagePicture, StaticImageData>;
  window: Record<WindowHour, Record<WindowPicture, StaticImageData>>;
  props: Record<PropPicture, StaticImageData>;
  car: Record<CarPicture, StaticImageData>;
  rooms: Record<RoomPicture, StaticImageData>;
  roles: Record<RoleSprite, StaticImageData>;
  shadow: {
    day: Record<Character, Record<DayState, StaticImageData>>;
  };
  grain: StaticImageData;
  textures: Record<TexturePicture, StaticImageData>;
  small: SmallSprites;
} = {
  day: {
    owl: {
      base: owlBase,
      talking: owlTalking,
      thinking: owlThinking,
      out: owlOut,
      head: owlHead,
    },
    hare: {
      base: hareBase,
      talking: hareTalking,
      thinking: hareThinking,
      out: hareOut,
      head: hareHead,
    },
    cat: {
      base: catBase,
      talking: catTalking,
      thinking: catThinking,
      out: catOut,
      head: catHead,
    },
    badger: {
      base: badgerBase,
      talking: badgerTalking,
      thinking: badgerThinking,
      out: badgerOut,
      head: badgerHead,
    },
    cyclops: {
      base: cyclopsBase,
      talking: cyclopsTalking,
      thinking: cyclopsThinking,
      out: cyclopsOut,
      head: cyclopsHead,
    },
    threeEyes: {
      base: threeEyesBase,
      talking: threeEyesTalking,
      thinking: threeEyesThinking,
      out: threeEyesOut,
      head: threeEyesHead,
    },
    dragon: {
      base: dragonBase,
      talking: dragonTalking,
      thinking: dragonThinking,
      out: dragonOut,
      head: dragonHead,
    },
    onion: {
      base: onionBase,
      talking: onionTalking,
      thinking: onionThinking,
      out: onionOut,
      head: onionHead,
    },
    whale: {
      base: whaleBase,
      talking: whaleTalking,
      thinking: whaleThinking,
      out: whaleOut,
      head: whaleHead,
    },
    polarBear: {
      base: polarBearBase,
      talking: polarBearTalking,
      thinking: polarBearThinking,
      out: polarBearOut,
      head: polarBearHead,
    },
    shade: {
      base: shadeBase,
      talking: shadeTalking,
      thinking: shadeThinking,
      out: shadeOut,
      head: shadeHead,
    },
    kitsune: {
      base: kitsuneBase,
      talking: kitsuneTalking,
      thinking: kitsuneThinking,
      out: kitsuneOut,
      head: kitsuneHead,
    },
    mushroom: {
      base: mushroomBase,
      talking: mushroomTalking,
      thinking: mushroomThinking,
      out: mushroomOut,
      head: mushroomHead,
    },
    lionCub: {
      base: lionCubBase,
      talking: lionCubTalking,
      thinking: lionCubThinking,
      out: lionCubOut,
      head: lionCubHead,
    },
    automaton: {
      base: automatonBase,
      talking: automatonTalking,
      thinking: automatonThinking,
      out: automatonOut,
      head: automatonHead,
    },
  },
  kits: {
    healer: healerKit,
    investigator: investigatorKit,
    vigilante: vigilanteKit,
    serial_killer: serialKillerKit,
    wolf: wolfKit,
    villager: villagerKit,
    clock: clockKit,
    lamp: lampKit,
  },
  wood: walnut,
  station: {
    sky: stationSky,
    floor: stationFloor,
    post: stationPost,
    lamp: stationLampLit,
    train: stationTrain,
    blind: stationBlind,
  },
  stationAt1x: { sky: stationSky1x, train: stationTrain1x },
  carriage: {
    roof: carriageRoof,
    rail: carriageRail,
    teak: carriageTeak,
    frame: carriageFrame,
    bogie: carriageBogie,
    solebar: carriageSolebar,
    bellows: carriageBellows,
  },
  window: {
    day: { far: windowDayFar, near: windowDayNear },
    dusk: { far: windowDuskFar, near: windowDuskNear },
    night: { far: windowNightFar, near: windowNightNear },
    dawn: { far: windowDawnFar, near: windowDawnNear },
  },
  props: {
    jarGlass: propJarGlass,
    jarLid: propJarLid,
    stand: propStand,
    voteTable: propVoteTable,
    plate: propPlate,
    shutter: propShutter,
  },
  car: { day: carDay, night: carNight },
  rooms: {
    healer: roomHealer,
    investigator: roomInvestigator,
    vigilante: roomVigilante,
    serial_killer: roomSerialKiller,
    wolf: roomWolf,
    sentinel: roomSentinel,
    trailseer: roomTrailseer,
    sigilist: roomSigilist,
    speculator: roomSpeculator,
    necromancer: roomNecromancer,
    fortune_teller: roomFortuneTeller,
  },
  roles: {
    villager: roleVillager,
    wolf: roleWolf,
    investigator: roleInvestigator,
    vigilante: roleVigilante,
    healer: roleHealer,
    serial_killer: roleSerialKiller,
    sentinel: roleSentinel,
    trailseer: roleTrailseer,
    sigilist: roleSigilist,
    chanteuse: roleChanteuse,
    illusionist: roleIllusionist,
    necromancer: roleNecromancer,
    speculator: roleSpeculator,
    fortune_teller: roleFortuneTeller,
  },
  shadow: {
    day: {
      owl: {
        base: owlBaseShadow,
        talking: owlTalkingShadow,
        thinking: owlThinkingShadow,
        out: owlOutShadow,
      },
      hare: {
        base: hareBaseShadow,
        talking: hareTalkingShadow,
        thinking: hareThinkingShadow,
        out: hareOutShadow,
      },
      cat: {
        base: catBaseShadow,
        talking: catTalkingShadow,
        thinking: catThinkingShadow,
        out: catOutShadow,
      },
      badger: {
        base: badgerBaseShadow,
        talking: badgerTalkingShadow,
        thinking: badgerThinkingShadow,
        out: badgerOutShadow,
      },
      cyclops: {
        base: cyclopsBaseShadow,
        talking: cyclopsTalkingShadow,
        thinking: cyclopsThinkingShadow,
        out: cyclopsOutShadow,
      },
      threeEyes: {
        base: threeEyesBaseShadow,
        talking: threeEyesTalkingShadow,
        thinking: threeEyesThinkingShadow,
        out: threeEyesOutShadow,
      },
      dragon: {
        base: dragonBaseShadow,
        talking: dragonTalkingShadow,
        thinking: dragonThinkingShadow,
        out: dragonOutShadow,
      },
      onion: {
        base: onionBaseShadow,
        talking: onionTalkingShadow,
        thinking: onionThinkingShadow,
        out: onionOutShadow,
      },
      whale: {
        base: whaleBaseShadow,
        talking: whaleTalkingShadow,
        thinking: whaleThinkingShadow,
        out: whaleOutShadow,
      },
      polarBear: {
        base: polarBearBaseShadow,
        talking: polarBearTalkingShadow,
        thinking: polarBearThinkingShadow,
        out: polarBearOutShadow,
      },
      shade: {
        base: shadeBaseShadow,
        talking: shadeTalkingShadow,
        thinking: shadeThinkingShadow,
        out: shadeOutShadow,
      },
      kitsune: {
        base: kitsuneBaseShadow,
        talking: kitsuneTalkingShadow,
        thinking: kitsuneThinkingShadow,
        out: kitsuneOutShadow,
      },
      mushroom: {
        base: mushroomBaseShadow,
        talking: mushroomTalkingShadow,
        thinking: mushroomThinkingShadow,
        out: mushroomOutShadow,
      },
      lionCub: {
        base: lionCubBaseShadow,
        talking: lionCubTalkingShadow,
        thinking: lionCubThinkingShadow,
        out: lionCubOutShadow,
      },
      automaton: {
        base: automatonBaseShadow,
        talking: automatonTalkingShadow,
        thinking: automatonThinkingShadow,
        out: automatonOutShadow,
      },
    },
  },
  grain,
  textures: {
    walnut: textureWalnut,
    boards: textureBoards,
    velvet: textureVelvet,
    cork: textureCork,
    ink: textureInk,
  },
  small: {
    day: {
      owl: {
        base: owlBaseSmall,
        talking: owlTalkingSmall,
        thinking: owlThinkingSmall,
        out: owlOutSmall,
        head: owlHeadSmall,
      },
      hare: {
        base: hareBaseSmall,
        talking: hareTalkingSmall,
        thinking: hareThinkingSmall,
        out: hareOutSmall,
        head: hareHeadSmall,
      },
      cat: {
        base: catBaseSmall,
        talking: catTalkingSmall,
        thinking: catThinkingSmall,
        out: catOutSmall,
        head: catHeadSmall,
      },
      badger: {
        base: badgerBaseSmall,
        talking: badgerTalkingSmall,
        thinking: badgerThinkingSmall,
        out: badgerOutSmall,
        head: badgerHeadSmall,
      },
      cyclops: {
        base: cyclopsBaseSmall,
        talking: cyclopsTalkingSmall,
        thinking: cyclopsThinkingSmall,
        out: cyclopsOutSmall,
        head: cyclopsHeadSmall,
      },
      threeEyes: {
        base: threeEyesBaseSmall,
        talking: threeEyesTalkingSmall,
        thinking: threeEyesThinkingSmall,
        out: threeEyesOutSmall,
        head: threeEyesHeadSmall,
      },
      dragon: {
        base: dragonBaseSmall,
        talking: dragonTalkingSmall,
        thinking: dragonThinkingSmall,
        out: dragonOutSmall,
        head: dragonHeadSmall,
      },
      onion: {
        base: onionBaseSmall,
        talking: onionTalkingSmall,
        thinking: onionThinkingSmall,
        out: onionOutSmall,
        head: onionHeadSmall,
      },
      whale: {
        base: whaleBaseSmall,
        talking: whaleTalkingSmall,
        thinking: whaleThinkingSmall,
        out: whaleOutSmall,
        head: whaleHeadSmall,
      },
      polarBear: {
        base: polarBearBaseSmall,
        talking: polarBearTalkingSmall,
        thinking: polarBearThinkingSmall,
        out: polarBearOutSmall,
        head: polarBearHeadSmall,
      },
      shade: {
        base: shadeBaseSmall,
        talking: shadeTalkingSmall,
        thinking: shadeThinkingSmall,
        out: shadeOutSmall,
        head: shadeHeadSmall,
      },
      kitsune: {
        base: kitsuneBaseSmall,
        talking: kitsuneTalkingSmall,
        thinking: kitsuneThinkingSmall,
        out: kitsuneOutSmall,
        head: kitsuneHeadSmall,
      },
      mushroom: {
        base: mushroomBaseSmall,
        talking: mushroomTalkingSmall,
        thinking: mushroomThinkingSmall,
        out: mushroomOutSmall,
        head: mushroomHeadSmall,
      },
      lionCub: {
        base: lionCubBaseSmall,
        talking: lionCubTalkingSmall,
        thinking: lionCubThinkingSmall,
        out: lionCubOutSmall,
        head: lionCubHeadSmall,
      },
      automaton: {
        base: automatonBaseSmall,
        talking: automatonTalkingSmall,
        thinking: automatonThinkingSmall,
        out: automatonOutSmall,
        head: automatonHeadSmall,
      },
    },
    props: {
      jarGlass: propJarGlassSmall,
      jarLid: propJarLidSmall,
      plate: propPlateSmall,
      stand: propStandSmall,
    },
    roleTiles: {
      villager: roleVillagerTile,
      wolf: roleWolfTile,
      investigator: roleInvestigatorTile,
      vigilante: roleVigilanteTile,
      healer: roleHealerTile,
      serial_killer: roleSerialKillerTile,
      sentinel: roleSentinelTile,
      trailseer: roleTrailseerTile,
      sigilist: roleSigilistTile,
      chanteuse: roleChanteuseTile,
      illusionist: roleIllusionistTile,
      necromancer: roleNecromancerTile,
      speculator: roleSpeculatorTile,
      fortune_teller: roleFortuneTellerTile,
    },
    window: { night: { far: windowNightFarSmall, near: windowNightNearSmall } },
  },
};

/**
 * Where each day figure's head starts and how tall the figure is, as fractions of the image
 * height, so puppets of different builds stand at one height on the stage. Measured on the base
 * pose: `top` is the crown of the skull (under any hat; ears, antenna, curl and the thinking
 * bubble rise above it), the feet are the canvas's foot. Every pose shares its base's canvas, so
 * one measure serves all four. Re-measure if the masters are re-exported (stage_architecture §4).
 */
export const BODY: Record<Character, { top: number; body: number }> = {
  owl: { top: 0.149, body: 0.851 },
  hare: { top: 0.232, body: 0.768 },
  cat: { top: 0.222, body: 0.778 },
  badger: { top: 0.165, body: 0.835 },
  cyclops: { top: 0.162, body: 0.838 },
  threeEyes: { top: 0.179, body: 0.821 },
  dragon: { top: 0.181, body: 0.819 },
  onion: { top: 0.186, body: 0.814 },
  whale: { top: 0.139, body: 0.861 },
  polarBear: { top: 0.093, body: 0.907 },
  shade: { top: 0.186, body: 0.814 },
  kitsune: { top: 0.192, body: 0.808 },
  mushroom: { top: 0.193, body: 0.807 },
  lionCub: { top: 0.211, body: 0.789 },
  automaton: { top: 0.157, body: 0.843 },
};

/**
 * How far each figure reaches either side of its canvas's centre line (its widest pose, props and
 * arms included), as fractions of its body height: two or three at the stand are spaced so their
 * reaches just meet (standSet). Measured with BODY; re-measure with it.
 */
export const REACH: Record<Character, { left: number; right: number }> = {
  owl: { left: 0.435, right: 0.402 },
  hare: { left: 0.418, right: 0.42 },
  cat: { left: 0.443, right: 0.434 },
  badger: { left: 0.455, right: 0.417 },
  cyclops: { left: 0.419, right: 0.402 },
  threeEyes: { left: 0.399, right: 0.405 },
  dragon: { left: 0.432, right: 0.42 },
  onion: { left: 0.411, right: 0.374 },
  whale: { left: 0.434, right: 0.411 },
  polarBear: { left: 0.369, right: 0.413 },
  shade: { left: 0.429, right: 0.428 },
  kitsune: { left: 0.396, right: 0.42 },
  mushroom: { left: 0.417, right: 0.441 },
  lionCub: { left: 0.448, right: 0.451 },
  automaton: { left: 0.421, right: 0.373 },
};

/**
 * How each head portrait sits in a round window so every face reads at one size: drawn `s` times
 * the window's diameter, its centre moved by `x`, `y` diameters. `s / 2 + y` stays at least 0.5,
 * so the portrait's cut collar never shows inside the circle. Judged by eye at 44 px.
 */
export const HEAD_FRAME: Record<Character, { s: number; x: number; y: number }> = {
  owl: { s: 1.15, x: 0, y: -0.05 },
  // tighter and lower on the face; the upright ear runs off
  hare: { s: 1.55, x: -0.02, y: -0.19 },
  cat: { s: 1.3, x: 0, y: -0.08 },
  badger: { s: 1.3, x: 0, y: -0.08 },
  cyclops: { s: 1.3, x: 0, y: -0.1 },
  threeEyes: { s: 1.35, x: 0, y: -0.15 },
  dragon: { s: 1.35, x: 0, y: -0.12 },
  onion: { s: 1.45, x: 0, y: -0.22 },
  whale: { s: 1.3, x: 0, y: -0.1 },
  // drawn smaller so the ears stay in
  polarBear: { s: 1.0, x: 0, y: 0 },
  shade: { s: 1.35, x: -0.01, y: -0.16 },
  kitsune: { s: 1.3, x: 0, y: -0.1 },
  mushroom: { s: 1.45, x: 0, y: -0.2 },
  // the mane fills the circle as the owl's feathers do
  lionCub: { s: 1.15, x: 0, y: -0.05 },
  automaton: { s: 1.4, x: 0, y: -0.15 },
};
