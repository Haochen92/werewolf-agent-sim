> **Superseded record (May 2026).** Written 2026-05-24 and kept as it was, with its 2026-10-14 addendum
> at the end. The read path today, and this study beside the filter and reranker studies, are in the
> [retrieval report](../report.md), "The wider fetch: how many observations to show".
>
> - **Question.** With observations alone in the prompt, do more of them per situation help a small
>   model's decisions, or dilute them?
> - **Test.** 120 frozen decisions replayed with 3, 5 and 7 observations per situation from the v4_deduped
>   store (5.0, 7.6 and 9.8 a turn), each decision scored by one judge (Gemini 2.5 Flash).
> - **Answer.** Five scored slightly highest: action quality 4.40 against 4.33 (three) and 4.26 (seven);
>   strategy application 4.35 against 4.20 and 4.34. No significance test.
> - **What followed.** The "Decision" below was built on 2026-06-11 as a fetch of five with the cap of
>   three still after it, so live prompts kept about the three-per-situation condition (see the
>   addendum). Served games retrieve no observations.

---

# Retrieval Capacity Limits: Optimal Observation Count

## Motivation

With the decision to default to observations-only retrieval, the `top_k` retrieval cap — previously set at 3 to accommodate both observations and strategy points — can be revisited. Without strategy points consuming slots, agents can potentially benefit from more retrieved observations per situation. But more context isn't always better for a weak model at minimal thinking budget — there's likely a saturation point where additional observations dilute focus rather than add value.

## Design

Three-condition test using the application experiment's snapshot replay mode, all observations-only on the v4_deduped store:

- **Cap=3** — current default (avg 5.0 observations per turn across situations)
- **Cap=5** — moderate increase (avg 7.6 observations per turn)
- **Cap=7** — high density (avg 9.8 observations per turn)

Note: `top_k` applies per-situation, and agents have multiple situations per turn, so the actual observation count exceeds the cap value.

Dataset: 230 frozen cases from the v2 adoption eval set, sampled at n=120. Judge: `gemini-2.5-flash`.

## Results

Cap=5 produces the best action quality and strategy application, with cap=7 showing diminishing returns.

| Metric | Cap=3 | Cap=5 | Cap=7 |
|--------|-------|-------|-------|
| action_quality | 4.33 | **4.40** | 4.26 |
| strategy_application | 4.20 | **4.35** | 4.34 |
| grounding | 4.68 | 4.68 | 4.62 |

The improvement from cap=3 to cap=5 is small but consistent: +0.07 on action quality and +0.15 on strategy application, with no grounding regression. Cap=7 maintains the strategy application gain (4.34) but drops action quality back below cap=3 (4.26), suggesting ~10 observations per turn is where flash-lite starts losing focus.

## Decision

**Default `top_k` moves from 3 to 5 for observations-only retrieval.** The improvement is marginal but consistent with no downside. This is a configuration change — no code modification needed.

The tradeoff: slightly more tokens per agent call (~2 extra observations per situation). At flash-lite pricing this is negligible. The risk of cap=5 producing worse results than cap=3 is low given the consistent improvement across two metrics at n=120.

## Artifacts

| File | Description |
|------|-------------|
| `eval_configs/obs_cap_3.json` | Config: observations-only, top_k=3, n=120 |
| `eval_configs/obs_cap_5.json` | Config: observations-only, top_k=5, n=120 |
| `eval_configs/obs_cap_7.json` | Config: observations-only, top_k=7, n=120 |
| `eval_results/cap_3_n120.jsonl` | Results for cap=3 |
| `eval_results/cap_5_and_7_n120.jsonl` | Results for cap=5 and cap=7 (distinguished by `snapshot` field) |

*Addendum 2026-10-14: the decision above never reached the prompt.* The change was made on
2026-06-11 (`152cf1a9`) as the width of the fetch: retrieval asks the store for 5 items per
situation. But the per-situation cap (`RETRIEVAL_KEEP_PER_SITUATION = 3`, applied in
`Agents/memory/retrieval/pipeline.py` after retrieval) still runs on every turn. So a live prompt
gets at most 3 observations per situation, which is about the cap=3 condition measured here. The
cap=5 condition (about 7.6 observations a turn) was measured only in this replay, where no cap
followed the fetch. The wider fetch changes one thing: when two situations retrieve the same item
it is kept once, and the situation that lost it can refill from its 4th or 5th hit. Every
observation-on campaign since June (the paired A/B, v6, v7) therefore ran at an effective cap of 3.
The consequence is small, since the measured gain was +0.07 action quality at n=120 with no test of
significance, and the served game retrieves no observations at all. The comment above the fetch in
`pipeline.py` that calls 5 a "cap" is misleading for the same reason.
