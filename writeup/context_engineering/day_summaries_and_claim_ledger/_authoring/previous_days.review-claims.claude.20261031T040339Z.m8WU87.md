<!-- claims review of writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md by claude (opus), 2026-10-31T04:03Z -->

## 1. Findings

- **Claim:** "The ledger rule catches it however the model phrases it, and a unit test pins the rule." (§ How a carried-forward error cascades)
  - **Source checked:** `Agents/rules/claim_ledger.py` lines 226–237 (the Chanteuse branch) and `_DONE_TO_ONESELF`; report §7, "What it shows".
  - **Verdict:** overstated
  - **Why:** The rule only fires on one stored shape: a Chanteuse claim whose night action is a block on the speaker. It works whatever words the speaker used, because the summary is stored in fixed words. But if the summariser invented the claim in any other shape (a Chanteuse claim with no night action, or a block on someone else), the rule would let it through. The report has the same wording, but the code does not support "however".
  - **Suggested scope:** "The ledger rule catches it whenever the summary records the claim as a block on the speaker, whatever was said in the day; a unit test pins the rule."

- **Claim:** "The accusation's record check stayed until a later test caught it." (§ Why judging left the model)
  - **Source checked:** discussion_evidence.md §6.6, "`record_check` is narrowed" (2026-10-04); experiment_log.md ③ 2026-10-10 (the copied example, removed in commit 6248fc58); deduction/experiment_log.md §3.
  - **Verdict:** conflicts with source
  - **Why:** The record check had already been caught misfiring twice before the 2026-10-16 test, and patched both times. On 2026-10-04 it was narrowed after false "never announced" flags. On 2026-10-10 its copied example was removed. The page's own §6 lists "a copied record-check line" as a replay case, so "until a later test caught it" contradicts the page itself.
  - **Suggested scope:** "The accusation's record check stayed, patched twice after wrong flags, until a later test found it judged wrong every time it was written."

- **Claim:** "Re-running the summariser on the frozen input of the days that had gone wrong, the **summary replay** described below, caught it before it shipped" (§ How a carried-forward error cascades)
  - **Source checked:** `evidence/gameplay/data/phase3_summary_replay/README.md`, table and "Reading" (e02 day 3 is a `control` case).
  - **Verdict:** wrong mechanism
  - **Why:** The lost Vigilante was caught on a control case. Controls are days where a true claim has to be kept, not days that had gone wrong. The catch therefore came from the controls inside the replay, and that is the point the page is making.
  - **Suggested scope:** "Re-running the summariser on frozen days, including control days where a true claim must survive (the **summary replay** described below), caught it before it shipped."

- **Claim:** "Since mid-October a speaking player states, in fields of its own answer, the role it claims and the night actions it says it took" (§ One call, two lists), read beside "the Investigator's answer had a claim field" in an "early October" game (§ cascades)
  - **Source checked:** experiment_log.md ③ 2026-10-09 (the role field) and 2026-10-18 (night actions, commit c957fdb5); turn_prompt/report.md decision 13.
  - **Verdict:** conflicts with source
  - **Why:** The role field dates from 2026-10-09 and only the night-action field from mid-October. As written, the page dates both to mid-October and then shows an early-October game that already had a claim field. A careful reader will see the conflict. The brief's open question 2 already raises this.
  - **Suggested scope:** "Since early October a speaking player states the role it claims in a field of its own answer, and since mid-October the night actions it says it took."

- **Claim:** "15 of 15 on the model that showed it" (§ How it is checked, table row 2)
  - **Source checked:** phase3_summary_replay/README.md, "Roleblocks and empty results" (Luna 15/15 → 0/15; Flash-Lite 6/15 → 0/15).
  - **Verdict:** overstated
  - **Why:** Two summariser models showed this misfiling, not one. The phrase "the model that showed it" implies the failure belonged to a single model.
  - **Suggested scope:** "15 of 15 on one summariser model (6 of 15 on the other)" → "0 of 15 on both".

- **Claim:** "The summariser never writes the vote tally or the night's deaths, which the engine records exactly" (§ One call, two lists)
  - **Source checked:** report §2 ("It also tells the summariser to leave out the vote tally and the night outcomes").
  - **Verdict:** overstated
  - **Why:** This is a prompt instruction, not something enforced. A 30-word reasoning field can still quote a vote. What actually protects these facts is that the engine writes the game master's record, and §3 already says that correctly.
  - **Suggested scope:** "The summariser is told to leave out the vote tally and the night's deaths, which the engine records exactly."

- **Claim:** "The Investigator checks one player a night" (§ What a player reads)
  - **Source checked:** `evidence/gameplay/roles/role_sheet.md` (Investigator row: "2 checks for the game", balance ruling 2026-10-09; Necromancer also reads Suspicious on nights it attacks).
  - **Verdict:** conflicts with source
  - **Why:** This is a minor gloss, but since 2026-10-09 the Investigator has two checks per game, not one every night. It does not affect the point about player_9.
  - **Suggested scope:** "The Investigator checks a player at night (twice a game) and learns whether they read Suspicious, which the wolves do."

## 2. Checked and supported

- Hundreds of lines by day four, carried in every call; one call per day before the vote: report §1.
- Two lists, at most 30 words a field, claimed or retracted, the fixed action and result words, plans kept apart inside each role-claim entry, and the prompt forbids stating a claim as fact: report §2; `claim_ledger.py` (`planned_actions` read per role-claim entry); experiment_log ③ 2026-10-04.
- The speaker's fields come first and the summary fills in per kind of field (a human player or an older game); accusations, retractions and plans come from the summary alone: `build_claim_ledger` (lines 180–253) and its module docstring; report §4 and §8.
- The day-2 rendering and the day-3 "Previous days" block match report §2 and §3. The elisions are marked.
- The labelled blocks came out of the 2026-10-03 code review (engine facts and the summary looked the same once rendered): turn_prompt/report.md decision 3.
- The three authors; checks marked "Record:" or "Rules:"; silent where the record fits more than one reading (the shot player who lived); a check on a living player stays a claim; the ledger is never stored and is rebuilt for every prompt: `claim_ledger.py` docstring and the `role_checks` / `action_checks` strings; report §3 and §8; discussion_evidence §6.6.
- Role gloss (wolves read Suspicious; the Illusionist is a wolf; the Trailseer follows a player): role_sheet.md.
- Case 1 (game 46355b89): the wolf's premise came from its failed attack on the serial killer, two villagers rejected it, the day-3 summary line is quoted verbatim, three town players took it as fact on day 4, the summary is called the "likely" route, and village dynamics was dropped the next day: discussion_evidence §6.4 and §6.6; experiment_log ③.
- e06: the quoted line and the summary's version are verbatim; the sigilist opened on it; the Investigator accepted it against its own note; voted out 7 to 1 while holding a true Suspicious read; the Necromancer won; the field was left empty, so the ledger fell back on the summary: report §7; discussion_evidence §8.4.
- The fix in two parts, and the role dropped only for a Chanteuse claim resting on a self-block: commit 6248fc58 as described in report §7; the code at `claim_ledger.py:226–237`.
- The first broader rule lost a true Vigilante and was narrowed: replay README, "Reading".
- No recurrence in 10 re-runs (5 per arm), so the code rule is the guard; the two e06 numbers are kept apart and "5 of 5 → 0 of 5" stays off the page: README table; §8.4.
- e06 is why the speaker's fields were extended to night actions: turn_prompt decision 13.
- v3's verdicts were mostly "unverified", "supported" was subjective, the verdicts were dropped between days, and code took over a day later: discussion_evidence §6.6; experiment_log ③ 2026-10-04.
- 6 days × 5 per model = 60, plus 6 live = 66; the record check was written 27 times and all 27 were judged wrong, none a real conflict, then removed; 18 of 30 flawed for each model, with the judge being the stronger model: deduction/experiment_log §3 including the 2026-10-24 note.
- Denials 30 of 30 lost (six days × 5) → 7 of 30 and 0 of 30; a possible cost in true claims that five samples cannot settle: README, "Claim retention".
- The summary runs on the game's own model; the rescue model where one is assigned, otherwise the raw transcript: report §5 (which also notes that a Haiku house game has no rescue model).
- Never compared with the raw transcript, and why it stays anyway; plans, retractions and accusations rest on the summary; no rate for today's prompt; the May judge is retired: report §8; experiment_log ④.
- The summary is not memory: nothing under `Agents/memory/` reads `DaySummary` except the checkpointer's serialiser.
- Off-page items: no bench number, no 97% figure, no model family names in the prose, "judged wrong" throughout, and "checked against the record" kept with every mention of code checking claims.

## 3. Not checked

- **"I changed the summariser…" (ownership):** the records date the 2026-10-03 change but do not say who wrote the prompt. The earlier review reworded this as the owner's design decision. Only the owner can confirm it.
- **The opening line about the private note** ("returns as the private note it wrote last turn"): I did not read turn_prompt/experiment_log.md §2.
- **The exhibits against their raw data:** I checked them against report §2 and §3 only, not against `haiku_summary_compare/summaries.jsonl` or `deduction_placement_n10/prompts/AC2_before_note.txt`.
- **The rescue and raw-transcript path:** I relied on report §5 and did not read `Agents/nodes/day/summary_agent.py`.
- **The unit tests:** I did not re-run them. That they are "pinned by unit tests" rests on report §6, where they passed at `c0732f88`.
