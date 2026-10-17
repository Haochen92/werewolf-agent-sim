/**
 * Which company an API key and a model belong to, so the ticket office can say a key cannot
 * fit before anything is sent (a remembered OpenAI key once went out with house-paid Claude
 * Haiku and the game played on 401s). Only prefixes that name one company count: a plain
 * `sk-…` is an old OpenAI key or a DeepSeek one, and the server's own check decides.
 *
 * The model side mirrors the server's `provider_name` (Agents/llm_factory/chat.py): the id's
 * prefix before "/", bare ids (gemini-…) are Google's.
 */
import { ApiError } from './request';

export type Provider = 'anthropic' | 'openai' | 'deepseek' | 'google';

export const PROVIDERS: Record<
  Provider,
  { name: string; article: 'A' | 'An'; prefix: string }
> = {
  anthropic: { name: 'Anthropic', article: 'An', prefix: 'sk-ant-…' },
  openai: { name: 'OpenAI', article: 'An', prefix: 'sk-proj-…' },
  deepseek: { name: 'DeepSeek', article: 'A', prefix: 'sk-…' },
  google: { name: 'Google', article: 'A', prefix: 'AIza…' },
};

// most specific first: `sk-ant-` before any plain `sk-` rule could be added
const KEY_PREFIXES: [string, Provider][] = [
  ['sk-ant-', 'anthropic'],
  ['AIza', 'google'],
  ['sk-proj-', 'openai'],
  ['sk-svcacct-', 'openai'],
  ['sk-admin-', 'openai'],
];

/** The company a key's prefix names, or null when it names none for certain. */
export function keyProvider(key: string): Provider | null {
  const k = key.trim();
  return KEY_PREFIXES.find(([prefix]) => k.startsWith(prefix))?.[1] ?? null;
}

/** The company whose key a model id runs on; null for no model or an unknown prefix. */
export function modelProvider(model: string): Provider | null {
  if (!model) return null;
  const family = model.includes('/') ? model.split('/', 1)[0] : 'google';
  return family in PROVIDERS ? (family as Provider) : null;
}

export interface KeyHint {
  /** "An OpenAI key. Claude Haiku 5.5 needs an Anthropic key" */
  lead: string;
  /** the prefix the right key starts with, shown as code */
  prefix: string;
  /** "Clear it and the house pays.", only when the house covers this model */
  tail: string | null;
}

/** The hint for a key that cannot run the chosen model, or null when it may. */
export function keyHint(
  key: string,
  model: string,
  label: string,
  housePays: boolean,
): KeyHint | null {
  const has = keyProvider(key);
  const needs = modelProvider(model);
  if (!has || !needs || has === needs) return null;
  const want = PROVIDERS[needs];
  return {
    lead: `${PROVIDERS[has].article} ${PROVIDERS[has].name} key. ${label} needs ${want.article.toLowerCase()} ${want.name} key`,
    prefix: want.prefix,
    tail: housePays ? 'Clear it and the house pays.' : null,
  };
}

// the server's start-time key check (server/game/key_check.py): "<Provider> refused this key: …"
// or "<Provider> did not answer within 20 s. Try again."
const KEY_REFUSAL = /refused this key|did not answer within/;

/** The provider's words when a create request failed on the key check; null for any other error. */
export function keyRefusal(error: unknown): string | null {
  return error instanceof ApiError && error.isValidation && KEY_REFUSAL.test(error.message)
    ? error.message
    : null;
}
