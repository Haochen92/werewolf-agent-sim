# Metrics Audit — Workstream 2: does the scheduler bias what roles can do?

> **What this is.** The chronological log of the structural-bias exploration opened 2026-07-02:
> whether the sequential discussion scheduler — role-blind by design — nonetheless starves
> specific role behaviors (investigator reveals, wolf/SK steering), which would make several
> metric nulls scheduler-shaped rather than agent-shaped. Later entries supersede earlier ones.
> Sibling workstream: [`proxy_discovery_log.md`](proxy_discovery_log.md) (the metrics themselves).
> Companion: the scheduler's own reference doc
> ([`../../sequential_discussion/report.md`](../../sequential_discussion/report.md)) — read its §2
> (reactive/proactive model, novelty gate) before this log.
>
> **Status: diagnostics A–C RAN 2026-07-02 (all $0, N=50).** §3 carries the results + the D-gate
> assessment. Headline: **no scheduler floor-starvation** — the two flagged roles (investigator,
> wolf) are floor-*rich*, pending-find investigators speak 100% before the vote, and unconverted
> finds have **zero** no-floor/late-floor cases (they are withheld / town-ignored). **B is
> unmeasurable** from records (gated vs voluntary passes are indistinguishable — an instrumentation
> gap). Recommendation: **do not open D on access grounds; do the cheap B instrumentation first.** A
> scheduler/tagger REBUILD stays gated (and closed) on those verdicts — beyond evaluation scope,
> and expected to reset behavioral baselines.

## §1 · Motivation — role-blind access is not role-neutral opportunity

The scheduler's design choices are defensible and were made deliberately (charitably: fairness
lives at the blind vote; who-speaks-next is deterministic; private-info priority was *considered
and dropped* because a guaranteed investigator slot is a power-role tell; participation is
need-based, not equal-time). The hypothesis of this workstream is that those same choices create
three role-asymmetric channels the design never measured:

1. **Reactive obligations privilege defense over initiative.** The floor goes first to the
   questioned/accused. Information injection (an investigator revealing a find) and steering (a
   wolf/SK starting or amplifying a pile-on) both need *proactive* slots — and on reactive-heavy
   days the scheduler's own report notes pass-termination rarely fires and the day runs to the
   utterance cap, i.e. proactive slots are exactly what gets crowded out.
2. **The novelty gate penalizes strategically-valuable-but-low-information speech.** It judges
   information, not strategy. A wolf's optimal steering move is often "amplify existing suspicion"
   — the gate's favorite target — and town coalition-building (low-info agreement before a blind,
   simultaneous vote) is the same shape.
3. **The cap ends active days with quiet info-holders unheard.** Quietest-first mitigates but
   obligations always outrank proactive offers.

**Why this matters to the metrics workstream.** Three recorded results are candidate artifacts of
these channels: the wolf-steering null and its 109/169 datum (no wolf among the accusers on most
mislynch days) may reflect a floor the scheduler narrows, not a skill wolves lack; and the
investigator conversion baseline — **40% of confirmed wolves never lynched** [correction
2026-07-02: that "40%" is the **v6ab (180-game)** WOLF-only per-game-mean rate (0.60); on THIS
workstream's own **50-game v5** set the wolf-find→lynch rate is **~70%** → ~30% unlynched. Both are
correct on their own set — full decomposition in the §3 reconciliation (③.D)] — has three
explanations nobody has separated: *couldn't get the floor*, *got it too late*, or *got it and
withheld*. Only the third is an agent problem. A proxy validated as null against
scheduler-suppressed behavior is null about this epoch, not about the construct.

**The adjacent information-design gap (SK–wolf).** Separate from the scheduler but raised in the
same discussion: the SK is night-immune, so a wolf attack on the SK silently whiffs, and the
whiff's disclosure is a known deferred gap. Wolves' single biggest win-correlate is `sk_lynched`
(+0.455) — currently an environmental event. A wolf that learned "my kill failed → target is
likely SK (or healed)" and could then steer town onto the SK would convert wolves' biggest
win-lever from luck into skill. That play needs *both* the information (whiff disclosure) and the
floor (steering opportunity) — and changing the disclosure is a **game-design change that resets
the epoch**, so it is a deliberate versioning decision, never a quiet patch.

## §2 · Design — the diagnostics, costed

| Diagnostic | Build | Experiment cost | Explainability | What it settles |
|---|---|---|---|---|
| **A. Floor-access audit** — per role × day over existing records: turns taken, reactive vs proactive share, spoke-zero rate; key joins: investigator-with-pending-find → spoke before the vote?; wolf → any proactive turn before the bandwagon formed? | small (script over `day_channel` + persisted `firing_reason`) | $0 | high | Whether starvation actually happens, per role — the direct question |
| **B. Gate-silencing audit** — who gets novelty-gated, by role and stance | small *if* pass/gate events are persisted; small instrumentation change if not | $0 | high | Whether the gate disproportionately eats wolf pile-ons / agreement turns |
| **C. Reveal-vs-withhold decomposition** — join `role_claims` + finds + floor access to classify the 40% unconverted finds into no-floor / late-floor / withheld | small–moderate | $0 | high | Whether investigator conversion is a scheduler artifact or an agent choice |
| **D. Scheduler-variant A/B** — config-flagged variant per the versioning policy: e.g. a role-blind "last words" pre-vote round (one proactive offer to every quiet agent — no role tell, every info-holder gets a window), and/or a gate-off arm | moderate | fresh games, ~$5–10 directional | medium-high | Whether fixing access moves discussion/vote outcomes |
| **E. Whiff-disclosure change + wolf→SK conversion metric** — disclose the failed kill to the attacker; measure wolf-accuses/votes-SK-after-whiff deterministically | small code + prompt; **epoch reset** | fresh games only (behavior change — not replayable) | high | The SK-information lever, priced honestly at a full re-baseline |

**Sequencing and gates.** A–C first (all $0, deterministic, existing records). D is **gated on
A–C finding a real access problem**; it is a config-flag variant, not a rebuild. E is a separate
versioning decision regardless of A–D, because of the epoch reset. **The rebuild gate:** only if D
shows that access changes move outcomes does a scheduler redesign enter scope — at which point it
leaves this evaluation workstream and becomes a design workstream with fresh baselines (and the
sibling log's proxies re-validated on the new epoch, per its pre-committed discipline).

**Pre-committed reading discipline.** A–C are *descriptive* audits: they establish whether the
starvation exists, not that it costs wins. Only D speaks to outcomes. Do not promote an A–C
finding into "the scheduler hurts town/wolf" without D — the same direction-vs-magnitude
discipline as everywhere else in this project.

## §3 · Implement → verify → decide

### Pre-registration — definitions committed before running the audits (2026-07-02)

Committed after inspecting record *structure* (field names, `firing_reason` tier values,
`addressed_targets` shape, timeline ordering) but **before computing any audit outcome**. Runner:
[`evaluation/src/experiments/scheduler_access_audit.py`](../../../evaluation/src/experiments/scheduler_access_audit.py)
(subcommands `floor-access` / `gate-silencing` / `reveal-withhold` / `all`). Validation set =
the same 50 v5 games as [`proxy_win_monotonicity.py`](../proxy_win_monotonicity.py) (30 memory-off
`v5_seed_b1..4` + `v5_baseline_pad`; 20 memory-on `v5_1_b1..4`) — chosen for consistency with the
proxy-trust work these audits contextualize. No loop-era runs added: they share the epoch's schema
gaps (below) and would not lift the blocked measures.

**Timeline convention (verified from records, not assumed).** `first_voting_day=2`, so day 1 is
pre-voting discussion; night *N* follows day *N*'s discussion (a player who dies on
`night_resolutions[day=N]` still spoke on day *N* — e.g. player_9 in `v5_seed_b1`). Therefore a
night action recorded at `investigator_results[day=N]` / `night_resolutions[day=N]` is announced
and first usable in **day N+1** discussion. "Alive at the start of day *D*" = cast roles − players
lynched on days `< D` − players who died on nights `≤ D−1`.

**(a) "Bandwagon formed."** On a given day, the first `seq` at which some single target is held by
**≥2 distinct accusers** — an "accuser of T" being any player who, in a non-passed message that day,
carries an `addressed_target` with `target==T` and `stance=="accusation"` (self-accusation
excluded). Recorded per (game, day); the game-level bandwagon is the earliest such day. (Chosen over
alternatives — vote-share threshold needs the vote, not discussion; ≥3 is too rare at 9-handed — as
the least-arbitrary discussion-time proxy for "a pile-on is underway.")

**(b) "Pending find."** At the start of day *D*, the investigator (alive) holds a confirmed
`investigator_results` entry with `role_revealed ∈ {wolf, serial_killer}` whose target is (i) still
alive at the start of day *D* and (ii) never lynched on any day `< D`, and whose result day
`≤ D−1` (i.e. already usable). "Confirmed find" for diagnostic C = any such threat result,
independent of a specific day.

**(c) Investigator "reveal."** Two forms, both text-matched on non-passed investigator-authored
day messages (role_claims is **not persisted in this epoch** — see the gate assessment / §4; a
conservative text match is the only available signal, reused from the shipped
`investigator_transmission.py` matcher):
- **Role claim** (generic): message contains a self-identification token
  (`i am the investigator`, `as the investigator`, `my role as investigator`, `i'm the
  investigator`, `my investigation`, `my findings`).
- **Find disclosure of target T** (specific, used for C's reveal/withhold split): message names T
  (`player_N` / `player N` / `playerN`) **and** carries an investigation-basis token
  (`investigat`, `i checked`, `i identified`, `confirmed`, `my result`, `scan`) **and** asserts T's
  found threat role (`wolf` / `serial killer` / `sk`). Requiring name + basis + threat together in
  one message is deliberately conservative: it under-counts disclosures split across turns (a
  known false-negative direction, reported as a bound, never as zero).

These are **descriptive** audits. Per §2's pre-committed discipline, no A–C finding is promoted to
"the scheduler hurts role X" — that is diagnostic D's job. Verdicts below read floor **access**, not
win cost.

### A · Floor-access audit — ran 2026-07-02, N=50 games (3843 non-narration entries, 890 passes)

`firing_reason.tier ∈ {reactive, proactive}` was verified in the records first: **every** non-narration
entry carries one (0 nulls in this epoch), and **all 890 passes are proactive-tier** — reactive turns
are never passed (the scheduler re-picks an un-discharged debtor, so a reactive pass is impossible by
construction). "Reactive/proactive share" below is of a role's *real* (non-passed) utterances; "pass
rate" is passes ÷ proactive offers (passes + proactive reals). Artifact:
[`data/floor_access.json`](data/floor_access.json).

| role | real utts | turns / alive-day | reactive share | proactive share | spoke-zero-day rate | pass rate (of proactive offers) |
|---|---|---|---|---|---|---|
| investigator | 380 | **2.45** | 0.40 | 0.60 | **0.10** | 0.19 |
| serial_killer | 441 | 2.15 | 0.36 | 0.64 | 0.17 | 0.28 |
| wolf | 669 | 2.04 | 0.45 | 0.55 | 0.16 | 0.35 |
| vigilante | 293 | 1.77 | 0.25 | 0.75 | 0.22 | 0.31 |
| villager | 926 | 1.73 | 0.16 | 0.84 | 0.21 | 0.27 |
| healer | 244 | 1.44 | 0.18 | 0.82 | 0.25 | 0.40 |

**Interpretation.** The two roles the hypothesis flagged as starvation-risk — investigator (info
injection) and wolf (steering) — are the *most* active and *least* silent, not the least. The
investigator leads every role on turns/alive-day (2.45) and has the lowest spoke-zero rate (0.10);
the wolf is third (2.04) at 0.16. Their higher **reactive** shares (0.40 / 0.45 vs villager 0.16) are
the mechanism *feeding* them the floor: power-role and wolf turns draw questions/accusations, and each
obligation is a guaranteed slot. The reactive-obligation channel the design worried would *crowd out*
initiative in fact *grants* these roles more floor than the quiet villagers get. Wolves also **decline
35% of the proactive offers they do get** — the opposite of a starved role. (Healer is the quietest /
highest-pass role, consistent with its optimal low profile — and not a role this workstream flagged.)

*Join (i) — investigator with a pending threat find → spoke before the vote?* **58 / 58 (100%).** On
every game-day an investigator held a usable, unlynched wolf/SK find, they took a non-pass turn before
that day's blind vote. Zero floor-starvation on the single most valuable information event in the game.

*Join (ii) — wolf → proactive floor before the bandwagon formed?* Of **85** game-days where a bandwagon
formed (§3a) with a live wolf at the table, a wolf held a **proactive non-pass turn before the pile-on
formed on 65 (76.5%)**; a wolf was *already* accusing someone before formation on 33 (38.8%). So on
~3/4 of pile-on days a wolf had an unforced slot to shape or start it. The log's `109/169` datum ("no
wolf among the accusers on most mislynch days") reproduces in *direction* here (wolves are among the
accusers pre-formation only 39% of the time) — but this audit shows that is **not for lack of floor**:
the proactive slot was there 76% of the time and the wolf didn't (or chose not to) use it to accuse.
Access is present; the accuse-or-not is behavior. *(Descriptive only — not a win claim; that is D.)*

**A verdict: no scheduler floor-starvation for any role, and specifically not for the two roles the
hypothesis targeted.** Investigators and wolves are floor-*rich*, pending-find investigators speak
100% of the time, and wolves had pre-bandwagon proactive floor on 3/4 of pile-on days. Channel #1
(reactive-crowds-out-initiative) is *falsified as an access effect* in this epoch — obligations feed
the power/wolf roles rather than starving them.

### B · Gate-silencing audit — ran 2026-07-02; verdict: UNMEASURABLE FROM RECORDS (instrumentation gap)

Establishing what is persisted first (the audit the design demanded): a novelty-gated pass and a
voluntary `pass_turn` are written by **one code path** (`Agents/turn/agent.py`) to an **identical**
`DayChannel(passed=True, message="", firing_reason=<proactive>)` marker — and the attempted-but-gated
candidate message is **discarded, never persisted anywhere**. The records confirm it: of all **890**
pass markers, **0** carry a non-empty message and **0** carry `addressed_targets`; all are
proactive-tier. Artifact: [`data/gate_silencing.json`](data/gate_silencing.json).

Consequence: from records we **cannot** separate "the gate silenced this turn" from "the agent
volunteered a pass" from "the agent was never offered the floor" (never-offered leaves no marker at
all). So B's core question — *does the novelty gate disproportionately eat wolf pile-ons / low-info
coalition turns?* — **is not answerable from the existing epoch.** The per-role pass-share-of-offers
(healer 0.40, wolf 0.35, vigilante 0.31, SK 0.28, villager 0.27, investigator 0.19) is the only census
available, and it **lumps gated + voluntary**, so it cannot attribute the wolf's 35% to the gate vs to
wolves genuinely having less to add on a quiet turn.

**This is itself the finding: the gate's selectivity is structurally invisible in the record.** The
fix is a small instrumentation change to **propose, not build in this workstream** — persist on the
pass marker (i) a `gated: bool` distinguishing gate-silence from voluntary pass, and (ii) the gated
candidate text + its `addressed_targets`, so a future audit can class *what the gate ate* by role and
stance. Until then B contributes only a bound: the gate *could* be role-selective and we would not see
it.

**[UPDATE 2026-07-02 — instrumentation built.]** The 2-field add proposed above is now shipped:
`DayChannel` carries `gated: bool` (novelty-gated silence vs voluntary `pass_turn`) and
`gated_candidate` (the discarded candidate text), set at the gate in `Agents/turn/agent.py`. The
candidate text is leak-guarded (persisted-but-hidden like `firing_reason`; the day-channel
formatters drop passed markers, and `tests/leak_test.check_gated_candidate_isolation` is the standing
guard). Gate selectivity by role/stance is therefore **measurable from the next generation batch
onward** — existing records still lack the fields, so this unblocks a FUTURE gate-selectivity audit
on new records only, not a re-run on this epoch.

### C · Reveal-vs-withhold decomposition — ran 2026-07-02; the unconverted finds are NOT a floor problem

54 distinct confirmed threat finds (deduped per target; wolf 37, SK 17) over the 50 games. **42
converted** to a lynch of the found player on/after the find became usable (**77.8%**); by role, wolf
finds convert **70.3%** (26/37), SK **94.1%** (16/17). The **12 unconverted** finds decompose (§3c
matched, conservative) as:

| class | count | share of unconverted | is it a scheduler-access failure? |
|---|---|---|---|
| **NO-FLOOR** (never got a non-pass turn while pending) | **0** | 0% | would be — but never occurs |
| **LATE-FLOOR** (spoke only after the target died / game decided) | **0** | 0% | would be — but never occurs |
| **WITHHELD** (had the floor, find pending, never hard-claimed it) | 7 | 58% | no — agent choice |
| **REVEALED-BUT-IGNORED** (disclosed the find, town didn't convert) | 5 | 42% | no — town behavior |

**Interpretation.** The scheduler-access explanation for the unconverted-find residual is **empty in
this epoch: NO-FLOOR = LATE-FLOOR = 0.** Every investigator with an unconverted find was on the floor
while the find was still actionable. The residual is entirely *WITHHELD* (the investigator spoke but
soft-pedaled — "I'm keeping an eye on player_8", "I'm watching player_4" — never hard-claiming the
confirmed read; verified by eyeballing all 7 transcripts) or *REVEALED-BUT-IGNORED* (hard-claimed, town
still didn't remove them). Critically, the conservative reveal-matcher's error only shuffles cases
**between** WITHHELD and REVEALED-BUT-IGNORED (an under-detected disclosure lands in WITHHELD) — it can
**never** move a case into NO-FLOOR/LATE-FLOOR, which are computed from floor timing, not text. So the
"not a scheduler problem" conclusion is robust to matcher noise; only the WITHHELD-vs-ignored split is
soft. `role_claims` is **not persisted in this epoch** (`day_summaries[].structured == {}` for all 50
games), so text-matching was the only route; of the 12 unconverted-find investigators, only 5 made even
a generic role claim.

**Reconciliation note.** This validation set gives **70% wolf-find conversion**, not the log's cited
"40% of confirmed wolves never lynched" (= 60% converted). **[RESOLVED 2026-07-02 — see ③.D below.]**
Both numbers are correct on different sets: the cited 60% is the **v6ab (180-game)** wolf-only
per-game-mean; this audit's 70% (wolf) / 77.8% (threat, wolf+SK) is the **v5 (50-game)** set. The gap
decomposes cleanly into set + aggregation + role-scope — no bug behind either figure.

**C verdict: investigator non-conversion is an agent/town phenomenon, not a scheduler artifact** — the
third of the log's three candidate explanations ("got the floor and withheld") plus a fourth the design
named ("revealed but town ignored"), with the two access explanations ("couldn't get the floor", "got
it too late") measuring **exactly zero**.

### §2 gate assessment — does A–C justify diagnostic D? Recommendation: **mostly NO, one narrow caveat.**

Recommendation (not a decision — D is a spend + fresh-games call the user owns):

- **The floor-access arm of D (the role-blind "last-words" pre-vote round) is NOT justified.** D is
  gated on A–C finding a real access problem, and they find none: investigators and wolves are the
  floor-richest roles (A), pending-find investigators speak 100% before the vote (A join i), wolves
  hold pre-bandwagon proactive floor on 76% of pile-on days (A join ii), and unconverted finds have
  **zero** no-floor/late-floor cases (C). A "give every quiet agent one more proactive offer" variant
  targets a starvation that isn't there — the agents who fail to convert **already had the floor** and
  either withheld or were ignored. A last-words round would not move those.
- **The gate-off arm of D is DEFERRED, not refused — behind the B instrumentation change.** B is the
  one live question A–C could not close: the novelty gate's role/stance selectivity is unmeasurable
  from the current record. The correct next step is the cheap 2-field instrumentation change (propose,
  §B), re-run a handful of games, and *then* decide whether a gate-off arm is worth it. Running a
  gate-off A/B now would be premature — we don't yet know the gate silences anything role-relevant.

Net: **do not open the scheduler-redesign / last-words D on access grounds; do the B instrumentation
first and let it decide whether any gate-question D follows.** The rebuild gate (§2) stays closed — no
A–C finding shows access changes would move outcomes, because access is not the binding constraint.

### ③.D · Reconciliation of the 60% vs 78% find-conversion figures (2026-07-02, $0, both sets, ZERO LLM)

Re-sourced by running every definition on BOTH validation sets (`investigator_results` → the
`day_resolutions` lynch join, no LLM). **Both headline numbers are correct — they measure different
things on different sets; neither is a bug.**

| figure (as cited) | set | role scope | grain | aggregation | value |
|---|---|---|---|---|---|
| "~0.60 / 40% never lynched" (`../town_metric_refinement.md`) | **v6ab (180)** | wolf-only | per-find-night | **per-game mean** | **0.601** |
| "77.8%" (§3C above) | **v5 (50)** | **threat = wolf+SK** | dedup-by-target | pooled | 0.778 |
| wolf-only sub-rate (§3C above) | v5 (50) | wolf-only | dedup-by-target | pooled | 0.703 |

- **"n=117" is 117 GAMES, not 117 finds.** On v6ab, 117 games carry ≥1 wolf find (the per-game
  correlation's N) — there are 138 wolf find-nights / 135 deduped. `town_metric_refinement.md`'s
  "n=117 finds" is loose wording for "117 games with a find"; its rate (0.601 = per-game mean) and
  its N (117 games) both reproduce exactly, so its number is **correct for its (v6ab) set**.
- **The 60→78 gap decomposes into three independent axes** (each measured apples-to-apples):
  - **SET** — wolf-only per-game-mean is **v6ab 0.601 vs v5 0.65** (~+5pp; a genuine epoch difference,
    the same cross-epoch drift the sibling log flags).
  - **AGGREGATION** — per-game-mean → pooled, v5 wolf: **0.65 → 0.711** (~+6pp; long games with many
    finds pull the pool up).
  - **ROLE SCOPE** — adding the SK (which converts **16/17 = 94%**) to the wolf pool, v5: wolf pooled
    **0.711 → threat 0.778** (~+7pp). The §3C "77.8%" is a *threat* figure.
  - The **off-by-one lynch window** (`>=find_day` vs `>=find_day+1`) and **dedup-by-target vs
    per-find-night** each move it **<1pp** on both sets (no wolf is lynched the same day its find lands).
- **Which number for which claim.** "40% of confirmed wolves never lynched" is the **v6ab wolf-only**
  bottleneck and must be cited as v6ab — on this workstream's own **v5** set the wolf-conversion rate
  is **~70%** (~30% unlynched, dedup 70.3% / per-find 71.1%). The audit's **77.8%** is a **wolf+SK**
  rate inflated by the SK's 94%; the comparable wolf-only v5 figure is **70.3%**.
  `../town_metric_refinement.md` is left **unchanged** (its 0.60 is right for its set — frozen
  evidence); only the §1 citation here, which quoted the v6ab "40%" while running on v5, is corrected
  in place.

*Runner: [`evaluation/src/experiments/scheduler_access_audit.py`](../../../evaluation/src/experiments/scheduler_access_audit.py)
(`floor-access` / `gate-silencing` / `reveal-withhold` / `all`); logic tests
`tests/test_scheduler_access_audit.py` (11, synthetic fixtures, no LLM). Artifacts in
[`data/`](data/). Ran 2026-07-02 at repo `4b1449e` (uncommitted tree). Zero LLM calls.*

### ③.E · Whiff-conversion audit — does the attacker convert a silent whiff into action? (2026-07-02)

The §1 SK–wolf information-design gap, measured directly. When an attacker (wolf night-kill /
vigilante shot) hits the night-immune SK, the attack silently whiffs. This beat asks: does the
attacker convert that private event into action, and if not, which layer fails — **visibility**
(what the attacker sees), **behavior** (whether it acts), or **floor** (whether it had the
opportunity)? It is the diagnostic that prices the held change **E** (whiff disclosure): a low
conversion rate caused by *visibility* supports E; one caused by *behavior* does not.

Runner:
[`evaluation/src/experiments/whiff_conversion_audit.py`](../../../evaluation/src/experiments/whiff_conversion_audit.py)
(sibling module — reuses `scheduler_access_audit`'s record-loading + timeline machinery by import;
kept separate because it runs on BOTH validation sets, not the 50-game access set, and its concern
— attacker conversion — is orthogonal to floor access). Logic tests
`tests/test_whiff_conversion_audit.py` (synthetic fixtures, no LLM). Artifact
[`data/whiff_conversion.json`](data/whiff_conversion.json).

**Pre-registration — definitions committed before computing any conversion outcome (2026-07-02).**
Committed after verifying the whiff mechanic *in code* (`Agents/nodes/night/resolution.py`) and the
record fields (`night_resolutions[]`), but before joining any conversion.

- **(a) "Whiff event" — verified in code, not assumed.** SK night-immunity resolves at
  `resolution.py:92-100`: `_resolved(target)` returns `"immune"` when `target == sk_player`
  (checked *before* the heal check), the immune target is excluded from `deaths`, and the whiff is
  **silent** (`:149` `continue` — no death line; if it was the only attack, the GM prints "No one
  died last night", `:164`). The record signature is therefore *not* a dedicated flag but a JOIN:
  a **target-survived event** = an attacker's target that is set but absent from `deaths`
  (equivalently `kill_successful == False` for the wolf, `vigilante_kill_landed == False` for the
  vigilante). Per `_resolved`, a target survives for **exactly two** reasons — immune or healed —
  giving the ground-truth split below.
- **(b) Comparison class — target-survived events, split by ground truth.** All target-survived
  events look observably identical to the attacker (no death announced for their target); their
  ground truth differs. **SK-whiff** = `wolf_target_role == "serial_killer"` (resp.
  `vigilante_target_role`), checked first. **HEALED-survival** = the fallback (`healer_saved` for
  the wolf; `vigilante_target == healer_target` for the vigilante). Conversion is measured on ALL
  target-survived events with the SK subset as the ground-truth split — the healed subset is the
  built-in control (same public signal, different truth).
- **(c) Conversion window + actions.** Window = whiff night *N* (usable from **day N+1**, per the
  §3 timeline convention) → game end. Events deduped per (game, attacker-faction, target) keeping
  the **earliest** whiff night, so the window is well-defined (raw per-night count also reported).
  Conversion actions: **accuse** the target (a living attacker carries an `addressed_target` with
  `target==T`, `stance=="accusation"` on a day ≥ N+1) OR **vote** the target
  (`day_resolutions[].votes` with `voter ∈ attackers`, `votee==T`, day ≥ N+1). **Primary
  conversion = accuse-OR-vote** (day-steering onto the SK — the play E enables). **Night re-target**
  (attacker re-targets T on a later night) is reported *separately*, NOT as conversion: for the wolf
  it is a futile re-attack on the immune SK (evidence of NON-learning); for the vigilante likewise.
  The wolf "attacker" is the PACK — any living wolf accusing/voting T counts (the kill was a pack
  decision).
- **(d) Base rates.** (i) The attacker's rate of accusing/voting *that same player* BEFORE the whiff
  (days ≤ N) — controls for pre-existing suspicion. (ii) The attacker's rate of accusing/voting
  *any non-whiffed* player after the whiff — the general-propensity floor that separates "didn't
  convert" from "never accuses anyone".
- **Small-N discipline (committed up front).** Whiffs are rare. From the field scan the expected N
  is ~19 (v5) / ~85 (v6ab) wolf SK-whiffs and ~8 / ~9 vigilante SK-whiffs (per-night, pre-dedup).
  Results are reported **direction-only** — no significance tests, no p-values; the healed-survival
  control and the pre/post base rates carry the inference, not thresholds. Sets kept separate;
  within v6ab, memory-arm siblings share `game_id` (6 arms × 30 seeds) so events are correlated
  across arms — v6ab N is not 6× independent.
- **Side-read (reasoning scan, keyword heuristic — NOT a judge).** Where eval-case sidecars exist
  (v6ab only — v5 has none), scan the attacker's post-whiff `updated_strategy` / `previous_strategy`
  text for the survived-target inference: a target-name form (`player_N` / `player N` / `playerN`)
  co-occurring with an inference token (`survive`, `immune`, `failed`, `heal`, `didn't die`,
  `unharmed`, `still alive`, `no one died`, `couldn't kill`, `blocked`, `protected`, …) in the SAME
  strategy field. Conservative (whole-field co-occurrence, one field). Split: never-mentions vs
  mentions-but-doesn't-act vs mentions-and-acts.

### ③.E-results · ran 2026-07-02 — the binding layer is VISIBILITY (both sets, ZERO LLM)

Ran on both sets (v5 N=50, v6ab N=180). Artifact
[`data/whiff_conversion.json`](data/whiff_conversion.json). Rates are on **deduped** events (per
game × attacker × target, earliest whiff night); raw per-night N in the first column.

**Layer 1 — VISIBILITY (the decisive read; a code/payload fact, not a record statistic).** The two
attackers see *categorically different* things after a whiff:

- **Wolf: NO explicit signal — inference-only, and even the inference is blind.** SK-immunity
  resolves at `Agents/nodes/night/resolution.py:92-100`; the immune outcome is DROPPED from the GM
  announcement (`:149` `continue`) and, if the whiff was the only attack, the GM prints "No one died
  last night" (`:164`). The wolf's own target is available (it persists in `wolf_channel`, which
  accumulates all game and is replayed into every wolf-night payload), but **nothing tells the wolf
  the kill failed**, and it cannot even distinguish heal from immune from public info. Crucially, a
  **healed** survival IS announced ("player_X was attacked by the wolves but was saved by the
  healer!", `resolution.py:152-155`) — so the pre-registered "observably identical" assumption is
  **falsified in place: the healed control is MORE visible than the silent whiff, not equal**. That
  makes the two survival types a within-wolf visibility contrast, which the reasoning scan exploits
  below.
- **Vigilante: EXPLICIT, pre-disambiguated signal.** `resolution.py:139-143` writes a private note
  on an immune outcome — "you shot T, but they were unharmed — immune to night kills, which confirms
  T is the serial killer" — fed into the next vigilante prompt (`prompts/night.py:124`); a heal does
  NOT trigger it (`:138`), so no false positive. The bullet is spent on the whiff either way
  (`:133-134`). The vigilante is handed the SK identity outright. **Change E is a WOLF-side
  disclosure; the vigilante already has it** — which makes the vigilante a built-in natural
  experiment for "what happens when you DO disclose."

**Layer 2 — BEHAVIORAL CONVERSION.** Conversion = accuse-or-vote the target on day ≥ N+1
(dedup rate). `pre` = same-target accuse/vote before the whiff; `other` = accused/voted *some other*
player post-whiff (general propensity); `retgt` = re-targeted at night (futile).

| set | attacker | truth | N raw/dedup | **converted** | accuse / vote | pre (same tgt) | other | night re-tgt | floor-had |
|---|---|---|---|---|---|---|---|---|---|
| v5 | wolf | **SK-whiff** | 19/14 | **0.71** | 0.29 / 0.64 | 0.29 | 0.93 | 0.29 | 1.00 |
| v5 | wolf | healed | 52/37 | 0.57 | 0.46 / 0.43 | 0.22 | 0.84 | 0.43 | 0.97 |
| v5 | **vig** | **SK-whiff** | 8/8 | **0.75** | 0.75 / 0.75 | **0.00** | 0.25 | 0.00 | 0.75 |
| v5 | vig | healed | 7/7 | 0.14 | 0.14 / 0.14 | 0.29 | 0.86 | 0.00 | 0.86 |
| v6ab | wolf | **SK-whiff** | 85/66 | **0.58** | 0.21 / 0.53 | 0.20 | 0.77 | 0.24 | 0.88 |
| v6ab | wolf | healed | 167/123 | 0.38 | 0.22 / 0.34 | 0.15 | 0.95 | 0.48 | 0.98 |
| v6ab | **vig** | **SK-whiff** | 9/9 | **0.89** | 0.89 / 0.89 | 0.11 | 0.00 | 0.00 | 0.89 |
| v6ab | vig | healed | 3/3 | 0.33 | 0.00 / 0.33 | 0.33 | 0.67 | 0.00 | 0.67 |

*Interpretation (direction-only; small N, esp. vigilante).* The **vigilante is the clean signal**:
SK-whiff conversion is **0.75 / 0.89** — lifting from a **~0 pre-rate** (0.00 / 0.11) — versus its
healed control at **0.14 / 0.33**. Given explicit disclosure, the attacker DOES convert. The **wolf's
higher-looking rate (0.71 / 0.58) is confounded and mostly NOT whiff-driven**: (i) the target IS the
SK, a genuine threat town votes anyway, so a blending wolf's vote is caught even without noticing the
whiff (note vote ≫ accuse, 0.53 vs 0.21 on v6ab — passive vote-following, not active steering);
(ii) the wolf's lift over its *healed* control is only +0.15 / +0.19, and the healed control is
itself *more visible* (announced) — so the small gap is not clean conversion. The wolf converts on an
SK-whiff at barely more than it converts on a random announced heal.

**Layer 3 — FLOOR.** `floor-had` is **0.75–1.00** across every row — the attacker almost always took
a non-pass turn in the conversion window. Floor is **not** the binding constraint (same WS2-A
finding, same known limit: never-offered turns are only structurally inferable, not counted here).

**Side-read — reasoning scan (v6ab sidecars, 180/180 games; keyword heuristic, NOT a judge).** Split
by ground truth (does the attacker's post-whiff strategy text even *mention* the survival inference?):

| attacker | truth | never-mentions | mentions, no act | mentions & acts |
|---|---|---|---|---|
| wolf | **SK-whiff** | **45 (68%)** | 2 | 19 |
| wolf | healed | 38 (31%) | 46 | 39 |
| vig | **SK-whiff** | 1 (11%) | 0 | 8 |
| vig | healed | 1 | 1 | 1 |

This is the crux. On a **silent SK-whiff the wolf NEVER NOTICES 68% of the time** (never mentions the
survival at all); on an **announced heal it never-mentions only 31%** — the wolf's noticing rate
**tracks visibility** directly, within the same role. The vigilante, handed an explicit note,
notices-and-acts on 8/9 SK-whiffs. Sample wolf lines confirm the mechanism: on *healed* survivals the
wolf reasons explicitly about the announced save ("the healer's save of player_1", "since player_1
was protected"); on *silent whiffs* the survival simply never enters the note. So the wolf's failure
is **"never noticed" (→ disclosure fix), not "noticed, didn't convert" (→ prompt fix)** — of the
wolves that DID notice (21/66), 19 acted.

**Verdict — the binding layer is VISIBILITY.** Floor is present (Layer 3 ≈ 1.0); behavior is willing
(the vigilante, given the info, converts 0.75–0.89 from a ~0 base — Layer 2); the wolf fails at
**Layer 1** — it is told nothing, and the reasoning scan shows it never notices the whiff 68% of the
time, a rate that moves with visibility (31% on the announced heal, 11% for the vigilante's explicit
note). **Implication for the held change E (recommendation, not a decision — E is an epoch-reset
game-design call the user owns):** the diagnostic **SUPPORTS E**. The wolf→SK conversion lever is
gated by information design, not by wolf skill or scheduler floor, and the vigilante is a live proof
that disclosing the whiff produces conversion. E should disclose the *fact of a failed/immune kill*
to the wolf (mirroring the vigilante's note) — but priced honestly at the pre-registered epoch reset,
and its effect measured on fresh games (behavior change, not replayable).

*Runner:
[`evaluation/src/experiments/whiff_conversion_audit.py`](../../../evaluation/src/experiments/whiff_conversion_audit.py)
(`run`); logic tests `tests/test_whiff_conversion_audit.py` (10, synthetic fixtures, no LLM).
Artifact [`data/whiff_conversion.json`](data/whiff_conversion.json). Ran 2026-07-02 at repo `4b1449e`
(uncommitted tree). Zero LLM calls.*

## §4 · Limitations known at design time

- A and C depend on self-labeled `addressed_targets` (tuned for scheduling, not measurement); the
  scheduler's own report records a mislabel→domination residual. Audit results inherit that label
  noise, and B's denominators depend on whether gate/pass events were persisted at all.
- "Bandwagon formed" (diagnostic A's wolf join) needs a pre-registered deterministic definition
  (e.g. first day-moment a target holds ≥2 accusers) — decide before looking at data.
- D's ~$5–10 read is directional at best (N≈10–20 games); it screens for a large access effect,
  it does not size one.
- All findings are epoch-stamped to the current scheduler config (`per_pair_reengagement_cap=2`,
  `reengagement_cooldown_multiplier=1.0`, `opener_floor=3`); the tunables were never swept, which
  is itself a recorded gap in the scheduler report.

**Surfaced by the A–C run (2026-07-02):**

- **[B-blocking] Pass provenance is not persisted — the gate is measurement-invisible.** A
  novelty-gated pass and a voluntary `pass_turn` are the same `passed=True`/empty-message/proactive
  marker (`Agents/turn/agent.py`); the gated candidate text is discarded. So *which* turns the gate
  ate, and their stance/role, cannot be recovered from any existing record — B is answerable only
  after a small instrumentation add (a `gated` flag + the gated candidate on the pass marker). This
  is the single hardest blocker the audits hit and it caps B at a bound, not a measurement.
- **[C-blocking] `role_claims` is empty for the whole epoch.** `day_summaries[].structured == {}`
  for all 50 validation games (and every other batch file checked), so C's reveal detection had to
  fall back entirely to conservative text-matching. The matcher under-counts disclosures split
  across turns (false-negatives → WITHHELD), so the WITHHELD-vs-REVEALED-BUT-IGNORED split is soft;
  the NO-FLOOR/LATE-FLOOR classes are text-independent (floor-timing only) and therefore firm.
- **[label-noise, as flagged at design time] A/C inherit `addressed_targets` mislabels.** Both the
  bandwagon definition (accusation stance) and the reactive/proactive tier attribution ride the
  model's self-labeled speech-acts; the scheduler report's domination residual is the same noise.
  Direction of the audit conclusions (roles floor-*rich*, access-classes empty) is robust to it;
  point shares (e.g. exact reactive/proactive split) are not exact.
- **[reconciliation RESOLVED 2026-07-02, ③.D] The 70% (v5 wolf) / 77.8% (v5 threat) / 60% (v6ab
  wolf) figures are all correct on their own set × role-scope × aggregation** — decomposed in ③.D
  into SET (~+5pp) + AGGREGATION per-game-mean→pooled (~+6pp) + ROLE-SCOPE adding the SK at 94%
  (~+7pp); the off-by-one lynch window and dedup-vs-per-find are each <1pp. The "40%" is the v6ab
  wolf-only per-game-mean and is now cited as such (§1 correction).

**Surfaced by the whiff-conversion run (③.E, 2026-07-02):**

- **[pre-reg falsified in place] The healed control is NOT observably identical to the whiff.** ③.E-b
  pre-registered healed survivals as the visually-identical comparison class. In fact a heal is
  *announced* ("saved by the healer", `resolution.py:152-155`) while the SK-whiff is *silent* — the
  healed control is MORE visible. This does not break the audit; it repurposes the two survival types
  as a within-wolf visibility contrast (the reasoning-scan never-mentions rate, 31% healed vs 68%
  whiff, is exactly that contrast) and makes the *vigilante* SK-whiff-vs-healed the clean same-role
  Layer-2 control instead.
- **[N + confound] The wolf conversion rate is not clean whiff-conversion.** Because the whiff target
  IS the SK (a threat town votes anyway), a blending wolf's day-vote is scored as "converted" without
  the wolf ever noticing the whiff (vote ≫ accuse). The load-bearing wolf evidence is therefore the
  reasoning scan (does it *notice*), not the conversion rate. Vigilante N is tiny (8/9 SK-whiffs) —
  direction-only, reported as such.
- **[coverage] The reasoning scan is v6ab-only.** The v5 set predates local eval-case emission (no
  sidecars; `eval_cases_path` absent), so the "noticed vs converted" split exists only on v6ab
  (180/180 games). v5 carries Layers 1–3 but no reasoning read.
- **[matcher] The reasoning scan is a conservative keyword heuristic, not a judge.** Whole-field
  co-occurrence of a target-name form with an inference token; it under-counts obliquely-worded
  inferences (false-negative direction on "noticed") and never inspects semantics — a bound on the
  never-mentions rate, not an exact count.

*Opened 2026-07-02 at repo `4b1449e` (uncommitted working tree). Diagnostics A–C ran the same day
(runner `evaluation/src/experiments/scheduler_access_audit.py`, 50-game v5 validation set, zero LLM
calls); results + gate assessment in §3. The whiff-conversion beat (③.E, runner
`evaluation/src/experiments/whiff_conversion_audit.py`, both sets, zero LLM) ran the same day — its
verdict: the binding layer is VISIBILITY, which SUPPORTS the held change E (recommendation only).*
