import { describe, expect, it } from 'vitest';
import { ApiError } from './request';

describe('a refused seat token', () => {
  it('is one the server will never take, not a failure that says nothing about it', () => {
    for (const status of [403, 404, 410])
      expect(new ApiError(status, '').refusesToken).toBe(true);
    // a server restarting, a proxy's 502, a conflict: the token may still be good
    for (const status of [0, 409, 500, 502, 503])
      expect(new ApiError(status, '').refusesToken).toBe(false);
  });
});
