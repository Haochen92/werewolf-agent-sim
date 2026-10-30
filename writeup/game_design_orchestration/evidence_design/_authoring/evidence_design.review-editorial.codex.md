<!-- editorial review of writeup/game_design_orchestration/evidence_design/evidence_design.md by codex (gpt-6-astra, smoke test), 2026-10-28T13:30Z -->

## 1. The argument as I understood it

The page asks how to give game-playing agents evidence they can contest, and how to get evil agents to offer competing accounts. Its central answer is to replace exact role identification with partial observations, then explicitly instruct evil agents to construct plausible covers. The sections move from an observed lack of competing claims through the information redesign, an isolated instruction test, and whole-game comparisons with additional support. The evidence supports increased claiming in sampled situations and examples of false claims persuading town; it does not establish better discussion, stable balance, or improved reasoning.

## 2. Findings

1. **Where:** “Give the town partial evidence it can cross-check” — “the Illusionist conceals a victim's role and the wolf's visit to that victim.”
   - **Kind:** missing connection
   - **What broke:** A visit has been defined as an action that went ahead, the Sentinel learns who visited, and engine reports remain truthful. I cannot reconcile those statements with concealing a visit: does an observer receive an incomplete list, no result, or a different kind of report? This affects what agents can legitimately infer from the central evidence system.
   - **Repair:** Explain what each affected observer receives when a visit is concealed and what an absent visit establishes.
   - **Severity:** blocking

2. **Where:** “Isolating the instruction change” — “Some other labels also changed, including the old-condition denial count.”
   - **Kind:** caveat reverses an earlier claim
   - **What broke:** The table gives precise counts and supports a clear reduction in denials, but the subsequent paragraph says some counts were revised without supplying the replacements. I cannot tell which table entries remain supported or assess the final size of the reported change without opening the linked record.
   - **Repair:** Present the final assessment counts on the page and identify which conclusions survive reassessment.
   - **Severity:** worth fixing

3. **Where:** “What changed when the claims entered games” — “recognition of role claims implied by a described action”
   - **Kind:** missing connection
   - **What broke:** The revised version changes claim recognition while the outcome being counted is agents who claimed a role. I cannot tell whether both versions were evaluated using the same definition, or whether some of the increase from 3 to 11 comes from recognizing claims that previously went uncounted.
   - **Repair:** Explain what claim recognition changes and whether the reported counts use the same assessment rule across versions.
   - **Severity:** worth fixing

4. **Where:** “Page copy (draft)” — “In the earlier game, an Investigator could identify a player's exact role”
   - **Kind:** term before introduction
   - **What broke:** The opening assumes I know the game and its factions. I can infer a hidden-role game, but the relationship between town, wolves, the Serial Killer and “evil” is never stated; neither is the connection between night actions, public discussion and voting players out.
   - **Repair:** Introduce the game’s basic cycle, opposing factions and use of “evil” before describing the earlier design.
   - **Severity:** worth fixing

5. **Where:** “What changed when the claims entered games” — “under an earlier and a revised version”
   - **Kind:** unit or term changes meaning
   - **What broke:** “Earlier” initially refers to the nine-seat game, then “old” refers to role-card instructions, and here “earlier” refers to a ten-seat version. The final references to “today’s rules” and subsequent instruction changes add another version boundary. I have to reconstruct which design each result actually evaluates.
   - **Repair:** Identify the shared rules and changed components for each comparison, and distinguish the evaluated version from the current version.
   - **Severity:** worth fixing

6. **Where:** “Isolating the instruction change” — “with one judge per line”
   - **Kind:** unit or term changes meaning
   - **What broke:** The test begins with recorded turns, generates responses, then assigns judges to spoken “lines.” I do not know whether a line is an entire response or part of one, or whether claims and denials are mutually exclusive response labels. That leaves the table’s counting procedure unclear.
   - **Repair:** Define the judged unit and explain whether one response can count as both a claim and a denial.
   - **Severity:** worth fixing

7. **Where:** “What the redesign establishes—and what remains open” — “scripted-model games exercise the real graph across two lineups”
   - **Kind:** more than one job in a paragraph
   - **What broke:** This paragraph moves through execution testing, role coverage, balance experiments, design changes and model coverage. “Scripted-model” and “real graph” introduce implementation concepts without explaining what they test, while the balance discussion answers a different question from the claiming experiments.
   - **Repair:** Separate execution validation from balance evidence and describe the tested behavior in terms understandable without repository context.
   - **Severity:** worth fixing

## 3. The three changes that would help this reader most

1. Establish the game’s basic rules and explain exactly how concealed visits coexist with truthful observer reports.
2. Give the final replay counts and clarify whether whole-game claim counts use a consistent recognition rule.
3. Name the evaluated versions consistently so readers can connect each result to its rules, instructions and engine support.
