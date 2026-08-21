/**
 * Typed endpoint functions. Thin by design — the only thing they add over `request<T>()` is
 * that every URL string in the app is written exactly once, here.
 */
import { request } from './request';
import type {
  GameStatus,
  ModelsMenu,
  ReplayGame,
  ReplaySummary,
  RoomSummary,
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
