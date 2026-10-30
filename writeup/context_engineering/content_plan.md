# Context engineering: portfolio content plan

Status: candidate plan, 2026-10-29, from a subagent pass checked against the record. The owner chose to keep the default recommendations for now and review all plans later; nothing here is approved. The open questions at the end stay listed; the defaults taken are below.

## Defaults taken (owner 2026-10-29: keep the recommendations for now)

- Section 1's lead: the Sentinel who conceded a false rule (the invented check is already Evaluation's Level 1 example).
- Candidate page 5 (prompting methods) is dropped as a Level 2 page; page 3 closes with a short pointer paragraph.
- The Group B intro goes on the overview page, above the group's chapter cards, reworded without "pre-registered".
- Section 3's lead: the compare-candidates sentence. No thinking-level number on Level 1 (it stays on page 3).
- No Level 3 on how the deduction engine is checked: Evaluation's `code_checks.md` already explains it; page 4 explains the algorithm and links there. The roleblocked healer is the one Level 3.
- Done 2026-10-29: Evaluation's factual-errors page no longer says the higher thinking budget was not adopted; that model runs at it by default. Links from Evaluation to pages 1–2 wait for Evaluation's reconcile pass.
- The human contrast sits in the intro only.
- The visit-wording replay (triage card 15) stays off page 4 until checked against `evidence/gameplay/data/visit_wording_ab/`.
- Headings name the four responsibilities; the Level 1 figure (what a player reads on one turn, five categories) is included.
- Revised 2026-10-29 after an outside review (owner approved): four responsibilities replace the diagnostic ladder; claim-ledger and healer wording corrected to the record; section 3 cut to one lead; a plain link to Memory, not the stale note; the figure grouped into five categories by author; the chapter-wide limit moved to the close.
- Card tags: Context engineering + Structured outputs and validation; Symbolic reasoning added once the owner is ready to explain the algorithm and its test limits.

---

Context engineering: what each agent is given, and how. A plan, not page copy. Read on 2026-10-29
against: `writeup/structure_proposal.md`; `writeup/map.md` (the model, page levels, blocks 30–33, 48–55,
68–72, 140–152, the factual-errors topic, lessons, the parked list); the two approved Level 1 pages and
their "Level 1 presentation" plans; `writeup/memory/memory.md`; `writeup/evaluation/factual_errors/`;
the writing prompt, `voice.md`, `page_types.md`; `writeup/skills_inventory.md`; `writeup/lessons/README.md`;
the reports `evidence/gameplay/turn_prompt/report.md`, `evidence/extraction/day_summary/report.md`,
`evidence/gameplay/deduction/report.md`, `evidence/gameplay/report.md` (problems 1 and 3), and
`evidence/gameplay/deduction/experiment_log.md` §2, §4–5 (where a claim needed it).

---

## 1. Frame

*Revised 2026-10-29 after an outside review, approved by the owner: the chapter is organised around four
responsibilities in preparing context, not a diagnostic ladder. Diagnosis explains individual decisions
inside each section; it is not the chapter's spine. The earlier ladder framing claimed each lever was
reached because the previous one left a class of failure. The record does not support that for the
chapter as a whole: the day summary also exists to keep prompts bounded and to give code fields to read
(`day_summary/report.md` §144), and conditional composition matters even when the facts are right.*

**The reader's question.** What does an AI player need to be given, and in what form, to keep the
facts of a game straight and reason from them?

**Central answer.** Each agent turn starts from an assembled context: the rules, the public record, its
private information, earlier discussion and its own notes. Context engineering decides what enters that
context (within what chapter 2 permits), how its sources are told apart, and what the agent is asked to
do with it. Four responsibilities organise the work:

1. **Make the relevant facts available and unambiguous.**
2. **Preserve earlier information without changing its meaning or its source.**
3. **Design and test how the agent is asked to respond.**
4. **Compute selected deductions the model would otherwise have to reconstruct.**

Throughout: code computes facts, the model keeps judgement.

**The shape chosen: one section per responsibility.** Each section leads with its design principle, then
one short case that shows why the responsibility needed real work (the failure that pushed the
decision), with its limit beside it, then the Level 2 link. The point is the subject; the case supports
it. Sections connect by what each responsibility covers that the previous one does not (facts the engine
holds → what exists only as talk → how the request is posed → what the model fails to infer), not by a
claim that each fix was forced by the last.

Why not the two references' shapes:
- **Not Evaluation's question subheadings.** Four sections need no grouping, and the responsibilities
  read better as one connected account of a context than as separate questions.
- **Not Game design's requirement pattern (need → human table → why a model call can't → what I
  built).** The human contrast is used once, in the intro, where it explains why everything must be in
  the prompt.
- **Not a diagnostic ladder.** The deduction report's §1 table sorts *different causes with different
  remedies*; it is not a sequence. One true piece of sequence stays, inside section 4: the engine was
  built after the input and prompt fixes, and that is what justifies its cost in complexity.

**One figure on Level 1.** *What one player reads on a turn, grouped by who wrote it.* Five categories,
not every block:
- engine-provided facts and private records (the rules, the game master's record, the board, the
  player's own night record);
- player claims, attributed to their speaker, with the record checks that apply;
- model-written accounts: the summariser's account of accusations, and the player's own note from its
  last turn;
- computed deductions, each worded with its condition;
- the current task and the response fields (reads → note → the move).
The colour key is the author, because that is the chapter's principle: facts come from the engine or are
checked by code; anything a model wrote is labelled as a claim or a note. Sources:
`turn_prompt/report.md` "A turn today" and its example; `day_summary/report.md` §3. The figure carries
*what*; the sections keep *why*. The cache boundary stays off it (chapter 6).

---

## 2. Sections in order

Word guides: intro 150–200; each section 90–130. Total about 650–750 words plus the figure. Limits sit
beside the example they qualify; the intro does not open by defending every result.

### Intro (no heading beyond the chapter title)

- **Question it answers:** what is being engineered, and how the chapter is organised.
- **Beats, in order:**
  1. Name the object: each agent turn starts from an assembled context (rules, public record, private
     information, earlier discussion, the agent's own notes). Context engineering determines what enters
     it, how its sources are distinguished and what the agent is asked to do with it. Familiar →
     specific: a human player hears the table, remembers earlier days and knows the rules; a model call
     starts each turn with only its prompt.
  2. Boundary with chapter 2 in one clause: chapter 2 decides what a player *may* know; this chapter
     makes what it may know usable.
  3. Why it needed work, in one or two sentences: players stated things the record contradicted
     (miscounted who was left, misread an ability, believed a summary's mistake). In the earlier
     nine-seat game about 3% of public messages held such an error; how errors were found and counted is
     in Evaluation (bridge).
  4. The four responsibilities as the frame for the parts, and the principle: code computes facts, the
     model keeps judgement.
  5. The figure.
- **Lead example:** none (the figure is the exhibit).
- **Group B placement:** the group intro is on the overview page. If needed here, one sentence: this
  chapter and Memory are the two ways I tried to improve play: what a player is given during a game, and
  lessons carried from earlier games.

### Section 1. Making facts available and unambiguous

- **Principle:** a fact that is present but easy to misread fails like a missing one. So the engine
  prints what a player would otherwise reconstruct from prose: who died and as what, the roles still in
  play, and the player's own night actions worded as its own act on a named night. The rules state what
  each ability observes, and rank above any player's account of a rule.
- **Case: the Sentinel who conceded a rule that was not true.** In every game of a four-game batch on one
  model, a player argued the Sentinel should appear in its own visitor list; in three, the real Sentinel
  conceded and was voted out. With the missing rule sentence in the prompt, the replayed Sentinel
  conceded 0 times in 10, against 10 in 10 before. Limit beside it: a replay of one game's turn; it shows
  the rule sentence removed this failure, not that misreadings are prevented. Source:
  `evidence/gameplay/turn_prompt/report.md` decision 4; `evidence/gameplay/discussion_evidence.md` §8.4;
  map block 144. Ties back to chapter 1 (partial observers made misreading an ability the commonest
  error; chapter 1 links here for the fix).
  - *Kept for Level 2:* the invented check (reworded, 20/20 → 0/20) as page 1's featured story, told from
    the cause side (Evaluation's Level 1 already tells it); the July board-and-reads bundle (48% → 30%).
- **Links to:** Level 2 page 1, "Making facts available and unambiguous".
- **Connection to section 2:** these facts are held by the engine. What players *said* on earlier days
  exists only as talk, and its account is written by a model, so it needs a different treatment.

### Section 2. Preserving earlier days without changing their meaning or source

- **Principle:** earlier information reaches a player with its source kept. One model call per day
  transcribes who claimed and accused what, attributed to the speaker, and never judges whether it is
  true. Code builds a claim ledger from fields speakers fill themselves and tests each claim against what
  the engine has made public; where the record fits more than one reading it says nothing, and a claim the
  record cannot contradict stays a claim. A player reads earlier days as labelled blocks in order of
  trust: the engine's record, the claims with their record checks, the summariser's account of the
  accusations. The summary also keeps prompts bounded as a game runs on (one clause).
- **Wording rule for this section:** the distinction is between *a faithfully recorded claim* and *an
  established fact*. Never "code checks every claim" or "code-checked claims" without saying against
  what; say "checked against the public record" (`day_summary/report.md` §3 item 2, §148).
- **Case: one summary line that decided a game.** The investigator said "I was roleblocked last night";
  the summary recorded it as the investigator claiming to be the Chanteuse, the role that blocks. Two
  players repeated it, the investigator accepted the false premise about itself, and was voted out 7 to 1;
  a lone killer won. The safeguard moved into code: speakers state their own claims in fields, and the
  ledger drops an action that can only have been done to the speaker. Limit beside it: the summariser's
  invention was too rare to recur in replays, so the code rule, pinned by a test, is the guard. Source:
  `evidence/extraction/day_summary/report.md` §7; `discussion_evidence.md` §8.4; map 71.
  - *Level 2 only:* when the summariser was asked to check claims against the record itself, every check
    it wrote was judged wrong (27 of 27), so checking left the model (`day_summary/report.md` §4, §6).
- **Links to:** Level 2 page 2, "Carrying earlier days forward: the day summary and the claim ledger".
- **Connection to section 3:** sections 1 and 2 decide what the context contains; the same context can
  still produce different answers depending on how the turn is asked.

### Section 3. Designing and testing how the agent is asked

- **Principle:** plausible instructions need testing. How a turn is asked (the instructions, the order
  of the answer fields, an example in the prompt) changes what the player does, and an instruction that
  reads well can help one case and break another. So every sentence that stays was replayed on recorded
  turns first. The section names the techniques only in passing; page 3 explains them (field order,
  example bias and the night-1 lot, conditional sections, thinking effort).
- **Case: a sentence that helped one case and broke another.** An instruction to compare candidates in
  each read helped where the evidence was strong (reads cited the decisive vote 11 times in 30, against
  2), but on the ballot it was written for, the Vigilante's vote for the real threat fell from 7 in 10 to
  0 in 10. It was not kept. Limit beside it: replays of selected turns, not a whole-game effect. Source:
  `turn_prompt/report.md` decision 9; `discussion_evidence.md` §8.7; map 150.
  - *Level 2:* the night-1 lot as page 3's featured story (seat 1 took 78 of 96 night-1 actions;
    shuffling the lists did not help; the engine's lot spread actions over all nine seats). The thinking
    level gets no number on Level 1.
- **Links to:** Level 2 page 3, "Testing how each turn is asked: instructions, answer order and thinking
  effort".
- **Connection to section 4:** with the facts present and the request tested, one kind of failure
  remained in the replays: the player had the facts and still missed the first step of an inference.

### Section 4. Computing selected deductions in code

- **Principle:** some conclusions follow mechanically from what a player is allowed to know, and a model
  may fail to reconstruct them. A deduction engine starts from the player's permitted view (chapter 2's
  boundary), narrows which roles each player could still hold by constraint propagation (simple
  elimination rules repeated until nothing changes), and writes its conclusions into the prompt. Each line
  carries its grade in its wording: certain; true if a named claim is true; or the full list of
  alternatives. That rule exists because injected text is taken up almost every time, so a wrong line
  would be a false premise in every game where it fires. It supplements selected reasoning; the model
  still decides what to say, whom to trust and how to act.
- **Why it came after the earlier work (the one true sequence):** it was built after input and prompt
  fixes, and more thinking, had been tried on these failures (`deduction/report.md` §1, "Why build this
  after trying prompts?"). That is what justifies its cost in complexity. Not "the inevitable last stage".
- **Authorship in one sentence:** the engine, solver included, was written by an AI coding assistant; my
  part was the requirement, the grading rule, the acceptance cases from real failures and the
  experiments. How its conclusions are tested is linked to Evaluation's code-checks page, not retold.
- **Case: the roleblocked healer.** Only the Chanteuse could block it, and a block is a visit; another
  player reported the Chanteuse's likely visitor, who admitted the visit. The healer wrote every premise
  into its notes and never connected them. With the certain step injected, all 10 replays recorded that
  the Chanteuse had visited (0 without it), 2 named the likely player, and none spoke. Limit beside it:
  uptake, not changed behaviour. Its own earlier note, "stay quiet unless addressed", re-read each turn,
  was investigated as an obstacle: with a neutral note it spoke 9 times in 20, against 3 in 30. So the
  note is one obstacle, not the whole cause, and the fix is open. Source:
  `evidence/gameplay/deduction/report.md` §2, §5; `deduction/experiment_log.md` §4–5; map 48, 53.
- **Links to:** Level 2 page 4, "Working out selected conclusions in code: the deduction engine"; its
  Level 3, "The roleblocked healer".

### Close

- **The chapter-wide limit, once:** no whole-game error rate was measured after these changes; each
  result above is a replay of selected failures.
- **A plain link to Memory:** chapter 4 is the other way I tried to improve play, lessons carried from
  earlier games. No suggestion that it addresses the stale note: within-game notes and cross-game lessons
  are different mechanisms.

---

## 3. Narrative check (the main points as one paragraph)

Each agent turn starts from an assembled context, and this chapter is about preparing it. First, the
facts the engine holds have to be there and hard to misread, so the engine prints the board and each
player's own night record, and the rules say what each ability observes; one missing rule sentence was
enough for a real Sentinel to concede a false rule and be voted out. Earlier days are different: they
exist only as talk, so a model transcribes them with each claim attributed to its speaker, and code tests
the claims against the public record without treating them as facts; one mis-transcribed line had cost a
game. With the content settled, how the turn is asked still changes the answer, so each instruction is
replayed before it stays; a sentence that helped one case broke a vote in another. Finally, where a
player had the facts and still missed the first inference, code works out selected conclusions, graded
by certainty in their wording; the player took them up, but taking them up did not by itself change what
it did. None of this was measured over whole games, and Memory is the separate attempt to carry lessons
between games.

Reads as one account of a context, with each case showing why its responsibility needed real work.

---

## 4. Level 2 pages, page 5, Level 3, and the Group B intro

### Level 2 pages

| # | Level 2 page | Why it deserves a page | Featured story | Main sources | Blocks |
|---|---|---|---|---|---|
| 1 | **Making facts available and unambiguous** | A complete diagnostic arc with its own fixes: the invented check (one line read as public news), the code review that found facts lost between engine and prompt, the board and reads bundle (the prompt's one planned comparison), the rules stated in full and their limit (a false rule players have already repeated is not undone by a correct one) | The invented check, told from the cause side: the line, the four variants, why the fix went into every game; Evaluation's page tells how it was found | `turn_prompt/report.md` decisions 1–4, "The board facts"; `discussion_evidence.md` §6.2, §8.4; `evaluation/factual_errors/report.md` step 1 | 49, 141, 142, 143 (own night record), 144 |
| 2 | **Carrying earlier days forward: the day summary and the claim ledger** | A distinct architecture (the model transcribes, code checks: generator-verifier separation) with a real exhibit (the "Previous days" section a player reads), a case where one line decided a game, regression replays of known failures, and an honest open gap (never compared with the raw transcript) | One summary line that decided a game (e06) | `day_summary/report.md` §1–8; `turn_prompt/report.md` decisions 3 (labelled blocks), 13 (claims as fields) | 68–72, 143 (labelled blocks) |
| 3 | **Testing how each turn is asked: instructions, answer order and thinking effort** | Several distinct decisions, each with its own evidence: answer order, example bias and the lot, conditional composition, what the prompt deliberately does not say, sentences tried and dropped, the thinking level as a lever on correctness; plus the method lesson (single cases swing by up to five in ten, so a one-game replay finds a local effect) | The night-1 lot: symptom, the obvious fix that failed, the engine's lot, the rule it set ("an example never names a legal answer") | `turn_prompt/report.md` decisions 5–12, 14 (as a gap), 15; `prompt_boundary/`, `prompt_claims_audit/` logs; `caching/experiment_log.md` §12, §16 | 145–150, 152 |
| 4 | **Working out selected conclusions in code: the deduction engine** | The chapter's one substantial algorithm with its own safety rule, verification and cost in complexity, why it came after the cheaper levers, and a bounded result (uptake, not behaviour) | The roleblocked healer, short; the full investigation on Level 3 | `deduction/report.md` §1–5; `deduction_catalogue.md` §0; `experiment_log.md` §2–6 | 48–55 |

Notes on the arrangement:
- **Labelled sources move to page 2.** The proposal put them on page 1; the three labelled blocks are how
  earlier days are presented, so they live with the summary and ledger. Page 1 keeps the player's own night
  record (the engine writes it).
- **The night-1 lot moves to page 3.** The proposal had it on page 1, but it is not a fact; it is about
  what a prompt's example and an undecided choice do to the answer, which is page 3's subject.
- **The board-and-reads bundle stays on page 1** (printing the facts alone did not stop the counting
  error, which is why reads were added); page 3 links back to it for the answer order.
- **Required fields and "no" as a value** (decision 11) stay chapter 1's output contract
  (`agent_turn.md`); page 3 gives it one sentence.
- **The shared-prefix layout** (decision 14): its cost case is chapter 6's. Page 3 keeps only what it cost
  in what the player reads first (the role card now after the transcript; the participation change; the
  unresolved vote lead, entangled with thinking level) as a gap, with a link to chapter 6.

### Candidate page 5 ("Prompting methods across the project's model calls"): recommend no page

- The owner ruled on 2026-10-27 that cross-project lessons get no page; each instance is told in its own
  chapter (`writeup/lessons/README.md`). A methods overview is that kind of synthesis.
- Its content already has homes: directional lean, presentation order and action-space reduction in the
  dedup prompts are told in chapter 4's Level 3 "How the deduplication judge was built" ("What moved the
  judge's accuracy"); rubric design and narrow judge questions in Evaluation's LLM-judges page;
  generator-verifier separation on page 2 here and in chapter 4's extraction page.
- As an overview it would be a catalogue linking out, repeating numbers from three chapters on different
  models and eras: the failure the Level 1 principles warn against, moved to Level 2.
- **Instead:** page 3 names each method where it is demonstrated (field order, example bias, conditional
  composition), and closes with one short paragraph pointing to the same patterns in other calls (chapter
  4's dedup judge for order and the "when unsure" lean; Evaluation's judges for narrow questions). The
  "prompt engineering" tag on the chapter card points at page 3.

### Level 3 candidates

| Candidate | Verdict | Anchor (Level 2 subsection) | Reader question | What it adds | What stays on Level 2 |
|---|---|---|---|---|---|
| **The roleblocked healer** | Selected (proposal) | Page 4, "what changed in the agents" | When a computed conclusion lands in the notes and the player still does not act, what is stopping it? | The before/after night-record line; the uptake table at two thinking levels; the 2×2 on the note against the role card; that speaking did not mean reasoning well; the placement screens. Optionally the investigator's vote case with the moderator line (a code bug fixed separately) | Uptake 0/10 → 10/10, 2/10 named, 0/10 spoke; the stale note as one obstacle investigated (9/20 spoke with a neutral note, against 3/30); no whole-game effect |
| How the deduction engine is checked | Possible; owner's call | Page 4, "checking a conclusion before a player reads it" | How do you check an engine whose wrong line would be a false premise in every game? | Oracle against exhaustive search, random nights through the real engine, trait-flip test, acceptance cases with a "must not say" sentence | The safety rule and that coverage is not proved. Interview risk: AI-written code; the owner's claim is the test design |
| The night-1 lot | Not needed | — | — | Fits as page 3's featured story | — |
| The invented check; the e06 summary line | Not needed | — | — | Evaluation's factual-errors page tells both; pages 1 and 2 tell the change | — |
| Layout or thinking level? (the vote lead) | No | — | — | Unresolved; a gap line on page 3 | — |

### Where the Group B intro lives

Recommend: **on the overview page, as two or three sentences above the Group B chapter cards**, not on
this page.
- Groups are headings with no page of their own (Evaluation's precedent: question subheadings are
  headings only). Every Level 1 page must stand alone; the memory chapter's Level 1 does not mention the
  group either.
- This page carries only its own half in the intro (two of the three approaches are here: give the
  information, compute the inference; their results differ: replay fixes against uptake) plus the
  one-sentence pointer to chapter 4.
- The proposal's wording needs one change wherever it lands: "a pre-registered self-improving loop" →
  plain words ("a self-improving loop, tested against a measure chosen in advance, that did not
  compound"), per the owner's rule against research terms on pages.

---

## 5. Disposition of every source

| Source | Where it goes |
|---|---|
| `turn_prompt/report.md` "The problem" (block 140) | L1 intro; page 1 opening |
| "A turn today", "The order of the prompt", the example | L1 figure; page 1 exhibit (board lines, night record); page 3 (answer fields) |
| Decision 1, board and reads (142; July `validation/` T1–T3, T1c) | Page 1 (the bundle); page 3 links back for reads-before-action |
| Decision 2, results worded as own action (141) | Page 1 featured story; L1 alternative lead; Evaluation tells the finding |
| Decision 3, the code review, own night record, labelled blocks (143) | Split: own night record and the 12 lost facts → page 1; labelled blocks → page 2 |
| Decision 4, rules in full, ranked above claims (144) | Page 1; L1 lead (Sentinel); the illusionist case as its limit |
| Decision 5, the night-1 lot (146) | Page 3 featured story |
| Decisions 6–7, suspicion cues removed, tactical advice audited (148; `prompt_boundary/`, `prompt_claims_audit/`) | Page 3, one subsection "what the prompt does not tell the player" |
| Decision 8, per-turn briefs (145) | Page 3 (conditional composition) |
| Decision 9, sentences tried and dropped (150) | Page 3; L1 lead (compare candidates) |
| Decision 10, field order (147) | Page 3; chapter 1's `agent_turn.md` links here |
| Decision 11, required fields | Chapter 1 (output contract); one sentence on page 3 (the verdict example copied onto 426 turns belongs with example bias) |
| Decision 12, numbered memory items, memory instructions only when shown | Page 3 (conditional composition); numbering one clause |
| Decision 13, claims as fields | Page 2 |
| Decision 14, shared-prefix layout | Chapter 6 (cost); page 3 gap (what the player reads first; the vote lead) |
| Decision 15, thinking level (149) | Page 3; one study, also the first lever in page 4's "why after" (tell it once, link) |
| "How it is checked" (151) | Each page's verification: goldens and layout tests → page 3; the bench → Evaluation's factual errors (link) |
| "What is not established" (152) | L1 intro caveat (no rate, no whole-prompt comparison); page gaps |
| "When to revisit the design" | Stays in evidence |
| `turn_prompt/experiment_log.md`, `validation_plan.md`, `validation/` | Evidence links (provenance) |
| `day_summary/report.md` §1–2 (68) | Page 2 opening |
| §3–4 (69), the "Previous days" exhibit | Page 2 core; L1 figure |
| §5 (runtime, rescue model, raw-transcript fallback) | Page 2 one paragraph; the rescue model is chapter 7's |
| §6 checks (70): bench results, regression replays, stronger-model test | Page 2 verification; the 27/27 record checks as design evidence |
| §7 e06 (71) | Page 2 featured story; L1 lead |
| §8 gaps (72) | Page 2 gaps |
| `day_summary` May-era files (`prompt_versions/`, `eval_*`, `regen_comparison.json`) and the five-dimension judge | Evidence only; the judge's story is Evaluation's (LLM judges) |
| `deduction/report.md` §1 (48), §2 (50), §3 (51), §4 (52), §5 (53–54), gaps (55) | Page 4, in that order; §5's healer → L3 |
| Block 49, facts on the payload as data | Page 1 opening principle |
| Block 54, evil covers (the engine's half) | Page 4 short subsection; chapter 1 owns the evil contest; L1 one clause at most |
| `deduction_catalogue.md` and its three reviews | Evidence (the three grades come from catalogue §0); reviews not on pages |
| `deduction/experiment_log.md` §2 (thinking), §3 (stronger summariser), §6 (rewritten note) | Page 4 "why after the cheaper levers" (one table); §2 also page 3 |
| §4–5 (R1, the healer) | L3 |
| §7 and the case register (R9–R14) | Evidence; R11 (rule sentences recited as arguments) → page 1 gap line |
| `deduction/live_e79f21d7/review.md` | Evidence only (a diagnosis and prompt revision; not needed) |
| `gameplay/report.md` problems 1 and 3 | Sources for the intro framing and the cause table; problems 2, 4, 5 are chapter 1's |
| `discussion_evidence.md` §6.2, §6.4–6.7, §7.5, §8.4–8.7 | Sources per page, as cited above |
| Triage card 10 (errors spread between agents) | Page 1 limit (a correct rule does not undo a false one already repeated); page 2 (a summary line is every player's input) |
| Triage card 15 (visit-wording A/B: wording not the cause; engine lines cut the Sentinel's own report errors 15% → 5%, replies stayed 31%) | Candidate second instance on page 4 of "the first speaker, not the replies"; **verify against `gameplay/data/visit_wording_ab/` first**: it is not in the deduction report |
| Map blocks 30–33 (dedup prompts) | Chapter 4 (already told in `memory/store_upkeep/dedup_judge.md`); page 3 points there |
| Lessons 15, 16, 80 | No page (owner ruling 2026-10-27). Lesson 16 is this chapter's principle, stated in plain words in the intro, not as a cross-project lesson |

---

## 6. Bridges

- **Chapter 2 (information boundaries).** Ch2 decides what a player may know and enforces it at the
  payload; ch3 makes what it may know usable. Intro: one clause. Page 4: the engine starts from the
  player's permitted view, the boundary chapter 2 enforces (link). Ch2's Level 1 names the engine's view
  as built from the payload; ch3 owns what the engine computes from it.
- **Evaluation (chapter 5).** Evaluation owns how an error was found, frozen and counted (the census, the
  invented check found by playing, turn replays, the judges, regression checks); ch3 owns why it happened
  and what changed. Intro: "how these errors were found and counted is in Evaluation". Page 1: "how the
  invented check was found and frozen" → Evaluation's factual-errors page. Every page that cites a replay
  links Evaluation's "Choosing between turn replays and whole games" once. Evaluation's factual-errors
  page should link pages 1 and 2 for the changes (reconcile item, open question 7).
- **Chapter 1.** Inbound links ch3 must host: field order (from `agent_turn.md`) → page 3; rules stated in
  full, the fix for misreading partial observers (from `evidence_design.md`) → page 1; the covers line
  (from `evidence_design.md`) → page 4; the claim field and the ledger, and the fixes to the shared
  records (from ch1's content plan, change 3) → page 2.
- **Chapter 4 (memory).** L1 close: one pointer sentence. Page 3: memory instructions and verdict fields
  appear only when lessons are shown; the field-order finding came first from the memory adoption field;
  the dedup judge's order and lean findings (link). Page 2: the summary is not memory (within a game,
  never stored across games).
- **Chapter 6 (cost).** The shared-prefix layout's cost case; the thinking level's cost (a game about
  twice as expensive at the higher level); the reads' added output. Ch3 states each trade-off in a clause
  and links; ch6 owns the numbers and the layout.
- **Chapter 7.** The summary's rescue model and raw-transcript fallback; prompt captures (how we know
  what a player saw). Links only.

---

## 7. Claims to handle with care

- **The invented check.** "Rewording the results removed it in all 20 replays" is supported. Not "the
  wording, not the reasoning": the rewording changed two things (the night dating and "you checked"),
  and no variant varied the reasoning. Removing the previous note alone did not help in these samples.
  One turn of one game, not a rate.
- **The ~3% rate** is the earlier nine-seat game (July census; floors, since the sweep missed some). Never
  the 0.14% rate. No ten-seat rate exists; never imply errors are now rare as a measured fact.
- **Replays** estimate the response on selected cases, not effect size across games. 20 samples of one
  turn are not 20 situations. Single cases moved by up to five in ten on small wording changes.
- **The July bundle (48% → 30%)**: selected error-prone contexts, one sample each, judged by the census's
  model reader; vote turns were rebuilt with the vote's own result in view; the bundle does not separate
  the board from the reads. Describe the fixed measure as "the question was fixed before the second run",
  never with research terms.
- **Deduction lines: uptake without changed behaviour.** 0/10 → 10/10 notes; 2/10 named the player (low
  thinking level arm); 0/10 spoke. The neutral-note screen: 9/20 against 3/20 (p = 0.08 in that run; 0.007
  pooled with the earlier cell): "suggests", a small screen. No paired town-side whole-game comparison.
  The wolves' 3/8 games bundled card text with cover lines and cannot be split. Cover-line counts were
  labelled by different judges per arm: exploratory.
- **Verification wording.** Say "checked", never "proved": block 52's "soundness is proved" overstates;
  the report says tests do not establish every interaction, and the 150-game census against the oracle is
  "not a completeness proof".
- **Authorship.** State the engine (solver included) as AI-written, with the owner's part named. Never
  mention test authorship either way (the reports' "largely AI-written, not audited" line stays off).
- **Thinking level.** A setting that "reported no reasoning tokens" is not "the model did no reasoning".
  The faster model runs at the higher level today (catalogue seed: `turn_thinking="medium"`); the default
  player model runs every turn at the lower level, and votes at the higher level is an open decision. The
  thinking study appears in sections 3 and 4: it is one study, tell it once.
- **e06.** The summariser's invented claim did not recur in 10 replays before or after; the code rule,
  pinned by a test, is the guard. The "5 of 5 → 0 of 5" figure is the later speakers repeating the claim
  in replay with the fixed ledger (`discussion_evidence.md` ~line 1796), not the summary itself. Keep
  the two apart.
- **27 of 27 record checks wrong** were judged by a model reading against the transcript and the record:
  "judged wrong".
- **Field order.** Do not call it chain-of-thought or claim it changes internal reasoning (skills
  inventory). The May evidence partly rests on 1–5 judge scores (4.00 → 4.38), the kind Evaluation's own
  judges page says could not rank versions: avoid those numbers; prefer counts (verdict coverage 0.27 →
  0.97 by code; Haiku order kept 15/24 → 24/24, which is compliance, not quality). Today's order is
  untested for message quality.
- **Correlations stay correlations**: the wolves' blend line (38% vs 25% of games, r = +0.16).
  Tone-policing 20% → 10% was confounded with an easier board; kept on principle.
- **Participation** under the new layout (53–54% vs 20–35%) is not better discussion.
- **The moderator closing line** fix removed a wrong statement; it is not an engine effect on votes
  (9/25 → 5/25, suggestive).
- **No model family names** in the narrative; exact models in source notes. The Sentinel lead says "one
  model".
- **No research terms** on pages ("pre-registered", "power"); describe the practice plainly.
- **Faults as caught and fixed**: the self-block rule's first, broader version dropped a true Vigilante
  claim and the replay caught it before it shipped; tell it that way, scoped, on page 2.

---

## 8. Open questions for the owner

1. **Section 1's lead example.** The Sentinel concession (recommended: fresh, pushed the design), the
   invented check (strongest, but Evaluation's Level 1 already tells it with the same numbers), or the
   July bundle?
2. **Page 5.** Agree to drop it as a Level 2 page, and point page 3's closing paragraph at chapter 4's
   dedup judge and Evaluation's judges instead?
3. **Group B intro.** On the overview above the group's cards (recommended), or on this page's intro? And
   the reworded memory clause without "pre-registered".
4. **Section 3's lead.** The compare-candidates sentence (recommended: shows the method) or the night-1 lot
   (continues the story Evaluation's Level 1 leaves at the failed shuffle)? Should the thinking level get a
   number on Level 1, or stay a stated point with numbers on page 3?
5. **Optional Level 3 "How the deduction engine is checked".** Worth it given the AI-written code and the
   interview risk, or leave the checks on page 4?
6. **Settled 2026-10-29: a plain link to Memory.** *Was:* **The closing bridge.** Close on the healer's own stale note as the cause still open ("what an agent
   carries forward"), then point to Memory? It is thematic, not causal; keep it, or use a plain pointer?
7. **Evaluation reconcile.** `writeup/evaluation/factual_errors/factual_errors.md` says the higher thinking
   budget (82 → 27 of 267) "was not adopted for live play", but the model it was tested on runs at that
   level today (`Agents/llm_factory/catalog.py`, `turn_thinking="medium"`; `turn_prompt/report.md`
   decision 15). It also needs links to pages 1–2. Fix in Evaluation's light reconcile pass?
8. **Human contrast.** Use it once in the intro only (recommended), or also in section 2 (a human table
   remembers earlier days and corrects itself aloud)?
9. **Triage card 15** (engine lines cut the Sentinel's own report errors, replies to it unchanged): include
   on page 4 as the second "first speaker, not the replies" instance after checking it against its data?
10. **Headings.** Statement headings in plain words, as drafted, or Game design's gerund style ("Giving
    each player facts it cannot misread")? The figure on Level 1: yes or no?
