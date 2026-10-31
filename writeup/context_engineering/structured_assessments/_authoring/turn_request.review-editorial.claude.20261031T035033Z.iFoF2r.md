<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/edrev/context_engineering/structured_assessments/turn_request.md by claude (opus), 2026-10-31T03:50Z -->

## 1. The argument as I understood it

The page asks how to get an agent to write down its assessment before it acts, and whether a fuller written assessment leads to better decisions. Its answer has two parts. Prompt instructions don't control whether the assessment appears or in what order. The shape of the answer does: required fields, fields that appear only when they apply, and a schema whose order matches the prompt. A fuller assessment, though, does not reliably improve the decision. The sections build that case in order:

- A healer example shows what the fields reveal.
- Three schema fixes show how the fields were made to appear.
- An ordering experiment shows that compliance is not quality.
- A comparative-read sentence improved the written assessment but not the decision, so it was dropped.
- Two later sections cover other things that move decisions: accidental cues (seat numbers, the answer example) and thinking effort.

The final sentence, "the shape of the answer moves the result as much as the instructions do", looks like the thesis. It is stated only at the end, and the opening does not set it up.

## 2. Apply the explanation

**Question:** Suppose that, instead of reordering the schema, the author had rewritten the prompt's opening line to ask for verdicts first, matching the old schema. Would the page predict the same 24 of 24?

**What the page supports:** Very little.
- The page says "the prompt's opening line asked for the reads before the decision, while the schema listed the memory verdicts first."
- It reports that the model "kept the schema's order on 15 of 24 real turns, and every mismatch put the reads first."
- It reports that reordering "the schema to match the prompt … gave 24 of 24."

So the page shows that agreement between prompt and schema produced compliance in one direction.

**What I had to supply:** "every mismatch put the reads first" could mean the prompt's line pulled the model, or that the model prefers reads first anyway. The page doesn't say which. That leaves the variation unanswerable. If the pull came from the prompt, verdicts-first agreement should also work. If the model has its own preference, it might not.

**Ambiguity:** I also had to guess what "kept the schema's order" counts. It could mean the order of all fields or only reads versus verdicts. The page leaves the mechanism ("agreement") implicit. A single clause naming what the author takes the cause to be would settle this.

## 3. Findings

**1.**
- **Where:** Testing whether a fuller assessment helps. "The Vigilante's vote for the real threat fell from 7 of 10 to 0 of 10"
- **Kind:** missing connection
- **What broke:** In the game, the Vigilante voted out the Sentinel. Yet the no-sentence replay voted for the real threat 7 times out of 10. The page never says that the recorded ballot was a minority outcome, so I first read "fell from 7" as a misprint. The cast also has to be reconstructed:
  - Which seats are town and which is the wolf among "the two quiet seats"?
  - What are the Sentinel and the Investigator?
  - What was "the two a bluff won on day 6"?
  - Who cast the second "wrong day-5 ballot"?
- **Repair:** Before the results, give a one-line cast for the four-player board: the roles, which seat is the threat, and what each frozen ballot was. Then state that the game's ballot was one draw from a decision that leaned right 7 out of 10 times.
- **Severity:** blocking

**2.**
- **Where:** Same section. "votes for the player rose from 13 to 17 of 30"
- **Kind:** number before orientation
- **What broke:** The setup was "Eleven votes … each answered ten times." Then 30 samples appear for day 4 without saying which three ballots they are. "The suspect had voted the Investigator out beside a wolf" also leaves it unclear whether the suspect is a wolf.
- **Repair:** Say which control ballots make up the day-4 set and state that the suspect is the threat.
- **Severity:** worth fixing

**3.**
- **Where:** Opening, then the healer example. "it missed a clue, it misapplied a lesson … or it decided against its own assessment"
- **Kind:** unit or term changes meaning
- **What broke:** The parent's list was a missed fact, an unsupported inference, and a decision that didn't follow the assessment. The page's list is a missed clue, a misapplied lesson, and a decision against the assessment. The worked example then lands on a fourth category, "a missed inference", which is in neither list. The example seems to show the taxonomy working, but it actually falls outside the page's own list.
- **Repair:** Use one list across the parent and this page, and include the missed inference, since that is the case the example demonstrates.
- **Severity:** worth fixing

**4.**
- **Where:** Getting the requested assessment into the answer. "also moved from the field description into the prompt body, which took the share … from 0.27 to 0.97"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** Two changes were made (a required field, and moving the instruction), and one number is reported. The grammar credits the move. The parent credits the required field. I can't tell which one did the work, or whether they were tested separately.
- **Repair:** Attribute the 0.27→0.97 change to both changes together, or report them separately.
- **Severity:** worth fixing

**5.**
- **Where:** Same section. "Three things went missing" / "A field that did not apply was filled anyway"
- **Kind:** more than one job in a paragraph
- **What broke:** The third item is extra output, not missing output. Its paragraph also brings in a separate change: the one-line brief and the vote-now nudge. That change has its own result (24 of 25 → 16 of 25 passes) but no statement of whether fewer passes is the goal. The healer example implies it is, but the page doesn't connect them.
- **Repair:** Reframe the lead-in, for example as "three ways the answer did not match the request". Move the brief and its result to its own short paragraph or to the accidental-cue section, and say why fewer passes counts as better.
- **Severity:** worth fixing

**6.**
- **Where:** Testing whether a fuller assessment helps. "One kind of sentence was removed on principle rather than on a count."
- **Kind:** section order
- **What broke:** Removing the role-card cues about "evasiveness" has nothing to do with whether a fuller assessment helps. It is a cue built into the prompt, which is the next section's subject. The paragraph also mixes the change, a confounded comparison, and a design principle.
- **Repair:** Move it into "When the prompt supplies an accidental cue", or remove it.
- **Severity:** worth fixing

**7.**
- **Where:** Giving the model more thinking effort. "Those vote counts come from a run with the schema enforced"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The table's headline vote figures turn out to come from a mode that isn't the one the game uses. I only learn this after reading the table. Other problems in the table:
  - The "Cost" column mixes a multiplier, dollars per game and latency.
  - The levels are never named.
  - The first row's 82 vs 27 has no denominator.
- **Repair:** Add the output mode to the table, or put the live-mode figures in it. Give the first row a denominator, and either split cost and latency into separate columns or label them clearly.
- **Severity:** worth fixing

**8.**
- **Where:** Same section, against the opening. "which this record neither shows nor claims to improve"
- **Kind:** missing connection
- **What broke:** The opening sets hidden reasoning outside the page's scope. A whole section then tunes it. The section's own justification ("a separate lever") doesn't explain why it belongs on a page about the written assessment.
- **Repair:** In the opening or the section's first line, say that thinking effort is included as the alternative lever the written assessment was compared against. Otherwise, move it to the cost page.
- **Severity:** worth fixing

**9.**
- **Where:** Putting assessment before action. "The reads joined in July … a seat overrode a retrieved lesson's suggestion about three times as often"
- **Kind:** missing connection
- **What broke:**
  - "That replay" has no referent.
  - I don't know whether overriding a lesson more often is good or bad.
  - "No earlier reads to update" implies reads carry over between turns, which the page never says.
  - "Judged thinner" doesn't say who judged.
- **Repair:** Say whether more overrides were wanted, name the judge, and say that previous reads are shown back to the seat (if they are).
- **Severity:** worth fixing

**10.**
- **Where:** The schema block. "memory_applicability fully / partly / does_not_apply, one per numbered observation"
- **Kind:** term before introduction
- **What broke:** The text described four fields, with verdicts only on "lessons". The block adds a fifth field and a new kind of item, "observation". "Four fields open every turn's answer" also clashes with verdicts appearing only when lessons are shown.
- **Repair:** Define observations versus lessons in one clause, and fix the field count, or say that some fields are conditional where the four are first listed.
- **Severity:** worth fixing

**11.**
- **Where:** When the prompt supplies an accidental cue. "lowest-numbered other seat in 95 of 96 calls" / "seat 1 had taken 78 of 96 night-1 actions"
- **Kind:** unit or term changes meaning
- **What broke:** The text moves from Investigator checks to all night-1 actions. I can't tell whether both 96s are the same set. "Seat 1 had taken" also reads as seat 1 acting, rather than being targeted.
- **Repair:** Name the population of each 96, and say "targeted player_1".
- **Severity:** worth fixing

**12.**
- **Where:** The healer example. "follow result on player_7 to player_8"
- **Kind:** missing connection
- **What broke:** The prose never says the healer is player_8, or that player_3 is the trailseer. I had to work out both to see that the reads "recognised the clue".
- **Repair:** Give the seat numbers in the setup paragraph.
- **Severity:** worth fixing

**13.**
- **Where:** Closing paragraph. "a fall in one game's day-4 votes across three code versions is entangled"
- **Kind:** other (a new result arrives in the conclusion)
- **What broke:** This result appears nowhere earlier. The paragraph also does two jobs: listing what is untested, and connecting to the dedup judge.
- **Repair:** Remove the day-4 fall, or introduce it where the evidence is discussed. Keep the closing to its summary of what remains untested and the cross-reference.
- **Severity:** worth fixing

**14.**
- **Where:** The table caption. "the note it was shown is the one the game recorded, and the game's own notes set the same premises side by side…"
- **Kind:** detail that does not change understanding
- **What broke:** The caption is dense provenance. I couldn't parse "set the same premises side by side", and it doesn't affect the example's point.
- **Repair:** Cut it to "one of ten replay samples of this turn; the recorded game shows the same pattern on all three turns".
- **Severity:** taste

**15.**
- **Where:** Opening. "each was tested against the decisions it produced"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** Several fixes were measured on compliance (0.27→0.97, 24 of 24), not on decisions. The page itself later says "compliance, not quality."
- **Repair:** Say that each change was tested, some for compliance and some for decisions.
- **Severity:** taste

## 4. Highest-impact improvements

1. Give a short cast and baseline before the comparative-read results: roles, the threat's seat, which ballots were frozen, and the fact that the recorded ballot was a minority draw. Then the central experiment can be followed.
2. State the thesis and a single failure list in the opening, and make the healer example land on a category from that list.
3. Remove or relocate the side branches so each section answers its heading:
   - the role-card paragraph moves to the cue section;
   - the one-line brief gets its own paragraph or moves to the cue section;
   - the new day-4 result leaves the closing;
   - the thinking-effort section gets a framing line, or moves to the cost page.
