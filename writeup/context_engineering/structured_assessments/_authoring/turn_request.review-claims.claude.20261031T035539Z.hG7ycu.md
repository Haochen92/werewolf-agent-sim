<!-- claims review of writeup/context_engineering/structured_assessments/turn_request.md by claude (opus), 2026-10-31T03:55Z -->

## 1. Findings

**1.**
- **Claim:** "Getting the fields filled, putting them before the action, and finding out whether more of them helped took several changes, and each was tested against the decisions it produced." (opening)
- **Source checked:** `evidence/gameplay/turn_prompt/report.md` decisions 6, 7, 10, 11 and "What is not established"; `evidence/caching/experiment_log.md` §12, §16.
- **Verdict:** overstated
- **Why:** Several of the page's own changes were never tested against decisions:
  - The all-required rule has "no failure rate … recorded".
  - The reason for putting `pass_turn` before the message "was not tested".
  - The Claude reorder was checked for compliance only. The page itself says it was not checked for message quality.
  - Dropping the verdict fields when no lessons are shown has no recorded test.
  - The suspicion cues were kept "on principle, not on the counts".
  - The investigator rewrite was never compared.

  The Level 2 rules forbid turning a practice into "every change is tested".
- **Suggested scope:** "…took several changes, and where a change could move a decision it was replayed against the decisions it produced."

**2.**
- **Claim:** "Three things went missing, and each needed a change to the answer's shape rather than another sentence of instruction." Also: "The instruction to write them also moved from the field description into the prompt body, which took the share … from 0.27 to 0.97." (Getting the requested assessment into the answer)
- **Source checked:** `evidence/memory_system/strategy_adoption/forced_schema_screen/experiment_log.md`, "Prompt-limit vs output-limit" (lines 105–118); `turn_prompt/experiment_log.md` §7.
- **Verdict:** conflicts with source
- **Why:** The forced per-item field was already in the "base" arm of that screen, and coverage there was 0.27. Coverage reached 0.97 "purely by moving the instruction into the prompt body", which is a sentence of instruction. The same section also credits a sentence (the vote-reason line) with 24 → 16 passes. Only the length-pinned schema, which was not shipped, is a shape fix that worked.
- **Suggested scope:** Drop "rather than another sentence of instruction". Say the required field gave each verdict a slot, and coverage rose only when the instruction moved out of the field description into the prompt body.

**3.**
- **Claim:** "The assessment became a **required field**, a field without which the answer is invalid, one verdict per lesson" and "Every field the turn shows is therefore required" (same section)
- **Source checked:** `Agents/schemas/lineup_output.py::TurnOutput` (lines 84–93); `turn_prompt/report.md` "What the seat must answer".
- **Verdict:** wrong mechanism (as current behaviour)
- **Why:** Today `strategy_verdicts` and `memory_applicability` use `default_factory=list`. A reply with no verdicts is valid even when lessons are shown. The report names the verdict lists as the exception to the all-required rule. The brief's open question 4 says the page states this exception, but the page copy does not.
- **Suggested scope:** Make the first sentence historical ("became a required field in June"). Add that today the verdict lists are the one exception: they default to empty, and coverage rests on the prompt-body instruction.

**4.**
- **Claim:** "…which took the share of lessons that received a verdict from 0.27 to 0.97" (same section)
- **Source checked:** `forced_schema_screen/experiment_log.md` lines 51–52 and 107–112.
- **Verdict:** conflicts with source
- **Why:** The page has the wrong denominator. 0.27 is `row_reliability`, the share of decisions that gave one verdict per item. The share of items that got a verdict was 168 of 300, about 0.56. The screen also measured numbered observations (`memory_applicability`), not strategy lessons, which the page's own skeleton treats as a separate field.
- **Suggested scope:** "…which took the share of answers giving one verdict per retrieved memory from 0.27 to 0.97."

**5.**
- **Claim:** "That narrows the failure to a missed inference, the case the deduction engine on the next page was built around" (What the written assessment needs to reveal)
- **Source checked:** `evidence/gameplay/deduction/experiment_log.md` §4 (design, decision), §5, §8.
- **Verdict:** overstated
- **Why:** There are three problems:
  - The healer's night record told it "you learned nothing tonight". The log calls that clause false and says it "works against the deduction", so the fields cannot separate a missed inference from an inference the prompt worked against.
  - §4's own decision is that "R1's bottleneck is the choice to stay silent, not the missing fact". §5 found the carried-forward note to be the main cause of the silence (Fisher p = 0.007).
  - The exhibit sample comes from the enforced-schema run, and §8 says the output mode "decided most of what §4 measured". The caption says "the prompt as played" but does not name the mode.
- **Suggested scope:** "The record rules out a misread clue and a misapplied lesson. It points to a missing link, under a night record that told the healer it had learned nothing, and a self-set stance of silence (page 4 tests both)." Name the sample as the enforced-schema run.

**6.**
- **Claim:** "Tagging each ballot … moved single cases both ways (one voter 4 → 9 of 10, another 6 → 2) without moving the day's total" (Testing whether a fuller assessment helps)
- **Source checked:** `discussion_evidence.md` §8.7, "Tagging each ballot…".
- **Verdict:** conflicts with source
- **Why:** Day 4 held (13 → 12 of 30), but day 5 fell from 14 to 7 of 30 in the same run.
- **Suggested scope:** "…moved single cases both ways (…) and halved day 5's right votes while leaving day 4's total unchanged."

**7.**
- **Claim:** "Where the evidence was strong, it helped. … votes for the player rose from 13 to 17 of 30." (same section)
- **Source checked:** `discussion_evidence.md` §8.7, "Where the evidence was strong…".
- **Verdict:** overstated
- **Why:** The source marks the vote rise "not significant at this size". The page's own swing-of-five limit, measured on these same day-4 cases, is as large as the gain. Only the citation result (11 against 2 of 30, p = 0.01) carries "helped".
- **Suggested scope:** Rest "helped" on the reads citing the vote. Give 13 → 17 as within the sample variation.

**8.**
- **Claim:** "…its effect depended on how strong the evidence was, which no fixed wording can know in advance." (same section)
- **Source checked:** `discussion_evidence.md` §8.7 ("One plausible reading of the two days together…"; Decision).
- **Verdict:** unsupported inference
- **Why:** The source offers this as one plausible reading of two situations in one game. The page states it as an established property of the sentence. The source's decision line repeats it, but repetition does not widen the evidence.
- **Suggested scope:** "…on this game it helped where the evidence was strong and hurt where it was thin, so its effect looked dependent on evidence a fixed wording cannot see in advance."

**9.**
- **Claim:** "Two more sentences went the same way. … 'cite the record exactly' left vote misquotes at 24 before and 24 after: a request to cite produces prose that nothing checks." (same section)
- **Source checked:** `evidence/gameplay/report.md` Problem 1 table; `discussion_evidence.md` §6.7 ("What this does to §6.4–6.6").
- **Verdict:** overstated
- **Why:** The cite test was a separate study: nine-seat, a different model, 2026-10-04. It ran at a setting where that model reported no reasoning tokens. §6.7 says such comparisons "measured layout and wording for a model that wasn't checking anything, which may be why they stayed within noise", and the same misquotes fell from 22 to 5 with thinking on. The source table limits it to: "did not help on the replay set; it does not show that all prompt changes fail".
- **Suggested scope:** Mark it as an earlier study on an earlier model with no reasoning tokens. Say the request "did not reduce misquotes there" rather than giving a general law.

**10.**
- **Claim:** "a field reporting which lesson the seat had followed changed the action when it moved before it" (Putting assessment before action)
- **Source checked:** `evidence/memory_system/strategy_adoption/report.md` (Test, Answer); `turn_prompt/experiment_log.md` §3.
- **Verdict:** unsupported inference
- **Why:** The only evidence is one model judge's 1–5 action-quality score. v1 was scored on 30 turns and v2 on 120, drawn from different games played under each prompt. No paired actions were compared. The content plan's handle-with-care list flags these scores as the kind that could not rank versions.
- **Suggested scope:** "…a judge rated the actions higher when it moved before them."

**11.**
- **Claim:** "The second cue was the answer example. Every prompt's sample read named `player_2`, and on day 2 … drew 40 accusation tags and 41 votes…" Also: "the choice followed the seat number or the example" (When the prompt supplies an accidental cue)
- **Source checked:** `discussion_evidence.md` §7.5; `turn_prompt/report.md` decision 5.
- **Verdict:** unsupported inference (narrow)
- **Why:** The night-1 lot was tested by intervention on 32 boards. The example's effect is inferred from counts across games, and no replay or later count of day-2 accusations measured the change after the example stopped naming a seat. The only after-check is that no read copied the placeholder.
- **Suggested scope:** "…drew 40 accusation tags and 41 votes … which points to the example as the cue. The example now names no seat (its effect on day 2 was not re-measured)."

**12.**
- **Claim:** "One earlier player model, 267 replayed turns of the nine-seat game | samples with a factual error | 82 | 27" (Giving the model more thinking effort, table)
- **Source checked:** `discussion_evidence.md` §6.7; map block 143 ("89 cases, 3 samples each").
- **Verdict:** conflicts with source (unit)
- **Why:** 267 is the number of samples (89 bench cases × 3), not turns. The "36 improved / 4 worsened" in the next paragraph are cases out of 89.
- **Suggested scope:** "89 replayed turns of the nine-seat game, 3 samples each".

**13.**
- **Claim:** "The same pattern, that the shape of the answer moves the result as much as the instructions do, appears in … the deduplication judge's field order and its 'when unsure' lean" (closing paragraph)
- **Source checked:** `writeup/memory/store_upkeep/dedup_judge.md` ("Order beat rules", "A 'when unsure' lean…").
- **Verdict:** wrong mechanism
- **Why:** The dedup judge's result is about input order: showing the action before the situation. It is not about the order of fields in the answer. The "when unsure" lean is an instruction, not answer shape. "As much as the instructions do" is a comparison nothing measured.
- **Suggested scope:** "A related pattern, that where information sits changes the result, appears in the deduplication judge's input order and its 'when unsure' lean…"

**14.**
- **Claim:** "The Vigilante's vote for the real threat fell from 7 of 10 to 0 of 10" (Testing whether a fuller assessment helps)
- **Source checked:** `discussion_evidence.md` §8.7 ("The current arm's 7 of 10 is not all sound reasoning either…").
- **Verdict:** overstated (a limitation is missing)
- **Why:** Three of the seven right baseline votes rested on a false fact: reads saying player_3 voted out the Investigator, which player_1 did. The reversal still stands at 0 of 10. However, the baseline is not the clean reasoning the page implies.
- **Suggested scope:** Add a clause: "(three of those seven rested on a misquoted vote)".

**15.**
- **Claim:** "…and in a larger replay on the same model the note-first layout voted against a real threat less often." (Putting assessment before action)
- **Source checked:** `decision_replay/experiment_log.md` Step 2 and the coherence table.
- **Verdict:** unclear (needs the owner)
- **Why:** "The same model" refers to the earlier model of the coherence study. The paragraph just before is about "today's model", so a reader will likely read it as today's model, which the figure does not cover.
- **Suggested scope:** "…in a larger replay on that earlier model…"

**16.**
- **Claim:** "The verdict fields, their example and the memory instructions, about 1,200 characters, now appear only when lessons are shown." (Getting the requested assessment into the answer)
- **Source checked:** `turn_prompt/report.md` decisions 11 and 12; `caching/experiment_log.md` §16.
- **Verdict:** conflicts with source (minor)
- **Why:** The 1,200 characters were the memory instructions alone (2026-10-04). The verdict fields and example were removed in a separate change on 2026-10-14.
- **Suggested scope:** "The memory instructions, about 1,200 characters, and later the verdict fields and their example, now appear only when lessons are shown."

**17.**
- **Claim:** "on 18 frozen turns from one game that line brought open-floor passes from 24 of 25 samples to 16 of 25" (same section)
- **Source checked:** `discussion_evidence.md` §8.6; `evidence/gameplay/data/haiku_turn_replay/README.md` (arms).
- **Verdict:** overstated (minor)
- **Why:** The 25 samples come from the 5 vote-reason turns, not the 18. The "after" arm also carried the visit rule and the reply brief, which with the line's first wording gave 23. The second wording's own step is 23 → 16.
- **Suggested scope:** "…on five open-floor turns from one game, five samples each, passes went from 24 of 25 to 16 of 25 (23 with the line's first wording)."

## 2. Checked and supported

- Written assessment versus hidden reasoning tokens, named once with its scope: the owner's 2026-10-30 ruling as recorded in `content_plan.md` §7 "Field order".
- Replays answer a decision and are not a frequency; the up-to-five-of-ten swing: `turn_prompt/report.md` "What is not established"; §8.7 tag paragraph.
- Exhibit setting:
  - healer roleblocked; the trailseer's follow; player_7 admitted the visit; only the Chanteuse blocks; a block is a visit; three passed turns; premises side by side in the notes: `deduction/experiment_log.md` §4.
  - the exhibit's read and note text match a sample of case `9b3219e5dc1eb831` in `judged_haiku_low.jsonl`.
  - a missed link is representative across samples: 0 of 10 at low as played (enforced, §4) and 2 of 10 (live mode, engine off, §8).
- Healer as the engine's worked example and acceptance case: `deduction/report.md` §2.
- 426 copied verdicts out of 3,118 seat decisions in 20 games, in the unenforced mode, copied from the example: `caching/experiment_log.md` §16.
- Nullable fields dropped by an earlier model; `pass_turn`, `abstain`, `no_check`: `turn_prompt/report.md` decision 11; `turn_prompt/experiment_log.md` §4–5.
- The `TurnOutput` skeleton and its field order: `Agents/schemas/lineup_output.py:79-93`; report "What the seat must answer".
- Firing-brief wording; the conditional schema exists: `Agents/prompts/prompt_inputs.py::_firing_brief`, `Agents/turn/action_space.py::output_schema_for_memory_shown`.
- Reads before the note in July: about three times the override rate, thinner reads with no earlier reads to update, shipped provisionally: `turn_prompt/experiment_log.md` §11.1; report decision 10.
- Prompt and schema disagreeing; 15/24, every mismatch reads-first; 13/23 when asked in words; 24/24 after the reorder: `caching/experiment_log.md` §12.
- Vote-first notes uncommitted a quarter of the time; 0.40 → 0.26 votes against a real threat with the note first: `decision_replay/experiment_log.md` coherence table and Step 2.
- "Not tested for message quality": report decision 10 and "What is not established".
- Compare-candidates:
  - setup: 11 votes, 10 samples, memory off, the sentence's text.
  - results: 7/10 → 0/10 (abstain 6, sentinel 3); 7 of 10 "nothing separates"; abstention fact cited 3/10 against 8/10; citations 11 against 2 of 30; 960 → 1,297 tokens; not adopted.
  - the owner played the game as Necromancer: `discussion_evidence.md` §8.6–8.7.
- Suspicion cues removed, the comparison confounded by an easier board, kept on principle; the tactical audit: `turn_prompt/report.md` decisions 6–7.
- Night-1 lot (21 of 28; 95 of 96 shuffled; 78 of 96; 6–16 per seat; seeding; Vigilante exempt; the lot sentence): `discussion_evidence.md` §7.5; report decision 5; `prompt_inputs.py::night_one_lot`.
- Thinking effort:
  - 82 → 27 at about 2.4× cost; 36 better / 4 worse; the earlier model reported no reasoning tokens.
  - 65 → 98 of 160 votes; 12 better / 1 worse; discussion 49 against 47 of 115; 11.2 s against 6.7 s; $0.23 against $0.12.
  - live mode 97/157 against 122/158.
  - Sources: §6.7; `deduction/experiment_log.md` §2 and §9.
- Status: the earlier model at medium and Haiku at low for every seat turn: `Agents/llm_factory/catalog.py` (`turn_thinking`); votes at medium is an open decision (§9).
- Day-4 lead with layout and thinking level not separated: report decision 14.
- Off-page items: no model names, 1–5 scores, p-values, the participation figures or bookkeeping (uncommitted runs, test authorship) appear in the page copy.

## 3. Not checked

- The July T3 ordering arm's denominators (0.06 → 0.17) in `turn_prompt/validation/t2_results.md`. I relied on the log's "triples".
- The unit of "24 real turns" in `caching/experiment_log.md` §12. The trial lists "8 real … discussion turns × 3 variants", so 24 may be replies, not turns. The source is ambiguous and the page copies the report.
- Whether game `2f19d908` was played in the live text mode or the enforced mode. This decides whether the §1 exhibit's mode is "as played".
- The night-1 and Haiku replay data files (`night1_target_bias/`, `haiku_vote_replay/`), beyond the narrative logs.
- The Level 1 chapter page's own wording of the recalled figures, which this page leans on with "as the chapter page tells".
