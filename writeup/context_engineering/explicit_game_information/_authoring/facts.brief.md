# Explanation prototype: Making facts available and unambiguous

Page: `writeup/context_engineering/explicit_game_information/facts.md` · Level 2 · Purpose: diagnostic path through successive
questions (closest example B, `evidence_design.md`) · Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (`../../_authoring/l2_outlines.md`, "Page 1").

Authoring material, not page copy. The cold reviewer does not see it. Topics: `../../content_plan.md`
§2 section 1, §5, §6, §7; presentation: `../../_authoring/l2_outlines.md` page 1 (section order, exhibits,
"stays off" column, terms to gloss, handle-with-care).

## Reader and explanation

- **Reader outcome:** when a model player states a false fact, the reader can ask three questions of
  the prompt in order (was the fact there at all; was it there but left to be reconstructed or worded
  so it could mean something else; did it rest on a rule the prompt never stated) and knows that the
  repair in each case is code printing the fact as data, and that printing alone was not enough.
- **Starting knowledge:** the parent says each turn is a new model call built from selected state,
  that the prompt gained a death roster and remaining-role counts, tells the visit-direction example
  and the Sentinel concession (10 of 10 → 0 of 10), and says a correct board had not stopped a
  survivor-count error. This page adds: the two board lines as they read, the code review and the
  night record, the invented check from the cause side, the rule text and its limit, the bundle test
  with its limits. New terms, each glossed in a clause on first use: board lines, census, night
  record, replay/frozen turn, role card, rules block, read, the bundle.
- **Concept order:** (1) absent information and information present but needing reconstruction fail
  the same way from the outside → (2) what the player had to reconstruct, and the two lines that
  print it → (3) what never reached the prompt, and the night record → (4) what a present line could
  be read as, and the rewording → (5) which rules the engine applied but never stated, and the limit
  of stating them → (6) whether printing sufficed: the July bundle and its limits → (7) what is not
  established.
- **Likely confusion:** reading the July bundle (48% → 30%) as a test of today's prompt, or as
  evidence for the board alone; and reading the invented-check replay as "the wording, not the
  reasoning" or as a rate. Both are met beside the numbers.
- **Section order:**
  - §0 Opening: two faults that look the same from outside; the principle (code prints what a player
    would otherwise work out). Two short paragraphs. The ~3% only as "about 3% of public messages in
    the earlier nine-player version".
  - §1 What was the player expected to reconstruct? Before/after from one recorded game: the game
    master's announcement as the transcript shows it, then the two board lines from the same
    prompt; the commonest census error (survivor arithmetic).
  - §2 What never reached the prompt at all? The code review (12 places; healer protections, the
    vote overwriting a note, engine facts rendered like a summary); the night record with quiet
    nights explained; 8 addressed / 4 partly, "addressed" is wiring; replay 97 → 82 of 267 with its
    uncertainty; labelled blocks → page 2.
  - §3 What could the wording mean? The quote pair from the same game; one sentence of result;
    shipped everywhere as a correctness fault; link to Evaluation for how it was found and what else
    was varied; one turn, two changes at once.
  - §4 What mechanics needed spelling out? October ten-seat games: invented facts rare, ability
    inferences the commonest error; the visit rule as written; the ranking line; visits 16 of 35 → 5;
    the Illusionist case as the limit (10 → 7 → 4 of 10 on one model, 10 of 10 on a smaller one; later
    speakers repeat a false rule already in the transcript). Sentinel in one sentence.
  - §5 Did making the facts explicit suffice? T1b (3 of 4 never recurred; the fourth with a correct
    line), so reads were added; the bundle on 100 error-prone turns, 48% → 30%, 29 better / 11 worse,
    about 60% more output; limits beside it; it tested §1's lines plus the reads, in July; why reads
    come first → page 3.
  - §6 What is not established: no ten-seat rate; no whole-prompt comparison; rule sentences recited.

## Sample passage

(§1, the page's central idea made concrete. Both halves are lifted from the investigator's as-played
day-4 prompt in game `832404e9`, `evidence/gameplay/data/investigator_replay/prompt_A.txt`; the
outline named the golden fixture's test board, and the same-game pair was preferred because §3's
result line comes from the same prompt. Not an illustration: real recorded text.)

The first version of the prompt gave each player the rules, the list of living players and the
transcript, in which the game master announces each death. Who had died, with which role, and which
roles were therefore still in play were all in there, spread across days of prose. One such
announcement, as the transcript of a recorded game shows it:

> game_master: Night of day 3: player_5 was killed by the wolves last night. They were a healer.

To know on day 4 how many wolves could still be alive, a player had to collect every line like it
since day 1, subtract the revealed roles from the public cast and hold the result while writing. The
July census, a count of factual errors over 50 games of the earlier nine-player version, found that
the commonest error was exactly this arithmetic: hunting "the remaining wolf" when no wolf was alive.

Every call now carries two board lines below the transcript, computed by code from the engine's own
record of deaths. From the same prompt:

> == Dead so far (public) ==
> player_2 (vigilante, night 1), player_1 (wolf, lynched day 2), player_4 (villager, night 2), player_5 (healer, night 3)
>
> == Roles still in play (fixed cast minus revealed deaths) ==
> 1 wolf, 1 serial killer, 1 investigator, 2 villager

The announcement stays in the transcript; what changed is that the player no longer derives the count
from it.

## Evidence and scope

- **Sources:** `evidence/gameplay/turn_prompt/report.md` ("The problem", "The board facts", decisions
  1–4, "How it is checked", "What is not established"); `evidence/gameplay/discussion_evidence.md`
  §6.2, §8.4–8.6; `evidence/evaluation/factual_errors/experiment_log.md` §2, §8–9;
  `evidence/evaluation/factual_errors/report.md` step 1 (census); recorded prompt
  `evidence/gameplay/data/investigator_replay/prompt_A.txt`; rule text `Agents/prompts/game_rules.py`;
  formatters `Agents/prompts/prompt_formatters.py`. Map blocks 49, 141–144.
- **Claim and limits:** mechanisms (what code prints, how results and quiet nights are worded, the
  rule text) are current behaviour per the report at `588a3273`; the invented check is one turn of
  one game, rewording changed two things at once; the fidelity replay is "an improvement in this
  sample with substantial uncertainty"; the rules replays are single-game replays on the model that
  showed each error; the bundle is selected error-prone turns, one sample each, model-judged, vote
  turns rebuilt with the result in view, two changes never separated, July nine-seat, before the
  October repairs.
- **Elsewhere:** the four-variant table and how the failure was found → Evaluation's factual-errors
  page; the labelled blocks and the vote-note fix beyond a clause → page 2; why reads precede the
  action → page 3; T2/T3 token counts and the coverage monitor → notes; the Sentinel beyond one
  sentence → parent. Handle-with-care applied: never "the wording, not the reasoning"; 20 of 20 is
  one turn; "addressed" is wiring; no model family names; no ~3% beyond the earlier nine-player
  version; no test authorship; the opening-order mismatch stays off (chapter 1).
- **Open questions:**
  1. §1's exhibit uses the recorded game `832404e9` (nine-seat, October, board already shipped) for
     both halves rather than the golden fixture's test board the outline named. Same wording as
     today's lines; accept, or swap the "after" for the golden lines?
  2. Ownership of the rule text (§4). The record shows the owner's rulings (the carried kill is
     invisible; the Sentinel is not among its own visitors) but not who drafted the sentences. The page
     says "the missing rules went in"; change to "I wrote" if the owner drafted them.
  3. The reads' mechanism (§5) is quoted from the T1b record as the idea recorded before the test; the
     bundle never tested it apart from the board. The page says "the idea, recorded before the test".
     Acceptable, or drop the mechanism and point only to page 3?
  4. The rules limit (§4). The outline's one-line limit ("a correct rule may not undo one the players
     have repeated") is contradicted in part by the visit replay, where the repeated misreading did
     fall (11 → 3 of 20). The page now states both and calls the reach of a stated rule open. The
     Level 1 does not make the stronger claim, so nothing there needs changing.
  5. The §2 replay figure follows the report (82 of 267, the re-summarised arm); the plain "after" arm
     was 86 of 267. The page names the arm; the owner may prefer both numbers or the plain arm.

## Review resolution

Editorial: `facts.review-editorial.claude.20261031T035057Z.H2lPK1.md` (run on a scratch copy of the
chapter whose Level 1 placeholder carried the link; the Level 1 was not edited). Claims:
`facts.review-claims.claude.20261031T035250Z.IIM0yZ.md`.

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 / C1: "guards the origin, does not undo" read stronger than its support; which Illusionist case and which sentence unclear; first-speaker figures missing; "same model" vs two models | Fixed. §4 now names the carried-kill case, quotes the sentence tested, gives the first speaker's 1 of 5 → 0 of 5 ("too few to measure"), the cascade 10 → 7 → 4 of 10 and the smaller model's 10 of 10, and states that the visit replay's repeated misreading did fall; conclusion changed to "how far a correct rule reaches a false one already in the transcript is open" (phase3_turn_replay README; §8.6 "Cascades") | §4 reread as a whole; the outline's limit line is now qualified (open question 4) |
| E3: July result arrives last and reads as the verdict on the October repairs; timeline split | Fixed in place, order kept (owner-approved outline): §5 opens with its scope (July, nine-player, board lines plus reads, not the October repairs); the opening gains a two-sentence orientation on the nine- and ten-player versions and which work belongs to which; §1's forward reference no longer uses "replay" | Opening, §1 end, §5 reread |
| C2: "the one comparison whose measure was written down before its data" conflicts with T1b/T2 also planned | Fixed: "the most firmly planned comparison behind this page: its measure was written into the plan before the second run's data existed" | §5 |
| C3: "the board's first test said it did not on its own" overstated (one case, 6 samples an arm, no between-arm claim supportable) | Fixed: "in the one error that recurred ... it did not" (§1); §5 says one case, not a measured shortfall, but the board could not be relied on alone; T1b's three arms named (E10) | §1, §5 |
| C4: visit result not isolated (after v1 arm bundled three prompt lines); "on the same model" | Fixed: "tested together with two other prompt lines added the same day"; "on the model that had made it" | §4 |
| C6 / E6: "about 3% ... of some kind" overstated; nine/ten-player versions never introduced; 3% unsourced | Fixed: the 3% is attributed to the census, scoped to deaths, roles and who was left, called a floor; census glossed with its model reader (also E11); versions oriented in the opening | Opening |
| C7 / E4: "read as a repeat of public news" stated as fact; the inference step to the invented check missing | Fixed: "could read as"; the promise-then-no-recognised-result step added and labelled "the record's reading, not a measurement"; "real check reported" attached to the reworded arm | §3 |
| C8 / E9: 97 → 82 arm bundles a summary rewrite; unit switches samples/turns; what "after" means | Fixed: the sentence names the before/after prompts, the re-summarised earlier days, the model reader, and gives samples and turns each with their denominator | §2 |
| C9: healer "could not say" overstated | Fixed: "nothing the engine wrote could tell it" | §2 |
| C10: reconstruct-from-prose case dated to October | Fixed: "in July and again in October" | Opening |
| C5: "I wrote the missing rules in" ownership unclear | Changed to "the missing rules went in"; flagged (open question 2) | §4 |
| E5: opening's two cases vs four sections; principle fits only the board | Fixed: the unstated rule is "the facts were there but the rule needed to read them was not"; the repair stated in its three forms | Opening |
| E7: why a read would make the board get used | Fixed: the recorded hypothesis from T1b added in one sentence, labelled as the idea recorded before the test (open question 3) | §5 |
| E8: Trailseer, hiding visit, carried kill undefined | Fixed: a clause each, and the carried-kill rule quoted | §4 |
| E2: 16 of 35 → 5, denominator and unit | Fixed: "16 of 35 to 5 of 35", "public messages" | §4 |
| E11: "a model's summary of the day", "census's model reader" unexplained | Fixed: day summary glossed in §2; the census gloss in the opening names the model reader | §2, opening |
| E12: run-1 and vote-rebuild detail slow the bundle result | Declined in part: the reworded question is the owner's required wording of the fixed-measure practice and the vote rebuild is a limit that changes how to read both arms (content plan §7); run 1 compressed to one sentence | §5 |
| E13: models not named per result | Declined: the owner's rule keeps model family names off the prose; "the model that had made it", "a smaller model" and §6's "on different models" stay; names are in the sources comment | — |
| E14 / E15: "replay" before its gloss; "behind a setting" | Fixed: "replay" removed from §1; "rather than as an optional variant" | — |
| Own read: "you checked" (§2) vs "you investigated" (§3) looked inconsistent | Fixed: one bracketed sentence in §3 on the ten-player investigator's wording | §3 |

Not re-run: the structure (section order) did not change; the central explanation of §4's limit was
re-scoped, not rebuilt. Word count after revision is reported in the trial record.

## Trial record

Draft snapshots: `facts.first-draft.md` (before reviewer edits, 2,165 words of page copy);
`facts.reviewed-draft.md` (after, 2,504 words including 201 words of verbatim exhibits: the
announcement, the two board lines, the quote pair, the visit rule and the ranking line). The guide is
1,200–2,000. The growth is the reviewers' required additions: the version orientation, the Trailseer
and Illusionist glosses, the carried-kill sentence, the first-speaker and smaller-model figures, the
reads' recorded mechanism, the replay arm description, and the inference step in §3. Secondary clauses
were trimmed (the vote-note fix, the Sentinel sentence to a clause, the board-line description, the
hidden-body and run-1 wording). Further cuts would remove an exhibit or a limit; left for the owner.
Model and owner interventions: default model (reviewers on opus via review.sh), one agent for this
page; outline approved in conversation 2026-10-31; no second stop. Deviations from the outline: the
§1 exhibit source (open question 1); the §4 limit re-scoped after both reviewers (open question 4).

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |
| §5 "Did making the facts explicit suffice?" rewritten (2026-10-31) for a reader with minimal context: the error named, "board" said in words, the first test's three-arm design and the non-recurring cases moved to the sources comment, the vote-prompt limit moved to the comment | example or representation; prose | Explanation redesigned: the section now leads with the answer and tells the two tests as two stories; numbers unchanged |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
