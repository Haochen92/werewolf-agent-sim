'use client';

/**
 * Game modes: solo, or with friends (host or join), each as four steps from the ticket to the
 * table, with the button that starts it.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import { Button } from '@/components/site';
import { useTabs } from './useTabs';
import guide from './Guide.module.css';
import classes from './GameModes.module.css';

const SOLO: [ReactNode, string][] = [
  ['Take the solo ticket', 'One seat is yours. The other nine are played by agents.'],
  [
    'Pick your cast',
    'Choose a role, or leave it and it’s dealt at random like everyone else’s. Choose the puppet you play as; it hints at no role.',
  ],
  [
    <>
      Agents&rsquo; memory <em>experimental</em>
    </>,
    'Switch it on and the agents bring lessons learned in past games to the table. It’s off by default.',
  ],
  [
    'Choose the model',
    'The model the agents run on. The house pays for some; for the others, paste your own API key. Your key is used for this game only and never stored.',
  ],
];

const HOST: [ReactNode, string][] = [
  [
    'Open a room',
    'Name it if you like. Choose the agents’ memory and the model, as for solo.',
  ],
  ['Board', 'Give your name and pick your puppet on the boarding pass.'],
  ['Invite', 'Send the room’s link, or let people find it in Rooms.'],
  [
    'Depart',
    'Lock the room if you want no one else to join, then press Depart. Agents take any empty places.',
  ],
];

const JOIN: [ReactNode, string][] = [
  ['Open Rooms', 'Every room still boarding is listed there.'],
  ['Pick a room', 'Choose an open one and press Board, or follow the link you were sent.'],
  ['Board', 'Give your name and pick your puppet.'],
  [
    'Wait for the host',
    'Seats and roles are dealt at random when the train departs. If the room is full, you can still watch.',
  ],
];

function Steps({ steps }: { steps: [ReactNode, string][] }) {
  return (
    <ol className={classes.steps}>
      {steps.map(([title, text], i) => (
        <li key={i}>
          <b>{title}</b>
          <span>{text}</span>
        </li>
      ))}
    </ol>
  );
}

export function GameModes() {
  const mode = useTabs(['solo', 'friends'] as const);
  const path = useTabs(['host', 'join'] as const);
  return (
    <>
      <div className={classes.tabs} role="tablist" aria-label="Game mode">
        <button {...mode.tab('solo')}>Solo</button>
        <button {...mode.tab('friends')}>With friends</button>
      </div>

      {/* every panel in one cell: the box is as tall as the tallest, so a switch moves nothing */}
      <div className={`${guide.stack} ${classes.modes}`}>
        <div className={classes.mode} {...mode.panel('solo')}>
          <div className={classes.head}>
            <p>You against nine agents.</p>
            <Button component={Link} href="/play" variant="primary">
              Play solo &rarr;
            </Button>
          </div>
          <Steps steps={SOLO} />
        </div>

        <div className={classes.mode} {...mode.panel('friends')}>
          <div className={classes.head}>
            <div className={classes.subtabs} role="tablist" aria-label="Host or join">
              <button {...path.tab('host')}>Host</button>
              <button {...path.tab('join')}>Join</button>
            </div>
            <p>Up to ten people at one table.</p>
            <span className={`${guide.stack} ${classes.go}`}>
              <Button
                component={Link}
                href="/rooms/new"
                variant="primary"
                {...path.with('host')}
              >
                Open a room &rarr;
              </Button>
              <Button
                component={Link}
                href="/rooms"
                variant="primary"
                {...path.with('join')}
              >
                Find a room &rarr;
              </Button>
            </span>
          </div>
          <div className={`${guide.stack} ${classes.paths}`}>
            <div className={classes.path} {...path.panel('host')}>
              <Steps steps={HOST} />
            </div>
            <div className={classes.path} {...path.panel('join')}>
              <Steps steps={JOIN} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
