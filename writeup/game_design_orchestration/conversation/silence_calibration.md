# Deciding when an agent should speak

*Level 3 · [Game design and orchestration](../game_design_orchestration.md) · parent: [Orchestrating the conversation](conversation.md), "Testing who should judge a contribution" · status: page copy drafted 2026-10-26 with the level prompts, as a complete study; revised 2026-10-28 as a focused explanation of the open-floor policy and the evidence that informed it; to be updated when the owner's labels arrive; for the owner's review.*

## Original drafting brief

This brief records the earlier investigation-only outline. The current page also explains the
implemented silence policy. Revision scope and verification questions are recorded in
[the editorial notes](../editorial_notes.md); the brief below is historical, not the current page specification.

Copied from [`../content_plan.md`](../content_plan.md), "Level 3 candidates", "Possible", condensed; the
plan keeps its copy until the owner moves it.

**Reader question:** can a model player's own choice to pass be tuned into a filter for useful speech?

**Added value:** readers will learn how replaying each voluntary pass with "do not pass", blind
classification of the forced lines, and a one-sentence ablation showed that the choice to pass did not
separate value; and how the shipped gate was then measured on the same lines.

**Why separate:** the replay design, the counting units (turns drawn, lines judged, samples per arm),
the four-lever table and the gate's bar-by-thinking table need sustained attention. The parent's
argument is how the day is run.

**What stays on Level 2:** the result (held-back lines 23 of 40 worth hearing against 13 of 25 posted;
the volume-knob table), the shipped gate's 10 of 29 restatements and 0 of 36 worthwhile lines, the
whole-game counts, and the readers' scope.

**Owner's ruling (2026-10-26):** draft it now as a complete study; update it when the owner's own labels
arrive (Evaluation hardening task 1b). Present it as an engineering decision informed by model
judgements: one Claude Sonnet reader per line, never checked against a person, and 23–46 turns per
cell, stated where the results are, not as a closing caveat. The gate as shipped is 10 of 29; 12 of 29
was the trial bar before porting.

**Tags:** output guardrails, LLM-as-a-judge, blind annotation, ablation.

This page's exhibit rows (SC-…) are proposed in the drafting notes, for the owner to merge into
[`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Editorially drafted, not independently
verified; the questions for the verifier are in the drafting notes (NOTES_sc.md). -->

## Page copy (draft)

A discussion needs both participation and restraint. An agent that repeats earlier speakers adds
noise; one that stays silent may withhold a useful question or interpretation. The silence policy has
to balance those two errors.

The current design separates writing from checking. On the **open floor**—a turn offered when no reply
is owed—the player is encouraged to contribute. A separate model then checks whether the completed
line adds anything to the discussion.

This page explains how that rule works and the experiments that led to it.

### How the silence policy works

This policy applies to the open floor. Opening statements use a separate filter, described in
[Orchestrating the conversation](conversation.md).

The open-floor prompt no longer tells players to pass when they have nothing new to add. Passing is
still an allowed response, but the default instruction encourages a contribution and warns that a line
adding nothing may be withheld. This gives the checker an actual line to assess instead of relying
entirely on the player's decision about whether to write one.

That checker is the **echo gate**. It compares the new line with the day's published player messages.
Its rule concerns contribution, not truth or strategic wisdom: a false claim can add something the
table needs to discuss.

| Publish a line that adds… | Withhold a line that only… |
|---|---|
| A previously unstated claim about the speaker's role or night action/result | Restates an earlier point |
| A different interpretation, with a reason | Agrees without adding a reason |
| A new question or concrete test directed at a player | Repeats a request or question |
| A confirmation or denial of something said about the speaker | Offers filler, such as urging patience without naming a fact, player or test |

One useful addition is enough to keep a line. The gate asks what the line adds and whose contribution
it repeats. Code withholds it only when the model says it adds “nothing” and identifies an earlier
speaker or marks it as filler. An invalid reference does not justify a hold.

Some contributions bypass the gate. Human lines and owed replies are exempt; code also protects an
open-floor reply to someone who named the speaker, using the message tags. The gate is skipped when no
player has spoken yet. If its model call fails, it **fails open** and publishes the line.

A withheld line remains in the records but reaches no player's prompt, including its author's. The
private note generated with it is discarded, so the author does not carry forward a note based on a
statement the table never heard. Its tags create no reply obligation, and the scheduler does not offer
its author another turn that day. Withholding therefore has a real cost: a mistaken decision can
remove a useful contribution and the opportunity to replace it.

### What players were leaving unsaid

Before this change, the open-floor rule said: “If you have nothing new to add, set pass_turn=true; a
pass costs nothing here.” An echo gate already existed, but used the narrower test of whether a line
made “the same point as an earlier line.” It withheld nothing in the 16 ten-seat games used for this
study. The open-floor silence in those games came from players choosing to pass.

**Were agent players passing when they had something useful to say?** To investigate, I replayed
40 turns where an agent had passed, using the same input but asking it to speak. I compared those
responses with 25 messages agents had posted voluntarily.

A model judge assessed each message without knowing which group it came from. It classified new facts,
interpretations and questions as worthwhile contributions, and repetition or filler as unhelpful.
“Worthwhile” meant adding to the discussion, not necessarily being correct.

The judge classified **23 of 40 replayed responses** and **13 of 25 voluntary messages** as worthwhile.
The replayed responses included specific questions: one agent used an earlier visitor report to ask
a surviving player to explain their night action.

This suggested that passing was not reliably separating useful contributions from repetition.
However, asking an agent to speak generates a new response; it does not reveal an original, unspoken
thought. The labels also came from one model judge per message and have not been validated by a person.

The next question was whether changing the pass instruction could release more useful contributions
without also increasing repetition.

### Could a different instruction make passing selective?

A better pass rule needed to encourage useful contributions while suppressing repetition. Rewriting
it to explicitly welcome interpretations and questions, removing the player's private note, and
softening a role-card instruction to “blend in” produced only small differences in speaking frequency.
With one sample per turn and version, those differences did not establish a dependable effect.

Removing the entire instruction—“If you have nothing new to add, set pass_turn=true; a pass costs
nothing here”—produced a larger change. On the same open-floor turns, speech rose from **20 of 64
successful samples to 41 of 64**. This did not isolate the effect of “a pass costs nothing” alone.

Turns were grouped by their original line's label, and speech increased in both the worthwhile and
repetitive groups. The newly generated lines were not relabelled, so the test measured willingness to
speak, not their quality.

Relaxing the pass instruction encouraged participation, but did not establish a better distinction
between useful contributions and repetition. Keeping the rule risked withholding useful speech;
removing it risked letting more repetition through. I chose to encourage contributions and revise the
echo gate to check the completed lines. This moved the tradeoff to a separate checker rather than
eliminating it.

### Calibrating the echo gate

The old gate's “same point” test missed forms of repetition the readers had labelled unhelpful,
including repeated requests and agreement without a new reason. The revised rule broadened the test
to whether any part of the line added something, using the policy described above.

I tested candidate gates on the same 65 open-floor lines, rebuilding their earlier discussion from
the captured prompts. In the game's implementation, the revised gate withheld **10 of 29 lines labelled
repetition and none of 36 labelled worthwhile**. The original gate withheld none of either group.

The prompt and reasoning setting were both adjusted, and small differences between variants were
comparable to variation across repeated calls. The final
before/after comparison therefore does not isolate a prompt effect from a reasoning-setting effect.

These were **calibration results**, not a held-out evaluation: the same lines helped choose the rule
and measure it. Catching some repetition without withholding any labelled worthwhile line was
encouraging, but does not establish a generally low false-hold rate. The labels themselves also remain
model judgements awaiting human validation.

Some misses reflect the gate's available context. It receives player messages, not the moderator's
morning report, and skips an empty discussion. Six of the 29 labelled repetitions were first lines
that it never checked. Most restated the record and requested claims. Whether that is useless filler
or a reasonable way to start a quiet discussion is also a question for the human labelling, not merely
an implementation defect.

### What happened in whole games

The revised instruction and gate then ran together in four ten-seat games, on the same deals as four
source games. Both sets used character voices. Matching deals held the starting conditions fixed;
the discussions could diverge after the first different response.

Published open-floor lines rose from **41 of 100 turns to 54 of 93**. The revised gate withheld seven
lines; review of the games identified all seven as repeating recent contributions, with none identified
as a fact or claim. This checked that the mechanism operated in play. Four games cannot establish its
general error rate or show that the additional speech improved reasoning or voting.

### What the evidence supports

The result was a design decision: encourage contributions, then assess the completed line separately.
This retains a checking call for eligible open-floor lines and accepts that repetition will still get
through. The old design already called an echo gate, so this was a revision of its role and rule, not
the introduction of a new call where none existed.

The next evaluation needs human-checked labels and fresh cases that were not used to tune the gate.
A prepared hand-labelling set is intended to check the model judgements. It also needs an explicit
tradeoff between missed repetition and wrongly withheld contributions; the observed 10 of 29 is where
calibration landed, not a predefined target. Whole-game evaluation remains a separate step: publishing
more lines and catching some repetition does not establish a better discussion.

**Evidence.**

- [Silence calibration](../../../evidence/gameplay/data/silence_calibration/README.md), steps 1–5:
  sampling, forced replays, blind labels, prompt variants, gate calibration and the four-game check.
- [The day discussion](../../../evidence/gameplay/discussion/report.md), decisions 12–14:
  the policy and its place in the scheduler.
- [Echo-gate implementation](../../../Agents/turn/echo_gate.py) and
  [turn resolution](../../../Agents/turn/resolve.py): the prompt, hold condition and exemptions.
- [Source games](../../../evidence/gameplay/data/persona_voice_games/README.md): the 16 ten-seat games
  from which the calibration turns were sampled.

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: silence_calibration/README.md step 1 "Question (owner)" (a player with a genuinely different
view got silenced; how to calibrate on principle); content plan Level 3 "Possible" row; report decision
13 ("Instead of: tuning the rule that tells a player when to pass").
Before the change: discussion_evidence §2.4 (517 passes, 367 judge holds; June design) via the parent's
"Silence had three sources"; §7.4 step 4c (the per-line gate under "the same point" bar, owner
2026-10-07); the pass sentence verbatim from README step 3 ("If you have nothing new to add, set
pass_turn=true; a pass costs nothing here."); README step 1 reading 3 (the gate never fired in the 16
games, 0 novelty-gated turns).
Replay: README step 1 Method (source = the 16 persona voice games, every turn's prompt input captured;
draw, seeded; forced replays; six failed, 156 lines; four blind Sonnet subagents; kinds A–D; worth
hearing); runner evaluation/experiments/silence_calibration.py (FORCE string verbatim: "Measurement
turn: whatever the rules above say about passing, do not pass this time. Write the message you would
say if you spoke now, as you would say it, and set pass_turn to false."; SEED 20261018; DRAW
strata; asserts anthropic/claude-haiku-5-5 at thinking low; SUMMARY_TAIL 3000 chars of earlier
summaries). persona_voice_games/README.md (8 pairs, Haiku 5.5, thinking low, memory off, 2026-10-18).
"Worth hearing" tracking: README step 1 ("yes for every A and B, for 32 of 34 C, and for no D"). Strict
bar: README step 1 Limits. Six failures all opening passes: opening-pass row n = 34 of 40.
Example 1: items.jsonl turn voices-08.off:4:player_5:1 (pass_reason voluntary, forced, context today
"No messages yet."); verdict C ("asks player_2 what they did night 2, since only they can be checked").
Results table: README step 1 Results rows "Open-floor pass, forced line" and "Posted open floor";
re-tallied from blind_key.json + verdicts_1..4.jsonl (forced proactive A1 B11 C11 D17; posted proactive
A1 B7 C5 D12; each judge 39 items). Reading: README step 1 reading 2. Opening: reading 1. Readers
unchecked: map 128, hardening task 1b; Evaluation llm_judges.md "The open gap".
Decision rule: README step 1 "Next (proposed)" (P(A–C | spoke) up, P(A–C | passed) down; measure the
decision's discrimination, not its level).
Levers: README step 2 (variant 1 wording; 90 later turns; table) and step 3 (no_note, no_pass_sentence,
no_blend_in; turns touched 90/65/48; table; reading 1–3; limits: one sample per turn and arm, 23–46
turns per cell, value = step 1's line); lever_scores.json; runner lever_score() (the "before" arm is
step 2's current arm on the same turns). 20 of 64 → 41 of 64 and 37/24 → 66/62: README step 3 reading.
Gate: README step 4 (owner ruling 2026-10-18; method: 65 lines, earlier entries rebuilt from the
capture; hold when "adds" is exactly "nothing"; table incl. v2 minimal two runs 5/29 and 8/29, only the
second's rows kept; v3 low 12/29; v3 as ported 10/29, 0/36; the six empty-floor D lines, the gate not
called and blind to the morning report); gate_check_scores.json, gate_check_judge_low_scores.json,
gate_check_ported.jsonl (10 D held, 0 A–C held, re-tallied). Agents/turn/echo_gate.py (three-step
answer; hold only when adds == "nothing"; returns "" when no spoken lines; game_master lines excluded;
fails open; get_llm_judge("low")), checked 2026-10-26. "Errs toward keeping": the reasoning is editorial (the
Evaluation page llm_judges.md makes the same point); not a recorded design rationale.
Example 2: items.jsonl voices-07.on:2:player_7:1 (forced from a voluntary pass; today context = player_3
and player_5 lines verbatim, cut with ellipses); verdicts D ("agrees, repeats ask for named visitor")
and voices-07.on:2:player_5:1 posted D ("echoes player_3's call for watch/follow results");
gate_check_ported.jsonl held = "player_5" and "player_3" respectively.
Estimate: README step 4 "Expected open floor" (uses the trial bar's ~40% of D; restated here
qualitatively with the shipped gate's third, no new figure).
Cost: report decision 13 "Cost accepted".
Whole games: README step 5 (four Haiku games on voices-01..04's deals, voices on; 41 of 100 → 54 of
93; held 0 → 7; passed 59 → 32; read in full; all seven restate a line spoken shortly before; none held
a fact or a claim); games_scores.json re-summed.
Settled/open: report decision 12 (generator-verifier separation) via the parent; hardening task 1b and
llm_judges.md "The open gap" (labelling packets prepared, echo gate among the three sources); report
"What is not established" (no standing regression bar). -->

<!-- Supporting notes (moved out of the page copy 2026-10-28, editorial restructure; interview
defence, not page text).
- Models: the 16 source games and every replay and lever sample ran on Claude Haiku 5.5 (thinking
  low, memory off, 2026-10-18); the four blind readers were Claude Sonnet subagents, one per line; the
  gate check ran the game's judge model at the thinking levels in the table. The page says "a stronger
  model" per the no-model-families rule.
- The full draw (seed 20261018, 162 turns): 40 passes each from the opening round and the open floor,
  each replayed; the 7 lines the opening round's filter had held; 25 posted lines each from the
  opening, the open floor and the replies players owed. Six replays failed, all opening passes,
  leaving 156 lines. The lever test's 90 turns = the 65 open-floor turns + the 25 owed replies.
- Lever motivations: README step 3 is titled "the other things that tell a seat to pass" (note and
  "blend in"); step 2's rewrite follows step 1 reading 2 (the rule licensed facts, never readings);
  the pass-sentence cut is step 3's no_pass_sentence. The three questions on the page are worded from
  those headings, not separately recorded hypotheses.
- Combined estimate (removed from the narrative; conditional, never measured): with the sentence cut
  a player speaks on about two-thirds of both kinds of turn, and the gate removes about a third of the
  restatements and none of the worthwhile lines. IF the original labels still describe the new lines
  AND the gate behaves similarly on them, about two-thirds of worthwhile-labelled turns would reach
  the table (against 37% before), and restatement would still rise above its old 24%. Source: README
  step 4 "Expected open floor" (which uses the trial bar's ~40% of D).
- Rule tables (added 2026-10-28): pass sentence verbatim from README step 3 no_pass_sentence (the
  whole sentence was cut, not only "a pass costs nothing here"; the earlier draft quoted only the
  clause); the live open-floor block is Agents/prompts/day_discuss.py PROACTIVE_ROUND_RULES, and the
  pass_turn field description still allows a pass. Keep/hold table paraphrases LINE_ECHO_PROMPT in
  Agents/turn/echo_gate.py; never-held rows from its docstring and line_echo_of (reactive turns and
  human seats skipped in resolve_decision; returns "" with no spoken lines, game_master lines
  excluded; fails open). Checked against today's code, 2026-10-28. -->
