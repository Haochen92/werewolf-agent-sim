'use client';

/**
 * The BYOK field on the restart card (`KeyNeededCard`). The ticket office (`/play`, `/play/room`)
 * draws its own key row over the same behaviour, `useRememberedKey`.
 *
 * Remembering is PURELY client-side and needs zero server support: the server never stores
 * keys — BYOK games even die on restart for exactly that reason — so the key's only wire
 * appearance is the create-request body. Off by default, opt-in only, and when a saved key
 * loads it renders masked with its own clear button right there in the field.
 *
 * All of that is said in the UI, not just implemented. A key input that does not explain
 * itself is a key input people rightly refuse to use.
 */
import { Switch } from '@mantine/core';
import { Button } from '@/components/site';
import { useRememberedKey } from '@/hooks/useRememberedKey';
import classes from './Lobby.module.css';

export function ByokField({
  value,
  onChange,
}: {
  value: string;
  onChange: (key: string) => void;
}) {
  // the restart card is not told the game's model: a lone saved key is offered
  const key = useRememberedKey(value, onChange, null);

  return (
    <div className={classes.group}>
      <label className={classes.label} htmlFor="byok">
        Your API key (optional)
      </label>
      <div className={classes.joinRow}>
        <input
          id="byok"
          className={classes.textInput}
          type={key.masked ? 'text' : 'password'}
          value={key.shown}
          onChange={(e) => key.update(e.target.value)}
          onFocus={key.unmask}
          onBlur={key.commit}
          placeholder="leave empty to use the house default"
          autoComplete="off"
          spellCheck={false}
        />
        {value ? (
          <Button type="button" variant="text" size="sm" onClick={key.clear}>
            {key.saved.some((s) => s.key === value)
              ? 'Delete the saved key'
              : 'Clear the key'}
          </Button>
        ) : null}
      </div>

      <Switch
        className={classes.checkRow}
        checked={key.remember}
        onChange={(e) => key.setRemember(e.currentTarget.checked)}
        label="Remember on this device"
      />

      <p className={classes.fine}>
        The key is sent once, with the request that starts the game, and held in the
        server’s memory for that game only. Remembering it saves it in this browser only.
        Games started with your own key don’t survive a server restart — because the server
        kept nothing to restart them with.
      </p>
    </div>
  );
}
