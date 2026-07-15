# Prompt caching — investigation log

**What this is.** The path to the caching decision: what we hoped to cache, what the measurements
said, and what we shipped vs. deferred. The destination — how caching works in the pipeline *today* —
is the companion [report.md](report.md); this log keeps the chronology and the bet that didn't pan out.

**Reading contract.** Sections are in time order (2026-06-06 analysis → 2026-06-08 measurement; distilled
2026-06-25; a 2026-07-13 postscript, §⑤, when a second consumer adopted the mechanism). Designs are shown
**as they were proposed**; the central hypothesis was *falsified* and is left in place rather than edited
away — the falsification is the point. Forward-pointers `(§N)` are navigation, not hindsight.

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
   [`../extraction/post_game/`](../extraction/post_game/report.md); what is unmeasured is the counterfactual
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

---

## ⑤ 2026-07-13 — a second consumer: the tell detector (mechanism verified; a determinism cost discovered)

A year-later postscript in log time, a month in calendar time: the tell-ledger workstream
(`../extraction/tell_extraction/`) built a **role-blind tell detector** — flash-lite, temp 0,
per (game, player, channel) — whose 9 per-player calls share a byte-identical
rules+transcript+checklist prefix (~5.5–8k tokens, clears the 4,096 floor; reuse count 9, well
past break-even). The forcing function was a billing correction: the detector's 60-game held-out
pass billed **$13 against a $1.50–2.50 estimate** (~$0.006/call at ~8k-token prompts), so the
prefix became worth caching. Built as `--cache` in
[`detector_probe.py`](../extraction/tell_extraction/scripts/detector_probe.py), reusing this
investigation's exact mechanism (`create_context_cache` → `cached_content`-bound model → delete
in a finally; per-(game, channel) cache units).

**Verified, two ways — one clean, one not:**

- **The mechanism fires cleanly at the new consumer.** A real game prefix (5,793 est. tokens)
  cached and referenced: `cache_read = 5,374` of 5,716 input tokens (**94%**), creation and
  deletion clean, fallback-to-uncached on any failure. The same probe's usage metadata also
  produced the missing half of the billing diagnosis: **1,051 reasoning tokens per call** at
  `thinking_level="low"` — the 1,024 thinking budget runs saturated and bills at output rates,
  which is where the $13 run's non-input cost lived. (Follow-up lever, not yet probed:
  `minimal` = 128-token budget, ~8× less reasoning spend, accuracy effect unmeasured.)
- **⭐The catch: cache-bound serving is not bit-deterministic at temp 0.** The uncached detector
  is exactly reproducible — byte-identical single-string prompts returned row-identical output
  across separate runs (Jaccard 1.00 over 179 rows, measured 2026-07-12). Under caching that
  guarantee dies twice over: cached-vs-uncached on the same game agrees at 0.82 (discussion
  1.00, vote 0.69 — the flicker concentrates in the channel with the most decision-boundary
  cases), and **two identical cached runs agree with each other at only 0.56 (vote) / 0.77
  (discussion)**. The cached serving path — not the prompt content — introduces run-to-run
  nondeterminism that temp 0 does not control. Mechanism unconfirmed (server-side
  batching/kernel differences for cache-referencing requests is the standard suspect); what is
  established is the measurement.

**Decision.** The flag ships **opt-in, default OFF**. For the tell detector the trade is real
and unresolved: caching cuts ~94% of prefix input cost but converts exactly-reproducible counts
into sampled counts — and bit-reproducibility is a documented guarantee of that workstream's
uncached configuration. Whether measurement runs adopt caching (accepting stochastic counts
that average out at lift's aggregation grain) or keep determinism and cut cost via the thinking
budget instead is deferred to the detector's golden round, where both variants can be scored on
the same cells. **Extraction is unaffected**: it runs at temp 1.0 and never claimed
determinism, so its live `cache_prefix=True` stands as-is.

*Catches, for the standing record: (a) "explicit caching works" (§③) and "explicit caching is
output-neutral" are different claims — this investigation verified the first and §③ already
flagged prompt-shape non-neutrality for extraction; the detector adds serving-path
non-determinism as a third, distinct effect. (b) A saturated thinking budget is invisible in
cost estimates built from input tokens — pull `output_token_details.reasoning` before quoting a
per-call price.*

### ⑤a Option-C probe (same day): the determinism story inverts, and cheap thinking fails on accuracy

The owner ordered the obvious follow-up: does **cached + `minimal` thinking** restore
determinism (the reasoning-variance hypothesis)? The full 2×2, two identical runs per cell,
same game, row Jaccard between them:

| | uncached | cached |
|---|---|---|
| **thinking = low** | **0.90–1.00** (and today's run 1 matched *yesterday's* run exactly) | 0.56–0.77 |
| **thinking = minimal** | 0.67 | 0.83 |

Two findings, both corrections to ⑤ as first written:

1. **Nothing is bit-deterministic — including the uncached baseline.** Yesterday's
   "temp-0 flash-lite is deterministic (Jaccard 1.00 over 179 rows)" was a real measurement but
   an overgeneralization from one lucky pair: today the same uncached+low config self-agrees at
   0.90 while *also* reproducing yesterday's rows exactly on one of the two runs. The honest
   model: the endpoint is **near-deterministic with occasional serving-side flips in every
   configuration**; caching *worsens* stability (0.56–0.83) rather than being the sole cause of
   instability. The serving-path hypothesis was half right.
2. **`minimal` thinking guts detection recall — Option C rejected on accuracy.** On the probe
   game's six golden cells, minimal-thinking variants scored **0 true-positive days vs the
   low-thinking baseline's 2** (consistent across cached/uncached and across repeat runs; they
   also emit ~30% fewer rows overall). N=6 is direction-grade, but 0-for-4 gold days in every
   minimal run is not a close call: the 1,051 saturated reasoning tokens are doing the
   detection work. The "biggest safe-looking lever" of ⑤ is not safe.

**Standing decisions after ⑤a:** the detector's measurement configuration stays
**uncached + low** (most stable, calibrated accuracy); `--cache` remains opt-in with its
stability cost now measured *relative to a non-deterministic baseline* (0.56–0.77 vs
0.90–1.00); and because no configuration reproduces exactly, the reproducibility guarantee
moves from the model to the artifact — **detected rows are stored outputs, goldens certify the
stored run, and re-runs are new samples**. (This was already the pipeline's shape — detections
are JSONL artifacts — so the correction costs nothing operationally.)

### ⑤b The accuracy-parity check flips the default (same day, owner-approved)

The owner drew the pragmatic conclusion of ⑤a: reproducibility was never load-bearing for
detection's consumers — lift and credit are aggregates, role-blindness makes the flicker
role-uncorrelated by construction, certification already binds to stored artifacts, and
**extraction took this exact trade when `cache_prefix=True` shipped**. That left one real gate:
does the cached configuration score the same against the golden? Decision rule pre-stated:
within a few points of the uncached union → cached becomes the standing config.

**Result — parity, marginally better.** Cached k=2 union over the 5 calibration games,
rescored on the same 40 golden cells: vote precision **0.83 vs 0.77** (same tp=10/fp=1, one
fewer day-slip), vote recall 77% = 77%, discussion **0.93/87% identical**. The run-to-run
flicker lives in cells the golden scores as noise in either configuration.

**Decision: the detector's standing config is CACHED + low thinking** (`--cache` default ON,
opt-out via `--no-cache`). Detection re-prices from ~$0.22 to roughly **$0.12–0.14/game**
(caching discounts input only; the ~1k reasoning tokens that do the detection remain), putting
the tell system's standing overhead near **$0.17–0.20/game**. Reproducibility-by-artifact
(goldens certify stored runs) stands unchanged — it was adopted for the uncached config too.
The one thing this does NOT change: the golden numbers themselves remain temp-golden-grade;
the owner's detector-blind adjudication still certifies, and should be run against a stored
CACHED run, since that is now the configuration being certified.

