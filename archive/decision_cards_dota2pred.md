# Decision cards — dota2pred

Local only (folder ignored via .git/info/exclude). Pre-filled from a code survey 2026-06-11;
edit into your own voice. This is the production/MLOps flagship — these cards should be the most
*confident* of the three sets, because almost every "why" below has a measurement behind it.
Sources to re-read before interviews: `model_factory/ML_EXPLORATION_SUMMARY.md` (your own
experiment record — it is already tier-1 interview material) and the README architecture diagram.

---

## D1. Redis Streams + consumer groups + per-stage DLQ (over Celery/Kafka)

- **Chose:** 5-stage pipeline (match detection → feature eng → prediction → completion → odds
  capture) on Redis Streams; consumer groups ACK on success; failures go to a per-stage
  dead-letter queue swept with exponential backoff (max 3 retries).
- **Realistic alternative:** Celery/RQ job queue, or Kafka for event sourcing.
- **Why:** at-least-once delivery from consumer groups + **idempotent upserts**
  (`INSERT ... ON CONFLICT`) in the DB = effective exactly-once without distributed
  transactions. Stage isolation means one failing stage doesn't block the others. And Redis was
  already in the stack for pub/sub — no new infrastructure for Kafka-grade semantics at this
  scale.
- **What would change my mind:** multi-consumer replay or cross-service event history → Kafka;
  many heterogeneous job types with priorities → a real task framework.
- **Probe I'm ready for:** "How do you know you didn't lose messages?" → ACK-on-success + DLQ
  catches the failures, idempotent reprocessing makes retries safe, and the scheduled backfill
  (D5) is the third net under both. Six months live, no documented loss.

## D2. Time-decayed Bayesian features with time-travel state (over rolling windows / Elo)

- **Chose:** 4 aggregated difference features (team WR, H2H matchup, hero WR, player-hero WR),
  each exponentially decayed (`0.5^(Δt/half_life)`, 45–60d half-lives) with Bayesian priors
  (e.g. team prior_count=13, prior_mean=0.52); per-entity decayed-state history stored after
  every match so feature generation **looks up the state as it was before the match timestamp**.
- **Realistic alternative:** fixed rolling windows (last-N games), raw frequencies, or Elo/
  TrueSkill ratings.
- **Why:** (a) **leakage-correctness is structural** — time-travel lookup makes it impossible to
  peek at the future, which is the failure mode that silently inflates most sports predictors;
  (b) Bayesian priors handle sparsity (a player-hero pair with 3 games shrinks toward the hero
  prior instead of overfitting); (c) decay adapts across game patches automatically — no
  re-tuning per meta shift, which is why accuracy held across 3 patches without retraining.
- **What would change my mind:** if Optuna had found a sharp optimum away from the domain
  defaults — it didn't (165 trials, landscape flat, McNemar p=0.66 vs defaults), which itself
  validated principled-defaults-over-blind-tuning.
- **Probe I'm ready for:** "Why not Elo?" → Elo is a special case of this idea with a fixed
  update rule and no entity hierarchy; the Bayesian-decay scheme gives the same recency behavior
  plus principled sparsity handling for player-hero and matchup levels Elo can't express cleanly.
  What Elo/Glicko WOULD add is opponent-strength adjustment (my team WR is opponent-blind; H2H
  only partially covers it) plus an uncertainty term — that's on the documented roadmap as one
  more feature column through the same temporal harness, expected gain <1% given the measured
  flat landscape (Optuna 165 trials, LightGBM +1%). Decided not to build pre-job-search: marginal
  accuracy isn't the bottleneck, and every shipped feature is interview surface to defend.

## D3. Logistic regression in production (over LightGBM / deep learning)

- **Chose:** sklearn LogisticRegression on the 4 aggregated features. Measured the alternatives
  first: LightGBM on granular features = 58.22% vs LR 57.15%.
- **Realistic alternative:** ship LightGBM (+1%), or the GNN line.
- **Why:** +1% accuracy was not worth 10× production complexity — tuning surface, slower
  inference, patch-fragility of memorized granular patterns. LR is interpretable (linear weights
  on 4 legible features), converges deterministically, predicts in ~1ms, and held 57–58% across
  patches without retraining. The deliberate-simplicity decision IS the senior signal.
- **What would change my mind:** the documented next step — GNN-embedding stacking gained +1.33%
  on public matches (54.76→56.09); if that transfers to the pro feature set it earns its
  complexity, and the experiment is already designed.
- **Probe I'm ready for:** "You spent months on deep learning and shipped logistic regression —
  failure?" → No: the experiments are why I *know* LR is the right ship. Multi-hot 51.9%,
  Word2Vec 53.3%, frozen sentence-transformer dead end, RGCN 52.8–55.8% after I found and fixed
  a global-pooling bug that made the model team-agnostic. Measured rejection is the deliverable.

## D4. The "58% — is that even good?" question (evaluation discipline)

- **Have this cold:** baseline = 51.8% (always-predict-Radiant), so the model carries ~6pp of
  real signal in a domain where pro-match outcomes are genuinely high-entropy. Validation is
  **temporal** (shuffle=False train/test) precisely because random splits leak future meta into
  the past. Calibration matters more than accuracy for the betting use case — Brier 0.24 and
  calibration plots are on the public dashboard; the paper-betting PnL replay exists to test the
  only question that matters commercially (does the model beat the market's implied odds?).
- **Probe I'm ready for:** "What would make this profitable?" → edge vs market odds, not raw
  accuracy — a well-calibrated 58% can be profitable if it disagrees with the market in the
  right places; that's what odds capture + paper-bet replay measures.

## D5. Scheduled gap-repair backfill (defense in depth for feature integrity)

- **Chose:** a scheduled flow scans for matches that have outcomes but missing decayed-state
  rows (`get_earliest_missing_decayed_state_time`), then recomputes feature state sequentially
  in ordered 2000-match batches, bounded by a within-days window.
- **Realistic alternative:** trust the live completion path + retries.
- **Why:** the live path can strand a match (API timeout, lock) in a state the per-stage
  detectors don't catch — outcome stored, history never updated. That corrupts *future* features
  silently, which is the worst failure class in an ML system: no error, just quiet drift. The
  backfill converts "silent corruption" into "self-healing within a day."
- **Probe I'm ready for:** "Why sequential/ordered recompute?" → decayed state is a fold over
  match history — order is causality; recomputing out of order rebuilds a different (wrong)
  state.

## D6. BentoML as a separate inference service (over in-process sklearn)

- **Chose:** models served from their own container (`/predict/pro`, `/predict/public`); the
  API and pipeline call it over HTTP.
- **Realistic alternative:** `import sklearn` inside FastAPI and predict in-process.
- **Why:** independent versioning/deploy of the model artifact (swap models without touching API
  code), pinned-dependency reproducibility inside the Bento, separately scalable, and the
  contract is E2E-testable. Cost = one ~10ms hop, irrelevant against a 2-minute polling cycle.
- **What would change my mind:** sub-100ms latency budget or a single-service deployment target
  → in-process with a model-loading abstraction.
- **Probe I'm ready for:** "Two models — why not one with masked features?" → public/draft
  matches simply don't have team/player identities; zero-masking team features breaks the pro
  model's calibration. Different feature availability = different models, routed by the caller.

## D7. Test pyramid with TestContainers + CI that deploys (over manual QA)

- **Chose:** 117 test files in 5 tiers — unit (47), integration against real Postgres+Redis via
  TestContainers (39), E2E on the full compose stack (6), contract tests for external APIs (4),
  Polyfactory data factories. CI: ruff/black/mypy → tests → frontend build → on main: SSH
  deploy, `compose up --build`, image prune.
- **Realistic alternative:** unit tests + mocks only; manual deploys.
- **Why:** the system's risk lives in the seams (DB upsert semantics, Redis group behavior,
  service contracts) — mocks can't catch those; real containers can. Auto-deploy on green main
  removes the "works locally" class of incident — and when the deploy step caused a disk-full
  via build-cache accumulation, the fix (prune step + builder GC cap) went back into the
  pipeline, which is the ops loop working as intended.
- **Probe I'm ready for:** "No approval gate on prod deploy?" → solo project, full test wall
  before the gate, and rollback = redeploy previous commit; with a team I'd add an environment
  gate + migrations review.

## D8. Honest-gap card: what this system deliberately doesn't have

- **No auto-retraining** — defensible: features adapt via decay, model held 57–58% across
  patches, so retraining cadence wasn't earned by drift evidence. Would add: scheduled eval-on-
  recent-window with a drift alert before any auto-retrain.
- **No experiment tracker / model registry** — notebooks + git + a written ML_EXPLORATION_SUMMARY
  served the solo scale; first team hire makes MLflow/W&B the obvious add. (The werewolf project
  is where I built heavier provenance discipline — fingerprints, frozen eval sets.)
- **No feature store** — the decayed-state history tables ARE the feature store for this domain;
  a general store would be premature abstraction.
- **MyPy non-blocking, no served API docs** — known debt, cheap to fix, say it before they find it.
- **Prefect server memory leak** — upstream issue; mitigated with mem_limit 512MB + auto-restart;
  worst case drops one 2-minute cycle. Good war story: contain what you can't fix.

---

## The cross-project narrative (rehearse this transition)

"dota2pred is six months and ~1,500 commits of hand-built production ML — streams, DLQs,
temporal validation, a deliberate simple-model decision backed by measured alternatives. The
werewolf project is where I then took the *evaluation* discipline much deeper — statistical
gates, gold labels, judge validation — and where I learned to multiply myself with coding
agents while owning every design decision. nutri_ally turns those two muscles into the
enterprise-agent pattern businesses actually deploy." — three axes, one arc, no overlap.
