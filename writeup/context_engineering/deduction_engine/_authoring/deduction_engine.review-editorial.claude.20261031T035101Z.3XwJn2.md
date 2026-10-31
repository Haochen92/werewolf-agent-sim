<!-- editorial review of writeup/context_engineering/deduction_engine/deduction_engine.md by claude (opus), 2026-10-31T03:51Z -->

## 1. The argument as I understood it

The page asks why and how the project works out some game conclusions in code instead of leaving them to the model. Its answer is that a small model at a low thinking setting misses easy first inferences, such as "I was blocked, so the Chanteuse visited me." Stronger or slower settings catch these, but they cost far more, so code computes a selected set of conclusions and adds them to the prompt. The model still makes the judgements. The page then shows how a conclusion is built: what the seat can see, then the rules as traits, then a solver that narrows each player's possible roles, then the printed line. Next it explains the three strength grades for printed lines and why the grading matters: models adopt injected lines almost every time. Two boundaries follow: the engine uses only what the seat can see (checked by a metamorphic test), and it states consequences rather than advice. The page ends with replay results that bound the benefit to "a substitute for a costlier configuration on a step of this kind," and with the engine's scope limits.

## 2. Apply the explanation

**Question:** Suppose the cast had no other visiting role that could have reached the healer on night 1, and player_3 and player_7 still say player_7 visited. What line would the engine print about player_7, and with which grade?

**Answer from the page:** The page says the second line stops short of naming player_7 for two reasons: "Another visiting role could also have come to the healer that night," and "a true report does not establish the reporter's role." The variation removes the first reason. The Conditional grade holds "in every such game in which the named claims are also true," and such lines come from "running the solver again with the named claim assumed true." So the line should be conditional: "If player_3's report is true, player_7 is the Chanteuse."

**Gaps I had to fill:**
- I can't tell whether the second reason would still block this line. "The reporter" could mean player_3 (who reported the visit) or player_7 (who "agrees"). If it means player_3, it seems to bear only on whether the claim is true, which the conditional already assumes. I settled on that reading by working it out myself, not from the text.
- Which mechanism would produce the line is unclear. The page says "The healer's lines do not need" the solver, yet conditional lines come from rerunning the solver. The healer's actual second line is conditional on a claim.
- The grade of the original line is unclear too. The grade table files it under Alternatives, but it opens with "If that is true," which is the Conditional form.

## 3. Findings

**1.**
- **Where:** What changed in replayed decisions, row 1: "'Without' restores the game's original night record, whose 'you learned nothing tonight' works against the deduction"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The opening says the healer "had every premise in front of it." The parent attributes 8 of 10 against 2 of 10 to the deductions. This caveat says the "without" arm got a night record that worked against the deduction, so the headline comparison mixes the engine with an input repair. That undermines the cost argument too. The page benchmarks the engine against high thinking (9 of 10) and larger models (9 and 10 of 10). I can't tell whether those runs saw the original misleading record or the repaired one. If they saw the repaired one, the "substitute for a costlier configuration" comparison isn't like for like.
- **Repair:** State what each arm received (night record and engine lines) before giving any numbers, and say which record the high-thinking and larger-model runs used. If the opening premise only holds after the input repair, qualify it there.
- **Severity:** blocking

**2.**
- **Where:** Narrowing the possible roles: "The healer's lines do not need it" (compare "A conditional line comes from running the solver again")
- **Kind:** missing connection
- **What broke:** The page seems to describe two mechanisms: direct rules from the trait table, and the constraint-propagation solver. The parent described the engine only as constraint propagation. The page says "most" lines come from the solver but the followed case doesn't use it, while conditional lines (including, apparently, the healer's second line) do. So "shows the whole path" overclaims, and I can't tell which stage produced which healer line. I'm not assuming the two are one mechanism.
- **Repair:** Say plainly that there are two stages (trait-rule inferences and the solver), show which healer line comes from each, and drop "the whole path" or adjust it.
- **Severity:** worth fixing

**3.**
- **Where:** How strongly…: "Every line the engine prints carries one of three grades"
- **Kind:** unit or term changes meaning
- **What broke:** The page's own example of the Alternatives grade is conditional on a claim ("If that is true, either…"), and the text calls it "the alternatives under a named claim." So grades can combine, which contradicts "one of three." The same section's two-reason sentence leaves "the reporter" ambiguous (see section 2).
- **Repair:** Present Alternatives as something that can sit under a Certain or Conditional premise, or pick an Alternatives example with no condition. Name the player meant by "the reporter."
- **Severity:** worth fixing

**4.**
- **Where:** How strongly…: "in ten replays of the healer's turn, every note recorded the Chanteuse's visit once the line was present, and none did without it"
- **Kind:** number before orientation
- **What broke:** This replay figure comes before "frozen turn" and "output mode" are defined, and it seems to clash with the later 2 of 10 "without." I only reconciled the two after finding, in a table caveat, that this was a different measure (the note, not the read) in a different output mode (enforced). The opening's cost ratios also come before any method. "Taken up almost every time" rests on one turn, which reads stronger than its support.
- **Repair:** Move the frozen-turn and output-mode definitions ahead of the first replay number, or label this figure in place as the enforced-mode replay, measuring notes. Soften "almost every time" to what one turn shows.
- **Severity:** worth fixing

**5.**
- **Where:** From visible facts…: "The engine works at eight levels in all"; Scope: "the Level 3 above"; row 1: "the Level 3 tells it"
- **Kind:** unit or term changes meaning
- **What broke:** "Level" means a category of engine output in one place and a portfolio page in another. "Level 3" is also unexplained portfolio jargon to this reader. The scope section's "one level… has never produced a line in 278 recorded turns" depends on levels that are never listed.
- **Repair:** Rename the engine's categories (for example, "eight kinds of line"). Refer to the linked page by its title, "The roleblocked healer." Either list the kinds briefly or name the unused one in plain terms.
- **Severity:** worth fixing

**6.**
- **Where:** Results table rows 2–3: "replies to such reports stayed at 17 of 55"; "Claims 44 against 36; denials 0 against 4"
- **Kind:** missing connection
- **What broke:** "Watch" and "a false rule" are never explained. "17 of 55" doesn't say what was counted: replies that were wrong? That relied on the false rule? In row 3 I can't tell what a "claim" is (a role claim? a visit story?), why claims are better than denials, or what the remaining samples did. I worked out the 40/55 split from 19 × 5 = 95 myself.
- **Repair:** In each row, state what counts as an error or a success and which direction is the desired one. Define "watch" where the Sentinel first appears.
- **Severity:** worth fixing

**7.**
- **Where:** Row 1: "it spoke in 7 against 3"; boundaries section: "whether to say any of this aloud, stays the player's call"
- **Kind:** missing connection
- **What broke:** The engine is said not to advise speaking, yet a higher speaking rate is reported as an effect of it. The page never says why speaking is the right outcome for this turn or how it relates to the read.
- **Repair:** Add one clause on why speaking was the desired action for this turn, or drop the speaking figure here and leave it to the linked healer page.
- **Severity:** worth fixing

**8.**
- **Where:** Narrowing the possible roles: "for each body whose role was hidden at death"
- **Kind:** unit or term changes meaning
- **What broke:** The seat's view listed "the dead with the roles revealed at death." Now some deaths hide roles, and the game-continuation rule depends on that. When roles are hidden is never explained.
- **Repair:** Say in the seat's-view paragraph that some deaths reveal the role and some don't, and when.
- **Severity:** worth fixing

**9.**
- **Where:** Consequences, not advice: "a summary of what each rival claimant had said moved one case's votes toward the named player"
- **Kind:** detail that does not change understanding
- **What broke:** "Rival claimant," "one case" and "the named player" have no antecedent, so I couldn't tell what steering happened. The point (an advice-like line was dropped) is clear without it.
- **Repair:** Either remove it or reduce it to a one-clause example with the steering stated plainly.
- **Severity:** worth fixing

**10.**
- **Where:** In the paragraph after the results table: "In each case the lines changed what the first speaker did."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** "First speaker" isn't defined. Row 1 is confounded with the record repair, and row 3 is called "exploratory," so "in each case… changed" overstates them.
- **Repair:** Define "first speaker" (the seat receiving the lines, as opposed to those replying) and qualify the claim to match each row's limits.
- **Severity:** worth fixing

**11.**
- **Where:** What the engine is responsible for: "about 2.8 times the time a turn, or… seats costing roughly twenty times as much a game"
- **Kind:** unit or term changes meaning
- **What broke:** The comparison switches from time per turn to cost per game, and "seats costing" leaves unclear whether $2.30 is per seat or per game.
- **Repair:** State both alternatives in matching units, or say plainly that one is a latency cost and the other a money cost, and give the unit for each figure.
- **Severity:** worth fixing

**12.**
- **Where:** Seat's view: "the trailseer's report"; boundaries section: "the Investigator"; evil side: "a wolf or lone killer"; traits: "does a check on it read Suspicious"
- **Kind:** term before introduction
- **What broke:** Several roles and mechanics appear once with no gloss. That trailseer = player_3 is left for me to infer from the printed line. The metamorphic illustration also switches cast and naming (Investigator, Alice and Bob) partway through a page that otherwise follows player_N.
- **Repair:** Gloss each role in a few words on first use, or use roles already introduced in the illustrations. Write "the trailseer (player_3)."
- **Severity:** taste

**13.**
- **Where:** Mechanics as constraints: "checked against the game engine's own behaviour rather than written by hand"
- **Kind:** other (ambiguity)
- **What broke:** I can't tell whether the trait table was generated from the engine or written by hand and then tested against it.
- **Repair:** Say which one it is.
- **Severity:** taste

## 4. Highest-impact improvements

1. Before the healer numbers, say what each arm received: the night record and engine lines in the "without," high-thinking and larger-model runs. Put the frozen-turn and output-mode definitions ahead of the first replay figure.
2. Separate the two production stages (trait-rule inferences and the solver), show which stage and grade each healer line comes from, and fix the "one of three grades" claim.
3. Define the outcome measures for the Sentinel and evil-cover rows, and why speaking counts. Remove the opaque dropped-line sentence, and rename the engine's "levels" so they don't collide with the page levels.
