import type { BackdropSpec } from './set';

/** Small, in-memory crash context. Never retain the game view or player-written text. */
interface LiveFrame {
  gameId: string;
  beat: string | null;
  seq: number | null;
  slot: string | null;
  revealed: boolean;
  serverOver: boolean;
  fileTab: string;
  fileSeat: string | null;
}

let live: LiveFrame | null = null;
const backdrops: { at: number; spec: BackdropSpec | null }[] = [];
const KEEP = 16;

export function recordLiveFrame(frame: LiveFrame): void {
  if (live && live.gameId !== frame.gameId) backdrops.length = 0;
  live = { ...frame };
}

/** Includes withdrawals: the reported update loop was thrown in a backdrop cleanup. */
export function recordBackdrop(spec: BackdropSpec | null): void {
  backdrops.push({ at: Date.now(), spec: spec ? { ...spec } : null });
  if (backdrops.length > KEEP) backdrops.shift();
}

/** Copy before handing it to the reporter, so later renders cannot change the event. */
export function stageDiagnostics() {
  return {
    live: live ? { ...live } : null,
    backdrops: backdrops.map(({ at, spec }) => ({
      at,
      spec: spec ? { ...spec } : null,
    })),
  };
}
