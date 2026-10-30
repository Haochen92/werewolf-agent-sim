<!-- editorial review of writeup/evaluation/llm_judges/llm_judges.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:05Z -->

## 1. The argument as I understood it

The page asks when an LLM judge's output can be trusted, and how this project designed and checked its judges. Its answer is that a judge holds up when three things are true: it asks a narrow question, it is given the facts it needs, and its answers are checked against something it never sees, ideally a person's labels. Broad 1–5 rubrics worked only as a "smoke alarm". They could not rank close versions. The page first sets out when to use a model judge, then shows a broad rubric failing to rank versions and narrow factual-error judges working. It then lists rubric rules, describes how to check a judge against a person, and covers live classifiers whose labels change the game. It ends with a status table: only the earlier game's factual-error judges have a person's check, and human labelling for the current game is prepared but not done.

## 2. Findings

**1.**
- **Where:** "Narrow questions with the facts handed over": "I checked its flagged public messages… On 25 flagged private notes, about four in five…"
- **Kind:** unit or term changes meaning
- **What broke:** The sentence says public messages were checked, but the numbers given are for private notes, and no result for public messages appears. "Its" could mean the cheap first-pass model or the whole two-stage screen. "2 or 3 of 15" reads as if the count itself is uncertain. The final table says this is the only judge with a person's check, so this is the one human-anchored result on the page, and I can't tell what was measured.
- **Repair:** Explain. Say which stage was checked, give the result for each statement type that was checked (or say public messages were checked without a tally), and say why the count is "2 or 3".
- **Severity:** blocking

**2.**
- **Where:** "Narrow questions…" rules list: "Grade what the output was required to do"; also "the memory rubrics fell short on definition, not on their number"
- **Kind:** missing connection / claim reads stronger than its support on the page
- **What broke:** The main failure shown earlier was a judge grading a required section and confirming only that it existed. The first rule then says to grade what the output was required to do. Read plainly, that recreates the failure. The second claim, that the rubrics fell short on definition, doesn't fit either. The quoted village-dynamics criterion has a written three-part definition and a stated 5-point anchor. The page's own diagnosis was presence-checking, not a missing definition.
- **Repair:** Explain. Link each rule to the case it comes from. For example, the first rule seems to be about keeping the rubric in step with the generating prompt (the dropped section), not about what to grade. Restate the memory-rubric diagnosis so it matches the evidence shown.
- **Severity:** worth fixing

**3.**
- **Where:** "What is established and what remains open": "Only the factual-error judges have a person's check"
- **Kind:** term before introduction / other (inconsistency)
- **What broke:** The table's expectation-judge row says "every verdict read by hand", which is also a person's check. That only fits the opening sentence if the expectation judge counts as one of the "factual-error judges", and the page never says so. "Speakers' accusation tags" appear for the first time in the table, so I don't know what they are or why "who must reply" matters. Their "Game" entry ("Checked on the earlier game") is also unlike the other rows.
- **Repair:** Explain. Make the opening sentence and the expectation-judge row agree. Either add a sentence on accusation tags in the body or drop the row.
- **Severity:** worth fixing

**4.**
- **Where:** "Checking a judge against a person": "The check draws 30 to 100 items…", and later "has not yet been run on real labels"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The paragraph is in the present tense and gives a precise procedure and pass bar, so I read it as how the judges were validated. Only the last sentence says it has never been run. The parent warned that the results are provisional, but here the sequence still misleads.
- **Repair:** Explain. Say first that this is the designed procedure, not yet applied, and then describe it.
- **Severity:** worth fixing

**5.**
- **Where:** "High scores that could not rank versions": "In the earlier nine-player game…"
- **Kind:** term before introduction
- **What broke:** An earlier nine-player game and a current ten-player game come up without introduction. The page later depends on that difference: which judges were checked on which game, and why the earlier checks don't carry over. Neither the parent nor the page says the game changed or whether results from the earlier game transfer.
- **Repair:** Explain. Add one sentence early on naming the two game versions and saying that checks on the earlier game don't validate the current game's judges.
- **Severity:** worth fixing

**6.**
- **Where:** "Narrow questions…": "For a recorded failure kept as a test case, a person writes an expectation instead…"
- **Kind:** term before introduction
- **What broke:** Midway through the factual-error section, the subject quietly moves to a second judge: replay test cases checked against written expectations. That judge is only named ("the expectation judge") two sections later. The example ("a night watch that only saw a visit to back a player's role claim") uses game mechanics the page never explains, so it doesn't help me understand.
- **Repair:** Explain. Name the expectation judge where it first appears and link it to the parent's frozen-turn replays. Replace the example with one that needs no game rules, or explain the mechanic in a clause.
- **Severity:** worth fixing

**7.**
- **Where:** "High scores…": "moved one pair's score by a full point, while prompt versions differed by a tenth or two"
- **Kind:** unit or term changes meaning / one example standing for a general rate
- **What broke:** The first number is one pair's swing. The second compares versions, apparently as averages over 18 pairs. A single pair moving by a point doesn't by itself show that differences in the averages are noise. Averaging is meant to shrink exactly that variation.
- **Repair:** Explain. Compare like with like: say how far a version's average moved between reruns of the same prompt.
- **Severity:** worth fixing

**8.**
- **Where:** "When a judge's label changes the game": "Yet before a fix, blind readers judged 6 of the 7 lines it held worth hearing."
- **Kind:** missing connection
- **What broke:** The opening filter is introduced, shown to have been badly wrong, then "fixed". The page doesn't say what the fix changed, so I can't tell whether the live filter is likely fine or still suppressing useful lines. The paragraph's point (measure, don't trust failing open) lands, but this classifier's current status doesn't.
- **Repair:** Explain. Say in one clause what the fix changed and that its current error rate is unknown.
- **Severity:** worth fixing

**9.**
- **Where:** "When a model is the right reader": "The memory-quality judges described next lacked that check."
- **Kind:** unit or term changes meaning
- **What broke:** The next section opens on a day-summary judge, not a "memory" judge. Memory notes come up as a separate judge several paragraphs later. I had to work out that "memory-quality" covers both.
- **Repair:** Explain. Name both judges here, or use the same term in both places.
- **Severity:** worth fixing

**10.**
- **Where:** "High scores…" table, third row: "A faster model at medium thinking, which a reading showed avoided the two worst failures of its lowest setting"
- **Kind:** detail that does not change understanding / unit or term changes meaning
- **What broke:** The column is headed "Completeness score", but this row gives a runtime. "Medium thinking", "lowest setting" and "two worst failures" are never explained. The table's point is that decisions rested on something other than scores, and the first two rows already show that.
- **Repair:** Remove the row, or cut it to "chosen for speed after a reading, not for score".
- **Severity:** taste

**11.**
- **Where:** "Checking a judge against a person": "on the nine-player factual-error test set, 1 or 2 of 267 samples"
- **Kind:** number before orientation
- **What broke:** I don't know what a "sample" is (statement? reply?), what "totals" counts, or whether "1 or 2" is a range across reruns.
- **Repair:** Explain. Name the unit and say "changed verdict on 1–2 of 267 statements across reruns", or whatever is meant.
- **Severity:** worth fixing

**12.**
- **Where:** "Narrow questions…": "one that regenerated and judged in a single pass could not separate a better prompt from sampling"
- **Kind:** missing connection
- **What broke:** It's unclear whether a pairwise judge was actually tried or this is general advice. "One that…" suggests a real case the page doesn't describe.
- **Repair:** Explain in a clause whether this happened, or remove it.
- **Severity:** taste

## 3. Highest-impact improvements

1. Make the factual-error human check clear: which stage, which statement types, which counts. Then reconcile it with the final table's claim of "only the factual-error judges".
2. Add one early sentence separating the earlier nine-player game from the current ten-player game, and present the human calibration procedure as planned before describing it.
3. Link the rubric rules to the cases they come from, especially "grade what the output was required to do" against the village-dynamics failure, and cut the generating-model table row.
