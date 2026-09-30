import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { MemoryConsulted } from '@/types/contracts';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import OLD from './__fixtures__/old-situations.json';
import {
  asOf,
  ballotCut,
  fileFocus,
  fileTabs,
  firstSentence,
  marginNote,
  notePages,
  openTab,
  parseSituation,
  seatFile,
  shortForm,
  shownSeat,
  tickOf,
  when,
  wordDiff,
  type ExtractedLesson,
} from './case-file';

const beats = beatsFor(FIXTURE_EVENTS, { xray: true });
const whole = foldEvents(FIXTURE_EVENTS);
function at(id: SceneBeat['id'], pick: (b: SceneBeat) => boolean = () => true) {
  const beat = beats.find((b) => b.id === id && pick(b))!;
  return { beat, view: foldEvents(FIXTURE_EVENTS.slice(0, beat.end)) };
}
const consults = FIXTURE_EVENTS.filter(
  (e): e is MemoryConsulted => e.type === 'memory_consulted',
);
/** The same game with its memory taken out: a memory-off game. */
const NO_MEMORY = FIXTURE_EVENTS.filter(
  (e) => e.type !== 'memory_consulted' && e.type !== 'memory_extracted',
);

describe('whose file is open', () => {
  it('follows the speaker at a turn and the actor at a night spoke; the pack has both wolves', () => {
    const turn = at('day.speech', (b) => b.seq === 200);
    expect(fileFocus(turn.view, turn.beat)).toEqual({
      seats: ['player_8'],
      key: 'turn:200',
    });
    const spoke = at('rnight.spoke', (b) => b.day === 2 && b.seq === 126);
    expect(fileFocus(spoke.view, spoke.beat)?.seats).toEqual(['player_4']);
    const pack = at('rnight.spoke', (b) => b.day === 2 && b.seq === 140);
    expect(fileFocus(pack.view, pack.beat)).toEqual({
      seats: ['player_3', 'player_8'],
      key: 'night:2:pack',
    });
  });

  it('has no seat in focus at the count, the lynch, the morning, the night whole, the deal, the end', () => {
    for (const id of [
      'vote.chip-counted',
      'lynch.card-up',
      'morning.carried-summary',
      'rnight.whole',
      'deal.face-up',
      'over.curtain',
    ] as const) {
      const { view, beat } = at(id);
      expect(fileFocus(view, beat)).toBeNull();
    }
  });

  it('holds the viewer’s pick until a beat brings a different seat into focus', () => {
    const turn = { seats: ['player_8'], key: 'turn:200' };
    // no pick: the beat's own seat, or the docket
    expect(shownSeat(turn, null)).toBe('player_8');
    expect(shownSeat(null, null)).toBeNull();
    // picked at seat 8's turn: held there, and through the docket beats after it
    const pick = { seat: 'player_2', key: 'turn:200' };
    expect(shownSeat(turn, pick)).toBe('player_2');
    expect(shownSeat(null, pick)).toBe('player_2');
    // the next turn brings its speaker into focus
    expect(shownSeat({ seats: ['player_9'], key: 'turn:204' }, pick)).toBe('player_9');
    // picked at a docket beat, the docket included
    expect(shownSeat(null, { seat: null, key: null })).toBeNull();
    expect(shownSeat(turn, { seat: 'player_5', key: null })).toBe('player_8');
    // the pack's other wolf
    const pack = { seats: ['player_3', 'player_8'], key: 'night:2:pack' };
    expect(shownSeat(pack, null)).toBe('player_3');
    expect(shownSeat(pack, { seat: 'player_8', key: 'night:2:pack' })).toBe('player_8');
  });

  it('says where the playhead is', () => {
    expect(asOf(at('day.speech', (b) => b.seq === 200).beat)).toBe('Day 3 · discussion');
    expect(asOf(at('vote.chip-counted', (b) => b.day === 3).beat)).toBe('Day 3 · vote');
    expect(asOf(at('rnight.whole', (b) => b.day === 2).beat)).toBe('Night 2');
    expect(asOf(at('over.curtain').beat)).toBe('Game over');
  });
});

describe('the notes', () => {
  it('holds a page per note written by the beat, no later', () => {
    const { view } = at('day.speech', (b) => b.seq === 200);
    const pages = notePages(view, 'player_8');
    expect(pages).toHaveLength(8);
    expect(pages.every((p) => p.seq < 200)).toBe(true);
    // written in the night of day 1, then the vote of day 2
    expect(pages[0]).toMatchObject({ day: 1, phase: 'night' });
    expect(pages[3]).toMatchObject({ day: 2, phase: 'voting' });
  });

  it('pencils how each page came from the one before', () => {
    const pages = notePages(whole, 'player_2');
    expect(marginNote(pages, 0)).toBe('first page');
    expect(marginNote(pages, 1)).toBe(
      'edited from p. 1, added: “Since seat 1 survived a double attack, pay close…”',
    );
    expect(marginNote(pages, 2)).toBe('rewritten from scratch');
    expect(marginNote(pages, 10)).toBe(
      "edited from p. 10, added: “while deflecting attention to seat 7 and seat 8's…”",
    );
  });

  it('quotes at most nine added words, says so when only words were cut, and when nothing changed', () => {
    const a = { text: 'Stay quiet and vote with the village today.' };
    expect(marginNote([a, { text: 'Stay and vote with the village today.' }], 1)).toBe(
      'edited from p. 1',
    );
    expect(marginNote([a, a], 1)).toBe('unchanged from p. 1');
    expect(
      marginNote(
        [a, { text: 'Stay quiet and vote with the village today. Watch seat 4.' }],
        1,
      ),
    ).toBe('edited from p. 1, added: “Watch seat 4.”');
    expect(marginNote([a, { text: 'Push seat 4 hard, the lynch is ours.' }], 1)).toBe(
      'rewritten from scratch',
    );
    // the share kept is of the previous page's words
    expect(wordDiff('a b c d', 'a b x y z').kept).toBe(0.5);
  });
});

describe('the situation a precedent was written for', () => {
  it('splits a real situation at its labels, lead first', () => {
    const s = parseSituation(consults[0].lessons[0].situation);
    expect(s.lead).toBe(
      'Early game (Day 1-2) with a complete lack of verifiable evidence or night action results, creating a vacuum in village leadership.',
    );
    expect(s.facets.map((f) => f.key)).toEqual([
      'information',
      'stakes',
      'consensus',
      'position',
      'heat',
      'exposure',
      'targets',
      'public',
    ]);
    expect(s.facets.find((f) => f.key === 'position')?.value).toBe('with_majority');
    expect(s.facets.find((f) => f.key === 'heat')?.value).toBe(
      'None; neutrality ensures the agent is not a subject of interest.',
    );
  });

  it('reads every situation in the fixture into a lead and facets', () => {
    for (const c of consults)
      for (const l of c.lessons) {
        const s = parseSituation(l.situation);
        expect(s.lead.length).toBeGreaterThan(0);
        expect(s.facets.length).toBeGreaterThan(0);
        expect(s.facets.every((f) => f.value.length > 0)).toBe(true);
      }
  });

  it('reads the older stores’ labels too', () => {
    const [first, second] = OLD.old;
    const a = parseSituation(first);
    expect(a.lead).toBe(
      "The village's first vote is approaching with no prior voting records or eliminations.",
    );
    expect(a.facets.map((f) => [f.key, f.name])).toEqual([
      ['information', 'Information'],
      ['consensus', 'Consensus'],
      ['phase', 'Phase'],
    ]);
    expect(a.facets[2].value).toBe('Early mid-game, first elimination pending.');
    expect(parseSituation(second).facets.map((f) => f.key)).toEqual([
      'exposure',
      'information',
      'phase',
    ]);
  });

  it('keeps a situation with no labels whole', () => {
    expect(parseSituation('  The pack split its vote.  ')).toEqual({
      lead: 'The pack split its vote.',
      facets: [],
    });
  });

  it('shortens a facet to its first sentence, a value to its first clause', () => {
    expect(firstSentence('Low. Nobody looks at you. Keep it so.')).toBe('Low.');
    expect(firstSentence('no stop here')).toBe('no stop here');
    expect(shortForm('Negligible; you remain beneath the radar.')).toBe('Negligible');
    expect(shortForm('holding_out')).toBe('holding out');
  });
});

describe('the form’s ticks (a wrong tick misstates what the agent believed)', () => {
  it('ticks a box only when the value starts with its closed word', () => {
    expect(
      tickOf('heat', 'None; neutrality ensures the agent is not a subject of interest.'),
    ).toBe('None');
    expect(
      tickOf('heat', 'Low; by acting as a helpful and non-aggressive contributor'),
    ).toBe('Low');
    expect(tickOf('heat', 'low heat; the agent is currently aligned')).toBe('Low');
    expect(tickOf('heat', 'High due to direct accusation.')).toBe('High');
    expect(tickOf('position', 'with_majority')).toBe('With majority');
    expect(tickOf('position', 'holding out')).toBe('Holding out');
    expect(tickOf('position', 'driving')).toBe('Driving');
    expect(
      tickOf('information', 'Information-starved environment relying on behavioral reads.'),
    ).toBe('Starved');
    expect(
      tickOf('information', 'Information-rich: voting records and prior evidence'),
    ).toBe('Rich');
    expect(tickOf('information', OLD.old[0].split('Information landscape: ')[1])).toBe(
      'Starved',
    );
  });

  it('ticks nothing for a near word, a word inside the sentence, or a range', () => {
    // the bench's loose matching ticked these: not allowed
    expect(
      tickOf('heat', 'Minimal; you are blending in with the neutral majority.'),
    ).toBeNull();
    expect(tickOf('heat', 'Negligible; you remain beneath the radar')).toBeNull();
    expect(tickOf('heat', 'Maximum; you are the consensus target')).toBeNull();
    expect(tickOf('heat', 'Very low to low; maintained by high alignment')).toBeNull();
    expect(tickOf('heat', 'Critical; the village has a concrete lead')).toBeNull();
    expect(tickOf('position', 'with the majority')).toBeNull();
    expect(
      tickOf(
        'information',
        'The game environment is completely information-starved with no hard evidence.',
      ),
    ).toBeNull();
    expect(tickOf('information', 'info-starved; reliance on behavioral reads')).toBeNull();
    // a range names two boxes: neither is what the agent believed
    expect(tickOf('heat', 'Moderate to high; the healer is often suspected')).toBeNull();
    expect(tickOf('heat', 'Low to Moderate; the agent is protected')).toBeNull();
    expect(tickOf('heat', 'moderate-to-high')).toBeNull();
    expect(
      tickOf('information', 'information-starved to information-rich depending on results'),
    ).toBeNull();
  });
});

describe('one seat’s file', () => {
  it('holds a speaker’s notes, its latest reads against the truth, and its latest consult', () => {
    const { view } = at('day.speech', (b) => b.seq === 200);
    const f = seatFile(view, 'player_8', whole);
    expect(f.role).toBe('wolf');
    expect(f.pages).toHaveLength(8);
    expect(f.reads?.day).toBe(3);
    expect(f.reads?.rows.map((r) => [r.seat, r.suspected, r.sure, r.mark])).toEqual([
      ['player_1', 'villager', true, 'role'],
      ['player_2', 'villager', false, 'none'],
      ['player_5', 'unclear', false, 'none'],
      ['player_6', 'unclear', false, 'none'],
      ['player_7', 'unclear', false, 'none'],
      ['player_9', 'unclear', false, 'none'],
    ]);
    expect(f.consult).toMatchObject({ day: 3, phase: 'day_discussion' });
    expect(f.consult?.lessons.map((l) => l.verdict)).toEqual([
      'follow',
      'follow',
      'not_relevant',
    ]);
    // no findings before the game is over
    expect(f.findings).toBeNull();
    expect(fileTabs(f).map((t) => [t.id, t.count, t.enabled])).toEqual([
      ['notes', 8, true],
      ['reads', 6, true],
      ['precedents', 3, true],
    ]);
  });

  it('at a vote, holds what the voter voted on: its reads and its consult before the ballots', () => {
    const { beat, view } = at('vote.chip-counted', (b) => b.day === 2);
    const cut = ballotCut(view, beat);
    expect(cut).toBe(view.days[2].vote.ballots[0].seq);
    const f = seatFile(view, 'player_5', whole, cut);
    expect(f.reads).toMatchObject({ day: 2, phase: 'day_vote' });
    expect(f.consult).toMatchObject({ day: 2, phase: 'day_vote' });
    expect(when(f.consult!.day, f.consult!.phase)).toBe('Day 2 · vote');
    // the cut holds even when the log runs on past the night's reads and consults
    const later = at('morning.shutter-down', (b) => b.day === 2).view;
    const g = seatFile(later, 'player_4', whole, ballotCut(later, beat));
    expect(g.reads).toMatchObject({ day: 2, phase: 'day_vote' });
    expect(g.consult).toMatchObject({ day: 2, phase: 'day_vote' });
    expect(seatFile(later, 'player_4', whole).reads?.phase).toBe('night_action');
    // no cut away from the vote and the lynch
    expect(ballotCut(view, { scene: 'day', day: 2 })).toBeNull();
  });

  it('knows on day 1 that memory is on, from the log ahead, and greys Precedents until a consult', () => {
    const { view } = at('day.pass', (b) => b.seq === 15);
    const f = seatFile(view, 'player_1', whole);
    expect(f.memory).toBe(true);
    expect(fileTabs(f).find((t) => t.id === 'precedents')).toMatchObject({
      enabled: false,
    });
  });

  it('adds Findings after the game, per role: the role’s observations, from every seat', () => {
    const { view } = at('over.curtain');
    const f = seatFile(view, 'player_2', whole);
    expect(f.findings?.role).toBe('serial_killer');
    expect(f.findings?.observations).toHaveLength(9);
    expect(f.findings?.observations.every((o) => o.perspective === 'serial_killer')).toBe(
      true,
    );
    // served games extract no strategy points
    expect(f.findings?.lessons).toEqual([]);
    expect(fileTabs(f).at(-1)).toMatchObject({ id: 'findings', count: 9, enabled: true });
    // both wolves' files hold the same twelve: the wire files them by role
    expect(seatFile(view, 'player_3', whole).findings?.observations).toHaveLength(12);
    expect(seatFile(view, 'player_8', whole).findings?.observations).toHaveLength(12);
    // a game that kept lessons: the role's, from every seat that held it
    const points: ExtractedLesson[] = [
      { perspective: 'wolf', action_phase: 'night_action', situation: 'A', action: 'a' },
      {
        perspective: 'serial_killer',
        action_phase: 'day_vote',
        situation: 'B',
        action: 'b',
      },
    ];
    const kept: GameView = {
      ...whole,
      xray: {
        ...whole.xray,
        extracted: {
          ...whole.xray.extracted!,
          strategy_points: points,
        },
      },
    };
    expect(seatFile(view, 'player_8', kept).findings?.lessons).toEqual([points[0]]);
  });

  it('has only Notes and Reads in a memory-off game', () => {
    const beat = beatsFor(NO_MEMORY, { xray: true }).find((b) => b.id === 'over.curtain')!;
    const view = foldEvents(NO_MEMORY.slice(0, beat.end));
    const f = seatFile(view, 'player_2', foldEvents(NO_MEMORY));
    expect(fileTabs(f).map((t) => t.id)).toEqual(['notes', 'reads']);
  });

  it('opens the viewer’s tab where the file has it, else the notes', () => {
    const { view } = at('day.speech', (b) => b.seq === 200);
    const tabs = fileTabs(seatFile(view, 'player_8', whole));
    expect(openTab(tabs, 'precedents')).toBe('precedents');
    expect(openTab(tabs, 'findings')).toBe('notes');
    expect(openTab(tabs, 'note')).toBe('notes');
    const d1 = at('day.pass', (b) => b.seq === 15);
    expect(openTab(fileTabs(seatFile(d1.view, 'player_1', whole)), 'precedents')).toBe(
      'notes',
    );
  });
});
