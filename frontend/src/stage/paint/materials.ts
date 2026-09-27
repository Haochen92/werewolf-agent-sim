/**
 * The stage's palette: the materials the HUD is made of, the four phase paints the car shows
 * through its window, and the rule for how each hour lights the room.
 *
 * These are copied from the design kit (kits/stage-kit.js, VERSION 2026-09-23) unchanged.
 * They are data, not style: the paint generators bake them into SVG strings, and `vars()`
 * hands the same values to CSS as custom properties on the stage box, so a card drawn in JSX
 * and a panel drawn by a generator can never disagree about what "brass" is.
 */

export type Phase = 'day' | 'dusk' | 'night' | 'dawn';
export const PHASES_IN_ORDER: readonly Phase[] = ['day', 'dusk', 'night', 'dawn'];

// the HUD's materials, from the X-ray bench (locked revision 52) and the HUD blockout
export const MATERIALS = {
  ink: '#24180c',
  bone: '#efe4cb',
  bone2: '#cdbb93',
  bone3: '#8d7a55',
  cloak0: '#0e0906',
  cloak1: '#241910',
  cloak2: '#4d3824',
  paper: '#ecdfc3',
  paperInk: '#24180c',
  glassTop: 'rgba(33,27,20,.96)',
  glassBot: 'rgba(14,9,6,.96)',
  film: '#0b191f',
  filmInk: '#7fdcf2',
  filmText: '#c6e2ea',
  filmMain: '#eefaff',
  filmMut: '#7ea9b6',
  filmLine: '#264a56',
  filmBorder: '#dfe9ec',
  sure: '#7fdcf2',
  slip: '#fbf7ea',
  slipInk: '#26283a',
  slipRule: '#c3d3e8',
  amber: '#e0a63a',
  warm: '#ffb35c',
  town: '#e0a63a',
  wolf: '#e3503f',
  sk: '#9d7cff',
  townInk: '#4a2e0a',
  wolfInk: '#4a120c',
  skInk: '#241548',
  border: '#1b120b',
  frameLine: '#8d7a55',
  floor: '#0c0a07',
} as const;

export interface PhasePaint {
  name: string;
  skyTop: string;
  row: string;
  win: string;
  ray: string;
  floor: string;
  cold: boolean;
  /** The lantern is lit at this hour. */
  lit: boolean;
}

// one set of shapes, four paints (the glass takes `skyTop` until the felt country loads)
export const PHASES: Record<Phase, PhasePaint> = {
  day: {
    name: 'Day',
    skyTop: '#c9b26e',
    row: '#5f5e3c',
    win: '#3d4030',
    ray: '#d8b65a',
    floor: '#4a4a30',
    cold: false,
    lit: false,
  },
  dusk: {
    name: 'Voting (dusk)',
    skyTop: '#5a4a6a',
    row: '#3a3040',
    win: '#ffd27a',
    ray: '#d8804f',
    floor: '#2a2430',
    cold: false,
    lit: true,
  },
  night: {
    name: 'Night',
    skyTop: '#0d1626',
    row: '#0e1c24',
    win: '#ffd27a',
    ray: '#bcd0d4',
    floor: '#0b161c',
    cold: true,
    lit: true,
  },
  dawn: {
    name: 'Dawn',
    skyTop: '#7d8b94',
    row: '#46534c',
    win: '#4a5550',
    ray: '#dcc08a',
    floor: '#3a463f',
    cold: false,
    lit: false,
  },
};

/* the room-light rule: the phase's ambient multiplied over the walls (not the glass), then a warm pool per source */
export const ROOMLIGHT: Record<Phase, { tint: string | null; a: number; glow: number }> = {
  day: { tint: null, a: 0, glow: 0.35 },
  dusk: { tint: '#c0703a', a: 0.24, glow: 0.7 },
  night: { tint: '#0c1426', a: 0.66, glow: 1 },
  dawn: { tint: '#6d7c86', a: 0.26, glow: 0.3 },
};

// the wall clock keeps the phase: [hour, minute]
export const CLOCK: Record<Phase, [number, number]> = {
  day: [2, 12],
  dusk: [6, 12],
  night: [12, 12],
  dawn: [6, 6],
};

/** The dining car's woods and its brass. */
export const CAR = {
  dadoH: 0.15,
  wall: '#4a2c18',
  wallDark: '#3a2212',
  dado: '#3a2212',
  brass: '#b08a4a',
};
/** The stage floor's boards, and the one ink every outline is drawn in. */
/**
 * The station platform's paint (the waiting room, review 2026-09-26 §A5), from the waiting-room
 * mockup's CSS: a winter night under a walnut beam, a cold stone platform whose edge holds a
 * drift of snow, the track bed, and the lamps' warm pools.
 */
export const STATION = {
  sky: '#1c2550',
  /** The beam: flat walnut (the bleed, or no picture), the shade over the wood, its brass trim, the snow on it. */
  beam: '#2b190e',
  beamShadeTop: 'rgb(30,16,8)',
  beamShadeBot: 'rgb(12,6,3)',
  trim: '#c9a25e',
  lipTop: '#f3f5f4',
  lipBot: '#dfe4e6',
  floor: '#3b4046',
  /** The edge: flat stone (the bleed, or no picture), the tint over it, its light from above, the drift. */
  edge: '#8d9198',
  edgeTintTop: 'rgb(150,155,162)',
  edgeTintBot: 'rgb(40,42,48)',
  edgeLight: 'rgb(235,238,242)',
  drift: 'rgb(245,247,250)',
  railTop: '#6d6a66',
  railBot: '#2a2826',
  railFar: '#3b3936',
  moon: '#f1ecd8',
  lamp: 'rgb(255,196,110)',
} as const;

export const BOARD = '#5a3f26';
export const BOARD2 = '#4a3320';
export const K2 = '#24180c';

type CssVar = `--${string}`;

/** The materials as CSS custom properties, for the stage element. */
export function vars(): Record<CssVar, string> {
  const m = MATERIALS;
  return {
    '--ink': m.ink,
    '--bone': m.bone,
    '--bone2': m.bone2,
    '--bone3': m.bone3,
    '--cloak0': m.cloak0,
    '--cloak1': m.cloak1,
    '--cloak2': m.cloak2,
    '--paper': m.paper,
    '--paper-ink': m.paperInk,
    '--glass-top': m.glassTop,
    '--glass-bot': m.glassBot,
    '--film': m.film,
    '--film-ink': m.filmInk,
    '--film-text': m.filmText,
    '--film-main': m.filmMain,
    '--film-mut': m.filmMut,
    '--film-line': m.filmLine,
    '--film-border': m.filmBorder,
    '--sure': m.sure,
    '--slip': m.slip,
    '--slip-ink': m.slipInk,
    '--slip-rule': m.slipRule,
    '--amber': m.amber,
    '--town': m.town,
    '--wolf': m.wolf,
    '--sk': m.sk,
    '--town-ink': m.townInk,
    '--wolf-ink': m.wolfInk,
    '--sk-ink': m.skInk,
  };
}
