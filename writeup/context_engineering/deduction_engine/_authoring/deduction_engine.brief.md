# Explanation prototype: Working out selected conclusions in code: the deduction engine

Page: `writeup/context_engineering/deduction_engine/deduction_engine.md` · Level 2 · Purpose: mechanism explanation (how a conclusion is derived from what a seat may know, how strongly it is stated, and how it is kept in bounds), with a short comparative passage for the replayed decisions · Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (`../../_authoring/l2_outlines.md`, "Page 4", revised twice that day). No second stop; the sample passage below was still written before drafting.

Authoring material, not page copy. The cold reviewer does not see it. The outline file holds the section
table, the "stays off" column and the handle-with-care list; this brief does not copy them.

## Reader and explanation

- **Reader outcome:** the reader can say what the engine starts from, how it gets from a seat's facts to a
  printed line, why each line's grade sits in its wording, what the two boundary tests do and do not show,
  and what the three replay screens establish and leave open. They should be able to say why "player_7 is
  the Chanteuse" is never printed on the healer's turn, and why the engine is a cost choice for a small
  model at a low setting rather than a necessity.
- **Starting knowledge:** the parent section already tells the healer's missed inference, propagation in a
  clause, the two boundaries in a sentence each, the three grades with the Alice example, the live-mode
  healer result (2 → 8 of 10; spoke 7 against 3), the Sentinel result (6 → 2 of 40, replies unchanged),
  the cover screen in a clause, that whole-game effect is unmeasured, and that larger models or more
  thinking made the connection alone. This page recalls each in a clause and adds the mechanism, the
  grading rule's reasons, the two checks and each screen's setup and limit.
- **Concept order:** (1) the failure class and the cost rationale → (2) the seat's view (permitted facts
  only; claims as claims) → mechanics as constraints via role traits → the solver's candidate sets and
  propagation (A/B/C illustration, because the healer's own lines do not narrow candidate roles) → the
  rendered line beside the night record → (3) the three grades and why the grade is in the sentence
  (uptake almost every time) → (4) the two boundaries: independence from hidden information (the test in
  words, then its name) and consequences-not-advice (one cover line beside one card sentence) → (5) the
  three screens with comparison and limit, then the larger-model and higher-thinking results as the limit
  on where the engine adds value → (6) scope, gaps, authorship.
- **Likely confusion:** (a) reading "the deductions do not change when hidden roles change" as "the
  deductions are correct"; the page separates the two and links Evaluation for correctness. (b) reading the
  healer's 2 → 8 of 10 as the effect of one line; the comparison is the engine on against the game's
  original night record, whose "you learned nothing tonight" works against the deduction. (c) taking the
  earlier "all ten stayed silent" as the current result; it is named once with its output mode and sent to
  the Level 3.
- **Section order:** as the approved outline: §1 responsibility and cost rationale (two paragraphs) · §2 the
  path through the engine on the healer's turn, with the A/B/C table once · §3 the grades, the contradiction
  case, the wording rule and its reason · §4 information access (Alice/Bob illustration, named after the
  words) then consequences against advice (healer, evil cover, the dropped counter-claimant line) · §5 the
  three-row table, then the model/thinking limits and the bundled games, then the Level 3 link · §6 scope,
  coverage, unmeasured effects, authorship.

## Sample passage

The difficult relationship is §3: why the second healer line cannot promote player_7, and why the grade
lives in the sentence. Draft page copy:

> Look at the two lines again. The first says the Chanteuse came to the healer; the second does not say
> that player_7 is the Chanteuse, even though player_7 admitted the visit. Two things stop it. Another
> visiting role could also have come to the healer that night, so the block does not single out player_7.
> And a true report does not establish the reporter's role: a wolf can report a visit that really happened.
> So the first line is certain, and the second lists the alternatives under a named claim.
>
> Every line the engine prints carries one of three grades, and the grade is in the sentence itself:
>
> | Grade | When it holds | On the healer's turn |
> |---|---|---|
> | Certain | in every legal game that agrees with what the seat knows | "…so the Chanteuse, a wolf, came to you that night." |
> | Conditional | in every such game in which the named claims are also true | "If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on night 2." (another seat's turn) |
> | Alternatives | a complete list of the branches the facts leave open, none promoted | "…either player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you." |
>
> The grade is in the wording rather than a heading because an injected line is taken up almost every
> time: in ten replays of the healer's turn, every note recorded the Chanteuse's visit once the line was
> present, and none did without it. A wrong certainty would therefore not be an occasional error. It would
> be a false premise in every game where the line's conditions hold, read by the player as its own result.

The three-row A/B/C table (illustrative) is the §2 exhibit; the Alice/Bob table (the owner's illustration,
not a specific test's state) is the §4 exhibit; the three-row results table is §5's.

## Evidence and scope

- **Sources:** `evidence/gameplay/deduction/report.md` §1–§5 and its 2026-10-30 note;
  `evidence/gameplay/deduction/experiment_log.md` §2, §4, §5, §8, §9 and the case register;
  `evidence/gameplay/deduction/deduction_catalogue.md` §0 (the grades) and AC1 (the healer's lines);
  `evidence/gameplay/data/visit_wording_ab/README.md` "Arm C" (the Sentinel row);
  `evidence/gameplay/roles/report.md` decision 11 and "The games: a bundle, eight pairs";
  `Agents/prompts/roles/pack.py` (the card sentence beside the cover line);
  `tests/engine/deduction/test_candidates.py::test_hidden_roles_the_seat_cannot_see_do_not_change_its_items`
  (source note only); the content plan §2 section 4 (the Alice/Bob table) and §7; map blocks 48–55.
- **Claim and limits:** mechanism (the view → constraints → propagation → rendered line, with premises
  kept); design rule (three grades in the wording; never state as absolute what some legal game makes
  false; contradiction returns no candidate result); checks (hidden-role swap shows independence from
  hidden information on the tested cases, not correctness); measured results on replays of chosen failures
  on one small model: healer 2 → 8 of 10 read, 7 against 3 spoke, one turn, 10 samples a setting, engine on
  against the original night record; Sentinel own-report errors 6 → 2 of 40, replies 17 of 55 unchanged,
  19 turns × 5 samples, downstream effect unresolved; covers 36 → 44 claims, 4 → 0 denials, 41 turns × 2,
  different judges per arm. Larger models (9 and 10 of 10) and the same model at a high setting (9 of 10,
  about 2.8× the time a turn) made the connection without the engine. Whole-game effect unmeasured;
  wolves 3 of 8 against 0 bundles cards with the engine.
- **Elsewhere:** the enforced-mode uptake result, the carried-note 2×2, placement screens, the
  investigator's vote case and the moderator line, and the 2026-10-30 comparison in full → the Level 3
  (planned, `roleblocked_healer.md`). The rest of the test suite (oracle, random nights, trait flips) →
  Evaluation's code-checks page. The output-mode story → chapter 6's cost page. The evil contest and the
  bundled games → chapter 1's evidence-design page. The four-attempt table and the acceptance-case seat
  block → this page's notes. Handle-with-care items applied: "checked" never "proved"; the enforced-mode
  "none spoke" named once with its mode and sent to the Level 3; boundary test = independence on tested
  cases; rationale = cost; Sentinel downstream unresolved; cover arms judged by different judges; wolves'
  3 of 8 not attributable; authorship one sentence, test authorship unmentioned; no model family names;
  no research terms; ~3% rate off.
- **Open questions:**
  1. **The authorship sentence** (§6) is on the page per the outline; the owner has not yet confirmed it
     stays. Flagged. Both claims rounds note that "the experiments" reads as running them, while the
     record supports choosing and directing them (runs and judging by AI agents); "the choice of
     experiments" is the suggested narrowing, for the owner.
  6. **"Cost, not necessity" is dated.** The outline states it as the rationale; the record shows the
     high-thinking and larger-model evidence came 2026-10-30, after the build. The page now tells it as
     "at the time … a later check …". If the owner prefers the undated framing, say so.
  7. **Length.** The page copy is above the 1,200–2,000 guide (see the trial record). Candidate cuts if
     the owner wants it shorter: the cover row (chapter 1 tells the screen; keep one sentence here), the
     Alice/Bob table (one sentence), and the "possible roles" illustration if the solver is left to the
     evidence report.
  2. **"Roughly twenty times the seat cost."** The log gives $2.30 a game for the larger model's seats
     against $0.12 (§2's question, restated in §8). The page prints both dollar figures beside the ratio
     so the ratio is not a bare re-derivation. If the owner prefers only the dollar figures, drop the ratio.
  3. **The card sentence beside the cover line** is lifted from the live wolves' card
     (`Agents/prompts/roles/pack.py`, "Plan your cover before you need it. Your worked-out lines list the
     roles you can claim without contradicting the public record…"), which is the current card, not a
     historical one. The report quotes a different sentence of the same card; both are the card as deployed
     2026-10-19.
  4. *Closed 2026-10-31 after the claims review:* the counter-claimant line's record
     (`gameplay/data/counter_claim_votes/README.md`) calls it a true fact dropped because it did not move
     votes toward the truth, likely through name order; it is in the page's notes, not on the page.
  5. **The Sentinel row's unit.** The README's "mech report 6/40 → 2/40" counts report-turn samples whose
     line states or relies on false watch/follow mechanics; the Level 1 calls these "its own report errors".
     The page keeps that wording with "lines relying on a false rule" in the table.

## Review resolution

Round 1 (first draft; editorial `review-editorial.claude.20261031T035101Z`, claims `review-claims.claude.20261031T0353Z`).

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 (blocking): the "without" arm's night record worked against the deduction, so the 2 → 8 comparison mixes the engine with a record repair, and the reader cannot tell what the high-thinking and larger-model runs saw | Fixed: §5 now states what each arm received before the table ("without" = engine off and the original record, "with" = the engine replacing that record and adding its lines) and that the model and thinking runs were all engine off with the original record (log §8 Result 2), so like for like with the 2 of 10 arm. §1's "every premise in front of it" stands: the record did say "roleblocked"; its "learned nothing" clause is what works against the step | §5 reread |
| E2 (worth fixing): two mechanisms (direct rules, the solver) but "shows the whole path" and "most lines come from the solver"; which stage produced each healer line unclear | Fixed: §2 opens with the two stages and places the healer's lines in the first (own result; join with claims), the solver introduced as the engine's centre. Claims F8 ("most lines" unsupported) and F11 (joins are not solver reruns) fixed in the same pass | §2 and §3 reread |
| E3 / claims F10: "one of three grades" vs the healer's second line, which is alternatives under a premise; "the reporter" ambiguous; the trailseer-honesty reason does not bear on naming player_7 | Fixed: §3 says the second line holds under the premise of two named claims and lists both branches because a second visitor is possible (catalogue AC1's reason); the grades sentence says a list of alternatives can sit under a named claim; the reporter-honesty point moved to notes | §3 reread |
| E4 / claims F2: the uptake figure before the replay and output-mode glosses; "taken up almost every time" from one turn | Fixed: §3 glosses "replay" and names the enforced mode at the figure; scoped to "one turn, but how the lines are meant to work, and a wrong certain line would be taken up the same way" | §3 |
| E5: "levels" collides with page levels; "Level 3" is jargon | Fixed: "eight kinds of line"; the linked page named by title (*The roleblocked healer*); §6 names the unfired kind in words | §2, §5, §6 |
| E6 / claims F13: the Sentinel and cover rows' measures undefined; the 40 report samples include a Trailseer's; arm C bundled a fix | Fixed: both rows now say what was counted and which direction is wanted; the Sentinel row says "a Sentinel or Trailseer reported its own result", "the gain on the Sentinel's turns", 8 report turns and 11 replies, and the bundled fix | §5 |
| E7: speaking reported as an effect while the engine gives no advice to speak | Fixed: §5's intro says why speaking is the wanted outcome on this turn (as played the healer passed all day holding the one fact that would have exposed player_7; log §1) | §5 |
| E8: hidden roles at death unexplained | Fixed: a clause in the seat's view ("unless a wolf concealed it"); the continuation rule says "concealed bodies" | §2 |
| E9 / claims F5: the dropped counter-claimant line opaque, and its record calls it a true fact dropped for not moving votes toward the truth (likely name order), not advice | Moved off the page to the notes with its record; it answers a different question (what a true line's form can do), and the outline's "moved votes toward the named seat" is not how the record reads. Open question 4 closed | §4 reread |
| E10 / claims F12, F1: "in each case the lines changed what the first speaker did" and "a substitute … on a step of this kind" overstate | Fixed: "moved in the intended direction, within those limits; the cover counts are a direction only"; "On this turn the engine stood in for …; whether it does so for other missed steps is untested" | §5 |
| E11: time per turn against cost per game in one breath; "$2.30" unit | Fixed: the two costs named as time and money, with "a game's ten seats at about $2.30 against $0.12" | §1 |
| E12 (taste): roles unglossed (trailseer, Investigator, lone killer); "player_3" | Fixed with a clause each | §2, §4 |
| E13 / claims F6: trait table "rather than written by hand" reads as derived from the engine | Fixed: "declared by hand and tested against the game engine's own behaviour" (report §3: a new role "is declared there") | §2 |
| Claims F3: the enforced-mode silence result needs its date; placed beside the live row it implies the mode explains the silence | Fixed: dated 2026-10-16, "only this one line added"; the §8 enforced re-run with the whole engine (5 of 10 spoke) recorded in the notes for the Level 3 | §5 |
| Claims F4: "the two changes cannot be separated" understates the bundle | Fixed: "revised evil cards with two engine changes and everything else committed between the two builds; the engine's share cannot be separated" | §5 |
| Claims F7: "never connecting" overstates; it reached "likely the chanteuse" in a private note that night | Fixed: "through all three of its turns that day … (it got there only in a private note that night, and never said so)" | §1 |
| Claims F9: the seat view holds no votes | Fixed: "the read-out wills" replaces "the votes" (schemas/deduction.py) | §2 |
| Claims F14: continuation rule excludes combinations | Fixed: "roles that together would have ended the game earlier" | §2 |
| Claims F15: authorship sentence unconfirmed; "the experiments" broader than the recorded "experiment choices" | Flagged for the owner (open question 1); wording left as the content plan's | — |
| Claims, not checked: no turn time recorded with the engine on in the live mode | §1's "at the live setting's speed" kept as the log's own reading (§8 "What it shows"); the engine's own runtime is milliseconds (report §4), but turn latency with the engine on was not measured. Noted here, not on the page | — |

Round 2 (revised draft; editorial `review-editorial.claude.20261031T0359Z`; claims round 2 recorded below when in).

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 (blocking): the enforced-mode replay told twice (uptake in §3, silence in §5) read as a contradiction with "spoke 7 against 3"; what differs between the runs unstated | Fixed: §3 keeps the rationale only (a line is copied into the notes, so the grade must survive the copying) and points to the results; §5's healer row reports the 2026-10-16 replay once, with what differs (output mode and the extra lines) and that the speaking gain cannot be attributed to either | §3 and §5 reread |
| E2 (blocking): the Sentinel row's label (a Sentinel denying a visit), count (false rules across Sentinel and Trailseer reports) and "the gain on the Sentinel's turns" did not match; "follow" and the bundled fix unexplained | Fixed: the label defines both observers and names the failing case; the count is one definition (false rules about these results) with "all of the fall on the Sentinel's turns"; the fix is "an unrelated input fix shipped with the lines" | §5 |
| E3: the solver gets the most explanation, but no replay row says which stage produced its lines | Fixed: §5 says the targeted lines come from the direct rules and that no replay isolates the solver's lines, whose checks are the code tests; the solver's four rule kinds cut to one sentence (a departure from the outline's "one sentence each", for the same reason) | §2, §5 |
| E4: the cost comparison in two places with the unit unclear | Fixed: §1 keeps the two ratios the outline asks for, as time and money with their units; the raw figures (17.4 s against 6.3; $2.30 against $0.12 for a game's seats) appear once, in §5 | §1, §5 |
| E5: three exclusive grades vs an example combining two; "holds on only some branches is not printed" seemed to contradict Alternatives | Fixed: the grade presented as two dimensions (certain information or a named claim; one conclusion or a complete list), with "a complete list is itself true in every legal game"; "a single conclusion that holds on only some branches" | §3 |
| E6: the uptake paragraph mixed rationale, experiment and risk | Fixed with E1 | §3 |
| E7: "82 samples" per arm or total; what a judge is | Fixed: "82 samples in each arm"; "classified by different model readers, so a shift can reflect the reader as much as the behaviour" | §5 |
| E8: cast, concealment and "ten seats / twelve roles" undefined; the seat's-view point buried | Fixed: the paragraph leads with "reads what the player's own prompt is built from, and never the hidden roles"; the cast defined as the set of roles dealt this game; the conceal in a clause | §2 |
| E9 (taste): "lone killer", "role card" | Fixed: "the solo evil seat"; "the role card, the seat's role instructions" | §4 |
| E2's probe (conflicting claims): the page does not say how joins treat claims that contradict each other | Not added: outside this page's scope; the reviewer called it acceptable. Noted for the Level 3 if it tells the joins | — |

Claims round 2 (`review-claims.claude.20261031T0402Z`):

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| C1: "cost, not necessity" rests on the 2026-10-30 check, two weeks after the build; stated generally | Fixed: §1 separates the two times: at the build, one step more thinking left the connection at 3 of 10 and a larger model was ruled out on cost; a later check on the same turn found high thinking or a larger model makes it alone, "so the engine is the cheaper route to this step, not the only one". The outline's framing (cost, not necessity) is kept, dated | §1 reread |
| C2: "none removed this failure" implies all three levers were tried on this turn | Fixed: "each helped elsewhere"; for this turn only the thinking step is named; the input repair's entanglement with the engine's line is in §5 and the notes | §1 |
| C3: rows 2 and 3 are not engine on against off | Fixed: the intro says only row 1 turns the engine off and the other two add a line to a running engine; the first column names what each row added; the header is "With the lines, against without" | §5 reread |
| C4: the cover row's adverse measure (catchable claims 0 → 3) left out under "moved in the intended direction" | Fixed: added to the row's limits cell ("seats departing from the line"); the closing sentence narrowed to "the counts named" | §5 |
| C5: "stood in for" implies equal results | Fixed: "closed most of the gap" (the log's wording) | §5 |
| C6: $2.30 is the cheaper larger model's cost, applied to both | Fixed in §1 ("on the cheaper of the two") and §5 ("a game with the cheaper of them in every seat") | §1, §5 |
| C7: the 2026-10-16 replay used an earlier wording, replacing the record, not "this one line added" | Fixed: "only an earlier wording of the first line in place of the original record" | §5 |
| C8: the card quote ends mid-sentence | Fixed: ellipsis | §4 |
| C9: authorship: "the experiments" reads as running them; the record supports choosing and directing them | Kept as the content plan's wording and flagged (open question 1); two reviewers suggest "the choice of experiments" or "experiment design" | — |
| Not checked (both rounds): turn latency with the engine on; whether $0.12 holds in the live output mode | Noted; "at the live setting's speed" removed from §1 in the C1 rewrite; the live-mode per-vote output rise (§9) is chapter 6's question | — |

No third run of either reviewer: the section structure did not change in round 2; the fixes relocated and reworded within sections, and each claims correction was checked against its source by the writer.

Departures from the outline: the four kinds of solver rule are one sentence, not one each; the counter-claimant line is in notes; both for length and because two reviewers found the detail did not carry the argument.

Check technical repairs against sources. A misunderstanding can identify a problem even when the
reviewer's proposed solution is wrong. Record material findings, not cosmetic bookkeeping.

## Trial record

Draft snapshots: `deduction_engine.first-draft.md` (before reviewer edits; 2,388 words of page copy) · `deduction_engine.reviewed-draft.md` (after two rounds; 2877 words, of which 617 in the three tables and 72 in the two quoted lines, prose about 2188) · owner revision when available. The guide is 1,200–2,000 including tables; the growth came from the reviewers' requests (what each arm received, the two production stages, defined measures in every results row, glosses on first use) and from the outline's three exhibits; the counter-claimant line and the solver's rule detail were cut to pay for part of it.
Model and owner interventions: drafting agent on the default model; outline approved in conversation 2026-10-31 (checkpoint satisfied before this run); reviewers run with the `claude` CLI per the skill. Parent excerpt: the Level 1's "Explore" line is not a markdown link, so `parent_context.py` finds no link; the editorial review was run from a patched copy of the runner (outside the repo) that supplies the same excerpt by matching the parent's "Compute selected implications" section. Nothing in `writeup/context_engineering/context_engineering.md` was edited.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
