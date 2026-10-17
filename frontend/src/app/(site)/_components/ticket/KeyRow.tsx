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
 * A key whose prefix names another company than the model's gets a hint as it is typed
 * (`lib/key-provider`); it never holds the ticket, since the server checks the key with the
 * provider anyway, and a refusal from that check is shown here, under the field it is about.
 *
 * The key's words follow the server: it is sent once with the create request, held in memory
 * for that game only, and lost only if the server restarts, after which the game waits for a
 * player to enter a key again (`POST /games/{id}/key`, the restart card).
 */
import { forwardRef, useState } from 'react';
import { Switch, TextInput } from '@mantine/core';
import { useRememberedKey } from '@/hooks/useRememberedKey';
import type { ModelsMenu } from '@/types/contracts';
import { Button, Icon } from '@/components/site';
import { keyHint } from '@/lib/key-provider';
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
  /** The provider's words when the server's check refused the key. */
  refusal: string | null;
}

export const KeyRow = forwardRef<HTMLInputElement, KeyRowProps>(function KeyRow(
  { kind, menu, menuFailed, model, required, value, onChange, error, refusal },
  ref,
) {
  const key = useRememberedKey(value, onChange);
  const [ownKey, setOwnKey] = useState(false);
  const open = required || ownKey || menuFailed || value !== '';
  const line = menu ? houseLine(menu, model) : '';
  const row = menu?.models.find((r) => r.model === model);
  // what clearing the key would mean: the house runs this model right now
  const housePays = !!row?.house_funded && !required;
  const hint = keyHint(value, model, row?.label ?? 'This model', housePays);

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
                error={
                  error ??
                  (refusal ? (
                    <>
                      <span className={classes.refusal}>{refusal}</span>
                      <span className={classes.refusalHow}>
                        {housePays
                          ? 'Check the key and its credit, or clear it and the house pays.'
                          : 'Check the key and its credit.'}
                      </span>
                    </>
                  ) : null)
                }
                errorProps={refusal ? { role: 'alert' } : undefined}
                aria-required={required}
                classNames={{
                  root: classes.lineRoot,
                  input: `${classes.line} ${classes.keyInput}${hint ? ` ${classes.lineHint}` : ''}`,
                  error: classes.lineError,
                }}
              />
              {/* a hint's "Clear the key" forgets a saved key too (a wrong key kept would come
                  back on the next visit), so this button steps aside */}
              {key.loadedFromStorage && !hint ? (
                <Button
                  type="button"
                  variant="text"
                  size="sm"
                  className={classes.textButton}
                  onClick={key.clearSaved}
                >
                  Forget the saved key
                </Button>
              ) : null}
            </div>
            <div aria-live="polite">
              {hint ? (
                <div className={classes.keyHint}>
                  <p className={classes.keyHintLine}>
                    <Icon name="i-key" size={16} />
                    <span>
                      {hint.lead} (<code>{hint.prefix}</code>).
                      {hint.tail ? ` ${hint.tail}` : null}
                    </span>
                  </p>
                  <Button
                    type="button"
                    variant="text"
                    size="sm"
                    className={classes.hintButton}
                    onClick={key.clearSaved}
                  >
                    Clear the key
                  </Button>
                </div>
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
              <Button
                type="button"
                variant="text"
                size="sm"
                className={classes.textButton}
                onClick={() => {
                  setOwnKey(false);
                  onChange('');
                }}
              >
                Let the house pay instead
              </Button>
            ) : null}
          </>
        ) : (
          <Button
            type="button"
            variant="text"
            size="sm"
            className={classes.textButton}
            onClick={() => setOwnKey(true)}
          >
            Use my own key instead
          </Button>
        )}
      </div>
    </div>
  );
});
