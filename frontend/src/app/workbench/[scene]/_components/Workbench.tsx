'use client';

/**
 * The workbench page: reads the URL, draws that one view of that one scene from the fixture,
 * and offers a strip of controls that write the URL back. Nothing else holds state, so the
 * address bar can be copied and the same frame comes back (`strip=0` hides the controls, for
 * a screenshot of the stage alone).
 */
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Layer, Stage } from '@/stage/Stage';
import type { SceneId } from '@/stage/beats/types';
import { useDrawerFilters } from '@/stage/drawer/use-drawer-filters';
import type { FileChoice } from '@/stage/film/case-file';
import { useNoteEditing } from '@/stage/notebook';
import type { SlotInput, StopInput } from '@/stage/scenes/types';
import { LeaveConfirm } from '@/stage/instruments/TopStrip';
import { pressFile, pressTranscript, sideOpen } from '@/stage/slot';
import {
  BeatStepper,
  ControlStrip,
  Select,
  Seg,
  UrlReadout,
} from '@/stage/workbench/ControlStrip';
import { anchorLine, workbenchFrame } from '@/stage/workbench/frame';
import { FIXTURE_GAME_ID } from '@/stage/workbench/fixture';
import { SCENE_IDS, SCENES, isSceneId } from '@/stage/workbench/registry';
import {
  parseFrame,
  parseQuery,
  parseViewer,
  viewerParam,
  writeQuery,
  type DeviceFrame,
  type FramePreset,
  type WorkbenchQuery,
} from '@/stage/workbench/url';
import { PaintBench, PaintControls } from './PaintBench';
import styles from './Workbench.module.css';

const VIEWERS = [
  { value: 'spect', label: 'spectator' },
  { value: 'xray', label: 'X-ray' },
  ...Array.from({ length: 9 }, (_, i) => ({
    value: `seat:player_${i + 1}`,
    label: `seat ${i + 1}`,
  })),
];

// The workbench has no server: a prompt's answer is logged where the console can see it.
const logAct = (target: string | null) =>
  console.info('[workbench] act →', target ?? 'no one');
const logSay = (text: string) => console.info('[workbench] say →', text);

/** The strip's frame buttons: fill, then the presets under a short name (a WxH is URL-only). */
const FRAMES: { value: 'fill' | FramePreset; label: string }[] = [
  { value: 'fill', label: 'fill' },
  { value: 'iphone14', label: 'iPhone 14' },
  { value: 'iphone15max', label: '15 Max' },
  { value: 'pixel8', label: 'Pixel 8' },
];

/**
 * The stage in a box of a phone's landscape size, mounted with the same `fit` as the real
 * routes, so it letterboxes as it would on the device. A phone's CSS px is drawn about 30%
 * smaller than a desktop's, which the caption says once.
 */
function PhoneFrame({ frame, children }: { frame: DeviceFrame; children: ReactNode }) {
  const size = `${frame.w}×${frame.h} css px`;
  return (
    <div className={styles.frameArea}>
      <div className={styles.frame} style={{ width: frame.w, height: frame.h }} data-frame>
        {children}
      </div>
      <p className={styles.frameCaption}>
        {frame.name ? `${frame.name} · ${size}` : size} · in the hand ≈ 0.7× this
      </p>
    </div>
  );
}

function Placeholder({ title, detail }: { title: string; detail?: string }) {
  return (
    <Layer name="hud">
      <div className={styles.placeholder}>
        {title}
        {detail ? <small>{detail}</small> : null}
      </div>
    </Layer>
  );
}

export function Workbench({ scene }: { scene: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const q = useMemo(() => parseQuery(params), [params]);
  const showStrip = params.get('strip') !== '0';
  // the GPU probe (styles/gpu-probe.css): `?gpu=nofilter noblend …` subtracts kinds of GPU work
  // from the whole page, to find what a phone's browser cannot draw; cleared when the page goes
  const gpu = params.get('gpu');
  useEffect(() => {
    const html = document.documentElement;
    if (gpu) html.dataset.gpu = gpu.replace(/[,+]/g, ' ');
    else delete html.dataset.gpu;
    return () => {
      delete html.dataset.gpu;
    };
  }, [gpu]);

  const go = useCallback(
    (next: Partial<WorkbenchQuery>, toScene?: string) => {
      const path = toScene ? `/workbench/${toScene}` : pathname;
      router.replace(`${path}?${writeQuery({ ...q, ...next }, params)}`, { scroll: false });
    },
    [q, params, pathname, router],
  );
  const setParam = useCallback(
    (k: string, v: string) => {
      const next = new URLSearchParams(params);
      next.set(k, v);
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [params, pathname, router],
  );

  const known = isSceneId(scene);
  const frame = useMemo(
    () => (known ? workbenchFrame(scene as SceneId, q) : null),
    [known, scene, q],
  );

  // The side slot's state that outlives a beat: the drawer's filters and the film's tab. The
  // strip's two tabs on the stage write the URL, as the replay's container holds them.
  const drawer = useDrawerFilters();
  const [filmTab, setFilmTab] = useState('notes');
  const [fileSeat, setFileSeat] = useState<FileChoice | null>(null);
  // a live cut's seat notebook: the open editor stays open as the beats are stepped
  const noteEditing = useNoteEditing();
  // a live cut's door: "Leave the table?" is open (Leave is only logged: there is no lobby here)
  const [leaving, setLeaving] = useState(false);
  const slotInput = useMemo((): SlotInput | undefined => {
    if (!frame) return undefined;
    const now = frame.presentation;
    return {
      filters: drawer.filters,
      onFilters: drawer.setFilters,
      drawerScroll: drawer.scroll,
      filmTab,
      onFilmTab: setFilmTab,
      fileSeat,
      onFileSeat: setFileSeat,
      notebook: noteEditing,
      // a live cut draws the closed file's link to the replay, as a live game would
      replayHref: q.live ? `/replays/${FIXTURE_GAME_ID}` : undefined,
      ahead: frame.ahead,
      onTranscript: () => go({ slot: pressTranscript(now).slot ?? 'none' }),
      onFile: () => go({ slot: pressFile(now).slot ?? 'none' }),
      onOpenFile: (seat) => {
        setFileSeat({ seat, key: null });
        go({ slot: 'film' });
      },
      // the strip's Reveal as its containers draw it: the replay's switch writes the viewer
      // (as the viewer control above does); a live cut's is locked until the game is over
      ...(q.live
        ? {
            revealLocked: !now.xray,
            onLeave: frame.me && !now.xray ? () => setLeaving(true) : undefined,
          }
        : q.hud === 'replay'
          ? {
              onReveal: () =>
                go({ viewer: now.xray ? { kind: 'spect' } : { kind: 'xray' }, beat: 0 }),
            }
          : {}),
    };
  }, [frame, drawer, filmTab, fileSeat, noteEditing, go, q.live, q.hud]);

  // the replay's stops, as its container hands them down (the X-ray's cut in the replay's
  // frame): the rooms and the hub are this scene's beats; "End the night" leaves the scene, so
  // here it is only logged, like a prompt's answer
  const stopInput = useMemo((): StopInput | undefined => {
    if (!frame || q.live || q.hud !== 'replay' || !frame.presentation.xray)
      return undefined;
    const { beats, index } = frame;
    const hub = beats.findIndex(
      (b) => b.id === 'rnight.hub' && b.day === beats[index]?.day,
    );
    return {
      visited: [],
      onVisit: (find) => {
        const i = beats.findIndex(find);
        if (i >= 0) go({ beat: i });
        return i >= 0;
      },
      onPlay: () => index < beats.length - 1 && go({ beat: index + 1 }),
      onEndNight: () => console.info('[workbench] end the night'),
      onBack: () => hub >= 0 && go({ beat: hub }),
    };
  }, [frame, go, q.live, q.hud]);

  // the arrow keys step beats, unless a control has the focus
  useEffect(() => {
    if (!frame) return;
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
      if (e.key === 'ArrowRight' && frame.index < frame.beats.length - 1)
        go({ beat: frame.index + 1 });
      if (e.key === 'ArrowLeft' && frame.index > 0) go({ beat: frame.index - 1 });
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [frame, go]);

  const scenePicker = (
    <Seg
      label="scene"
      options={[
        ...SCENE_IDS.map((id) => ({ value: id as string, muted: SCENES[id] === null })),
        { value: 'paint' },
      ]}
      value={scene}
      onChange={(id) => go({ beat: 0 }, id)}
    />
  );

  let stage: ReactNode;
  let controls: ReactNode;
  if (scene === 'paint') {
    stage = <PaintBench params={params} />;
    controls = <PaintControls params={params} set={setParam} />;
  } else if (!frame) {
    stage = <Placeholder title={`No scene called “${scene}”`} />;
  } else {
    const Scene = known ? SCENES[scene as SceneId] : null;
    const { beat, view } = frame;
    stage = !Scene ? (
      <Placeholder
        title={`The ${scene} scene is not built yet`}
        detail={`${frame.beats.length} beats for this viewer`}
      />
    ) : !beat || !view ? (
      <Placeholder title={`No ${scene} beats for this viewer`} />
    ) : (
      <Scene
        view={view}
        beat={beat}
        me={frame.me}
        presentation={frame.presentation}
        turn={frame.turn}
        room={frame.room}
        slot={slotInput}
        stop={stopInput}
        onSeek={(find) => {
          const i = frame.beats.findIndex(find);
          if (i >= 0) go({ beat: i });
          return i >= 0;
        }}
        onAct={logAct}
        onSay={logSay}
        onNext={
          frame.index < frame.beats.length - 1
            ? () => go({ beat: frame.index + 1 })
            : undefined
        }
      />
    );
    if (leaving && q.live && Scene && beat && view)
      stage = (
        <>
          {stage}
          <Layer name="hud">
            <LeaveConfirm
              hud="live"
              side={sideOpen(frame.presentation)}
              onStay={() => setLeaving(false)}
              onLeave={() => {
                console.info('[workbench] leave → /rooms');
                setLeaving(false);
              }}
            />
          </Layer>
        </>
      );
    controls = (
      <>
        <Select
          label="viewer"
          options={VIEWERS}
          value={viewerParam(q.viewer)}
          onChange={(v) => go({ viewer: parseViewer(v), beat: 0 })}
        />
        <BeatStepper
          index={frame.index}
          count={frame.beats.length}
          label={frame.situation?.label ?? (beat ? beat.label : '—')}
          anchor={beat ? anchorLine(beat) : 'no beats'}
          onChange={(i) => go({ beat: i })}
        />
        <Seg
          label="motion"
          options={['normal', 'fast'] as const}
          value={q.motion}
          onChange={(motion) => go({ motion })}
        />
        <Seg
          label="slot"
          options={['none', 'drawer', 'film'] as const}
          value={q.slot}
          onChange={(slot) => go({ slot })}
        />
        <Seg
          label="memory"
          options={['on', 'off', 'fields'] as const}
          value={q.memoryOff ? 'off' : q.memoryFields ? 'fields' : 'on'}
          onChange={(m) =>
            go({
              memoryOff: m === 'off' || undefined,
              memoryFields: m === 'fields' || undefined,
            })
          }
        />
        <Seg
          label="hud"
          options={['live', 'replay', 'none'] as const}
          value={q.hud}
          onChange={(hud) => go({ hud })}
        />
        <Seg
          label="animate"
          options={[
            { value: '0', label: 'at rest' },
            { value: '1', label: 'play' },
          ]}
          value={q.animate ? '1' : '0'}
          onChange={(v) => go({ animate: v === '1' })}
        />
      </>
    );
  }
  const frameControl = (
    <Seg<string>
      label="frame"
      options={FRAMES}
      // a WxH frame presses none of them
      value={q.frame?.id ?? 'fill'}
      onChange={(v) => go({ frame: parseFrame(v) })}
    />
  );

  return (
    <main className={styles.main}>
      {showStrip ? (
        <ControlStrip>
          {scenePicker}
          {controls}
          {frameControl}
          <UrlReadout url={`${pathname}?${params.toString().replace(/%3A/g, ':')}`} />
        </ControlStrip>
      ) : null}
      <div className={styles.stageArea}>
        {q.frame ? (
          <PhoneFrame frame={q.frame}>
            <Stage fit="contain">{stage}</Stage>
          </PhoneFrame>
        ) : (
          <Stage fit="contain">{stage}</Stage>
        )}
      </div>
    </main>
  );
}
