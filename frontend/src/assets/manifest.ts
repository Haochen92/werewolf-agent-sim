/**
 * The ONE import site for art (build_plan §3). Components never hold path strings — they
 * ask this module for a typed handle, so swapping the asset set is files + this file, with
 * zero component edits.
 *
 * The v1 set is twelve compact pixel avatars, owner-ruled from Sample E on 2026-08-22.
 * `portraitFor()` still returns null when the list is empty, preserving the deterministic
 * initials fallback if an asset set is deliberately removed or replaced.
 *
 * Static imports (not `public/`) buy content-hashed URLs — regenerated art can never get
 * stuck behind a cached copy — plus inferred dimensions, so no layout shift.
 */
import type { StaticImageData } from 'next/image';
import type { AttackerType } from '@/types/contracts';
import p01 from './portraits/01.webp';
import p02 from './portraits/02.webp';
import p03 from './portraits/03.webp';
import p04 from './portraits/04.webp';
import p05 from './portraits/05.webp';
import p06 from './portraits/06.webp';
import p07 from './portraits/07.webp';
import p08 from './portraits/08.webp';
import p09 from './portraits/09.webp';
import p10 from './portraits/10.webp';
import p11 from './portraits/11.webp';
import p12 from './portraits/12.webp';
import owlBase from './sprites/day/owl/base.webp';
import owlTalking from './sprites/day/owl/talking.webp';
import owlThinking from './sprites/day/owl/thinking.webp';
import owlOut from './sprites/day/owl/out.webp';
import owlHead from './sprites/day/owl/head.webp';
import hareBase from './sprites/day/hare/base.webp';
import hareTalking from './sprites/day/hare/talking.webp';
import hareThinking from './sprites/day/hare/thinking.webp';
import hareOut from './sprites/day/hare/out.webp';
import hareHead from './sprites/day/hare/head.webp';
import catBase from './sprites/day/cat/base.webp';
import catTalking from './sprites/day/cat/talking.webp';
import catThinking from './sprites/day/cat/thinking.webp';
import catOut from './sprites/day/cat/out.webp';
import catHead from './sprites/day/cat/head.webp';
import badgerBase from './sprites/day/badger/base.webp';
import badgerTalking from './sprites/day/badger/talking.webp';
import badgerThinking from './sprites/day/badger/thinking.webp';
import badgerOut from './sprites/day/badger/out.webp';
import badgerHead from './sprites/day/badger/head.webp';
import cyclopsBase from './sprites/day/cyclops/base.webp';
import cyclopsTalking from './sprites/day/cyclops/talking.webp';
import cyclopsThinking from './sprites/day/cyclops/thinking.webp';
import cyclopsOut from './sprites/day/cyclops/out.webp';
import cyclopsHead from './sprites/day/cyclops/head.webp';
import threeEyesBase from './sprites/day/threeEyes/base.webp';
import threeEyesTalking from './sprites/day/threeEyes/talking.webp';
import threeEyesThinking from './sprites/day/threeEyes/thinking.webp';
import threeEyesOut from './sprites/day/threeEyes/out.webp';
import threeEyesHead from './sprites/day/threeEyes/head.webp';
import dragonBase from './sprites/day/dragon/base.webp';
import dragonTalking from './sprites/day/dragon/talking.webp';
import dragonThinking from './sprites/day/dragon/thinking.webp';
import dragonOut from './sprites/day/dragon/out.webp';
import dragonHead from './sprites/day/dragon/head.webp';
import onionBase from './sprites/day/onion/base.webp';
import onionTalking from './sprites/day/onion/talking.webp';
import onionThinking from './sprites/day/onion/thinking.webp';
import onionOut from './sprites/day/onion/out.webp';
import onionHead from './sprites/day/onion/head.webp';
import whaleBase from './sprites/day/whale/base.webp';
import whaleTalking from './sprites/day/whale/talking.webp';
import whaleThinking from './sprites/day/whale/thinking.webp';
import whaleOut from './sprites/day/whale/out.webp';
import whaleHead from './sprites/day/whale/head.webp';
import polarBearBase from './sprites/day/polarBear/base.webp';
import polarBearTalking from './sprites/day/polarBear/talking.webp';
import polarBearThinking from './sprites/day/polarBear/thinking.webp';
import polarBearOut from './sprites/day/polarBear/out.webp';
import polarBearHead from './sprites/day/polarBear/head.webp';
import shadeBase from './sprites/day/shade/base.webp';
import shadeTalking from './sprites/day/shade/talking.webp';
import shadeThinking from './sprites/day/shade/thinking.webp';
import shadeOut from './sprites/day/shade/out.webp';
import shadeHead from './sprites/day/shade/head.webp';
import kitsuneBase from './sprites/day/kitsune/base.webp';
import kitsuneTalking from './sprites/day/kitsune/talking.webp';
import kitsuneThinking from './sprites/day/kitsune/thinking.webp';
import kitsuneOut from './sprites/day/kitsune/out.webp';
import kitsuneHead from './sprites/day/kitsune/head.webp';
import mushroomBase from './sprites/day/mushroom/base.webp';
import mushroomTalking from './sprites/day/mushroom/talking.webp';
import mushroomThinking from './sprites/day/mushroom/thinking.webp';
import mushroomOut from './sprites/day/mushroom/out.webp';
import mushroomHead from './sprites/day/mushroom/head.webp';
import lionCubBase from './sprites/day/lionCub/base.webp';
import lionCubTalking from './sprites/day/lionCub/talking.webp';
import lionCubThinking from './sprites/day/lionCub/thinking.webp';
import lionCubOut from './sprites/day/lionCub/out.webp';
import lionCubHead from './sprites/day/lionCub/head.webp';
import automatonBase from './sprites/day/automaton/base.webp';
import automatonTalking from './sprites/day/automaton/talking.webp';
import automatonThinking from './sprites/day/automaton/thinking.webp';
import automatonOut from './sprites/day/automaton/out.webp';
import automatonHead from './sprites/day/automaton/head.webp';
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
import stationLamp from './sprites/station/lamp.webp';
import stationTrain from './sprites/station/train.webp';
import stationBlind from './sprites/station/blind.webp';
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
import propValance from './sprites/props/valance.webp';
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
import owlBaseShadow from './sprites/shadow/day/owl/base.webp';
import owlTalkingShadow from './sprites/shadow/day/owl/talking.webp';
import owlThinkingShadow from './sprites/shadow/day/owl/thinking.webp';
import owlOutShadow from './sprites/shadow/day/owl/out.webp';
import hareBaseShadow from './sprites/shadow/day/hare/base.webp';
import hareTalkingShadow from './sprites/shadow/day/hare/talking.webp';
import hareThinkingShadow from './sprites/shadow/day/hare/thinking.webp';
import hareOutShadow from './sprites/shadow/day/hare/out.webp';
import catBaseShadow from './sprites/shadow/day/cat/base.webp';
import catTalkingShadow from './sprites/shadow/day/cat/talking.webp';
import catThinkingShadow from './sprites/shadow/day/cat/thinking.webp';
import catOutShadow from './sprites/shadow/day/cat/out.webp';
import badgerBaseShadow from './sprites/shadow/day/badger/base.webp';
import badgerTalkingShadow from './sprites/shadow/day/badger/talking.webp';
import badgerThinkingShadow from './sprites/shadow/day/badger/thinking.webp';
import badgerOutShadow from './sprites/shadow/day/badger/out.webp';
import cyclopsBaseShadow from './sprites/shadow/day/cyclops/base.webp';
import cyclopsTalkingShadow from './sprites/shadow/day/cyclops/talking.webp';
import cyclopsThinkingShadow from './sprites/shadow/day/cyclops/thinking.webp';
import cyclopsOutShadow from './sprites/shadow/day/cyclops/out.webp';
import threeEyesBaseShadow from './sprites/shadow/day/threeEyes/base.webp';
import threeEyesTalkingShadow from './sprites/shadow/day/threeEyes/talking.webp';
import threeEyesThinkingShadow from './sprites/shadow/day/threeEyes/thinking.webp';
import threeEyesOutShadow from './sprites/shadow/day/threeEyes/out.webp';
import dragonBaseShadow from './sprites/shadow/day/dragon/base.webp';
import dragonTalkingShadow from './sprites/shadow/day/dragon/talking.webp';
import dragonThinkingShadow from './sprites/shadow/day/dragon/thinking.webp';
import dragonOutShadow from './sprites/shadow/day/dragon/out.webp';
import onionBaseShadow from './sprites/shadow/day/onion/base.webp';
import onionTalkingShadow from './sprites/shadow/day/onion/talking.webp';
import onionThinkingShadow from './sprites/shadow/day/onion/thinking.webp';
import onionOutShadow from './sprites/shadow/day/onion/out.webp';
import whaleBaseShadow from './sprites/shadow/day/whale/base.webp';
import whaleTalkingShadow from './sprites/shadow/day/whale/talking.webp';
import whaleThinkingShadow from './sprites/shadow/day/whale/thinking.webp';
import whaleOutShadow from './sprites/shadow/day/whale/out.webp';
import polarBearBaseShadow from './sprites/shadow/day/polarBear/base.webp';
import polarBearTalkingShadow from './sprites/shadow/day/polarBear/talking.webp';
import polarBearThinkingShadow from './sprites/shadow/day/polarBear/thinking.webp';
import polarBearOutShadow from './sprites/shadow/day/polarBear/out.webp';
import shadeBaseShadow from './sprites/shadow/day/shade/base.webp';
import shadeTalkingShadow from './sprites/shadow/day/shade/talking.webp';
import shadeThinkingShadow from './sprites/shadow/day/shade/thinking.webp';
import shadeOutShadow from './sprites/shadow/day/shade/out.webp';
import kitsuneBaseShadow from './sprites/shadow/day/kitsune/base.webp';
import kitsuneTalkingShadow from './sprites/shadow/day/kitsune/talking.webp';
import kitsuneThinkingShadow from './sprites/shadow/day/kitsune/thinking.webp';
import kitsuneOutShadow from './sprites/shadow/day/kitsune/out.webp';
import mushroomBaseShadow from './sprites/shadow/day/mushroom/base.webp';
import mushroomTalkingShadow from './sprites/shadow/day/mushroom/talking.webp';
import mushroomThinkingShadow from './sprites/shadow/day/mushroom/thinking.webp';
import mushroomOutShadow from './sprites/shadow/day/mushroom/out.webp';
import lionCubBaseShadow from './sprites/shadow/day/lionCub/base.webp';
import lionCubTalkingShadow from './sprites/shadow/day/lionCub/talking.webp';
import lionCubThinkingShadow from './sprites/shadow/day/lionCub/thinking.webp';
import lionCubOutShadow from './sprites/shadow/day/lionCub/out.webp';
import automatonBaseShadow from './sprites/shadow/day/automaton/base.webp';
import automatonTalkingShadow from './sprites/shadow/day/automaton/talking.webp';
import automatonThinkingShadow from './sprites/shadow/day/automaton/thinking.webp';
import automatonOutShadow from './sprites/shadow/day/automaton/out.webp';
import grain from './sprites/atmosphere/grain.webp';
import textureWalnut from './sprites/textures/walnut.webp';
import textureBoards from './sprites/textures/boards.webp';
import textureVelvet from './sprites/textures/velvet.webp';
import textureCork from './sprites/textures/cork.webp';
import textureInk from './sprites/textures/ink.webp';
import owlBaseSmall from './sprites/day/owl/base@small.webp';
import owlTalkingSmall from './sprites/day/owl/talking@small.webp';
import owlThinkingSmall from './sprites/day/owl/thinking@small.webp';
import owlOutSmall from './sprites/day/owl/out@small.webp';
import hareBaseSmall from './sprites/day/hare/base@small.webp';
import hareTalkingSmall from './sprites/day/hare/talking@small.webp';
import hareThinkingSmall from './sprites/day/hare/thinking@small.webp';
import hareOutSmall from './sprites/day/hare/out@small.webp';
import catBaseSmall from './sprites/day/cat/base@small.webp';
import catTalkingSmall from './sprites/day/cat/talking@small.webp';
import catThinkingSmall from './sprites/day/cat/thinking@small.webp';
import catOutSmall from './sprites/day/cat/out@small.webp';
import badgerBaseSmall from './sprites/day/badger/base@small.webp';
import badgerTalkingSmall from './sprites/day/badger/talking@small.webp';
import badgerThinkingSmall from './sprites/day/badger/thinking@small.webp';
import badgerOutSmall from './sprites/day/badger/out@small.webp';
import cyclopsBaseSmall from './sprites/day/cyclops/base@small.webp';
import cyclopsTalkingSmall from './sprites/day/cyclops/talking@small.webp';
import cyclopsThinkingSmall from './sprites/day/cyclops/thinking@small.webp';
import cyclopsOutSmall from './sprites/day/cyclops/out@small.webp';
import threeEyesBaseSmall from './sprites/day/threeEyes/base@small.webp';
import threeEyesTalkingSmall from './sprites/day/threeEyes/talking@small.webp';
import threeEyesThinkingSmall from './sprites/day/threeEyes/thinking@small.webp';
import threeEyesOutSmall from './sprites/day/threeEyes/out@small.webp';
import dragonBaseSmall from './sprites/day/dragon/base@small.webp';
import dragonTalkingSmall from './sprites/day/dragon/talking@small.webp';
import dragonThinkingSmall from './sprites/day/dragon/thinking@small.webp';
import dragonOutSmall from './sprites/day/dragon/out@small.webp';
import onionBaseSmall from './sprites/day/onion/base@small.webp';
import onionTalkingSmall from './sprites/day/onion/talking@small.webp';
import onionThinkingSmall from './sprites/day/onion/thinking@small.webp';
import onionOutSmall from './sprites/day/onion/out@small.webp';
import whaleBaseSmall from './sprites/day/whale/base@small.webp';
import whaleTalkingSmall from './sprites/day/whale/talking@small.webp';
import whaleThinkingSmall from './sprites/day/whale/thinking@small.webp';
import whaleOutSmall from './sprites/day/whale/out@small.webp';
import polarBearBaseSmall from './sprites/day/polarBear/base@small.webp';
import polarBearTalkingSmall from './sprites/day/polarBear/talking@small.webp';
import polarBearThinkingSmall from './sprites/day/polarBear/thinking@small.webp';
import polarBearOutSmall from './sprites/day/polarBear/out@small.webp';
import shadeBaseSmall from './sprites/day/shade/base@small.webp';
import shadeTalkingSmall from './sprites/day/shade/talking@small.webp';
import shadeThinkingSmall from './sprites/day/shade/thinking@small.webp';
import shadeOutSmall from './sprites/day/shade/out@small.webp';
import kitsuneBaseSmall from './sprites/day/kitsune/base@small.webp';
import kitsuneTalkingSmall from './sprites/day/kitsune/talking@small.webp';
import kitsuneThinkingSmall from './sprites/day/kitsune/thinking@small.webp';
import kitsuneOutSmall from './sprites/day/kitsune/out@small.webp';
import mushroomBaseSmall from './sprites/day/mushroom/base@small.webp';
import mushroomTalkingSmall from './sprites/day/mushroom/talking@small.webp';
import mushroomThinkingSmall from './sprites/day/mushroom/thinking@small.webp';
import mushroomOutSmall from './sprites/day/mushroom/out@small.webp';
import lionCubBaseSmall from './sprites/day/lionCub/base@small.webp';
import lionCubTalkingSmall from './sprites/day/lionCub/talking@small.webp';
import lionCubThinkingSmall from './sprites/day/lionCub/thinking@small.webp';
import lionCubOutSmall from './sprites/day/lionCub/out@small.webp';
import automatonBaseSmall from './sprites/day/automaton/base@small.webp';
import automatonTalkingSmall from './sprites/day/automaton/talking@small.webp';
import automatonThinkingSmall from './sprites/day/automaton/thinking@small.webp';
import automatonOutSmall from './sprites/day/automaton/out@small.webp';
import propJarGlassSmall from './sprites/props/jar-glass@small.webp';
import propJarLidSmall from './sprites/props/jar-lid@small.webp';
import propPlateSmall from './sprites/props/plate@small.webp';
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

export const PORTRAITS: StaticImageData[] = [
  p01,
  p02,
  p03,
  p04,
  p05,
  p06,
  p07,
  p08,
  p09,
  p10,
  p11,
  p12,
];

/** Deterministic per-seat pick, so a seat wears the same face in every view and every session. */
export function hashSeat(seat: string): number {
  let hash = 0;
  for (let i = 0; i < seat.length; i += 1) {
    hash = (hash << 5) - hash + seat.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function portraitFor(seat: string): StaticImageData | null {
  if (PORTRAITS.length === 0) return null;
  return PORTRAITS[hashSeat(seat) % PORTRAITS.length];
}

/** The initials fallback's hue — same hash, so face and fallback are the same identity. */
export function hueFor(seat: string): number {
  return hashSeat(seat) % 360;
}

export function initialsFor(seat: string): string {
  const parts = seat.split(/[_\s-]+/).filter(Boolean);
  if (parts.length === 0) return '??';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  // "player_5" → "P5", which keeps a nine-seat table distinguishable at chip size.
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Kill glyphs, keyed by how the death happened. Death notices carry the attacker type as a
 * typed mark rather than as grey text (ux_baseline §1) — the glyphs are hand-authored
 * pixel SVGs on one 16px grid, imported here as React components.
 */
export type DeathGlyphKind = AttackerType | 'lynch';

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
 * The country behind the dining car's window (FeltWindow): per hour, the far sky and hills, and
 * the near row of pines, fence and pole that scrolls past (alpha). Recipe: stage_architecture §4.
 */
export type WindowHour = 'day' | 'dusk' | 'night' | 'dawn';
export type WindowPicture = 'far' | 'near';

/**
 * The painted props (alpha): the ballot jar's glass and its lid, the stand's front (drawn as a
 * 9-slice), the vote's table with its cloth, the count's plate (already squashed to the table's
 * perspective, ry = 0.3 rx), the replay's red velvet valance (one piece, the stage's width, its
 * fringed hem transparent below) and the window's three-leaf shutter. Recipe: stage_architecture §4.
 */
export type PropPicture =
  'jarGlass' | 'jarLid' | 'stand' | 'voteTable' | 'plate' | 'valance' | 'shutter';

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
  day: Record<Character, Record<DayState, StaticImageData>>;
  props: Record<'jarGlass' | 'jarLid' | 'plate', StaticImageData>;
  roleTiles: Record<RoleSprite, StaticImageData>;
  window: { night: Record<WindowPicture, StaticImageData> };
}

export const SPRITES: {
  day: Record<Character, Record<DayState | 'head', StaticImageData>>;
  kits: Record<KitName, StaticImageData>;
  wood: StaticImageData;
  station: Record<StationPicture, StaticImageData>;
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
    lamp: stationLamp,
    train: stationTrain,
    blind: stationBlind,
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
    valance: propValance,
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
      },
      hare: {
        base: hareBaseSmall,
        talking: hareTalkingSmall,
        thinking: hareThinkingSmall,
        out: hareOutSmall,
      },
      cat: {
        base: catBaseSmall,
        talking: catTalkingSmall,
        thinking: catThinkingSmall,
        out: catOutSmall,
      },
      badger: {
        base: badgerBaseSmall,
        talking: badgerTalkingSmall,
        thinking: badgerThinkingSmall,
        out: badgerOutSmall,
      },
      cyclops: {
        base: cyclopsBaseSmall,
        talking: cyclopsTalkingSmall,
        thinking: cyclopsThinkingSmall,
        out: cyclopsOutSmall,
      },
      threeEyes: {
        base: threeEyesBaseSmall,
        talking: threeEyesTalkingSmall,
        thinking: threeEyesThinkingSmall,
        out: threeEyesOutSmall,
      },
      dragon: {
        base: dragonBaseSmall,
        talking: dragonTalkingSmall,
        thinking: dragonThinkingSmall,
        out: dragonOutSmall,
      },
      onion: {
        base: onionBaseSmall,
        talking: onionTalkingSmall,
        thinking: onionThinkingSmall,
        out: onionOutSmall,
      },
      whale: {
        base: whaleBaseSmall,
        talking: whaleTalkingSmall,
        thinking: whaleThinkingSmall,
        out: whaleOutSmall,
      },
      polarBear: {
        base: polarBearBaseSmall,
        talking: polarBearTalkingSmall,
        thinking: polarBearThinkingSmall,
        out: polarBearOutSmall,
      },
      shade: {
        base: shadeBaseSmall,
        talking: shadeTalkingSmall,
        thinking: shadeThinkingSmall,
        out: shadeOutSmall,
      },
      kitsune: {
        base: kitsuneBaseSmall,
        talking: kitsuneTalkingSmall,
        thinking: kitsuneThinkingSmall,
        out: kitsuneOutSmall,
      },
      mushroom: {
        base: mushroomBaseSmall,
        talking: mushroomTalkingSmall,
        thinking: mushroomThinkingSmall,
        out: mushroomOutSmall,
      },
      lionCub: {
        base: lionCubBaseSmall,
        talking: lionCubTalkingSmall,
        thinking: lionCubThinkingSmall,
        out: lionCubOutSmall,
      },
      automaton: {
        base: automatonBaseSmall,
        talking: automatonTalkingSmall,
        thinking: automatonThinkingSmall,
        out: automatonOutSmall,
      },
    },
    props: { jarGlass: propJarGlassSmall, jarLid: propJarLidSmall, plate: propPlateSmall },
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
