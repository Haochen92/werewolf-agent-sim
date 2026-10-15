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
  [
    'Start a solo game',
    'Select Play solo. You take one seat; AI players take the other nine.',
  ],
  [
    'Choose your role and appearance',
    'Pick a role, or leave it to be dealt at random. Choose your puppet\u2019s appearance; it doesn\u2019t affect or reveal your role.',
  ],
  [
    <>
      Agents&rsquo; memory <em>experimental</em>
    </>,
    'Off by default: every AI player starts fresh. When it\u2019s available, switch it on and they bring lessons from past games.',
  ],
  [
    'Choose the model',
    'The AI model the players run on. Some are free to play, up to a daily limit; for the others, paste your own API key. Your key is used for this game only and never stored.',
  ],
];

const HOST: [ReactNode, string][] = [
  [
    'Open a room',
    'Name it if you like, choose Agents\u2019 memory and the model as for solo, then select Open the room.',
  ],
  [
    'Board',
    'Fill in the boarding pass with your name and puppet, then select Step onto the platform.',
  ],
  ['Invite', 'Send the room\u2019s link, or let people find it on the Rooms page.'],
  [
    'Depart',
    'Select Lock if you want no one else to join. Select Depart to start the game; AI players fill any empty seats.',
  ],
];

const JOIN: [ReactNode, string][] = [
  ['Open Rooms', 'The Rooms page lists every room still boarding.'],
  ['Pick a room', 'Select Board on an open room, or follow the link you were sent.'],
  [
    'Board',
    'Fill in the boarding pass with your name and puppet, then select Step onto the platform.',
  ],
  [
    'Wait for the host',
    'Seats and roles are dealt at random when the host selects Depart. If a room is full or locked, select Watch instead.',
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
            <p>Play with nine AI players. Your role decides who your teammates are.</p>
            <Button component={Link} href="/play" variant="plate">
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
                variant="plate"
                {...path.with('host')}
              >
                Open a room &rarr;
              </Button>
              <Button
                component={Link}
                href="/rooms"
                variant="plate"
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
