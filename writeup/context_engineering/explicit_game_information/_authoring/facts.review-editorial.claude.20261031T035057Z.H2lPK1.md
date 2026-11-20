<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/context_engineering/explicit_game_information/facts.md by claude (opus), 2026-10-31T03:50Z -->

## 1. The argument as I understood it

The page asks why model players state false facts about the game, and what changed in the prompt to stop it. Its central answer is that there are two kinds of fault. Either the fact never reached the prompt (a wiring fault), or it was there but hard to use (a presentation fault). The repair for presentation faults is that code prints, as data, what a player would otherwise have to work out.

The sections apply this in order:
- a printed board of the dead and the roles still in play;
- a "night record" for facts that were lost before reaching the prompt;
- reworded private results;
- rules stated in both directions, ranked above what players say about the rules.

The last two sections ask whether this was enough. Printed facts alone were not: one error came back with a correct board in view. A board plus a required per-player "read" reduced errors on error-prone turns. Most October repairs have only been tested by replaying single turns. I can state that conclusion, but I had to put it together myself. The page never says in one place what was validated and what was not.

## 2. Apply the explanation

**Probe:** The page ends the rules section with "A stated rule guards the origin of a misreading. It does not undo one the players have already repeated to each other." Suppose the Illusionist rule sentence had been in the prompt from night 1 of that game. Would the page predict that the false rule never arises?

**Answer from the page:** The page cannot support a confident answer.
- The claim that the rule "guards the origin" rests on: "the first speaker seldom made the error at all." That observation is reported "on that game's turns replayed before and after the sentence." I can't tell whether the first speaker seldom erred *only after* the sentence was added, or *in both conditions*. If it was both, the data show the origin turn rarely failed anyway. They do not show the sentence prevented it.
- Which sentence was tested is not shown. The quoted rules block covers watch and follow direction. It says nothing about an Illusionist's "concealing visit" being seen or unseen. The added "ranking line" is quoted, but "the sentence" itself is not.
- "The Illusionist case" could mean the parent's case ("I visited nobody on night 2") or this page's case (four players asserting a concealing visit is always seen). I took it to be this page's case because of "false rule asserted by their peers". That is my inference.
- So the takeaway the page offers ("guards the origin, not the spread") reads stronger than the numbers shown for it.

## 3. Findings

**1.**
- **Where:** "What mechanics needed spelling out?", quote: "The Illusionist case shows the limit." / "the first speaker seldom made the error at all"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The probe above shows three gaps. It is unclear which Illusionist case is meant and which sentence was tested. It is also unclear whether the first speaker's low error rate came before or after the change. "On one model… on a smaller model" also conflicts with the paragraph's opening claim that each sentence was measured "on the same model", and neither model is named.
- **Repair:** Name the case and quote the tested sentence. Give the first speaker's before and after figures, or soften the "guards the origin" claim to match. Say which models were used, and why a second model appears here.
- **Severity:** blocking

**2.**
- **Where:** same section, quote: "public messages reading a visit the wrong way round fell from 16 of 35 to 5"
- **Kind:** unit or term changes meaning
- **What broke:** The setup is 18 turns × 5 samples, which is 90 samples. But the denominator is 35 public messages, and the "to 5" has no denominator. I can't tell what was counted or whether the before and after totals match. "Frozen turns" also appears without being tied to "replay", which section 2 defined.
- **Repair:** Say what the 35 are (public messages within the 90 samples?) and give the after denominator. Use "replayed turns" consistently.
- **Severity:** worth fixing

**3.**
- **Where:** "Did making the facts explicit suffice?", quote: "It tested the first section's lines with the reads, not the October repairs"
- **Kind:** section order / caveat reverses an earlier claim
- **What broke:**
  - The page is ordered by theme, but its evidence comes from two periods. July covers the census, the board, the board-only replay and the bundle. October covers the code review, the night record, the rewording and the rules.
  - The page's only pre-registered result arrives last. A reader naturally takes it as the verdict on everything before it. A clause near the end then says it covers only section 1 plus the reads.
  - Section 1 already forward-refers to this test ("the first replay of the board said it did not on its own"), so the board's evaluation is split across the page.
  - I had to rebuild the timeline myself to know which result supports which repair.
- **Repair:** Relocate. Either move the July board-and-reads test straight after section 1, or open with a two-line timeline (July: census, board, bundle; October: review, night record, wording, rules). Each repair is then read next to its own evidence.
- **Severity:** blocking

**4.**
- **Where:** "What could the wording mean?", quote: "on day 4 the investigator announced a check it had never made, on another player"
- **Kind:** missing connection
- **What broke:** The page says the result line "read as a repeat of public news", then jumps to the investigator inventing a check on someone else. The step between is missing. Presumably the investigator concluded it had no private result for night 3 and made one up to have something to report. I supplied that link myself. Also, "with the real check reported in all 20" does not say which arm it belongs to. I assume the reworded one.
- **Repair:** Add the one inference step (it believed it had no night-3 result) and attach "real check reported" to its arm.
- **Severity:** worth fixing

**5.**
- **Where:** opening, quote: "But reading the games in October found a second case that looks the same from the outside"
- **Kind:** missing connection
- **What broke:** The opening sets up two cases: missing versus present-but-costly. But its list of "present" failures includes "a rule the prompt never stated", which is a missing fact. The stated principle ("code prints, as data, what a player would otherwise have to work out") fits the board and the night record. It does not obviously fit rewording a line or adding rule sentences.
  - So I can't map the four question sections onto the two cases. Is an unstated rule a wiring fault, a presentation fault, or a third kind?
- **Repair:** Either make it three cases (missing data, data hard to use, rule unstated) with one repair principle each, or say how rewording and rule-writing are instances of the one principle.
- **Severity:** worth fixing

**6.**
- **Where:** opening, quote: "In the earlier nine-player version, about 3% of public messages carried a factual error of some kind."
- **Kind:** number before orientation
- **What broke:**
  - Neither the parent nor the page has introduced a nine-player and a ten-player version. I first learn the ten-player game is the current one in section 4.
  - The 3% has no source. I later guess it comes from the July census. It is not used again.
  - It also sits uneasily beside the later 48%/30%, which are rates on selected error-prone turns.
  - The October night-record replay uses "recorded turns of the nine-player game", even though the October work is otherwise about the ten-player game. That is never explained.
- **Repair:** Add one orienting sentence on the two versions (which is current, and which measurements came from which). Attribute the 3% to the census, or drop it from the opening.
- **Severity:** worth fixing

**7.**
- **Where:** "Did making the facts explicit suffice?", quote: "added a second change meant to make the player use it: a **read**"
- **Kind:** missing connection
- **What broke:** A read is a per-player assessment. The failure being fixed was arithmetic about roles still in play. The page never says why judging each living player would make the agent consult the roles count. As written, the read looks like an unrelated change bundled in.
- **Repair:** State the intended mechanism in one sentence, or say outright that it is untested and point to the turn-request page.
- **Severity:** worth fixing

**8.**
- **Where:** "What mechanics needed spelling out?", quote: "In one, four players asserted that an Illusionist's concealing visit is always seen and voted out the real Trailseer"
- **Kind:** term before introduction
- **What broke:** Three terms are never defined: Trailseer, "concealing visit", and "an Illusionist that carries its own kill leaves no trace". I can only guess the Trailseer is the follow role. I can't work out why its empty trail was correct, so the example doesn't land. It is also what finding 1's "Illusionist case" depends on.
- **Repair:** Explain or remove. Either define the two roles in a clause each, or replace the example with the watch-reversal case the parent already set up.
- **Severity:** worth fixing

**9.**
- **Where:** "What never reached the prompt at all?", quote: "the samples with a factual error went from 97 to 82 of 267, with 24 turns better and 14 worse"
- **Kind:** unit or term changes meaning
- **What broke:** The unit switches from samples to turns within one sentence. It is also unclear what "after" includes: all 8 addressed findings, or only the night record. Earlier the page says "addressed" means the fact reaches the prompt, not that the model uses it. I can't tell whether this replay tests use.
- **Repair:** State the before and after prompts, and keep one unit, or label both explicitly.
- **Severity:** worth fixing

**10.**
- **Where:** "Did making the facts explicit suffice?", quote: "replayed six times each under three arms, with and without the board"
- **Kind:** missing connection
- **What broke:** Three arms are announced but only two are described ("with and without the board"). I can't tell what the third arm was.
- **Repair:** Name all three arms, or say two.
- **Severity:** worth fixing

**11.**
- **Where:** "What never reached the prompt at all?", quote: "a model's summary of the day were rendered under the same day headings"; and "Did… suffice?", quote: "the census's model reader judged each answer"
- **Kind:** term before introduction
- **What broke:** Two roles appear unexplained:
  - "A model's summary of the day": which model writes it, and for whom?
  - The census's "model reader": the census was described only as "a count of factual errors over 50 games", not as model-judged.
- **Repair:** Add a clause for each: who writes the day summary (or defer it explicitly to the next page), and that census errors were judged by a model.
- **Severity:** worth fixing

**12.**
- **Where:** "Did making the facts explicit suffice?", quote: "A first run pointed the right way and showed that the turns chosen as clean controls were error-prone too"
- **Kind:** detail that does not change understanding
- **What broke:** Two research-method details slow the bundle result down without changing what the reader should conclude: the first run and the reworded question, and the "vote turns were rebuilt with the vote's own result in view" caveat. The caveats that matter are already there: selected turns, one answer per arm, model-judged, board and reads not separated.
- **Repair:** Relocate these to the Evaluation pages. Keep "written down before the data existed" and the four limitations that bound the claim.
- **Severity:** worth fixing

**13.**
- **Where:** "What is not established", quote: "on different models, so their results cannot be added up"
- **Kind:** other (information arrives too late)
- **What broke:** This is the first clear statement that the tests used different models. Earlier sections either say "the same model" or name none. Reading back, I can't tell which model applies to which result.
- **Repair:** Name the model with each result as it is reported.
- **Severity:** worth fixing

**14.**
- **Where:** "What is the board…", section 1, quote: "the first replay of the board said it did not on its own"
- **Kind:** term before introduction
- **What broke:** "Replay" is used here but only defined in section 2. The parent uses the word too, so this is mild.
- **Repair:** Move the replay definition to its first use.
- **Severity:** taste

**15.**
- **Where:** "What could the wording mean?", quote: "in every game rather than behind a setting"
- **Kind:** other
- **What broke:** "Behind a setting" suggests a configuration flag that has not been mentioned before, so a reader may wonder what else is behind settings.
- **Repair:** Say "behind a configuration option", or drop the clause.
- **Severity:** taste

## 4. Highest-impact improvements

1. Put each repair next to its own evidence, either by reordering or with a short July/October timeline at the top. The July bundle result then can't be read as validating the October repairs.
2. Rewrite the rules-measurement paragraph so the Illusionist case, the sentence tested, the units, the models and the first speaker's before and after figures are all explicit. As written, its headline claim ("guards the origin") goes beyond its numbers.
3. Remove or relocate the undefined ten-player example (Trailseer, concealing visit) and the bundle's run-history detail. Then say in one sentence each how the read is meant to make the board get used, and why the reworded result stopped the invented check.
