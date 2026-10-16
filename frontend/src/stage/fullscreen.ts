/**
 * The whole screen, where the page may take it (a browser's fullscreen: Android's Chrome, a
 * computer, an iPad), and where it may not: Safari on an iPhone has no fullscreen for a page,
 * and its one way to the whole screen is the Home Screen (manifest.ts, `HomeScreenTip`). Where
 * Chrome can install the house, the stage offers that too, for the whole screen every time.
 */

/** `screen.orientation.lock` is not in every TypeScript DOM lib yet. */
type Lockable = ScreenOrientation & { lock?: (o: 'landscape') => Promise<void> };

/** An iPhone in its browser, not opened from the Home Screen (an iPad has fullscreen). */
export function homeScreenOnly(): boolean {
  const iphone = /iPhone|iPod/.test(navigator.userAgent);
  const standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true;
  return iphone && !standalone;
}

/** The page can take the whole screen itself. */
export function canFullscreen(): boolean {
  return (
    !!document.documentElement.requestFullscreen && document.fullscreenEnabled !== false
  );
}

/** A phone that can be told to turn (Android's Chrome): the stage plays sideways. */
export function canTurn(): boolean {
  return !!(screen.orientation as Lockable | undefined)?.lock;
}

/**
 * The whole screen, and on a touch screen the stage's sideways (the lock needs the whole screen
 * first). Both need a press on the page; refused, nothing changes.
 */
export function enterFullscreen(): Promise<void> {
  const orientation = screen.orientation as Lockable | undefined;
  return document.documentElement
    .requestFullscreen({ navigationUI: 'hide' })
    .then(() => {
      if (window.matchMedia('(pointer: coarse)').matches)
        return orientation?.lock?.('landscape');
    })
    .catch(() => {});
}

/** Chrome's own offer to install the house (`beforeinstallprompt`): Android's Chrome, a computer. */
interface InstallPrompt extends Event {
  prompt: () => Promise<void>;
}
let install: InstallPrompt | null = null;

/**
 * Keeps Chrome's install offer for the full-screen switch to make (`HomeScreenTip`), in place of
 * Chrome's own bar. Listened for from the first page (Providers): Chrome makes it once a page has
 * loaded, often before any stage is opened.
 */
export function keepInstallPrompt(): () => void {
  const keep = (e: Event) => {
    e.preventDefault();
    install = e as InstallPrompt;
  };
  const installed = () => {
    install = null;
  };
  window.addEventListener('beforeinstallprompt', keep);
  window.addEventListener('appinstalled', installed);
  return () => {
    window.removeEventListener('beforeinstallprompt', keep);
    window.removeEventListener('appinstalled', installed);
  };
}

/** Chrome will install the house if asked. */
export function canInstall(): boolean {
  return install !== null;
}

/** Chrome's install dialog (it may be shown once per offer). Needs a press on the page. */
export function promptInstall(): void {
  const offer = install;
  install = null;
  void offer?.prompt().catch(() => {});
}
