<!-- editorial review of writeup/game_design_orchestration/evidence_design/evidence_design.md by claude (haiku, smoke test), 2026-10-28T13:30Z -->

## 1. The argument as I understood it

The page asks how to design a social-deduction game, played by LLM agents, so that the town produces evidence it can argue about and evil can contest it. Its answer is to give town roles partial but true observations that must be cross-checked, let evil explain them with false role claims, and add explicit instructions that make evil use that cover. The sections build this in order: the nine-seat game gave too little to contest, the ten-seat redesign supplies partial observers, replays isolate the instruction change and show more role claims, and eight paired whole games show contested claims entering play. The final section narrows the answer to more claiming in sampled situations and says discussion quality and balance are unmeasured, which is weaker than the title's "evidence worth debating". I can state a central answer, but the page gives two, and the closing one does not support the opening one.

## 2. Findings

**1. The game is never described**
- **Where:** Opening paragraph, "In the earlier game, an Investigator could identify a player's exact role"
- **Kind:** term before introduction
- **What broke:** The page never says what the game is. "Town", "evil", "Investigator", "night", "role", "seat", "engine" and "agents" are all used before being explained. I could not tell who wins or what counts as a "claim". "Agents" is not identified as language models until a methods sentence much later.
- **Repair:** Add a short orientation before the first role name: a social-deduction game with hidden evil roles, night actions and daytime accusation and voting, played by LLM agents. Define town, evil, claim and winning in one sentence each.
- **Severity:** blocking

**2. The closing answer is narrower than the title and opening promise**
- **Where:** Final section, "The replay supports a narrower conclusion"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The title and opening promise "evidence worth debating" and describe a case the town can argue. The closing section says only that claiming increased in sampled replays, that "the presence of competing claims does not establish better discussion", and that discussion quality is unmeasured. Nothing on the page defines what "worth debating" would be measured by, so I cannot tell whether the title's claim is met.
- **Repair:** State the measured outcome in the introduction (more contested role claims). Either drop "worth debating" from the title or say what debate quality would have to show.
- **Severity:** blocking

**3. The motivation for the redesign rests on an unmeasured observation**
- **Where:** "The earlier game gave agents little to contest", "My reading was that this combination left little room for evidence-based disagreement"
- **Kind:** claim reads stronger than its support
- **What broke:** The redesign is motivated by discussion that was "thin" and turned to "tone, phrasing and timing". The page gives no count of games, no measure of discussion and no example. The closing section then says "Discussion quality has not been measured against the nine-seat game." I read the first as an observed fact and the last as withdrawing it.
- **Repair:** Label the thin-talk point as a hypothesis that motivated the design, or give the observation it rests on (how many games, what was read). If it cannot be supported, remove it as the reason for the change.
- **Severity:** blocking

**4. The headline replay table reports figures the page says were revised**
- **Where:** "Isolating the instruction change", table under "Across 82 responses per condition"; "Some other labels also changed, including the old-condition denial count."
- **Kind:** other (superseded figures presented as results)
- **What broke:** The table reads as the replay result, but the text says the labels were revised later and the old-condition denial count changed. The page never gives the revised numbers or says which judging produced the table, so the headline shift (13 to 33 claims, 21 to 3 denials) cannot be taken as final.
- **Repair:** Replace the table with the final labels, or show initial and final columns side by side, and say which judging produced each figure.
- **Severity:** blocking

**5. The isolation claim is weaker than the heading says**
- **Where:** "Only the card text changed." and "and their private notes still came from games using the old instructions."
- **Kind:** caveat reverses an earlier claim
- **What broke:** The section is titled "Isolating the instruction change" and says only the card text differed. Later, the private notes, which were held constant, came from old-instruction games. That is a partial control with a known direction of bias, and the page does not assess it. The reader has to reconcile the two statements.
- **Repair:** State the limitation in the design paragraph, and retitle the section (for example, "Replaying the instruction change") if the control is partial.
- **Severity:** worth fixing

**6. The replay units change without notice**
- **Where:** "41 recorded turns in which an evil agent had been accused"; table row "Across 82 responses per condition (41 turns × 2)"
- **Kind:** unit or term changes meaning
- **What broke:** The unit moves from turns to situations to responses within one section. "Turn" is never defined. The table counts claims and denials out of 82, but the other responses are not described, so no rate can be read. "One judge per line" uses "line" for a unit the reader cannot identify.
- **Repair:** Define a turn once. State that there are 82 responses per condition from 41 situations, list every response category so the columns account for all responses, and define "line".
- **Severity:** worth fixing

**7. An engine change is introduced without setup**
- **Where:** "supply possible night stories consistent with the evil agent's actual visits"
- **Kind:** term before introduction
- **What broke:** The whole-game test depends on this engine feature, but nothing before it says the engine can generate explanations for visits. "Night stories" is used as an established term.
- **Repair:** Add one sentence before the change saying what an engine-supplied night story is and why it was needed (proposed covers contradicted the true visits).
- **Severity:** worth fixing

**8. The Ash example skips its key inference**
- **Where:** "an agent reports tracking Ash to Birch, but Ash claimed to protect Clover."
- **Kind:** missing connection
- **What broke:** The reader has to supply why a visit to Birch contradicts a protect claim for Clover: a protector's claim implies a visit to the protected player. The example also does not name the protecting role, and it says "tracking" where the table says "follows".
- **Repair:** Name the protective role, state the expectation in one clause, and use the table's verb.
- **Severity:** worth fixing

**9. The mechanics paragraph does three jobs**
- **Where:** "Evil can instead remove evidence: the Illusionist conceals a victim's role and the wolf's visit to that victim."
- **Kind:** more than one job in a paragraph
- **What broke:** The paragraph states a design rule (reports stay truthful), introduces the Illusionist and the block mechanic, and points to the role sheet. "Illusionist", "block", "wolf" and "victim" are used before any explanation. The block sentence does not say which role blocks.
- **Repair:** Separate the design rule from the mechanics. Name the blocking role and define "victim" before using it.
- **Severity:** worth fixing

**10. The public-records paragraph introduces several mechanics at once**
- **Where:** "The lineup is known, with one true holder of each dealt role"; "When a town player dies with its role revealed, the engine publishes its earlier night results"
- **Kind:** term before introduction
- **What broke:** "Lineup", "dealt role", "claim ledger" and "a concealed body" are undefined. "Dies with its role revealed" implies a rule the page never states: how a role becomes revealed. I cannot tell whether the lineup is public from the start.
- **Repair:** State once what is public at the start and when a role becomes public, then say what each record lets agents do.
- **Severity:** worth fixing

**11. The same things carry several names**
- **Where:** "a reported visit as proof of the visitor's role"
- **Kind:** unit or term changes meaning
- **What broke:** Engine output is called an observation, sighting, reading, result, report, check and watch. "Report" also names the documents at the end. "Cover" means a strategy, a claimed role and a story. "Seat", "player" and "agent" alternate for the same participants. I cannot tell whether "a reported visit" is engine output or an agent's statement.
- **Repair:** Choose one term per concept (for example, observation for engine output, claim for an agent's statement, cover for a claimed role plus story), define it on first use, and keep it.
- **Severity:** worth fixing

**12. The 24-of-28 figure arrives before its meaning and before its caveat**
- **Where:** "found that the Investigator claimed publicly in 24 games."
- **Kind:** number before orientation
- **What broke:** "24" appears before the reader knows what a claim or a game is. The denominator (28) is there, but the page does not say whether this is a rate. The caveat that the analysis used model-generated labels comes in the next sentence, after the figure has been read as a finding.
- **Repair:** State "24 of 28 games" once, define claim and game, and put the labelling caveat in the same sentence or immediately after.
- **Severity:** worth fixing

**13. The model and condition switch is not explained**
- **Where:** "An exploratory analysis of 28 games on Gemini 3.5 Flash-Lite, with memory off"
- **Kind:** missing connection
- **What broke:** The page moves between Gemini (baseline and balance batches), Haiku 5.5 (replays and paired games) and Sonnet (judges) without saying which results can be compared. "Memory off" is a condition the page never explains.
- **Repair:** Add a short note or table saying which experiment used which model and what memory means, and say whether results are comparable across them.
- **Severity:** worth fixing

**14. A design stance is reversed without a reason**
- **Where:** "I initially avoided prescribing a fake-claim strategy."; "This deliberately steers the agent towards maintaining a cover"
- **Kind:** missing connection
- **What broke:** The page moves from avoiding a deception strategy to prescribing one. Its only stated justification is that the agent "still chooses the role and the story". The reader wants to know why the earlier avoidance was dropped and where the author draws the line.
- **Repair:** Give the reason for the change and the boundary in one or two sentences.
- **Severity:** worth fixing

**15. Failure modes are reported without counts**
- **Where:** "Agents sometimes treated a watch as clearing the watched player"; "Others denied sightings rather than offering a different explanation for the visit."
- **Kind:** one example standing for a general rate
- **What broke:** Errors are described as "sometimes", "others" and "other games", with no totals. The reader cannot judge how common each error was or whether the later fix worked. The sentence "it was not enough to establish that permission alone could never work" is a double negative that blurs its conclusion.
- **Repair:** Give a count for each failure mode (x of y games or turns) and state what the two-game observation covers.
- **Severity:** worth fixing

**16. The whole-game table has an undefined denominator and a shifted term**
- **Where:** "Evil seats that claimed a role, out of 24"; "Eight ten-seat deals were each played under an earlier and a revised version"
- **Kind:** number before orientation
- **What broke:** "Out of 24" has no explained denominator; the page never says there are three evil seats per game. "Earlier" now means the earlier engine version, while earlier in the page it meant the nine-seat game. "Recognition of role claims implied by a described action" is unexplained.
- **Repair:** State the three evil seats per game, rename the baseline ("pre-change version"), and describe the recognition feature in plain terms.
- **Severity:** worth fixing

**17. The whole-game result is stated before its caveat**
- **Where:** "These cases show that competing accounts entered play and could persuade town."
- **Kind:** claim reads stronger than its support
- **What broke:** The claim rests on two of three wolf wins and one vignette. The caveat that eight pairs do not establish a change in win probability comes after the table and the anecdotes, so the "Winners" row reads as the result first.
- **Repair:** Move the caveat next to the table and present the vignette as an illustration rather than evidence of persuasion.
- **Severity:** worth fixing

**18. The final section introduces new checks and jargon**
- **Where:** "scripted-model games exercise the real graph across two lineups that together include every drawn role"
- **Kind:** term before introduction
- **What broke:** Rule-correctness checks and balance batches appear for the first time in the last section. "Graph", "lineups", "drawn role", "balance batch" and "balance" are undefined, and "Evil won some later games" does not say which games.
- **Repair:** Define balance (for example, town versus evil win rate) and each test type where it first appears, or reduce this paragraph to a pointer to the roles report.
- **Severity:** worth fixing

**19. The scope caveat points to something the reader cannot see**
- **Where:** "A later warning about dangerous cover choices has only prompt-test coverage"
- **Kind:** missing connection
- **What broke:** The reader does not know what the warning is, so the caveat about later instruction changes cannot be applied. "Cross-night checks" and "stronger reasoning" in the same section are also undefined.
- **Repair:** Name the warning in one clause, or remove the sentence if it is not part of the argument.
- **Severity:** worth fixing

**20. Internal section labels in the evidence list**
- **Where:** Evidence list: "decisions 1–5 and 10"; "§2 (the nine-seat census) and §3 (the permission paragraph)"
- **Kind:** detail that does not change understanding
- **What broke:** These labels point to sections of documents the reader will not open. "Census" and "permission paragraph" are not explained.
- **Repair:** Replace with one line per linked document saying what it contains.
- **Severity:** taste

**21. The memory-experiment aside**
- **Where:** "The nine-seat game had originally been chosen for a memory experiment"
- **Kind:** detail that does not change understanding
- **What broke:** The aside explains the seat count with a different experiment. It leaves "memory", which later appears as a condition, undefined.
- **Repair:** Cut the sentence, or give one clause saying what the memory condition is.
- **Severity:** taste

## 3. The three changes that would help this reader most

1. Open with a paragraph that defines the game, the roles, town, evil, claim and winning, and says the players are LLM agents, before any role name appears.
2. Make the title and introduction match the measured result (more contested role claims), and either measure debate quality or drop "worth debating" and the thin-talk motivation.
3. Replace the replay table with the final labels covering every response category, and move the old-instruction notes caveat into the design paragraph.
