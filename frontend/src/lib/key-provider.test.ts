import { describe, expect, it } from 'vitest';
import { keyHint, keyProvider, keyRefusal, modelProvider } from './key-provider';
import { ApiError } from './request';

describe('keyProvider', () => {
  it('names the company only for a prefix that belongs to one', () => {
    expect(keyProvider('sk-ant-api03-abc')).toBe('anthropic');
    expect(keyProvider('  AIzaSyAbc')).toBe('google');
    expect(keyProvider('sk-proj-abc')).toBe('openai');
    expect(keyProvider('sk-svcacct-abc')).toBe('openai');
    expect(keyProvider('sk-admin-abc')).toBe('openai');
    // an old OpenAI key or a DeepSeek one: the server decides
    expect(keyProvider('sk-abc123')).toBeNull();
    expect(keyProvider('')).toBeNull();
  });
});

describe('modelProvider', () => {
  it('reads the id’s prefix, and bare ids are Google’s', () => {
    expect(modelProvider('anthropic/claude-haiku-5-5')).toBe('anthropic');
    expect(modelProvider('openai/gpt-6-luna')).toBe('openai');
    expect(modelProvider('deepseek/deepseek-v4-pro')).toBe('deepseek');
    expect(modelProvider('gemini-3.5-flash-lite')).toBe('google');
    expect(modelProvider('mistral/large')).toBeNull();
    expect(modelProvider('')).toBeNull();
  });
});

describe('keyHint', () => {
  const haiku = 'anthropic/claude-haiku-5-5';

  it('says whose key it is and whose the model needs, and that clearing it lets the house pay', () => {
    expect(keyHint('sk-proj-abc', haiku, 'Claude Haiku 5.5', true)).toEqual({
      lead: 'An OpenAI key. Claude Haiku 5.5 needs an Anthropic key',
      prefix: 'sk-ant-…',
      tail: 'Clear it and the house pays.',
    });
  });

  it('drops the house sentence when the house does not cover the model', () => {
    expect(
      keyHint('AIzaAbc', 'deepseek/deepseek-v4-pro', 'DeepSeek V4 Pro', false),
    ).toEqual({
      lead: 'A Google key. DeepSeek V4 Pro needs a DeepSeek key',
      prefix: 'sk-…',
      tail: null,
    });
  });

  it('stays quiet for a key that fits, an ambiguous key, or an unknown model', () => {
    expect(keyHint('sk-ant-abc', haiku, 'Claude Haiku 5.5', true)).toBeNull();
    expect(keyHint('sk-abc', haiku, 'Claude Haiku 5.5', true)).toBeNull();
    expect(keyHint('sk-ant-abc', '', 'This model', true)).toBeNull();
  });
});

describe('keyRefusal', () => {
  it('passes on the key check’s 422s in the provider’s words', () => {
    const refused = 'Anthropic refused this key: 401, invalid x-api-key.';
    expect(keyRefusal(new ApiError(422, refused))).toBe(refused);
    const late = 'OpenAI did not answer within 20 s. Try again.';
    expect(keyRefusal(new ApiError(422, late))).toBe(late);
  });

  it('leaves every other error to the alert', () => {
    expect(keyRefusal(new ApiError(422, 'model: unknown model'))).toBeNull();
    expect(keyRefusal(new ApiError(500, 'Anthropic refused this key: 401.'))).toBeNull();
    expect(keyRefusal(new Error('Anthropic refused this key: 401.'))).toBeNull();
    expect(keyRefusal(null)).toBeNull();
  });
});
