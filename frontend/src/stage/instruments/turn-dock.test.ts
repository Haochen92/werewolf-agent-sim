import { describe, expect, it } from 'vitest';
import { AGENT_WOULD_PASS, initialTurnState, turnReducer } from '../containers/live-state';
import { notebookForAgent } from '../notebook';
import type { DockInput } from '../scenes/types';
import { dockControls, draftRequest, draftsLeftText } from './turn-dock';

const dock = (over: Partial<DockInput> = {}): DockInput => ({
  text: '',
  notes: '',
  onDraft: () => {},
  draftsLeft: 3,
  ...over,
});

describe('the speaking turn’s dock: one Draft button', () => {
  it('asks the agent for its own line: Draft for an empty box, Redraft once it holds one', () => {
    const c = dockControls(dock());
    expect(c).toMatchObject({ canDraft: true, notes: '', draftLabel: 'Draft' });
    expect(c.draftHint).toMatch(/the line it would say/);
    // an optional steer goes along (trimmed)
    const told = dockControls(dock({ notes: '  push on seat 5, they voted fast ' }));
    expect(told).toMatchObject({
      canDraft: true,
      notes: 'push on seat 5, they voted fast',
      draftLabel: 'Draft',
    });
    expect(told.draftHint).toMatch(/steered by what you told it/);
    // a line in the box: the same button redrafts, and a steer revises that line
    expect(dockControls(dock({ text: 'Seat 5 is odd.' }))).toMatchObject({
      draftLabel: 'Redraft',
    });
    const revise = dockControls(dock({ text: 'Seat 5 is odd.', notes: 'softer' }));
    expect(revise).toMatchObject({ draftLabel: 'Redraft', line: 'Seat 5 is odd.' });
    expect(revise.draftHint).toMatch(/revises the line in the box/);
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

  it('an empty draft means the agent would pass: the box keeps its line, and says so', () => {
    let t = turnReducer(initialTurnState, { type: 'open', seq: 201 });
    t = turnReducer(t, { type: 'text', text: 'my own line' });
    t = turnReducer(t, { type: 'drafting', seq: 201 });
    t = turnReducer(t, {
      type: 'drafted',
      seq: 201,
      draft: '',
      draftsLeft: 2,
      deadline: null,
    });
    expect(t).toMatchObject({
      text: 'my own line',
      draftsLeft: 2,
      error: AGENT_WOULD_PASS,
    });
    // a line the next time clears the note
    t = turnReducer(t, {
      type: 'drafted',
      seq: 201,
      draft: 'x',
      draftsLeft: 1,
      deadline: null,
    });
    expect(t).toMatchObject({ text: 'x', error: null });
  });
});

describe('“Use my seat notes”: the notebook goes with a draft only when ticked', () => {
  const book = { notes: { 5: '  jumped on 3’s slip  ', 8: '   ' }, suspect: 5 };

  it('is shown only when the notebook holds a note or a suspect', () => {
    expect(notebookForAgent(null)).toBeNull();
    expect(notebookForAgent({ notes: {}, suspect: null })).toBeNull();
    expect(notebookForAgent({ notes: { 4: '  ' }, suspect: null })).toBeNull();
    expect(dockControls(dock()).hasNotebook).toBe(false);
    const on = { shared: true, onShared: () => {} };
    expect(dockControls(dock({ notebook: on })).hasNotebook).toBe(true);
    // no draft helper, no box either
    expect(dockControls(dock({ notebook: on, onDraft: undefined })).hasNotebook).toBe(
      false,
    );
  });

  it('names seats as the agents do, and drops a dead seat’s suspect mark', () => {
    expect(notebookForAgent(book)).toEqual({
      seat_notes: { player_5: 'jumped on 3’s slip' },
      suspect: 'player_5',
    });
    expect(notebookForAgent(book, (n) => n === 5)).toEqual({
      seat_notes: { player_5: 'jumped on 3’s slip' },
      suspect: '',
    });
    const long = notebookForAgent({ notes: { 2: 'x'.repeat(600) }, suspect: null });
    expect(long?.seat_notes.player_2).toHaveLength(300); // the server's cap
  });

  it('ticked (the default) sends it; unticked sends nothing of it', () => {
    expect(initialTurnState.shareNotebook).toBe(true);
    const shared = notebookForAgent(book);
    expect(draftRequest(' softer ', ' Seat 5 is odd. ', shared, true)).toEqual({
      notes: 'softer',
      current: 'Seat 5 is odd.',
      seat_notes: { player_5: 'jumped on 3’s slip' },
      suspect: 'player_5',
    });
    expect(draftRequest('softer', 'Seat 5 is odd.', shared, false)).toEqual({
      notes: 'softer',
      current: 'Seat 5 is odd.',
    });
    let t = turnReducer(initialTurnState, { type: 'open', seq: 7 });
    t = turnReducer(t, { type: 'share-notebook', share: false });
    expect(t.shareNotebook).toBe(false);
    // a new turn starts ticked again
    expect(turnReducer(t, { type: 'open', seq: 8 }).shareNotebook).toBe(true);
  });
});
