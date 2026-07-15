# Role-fact hallucination census — v2_full

**Verdict first.** Once private reasoning is measured, role-fact hallucination is **not rare**.
Across all 50 `v2_full` games in both paired arms (epoch 2026-06-22, pre-dead-roster prompt), the
pipeline scanned 7,846 agent text units and confirmed hallucinations on two surfaces. On public
chat, about **68 genuine cases of 90 machine-confirmed over 2,292 messages** — roughly **3.0% of
messages** carry a role-fact error. On private strategy notes, **278 machine-confirmed over 5,554
notes**, and a sampled precision of about 0.8 puts the genuine count near **222 — roughly 4.0% of
notes**. The single worst surface is the night-action note: **113 of 1,179 ≈ 9.6%** carry an error
(about 7.7% after the precision adjustment), against 3.9% for day-discussion notes and 3.3% for
day-vote notes. The night prompt is also the one surface that currently carries no dead-roster
board, so this number directly answers the plan's day-versus-night question. The dominant error is
composition arithmetic (wrong remaining-count claims), which is 221 of the 368 machine-confirmed
positives. These rates revise the board's premise **upward**: the earlier "rare" reading was an
artifact of measuring only public chat with a leaky candidate set, not a property of the games.

This document is the standing census for role-fact hallucination — the surface a re-run measures
after any prompt change, not a one-off baseline. Below: how the four-stage pipeline produces the
numbers, the funnel it runs, what the confirmed errors look like, how this relates to the earlier
manual baseline, and what the instrument still cannot see.

## The pipeline — four stages, each doing only what it can do reliably

The work splits by reliability. A deterministic screen finds candidates and can prove it missed
none within its scope. A cheap reader then judges meaning, which no parser can. A stronger reader
tightens precision, and a human checks the machine.

### Stage 1 — find every text that touches a checkable fact

The screen (`evaluation/src/audits/role_hallucination_screen.py`, console
`eval-role-hallucination`, zero-LLM) flags every text unit that names an entity or states a count
the structured game record can contradict. Four anchors fire: a mention of a dead player id (692
units), a role word whose holders are all dead (2,182), an explicit count claim that mismatches the
true alive count (395), and a claim-attribution absent from the logged claim record (244). The
count anchor reads spelled numbers, "both", and the definite singular ("the remaining wolf",
treated as exactly one); bounded phrasing like "at least one" is excluded because it asserts no
count. The design reason for anchoring on entities and counts is a recall guarantee. Player ids and
role words form closed sets that can be matched exhaustively, so **any hallucination that names a
dead entity or states a count is caught by construction** — the screen never has to guess how an
error might be worded. What this guarantee excludes is stated plainly under limitations: an
anchor-less fabrication, such as "the guy we lynched" or an invented event that names no id or role
word, has nothing to anchor on and is out of scope by design.

Two other checks run here as deterministic verdicts rather than candidates: whether any vote was
cast for a dead player, and whether any question or response was addressed to one. Both found
**zero violations** across the corpus.

### Stage 2 — throw away only what is provably fine

The same module drops only candidates it can prove legitimate. Game-master messages are excluded
outright, because GM text is rendered from state and cannot hallucinate; this is why the 2,292
scanned public messages carry no GM lines. A count claim that matches the true alive count is
dropped. Nothing is discarded on position or phrasing, because a "the early turns just recap the
GM" filter would throw away wrong recaps, and a wrong recap is exactly the attacker-misattribution
error. After stage 2, **2,461 units remain as candidates** — 39% of messages and 28% of notes.

### Stage 3 — a cheap LLM reads the rest against a fact sheet

The reader (`evaluation/src/judges/role_fact_read.py`, console
`eval-role-hallucination-read`) judges each candidate against a deterministic fact sheet built from
the game record: deaths with their revealed role, day, and attacker; the alive players and per-role
counts; the per-day public vote records; the logged role-claims; and the speaker's own first-hand
knowledge, meaning a wolf's pack roster, an investigator's checks, and the speaker's own night
actions. No transcript is sent, so the judgment is text against facts. The reader returns one of
four verdicts: consistent, hallucination, deliberate_deception, or ambiguous. The deception verdict
is deliberately narrow. It applies **only to a public message that contradicts the speaker's own
private knowledge**, such as a wolf misstating its dead packmate's role. Misstating a *public* fact
counts as a hallucination even for an evil role, because forgetting a public fact is exactly the
failure being measured and cannot be told apart from strategic lying about it. A private note can
never be deception, because a note has no audience. The output schema puts the reasoning before the
verdict, the same commitment ordering the game schemas use.

The reader is a cascade of two models, and the reason is a calibration finding. A 23-case golden
set was assembled from confirmed hallucinations, one known wolf lie, true and false claims verified
against the vote record, and known-legitimate retrospection windows. Across four calibration
rounds, `gemini-3.1-flash-lite` caught every golden hallucination but over-called fine
distinctions, while `gemini-3.5-flash` handled the fine distinctions but occasionally missed a
positive between runs. So flash-lite (temp 0) reads all 2,461 candidates as the recall layer, and
3.5-flash re-reads only flash-lite's positives as the precision layer. The recall model is allowed
to over-flag because the precision model cleans up after it.

### Stage 4 — a human checks the LLM's positives and a sample of its negatives

The owner read every stage-2 positive on public chat and sampled the rest (2026-07-08). All 90
public-message positives were read. A sample of 25 of the 278 private-note positives was read, and
a sample of 15 of the 273 units the precision model *rejected* was read to estimate misses. The
results feed the human-adjusted point estimates below and set the honest error bars.

## The funnel

The overall funnel narrows from 7,846 scanned units to 368 machine-confirmed positives. Each stage
removes what the previous one could not yet rule out: stage 1 keeps only checkable text, the recall
reader keeps only apparent errors, and the precision reader discards the recall model's over-calls.

| stage | what remains | units |
|---|---|---|
| scanned | all agent text (GM excluded) | 7,846 |
| stage 1–2 — deterministic candidates | touch a checkable entity or count | 2,461 |
| stage 3 — flash-lite positives (recall pass) | 610 hallucination + 31 deception | 641 |
| stage 3 — 3.5-flash positives (precision pass) | 361 hallucination + 7 deception | 368 |

The precision pass matters: it removed 273 of the recall model's 641 flags as consistent on
re-read, which is why the recall model can be run hot without inflating the reported rate. The 368
survivors split 90 on public chat and 278 on private notes, and the human read then adjusts each
surface differently, because the public positives were read in full while the private positives
were sampled.

| surface | units scanned | machine positives | genuine (adjusted) | rate |
|---|---|---|---|---|
| public chat | 2,292 | 90 | ≈68 (all 90 read) | ≈3.0% |
| private notes | 5,554 | 278 | ≈222 (0.8 sampled precision) | ≈4.0% |

Read the two rates as directions you can trust and magnitudes you should hold loosely. The public
rate rests on a full read of all 90 positives, so ~3.0% is well grounded. The private rate rests on
a 25-item precision sample, so ~4.0% is a point estimate with real sampling uncertainty, not a
measured share. The direction is the finding: private notes hallucinate at least as often as public
chat, and probably more.

## Findings

**Class mix.** Of the 368 machine-confirmed positives, composition arithmetic dominates at 221 —
wrong remaining-counts and phantom "remaining wolf" claims. The rest: 57 treat a dead player as
alive (dead_as_alive), 59 are "other" (mostly fabricated vote records, such as an agent claiming it
abstained when the record shows it voted, plus fabricated attack events), 18 misattribute a
role-claim (claim_attrib), and 13 misstate a dead player's revealed role (dead_role). Composition
being the largest class by a wide margin is what tells us the alive-roles line targets the right
error: a printed cast-minus-dead composition makes remaining-count arithmetic trivial.

**Night is the worst surface.** Splitting the 278 private-note positives by phase shows night
reasoning failing more than twice as often as day reasoning.

| note phase | units scanned | machine positives | rate |
|---|---|---|---|
| day-discussion | 3,210 | 126 | 3.9% |
| day-vote | 1,165 | 39 | 3.3% |
| night-action | 1,179 | 113 | 9.6% (≈7.7% adjusted) |

The night prompt is the only one of the three that carries no dead-roster board today. The 9.6%
machine rate is direct evidence for extending the board to night, which the earlier plan could only
pose as a question.

**Errors cluster within a game-day.** Confirmed errors are contagious: one agent's phantom-wolf
premise spreads through that day's discussion. The worst clusters are 24 positives in a single
game-day (gen5_g3 all_enabled, day 4), then 16 and 12 in gen4_g3 day 5 across its two arms, and 11
in gen2_g1 day 4. A single false composition premise, once spoken, becomes the room's shared
starting point.

**Deception is held separate from hallucination.** The speaker-knowledge check keeps a strategic
lie out of the hallucination count. Only 7 of the 368 positives are labelled deliberate_deception,
all public messages that contradict the speaker's own private knowledge. A wolf misstating a fact
it knows is deception, not a memory failure, and it does not count toward the hallucination rate.

**Lifted examples.** Three confirmed cases, quoted verbatim:

- A wolf's private note: *"I have successfully maneuvered player 1 out of the game, leaving only 7
  and 8"* — while player_1 was still alive.
- An investigator's private note: *"With both wolves eliminated, my primary objective is now to
  identify the Serial Killer"* — while a wolf was still alive.
- A villager's public message: *"cleared out two wolves, but … the remaining wolf"* — with zero
  wolves left, a self-contradictory composition claim.

A fourth, from a vigilante's note, cites *"the healer's save on me"* after the vigilante had itself
shot the healer — a fabricated event contradicting the speaker's own action.

## Relation to the earlier manual baseline

The previous manual measurement confirmed 4 public-message cases, about 0.14 per 100 messages.
Re-verification against the per-arm records **refuted one of those four**. The old "case 4" quoted a
note saying "wolves killed player_2", which described the *other* arm's night; in the case's own
game the serial killer really did kill player_2, so the agent's statement was true. The old true
set is therefore 3, all composition. Do not cite 0.14/100 as a current estimate — it stands only as
a superseded floor.

The new public-chat rate is roughly 20× higher on the same surface, for two reasons stated plainly.
First, the candidate set is now provably complete over named entities and counts, whereas the old
pattern set demonstrably leaked. Second, an LLM reader can judge the 2,461 windows the screen
surfaced, where the manual read could only work through 171. The jump is a measurement improvement,
not a change in the games.

## Limitations

Ordered by criticality; freshness 2026-07-08.

1. **Anchor-less fabrications are out of scope by design.** An error that names no dead id and no
   role word — a pronoun reference, an invented event — has nothing for the screen to anchor on and
   is never surfaced. The census measures errors *about named entities and counts*, and says so.
2. **The fact sheet lists deaths only, so failed or unseen night attacks are unverifiable.** A
   claim like "the wolves tried to hit X and failed" cannot be checked against a sheet that records
   only who died. This is the main "uncertain" residue in the human read (about 9 of the 90 public
   positives).
3. **Same-day role-claims are invisible to the claims log.** The log is compiled at each day's end,
   so a claim made earlier the same day is not yet in it. This makes claim_attrib the weakest class;
   in the sample, a "confirmed villager" attribution often traced to an unlogged in-chat
   investigator report.
4. **The confirmed counts are floors-to-midpoints, not ceilings, and the private rate rests on a
   small sample.** In the 15-unit rejection sample, about 2–3 of the precision model's rejections
   were wrong misses — including one wolf publicly "hunting the final wolf" while being the final
   wolf, a composition-lie that should have read deliberate_deception. The precision model discards
   some real errors, so the reported counts understate. And the private-note precision of ~0.8 rests
   on 25 sampled items, so its magnitude carries genuine sampling uncertainty.
5. **The rates are per-unit shares on one epoch.** They describe the `v2_full` corpus under the
   2026-06-22 prompts. Re-run the standing audit plus the reader on any post-ship batch to
   re-measure.

## Decision

The census revises the board's premise upward but does not by itself change the ship decision, which
T1b already settled. Role-fact hallucination is common once private reasoning is in scope, so the
board is justified by a real and sizeable problem, not a face-valid hunch. The dead-roster board
still ships as cheap hygiene rather than a proven fix: T1b's finding stands that an explicit correct
board did not stop the one recurring composition case (`validation/t1b_results.md`, unchanged).
Composition being the dominant class (221 of 368) confirms the alive-roles line aims at the right
error. The night-note rate of 9.6% is new, direct evidence for extending the board to the night
prompt, which currently has none. The suspicion read list's hypothesis strengthens: free-text
private notes carry stale and false beliefs forward, so a forced per-player structured commitment
with a composition-coherence check is the fix now under test (T3(b)). The attacker-typed roster
keeps zero confirmed motivating cases after case 4's refutation, but it costs nothing and stays.

---

*Corpus: 50 `v2_full` games × 2 paired arms, epoch 2026-06-22. Census run 2026-07-08. Screen:
`evaluation/src/audits/role_hallucination_screen.py` (console `eval-role-hallucination`, zero-LLM,
11 unit tests). Reader: `evaluation/src/judges/role_fact_read.py` (console
`eval-role-hallucination-read`, 5 unit tests on its deterministic fact sheet + the 23-case golden
calibration gate),
cascade of `gemini-3.1-flash-lite` (temp 0, recall) then `gemini-3.5-flash` (precision). Pipeline
cost ≈ $3–5, ~25 minutes. Artifacts: [hallucination_candidates.jsonl](hallucination_candidates.jsonl)
(stage 1–2), [hallucination_verdicts.jsonl](hallucination_verdicts.jsonl) (flash-lite recall pass),
[hallucination_verdicts_stage2.jsonl](hallucination_verdicts_stage2.jsonl) (3.5-flash precision
pass). Method and pre-registration: [../validation_plan.md](../validation_plan.md) T1. Re-run
post-ship on any new batch via the two consoles above.*
