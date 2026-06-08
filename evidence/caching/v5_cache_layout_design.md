# v5 prompt cache-layout design — measured

**Date:** 2026-06-08. **Status: DESIGN + measured probes. No production prompt changes.**
Follows up [cost_variance_claims_analysis.md](cost_variance_claims_analysis.md) (2026-06-06, which
was analysis-only). This note replaces the earlier theorizing with **measured** numbers from the live
game model and turns them into a finalized layout target for the v5 rebuild.

Probes (reproducible, colocated): [probe_implicit_cache.py](probe_implicit_cache.py),
[probe_explicit_cache.py](probe_explicit_cache.py), [probe_explicit_min.py](probe_explicit_min.py).
Run with `PYTHONPATH=. .venv/bin/python evidence/caching/<probe>.py`. Model = `gemini-3.1-flash-lite`,
backend = Vertex (project default, location `global`) — the exact game config.

---

## Measured facts (this is the whole decision)

| question | measured result |
|---|---|
| Does **implicit** caching fire? | **No.** 15,007-token *identical* prefix, sent 4× back-to-back, and again warmed + 20 s delay + 3 probes → `input_token_details.cache_read = 0` every single call. The field is wired correctly (it surfaces, reads 0). Matches the production finding (2/600 gens, 0.4%). |
| Does **explicit** caching fire? | **Yes, cleanly.** Created a `CachedContent` of 15,001 tok; a `generate_content` referencing it billed `cached_content_token_count = 15,001` of `prompt_token_count = 15,005`. |
| **Explicit-cache minimum** | **4,096 tokens** — API-enforced, verbatim: *"The cached content is of N tokens. The minimum token count to start caching is 4096."* (rejects every create below it). |
| Cached-token price | 10% of input (90% off), per Vertex docs for 2.5+ models. |

Published implicit minimums for context (ai.google.dev): 3.5 Flash 4,096; 3.1 Pro preview 4,096;
2.5 Flash/Pro 2,048; 3.x Flash-Lite **unpublished**. Moot here — implicit doesn't fire on Vertex for
this model regardless of size.

---

## Conclusion 1 — gameplay caching needs explicit PREFIX-CHECKPOINT caching + layout (c); worth it only at scale

The earlier discussion floated layout **(c)** — move all role-specific content behind the public
`day_channel` so the append-only transcript becomes a long shared prefix — as the big win. **The
measurement kills it for the current model/backend:**

- **Implicit caching** would be the only mechanism that could exploit a *growing* prefix, and it
  **does not fire**. Layout (c) caches nothing if there is no implicit cache.
- **Explicit caching** is billed: **creation at FULL input rate**, reads at 10% (90% off), storage
  ~$4.50/1M-tok/hr (negligible at our sizes/minutes). Break-even for a shared block of size B reused N
  times: `B + 0.1·N·B < N·B` ⟹ **N ≥ 2 reuses** (Google's rule-of-thumb: ~3–4 to be safe).

**Implicit is gone, but explicit CAN harvest the sequential day chat via PREFIX-CHECKPOINT caching.**
`cached_content` is a *reusable prefix*, not a static document: cache `[preamble+rules+summaries+
channel-so-far]` once (when it clears 4,096) and every LATER turn that day passes `cached_content=<that>`
+ appends only its new messages + role tail. The one cache is reused by all remaining turns of the day
(≫2) → wins, ~80–90% off the cached-prefix portion of mid/late-day turns.

- The **naive** "cache each exact channel state" loses: in sequential play each state is consumed by
  exactly ONE next speaker → 1 reuse → `100% create + 10% read = 110%` > just sending it. (This is the
  real meaning of "explicit doesn't fit sequential" — it's about reuse count, not dynamism.)
- The **checkpoint** scheme wins because the prefix is reused many times before the next checkpoint.

**This re-validates layout (c) — for explicit prefix caching, not implicit.** (c) is REQUIRED: role/
private/memory must be in the tail so the cached prefix is **role-agnostic** (one shared cache, not 13).
Conditions: (1) layout (c) (+ identity-late validation); (2) ≥4,096 floor → early-day turns uncached, the
win grows through the day; (3) per-game cache lifecycle in the harness (create at the 4,096 crossing,
reuse for the rest of the day, delete). Ballpark ~10–15% of game cost from day chat. **Worth it only if
Phase C runs many games** — otherwise the harness complexity + early-day gap aren't worth it. Today's
factory (commit 96c3055) makes (c) a one-line section-reorder when/if this is greenlit.

(The "role block → end of **system**" variant (b) is strictly weaker than (c) — it caps the shared prefix
at the role-agnostic system (~1.2k) and never reaches the channel, because the system message fully
precedes the human turn and ends in role-specific text. If gameplay caching is pursued, it must be (c).)
Night phase is a secondary candidate: the COMPLETED day channel is static and reused by all ~6–8 night
actors → clears the ≥2-reuse bar without checkpointing, if the prefix ≥4,096 and role is in the tail.

## Conclusion 2 — extraction IS the lever, via EXPLICIT caching (conditional on per-role extraction)

Why explicit caching was rejected before (Claim 2 of the prior analysis) — and why none of it applies
here:

| prior rejection (gameplay) | extraction |
|---|---|
| shared block ≈ 1.2k < bar | game transcript is 10k+ → **clears 4,096 easily** |
| ~13 caches, fan-out + TTL mgmt | **one** cache per game, reused for **every role** → no fan-out |
| ceiling ≤ $0.10/game | runs on **Pro** (expensive), transcript is the bulk of a ~30 KB prompt |

`ROLE_EXTRACTION_PROMPT` ([Agents/prompts/extraction.py:246](../../Agents/prompts/extraction.py#L246))
today opens *"You are a {role} analyst"* and weaves `{role}` throughout, with the shared
`{formatted_discussions}` transcript **below** it — so the transcript is not a clean prefix. Restructure:

```
[ static, role-agnostic game transcript + roster ]   <- cache this (≥4,096; create once per game)
─────────────────────────────────────────────────
[ "You are a {role} analyst…" + per-role instructions + extraction schema ]   <- per-role tail
```

Then per game: `client.caches.create(...)` once from the transcript, and each of the N role-extraction
calls passes `cached_content=<name>`. The transcript bills at 10% across all N perspectives; only the
small per-role tail + output pays full price.

**This changes the per-role-vs-single extraction decision for v5.** The naive cost of per-role
extraction is N× Pro calls; with the transcript cached, the marginal cost of each extra perspective is
just (role tail + output) at 10% on the shared transcript — making richer per-role extraction much
cheaper to justify.

**Preconditions:** (a) v5 adopts per-role extraction (today it lives only in
`scripts/extraction_model_comparison.py`; production runs the single `POSTGAME_EXTRACTION_PROMPT`, one
call/game → nothing to share). (b) the extraction prompt is restructured transcript-first /
perspective-last. Both are v5 items; extraction prompts are in the frozen set
(see `feedback-memory-pipeline-prompt-freeze`).

---

## v5 checklist

- [ ] **Re-measure implicit** at v5 model pin (run `probe_implicit_cache.py`). If a future flash-lite
      build enables implicit caching, layout (c) for gameplay reopens (one-line factory reorder).
- [ ] **Decide per-role extraction** for v5. If yes:
  - [ ] restructure `ROLE_EXTRACTION_PROMPT` transcript-first / perspective-last (output-validate — it's a real prompt change behind the freeze; do it as part of v5 generation).
  - [ ] wire `client.caches.create` once per game (TTL ≈ minutes, covers the N role calls) + pass `cached_content` through `create_chat_model` (it already forwards kwargs); delete the cache after.
  - [ ] confirm transcripts clear 4,096 (they do at 10k+; trivially true).
- [ ] **Gameplay caching decision (gated on Phase C game count):** if pursued → layout (c) (role/private/
      memory to tail) + identity-late output-validation + per-game prefix-checkpoint cache lifecycle
      (create at 4,096 crossing, reuse for the rest of the day, delete) + night-phase shared-day-channel cache.
      If NOT pursued → finalize day/night on quality/legibility only; (c) is a one-line factory reorder later.
- [ ] Report per-arm `cached_content_token_count` in cost accounting if explicit caching lands.
