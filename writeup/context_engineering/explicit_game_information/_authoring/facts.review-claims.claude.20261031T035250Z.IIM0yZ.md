<!-- claims review of writeup/context_engineering/explicit_game_information/facts.md by claude (opus), 2026-10-31T03:52Z -->

## 1. Findings

- **Claim:** "A stated rule guards the origin of a misreading. It does not undo one the players have already repeated to each other" (§ What mechanics needed spelling out?)
  - **Source checked:** `evidence/gameplay/discussion_evidence.md` §8.6 "The replay", "Cascades"; `evidence/gameplay/data/haiku_turn_replay/README.md` totals; `evidence/gameplay/data/phase3_turn_replay/README.md` (f02 tables).
  - **Verdict:** conflicts with source
  - **Why:** The wording comes from the f02 replay of 2026-10-10. The later visit replay, which the page cites in the same paragraph, contradicts it. In that replay cascade turns fell from 11 to 3 of 20, and §8.6 says "A stated rule did more against a spreading misreading than the f02 replay (§8.4) found". On f02 itself the ranking line took the cascade turns on one model from 7 to 4 of 10, so "does not undo" is too absolute. "Guards the origin" was never shown either. The f02 first speaker made the error 1 in 5 times even before the sentence, and §8.6 says the three origin turns are "too few to measure the rule on its own".
  - **Suggested scope:** "On that game's later turns, a stated rule did little against a false rule the players had already repeated: 10 of 10 → 7 of 10, 4 of 10 with the ranking line, and no change on a smaller model. In the visit replay, cascade messages did fall (11 → 3 of 20). So how far a stated rule reaches a misreading already in the transcript is open, and these are single-game replays."

- **Claim:** "in the one comparison in this chapter whose measure was written down before its data existed" (§ Did making the facts explicit suffice?)
  - **Source checked:** `evidence/evaluation/factual_errors/experiment_log.md` §2 intro ("All three replays were pre-registered in `validation_plan.md`"); `evidence/gameplay/turn_prompt/validation/t1b_results.md` ("The pre-registered expectation…"); turn_prompt `report.md` ("The strongest planned comparison").
  - **Verdict:** conflicts with source
  - **Why:** T1b, which this page describes two paragraphs earlier, also had its expectation written into the plan before it ran, and so did T2. The report calls T1c the *strongest* planned comparison, not the only one.
  - **Suggested scope:** "in the most firmly planned comparison behind this page: its measure was written into the plan before the second run's data existed."

- **Claim:** "Not on its own, and the first test of the board lines said so before they shipped" (§ Did making the facts explicit suffice?). The same claim appears in §1: "the first replay of the board said it did not on its own".
  - **Source checked:** `t1b_results.md`; factual_errors log §2 T1b.
  - **Verdict:** overstated
  - **Why:** The verdict rests on one error case. It recurred 2 of 6 times with the board, 1 of 6 with the full board and 0 of 6 without it. The T1b record itself says "At N=6/arm no directional claim between arms is supportable". The bundle test never ran the board without the reads, so nothing else on the page shows that the board alone fell short.
  - **Suggested scope:** "Not reliably: in the one replayed error that recurred, a correct roles-still-in-play line did not stop it, so the board was kept as a reference and reads were added."

- **Claim:** "Each sentence was measured by replaying the turns that had shown the error, on the same model." (§ What mechanics needed spelling out?)
  - **Source checked:** `haiku_turn_replay/README.md` (arm definitions); `phase3_turn_replay/README.md`.
  - **Verdict:** overstated
  - **Why:** The visit result (16 of 35 → 5) comes from the "after v1" arm, which added three prompt changes at once: the visit rule, the reply brief and the vote-reason line. That result does not isolate the visit sentence. The Illusionist sentence was also replayed on a second, smaller model, which the page reports in the next sentences.
  - **Suggested scope:** "Each fix was replayed on the turns that had shown the error, on the model that made it. The visit rule was tested together with two other prompt lines added the same day."

- **Claim:** "I wrote the missing rules in, stated both ways" (§ What mechanics needed spelling out?)
  - **Source checked:** `discussion_evidence.md` §8.4 ("The owner ruled the same day … and the rules now say so"), §8.6 ("The fix states both ends…").
  - **Verdict:** ownership · unclear (needs the owner)
  - **Why:** The records show that the owner made the rulings: the Illusionist carrier is invisible, and the Sentinel is not among its own visitors. They do not say who drafted the rule text. The page's sources note equates the ruling with the writing.
  - **Suggested scope:** Keep it if the owner drafted the text. Otherwise write "I ruled what the engine does and had the missing rules written in, stated both ways."

- **Claim:** "about 3% of public messages carried a factual error of some kind" (opening)
  - **Source checked:** `evidence/evaluation/factual_errors/report.md` Step 1; log §1.
  - **Verdict:** overstated
  - **Why:** The census counted role-fact errors only: deaths, roles, counts of who is left, and who claimed what. It could only see what its four screen rules catch, and the report calls the counts floors. It excludes by design an invented event that names no player or role, and also "I investigated player_9". "Of some kind" turns that into a rate for all factual errors.
  - **Suggested scope:** "about 3% of public messages carried an error about deaths, roles or claims, counted as a floor."

- **Claim:** "Next to the public announcement quoted in the first section it read as a repeat of public news" (§ What could the wording mean?)
  - **Source checked:** `discussion_evidence.md` §6.2 "How the prompt may have set it up" ("readings of the prompt's structure, not measurements"); turn_prompt `report.md` decision 2.
  - **Verdict:** unsupported inference
  - **Why:** The replay shows that rewording the line removed the invention. It does not show how the model read the old line. The page states the interpretation as an observed fact and puts it in a causal chain with the false announcement.
  - **Suggested scope:** "Next to the public announcement it could read as a repeat of public news."

- **Claim:** "the samples with a factual error went from 97 to 82 of 267" (§ What never reached the prompt at all?)
  - **Source checked:** `discussion_evidence.md` §6.5 table and bullets; factual_errors log §9 "Verification".
  - **Verdict:** overstated (minor)
  - **Why:** 82 is the arm in which earlier days were also rewritten by the new summariser. The plain "after" arm was 86 (18 better / 11 worse, p = 0.26). The verdicts come from a flash-lite judge that §6.5 says "needs work". The page's hedge, "with substantial uncertainty", covers the size of the change but not the fact that the arm bundles a summary rewrite.
  - **Suggested scope:** Add "with earlier days re-summarised as a live game would have them" and "judged by a model reader".

- **Claim:** "The healer had no record of its own past protections, so it could not say whom it had protected on night 2" (§ What never reached the prompt at all?)
  - **Source checked:** factual_errors log §8, finding 1.
  - **Verdict:** overstated (minor)
  - **Why:** The audit says it "cannot reliably answer … from engine facts in its prompt" and that "a strategy note may hold this". This was confirmed in the code. Its effect on behaviour was not measured.
  - **Suggested scope:** "so nothing the engine wrote could tell it whom it had protected on night 2."

- **Claim:** "reading the games in October found a second case … because the player had to reconstruct it from prose spread over several days" (opening)
  - **Source checked:** turn_prompt `report.md` decision 1 (shipped 2026-07-09); log §2.
  - **Verdict:** conflicts with source (timeline, minor)
  - **Why:** The reconstruct-from-prose case was found and fixed in July. By October the board was already in the prompt. October found the wording and unstated-rule cases.
  - **Suggested scope:** "reading the games, in July and again in October, found a second case…"

## 2. Checked and supported

- The announcement line and both board lines are verbatim from the as-played prompt: `evidence/gameplay/data/investigator_replay/prompt_A.txt` lines 106–110 and 169. Only the second sentence of the announcement is cut.
- What the board shows, and the hidden-body clause "(one of these is dead: a body whose role is hidden)": `Agents/prompts/prompt_formatters.py::format_dead_roster`, `format_alive_roles`; report "The board facts".
- The first version left deaths to be worked out from the game master's prose: report decision 1 "Instead of".
- The commonest census error was survivor arithmetic, "the remaining wolf": factual_errors report Step 1 table, 221 of 368.
- The code review found 12 places; the healer, vote-note and same-heading findings match: log §8, findings 1, 3 and 5.
- 8 of the 12 findings addressed and 4 partly, where "addressed" means the wiring: log §9 table and its closing line.
- The 89 cases × 3 samples, 24 better / 14 worse, "an improvement in this sample, with substantial uncertainty": report decision 3; §6.5.
- Night-record wording, "(last night)", "you checked", and the quiet-night reasons: `prompt_formatters.py::format_night_actions`, `_quiet_nights`. A generic "you did not act." remains for edge cases.
- The vote turn now sees its note, and earlier days come in three labelled blocks: log §9; `format_day_summaries`.
- The invented-check story, the quote pair, 20/20 → 0/20 with the real check in 20/20, two changes at once, and "one turn of one game": §6.2; report decision 2. "The wording, not the reasoning" stays off the page.
- The fix ships in every game, not behind a switch, as a correctness bug: §6.2 "The fix".
- October ten-player games: invented facts rare (2 in ten audited games), and invalid deductions about abilities the commonest player error: §8.4.
- The f02 case (four players, the real Trailseer voted out, the carried kill leaves no trace): §8.4; `phase3_turn_replay/README.md`.
- The rules defined a visit in the passive, and the role cards say what an ability learns, never what it cannot: §8.6.
- The visit rule text and the closing "These rules are exact…" lines are verbatim in `Agents/prompts/game_rules.py` (lines 70–74 and 103–104).
- Visits 16 of 35 → 5 on 18 frozen turns, 5 samples each: §8.6; haiku_turn_replay README.
- Illusionist replay: 10 → 7 → 4 of 10 on one model, 10 of 10 on the smaller one, and the first speaker seldom erred: phase3_turn_replay README.
- T1b: four errors, 6 samples × 3 arms, three never recurred in any arm (including no change), the fourth recurred with a correct roles line: log §2; t1b_results.md.
- T1c: error-prone census turns, one sample per arm, the census reader, run 1 rewording, 100 fresh contexts, 48% vs 30%, 29 better / 11 worse: log §2; report decision 1.
- The T1c limits paragraph (selected turns, no hand read of the verdicts, vote turns rebuilt with the result in view, board and reads never tested apart) matches log §2 "How far to trust T1c" and report decision 1.
- "What is not established" (no ten-player rate, no whole-prompt comparison, rule sentences recited) matches report "What is not established".
- Off-page items: no 0.14%, no test authorship, no model names, no opening-order mismatch, and the census's "never re-run" status is absent. The Handle-with-care list is respected.

## 3. Not checked

- **Reads cost "about 60% more output" and the board adds none:** I did not open the T2/T3 records (`t2_results.md`, T3). The claim is taken from report decision 1 as it stands.
- **"Every call now carries two board lines below the transcript", wolf chat included:** I did not open `Agents/prompts/layout.py` or `night.py`. The claim rests on the report at `588a3273`. In the as-played 2026-10-03 exhibit the board sat above the transcript, which is the earlier layout.
- **Rule sentences recited as arguments:** I did not open the R11 entry in `evidence/gameplay/deduction/experiment_log.md`. The claim is taken from report "What is not established".
- **The Sentinel concession:** only its kind was checked, against §8.4 and the phase3_turn_replay README. Its number stays on the parent page.
- **The day-4 vote of game `832404e9`:** the page only says the village voted out the player the investigator named. I checked this against the records (§6.2), not against raw game data.
