'use client';
/**
 * The ticket office (ticket-office mockup, review §A4): the form that starts a game, as a paper
 * ticket with a stub. It has two kinds, each on its own page (review §F4):
 *
 * - `solo` (`/play`): one seat against the agents, started on the spot. The player may choose
 *   their role. Punching the ticket calls `POST /games`, keeps the seat token that comes back
 *   (it is returned once, and a lost cookie has nothing else to rejoin with) and goes straight to
 *   `/games/[id]`, which opens on the deal.
 * - `room` (`/rooms/new`): a room others join. Rooms always deal at random, so there is no role
 *   choice. Punching calls `POST /rooms`, keeps the host key (returned once, the only proof of
 *   hosting) and goes to `/games/[id]`, where the host gives a name and waits for the others.
 *
 * Both send the model, the agents' memory (off by default) and the key. Whether a key is needed
 * is the house's call, per model (`KeyRow`, `house.ts`). The two hung tags at the top are doors
 * between the two pages. States: loading the menu, idle, a key missing (the ticket is held and
 * the key field says why), submitting (the button is busy), and a server refusal (an alert on
 * the stub); success is the redirect.
 *
 * Left out, because the wire has no field for them yet: the puppet picker (review §F5 rules it
 * a later step), the turn clock, watchers, and locking the room at creation (a locked room
 * admits nobody, the host included, so the host locks it from the room once everyone is in).
 */
import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Alert, Select, Switch, TextInput } from '@mantine/core';
import { createGame, createRoom, getModels } from '@/lib/api';
import { hostKey, seatToken } from '@/lib/storage';
import { queryKeys } from '@/lib/queryKeys';
import { Button, HangTag, Icon, Paper } from '@/components/site';
import { CARD_TEXT } from '@/stage/card-text';
import type { Role } from '@/types/contracts';
import { defaultRow, needsKey } from './house';
import { KeyRow } from './KeyRow';
import { RoleCards } from './RoleCards';
import classes from './Ticket.module.css';

export type TicketKind = 'solo' | 'room';

const COPY = {
  solo: {
    kicker: 'Admit one',
    heading: 'One seat, the rest agents',
    lede: 'No waiting: the cards are dealt as soon as you punch the ticket.',
    submit: 'Start the game',
    fine: 'Straight to the deal.',
    failed: 'The game could not be started',
  },
  room: {
    kicker: 'Admit a party',
    heading: 'Open a room',
    lede: 'You’ll give your name on the next page, then wait there with whoever boards.',
    submit: 'Open the room',
    fine: 'You’ll get a link to send. Seats and roles are dealt when you start the game.',
    failed: 'The room could not be opened',
  },
} as const;

// the places drawn on the room ticket: the table as the server deals it today (its
// MAX_HUMAN_SEATS). No room exists yet to ask; the room's own page shows the server's count.
const TABLE_PLACES = 9;

const KEY_NEEDED = 'Paste an API key: the house is not paying for this model right now.';

export function TicketOffice({ kind }: { kind: TicketKind }) {
  const router = useRouter();
  const copy = COPY[kind];
  const ids = useId();
  const [role, setRole] = useState<Role | null>(null);
  const [name, setName] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [memory, setMemory] = useState(false);
  const [keyError, setKeyError] = useState<string | null>(null);
  const keyInput = useRef<HTMLInputElement>(null);

  const models = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: 30_000, // the purse changes as games start; the menu itself is static
  });
  const menu = models.data;

  // The default is a live server setting: preselect it once the menu arrives, so the select
  // never shows a blank and the house line always describes a real row.
  useEffect(() => {
    if (!menu || model) return;
    const row = defaultRow(menu);
    if (row) setModel(row.model);
  }, [menu, model]);

  const required = needsKey(menu, model);
  const row = menu?.models.find((r) => r.model === model);

  const create = useMutation({
    mutationFn: async (): Promise<string> => {
      if (kind === 'solo') {
        const game = await createGame({
          human: true,
          human_role: role,
          api_key: apiKey,
          model,
          memory,
        });
        // The seat token comes back exactly once: stash it before navigating, or a cookie
        // loss later has nothing to rejoin with.
        if (game.seat_token) seatToken.set(game.game_id, game.seat_token);
        return game.game_id;
      }
      const room = await createRoom({ name: name.trim(), model, api_key: apiKey, memory });
      hostKey.set(room.game_id, room.host_key);
      return room.game_id;
    },
    onSuccess: (gameId) => router.push(`/games/${gameId}`),
  });

  const onKeyChange = (next: string) => {
    setApiKey(next);
    if (next.trim()) setKeyError(null);
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (create.isPending) return;
    if (required && !apiKey.trim()) {
      setKeyError(KEY_NEEDED);
      keyInput.current?.focus();
      return;
    }
    create.mutate();
  };

  const paidBy = required || apiKey.trim() ? 'Your key' : menu ? 'The house' : null;
  const roleLabel = role ? `${CARD_TEXT[role].name}, chosen` : 'Dealt at random';

  return (
    <main className={classes.office}>
      <div className={classes.intro}>
        <div>
          <h1 className={classes.title}>The ticket office</h1>
          <p className={classes.lede}>Choose a ticket, fill it in, and punch it.</p>
        </div>
        <nav className={classes.kinds} aria-label="Kind of game">
          <span className={classes.rail} aria-hidden="true" />
          <HangTag
            href="/play"
            current={kind === 'solo'}
            kicker="Admit one"
            title="Play solo"
            className={kind === 'solo' ? undefined : classes.otherDoor}
          >
            One seat at a table of agents.
          </HangTag>
          <HangTag
            href="/rooms/new"
            current={kind === 'room'}
            kicker="Admit a party"
            title="Play with others"
            className={kind === 'room' ? undefined : classes.otherDoor}
          >
            Open a room; anyone can board until you start.
          </HangTag>
        </nav>
      </div>

      <Paper
        component="form"
        className={classes.ticket}
        onSubmit={submit}
        noValidate
        aria-busy={create.isPending}
        aria-labelledby={`${ids}-heading`}
      >
        <div className={classes.body}>
          <h2 id={`${ids}-heading`} className={classes.heading}>
            {copy.heading}
          </h2>
          <p className={classes.ticketLede}>{copy.lede}</p>

          {kind === 'solo' ? (
            <div className={`${classes.fld} ${classes.wide}`}>
              <div className={classes.lab} id={`${ids}-role`}>
                Your role <small>optional; the table never knows you chose</small>
              </div>
              <div className={classes.ctl}>
                <RoleCards value={role} onChange={setRole} labelledBy={`${ids}-role`} />
              </div>
            </div>
          ) : (
            <>
              <div className={classes.fld}>
                <div className={classes.lab}>
                  <label htmlFor={`${ids}-name`}>Room name</label>
                  <small>shown on the rooms board</small>
                </div>
                <div className={classes.ctl}>
                  <TextInput
                    id={`${ids}-name`}
                    value={name}
                    onChange={(e) => setName(e.currentTarget.value)}
                    placeholder="Unnamed table"
                    maxLength={40}
                    autoComplete="off"
                    classNames={{
                      root: classes.lineRoot,
                      input: `${classes.line} ${classes.nameInput}`,
                    }}
                  />
                </div>
              </div>
              <div className={classes.fld}>
                <div className={classes.lab}>At the table</div>
                <div className={classes.ctl}>
                  <div className={classes.seats} aria-hidden="true">
                    {Array.from({ length: TABLE_PLACES }, (_, i) => (
                      <i key={i} data-first={i === 0 || undefined} />
                    ))}
                  </div>
                  <p className={classes.note}>
                    Anyone can board until you start the game; agents take every place still
                    empty when it starts.
                  </p>
                </div>
              </div>
            </>
          )}

          <div className={classes.fld}>
            <div className={classes.lab}>
              <span id={`${ids}-memory`}>Agents&rsquo; memory</span>
              <small>what the agents bring to the table</small>
            </div>
            <div className={classes.ctl}>
              <Switch
                checked={memory}
                onChange={(e) => setMemory(e.currentTarget.checked)}
                label={
                  memory ? 'On: lessons from past games' : 'Off: every agent plays fresh'
                }
                aria-labelledby={`${ids}-memory`}
                classNames={{
                  root: classes.paperSwitch,
                  track: classes.track,
                  thumb: classes.thumb,
                  label: classes.switchLabel,
                }}
              />
              <p className={classes.note}>
                {memory
                  ? 'From day 2, before each decision, the agents look up lessons from past games, and the replay’s X-ray shows which ones they weighed. One extra model call per agent decision.'
                  : 'Every agent plays from the rules and its role alone. Switch it on to have them consult lessons from past games; the replay’s X-ray then shows which ones they weighed.'}
              </p>
            </div>
          </div>

          <div className={classes.fld}>
            <div className={classes.lab}>
              <label htmlFor={`${ids}-model`}>Model</label>
              <small>what every agent runs on</small>
            </div>
            <div className={classes.ctl}>
              <Select
                id={`${ids}-model`}
                data={(menu?.models ?? []).map((r) => ({ value: r.model, label: r.label }))}
                value={model || null}
                onChange={(next) => next && setModel(next)}
                allowDeselect={false}
                disabled={!menu}
                placeholder={models.isError ? 'The server’s default' : 'Reading the menu…'}
                renderOption={({ option }) => {
                  const r = menu?.models.find((m) => m.model === option.value);
                  return (
                    <span className={classes.option}>
                      <span>{option.label}</span>
                      <span className={classes.optionMeta}>
                        <code>{option.value}</code>
                        {r ? ` · ${r.house_funded ? 'house pays' : 'your key'}` : ''}
                        {r?.is_default ? ' · default' : ''}
                      </span>
                    </span>
                  );
                }}
                classNames={{
                  root: classes.lineRoot,
                  input: `${classes.line} ${classes.selectInput}`,
                  section: classes.lineSection,
                }}
              />
              {row ? <code className={classes.rawId}>{row.model}</code> : null}
            </div>
          </div>

          <KeyRow
            ref={keyInput}
            kind={kind}
            menu={menu}
            menuFailed={models.isError}
            model={model}
            required={required}
            value={apiKey}
            onChange={onKeyChange}
            error={keyError}
          />

          {kind === 'room' ? (
            <div className={classes.fld}>
              <div className={classes.lab}>The room</div>
              <div className={classes.ctl}>
                <p className={classes.lockLine}>
                  <Icon name="i-lock-open" size={17} />
                  <span>
                    Opens unlocked: anyone on the rooms board, or with your link, can board.
                  </span>
                </p>
                <p className={classes.note}>
                  Once your party is aboard you can lock it from the room. A locked room
                  admits nobody, link or not, until you unlock it.
                </p>
              </div>
            </div>
          ) : null}
        </div>

        <div className={classes.stub}>
          <span className={classes.punch} aria-hidden="true" />
          <small className={classes.stubKicker}>{copy.kicker}</small>
          <div className={classes.stubTitle}>
            {kind === 'solo' ? 'Solo game' : name.trim() || 'Your room'}
          </div>
          <dl className={classes.terms}>
            <dt>At the table</dt>
            <dd>{kind === 'solo' ? 'You and 8 agents' : 'Up to 9 people'}</dd>
            {kind === 'solo' ? (
              <>
                <dt>Role</dt>
                <dd>{roleLabel}</dd>
              </>
            ) : null}
            <dt>Memory</dt>
            <dd>{memory ? 'On' : 'Off'}</dd>
            <dt>Model</dt>
            <dd>{row?.label ?? (models.isError ? 'Default' : '…')}</dd>
            {paidBy ? (
              <>
                <dt>Paid by</dt>
                <dd>{paidBy}</dd>
              </>
            ) : null}
            {kind === 'room' ? (
              <>
                <dt>Room</dt>
                <dd>Opens unlocked</dd>
              </>
            ) : null}
          </dl>

          <div className={classes.go}>
            {create.error ? (
              <Alert
                title={copy.failed}
                withCloseButton
                closeButtonLabel="Dismiss"
                onClose={() => create.reset()}
                icon={<Icon name="i-x" size={16} />}
                className={classes.alert}
              >
                {create.error.message || 'The server did not answer.'}
              </Alert>
            ) : null}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={create.isPending}
            >
              {copy.submit}
            </Button>
            <p className={classes.fine}>{copy.fine}</p>
          </div>
        </div>
      </Paper>
    </main>
  );
}
