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
import owlChip from './sprites/day/owl/chip.webp';
import hareBase from './sprites/day/hare/base.webp';
import hareTalking from './sprites/day/hare/talking.webp';
import hareThinking from './sprites/day/hare/thinking.webp';
import hareOut from './sprites/day/hare/out.webp';
import hareChip from './sprites/day/hare/chip.webp';
import catBase from './sprites/day/cat/base.webp';
import catTalking from './sprites/day/cat/talking.webp';
import catThinking from './sprites/day/cat/thinking.webp';
import catOut from './sprites/day/cat/out.webp';
import catChip from './sprites/day/cat/chip.webp';
import badgerBase from './sprites/day/badger/base.webp';
import badgerTalking from './sprites/day/badger/talking.webp';
import badgerThinking from './sprites/day/badger/thinking.webp';
import badgerOut from './sprites/day/badger/out.webp';
import badgerChip from './sprites/day/badger/chip.webp';
import cyclopsBase from './sprites/day/cyclops/base.webp';
import cyclopsTalking from './sprites/day/cyclops/talking.webp';
import cyclopsThinking from './sprites/day/cyclops/thinking.webp';
import cyclopsOut from './sprites/day/cyclops/out.webp';
import cyclopsChip from './sprites/day/cyclops/chip.webp';
import threeEyesBase from './sprites/day/threeEyes/base.webp';
import threeEyesTalking from './sprites/day/threeEyes/talking.webp';
import threeEyesThinking from './sprites/day/threeEyes/thinking.webp';
import threeEyesOut from './sprites/day/threeEyes/out.webp';
import threeEyesChip from './sprites/day/threeEyes/chip.webp';
import dragonBase from './sprites/day/dragon/base.webp';
import dragonTalking from './sprites/day/dragon/talking.webp';
import dragonThinking from './sprites/day/dragon/thinking.webp';
import dragonOut from './sprites/day/dragon/out.webp';
import dragonChip from './sprites/day/dragon/chip.webp';
import onionBase from './sprites/day/onion/base.webp';
import onionTalking from './sprites/day/onion/talking.webp';
import onionThinking from './sprites/day/onion/thinking.webp';
import onionOut from './sprites/day/onion/out.webp';
import onionChip from './sprites/day/onion/chip.webp';
import whaleBase from './sprites/day/whale/base.webp';
import whaleTalking from './sprites/day/whale/talking.webp';
import whaleThinking from './sprites/day/whale/thinking.webp';
import whaleOut from './sprites/day/whale/out.webp';
import whaleChip from './sprites/day/whale/chip.webp';
import polarBearBase from './sprites/day/polarBear/base.webp';
import polarBearTalking from './sprites/day/polarBear/talking.webp';
import polarBearThinking from './sprites/day/polarBear/thinking.webp';
import polarBearOut from './sprites/day/polarBear/out.webp';
import polarBearChip from './sprites/day/polarBear/chip.webp';
import shadeBase from './sprites/day/shade/base.webp';
import shadeTalking from './sprites/day/shade/talking.webp';
import shadeThinking from './sprites/day/shade/thinking.webp';
import shadeOut from './sprites/day/shade/out.webp';
import shadeChip from './sprites/day/shade/chip.webp';
import owlPlush from './sprites/plush/owl.webp';
import harePlush from './sprites/plush/hare.webp';
import catPlush from './sprites/plush/cat.webp';
import badgerPlush from './sprites/plush/badger.webp';
import cyclopsPlush from './sprites/plush/cyclops.webp';
import threeEyesPlush from './sprites/plush/threeEyes.webp';
import dragonPlush from './sprites/plush/dragon.webp';
import onionPlush from './sprites/plush/onion.webp';
import whalePlush from './sprites/plush/whale.webp';
import polarBearPlush from './sprites/plush/polarBear.webp';
import shadePlush from './sprites/plush/shade.webp';
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
import propStand from './sprites/props/stand-front.webp';
import propVoteTable from './sprites/props/vote-table.webp';
import propWallClock from './sprites/props/wall-clock.webp';
import propWallLampUnlit from './sprites/props/wall-lamp-unlit.webp';
import propWallLampLit from './sprites/props/wall-lamp-lit.webp';
import wallClockShadow from './sprites/shadow/wall-clock.webp';
import wallLampShadow from './sprites/shadow/wall-lamp.webp';
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
import owlPlushShadow from './sprites/shadow/plush/owl.webp';
import harePlushShadow from './sprites/shadow/plush/hare.webp';
import catPlushShadow from './sprites/shadow/plush/cat.webp';
import badgerPlushShadow from './sprites/shadow/plush/badger.webp';
import cyclopsPlushShadow from './sprites/shadow/plush/cyclops.webp';
import threeEyesPlushShadow from './sprites/shadow/plush/threeEyes.webp';
import dragonPlushShadow from './sprites/shadow/plush/dragon.webp';
import onionPlushShadow from './sprites/shadow/plush/onion.webp';
import whalePlushShadow from './sprites/shadow/plush/whale.webp';
import polarBearPlushShadow from './sprites/shadow/plush/polarBear.webp';
import shadePlushShadow from './sprites/shadow/plush/shade.webp';
import grain from './sprites/atmosphere/grain.webp';
import textureWalnut from './sprites/textures/walnut.webp';
import textureBoards from './sprites/textures/boards.webp';
import textureVelvet from './sprites/textures/velvet.webp';

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
 * The stage's cast (stage_architecture.md §4). Order is the puppet kit's, and it matters:
 * castForGame shuffles this list, so reordering it would recast every past game.
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
export type StationPicture =
  'sky' | 'floor' | 'post' | 'lamp' | 'train' | 'blind';

/**
 * The country behind the dining car's window (FeltWindow): per hour, the far sky and hills, and
 * the near row of pines, fence and pole that scrolls past (alpha). Recipe: stage_architecture §4.
 */
export type WindowHour = 'day' | 'dusk' | 'night' | 'dawn';
export type WindowPicture = 'far' | 'near';

/**
 * The painted props (alpha): the ballot jar's glass and its lid, the stand's front (drawn as a
 * 9-slice), the vote's table with its cloth, the car's wall clock (no hands) and its wall lamp,
 * unlit and lit. Recipe: stage_architecture §4.
 */
export type PropPicture =
  | 'jarGlass'
  | 'jarLid'
  | 'stand'
  | 'voteTable'
  | 'wallClock'
  | 'wallLampUnlit'
  | 'wallLampLit';

/*
 * The atmosphere's pictures (stage_architecture §4 "Atmosphere"): each day figure's and plush
 * doll's cast shadow, its silhouette baked small and soft (a 12 px margin round 128 px tall),
 * and the film grain, a 160 px tile of noise.
 */

/**
 * The room's surfaces (seamless tiles, opaque): the walls' walnut veneer, the floor's boards and
 * the replay valance's velvet, each tinted to the flat colour it fills. Recipe: stage_architecture §4.
 */
export type TexturePicture = 'walnut' | 'boards' | 'velvet';

export const SPRITES: {
  day: Record<Character, Record<DayState | 'chip', StaticImageData>>;
  plush: Record<Character, StaticImageData>;
  kits: Record<KitName, StaticImageData>;
  wood: StaticImageData;
  station: Record<StationPicture, StaticImageData>;
  window: Record<WindowHour, Record<WindowPicture, StaticImageData>>;
  props: Record<PropPicture, StaticImageData>;
  shadow: {
    day: Record<Character, Record<DayState, StaticImageData>>;
    plush: Record<Character, StaticImageData>;
    wall: { clock: StaticImageData; lamp: StaticImageData };
  };
  grain: StaticImageData;
  textures: Record<TexturePicture, StaticImageData>;
} = {
  day: {
    owl: {
      base: owlBase,
      talking: owlTalking,
      thinking: owlThinking,
      out: owlOut,
      chip: owlChip,
    },
    hare: {
      base: hareBase,
      talking: hareTalking,
      thinking: hareThinking,
      out: hareOut,
      chip: hareChip,
    },
    cat: {
      base: catBase,
      talking: catTalking,
      thinking: catThinking,
      out: catOut,
      chip: catChip,
    },
    badger: {
      base: badgerBase,
      talking: badgerTalking,
      thinking: badgerThinking,
      out: badgerOut,
      chip: badgerChip,
    },
    cyclops: {
      base: cyclopsBase,
      talking: cyclopsTalking,
      thinking: cyclopsThinking,
      out: cyclopsOut,
      chip: cyclopsChip,
    },
    threeEyes: {
      base: threeEyesBase,
      talking: threeEyesTalking,
      thinking: threeEyesThinking,
      out: threeEyesOut,
      chip: threeEyesChip,
    },
    dragon: {
      base: dragonBase,
      talking: dragonTalking,
      thinking: dragonThinking,
      out: dragonOut,
      chip: dragonChip,
    },
    onion: {
      base: onionBase,
      talking: onionTalking,
      thinking: onionThinking,
      out: onionOut,
      chip: onionChip,
    },
    whale: {
      base: whaleBase,
      talking: whaleTalking,
      thinking: whaleThinking,
      out: whaleOut,
      chip: whaleChip,
    },
    polarBear: {
      base: polarBearBase,
      talking: polarBearTalking,
      thinking: polarBearThinking,
      out: polarBearOut,
      chip: polarBearChip,
    },
    shade: {
      base: shadeBase,
      talking: shadeTalking,
      thinking: shadeThinking,
      out: shadeOut,
      chip: shadeChip,
    },
  },
  plush: {
    owl: owlPlush,
    hare: harePlush,
    cat: catPlush,
    badger: badgerPlush,
    cyclops: cyclopsPlush,
    threeEyes: threeEyesPlush,
    dragon: dragonPlush,
    onion: onionPlush,
    whale: whalePlush,
    polarBear: polarBearPlush,
    shade: shadePlush,
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
    wallClock: propWallClock,
    wallLampUnlit: propWallLampUnlit,
    wallLampLit: propWallLampLit,
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
    },
    plush: {
      owl: owlPlushShadow,
      hare: harePlushShadow,
      cat: catPlushShadow,
      badger: badgerPlushShadow,
      cyclops: cyclopsPlushShadow,
      threeEyes: threeEyesPlushShadow,
      dragon: dragonPlushShadow,
      onion: onionPlushShadow,
      whale: whalePlushShadow,
      polarBear: polarBearPlushShadow,
      shade: shadePlushShadow,
    },
    wall: { clock: wallClockShadow, lamp: wallLampShadow },
  },
  grain,
  textures: { walnut: textureWalnut, boards: textureBoards, velvet: textureVelvet },
};

/**
 * Where each day figure's head starts and how tall the figure is, as fractions of the image
 * height, so puppets of different builds stand at one height on the stage. Copied from the
 * bundle's sprites-manifest.json; re-copy it if the masters are re-exported.
 */
export const BODY: Record<Character, { top: number; body: number }> = {
  owl: { top: 0.07, body: 0.93 },
  hare: { top: 0.086, body: 0.914 },
  cat: { top: 0.058, body: 0.942 },
  badger: { top: 0.15, body: 0.85 },
  cyclops: { top: 0.103, body: 0.897 },
  threeEyes: { top: 0.276, body: 0.724 },
  dragon: { top: 0.087, body: 0.913 },
  onion: { top: 0.131, body: 0.869 },
  whale: { top: 0.104, body: 0.896 },
  polarBear: { top: 0.051, body: 0.949 },
  shade: { top: 0.147, body: 0.853 },
};

/**
 * How much larger or smaller to draw each plush doll so every doll has the same head-to-toe
 * height on its hook (ears, hats and antennae rise above; three-eyes' antennae are the reason
 * its number is the largest). The sprites are all cut to one image height, so without this a
 * doll with tall ears would hang with a smaller body. Copied from the bundle's
 * sprites-manifest.json (`plush_scale`); re-copy it if the plush masters are re-exported.
 */
export const PLUSH_SCALE: Record<Character, number> = {
  owl: 1.011,
  hare: 1.043,
  cat: 0.98,
  badger: 1.014,
  cyclops: 0.974,
  threeEyes: 1.163,
  dragon: 0.946,
  onion: 1.027,
  whale: 1.0,
  polarBear: 0.964,
  shade: 0.994,
};
