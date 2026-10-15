'use client';

/**
 * The score's one player for the page, and the React side of it: the viewer's choice of
 * music (kept on this device, `lib/storage` `musicPref`), the director that hears the first
 * press and the page hiding, and the hooks a page uses to say what plays. A page says what
 * plays under it with `useMusicBed`; a moment's one-shot goes through `playSting`.
 */
import { useEffect } from 'react';
import { create } from 'zustand';
import { musicPref } from '@/lib/storage';
import type { Bed } from './cues';
import { MusicPlayer } from './player';

let player: MusicPlayer | null = null;
/** The page's player, made on first use (never on the server). */
export const music = (): MusicPlayer => (player ??= new MusicPlayer());

type Pref = 'on' | 'off' | null;

interface MusicState {
  pref: Pref;
  /** The viewer has pressed something on the page, so the browser lets sound start. */
  pressed: boolean;
  choose: (pref: 'on' | 'off') => void;
}

export const useMusicState = create<MusicState>((set) => ({
  pref: null,
  pressed: false,
  choose: (pref) => {
    musicPref.set(pref);
    music().setPref(pref);
    set({ pref });
  },
}));

/** Whether music plays here for this viewer: a page's own (opt-in) or the game's (default). */
export const musicOn = (pref: Pref, optIn = false) =>
  optIn ? pref === 'on' : pref !== 'off';

/**
 * Mounted once, in the providers: reads the viewer's choice, unlocks sound on the first press
 * (and wakes it on any later one, as a phone may have suspended it), and stops the clock while
 * the page is hidden.
 */
export function MusicDirector() {
  useEffect(() => {
    const pref = musicPref.get();
    music().setPref(pref);
    useMusicState.setState({ pref });
    const onPress = () => {
      music().unlock();
      if (!useMusicState.getState().pressed) useMusicState.setState({ pressed: true });
    };
    const onVisibility = () => music().setVisible(document.visibilityState === 'visible');
    window.addEventListener('pointerdown', onPress, true);
    window.addEventListener('keydown', onPress, true);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('pointerdown', onPress, true);
      window.removeEventListener('keydown', onPress, true);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);
  return null;
}

/**
 * What plays under this page now; null is silence. Leaving the page fades it out. An inactive
 * caller (a preview) says nothing, so it never silences the page it sits in.
 */
export function useMusicBed(bed: Bed | null, active = true) {
  // a new object with the same key changes nothing (`setBed`), so this may run every render
  useEffect(() => {
    if (active) music().setBed(bed);
  }, [bed, active]);
  useEffect(() => {
    if (!active) return;
    const leave = music().enter();
    return () => {
      music().setBed(null);
      leave();
    };
  }, [active]);
}

/**
 * The stage's music: the bed under its beat, and a moment's one-shot when the beat plays as it
 * happens (`played`). A beat the stage jumped to (a refresh's landing, a seek, a chapter jump)
 * plays no one-shot and cuts one still sounding: it belonged to where the stage was.
 */
export function useStageMusic({
  bed,
  sting,
  beat,
  played,
  active = true,
}: {
  bed: Bed | null;
  sting: string | null;
  /** The beat on the stage, as a key that changes with every beat (its index and id). */
  beat: string | null;
  played: boolean;
  active?: boolean;
}) {
  useMusicBed(bed, active);
  useEffect(() => {
    if (!active || beat === null) return;
    if (!played) music().cutStings();
    else if (sting) music().sting(sting);
  }, [active, beat, played, sting]);
}
