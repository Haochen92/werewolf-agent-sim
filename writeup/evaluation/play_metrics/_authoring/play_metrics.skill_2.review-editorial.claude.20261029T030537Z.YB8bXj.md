<!-- editorial review of writeup/evaluation/play_metrics/play_metrics.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:05Z -->

## 1. The argument as I understood it

The page asks how to judge whether one version of the agents plays better than another when win rate needs more games than the project can run. Its answer is to grade individual decisions against the true roles, using a fixed rule table that code applies, and combine the grades into a per-game rate. Each rate is then checked against real wins before it is trusted as a proxy for playing strength. The sections build in this order: why decisions are steadier than wins, how a decision is graded and turned into a rate, and how the win correlation is checked. The expanded ten-player game then serves as the test case: the lynch share carried over to it, the healer's save rate did not, and many new-role scores could not be judged at 78 games. The page ends with what correlations cannot show. Its central lesson is that a move can be correctly counted as good without being a proxy for winning, and the two need separate evidence.

## 2. Findings

**1.**
- **Where:** "When the game expanded", paragraph 4: "What differed was how long it lived: 3.25 protection nights in games the town won, 2.48…"
- **Kind:** missing connection
- **What broke:** The page shows that saves per game were the same in wins and losses, but the healer lived longer in won games. Because the rate divides by protection nights, a longer life lowers the rate in exactly the games the town won. That looks like a mechanical reason the rate stopped tracking wins. The page never draws this link. Instead it moves to a different explanation (choosing whom to guard became a harder guess), so I could not tell whether the lifespan numbers support that reading, weaken it or are unrelated. It also cuts against the earlier reason for using a rate ("a healer who lived nine nights would outscore one killed…").
- **Repair:** Explain. Say what the lifespan difference does to the rate's denominator, and place the "harder guess" interpretation relative to that effect.
- **Severity:** blocking

**2.**
- **Where:** "Checking that good moves win games", last paragraph: "On the original game, the check chose the scores: 48 candidates were tried and 11 kept."
- **Kind:** caveat reverses an earlier claim / section order
- **What broke:** "Grading a decision by the rules" reads as the general method: rules define good moves and code applies them. Only here do I learn that the rule table exists only for the expanded game, and that the original game's scores were chosen by correlation. That changes how I read the original +0.65 and +0.36. They are the survivors of 48 candidates, which matters for the claim that the healer's drop is unlikely to be chance.
- **Repair:** Relocate. Say near the start of the grading section that the two games used different selection methods. Also acknowledge the selection when comparing the original and expanded correlations.
- **Severity:** worth fixing

**3.**
- **Where:** "When the game expanded", paragraph 4: "a direct comparison of the two correlations makes chance an unlikely explanation for the drop."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** No test, statistic or p-value is given. The original correlation also has no interval and was picked from 48 candidates (finding 2). As written, I have to take the conclusion on trust.
- **Repair:** Explain. Give the comparison's result in one clause, or soften the claim.
- **Severity:** worth fixing

**4.**
- **Where:** "Grading a decision by the rules", last paragraph: "a situation summary, existed only in games with memory switched on"
- **Kind:** term before introduction / more than one job in a paragraph
- **What broke:** This is the first time memory appears as an on/off condition in comparisons, and "situation summary" is never defined. The paragraph does three jobs: it states a limitation of grading (luck inside a decision), describes a rejected design, and explains a bias specific to the memory experiment. The memory condition matters later (memory-off readings), but it is introduced here inside a side branch.
- **Repair:** Remove the rejected-weighting branch, or cut it to one sentence. Introduce memory on/off as a compared condition where the "Two readings" paragraph first needs it.
- **Severity:** worth fixing

**5.**
- **Where:** "Checking that good moves win games": "On the original game, the town's lynch scores passed clearly."
- **Kind:** missing connection
- **What broke:** "Passed" is never defined. A failing score is defined later ("an interval that rules out a link of a size worth having"), but there is no threshold for passing on either game. So I can't tell why +0.65 passes while +0.36 or +0.29 does or doesn't.
- **Repair:** Explain. State the pass criterion before the first result.
- **Severity:** worth fixing

**6.**
- **Where:** "When the game expanded", paragraph 1: "several scores read zero in the first 28 ten-player games even when the event happened."
- **Kind:** more than one job in a paragraph / missing connection
- **What broke:** One paragraph gives the headline result, lists the new roles and reports a scoring-code bug. I couldn't tell whether the 28 games are among the 78 analysed, or whether they were rescored.
- **Repair:** Explain in one clause whether the 28 are included and rescored. Then split the bug fix from the description of the new roles.
- **Severity:** worth fixing

**7.**
- **Where:** "When the game expanded", paragraph 4: "of 220 protections that went ahead, 79 saved a player who was attacked"
- **Kind:** unit or term changes meaning / number before orientation
- **What broke:** The table defines a save as protecting a townsperson who was attacked and survived. Here a save becomes "a player who was attacked", and 23 of the 79 had someone else die that night. I could not tell whether 79 is the numerator of the save rate. The paragraph also packs in eight numbers, and only two of them (save counts per game in wins and losses, and lifespan) carry the argument.
- **Repair:** Keep the numbers that feed the explanation in finding 1 and say which of them is the rate's numerator. Cut or move the rest.
- **Severity:** worth fixing

**8.**
- **Where:** Healer save-rate table: "Another role blocked the healer's protection"
- **Kind:** term before introduction
- **What broke:** The blocking role is introduced only in the next section ("a wolf-side role that can block…"). A reader of the nine-player context doesn't know such a role exists.
- **Repair:** Explain. Add a short parenthetical saying that the expanded game adds a wolf-side role that blocks night actions.
- **Severity:** taste

**9.**
- **Where:** "Checking that good moves win games": "Batches played on different setups can differ in both play and results"
- **Kind:** term before introduction
- **What broke:** "Batch" and "setup" are not defined. Only later do I learn the ten-player games ran "mostly on different models", which suggests setups mean model choices, but I had to infer this.
- **Repair:** Explain. Say in one clause what varies between batches.
- **Severity:** worth fixing

**10.**
- **Where:** Expanded-game table: "−0.03 (… 75 games)" against "78 ten-player games" above
- **Kind:** number before orientation
- **What broke:** The game count changes without explanation. The "not dealt" row in the earlier table suggests why, but I had to work it out.
- **Repair:** Explain in a short clause or caption note.
- **Severity:** taste

**11.**
- **Where:** "When a result is too weak to read", paragraph 2: "The investigator's pattern reappeared among the information roles… (+0.19, p = 0.12, 66 games)"
- **Kind:** detail that does not change understanding / unit or term changes meaning
- **What broke:** The section's point (rare roles leave scores untested) is already made by the vigilante example. This branch adds a third role group, switches from intervals to a p-value, and changes "finds" to "named".
- **Repair:** Remove, or reduce to a single pointer to the linked page.
- **Severity:** taste

**12.**
- **Where:** "What the checks do not establish": "The check also tested per-game scores, not the table that grades every decision."
- **Kind:** missing connection
- **What broke:** I had understood per-game scores as built from the table's grades, so I couldn't see what "the table as a whole" would mean as a separate untested object. Is it an aggregate score, or the grades for turn types that have no score?
- **Repair:** Explain in one sentence what testing the table would involve that testing the scores does not.
- **Severity:** taste

**13.**
- **Where:** Opening: "could reliably detect only a difference of about 35 points in win rate."
- **Kind:** number before orientation
- **What broke:** "Reliably" has no stated confidence or power, and "points" (percentage points, I assume) is left implicit. The figure is persuasive, but I couldn't judge how strict the comparison is.
- **Repair:** Explain the standard in a short clause.
- **Severity:** taste

## 3. Highest-impact improvements

1. Connect the healer's lifespan numbers to the rate's denominator before giving the "harder guess" interpretation. The central example currently leaves its likeliest explanation unstated.
2. Say early that the original game's scores were chosen by correlation from 48 candidates and only the expanded game used a rules-first table. Then qualify the claim that the healer's drop is unlikely to be chance.
3. Trim the side branches (rejected confidence weighting, the information-role p-value, surplus healer counts), and introduce memory on/off and "batch" where they are first needed.
