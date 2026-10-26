# The day summary: how a past day reaches later prompts

**Version.** The implementation described here is the 2026-10-22 snapshot at `c0732f88`; the
summary's readers (§1, §3, §8) were rechecked against the 2026-10-26 snapshot at
`ccaec2f64788c1d3183940dd31a4c93475c164b5`. Historical results belong to the models, prompts and
configurations recorded in each study; they are not all measurements of this snapshot.

**Scope:** the call that records each day's discussion at the end of the day, what it writes, what later
prompts build from it, how it runs today, how it has been checked, and the October case where one
summary error decided a game. It describes the ten-seat, twelve-role game.
**Revised against the code:** 2026-10-22 at `c0732f88` (the summary's files have no uncommitted edits).
**Companion docs:** [the build journey](experiment_log.md) · [the information-fidelity record](../../gameplay/discussion_evidence.md) §6.4–6.6 and §8.4 (where the current design was built and tested) · [the reasoning-failures log](../../gameplay/deduction/experiment_log.md) §3 (the summary on a stronger model) · [the old judge's write-up](../../evaluation/llm_judge/day_summary.md) (the May quality judge).

> **Orientation: one day's path.**
>
> **the day's discussion → one summary call, before the vote → a structured record of accusations and role claims → every later prompt rebuilds "Previous days" from it: the game master's record, a claim ledger checked by code, and the accusations**
>
> Players never see an earlier day's discussion again. They see today's discussion as it was spoken, and earlier days only through this path.

---

## 1. What the summary is for

A day in this game is a discussion among the ten seats, followed by a vote. Each seat is an LLM agent. By day four, the earlier discussions run to hundreds of lines, and every seat's prompt on every turn would have to carry all of them.

So at the end of each day's discussion, before the vote, one model call records that day. From then on, that record stands in for the day's talk in every later prompt, by day and by night. This keeps each prompt to a fixed-size account of every past day.

It also means a mistake in the summary is a mistake every seat reads for the rest of the game. A seat that heard a claim rejected in the discussion may accept the same claim from the summary the next morning. Much of the design below exists to keep that from happening.

**Who writes it:** one call per day, on the same model the game's seats play on.
**Who reads it:** every later seat prompt; the replay page, which shows each day's summary and a "Record" tab with the claim ledger; and some post-game analysis, which reads only the role claims. One reader is the discussion tagger (`evaluation/src/loop/discussion_tagger.py`), a model pass that labels each player's day; since its use for memory credit was retired on 2026-07-13, it runs only as a diagnostic on stored games. Another is the factual-error screen (`evaluation/src/audits/role_hallucination_screen.py`). The credit scoring of the agents' memory lessons does not read the summary: it uses the speakers' own accusation tags (`Agents/memory/consolidation/credit.py`).

## 2. What the summary writes

The summariser fills two lists and nothing else:

- **Accusations.** One entry per distinct accusation, with every player who joined it, the target, the accusers' stated reasoning, the target's defence, and who else disputed it and why. The prompt asks for at most 30 words per field.
- **Role claims.** Each role claim made that day, marked *claimed* or *retracted*, with the night actions the player says they took. A night action is written in fixed words, not prose: the action (investigate, protect, watch, block, …), the night, the target, and a result from a fixed list (`suspicious`, `saved_from_attack`, `no_visitors`, `roleblocked`, `not_said`, …). A plan for the coming night goes in a separate list, because a plan is not something that happened.

The fixed words matter because code reads them. Section 3 shows what code does with them.

The record is stored with a plain-text rendering, which is what the replay shows. This is a real one, from day 2 of game `2f19d908` (Claude Haiku 5.5 in every seat):

> Key accusations and defenses: player_5 → player_9: player_5 argued player_9 is a wolf because player_5's night-1 investigation of player_9 read Suspicious. (evidence type: concrete_claim) Defense: player_9 said a single Suspicious read can't be verified, that they have no role to counter with, and asked which night and why player_5 checked them. Disputed: player_3 argued player_5's Suspicious read is only a claim until someone backs it up and should be weighed against player_3's follow on player_7. | player_3 → player_8: player_3 argued player_8 is worth watching because player_3's night-1 follow on player_7 showed player_7 went to player_8. (evidence type: concrete_claim) Defense: player_7 confirmed they went to player_8 but claimed no role and said the trailseer and investigator should give checkable results. Disputed: player_5 argued player_3's trailseer claim is only a claim and told player_3 not to push player_8 yet.
> Role claims: player_5 claimed investigator — Night 1: checked player_9, says they read Suspicious; player_3 claimed trailseer — Night 1: followed player_7

Every statement is attributed to a player ("player_5 argued", "player_9 said"). The prompt forbids stating any player's claim as fact, including the premise an accusation rests on. It also tells the summariser to leave out the vote tally and the night outcomes, because the game master records those exactly.

## 3. What the seats read about earlier days

A seat's prompt never shows the summary as written. Each prompt rebuilds a "Previous days" section in three labelled blocks, in order of how far to trust them. This is that section in a seat's prompt on day 3 of the same game, built in part from the summary above:

```text
== Previous days ==
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_1 was attacked by the wolves and the serial killer last night. Their role is hidden by an illusionist.
[Day 2] Here's the vote result for day 2:
  player_2 voted to eliminate player_9
  ... (one line per voter)
Player player_9 has been voted out and was a illusionist.
[Day 2] Night of day 2: player_3 was attacked by the wolves and the serial killer last night. They were a trailseer. ...

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed investigator (day 2).
  Night 1: checked player_9, says they read Suspicious. Record: player_9 was revealed as illusionist, as claimed.
player_3: claimed trailseer (day 2). Record: revealed as trailseer when they died on night 2, as claimed.
  Night 1: followed player_7; says they visited player_8 (a visit alone does not establish what they did there).

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_5 → player_9 (revealed illusionist, voted out day 2): player_5 argued player_9 is a wolf because ...
[Day 2] player_3 (revealed trailseer, killed night 2) → player_8: player_3 argued player_8 is worth watching because ...
```

The three blocks have three different authors.

1. **The game master's record** is written by the game engine, not by a model: each night's outcome, each vote ballot by ballot, and each revealed role. The summariser never writes these facts, so a summary error cannot lose or alter them.
2. **The claim ledger** is built by code. It folds every day's role claims and claimed night actions into one history per player. It then checks each claim against what the engine has made public: a dead claimant's revealed role, an investigation result against the target's revealed role, a claimed save against the announced saves, more living claimants of a role than the cast holds. A check states a fact ("Record: player_9 was revealed as illusionist, as claimed") and nothing more. Where the record fits more than one reading it says nothing. A shot player who lived may have been saved, or may be the serial killer, whose survival is never announced. The ledger is never stored; every prompt rebuilds it, so a role revealed overnight appears in the next prompt's checks.
3. **The accusations** come from the summary's accusation list, each player tagged with their revealed role once dead. They go into the prompt directly (`Agents/prompts/prompt_formatters.py::format_accusations`), not through the claim ledger.

Older summary sections (alliances, "village dynamics", the evidence-type labels) are not shown. A day stored only as text is shown as written. That happens when every summary attempt failed, or for a game from before the structured summary.

## 4. The division of labour: the model transcribes, code checks

The current design rests on one rule. **The summariser records what was said; it never judges whether it is true.** Judging is done by code, against facts the engine holds. This rule came from two observed failures (the journey log has both):

- When the summariser retold the day as a story, a wolf's false premise entered the record as narration, and seats who had rejected it in the discussion accepted it the next morning.
- When the summariser was asked to check claims against the record itself, its checks were wrong. In the stronger-model test of §6, it wrote a check 27 times across 66 summaries (the 60 written for the test and the 6 the games had used), and all 27 were judged wrong.

**Where role claims come from today.** A speaking seat now fills in its own claim as part of its turn: the role it claims and the night actions it says it took. The ledger takes a seat's claims from those fields first. The summary's transcription of a role claim is used only for a player who filled no field of that kind that day: a human player, whose line carries no fields, or a game recorded before the fields existed. The summary remains the only source for three things: the accusations, the retractions, and the stated plans.

## 5. How it runs today

This is the live default, with no switch. It runs in every game, with memory on or off.

- **Model.** The game's own model, the one its seats play on. A game on the website uses the model the player chose, or the house default, a live setting recorded as Claude Haiku 5.5 since 2026-10-15. Batch runs default to Claude Haiku 5.5 too.
- **Thinking.** At "medium" effort, unless that model's entry in the model catalogue (the list of models a game can run on, with their settings) sets another level. One listed model (GLM-5.3 Flash) is set to "minimal", because with thinking it took 34–55 seconds a call.
- **Output.** Structured output against the two-list schema. If a reply breaks the schema, the retry has the schema enforced by the provider.
- **When the model fails.** A request waits up to 90 seconds (seat turns get 30). A timeout, rate limit or server error is not retried on the same model: the summary goes to the game's rescue model, a different model assigned to the game. If the primary keeps stalling, later summaries start on the rescue model. If there is no rescue model, or it fails too, that day is stored as the raw transcript.
- **Tracing.** Each summary is saved as an evaluation case, so any day can be re-judged later without replaying the game.

The rescue path was added on 2026-10-21 and deployed with the server the same day. In the catalogue as seeded in code, Claude Haiku 5.5 has no rescue model, so a house game on it falls back on the raw transcript unless the player has added a backup key from another company.

## 6. How it has been checked

Four kinds of check bear on the current design. None shows that the summary leads to better play than giving seats the raw earlier transcript (§8).

**Does a more faithful summary reduce the seats' own errors?** The *hallucination bench* is a fixed set of 89 frozen moments from earlier nine-seat games, re-run on new code, where a judge checks each seat's message and private note against the game's facts. Two summary changes were run on it in early October, on Gemini 3.5 Flash-Lite with no reasoning step:

- Attributing every claim (the change after the §4 premise failure) moved bad samples from 36% to 31% of 267, with 24 cases better and 14 worse. That is a direction, not an established effect (p = 0.14).
- Moving to transcription plus the code ledger made no difference to the seats' errors: 31% against 32%, 11 cases better and 11 worse. What it did change was size. The stored summaries were 55% shorter, and one seat's "Previous days" section went from 4,911 to about 2,600 characters.

Both comparisons ran with seats that did not reason before answering. The same bench later found that turning reasoning on cut bad samples from 31% to 10%, larger than every layout and wording change before it. So these two results say little about how the summary's design matters to a model that reasons.

**Do known summary failures stay fixed?** Each summary that went wrong in a ten-seat game was frozen as a replay case: the summariser gets exactly what it got in the game, and the check reads the structured fields and the ledger built from them, not prose. Each fix was replayed before and after, five samples a case. Two examples:

- A spoken denial ("I didn't visit anyone last night") had no field to go in. Every one in the games was lost (30 of 30 replayed samples). After a "did not act" action was added, Gemini 3.5 Flash-Lite lost 7 of 30, and Gemini 3.5 Flash lost none.
- "I was roleblocked" was filed as a denial by GPT-6 Luna in 15 of 15 samples, and by Gemini 3.5 Flash-Lite in 6 of 15. After the summariser was told that a roleblock is an attempt, it was 0 of 15 for both.

These are regression checks on known failures, five samples a case, not error rates.

**Would a stronger model write better summaries?** Every day with speech in two Claude Haiku 5.5 games (6 days) was re-summarised five times each on Haiku and on Claude Sonnet 5.5, and Sonnet judged each summary against the transcript and the record. Both models had flaws in 18 of 30 summaries. Sonnet made fewer errors in the accusation's record check and more transcription errors. The summary stayed on the game's model. The same run found that the record check written by the summariser was wrong all 27 times it was written: 20 times on Haiku and 6 on Sonnet, among the 60 test summaries, and once among the 6 summaries the games had used, which the judge read too. It was removed on 2026-10-16.

**Do the rules hold in code?** The claim ledger and the "Previous days" rendering are pinned by unit tests (`tests/engine/test_claim_ledger.py`, `tests/engine/test_information_fidelity.py`); they passed on the working tree at `c0732f88`. The rescue path is covered in `tests/engine/test_model_fallback.py`.

## 7. Case study: one transcription error decided a game

**Verdict.** In ten-seat game `e06` (one of the first ten-seat test batches, read on 2026-10-10; Gemini 3.5 Flash-Lite in every seat), the summary turned something done *to* the investigator into a claim *by* the investigator. The ledger passed it on, the town believed it, and the real investigator was voted out. The fix moved the safeguard into code.

**What happened.** On day 2 the investigator said: "I was roleblocked last night, which confirms we have an active Chanteuse in play." (The Chanteuse is the wolf that blocks a player's night action.) The summary recorded: "player_2 claimed chanteuse — Night 1: blocked player_2". On day 3 the sigilist, a town player, opened on that claim. The investigator then accepted the false premise about its own past ("I claimed chanteuse yesterday to draw fire away from town PRs"), against its own private record. It was voted out 7 to 1, though its own check had correctly found the Chanteuse Suspicious. The Necromancer, a lone killer, won the game.

**Why it got through.** The investigator had described its night without filling in its own claim field. So the ledger fell back on the summary's transcription, and nothing checked that a player cannot block itself.

**The fix** (commit `6248fc58`):
- The summariser is told that something done to a player is not their claim: "I was roleblocked", "I was protected" and "someone visited me" claim no role.
- The ledger drops a claimed action that can only have been done to the speaker (a block, a watch, a check on oneself). It drops the claimed role with it only for the one case seen here, a Chanteuse claim resting on a self-block. A first, broader version also dropped a true Vigilante claim and was caught by the replay before it shipped.

**What it shows.** A summary line is not one seat's mistake. It is shared context for every seat, and a seat will accept a premise about itself from it. A rule in code catches the error however the model phrases it; an instruction to the model only lowers the chance of the error.

**Limits.** The invented claim did not recur in 10 replayed samples, before or after the fix. It is rare, so the replay cannot show that the instruction prevents it. The ledger rule is what guards against it, and a test pins that rule.

## 8. What is not established

- **That seats decide better with the summary than with the raw transcript.** This is a real gap: no comparison has given seats the full earlier discussions instead of the summary. The summary is kept for two reasons that do not depend on that comparison. It keeps every prompt bounded as a game runs on. And its structured fields are read by code, not only by the seats: the claim ledger takes retractions and plans from it (`Agents/rules/claim_ledger.py`), the accusations block is rendered from its accusation list (§3), and the deduction engine builds each seat's view of the claims from the ledger's fold (`Agents/deduction/claim_view.py`). A raw transcript would leave the seats readable text but give that code nothing to read. So the comparison would answer whether the seats lose anything, not whether the summary is needed.
- **The current error rate.** The summary's errors have been counted on replayed cases and on small samples: 6 days from two games in the stronger-model test, and ten audited games in which summary errors were the most common error found. There is no population rate for today's prompt on today's default model.
- **A current quality judge.** The five-dimension judge built in May still exists in code. It scores sections the summary no longer writes (alliances, village dynamics), so it does not measure the current design.
- **Plans, retractions and accusations still rest on the summary alone.** A speaker fills its own role claim and claimed night actions, so for those the summary is only a fallback. There is no field on the speaker's turn for a plan ("tonight I'll protect player_4"), a withdrawn claim or an accusation, so the ledger takes plans and withdrawn claims as the summary transcribed them, the prompt shows the accusations as the summary wrote them, and a slip in any of them reaches every seat. Giving the speaker those fields too, with the summary as fallback, would close it; it is not built.
- **Claims the record cannot check.** The ledger checks only against public facts. A false claim that the record never contradicts, such as a fake investigation of a player still alive, stays a claim. The ledger is right to say nothing, but the seats still have to weigh it.

## Sources and implementation

| What | Where |
|---|---|
| The summary call, retries, rescue and raw-transcript fallback; the text rendering | `Agents/nodes/day/summary_agent.py` |
| The graph step, run before the vote, and its saved evaluation case | `Agents/nodes/day/flow.py` (`summarize_day_discussion`) |
| The summariser's prompt and its change history | `Agents/prompts/extraction/day_summary.py` |
| The two-list schema and the fixed result words | `Agents/schemas/output.py` (`DaySummaryOutputV4`) |
| The stored record (`DaySummary`, with `source` and `structured`) | `Agents/schemas/game_events.py` |
| The model, thinking level and 90-second wait | `Agents/llm_factory/accessors.py` (`get_llm_summary`, `get_llm_summary_fallback`); per-model levels in `Agents/llm_factory/catalog.py` |
| The claim ledger and its checks | `Agents/rules/claim_ledger.py` |
| The "Previous days" section | `Agents/prompts/prompt_formatters.py` (`format_day_summaries`); placed in the shared public part of every seat prompt by `Agents/prompts/layout.py` |
| The ledger for the replay page | `server/game/ledger.py` |
| Tests | `tests/engine/test_claim_ledger.py`, `tests/engine/test_information_fidelity.py`, `tests/engine/test_model_fallback.py` |
| Bench results for the attributed and transcribe-only summaries | [discussion_evidence.md](../../gameplay/discussion_evidence.md) §6.5–6.6 |
| The ten-seat audit, the `e06` case and the replays | discussion_evidence.md §8.4; `evidence/gameplay/data/phase3_reads/`, `data/phase3_summary_replay/` (runner: `evaluation/experiments/summary_claim_replay.py`) |
| The Haiku-against-Sonnet test and the record-check removal | [gameplay/deduction/experiment_log.md](../../gameplay/deduction/experiment_log.md) §3; `evidence/gameplay/deduction/data/haiku_summary_compare/` (runner: `evaluation/experiments/haiku_summary_compare.py`) |
| The example summary (`2f19d908` day 2) | `evidence/gameplay/deduction/data/haiku_summary_compare/summaries.jsonl`, live arm |
| The example "Previous days" section (`2f19d908` day 3) | `evidence/gameplay/deduction/data/deduction_placement_n10/prompts/AC2_before_note.txt` |
| The May prompt series and judge runs (history) | this folder: `prompt_versions/`, `eval_summary*.txt`, `eval_results*.jsonl`, `regen_comparison.json`; judge in `evaluation/src/judges/day_summary.py` |
