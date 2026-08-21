# Frontend Design Log

Ideas log for a frontend to the werewolf agent sim. Status: **ideas only — nothing here is
implemented or scheduled.** Captured 2026-06-06 from a design discussion; this folder is for
frontend concerns only (the `Agents/` package stays backend-only).

Context: the project is primarily a portfolio piece, but the frontend should not preclude a
publishable MVP where real players sit in games with the agents.

---

## 1. Framing decision (the identity of the product)

A generic werewolf frontend competes with Wolvesville and dozens of Mafia apps — an unwinnable
fight. What this project uniquely has is **a fully observable AI mind on every seat**: Langfuse
traces, memory retrievals, situation summaries, the scheduler's reactive queue, enforced
information boundaries with leak checks.

> **Identity: "watch AIs deceive each other — and see exactly why."**
> Observability is not backend plumbing to hide; it IS the product. Human play is the MVP layer
> on top, not the core.

## 2. Features, in build-order tiers

### Tier 1 — Spectator / Replay Theater (portfolio core, cheapest to build)

- **Replay player** over existing batch artifacts (JSONL records + `day_channel` /
  `day_summaries`) — the backend already persists everything a replay needs. Timeline scrubber by
  day/phase; speech bubbles around a virtual table. Zero new game code.
- **The X-ray toggle** (the differentiator): click any agent mid-replay and see its private
  context — role, the actual retrieved memories (observations / strategy points), its
  `firing_reason`, what the novelty gate rejected. A **"thoughts vs. words" split pane**: what the
  agent *said* publicly vs. what its reasoning trace shows it was *doing*. This is the
  interview-screenshot artifact.
- **Scheduler visualization**: live mini-graph of the reactive queue — who got mentioned, whose
  obligation fired, pass-turn markers, trailing-pass termination. Phase A #1 made turn-taking
  legible; show it.
- **Dramatic irony meter**: spectators know all roles, so the UI can surface "the village is
  about to vote out the investigator" moments. Free tension from data that already exists.

### Tier 2 — Live mode

- Same view, streaming. LangGraph streams natively; an SSE/WebSocket relay is straightforward.
  **Sequential discussion is a gift for broadcast** — one speaker at a time is already a
  watchable format (concurrent fan-out would have been unwatchable).
- Spectator prediction overlay: "who's the SK?" bets that lock before reveal. Engagement without
  touching game logic.

### Tier 3 — Human-in-a-seat (the publishable MVP)

- One human takes a chair among 8 agents. Architecturally close: the scheduler is **stateless and
  recomputes from `day_channel`**, so a human turn is an external-input node with a timer.
- A vestigial `human_player` concept already exists in the codebase (currently slated for v5
  cleanup) — **this tier is the argument for keeping/reviving it rather than deleting it.**
- **Security story, verbatim from the backend**: the human client gets the same information
  surface the agent payload gating allows. Server-authoritative role-gated views, mirroring
  `build_speaker_send` / `fan_out_day`; the same leak-check invariants
  (`tests/leak_test.py`, see `evidence/agent_boundaries/`) guarantee the client never receives
  private state. The boundary doctrine becomes a user-facing feature.
- **Post-game reveal**: "here's what the AIs thought of *you*" — every memory/suspicion entry
  referencing the human player. The shareable screen.

### Tier 4 — Stretch / fun

- **Coach mode**: play with an AI whispering retrieved strategy points to you — the memory
  pipeline as a player-facing feature.
- **Public eval dashboard**: faction win rates, memory-on vs. memory-off — the Phase C A/B as a
  living page instead of a notebook.

## 3. Design theme

Skip cartoon-medieval (Wolvesville owns it) and generic dark-dashboard. Theme:
**"séance noir meets control room"** — the seam between story world and machine world is the
visual thesis of the whole project.

- **Table view (story world)**: candlelit; deep ink/charcoal palette; warm amber light pooling at
  the table center. Agents as minimal portrait cards — tarot-card framing, not 3D avatars (cheap,
  stylish, AI-generatable). Serif display type for speech. Night phase drops to blue-black with
  only acting roles' cards lit.
- **X-ray layer (machine world)**: deliberate contrast — flipping into an agent's mind goes
  clinical: monospace, thin cyan-on-dark, trace-viewer aesthetics. Warm deception on top, cold
  observability underneath.
- **Micro-touches**: retrieval events as a faint card-glow ("it's remembering something"); votes
  as chips physically sliding toward the accused; SK kills rendered differently from wolf kills
  (deaths are already attacker-typed in the backend).

## 4. If only one artifact gets built

**The replay theater with the thoughts-vs-words pane**, fed straight from existing batch
artifacts. Zero new game code, maximum "nobody else can show this" factor — and it doubles as a
debugging/inspection tool for Phase B labelling, so it isn't even scope creep.

## 5. Competitive landscape (researched 2026-06-06)

Question asked: does a productionized mafia/werewolf game where humans play against actual LLM
agents exist? **Answer: no.** Verified by web search 2026-06-06 (US-only search; can't see behind
waitlists; small mobile apps may not advertise LLM use).

| Bucket | Who | Status |
|---|---|---|
| Near-product (the only one) | [AI Mafia / botmafia.games](https://botmafia.games/) | **Waitlist-only.** 30+ roles, cognitive-bias personalities, TTS theater mode, 35-model leaderboard. **No agent memory/learning anywhere** (site, repo, docs). Strong evidence it's a solo side project by [guzus](https://github.com/guzus) (same OpenRouter stack + leaderboard concept as [guzus/llm-mafia-game](https://github.com/guzus/llm-mafia-game), 52★; repo roadmap says "Human vs LLMs 3D Mafia Game"; dev's main work is prediction-market tooling). Leaderboard page doesn't server-render. |
| Agent-vs-agent spectator/benchmark | [werewolf.foaster.ai](https://werewolf.foaster.ai/), mafia.opennumbers.xyz ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/ai-bots-can-now-play-mafia-with-each-other-and-almost-all-of-them-are-terrible-at-it), [Gigazine](https://gigazine.net/gsc_news/en/20250310-llm-mafia-game-competition/)), [mafiabench](https://github.com/nickslevine/mafiabench) | Humans watch, don't play. Headline third-party finding: naive stateless LLMs are *bad* at mafia. |
| Research demos / OSS hobby | [MetaGPT werewolf](https://werewolf.deepwisdom.ai/) (`add_human=True` flag), [wolfcha](https://github.com/oil-oil/wolfcha), [hiper2d](https://github.com/hiper2d/werewolf-ai-party-game), [niveck/LLMafia](https://github.com/niveck/LLMafia) (the one *research* agent playing vs humans, async) | Not products. |

Cross-game memory exists **only in papers** (Tsinghua experience-pool / [ICML 2024 strategic
werewolf](https://dl.acm.org/doi/10.5555/3692070.3694355)) — research mechanisms evaluated once,
never shipped, and none with an eval harness measuring whether memory helps.

**Moat statement** (sharper than §1's): not just "watch AIs deceive each other" but **"AIs that
got *better* at deceiving since last week — and you can inspect why."** Three empty lanes at
once: (a) human-vs-LLM play is ~vacant (one waitlisted stateless solo project), (b) measured
episodic memory exists nowhere in products, (c) observability/X-ray exists nowhere at all
(botmafia's theater mode shows speech, not minds). The third-party "LLMs are terrible at mafia"
result is external evidence *for* the memory build: the gap it documents is the gap this project
closes. Roadmap extension (separate story, noted for the narrative): fine-tuned model trained on
accumulated memory data — the data flywheel.

## 6. MVP scope v0.1 (discussion 2026-06-06 — owner's cut, supersedes tier list as the concrete plan)

The tier list (§2) is the idea inventory; this is the agreed minimal product loop:

1. **Login: OAuth or continue-as-guest.** Guests get the full game *including* the replay; only
   persistence (stats, history) requires OAuth. The sign-in prompt goes on the post-game screen
   ("save this game and your stats?") — highest-conversion moment, zero friction before game 1.
2. **Play**: human in one seat, sees exactly the information surface their role's agent would see
   — **except memory**. Dialogue appears like a normal werewolf game; make decisions on your turn.
   - The memory asymmetry is the *premise*, not a gap: "you're the rookie at a table of veterans."
     Memory-on/off doubles as a difficulty knob later (easy = memory-off agents; future coach
     mode = human gets retrieval too — the existing flag, no new machinery).
3. **Endgame reveal → X-ray replay**: trace what each agent was thinking/retrieving at each point.
   Endgame-only replay deliberately: no live-spoiler problem, no streaming-thoughts infra (replay
   reads completed artifacts), and the unlock lands at peak curiosity ("the SK was WHO?").
   Loser's autopsy converts frustration into engagement.
4. **Post-game MVP score**: deterministic score from the de-lucked outcome proxies already built
   for the metrics work (`evidence/metrics/` — the eval pipeline doubles as the fun layer) +
   one cheap LLM call for flavor commentary. For fun, not rigorous — but the number has a real
   methodology, the LLM only writes prose. (botmafia has "postgame autopsies"; the methodology is
   the edge.)
5. **(OAuth'd) personal board**: win rate per role, game history. Trivially derived from the
   existing batch-record schema.

**Human turn-taking (decided in discussion):** reactive preserved symmetrically (human
obligations enter `build_reactive_queue` like any agent's, same per-pair K=2; turn timer, timeout
plays `pass_turn` so an AFK human degrades to passes and the day still terminates). Proactive =
**raised-hand preemption**: a standing toggle, checked by `select_next` before `rank_proactive`
when no reactive obligations pend — raised → human speaks (consumes from the same P=3 budget);
not raised → agents proceed. No blocking "want to speak?" prompts. Honest privilege granted: the
human is guaranteed access to their full proactive budget while agents face the recency+seeded
lottery — bounded by the same P, a scheduling privilege not a volume/information one. Novelty
gate exempts the human (it exists to stop agent echo; never bounce a human message). Scheduler
stays stateless — raised-hand flag is one more per-recompute input, no new state.

**Explicitly cut from MVP:** live spectator mode (replay covers it), agents-remember-you
(unproven value vs. real namespace/isolation/cold-start cost — revisit only if retention becomes
the problem), seasons/flywheel UI (post-fine-tune story), prediction overlays, coach mode.

## 7. Brainstorm round 2 (2026-06-06): art direction + feature annex (unshortlisted ideas)

### Art direction: pixel art — viable with two hard rules

Fear of "pixel art might not look good" is about the wrong variant (16×16 sprites + pixel fonts —
that WOULD hurt a reading-heavy game). The proven formula for dialogue games is **Coffee Talk /
VA-11 Hall-A style**: large detailed pixel portraits + moody lighting + **clean modern font for
all dialogue text**. Hi-bit (big canvas, rich palette, modern lighting over pixels — Eastward /
HD-2D), not retro-authentic.

- Hard rules: portraits big; dialogue font clean (pixel fonts for chrome/titles only).
- Werewolf-native wins: day/night palette swaps are trivially beautiful in pixel art; kill
  cinematics cheap (silhouette, few frames) and **attacker-typed deaths already in the data** →
  distinct wolf/SK/vigilante kill animations; dead players' portraits desaturate.
- Strategic: pixel-gen AI constrained to one palette reads *intentional*, dodging the AI-slop
  look (botmafia's weakness); solo-buildable visual consistency.
- Séance-noir thesis survives: pixel tavern + amber pooled light; X-ray layer becomes
  green-phosphor CRT terminal aesthetic — pixel-native machine-world contrast.

### Feature annex

- **⭐ Daily deduction puzzle (standout idea)**: one agent-only batch game published per day, same
  seed for everyone; players read the transcript phase-by-phase and lock guesses (wolves? SK?);
  scored by how early you call it; emoji-grid share (Wordle loop). Near-zero marginal cost (one
  game serves unlimited players — batch pipeline as content factory); is the replay theater WITH
  a game loop; shippable BEFORE the human-seat MVP; post-guess reveal = the X-ray replay served
  daily.
- **Vote matrix**: who-voted-whom grid per day — pure `day_channel` parse; the veteran's view.
- **Mention graph**: who's talking about whom — already computed by the scheduler's reactive
  queue; render as a live web, watch suspicion converge.
- **Achievements**: "survived to day 5 as SK", "won without being mentioned", "called the wolf
  day 1" — all derivable from batch records.
- **Play of the game**: MVP-score pipeline picks the pivotal turn; replay deep-links to it.
- **Pacing controls**: staged thinking delays (typing indicator → beat → message), always
  skippable — LLM latency becomes suspense if staged, frustration if not.
- **Tutorial table**: first guest game vs memory-off agents, villager role, phase tooltips.
- **Parked (dangerous-but-tempting)**: human "last will" on death (Town of Salem) — a game-RULE
  change requiring agent prompt edits → crosses the frozen prompt surface; post-v5 only.

## 8. Architectural concerns: connection / view / platform (discussed 2026-06-06)

- **Stream EVENTS, not tokens.** Messages post whole after generation, preceded by a typing
  indicator. Three reasons token-streaming is actively wrong here: (a) the **novelty gate vetoes
  proactive speeches post-generation** — a token-streamed speech can be rejected after the client
  has shown half of it; (b) agent speech is embedded in structured output, not a bare text
  stream; (c) fiction break — players post whole messages, assistants stream tokens; streaming
  reads as "chatbot", typing-indicator-then-message reads as "player". Latency masking job goes
  to staged pacing (above).
- **Game = append-only event log** (speech_posted, vote_cast, phase_changed, typing_on/off,
  death, reveal), client holds a cursor. This buys: trivial reconnect (replay since cursor),
  spectator = same stream, and **the event log IS the replay artifact** — replay theater reads
  the same format. Decide the event schema once, transport is swappable.
- **Transport: SSE + POST for MVP** (server→client dominates; client acts only on its turn —
  raise-hand toggle, speech, vote as plain POSTs). SSE auto-reconnects, no WS infra, works
  serverless. WebSocket is a fine later swap if needed (the event schema doesn't change);
  not required by this traffic pattern.
- **Web app, decisively — not native mobile.** Zero install friction (guest mode synergy: click
  link → playing); daily-puzzle share links need the web anyway; no app-store review between you
  and iteration; recruiters click URLs, not TestFlight invites. Build **mobile-first responsive**
  (werewolf reading is phone-shaped), add PWA manifest later for home-screen install + push.
  Native only earns its cost post-MVP (push-driven retention, IAP, store discovery).

**Process model (no Redis):** single asyncio process (FastAPI/uvicorn) — game orchestrator and
SSE handlers share one event loop; per-game broadcast = in-memory asyncio queues. **Durability =
the event log itself** (append to SQLite/JSONL as emitted); reconnect = `Last-Event-ID` →
replay-since-cursor from the log. Redis exists to fan events out ACROSS processes — irrelevant at
one box + capped concurrency; if ever multi-process, Postgres LISTEN/NOTIFY or Redis pub/sub
slots behind the same event schema. Caveat: long-lived SSE + serverless timeouts don't mix —
fine on own box/VPS.

**Meta-observation worth keeping:** the backend architecture keeps making frontend decisions —
the novelty gate decides no-token-streaming, the stateless scheduler decided human turn-taking,
the batch pipeline decided the daily puzzle is near-free. When a frontend question feels open,
first check which existing backend invariant already answers it.

## 9. Human involvement as model-feedback signal (discussed 2026-06-06)

Question: can human players feed model tuning? **Verdict: evaluation signal first, training
signal only after scale. Nothing in Phases A–C changes.** Ranked by value-per-cost:

1. **⭐ Daily puzzle = labelling machine (eval-grade, the real win).** Same-seed puzzle → N humans
   read ONE transcript with per-phase guesses → aggregate = **timestamped human-suspicion curve
   per agent per speech** ("after Marcus's day-2 speech, suspicion 30%→70%"). Per-speech
   deception-quality labels no LLM judge can give (judges miss this — known limitation), at
   scale, free, zero consent friction (agent-only transcripts). Feeds: (a) **proxy validation**
   — proxy-vs-human-suspicion as a second monotonicity check alongside proxy-vs-win; (b) later,
   preference pairs (suspicion-lowering vs -raising speeches) for a deception-quality model —
   same training shape as the CE reranker, new signal. **Schema requirement NOW: record guesses
   keyed (game_id, phase, guesser), not just final score.**
2. **Live human games = headline eval metric, not a dataset.** "Deception rate vs humans" is the
   real benchmark + distribution-shift detector vs self-play overfit; but sparse at MVP scale,
   noisy (human skill variance), hard credit assignment. Dashboard number only.
3. **Explicit post-game ratings** ("most human-like?", MVP vote): one screen, doubles as
   engagement, weak-but-free baseline against the deterministic MVP score. Never load-bearing.
4. **Human utterances → extraction pipeline (agents learn from humans): defer, don't foreclose.**
   Most flywheel-shaped, most fraught (quality variance, trolls). **Consent line in TOS from day
   one** ("gameplay may be used to improve the agents") — one sentence now, painful retrofit.

Near-term fine-tunes (dedup classifier, CE) are retrieval-infra — human signal irrelevant to
them. Option-preservers to build in: per-phase guess schema, consent sentence, the §8 event log.

## 10. Daily puzzle implementation + cost & scale posture (discussed 2026-06-06)

### Puzzle implementation sketch

- **Unit = one full game, revealed day-by-day, PUBLIC channel only**: puzzle player is a "ghost
  villager" — sees exactly `day_channel` (discussion/votes/deaths), never night internals. Fair
  (same info the village had), length-bounded, maps 1:1 to existing serialization. Guess
  checkpoints at day boundaries, earliness-weighted score.
- **Source = fresh daily batch generation** (~$0.3/day ≈ $9/mo content factory), NOT store pulls.
  Generate 3–5 candidates, auto-curate via the metrics pipeline (close outcome, late wolf
  detection, vote churn — blowouts are boring puzzles). `batch_results/` = launch backfill.
- **Guess-the-human mode = crowdsourced Turing test**: some days include a recorded human seat,
  some don't; "no human here" is a valid guess → human-detection rate vs chance = longitudinal
  "do agents talk like people" metric, improving for free. Needs consent line + username
  anonymization. Caveat: measures STYLE indistinguishability, not play quality.

### Cost posture

- Per-game: ~$0.4 today → ~$0.2–0.3 after cache/optimization (cache reorder is v5-gated, see
  prompt-cache debt). Human games slightly cheaper (one seat = no LLM calls).
- **Deferred extraction for human games**: snapshot inputs, skip inline extraction (dump-gate
  plumbing exists), nightly scheduled extraction of SELECTED games — which unlocks the **Gemini
  Batch API 50% discount**. Serving cost decoupled from learning cost.
- **Tiered affordability**: (1) puzzle + replay theater = unlimited/free (static JSON + CDN,
  ~$0.30/day total — serves 95% of portfolio viewers incl. recruiters); (2) live games capped
  5–10/day (≤$2.50/day worst case; scarcity is thematic — village seats are limited); (3) BYOK
  escape hatch for technical visitors (never store keys; proxy per-request or client-side).
- **Free-API options rejected**: Gemini free tier = top-up at best (few games/day; training-data
  terms); NVIDIA NIM rejected ON PRINCIPLE not just uptime — eval story (memory content, proxies,
  win rates) is Gemini-conditioned; never compare across backends → serving on a different model
  means the product is no longer the thing that was evaluated. Worst-case budget ~$50–80/mo.

### Scale posture ("the server is a waiting room, not a factory")

- All model compute is API-hosted; a live game = async orchestration awaiting Gemini, KB of
  state, ~zero CPU. Only local compute = CE reranker (ONNX, top-k=10, ms on CPU). Current 24GB
  box orchestrates hundreds of concurrent games; SSE = thousands of connections per box.
- Real ceilings in order: (1) **API RPM/TPM quota** — game-worker queue with max-concurrency
  matched to quota budget (batch-runner pattern); "table's full, next game in N min" =
  thematic backpressure; (2) **cost** — the daily cap IS the autoscaler; (3) infra a distant
  third ($10–20/mo VPS when outgrowing the home box). The thing that scales with users (puzzle)
  is static-file CDN ≈ $0; the expensive thing (live games) is capped by policy.

## 11. Rigor boundary + ghost mode (discussed 2026-06-06)

### The rigor boundary (research vs fun-production)

Decision: the PORTFOLIO CLAIM ("memory improves play, measured") is made and frozen under the
pinned Gemini config; after that, production-for-fun relaxes — BYOK with any backend (various
integrations, incl. NVIDIA NIM) is allowed with a disclaimer ("not the evaluated configuration").
A minor end-of-project model comparison closes the loop ("same agents on other backends" as a
chapter, not a confound). This supersedes §8's blanket NIM rejection — that argument applies to
the EVAL phase only.

- Mechanically already supported: `runtime_fingerprint` stamps backend+model into every record →
  "evaluated configuration" vs "exhibition mode" is a FILTER, not new infra. UI labels it;
  leaderboards/eval dashboards filter to canonical config.
- **The one guardrail: foreign-backend games are READ-ONLY on the memory store.** Retrieval
  during exhibition games = fine; extraction writing back = memory-store contamination right
  before fine-tuning on accumulated memory. `extraction_enabled = (backend == canonical)`.
  Cheap now, unrecoverable later.

### Ghost mode (free playable replays — zero LLM calls)

Human takes a VILLAGER seat in an already-completed game: reads `day_channel` day-by-day (public
info only), maintains role predictions; "voting" = suspicion ranking. No generation at all.

- **Beat-the-ghost scoring** (turns the non-interventional gap INTO the game): you replaced a
  specific seat → benchmark your daily suspicion ranking against what that agent actually voted;
  endgame: "the villager you replaced voted out the investigator day 2; you had the wolf at #1."
  Side product: a human-vs-agent deduction benchmark feeding §9's eval story.
- Villager-only v1 for timeline validity (their night is a no-op). Investigator ghost is half
  possible (results derivable from frozen roles) but forks the discussion timeline — parked.
- **Serve from replay artifacts (§8 event-log format / batch records) as static JSON + CDN — NOT
  Langfuse** (trace store: auth-coupled, rate-limited, not a serving API; it's the offline source
  replay files are built from).
- Funnel gradient: ghost games (unlimited, free) → daily puzzle (curated, social) → live seat
  (capped) → BYOK (unlimited, their key). Ghost mode = the guest default experience.

## 12. Build phasing + effort estimate (agent-assisted, part-time; discussed 2026-06-06)

| Phase | Scope | Backend coupling | Estimate |
|---|---|---|---|
| **F1** | Ghost mode + replay theater + daily puzzle: export script (batch records → static event-log JSON) + SPA (progressive dialogue, guesses, X-ray reveal) + curation cron | **Zero — reads frozen artifacts; safe to build TODAY, can't conflict with Phase A/B/C** | ~2–3 weekends; ~80% of portfolio value |
| **F2** | MVP score + autopsy screen (proxies exist + one LLM prose call) | Minimal | Days |
| **F3** | Live human game: human-input node, turn timer, raised-hand, SSE emitter, OAuth/sessions, worker queue | **Deep (graph + scheduler) — WAIT FOR v5 rebuild** or the integration gets rebuilt | ~3–4 weeks; time goes to reconnect/timeout/pacing edge cases, not typing |
| Art | Pixel assets | None | Timebox; ship F1 with placeholders |

Agent assistance compresses typing, not decisions/integration-debugging/playtesting. Total to
full MVP ≈ 6–8 part-time weeks; shareable artifact in ~3 weekends.

**Concurrency decision (2026-06-06): once Phase C win-rate A/B is proven, frontend runs in
parallel with the fine-tuning + labelling experiments.** Disjoint surfaces (frontend never
touches the frozen prompt surface or labelled corpus); fine-tuning/labelling cadence (Modal
waits, labelling sessions) interleaves with frontend gaps; **Phase C's A/B batch = F1's launch
content library** (largest v5 game corpus); replay viewer doubles as labelling-inspection tool.
Guards: F3 behind a flag so experiment batches run an identical code path (fingerprint + leak
checks prove non-interference); displacement risk named — labelling is tedious, frontend is fun:
experiments get prime hours, frontend gets the gaps, split decided up front.

## 13. Multi-human tables (5 humans + agents) — discussed 2026-06-06

**Status: deferred consideration, NOT planned work.** HITL is unimplemented (like every frontend
decision here); concurrent-human coordination is a design input to revisit *when implementing
HITL* — and the entire HITL track itself waits until the Phase B/C experiments prove (or
disprove) whether memory works. Recorded now only so the F3-era architecture choices below
aren't accidentally foreclosed.

**Infra verdict: non-problem.** 5 SSE connections, same event log/process model; every human seat
is an agent NOT run → a 5-human 9-seat game ≈ half the LLM spend. Infra-adjacent sharpening:
event stream must be **role-filtered per recipient** (human wolf sees wolf events) — same
invariant as payload gating, extended to the event layer, needed even at 1 human; multi-human
just makes it N views.

**The three real (design) problems:**
1. *Turn arbitration* — small: FIFO on raise-time for competing human hands; pacing shifts (every
   reactive obligation now waits on a person → turn timers become core mechanic, not AFK guard).
2. *Synchronous presence* — lobby, invite links, ready-up, reconnect grace, desertion policy.
   Killer card: **deserter's seat inherited by an agent natively** — the agents ARE the
   bot-replacement system other party games build badly.
3. *Mixed human/agent night channels* — the genuinely new chunk: human wolf chats in
   `wolf_channel` with agent wolves (real-time chat phase + its own turn semantics); night-action
   pickers for human power roles are easy, the channel is the work.

**Sequencing: single-human F3 first; multi-human = F4 (+1–2 weeks, mostly lobby + night chat).**
Two F3 choices to make as-if-F4-exists (zero cost now): per-player role-filtered event streams
(never a single "the human's" stream), and lobby/seat abstraction with human count as a variable.
Friends-via-invite-link only at first → defers all moderation/trust questions.

## 14. Backend touchpoints to keep in mind (no action yet)

- Replay reads from batch JSONL + `day_channel`/`day_summaries` — keep those fields stable in
  v5 record schemas.
- Live mode wants a streaming relay over the LangGraph run — no graph changes, just a consumer.
- Tier 3 depends on the `human_player` vestige: don't hard-delete it in the v5 cleanup without
  noting this use case.
- Any client-facing view layer must be derived from role-gated payloads, never raw graph state —
  same invariant the leak checks enforce for prompts.
