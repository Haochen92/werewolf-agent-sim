<!-- claims review of writeup/context_engineering/context_engineering.md by claude (opus), 2026-10-30T04:51Z -->

I couldn't reach the Sentry, Gmail and Calendar connectors, but this review didn't need them.

## 1. Findings

**1. The healer case: the "before" condition, and what the engine added**
- **Claim:** "every fact was present and clear, and the player still did not draw the conclusion" … "For the Healer it added one certain line: the Chanteuse came to you that night. With that line, the read rose to 8 in 10." (*Facts the model has but does not connect*)
- **Source checked:** `evidence/gameplay/deduction/experiment_log.md` §4 (the design paragraph) and §8 (setup, Results 1–2); `evidence/gameplay/deduction/data/healer_model_compare/turn_engine_off.md` line 241 and `turn_engine_on.md` lines 173–175, 245 and 262–265.
- **Verdict:** conflicts with source.
- **Why:** With the engine off, the night record read "your action was not carried out and you learned nothing tonight". §4 calls that last clause "false" and says it "works against the deduction", so the facts were not all clear. Turning the engine on did two things at once: it swapped that misleading line for the certain one, and it added three more general lines (the hidden-role candidates, the wolf and Serial Killer candidates, and "No one else claims the Investigator or the Trailseer"). So 2 → 8 in 10 measures the whole engine against a misleading baseline, not one added line against clear facts.
- **Suggested scope:** Say the game's original line told the healer it had "learned nothing", and that turning the engine on (which replaced that line with the certain one and added a few general lines) raised the read from 2 to 8 in 10.

**2. "Doing no reasoning at all"**
- **Claim:** "enforcing the answer format through the provider left the game's model doing no reasoning at all in 4 samples of 10; sending the format as text, it reasoned every time." (*Information the model has but does not use*)
- **Source checked:** `deduction/experiment_log.md` §8, Result 1; the writing prompt's EVIDENCE DISCIPLINE section; `content_plan.md` §7 ("Thinking level").
- **Verdict:** overstated.
- **Why:** The record counts reasoning tokens: 0 in 4 of the 10 samples. The evidence rules say outright that zero reasoning tokens do not show the model did no reasoning, and the chapter's own care list repeats this.
- **Suggested scope:** "…reported no reasoning tokens in 4 samples of 10; with the format sent as text, every sample used reasoning tokens."

**3. What the e06 game actually changed**
- **Claim:** "The rule came from a game a summary decided … The summariser now records what was said and never judges it, and code drops any claimed action that could only have been done to the speaker." (*Earlier days that lose their meaning or source*)
- **Source checked:** `evidence/extraction/day_summary/report.md` §4 and §7.
- **Verdict:** conflicts with source.
- **Why:** §4 traces the "records, never judges" rule to two other failures: a narrated wolf premise, and 27 of 27 record checks judged wrong. "The rule" in the page's sentence points back to the record-check rule, and the e06 game produced neither. The e06 fix (commit `6248fc58`) was narrower: the summariser is told that something done *to* a player is not their claim, and the ledger drops self-directed actions.
- **Suggested scope:** Present e06 as showing why the summary needs a code guard, and give its fix as written in §7: the summariser instruction about things done to a player, plus the ledger rule.

**4. What the 75% → 92.5% result shows**
- **Claim:** "the stated reasoning and the vote agreed 92.5% of the time, against 75%. That shows the order changes what the model does, not that its reasoning got better." (*Information the model has but does not use*)
- **Source checked:** `evidence/gameplay/turn_prompt/report.md` decision 10; `turn_prompt/experiment_log.md` §7; `evidence/memory_system/effectiveness/decision_replay/experiment_log.md` section D.
- **Verdict:** unsupported inference.
- **Why:** The measure is whether a judge, reading only the reasoning, lands on the voted player. The gain came mostly from fewer non-committal "unclear" reasonings (25% → 5%), so it shows the vote follows the written reasoning more closely, not that the action itself changed. The action-change evidence in the records is a different study (the adoption field). The number also has no context on the page: 40 decisions, one judge, an earlier model, lessons from memory shown. One more thing to know: the report says the reorder alone "changed nothing", but the replay table shows 87.5% for it alone.
- **Suggested scope:** "…on 40 replayed votes from an earlier model; that shows the vote follows the written reasoning more closely, not that the reasoning got better."

**5. Which model the failures happened on**
- **Claim:** "On the small, low-cost model the game runs on, that was not enough." (intro)
- **Source checked:** `turn_prompt/report.md` decisions 1, 2 and 4; `day_summary/report.md` §7; the sources comment ("Claude Haiku 5.5").
- **Verdict:** overstated.
- **Why:** The page's evidence comes from several models:
  - the July census and the evidence that the plain design was "not enough" (decision 1): Flash-Lite;
  - the e06 summary game: Flash-Lite;
  - the 75% → 92.5% result: Flash-Lite;
  - the Sentinel case: GPT-6 Luna, where "flash-lite never conceded";
  - only the healer and output-mode results are on today's model.
  The page frames them all under one model, and the sources comment names it as today's default.
- **Suggested scope:** "On the small, low-cost models the game has run on, that was not enough."

**6. The "remaining wolf" example and its remedy**
- **Claim:** "A correct list of the roles still in play did not, on its own, stop a player hunting for 'the remaining wolf'… So the engine now prints what a player would otherwise work out from prose…" (*Facts the model misreads or invents*)
- **Source checked:** `turn_prompt/report.md` decision 1; `turn_prompt/experiment_log.md` §10.2.
- **Verdict:** unsupported inference.
- **Why:** The record says printing the facts did not stop this error. The response was to add a forced read of every player, tested together with the printed board (48% → 30% bad on 100 selected error-prone turns), and §10.2 calls the cause "reasoning under a confusing death pattern, not missing information". The page's "So" makes printing look like the fix for the very error it just said printing didn't fix.
- **Suggested scope:** Either say that reads were added because printing alone didn't work (pointing to the reads described in the next section), or lead with a misreading that printing or rewording did fix, such as the invented check.

**7. "Other low-cost models showed the same pattern"**
- **Claim:** "Other low-cost models showed the same pattern to different degrees." (*Information the model has but does not use*)
- **Source checked:** `deduction/experiment_log.md` §8 ("What it shows"); `discussion_evidence.md` §6.7; `evaluation/model_admission/report.md` finding 1; `Agents/llm_factory/catalog.py`.
- **Verdict:** overstated.
- **Why:** Flash-Lite's zero reasoning tokens were a thinking-level finding (at minimal and low), with no text-format comparison. The only like-for-like evidence is that a forced tool call turned thinking off for DeepSeek V4 Pro, which is a different way of enforcing the format.
- **Suggested scope:** "A forced tool call turned thinking off on another low-cost model too."

**8. Figure caption**
- **Claim:** "Facts come from the engine or are checked by code; anything a model wrote is labelled as a claim or a note." (figure caption)
- **Source checked:** `day_summary/report.md` §3 item 2 and §8 ("Claims the record cannot check"); `content_plan.md` §2 (wording rule for section 2).
- **Verdict:** overstated.
- **Why:** The caption puts the "Players, checked by code" box on the facts side, but those entries stay claims. Code checks them only where the record can settle them, and the players are themselves models. This is the brief's own listed confusion ("checked claims" read as true facts).
- **Suggested scope:** "Facts come from the engine; players' claims stay claims, checked against the public record where it can settle them; anything else a model wrote is labelled as a claim or a note."

**9. "Nearly three times the wait on every turn"**
- **Claim:** "at nearly three times the wait on every turn" (*Facts the model has but does not connect*)
- **Source checked:** `deduction/experiment_log.md` §8, Result 2 (median 17.4 s against 6.3 s).
- **Verdict:** overstated.
- **Why:** These are medians from one frozen turn. They don't measure the cost of the setting across turns.
- **Suggested scope:** "a turn took nearly three times as long on this case".

**10. Closing sentence**
- **Claim:** "each result is a replay of a failure that had happened in a game." (close)
- **Source checked:** `decision_replay/experiment_log.md` section D; `turn_prompt/report.md` decision 10.
- **Verdict:** overstated.
- **Why:** The 75% → 92.5% result came from 40 replayed votes in a memory study, not from a replay of an observed failure.
- **Suggested scope:** "each result is a replay of selected turns from earlier games."

**11. Table, "Claims" row**
- **Claim:** "Claims | each speaker's own claim fields, checked by code against the record" (*Earlier days…*, table)
- **Source checked:** `day_summary/report.md` §4 ("Where role claims come from today") and §8.
- **Verdict:** overstated (minor).
- **Why:** For a human seat, or a player who filled no field, claims still come from the summary's transcription, as do plans and withdrawn claims.
- **Suggested scope:** Add "(the summary's transcription for a player who filled none, such as a human)".

**12. Where the ranking line came from**
- **Claim:** "That last line came from a run of games in which a player argued that the Sentinel should appear in its own visitor list" (*Facts the model misreads or invents*)
- **Source checked:** `turn_prompt/report.md` decision 4; `discussion_evidence.md` lines 1839–1849.
- **Verdict:** unclear (needs the owner).
- **Why:** "That last line" is the rule that the rules outrank any player's account of a rule. The record ties it to the October failures as a group. The 10/10 → 0/10 replay tested the Sentinel card sentence, not the ranking line. The ranking line's own test was the f02 Illusionist case, where Flash-Lite stayed at 10 of 10.
- **Suggested scope:** "The rule sentences came from…", keeping "the missing rule sentence" as the thing replayed.

**13. "From the rules alone"**
- **Claim:** "Some conclusions follow from the rules alone, so code can work them out." (*Facts the model has but does not connect*)
- **Source checked:** `deduction/experiment_log.md` §4 ("certain from public rules and its own private result"); `deduction/report.md` §3.
- **Verdict:** overstated (minor).
- **Why:** The engine works from the rules plus what the seat has seen, its own night results included, and the healer's line depends on its own roleblock result.
- **Suggested scope:** "Some conclusions follow from the rules and what the player has seen".

## 2. Checked and supported
- About 3% of public messages in the earlier nine-player game, kept separate from lies: `evaluation/factual_errors` via `turn_prompt/report.md` decision 1 and `turn_prompt/experiment_log.md` §10.1.
- A correct "roles still in play" line did not stop the "remaining wolf" hunt: `turn_prompt/experiment_log.md` §10.2 (T1b).
- The engine prints the dead with their roles, and words night results as the player's own action on a named night: `turn_prompt/report.md` "The board facts" and decision 2.
- Sentinel case: concessions in a batch, voted out in three of four games, 10/10 → 0/10 on replay, with the one-turn limit stated: decision 4; `discussion_evidence.md` §8.4 (the source says the Sentinel conceded in all four games, so the page understates rather than overstates).
- The three blocks by author, the claims line quoted verbatim, and a ledger that says nothing where the record fits more than one reading: `day_summary/report.md` §3 and §8.
- e06 sequence (the roleblock read as a Chanteuse claim, the Investigator accepted it, voted out 7 to 1) and the self-action drop rule: `day_summary/report.md` §7.
- Answers after acting read as rationalisations, and today's answer order (reads, verdicts when lessons are shown, note, then the action): decision 10; `TurnOutput` as described in "What the seat must answer".
- "A structured form of chain of thought", with the limit that the reasoning did not improve: `skills_inventory.md` line 61 (owner revision 2026-10-30, replacing the content plan's earlier ban).
- Healer setup (only the Chanteuse blocks, a block is a visit, player_7 admitted the visit): `deduction/experiment_log.md` §4; `turn_engine_on.md`.
- 2/10 with the engine off at low; Sonnet 9/10 and Opus 10/10 without the engine; Haiku 9/10 at `high` (the highest of `VALID_THINKING_LEVELS` in `Agents/llm_factory/accessors.py`): `deduction/experiment_log.md` §8, Result 2.
- The engine was added after the earlier fixes, narrows candidate roles, and words each line as certain, conditional or alternatives: `deduction/report.md` §1–3.
- The engine reads only the seat's view, and a test swaps hidden roles and requires the same output: `deduction/report.md` §3–4; `tests/engine/deduction/test_candidates.py::test_hidden_roles_the_seat_cannot_see_do_not_change_its_items`.
- Authorship (the engine is AI-written; the owner set the requirements, the grading rule and the acceptance cases), with nothing said about who wrote the tests: memory `project-code-authorship-split`; `content_plan.md` §2 section 4.
- Nothing from the care lists reaches the page: no 0.14%, no unaudited tests, no model family names. The ~3% is scoped to the earlier game, and the close states that no whole-game error rate was measured.

## 3. Not checked
- The figure's grouping against the full rendered prompt order: it is labelled simplified and not in prompt order, so I only checked the categories.
- Whether the July census rate is a floor: the page states it as "about 3%", as the reports do; I did not re-audit the census.
- The hidden-role swap tests beyond the one named test: the content plan says sibling tests cover each part of the engine that writes into a prompt, and I did not check that coverage.
- The summariser's current instruction text in code: I relied on `day_summary/report.md` §4 and §7 as the record of it.
