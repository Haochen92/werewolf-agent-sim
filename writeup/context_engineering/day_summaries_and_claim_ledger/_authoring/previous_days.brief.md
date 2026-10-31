# Explanation prototype: Carrying earlier days forward: the day summary and the claim ledger

Page: `writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md` · Level 2 · Purpose: how what was said on an
earlier day reaches a player later, and why it is condensed into fields rather than passed as the transcript ·
Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (`../../_authoring/l2_outlines.md`, "Page 2"); the sample
passage below was still written before drafting, and the rest of the skill ran without a second stop.

Authoring material, not page copy. The cold reviewer does not see it. The topic list and section order are
the approved outline's; this brief records the presentation and the evidence.

## Reader and explanation

- **Reader outcome:** the reader can say why a past day is carried as two lists in fixed words plus a
  code-built ledger instead of as its transcript (claims decide the game, span days, and code can gather and
  check them against the record only from fields), can follow one mis-transcribed line through the ledger to
  a lost game, and can say which part of the fix is the guard (the code rule, not the instruction) and why
  (the invention is too rare to replay).
- **Starting knowledge:** the parent (chapter page, section "Preserve earlier information without changing
  its meaning") has told the reader that each turn is a new call; that the private note carries the agent's
  own thinking; that summaries condense earlier days while today's talk stays in full; that fields let code
  build a claim ledger and check it against public facts; that anything carried forward can carry an error
  forward, with e06 in one sentence; and the guard at a glance. It no longer tells the incident, the
  self-block rule or any concrete check. New here: what the two lists hold, the three-block "Previous days"
  section and its three authors, the two cascade cases with their guards, why judging left the model, the
  replay checks, the runtime, the limits.
- **Concept order:** (1) nothing carries over unless the prompt carries it; (2) a *claim* (a player's
  statement about its own role or nights) differs from an *accusation*, and claims span days, so each
  player's claims must be gathered and set against the record, which code can do only from fields; (3) the
  summariser's two lists and their fixed words; (4) the three blocks a player reads, by author and trust;
  (5) a summary line is every player's input, so an error cascades: narration (guard: attribution), then the
  misread speaker (guard: the code rule); (6) the evidence that judging belongs in code; (7) replay checks
  and the runtime; (8) the never-run transcript comparison and the other gaps.
- **Likely confusion:** reading "code checks claims" as "code decides which claims are true". The page says
  "checked against the public record" every time, shows a check that confirms, states that the ledger says
  nothing where the record fits more than one reading, and that a claim the record cannot contradict stays
  a claim. Second confusion: the two e06 numbers. The invented claim did not recur in 10 replays (so the
  code rule, not the instruction, is the guard); the "5 of 5 → 0 of 5" figure is later speakers in replay
  with the fixed ledger and stays in the notes.
- **Section order:**
  0. What a new call lacks: the private note in one clause, then the earlier days (two short paragraphs).
  1. Why earlier days cannot simply be replayed: size in one clause; then claims decide the game, span days,
     and must be gathered per player and set against the record; code can do that from fields, not prose.
     Answers the reader's objection as a reason, not a defence. Link chapter 1's evidence-design page.
  2. One call, two lists: what the summariser writes, in fixed words; plans kept apart; what it never writes.
     Exhibit: the stored rendering of day 2 of a real game (first accusation and the claims line).
  3. What a player reads: the real "Previous days" block lifted whole (owner's ruling), then the three
     authors, the confirming check, the silent case, "rebuilt every prompt".
  4. How a carried-forward error cascades: two cases, each with the guard it produced. Narration → every
     statement attributed (bench result in one clause). e06 in full → the code rule, with the caught fault
     (the first broader rule dropped a true Vigilante claim; the replay caught it) and the limit.
  5. Why judging left the model: the verdicts of 2026-10-03 (subjective, mostly "unverified", lost between
     days); the record check judged wrong 27 of 27 across 66 summaries and removed; the stronger model no
     better (18 of 30 flawed in each arm) in one sentence; the speaker's own fields first, the summary as
     fallback, and what still rests on the summary alone.
  6. How it is checked, and how it runs: replay cases, five samples each, a two-row before/after table; the
     bench ran on seats that reported no reasoning tokens (one sentence); unit tests; the game's own model,
     the rescue model, the raw-transcript fallback (link the production chapter in words only: its Level 1
     file does not exist yet).
  7. What is not established: the never-run transcript comparison and why the summary stays regardless;
     plans, retractions and accusations on the summary alone; claims the record cannot check; no error rate
     for today's prompt; the retired May judge (link Evaluation's judges page); not memory (link Memory).

Page type: need → what was built → the risk it introduced → the guard → checks → limits (example B's
successive questions for §1 and §4–§5; example A's path-following for §2–§3).

## Sample passage

The difficult passage is §4's second case: the reader must see the line change meaning, follow it through
the ledger's fallback, and come away knowing that the code rule, not the instruction, is the guard.

> **A speaker's own words misread.** Attribution was not enough when the summariser misread what a speaker
> had said about itself. In a ten-seat game read on 2026-10-10, the Investigator said on day 2:
>
> | What the Investigator said | What the summary recorded |
> |---|---|
> | "I was roleblocked last night, which confirms we have an active Chanteuse in play." | "player_2 claimed chanteuse — Night 1: blocked player_2" |
>
> The Chanteuse is the wolf that blocks a player's night action. Something done *to* the Investigator became
> a claim *by* it. On day 3 a town player opened on that claim. The Investigator then accepted the false
> account of its own statement, saying it had claimed Chanteuse "to draw fire", against its own private
> record, and was voted out 7 to 1, though its own check had correctly found the Chanteuse Suspicious. The
> lone killer won the game.
>
> The line got through because the Investigator had described its night without filling in its own claim
> field, so the ledger fell back on the summary's transcription, and nothing checked that a player cannot
> block itself. The fix has two parts. The summariser is told that something done to a player is not that
> player's claim: "I was roleblocked", "I was protected" and "someone visited me" claim no role. And the
> ledger drops a claimed action that can only have been done to the speaker (a block, a watch, a check on
> oneself), dropping the claimed role with it only for the one case seen here, a Chanteuse claim resting on a
> self-block. A first, broader version of that rule dropped the role whenever every claimed action was on the
> speaker, and lost a true Vigilante whose "held my fire" the summariser had written as shooting itself; the
> replay caught it before it shipped, and the rule was narrowed.
>
> The code rule is the guard, not the instruction. In 10 replayed samples of that day, before and after the
> fix, the invented claim never recurred: it is rare, so the replay cannot show that the instruction prevents
> it. The ledger rule catches it however the model phrases it, and a unit test pins the rule.

The two-line table is real (game `e06`, `day_summary/report.md` §7); nothing in the passage is invented.

## Evidence and scope

- **Sources:** `evidence/extraction/day_summary/report.md` §1–§8 (the "Previous days" exhibit in §3 lifted
  whole; the rendered summary in §2); `evidence/extraction/day_summary/experiment_log.md` ① and the ③
  entries (the day-4 premise in game `46355b89`; the attributed design and the bench; the transcription +
  ledger design; the ten-seat audit and e06; the stronger summariser and the record check's removal; the
  speaker's own fields); `evidence/gameplay/discussion_evidence.md` §6.4–6.6 and §8.4;
  `evidence/gameplay/turn_prompt/report.md` decisions 3 and 13; `evidence/gameplay/deduction/experiment_log.md`
  §3 (the 27 of 27); `evidence/gameplay/data/phase3_summary_replay/README.md` (the Vigilante regression);
  `Agents/rules/claim_ledger.py` (the self-block rule as coded). Inventory: `../../content_plan.md` §5.
- **Claim and limits:** a mechanism (what is written, what is read, who writes each block) and a design
  rule (record apart from judge) supported by two recorded failures and one judged comparison. Limits kept
  on the page: the transcript comparison was never run; the bench comparisons ran on seats that reported no
  reasoning tokens; the replays are regression checks on known failures, five samples a case, not rates; the
  invented e06 claim did not recur in replay, so the code rule is the guard; "judged wrong" is a model's
  reading against transcript and record; no error rate for today's prompt and model.
- **Elsewhere:** the private note's stale-plan cost (page 4 and its Level 3); the "5 of 5 → 0 of 5"
  later-speaker figure (notes); the first case's bench result beyond one clause; the full ledger check list;
  formatter and file names (notes); the rescue model's detail (production chapter); the May judge's story
  (Evaluation's judges page); chapter 1 owns why claims decide the talk and its numbers (the 97% figure stays
  off). Handle with care, applied: never "code checks every claim" without "against the public record"; the
  two e06 numbers kept apart; no recorded failure of the raw transcript, so no claim that the summary fixed
  one; "judged wrong", not "wrong"; no model family names in prose; the caught Vigilante fault told as caught
  and narrowed.
- **Open questions:**
  1. The parent page's "Explore" line for this page is italic text, not a Markdown link, so
     `parent_context.py` reports "does not link" and the editorial reviewer would be told the page was opened
     directly. I built the same excerpt (the parent's introduction and the "Preserve earlier information"
     section) by the script's own rule and ran the editorial reviewer with it through the same prompt. The
     parent needs a real link when its placeholders are wired; I did not edit it.
  2. The claim field's history: the role field existed from the ten-seat game (2026-10-09, so before e06);
     the night-actions field came on 2026-10-18 (decision 13 dates the pair 2026-10-17). The page says
     "since mid-October" for the pair and, for e06, that the Investigator "had described its night without
     filling in its own claim field", as the report has it. If the owner wants the dates precise, they are in
     the sources comment.
  3. The stronger-summariser judge was the stronger of the two models compared (the log's 2026-10-24 note).
     The page uses only the equal 18 of 30 and the 27 of 27, which that note says hold; the split of error
     kinds stays off. Flagging in case the owner wants the judge's identity acknowledged in words.
  4. The production chapter's Level 1 file does not exist yet, so the rescue model is named in words with no
     link. Add the link when the chapter lands.
  5. Word count. After two review rounds the page copy is about 2,770 words against the 1,200–2,000 guide:
     about 390 are the two lifted exhibits (the day-2 rendering and the day-3 "Previous days" block, the
     owner's ruling), and the cascade section with the e06 case told in full is about 640. The remaining
     prose is about 1,750. Round 2's repairs added words rather than removing them (the fallback's full
     scope, the two fields' dates, the four-role gloss, the comparison told once with its error list, the
     second accusation restored so a ledger line can be traced). The branches the reviewers marked
     removable are gone (the bench number and its caveat, the headers' history, the duplicated
     speaker-field paragraph, the duplicated model-choice sentence). If the owner wants the guide met, the
     candidates are the §2 rendering (the §3 block shows the same claims as the ledger renders them, at the
     cost of the input → output pairing) and the §5 comparison paragraph; I did not cut the core
     explanation to reach the count.
  6. The bench result for the attributed summary is off the page. The outline allowed it in one clause,
     but the claims review found the 36% → 31% belongs to the whole 2026-10-03 pass (page 1 and the turn
     prompt's decision 3 credit it there), and the arm that isolates the re-summarised days is 32% → 31%.
     The owner may prefer it restored in that scoped form; the arms are in the sources comment.

## Review resolution

Round 1 (editorial `review-editorial.claude.20261031T035213Z`, claims `review-claims.claude.20261031T035408Z`).
The editorial reviewer received the parent excerpt built by hand (see Open questions 1).

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 (blocking) The speaker's own claim fields, which the e06 case depends on, appeared only in §5; the opening read as if the summariser were the ledger's only source and seemed to contradict the parent | Fixed: the two-source arrangement now sits in §2 (after the two lists) and in §3's ledger item; §5's history paragraph removed; one sentence at the end of e06 says the misread line is why the fields were extended to night actions | §2, §3, §4, §5 reread as a whole; the §5 heading still fits (verdicts, record check) |
| E2 / C1 The bench figure (36% → 31%) arrived without its unit, with its reasoning caveat three sections later; the claims reviewer found it measured the whole 2026-10-03 pass (rules, night records, labelled blocks, vote wording) with v3 on top, not attribution alone; the isolating arm is 32% → 31% | Fixed by removal: the number is off the page; the case carries the attribution guard. Dates and arms in the sources comment. The "seats reported no reasoning tokens" caveat went with it (nothing on the page to attach it to); recorded in the notes | §4 case 1 and §6 reread; the §6 paragraph that held the caveat now holds the regression-check scope and the unit tests |
| E3 "Replay" used before it was defined and covering two methods (player turns, summariser re-runs) | Fixed: player-turn replays no longer appear on the page (they went with the bench number); the summariser re-run is named "summary replay" at first use in e06 and defined again as "replay cases" in §6; the e06 limit says "re-runs of that day's summary" | §4, §6 |
| E4 The "Previous days" exhibit's "as claimed" check needs role knowledge (Suspicious read against an Illusionist reveal) | Fixed: a four-line gloss after the block names the three roles in it and why the reveal bears the read out (role sheet: wolves read Suspicious; the Illusionist is a wolf) | §3 |
| E5 "Two lists and nothing else" followed by "a separate list" for plans | Fixed from the schema: plans are a sub-list inside each role-claim entry; the page now says "each entry keeps the player's stated plans … apart from the actions it says it took" | §2 |
| E6 "Size is not the deciding reason" versus "kept for the two reasons the page opened with"; "That objection stands" had no antecedent | Fixed: §1 says size decides that days are condensed and not the form; §7 states the objection in words (whether players lose anything by reading a record of a day instead of the day) | §1, §7 |
| E7 Whether the claim field existed in e06 | Fixed: "the Investigator's answer had a claim field and it left the field empty" (report §7: the field existed; the night-actions field came later). "Read on 2026-10-10" replaced by "from early October"; the date is in the notes | §4 |
| E8 The table's roleblock row looked like the Chanteuse case with contradicting numbers | Fixed: the row says it is a different misfiling (the attempt dropped, not a role invented) | §6 |
| E9 The stronger-model paragraph mixed two decisions and the counts (60 vs 66 vs 30) did not reconcile | Fixed: §5 keeps the record-check result with the arithmetic stated (6 days × 5 per model = 60, plus the 6 the games used = 66); the model choice moved to §6's runtime paragraph (18 of 30 each) | §5, §6 |
| E10–E15 (taste) "next day" ambiguity; the headers paragraph; the narrative section unannounced; table orientation; the private-note opening repeating the parent; small glosses | Applied: "a day later"; the headers' origin folded into §3's lead sentence as the reason they exist; "the summary then still had prose sections"; "(six days, five samples each)"; the opening cut to one clause; "(evidence type …)" elided as "[…]"; "private note" for the Investigator's own record; "Rules:" glossed; "shown only this summary of day 3" | the sections named |
| C2 "What the town acts on is mostly claims" had no measurement behind it (the one found, nine-seat §2.1, points the other way) | Fixed: "The evidence the town can test is claims … the game is designed to make them testable"; the link now describes chapter 1's design, not a claim that claims carry the talk | §1 |
| C3 "Each summary that went wrong … was frozen" overstated how the cases were chosen | Fixed: "the summary failures found in the ten-seat games (the self-block, a copied record-check line, dropped denials, misfiled roleblocks) were frozen as replay cases"; selection method in the notes | §6 |
| C4 The rescue path implied every game has a rescue model; the house default has none | Fixed: "where one is assigned … and otherwise the day is stored as the raw transcript" | §6 |
| C5 The summary presented as the cause of the day-4 acceptance; the record says likely, beside a rules gap | Fixed: "the summary is the likely route, since the same players had rejected the claim while reading the discussion"; the rules gap is in the notes (it is page 1's subject) | §4 case 1 |
| C6 The fallback is per kind of field | Fixed: "no field of that kind" in §2 and §3 | §2, §3 |
| C7 The judge was the stronger of the two models compared (brief's open question 3) | Fixed in words: "judged by that stronger model itself" beside the 18 of 30 | §6 |
| C8 "Rebuilt" said of the summary (it is the ledger that is rebuilt) | Fixed: "written for each day of one game and never carried into another" | §7 |
| C9 The before/after table shows only the targeted failure; the same replays tracked true claims lost | Fixed: one clause after the table (the denial fix may have cost a few true claims, which five samples cannot settle) | §6 |
| C (not checked) "I rewrote the summariser" authorship | Reworded to "I changed the summariser to …": the design decision is the owner's; who typed the prompt is not in the record | §4 |

Round 2 (editorial `review-editorial.claude.20261031T040149Z`-series, claims `review-claims.claude.20261031T040339Z`;
both re-run because the speaker-field arrangement moved sections and the bench number came off).

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 (blocking) The fallback read as a rare backup for humans and old games; the e06 case shows it applies to any model player that leaves its claim field empty | Fixed: "the fallback for any player that filled no field of that kind that day: a model player that made no claim, a human player …, or a game recorded before the fields existed" | §2, §4 |
| E2 / C4 Both fields dated "mid-October" while an early-October game had a claim field | Fixed: the role field "since the ten-seat game began in early October", the night actions "since mid-October"; e06's closing sentence says the fields were extended from the role to the night actions | §2, §4 |
| E3 The opening justified fields for the summary alone, before the speaker's fields were introduced | Fixed: §1's last sentence now says claims reach the ledger as fields, stated by the speaker where it makes one and otherwise transcribed by the daily call, which also records the accusations | §1 |
| E4 Design history spread over three sections; "the accusation's record check stayed" sent the reader back | Declined the proposed move of §5 to directly after case 1: the approved outline keeps the two cascade cases together, and the second case needs the first. Fixed the connectives instead: case 1 names the first and second rewrites; §5 opens "the attribution rewrite of early October did more than attribute" and ends its first paragraph "one piece of judging stayed: the check each accusation got against the record" | §4, §5 |
| E5 The two-model comparison reported in two places; "flawed" undefined; 27 against 18 of 30 unclear | Fixed: told once in §5 (what was compared, what counted as an error, the 18 of 30 each with the judge named, then the 27 of 27); the model-choice sentence left §6 | §5, §6 |
| E6 Roles used in the exhibits before they were defined; the serial killer never defined; two names for lone killers | Fixed: a four-role gloss sits before the first exhibit (Investigator, Illusionist, Trailseer, serial killer as a lone killer that survives night attacks, with failed attacks never announced); e06's winner is "the game's lone killer, a third side"; the tie sentence after the block stays short | §2, §3, §4 |
| E7 The ledger's player_8 line could not be traced to the excerpt | Fixed: the second accusation restored to the §2 excerpt (defences and disputes shortened with marked ellipses); the tie sentence after the block names player_3's line | §2, §3 |
| E8 "Two villagers" against "the same players" | Fixed: "villagers called the argument fabricated"; "they had rejected the same claim the day before" (§6.4 item 3 says the same players had) | §4 |
| E9 "10 re-runs" split | Fixed: "five before the fix and five after" (the README's "10 samples on either arm" read at five a case; noted in the sources comment) | §4 |
| E10–E12 (taste) "lost between game days" unexplained; the rescue path; "copied record-check line" and "e06" | Applied: the clause dropped (the two remaining reasons carry the point); "rescue model, a second model assigned to the game" with the production chapter named; "a record-check line copied from the prompt's own example"; "the misread-roleblock game" in the evidence list | §5, §6 |
| C1 "catches it however the model phrases it" overstates a rule that fires on one stored shape | Fixed: "whenever the summary records the claim as a block on the speaker, whatever was said in the day" | §4 |
| C2 "stayed until a later test caught it" ignores two earlier patches | Fixed: "patched twice after wrong flags"; dates in the notes | §5 |
| C3 The Vigilante was caught on a control day, not a day that had gone wrong | Fixed: "re-running the summariser on frozen days, including days where a true claim has to survive" | §4 |
| C5 The roleblock misfiling showed on two models | Fixed: "15 of 15 on one summariser model, 6 of 15 on another → 0 of 15 on both" | §6 |
| C6 "Never writes the vote tally" is an instruction, not enforcement | Fixed: "is told to leave out …"; §3 keeps the enforced part (the engine writes the record) | §2 |
| C7 The Investigator has two checks a game | Fixed: "checks a player at night (twice a game)" | §2 |

Round 3 (editorial only, after the §5 restructure and the gloss move; the drafting agent was cut off by a
rate limit before resolving it, so the main session resolved it on 2026-10-31):

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| R3-1 (blocking) The 18 of 30 paragraph mixed the model comparison, an error rate and the record-check removal, and read as today's error rate | Fixed: split into two paragraphs (the record-check removal with the 27 of 27 first; then the model choice), the judge named as the stronger model, and the 18 of 30 scoped to the mid-October prompt that still asked for the record check, with a pointer to the close | §5 |
| R3-2 The source rule (speaker fields first, summary second) told three times and in flipping order | Flagged for the owner: fixing it means re-cutting §2's opening; left for the owner's read rather than a fourth review loop |
| R3-3 The exhibit's player_3 ledger line ("says they visited player_8") cannot be traced to a line in the summary excerpt above it | Flagged for the owner: the visit result comes from the accusation text, not the role-claim line; one clause after the block would say so |
| R3-4 The two rewrites' history told in two pieces, two sections apart | Flagged for the owner: a timeline sentence in §5 would close it; declined to restructure without the owner |

Check technical repairs against sources. A misunderstanding can identify a problem even when the
reviewer's proposed solution is wrong. Record material findings, not cosmetic bookkeeping.

## Trial record

Draft snapshots: `previous_days.first-draft.md` (before reviewer edits) · `previous_days.reviewed-draft.md`
(after) · owner revision when available.
Model and owner interventions: default model, one agent for this page in parallel with the other three;
the outline approved in conversation 2026-10-31 stood in for the prototype checkpoint; no owner
intervention during drafting.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
