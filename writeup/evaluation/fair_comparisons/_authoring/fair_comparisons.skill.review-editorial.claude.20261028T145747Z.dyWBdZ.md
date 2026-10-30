<!-- editorial review of writeup/evaluation/fair_comparisons/fair_comparisons.skill.md by claude (claude-opus-5-5), 2026-10-28T14:57Z -->

## 1. The argument as I understood it

The page asks how this project makes sure that a difference between two versions of an LLM-agent system comes from the change being tested. Its answer is that two conditions must hold. First, the two sides must differ in nothing else. The page covers this with matched deals, replayed turns, one judging pass for both sides, a recorded fingerprint, a memory guard, and running both sides in the same time window. Second, the gap must be larger than run-to-run noise. The page covers this with measured noise floors, a power simulation, and a test whose reading was fixed before the games were played. A June baseline that shifted with nothing changed is the case that produced the same-window rule. A later reanalysis weakened the explanation for that shift but did not weaken the rule. The page ends by separating controls that code enforces from steps that still depend on a person.

## 2. Findings

**1.**
- **Where:** "Giving both sides the same start and the same judge": "Each game starts with a deal: the assignment of roles to seats."
- **Kind:** term before introduction
- **What broke:** The page never says what the project is. "Game", "roles", "seats", "vote", "town" and "wolves" all appear before the reader learns, in the baseline section, that this is a social-deduction game played by LLM agents with town roles against wolves and a serial killer. Until then I had to guess what a game, a turn or a vote is. "Evil player" (in "Reading a difference against noise") is never defined.
- **Repair:** Open the page with one or two sentences on the game: who plays, the two teams, how a game is won and what a vote is.
- **Severity:** blocking

**2.**
- **Where:** "Checking that the run is the one declared": "In the learning-loop runs of the memory experiments, a separate check enforces a rule"
- **Kind:** term before introduction
- **What broke:** The page never explains "memory", the "learning loop", a "round", or the "store" that the July run "built". Without them I cannot follow why giving memory to wolves invalidates the result. I also cannot see how the learning loop (rounds that build a store) relates to the final memory test (memory on vs. off on 30 deals).
- **Repair:** Before the guard is described, say in one sentence what agent memory is, what a learning-loop round does, and that the store it builds is what the final test switches on or off.
- **Severity:** blocking

**3.**
- **Where:** "A baseline that shifted with nothing changed": "comparing each deal's two results with each other rather than treating the games as unrelated."
- **Kind:** missing connection
- **What broke:** The table suggests that pairing caused the drop from "3 in 1,000" to "18 in 100". But the two rows compare different games: the first uses the 10 new deals, the second leaves them out. The page sends the explanation to a link. A later section then says "Pairing whole games by deal turned out to buy little precision", which seems to contradict what I took from the table. I could not tell which reading to believe, or what happened to the striking 1-in-10 result.
- **Repair:** Say on the page why the two readings differ: different games are compared, and the paired reading excludes the 10 new deals. Then state how that fits with pairing buying little precision.
- **Severity:** blocking

**4.**
- **Where:** "A baseline that shifted with nothing changed": "The experiment reused 20 of those deals, whose winners were on record, and played 10 new deals."
- **Kind:** unit or term changes meaning
- **What broke:** "Reused 20 of those deals" reads as replaying those deals. Only later ("The 20 reused deals were played again") did I work out that the old *results* had been reused without replaying anything. Elsewhere on the page, "deal" means a starting position you play, so here the word quietly means a recorded outcome.
- **Repair:** Say plainly that the first baseline combined 20 recorded results from the earlier run with 10 newly played games.
- **Severity:** worth fixing

**5.**
- **Where:** "Reading a difference against noise": "a decision score spread by 0.25 within a deal, against 0.21–0.26 across deals"
- **Kind:** number before orientation
- **What broke:** "Decision score" has not been defined at this point. Its scale (−1 to +1) only arrives in the next section, and what it measures is sent to a link. "Spread" could mean standard deviation, range or something else. So the comparison that supports "pairing bought little" cannot be judged.
- **Repair:** Define the decision score (what it scores and its scale) at first use, and name the spread statistic.
- **Severity:** worth fixing

**6.**
- **Where:** "Giving both sides the same start and the same judge": "Judging the sides at different times is not safe even with the same judge."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The example that follows is a rubric change. The judge changed, so the example shows that a changed judge shifts labels, not that the *same* judge drifts over time. It is also unclear what "74%" is a share of.
- **Repair:** Either give an example of the same judge drifting, or narrow the claim to "the judge or its rubric can change between runs". Say which label's share of which messages moved.
- **Severity:** worth fixing

**7.**
- **Where:** "Checking that the run is the one declared": "Three safeguards answer that" … "The memory runs have a second guard."
- **Kind:** unit or term changes meaning
- **What broke:** The page promises three safeguards (record, enforce, check). It then gives a fingerprint, a stop-on-change check, a "second guard", and later "the third safeguard", which turns out to be an October probe plus a partial logging fix. I could not match the named items to the three jobs. "Second guard" seems to count differently from "three safeguards".
- **Repair:** Name each safeguard once against its job. Say plainly that the third job (checking a setting works) is mostly not yet automated.
- **Severity:** worth fixing

**8.**
- **Where:** "Reading a difference against noise": "Effects near 0.10 would need about 100 games a side."
- **Kind:** unit or term changes meaning
- **What broke:** The previous sentence gives two units: win-rate points and vote share. "0.10" could be either, or a decision score. The page also doesn't say what "can be detected" means (what power, which test). So "36 points" cannot be weighed.
- **Repair:** Attach a unit to 0.10 and state the detection criterion once.
- **Severity:** worth fixing

**9.**
- **Where:** "Deciding the test before the games": "At the size of the previous paid run, 24 games over six rounds, the test noticed the +0.15 improvement"
- **Kind:** number before orientation
- **What broke:** The only run described in detail so far is the July run, with four rounds of ten games a side. "Previous paid run, 24 games over six rounds" seems to be a different run that has not been introduced. I also cannot tell whether +0.15 is a change per round or over the whole run.
- **Repair:** Identify which run is meant and how it relates to the July run. Give +0.15 a unit, for example "on the decision score over the whole run".
- **Severity:** worth fixing

**10.**
- **Where:** "Reading a difference against noise": "moved the totals by 1 or 2 of 267 on the factual-error test set"
- **Kind:** term before introduction
- **What broke:** "Factual-error test set", "267" (what is counted), "the right player", "the test set" in the third bullet (the same set?) and "quality check" all appear without introduction. Each bullet also switches unit: judgements, samples, percentage points.
- **Repair:** In one clause per bullet, say what is being scored and what the count is a count of.
- **Severity:** worth fixing

**11.**
- **Where:** "A baseline that shifted with nothing changed": "a memory experiment in the original nine-player game"
- **Kind:** missing connection
- **What broke:** "Original" implies a later variant. The ten-player game only appears near the end, and its defining feature (ten seats from twelve roles) is in the last paragraph. I could not tell which game the July run and the final memory test used. That matters, because pairing is said to be "not re-measured on the ten-player game".
- **Repair:** Introduce both game variants with the game description (Finding 1), and say which game each experiment used.
- **Severity:** worth fixing

**12.**
- **Where:** "Keeping both sides in one time window": "the same model served through two services gave different scores even at temperature 0."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The page doesn't say whose observation this is (this project's or someone else's), which model, or what scores. "One provider states" is likewise unattributed. These read as general facts with no support on the page.
- **Repair:** Say whether this was measured in this project and on what.
- **Severity:** worth fixing

**13.**
- **Where:** "Deciding the test before the games": "a game whose decisions had fallen back to defaults was excluded."
- **Kind:** term before introduction
- **What broke:** "Fallen back to defaults" is not explained (a failed model call?). The page also doesn't say whether this exclusion rule was fixed in advance with the other choices. That matters, because a rule set afterwards would undercut the section's point.
- **Repair:** Say in a clause what a default decision is, and that the exclusion rule was set before the run, if it was.
- **Severity:** taste

## 3. Highest-impact improvements

1. Open with a short description of the game (teams, roles, votes, the nine- and ten-player variants) and of the memory learning loop, so later sections don't depend on terms that are never defined.
2. Explain on the page why the independent and paired readings of the June baseline differ, and reconcile that with "pairing buys little precision".
3. Define the decision score at first use, and give every noise and power figure a stated unit and denominator.
