import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchPicture, hasArrived, markArrived } from './pictures';

/** An image whose decode the test settles by hand. */
class FakeImage {
  static made: FakeImage[] = [];
  decoding = '';
  src = '';
  settle!: (ok: boolean) => void;
  private done = new Promise<void>((resolve, reject) => {
    this.settle = (ok) => (ok ? resolve() : reject(new Error('bad picture')));
  });
  constructor() {
    FakeImage.made.push(this);
  }
  decode() {
    return this.done;
  }
}

afterEach(() => {
  vi.unstubAllGlobals();
  FakeImage.made = [];
});

describe('the puppet pictures a turn waits for', () => {
  it('fetches a picture once, however many turns ask for it, and remembers it arrived', async () => {
    vi.stubGlobal('Image', FakeImage);
    const a = fetchPicture('/one.webp');
    const b = fetchPicture('/one.webp');
    expect(FakeImage.made).toHaveLength(1);
    expect(hasArrived('/one.webp')).toBe(false);
    FakeImage.made[0].settle(true);
    await Promise.all([a, b]);
    expect(hasArrived('/one.webp')).toBe(true);
    // arrived: asking again fetches nothing
    await fetchPicture('/one.webp');
    expect(FakeImage.made).toHaveLength(1);
  });

  it('does not count a picture that failed, and asks again next time', async () => {
    vi.stubGlobal('Image', FakeImage);
    const a = fetchPicture('/two.webp');
    FakeImage.made[0].settle(false);
    await expect(a).rejects.toThrow();
    expect(hasArrived('/two.webp')).toBe(false);
    void fetchPicture('/two.webp').catch(() => {});
    expect(FakeImage.made).toHaveLength(2);
  });

  it('takes the decode-ahead’s word for a picture it decoded', () => {
    markArrived('/three.webp');
    expect(hasArrived('/three.webp')).toBe(true);
  });
});
