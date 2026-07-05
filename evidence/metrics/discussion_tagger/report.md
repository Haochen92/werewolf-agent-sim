# Discussion Tagger — how it works today

**Orientation.** The discussion tagger is one omniscient, end-of-day LLM pass that reads each player's day
discussion **and** night action and emits a per-player, de-lucked **merit verdict** — the piece of play that
no deterministic proxy can score. Despite the name it covers both channels; "discussion" is where it is
*irreplaceable*, because a vote-based proxy can already score night and town play. Its verdicts are consumed by
the v7 compounding loop's **credit** step — the only reason the loop can reward a wolf for talking its way out
of a corner even in a game the wolf lost. The tagger is **not a separate upstream stage**: the credit step
*invokes* it on demand (per game, cached) and then folds what it returns into the strategy-point ledger.

```
loop generation
    └─▶ credit step:  credit_apply ─▶ _tagger_ledger ─┐
                                                      │  (1) invokes the tagger per game (cached)
                                                      ▼
                         per-day tagger pass ─▶ {discussion verdict, night verdict} per player
                         (omniscient, one flash-lite call/day)
                                                      │  (2) _tagger_ledger folds the verdicts in
                                                      ▼
                         per-strategy-point de-luck ledger ─▶ consolidation
```

This is the write-up of the **current shipped mechanism and its design lineage**; the path that got here is
[experiment_log.md](experiment_log.md). How far the instrument is *trusted* — the validation apparatus and its
bounds — is owned by the companion apparatus report
[../../evaluation/discussion_tagger/report.md](../../evaluation/discussion_tagger/report.md); this doc points
at it rather than repeating it.

## What it produces (current schema)

One `DayTags` object per (game, day), each holding two lists
([discussion_tagger.py:51-80](../../../evaluation/src/loop/discussion_tagger.py#L51-L80)). The schema is
**all-required** — flash-lite silently drops optional/nullable fields, so every field is mandatory by design.

- **`TurnTag`** (one per player who spoke that day): a holistic **`verdict`** ∈ {positive, neutral, negative}
  — "weighing framing, credibility and any role-reveal, did this player's discussion *advance their own
  faction's win condition*, judged omnisciently and **independent of whether the vote or the game went their
  way**" — plus the detection lens the verdict weighs: **`framing`** ∈ {none, legitimate, manipulative},
  **`credibility`** ∈ {low, medium, high}, **`role_reveal`** ∈ {none, own_role_claim, challenge_claim}, and a
  one-line `why`.
- **`NightTag`** (one per player who acted that night): a **`verdict`** scoring the **read quality** of the
  target choice given the day's discussion — "a *skilled read* the discussion justified vs a *blind/lucky
  pick*" — plus **`read_quality`** ∈ {skilled, reasonable, blind_or_lucky, misread} and a `why`.

**Tag-fine, credit-coarse.** The `framing` / `credibility` / `role_reveal` / `read_quality` sub-tags are a
**detection lens**, consumed only by the offline validation runner. **Credit reads only the coarse `verdict`.**
This is deliberate: a per-dimension credit signal would spread thin and drift toward the halo the design fought
to avoid; one holistic verdict per turn keeps the reward legible.

## Guarantee / contract (present-tense)

- **Valence comes only from observable behavior + true roles; the agent's own reasoning is attribution-only.**
  Each agent's `updated_strategy` (its private in-game thinking) is fed in **only** to de-confound a night
  target (a discussion-driven read vs an obvious known-power-role removal), surface a read that was *formed but
  never voiced*, and trace influence — never to set merit, because LLMs confabulate self-serving accounts. This
  split is **enforced by the prompt, not by code** ([discussion_tagger.py:113-118](../../../evaluation/src/loop/discussion_tagger.py#L113-L118));
  it is a trust boundary, not a mechanical guard.
- **Only the holistic `verdict` feeds credit, at base 0.** `credit.py::_tagger_ledger` credits each followed
  strategy point by `verdict` alone, with a **base reward of 0** — the tagger is a *de-luck* signal, so a
  positive verdict is worth `+1 − base_rate`, never the game's win/loss
  ([credit.py:102-106](../../../evaluation/src/loop/credit.py#L102-L106)). The reward is *never* the game
  outcome (that is the halo).
- **Winner-blind on reasoning quality.** The tagger judges one day at a time on the information visible *at the
  time*: true roles let it *check* a read's conclusion, but a baseless accusation that merely lands on a real
  threat earns no credit, and a well-justified read that turns out wrong is still good reasoning
  ([discussion_tagger.py:96-102](../../../evaluation/src/loop/discussion_tagger.py#L96-L102)).
- **Role-reveal is anchored on structured extraction, not re-judged from chat.** `role_reveal` and the
  credibility of a claim key on the persisted day-summary `role_claims` (a claim whose declared role ≠ true
  role is a deception tell); a raw-message fallback covers pre-A4 records that lack the structured field.
- **Fails loud, not silent** (2026-07-02 hardening). A per-day LLM failure is collected and surfaced as an
  end-of-game `logger.error` counting degraded days (with a `strict` mode that re-raises); a missing
  eval-cases sidecar — which would silently empty `role_claims`/`private_reads` — warns once per game; and the
  per-game tag cache folds a **session/trace provenance slug** into its key and asserts it on read, re-tagging
  fresh on mismatch (this closed a real cross-arm collision that helped invalidate a paired run).
- **What is NOT guaranteed.** Per-field calibration (there is no human golden behind `framing`/`credibility`/
  `role_reveal`); a *memory* verdict (the validation is correlational, N=24, single-epoch — it validates the
  metric, not that wolf/SK memory compounds); the night verdict's residual outcome-leak (untested — see gaps);
  and the "flash-lite" property, which is **caller-injected, not intrinsic** (the tagger calls `get_llm_pro()`,
  whose bare default is `gemini-2.5-pro`; the loop env-pins it to flash-lite).

## The mechanism / model

- **Live entry point, and who calls whom.** `tag_game` / `tag_game_cached`
  ([discussion_tagger.py:228-351](../../../evaluation/src/loop/discussion_tagger.py#L228-L351)) is **invoked by
  its consumer**, not scheduled ahead of it: the credit step `credit.py::_tagger_ledger` lazy-imports and calls
  `tag_game_cached` per game ([credit.py:73-84](../../../evaluation/src/loop/credit.py#L73-L84)), so the tagger
  runs *inside* the credit stage, on demand and cached. `_tagger_ledger` is in turn called by `credit_apply`,
  which the loop driver runs once per generation as step 2 of 4 (generate → **credit** → consolidate → score;
  [driver.py:280-282](../../../evaluation/src/loop/driver.py#L280-L282)). So `_tagger_ledger` is downstream of
  the tagger's *verdicts* but upstream of it in *call order* — it both triggers the pass and folds the result.
- **Inputs assembled per day.** True roles + that day's public discussion (grouped from `day_channel`) are the
  **valence** inputs; the persisted `role_claims` anchor `role_reveal`; each agent's `updated_strategy` (as
  "private reads") and the night-target rationales are **attribution-only**; the day's vote result and night
  deaths are appended as an optional `outcome_block`.
- **Model + execution.** `get_llm_pro()`, env-pinned to `gemini-3.1-flash-lite` by the loop
  ([config.py:110-118](../../../evaluation/src/loop/config.py#L110-L118)); one LLM call per day, run in parallel
  across a game's days (`ThreadPoolExecutor`, `max_workers=8`); `.with_structured_output(DayTags)`. Tags are
  **cached immutably per `game_id`** with a versioned, provenance-slugged key (`version="v2"`), so the driver's
  rolling-window recompute re-reads tags rather than re-paying for them.
- **Two credit tiers, selected by `discussion_mode`.** This is the load-bearing wiring:

  | Tier | `discussion_mode` | Discussion credit | Night credit | Cost |
  |---|---|---|---|---|
  | **Free ("floor")** | `floor` | day-vote **endpoint** (`_discussion_ledger` → `_vote_credit`, faction-relative lynch outcome) | deterministic `_night_credit` (outcome-luck) | $0, no LLM |
  | **Paid ("tagger")** | `tagger` *(default)* | tagger **holistic verdict** (`_tagger_ledger`) | tagger **read-quality verdict** — *overrides* the deterministic night credit | flash-lite, 1 call/day |

  Under `tagger` mode the night ledger **overrides** the deterministic night credit (a de-lucked read beats
  outcome-luck) and the discussion ledger **adds** the day-discussion channel that the deterministic substrate
  leaves blank ([credit.py:124-128](../../../evaluation/src/loop/credit.py#L124-L128)). The free floor exists
  because discussion has no *clean per-decision* deterministic proxy — the vote endpoint is the best zero-cost
  approximation, and the paid tagger must **beat** it to earn its keep.

## Config / defaults

| Setting | Value | Where |
|---|---|---|
| discussion credit on | `discussion_credit = True` | config.py:101 |
| credit source | `discussion_mode = "tagger"` (paid); `"floor"` = free vote-endpoint fallback | config.py:108 |
| tagger model | `get_llm_pro()` env-pinned to `gemini-3.1-flash-lite` (temp 1.0, **not** 0) | config.py:110-118 |
| show outcome to tagger | `show_outcome = True` (vote result + deaths shown; leak measured negligible) | discussion_tagger.py:204 |
| skip silent players | `speakers_only = True` | discussion_tagger.py:205 |
| tag cache version | `v2` (bump on prompt change); keyed per `game_id` + provenance slug | discussion_tagger.py:318 |
| credit window | rolling `window_generations = 3` | config.py |

The blinded path (`show_outcome=False`, the `_CLAUSE_NO_OUTCOME` prompt variant) is **research-only** — the
live loop never blinds; only the validation runner's `skill`/`deleak` modes exercise it.

## Verification

**Verdict: 🟡 a validated deceiver-skill *metric*, not a memory *verdict*.** The instrument measures what it
claims — a de-lucked discussion merit signal the vote proxy is blind to — and survived an adversarial review
that shrank its claim three times. But it is correlational, single-epoch (N=24), and uncalibrated at the
per-field level. The full L1/L2 write-up is
[../../evaluation/discussion_tagger/report.md](../../evaluation/discussion_tagger/report.md); the load-bearing
results:

- **The holistic verdict predicts the win *beyond* the vote proxy, and it is real skill — not leak, not
  wordiness.** Partial *r*(discussion verdict, faction **won** | de-luck proxy, message verbosity) = **+0.56
  wolf / +0.60 SK / +0.02 town**, N=24, with the tagger **blinded to the outcome** and verbosity partialled
  out ([../../v7_final/v2_full/tagger_skill_retest.py](../../v7_final/v2_full/tagger_skill_retest.py)). The
  town row (+0.02) is the negative control: town discussion merit is already captured by its vote endpoint, so
  the tagger adds nothing there — exactly as intended.
- **Outcome-leak is negligible.** A 2×2 ablation (outcome shown/withheld × all/speakers-only, N=6) moved the
  discussion-verdict coupling by **+0.07 town / ~0 wolf-SK** when the vote result and deaths were withheld —
  within noise ([../../v7_final/v2_full/tagger_deleak_ablation.py](../../v7_final/v2_full/tagger_deleak_ablation.py)).
  So the tagger keeps *showing* the outcome by default; blinding bought a within-noise gain at the cost of the
  night verdict's legitimate lynch context.
- **The night verdict reassigns luck to skill.** On the effectiveness check it re-scored ~31% of night actions
  vs the outcome-only deterministic credit — crediting skilled misses and demoting lucky hits — which no free
  signal can do ([../../v7_final/tagger_effectiveness.py](../../v7_final/tagger_effectiveness.py)).
- **Per-field distributions pass a sanity check, but no accuracy number is on record.** `framing=manipulative`
  skews as expected by faction (town 7% / wolf 85% / SK 88% against true roles), and `role_reveal` was
  cross-checked against a deterministic self-claim detector — but the accuracy script prints to stdout only, so
  no persisted per-field accuracy figure exists ([../../v7_final/tagger_accuracy.py](../../v7_final/tagger_accuracy.py)).

**What it can't do.** Flag a bad verdict distribution, yes; certify a correct per-turn verdict, no. And a
*metric* that correlates with the win is not a *demonstration* that wolf/SK memory compounds — that needs a
direct wolf SP/obs A/B, which has never been run.

## Known gaps (freshness: 2026-07-04)

Ordered by how misleading each is to a reader; severity = likelihood × impact × detectability.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **Metric, not a memory verdict** | The +0.56/+0.60 validates that the tagger *sees* deceiver discussion skill; it does **not** show wolf/SK memory helps. That requires a direct wolf SP/obs A/B (never run — the v2 loop mis-configured to all-factions-on, confounding the town question and never isolating wolf). The tagger is the *instrument* that A/B would use. | **Med-High** |
| 2 | **Uncalibrated per-field** | No human golden sits behind `framing`/`credibility`/`role_reveal`; they are face-valid + distributionally sane, never label-validated. The holistic `verdict` (the only credited field) is validated correlationally; the sub-tags are not. | **Med** |
| 3 | **Single-epoch, N=24** | The load-bearing correlation rests on one epoch of 24 ON games; it would piggyback on a held town-only rerun to gain power and a fresh epoch. Directionally trustworthy now; not yet robust. | **Med** |
| 4 | **Night-verdict residual leak untested** | The night verdict still sees its own kill's death (the night analogue of the day leak the ablation cleared). A two-prompt split would fix it if a clean deceiver *night* metric is ever needed; the discussion verdict is the load-bearing signal and night has a deterministic de-luck proxy underneath it. | **Low** |
| 5 | **Not promoted to the standing scorecard basket** | The tagger is wired into the loop's **credit** ledger and its own validation apparatus, but has not been promoted as a standing de-lucked proxy in the metrics basket (the "Phase-2 LLM tagger" the discussion-scoring plan deferred — see [../../evaluation/metrics/report.md](../../evaluation/metrics/report.md)). Its numbers live in the credit loop, not the frozen scorecard. | **Low** |
| 6 | **"flash-lite" is caller-pinned** | The tagger calls `get_llm_pro()`, whose bare default is `gemini-2.5-pro`; flash-lite holds only because the loop env-pins it. A standalone `tag_game` call with unset env would silently run pro-2.5. Documented, not a live hole (the driver always pins). | **Low** |
| 7 | **Durable artifacts pending** | The retest/ablation scripts now *also* write `*_results.json`, but only on their next (paid) run — the JSON files are not yet on disk; the durable numbers still live in [../../v7_final/experiment_log.md](../../v7_final/experiment_log.md) §12g. | **Low** |

**Open work.** The one upgrade that would move the verdict from 🟡 to green is the direct wolf A/B (gap 1),
using the tagger as its discussion-merit ruler on a fresh, correctly-configured epoch (gaps 1+3 close
together). Per-field calibration (gap 2) is the cheapest independent add. Neither is a priority while the
binding open question is whether wolf/SK memory compounds at all — the science the tagger was built to help
measure, which belongs to the loop spoke and chapter 3.

---

*Companion journey: [experiment_log.md](experiment_log.md) · Trust/reliability apparatus:
[../../evaluation/discussion_tagger/report.md](../../evaluation/discussion_tagger/report.md) · Design record +
run artifacts: [../../v7_final/discussion_credit_design.md](../../v7_final/discussion_credit_design.md),
[../../v7_final/experiment_log.md](../../v7_final/experiment_log.md) §12g. Live code:
[../../../evaluation/src/loop/discussion_tagger.py](../../../evaluation/src/loop/discussion_tagger.py),
[../../../evaluation/src/loop/credit.py](../../../evaluation/src/loop/credit.py) (consumer),
[../../../evaluation/src/cli_runner/discussion_tagger_eval.py](../../../evaluation/src/cli_runner/discussion_tagger_eval.py)
(`eval-tagger`, validation). Written 2026-07-04.*
