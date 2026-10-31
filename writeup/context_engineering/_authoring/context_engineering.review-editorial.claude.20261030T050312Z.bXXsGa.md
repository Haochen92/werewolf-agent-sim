<!-- editorial review of writeup/context_engineering/context_engineering.md by claude (opus), 2026-10-30T05:03Z -->

## 1. The argument as I understood it

The page asks how to get LLM players in a Werewolf variant to reason correctly from the facts they have. Its central answer is that giving the facts is not enough. Code should work out whatever is certain and state it plainly in the prompt, and the model should keep the judgement calls. The first section lists what a turn receives, shows a real Healer turn, and reports that players still made factual mistakes. It then names four kinds of failure, each with a remedy:
- facts the player misread, fixed by stating them explicitly
- earlier days that reached players distorted, fixed by a summary split by author and claims checked against the record
- decisions that did not follow the player's own assessment, fixed by having it write the assessment first
- conclusions the player failed to draw, fixed by a deduction engine

Each remedy comes with a replayed-turn result. The last section weighs the engine against larger models or more thinking, and cost and waiting time decide it.

## 2. Apply the explanation

**Question:** In the Healer case, suppose a larger model cost the same per game and was just as fast as the game's current model. Would the page's reasoning still choose the deduction engine?

**Answer from the page:** The page gives one deciding criterion: "What decided between them was cost and waiting time." On accuracy alone, the larger models did better on this case ("9 and 10 in 10") than the current model with the engine ("8 in 10"). With cost and speed equal, the page's own criterion no longer favours the engine, and the accuracy figures point the other way.

**Gaps I hit:**
- The page doesn't say whether the engine adds anything for a larger model, for example the wording that marks how certain each conclusion is. It also doesn't say whether engine plus larger model was tried. So I can't tell whether the engine is a cost workaround or a lasting design choice. The principle stated earlier ("code works out what is certain, and the model keeps the judgement") suggests a lasting choice, but the comparison paragraph argues only from cost.
- The whole comparison rests on one replayed turn ("on this case"). The page doesn't say whether that case stands for the general decision.
- I needed a reread to find which version of the Healer's prompt the baseline used (see the first finding).

## 3. Findings

**1.**
- **Where:** "Computing selected conclusions in code". The passage is "Its night record, as the game first showed it, also said it had 'learned nothing tonight'".
- **Kind:** missing connection
- **What broke:** The Healer turn shown earlier reads "You were roleblocked: your protection of player_5 did not happen." It doesn't say "learned nothing", and this section says the engine "replaced 'learned nothing' with one certain line". So I can't tell which prompt the excerpt shows (original, reworded, or engine-on), or which prompt produced the 2-in-10 baseline. Because this is the chapter's main worked example, the before/after comparison loses its footing.
- **Repair:** Label the excerpt with its version. State which prompt each figure (2/10, 8/10) used. If needed, show the old and new night-record lines side by side.
- **Severity:** blocking

**2.**
- **Where:** "Connecting the assessment to the action". The passage is "printing the facts together with it cut errors on 100 replayed error-prone turns from 48% to 30%".
- **Kind:** unit or term changes meaning
- **What broke:**
  - Replay was defined as one turn sent "ten times". Here the counts are 40 votes and 100 turns, and I can't tell whether each was sampled once or ten times, or what 48% is a share of.
  - "Printing the facts together with it" bundles two changes, so the effect can't be credited to the assessment.
  - This result is about the "remaining wolf" error from the first section, so it interrupts the vote-follows-assessment argument.
- **Repair:**
  - Define the unit (samples or turns) wherever a figure appears.
  - Say this result measures the two changes together.
  - Consider moving it next to the "remaining wolf" error it answers.
- **Severity:** worth fixing

**3.**
- **Where:** "Preserving earlier days faithfully". The passage is "the fields in which each AI speaker states the role it claims".
- **Kind:** term before introduction
- **What broke:** Nothing so far has said that a player's answer has fields, or that a claimed role is one of them. Structured answers are first described in the next section. The Investigator story then depends on "without filling in its claim fields", so I had to guess at a mechanism the page hadn't shown me yet.
- **Repair:** Before the blocks table, add one sentence saying that each turn's answer includes optional fields where the speaker states its claimed role and actions.
- **Severity:** worth fixing

**4.**
- **Where:** end of "What a player needs for its turn". The passage is "The remedies share one principle: code works out what is certain, and the model keeps the judgement."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The third remedy, writing the assessment before acting, is a change to the answer structure. No code works anything out in it. So the "one principle" doesn't hold for all four remedies, and I lost confidence in the chapter's framing.
- **Repair:** Narrow the principle to the remedies it fits, or name the third remedy as a separate idea.
- **Severity:** worth fixing

**5.**
- **Where:** the inputs table, "In the first version?" column. The passages are "added after miscounts" and "An assessment of every other player, written before the move".
- **Kind:** section order
- **What broke:**
  - The column tells the history of fixes ("restructured with checked claims", "reworded as its own action") before any failure has been described.
  - The assessment row is something the player writes, not something "the turn receives".
  - The page says a printed list of roles still in play "did not stop a player hunting for 'the remaining wolf'". I couldn't tell whether that happened before or after the "added after miscounts" change.
  - Separately, I was puzzled how a game continues once no wolf is left. The page doesn't say what else keeps it going.
- **Repair:**
  - Keep the table to inputs and why the player needs them.
  - Move the assessment row to the third section, as part of what the player writes.
  - Either drop the history column or put a short timeline next to the "remaining wolf" error.
- **Severity:** worth fixing

**6.**
- **Where:** after the Healer excerpt. The passage is "This Healer's note still says to stay quiet after another player has reported a visit to it."
- **Kind:** missing connection
- **What broke:** This flaw in the strategy note is raised and then dropped. None of the four failures picks it up. Why a reported visit should change the plan only becomes clear in the last section. Here it reads as a loose observation.
- **Repair:** Either remove the sentence, or point forward: "why this visit matters is the subject of the last section".
- **Severity:** worth fixing

**7.**
- **Where:** "Making the facts understandable". The passage is "a player argued that the Sentinel should appear in its own list of visitors".
- **Kind:** missing connection
- **What broke:** The page doesn't say why accepting this rule got the Sentinel voted out. I had to work out that the false rule made the Sentinel's genuine report look fake.
- **Repair:** Add one clause on what conceding implied, for example: "so its real report, which didn't list itself, looked invented".
- **Severity:** worth fixing

**8.**
- **Where:** "Preserving earlier days faithfully". The passages are "the summary recorded the Investigator as claiming to be the Chanteuse" and "code drops any claimed action".
- **Kind:** missing connection
- **What broke:**
  - The steps from "I was roleblocked" to a recorded claim of blocking someone, and from there to a role claim of Chanteuse, are left for me to fill in.
  - The fix filters claimed actions, but the error was a role claim. That only lines up if roles are inferred from actions, and the page never says so.
  - "Accepted that premise about itself" is unclear: did it accept that it had claimed Chanteuse?
  - Unlike the other fixes, this one reports no replay result.
- **Repair:** Spell out the chain in one sentence (blocked → recorded as a block it did → only the Chanteuse blocks → Chanteuse). Give a replay result, or say none was run.
- **Severity:** worth fixing

**9.**
- **Where:** "Connecting the assessment to the action". The passage is "the game's current model reported no reasoning tokens in 4 samples of 10, so it skipped that thinking".
- **Kind:** missing connection
- **What broke:** The page doesn't say why skipped hidden reasoning matters when the player still writes its assessment out. No effect on play is reported. "Enforced the answer format" also assumes I know about provider-side structured output. I couldn't tell whether this is a quality finding or just a configuration note.
- **Repair:** State what skipped reasoning cost, or was expected to cost, in play. If nothing was measured, shorten this to a one-line implementation note.
- **Severity:** worth fixing

**10.**
- **Where:** "Connecting the assessment to the action". The passage is "On 40 replayed votes from an earlier model".
- **Kind:** term before introduction
- **What broke:** This is the first sign that the game changed models. Later the page says "the game's current model", which leaves me unsure which results apply to the game as it runs now.
- **Repair:** Say once, early on, that the game switched models, and tag each result with the model it used.
- **Severity:** worth fixing

**11.**
- **Where:** "Computing selected conclusions in code". The passage is "The engine's code was written by an AI coding assistant; I set its requirements, its grading rule".
- **Kind:** detail that does not change understanding
- **What broke:** "Grading rule" is never explained. The sentence is about who wrote the code, not about how conclusions are computed.
- **Repair:** Either explain what was graded, or move this line to a credits/process note.
- **Severity:** taste

## 4. Highest-impact improvements

1. Fix the Healer example's versioning. Show which night-record text produced the baseline and which the engine result, so the main worked example holds together.
2. Settle the replay unit once (samples per turn) and use it for every figure. Untangle the 48%→30% result from the vote-alignment result.
3. Strip the fix history out of the inputs table, and limit the "one principle" to the remedies it covers. The four failures can then arrive in order without being previewed in code-review shorthand.
