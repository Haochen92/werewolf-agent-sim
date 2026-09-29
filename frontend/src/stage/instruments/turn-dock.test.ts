import { describe, expect, it } from 'vitest';
import { initialTurnState, turnReducer } from '../containers/live-state';
import type { DockInput } from '../scenes/types';
import { dockControls, draftsLeftText } from './turn-dock';

const dock = (over: Partial<DockInput> = {}): DockInput => ({
  text: '',
  notes: '',
  onDraft: () => {},
  draftsLeft: 3,
  ...over,
});

describe('the speaking turn’s dock: one Draft button', () => {
  it('drafts with the instructions empty: the agent writes a line of its own', () => {
    const c = dockControls(dock());
    expect(c).toMatchObject({ canDraft: true, notes: '', draftLabel: 'Draft' });
    expect(c.draftHint).toMatch(/of its own/);
    // with instructions, the same button drafts from them (trimmed)
    const told = dockControls(dock({ notes: '  push on seat 5, they voted fast ' }));
    expect(told).toMatchObject({
      canDraft: true,
      notes: 'push on seat 5, they voted fast',
    });
    expect(told.draftHint).toMatch(/what you told it/);
  });

  it('counts the drafts left, and stops at none, while drafting, or once the turn is over', () => {
    expect([3, 2, 1, 0].map(draftsLeftText)).toEqual([
      '3 drafts left',
      '2 drafts left',
      '1 draft left',
      '0 drafts left',
    ]);
    expect(dockControls(dock({ draftsLeft: 0 })).canDraft).toBe(false);
    expect(dockControls(dock({ drafting: true }))).toMatchObject({
      canDraft: false,
      draftLabel: 'Drafting…',
    });
    expect(dockControls(dock({ sending: true })).canDraft).toBe(false);
    expect(dockControls(dock({ closed: true })).canDraft).toBe(false);
    // no helper handed in: no draft row at all
    expect(dockControls(dock({ onDraft: undefined }))).toMatchObject({
      hasDraft: false,
      canDraft: false,
    });
  });

  it('sends whatever is in the box, drafted or typed; an empty box sends nothing', () => {
    expect(dockControls(dock()).canSend).toBe(false);
    expect(dockControls(dock({ text: '   ' })).canSend).toBe(false);
    expect(dockControls(dock({ text: ' my own line ' }))).toMatchObject({
      canSend: true,
      line: 'my own line',
    });
    expect(dockControls(dock({ text: 'x', sending: true })).canSend).toBe(false);
  });

  it('a free draft fills the box, where it stays editable, and counts down the drafts', () => {
    let t = turnReducer(initialTurnState, { type: 'open', seq: 201 });
    t = turnReducer(t, { type: 'drafting', seq: 201 });
    t = turnReducer(t, {
      type: 'drafted',
      seq: 201,
      draft: 'Why did seat 5 vote before anyone spoke?',
      draftsLeft: 2,
      deadline: null,
    });
    expect(t).toMatchObject({
      notes: '',
      text: 'Why did seat 5 vote before anyone spoke?',
    });
    t = turnReducer(t, { type: 'text', text: 'Why did seat 5 vote so fast?' });
    const c = dockControls(
      dock({ text: t.text, notes: t.notes, draftsLeft: t.draftsLeft }),
    );
    expect(c).toMatchObject({
      line: 'Why did seat 5 vote so fast?',
      canSend: true,
      canDraft: true,
    });
    expect(draftsLeftText(c.draftsLeft)).toBe('2 drafts left');
  });
});
