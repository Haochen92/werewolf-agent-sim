'use client';

/**
 * The stage box: a 16:9 frame holding a 1600×900 world, and the nine layers every scene
 * is built from.
 *
 * Everything on the stage is placed in units of that 1600×900 world (see units.ts). The box
 * measures how wide it is actually drawn, and scales the whole world by that one factor,
 * written to `--stage-scale`. So a child positioned at `left: 844px` inside the world is at
 * unit 844 on every screen, and the drawer, the wing and the text shrink with the picture.
 *
 * Why a ResizeObserver rather than pure CSS: CSS cannot yet divide a width by a width to get
 * a plain number, which is what a scale needs. The observer writes the factor straight onto
 * the element (no React re-render), and it runs before the first paint, so nothing shows at
 * the wrong size; until it runs the scale is 0 and the box is just its dark ground.
 *
 * Why one scaled world rather than one scale per layer: a transform walls off blending.
 * The light layer's glows use `mix-blend-mode: screen` over the paint below; if each layer
 * had its own transform, each would blend only with itself and the glows would go flat.
 *
 * The camera: every layer but the HUD sits in one more box that can scale about a point, so
 * the vote's count can push in on the table and the lynch pull back from it, while the wing,
 * the strip and the words stay put. One box for all of them, for the same blending reason.
 *
 * The bleed: mounted `fit="contain"`, the box sits in a wider "house" that clips in its place,
 * so a scene's paint and the HUD's panels can carry on a fixed 600 units past the world's
 * sides where a wide screen shows them (see `Bleed`). Nothing that matters is placed there.
 */
import { animate, useMotionValue, motion } from 'motion/react';
import {
  createContext,
  useContext,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { BackdropSheet } from './instruments/Backdrop';
import { BackdropContext, SmallContext, useSmall, type BackdropSpec } from './set';
import { STAGE_W } from './units';
import { vars } from './paint/materials';
import styles from './Stage.module.css';
import './stage.css';

export { useSmall };

/**
 * The layers, bottom to top (stage_architecture.md §3). `haze` and `grade` are the atmosphere's
 * (Atmosphere.tsx): the haze pushes the room's paint back behind what stands in front of it;
 * the grade (the key light's falloff, the vignette, the grain) is the camera's own, so it sits
 * outside the camera's box with the HUD, under it.
 */
export const LAYERS = [
  'paint',
  'haze',
  'floor',
  'figures',
  'stand',
  'instruments',
  'light',
  'grade',
  'hud',
] as const;
export type LayerName = (typeof LAYERS)[number];
/** The layers the camera does not move. */
const FIXED: readonly LayerName[] = ['grade', 'hud'];

/** Where the camera looks: `scale` about the world point (x, y), which stays where it is. */
export interface StageCamera {
  scale: number;
  x: number;
  y: number;
}

/** A camera move: to `to`, from `from` if given (else from wherever it is), in seconds. */
export interface CameraShot {
  to: StageCamera;
  from?: StageCamera | null;
  duration?: number;
  delay?: number;
  ease?: [number, number, number, number];
}

export type StageProps = Partial<Record<LayerName, ReactNode>> & {
  /**
   * 'width' (default): fill the parent's width. 'contain': fit inside the parent's box, the
   * picture bleeding past the world's sides into the rest of it, up to 21:9 (§3 "The bleed").
   */
  fit?: 'width' | 'contain';
  className?: string;
  /** Where the camera rests when no scene has moved it (default: the whole stage, unscaled). */
  camera?: StageCamera;
  /** A scene (or anything else) that puts its parts into the layers with `<Layer>`. */
  children?: ReactNode;
};

const MATERIAL_VARS = vars();
const WIDE: StageCamera = { scale: 1, x: 0, y: 0 };

type LayerNodes = Partial<Record<LayerName, HTMLDivElement>>;
const LayerContext = createContext<LayerNodes | null>(null);
const CameraContext = createContext<((shot: CameraShot | null) => void) | null>(null);
/** The 16:9 box itself, outside the world's scale: where `Overlay` puts what is laid out in css px. */
const BoxContext = createContext<HTMLDivElement | null>(null);

export function Stage({
  fit = 'width',
  className,
  camera,
  children,
  ...layers
}: StageProps) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [boxNode, setBoxNode] = useState<HTMLDivElement | null>(null);
  const [small, setSmall] = useState(false);
  // the scene's backdrop, drawn here so it outlives the scene's beats (set.ts)
  const [backdrop, setBackdrop] = useState<BackdropSpec | null>(null);
  // The layer divs, once mounted, so `<Layer>` can portal into them. Set during the commit,
  // so the filled layers are drawn before the first paint.
  const [nodes, setNodes] = useState<LayerNodes>({});
  const refs = useMemo(
    () =>
      Object.fromEntries(
        LAYERS.map((name) => [
          name,
          (el: HTMLDivElement | null) => {
            if (el) setNodes((n) => (n[name] === el ? n : { ...n, [name]: el }));
          },
        ]),
      ) as Record<LayerName, (el: HTMLDivElement | null) => void>,
    [],
  );

  useLayoutEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    setBoxNode(el);
    // the house around a `contain` box: how much of the bleed shows left of the world
    const house = fit === 'contain' ? el.parentElement : null;
    const set = () => {
      const w = el.getBoundingClientRect().width;
      el.style.setProperty('--stage-scale', String(w / STAGE_W));
      // a phone: the HUD's boxes that have to fold (the drawer's head, the ballot's row) do.
      // The same 0.75 as `--legible` in Stage.module.css: once the type has grown, they fold.
      const sm = w / STAGE_W < 0.75;
      el.toggleAttribute('data-small', sm);
      setSmall(sm);
      // the bleed a screen wider than 16:9 shows beside the world, in units: the seat rail
      // grows out into it (Wing.tsx), so on a phone the letterbox holds the rail, not the room
      const spare =
        house && w > 0
          ? Math.max(
              0,
              el.getBoundingClientRect().left - house.getBoundingClientRect().left,
            ) /
            (w / STAGE_W)
          : 0;
      el.style.setProperty('--spare', `${spare.toFixed(1)}px`);
    };
    set();
    const ro = new ResizeObserver(set);
    ro.observe(el);
    if (house) ro.observe(house);
    return () => ro.disconnect();
  }, [fit]);

  // The camera: a scene's shot wins over the container's resting camera. Scaling by k about
  // (x, y) is a translate of (x, y)·(1 − k) plus the scale, so all three move in step.
  const [shot, setShot] = useState<CameraShot | null>(null);
  const cx = useMotionValue(0),
    cy = useMotionValue(0),
    ck = useMotionValue(1);
  const shotKey = JSON.stringify(shot ?? camera ?? null);
  useLayoutEffect(() => {
    const s: CameraShot = shot ?? { to: camera ?? WIDE };
    const place = (c: StageCamera) => [c.x * (1 - c.scale), c.y * (1 - c.scale), c.scale];
    if (s.from) {
      const [x, y, k] = place(s.from);
      cx.set(x);
      cy.set(y);
      ck.set(k);
    }
    const [x, y, k] = place(s.to);
    // a phone (`data-small`): the camera has no layer of its own there (Stage.module.css), so
    // a move would repaint the whole world every frame, a full-stage bitmap a frame, which is
    // the stutter and the memory churn at the count's push-in and the pull-backs (build log
    // §8.5); the shot cuts instead, where the move would have started
    const cut = boxRef.current?.hasAttribute('data-small') ?? false;
    const t = {
      duration: cut ? 0 : (s.duration ?? 0),
      delay: s.delay ?? 0,
      ease: s.ease ?? [0.4, 0.2, 0.3, 1],
    };
    const runs = [animate(cx, x, t), animate(cy, y, t), animate(ck, k, t)];
    return () => runs.forEach((r) => r.stop());
    // the shot's JSON is its identity: a new-but-equal object does not restart the move
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shotKey]);

  // the paint layer's foot holds the persistent backdrop in a box of its own, present from the
  // first render, so the scenes' portalled paint (the shutter, the light) always lands above it
  const layerDiv = (name: LayerName) => (
    <div key={name} ref={refs[name]} className={styles.layer} data-layer={name}>
      {name === 'paint' ? (
        <div data-set="" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {backdrop ? <BackdropSheet {...backdrop} /> : null}
        </div>
      ) : null}
      {layers[name]}
    </div>
  );
  const box = (
    <div
      ref={boxRef}
      className={fit === 'width' && className ? `${styles.box} ${className}` : styles.box}
      style={MATERIAL_VARS}
    >
      <div className={styles.world}>
        {/* the small-screen flag reaches the layers too: the Stage's own sheet reads it */}
        <SmallContext.Provider value={small}>
          <motion.div className={styles.camera} style={{ x: cx, y: cy, scale: ck }}>
            {LAYERS.filter((name) => !FIXED.includes(name)).map(layerDiv)}
          </motion.div>
          {FIXED.map(layerDiv)}
          <LayerContext.Provider value={nodes}>
            <BoxContext.Provider value={boxNode}>
              <CameraContext.Provider value={setShot}>
                <BackdropContext.Provider value={setBackdrop}>
                  {children}
                </BackdropContext.Provider>
              </CameraContext.Provider>
            </BoxContext.Provider>
          </LayerContext.Provider>
        </SmallContext.Provider>
      </div>
    </div>
  );
  if (fit === 'width') return box;
  return (
    <div className={className ? `${styles.fit} ${className}` : styles.fit}>
      <div className={styles.house}>{box}</div>
    </div>
  );
}

/**
 * Puts its children into one of the stage's layers. A scene is one component, but its parts
 * belong at different depths (the puppet under the stand, the light over both, the wing on
 * top); the layers have to stay sibling divs in one order for the light's blending to reach
 * the paint, so each part is carried to its layer rather than nested. The container owns the
 * `<Stage>`, the scene inside it only says which layer each part goes in.
 */
export function Layer({ name, children }: { name: LayerName; children?: ReactNode }) {
  const node = useContext(LayerContext)?.[name];
  return node ? createPortal(children, node) : null;
}

/**
 * Puts its children in the stage's box but outside the world, so they are not scaled with it:
 * for what is laid out in css px over the whole stage (the full-screen composer, which has to
 * fit a phone's visible height with the soft keyboard up). It takes the stage's materials; it
 * sits over every layer. `position: fixed` inside it is the stage's frame (the house's
 * container) on the theatre pages, which fill the window.
 */
export function Overlay({ children }: { children?: ReactNode }) {
  const box = useContext(BoxContext);
  return box ? createPortal(children, box) : null;
}

/**
 * Moves the stage's camera while it is mounted (the vote's push-in, the lynch's pull-back);
 * when the scene goes, the camera goes back to the stage's resting shot at once. Durations are
 * as given: the scene scales them by the motion speed, since the stage sits outside it.
 */
export function Camera({ to, from, duration, delay, ease }: CameraShot) {
  const set = useContext(CameraContext);
  const key = JSON.stringify({ to, from, duration, delay, ease });
  useLayoutEffect(() => {
    if (!set) return;
    set(JSON.parse(key) as CameraShot);
    return () => set(null);
  }, [set, key]);
  return null;
}

/**
 * A unique id prefix for one paint drawing. React's `useId` contains characters that SVG
 * `url(#…)` references choke on, so they are dropped.
 */
export function usePaintId(): string {
  return 'p' + useId().replace(/[^A-Za-z0-9_-]/g, '');
}

/* A generator's markup for an id and options, kept across instances and beats: the house
   light's holes take 60–110 ms to trace (paint/holes.ts) and a beat's light often repeats an
   earlier one (the count's, the morning's). A few dozen drawings per generator, oldest out. */
const DRAWN = new WeakMap<(o: never) => string, Map<string, string>>();
const KEEP = 48;
function drawn<O extends { id: string }>(of: (o: O) => string, id: string, key: string) {
  let m = DRAWN.get(of as (o: never) => string);
  if (!m) DRAWN.set(of as (o: never) => string, (m = new Map()));
  const k = id + '\0' + key;
  const hit = m.get(k);
  if (hit !== undefined) return hit;
  const html = of({ ...JSON.parse(key), id } as O);
  if (m.size >= KEEP) m.delete(m.keys().next().value as string);
  m.set(k, html);
  return html;
}

/**
 * One paint generator's output, drawn once and kept until its options change (and remembered
 * across instances, see `drawn`). `of` is a generator from `src/stage/paint/`; `opts` its
 * options minus `id`, which comes from `useId()` so two stages on one page never share a
 * gradient or a mask.
 */
export function Paint<O extends { id: string }>({
  of,
  opts,
}: {
  of: (o: O) => string;
  opts: Omit<O, 'id'>;
}) {
  const id = usePaintId();
  // The options are plain data; their JSON is the memo key, so a new-but-equal object is free.
  const key = JSON.stringify(opts);
  const html = useMemo(() => drawn(of, id, key), [of, key, id]);
  // The kit's scatter hash (draw.ts `rnd`) magnifies the last bit of Math.sin, which differs
  // between Node and the browser, so a few coordinates differ by ~1e-10 after hydration. That
  // is invisible, and the hash has to stay the kit's to draw the kit's picture.
  return (
    <div
      className="stage-paint"
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
