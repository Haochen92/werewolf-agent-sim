/**
 * Typed endpoint functions. Thin by design — the only thing they add over `request<T>()` is
 * that every URL string in the app is written exactly once, here.
 */
import { request } from './request';
import type {
  ActionKind,
  GameCreated,
  GameStatus,
  ModelsMenu,
  NewGame,
  NewRoom,
  ReplayGame,
  ReplaySummary,
  RoomCreated,
  RoomSummary,
  SeatJoined,
  TurnAccepted,
} from '@/types/contracts';

export interface ReplayListParams {
  limit?: number;
  offset?: number;
}

export function listReplays(params: ReplayListParams = {}): Promise<ReplaySummary[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set('limit', String(params.limit));
  if (params.offset !== undefined) query.set('offset', String(params.offset));
  const suffix = query.toString();
  return request<ReplaySummary[]>(`/replays${suffix ? `?${suffix}` : ''}`);
}

export function getReplay(gameId: string): Promise<ReplayGame> {
  return request<ReplayGame>(`/replays/${encodeURIComponent(gameId)}`);
}

export function getGameStatus(gameId: string): Promise<GameStatus> {
  return request<GameStatus>(`/games/${encodeURIComponent(gameId)}`);
}

export function listRooms(): Promise<RoomSummary[]> {
  return request<RoomSummary[]>('/rooms');
}

export function getModels(): Promise<ModelsMenu> {
  return request<ModelsMenu>('/models');
}

// --- games: create, join, rejoin, start, lock ------------------------------

/** Solo / instant-start door. Returns the seat token ONCE — stash it immediately. */
export function createGame(body: NewGame): Promise<GameCreated> {
  return request<GameCreated>('/games', { method: 'POST', body });
}

export function joinGame(gameId: string, name: string): Promise<SeatJoined> {
  return request<SeatJoined>(`/games/${encodeURIComponent(gameId)}/join`, {
    method: 'POST',
    body: { name },
  });
}

/** Re-prove seat ownership after cookie loss, using the localStorage copy of the token. */
export function rejoinGame(gameId: string, token: string): Promise<SeatJoined> {
  return request<SeatJoined>(`/games/${encodeURIComponent(gameId)}/rejoin`, {
    method: 'POST',
    body: { token },
  });
}

/** host_key rides as a QUERY parameter, not a body — the server's contract. */
export function startGame(gameId: string, hostKey?: string | null): Promise<unknown> {
  const query = hostKey ? `?host_key=${encodeURIComponent(hostKey)}` : '';
  return request(`/games/${encodeURIComponent(gameId)}/start${query}`, { method: 'POST' });
}

export function lockRoom(
  gameId: string,
  locked: boolean,
  hostKey: string,
): Promise<RoomSummary> {
  const query = `?host_key=${encodeURIComponent(hostKey)}&locked=${locked}`;
  return request<RoomSummary>(`/games/${encodeURIComponent(gameId)}/lock${query}`, {
    method: 'POST',
  });
}

export function createRoom(body: NewRoom): Promise<RoomCreated> {
  return request<RoomCreated>('/rooms', { method: 'POST', body });
}

// --- turns ------------------------------------------------------------------

/**
 * The turn payload shapes, taken from the engine's own contract
 * (`Agents/turn/human_turn.py::validate_human_response`) rather than guessed:
 *
 *   delegate       → `{delegate: true}` and NOTHING else. Legal in every phase.
 *   discuss        → `{message}` or `{pass_turn: true}` (pass needs the turn to be passable)
 *   wolf_discuss   → `{message}` only — wolf talk cannot be passed and takes no target
 *   every other kind → `{target}`, which must be one of the request's candidates
 */
export type TurnPayload =
  { delegate: true } | { pass_turn: true } | { message: string } | { target: string };

export function submitTurn(gameId: string, payload: TurnPayload): Promise<TurnAccepted> {
  return request<TurnAccepted>(`/games/${encodeURIComponent(gameId)}/turns`, {
    method: 'POST',
    body: payload,
  });
}

/** Which of the two dock shapes an action_kind takes (D17 — the list is closed at 8). */
export function isTextTurn(kind: ActionKind): boolean {
  return kind === 'discuss' || kind === 'wolf_discuss';
}
