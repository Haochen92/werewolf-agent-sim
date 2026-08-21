'use client';

/**
 * The BYOK field, shared by `/play` and `/rooms/new` (build_plan P2 ruling).
 *
 * Remembering is PURELY client-side and needs zero server support: the server never stores
 * keys — BYOK games even die on restart for exactly that reason — so the key's only wire
 * appearance is the create-request body. Off by default, opt-in only, and when a saved key
 * loads it renders masked with its own clear button right there in the field.
 *
 * All of that is said in the UI, not just implemented. A key input that does not explain
 * itself is a key input people rightly refuse to use.
 */
import { useEffect, useState } from 'react';
import { byokKey } from '@/lib/storage';
import classes from './Lobby.module.css';

export function ByokField({
  value,
  onChange,
}: {
  value: string;
  onChange: (key: string) => void;
}) {
  const [remember, setRemember] = useState(false);
  const [loadedFromStorage, setLoadedFromStorage] = useState(false);

  // localStorage is client-only: read after mount so server and client markup agree.
  useEffect(() => {
    const saved = byokKey.get();
    if (saved) {
      onChange(saved);
      setRemember(true);
      setLoadedFromStorage(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (next: string) => {
    onChange(next);
    setLoadedFromStorage(false);
    if (remember && next) byokKey.set(next);
  };

  const masked = loadedFromStorage && value.length > 8;

  return (
    <div className={classes.group}>
      <label className={classes.label} htmlFor="byok">
        Your API key (optional)
      </label>
      <div className={classes.joinRow}>
        <input
          id="byok"
          className={classes.textInput}
          type={masked ? 'text' : 'password'}
          value={masked ? `${value.slice(0, 4)}••••••••${value.slice(-4)}` : value}
          onChange={(e) => update(e.target.value)}
          onFocus={() => setLoadedFromStorage(false)}
          placeholder="leave empty to use the house default"
          autoComplete="off"
          spellCheck={false}
        />
        {loadedFromStorage ? (
          <button
            type="button"
            className={classes.secondary}
            onClick={() => {
              byokKey.clear();
              onChange('');
              setRemember(false);
              setLoadedFromStorage(false);
            }}
          >
            clear saved key
          </button>
        ) : null}
      </div>

      <label className={classes.checkRow}>
        <input
          type="checkbox"
          checked={remember}
          onChange={(e) => {
            setRemember(e.target.checked);
            if (e.target.checked && value) byokKey.set(value);
            else byokKey.clear();
          }}
        />
        Remember on this device
      </label>

      <p className={classes.fine}>
        The key is sent once, with the request that starts the game, and is never stored on
        the server. Remembering it saves it in this browser only. Games started with your
        own key don’t survive a server restart — because the server kept nothing to restart
        them with.
      </p>
    </div>
  );
}
