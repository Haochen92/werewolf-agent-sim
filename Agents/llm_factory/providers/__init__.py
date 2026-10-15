"""One module per provider family: how its chat model is built for live calls (LangChain) and, where
it has them, its direct SDK calls for offline work (cached prefixes, batches, exact usage).

- ``google``: Gemini on Vertex or the Developer API, and Vertex's explicit prefix cache.
- ``anthropic``: Claude seats (LangChain) and direct calls: enforced or in-prompt schemas, cache
  marks, Message Batches, usage and cost.
- ``openai_compat``: the OpenAI protocol (NVIDIA NIM, DeepSeek, OpenAI, OpenRouter, xAI).
- ``mistral``: a thin client with an ``.invoke()``.
- ``common``: what more than one provider uses: the structured-output modes and their parsers.

The provider-neutral entries are ``Agents.llm_factory.chat`` (live, LangChain) and
``Agents.llm_factory.structured`` (offline).
"""
