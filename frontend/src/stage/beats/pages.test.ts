import { describe, expect, it } from 'vitest';
import { PAGE_CHARS, pageHold, paginate, speechPages } from './pages';

describe('paginate', () => {
  it('keeps a short speech as one page', () => {
    expect(paginate('  I think seat 3 is\n lying.  ')).toEqual([
      'I think seat 3 is lying.',
    ]);
    expect(paginate('')).toEqual([]);
  });

  it('breaks at the last sentence end that fits', () => {
    const a = 'Seat 4 is gone.'; // 15
    const b = 'Seat 3 was the wolf, so look at who defended them.'; // 51
    const c = 'I say we start with seat 6.'; // 27
    expect(paginate(`${a} ${b} ${c}`, 70)).toEqual([`${a} ${b}`, c]);
    // a closing quote stays with its sentence
    expect(paginate('He said “trust me.” I do not. Nobody should.', 30)).toEqual([
      'He said “trust me.” I do not.',
      'Nobody should.',
    ]);
  });

  it('falls back to a clause break, then to a word', () => {
    const clause =
      'We lost our investigator last night, but the wolf is out and that is a start';
    expect(paginate(clause, 50)).toEqual([
      'We lost our investigator last night,',
      'but the wolf is out and that is a start',
    ]);
    const dash = 'Seat 2 kept quiet all day — and that is the tell I keep coming back to';
    expect(paginate(dash, 40)[0]).toBe('Seat 2 kept quiet all day —');
    const plain = 'one two three four five six seven eight nine ten eleven twelve';
    const pages = paginate(plain, 20);
    expect(pages).toEqual([
      'one two three four',
      'five six seven eight',
      'nine ten eleven',
      'twelve',
    ]);
  });

  it('splits one long sentence without ever cutting a word', () => {
    const long =
      'Since everyone abstained yesterday, looking at who seat 3 might have interacted with or how the night kills land could give us a thread to pull, and I would rather pull it now than wait for another body in the morning while the rest of us argue about nothing at all';
    const pages = paginate(long);
    expect(pages.length).toBeGreaterThan(1);
    for (const p of pages) expect(p.length).toBeLessThanOrEqual(PAGE_CHARS);
    expect(pages.join(' ')).toBe(long);
    const words = new Set(long.split(' '));
    for (const p of pages) for (const w of p.split(' ')) expect(words.has(w)).toBe(true);
  });

  it('gives a word longer than a page a page of its own', () => {
    expect(paginate('see https://example.com/a-very-long-address ok', 10)).toEqual([
      'see',
      'https://example.com/a-very-long-address',
      'ok',
    ]);
  });

  it('pages a speech as the box shows it, seat names rewritten', () => {
    expect(speechPages('player_3 is a wolf.')).toEqual(['Seat 3 is a wolf.']);
  });
});

describe('pageHold', () => {
  it('holds a page for its words at 2.4 a second (a reading pace), 5 to 15 s', () => {
    expect(pageHold('Yes.')).toBe(5000);
    expect(pageHold(Array(24).fill('word').join(' '))).toBe(10000);
    expect(pageHold(Array(60).fill('word').join(' '))).toBe(15000);
  });
});
