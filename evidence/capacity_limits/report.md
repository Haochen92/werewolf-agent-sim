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
