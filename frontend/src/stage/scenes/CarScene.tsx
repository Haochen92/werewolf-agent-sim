'use client';

/**
 * The dining car as one set across the scenes played in it: the deal, the day, the vote, the
 * lynch, the night's lobby, the morning, the game over and the replay's night. Each of those
 * used to be its own component, so a change of scene unmounted the car and built it again: the
 * wing, the house light, the shutter, the valance, every picture decoded afresh, which on a
 * phone was a burst of script and paint at the first beat of every scene (build log §8.9), on
 * top of the per-beat rebuilds the keyed scenes paid.
 *
 * Now every car scene is a *body* under this one host, and describes the set it wants with
 * `<CarSetSpec>`, as a scene describes its backdrop to the Stage (instruments/Backdrop.tsx) and
 * its shot with `Camera`. The host draws the set once (`CarSetSheet`) and keeps it from body to
 * body, updating it in place: the wing's tiles change, the light's sheet is redrawn when its
 * options change, the shutter plays into its new state. A body that describes no set (the
 * replay's night rooms) leaves the car's set down, and the next body that does brings it up.
 *
 * The set is drawn before the body, so the body's own HUD (a notice, the speech box, a read
 * card) paints over the wing and the strip as it always did. The first time the set comes up
 * the body is mounted again under it, in the same commit, so its pieces land after the set's.
 *
 * The set is drawn from the description *and the scene props the body described it with*,
 * never from the host's current props: on a change of beat the host renders once before the
 * body's new description lands, and a set drawn from the new view under the old description
 * (the morning's view, the night's wing with no death held back) would tell the wing a seat
 * had died and close its open notes.
 */
import {
  createContext,
  memo,
  useContext,
  useLayoutEffect,
  useRef,
  useState,
  type ComponentType,
} from 'react';
import { Atmosphere } from '../Atmosphere';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import type { SceneId } from '../beats/types';
import { Backdrop } from '../instruments/Backdrop';
import { Trap, type TrapState } from '../instruments/Floor';
import { Shutter } from '../instruments/Shutter';
import { TopStrip, type TopStripProps } from '../instruments/TopStrip';
import { StageMotion } from '../motion';
import { notebookGame } from '../notebook';
import type { Special } from '../paint/draw';
import type { Pool } from '../paint/light';
import type { Phase } from '../paint/materials';
import type { ShutterState } from '../paint/window';
import { sideOpen, stripButtons } from '../slot';
import { geometry } from '../units';
import { HouseLights, TableWing, type WingSeatOptions } from './DiningCarParts';
import type { SceneProps } from './types';

/** What a body asks of the car's set at a beat. */
export interface CarSet {
  /** The car's hour: the backdrop's sheet, the grade and the house light's warmth. */
  phase: Phase;
  /** The hour the car was at before this beat, to fade from (instruments/Backdrop.tsx). */
  backdrop?: { from?: Phase | null; fadeDelay?: number };
  shutter: { state: ShutterState; animate?: boolean; delay?: number };
  /** The trap in the floor, where the scene has one; absent, the painted floor is shut. */
  trap?: { state: TrapState; animate?: boolean; phase?: Phase } | null;
  light: { pool: Pool; specials?: Special[]; quiet?: Special[]; dark: number };
  wing: WingSeatOptions;
  strip: Pick<TopStripProps, 'title' | 'sub' | 'disc' | 'count' | 'side' | 'unlocked'>;
}

interface Described {
  spec: CarSet;
  props: SceneProps;
}

const CarSetContext = createContext<((d: Described | null) => void) | null>(null);
const BodyProps = createContext<SceneProps | null>(null);

/**
 * A body's description of the set, applied after each of its renders (before paint) and
 * withdrawn when the body goes, together with the scene props the body rendered with. The
 * host memoises the body on its props, so a description landing cannot start the body over.
 */
export function CarSetSpec(spec: CarSet) {
  const set = useContext(CarSetContext);
  const props = useContext(BodyProps);
  useLayoutEffect(() => {
    if (props) set?.({ spec, props });
  });
  useLayoutEffect(() => () => set?.(null), [set]);
  return null;
}

/** The set itself, drawn by the host from the body's description. */
function CarSetSheet({ spec, ...props }: SceneProps & { spec: CarSet }) {
  const { view, me, presentation, slot: slotInput } = props;
  const { hud, cast } = presentation;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  return (
    <>
      <Atmosphere room="car" phase={spec.phase} hud={hud} side={side} baked />
      <Layer name="paint">
        <Backdrop
          phase={spec.phase}
          from={spec.backdrop?.from}
          fadeDelay={spec.backdrop?.fadeDelay}
          hud={hud}
          side={side}
        />
        <Shutter
          g={g}
          state={spec.shutter.state}
          animate={spec.shutter.animate}
          delay={spec.shutter.delay}
        />
      </Layer>
      {spec.trap ? (
        <Layer name="floor">
          <Trap
            g={g}
            phase={spec.trap.phase ?? spec.phase}
            state={spec.trap.state}
            animate={spec.trap.animate}
          />
        </Layer>
      ) : null}
      <Layer name="light">
        <HouseLights
          phase={spec.phase}
          hud={hud}
          side={side}
          pool={spec.light.pool}
          specials={spec.light.specials}
          quiet={spec.light.quiet}
          dark={spec.light.dark}
        />
      </Layer>
      <Layer name="hud">
        <TableWing
          view={view}
          cast={cast}
          me={me}
          hud={hud}
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          edit={slotInput?.notebook}
          opts={spec.wing}
        />
        <TopStrip hud={hud} {...spec.strip} {...stripButtons(presentation, slotInput)} />
      </Layer>
    </>
  );
}

const memoised = new Map<ComponentType<SceneProps>, ComponentType<SceneProps>>();

/** The host for a car scene's body: `bodies` names the body for each scene it plays. */
export function carScene(bodies: Partial<Record<SceneId, ComponentType<SceneProps>>>) {
  return function CarScene(props: SceneProps) {
    const [described, setDescribed] = useState<Described | null>(null);
    // the set drawn first: when it comes up, the body mounts again under it in the same commit
    const [epoch, setEpoch] = useState(0);
    const wasUp = useRef(false);
    const up = described !== null;
    useLayoutEffect(() => {
      if (up && !wasUp.current) setEpoch((e) => e + 1);
      wasUp.current = up;
    }, [up]);
    const body = bodies[props.beat.scene];
    if (!body) return null;
    let Body = memoised.get(body);
    if (!Body) memoised.set(body, (Body = memo(body)));
    return (
      <StageMotion speed={props.presentation.motion}>
        {described ? <CarSetSheet {...described.props} spec={described.spec} /> : null}
        <CarSetContext.Provider value={setDescribed}>
          <BodyProps.Provider value={props}>
            <Body key={epoch} {...props} />
          </BodyProps.Provider>
        </CarSetContext.Provider>
        <SideSlot {...props} />
      </StageMotion>
    );
  };
}
