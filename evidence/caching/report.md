# Prompt caching — how it works in the pipeline

**Orientation.** The live pipeline caches exactly **one** thing: the shared game-transcript prefix of
post-game extraction, via *explicit* Vertex context caching. Everything else — every in-game agent
turn — pays full input price, by deliberate decision. (A second, probe-stage consumer exists as of
2026-07-13: the tell detector caches its per-(game, channel) prefix **by default** — adopted after
a golden accuracy-parity check; see *Verification*, gap 0, and the log's §⑤a–⑤b.) This doc states what holds today and
why; the path that got here (what was hoped, measured, and dropped) is the companion
[experiment_log.md](experiment_log.md).

Companion code: extraction fan-out [`Agents/memory/extraction/extraction_agent.py`](../../Agents/memory/extraction/extraction_agent.py),
cache plumbing [`Agents/memory/extraction/prefix_cache.py`](../../Agents/memory/extraction/prefix_cache.py),
config [`Agents/memory/persistence/config.py`](../../Agents/memory/persistence/config.py).
Reproduction probes in [`scripts/`](scripts/).

---

## Guarantee (what holds today, and where it is enforced)

- **Post-game extraction is cached.** Extraction fans out over **11 (role × phase) cells** — villager
  contributes a day cell; the other five roles contribute a day and a night cell — and every cell's
  prompt opens with a **byte-identical, role-agnostic game-transcript prefix**
  (`build_cell_extraction_prefix`). That prefix is created **once per game** as a Vertex context cache
  (`create_prefix_cache`) and read by all 11 cells at the cached input rate (~10% of full price).
  Measured cache hit: **~97% cache_read** (`prefix_cache.py`).
- **It is on by default.** `ExtractionConfig.cache_prefix` defaults `True`
  ([`config.py:73`](../../Agents/memory/persistence/config.py#L73)); the live graph passes it through to
  the per-cell extractor ([`orchestrator.py:432`](../../Agents/nodes/orchestrator.py#L432)). The cache is
  deleted in a `finally` after the fan-out — no lingering storage.
- **In-game play is NOT cached.** Day and night agent turns send full-price input. No `cached_content`
  is wired anywhere in `Agents/nodes/`, `Agents/agents.py`, or `Agents/prompts/`. This is a decision,
  not an omission (see *Model* below).

The honest cost stance that falls out of this: **gameplay cost figures are full-price numbers.** There
is no hidden discount on the per-game spend to reason about.

---

## Model (why explicit, why only extraction)

**Two caching mechanisms exist; only one is usable here.**

- **Implicit caching** (the provider opportunistically reuses a hot prefix, zero harness work) **does
  not fire** on the game model/backend (`gemini-3.1-flash-lite`, Vertex) — measured, see *Verification*.
  So any layout trick that relies on it (e.g. moving variable content to the prompt tail so the stable
  head stays hot) buys nothing here.
- **Explicit caching** (you create a named `CachedContent` and reference it) **works cleanly**, but it
  is billed — **creation at full input rate, reads at ~10%**, plus negligible storage. So it only pays
  when a cached block is **reused ≥ 2 times**: break-even for a block of size `B` reused `N` times is
  `B + 0.1·N·B < N·B` ⟹ **N ≥ 2** (Google's rule of thumb is ~3–4 to be safe).

**That reuse-count test is the whole story of why extraction wins and gameplay loses:**

| | in-game turn | post-game extraction |
|---|---|---|
| shared prefix size | ~1.2k tok (system) — **below the 4,096 floor** | full transcript, **10k+ — clears 4,096 easily** |
| reuse count | each exact channel state is consumed by **one** next speaker → **1 reuse** → `100% create + 10% read = 110%`, worse than not caching | **one** transcript cache reused by **all 11 cells** → deep reuse |
| number of caches | ~13 (6 roles × discuss/vote + night + wolf + summary + judge) → fan-out + TTL churn | **one** per game → no fan-out |
| cost ceiling | shared prefix ≈ 35–40% of a ~3.2k turn → ≲ $0.10/game even at 90% off | extraction runs on **Pro** and the transcript is the bulk of a ~30 KB prompt → the cache covers the expensive part |

In-game play *could* be cached by a **prefix-checkpoint** scheme (cache the frozen prefix once it
crosses 4,096, reuse it for the rest of the day) — that clears the ≥2-reuse bar — but it needs a
per-day cache lifecycle in the harness and only starts paying mid/late-day. It is **deferred** (see
*Known gaps*), not impossible.

**Caches are model-specific** (the cached artifact is the model's per-layer KV state, meaningless to any
other weights — which is why the explicit API binds a model name at creation). This is *neutral-to-
positive* for the eval: caching can never create a cost or latency **asymmetry between model-comparison
arms** (every arm warms its own cache or pays full price uniformly), so it cannot bias a cross-model
A/B. If a future multi-model cost report is produced, carry the per-generation `input_cache_read` field
so per-arm cost is attributed honestly.

---

## Verification

Measured on the exact game config (`gemini-3.1-flash-lite`, Vertex, location `global`) with the
reproducible probes in [`scripts/`](scripts/):

| question | probe | measured result |
|---|---|---|
| Does **implicit** caching fire (flash-lite)? | [`probe_implicit_cache.py`](scripts/probe_implicit_cache.py) | **No.** A 15k-token identical prefix sent 4× back-to-back (and again warmed + 20 s + 3 probes) → `cache_read = 0` every call. The field is wired correctly (it surfaces, reads 0). Matches production: 2 / 600 recent generations, 0.4% of input. |
| Does **implicit** caching fire (2.5-flash)? | [`probe_implicit_25flash.py`](scripts/probe_implicit_25flash.py) | **Flaky/partial.** ~8.7k identical prefix → `cache_read = 4085` on ~2 of 11 calls, 0 otherwise; nothing at 1.7k / 2.7k / **5k**. So the 2,048 doc-minimum is necessary-not-sufficient and Vertex caches in ~4k blocks — not a reliable lever. |
| Does **explicit** caching fire? | [`probe_explicit_cache.py`](scripts/probe_explicit_cache.py) | **Yes, cleanly.** A `CachedContent` of 15,001 tok → a referencing call billed `cached_content_token_count = 15,001` of `prompt_token_count = 15,005`. |
| **Explicit-cache minimum?** | [`probe_explicit_min.py`](scripts/probe_explicit_min.py) | **4,096 tokens**, API-enforced verbatim: *"The minimum token count to start caching is 4096."* |

Live confirmation: the per-cell extractor runs with `cache_prefix=True` and reports **~97% cache_read**
across the 11-cell fan-out (`prefix_cache.py`).

**Added 2026-07-13 — a second consumer verified the mechanism and found a new cost.** The tell
detector ([`../extraction/tell_extraction/scripts/detector_probe.py`](../extraction/tell_extraction/scripts/detector_probe.py)
`--cache`, opt-in) caches its per-(game, channel) rules+transcript+checklist prefix (~5.5–8k tokens,
9 per-player reuses):

| question | measured result |
|---|---|
| Does the extraction mechanism transfer? | **Yes** — `cache_read = 5,374` of 5,716 input tokens (94%) on a real game prefix; create/reference/delete clean; uncached fallback on any failure. |
| Is cache-bound serving **bit-deterministic** at temp 0? | **No — and neither is anything else** (superseded same-day by the §⑤a matrix): uncached+low self-agrees at 0.90–1.00 (occasionally exact), cached+low at 0.56–0.77, cached+minimal 0.83, uncached+minimal 0.67. Caching *degrades* stability; it isn't the sole source. |
| Where did the detector's surprise cost live? | `output_token_details.reasoning` = **1,051 tokens/call** at `thinking_level="low"` (1,024 budget, saturated) — billed at output rates and invisible to input-only cost estimates. |

---

## Evidence — verdict, then forensics

**Verdict.** Of the caching levers explored, exactly **one shipped** and it is the high-value one:
explicit context caching of the extraction transcript, where one cache is reused across all 11 role/phase
cells of an expensive Pro call. Implicit caching is **dead** on this model/backend (so no prompt-layout
trick helps), and in-game caching is **deferred** because each channel state is reused only once — below
explicit caching's break-even. The most useful empirical fact the investigation produced is the negative
one: **implicit caching contributes ~0% today, so all gameplay cost planning assumes full-price input.**

**Forensics.** The forensic detail is the measured-facts table in *Verification* above plus the
reuse-count economics in *Model*. The two design conclusions that follow:
1. *Gameplay:* implicit is the only mechanism that could exploit a growing append-only channel, and it
   does not fire → the "move variable content to the tail" layout caches nothing today; explicit would
   need a checkpoint lifecycle and only pays at scale.
2. *Extraction:* the transcript is large (clears the floor), role-agnostic (one cache, no fan-out), and
   on the expensive model (Pro) — so caching it makes each *extra* per-role perspective nearly free
   (marginal cost ≈ the small per-role tail + output), which is what made richer per-cell extraction
   affordable.

---

## Known gaps (criticality-ordered; freshness 2026-06-25, gap 0 added 2026-07-13)

0. **No temp-0 configuration is bit-deterministic; caching makes it worse** (measured 2026-07-13,
   detector probe, full 2×2 in the log §⑤a). Identical-run row agreement: uncached+low **0.90–1.00**
   (occasionally exact — an early 1.00 was overgeneralized into a determinism claim, since
   corrected), cached+low 0.56–0.77, cached+minimal 0.83, uncached+minimal 0.67. The Option-C escape
   (cached + `minimal` thinking) was probed and **rejected on accuracy**: minimal-thinking variants
   scored 0 true-positive golden days vs the low-thinking baseline's 2 (N=6 cells,
   direction-grade) — the saturated ~1k reasoning tokens are doing the detection work. Severity:
   **medium, consumer-dependent** — irrelevant to extraction (temp 1.0, no determinism claim; live
   `cache_prefix=True` stands). Standing consequence for the detector (revised ⑤b, same day): the golden accuracy-parity
   check passed (cached union = 0.83/77% vote, 0.93/87% discussion vs 0.77/77%, 0.93/87%
   uncached), so the standing config is **cached + low** — the stability gap is real but scores
   as noise, and reproducibility lives in the stored detection artifacts (goldens certify a
   stored run, re-runs are new samples), not in the model.

1. **The extraction reorder's output-neutrality is unvalidated.** Caching requires a role-agnostic
   prefix, so the extraction prompt ships **transcript-first / perspective-last** rather than the older
   *"You are a {role} analyst…"*-first form. Whether that reorder changed extraction *quality* was never
   isolated in an A/B (deferred under the memory-pipeline prompt freeze). Severity: **medium** —
   likelihood is real (LLMs are order-sensitive) but impact is bounded: the *live* prompt's quality is
   separately characterized in [`../extraction/post_game/`](../extraction/post_game/report.md); what is
   unmeasured is the counterfactual (could perspective-first have scored higher?), i.e. the risk is
   leaving quality on the table, not unknown current quality. *What would change the verdict:* a
   transcript-first vs perspective-first A/B on the extraction judge basket.
2. **Implicit caching could return for a future model pin.** It is dead on today's flash-lite/Vertex,
   but a later build could enable it. Severity: **low** (detectable, cheap to recheck). *Mitigation:*
   re-run [`probe_implicit_cache.py`](scripts/probe_implicit_cache.py) at any model-pin change; if it
   fires, gameplay caching via a stable→volatile layout reopens for a near-zero-cost win.
3. **In-game caching is deferred, not implemented.** The per-turn intra-pipeline lever (the ~2–3
   memory-pipeline calls per turn share a fixed context) and the per-day prefix-checkpoint are both
   designed but unbuilt. Severity: **low** (a cost optimization, not a correctness issue). *Trigger to
   build:* Phase C game volume large enough that the harness complexity pays for itself.
4. **Currency: v5 per-role → v6 per-cell.** The original analysis (2026-06-06/08) reasoned about v5
   per-role extraction; the live path is now the v6 per-cell fan-out (11 cells). Severity: **low** — the
   cache lever carries forward unchanged: the neutral prefix is byte-identical across cells exactly as it
   was across roles, so the economics in *Model* hold as written.

---

## Provenance

- Investigation dates: 2026-06-06 (analysis) → 2026-06-08 (measurement). Consolidated 2026-06-25.
  Detector-consumer postscript (94% cache_read; determinism finding) measured 2026-07-13.
- Backend/model under test: `gemini-3.1-flash-lite`, Vertex, location `global` (the live game config).
- Probes: [`scripts/`](scripts/) (run `PYTHONPATH=. .venv/bin/python evidence/caching/scripts/<probe>.py`).
- Live enforcement: `ExtractionConfig.cache_prefix=True` (`config.py:73`) → `orchestrator.py:432` →
  `extract_postgame_per_cell` → `create_prefix_cache` (`prefix_cache.py`, ~97% cache_read).
