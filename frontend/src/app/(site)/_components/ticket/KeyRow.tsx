'use client';
/**
 * The ticket's "Your key" row: who pays for the agents, and the key field when it is needed.
 *
 * The house pays for a fixed number of games a day, so whether a key is needed is live state
 * (`GET /models`, see `house.ts`). While the house covers the chosen model the row says so and
 * keeps the field folded away behind "Use my own key instead"; when it does not, the field is
 * open and the ticket will not be punched without a key. A key remembered on this device opens
 * the field too, since it will be sent. (The mockup shows the key as always required, which
 * would turn away every visitor the house would have paid for.)
 *
 * The key's words follow the server: it is sent once with the create request, held in memory
 * for that game only, and lost only if the server restarts, after which the game waits for a
 * player to enter a key again (`POST /games/{id}/key`, the restart card).
 */
import { forwardRef, useState } from 'react';
import { Switch, TextInput } from '@mantine/core';
import { useRememberedKey } from '@/hooks/useRememberedKey';
import type { ModelsMenu } from '@/types/contracts';
import { Icon } from '@/components/site';
import { houseLine } from './house';
import type { TicketKind } from './TicketOffice';
import classes from './Ticket.module.css';

export const KEY_INPUT_ID = 'byok';

interface KeyRowProps {
  kind: TicketKind;
  menu: ModelsMenu | undefined;
  /** The menu failed to load: nobody can say who pays, so the field stays open. */
  menuFailed: boolean;
  model: string;
  /** The server needs a key for this model right now. */
  required: boolean;
  value: string;
  onChange: (key: string) => void;
  /** Set when the ticket was punched without a key it needed. */
  error: string | null;
}

export const KeyRow = forwardRef<HTMLInputElement, KeyRowProps>(function KeyRow(
  { kind, menu, menuFailed, model, required, value, onChange, error },
  ref,
) {
  const key = useRememberedKey(value, onChange);
  const [ownKey, setOwnKey] = useState(false);
  const open = required || ownKey || menuFailed || value !== '';
  const line = menu ? houseLine(menu, model) : '';

  return (
    <div className={classes.fld}>
      <div className={classes.lab}>
        {open ? <label htmlFor={KEY_INPUT_ID}>Your key</label> : <span>Your key</span>}
        <small>who pays for the agents</small>
      </div>
      <div className={classes.ctl}>
        {menu ? (
          <p className={classes.house} data-pays={required ? 'key' : 'house'}>
            <Icon name={required ? 'i-key' : 'i-ticket'} size={17} />
            <span>{line}</span>
          </p>
        ) : (
          <p className={classes.note}>
            {menuFailed
              ? 'The model list did not load, so nobody can say yet whether the house pays. A key is optional; the server will say if it needs one.'
              : 'Asking the house what it will pay for…'}
          </p>
        )}

        {open ? (
          <>
            <div className={classes.keyRow}>
              <TextInput
                ref={ref}
                id={KEY_INPUT_ID}
                type={key.masked ? 'text' : 'password'}
                value={key.shown}
                onChange={(e) => key.update(e.currentTarget.value)}
                onFocus={key.unmask}
                placeholder={required ? 'Paste an API key' : 'Paste an API key (optional)'}
                autoComplete="off"
                spellCheck={false}
                error={error}
                aria-required={required}
                classNames={{
                  root: classes.lineRoot,
                  input: `${classes.line} ${classes.keyInput}`,
                  error: classes.lineError,
                }}
              />
              {key.loadedFromStorage ? (
                <button
                  type="button"
                  className={classes.textButton}
                  onClick={key.clearSaved}
                >
                  Forget the saved key
                </button>
              ) : null}
            </div>
            <Switch
              size="sm"
              checked={key.remember}
              onChange={(e) => key.setRemember(e.currentTarget.checked)}
              label="Remember on this device"
              classNames={{
                root: classes.paperSwitch,
                track: classes.track,
                thumb: classes.thumb,
                label: classes.switchLabel,
              }}
            />
            {kind === 'room' ? (
              <p className={classes.note}>
                Your key runs every agent at this table; nobody who boards needs one.
              </p>
            ) : null}
            <p className={classes.note}>
              It is sent once, with the request that starts the game, and held in the
              server&rsquo;s memory for that game only: never written to disk or to the
              archive. Remembering it keeps it in this browser, nowhere else.
            </p>
            <p className={classes.note}>
              If the server restarts mid-game, the key is lost with it, and the game waits
              until {kind === 'solo' ? 'you enter it' : 'someone at the table enters a key'}{' '}
              again.
            </p>
            {!required && menu ? (
              <button
                type="button"
                className={classes.textButton}
                onClick={() => {
                  setOwnKey(false);
                  onChange('');
                }}
              >
                Let the house pay instead
              </button>
            ) : null}
          </>
        ) : (
          <button
            type="button"
            className={classes.textButton}
            onClick={() => setOwnKey(true)}
          >
            Use my own key instead
          </button>
        )}
      </div>
    </div>
  );
});
