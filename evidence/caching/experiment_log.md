# Prompt caching — investigation log

**What this is.** The path to the caching decision: what we hoped to cache, what the measurements
said, and what we shipped vs. deferred. The destination — how caching works in the pipeline *today* —
is the companion [report.md](report.md); this log keeps the chronology and the bet that didn't pan out.

**Reading contract.** Sections are in time order (2026-06-06 analysis → 2026-06-08 measurement; distilled
2026-06-25). Designs are shown **as they were proposed**; the central hypothesis was *falsified* and is
left in place rather than edited away — the falsification is the point. Forward-pointers `(§N)` are
navigation, not hindsight.

Sources: `cost_variance_claims_analysis.md` (2026-06-06, analysis-only) and `v5_cache_layout_design.md`
(2026-06-08, measured), now distilled into this log + `report.md`. Probes: [`scripts/`](scripts/). *(The
2026-06-06 analysis also audited four non-caching eval-cost levers — CUPED, bootstrap CIs, telemetry
density, pairing — which are out of scope here and move to [`../metrics/`](../metrics/).)*

---

## ① Motivation

The budget-constrained Phase C win-rate A/B runs many games at ~$0.3–0.4 each, and cost was building up.
Two places in the pipeline send a large, *recurring* prefix where caching could cut the bill:

1. **In-game agent turns**, especially day discussion — the public channel is **append-only**, so on
   every turn everything before the latest message is fixed. A textbook stable-prefix shape.
2. **Post-game extraction** — we wanted to make it **finer-grained** (one call *per role* instead of a
   single combined call) to get richer, less-diluted per-perspective signal. The worry was cost: per-role
   means N× calls on the expensive Pro model.

The free-lunch idea tying both together: **implicit caching** reuses a hot prefix at *zero* harness cost.
If we simply keep the variable content at the tail of each prompt, the fixed head is reused
automatically. This was a reasonable bet — it is exactly how implicit caching is documented to behave,
and the append-only channel is the ideal stable-prefix case.

---

## ② Design — two hypotheses

**Hypothesis A — gameplay, via implicit caching + a stable→volatile reorder ("layout (c)").**
Restructure every turn's prompt so the role-agnostic content leads and the per-agent content trails:
`[preamble → rules → frozen prior-days transcript → today's channel] ‖ [role → private → memory →
firing_brief → task]`. The leading block is shared across all 9 agents *and* grows append-only within a
day, so implicit caching reuses it turn-to-turn for free.
- *Alternative weighed and rejected:* "(b) role-block to the end of the **system** message" is strictly
  weaker — it caps the shared prefix at the ~1.2k-token system and never reaches the channel (the system
  message fully precedes the human turn and ends in role-specific text). If gameplay caching happens, it
  must be (c).
- *Alternative rejected up front:* explicit caching of each exact channel state — in sequential play each
  state is consumed by exactly one next speaker, so it would be reused once (see §③ for why that loses).

**Hypothesis B — make extraction finer without N× cost, via a cached transcript.**
Move from the single combined extraction call to per-role calls, but cache the shared game transcript so
each extra role pays only for its own small instruction tail, not a fresh copy of the transcript. If that
holds, "richer per-role extraction" stops being N× expensive.

---

## ③ Implement → Verify → Decide

### The load-bearing assumption first: does implicit caching even fire?

Hypothesis A rests entirely on implicit caching working on our model. Test that before building anything.

- **Probe — implicit on the game model** ([`probe_implicit_cache.py`](scripts/probe_implicit_cache.py)).
  *Catches:* whether implicit caching fires at all on `gemini-3.1-flash-lite` / Vertex. Send a 15k-token
  identical prefix 4× back-to-back; also warm it, wait 20 s, and probe 3×. **Result: dead — `cache_read =
  0` on every call.** The field is wired correctly (it surfaces, it reads zero). Cross-checked against
  production: **2 of 600** recent generations, 0.4% of input tokens.

  **Decision: Hypothesis A is falsified for this model/backend.** Layout (c) caches *nothing* if implicit
  never fires — the whole "free gameplay caching via reorder" plan collapses here. This was the central
  bet; it died at the first measurement.

- **Probe — implicit on 2.5-flash** ([`probe_implicit_25flash.py`](scripts/probe_implicit_25flash.py)).
  *Catches:* is implicit merely *flash-lite*-specific — would designing around it work on a friendlier
  model? **Result: flaky/partial** — `cache_read` fires on ~2 of 11 calls, only in ~4k blocks, and
  nothing at 1.7k / 2.7k / **5k**. So the documented 2,048 minimum is *necessary-not-sufficient*, Vertex
  caches in ~4k quanta, and real day-discuss prompts (~4.2–5.3k total, prefix below that) would rarely
  clear it before late-day. Conclusion: not a lever to design around even where it exists.

### Pivot: can explicit caching rescue either target?

Implicit is out. Re-enter design with the *explicit* mechanism (a named cache you create and reference).

- **Probe — explicit fires?** ([`probe_explicit_cache.py`](scripts/probe_explicit_cache.py)). *Catches:*
  whether explicit caching works on this model at all. **Result: yes, cleanly** — a 15,001-token cache,
  referenced, billed `cached_content_token_count = 15,001` of `prompt_token_count = 15,005`.
- **Probe — the entry bar** ([`probe_explicit_min.py`](scripts/probe_explicit_min.py)). *Catches:* the
  minimum cacheable size. **Result: 4,096 tokens**, API-enforced verbatim.

Explicit is billed (creation at full rate, reads at ~10%), so it only pays at **≥ 2 reuses**
(`B + 0.1·N·B < N·B`). Apply that to each target:

- **Gameplay (explicit): DEFER.** Caching each exact channel state loses — 1 reuse → `100% create + 10%
  read = 110%`, worse than just sending it. (This is the real meaning of "explicit doesn't fit sequential
  play" — it's the reuse count, not the dynamism.) A **prefix-checkpoint** scheme — cache the frozen
  prefix once it crosses 4,096, reuse it for the rest of the day — *would* clear the bar, but it needs a
  per-day cache lifecycle in the harness and only starts paying mid/late-day (early turns are sub-4,096).
  **Worth it only if Phase C runs many games**; deferred.
- **Extraction (explicit): SHIP.** The transcript is 10k+ (clears 4,096 trivially), **role-agnostic** (one
  cache reused by *every* role → no 13-cache fan-out), and on the expensive **Pro** model. So the
  transcript bills once at full rate and at ~10% thereafter, and each *extra* per-role perspective costs
  only its small tail + output. **This flips Hypothesis B's tradeoff: per-role extraction is no longer N×
  cost** — richer extraction becomes cheap to justify.

  **Build (problem → fix).** *Problem:* the extraction prompt opened `"You are a {role} analyst…"` with
  the transcript *below* it, so the transcript wasn't a clean shared prefix. *Fix:* restructure
  **transcript-first / perspective-last** so the cached block is role-agnostic; create the cache once per
  game, pass `cached_content` through, delete it after the fan-out. This shipped and is **live today** on
  the v6 per-cell fan-out — `cache_prefix=True` by default, ~97% cache_read (see `report.md`).

  **Caveat carried forward (deferred ≠ done).** The transcript-first reorder is a real output-affecting
  prompt change. Its **output-neutrality was not A/B'd** — it shipped because caching *requires* a
  role-agnostic prefix, not because reorder-neutrality was proven; the validation was deferred under the
  memory-pipeline prompt freeze (§④).

---

## ④ Limitations / future work (criticality-ordered; freshness 2026-06-25)

1. **Extraction reorder neutrality unvalidated** — the transcript-first reorder shipped without an A/B
   isolating its quality effect. The *live* prompt's quality is separately characterized in
   [`../extraction/quality/`](../extraction/quality/report.md); what is unmeasured is the counterfactual
   (could perspective-first have scored higher?). Resolve with a transcript-first vs perspective-first A/B
   on the extraction judge basket. (Full severity rationale: `report.md` gap #1.)
2. **Implicit caching may return at a future model pin** — dead on today's flash-lite/Vertex, but a later
   build could enable it. Re-run [`probe_implicit_cache.py`](scripts/probe_implicit_cache.py) at any pin
   change; if it fires, gameplay caching via layout (c) reopens for a near-free win.
3. **In-game caching deferred** — two designed-but-unbuilt levers: (a) **per-turn intra-pipeline** — the
   ~2–3 memory-pipeline calls per agent-turn (situation-summary → generation → novelty-gate) run on the
   *same* fixed game state; caching it once and reading 2–3× saves `90% − 100%/N` (N=3 → 57%), the
   cleanest case, but needs those call *types* to share a byte-identical leading block, which they don't
   yet; (b) **per-day prefix-checkpoint** (§③). Build when Phase C volume justifies the harness work.
4. **Day-summary A/B, enabled by caching** — once the transcript is cached, sending the *full verbatim*
   transcript is ≈ cost-neutral vs a summary, so the cost reason to summarize falls away → an affordable
   A/B "full transcript vs day-summary" on reasoning quality. Note the couplings before removing
   summaries: `summarize_day_discussion` emits the `DaySummaryCase` judge signal, and `day_summaries`
   feed extraction. Deferred.
5. **Currency: v5 per-role → v6 per-cell** — this investigation reasoned about v5 per-role extraction; the
   live path is now the v6 per-cell fan-out (11 cells). The lever carries forward unchanged: the neutral
   prefix is byte-identical across cells exactly as it was across roles.
