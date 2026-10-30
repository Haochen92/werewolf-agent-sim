<!-- editorial review of writeup/evaluation/play_metrics/play_metrics.skill.md by claude (claude-opus-5-5), 2026-10-28T14:57Z -->

## 1. The argument as I understood it

The page asks how to tell which version of a set of game-playing agents plays better when there aren't enough games for win rate to settle it. Its answer has two parts. Code grades each vote and night action against the true roles and turns the grades into per-game scores. A separate check then tests whether each score goes with winning. The sections explain why wins are too noisy, how decisions are graded, and how the check works on the nine-player game. They then show what happened in a ten-player game: the lynch score still tracked town wins, but the healer's save rate stopped doing so. The page concludes that a grade can be right by the rules and still not be evidence of winning play. Only the scores that carried over should be used to compare versions. I could state this central answer, but I had to work out what the game was and several key links myself.

## 2. Findings

**1.**
- **Where:** Opening paragraphs, "the town's lynch score still went with town wins"
- **Kind:** term before introduction
- **What broke:** The intro uses "agents", "role deal", "town", "lynch score" and "healer" before saying what the game is. The page never says outright that LLM agents are playing a Werewolf/Mafia-style hidden-role game. I only pieced that together in the third section. Until then, the intro's key contrast (lynch score versus save rate) meant nothing to me.
- **Repair:** In the first paragraph, say in one sentence what the game is, who the agents are, and what "version" means.
- **Severity:** blocking

**2.**
- **Where:** Why the win alone is not enough, "only a difference of about 36 percentage points in win rate would reliably show" vs "a change of about 0.18 in that share would reliably show"
- **Kind:** number before orientation / unit or term changes meaning
- **What broke:** The whole case for grading decisions rests on this comparison, but the two numbers are on different scales. One is percentage points of win rate. The other is a share of votes, where 0.18 is 18 points. Without knowing how much the score usually varies, or how big a change you would expect, I can't tell whether 0.18 is better than 36 points. The next sentence ("Whether a given change … moves the score that far is a separate question") then leaves the advantage unproven.
- **Repair:** Put both figures on one scale, for example as a share of each measure's typical spread or of a realistic effect, and say plainly how much the score gains.
- **Severity:** blocking

**3.**
- **Where:** A good move that decides fewer games, "What differed was how long it survived: 3.25 protection nights in games the town won"
- **Kind:** missing connection
- **What broke:** The section says it shows "what changed", but it never links these numbers to the rate. I had to do the arithmetic myself. About 1.07/3.25 ≈ 0.33 in won games and 1.03/2.48 ≈ 0.42 in lost games, so the rate runs higher in losses. The cause is the denominator, which earlier was introduced specifically to *remove* survival effects. "What changed" also suggests a comparison with nine players, but only ten-player figures are given.
- **Repair:** Spell out how equal saves per game plus longer survival in wins push the per-protection rate toward zero or negative. Either give the nine-player figures or drop "what changed".
- **Severity:** blocking

**4.**
- **Where:** A good move that decides fewer games, "the nine-player games were played on an earlier set of models"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The intro and the section headings present the healer split as caused by the expansion ("When the game expanded … The healer's save rate no longer did"). Only the last sentence of a late section reveals that the models changed too. That undoes the framing I had carried through the page.
- **Repair:** State in the intro, and again before the comparison table, that the nine-to-ten comparison also crosses a change of models.
- **Severity:** worth fixing

**5.**
- **Where:** Does a good move go with winning?, "Memory can raise a score and the chance of winning together"
- **Kind:** term before introduction
- **What broke:** "Memory" first appears here with no explanation. Later, "the memory system … to credit the lessons agents had followed" assumes I know that agents carry lessons between games. I couldn't tell why memory on or off is a confound, or how it relates to the "versions" being compared.
- **Repair:** Before this point, define the memory system in one sentence (what it stores and that it is one of the things being compared). Then say why pooling games with memory on and off could create a false link.
- **Severity:** worth fixing

**6.**
- **Where:** Does a good move go with winning?, "are games with higher scores the games that side won?" (also intro)
- **Kind:** missing connection
- **What broke:** The page first argues that wins are too noisy to judge versions, then uses wins to validate the scores. A careful reader will ask why wins are good enough for one job but not the other. The answer is probably that the check pools 50 to 180 games across versions rather than comparing 30 against 30, but the page never says so.
- **Repair:** Add a sentence explaining why pooling many games makes win a usable yardstick for validating scores even though it is too noisy for comparing versions.
- **Severity:** worth fixing

**7.**
- **Where:** Does a good move go with winning?, "That changed with the expanded game. Ten seats are dealt from twelve roles"
- **Kind:** section order / more than one job in a paragraph
- **What broke:** This paragraph covers four things: the nine-player gate (48 scores tried, 11 kept), the ten-player game before its own section, the needs of the memory system, and a new rules-first grading table. That table conflicts with my reading of "Grading a decision by the rules", which already sounded rules-first. I couldn't tell which method produced the scores in the later tables.
- **Repair:** Move the change of method into "When the game expanded". Earlier, say which approach came first and that the per-turn table came later.
- **Severity:** worth fixing

**8.**
- **Where:** Why the win alone is not enough, "share of town votes cast against a threat" vs Does a good move…, "the share of eliminations that removed a threat"
- **Kind:** unit or term changes meaning
- **What broke:** The lynch score is defined per vote in one place and per elimination in another. I couldn't tell which one the 0.18 figure and the correlations refer to.
- **Repair:** Pick one definition and use it everywhere, or name them as two separate scores.
- **Severity:** worth fixing

**9.**
- **Where:** When the game expanded, "how many of the town's players with night abilities were killed at night"
- **Kind:** unit or term changes meaning
- **What broke:** The page's premise is to measure decisions rather than outcomes, but this score is an outcome. I could no longer tell what counts as a "score" among the 32.
- **Repair:** Say that the scores include some outcome counts as well as decision grades, or explain which decision this score grades.
- **Severity:** worth fixing

**10.**
- **Where:** When the game expanded, "in the first 28 ten-player games they read zero even when the event happened"
- **Kind:** missing connection
- **What broke:** I can't tell whether these 28 games are part of the 78 used in the check, or whether they were rescored. The closing advice to "record each night's full outcome from the first game" suggests some data couldn't be recovered. That makes me unsure about the healer result.
- **Repair:** Say whether the 28 games are in the 78 and, if so, whether their scores were recomputed correctly.
- **Severity:** worth fixing

**11.**
- **Where:** Does a good move go with winning?, "In these games, what mattered was not the find but turning it into a vote."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** A correlation of +0.40 is presented as what "mattered", which reads as a cause. Elsewhere the page insists these are associations.
- **Repair:** Reword it as an association, for example "what went with winning".
- **Severity:** worth fixing

**12.**
- **Where:** A good move that decides fewer games, "The records fit that reading" / "makes chance alone an unlikely explanation"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** "Harder guess" implies a comparison, but there are no nine-player protection counts to compare against. The test of the two correlations is reported without any number. With 50 games behind the +0.36, I expected that difference to be shaky.
- **Repair:** Give the nine-player baseline for unattacked protections and the result of the correlation comparison, or soften both claims.
- **Severity:** worth fixing

**13.**
- **Where:** What the scores can support, "with 32 scores examined, one or two could pass by chance"
- **Kind:** number before orientation
- **What broke:** The figure of 32 first appears in the closing caveat. I had to reconcile it myself with the earlier 48 candidates and 11 kept. The same chance-pass concern applies to the 48 nine-player scores but isn't raised there.
- **Repair:** State how many scores the ten-player check covered when introducing that check, and apply the same caveat to the nine-player gate.
- **Severity:** worth fixing

**14.**
- **Where:** When the game expanded, "and a lone killer that may be either of two roles"
- **Kind:** other (unclear which game is being described)
- **What broke:** The rules section had already described a lone killer, and its healer table includes a block by an evil player. Here the blocker and the lone-killer options are listed as new. I couldn't tell which version of the game the rules section was describing.
- **Repair:** Say that the rules section describes the ten-player game, or mark which roles are new in it.
- **Severity:** worth fixing

**15.**
- **Where:** Does a good move go with winning?, "and it held on the later 180"
- **Kind:** other
- **What broke:** The other results come with numbers; this one gives none. It also isn't clear whether the 180 games include the first 50.
- **Repair:** Give the correlation at 180 and say whether those games include the first 50.
- **Severity:** taste

**16.**
- **Where:** "**Level 3:**"; What the scores can support, "in the labels the live game reports"; "The record names three changes"
- **Kind:** term before introduction
- **What broke:** "Level 3", "the labels the live game reports" and "the record" are internal names that mean nothing to a cold reader.
- **Repair:** Replace each with a plain description, or drop the sentence about labels.
- **Severity:** taste

## 3. Highest-impact improvements

1. Open with one sentence on what the game and agents are (and, briefly, what memory is), so the intro's contrast between the lynch score and the healer's save rate makes sense.
2. Put the figures behind "36 percentage points vs 0.18" on a common scale, and explain why wins are noisy for comparing versions but usable for validating scores.
3. In the healer section, spell out how longer survival in won games pulls down the per-protection rate. Move the model-change caveat up to where the split is first presented.
