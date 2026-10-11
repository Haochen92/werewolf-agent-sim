import { afterEach, describe, expect, it, vi } from 'vitest';
import { AGENT_WOULD_PASS, initialTurnState, turnReducer } from '../containers/live-state';
import { guessChoices, notebookForAgent, parseNotebook } from '../notebook';
import type { DockInput } from '../scenes/types';
import {
  DRAFT_WORDS,
  LINE_MAX,
  PREVIEW_MAX,
  cycleDraftWords,
  dockControls,
  draftRequest,
  draftsLeftText,
  previewText,
} from './turn-dock';

const dock = (over: Partial<DockInput> = {}): DockInput => ({
  text: '',
  notes: '',
  onDraft: () => {},
  draftsLeft: 3,
  ...over,
});

describe('the speaking turn’s composer: one Draft button', () => {
  it('asks the agent for its own line: Draft for an empty box, Redraft this once it holds one', () => {
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
      draftLabel: 'Redraft this',
    });
    const revise = dockControls(dock({ text: 'Seat 5 is odd.', notes: 'softer' }));
    expect(revise).toMatchObject({ draftLabel: 'Redraft this', line: 'Seat 5 is odd.' });
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

describe('the dock’s three plaques and the line’s preview (2026-10-01)', () => {
  it('reads Write your line with no line, Edit your line once there is one', () => {
    expect(dockControls(dock())).toMatchObject({
      writeLabel: 'Write your line',
      preview: null,
      canSend: false,
    });
    // white space alone is no line
    expect(dockControls(dock({ text: ' \n ' }))).toMatchObject({
      writeLabel: 'Write your line',
      preview: null,
      canSend: false,
    });
    expect(dockControls(dock({ text: 'Seat 5 is odd.' }))).toMatchObject({
      writeLabel: 'Edit your line',
      preview: 'Seat 5 is odd.',
      words: '4 words',
    });
  });

  it('makes Send live the moment the box holds text, open or closed, until it is on its way', () => {
    // the dock has no box: it is handed the composer's line, and Send follows it keystroke by keystroke
    expect(dockControls(dock({ text: 'S' })).canSend).toBe(true);
    expect(dockControls(dock({ text: 'Seat 5', drafting: true })).canSend).toBe(true);
    expect(dockControls(dock({ text: 'Seat 5', sending: true })).canSend).toBe(false);
    expect(dockControls(dock({ text: 'Seat 5', closed: true })).canSend).toBe(false);
    // over the cap the dock's Send waits as the composer's does, and the preview stays
    const over = dockControls(dock({ text: 'a '.repeat(371) }));
    expect(over).toMatchObject({ canSend: false, over: true, words: '371 words' });
    expect(over.preview).not.toBeNull();
  });

  it('previews the line on one line, cut at a word with an ellipsis', () => {
    expect(previewText('')).toBeNull();
    expect(previewText('  Seat 5 voted\n\nfirst,   and fast. ')).toBe(
      'Seat 5 voted first, and fast.',
    );
    const long = 'Seat five has been far too quiet today '.repeat(5);
    const cut = previewText(long)!;
    expect(cut.endsWith('…')).toBe(true);
    expect(cut.length).toBeLessThanOrEqual(PREVIEW_MAX + 1);
    // cut at the end of a word, with no space before the ellipsis
    expect(cut).toMatch(/\S…$/);
    expect(long.startsWith(cut.slice(0, -1))).toBe(true);
    expect(long.charAt(cut.length - 1)).toBe(' ');
    // one word longer than the cut is cut through
    expect(previewText('x'.repeat(200), 20)).toBe(`${'x'.repeat(20)}…`);
    // the dock's count is of the whole line, not the preview
    expect(dockControls(dock({ text: long })).words).toBe('40 words');
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

describe('the notebook’s role guess (2026-09-30)', () => {
  it('offers only the roles that could still be alive, with how many are left', () => {
    const cast = {
      villager: 3,
      healer: 1,
      investigator: 1,
      vigilante: 1,
      wolf: 2,
      serial_killer: 1,
    };
    // a wolf and the investigator have died (their roles were shown), and a seat with no role yet
    // (or a concealed body); the list reads in the role sheet's order
    expect(guessChoices(cast, ['wolf', 'investigator', null])).toEqual([
      { role: 'villager', left: 3 },
      { role: 'vigilante', left: 1 },
      { role: 'healer', left: 1 },
      { role: 'wolf', left: 1 },
      { role: 'serial_killer', left: 1 },
    ]);
  });

  it('keeps a guess in the notebook; an old notebook without one still reads', () => {
    expect(parseNotebook({ notes: { 5: 'quiet' }, suspect: 5, hinted: true })).toEqual({
      notes: { 5: 'quiet' },
      guesses: {},
      suspect: 5,
      hinted: true,
    });
    expect(
      parseNotebook({ notes: {}, guesses: { 3: 'wolf', 4: 'nonsense', x: 'wolf' } })
        .guesses,
    ).toEqual({ 3: 'wolf' });
  });

  it('folds the guess into that seat’s note for a draft; the request keeps its shape', () => {
    const book = {
      notes: { 3: 'pushed hard on day 2', 6: '  ' },
      guesses: { 3: 'wolf', 6: 'serial_killer', 7: 'healer' },
      suspect: 3,
    };
    expect(notebookForAgent(book, (n) => n === 7)).toEqual({
      seat_notes: {
        player_3: '(I think: wolf) pushed hard on day 2',
        player_6: '(I think: serial killer)',
      },
      suspect: 'player_3',
    });
  });
});

describe('the Draft button’s words while a draft is on its way', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('steps through its four words every 1.6 s, round and round, until stopped', () => {
    vi.useFakeTimers();
    const shown: string[] = [DRAFT_WORDS[0]];
    const stop = cycleDraftWords((i) => shown.push(DRAFT_WORDS[i]));
    vi.advanceTimersByTime(1599);
    expect(shown).toEqual(['Drafting…']);
    vi.advanceTimersByTime(1);
    expect(shown).toEqual(['Drafting…', 'Weighing the table…']);
    vi.advanceTimersByTime(1600 * 4);
    expect(shown).toEqual([
      'Drafting…',
      'Weighing the table…',
      'Finding the words…',
      'Reading the room…',
      'Drafting…',
      'Weighing the table…',
    ]);
    stop();
    vi.advanceTimersByTime(1600 * 3);
    expect(shown).toHaveLength(6);
  });
});

describe('the line’s length', () => {
  it('caps at 500, and counts once the line is within 100 of it', () => {
    expect(LINE_MAX).toBe(500);
    const at = (n: number) => dockControls(dock({ text: 'a'.repeat(n) }));
    expect(at(399)).toMatchObject({ count: null, canSend: true });
    expect(at(400)).toMatchObject({ count: '400 / 500', canSend: true });
    expect(at(412).count).toBe('412 / 500');
    expect(at(500)).toMatchObject({ count: '500 / 500', over: false, canSend: true });
    // a draft set from outside may run past what the box lets a hand type: Send waits
    expect(at(542)).toMatchObject({ count: '542 / 500', over: true, canSend: false });
  });
});
