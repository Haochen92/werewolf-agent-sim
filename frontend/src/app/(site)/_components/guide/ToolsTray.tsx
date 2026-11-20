'use client';

/**
 * The tools, on a walnut board in the owner's material kit: a brass plate per tool, and the
 * tool shown on a paper card, working (your file on a seat, in the case file; the composer with canned
 * drafts; your role card by day and at night), with numbered coins saying how to use it. The
 * seat cards' five steps are tabs, one shown at a time and each opening the file that shows it
 * (owner, 2026-10-22: five at once made the card twice the others' height). The tray holds
 * every card in one cell, so it is as tall as the tallest and a switch moves nothing.
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

/** The seat cards' steps: the coin's heading, what to know, and the seat whose file shows it. */
const FILE_STEPS: { head: string; text: string; seat: string }[] = [
  {
    head: 'Select a player\u2019s photo',
    text: 'Their file opens. The tabs along the top of the folder switch to another player.',
    seat: 'player_9',
  },
  {
    head: 'Your guesses, their claims',
    text: 'Pick the role they claim and the role you think they really are. Each day has a page: note what they say they did the night before, picked from the players\u2019 faces, and add lines of your own.',
    seat: 'player_9',
  },
  {
    head: 'Automatic fact checks',
    text: 'Some of it fills in by itself. Each day\u2019s votes come from the table, and a player who is out shows the role that was revealed. Each morning\u2019s Record, the folder\u2019s first tab, checks their claim: \u2713 on the record when it agrees with yours, the Record\u2019s version when it does not.',
    seat: 'player_9',
  },
  {
    head: 'Your own file',
    text: 'Your seat has a file too. Note the role you claim and what you said you did each night, so your story stays the same from one day to the next.',
    seat: 'player_1',
  },
  {
    head: 'Feeds your agent\u2019s drafts',
    text: 'Your notes stay in this browser. Tick Use my seat notes when you ask your agent for a draft, and they go with the request.',
    seat: 'player_9',
  },
];
const STEP_IDS = ['1', '2', '3', '4', '5'] as const;

/** The file on every player: its demo beside the steps, one coin at a time. */
function FileTool() {
  const s = useTabs(STEP_IDS);
  return (
    <div className={classes.tool}>
      <h3>A file on every player</h3>
      <div className={classes.demo}>
        <NotesDemo seat={FILE_STEPS[s.index].seat} />
      </div>
      <div className={classes.steps}>
        <div className={classes.coins} role="tablist" aria-label="Steps">
          {FILE_STEPS.map((step, i) => (
            <button key={i} {...s.tab(STEP_IDS[i])} aria-label={step.head}>
              {i + 1}
            </button>
          ))}
        </div>
        <div className={guide.stack}>
          {FILE_STEPS.map((step, i) => {
            const next = FILE_STEPS[i + 1];
            return (
              <div key={i} className={classes.step} {...s.panel(STEP_IDS[i])}>
                <b>{step.head}</b>
                <p>{step.text}</p>
                <button
                  type="button"
                  className={classes.next}
                  onClick={() => s.pick(STEP_IDS[next ? i + 1 : 0], true)}
                >
                  {next ? `Next: ${next.head} \u2192` : 'Back to the first step \u2192'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
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
          <FileTool />
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
