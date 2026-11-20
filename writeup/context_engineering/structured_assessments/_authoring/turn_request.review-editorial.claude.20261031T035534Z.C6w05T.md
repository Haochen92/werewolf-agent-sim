<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/edrev/context_engineering/structured_assessments/turn_request.md by claude (opus), 2026-10-31T03:55Z -->

## 1. The argument as I understood it

The page asks how to get an agent to write out its assessment before it acts, and whether doing so improves its decisions. Its central answer has two parts. First, the assessment appears reliably, and in the right order, only when the answer's structure requires it (required fields, fields shown only when they apply, a schema order that matches the prompt), not when the prompt merely asks. Second, a fuller assessment changes what the agent writes but doesn't reliably improve the decision, so every change has to be tested on decisions.

The sections build like this:
- A method for testing changes (replaying a recorded turn).
- A worked example of what the written record reveals.
- Three fixes that got the fields filled.
- Two decisions that set the field order.
- A rejected "compare the players" sentence that changed the assessment but not the decision for the better.
- Prompt cues that steered choices by accident.
- Thinking effort, presented as a stronger lever than any wording change.

The last two sections connect only loosely to the page's question.

## 2. Apply the explanation

**Question:** Suppose a new assessment, such as a verdict on each role claim, keeps getting skipped. Going by this page, what change would get it written: a clearer instruction or a change to the answer's structure?

**Answer from the page:** The section frames it as structure: "each needed a change to the answer's shape rather than another sentence of instruction." So the fix would be to make it "a **required field** … one verdict per lesson," show it "only when lessons are shown," and put it in the same order in the schema and the prompt. The ordering result supports this: "Adding a sentence asking it to keep the schema's order gave 13 of 23. Reordering the schema … gave 24 of 24."

**Where the page breaks:** In the case it explains most fully, the page gives the credit to an instruction. The text says "the instruction to write them was also moved … into the prompt body, and that move is what the record credits with taking the share … from 0.27 to 0.97." So the required field and the moved instruction were changed together, and the improvement is credited to moving the instruction. I can't tell whether making the field required did anything on its own, which means the page can't fully settle my question. I had to reread the section to notice that its framing and its evidence point different ways.

## 3. Findings

**1.**
- **Where:** Getting the requested assessment into the answer. "that move is what the record credits with taking the share of lessons that received a verdict from 0.27 to 0.97"
- **Kind:** Caveat reverses an earlier claim.
- **What broke:** The section opens by saying structure works and instructions don't. Its first example then credits the main gain to moving an instruction. I can't tell what the required field contributed.
- **Repair:** Say whether the required field and the instruction move were tested separately. If they weren't, describe the gain as the result of both changes together, and soften the section's opening claim to match.
- **Severity:** Blocking.

**2.**
- **Where:** Testing whether a fuller assessment helps. "Where the evidence was strong, it helped … votes for player_1 rose from 13 to 17 of 30."
- **Kind:** Claim reads stronger than its support on the page.
- **What broke:** The method paragraph warns that small wording changes "moved single cases by as much as five of ten samples either way." A gain of 4 in 30 across three cases looks like it falls within that range, yet the page calls it "helped." Later, the closing section says these day-4 votes "fell across three versions of the code", which seems to weaken the result further. That caveat comes two sections after the result it qualifies.
- **Repair:** Put the code-version caveat next to the day-4 result, and say how the 13→17 change compares with the noise range the page itself stated.
- **Severity:** Blocking.

**3.**
- **Where:** Testing whether a fuller assessment helps. "Eleven votes were frozen … the two day-6 ballots … and seven controls"
- **Kind:** Missing connection.
- **What broke:** The page lists eleven test cases but reports results for only four of them: the Vigilante's vote and the three day-4 controls. The Speculator's ballot, the two day-6 ballots, the day-3 controls and the Sentinel's own vote are never reported. I can't tell whether they changed or were simply left out.
- **Repair:** Report all eleven results briefly, or list only the cases that are discussed.
- **Severity:** Worth fixing.

**4.**
- **Where:** Getting the requested assessment into the answer. "With the schema sent as text, a turn shown no lessons still returned verdicts"
- **Kind:** Term before introduction.
- **What broke:** "Schema sent as text" is used here as if I already knew it. It's only defined in the next section ("the reply is checked in code rather than enforced by the provider"). Until then I couldn't tell why that mode would cause unwanted fields to be filled in.
- **Repair:** Define the two output modes (provider-enforced schema and schema sent as text) once, when the method is introduced.
- **Severity:** Worth fixing.

**5.**
- **Where:** Getting the requested assessment into the answer. "On 18 frozen turns from that game the line brought open-floor passes from 24 of 25 samples to 16 of 25"
- **Kind:** Unit or term changes meaning; more than one job in a paragraph.
- **What broke:** 18 turns produce 25 samples, which doesn't fit the "ten samples per turn" method described earlier. The next clause says "six of the nine seats that spoke", where nine seems to be 25 − 16 samples but is called seats. The paragraph has also moved from getting fields filled to changing whether seats speak at all.
- **Repair:** Name the unit for each number. Consider moving this paragraph to the prompt-cues section, or treating it as a separate point about adding lines only when they apply.
- **Severity:** Worth fixing.

**6.**
- **Where:** Putting assessment before action. "every mismatch put the reads first … Reordering the schema to match the prompt"
- **Kind:** Missing connection.
- **What broke:** The reads and the verdicts both come before the decision. So I couldn't see why their order relative to each other mattered, given that the section's subject is assessment before action. I had to work out the likely link myself: the July result suggests reads first leads a seat to override a lesson more often. The page doesn't make that connection.
- **Repair:** In one sentence, state why the reads should come before the verdicts, tying it to the July finding.
- **Severity:** Worth fixing.

**7.**
- **Where:** Putting assessment before action. "overrode a retrieved lesson's suggestion about three times as often … though a model judge rated the reads thinner"
- **Kind:** Missing connection.
- **What broke:** "Three times as often" doesn't say compared with what: reads placed after the note, or no reads at all. "Thinner" also has no stated comparison. "In July" has no year and doesn't affect the argument.
- **Repair:** Name the comparison condition for both measures. Drop the month.
- **Severity:** Worth fixing.

**8.**
- **Where:** Giving the model more thinking effort (table and the paragraph after it). "One earlier player model … it runs at the higher level now" / "Every seat turn still runs at the lower level"
- **Kind:** Unit or term changes meaning; missing connection.
- **What broke:**
  - If every seat runs today's model at the lower level, I can't tell what the earlier model still does that runs at the higher level.
  - The levels are never named.
  - The cost column uses a different unit in each row (multiplier, dollars per game, tokens, seconds).
  - The page says wording results "have to be read against" thinking effort, but never says which level the wording experiments used.
- **Repair:** Say which model plays now and what the earlier model is still used for. State the thinking level used for the wording experiments. Consider putting the cost unit in each row's heading or label.
- **Severity:** Worth fixing.

**9.**
- **Where:** What the written assessment needs to reveal; Testing whether a fuller assessment helps. "the trailseer … the Chanteuse, a wolf" / "the Vigilante and the real Sentinel … the Speculator … the Necromancer"
- **Kind:** Term before introduction.
- **What broke:** The parent excerpt never describes the game. Some roles are glossed in passing (trailseer, Chanteuse, Speculator, Necromancer). Others are not: healer, Vigilante, Sentinel ("watch"), Investigator ("check") and "lone killer." "The real Sentinel" implies a false claim the page never describes. "I was the Necromancer" is the first sign that a human plays, which I didn't expect.
- **Repair:** Before the healer example, add one line saying this is a social deduction game (town against hidden wolves and solo roles, day votes, night actions), and that the author sometimes takes a seat. Give each role a short gloss only where its ability matters to the argument.
- **Severity:** Worth fixing.

**10.**
- **Where:** When the prompt supplies the answer (whole section).
- **Kind:** Other (section belongs elsewhere).
- **What broke:** The page's question is about written assessments. This section is about cues in the prompt that biased choices: role-card tells, seat-number bias, and the example naming player_2. The lot-drawing fix doesn't involve the assessment at all. I couldn't see how it advances the argument, beyond the general point that a prompt shapes behaviour.
- **Repair:** Move it to a page about prompt design or bias, or open it with a sentence explaining why it belongs here (for example, that the answer example was part of the response format).
- **Severity:** Worth fixing.

**11.**
- **Where:** Testing whether a fuller assessment helps. "which is where the swing-of-five limit above comes from" / "left vote misquotes at 24 before and 24 after"
- **Kind:** Section order; number before orientation.
- **What broke:** The noise limit used to read every earlier result is explained only here, near the end. The misquote count is given as 24 with no total.
- **Repair:** Give the source of the noise limit in the method paragraph, and give the misquote count as a fraction of something.
- **Severity:** Worth fixing.

**12.**
- **Where:** What the written assessment needs to reveal. "a verdict on each item shown from memory, a lesson or an observation"
- **Kind:** Term before introduction.
- **What broke:** The parent excerpt only mentions lessons. The page doesn't say how an observation differs from a lesson, and the schema then gives them separate fields with different scales.
- **Repair:** Add one clause defining an observation and saying why it gets an applicability rating instead of follow/override.
- **Severity:** Taste.

**13.**
- **Where:** Putting assessment before action. "Keeping the order is compliance, not quality. The chapter page's figures already separate the two"
- **Kind:** Repeats parent context.
- **What broke:** This paragraph and the first sentence of the section repeat the parent's findings. The point that the current order hasn't been tested for quality is then stated again in the closing section.
- **Repair:** Keep only the reference to the parent's figures, and state the untested gap once.
- **Severity:** Taste.

## 4. Highest-impact improvements

1. Make the "structure, not instruction" claim match the evidence: either separate the effect of the required field from the instruction move, or soften the claim. As it stands, the page's main thesis is contradicted by its first example.
2. Put the caveats next to the results they qualify. The day-4 code versions, the source of the swing-of-five limit and the noise comparison should each sit next to the result they qualify, so the claim that the sentence "helped" can be judged when it's made. Report or drop the unreported test cases.
3. Move the prompt-cues section to another page, and define the two output modes and the game's basic setup once, early. Together these remove most of the work I had to do to piece the argument together.
