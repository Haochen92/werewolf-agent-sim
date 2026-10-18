'use client';

/**
 * The tools, on a walnut board in the owner's material kit: a brass plate per tool, and the
 * tool shown on a paper card, working (your file on a seat, in the case file; the composer with canned
 * drafts; your role card by day and at night), with numbered coins saying how to use it. The
 * tray holds every card in one cell, so it is as tall as the tallest and a switch moves nothing.
 */
import type { ReactNode } from 'react';
import dynamic from 'next/dynamic';
import { ComposerDemo } from './ComposerDemo';
import { RoleCardDemo } from './RoleCardDemo';
import { useTabs } from './useTabs';
import guide from './Guide.module.css';
import classes from './ToolsTray.module.css';

// a recorded game's view: loaded with the case file's demos, after the page
const NotesDemo = dynamic(() => import('./ExhibitDemos').then((m) => m.NotesDemo), {
  ssr: false,
});

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
  const t = useTabs(['cards', 'agent', 'role'] as const);
  return (
    <div className={classes.tray}>
      <div className={classes.tabs} role="tablist" aria-label="Tools">
        <button {...t.tab('cards')}>Seat cards</button>
        <button {...t.tab('agent')}>Your agent</button>
        <button {...t.tab('role')}>Your card</button>
      </div>
      <div className={`${guide.stack} ${classes.cards}`}>
        <div className={classes.card} {...t.panel('cards')}>
          <Tool
            title="A file on every player"
            demo={<NotesDemo />}
            how={[
              ['Select a player\u2019s photo', 'their file opens: their claim, your guess'],
              ['A page for each day', 'their night, the vote, your own lines'],
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
        <div className={classes.card} {...t.panel('role')}>
          <Tool
            title="Your role card"
            demo={<RoleCardDemo shown={t.at === 'role'} />}
            how={[
              ['By day, select Your card', 'at the foot of the stage'],
              ['At night it stands on your table', 'select it to read it full size'],
              ['It says what you do at night', 'and how many uses you have left'],
            ]}
          />
        </div>
      </div>
    </div>
  );
}
