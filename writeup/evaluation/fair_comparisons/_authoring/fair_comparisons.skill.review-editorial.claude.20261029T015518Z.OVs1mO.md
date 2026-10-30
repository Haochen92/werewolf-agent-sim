<!-- editorial review of writeup/evaluation/fair_comparisons/fair_comparisons.skill.md by claude (claude-opus-5-5), 2026-10-29T01:55Z -->

## 1. The argument as I understood it

The page asks what it takes for a difference between two versions of the agents to count as evidence for the change. Its answer is a two-part test. First, the two sides must differ in nothing except the change. Second, the gap must be bigger than what you get by running one unchanged version again. Each part has its own controls:

- **Nothing else differs:** matched deals, one judge scoring both sides in one run, a recorded fingerprint, code checks inside the learning loop, and a rule that both sides run in the same time window. The June baseline that shifted with nothing changed is the reason for that rule.
- **The gap beats noise:** measured noise floors, a lean on decision scores, and test designs simulated and written down before the games are paid for.

It ends by sorting the controls into those that code enforces (strong) and those that depend on a person remembering a step (weak), and lists next steps that follow from the weak ones. The central answer is clear.

## 2. Findings

**1.**
- **Where:** "A baseline that shifted with nothing changed": "reused the recorded results of 20 of those games, without replaying them, and added 10 newly played deals"
- **Kind:** missing connection
- **What broke:** The section uses three different groups of games: the earlier 30, a first new baseline (20 reused plus 10 new), and the final 30 (20 replayed plus 10 new). They share the words "baseline" and "30". I had to work out for myself that the 10 new deals are not among the earlier 30, and that the earlier 30 includes 10 deals that were never reused. I also had to work out that "12 the first time" is a subset of the earlier "20 of 30". Nothing says why only 20 of the 30 were reused. Until I had done that work, the table's two rows looked like they contradicted each other.
- **Repair:** Before the table, name each group of games once with its composition, and use those names in the table rows. Say why only 20 of the earlier games were reused.
- **Severity:** worth fixing (close to blocking for the table)

**2.**
- **Where:** "A baseline that shifted with nothing changed": "remain the strongest sign that something changed … chance remains possible"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The table says 3 in 1,000 for the 10-new-deals comparison. The section then says chance "remains possible" without saying what weakens the 3-in-1,000 figure. The only hint is "against a different set of deals", but that points to the deals being harder or easier, not to chance. As a reader I can't tell whether chance is still open because of the 18% paired result, because of how the 10 deals were picked, or because the test was run after the drop had been seen.
- **Repair:** Say in one sentence why the 3-in-1,000 figure does not settle the question.
- **Severity:** worth fixing

**3.**
- **Where:** "Reading a difference against noise": "The comparisons therefore lean on decision scores."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The paragraph gives detectable gaps for win rate and for the share of town votes, then says "therefore" decision scores. It never gives the detectable gap for the town's decision score. So I can't tell whether decision scores actually solve the problem. It is also unclear whether the vote share is itself one of the decision scores. The next section's simulation (only about 1 time in 9) suggests decision scores also struggle at these sizes, and that cuts against the "therefore".
- **Repair:** State the noise floor or detectable gap for the town's decision score, and say how it relates to the vote-share measure.
- **Severity:** worth fixing

**4.**
- **Where:** "Deciding the test before the games": "three versions on 20 deals became two on 30"
- **Kind:** missing connection
- **What broke:** The three versions are never named. The reason given ("the first-round store held no lessons yet") only makes sense if I guess that one version was the first-round store. That guess is mine, not the page's.
- **Repair:** Name the three versions where the plan change is described.
- **Severity:** worth fixing

**5.**
- **Where:** "Reading a difference against noise": "Pairing has not been re-measured on the ten-player game."
- **Kind:** term before introduction
- **What broke:** "The original nine-player game" hints that another game exists, but the ten-player game is never introduced. The last section then says its "lineups differ between deals". So I learn only at the very end that the role mix itself can vary, and I don't know which of the page's results apply to which game.
- **Repair:** Introduce the two game versions early, in one clause, including that ten-player lineups vary by deal.
- **Severity:** worth fixing

**6.**
- **Where:** Table caption: "a short list of public behaviours that hint at a hidden role was shown to every seat on the memory side, wolves included"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The table has just shown "town roles only" being checked and confirmed. The caption then says a second kind of memory went to wolves too. It is a new component that appears nowhere else on the page. A reader can't tell whether this weakens the town-only design or is harmless.
- **Repair:** Either drop this from the caption or say in a clause why it doesn't affect the comparison.
- **Severity:** worth fixing

**7.**
- **Where:** "A baseline that shifted with nothing changed": "The reanalysis did not gain precision by pairing (the noise section shows pairing bought little)"
- **Kind:** section order
- **What broke:** This leans on a finding presented a section later. It also comes right after a table whose paired row looks *less* conclusive than the unpaired one. That invites the misreading that pairing made things worse. The sentence spends its effort heading off a question the reader can't yet weigh.
- **Repair:** Either move the pairing-precision result ahead of the baseline section, or cut this sentence down to "it compared each deal with itself, as the design allowed".
- **Severity:** worth fixing

**8.**
- **Where:** "Reading a difference against noise": "the share of town votes cast against an evil player"
- **Kind:** unit or term changes meaning
- **What broke:** Everywhere else the opposing side is "wolves". "Evil player" could mean the same thing or a wider group.
- **Repair:** Use one term, or say that "evil" includes the wolves and anything else it covers.
- **Severity:** worth fixing

**9.**
- **Where:** "Reading a difference against noise": "8 of 10 samples on one run and 1 of 10 on the next"
- **Kind:** missing connection
- **What broke:** It doesn't say that nothing changed between the two runs. A swing this large, on a page that has just discussed drift in the hosted model, reads as possibly another drift case rather than a noise floor.
- **Repair:** Say what was held fixed between the two runs and how far apart they were.
- **Severity:** worth fixing

**10.**
- **Where:** "Checking that the run is the one declared", **Enforcing**: "produced a plausible but wrong number without raising any error"
- **Kind:** more than one job in a paragraph
- **What broke:** One paragraph introduces the memory experiments, defines learning loops, describes two checks, tells the June story and gives the scope limits. The phrase "a … wrong number" doesn't say what was being measured. Also, a second June incident (the baseline shift) comes later, so the two Junes are easy to blur.
- **Repair:** Split the definition of the memory experiments and learning loop from the checks, and name what the wrong number measured.
- **Severity:** taste

**11.**
- **Where:** Table caption: "the run that built the store for the final memory test"
- **Kind:** term before introduction
- **What broke:** "Final memory test" is defined only in the "Deciding the test" section.
- **Repair:** Gloss it in a few words at first use.
- **Severity:** taste

## 3. Highest-impact improvements

1. Name and lay out the three groups of baseline games before the table. Then say why the 3-in-1,000 result still leaves chance open.
2. Give the noise floor for the town's decision score, so that "therefore lean on decision scores" is backed by a number on the page.
3. Introduce the nine- and ten-player games early, and name the three versions in the plan change, so later references don't depend on guesswork.
