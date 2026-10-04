"""Model admission: the gameplay checks a model passes before it joins the model menu.

Three tests, all short calls rather than games (``eval-model-admission``):

1. Structured output: every seat schema, several samples, under each calling mode the model's
   protocol allows (``Agents/llm_factory/backends.py`` STRUCTURED_MODES; Gemini has only its own).
2. Caching: the provider's smallest cacheable prompt, found by sending identical prompts of
   growing size twice; then real game prompts (the same seat's next turn, and another seat at the
   same moment) to see how much of an actual turn the provider serves from cache.
3. Calling mode: from 1, the mode the model should play on. When thinking is asked for, a mode
   that switches it off (DeepSeek's forced tool call) is not recommended over one that keeps it.

What these do not test is play quality: the hallucination bench (a two-sample-per-case arm, see
``evaluation/config/template/hallucination_bench_admission.json``) and then a real game do.
"""
