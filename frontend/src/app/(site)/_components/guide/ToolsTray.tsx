'use client';

/**
 * The tools, on a tray of the platform's boards: a brass plate per tool, and the tool shown on
 * a paper card, working (the seat card with its notes pinned open; the composer with canned
 * drafts), with three numbered coins saying how to use it. The tray holds both cards in one
 * cell, so it is as tall as the taller and a switch moves nothing; the card fits what it holds.
 */
import type { CSSProperties, ReactNode } from 'react';
import { SPRITES } from '@/assets/manifest';
import { ComposerDemo } from './ComposerDemo';
import { SeatCardsDemo } from './SeatCardsDemo';
import { useTabs } from './useTabs';
import guide from './Guide.module.css';
import classes from './ToolsTray.module.css';

const BOARDS = { '--boards': `url(${SPRITES.textures.boards.src})` } as CSSProperties;

function Tool({
  title,
  demo,
  how,
}: {
  title: string;
  demo: ReactNode;
  how: [ReactNode, string][];
}) {
  return (
    <div className={classes.tool}>
      <h3>{title}</h3>
      <div className={classes.demo}>{demo}</div>
      <ol className={classes.how}>
        {how.map(([step, gist], i) => (
          <li key={i}>
            <b>{step}</b>
            <span>{gist}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function ToolsTray() {
  const t = useTabs(['cards', 'agent'] as const);
  return (
    <div className={classes.tray} style={BOARDS}>
      <div className={classes.tabs} role="tablist" aria-label="Tools">
        <button {...t.tab('cards')}>Seat cards</button>
        <button {...t.tab('agent')}>Your agent</button>
      </div>
      <div className={`${guide.stack} ${classes.cards}`}>
        <div className={classes.card} {...t.panel('cards')}>
          <Tool
            title="Notes on every player"
            demo={<SeatCardsDemo />}
            how={[
              ['Select a player\u2019s card', 'write a note, or guess their role'],
              ['Your guess shows on their card', 'only you can see it'],
              [
                'Saved in this browser',
                'shared only with a draft, if Use my seat notes is ticked',
              ],
            ]}
          />
        </div>
        <div className={classes.card} {...t.panel('agent')}>
          <Tool
            title="Draft with your agent"
            demo={<ComposerDemo />}
            how={[
              ['Select Draft', 'leave Your agent blank, or say what you want'],
              ['Or write your own', 'then Redraft this to have it revised'],
              ['Edit, then Send', 'nothing is sent until you do; three drafts a turn'],
              [
                <>Tick &ldquo;Use my seat notes&rdquo;</>,
                'your notes go with the draft request',
              ],
            ]}
          />
        </div>
      </div>
    </div>
  );
}
