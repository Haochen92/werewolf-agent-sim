<!-- editorial review of writeup/context_engineering/deduction_engine/deduction_engine.md by claude (opus), 2026-10-31T03:59Z -->

## 1. The argument as I understood it

The page answers this question: when a cheap agent has every premise in front of it but doesn't draw the conclusion, how do you supply that step without giving away hidden information and without making the agent's decisions for it? The answer is a deduction engine. It works only from what the seat can see. It derives consequences through direct rules and a role-narrowing solver, and it prints them into the prompt. Each line carries its certainty grade in its own wording, and the agent keeps every decision. The page follows the roleblocked healer from the seat's view to the two printed lines. It then explains the grading and the two boundaries (what the engine may know, and that it states consequences rather than advice). Next come replay results for three failures. It ends with the scope and the open questions. The justification is cost: a slower thinking setting or larger models also solve the healer's turn, and the engine matches them at the live setting's speed and price.

## 2. Apply the explanation

**Question:** Suppose player_7 had *denied* the visit while player_3 still reported following player_7 to the healer. What would the healer's second line say, and in which grade?

**What the page supports:**
- Under its named claim, the line would probably still list both branches. The grading table defines Conditional as "in every such game in which the named claims are also true." Here the only named claim would be player_3's report.
- Alternatives are needed because "another visiting role could still have come to the healer that night."

**Where it breaks:**
- The page doesn't say how the engine handles claims that contradict each other.
- The only contradiction rule given covers facts: "when the facts contradict one another, the solver returns no candidate result." This line doesn't come from the solver, though. "A join such as the healer's second line sets the seat's own result against the claim directly."
- So I can't tell whether the line would cite only player_3, cite both claims, or not appear at all.

I got as far as I did only by noticing the two stages (direct rules and joins on one side, the solver on the other). The page names them but never says which rules apply in which stage. The probe works for a single claim but not for conflicting ones. That is acceptable for this page's scope, but it shows that the two-stage split is doing work the reader has to reconstruct.

## 3. Findings

**1.**
- **Where:** What changed in replayed decisions, healer row: "found it taken up every time and no sample speaking"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The paragraph above the table says "Speaking is the wanted outcome here," and the row reports speaking in 7 of 10 samples against 3. The limits column then says a cleaner replay of the same turn, with only this one line added, had *no* sample speaking. Two things differ between the runs: the output mode and the extra lines. I can't tell which one produced the speaking gain, or whether the engine helps the healer speak at all. The "earlier replay" in the grading section ("every note recorded the Chanteuse's visit once the line was present") looks like the same run. It's told there as uptake and here as silence, and I had to guess that they match.
- **Repair:** Report this replay once, in the results section. State what differs between the two runs and what the speaking difference can and cannot be attributed to. Either qualify the speaking claim or point to *The roleblocked healer* for the explanation.
- **Severity:** blocking

**2.**
- **Where:** What changed, Sentinel row: "those stating a false rule about watching fell from 6 to 2, the gain on the Sentinel's turns"
- **Kind:** unit or term changes meaning
- **What broke:**
  - The row is labelled as a Sentinel *denying a visit its own watch had made*, but it measures "stating a false rule about watching" across Sentinel *and* Trailseer reports.
  - "The gain on the Sentinel's turns" could mean the whole improvement came from Sentinel turns, or it could be a separate figure.
  - In the replies, it's unclear what "17 did so" refers to.
  - "A fix that let one follow reach the engine" uses "follow" without explaining it, so I can't judge the confound it warns about.
- **Repair:** Use one failure definition across the label and the counts. Say which roles the 40 samples cover. Either explain the bundled fix in one clause or describe it only as "an unrelated input fix."
- **Severity:** blocking (for this row)

**3.**
- **Where:** Narrowing the possible roles: "The healer's lines do not pass through it, so an illustration (not a recorded game)"
- **Kind:** missing connection
- **What broke:**
  - The parent presents constraint propagation as how the engine works. Here the solver is called the engine's centre and gets the most explanation (a table, four rule kinds, a termination argument).
  - Yet the case the page follows doesn't use it, and none of the three replay rows says whether its lines came from the solver or from direct rules.
  - So I can't tell whether any evidence on the page bears on the solver.
- **Repair:** In each replay row, say which stage produced the lines. If no result involves the solver, say so under Scope, next to "never fired in 278 recorded turns." Consider cutting the list of four rule kinds and the termination detail to one sentence.
- **Severity:** worth fixing

**4.**
- **Where:** What the engine is responsible for: "a game's ten seats at about $2.30 against $0.12"
- **Kind:** number before orientation
- **What broke:**
  - The unit is unclear: per turn round, per day, or per game?
  - The same comparison comes back near the end ("17.4 seconds against 6.3… two larger models reached 9 and 10 of 10"), with accuracy figures added that the opening only asserts.
  - The opening uses the comparison as the *reason* for the choice; the results section uses it as a *bound* on where the help is worth having. I had to reread both to connect the 2.8× with the 17.4/6.3.
- **Repair:**
  - In the opening, state the trade-off qualitatively and point forward.
  - Put all the numbers once, in the results section, with the cost unit stated.
- **Severity:** worth fixing

**5.**
- **Where:** How strongly can the conclusion be stated?: "There are three, and a list of alternatives can sit under a named claim"
- **Kind:** unit or term changes meaning
- **What broke:**
  - The parent and the table present three exclusive grades, but the main example combines two of them.
  - Then "A conclusion that holds on only some branches is not printed at all" seems to contradict the Alternatives grade, which lists branches.
  - I resolved this myself: a disjunction holds on every branch. The page doesn't say so.
- **Repair:** Present two separate dimensions: certain versus conditional on a named claim, and a single conclusion versus a complete list of alternatives. Say that a complete list is itself true in every legal game.
- **Severity:** worth fixing

**6.**
- **Where:** How strongly can the conclusion be stated?: "The grade is in the wording rather than a heading because a printed line is read as the seat's own result"
- **Kind:** more than one job in a paragraph
- **What broke:**
  - The paragraph mixes three jobs: a design rationale, an experiment report (with "replay" defined here for the first time), and a risk argument.
  - The link between the parts is implied. If lines are adopted verbatim, the grade has to travel inside the sentence. I had to reconstruct that.
  - "Taken up" is never defined.
- **Repair:**
  - State the rationale directly: lines get copied into the agent's notes, so the grade must survive the copying.
  - Move the replay evidence to the results section (see finding 1), and define "replay" there or at first use.
- **Severity:** worth fixing

**7.**
- **Where:** What changed, cover row: "Of 82 samples, those claiming a role rose from 36 to 44"
- **Kind:** number before orientation
- **What broke:**
  - It isn't clear whether 82 is per arm or the total; "41 pressured turns, two samples each" suggests per arm.
  - "Labelled by different judges" doesn't say what a judge is (a model or a person) or what it labels. Without that, I can't weigh the caveat "the counts are exploratory."
- **Repair:** Write "82 samples in each arm." Add one clause on what the judges classify and why using different ones matters.
- **Severity:** worth fixing

**8.**
- **Where:** From visible facts to a conclusion, The seat's view: "the dead with the role each revealed at death, unless a wolf concealed it"
- **Kind:** term before introduction
- **What broke:**
  - Concealment, the "dealt cast," and the relationship between "ten seats," "the standard twelve roles," and the cast are used without explanation.
  - Concealment matters later ("bodies whose role was hidden," "game continuation").
  - The long parenthetical also buries the point of the paragraph: the engine sees what the prompt sees, never the hidden roles.
- **Repair:**
  - Lead with that point.
  - Define the cast as the set of roles dealt in this game, and concealment in one clause.
  - Move the list of inputs after the point.
- **Severity:** worth fixing

**9.**
- **Where:** Consequences, not advice: "a wolf, or a lone killer with no pack" / "The role card gives the advice"
- **Kind:** term before introduction
- **What broke:** "Lone killer" and "role card" appear without explanation. I assumed the role card is the parent's "role instructions," but the page doesn't say so.
- **Repair:** Gloss "role card" as the seat's role instructions. Drop "lone killer" unless the distinction matters.
- **Severity:** taste

## 4. Highest-impact improvements

1. Report the healer replays once, in the results section, and reconcile 7/10 speaking with "no sample speaking." Say what differs between the runs and what the speaking gain can be attributed to.
2. Rewrite the Sentinel and cover rows so the failure label, the counted outcome, and the sample unit match. Explain "follow" and "judges," or remove them.
3. Say which stage (direct rules or solver) produced the lines in each result. Shorten the solver's mechanics to match the evidence behind it, and put the cost/latency comparison in one place with its unit stated.
