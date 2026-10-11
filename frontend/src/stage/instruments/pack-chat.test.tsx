import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { PackChat, type PackChatProps } from './PackChat';

/** The chat at the seat's turn to talk, with the box as the container's turn state leaves it. */
const html = (input: Partial<NonNullable<PackChatProps['input']>>) =>
  renderToStaticMarkup(
    <PackChat
      entries={[]}
      you="player_3"
      mate="player_8"
      cast={[]}
      input={{ draft: 'Seat 1 tonight.', left: 0, onPass: () => {}, ...input }}
    />,
  );

/** How many of the box, "Say it" and "Pass" are shut. */
const shut = (out: string) => out.match(/disabled=""/g)?.length ?? 0;

describe('PackChat: your line to the pack', () => {
  it('is open with a draft and nothing sent', () => {
    const out = html({});
    expect(shut(out)).toBe(0);
    expect(out).not.toContain('role="alert"');
  });

  it('shuts the box and both buttons while the line is on its way or in', () => {
    expect(shut(html({ sent: true }))).toBe(3);
  });

  it('reopens on a failed send, with the words under the box', () => {
    const out = html({ sent: false, error: 'That line is too long.' });
    expect(shut(out)).toBe(0);
    expect(out).toMatch(/role="alert"[^>]*>That line is too long\./);
  });

  it('stays shut with the words when the turn was already answered', () => {
    const out = html({ sent: true, error: 'That turn was already answered.' });
    expect(shut(out)).toBe(3);
    expect(out).toContain('That turn was already answered.');
  });
});
