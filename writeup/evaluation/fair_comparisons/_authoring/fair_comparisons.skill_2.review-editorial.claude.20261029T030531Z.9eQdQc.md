<!-- editorial review of writeup/evaluation/fair_comparisons/fair_comparisons.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:05Z -->

## 1. The argument as I understood it

The page asks what makes a comparison between two versions of the agent system trustworthy. Its answer is that two things can make a difference misleading, and each needs its own remedy. Differences between the two sides are removed by matching deals, recording a set-up fingerprint, having code check it, and running both sides in the same time window. Randomness within each side cannot be matched away, so it needs a measured noise floor and a test planned before the games are played. The June baseline that shifted shows why the same-window rule exists. The sections on recording and checking the set-up show how the matching is enforced, and the noise and planning sections deal with randomness. The page ends by saying which controls code enforces and which still depend on a person remembering a step.

## 2. Findings

**1.**
- **Where:** "A baseline that moved with nothing changed": "looked too large a drop to be chance" … "chance at this size was recorded as the alternative" … "(p = 0.18)"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The page first says the drop was too large to be chance, then in the next sentence lists chance as the alternative explanation. Later it gives p = 0.18, which seems to say chance is plausible. That p-value comes from a different comparison: the 20 replayed deals (12 wins, then 7), not the 10 new games (1 win). I could not tell whether the original 1-in-10 result still counts as evidence, or why the paired analysis replaces the analysis that treated every game as independent.
- **Repair:** Explain. State in one sentence why treating games as independent was the weaker analysis. Say plainly that the paired test covers the 20 replayed deals, not the 10 new ones. Then say which conclusion holds.
- **Severity:** blocking

**2.**
- **Where:** "Reading a difference against noise": "What made the June comparison fair was the shared time window, not the shared deals."
- **Kind:** unit or term changes meaning
- **What broke:** Until this point, "June" has meant the comparison that failed. Calling it "fair" here reads as a contradiction. I guessed it means the re-run memory comparison that came afterwards, but the page doesn't say so.
- **Repair:** Explain. Name the comparison, for example "the June memory comparison, once both sides were re-run together".
- **Severity:** worth fixing

**3.**
- **Where:** "Recording the set-up, and enforcing it": "**Exhibit (content):** FC-record. Optionally render as an annotated record excerpt…" and the caption "One memory-experiment game record, trimmed…"
- **Kind:** other
- **What broke:** A production note to whoever builds the page appears in the reader-facing copy. The caption also describes a game record, but the table above it lists record fields and what each is used for. I went looking for a record that isn't there.
- **Repair:** Remove the exhibit note. Either change the caption to describe the table as it is, or replace the table with the annotated record the note describes.
- **Severity:** worth fixing

**4.**
- **Where:** "Reading a difference against noise": "This was not re-measured on the ten-player game."
- **Kind:** term before introduction
- **What broke:** Up to here, the only game mentioned is "the original nine-player game". The ten-player version first appears in a passing caveat and is only explained in the final section ("deals ten seats from a cast of twelve roles"). I couldn't tell which game the current results and rules apply to.
- **Repair:** Explain. Introduce the ten-player game where the nine-player game is first named, or at its first mention here, and say how its deals differ.
- **Severity:** worth fixing

**5.**
- **Where:** "Checking the experiment that actually ran": "Replays of the factual-error test set now record…". Also "Reading a difference against noise": "moved the totals by one or two of 267 responses"
- **Kind:** term before introduction / number before orientation
- **What broke:** The factual-error test set is never explained. In the noise section I don't know what "the totals" count, for example responses judged to contain a factual error, so "one or two of 267" gives me no sense of how large the judge's variation is.
- **Repair:** Explain. Define the test set in one clause at its first use, and say what the total counts before giving the number.
- **Severity:** worth fixing

**6.**
- **Where:** "Reading a difference against noise": "went to the right player in 8 of 10 samples on one run and 1 of 10 on the next"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** One vote turn is the only support for "far larger" generation variation. The two runs were also separate, so a gap from 8 to 1 out of 10 could reflect the between-run drift the previous section warned about, not just sampling. The noise floor is used as a threshold but never given as a number.
- **Repair:** Explain. Either give the floor as a rate across several cases, or say this example is illustrative and whether the two runs were in the same session.
- **Severity:** worth fixing

**7.**
- **Where:** "What has to match": "When one judge's rubric split a label in two, the rate of another label moved from 74% to 63%"
- **Kind:** missing connection
- **What broke:** I don't know what the labels are, which judge this was, or why splitting one label would change the rate of a different label. "The discussion redesign" is also undefined. The point, that changing the rubric changes the scores, gets through, but the mechanism doesn't.
- **Repair:** Explain the mechanism in one clause (for example, messages moved between labels), or reduce it to "a rubric change alone moved one label's rate by 11 points".
- **Severity:** worth fixing

**8.**
- **Where:** set-up table: "read back after each round of games, and a mismatch stops the run"
- **Kind:** section order / term before introduction
- **What broke:** The table describes the memory-setting guard before the next section tells the fault that motivated it. "Round of games" is never defined.
- **Repair:** Relocate. Remove that row from the table, or point it forward to the next section. Define a round once.
- **Severity:** taste

**9.**
- **Where:** "What has to match": "Measurement differences are the easiest to miss." … "The third row is the least obvious"
- **Kind:** other
- **What broke:** Two consecutive superlatives point at different rows, so I wasn't sure which risk the page considers most important.
- **Repair:** Keep one of the two claims, or explain how "easiest to miss" differs from "least obvious".
- **Severity:** taste

**10.**
- **Where:** opening, fourth paragraph: "One baseline showed why both matter. It shifted on unchanged prompts and code"
- **Kind:** repeats parent context
- **What broke:** This is the third telling of the baseline: once in the parent, once here, and in full in its own section. It also claims to show "why both matter", but it mainly illustrates the first problem.
- **Repair:** Remove, or cut to a one-line forward pointer to the baseline section.
- **Severity:** taste

## 3. Highest-impact improvements

1. In the baseline section, reconcile the "too large to be chance" reading of 1/10 against 20/30 with the paired p = 0.18 result on the 20 replayed deals, so the reader knows which analysis holds and why.
2. Introduce the ten-player game and the factual-error test set where they first appear, and name which "June comparison" is called fair.
3. Remove the leaked exhibit note and make the caption match the table. Support the generation-noise claim with more than one vote turn, or label that example as illustrative.
