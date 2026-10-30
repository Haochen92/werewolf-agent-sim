<!-- editorial review of writeup/evaluation/play_metrics/play_metrics.skill.md by claude (claude-opus-5-5), 2026-10-29T01:55Z -->

## 1. The argument as I understood it

The page asks what a decision-level play score has to show before it can be trusted as a measure of play quality. Its answer is that the score must pass two tests. First, it must count good moves exactly from the game record. Second, it must go with winning. The second test does not carry over automatically when the game changes. "What decision scores buy" explains why decisions are scored at all: they are closer to the behaviour being changed, but they don't add samples. The next two sections define exact rule-based scores and the correlation check against winning, and give nine-player results. The ten-player check shows that the elimination score held up and the healer's save rate didn't. A later section looks at why, but it can't separate the game change from the model change. The page ends by saying which scores a ten-player comparison can rely on and how far the evidence goes.

## 2. Findings

**1.**
- **Where:** "A good move that decides fewer games": "The healer's ten-player records show how its rate lost the link." and later "It cannot say why the association changed"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The section gives three different accounts:
  - The heading says a save decides fewer games.
  - The first paragraph gives a mechanism: extra protection nights without extra saves lower the rate in games the town won.
  - The third paragraph gives a different reading: protecting is a harder guess with more information roles.

  It then says the comparison can't explain the change. I took the first paragraph as the explanation and then had it withdrawn. I also couldn't tell whether the extra-nights effect is new to ten players or would also have existed on nine.
- **Repair:** Say at the start of the section that the extra-nights effect describes how the ten-player correlation comes out near zero, not why it differs from nine players. Present the harder-guess idea as a separate, untested reading. Align the heading with whichever point the section actually makes.
- **Severity:** blocking

**2.**
- **Where:** "A good move that decides fewer games": "against both the 50-game estimate and the +0.40 the healer's score held over 180 nine-player games"
- **Kind:** number before orientation
- **What broke:** This is the first mention of a 180-game healer figure. The nine-player result shown for the healer is +0.36 over 50 games, in the table. The only +0.40 I had seen was the investigator's find-to-vote share over 180 games. I suspected a copy error.
- **Repair:** Give the healer's 180-game figure when the nine-player results are reported, and add it to the table's nine-player column. Then the late reference only points back to it.
- **Severity:** worth fixing

**3.**
- **Where:** "What decision scores buy": "A decision score is no shortcut, though: at 30 games a side it too shows only large changes"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The parent says decision scores were used because win rates "required more games than the project could afford." This section says they don't clearly need fewer games, and that the size of any saving hasn't been measured. Its stated benefit, "a measurement closer to the play", isn't linked to any practical gain. I couldn't tell what the scores buy if not fewer games.
- **Repair:** State the concrete payoff the author claims, such as less noise per game in principle or a diagnosis of which behaviour changed. Make clear that the saving in games is expected but not yet measured.
- **Severity:** worth fixing

**4.**
- **Where:** "What the scores can support": "The check separated the grade from the rate."
- **Kind:** term before introduction
- **What broke:** The closing section introduces three new things: a grading table for "every kind of turn," "the grade," and "the memory system's credit for the lessons agents follow." It then draws a conclusion that depends on them. Earlier sections mention only per-game scores. The point that a save is still graded good depends on machinery I've only just met.
- **Repair:** Introduce the turn-grading table and what it feeds in "Scoring decisions by the rules", or make the closing point using only the per-game scores.
- **Severity:** worth fixing

**5.**
- **Where:** "What decision scores buy": "a comparison of 30 games for each version would reliably show only a difference"
- **Kind:** unit or term changes meaning
- **What broke:** Here "version" means a version of the agents. Later, "the game version" means nine versus ten players, and the final section mentions "the next version of the game." Coming from a page about a game that expanded, I first read "each version" as each game variant.
- **Repair:** Say "agent version" or "configuration" for the thing being compared. Keep "game version" for nine versus ten players.
- **Severity:** worth fixing

**6.**
- **Where:** opening paragraph: "kept its link on both games"
- **Kind:** unit or term changes meaning
- **What broke:** "Game" means both the rule variant ("both games", "the expanded game") and a single played match ("50 games"). Since the page's evidence is counted in matches, "both games" briefly reads as two matches.
- **Repair:** Use "both versions of the game" or "nine- and ten-player games" for the variants, and keep "game" for single matches.
- **Severity:** worth fixing

**7.**
- **Where:** "A good move that decides fewer games": "Of 220 protections that went ahead, 79 saved someone"
- **Kind:** number before orientation
- **What broke:** The paragraph lists six counts before I know what they are meant to show. I couldn't judge whether 79 of 220, or 36 saved players dying later, is high or low. The next paragraph admits there are no nine-player counts to compare them with.
- **Repair:** Say before the counts that they describe how often a save mattered on ten players, with no baseline. Alternatively, reduce them to the one or two counts the argument uses.
- **Severity:** worth fixing

**8.**
- **Where:** "What the scores can support": "the scores that carried over did so by a wider margin than that"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** "Wider margin than that" has no stated standard. The page gives an interval only for the elimination score. Night losses and the lone-killer vote are named as reliable but come with no numbers. I couldn't check the claim that they beat the multiple-comparison concern.
- **Repair:** Name the margin, for example intervals that exclude zero, and give the figures for the other two scores in the earlier paragraph or the table.
- **Severity:** worth fixing

**9.**
- **Where:** "When the game expanded": "Each score was read over all games, with memory off, and within batch."
- **Kind:** term before introduction
- **What broke:** Earlier, "batch" meant any set of games. Here it's a specific grouping whose average is removed. I couldn't tell what defines a batch (one agent version? one run of games?), which affects what the within-batch reading controls for.
- **Repair:** Define a batch in one clause before the three readings.
- **Severity:** worth fixing

**10.**
- **Where:** "When the game expanded": "and a lone killer that may be either of two roles."
- **Kind:** missing connection
- **What broke:** "Scoring decisions by the rules" treats the lone killer as part of the general vote rule, and refers to "the evil sides" in the plural. This list of new roles suggests the lone killer only arrives with ten players. I couldn't tell whether the nine-player game had one, or what "either of two roles" means.
- **Repair:** Say whether the lone killer existed on nine players, and what is new about it on ten.
- **Severity:** worth fixing

**11.**
- **Where:** "When the game expanded" table: "−0.03 (75 games; interval −0.26 to +0.20)"
- **Kind:** missing connection
- **What broke:** The check is described as using 78 games, but the healer row uses 75. I could work out the reason from the earlier caption ("never protected anyone gets no score"), but the page doesn't make the link.
- **Repair:** Add a short note that three games had no healer protection and so no score.
- **Severity:** taste

**12.**
- **Where:** "When the game expanded": "The original scorers read night fields the new game never fills"
- **Kind:** detail that does not change understanding
- **What broke:** Implementation detail about which fields the scorers read sits between the reason for the check and its method. The only part I needed was why the check used 78 games.
- **Repair:** Cut this to a clause about which game records were usable.
- **Severity:** taste

**13.**
- **Where:** "What the scores can support": "Whether to mark any of them formally as validated for the ten-player game is a separate decision"
- **Kind:** term before introduction
- **What broke:** "Formally validated" suggests a status or process the page never mentions. It slightly weakens "the scores a comparison … can lean on most" without saying what would change.
- **Repair:** Say what formal validation would add or change, or drop the sentence.
- **Severity:** taste

**14.**
- **Where:** "What decision scores buy" (placement)
- **Kind:** section order
- **What broke:** The opening sets up two questions: exact counting and a link with winning. The next section answers a third question, about statistical power, before either is addressed.
- **Repair:** Flag the "why score decisions at all" question in the opening, or move this section before the two-question framing.
- **Severity:** taste

## 3. Highest-impact improvements

1. Rework the healer section so the extra-nights effect is clearly a description of the ten-player result, not an explanation of the drop, and match the heading to it.
2. Report the healer's 180-game nine-player figure where nine-player results first appear, so the late +0.40 doesn't look like the investigator's number.
3. Introduce the turn-grading table and its role in memory before the conclusion relies on it. Separately, state plainly what decision scores buy if not fewer games.
