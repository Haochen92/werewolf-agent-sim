<!-- editorial review of writeup/context_engineering/context_engineering.md by claude (opus), 2026-10-30T04:47Z -->

## 1. The argument as I understood it

The page asks how to stop AI players in a Werewolf-style game, all running on a small, low-cost model, from getting facts wrong in their own turns. Its central answer is that each kind of mistake needs its own fix, and the fixes share one principle: **code works out what is certain, and the model keeps the judgement.** Four sections take four kinds of failure:
- facts that are present but misread, fixed by having the engine state them explicitly;
- summaries of earlier days that lose meaning or source, fixed by splitting them into three blocks by author, with claims checked by code;
- facts the model has but does not use, fixed by making it write its assessment before acting;
- facts the model has but does not connect, fixed by a deduction engine that writes certain conclusions into the prompt.

Each section supports its fix by replaying the failed turn several times. The closing lines say these replays show that each targeted failure was removed, not that the overall error rate fell.

## 2. Apply the explanation

**Question:** In the Healer case, suppose two players, player_7 and player_3, had both admitted visiting the Healer on night 1. What would the deduction engine add, and would the Healer's identification of player_7 still be "certain"?

**What the page supports:**
- The engine writes conclusions "each worded with its certainty: certain, true if a named claim is true, or the list of possibilities."
- In the actual case it added "one certain line: the Chanteuse came to you that night."
- The facts were: "only the Chanteuse, a wolf, can roleblock, and a block is a visit; the next day player_7 admitted visiting the Healer."

So the certain line would probably stay the same, because it doesn't name anyone. Choosing between player_7 and player_3 would be left to the model, which fits "the model keeps the judgement."

**What I had to supply:**
- In the original case, the step from "the Chanteuse came to you" to "player_7 is the Chanteuse" only works if player_7 was the only visitor, or if the Healer knew who visited. The page doesn't say which. I assumed it.
- The page doesn't say whether the engine uses public statements like "I visited the Healer." The phrase "true if a named claim is true" suggests it might, which would mean it could write "player_7 or player_3." "What that seat is allowed to know" doesn't settle it.
- So I can't tell whether the engine stops at "the Chanteuse came to you" or goes on to name a suspect. That changes what the 2→8 in 10 result means: did the engine do the deduction, or only take the first step?

## 3. Findings

**1.**
- **Where:** Opening, "Lying is part of Werewolf"; and throughout: "Sentinel", "Chanteuse", "illusionist", "visit", "roleblocked", "seat", "game master".
- **Kind:** term before introduction
- **What broke:** The page has no parent, but it assumes I know the game. Werewolf is first named in paragraph 2. Night and day phases, role abilities and the "visit" mechanic are never explained. The Sentinel's "visitor list" and the illusionist being "revealed … as claimed" after reading Suspicious only make sense if I already know these custom roles. "A block is a visit" is the key premise of section 4, and I can't judge it without knowing what a visit is.
- **Repair:** Explain. Add a short orientation before the first failure: the game, its phases, what a visit is, and a one-line definition for each of the five roles the examples use. A compact role table would work.
- **Severity:** blocking

**2.**
- **Where:** Closing, "None of these changes was measured as a whole-game error rate"; and § Facts the model misreads, "the replayed Sentinel conceded 0 times in 10"
- **Kind:** section order
- **What broke:** The method behind every result (replaying one failed turn N times) is only explained in the last paragraph. Before that, the units shift without notice:
  - "3% of public messages"
  - "three of four games"
  - "0 times in 10" (replay samples)
  - "92.5% of the time" (unit unclear)
  
  The opening 3% baseline invites me to expect a before/after error rate. The final paragraph then reverses that expectation.
- **Repair:** Relocate. Put the replay method and its limit in the opening, next to the 3% figure, so every later "N in 10" reads as replay samples.
- **Severity:** blocking

**3.**
- **Where:** § Facts the model has but does not connect, "For the Healer it added one certain line: the Chanteuse came to you that night."
- **Kind:** missing connection
- **What broke:** The conclusion being tested is "player_7 is the Chanteuse." The engine's line doesn't name player_7, and the page doesn't say player_7 was the only visitor. I can't tell which step the model was failing at, or how much the engine did (see §2).
- **Repair:** Explain. State what the Healer saw that night (blocked, plus who visited, if known) and whether the engine's line covers the whole deduction or only the first step.
- **Severity:** worth fixing

**4.**
- **Where:** § Information the model has but does not use, "the stated reasoning and the vote agreed 92.5% of the time, against 75%"
- **Kind:** claim reads stronger than its support on the page
- **What broke:**
  - The unit is missing: turns, replay samples or games?
  - Two changes were made at once (reasoning moved ahead of the vote, and a verdict on each lesson required), but the result is credited to "the order" alone.
  - It's unclear how "agreed" was judged.
- **Repair:** Explain. Give the unit and sample size, and either credit both changes or say which one the comparison isolates.
- **Severity:** worth fixing

**5.**
- **Where:** § Earlier days, "The rule came from a game a summary decided"
- **Kind:** more than one job in a paragraph
- **What broke:** The paragraph does three jobs: the limits of record checks, an origin story, and two fixes. "The rule" grammatically points to the record-check sentence just before it, but the story is about the summariser misattributing a statement. "Code drops any claimed action that could only have been done to the speaker" is hard to parse. I had to reconstruct that "I was roleblocked" describes something done *to* the speaker, which the summary turned into a claim of *doing* it.
- **Repair:** Relocate. Move the record-check limit next to the table's Claims row. Then tell the incident, then state both fixes, tying the code rule explicitly to "I was roleblocked."
- **Severity:** worth fixing

**6.**
- **Where:** § Information the model has but does not use, "which lesson from memory it had followed only after acting"
- **Kind:** term before introduction
- **What broke:** "Lessons from memory" appears here with no explanation. It's only identified in the last sentence as "lessons carried from earlier games" (chapter 4).
- **Repair:** Explain. Add a one-clause forward reference where the term first appears.
- **Severity:** worth fixing

**7.**
- **Where:** § Facts the model misreads or invents, "With the missing rule sentence added"
- **Kind:** missing connection
- **What broke:** "That last line" refers to rules ranking above players' accounts, but the fix tested is "the missing rule sentence," apparently a statement of how the Sentinel's ability works. I can't tell whether one fix or two was replayed, or which produced 0 in 10.
- **Repair:** Explain. Say which sentence was added for the replay and how it relates to the precedence rule.
- **Severity:** worth fixing

**8.**
- **Where:** Opening, "They counted the survivors wrong, misread what an ability shows, believed a mistaken summary"
- **Kind:** section order
- **What broke:** The opening lists four mistakes, but they don't line up with the four sections. The first two both belong to section 1. Nothing in the list matches section 3 (information present but unused). So "the four kinds of failure" doesn't match the list I just read.
- **Repair:** Explain. Restate the list so each item names one section's failure, in section order.
- **Severity:** worth fixing

**9.**
- **Where:** Opening, "in the earlier nine-player game about 3% of public messages held one"
- **Kind:** missing connection
- **What broke:** "Earlier" implies a later or different game configuration that is never mentioned. I can't tell whether the fixes were developed on a different game than the one this figure describes.
- **Repair:** Explain. One clause on which game versions exist, or drop "earlier".
- **Severity:** worth fixing

**10.**
- **Where:** § Information the model has but does not use, "enforcing the answer format through the provider left the game's model doing no reasoning at all"
- **Kind:** other (ambiguity)
- **What broke:** "No reasoning" could mean empty thinking output or empty assessment fields. "Through the provider" versus "as text" assumes I know about provider-side structured-output modes.
- **Repair:** Explain. Name the two mechanisms and what "no reasoning" looked like in the output.
- **Severity:** worth fixing

**11.**
- **Where:** § Facts the model has but does not connect, "Its code was written by an AI coding assistant"
- **Kind:** more than one job in a paragraph
- **What broke:** The paragraph mixes three things: the information-leak safeguard (with "seat" and "chapter 2" undefined here), an authorship disclosure, and the evidence caveat. The caveat repeats the closing paragraph.
- **Repair:** Relocate. Keep the leak test with the engine description and define "seat." Move authorship to a separate note. Remove the caveat that the closing already makes.
- **Severity:** taste

**12.**
- **Where:** Diagram, "Players, checked by code" next to the box labelled "Models"
- **Kind:** unit or term changes meaning
- **What broke:** Players are models too, so labelling one box "Players" and another "Models" blurs the grouping by author that the caption promises. The diagram also names the "deduction engine" three sections before it's explained.
- **Repair:** Explain. Label the boxes by author and status consistently, for example "Other players' claims (checked by code)" and "Model-written summaries and notes."
- **Severity:** taste

## 4. Highest-impact improvements

1. Add an orientation before the first failure: the game, its phases, what a visit is, and a short definition of each role the examples rely on.
2. Explain the replay method and its limits in the opening, so every later "N in 10" has a clear unit and no closing caveat reverses the reader's expectation.
3. Close the gaps in the two key results: what the Healer knew and what the engine actually concluded, and the unit and the two combined changes behind 92.5% versus 75%.
