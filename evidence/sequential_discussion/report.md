# Sequential Day Discussion — How It Works

**Scope:** the day-phase discussion engine — how agents take turns, when they stay silent, how the
conversation terminates, and why it reads as a conversation rather than parallel monologues. Covers the
shipped design (Phase A #1) and the evidence that it works. **Companion docs:** the chronological build
journey is in [`experiment_log.md`](experiment_log.md); the acceptance study is
[`quality_gate/`](quality_gate/experiment_log.md) (the concurrent-vs-sequential A/B).

**Distilled** 2026-06-24 from the workstream logs (2026-05-31 – 06-05); **re-verified against the repo
2026-06-25** (file paths, config values, and the open gaps all re-checked against the current code).
Framework-behavior claims below are pinned to LangGraph as used in this repo (`.invoke()` only; no
`.stream()`/`interrupt()`/checkpointer at the time of writing).

**Orientation — one cycle of the loop:**

```
day_channel (the running transcript)
   └─ SCHEDULE node: select_next_speaker(day_channel, survivors, config, seed)   ← pure, no LLM
        ├─ pick the next speaker (or terminate)
        └─ single Send → that one role node → generate message + speech-act tags → append to day_channel
   └─ loop back to SCHEDULE
   ...until terminate → SUMMARIZE → the vote (separate: blind, simultaneous, locked)
```

Every identifier below hangs on this loop: the **scheduler** decides *who speaks*, the **role node**
decides *what they say*, the **transcript** is the single source of truth both read from.

---

## Motivation — from parallel to sequential

Day discussion began as a **concurrent** design — every agent speaks once per round, generated in parallel
against the same frozen transcript snapshot, all revealed together. That was a *sound* first choice, not a
mistake to be undone. It bought three real things: it was the **simplest to build** (one round, fan out,
no scheduler or per-utterance state), the **fastest** (all agents generate concurrently → low wall-clock
latency), and **fair by construction** (everyone reads the same snapshot and is revealed together, so
speaking order confers no advantage).

The catch is that the very property buying that fairness — a single snapshot evaluated *simultaneously* —
also makes redundancy **invisible**. Redundancy is a cross-agent property: at the shared decision moment,
no agent can see that another is about to make the same point. So the day read as parallel monologues —
near-duplicate takes, questions answered a round late, everyone speaking every round, a dogpiled player
unable to defend until next round.

The shift turns on one observation: **fairness and naturalness matter at different moments.** Turn-order
*advantage* only bites at the **vote**, not the chatter. So fairness is kept exactly where it matters — a
blind, simultaneous, locked vote, which the concurrent design already did right and the sequential design
leaves unchanged — and the *discussion* is freed to go sequential and natural. Sequential does not discard
parallel's fairness; it **relocates** it to the vote, and pays a deliberate latency cost (turns are now
serial) to buy real turn-taking. The rest of this document is how that sequential discussion works.

---

## 1. The guarantee (the contract this design holds)

Concretely, the sequential design guarantees:

- **Adjacency: a questioned or accused agent answers *next*.** Being addressed creates a deterministic
  *obligation*; the scheduler serves open obligations before anyone else speaks. You cannot ask a
  question and have it answered three turns later (the concurrent model's defining failure).
- **Fairness lives only at the vote.** The vote is blind, simultaneous, and locked — every agent commits
  against the frozen transcript, all revealed at once. A later speaker's turn-to-turn information edge in
  discussion cannot be cashed in, so natural (unfair-by-turn-order) discussion is safe.
- **Who-speaks-next is deterministic and LLM-free.** Speaker selection is a pure function of the
  transcript plus a seed. No model call decides turn order → it is reproducible, unit-testable, and
  resume-safe (recomputed from the transcript, never from mutable side-state).
- **Ping-pong is bounded.** A two-agent feud is capped (per-pair K, with a cooldown that lets a genuinely
  re-surfacing topic back in) so it cannot starve the rest of the table.
- **Redundancy is handled at two levels — one structural, one best-effort.** The concurrent *blind-round*
  duplication (N agents reacting to one frozen snapshot, blind to each other) is **eliminated by
  construction**: every agent reads the running transcript before speaking, so same-round parallel
  monologues cannot occur. *Semantic* echo on quiet proactive turns (the same point reworded) is only
  **soft-reduced** — a disinterested novelty judge converts the worst of it into a silent pass, but it is
  deliberately lenient, un-ablated, and reduced **by design rather than quantitatively verified** (§5).
- **The day ends on its own.** Termination is structural — either everyone with something to say has said
  it (a run of passes) or a hard utterance cap fires as a backstop.

What it deliberately does **not** do: enforce equal speaking time (participation is need-based, and most
agents speak zero times on a quiet day — intended), and it does not yet handle a human player's turns
(see §5). And one honest dependency runs under all of it: the reactive layer is only as reliable as the
speech-act labels the model emits — a mislabelled turn can defeat the obligation bookkeeping, which is the
domination residual tracked in §5.

---

## 2. The model — reactive vs proactive, over a stateless transcript

Two ways an agent reaches the floor, and nothing else:

**Reactive — a message created an obligation.** Each spoken message carries structured speech-act tags
(`addressed_targets`): for each target, an `addressed_form ∈ {question, response, mention}` and a
`stance ∈ {accusation, defense, agreement, neutral}`. The scheduler nets these into open obligations:

- a `question` to you, or an `accusation` of you, **opens** an obligation (you owe an answer / a defense);
- a `response` or `mention` *toward someone you owe* **discharges** it (broadened from `response`-only
  during tuning, so a correctly-aimed turn clears the debt even when the model mislabels the form);
- obligations are **grouped by the obligated agent**, so someone questioned by three players answers all
  three in one turn (natural dedup, not three separate turns).

Two independent levers keep a feud bounded — they are often confused, so stated separately:
- **Freshness** — while an edge `(speaker→target, stance)` is still *open*, re-stating it (even reworded)
  creates no second obligation. The key ignores wording *by design*, so no LLM is needed to judge "is this
  a new angle?". Stops pressure-spam within one exchange.
- **Per-pair K-cap** (`per_pair_reengagement_cap = 2`) — counts *completed* accuse→defend cycles on a
  directed pair. After K, further opens are blocked **until a cooldown resets the count**: once the pair
  has sat `M = ceil(reengagement_cooldown_multiplier · survivors)` utterances untouched (multiplier
  `1.0` → M ≈ one full table), the burst is considered over and the pair may re-engage. This makes K a
  cap on *consecutive* ping-pong, not a topic ban for the day.

**Proactive — the scheduler offered a quiet turn.** When no obligation is open, the scheduler ranks
eligible agents **role-blind: quietest-first, seeded-random tiebreak** (private-info and accusation-graph
centrality were both considered and dropped — a guaranteed slot for the investigator is a power-role
tell). The top candidate is offered the floor and *may decline* (`pass_turn`): a proactive pick with
nothing fresh sets the flag, which appends a hidden pass marker rather than a message.

**The novelty gate (proactive only).** Because a proactive speaker proves no novelty, a **disinterested
external LLM judge** runs *post-generation* on proactive turns and converts a low-information echo into a
pass. It **owns only silencing — never priority (recency owns that) or termination (deterministic)**, and a
reactive answer is never gated. The day's first `opener_floor` (= 3) real utterances bypass the judge so
every day gets a substantive opening before gating can kick in. (This judge is the *re-introduction* of novelty detection
in the one form that survives — see §4.)

**Stateless by construction.** Every cycle recomputes the whole picture (recency + open obligations) from
the `day_channel` transcript in a single pass — there is no mutable per-turn state to desync on resume.
The verdict rests on one assumption, **verified for all-agent games**: the transcript (plus within-day
immutable night state) fully determines scheduling. The one known break — a human player's turns aren't
tagged yet — is on the Phase-1 list (§5).

**Wiring.** A `SCHEDULE` node runs `select_next_speaker` and emits a single `Send` to the chosen role
node (reusing the existing per-speaker payload construction — one `Send` instead of the old N-way
fan-out); the role node always loops back to `SCHEDULE`, which **owns all termination** (cap | trailing
passes | no eligible speaker). Per-utterance node boundaries (rather than one opaque loop node) keep the
door open for mid-discussion streaming / reconnect / `interrupt()` **later**, with no redesign.
*Framework pin:* the one LangGraph behavior **relied on today** is that a `Send` delivers its payload to
the target node verbatim. The checkpointer-at-node-boundaries behavior that would make reconnect a drop-in
is **not wired yet** — the graph runs `.invoke()`-only (per the header) — so the boundaries keep that
capability *possible*, not currently in use.

**Where it lives:** scheduler `Agents/turn/scheduler.py` · per-turn pipeline + novelty gate
`Agents/turn/agent.py` + `Agents/turn/novelty_agent.py` · graph wiring `Agents/nodes/day/flow.py` ·
schemas `Agents/schemas/{game_events,output,scheduler}.py` · knobs `Agents/game_config.py`.

---

## 3. How we verify it

Verification is layered to match where each risk lives — deterministic logic is unit-tested; the
LLM-dependent pieces were smoke-tested for capability; the end-to-end quality claim was settled by an A/B.

| Layer | What's checked | How |
|---|---|---|
| **Scheduler logic** | obligations open/discharge/group; freshness; K-cap; cooldown reset; trailing-pass + cap termination | `tests/test_scheduler.py` — 22 unit tests over hand-built synthetic transcripts, **no LLM** (pure functions) |
| **Speech-act labels** | can a weak model emit `(form, stance)` reliably? | Smoke 1/1b: 100% structured-output validity, 0 hallucinated targets; 1-D enum proved lossy → 2-D |
| **Novelty (folded)** | does a self-judged novelty label discriminate? | Smoke 4: **no** — falsified; mechanism dropped (see §4) |
| **End-to-end quality** | does sequential read *better* than concurrent? | The discussion-quality gate — A/B over transcripts, deterministic metrics + hand-judged rubric ([`quality_gate/`](quality_gate/experiment_log.md)) |

The deterministic-logic layer is the strongest guarantee: because the scheduler is a pure function of the
transcript, a test hand-writes a `day_channel` and asserts the pick — no replaying an update sequence to
reach a state first.

---

## 4. Case study — the design the data killed, then resurrected

**Verdict (skim this, skip the rest):** The original silence mechanism was an LLM novelty gate folded into
each agent's own situation summary. An experiment (Smoke 4) **falsified it** — self-judged novelty doesn't
discriminate — so it was dropped and silence went fully deterministic. Live runs then showed the *function*
was still needed (proactive echo / dogpiling), so novelty returned — but as a **disinterested external
judge**, never the folded self-label. No shipped result depended on the broken version; the architecture
absorbed the loss by going deterministic, and the experiment's finding ("self-judgment is the problem, not
novelty") is what shaped the fix. *The data overruled the design.*

*Forensics, by subhead:*

**The original design.** Silence was to be decided by a 3-level novelty label (`already-said / borderline
/ new`) emitted as the final fields of the situation-summary call (zero extra cost), gating whether a
proactive agent speaks. Standalone smoke tests (Smoke 2/3) validated the label in isolation: 100% clean
separation on polar cases, temperature-robust.

**The falsification (Smoke 4).** Tested in the *folded* production shape — the agent judging the novelty
of its own point — it collapsed in both framings. Situation-anchored: labels ~everything `repeated` (a
mid-game recap is "a continuation of the established discussion") → would silence everyone.
Contribution-anchored: labels ~everything `new` (self-authorship optimism) → would silence no one. The
standalone smoke worked *only* because the candidate was external and the judge disinterested; folding the
judgment into the agent's own generation destroyed both properties.

**The deterministic redesign.** Rather than patch a broken self-judgment, the mechanism was removed:
silence became structural (unscheduled = silent), with reactive obligations + a budget-capped proactive
path doing all the work — leaving Phase 0 with *no fragile LLM mechanism to validate*.

**The re-introduction.** First live runs surfaced the gap the dropped gate left: on low-information days,
proactive turns dogpiled — agents handed the floor with no obligation echoed whatever was salient (the
agents narrated it themselves: *"stuck in a cycle of agreeing… which itself is a trap"*). The fix honored
Smoke 4's actual lesson: re-add novelty detection as a **disinterested external judge** on proactive turns
(the Smoke-2/3 form that *did* work), plus an `opener_floor` so it can't collapse a day's opening. Novelty
came back in exactly the one form the original experiment had shown would survive — and in a single,
narrowed role: **silencing a proactive echo, never again touching priority (recency owns that) or
termination (deterministic)**.

**The acceptance test (the gate).** The whole concurrent→sequential change was then ratified by an A/B
([`quality_gate/`](quality_gate/experiment_log.md)): sequential clears the bar. Echo rate **0.00** (sequential, both
memory on/off) vs **0.05–0.06** (concurrent); responsiveness forced by reactive obligations; turn-fairness
comparable. The win is **structural** (HIGH confidence, reproduced across all games); the quantitative
delta is descriptive only (N=4/arm). Concurrent is not *broken* — with strong evidence it still converges
and wins — but it reads as parallel monologues where sequential reads as a conversation.

---

## 5. Known gaps

Criticality = likelihood × impact × detectability (not impact-if-violated alone). Freshness-checked
against the repo **2026-06-25**; all open unless noted. Minor gaps are kept, not deleted — the list is the
audit trail.

- **[medium] Human speech-act extraction is not built.** The stateless scheduler assumes every turn's
  obligations live in `day_channel`; a human turn carries no `addressed_targets`, so for human games the
  transcript is *not* sufficient and an obligation can be silently missed. **High impact, but zero current
  likelihood** — all games today are all-agent, where the assumption is verified. Deferred to Phase 1
  (human integration), which is where external speech-act extraction belongs anyway.
- **[medium] Self-labeled speech-acts are unreliable → a domination failure mode.** An agent that owes A
  but answers B (mislabeling the form) never discharges, so it stays the top reactive pick and can be
  re-selected repeatedly (observed live: one agent ×7, with a verbatim re-generation). Mitigated by the
  A+B tuning (a `mention` discharges; a firing-reason brief anchors the turn) — clean across 4 live games
  since — but **not eliminated**; the root fix is the same external extraction as above.
- **[low–medium] Proactive echo is reduced, not eliminated — duplication is still observable.** The
  novelty judge is a *probabilistic LLM filter, not a structural guard*, and it is deliberately lenient
  ("lean novel when uncertain"): it converts the *worst* low-information echo into a pass but lets
  "agreement + minor reframe" through. So despite the guards, a reader watching live transcripts will still
  find some near-duplicate turns — the gate is **best-effort, not failproof**. (Only the *blind-round*
  redundancy of §1 is eliminated by construction; *semantic* echo is soft-reduced and will never hit zero
  with a lenient judge.) A cheap embedding pre-filter (cosine vs transcript, 0 extra LLM calls) is the
  deferred next step if logs show it still bites.
- **[low] Scheduler tunables were never swept.** `per_pair_reengagement_cap`, `proactive_budget`,
  `opener_floor`, `reengagement_cooldown_multiplier` were all hand-set during tuning; a grid sweep is
  deferred. (Concrete evidence this matters: `reengagement_cooldown_multiplier` shipped at `3` against a
  recorded intent of `1.0` — a slip that detuned the cooldown ~3× and went unnoticed precisely because
  nothing swept it; **caught during this consolidation pass and fixed to `1.0` on 2026-06-24**.)
- **[low] Pass-termination rarely fires in reactive-heavy games.** Heavy reactive traffic means you seldom
  get `proactive_budget` consecutive passes, so active days run to the utterance cap (max cost) rather than
  converging gracefully. Cost/quality, not correctness.
- **[low] Wolf-night discussion is still concurrent.** The night uses the old round-based fan-out — the
  last `round`-based code path. Applying the same reactive/proactive scheduler would bring the same
  coherence win; deferred.
- **[note] `firing_reason` is persisted on `DayChannel`.** An early design note said it would be
  tracing-only and not persisted; the shipped schema persists it (observability). Harmless — it is hidden
  from agents — but noted so the record and the code agree.

**Deferred by design (future phases, not gaps).** Two pieces were decided at design time and parked, both
about *voice* rather than *flow* (which this architecture already solves):

- **Persona/voice firewall (Phase 3).** Personas would vary *voice* only (register, tics, humor), never
  *disposition* (aggression, trust, paranoia — those bias play); injected at the realization step,
  assigned independently of role so voice carries no role tell, stable within a game.
- **Style fine-tuning (Phase 4, optional).** The strongest lever for naturalness-of-voice (a model
  property), pursued only if a drift test shows prompted voice decaying across a game — and only as a
  single decide-and-write model, regression-gated so it doesn't degrade play. Neither blocks shipping the
  sequential design.
