/**
 * TanStack query-key factory. dota2pred lacked one and paid for it: keys were spelled
 * inline at each call site, so invalidation after a mutation silently missed half the
 * caches it meant to hit. Every key in the app comes from here.
 */
export const queryKeys = {
  replays: {
    all: ['replays'] as const,
    list: (params: { limit?: number; offset?: number } = {}) =>
      ['replays', 'list', params.limit ?? null, params.offset ?? null] as const,
    detail: (gameId: string) => ['replays', 'detail', gameId] as const,
  },
  games: {
    all: ['games'] as const,
    status: (gameId: string) => ['games', 'status', gameId] as const,
  },
  rooms: {
    all: ['rooms'] as const,
    list: () => ['rooms', 'list'] as const,
  },
  models: () => ['models'] as const,
} as const;
