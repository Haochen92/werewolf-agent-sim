# Finding and fixing factual errors

*Level 2 · [Evaluation](../evaluation.md) · next: [Measuring play quality beyond win rate](../play_metrics/play_metrics.md) · status: page copy drafted 2026-10-25, for the owner's review as the Level 2 exemplar.*

## Brief

**Reader question:** When an agent says something false, how do you find the source and choose a fix?

Subsections:

1. What counts as a factual error in a game where guesses and deliberate deception are legitimate.
2. Finding failures: two methods that answer different questions (added 2026-10-25, owner). Open with
   the featured story's origin: the invented investigation was found by playing, and the sweep could
   not have caught it.
   - **The wide sweep (the census):** how often errors happen, the project's only rate. Code flags
     candidates against the game record, a cheap model reads every one, a stronger model rechecks, the
     owner checks the flags. About 3% of public messages on 50 nine-seat games (July 2026); the counts
     are floors, since 2 to 3 of 15 sampled rejects were real errors. Its rules cannot see a claim about
     a living player such as "I investigated player_9", by design.
   - **Playing and reading games:** which errors happen in real games, how they unfold and what they
     cost; no rate. The owner plays a seat on the live site and flags errors as they happen (game
     `832404e9`, as a villager, is the featured story's game); AI readers also audited ten AI-only
     ten-seat games against a fixed list of error kinds. Ten games are too few for a rate.
   Source: factual errors, step 1.
3. Freezing a case: preserve the state and write an expectation, including whether the false premise
   already appeared in the input.
4. Diagnosing the invented investigation: real results were present; test wording and the previous note.
5. Matching the fix to its source, including summary errors passed downstream; checking later changes
   for regressions.
6. Testing more reasoning and a stronger model as separate interventions (added 2026-10-25): raising the
   players' thinking budget was the first change clearly beyond the test set's noise floor (bad samples
   82 → 27 of 267; 36 cases better, 4 worse), yet errors that came from the input still needed a prompt
   or pipeline fix. Source: factual errors, step 4.

**Exhibits:** the existing quote pair and four-version table, placed within the diagnostic explanation;
a compact input → summary → player diagram if it clarifies propagated errors. A short cause/fix table
can show missing input, misleading wording and reasoning slips without narrating every incident.

**Supporting fixes, used sparingly.** The full set of changes belongs on the gameplay page. Here, each
result accompanies the diagnostic question it answers: reworded investigation results in the featured
story; the repeated summary claim (5/5 → 0/5) in the upstream-error example; the unchanged citation
instruction as a failed candidate fix. The reasoning-budget and stronger-model studies remain separate.
Avoid a universal “instructions fail, code works” conclusion or attributing an internal reasoning process
to the model without evidence.

**Conclusion and limit:** rewording removed the invented investigation in the tested samples; it changed
both verb and dating, and does not establish a game-wide rate. The approximately 3% public-message rate
belongs to the earlier game and the census missed some errors. Keep both facts readable on this page.

**Sources:** [factual errors](../../../evidence/evaluation/factual_errors/report.md), supported by the
[gameplay report](../../../evidence/gameplay/report.md) and investigation record §6.2 in
[discussion evidence](../../../evidence/gameplay/discussion_evidence.md).

**Level 3:** not needed initially. The full investigation earns space here. Reconstructing prompts could
become a deep dive only if a concrete technical explanation adds more than the existing results table.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).


---

## Page copy (draft)

An agent can make a false claim because a necessary fact is missing or wrong, because correct
information is ambiguously presented, or because it fails to reason correctly from the available
facts. Even a complete input does not guarantee that the model will combine observations, apply a rule
or reach the right conclusion. These failures can look identical in the game, but they need different
fixes.

I used recorded game states to investigate them: find a failure, reconstruct the turn, compare possible
fixes, and retain the case for regression testing. The investigation below follows an agent that
announced a check it had never made. It also shows why testing a known failure and measuring the overall
error rate require different evidence.

Input inspection helps decide what to test next; the false answer alone does not establish its cause.

| What the inspection finds | What to investigate next |
|---|---|
| A necessary fact is absent or already incorrect | Prompt assembly, summaries and other upstream components |
| The fact is correct but its presentation is ambiguous | Wording, structure and placement |
| The necessary facts and rules are available, but the conclusion does not follow | Reasoning performance, including comparisons with a higher thinking budget or a stronger model |

### What counts as a factual error?

A factual error contradicts the game record. It may state something false directly, or rely on a false
premise: “We have to find the last wolf” is wrong if both wolves have already died. Deaths, revealed
roles, votes and night actions provide facts against which such statements can be checked. Interpreting
the statement still requires a reader.

Uncertainty and deception need different treatment. Guessing a hidden role is part of playing the game,
and deliberate public lies are assessed separately. A false factual claim in a private note counts as
an error: there is no other player to deceive. Loose wording is interpreted conservatively; “the
remaining wolves” can mean “at least one”, rather than asserting an exact count.

### Finding errors: systematic screening and live play

#### Discovering failures while playing

I encountered the featured failure while playing a villager on the live site. The investigator, whose
role is to check one player's identity each night, announced: *“I investigated player_9 last night, and
they are the remaining wolf.”* It had never checked player_9. The village voted that player out four
to one; they were innocent. The serial killer later won the game.

Playing exposed a consequential error, but it could not establish how often such errors occurred.
It covered only the games I played and the problems I noticed. A separate review by AI readers examined
ten games against a fixed list of error types. In that sample, invalid conclusions and distorted day
summaries were more common than invented facts. That helped identify what to investigate next.

#### Estimating frequency with a systematic screen

To estimate frequency, a census screened 50 games from the original nine-player version in July 2026.
Code selected statements matching known error patterns, such as references to dead players or incorrect
counts. A model checked the candidates against the record, a stronger model reviewed its flags, and
I checked the flagged public messages. A sample of rejected statements was reviewed too.

The census found errors in 68 of 2,292 public messages, about 3%. This is a lower-bound estimate:
reviewing rejected statements found additional errors the process had missed. The result belongs to
that version of the game, not the current ten-player version.

The screen also had no rule for an invented investigation involving a living player. It could therefore
miss the very failure I encountered while playing. Systematic screening estimated frequency within its
coverage; live play and targeted review exposed failures outside it.

### Turning a recorded failure into a repeatable test

Another full game would not reliably recreate the same situation. Instead, a frozen case preserves the
state before the failing turn: the transcript, deaths, revealed roles and the agent's private results.
Each version under test builds its prompt from that state. This holds the situation fixed while allowing
a prompt change to be tested repeatedly.

**Link (planned):** Explore how agent inputs are recorded → the observability page.

Repeated sampling matters because an error seen once may not recur. In an early replay check, three of
four observed July errors did not reproduce. The later screening procedure kept a candidate failure only
if it occurred in at least two of three replays. This selected recurring problems for investigation;
it did not produce a representative sample of all game turns.

Each case also needs a written expectation of an acceptable response. For an investigation claim, that
can name the checks the agent actually made. It should also record whether the false premise originated
in this response or was already present in the input. One ten-player set distinguishes those cases;
earlier sets mix them, making it harder to separate improvements to player reasoning from improvements
to the summaries players receive.

### Featured story: the invented investigation

#### The facts were present, but were they clear?

The investigator's input listed all its real checks. That ruled out a missing result, but did not
establish that the result was clearly presented.

Its night-3 check concerned player_5, who died that same night. The game publicly announces dead players'
roles, and the private check used the same word, “revealed”, without saying “you investigated”. It was
also dated by day rather than night. A second possible influence was the agent's previous private note,
which referred to “my investigation result from last night”. Reading the prompt suggested both
possibilities; it could not establish which change would help.

#### Comparing wording and the previous note

I tested four versions: the original input, reworded results, removal of the previous note, and both
changes together. Each generated 20 responses, all checked by reading them.

| Version | The investigator's night-3 result, as shown to it |
|---|---|
| As played | “Day 3: player_5 was revealed as healer” |
| Reworded | “Night 3 (last night): you investigated player_5, who is the healer” |

| Input version | Replies inventing a check | Replies reporting the real check |
|---|---|---|
| As played | 20 of 20 | 0 of 20 |
| Results reworded | 0 of 20 | 20 of 20 |
| Previous note removed | 20 of 20 | 0 of 20 |
| Both changes | 0 of 20 | 20 of 20 |

*One recorded turn, with 20 responses per version. The rewording changes both the description of the
action and its dating; the experiment does not isolate those two changes.*

#### What the result supported

Removing the note alone did not reduce the failure. With the results reworded, every response reported
the real check, whether the note was present or absent. This supported changing the shared result format.

A plausible explanation is that the original line looked like public news rather than the agent's
private investigation. The replay supports the wording intervention, not a definitive account of the
model's internal reasoning. It also does not identify which part of the rewording mattered.

The shared prompt formatter now uses the explicit investigation wording. The case remains available
for regression checks after later changes. These results concern one turn under the tested model and
settings; they do not establish how often agents invent investigations across games.

### Matching the fix to the source of the error

Input inspection became the first diagnostic step. When information was missing or wrong, the next
question was where it had been lost: in prompt assembly or in an earlier model's output. One audit found
that the healer's prompt omitted its own past protections. Adding that record addressed a different
problem from asking the model to reason more carefully about facts it already had.

The investigations led to several kinds of change. They were checked through different experiments;
the table is a map of interventions, not a claim that every fix received the same validation.

| Problem found | Example | Intervention |
|---|---|---|
| Missing history | The healer could not see its earlier protections | Include its own night-action record |
| Ambiguous presentation | A private investigation resembled a death announcement | Explicitly name the investigation and night |
| An inherited false claim | A summary turned being blocked into a claim to be the blocking role | Tighten summary instructions and use structured claims to maintain the claim record |
| A count the player had to derive | The agent searched for a wolf after both wolves had died | Supply an explicit count of remaining roles |
| An unclear rule | “I visited nobody” was read as “nobody visited me” | State the direction of visits and what each observation means |

#### Following an error through the summary

In one game, a player said “I was roleblocked last night”. The day summary treated that as a claim to
be the Chanteuse, the role that blocks others. Two players repeated the error, and the investigator
accepted the false claim about itself. Fixing only the later response would leave the misleading
summary available to other players.

The fix addressed that upstream source: clearer transcription rules and a claim record built by code
from players' structured claims. The repeated false claim went from five of five replay samples to
zero of five. That showed the failure stopped reproducing in those samples, not that every summary
error had been eliminated.

An instruction alone did not always help. In a separate replay of day turns, “cite the record exactly”
left the number of vote misquotes unchanged at 24 before and after, and the change was reverted. The record
was already available; asking for a citation did not add a mechanism to verify it. This result supported
checking the specific failure mechanism rather than assuming an instruction to be accurate was enough.

### When the facts are present but the reasoning fails

Correct input does not guarantee a correct conclusion. Some agents drew deductions that the recorded
actions did not support, even when those actions were available in their input. In these cases, model
capability was another factor to test: could additional reasoning or a stronger model make better use
of the same context?

Increasing the reasoning budget reduced responses with factual errors from 82 to 27 out of 267 samples
on the earlier game's test set. Re-judging the same outputs changed totals by only one or two, so the
reduction was much larger than the observed variation in the judge. The higher budget was not adopted
for live play. This result shows that more reasoning helped on those cases; the set contains several
error types, so it does not assign every improvement to one cause.

A separate comparison tested a stronger model on frozen turns from the expanded game, using the same
prompts. Responses with errors fell from six of 40 samples to one of 40. The improvement was
smaller in full games: over six games, invalid deductions fell from roughly one line in twelve to one
in fifteen. This was a different intervention on different cases, not a full-game confirmation of the
reasoning-budget result.

Together, these experiments support treating reasoning performance as a possible source of factual
errors, rather than assuming every false output comes from a bad prompt. They do not establish that a
stronger model fixes every such error. The invented investigation had a demonstrated wording fix, and
the inherited claim needed an upstream correction; model comparisons complement that diagnosis.

### Checking later changes for regressions

Regression comparisons run both versions on the same frozen cases and score them using the same
criteria. Known-correct cases show whether the judge raises false alarms, and whether a change breaks
turns that used to be right, while repeated judging of unchanged outputs checks measurement variation. Reviewing verdicts also matters: one review caught an incorrect written
expectation, showing that an apparent model failure can originate in the test itself.

Structured outputs can sometimes be checked directly by code. A day-summary replay caught a regression
before release: a broader claim-filtering rule removed a genuine Vigilante claim. That is why a fix
needs checks for behaviour it might break as well as the failure it targets.

The remaining limits are explicit. No factual-error rate has been measured for the ten-player game.
Review of individual replay verdicts does not substitute for systematic validation of the current judge
against human labels; that remains pending. Replays detect recurrence on known cases, while continued
play and review are needed to find failures the test set does not yet contain.

**Link:** Explore how reference labels are built to validate a judge → [Building reference labels](../reference_labels/reference_labels.md).

**Evidence.**

- [Factual errors: finding them, counting them, checking a fix](../../../evidence/evaluation/factual_errors/report.md) (the method report: the sweep, the test sets, the cause table, the test runs).
- [Gameplay problems and what we tried](../../../evidence/gameplay/report.md), problem 1 (every fix tried and its result).
- [Discussion evidence](../../../evidence/gameplay/discussion_evidence.md), §6.2 (the invented investigation) and §8.4 (the summary's invented claim).
- Optional: the game's replay on the live site, if game `832404e9` is served (to confirm).

<!-- Sources for the page copy (checked 2026-10-25):
Definition, what counts and does not: factual_errors/report.md, "What counts as a factual error".
Found by playing; 4-to-1 vote; serial killer won: factual_errors/report.md step 1 ("Playing and reading
games", game 832404e9, owner as a villager); game_play_enhancement/report.md problem 1.
Ten-game audit (28 bad conclusions, 22 summary errors, 2 invented facts; ten-seat): step 1 table.
Sweep: 50 nine-seat games, July 2026; four rules; 2,461 of 7,846; cheap reader, stronger re-read; the
owner checked all 90 flagged public messages; 68 of 2,292 (3.0%); 2–3 of 15 rejects real: step 1. The
sweep's blind spot ("I investigated player_9" about a living player): step 1, "How far to trust it".
Freezing as state; three of four observed July errors did not reproduce; kept if wrong at least twice in three;
origin vs repeat (one ten-seat set labels it; nine-seat sets mix): step 2.
Featured story: discussion_evidence.md §6.2; factual_errors/report.md step 3, "The worked example"
(the night-3 check on player_5, killed that night; the old and new lines; the note). The "public news"
reading is labelled as a plausible reading: the replay did not vary the reasoning.
Code reading: 12 places in all (the source and 11 more), healer protections: step 3 item 2.
Cause table rows: step 3, "What was found, symptom by symptom" (the visit row's fix; the count row's
printed line of roles alive from the July bundle).
Telling vs giving; "cite the record exactly" 24 → 24, p = 0.86, reverted the same day; the reason:
game_play_enhancement/report.md problem 1 and "Why telling did not work".
The roleblock claim: discussion_evidence.md §8.4 (game e06, AI-only; two players repeated it; the
investigator accepted it and was voted out 7 to 1; fix 6248fc58); the repeat 5 of 5 → 0 of 5:
factual_errors/report.md step 3 table and game_play_enhancement/report.md problem 1.
Thinking budget 82 → 27 of 267, 36 better / 4 worse; noise floor 1–2 of 267; not live (seats at low
thinking): step 4; game_play_enhancement/report.md "Where it stands". Separate stronger-model replay:
six bad samples in 40 versus one in 40, same prompts (factual_errors/report.md, step 3 symptom table
and step 4); selected ten-seat failure turns, not the earlier game's reasoning-budget test set.
Six games with a stronger model:
invalid deductions 1 in 12 → 1 in 15: step 4.
Guardrails: controls 4 of 120 against 22%; hand read caught a wrong expectation; the summary replay caught
the dropped vigilante claim: step 4; discussion_evidence.md §8.4 (the broader rule). No ten-seat rate;
Haiku judge unchecked against people: "What is not measured".
Kept off the page (handle-with-care): where records are stored; the judge's model name. -->
