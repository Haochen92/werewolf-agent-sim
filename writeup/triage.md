# Triage of the remaining evidence folders

Prepared 2026-10-22 for the owner's ruling. **Rule from the table;** open a card only where you
doubt the call. A card gives the question, what was found (with N), whether it is in today's design,
how sure, overlap with filed blocks, and candidate blocks. The appendix (every finding, and every
file accounted for, checked by a script against the folders) is for checking, not reading.

Calls lean toward KEEP on purpose: a folder is SKIP only if nothing in it shaped today's design or
adds a skill no filed block carries. MERGE means its one useful line goes into a filed block or
another folder's walk. Large folders are split into one card per sub-study. `evaluation/` rows
come last, as in the walk. Calls: 19 KEEP, 36 MERGE, 10 SKIP.

| # | Folder | Card | Call | What it would give, and why |
|---|---|---|---|---|
| 1 | `extraction/tell_extraction` | — | **MERGE (final check, accepted 2026-10-22)** | Design · A miner that sees the roles proposes behaviours that hint at a role, a separate role-blind detector marks who showed them in other games, and code joins the roles and counts; Case study · New wordings never stopped arriving (about 16 a game after review), so the checklist was capped at 48 per channel and duplicate judgment moved from every game to a batch every ten games; Verification · The detector was checked on 40 model-labelled cases and by a two-phase blind owner protocol (7 of 8 upheld), though only 1 of 6 owner games was done — *Tells are off and changed nothing in today's design. The role-blind detector is already lesson 15's instance and the split calls are already lesson 80. The two-phase blind owner protocol becomes a clause in 93 (both pool candidates and hide the source; only 1 of 6 owner games was done). "No plateau" becomes a clause in card 47's block.* |
| 2 | `fine_tuning/agent_dialogue` | Plan to fine-tune a cheap dialogue model | **SKIP** | no block — *It shaped nothing in today's design and shows no work the owner could defend in an interview.* |
| 3 | `fine_tuning/cross_encoder/dedup_prefilter` | Cross-encoder dedup prefilter, held and never wired | **MERGE INTO block 26** | Case study · A cross-encoder that reads both texts together still scored "lead the accusation" and "avoid leading" as duplicates (one clause plus the example in block 26). — *It adds one example and nothing to today's design. Fix the "deployed" note before anything cites it.* |
| 4 | `fine_tuning/cross_encoder/reranker` | Small trained reranker matched the LLM reranker | **NOTES ONLY (owner 2026-10-22)** | Verification · A 22M model trained on these labels matched the LLM reranker (0.882 vs 0.871, ranges overlap) for free, but was never wired in.; Gaps · A majority vote of models gave more credit than the careful labellers on 28% of items, and the human check was designed but never run. — *Kept in interview_prep/engineering_practices.md; the final check had it as one block (the only trained-model result), with the label-vote bias and cards 5–6 as clauses, but the page brief keeps fine-tuning out of the main story.* |
| 5 | `fine_tuning/dedup_classifier` | Small dedup classifier lost; agreeing models misled | **MERGE INTO golden-set construction** | Verification · Three agreeing models were wrong on 21% of unanimous discards, so labels were auto-accepted only on the side where the models were reliable.; Gaps · A fine-tuned 4B model could not match the API model (69% vs 83%), so the decision stays a model call. — *The labeller-bias finding is a skill no filed block carries. The training runs shaped nothing.* |
| 6 | `fine_tuning/embedding` | Seven embedder fine-tunes, none helped dedup | **MERGE INTO block 26** | Case study · Fine-tuning raised triplet accuracy 44% → 68% but shrank the duplicate–distinct gap 0.028 → 0.008, so the ceiling was not the model's fault (one clause in block 26). — *At most one clause; anything more repeats block 26.* |
| 7 | `fine_tuning/memory_selection_bandit` | Reinforcement learning rejected, per-lesson outcome score proposed | **SKIP** | Optional: Problem · one sentence in credit, "RL was considered and rejected: it needs thousands of paid games and retrains on every rule change." — *The idea that survived is already told, from the code, in the credit topic.* |
| 8 | `game_play_enhancement` | the premise check and Phase 1 | **KEEP, 1 block (final check, accepted 2026-10-22)** | Problem · Day talk was thin because one exact source went uncontested: town accusations resting on a claim hit evil 34 of 35 times, and no evil seat ever claimed a role; Case study · An invented investigator check came from the result wording, not the seat's note: 20 of 20 with the old wording, 0 of 20 with 'you investigated', and removing the note changed nothing; Case study · Vote misquotes resisted every prompt fix because the seats did no reasoning at all (0 reasoning tokens on 'minimal'); the 'medium' setting cut bad samples from 31% to 10% — *[page: the ten-seat redesign's Problem block, with card 36 as its second instance] New point: the premise was checked on 28 old games before building. Talk was thin because one exact source went unchallenged (34 of 35), and that led to the ten-seat roles; card 10's "several imperfect sources" is this block's answer. The invented-check replay becomes a clause in 53 (same input-ablation method). Zero reasoning becomes a clause in 96 (31% → 10% bad samples at 2.4× cost) and is already the caveat in 61, 67 and 72.* |
| 9 | `game_play_enhancement` | Phase 2, the day with rounds | **KEEP, 1 block (final check, accepted 2026-10-22)** | Design · The day with rounds: an opening for everyone filtered by an allow-list of statement kinds, a closing defence for the most-accused, and a one-at-a-time sweep of quiet players behind a repeat gate; one missing accusation tag can still silence an accused player; Case study · The rounds turned an investigator claiming in the opening into a certain lynch (3 of 3 games, 7–1), which led to the ruling that held lines count for nothing; Case study · With no evidence the model picked the lowest seat number, a shuffle still left 95 of 96 choices on it, and only a default drawn by lot worked — *[page] New point: positional bias. The model follows the seat number, not the list order: a shuffle left 95 of 96 picks on the lowest seat, and only a lot drawn by code worked. Block 51 and lesson 16 only use this, they never show the diagnosis. Card 33's 426 copied "lesson 1" verdicts and the example-named player_2 (40 tags vs about 8) join as clauses. The day with rounds and the lynch chain go into card 46's scheduler block.* |
| 10 | `game_play_enhancement` | Phase 3, the ten-seat roles | **KEEP, 1 block (final check, accepted 2026-10-22)** | Design · The ten-seat rules give several imperfect sources of information, and evil muddies them by blocking or concealing, so engine results stay true; Case study · The sigil's 'immune' result named the serial killer in one step and came before 3 of its 6 lynches; once merged with a quiet night, the serial killer won both games a sigil landed on it; Verification · An error audit by kind (invented facts 2 in about 345 lines; summary errors 22; wrong ability deductions 28) and replays with controls showed most remaining errors are the model's limit; stating a rule stops the first misreading, not a cascade, and a literal model exposed unwritten rules — *[page; also multi-agent orchestration if that topic forms] New point: errors spread between agents. Stating a rule stops the first misreading but not one already in the shared transcript (Flash 10 → 4 of 10 cascade turns; Flash-Lite 10 of 10 throughout); no filed block covers spread between agents. Card 15's 15% → 5% vs replies stuck at 31%, and card 11's visit cascade, are its other instances. The error audit by kind becomes a clause in 48; the literal reader becomes a clause in 96; the role design goes to card 8's block.* |
| 11 | `game_play_enhancement` | the first Haiku game (§8.6–8.7, `haiku_*` data) | **MERGE (final check, accepted 2026-10-22)** | Case study · A sentence asking seats to compare candidates was not adopted: the vote it targeted fell from 7 of 10 right to 0 of 10, because seats said nothing separated the players and abstained; Gaps · Day-4 control votes went from 25 to 20 to 13 of 30 right across three code versions, and citations of the decisive ballot fell from 19 to 2; the shared-prefix layout is suspected but unresolved — *The vote-record drop (25 → 13 of 30 right) becomes a clause in 8 and 12: it qualifies 8's "no detected quality change". The compare sentence becomes an instance under 31 (an escape option invited abstention). The visit-direction fix goes to card 10's block.* |
| 12 | `game_play_enhancement` | persona voices | **KEEP, 1 block (final check, accepted 2026-10-22)** | Case study · A rewrite call read better but changed something a listener could act on in 19 of 90 lines, and the code fact check caught 1, so it was rejected; one voice line in the seat's prompt read more natural without moving stance beyond sampling noise and was adopted — *[page: an evaluation point (compare against the noise floor)] New point: A rewrite that read better changed something a listener could act on in 19 of 90 lines, and a code check caught 1. The voice line was adopted because its stance moved no more than two plain replies differ (30% vs 30%). No block shows a rewrite judged against that noise baseline.* |
| 13 | `game_play_enhancement` | silence calibration | **MERGE into card 46's echo-gate block (final check, accepted 2026-10-22)** | Case study · Seats could not sort their own lines by rule text (lines from passed turns were worth hearing 57% of the time, posted lines 52%), so the sorting moved after the draft to a gate that held 12 of 29 restatements and 0 of 36 worthwhile lines — *Its 12 of 29 restatements held vs 0 of 36 worthwhile lines are that block's current numbers. "A seat can't sort its own lines" is the same point as card 46 S7.* |
| 14 | `game_play_enhancement` | evil covers and the counter-claim line | **MERGE → 54** | no block — *It is already filed as block 54, so it adds nothing new.* |
| 15 | `game_play_enhancement` | the visit-wording A/B | **MERGE (final check, accepted 2026-10-22)** | Case study · Swapping the 'visit' wording changed nothing, so the wording was not the cause; two deduction lines stating the conclusion cut the sentinel's own report errors from 15% to 5%, but replies stayed at 31% because the dispute was already in the transcript — *Own reports 15% → 5% while replies stayed at 31% is an instance in card 10's spread block. A56/E19 are engine lines (50–53). Cheaply falsifying a hypothesis is already shown by 92.* |
| 16 | `generation_prompt` | the prompt's evolution | **MERGE into 32 (final check, accepted 2026-10-22)** | Design · The output format is part of the prompt: fields are written in their listed order, so a field placed before the action is reasoning done first, and every field is required, never optional — *An index is not a block. "The field order is the reasoning order" is block 32's point, and the seat output is one more instance.* |
| 17 | `generation_prompt` | removing tactics from the role text | **MERGE into card 18's block (final check, accepted 2026-10-22)** | Design · The prompt says how to talk and what the rules are, and memory decides what signals mean; removing tactics from role text halved tone-policing messages (24 of 119 → 8 of 79) as corroboration — *Removing the tactics is card 18's fix. Its own numbers come from 2 unpaired games with an easy board.* |
| 18 | `generation_prompt` | testing the tactics that were left | **KEEP, 1 block (final check, accepted 2026-10-22)** | Problem · A tactic written into the prompt becomes a lesson in memory: 'let consensus build' made investigators hide confirmed finds, memory extracted 'build a case gradually' from that play, and fed it back — *[page] New point: A tactic written into the role prompt gets played, extracted and fed back by memory: investigators hid confirmed finds and memory learned "build a case gradually". Each prompt claim was tested against outcomes (blending held, 38% vs 25%), which gave today's neutral role text. 95 names the hiding only as a concern; card 17 joins here.* |
| 19 | `generation_prompt` | pre-registered tests of the July board layer | **KEEP, 1 block (final check, accepted 2026-10-22)** | Verification · A 50-game error census with recall guaranteed by code (a cheap model reads, a stronger one rechecks, the owner checks) found about 3% of public messages and 4% of private notes misstate a fact; Case study · Showing the answer did not fix it: with a correct roster in the prompt, agents still hunted 'the remaining wolf'; Verification · The ship test, with its main measure restated after run 1 and confirmed on fresh cases, cut errors on error-prone turns from 48% to 30% — *[page; candidate anchor of a hallucination topic] New point: the error census. Code finds every candidate so recall is guaranteed in scope, a cheap model reads, a strong model rechecks, the owner checks: about 3% of messages, 4% of notes. "Showing the answer did not fix it" becomes a clause in 48. The ship test becomes a clause in card 59's bench block (pre-registration with an amendment is already 66).* |
| 20 | `memory_system/ablation` | Do lessons add anything beyond observations? | **SKIP** | no block — *A judge-scored null whose decision was reversed; nothing in today's design comes from it.* |
| 21 | `memory_system/augmentation` | Re-mining games to fill thin memory cells | **SKIP** | no block — *A parked tooling probe whose result shaped nothing.* |
| 22 | `memory_system/effectiveness` | the `v5_0` paired A/B (hub `report.md`, `paired_ab/` main arms, the pilot, the pre-rebuild batches) | **KEEP, 1 block (final check, accepted 2026-10-22)** | Verification · On 30 paired boards, town decisions improved (healer saves 37% → 60%, correct lynches 47% → 64%), but the town win rate rose 27% → 43% without significance; the quoted '+17pp p=0.013' fuses two arms; Case study · Model drift doubled the memory-off town's wins overnight (27% → 51%), and the model alias cannot be pinned, so baselines are re-run alongside each arm; Design · The stock wolf-blending metric only counted days a wolf died, so it sampled disasters; the unconditioned version validates — *[page: beat 1 of the memory story] New point: the June paired result. Town decisions improved (saves 37% → 60%, lynches 47% → 64%) but wins were not significant, and the fused headline is corrected; no block holds this memory beat. Drift goes to card 37. Seeding the deal by game id becomes a clause in 65. The wolf-blend metric that only counted disaster days goes to card 35's block.* |
| 23 | `memory_system/effectiveness` | net-first outcome framing and the town regression | **MERGE (final check, accepted 2026-10-22)** | Design · The outcome horizon is chosen per role: the end-of-game verdict first for the wolf, the killer and the investigator by day, the immediate result first for town roles; Case study · One fix, predicted in writing beforehand to help the killer and not the wolf, did exactly that in direction (killer lynched 80% → 63%, wolf blending flat) — *The per-role outcome horizon becomes a clause in 75 (extraction rules). Reasoning before the action becomes an instance in 32. Pre-registration is already 66, and every result here is direction only at N = 30.* |
| 24 | `memory_system/effectiveness` | `decision_replay/`, the cheap screening layer (2026-06-13 to 07-02) | **MERGE (final check, accepted 2026-10-22)** | Design · A screen that freezes one recorded decision, swaps only the memory block, regenerates the action and scores it by code, at about $1 a question, built to rule out cheap fixes before paying for whole games; Case study · Pooling hid where memory helps: pooled from day 3 it did nothing (−0.006), but split by day it helped on day 2 (+0.078) and in the endgame (+0.117) — *The $1 frozen-decision replay is rung 1 of card 26's instruments ladder line; its method is already 53 and 70. "Pooling hid the day-2 effect" becomes a clause beside 82's stratification. The retired proxy becomes a clause in 79.* |
| 25 | `memory_system/effectiveness` | `v6_sp_ab/`, the v6 store A/B and the lessons channel (2026-06-15 to 06-17) | **MERGE (final check, accepted 2026-10-22)** | Verification · A lesson's 'follow' verdict really changes the action: seats following an 'abstain' lesson abstained 77% of the time, against 32% at baseline; Problem · Lessons were followed faithfully but play did not improve (63–66% right against 69% at baseline), because they copied the town's own weak play — *Follow changes the action (77% vs 32%) becomes a clause in 60, a behavioural check of the same "followed" claim. "Followed but no better, because it copied weak play" becomes a clause in 56 and a spine beat.* |
| 26 | `memory_system/effectiveness` | `day_replay/` | **MERGE → instruments topic, one Gaps line** | Gaps · The middle rung of the evaluation ladder (one day replayed live from a frozen start) is designed but not built; it is the tool for judging discussion changes by their effect on votes, since a per-turn replay keeps the old talk in its transcript. Frame with the three-rung table (per turn / per day / whole game) — *Unbuilt, so no block of its own, but it names a real gap: changes to how seats talk spread within a day, which the per-turn screen cannot see and whole games see only through deal noise (owner 2026-10-22).* |
| 27 | `memory_system/store_progression.md` | Eight store versions told as one story | **KEEP (as the spine, not as a source of numbers)** | Organisation · the spine of the memory section: each iteration told as problem → what we tried → how we found out → what it revealed — *It is the only telling of how the memory evolved and how each problem was found, and the landing page's "Read the case study" links to it today; cite every number from the primary folders, and its stale lines (the fused "+17→+33pp" headline, compounding "open", no July result) carry a dated correction note until the write-up replaces it (owner 2026-10-22).* |
| 28 | `memory_system/strategy_adoption` | Phase 1, the adoption report (May 2026, pre-rebuild game) | **MERGE (final check, accepted 2026-10-22)** | Design · Each shown lesson gets a numbered verdict (follow, override or not relevant) before the action; moving that field first raised judged report accuracy from 4.00 to 4.80 and action quality from 3.97 to 4.67; Gaps · The judge these numbers rest on was never checked against human labels; a protocol to choose judge rigour by use was written but never run — *The verdict field placed first is an instance in 32; numbered ids are 20's point. The judge-rigour plan was never run, so it is one gap line in the judge block.* |
| 29 | `memory_system/strategy_adoption` | `forced_schema_screen/` (June 16, 2026, nine-seat) | **KEEP, 1 block (final check, accepted 2026-10-22)** | Case study · Moving one sentence from the schema's field description into the prompt body raised per-memory verdict coverage from 27% to 97%; Verification · The skipped rows were not random: they were mostly memories that did not apply, so under full coverage 'applies' fell from 0.80 to about 0.55 — *[page: prompt engineering topic] New point: where an instruction sits. In the schema's field description it was followed 27% of the time; in the prompt body, 97% (counted by code, live, cited in code). The skipped rows not being random becomes a clause: it is the same missing-data bias family as 93.* |
| 30 | `memory_system/v8` | A. Lessons that state rules the game does not have, and the embedder swap (11–13 October 2026) | **KEEP, 1 block (final check, accepted 2026-10-22)** | Case study · Screening synthesized lessons against the rules text found wrong mechanics: 9% wrong on Flash-Lite, 20% on the stronger Sonnet, 11% after a prompt rule, and 6% on the 40-game store; flagged lessons are left out of the served store; Design · When the embedder changed, each similarity threshold was re-derived on labelled pairs for the new model, and the store refuses vectors from another model — *[page; candidate for a hallucination topic] New point: synthesized lessons screened against the rules text. The stronger model wrote more wrong rules (20% vs 9%); flagged lessons are left out of the served store. The embedder swap becomes a clause in 27, where it is already listed as an instance to file (map lines 148–150).* |
| 31 | `memory_system/v8` | B. Extraction for ten seats: the model, the day split, the offline batch | **MERGE → blocks 10, 11, 76, 77 and 83; the uses-left audit → block 91** | Verification · Stored 'uses left' counts were checked against an engine replay: 84% exact, 89% after the definition said 'before the decision', and 'some left' against 'none left' still wrong 4.4% (goes into block 91); Case study · The pilot's one factual error came from game state dropping a dying player's night record, so it was fixed in the data, not the prompt (goes into block 73) — *Its main findings are already filed in blocks 10, 11, 76, 77 and 83 and the model choice is superseded, while the two small new items show no new skill and fit into existing blocks.* |
| 32 | `memory_system/v8` | C. What lessons a seat sees, and how often | **MERGE (final check, accepted 2026-10-22)** | Design · A seat reuses its lesson lookup across a day's discussion (fresh after a new role claim) and across a night, and gets a fresh one for every vote, which cut about 60 lookups to about 38 in one game; Verification · Only 39 of 268 lessons shown fit the decision (15%), because the search matched the role and not the stage of the game, and the pass mark set before the games failed; Case study · A stage filter, tried on a replay that was first checked to reproduce 91 of 96 lookups, raised fit from 15% to 25% but left 25 lookups empty, so it stays off, and synthesis now splits lessons by stage instead — *Fit 15% and the 0.887 vs 0.829 pair are the ten-seat instance of 40. The stage filter (15% → 25%) is already in 91; the replay check (91 of 96) is a clause beside 89. Lookup reuse (60 → 38) becomes a cost clause in 96, and the stage split a clause in 91. Note: the owner's parked note (map lines 293–305) expected up to 2 blocks; under today's rule both are instances.* |
| 33 | `memory_system/v8` | D. Credit and the halo on ten seats | **MERGE, no block (final check, accepted 2026-10-22)** | Case study · Haiku copied the prompt example's 'followed lesson 1' onto 426 turns that had been shown no lessons, so such turns now get no verdict field and no example — *The 426-turn copy goes to card 9's positional-bias block as its example-copying clause.* |
| 34 | `memory_system/v8` | E. Porting memory to ten seats: what the audit found and the scope rulings | **KEEP → block 95 (ruled 2026-10-22)** | Verification · A code audit before seeding found the nine-seat cast still hard-coded: a Vigilante shooting a wolf was graded as friendly fire, pack votes were graded by the town rule, and 21 metrics read 0 on every ten-seat game; all were ported; Design · Town memory is night-only: town day lessons are extracted for the owner's review and never retrieved in play, which closes by scope the route through which the earlier credit rewarded abstaining; Design · No forced disclosure rule was added, because the owner first counted saved games and found the information roles already reported their results — *D1 (town memory at night only) is today's design, chosen because the July failure came through a town day lesson; D2 and the port audit go in as one line each, and "missing is not zero" becomes the owner's own note, not a page lesson.* |
| 35 | `metrics` | the scoring layer | **KEEP, 1 block (final check, accepted 2026-10-22)** | Design · Each vote and night pick is graded against the true roles and divided by the chances the seat had, and a score is kept only if it moves with its side's win in a direction written down beforehand; Verification · 48 scores were tested and 11 kept, and those 11 are 6 separate measures; the town vote score held at +0.65 on 50 games, on memory-off games alone, and on 180 games; Case study · How often the investigator finds a wolf did not track winning (−0.00), but whether the find led to a lynch did (+0.40) — *[page] New point: each stand-in score was checked against winning before use. 48 were tested, 11 kept, and those are 6 measures; finding a wolf scored −0.00, turning the find into a lynch +0.40. Credit (58–59) rests on this. Card 51's shuffled-label check and card 22's wolf-blend selection bias join as clauses.* |
| 36 | `metrics` | `metrics_audit/` (July 2026, the 180-game audit) | **MERGE → card 8's block as its second instance (owner 2026-10-22)** | Case study · Speaking order was not the problem (investigators holding a find spoke before the vote on 58 of 58 days); what a seat is told was: wolves never mentioned a silent failed kill in 45 of 66 cases, so every attacker is now told; Design · Town discussion adds nothing beyond the vote (+0.34 falls to +0.02 with vote accuracy held fixed), so measure at the vote and teach the reasoning upstream — *New point: the speaking-order hypothesis was falsified (58 of 58 spoke) and the real cause was what the seat is told (wolves silent in 45 of 66 cases), so every attacker is now told. The mediation result (+0.34 → +0.02) becomes a clause.* |
| 37 | `model_drift` | When the vendor's model changes under you | **KEEP, 1 block (final check, accepted 2026-10-22)** | Case study · the baseline moved twice in two days; every internal factor was ruled out, so drift; rule: run the arms together, never compare to history.; Design · the drift map: local fine-tuned models immune, embeddings most exposed, a canary as the guard. — *[page: instruments topic, with a pointer from the memory story] New point: vendor model drift. The baseline moved on identical code (town 27% → 51% overnight), so arms run in the same window and are never compared to history; block 27 covers only embedding thresholds. The drift map becomes a clause, and cards 22 and 64 supply its numbers.* |
| 38 | `model_selection` | July seat-model choice by cost, latency and reads | **MERGE INTO cost and latency → block 96 (ruled 2026-10-22)** | Design · One model per job (live seat = latency, bulk = cheapest, extraction = quality), with public benchmarks as a shortlist only. Tell it with today's slots from `accessors.py`. — *One Design block: one model per job by its binding constraint (latency for live seats, quality for extraction, cost for bulk). At most one Design block, framed on today's defaults. The July rankings are superseded and rest on unblinded N=1–2 reads.* |
| 39 | `refactor` | June structure audit, node collapse, and the code-versus-record rule | **MERGE (ruled 2026-10-22)** | Verification · A refactor meant to change nothing was accepted only on passing tests and an identical runtime fingerprint (goes under the fingerprint lines); Design · The research record points at the code that produced it by version and never copies it (goes under the fingerprint lines) — *The code-versus-record rule is live in the project instructions, but the factories are superseded and the skills are general software practice, so its lines belong under the fingerprint and instruments topics.* |
| 40 | `retrieval/capacity_limits` | The observation cap that never shipped | **MERGE INTO the lessons layer (block 44 only)** | Gaps / Lesson · a decision recorded in a report but missing from the prompt, found by re-checking (block 44). — *Block 43's +0.07 is too small, untested and unused to defend. Block 44 is an honest instance of a lesson, not a retrieval finding.* |
| 41 | `retrieval/context_eval` | Auditing the retrieval labels | **MERGE INTO `fine_tuning/cross_encoder/`** | Verification · a 5-model vote inherited the generous models' bias (514 of 1,848 pairs). — *It audits that model's training labels, which is where a reader would look for it. The majority-vote finding can also serve lesson 15.* |
| 42 | `retrieval/filtering` | — | **MERGE (as filed) (final check, accepted 2026-10-22)** | Problem · Similarity search returns many versions of one lesson, up to 12 observations for one investigator turn (block 40); Design · The retrieval judge contradicted itself until it grouped items by lesson before scoring (block 45); Verification · Caveat for block 45: the same retrieval scored relevance 4.30 under one judge model and 3.00 under another, so score levels do not carry across judges — *Blocks 40 and 45 are already filed from this folder. The judge-level caveat (4.30 vs 3.00) becomes a clause in 45. 42 folds into 38 and 46 into 27, as the card says.* |
| 43 | `retrieval/per_day_discussion` | Look up lessons once a day? | **MERGE INTO `memory_system/v8/` (D4)** | Design · one sentence under D4: a July recompute had shown that per-turn lookups changed mostly through rewording. — *The design it argued for is live, but the ruling rests on its own count.* |
| 44 | `retrieval/reranking` | — | **MERGE (as filed) (final check, accepted 2026-10-22)** | Design · A model that re-orders strategy-point candidates by situation raised efficiency from 1.80 to 3.60 and cut redundancy from 72% to 40%, while filtering plus re-ordering scored lower (block 41); Case study · On the uncleaned store, re-ordering matched the cleaned store for strategy points, so the reranker made store cleaning matter less (one clause in block 41) — *Block 41 already holds it. The dirty-store result becomes one clause in 41.* |
| 45 | `role_set` | The nine-seat role design | **SKIP** | no block — *The design was replaced, and its one surviving piece (abstain) is already told inside block 61.* |
| 46 | `sequential_discussion` | — | **KEEP, 2 blocks (final check, accepted 2026-10-22)** | Design · The vote stays blind and simultaneous, while discussion goes one speaker at a time, picked by a stateless code scheduler from the transcript through two hard paths (owed an answer, offered a quiet turn) instead of a weighted score; Case study · A seat judging its own point's novelty failed both ways, while a separate judge rating someone else's line got 20 of 20 right, so novelty came back only as a separate gate on quiet turns; Verification · The acceptance test showed word-level repeats at 0.00 against 0.05–0.06, unpaired, with the old design frozen at a tag; a cooldown setting shipped wrong for about 20 days — *[page (to be walked per document)] Two new points. (1) A stateless code scheduler with two hard paths, no model call, and a blind vote; card 9's rounds join it, and acceptance and the cooldown slip become clauses. (2) The echo gate: a seat judging its own novelty failed both ways while a separate judge got 20 of 20. This is the block lesson 15 is waiting for; card 13's current numbers and card 9's verdict reshape (29% → 18% held) join it.* |
| 47 | `store_curation` | — | **KEEP, 1 block (final check, accepted 2026-10-22)** | Problem · A memory that only appends bloats: one paid loop run grew lessons from 0 to 227, with bloated cells around 34 against healthy ones around 5; Design · Removal needs evidence, never age alone (prune, evict only on override, count-scaled decay, earned lessons protected); the best unproven lesson gets a guaranteed slot; every paid step scales with new arrivals (32 searches → 2); Gaps · Removal barely fires within a run (the ten-seat pass pruned 4 and evicted 4 of 498), so stores keep growing without a plateau — *[page] New point: the memory lifecycle. Removal needs evidence (evict only when overridden), the best unproven lesson gets a guaranteed slot, and paid cost scales with new arrivals (32 searches → 2). Card 50's bloat and proven-first design and card 51's prune rule join it. "No plateau" becomes a gap clause.* |
| 48 | `tracing` | capture | **NOTES ONLY (owner 2026-10-22)** | Design · Each gradable decision is saved when it happens as a self-contained case (what the seat saw, what memory returned before reranking, what it did, which store and settings), in one shape to Langfuse and to a local file; Case study · The tracer cannot be the dataset: reading cases back out of traces failed on long games (3 of 5 built), and writing them locally at game time built 20 of 20 with identical case ids; Verification · Capture was checked against each consumer's needs: 5 gaps found and 4 closed, with 72 of 72 cases recording their store on a seeded game — *notes only (owner): kept in interview_prep/engineering_practices.md. New point: each decision is saved as a self-contained eval case, local file first, because reading cases back from the tracer failed (3 of 5 games built → 20 of 20). The consumer-needs audit becomes a clause. Card 49's provenance and the refactor lines become clauses, so this block carries experiment provenance.* |
| 49 | `tracing` | `fingerprinting/` | **MERGE → the capture card** | Design · A result carries three labels: what was asked (run settings), what ran (the runtime fingerprint), and which files fed it (a manifest); drift shows up in the record, but exact reproduction is not claimed; Gaps · The prompt-hash coverage drifted silently when prompts moved into sub-folders, and no test failed — *Provenance is live but belongs to the same capture story, so it adds one design line and one gaps line to the capture card instead of a block of its own.* |
| 50 | `v7_final` | the June loop runs and the guards they left | **NOTES ONLY (owner 2026-10-22)** | Case study · Both paid June loop runs were invalid: one had credit silently at zero from generation 2, and the other gave memory to every faction while claiming a 'no-memory wolves' control; each failure became a guard that fails loudly; Design · Lessons piled up from 0 to 227 while the median lesson was followed about once, so retrieval now serves proven lessons first, with a cap of 12 unproven lessons per cell — *notes only (owner): the failure-stories list in interview_prep/engineering_practices.md. New point: both paid June runs were invalid (credit silently zero; memory given to every faction), and each failure became a guard that fails loudly; no block shows experiment-integrity guards. The bloat design goes to card 47's block. It is the lead instance of the queued lesson "check that the experiment that ran is the one you meant", with 44, card 8's zero reasoning and card 46's cooldown slip.* |
| 51 | `v7_final` | the free gates and the credit and prune design | **MERGE (final check, accepted 2026-10-22)** | Verification · Before building credit, each decision type's grade was checked against its side winning, with a shuffled-label null as the baseline: town votes scored +0.56, and the investigator's night find scored 0.00, because a find wins nothing unless it reaches a lynch; Design · Prune a lesson only after 8 follows and a lift of 0.15 or more below memory-off play, a practical stand-in for a confidence interval; on held-out games, 8 of 9 flagged losers stayed negative; Gaps · The similarity score could not tell useful retrievals from useless ones: 0.828 against 0.827 over 7,534 retrievals — *The shuffled-label check makes the same check as card 35, so it becomes that block's method clause. The prune rule (8 follows, −0.15; 8 of 9 held out) becomes a clause in 59 and card 47's block. Similarity 0.828 vs 0.827 becomes an instance in 26.* |
| 52 | `v7_final` | credit-aware synthesis | **MERGE (final check, accepted 2026-10-22)** | Case study · Synthesis weighted by the extractor's win-tinted verdict carried the Serial Killer's worst lesson ('blend in, abstain') forward almost word for word; feeding it each lesson's measured track record produced a conditioned rule on 3 of 3 clusters — *Synthesis fed each lesson's track record becomes a clause in 14 or card 47's block (`store_curation` F10, the same rule). It rests on a read of 3 clusters for one role, and 84 and 94 already hold the open comparison.* |
| 53 | `v7_final` | extraction screens | **MERGE → 78 (the recall principle) and 79 (the metric caught by a read)** | no block — *The model pin is superseded, and the recall principle and the broken capture metric already belong in blocks 78 and 79, so nothing here needs a block of its own.* |
| 54 | `v7_final` | discussion credit and the tagger | **MERGE → 57; the rest SKIP** | Design · (one clause in block 57) The tagger told good night reads that missed apart from blind picks that hit, an early form of scoring reads separately from tactics — *The tagger was retired from credit and its skills are already filed in blocks 82 and 90, so only its role as a forerunner earns one clause in block 57.* |
| 55 | `v7_final` | the outside evaluator's review | **MERGE → a clause in block 65 + lesson 15's fourth instance (ruled 2026-10-22)** | no block — *Its findings are already filed (the paired endpoint test is block 65, the fusion correction is on record); what it adds is where the July design came from and one instance of lesson 15, so a clause each, no block.* |
| 56 | `docs/agentic_ai_encountered_issues.md` | Served game hung on Vertex; rescue model | **KEEP → block 97, one block (ruled 2026-10-22)** | Case study · A turn hung for 301 s with no error, because 30 silent retries hid the stall from the fallback.; Design · Time counts as a failure; two stalls move the game to a rescue model from another family for 300 s.; Gaps · There is no notice to the viewer and no whole-game watchdog. — *Opens the reliability topic. It is part of today's design, it carries a skill no filed block has, and the owner can defend it from one real incident.* |
| 57 | `evaluation/dimension_extraction` | The situation-field audit, second copy | **MERGE INTO block 88** | None. — *Block 88 already carries every number from the source log, and this page is an out-of-date copy of it, so close it without reading.* |
| 58 | `evaluation/end_to_end_ab` | How the whole-game memory A/B was run | **MERGE INTO `evaluation/methodology/`** | Verification · pairing on the deal was measured and added almost no power; running the arms together is what controlled the error. — *One walk covers both folders, but the seed finding must be squared with block 65's wording before the page goes out.* |
| 59 | `evaluation/hallucination_bench` | — | **KEEP** | Verification · A judge checks each statement against a fact sheet built by code, and a turn is kept only if it fails at least 2 of 3 replays; failing turns went wrong in 22% of samples against 3% for controls; Case study · A code audit of how facts travel from engine to prompt found 12 holes, and 8 were fixed in a day; bad samples fell from 97 to 82 of 267, a direction only; Gaps · The frozen sets are nine-seat and do not render on today's prompts, and they hold day turns only, with no vote-only or night cases — *The bench and the fact-path fixes are live, and no filed block shows hallucination evaluation against a code-built fact sheet with a screen for failures that repeat.* |
| 60 | `evaluation/hardening_pass` | Review and repair of the eval tools | **SKIP** | None (its one Verification block would repeat 88–89). — *Its one key finding is already block 88. The hygiene fixes are real, but none shaped today's design except the canary, which `model_drift/` carries.* |
| 61 | `evaluation/labeling` | Model panels that agree can still be wrong | **KEEP (one block)** | Case study · Three models agreed on "discard" and were wrong 21.4% of the time (80 of 373); unanimity is not safety. — *It is a labelling skill no filed block shows and is easy to defend in an interview. The labelling sections of the two `fine_tuning/` folders can then close into it.* |
| 62 | `evaluation/llm_judge` | — | **KEEP (one block)** | Design · Judges as smoke alarms: tie a score to a real outcome, else to human labels, else compute it; four ways judges failed (a pinned score, saturation when the judge sees the answer, generating and judging in one pass, an outcome halo); close calls went to anchored tools instead — *The judges are not in the served game and are uncalibrated, but no filed block carries judge anchoring, so it gets one block marked as such.* |
| 63 | `evaluation/loop` | The v7 loop's measurement tools | **SKIP** | Case study · a config slip ran a treatment as the control; the guard now turns that slip into a crash at generation 1 (file it at `v7_final/`). — *Every live piece is covered elsewhere, and its one good story, the arm guard, belongs to `v7_final/`.* |
| 64 | `evaluation/methodology` | Keeping a 30-game A/B honest | **MERGE INTO `model_drift/`** | Case study · Byte-identical prompts, no code change, and the baseline moved (villagers 67% → 10%, p = 0.0028), so every comparison runs both arms in the same window.; Verification · The design's own check refuted pairing as the source of fairness: the deal explained almost nothing. — *The drift case is key to how every later A/B was run, but its numbers and the fuller story live in `model_drift/`, so it should be filed from there.* |
| 65 | `evaluation/metrics` | Which game proxies actually track winning | **MERGE INTO `metrics/`** | Verification · Proxies were checked against winning before use; only the town basket passed.; Case study · A wolf proxy hid behind a condition: null pooled, +0.31 once only games wolves could win were counted.; Gaps · No proxy has been validated on the ten-seat game. — *The finding is key (credit and every A/B rest on it), but this file only points at `metrics/`, which is where the walk should happen.* |
| 66 | `evaluation/replay_screens` | Frozen-turn memory screen and an unbuilt day replay | **SKIP** | Verification · a $1 frozen-turn screen eliminated every cheap memory-use idea before any $20 game run (file it at `memory_system/effectiveness/` if that walk keeps it). — *Blocks 53 and 70 already cover the method, and what the cheap-idea screening taught belongs to the `memory_system/effectiveness/` walk.* |
| 67 | `evaluation/report.md` | The trust ledger for every measuring tool | **SKIP** | no block — *Nothing in it is first-hand, it is stale on the facts that matter most (v7, ten seats, the tagger), and its "self-correction" list is a useful checklist of where to look in the other folders.* |
| 68 | `evaluation/sampled_human_review` | — | **SKIP** | no block — *The sampler is built but has never been used for a real review and shows no new skill, so only two one-line notes move to blocks 82 and the judge block.* |

---

## Cards

### 1. `extraction/tell_extraction`

**What it is.** July 2026, nine-seat game. Can the memory learn tells (public behaviours that hint at a hidden role) without hindsight? A miner (a model call that sees the roles) proposes behaviours. A detector (a separate call that cannot see the roles) marks who showed each one in other games. Code then joins the revealed roles and counts.

**What it found.** Splitting each game-day into a discussion call and a vote call let the cheap model do the mining: 116 candidates became 213 on the same five games (lesson 80). On 60 games the miner never saw, some behaviours were strong: 27 of 30 players who counter-accused an accuser of using a role claim as a distraction were evil, when evil players held a third of the seats. New wordings never stopped arriving (about 16 a game after review, over 30 games), so the checklist was capped at 48 per channel and duplicate judgment moved from every game (about 178 calls a game) to a batch every ten games. A 12-entry book replayed on 40 frozen votes gave 24 correct against 20 (six changed, chance about 11%).

**In today's design?** OFF. The prompt slot renders nothing unless `WW_TELL_BOOK` is set, and `server/` never sets it (grep). The 48 cap is in `evaluation/src/loop/tell_fold.py`, but the loop's tells switch is off. The books name roles the ten-seat game lacks.

**How sure.** The detector was checked on 40 cases labelled by models (0.93 of discussion detections right, 87% found) and on one game by the owner (7 of 8 upheld). The six-game owner protocol was designed and only one game done. The 60 games share 12 deals. No effect on play is shown.

**Overlap.** Lessons 15 and 80, blocks 10, 26, 59, 62, 67, 93; `caching/` §4.7; `store_curation/tells.md`.

**Skill it would add.** Mining open-ended patterns, then checking them on games the miner never saw. Also a two-phase blind golden protocol, where candidates are pooled and the owner cannot see which tool proposed them.

**Candidate blocks.** Design: propose with the roles, count without them (T1). Case study: the vocabulary that never levelled off (T5). Verification: the detector's golden checks (T6–T7). Gaps.

**Call: KEEP (small).** It is the clearest case of lesson 15, and it would file the golden-set topic's "tell detector" entry that is still waiting.

### 2. `fine_tuning/agent_dialogue` — Plan to fine-tune a cheap dialogue model

**What it is.** A costed plan from May 2026, with a June 12 update. The question: could a fine-tuned open model (GPT-OSS 120B, through Together or Fireworks) speak at the table for less than Flash-Lite? Nine-seat game. Nothing was trained.

**What it found.**
- On paper it would cost $0.108 a game against Flash-Lite's $0.193. Training would cost about $20 for 500 examples. These are list prices from May 28, not measured.
- The ruling: fine-tune for style, and improve decisions through the pipeline. The June update added two ideas: force valid JSON when the model writes its answer (constrained decoding), and a DPO step (training on pairs of better and worse answers). It also recorded that no human transcripts exist to train on.

**In today's design?** NEVER BUILT. No training data or code exists. Seats today run on Claude Haiku 5.5 (`Agents/llm_factory/accessors.py`, since 2026-10-15).

**How sure.** No data. Prices are from May and the models have changed since.

**Overlap.** None. Its June ideas live on in `memory_selection_bandit/`.

**Skill it would add.** None new (a plan, not a skill shown).

**Candidate blocks.** —

**Call: SKIP.** It shaped nothing in today's design and shows no work the owner could defend in an interview.

### 3. `fine_tuning/cross_encoder/dedup_prefilter` — Cross-encoder dedup prefilter, held and never wired

**What it is.** On May 28–29, 2026 the owner tested whether a small cross-encoder (MiniLM, 22M parameters, trained on the 861 dedup labels) could replace the similarity lines that let dedup skip the model call. Nine-seat store. It was tested on the 65-case golden set.

**What it found.**
- For lessons it decided a few more cases with no error: 6 of 25 against similarity's 4 of 25 (24% vs 16%). For observations it did slightly worse: 4 of 40 against 5 of 40.
- It hits the same wall as embeddings: it cannot tell opposite advice on the same topic apart. Its worst false duplicate scored 4.19, for "Immediately and aggressively lead the accusation" against "Avoid taking a strong leadership role".
- The log's own verdict: hold deployment. The gain is 2 cases out of 25, and the cutoffs were tuned on the same 25 cases they were scored on.

**In today's design?** NEVER WIRED. `Agents/memory/deduplication/pipeline.py` (lines 6–10) says the prefilter is "a static bi-encoder … A fine-tuned cross-encoder is the planned swap-in … not yet wired in." **The map's Notes column ("prefilter deployed") and the memory index ("CE prefilter deployed") are both wrong by this code.**

**How sure.** 25 lesson cases. The cutoffs were tuned and scored on the same cases. Training and test shared no game (checked by code).

**Overlap.** Blocks 24–26 (the prefilter, its ceiling, opposite advice).

**Skill it would add.** None new.

**Candidate blocks.**
- Case study · A cross-encoder that reads both texts together still scored "lead the accusation" and "avoid leading" as duplicates (one clause plus the example in block 26).

**Call: MERGE INTO block 26.** It adds one example and nothing to today's design. Fix the "deployed" note before anything cites it.

### 4. `fine_tuning/cross_encoder/reranker` — Small trained reranker matched the LLM reranker

**What it is.** A cross-encoder reads the query and one memory together and scores how well they fit. From May 29 to 31, 2026, a small one (MiniLM, 22M parameters, runs on a CPU) was trained to replace the paid Flash-Lite reranking call. Nine-seat v4 store. The labels came from 108 cases. The first 20 were labelled by the owner with Claude and Opus; these are the situation-summary golden labels behind block 93. The rest were majority votes of four or five models.

**What it found.**
- It ranked as well as the LLM reranker, at no cost per call. On 17 held-out cases (319 pairs) the ranking score was 0.882, against Flash-Lite 0.871 and plain similarity 0.767. (The score is NDCG@5, from 0 to 1, higher when the best memories are in the top 5.) The confidence ranges overlap, so the claim is "as good as", not "better".
- The labels themselves leaned generous. The merged labels gave more credit than the two careful labellers (ChatGPT, Sonnet) on 514 of 1,848 items (28%). The generous models outvoted the careful pair. And the careful pair agreed with each other only 80.5% of the time.
- A suspected leak was checked and found small. The labellers saw a lesson's advice, but the model sees only its situation. Training the model with the advice too gained only +0.015 (ranges overlap). Relabelling a sample without the advice flipped 0–4.6% of labels.

**In today's design?** BUILT, OFF BY DEFAULT. In fact it is not wired in at all: no file in `Agents/` or `server/` loads it. Only `evaluation/src/labeling/label_scorer/reranker_comparison.py` uses it, and the served game reranks nothing (block 41).

**How sure.** 17 test cases. The labels were mostly model votes, and a planned human check of about 150 items was never run. The store is May's. Per the owner's note of 2026-10-21, the training code was written by AI and the dataset was built by the owner.

**Overlap.** Blocks 93 (same labels), 44 ("trained, never wired"), 41. The map lists this as an instance still to file under the embeddings topic.

**Skill it would add.** Turning an LLM judge into a small trained model (distillation). Bias in how labels are combined, when the labellers are correlated.

**Candidate blocks.**
- Verification · A 22M model trained on these labels matched the LLM reranker (0.882 vs 0.871, ranges overlap) for free, but was never wired in.
- Gaps · A majority vote of models gave more credit than the careful labellers on 28% of items, and the human check was designed but never run.

**Call: NOTES ONLY (owner 2026-10-22).** Kept in interview_prep/engineering_practices.md; the final check had it as one block (the only trained-model result), with the label-vote bias and cards 5–6 as clauses, but the page brief keeps fine-tuning out of the main story.

### 5. `fine_tuning/dedup_classifier` — Small dedup classifier lost; agreeing models misled

**What it is.** Dedup decides whether a new memory is a duplicate (discard) or new (keep). In May 2026 (May 27–29), the question was whether a small fine-tuned model (Qwen, 1.5B and 4B parameters, QLoRA) could replace the API call that makes this decision. Nine-seat store. The labels came from three Gemini models voting, and the owner reviewed them with Claude.

**What it found.**
- Agreeing models were not reliable labellers. When the three disagreed, a 2–1 vote for "discard" was overturned on review 37% of the time, and a 2–1 vote for "keep" 7%. Even unanimous discards were wrong 80 of 373 times (21%). The rule that came out of it: auto-accept keeps, and review every discard. 863 labels in all.
- The 1.5B model guessed by item type: it discarded every lesson and kept almost every observation. It scored 28 of 65 (43%), even though its training score read 93.6% (that score measured copying the answer format).
- The 4B model did weigh the content, but it was too cautious to discard. It scored 69% on 65 cases, against Flash-Lite's 83%.

**In today's design?** SUPERSEDED. Dedup stays an API call: `DEFAULT_DEDUP_MODEL` is Haiku 5.5 in `accessors.py`.

**How sure.** The test set was 65 owner-labelled cases. The review was the owner with Claude. All three voters were Gemini, so their errors were likely shared.

**Overlap.** Block 28 is the mirror case: there, models agreeing against a label pointed to a bad label. Here, models agreeing with each other did not make them right. The `reranker` card has the same pattern.

**Skill it would add.** Measuring labeller bias (correlated annotators). Fine-tuning (QLoRA), with a case of shortcut learning (the model learned a feature that predicts the label without reading the content).

**Candidate blocks.**
- Verification · Three agreeing models were wrong on 21% of unanimous discards, so labels were auto-accepted only on the side where the models were reliable.
- Gaps · A fine-tuned 4B model could not match the API model (69% vs 83%), so the decision stays a model call.

**Call: MERGE INTO golden-set construction.** The labeller-bias finding is a skill no filed block carries. The training runs shaped nothing.

### 6. `fine_tuning/embedding` — Seven embedder fine-tunes, none helped dedup

**What it is.** On May 28, 2026 the owner tried to fine-tune an embedding model (gte-modernbert, 149M parameters). The goal was to pull apart memories that are similar but different, so the dedup similarity lines could decide more cases without a model. It trained on 861 pairs from the dedup labels above. Nine-seat store. Seven runs.

**What it found.**
- The training score rose while the score that mattered fell. Accuracy on held-out triplets went from 38 of 87 to 59 of 87 (44% → 68%). But the gap between average duplicate and average distinct similarity fell from 0.028 to 0.008, because every pair moved to about 0.97.
- Harder training examples and a different loss did not fix it. The cause found: the model saw only the situation text, while the labels had judged every field.

**In today's design?** RECORD ONLY. No fine-tuned embedder was ever used; the store embeds with an off-the-shelf model (Qwen, blocks 26–27).

**How sure.** 87 held-out triplets and the 65-case golden set. Scored by code. Small data: the log itself says 3,000–5,000 pairs would be needed.

**Overlap.** Block 26 ("embeddings capture topic, not stance"; the ceiling is a property of the space) and block 25.

**Skill it would add.** None new. "A training metric rose while the deciding metric fell" is the one teachable point.

**Candidate blocks.**
- Case study · Fine-tuning raised triplet accuracy 44% → 68% but shrank the duplicate–distinct gap 0.028 → 0.008, so the ceiling was not the model's fault (one clause in block 26).

**Call: MERGE INTO block 26.** At most one clause; anything more repeats block 26.

### 7. `fine_tuning/memory_selection_bandit` — Reinforcement learning rejected, per-lesson outcome score proposed

**What it is.** A paper design from June 12, 2026, parked. The question: should reinforcement learning (RL) pick which memories a seat sees? Nine-seat era. Nothing was built.

**What it found.**
- It rejected RL that trains a policy by playing games against itself. Training needs thousands of games at about 160 model calls each ("the generation wall"). The policy would also be tied to one model, one set of opponents and one rule set.
- It proposed a simpler first version: score each memory by how well the decisions it was used at turned out, graded so that luck is removed, and keep that score as a table. This is the same shape as today's credit system (lesson scored per followed decision, blocks 56–59). The credit record does not cite this file, though, so the line of descent is not shown.

**In today's design?** NEVER BUILT. Its v1 idea matches `Agents/memory/consolidation/credit.py`, but nothing links them.

**How sure.** No data, design only. The owner ruled on 2026-06-12: do not present it unless genuinely owned.

**Overlap.** Blocks 56–59 (credit).

**Skill it would add.** None new. "Why not RL" would make a good interview answer, but no filed block needs it.

**Candidate blocks.** Optional: Problem · one sentence in credit, "RL was considered and rejected: it needs thousands of paid games and retrains on every rule change."

**Call: SKIP.** The idea that survived is already told, from the code, in the credit topic.

### 8. `game_play_enhancement` — the premise check and Phase 1 (`discussion_evidence.md` §1–§6, Oct 3–4)

**What it is.** A test of why the nine-seat day talk was thin, using 28 old games, before anything was built. Then a set of prompt changes behind a switch, a replay of one invented claim, a pass on how faithfully seats get their information ("fidelity pass"), the day summary v4, and the finding that the seats did no reasoning at all.

**What it found.** Town accusations that rested on a claim hit evil 34 of 35 times. Accusations on votes or behaviour hit 54–60%. No evil seat ever claimed a role, and the investigator was not hiding: it claimed in 24 of 28 games. So the cause was one exact source that nobody contested. 71% of silences (367 of 517) were the engine's skip, which the agents could not see. One invented check was replayed: it happened 20 of 20 times with the old result wording and 0 of 20 with "you investigated". Removing the seat's note changed nothing. Layout and wording fixes stayed within noise. Then the reason showed up: on the "minimal" setting the model used 0 reasoning tokens. "Medium" cut bad samples from 31% to 10%.

**In today's design?** LIVE. The thinking level is set per model (`Agents/llm_factory/catalog.py:34–41`, which cites §6.7). The turn-order fact is in `Agents/prompts/game_rules.py:44–48`. The vote-history index and the "cite the record" rule are not in the code.

**How sure.** Bench arms ran at 3 samples × 89 cases, and every verdict was read by hand. Most Phase 1 results come from 1–3 games and give a direction only.

**Overlap.** Blocks 49 (fidelity pass), 68–72 (summary v4), the v7 caveat, block 70 (the replay method).

**Skill it would add.** Checking the premise on existing data before building. Treating the reasoning budget as a measured setting chosen per model.

**Candidate blocks.** Problem: one uncontested source (34 of 35). Case study: the invented check (20/20 → 0/20, with the note ruled out). Case study: zero reasoning (31% → 10%), with the vote misquotes that no prompt could fix as its lead-in.

**Call: KEEP.**

### 9. `game_play_enhancement` — Phase 2, the day with rounds (`discussion_evidence.md` §7, phase2 data, echo checks)

**What it is.** A redesign of how a day runs: an opening round for everyone at once, filtered by a list of allowed statement kinds; a closing defence for the most-accused; and a sequential "sweep" of quiet players, each line checked by a model gate that holds repeats (the "echo gate").

**What it found.** On old records, day 1 ended empty in 28 of 28 games. The lynched player was among the day's most-accused in 61 of 67 days. The speakers' own accusation tags agreed with a judge on 145 of 183 messages. Asking quiet players in parallel produced near-identical lines (seven written to keep two), so the sweep went back to one seat at a time. In the gate, reshaping the verdict worked where rewording did not: holds fell from 29% to 18% once the judge had to say what a line adds before it could call it a repeat. Four test games showed the mechanics working, but the opening drew no contest (5 of 106 opening turns spoken) and the closing changed no vote (7 of 7 defended players were lynched). In 3 of 3 games, an investigator who claimed in the opening was lynched 7–1. The chain behind that led to two rulings: held lines no longer count, and night 1 gets a drawn default. The model followed the seat number, not the list order: a shuffle left 95 of 96 choices on the lowest number. A default drawn by lot was taken in 95 of 96.

**In today's design?** LIVE: `Agents/rules/closing.py`, `round_filter.py`, `echo_gate.py`, `scheduler.py` sweeps, and `night_one_lot`.

**How sure.** About 4 games, plus offline checks of the gate on 146 June lines.

**Overlap.** `sequential_discussion/` (pending), lesson 16 (the lot), block 45 (judge design).

**Skill it would add.** Designing turn-taking among several agents. Diagnosing a positional bias in a model's choices.

**Candidate blocks.** Design: the day with rounds. Case study: the investigator lynch chain. Case study: the seat-1 bias, where the obvious fix failed. Gap: one missing tag can silence an accused player.

**Call: KEEP.**

### 10. `game_play_enhancement` — Phase 3, the ten-seat roles (`role_sheet.md`, `phase3_wiring_census.md`, §8.1–8.5, `phase3_*` data)

**What it is.** The ten-seat rules (the owner's ruling), the sweep of nine-seat assumptions in the code before the switch, 31 balance games, 15 games read in full against an error rubric, replays of frozen failures, and full games on two more models.

**What it found.** The first 13 games all went to the town. The sigil's "immune" result named the serial killer in one step and came before 3 of its 6 lynches. Once that result was merged with a quiet night, the serial killer won both games a sigil landed on it. Evil was not short of tools: the pack aimed 34 of its 56 kills at information roles. It was short of covers. A cover-story prompt raised evil claims from 4–8 per batch to 19. Invented facts were rare (2 in about 345 heard lines). Summary errors (22) and wrong deductions about what an ability shows (28) were the main faults. On frozen turns the controls failed as often as the positives, so most remaining errors are the model's limit: Flash made 1 bad message in 40 samples where Flash-Lite made 6 after the fixes. Stating a rule stops the first misreading, not one already spreading in the transcript. A more literal model (Luna) exposed rules nobody had written down.

**In today's design?** LIVE: the role sheet (`ROLE_SPECS`), "These rules are exact" (`game_rules.py:103`), the sentinel card sentence, and the result words `no_visitors`/`roleblocked` (`schemas/output.py:26`). The census is a RECORD.

**How sure.** Batches of 6–13 games, all on Flash-Lite, so the balance reading is specific to that model. The readers were Opus agents with quotes checked; replays used 5 samples per case.

**Overlap.** Blocks 48, 54, 70, 71; `model_selection/`.

**Skill it would add.** Error analysis by kind, game balance, misinformation cascades between agents, checking a prompt against several models, and a change-impact audit before a migration.

**Candidate blocks.** Design: several imperfect sources. Case study: the sigil leak. Verification: the error audit and replay with controls. Case study: cascades and the literal reader.

**Call: KEEP.**

### 11. `game_play_enhancement` — the first Haiku game (§8.6–8.7, `haiku_*` data)

**What it is.** One live game (`403f4dbc`, Haiku 5.5). From it, 18 discussion turns and 11 votes were frozen and replayed across several code versions.

**What it found.** Visits were read in the wrong direction. Once the shared rules stated the direction, bad public messages fell from 16 of 35 to 5. A "don't repeat yourself" line changed only how replies opened (27 of 30 samples still repeated, against 23 after), so the fix needs the scheduler. A vote-reason line failed at first because the seats had not yet formed a lean. "Decide now whom you would vote for" cut passes from 24 of 25 to 16. A sentence asking seats to compare candidates was dropped: the vote it was written for fell from 7 of 10 right to 0 of 10 (p = 0.003), because seats said nothing separated the players and then abstained. The bigger finding: day-4 control votes were right 25, 20 and then 13 of 30 times across three code versions (p = 0.003), and reads cited the decisive ballot 19, 12 and 2 times. One suspect is the shared-prefix layout, which moved the role card after the transcript. A harmless wording change moved one case's samples more than any effect tested here.

**In today's design?** The direction rule, the repeat line and the vote-reason line are LIVE (`game_rules.py:70`, `prompt_inputs.py:102`, `day_discuss.py:100`). The compare sentence is OFF. The vote-record drop is unresolved.

**How sure.** One game, 10 samples per case.

**Overlap.** This qualifies block 8's "no detected quality change" and fills block 12's gap (no vote cases on the bench).

**Skill it would add.** Measuring how sensitive a prompt is, and diagnosing a failed instruction from the seats' own notes.

**Candidate blocks.** Case study: the compare sentence not adopted. Gap: the vote record dropping out of use.

**Call: KEEP.**

### 12. `game_play_enhancement` — persona voices (`voice_rewrite/`, `persona_line/`, `persona_voice_games/`, Oct 18)

**What it is.** Two ways to make AI seats sound like people: a second call that rewrites each line, or one voice line in the seat's own prompt. Each was judged blind by Sonnet subagents, then tested in 8 pairs of games played on the same deals.

**What it found.** The rewrite read better (74 of 90 preferred), but 19 of 90 rewrites changed something a listener could act on: "I'd vote you" became "I'm voting you", or the wrong person ended up at a door. The code check on names and nights caught 1 of the 19, so the rewrite was not adopted. The voice line in the prompt read more natural in 25 of 30 pairs. Its stance differed from a plain reply in 30% of pairs, exactly as often as two plain replies differ from each other. In paired games, the seats' reads were more accurate with voices on: the Brier score (how far their confidence was from the truth; lower is better) fell from 0.155 to 0.129, better in 7 of 8 pairs (p ≈ 0.07).

**In today's design?** LIVE in served games (`server/game/run_config.py:38`, `persona_voices=True`). Off by default for batch runs (`Agents/config/run.py:75`). Note: the memory index says "voices off", but the code says otherwise.

**How sure.** 30–90 items per screen, one judge per item, 8 pairs of games.

**Overlap.** Lesson 15 (it shows a code fact check is not enough of a check), §9.7.

**Skill it would add.** Measuring whether a rewrite stays faithful, against a sampling-noise baseline.

**Candidate blocks.** Case study: rewrite rejected (19 of 90 changed, gate caught 1), the voice line adopted.

**Call: KEEP.**

### 13. `game_play_enhancement` — silence calibration (`silence_calibration/`, Oct 18)

**What it is.** Whether seats pass for good reasons. Passed turns were replayed with "do not pass" added, and the forced lines were judged blind by kind: a new fact, a new reading, a question, or a restatement.

**What it found.** On the open floor, the decision to speak or pass did not track value: lines from passed turns were worth hearing 57% of the time, posted lines 52%. Rewriting the silence rule moved no decision. One sentence, "a pass costs nothing here", set how much seats spoke (20 of 64 turns spoken with it, 41 of 64 without), but it did not change which lines got said. So the sorting moved after the draft, to the gate: the new gate held 12 of 29 restatements and 0 of 36 worthwhile lines. In 4 games, open-floor speech rose from 41% to 58%, and all 7 held lines were genuine restatements. The old echo gate had never fired in 16 games.

**In today's design?** LIVE: the sentence is gone (`day_discuss.py:92`), and the gate runs at low thinking (`echo_gate.py:96`).

**How sure.** 25–46 turns per cell, one sample per arm, 4 games.

**Overlap.** Lesson 15 (separate generating a line from checking it), block 14 above.

**Skill it would add.** Measuring whether a decision separates good from bad, not only its level.

**Candidate blocks.** Case study: a model cannot sort its own lines from rule text; a check after the draft can.

**Call: KEEP.**

### 14. `game_play_enhancement` — evil covers and the counter-claim line (`evil_cover_*`, `counter_claim_votes/`)

**What it is.** Already filed as block 54 (the 2026-10-21 walk).

**What it found.** Claims rose from 13 to 44 and denials fell from 21 to 0, on 41 frozen turns. In 8 paired games, 11 of 24 evil seats claimed a role, against 3, and the wolves won 3 games, against 0. The counter-claim line was dropped. Phase 1's weaker permission text (P3) had moved nothing in two games, and that is the history before this.

**In today's design?** LIVE (`Agents/deduction/evil/covers.py`).

**How sure.** See block 54.

**Overlap / Skill / Blocks.** Block 54.

**Call: MERGE→54.**

### 15. `game_play_enhancement` — the visit-wording A/B (`visit_wording_ab/`, Oct 21)

**What it is.** A replay A/B on 19 frozen turns, run from worktrees on a tag. It tested whether the physical "visit" metaphor causes the arguments about visits, then tried a fix in the deduction engine.

**What it found.** Swapping the words for "target/track" changed nothing on DeepSeek (25% → 23% mechanics errors) and was slightly worse on Haiku (20% → 29%, not significant). So the wording was not the cause. The errors clustered on one interaction between a sentinel and a trailseer. Two deduction lines that state what the seat should conclude (A56, E19) cut the sentinel's own report errors from 15% to 5%. Replies to it were unchanged at 31%, because the transcript already held the dispute.

**In today's design?** LIVE: A56/E19 are in the code (`Agents/deduction/wording.py:227`, `evil/covers.py:47`). The target wording is OFF.

**How sure.** n = 5 per case, blind subagent judges, sign tests with p ≥ 0.29.

**Overlap.** Block 53 (the fact lands, the behaviour does not). The cascade theme in the Phase 3 card.

**Skill it would add.** Cheaply falsifying an attractive hypothesis.

**Candidate blocks.** Case study under deduction: the wording hypothesis falsified; injecting the conclusion fixes the first speaker, not the replies.

**Call: KEEP.**

### 16. `generation_prompt` — the prompt's evolution (`experiment_log.md`)

**What it is.** A history of the seat's action prompt and its output format, May to July 2026 (nine-seat game), rebuilt from git on 2026-07-07. Most of its beats retell work recorded in other folders. What it owns is the assembly of those beats and two principles: the output format is part of the prompt (fields are written in their listed order, so a field placed before the action is reasoning the model does first), and every field is required, never optional.

**What it found.** It owns little that is new. Moving the commitment field first raised action quality (`strategy_adoption/`). Reasoning written before the vote raised agreement between stated reasoning and vote from 75% to 92.5%, and moving the "assess each lesson" instruction into the prompt body raised verdict coverage from 0.27 to 0.97 (`decision_replay/`). Its own small finds: four drifted copies of the rules text (some still describing eight players) became one, and the wolf's hand-written threat brief had silently left out the Serial Killer.

**In today's design?** LIVE. `TurnOutput` (`Agents/schemas/lineup_output.py`) puts reads, then verdicts, then notes before the action. Reads moved ahead of verdicts on 2026-10-13, from a caching-log finding. `pass_turn` comes before `message`. The rules text is one source (`Agents/prompts/game_rules.py`). No `threat_brief` exists in today's prompts (grep).

**How sure.** It is a reconstruction; prompt wordings tried and reverted early on left no trace.

**Overlap.** Blocks 20 and 32; `memory_system/strategy_adoption/`; `decision_replay/`; the parked item on conditional prompt composition.

**Skill it would add.** None of its own; it is the index for the beats below.

**Call: KEEP as the index; its beats merge into their own folders.**

### 17. `generation_prompt` — removing tactics from the role text (`prompt_boundary/`)

**What it is.** June 2026, eight seats. The role prompts told agents to treat tone and silence as tells ("treat evasiveness as warning signs"), and agents recited it back. The tactics were removed. The rule became: the prompt says how to talk and what the rules are; memory decides what signals mean. The effect was counted with a word-marker script on 2 games before the change and 2 after.

**What it found.** Messages policing tone or silence halved, from 24 of 119 to 8 of 79. Canned openers on day 1 fell from 10 of 19 to 2 of 14. The recited strategy line disappeared. Past day 1 the canned phrasing barely moved, so the clause mainly fixed the empty opener.

**In today's design?** LIVE as a principle. Role text is the neutral template that every later role was written against.

**How sure.** Two games per side, not paired. The markers are a lower bound (they miss paraphrase). The policing drop is confounded by an easy board. It was kept on principle, and the log says so: the numbers corroborate the change, they do not justify it.

**Overlap.** Memory note on the prompt boundary; `sequential_discussion/` §10 points here.

**Skill it would add.** Removing a source of bias at the generator, before measuring the memory built from its games.

**Candidate block.** Design: the prompt/memory boundary, with the policing numbers as corroboration.

**Call: KEEP (small).** It set the template every role card follows.

### 18. `generation_prompt` — testing the tactics that were left (`prompt_claims_audit/`)

**What it is.** 2026-06-17, nine seats. Every tactical claim left in the role text was tested against game metrics already tracked.

**What it found.** The audit told the claims apart. The wolf's "blend your vote with the majority" held up: wolves that blended won 38% against 25% (122 games, p = 0.07), in line with an earlier r = +0.20 (p = 0.003, 220 games). The investigator's "let consensus build" failed. Investigators voted for the wolf they had confirmed almost every time but said they had checked it only about a third to two-thirds of the time. The game shows one investigator writing five messages against a confirmed wolf without saying it had been investigated. The memory had extracted "build a case gradually" from such play and fed it back. So a tactic written into the prompt becomes a lesson in memory.

**In today's design?** LIVE. A neutral two-sided investigator block ("a result that stays in your head changes no votes", `Agents/prompts/roles/investigator.py`) has been the only text since 2026-10-07 (`099b5683`). Whether the planned A/B of the rewrite ran: not found in this folder.

**How sure.** Both tests are correlations; the clause typing is a judgement call.

**Overlap.** v6 SP A/B; block 61 (memory learned advice that hurt).

**Skill it would add.** Testing your own prompt's claims against outcome data.

**Candidate block.** Problem: prompt claim, then play, then extraction, then memory amplifies it.

**Call: KEEP.**

### 19. `generation_prompt` — pre-registered tests of the July board layer (`validation/`, `validation_plan.md`)

**What it is.** July 7–9, 2026, nine seats. Before shipping a board layer (a dead roster, an alive-roles line, and forced reads: a one-line role guess per living player), every test was written down in advance. Changes to the plan are dated in place.

**What it found.** The first error census, over 50 games: about 3% of public messages and 4% of private notes misstate a fact, and 9.6% of night notes. Code flags every text naming a dead player, a dead role or a count. A cheap model reads each one, a stronger model rechecks its positives, and the owner checks the result. A correct roster in the prompt did not stop agents hunting "the remaining wolf", which falsified the expectation. The bundle still cut errors on error-prone turns from 48% to 30% (100 fresh paired cases, 29 better, 11 worse, p = 0.003). Reads cost 60% more output and never broke the lesson verdicts. Chasing complete read lists was judged not worth a retry.

**In today's design?** LIVE: the roster on the payload, `{read_targets}` (`Agents/prompts/common.py`), the completeness monitor, `check_reads_isolation`. The census code is `evaluation/src/audits/role_hallucination_screen.py`, and the ship test became the hallucination bench (2026-10-03).

**How sure.** The census readers are models checked by the owner, on seats with zero reasoning tokens. The ship test's main measure was restated after run 1, then confirmed on fresh cases.

**Overlap.** Blocks 3, 49; `evaluation/hallucination_bench/` (not yet walked).

**Skill it would add.** An error census with guaranteed recall; pre-registration with dated amendments.

**Candidate blocks.** Verification: the census. Case study: showing the answer did not fix it. Verification: the ship test.

**Call: KEEP.** Every later fix is measured against this census.

### 20. `memory_system/ablation` — Do lessons add anything beyond observations?

**What it is.** Do lessons ("strategy points") add value beyond observations (records of what happened)? May 2026, on the game before the nine-seat rebuild. 120 frozen turns were replayed three ways: both kinds, observations only, lessons only. A model judge scored each turn 1–5.

**What it found.**
- No difference. Action quality was 4.46 (both), 4.33 (observations only) and 4.50 (lessons only) over 120 turns. Combining the two did not beat either alone.
- The judge was first shown the original memories, not the ones the agent got in each condition. Fixing that moved one score by about 1.5 points; the null held.

**In today's design?** SUPERSEDED. The report planned an observations-only default. Today is the opposite: served games retrieve lessons only (`retrieval_types_config={"observations": False, "strategy_points": True}` in `server/game/run_config.py`). That choice came from v7's credit loop, not from this result.

**How sure.** 120 turns from 3 games, one model judge (Gemini 2.5 Flash), no human check. Gaps of 0.04–0.17 are within noise.

**Overlap.** `effectiveness/v6_sp_ab/` (observations vs lessons in whole games); `store_curation/` report §6.8 (why lessons only).

**Skill it would add.** None new. The judge-input bug is a small case of "the grader must see the agent's actual inputs".

**Candidate blocks.** —

**Call: SKIP.** A judge-scored null whose decision was reversed; nothing in today's design comes from it.

### 21. `memory_system/augmentation` — Re-mining games to fill thin memory cells

**What it is.** Can re-mining finished games fill thin cells (a role and phase with few entries)? A June 2026 probe on the nine-seat game: one cell (investigator day vote), 20 games, one focused extraction pass.

**What it found.**
- It produced volume. From 141 candidates, the cell grew from 12 to 57 observations and from 6 to 59 lessons after the keep/discard check.
- Whether the new entries were distinct could not be measured. The merge pass merged 3 observations and no lessons, but a read by eye found only about 15–25 distinct lessons among the 59. The dedup prompt had been tuned on the older, terser extraction.

**In today's design?** BUILT, OFF BY DEFAULT. The code exists (`Agents/memory/extraction/augment_agent.py`, `scripts/augment_namespaces.py`), but nothing in the tick or the server calls it.

**How sure.** One cell, 20 games, an eyeball count; the log itself calls the result inconclusive.

**Overlap.** Dedup blocks 17–23; block 77 (per-role calls fixed starved roles upstream).

**Skill it would add.** None new.

**Candidate blocks.** —

**Call: SKIP.** A parked tooling probe whose result shaped nothing.

### 22. `memory_system/effectiveness` — the `v5_0` paired A/B (hub `report.md`, `paired_ab/` main arms, the pilot, the pre-rebuild batches)

**What it is.** Does memory make play better? This is a June 2026 test on the nine-seat game, with Flash-Lite players at minimal thinking. Each of 30 boards was played twice, memory on and memory off, with the same deal; the game id seeds the deal. The store was frozen (`v5_0`) and served only observations, which are records of what happened. Lessons were switched off in every arm.

**What it found.**
- **Town decisions improved on the plain-retrieval arm.** The healer saved the real night target 37% → 60% (p = 0.005), and lynches hit an enemy 47% → 64% (p = 0.028).
- **Town win rate rose but did not reach significance:** 27% → 43% (p = 0.27). The quoted "+17pp, p = 0.013" fuses two arms. The p = 0.013 belongs to the reranked arm's 27% → 60%, and that arm ran after the baseline with no drift check.
- **No gain for the wolves or the lone killer.**
- **Reranking missed its pre-registered prediction.** It did no better than plain retrieval.
- **The earlier alarm was refuted.** An unpaired pilot on a growing store had said memory cost the town 32 points. The paired all-memory arm refuted it (27% → 50%).
- **The model drifts.** A re-run of the old baseline had shifted (p = 0.0028). The next day, the town with memory off won 51% against 27%. The model alias cannot be pinned, and the drift cannot be seen in its responses.

**In today's design?**
- SUPERSEDED: served games retrieve lessons only (`server/game/run_config.py:40`), and town day turns retrieve nothing (`f17b53e6`).
- LIVE: the deal is seeded by the game id (`Agents/nodes/orchestrator.py:89`), the unconditioned wolf-blending metric is still computed (`Agents/ten_seat_metrics.py:149`), and baselines are re-run alongside each arm.

**How sure.** 30 boards per arm, graded by code against the true roles. At this N, win rate alone cannot detect less than about 36 points.

**Overlap.** Blocks 63–67 and 41; `model_drift/`; `metrics/`; the vote-level re-read in `credit/blindspot_fix/` (hits 55% vs 41%).

**Skill it would add.** Claim audit. Selection bias inside a metric's definition.

**Candidate blocks.** Verification: the town's decisions improved, its wins did not reach significance. Case study: the fused p-value. Case study: drift doubled the memory-off town's wins overnight. Design: a metric that only counted disaster days.

**Call: KEEP.**

### 23. `memory_system/effectiveness` — net-first outcome framing and the town regression (`paired_ab/`, 2026-06-12)

**What it is.** A follow-up to why memory did nothing for the deceivers. The observations stated the immediate success first and buried the cost in a trailing "However…". The store was re-extracted "net-first", meaning the end-of-game verdict comes first, and re-tested on the same boards. The predictions were written down before the games.

**What it found.**
- **A free read justified the build.** In 22 decisions where a memory-on wolf broke from a vote its memory-off twin joined, the retrieved precedents were success-framed. In 0 of 22 did the wolf reason about the cost.
- **Net-first helped the killer but not the wolf, as predicted.** The killer was lynched less (80% → 63%) and won more (20% → 37%). Wolf blending stayed flat (0.64 → 0.67). None of this is significant at N = 30.
- **Net-first hurt the town.** Transcripts read like "don't be aggressive", so the town kept immediate-first framing. The size of the drop was mostly overnight drift.
- **The output schema had the vote before the reasoning.** The reasoning was written after the vote was already cast.

**In today's design? LIVE.**
- Each role and phase gets a horizon (`Agents/prompts/cell_prompt.py:42–72`): net-first for the wolf, the killer and the investigator by day; immediate-first for the town roles.
- The outcome text is composed net-first (`Agents/schemas/memory.py:41`).
- Reasoning now comes before the action (`Agents/schemas/output.py:69–102`).

**How sure.** Every result here is direction only, matching what was written down beforehand. The town mechanism comes from about 3 games' transcripts.

**Overlap.** Blocks 13–14 and 81 (the outcome halo, later measured at scale). Block 32.

**Skill it would add.** A pre-registered differential prediction: one fix, written down beforehand as expected to work for one role and not the other.

**Candidate blocks.** Design: the outcome horizon is chosen per role. Case study: one fix, predicted to help the killer and not the wolf, did exactly that in direction.

**Call: KEEP.**

### 24. `memory_system/effectiveness` — `decision_replay/`, the cheap screening layer (2026-06-13 to 07-02)

**What it is.** Freeze one recorded decision, swap only the memory block, regenerate that one action, and score it by code against the true roles. It is paired at the decision, immune to drift within one sitting, and costs about $1 a question. It was used to test cheap fixes before paying for whole games.

**What it found.**
- **Pooling hid the effect.** Pooled from day 3 on, memory did nothing (−0.006 over 180 decisions). Split by day, it helped on day 2 (+0.078) and in the endgame (+0.117), and did nothing mid-game. Two things had hidden this: a sampler that took the earliest decisions first, and a scoring rule that counted a wise abstain as a mislynch (20 of 23 memory-induced day-2 abstains avoided a mislynch).
- **Memory adds where the role prompt is thin.** The wolf and killer nulls sit where the role card already states the heuristic.
- **Capability is not the same as use.** A planted wrong lesson was rejected 13 of 20 times (block 87). But forcing a verdict per memory hurt the vote on cautious content (0.75 → 0.55).
- **Reasoning first is a channel, not a fix.** It raised agreement between reasoning and vote from 75% to 92.5%. On bad content it lowered vote quality.
- **The engagement proxy failed validation and was retired.** Counting memory words in the reasoning did not track the judge (rank correlation 0.14, p = 0.38).

**In today's design? LIVE.** The harness is `evaluation/src/studies/decision_replay.py`; the retired proxy carries a deprecation warning there. Its replay method returns in blocks 48 and 53.

**How sure.** Small cells (20–40 decisions), temperature 1, three runs per cell pooled. It shows direction only.

**Overlap.** Blocks 53, 87 and 89. `strategy_adoption/forced_schema_screen/`.

**Skill it would add.** Stratified analysis. Retiring an instrument that fails validation.

**Candidate blocks.** Design: a screen built to rule out cheap fixes, not to prove them. Case study: pooling hid the day-2 effect.

**Call: KEEP.**

### 25. `memory_system/effectiveness` — `v6_sp_ab/`, the v6 store A/B and the lessons channel (2026-06-15 to 06-17)

**What it is.** A second paired test, 6 arms of 30 boards, on the v6 store. It was the first to switch lessons on. (Lessons are "strategy points": advice a seat can follow.) Every earlier test had served observations only: 0 lessons retrieved in 545 killer decisions.

**What it found.**
- **The town gain did not repeat.** Town with observations was +6 points (p = 0.77). The memory-off town itself had risen from 27% to 37% wins after a prompt change. A replay in the same week scored the v5 and v6 stores alike: votes hit a threat 0.625 vs 0.604 of the time, both below the 0.667 with memory off (48 votes).
- **Following a lesson really changes the action.** Seats that marked an "abstain" lesson *follow* abstained 77% of the time, against 32% at baseline. Seats that marked it *not relevant* abstained 30%.
- **Lessons were followed, but play did not improve.** Decisions made while following a lesson were right 63–66% of the time, against 69% at baseline. The lessons copied the town's own weak play, for example "do not reveal your findings".
- **Lessons alone hurt the killer.** Its win rate fell 17 points (30% vs 47%, p = 0.33). The "synergy" arm only cancelled that harm.

**In today's design?**
- Its conclusion drove the credit loop: content was the bottleneck, and only lessons scored by what they led to can repair it.
- The cross-check instruction is in code (`Agents/prompts/memory/context.py:22`), but it is OFF in served games.

**How sure.** Nothing reached p < 0.05. Still, "follow changes the action" is a large, direct effect.

**Overlap.** Blocks 56 and 60–62. `memory_system/ablation/`.

**Skill it would add.** None new.

**Candidate blocks.** Verification: a lesson's "follow" verdict really changes the action (77% vs 32%). Problem: memory was faithfully followed and still did not help, because it held the town's own mistakes.

**Call: KEEP.**

### 26. `memory_system/effectiveness` — `day_replay/`

**What it is.** A July 2026 design spec for re-running one day of a recorded game with memory swapped, playing out within that day. It sits between the one-decision screen and full games. Its core is a contract for rebuilding the day's starting state, with two independent derivations of the survivors that must agree before any model call.

**What it found.** Nothing: it was never built. No `day_replay.py` exists in `evaluation/`.

**In today's design?** PLAN, unbuilt.

**How sure.** Not applicable.

**Overlap.** `decision_replay/`.

**Skill it would add.** None that a built block does not already show.

**Candidate blocks.** None.

**Call: MERGE → instruments topic, one Gaps line** (owner 2026-10-22). Unbuilt, but it names a real gap: a per-turn replay keeps the old talk in its transcript, so it cannot judge a change to how seats talk by how the room then votes; a day replayed live from a frozen start can, with both arms sharing the history up to that day. The memory on/off purpose it was written for is gone (town day turns make no lookup; memory research closed), and the July state contract would need redoing for the ten-seat day (rounds, claim ledger, deduction engine). Not to build now.

### 27. `memory_system/store_progression.md` — Eight store versions told as one story

**What it is.** A June 2026 narrative across about eight store versions, from one big strategy document up to v7, with an October 2026 addendum on the ten-seat v8. It produces no data; every number is quoted from other folders.

**What it found.**
- The story: each version answered wherever the limit had moved. First it was overfitting (one big document), then duplicates, then retrieval precision, then the content of the lessons.
- The turning point: in the v6 test, memory was retrieved and followed, yet decisions did not improve. So the limit was taken to be lessons mined from the agents' own mediocre play, which motivated v7's credit loop.
- The v8 addendum: lessons that fit the decision rose from 15% to 24–27% (96 lookups, model readers), and synthesized lessons stating a wrong rule fell from 11% to 6.1%. Play was not tested.

**In today's design?** RECORD ONLY.

**How sure.** A secondary source, stale in places. Its v7 table and summary still call compounding "open"; they were written before the July pre-registered test closed negative (−0.147, p ≈ .06). Its Phase 0 cites an effectiveness-report section that no longer exists.

**Overlap.** `effectiveness/`, `dedup/`, `extraction/situation_dimensions/`, `v7_final/`, `memory_system/v8/`; blocks 63–67.

**Skill it would add.** None new.

**Candidate blocks.**
- Organisation · the spine of the memory section: each iteration told as problem → what we tried → how we found out → what it revealed

**Call: KEEP (as the spine, not as a source of numbers).** It is the only telling of how the memory evolved and how each problem was found, and the landing page's "Read the case study" links to it today; cite every number from the primary folders, and its stale lines (the fused "+17→+33pp" headline, compounding "open", no July result) carry a dated correction note until the write-up replaces it (owner 2026-10-22).

### 28. `memory_system/strategy_adoption` — Phase 1, the adoption report (May 2026, pre-rebuild game)

**What it is.** Can a seat say accurately which lessons it followed? Three versions of the reporting instruction were tested. The players were Flash-Lite at minimal thinking. A model judge scored frozen turns taken from 3 games per version.

**What it found.**
- **Moving the "lessons followed" field before the action was the largest gain.** I recomputed the scores from the raw result files. Judge-scored accuracy of the report, at 30 turns each with the same judge: 4.00 → 4.80. Action quality rose too: 3.97 → 4.67. The report's own pairing (v1 on 30 turns, v2 on 120) gives 4.00 → 4.38.
- **Wording mattered less.** "Influenced" invited over-claiming. "Advice your action follows" replaced it. Added DO/DON'T rules (v3) did no better; one hallucinating game made v3 look worse.
- **A diagnostic field reversed the first impression.** Adding a field for the direction of each error showed under-claiming, not over-claiming: of 120 reports, 87 accurate, 23 under, 10 over. The early read at 30 turns had suggested the opposite.
- **Long lesson ids broke.** 36-character ids were garbled about 30% of the time; numbers 1..N fixed it.
- **The judge plan was never run.** A protocol sorts judges by use: one that only compares versions needs consistency, one quoted as a level needs human labels. It was written but never executed.

**In today's design? LIVE.**
- Each shown lesson gets follow / override / not relevant, by number, before the action (`Agents/schemas/output.py:83–94`, `Agents/prompts/memory/context.py:10`).
- Credit counts "follow" (block 60).

**How sure.** One model judge, never checked against human labels. Each version came from different games.

**Overlap.** Block 32 (field order), block 20 (numbered references), block 37 (a small sample reversed), block 60.

**Skill it would add.** Choosing judge rigour by what the judge's output is used for.

**Candidate blocks.** Design: a numbered verdict per lesson before the action. Gaps: the load-bearing judge was never checked against human labels.

**Call: KEEP.**

### 29. `memory_system/strategy_adoption` — `forced_schema_screen/` (June 16, 2026, nine-seat)

**What it is.** A replay screen on 48 to 60 town decisions. It asked for one applicability verdict per shown memory and counted coverage by code.

**What it found.**
- **Where the instruction sat decided coverage.** In the schema's field description only, it was followed for 27% of memories. Stated in the prompt body, 97%. Fixing the list length in the schema, 100%. The rows were real, not filler; every reason differed.
- **The obvious fixes failed.** Numbering the memories did not help. Coverage was flat across ranks, so the model was not dropping the tail.
- **Partial coverage had biased the engagement number.** The skipped memories were mostly the ones that did not apply. Under full coverage, "applies" fell from 0.80 to about 0.55.
- **Forcing a verdict per memory hurt only on cautious content.** On the v5 store the vote fell 0.625 → 0.521. On v6 it held (0.604 → 0.625). No memory arm beat no memory (0.667).
- **Full coverage carried over to discussion.** 200 of 200 verdicts, with natural messages.

**In today's design? LIVE.**
- The instruction is in the prompt body (`Agents/prompts/memory/context.py:31–39`, citing 0.27 → 0.97).
- Lessons use the same delivery (`context.py:6–14`).
- The per-observation verdict exists but is OFF in served games.

**How sure.** Counted by code; Flash-Lite only; 48–60 decisions; votes unaffected within noise.

**Overlap.** Block 87; `effectiveness/decision_replay/` (where field-description delivery first failed).

**Skill it would add.** Instruction placement for structured output, and a metric biased by which rows go missing.

**Candidate blocks.** Case study: coverage 27% → 97% by moving one sentence. Verification: the skipped rows were not random.

**Call: KEEP.**

### 30. `memory_system/v8` — A. Lessons that state rules the game does not have, and the embedder swap (11–13 October 2026)

**What it is.** The ten-seat lesson store was built from AI-only games. Every set of synthesized lessons ("strategy points") was screened against the rules text for wrong mechanics. Then the embedder was swapped from Gemini to Qwen.

**What it found.**
- A stronger synthesis model wrote more wrong rules, not fewer. Flash-Lite got 14 of 150 lessons wrong (9%); Sonnet got 32 of 164 wrong (20%). Sonnet's lessons were about three times longer and stated more mechanics.
- Most errors were synthesis over-generalising facts that were right ("healed twice" became "permanently protected").
- Sonnet also slipped day advice into 31 of 34 town night lessons, which brought back the town day advice the scope ruling had removed.
- A prompt rule (mechanics only as the rules state them; this phase only; one move per lesson) brought this to 19 of 176 (11%) and 1 of 32. On the 40-game store, 37 of 605 (6%) were still wrong. They were flagged and left out of the served store.
- The screen also caught the agents' own rules text being wrong: it said the pack chooses its carrier, but the engine rotates by seat order.
- On the swap, each threshold was re-derived on labelled pairs, not mapped by percentile (that would have carried an old miscalibration over). The store refuses vectors from another model. Top-5 results overlapped 81% across 236 queries.

**In today's design?** LIVE: `Agents/prompts/extraction/cell.py:169`; the served store (498 lessons); `SIMILARITY_THRESHOLDS` in `Agents/llm_factory/embeddings.py`; the model check in `Agents/memory/persistence/postgres.py:73`.

**How sure.** Each screen was one read by Claude subagents, with no human check. The readers disagree (one quarter of the cells drew 4 flags, another 13).

**Overlap.** Blocks 11 (batch $1.51 against $4.02), 24, 26, 27.

**Skill it would add.** Auditing generated knowledge against a rules spec; migrating to a new embedding model.

**Candidate blocks.** Case study: 9% → 20% → 11% → 6%, with screen-and-exclude. Design: thresholds re-derived per model, and the index records its model.

**Call: KEEP.**

### 31. `memory_system/v8` — B. Extraction for ten seats: the model, the day split, the offline batch

**What it is.** The extraction model was chosen on two pilot games, then extraction moved offline into batches. Forty games were re-extracted and the cost was counted.

**What it found.** Most of it is already filed:
- 3.8 Flash replaced 2.5-pro (about $0.34 against $1.17 a game).
- Haiku wrote a seat id into 74 of 146 observations (block 76).
- Splitting the day call gave 0 → 16 discussion observations (block 77).
- Claude's cache failed because the enforced schema is part of the cache key, so runs billed $2.69 and $19.99 against estimates (block 10). The fix, putting the schema as text after the cached prefix, is live.
- Choosing the de-halo judge and its 25–29% revision rate are block 83.

New, small:
- An audit of the stored "uses left" counts against an engine replay: 84% exact, 89% after the definition said "before the decision". "Some left" against "none left" was still wrong in 4.4%.
- The pilot's one factual error came from game state dropping a dying player's night record. It was fixed in the data, not the prompt.

**In today's design?** LIVE: offline only, `scripts/extract_batch.py` (default Sonnet 5.5), `schema_in_prompt`, `DehaloConfig` (Haiku). The 3.8 Flash choice is SUPERSEDED.

**How sure.** Two-game comparisons, one reader.

**Overlap.** Blocks 7, 10, 11, 73, 76, 77, 83, 91.

**Skill it would add.** None new.

**Call: MERGE.** Into blocks 10, 11, 76, 77 and 83; the uses-left audit goes into block 91. This sub-study is the source block 11 still lists as "the v8 offline ruling".

### 32. `memory_system/v8` — C. What lessons a seat sees, and how often

**What it is.** The owner capped how often a seat looks up its lessons. Seven memory-on games were played, and 96 of their 352 lookups were read for fit. A stage filter was then tried in a replay, first on the 12-game store and again on the 40-game store.

**What it found.**
- **Reuse.** A seat reuses its lookup across a day's discussion (fresh after a new role claim) and across a night; every vote gets a fresh one. This cut about 60 lookups to about 38 on one game. Lookups were 20–28% of a Luna game's cost.
- **Fit.** Only 39 of 268 lessons shown fit (15%). The search matched the role, not the stage of the game: in one healer lookup the worst-fitting lesson scored 0.887 and the best 0.829. Seats rejected most misfits themselves (sound 65, mixed 25).
- **The pass mark.** It was set before the games, and the gate failed on relevance.
- **The replay was checked first.** It reproduced what seats saw in 91 of 96 lookups.
- **The filter.** Fit went from 15% to 25%, but 25 lookups were left empty. On the 40-game store, with gaps refilled from the same stage, fit was 24% and 52 of 96 lookups had a fitting lesson.
- **Mixed-stage lessons.** One lesson in five that carried a stage label had been written from sources that disagreed on that stage, so synthesis now splits by stage (live).
- **Duplicates.** Readers found 65 duplicate groups the point dedup missed. Of these, 37 crossed the labels the dedup splits on before comparing.

**In today's design?** Reuse LIVE (`lookup_cache.py`); stage split LIVE (`strategy_synthesis.py::synth_partition_key`); stage filter OFF (`DEFAULT_STAGE_FILTER = False`).

**How sure.** Read by Sonnet subagents, with no human check. Different readers did the 40-game read. No effect on play was measured.

**Overlap.** Blocks 18, 40, 88, 89, 91; the parked note.

**Skill it would add.** Metadata filtering; cutting how often lookups are called.

**Call: KEEP.**

### 33. `memory_system/v8` — D. Credit and the halo on ten seats

**What it is.** Credit was ported to ten seats with the owner's grading table. The outcome halo (verdicts that follow who won rather than the move) was measured, observations were tagged with their decision, and a demo credit pass was run on 20 memory-on Haiku games.

**What it found.**
- **Four grading principles:** grade what the actor controls; a failure the actor could have predicted is the actor's; being seen is a cost; a limited use spent for nothing is bad.
- **The halo held.** It is filed as block 82, with tags agreeing 98 of 102 in a blind read.
- **The demo pass.** 148 of 498 lessons were followed; 4 were pruned and 4 evicted.
- **Side finding.** Haiku copied the prompt example's "followed lesson 1" onto 426 turns that had been shown no lessons. The fix removes the verdict field and its example on such turns.

**In today's design?** LIVE: `grading.py`, and the separate `tick credit` and `tick learn` commands. Served memory is off by default.

**How sure.** 20 games; the prune and evict thresholds come from nine seats and are unvalidated here.

**Overlap.** Blocks 14, 58–62, 82–84.

**Skill it would add.** The 426-turn copy shows a model copying a prompt example, which no filed block carries.

**Call: MERGE.** Into blocks 58, 59, 82, 83 and 84. Keep the 426-turn copy as a small prompt-engineering case study.

### 34. `memory_system/v8` — E. Porting memory to ten seats: what the audit found and the scope rulings

**What it is.** This comes from `decisions.md` and `plan.md` (§9 wins): the code audit and rulings before seeding.

**What it found.**
- **Silent failures.** Three code searches found the nine-seat cast still hard-coded: a Vigilante shooting a wolf was graded as friendly fire, the pack's votes were graded by the town rule, and 21 metrics read 0 on every ten-seat game. All were ported.
- **D1: town memory is night-only.** Town day lessons are extracted for the owner's review and never retrieved in play. That closes, by scope, the route through which v7's credit rewarded abstaining.
- **D2: no forced disclosure rule.** The owner first counted 28 saved games and found the information roles already reported (Investigator 13 of 13 after Suspicious; Sentinel 42 of 42; Trailseer 44 of 44).

**In today's design?** LIVE: `Agents/memory/retrieval/plan_gating.py:18`; the ported metrics.

**How sure.** Rough counts (a claim field or a text match). D1 and D2 are product choices, not proven best play.

**Overlap.** Block 61 (the abstain blind spot), 62, 75, 87.

**Skill it would add.** Auditing a migration for silent zeroes; narrowing scope as a design lever.

**Call: KEEP.** D1 is today's design and no block files it.

### 35. `metrics` — the scoring layer (`report.md`, `experiment_log.md`, `candidate_ledger.md`, `proxy_win_monotonicity.md`, `design/`)

**What it is.** A game result is one lucky bit: which side won. That is too noisy to compare memory on and off at 30–50 games. So in June 2026, on the nine-seat game, every vote and night pick was graded against the true roles and divided by the chances the seat had. A score was kept only if it moved with its own side's win, in a direction written down before the check. It was checked on 50 games in June and re-audited on 180 in July.

**What it found.**
- The town vote can be scored this way. The share of lynches that hit an evil player moved with the town's win at a correlation of +0.65 (0 means unrelated, 1 means they move together perfectly). That held on 50 games, on the 30 memory-off games alone, and again on 180 games.
- 48 scores were tested. 11 were kept, and those 11 are 6 separate measures, not 11. Two of them sum to 1 by construction.
- How often the investigator *finds* a wolf did not track winning (−0.00, 169 games). Whether the find led to a lynch did (+0.40, 117 games).
- Wolves win by blending in, not by leading. A wolf leading an accusation scored −0.09 (53 games), voting with the room +0.27. On 109 of 169 days when the town lynched one of its own, no wolf was among the accusers.

**In today's design?** LIVE in batch runs. `Agents/main.py:174` calls `compute_game_metrics`, and `Agents/ten_seat_metrics.py` ports the scores, stating that every one is unvalidated on the ten-seat game. The wolf finding lives in credit: a pack vote scores well when it matches the room (`Agents/memory/consolidation/grading.py:311`).

**How sure.** Code computes every number. It was run on the nine-seat game only. A lucky blind vote still counts as correct.

**Overlap.** Credit blocks 58–59. Block 37 (a small-sample result that flipped). The third source of the parked lesson "grade the decision, not the result".

**Skill it would add.** Checking a stand-in score against the outcome it stands in for, while counting distinct measures rather than rows.

**Candidate blocks.** Design: the scoring layer. Verification: 48 tested, 6 measures, memory-off check. Case study: finding a wolf is not converting the find.

**Call: KEEP.**

### 36. `metrics` — `metrics_audit/` (July 2026, the 180-game audit)

**What it is.** Two free, code-only audits run on 2026-07-02. One tried to rescue rejected scores and find new ones, with the 180 games split into a discovery half and a confirmation half. The other tested whether the speaking order starved some roles.

**What it found.**
- **Discussion adds nothing beyond the vote.** Town accusations aimed at real threats scored +0.34, but nothing remained once vote accuracy was held fixed (+0.02, 175 games). The vote is how town talk reaches the result. A separate model-based tagger showed the same split: town +0.02, wolves +0.56, serial killer +0.60 (24 games). The design consequence: measure at the vote, teach the reasoning.
- **Speaking order was not the problem.** Investigators holding an unused find spoke before the vote on 58 of 58 days. Of 54 finds, 12 never became lynches. None of those 12 lacked the floor: 7 were withheld and 5 were ignored by the town. So no scheduler redesign was built.
- **What a seat is told is the problem.** When a wolf kill failed silently on the serial killer, who is immune at night, the wolves never mentioned it in 45 of 66 cases. After an announced heal, they never mentioned it in 38 of 123. The vigilante, told outright, noticed and acted 8 of 9 times.

**In today's design?** LIVE. Change E (commit `51de1917`, 2026-07-05) tells the attacker; today's line is "unharmed: immune to night kills tonight" (`Agents/rules/night_record.py:109`). The audit's fields that record a muted turn (`gated`, `gated_candidate`) are live in `Agents/schemas/game_events.py`.

**How sure.** Nine-seat games; small counts for the vigilante; a keyword scan, not a judge, for "noticed".

**Skill it would add.** Mediation analysis: telling a step on the causal path apart from a confounder.

**Candidate blocks.** Case study: what a seat is told mattered, not when it spoke; every attacker is now told. Design: measure at the vote, teach upstream.

**Call: KEEP.**

### 37. `model_drift` — When the vendor's model changes under you

**What it is.** A reference note from 12 June 2026 (nine-seat game). It was written after the memory-off baseline moved twice in two days on identical code. It maps which parts of the system a vendor can change under us, and the guards for each.

**What it found.**
- The drift was large. Town wins fell from 67% in the first baseline to 27% in a re-run. Then a 10-game memory-off canary run overnight found villager wins up from 27% to 51%. An audit fixed every factor under our control: deals, prompt hash, code (empty diff), configs, backend and temperature. Nothing was left but the model behind the name, and the `gemini-3.1-flash-lite` alias could be neither pinned nor detected.
- The rule that came out of it: a comparison is read only if its arms ran at the same time. Old runs are context, never a comparison.
- The embedding model is the most exposed part. The store was embedded once, but every query is embedded now, so the similarity thresholds can quietly stop meaning anything. The guard is a canary of fixed text pairs. The locally fine-tuned models are the only parts the vendor cannot change.
- The seed (the deal) adds almost no variance. At 30 games per arm, only about a 36-point win gap would show.

**In today's design?** LIVE in practice. Same-time baselines are the standing rule (the v7 signed run, the evil-cover pairs). The canary runs in `scripts/run_batch.py`, and thresholds have been kept per embedding model since 2026-10-12. Two things were never built. One is a runner that alternates arms game by game: `run_batch.py` runs configs one after another, so arms run as parallel batches instead. The other is a list of uncommitted files in the run fingerprint: `Agents/run_fingerprint.py` still records only whether the tree was dirty.

**How sure.** Drift is concluded by ruling everything else out, not seen directly. The canary runs are 10 games each. The −40 point town "regression" it explained was drift plus the treatment, mixed.

**Overlap.** Block 27 (a threshold means something only for its model), block 9 (probes); `end_to_end_ab/` and `evaluation/methodology/` (the seed finding).

**Skill it would add.** Experimental control under an unpinnable vendor model (model drift).

**Candidate blocks.**
- Case study · the baseline moved twice in two days; every internal factor was ruled out, so drift; rule: run the arms together, never compare to history.
- Design · the drift map: local fine-tuned models immune, embeddings most exposed, a canary as the guard.

**Call: KEEP, 1 block (final check, accepted 2026-10-22).** [page: instruments topic, with a pointer from the memory story] New point: vendor model drift. The baseline moved on identical code (town 27% → 51% overnight), so arms run in the same window and are never compared to history; block 27 covers only embedding thresholds. The drift map becomes a clause, and cards 22 and 64 supply its numbers.
| Folder | What it is (≤12 words) | Call |
|---|---|---|
| `evidence/metrics/` (+ design, metrics_audit) | Per-role scores that grade decisions, tested against which side won | KEEP (narrow) |
| `evidence/tracing/` | Every decision saved as a re-gradable record: trace plus local file | KEEP (small) |
| `evidence/tracing/fingerprinting/` | Each run stamped with its code, prompt hash and models | MERGE INTO `tracing/` |
| `evidence/v7_final/` (1 of 2: the June loop runs) | Two invalid learning-loop runs and the guards they left | KEEP (one case study) |
| `evidence/v7_final/` (2 of 2: gates, credit design, screens) | Free screens that set how lessons are credited and pruned | MERGE INTO credit blocks 56/59 |

### 38. `model_selection` — July seat-model choice by cost, latency and reads

**What it is.** The record from July 26, 2026 of which model plays the seats. It has measured costs from single live games, the owner's reads of transcripts, and public benchmarks used only to shortlist. Nine-seat game, memory off.

**What it found.**
- Latency decided the live default. A human waits on each turn, and with the sequential scheduler the turns add up. The flash-lite class took 3–5 s a turn; DeepSeek v4-pro took 8–25 s, even though the owner read it as the best table.
- Cost came from measured bills: gemini-3.6-flash $1.02 a game; v4-pro $0.24 after the word cap. N=1 each, and game length varies by a factor of two.
- The public benchmark did not predict this game. v4-pro was the best table but sat mid-board on EQ-Bench 4, so benchmarks shortlist and never select.

**In today's design?** SUPERSEDED. Since 2026-10-15 the defaults are Claude (Haiku 5.5 seats, Sonnet 5.5 fallback; `accessors.py`), because the Gemini credits ran out. A model now joins through admission probes (`evaluation/src/model_admission/`).

**How sure.** Quality calls are the owner's own reads, unblinded, over 1–2 games per model. Costs are single games.

**Overlap.** Block 76 (model choice by a count). The cost topic header names this folder as still to walk.

**Skill it would add.** Choosing a model per job under latency and structured-output constraints, partly carried by block 76's "model selection" tag.

**Candidate blocks.**
- Design · One model per job (live seat = latency, bulk = cheapest, extraction = quality), with public benchmarks as a shortlist only. Tell it with today's slots from `accessors.py`.

**Call: MERGE INTO cost and latency → block 96 (ruled 2026-10-22).** One Design block: one model per job by its binding constraint (latency for live seats, quality for extraction, cost for bulk). At most one Design block, framed on today's defaults. The July rankings are superseded and rest on unblinded N=1–2 reads.

### 39. `refactor` — June structure audit, node collapse, and the code-versus-record rule

**What it is.** Three documents from 2026-06-06 to 2026-06-10, written before the v5 store was rebuilt on the nine-seat game:
- a repo audit;
- a record of collapsing 16 per-role node functions into factories;
- the rule that `evaluation/` holds the eval code and `evidence/` holds the record.

**What it found.**
- **The real gap was tests, not folder layout.** There were 27 unit tests, 22 of them on the scheduler. Three paths had none: the memory on/off gate, the dedup thresholds, and the three-faction winner. A wrong number there would look plausible, and a smoke game cannot catch it. The ruling was tests first, then the refactor.
- **The node collapse was accepted only when nothing changed.** It needed 95 tests passing, an identical runtime fingerprint (prompt hash `c35e68e2d0cca9f0`), and a reading of the span-naming code, because the fingerprint cannot see tracing.
- **The record points back to its code by fingerprint.** Old evidence is frozen, not retrofitted. A study's code moves into `evaluation/` only when the current design adopts it.

**In today's design?** The rule is LIVE as the "Eval Architecture" section of `CLAUDE.md`. Both factories are SUPERSEDED: `Agents/nodes/night/` now holds `pack.py`, `solo.py` and `resolution.py`, and `Agents/nodes/day/actors.py` defines plain `discuss` and `vote` functions. `tests/` holds 1,878 test functions by a grep, including `tests/engine/test_determine_winner.py`.

**How sure.** These are decision records, not measurements.

**Overlap.** `tracing/fingerprinting/` (the fingerprint as refactor gate and as the record's pointer). Instruments topic: "a smoke game cannot catch a plausible wrong number".

**Skill it would add.** General software practice (a regression net before a refactor; keeping a research record). No agentic-AI tag is new here.

**Candidate blocks.**
- Verification line, under the fingerprint: a refactor that should change nothing was accepted only on an identical fingerprint.
- Design line, under the fingerprint: the record points at its code by version and never copies it.

**Call: MERGE (no blocks of its own).** Finding 1 goes to the instruments topic as one line; findings 5–6 go to the fingerprinting lines in `tracing/`.

### 40. `retrieval/capacity_limits` — The observation cap that never shipped

**What it is.** June 2026, nine-seat. Once only observations were retrieved, does showing more help a weak model? Three caps (3, 5 and 7 per situation, about 5, 7.6 and 9.8 observations a turn) were replayed on 120 frozen turns and scored by one model judge.

**What it found.**
- Five was best by a hair: action quality 4.33, 4.40 and 4.26 (n=120 each). Cap 5 was adopted.
- The adopted cap never reached the prompt. It was built as the search width, and the keep-3 cap still ran after it. So every observation-on campaign since June (the paired A/B, v6, v7) ran at about the cap-3 condition. This was found in October by checking the report against the code.

**In today's design?** SUPERSEDED. The search width is 5 with keep-3 after it (`Agents/memory/retrieval/pipeline.py`, comment near line 79). The served game retrieves no observations.

**How sure.** n=120, one judge (2.5 Flash), no significance test. The gain is +0.07 on a 5-point scale.

**Overlap.** Blocks 43–44. Block 44 is already queued as an instance of the lesson "check that the experiment that ran is the one you meant".

**Skill it would add.** None new.

**Candidate blocks.**
- Gaps / Lesson · a decision recorded in a report but missing from the prompt, found by re-checking (block 44).

**Call: MERGE INTO the lessons layer (block 44 only).** Block 43's +0.07 is too small, untested and unused to defend. Block 44 is an honest instance of a lesson, not a retrieval finding.

### 41. `retrieval/context_eval` — Auditing the retrieval labels

**What it is.** Late May 2026, nine-seat. Retrieval labels said whether a lesson matched the search text. Would they change if the labeller saw the game itself? A cheap check re-labelled 1,848 lesson–turn pairs. The two new label sets it then designed were deferred on 2026-06-01, and no labelling ran.

**What it found.**
- Two of the three cheap labeller models were useless: one marked 7 of 1,848 pairs irrelevant, the other none.
- Labels judged on the search text over-credit topical matches. Where they disagreed with two strong judges (ChatGPT and Sonnet) who saw the game, 93% of the disagreements were "useful" calls the strong judges rejected.
- The reranker's training labels, a 5-model majority vote, kept that bias: 514 of 1,848 pairs were over-credited, 458 of them where three generous cheap models outvoted the two careful ones. Unanimous labels were clean.
- The two strong judges agreed on only 80.5% of 400 pairs, a ceiling for any labeller.
- On the stricter labels the trained reranker lost about 0.06–0.09 NDCG@5 on observations. This was not significant at 13 cases and became significant at 25.

**In today's design?** RECORD ONLY. No relabel or retrain ran, and the model it audits is not wired in.

**How sure.** Model labellers only, no human labels. The 80.5% ceiling comes from one model pair.

**Overlap.** Lesson 15 ("a different model is not independence"), block 93 (incomplete labels) and block 37 (a small n reversed).

**Skill it would add.** Label-aggregation audit: a majority vote over correlated judges.

**Candidate blocks.**
- Verification · a 5-model vote inherited the generous models' bias (514 of 1,848 pairs).

**Call: MERGE INTO `fine_tuning/cross_encoder/`.** It audits that model's training labels, which is where a reader would look for it. The majority-vote finding can also serve lesson 15.

### 42. `retrieval/filtering`

**What it is.** May 2026, nine-seat game. Memory search returned many versions of one lesson (up to 12 observations for one investigator turn). The study asked whether filters could thin that out. It built three filters: a similarity line that drops near-copies of observations, a diversity re-pick (MMR, which trades closeness to the query against difference from items already picked) for strategy points, and a cap of 3 per situation. It also built a model judge. Four runs on the same frozen turns (10 cases in run 1, 5 after).

**What it found.**
- The judge had to be fixed before any score meant anything. One 9-item set got maximum redundancy and maximum novelty at once. The fix was to group items by lesson first and score from the groups. The cheapest judge model broke its output format on about 30% of calls.
- A similarity line of 0.85 cut observations from 4.9 to 1.6 per turn, and relevance fell from 4.30 to 2.70 (10 cases). The line was raised to 0.92.
- Without the cap, one turn received 12 observations.
- One case (healer, day vote) scored relevance 1 in every setting: no lesson for that moment existed.

**In today's design?** The filters are BUILT but OFF (`DEFAULT_FILTERING_CONFIG`, `Agents/config/run.py`, still keyed by nine-seat roles). The cap of 3 is LIVE (`RETRIEVAL_KEEP_PER_SITUATION`, `Agents/memory/retrieval/accessors.py`, not `pipeline.py`). The group-first judge prompt is LIVE ("STEP 1 — CLUSTER BY LESSON", `evaluation/src/judges/prompts/retrieval.py`).

**How sure.** 5 turns, one model judge, nine-seat store. It gives a direction, not a score. Between runs, two things often changed at once (run 2 changed the line and the judge model; run 4 changed the cap and the judge prompt). The report's example of opposing lessons being merged does not appear in its own run 1.

**Overlap.** Blocks 40, 42, 44, 45 and 46 are already filed from here. Block 42 duplicates 38, and block 46 sits close to 26–27.

**Skill it would add.** None new. Block 45 already carries judge design.

**Candidate blocks.** Keep block 45. Add one caveat to it: the same retrieval scored relevance 4.30 under one judge model and 3.00 under another, so score levels do not carry across judges.

**Call: KEEP, trimmed.** Block 45 is the core. Block 40 stays as the Problem block. Fold 42 into 38, and 46 into 27.

### 43. `retrieval/per_day_discussion` — Look up lessons once a day?

**What it is.** July 2026, nine-seat. Each discussion turn runs a lookup, which costs an extra model call. Should a seat look up once a day instead? A $0 recompute over logged turns from 19 batches (3,265 seat-days with more than one turn) measured how often a seat's lookups changed within one day.

**What it found.**
- They almost always changed: the same set came back twice on only 0–9% of seat-days. So a per-day lookup is not a free saving.
- Most of the change was noise. The model reworded its search text every turn (word overlap about 0.26 in every batch), and even the most alike searches shared fewer than half their results.
- The first measuring rule found zero qualifying pairs. The log keeps that result in place, as the reason the rule was replaced.

**In today's design?** LIVE, decided on other grounds. Since 2026-10-12 a seat reuses its first lookup of the day until someone makes a new role claim (`Agents/memory/retrieval/lookup_cache.py`; v8 decision D4, about 60 lookups a game down to 38). D4 cites its own count, not this study. Its claim trigger is the kind of event trigger this log proposed.

**How sure.** Code only; it compares result ids, not what the advice says.

**Overlap.** `memory_system/v8/decisions.md` §10 (D4).

**Skill it would add.** None new.

**Candidate blocks.**
- Design · one sentence under D4: a July recompute had shown that per-turn lookups changed mostly through rewording.

**Call: MERGE INTO `memory_system/v8/` (D4).** The design it argued for is live, but the ruling rests on its own count.

### 44. `retrieval/reranking`

**What it is.** May 2026, nine-seat. After the store was cleaned of duplicates, strategy points still came back on the right topic but for the wrong moment, for example mid-game advice on day 1. The test was whether a model that re-orders the candidates by situation fixes this. The reranker was Flash-Lite, shown only the situations and the candidate texts, and it skips turns with 3 or fewer items. Five setups ran on 5 frozen turns, judged by 2.5 Flash with the group-first prompt.

**What it found.**
- Re-ordering alone raised strategy-point efficiency (the judge's 1–5 score for how little the set repeats itself; not a count) from 1.80 to 3.60. Redundancy (the share of items repeating another's lesson) fell from 72% to 40%, and relevance rose from 3.20 to 3.80.
- Filtering plus re-ordering scored below re-ordering alone (efficiency 2.20). Two fixes for one problem over-corrected.
- On the uncleaned store, re-ordering did about as well (relevance 4.00, efficiency 3.40), so for strategy points the reranker made store cleaning matter less.
- Observations did not need it: distinct lessons fell from 3.00 to 2.00.

**In today's design?** BUILT, OFF. Both switches are False in `DEFAULT_RERANKING_CONFIG` (`Agents/config/run.py`, still keyed by nine-seat roles); the code is `Agents/memory/retrieval/rerank_agent.py`. The served game retrieves strategy points only and reranks nothing. A cross-encoder was trained to replace this call but never wired in.

**How sure.** 5 turns, one model judge, nine-seat store. Direction only. The baseline and filter-only rows come from `dedup/store_retrieval_impact/`, not from this folder's run logs.

**Overlap.** Blocks 40, 41 and 42 are filed from here. `memory_system/effectiveness/` holds the reranked arm, and `fine_tuning/cross_encoder/` the replacement.

**Skill it would add.** Reranking. Block 41 is that tag's only filed carrier.

**Candidate blocks.** Block 41 stands. Add one clause: on the uncleaned store, re-ordering matched the cleaned store.

**Call: KEEP as filed (block 41; fold 42 into 38).** This revises the first pass's merge: block 41 is the only reranking block filed so far. When `fine_tuning/cross_encoder/` is walked, block 41 can shrink to its "what the cross-encoder replaced" line.

### 45. `role_set` — The nine-seat role design

**What it is.** June 2026. The question was which roles to add to the original four-role, two-side game. The result was the nine-seat game, built and smoke-tested on 3 games (2026-06-06).

**What it found.**
- The guiding rule: a cast built for measurement is not a cast built for play. The "lean" cast was the smallest that made a memory test measurable, because each role splits the memory store. The serial killer was the single test subject, and richer roles waited until memory was proven.
- Relaxed voting was added: "abstain" became a vote option, two days without an elimination force a vote, and there is a 12-day cap.
- In the smoke games, telling the agents the new roles existed was the one clear fix: serial-killer mentions went from 0 to 15 and 9 messages.

**In today's design?** SUPERSEDED by the ten-seat game dealt from twelve roles (`role_sheet.md`; tag `nine-seat-baseline`). Relaxed voting survives (`abstain_enabled` and `no_lynch_streak` in `Agents/nodes/day/flow.py`). The June rule "keep at least 3 plain villagers" was dropped: the ten-seat game deals none.

**How sure.** Design reasoning plus 3 memory-off games.

**Overlap.** Block 61: the abstain lesson the credit rules could not prune depends on the abstain vote that started here.

**Skill it would add.** None new.

**Candidate blocks.** —

**Call: SKIP.** The design was replaced, and its one surviving piece (abstain) is already told inside block 61.

### 46. `sequential_discussion`

**What it is.** June 2026, eight seats at first, then nine. The day discussion went from "everyone speaks at once each round" to one speaker at a time. Code picks the next speaker from the transcript: a seat that is asked or accused answers next, and back-and-forth between one pair of seats is capped. The vote stays blind and simultaneous. The folder includes the acceptance test (`quality_gate/`).

**What it found.** A hand-weighted score for choosing speakers was dropped for two hard paths, "owed an answer" and "offered a quiet turn". The reason: no guarantee, no stable weights, no one-line reason, no clean test. Seats tagged whom they addressed with 30 of 30 valid outputs and 0 invented targets, and where the model and a keyword rule disagreed, the model was right in all 11. Letting a seat judge whether its own point was new failed both ways (12 cases), while a separate judge rating someone else's line got 20 of 20 right both ways. In live games the bigger problem was echo on quiet turns, not domination, and the word-level metrics scored those days clean. The acceptance test showed word-level repeats at 0.00 against 0.05–0.06 for the old design.

**In today's design?** LIVE in part. The answer-next queue, the per-pair cap of 2 and the cooldown (1.0) are in `Agents/turn/scheduler.py` and `Agents/config/game.py`. The vote still fans out to everyone at once. Quiet-first picks were replaced on 2026-10-07 by a sweep in seat order. The repeat judge is today's echo gate: after recalibration on 2026-10-18 it held 12 of 29 restatements and none of 36 worthwhile lines. Human turns are now tagged by a model (`addressing_agent.py`).

**How sure.** The scheduler has unit tests (22 at the time). The acceptance test was 4 new games against 8 older ones, unpaired, judged by the implementer, with a word-level metric. The judge's own effect was never isolated.

**Overlap.** Lessons 15 and 16; `game_play_enhancement/` (the echo gate's recalibration).

**Skill it would add.** Deterministic orchestration: a scheduler with no model call, rebuilt from the transcript each turn.

**Candidate blocks.** Design (S1, S3, S8). Case study (S7, S12). Verification (S14). Gaps (S15).

**Call: KEEP.** It is today's discussion engine.

### 47. `store_curation`

**What it is.** How the memory stays bounded and keeps only what earns its place. It covers the rules for three stores: observations, lessons and tells (behaviour-to-role facts). It was written for the nine-seat learning loop on July 14–16, 2026, as a design review with rulings. It is not an experiment.

**What it found.**
- **A memory that only appends bloats.** The first paid loop run grew lessons from 0 to 227, with bloated cells around 34 against healthy ones around 5. This set a cap of 12 untested lessons per cell.
- **Removal needs evidence, never age alone.**
  - Prune a lesson whose lift (gain over memory-off play) is below −0.15 after at least 8 follows. On held-out games, 8 of 9 flagged lessons stayed negative (block 59).
  - Evict a lesson shown at least 8 times and never followed, but only if seats overrode it. If they said it did not apply, that is the search's fault and the lesson is spared.
  - An observation decays after 4 × its count generations without recurring. A window of 2 dropped about 250 a generation and starved synthesis.
  - Lessons with positive lift and at least 2 follows are never dropped.
- **Lesson text is never merged,** so its counts always describe one sentence.
- **The best unproven lesson gets a guaranteed retrieval slot,** because credit only reaches lessons that are shown.
- **The writer of new lessons is shown each old lesson's measured record,** so it does not rewrite losers.
- **Every paid step scales with new arrivals, not store size.** In one example, 32 searches dropped to 2.
- **Eleven store failures each got a named guard.**
- **Settings were pinned, not tuned,** because a sweep cannot be detected at an affordable N.

**In today's design?**
- LIVE, same values (`Agents/memory/consolidation/config.py:29–48`, `store_ops.py:129`, `strategy_synthesis.py:110–126`, `retrieval/plan_gating.py`).
- The tell side is OFF: no `WW_TELL_BOOK` in `server/`.

**How sure.** The mechanisms are unit-tested, and the prune check covered 31 lessons. Only the prune line was ever checked, and synthesis quality was never judged. Removal barely fires within a run: the ten-seat pass pruned 4 and evicted 4 of 498.

**Overlap.** Blocks 17–23, 59 and 61–62; `extraction/tell_extraction/` (tells); `credit/`.

**Skill it would add.** Memory lifecycle management, explore/exploit, cost bounded by arrivals, and settings governance.

**Candidate blocks.** Problem: 0 → 227 lessons. Design: evidence-based removal, guaranteed exploration slot, inflow-bounded cost. Gaps: the stores grow without plateau.

**Call: KEEP.**

### 48. `tracing` — capture (`report.md`, `implementation_notes/`)

**What it is.** Built in June 2026 on the nine-seat game; the report is dated 2026-06-27. Each gradable moment is saved when it happens as a self-contained "case". There are four kinds: a seat's turn, an extraction, a dedup decision and a day summary. A case holds what the seat saw, what memory returned (including the wider pool before reranking), what it did, and which store and settings it used. One shape goes to two places: self-hosted Langfuse and a local file per game. Langfuse was chosen over LangSmith (self-hosting is paid) and Phoenix (built for automatic capture); this was a judgment of fit, not a benchmark.

**What it found.**
- **The tracer cannot be the dataset.** Reading cases back out of traces failed on long games: in one session, 3 of 5 games built and Langfuse's query-cost guard refused 2. A cheaper call cut the case out of the output. Writing cases locally at game time fixed it. All 20 games of the next batch built, and the local and Langfuse copies held identical case ids.
- **Capture is checked against each consumer's needs.** Each consumer (judges, reranker training, replay) was listed with the fields it needs. That found 5 gaps; 4 were closed. On one seeded game, 72 of 72 cases recorded their store, and 46 of 72 held the pre-rerank pool; the rest had nothing to retrieve.
- Night actions became cases. In a smoke game the healer retrieved and used lessons on nights 2–4.

**In today's design?** LIVE. `freeze_case` runs at five sites: `Agents/turn/pipeline.py:303` and `:503`, `Agents/nodes/day/flow.py:488`, `Agents/nodes/orchestrator.py:567` and `Agents/memory/deduplication/pipeline.py:371`. Served games build the case sink and Langfuse handler (`server/game/game_session.py:277`, `:349`). Whether they write it to a local file: not found by grep. Wolf-night talk still saves no case (no `freeze_case` in `Agents/nodes/night/pack.py`).

**How sure.** Smoke games and one 20-game batch, nine-seat only.

**Overlap.** Block 3 (prompt-input capture is a later sibling). The reranker's training data comes from these cases.

**Skill it would add.** LLM tracing (Langfuse, OpenTelemetry) turned into frozen eval datasets.

**Call: KEEP (two blocks, plus the fingerprint lines).**

### 49. `tracing` — `fingerprinting/`

**What it is.** Built 2026-06-06 and audited 2026-07-23. Every batch record and trace carries a "runtime fingerprint": the git commit, whether the tree had uncommitted edits, a hash of the prompt files, the model names, temperature, thinking level and backend. Derived files get a manifest that hashes their input files. Prompts stayed in git rather than Langfuse's prompt manager, so there is one source of truth.

**What it found.**
- **A result needs three labels:** what was asked (run settings), what ran (fingerprint), and which files fed it (manifest). The honest claim is that drift shows up in the record, not that runs can be reproduced exactly. An uncommitted change is detected but cannot be rebuilt.
- **Its coverage drifted silently.** On 2026-06-16 the extraction and memory prompts moved into sub-folders. The hash kept reading only the top folder, the docs still said "all prompts", and no test failed.

**In today's design?** LIVE, gaps wider than recorded. `Agents/run_fingerprint.py:78` still globs only top-level files, and `Agents/prompts/roles/` (the role cards) is now nested too. The docstring names only extraction and memory. The backend field still says only Google or Vertex (`:104`), while the default player model is `anthropic/claude-haiku-5-5`. No test in `tests/` references the fingerprint. The v7 loop does refuse mixed fingerprints (`evaluation/src/loop/driver.py:343`). That memory games ran with "minimal" thinking, which meant zero reasoning tokens, comes from records outside this folder.

**Skill it would add.** Experiment provenance.

**Call: MERGE INTO the capture card.** Add one Design line and one Gaps line.

### 50. `v7_final` — the June loop runs and the guards they left (`runs/`, `report.md`, `experiment_log.md` §8b–§12f, `production_design.md`)

**What it is.** June 2026, nine-seat. A loop plays a batch of games (a "generation"), scores each lesson the agents followed, then rewrites, prunes and ages the store, and repeats. A lesson's "lift" is its average decision grade minus the memory-off average on the same kind of decision. There were two paid runs plus six smoke runs. This is the prequel to the signed July run (block 67).

**What it found.**
- Run 1 cost $65. Its credit was silently zero from generation 2: a list of file paths was joined into one string, and the file search matched nothing. That gave 340 follows and an empty ledger. Its memory-off baseline was also biased and unpaired.
- The rerun ("v2", $15) gave memory to every faction instead of town only. Its "wolves have no memory" noise floor did not exist, and its +0.41 town lift was a level measured against zero.
- The loop's own output degraded what it was testing. Lessons piled up: 0 to 227 in v2, 318 in run 1, with the median lesson followed about once. The gate built to stop this never fired at that cadence, and the evictor could not fire.

**In today's design?** LIVE:
- `evaluation/src/loop/invariants.py`: arm check, credit-engaged check, and `assert_baseline_coherence`, which forbids a base of zero.
- The deal is seeded from `game_id` (`Agents/nodes/orchestrator.py:89`).
- Retrieval serves proven lessons first, on by default (`Agents/memory/retrieval/plan_gating.py:152`).
- A cap of 12 unproven lessons per cell, and adoption counters merged back (`Agents/memory/consolidation/credit.py:349`).

The run results themselves are RECORD only.

**How sure.** The bugs were checked in code and logs, and the costs come from Langfuse. The slopes rest on 4–5 games per arm, with zero reasoning tokens. Do not cite `report.md`'s headline: it has the fusion error, "compounding OPEN" and a wolf positive.

**Overlap.** Blocks 61 (base at zero again), 63–67 and 10.

**Skill it would add.** Experiment-integrity guards: a harness that fails loudly, and a check that the arm declared is the arm that ran.

**Candidate blocks.** Case study: both invalid runs, each turned into a guard. Design: the lesson-bloat fix (proven-first retrieval).

**Call: KEEP (two blocks).**

### 51. `v7_final` — the free gates and the credit and prune design (`plan.md`, `gates/`, `consolidation_design.md`, `credit_backfill_ledger.json`, log §0–§6, §10)

**What it is.** June 2026, nine-seat, $0, run on 180 stored games. These are pre-registered go/no-go screens, plus the design of credit and pruning.

**What it found.**
- Agents follow almost every lesson they are shown: 334 follows against 3 overrides. So credit has to be the graded outcome of followed decisions.
- The average lift was +0.43 raw but +0.03 against memory-off play. The most-followed lesson (79 follows) was a net loser.
- Prune rule: drop a lesson after 8 follows if its lift is 0.15 or more below memory-off. This is a practical stand-in for a confidence interval; held out, 8 of 9 flagged losers stayed negative.
- Before any credit was built, the de-lucked grade of each decision type was checked against its side winning, with a shuffled-label null (G2). Town votes scored r = +0.56. The investigator's night find scored 0.00: finding a wolf does not win unless the find reaches a lynch.
- The similarity score could not tell useful retrievals from useless ones: 0.828 against 0.827 over 7,534 retrievals.
- A longer credit window drifts toward plain win/loss.

**In today's design?** Prune is LIVE: `prune_tau=-0.15` and `prune_min_follow=8` in `Agents/memory/consolidation/config.py`, plus the `follow/(follow+5)` damping. Wolf blend and healer save grades are LIVE (`grading.py`). G2 is standing code (`evaluation/src/instrument_validation/credit/g2_separability.py`). Gating is OFF.

**How sure.** Code run on stored games. The "not relevant" share is an upper bound. Everything is valid only within that model epoch.

**Overlap.** Blocks 56, 59, 82, 89 and 26.

**Skill it would add.** A permutation test (shuffled-label null) as a precondition check.

**Candidate blocks.** Verification: G2. Design: the prune rule. Embeddings: score blind to applicability.

**Call: KEEP (three blocks); merge the rest into 56/59.**

### 52. `v7_final` — credit-aware synthesis (`runs/synth_deluck_ab*/`, `synthesis_checks/`, log §4)

**What it is.** June 2026, nine-seat, two Serial Killer cells, judged by a read. Synthesis is the step that writes new lessons from stored observations.

**What it found.** Synthesis weighted observations by the extractor's verdict, which carries the win/loss halo. On the town side it flipped the worst lesson ("abstain", lift −0.20, 69 follows). On the Serial Killer side it reproduced the worst lesson almost word for word ("blend in, abstain", −0.30, 79 follows): there, the halo and the de-lucked grade disagree.

Feeding synthesis the lessons' realized track records produced a conditioned rule every time, on 3 of 3 clusters: blend for cover, pivot against an analyst in the endgame. That beat keeping the best existing lesson alone. It made no difference on night actions. A later instruction splits a rule that spans game stages into one lesson per stage, so each is found where it applies. Flash-Lite matched Pro at about 15 against 45 seconds a call.

**In today's design?** LIVE: `Agents/memory/consolidation/store_ops.py::_track_record` with `synth_track_min_follow=5`, and the split-by-stage text at `Agents/memory/strategy_synthesis.py:133–138`. The Flash-Lite model pin is SUPERSEDED (synthesis now runs on Sonnet 5.5).

**How sure.** A read of 2 cells of one role, never tested in play. The lexical carry-forward check could not trace paraphrases.

**Overlap.** Blocks 14 and 84 (verdict versus grade fed to synthesis) and 81.

**Skill it would add.** Feedback-grounded generation: generation conditioned on measured outcomes.

**Candidate blocks.** Case study: halo-weighted synthesis carried the Serial Killer's worst lesson forward; the track record fixed it.

**Call: KEEP.**

### 53. `v7_final` — extraction screens (`extraction_screens/`, `extraction_coverage_ab_spec.md`, log §7)

**What it is.** June 2026, nine-seat, mostly $0. The screens asked whether a cheap model extracts well enough, whether the quota pads, and whether pointing the model at pivotal turns helps.

**What it found.** The quota was not binding: 2.78 observations per game and cell, with 98% below the prompt's own floor of 6 and no near-repeats. The design principle that came out of it is that a missed lesson can never be recovered, while an extra one can be pruned, so extraction should lean toward catching too much.

Neither hinting at pivotal turns nor an "exhaustive" pass helped Flash-Lite: 3 of 12 flagged turns either way. The capture metric itself was wrong. It counted only observations that stated a parseable player count, so a read found Flash-Lite covering what the metric marked as a miss.

**In today's design?** The model pin is SUPERSEDED (block 76). The high-recall principle is a RECORD.

**How sure.** 3 games per screen.

**Overlap.** Blocks 73, 78 and 79 (the instrument was wrong before the model).

**Skill it would add.** None new.

**Candidate blocks.** None standalone.

**Call: MERGE into 78 (the recall principle) and 79 (the metric caught by a read).**

### 54. `v7_final` — discussion credit and the tagger (`discussion_credit/`, `discussion_credit_design.md`, `runs/v2_full/tagger_*.py`, log §8, §12g)

**What it is.** June 2026, nine-seat. The design for crediting discussion lessons, with a free "floor" built from the day's vote, and a paid tagger: one model pass per day that sees every role.

**What it found.** The tagger's day verdict mostly repeated the free floor (r = +0.55). Its unique value was judging night reads: it moved about 31% of night actions from luck to skill, with 30 good reads that missed and 12 blind picks that hit. The claim that its verdict leaks the outcome shrank three times under a 2×2 ablation. Blinded and controlled for verbosity, the verdict still predicted deceiver wins beyond the vote grade: wolf +0.56, Serial Killer +0.60, town +0.02, over N=24.

**In today's design?** SUPERSEDED. The tagger was retired from credit on 2026-07-13 (`invariants.py` docstring). The read/tactic split (block 57) replaced it.

**How sure.** 8–24 games, model-judged.

**Overlap.** Block 57 (one sentence of tagger history, by earlier ruling).

**Skill it would add.** None new: confound control is in block 82, leak detection in block 90.

**Candidate blocks.** One clause in block 57: the skilled-miss / lucky-hit split is a forerunner of scoring reads separately from tactics.

**Call: MERGE into 57; the rest SKIP.**

### 55. `v7_final` — the outside evaluator's review (`EVALUATOR_BRIEF.md`, `evaluator_review.md`)

**What it is.** July 2026. The owner wrote a brief for a read-only evaluator agent: facts and open questions only, no author verdict, no reruns. The evaluator returned verdicts on five axes and a plan, before the third paid run.

**What it found.**
- It caught the "+17pp p=0.013" fusion in the owner's own report: the raw arm was p=0.267; p=0.013 belongs to the reranked +33pp.
- A retracted halo was still live in the loop's credit path: tagger verdicts scored against a base of zero, with a tag cache that ignored the arm.
- The slope test was too weak by construction: about 1.7 standard errors at 5 generations. It proposed answering at the endpoint instead: freeze the evolved store and run a paired static test on the town measures.
- It found lesson bloat and the inert evictor.
- It found silent fallbacks, including a baseline that falls back to zero when a cell has no memory-off data.

**In today's design?**
- LIVE: the endpoint design became the July run (30 paired boards, final store against memory-off). The tagger was retired from credit on 07-13. The baseline guard and proven-first tiering landed on 07-15.
- The zero fallback is exactly block 61's second cause, found on 2026-10-22. Why the 07-15 guard missed it: not found.
- Baselines split by board state: OFF, never done.

**How sure.** Code-cited findings. The execution-plan report does not cite this review.

**Overlap.** Blocks 61, 62, 65 and 9-adjacent cost blocks.

**Skill it would add.** A commissioned independent review: a briefed evaluator agent with the author's verdicts withheld.

**Candidate blocks.** Case study: the review that reshaped the July run.

**Call: KEEP.**

### 56. `docs/agentic_ai_encountered_issues.md` — Served game hung on Vertex; rescue model

**What it is.** The record of model problems in the served game, from September 30 to October 1, 2026. Ten-seat era. Entry 1 is about the agents. Entries 2–3 are about the human's draft clock and the stage's pacing, which belong to the server write-up.

**What it found.**
- A hang is not an error, so the fallback never fired. One agent's draft took 301 s, of which 282 s sat in the retrieval call. Vertex's shared pool for a new model held requests for minutes, then bounced them with a 429 (rate-limit) error. The SDK and LangChain retried them silently, up to 30 times. The rescue path was keyed on errors and never saw one.
- The fix made time a failure. Each request waits 30 s and is sent twice, then the turn goes to a rescue model from another model family. After two stalls in a row, every turn starts on the rescue model for 300 s. That is a circuit breaker: after repeated failures, calls go elsewhere for a cooling-off period. The worst normal turn measured before the change was 11 s.

**In today's design?** LIVE. The constants are in `Agents/llm_factory/accessors.py` and `health.py`, with tests in `tests/engine/test_model_fallback.py`. Two parts of the doc are stale. Its status line says "committed, not deployed", but the owner's memory note says it was deployed 2026-10-01 at `a651988`. And its rescue pairing (3.6-flash → 3.5-flash) is Gemini-era: today the defaults are Claude and served games use a rescue model assigned by the registry.

**How sure.** One incident, diagnosed from logs. Stall rates since the fix were never measured. The viewer is not told when a turn ran on the rescue model, and there is no whole-game watchdog yet.

**Overlap.** None.

**Skill it would add.** Graceful degradation: timeouts, a fallback model from another provider pool, and a circuit breaker.

**Candidate blocks.**
- Case study · A turn hung for 301 s with no error, because 30 silent retries hid the stall from the fallback.
- Design · Time counts as a failure; two stalls move the game to a rescue model from another family for 300 s.
- Gaps · There is no notice to the viewer and no whole-game watchdog.

**Call: KEEP → block 97, one block (ruled 2026-10-22).** Opens the reliability topic. It is part of today's design, it carries a skill no filed block has, and the owner can defend it from one real incident.

### 57. `evaluation/dimension_extraction` — The situation-field audit, second copy

**What it is.** A summary page in the evaluation hub, from July 2026 (nine-seat game). It covers the $0 audit that checked the model-filled situation fields (players alive, vigilante bullets, "is this a swing vote") against values code computed from the game record. The audit itself lives in `extraction/situation_dimensions/dimension_accuracy_audit/`.

**What it found.**
- The model got the numbers it was handed right and the numbers it had to work out wrong. Players alive was 97% exact (6,099 cases), bullets left 16% (1,109), and the wolf side's "swing" 61% (439). That last one is worse than always answering "no", which scores 83%.
- A rule fixed before the run said: if any field the gate keys on scores under 80%, the earlier "gating does not help" result counts as unproven. The rule fired.
- The audit caught its own input bug first: 176 wolf night cases had an empty roster, which had produced a false over-count.

**In today's design?** LIVE (the fix). `Agents/memory/retrieval/situation_agent.py::_computed_dims` computes players alive, bullets and uses left, and ally revealed. Since 2026-07-11 it also computes the swing and parity numbers from the public census, so this page's claim that those two "stay model-filled" is out of date. Gating is off by default for each role (`plan_gating.py`).

**How sure.** Code computed the truth. The counts are decisions, not games, so cases within one game are correlated. The two class labels were never checked.

**Overlap.** Block 88 (same audit, same numbers), block 89 (the re-screen that was costed and never run), block 91 (class labels never validated).

**Skill it would add.** None new.

**Candidate blocks.** None.

**Call: MERGE INTO block 88.** Block 88 already carries every number from the source log, and this page is an out-of-date copy of it, so close it without reading.

### 58. `evaluation/end_to_end_ab` — How the whole-game memory A/B was run

**What it is.** A June 2026 hub page (nine-seat game) on the whole-game memory test. Thirty fixed deals (a game id's seed fixes roles and seats) were each played with memory on and with memory off, on the same day, then compared with paired tests on wins and on decision-level scores. The data and the verdict are in `memory_system/effectiveness/paired_ab/`.

**What it found.**
- Win rate cannot carry a verdict at this size. With 30 games per arm, only a win gap of about 35 points would reliably show up. Decision-level scores (vote accuracy, correct eliminations) carry the verdict instead.
- Pairing on the deal bought almost nothing. Two memory-off runs on the same 8 deals varied as much within a deal as across deals: spread 0.25 against 0.21–0.26 on vote accuracy. At temperature 1.0 the luck comes from how a game plays out, not from the deal. What mattered was running both arms at the same time.
- The first baseline was thrown out because a fresh one on identical code disagreed: town won 67% before, 10% in the fresh games (p=0.0028). The cause was model drift (see `model_drift/`).

**In today's design?** LIVE as the method. Deal pinning (`scripts/run_batch.py --game-ids-file`) and the paired tests in `evaluation/src/core/stats.py` remain. The July pre-registered run and the October evil-cover games (8 paired deals) both used them.

**How sure.** The seed finding rests on one pair of 10-game runs sharing 8 deals, nine-seat, one model. It undercuts block 65's stated reason for the design ("both copies share the deal's luck"), though the paired design still controls drift.

**Overlap.** Blocks 63–65; `evaluation/methodology/` (pending, carries the same seed finding); `model_drift/`.

**Skill it would add.** None new (paired A/B and power analysis are already filed).

**Candidate blocks.** Verification · pairing on the deal was measured and added almost no power; running the arms together is what controlled the error.

**Call: MERGE INTO `evaluation/methodology/`.** One walk covers both folders, but the seed finding must be squared with block 65's wording before the page goes out.

### 59. `evaluation/hallucination_bench`

**What it is.** A standing benchmark built on 3 October 2026. Frozen game turns are replayed under any prompt or model, and a judge counts statements that contradict the game. The folder also holds a code audit of how facts travel from the engine into prompts (12 findings), and its re-check a day later.

**What it found.**
- The errors repeat. The July census turns found wrong (227; 228 in the manifest) were replayed 3 times each under October prompts: 153 of 684 samples went wrong (22%), against 4 of 120 for correct controls (3%). A turn was kept only if it failed at least 2 of 3 times, because a July replay found 3 of 4 confirmed errors never recurred.
- The commonest error was hunting "the last wolf" when the prompt's own roster showed both wolves dead. Vigilante turns failed most (37%), investigator turns never (0%).
- The audit found holes in the fact path. The healer had no record of its own protections. The vote prompt dropped the seat's private note and then overwrote it. Engine facts and model summaries were rendered alike. A day later, 8 findings were addressed and 4 partly.
- Those fixes cut bad samples from 97 to 82 of 267 (36% → 31%). That was 24 cases better and 14 worse, p=0.14: a direction, not proof.
- The bench caught a bug in itself: replayed vote turns saw their own result.

**In today's design?** The tool is LIVE (`eval-hallucination-bench` in `pyproject.toml`), and so are the fixes (`Agents/rules/night_record.py`; 16 tests in `tests/engine/test_information_fidelity.py`). The frozen sets (v1 125 cases, v2 129) are nine-seat, and today's prompts do not render them (docstring of `evaluation/src/replay/hallucination_bench.py`).

**How sure.** The judge was right on 10 of 12 hand-checked verdicts. These are selected cases, not a population rate (the census is about 3% of messages). Day turns only.

**Overlap.** Block 9 (layout check on the bench), blocks 70–71 (frozen regression), 49 (facts as data); `game_play_enhancement/discussion_evidence.md` §6.

**Skill it would add.** Hallucination evaluation against a fact sheet built by code; screening for failures that repeat; a data-flow audit of the prompt path.

**Candidate blocks.** Verification · the fact-sheet judge plus the 2-of-3 screen. Case study · the audit (12 holes, 8 fixed in a day; 97 → 82 of 267, direction only). Gaps · nine-seat set, no vote-only or night cases.

**Call: KEEP.** Walk it with `discussion_evidence.md` §6.

### 60. `evaluation/hardening_pass` — Review and repair of the eval tools

**What it is.** An independent review on 2 July 2026 (nine-seat game) of the four evaluation methods the memory verdicts rested on, done before freezing those verdicts. It led to ten $0 fixes, the field audit, code-computed fields, a case sampler that cannot see outcomes, and the per-day replay design. The report is marked interim: the paid and human-labelling items were held.

**What it found.**
- The biggest finding was that the situation fields had never been checked. The audit re-opened the gating result (block 88's numbers).
- Silent failures were fixed:
  - The tagger swallowed errors, and its cache once served one arm's tags to the other.
  - The retrieval judge scored "fewer than 2 items" as maximum efficiency and pooled those scores into its averages.
  - A metric with the wrong sign was reported alongside the trusted ones. Later investigator finds correlate with wins (+0.38), but only because longer games have both.
- Nothing detected embedding drift, so a canary was built: 12 fixed text pairs re-embedded at batch start, crashing if any moves more than 0.02.
- The test suite went from 405 to 445 passing.

**In today's design?** Partly LIVE. The embedding canary runs in `scripts/run_batch.py` and was re-pinned at each embedder swap. The metric tiers (`DO_NOT_USE_METRICS`) are in `Agents/compute_metrics.py`, and the computed fields in `situation_agent.py`. The tagger fixes are retired. The gating re-screen was never run (block 89). I found no record here of the judge calibration or the label check being done.

**How sure.** The fixes are code plus unit tests. Apart from the audit, the folder has no outcome numbers of its own.

**Overlap.** Blocks 88, 89 and 91; `model_drift/` (the canary); `replay_screens/` (wolf-side coverage).

**Skill it would add.** None new.

**Candidate blocks.** None (its one Verification block would repeat 88–89).

**Call: SKIP.** Its one key finding is already block 88. The hygiene fixes are real, but none shaped today's design except the canary, which `model_drift/` carries.

### 61. `evaluation/labeling` — Model panels that agree can still be wrong

**What it is.** A June 2026 synthesis of three labelling rounds: dedup classifier, reranker, context-eval. Several models label every item, disagreements go to a person, and the labels are merged into a golden set. The code is in `evaluation/src/labeling/`. The statistics that would certify the panel are planned but not built (`plan.md`).

**What it found.**
- Three Gemini flash models labelled 863 dedup cases. Where they split, a "discard" majority was wrong 37% of the time and a "keep" majority 7%. Of 373 cases where all three said discard, 80 (21.4%) were overturned on review.
- A panel mixing vendors still shared a bias. It rated 44% of retrieval pairs fully relevant against ChatGPT's 31%. The panel models agreed with each other (71–74%) more than with ChatGPT (56–68%). Only the outside reader caught it.
- The lesson: agreement inside a panel cannot reveal a bias the whole panel shares.

**In today's design?** BUILT, not in the served game. The pipeline exists. Its two goldens fed the dedup classifier (closed) and the cross-encoder reranker (trained, never wired in).

**How sure.** The "human" reviews were Claude together with the owner (`fine_tuning/dedup_classifier/experiment_log.md:211`). The panel's rates were worked out by hand. Nine-seat stores.

**Overlap.** 28 (labels audited when every model fails the same cases, the mirror image of this), 93. Source records are in `fine_tuning/dedup_classifier/` and `fine_tuning/cross_encoder/reranker/`.

**Skill it would add.** LLM-assisted labelling with human review, and detecting bias that all annotators share.

**Candidate blocks.**
- Case study · Three models agreed on "discard" and were wrong 21.4% of the time (80 of 373); unanimity is not safety.

**Call: KEEP (one block).** It is a labelling skill no filed block shows and is easy to defend in an interview. The labelling sections of the two `fine_tuning/` folders can then close into it.

### 62. `evaluation/llm_judge`

**What it is.** An audit written 30 June 2026 (nine-seat) of six LLM judges: situation summary, retrieval, application, extraction, dedup quality and day summary. It has three per-judge notes and a golden-set method that was never built. Its question: which design decisions did a judge actually make?

**What it found.**
- Judges decided two things, both in May on the old pipeline: the extraction model (on 5–10 games) and version 2 of the application prompt (120 cases from 3 games). Three other calls went to better-anchored tools: a human-labelled key, a downstream measure and a manual read. Judges are good at catching faults and poor at ranking close options.
- An anchor ladder: tie a score to a real outcome, else to human labels, else compute it. A dimension that never moves gets deleted.
- Four ways judges failed. A score pinned at its maximum. Saturation by design: the day-summary judge saw the transcript, so "is this section present" scored 5.00 in every run. One pass both generating and judging. A score conditioned on who won.
- The retrieval judge gives efficiency 5 when fewer than 2 items come back and averages it in uncounted. This is still in today's code (`evaluation/src/judges/retrieval.py`).

**In today's design?** BUILT, not in the served game. Every judge runs on Haiku 5.5 since 2026-10-12 (`evaluation/src/judges/config.py`), and so does the default seat model (`DEFAULT_GAME_MODEL`, `Agents/llm_factory/accessors.py`). So the report's rule "the judge is a different model from the one it grades" no longer holds by default. None of the judges is calibrated.

**How sure.** No human anchor sits behind any score, and nothing has been judged on v7 or the ten-seat game.

**Overlap.** Blocks 45, 79 (judge fixes), 22 (dedup fabrication), 92–93 (the labelled key). The 0.70 → 0.55 retraction belongs to `memory_system/strategy_adoption/`.

**Skill it would add.** Judge anchoring: deciding what a score must be tied to before it can rank.

**Candidate blocks.** Design · judges as smoke alarms: the anchor ladder, the four failures, and the decisions that went to anchored tools instead.

**Call: KEEP (one block),** marked as uncalibrated nine-seat judges, now on the seat model. Add the fewer-than-2-items bug to block 45's gaps.

### 63. `evaluation/loop` — The v7 loop's measurement tools

**What it is.** A June 2026 hub page (nine-seat game) on how the v7 learning loop was measured. The tools were a model-free score per generation for a rising-trend test, rule-based credit for each decision, the discussion tagger, and checks that stop a bad run. It was written before the signed v7 run.

**What it found.**
- Both paid loop runs before the signed one were invalid, and audits caught both. One had an unpaired baseline. The other silently gave memory to the wolves as well (a driver default), so the "town only" control was really a treatment arm. About $130 was lost. An "arm guard" now refuses to run when the declared and actual memory settings differ.
- The tagger "validated" as a measure of wolf and killer discussion skill (N=24, correlational only). The owner has since ruled the tagger out of the write-up.
- Consolidation quality was never measured, and the eviction rule did nothing (`retrieved_count` was never wired).

**In today's design?** SUPERSEDED. The power study dropped the trend test (blocks 64–65). The credit rules were ported to the ten-seat `Agents/memory/consolidation/` (blocks 58–59). `evaluation/src/loop/` last changed on 2026-07-21, and the arm guard is still in `invariants.py::assert_arm_factions`.

**How sure.** The page predates the signed run, which closed negative (−0.147, p≈.06, pre-registered, all games with zero reasoning tokens). Its "cheapest upgrade" is that run.

**Overlap.** Blocks 58–59 and 63–67; `v7_final/` (pending: the config slip and the arm guard); `discussion_tagger/` (closed).

**Skill it would add.** None new. Block 3 carries invariant checks.

**Candidate blocks.** Case study · a config slip ran a treatment as the control; the guard now turns that slip into a crash at generation 1 (file it at `v7_final/`).

**Call: SKIP.** Every live piece is covered elsewhere, and its one good story, the arm guard, belongs to `v7_final/`.

### 64. `evaluation/methodology` — Keeping a 30-game A/B honest

**What it is.** June 2026, nine-seat. An audit of the guards that keep a memory-on versus memory-off comparison fair at 30 games: drift guards, pairing arms on the same deal, a check that each arm really has the settings it claims, and power. It also covers three statistics fixes an advisor proposed (`variance_reduction_levers.md`).

**What it found.**
- Results drifted with no code change. Ten fresh memory-off games came back with villagers winning 10%, against 67% before (Fisher test p = 0.0028). The rule since: run both arms in the same window, and never compare against an old baseline.
- Pairing the arms on the same deal bought almost no variance reduction. Games varied as much within one deal as across deals (spread 0.249 against 0.21–0.26). What made the comparison fair was running in the same window.
- At 30 games a side, only a win-rate gap of about 36 points is detectable. That is why the proxies carry the signal.
- A covariate adjustment (CUPED) was ruled out: nothing measured before a game predicts its result.

**In today's design?** LIVE in part. Every run is stamped with model, backend and prompt hash (`Agents/run_fingerprint.py`). An embedding drift check now runs at the start of every batch (`scripts/run_batch.py:551`). The arm check lives only in the finished v7 loop. `run_batch` still does not alternate arms.

**How sure.** The drift result is 10 games against an earlier baseline. The numbers live in `model_drift/drift_surfaces_and_guards.md`, not here.

**Overlap.** 63–65 (power, paired design); `model_drift/` holds the source.

**Skill it would add.** Drift detection (the provider's behaviour changing under you).

**Candidate blocks.**
- Case study · Byte-identical prompts, no code change, and the baseline moved (villagers 67% → 10%, p = 0.0028), so every comparison runs both arms in the same window.
- Verification · The design's own check refuted pairing as the source of fairness: the deal explained almost nothing.

**Call: MERGE INTO `model_drift/`.** The drift case is key to how every later A/B was run, but its numbers and the fuller story live in `model_drift/`, so it should be filed from there.

### 65. `evaluation/metrics` — Which game proxies actually track winning

**What it is.** June to July 2026, nine-seat. A summary of the top-level `metrics/` folder. A "de-lucked proxy" is a rate that counts what a role did with its chances, such as how often a town vote hit an evil player. Each proxy was checked by correlating it with its own side winning.

**What it found.**
- The town basket holds: correct eliminations +0.65, mislynches −0.65, over 50 games, and again over 180. No other basket fully passed.
- The investigator's find-rate does not track winning. What does is whether a find led to a lynch (+0.40). An early "wrong-sign" scare (p = 0.039, 30 games) faded to nothing at 180.
- A wolf proxy looked null pooled because wolves cannot win in 77 of 180 games (the lone killer wins by default). In the 103 games where they can, it is +0.31.
- One sign was registered in advance and came out reversed. Wolves who accuse town players lose more (−0.33).

**In today's design?** LIVE in nine-seat form. The tiers (validated, diagnostic, do-not-use with a `dnu_` prefix) are in `Agents/compute_metrics.py:688`. `Agents/ten_seat_metrics.py` says every ten-seat proxy is unvalidated and none is pushed as validated.

**How sure.** Code computes everything, $0. About 30 proxies were tested with no built-in multiple-comparison correction. Everything is nine-seat.

**Overlap.** 58 (credit grading rules), the parked "grade the decision, not the result" lesson, and `metrics/` (the source).

**Skill it would add.** Metric validation (checking a proxy against the outcome before trusting it).

**Candidate blocks.**
- Verification · Proxies were checked against winning before use; only the town basket passed.
- Case study · A wolf proxy hid behind a condition: null pooled, +0.31 once only games wolves could win were counted.
- Gaps · No proxy has been validated on the ten-seat game.

**Call: MERGE INTO `metrics/`.** The finding is key (credit and every A/B rest on it), but this file only points at `metrics/`, which is where the walk should happen.

### 66. `evaluation/replay_screens` — Frozen-turn memory screen and an unbuilt day replay

**What it is.** A July 2026 hub page (nine-seat game) on two instruments cheaper than a whole game. The first is the per-turn "decision replay": freeze one recorded turn, swap only the memory block, regenerate the turn and score it against the true roles. The second is a per-day replay, which exists only as a design. The memory findings themselves are in `memory_system/effectiveness/decision_replay/`.

**What it found.**
- The screen points the same way as whole games: town memory helps, while wolf and killer memory do nothing. The screen's town gain was +0.078 value per day-2 decision. The whole-game side it is compared with is +17 points (not significant, p≈0.27) and +23 points (p≈0.17), at N=30. Never cite these as significant.
- Used as a $1 filter, it found every cheap way to make seats use memory better was null or harmful. For example, forcing a "does this lesson apply?" verdict dropped vote quality from 0.75 to 0.55 (N=20).
- The July fix: the screen could not replay a wolf, vigilante or killer vote, which is where the open questions were. A wolf scoring lens was added.

**In today's design?** BUILT, little used for memory since. The screen was ported to the ten-seat roles on 2026-10-09 (`evaluation/src/replay/decision_screen/`). The per-day replay was never built: no `day_replay.py` exists.

**How sure.** It reruns one frozen turn, so it misses knock-on effects. Cells are small (±5–9 points) and it ran on one model. The page says an earlier "−40 point town collapse" was model drift, but the paired A/B log says it was drift plus the treatment, in unknown proportion.

**Overlap.** Block 53 (replay screens), block 70 (regression testing on frozen state). The findings belong to `memory_system/effectiveness/` (pending).

**Skill it would add.** None new.

**Candidate blocks.** Verification · a $1 frozen-turn screen eliminated every cheap memory-use idea before any $20 game run (file it at `memory_system/effectiveness/` if that walk keeps it).

**Call: SKIP.** Blocks 53 and 70 already cover the method, and what the cheap-idea screening taught belongs to the `memory_system/effectiveness/` walk.

### 67. `evaluation/report.md` — The trust ledger for every measuring tool

**What it is.** A hub written 27 June to 2 July 2026 for the nine-seat game. It separates three questions: does a design work, how do we measure it, and can that measurement be trusted. It tags each tool from "validated" down to "deferred", and code-checked ten of the claims on 28 June.

**What it found.**
- The trusted tools were the ones that ran without a model: the town score proxies (they tracked winning at a correlation of about 0.6 over 50 games), the dedup scorer against human labels, and the loop's code-only measure. Every live LLM judge was uncalibrated.
- The tools caught their own errors six times. Example: a fresh baseline drifted with identical prompts (p = 0.0028). Each of the six is recorded in another folder.
- Its headline, "town memory helps +17/+23pp", is the nine-seat v5 static-memory result. The plain +17pp arm was not significant (p = 0.267).

**In today's design?** RECORD ONLY. It was written before v7 closed negative (signed July run, −0.147, p ≈ .06) and before the ten-seat game. Its bottom line still counts the discussion tagger as a "validated metric", and the owner ruled the tagger out on 2026-10-22.

**How sure.** The tags are its authors' own reading (one AI code-check pass). Most numbers come from v4 stores, May prompts and a Gemini backend.

**Overlap.** 37, 63–67. Each "caught itself" item belongs to `model_drift/`, `v7_final/`, `metrics/` or `memory_system/strategy_adoption/`.

**Skill it would add.** None new. Its "trust the anchored tools, treat judges as smoke alarms" idea is told better in `llm_judge/`.

**Candidate blocks.** —

**Call: SKIP.** Nothing in it is first-hand, it is stale on the facts that matter most (v7, ten seats, the tagger), and its "self-correction" list is a useful checklist of where to look in the other folders.

### 68. `evaluation/sampled_human_review`

**What it is.** Most nine-seat prompt decisions were made by reading a few cases by hand: extraction wording, situation-summary wording, the dedup tricky cases, the day-summary saturation call. The reading was ad hoc and left no record. On 2 July 2026 a sampler was built to fix this. It picks cases by a code-computed decision score and a code-computed swing count, adds a seeded stratified group, keeps replay switched off until spend is approved, and writes verdicts to a file.

**What it found.**
- The sampler refuses to pick cases by outcome: `assert_outcome_blind` raises on "winner" or "won". This turns the outcome-halo rule into code.
- Its swing signal comes from code, not the model's own field, because the model's field scored 0.606 (worse than always answering "no"; block 88).
- One $0 test run on old nine-seat data produced 9 review packets and 1 placeholder verdict ("pending", reviewer `model:demo`). It was never used for a real review. The reason counts add to 10 for 9 cases, presumably because one case carries two reasons.

**In today's design?** BUILT, unused: `evaluation/src/diagnosis/sampler.py`, the CLI in `evaluation/src/cli_runner/diagnosis/case_sampler.py`, and tests. Outside this folder only `hardening_pass/` mentions it.

**How sure.** One test run, no review.

**Overlap.** Blocks 14 and 82 (outcome halo), 60 (sampled audit), 88 (computed swing).

**Skill it would add.** None new.

**Candidate blocks.** None of its own. Add one line to block 82: the no-outcome selection rule is enforced in code. The "reading by hand was the workhorse, unrecorded" framing goes into the llm_judge block's anchor ladder.

**Call: SKIP,** with those two one-line merges.

---

## Appendix: every finding and every file, large folders

### `evaluation/hallucination_bench`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Most July errors were one-off slips, so candidates were replayed and kept only if they still failed 2 of 3 times | 3 of 4 confirmed July cases never recurred; 44 curated cases kept | LIVE (tool) | reproducible-failure screening | KEEP | `report.md` |
| 2 | Errors on failing turns repeat under today's prompts; controls stay clean | 153/684 (22%) vs 4/120 (3%); Flash-Lite, 3 samples a case | RECORD | hallucination evaluation | KEEP | `report.md` |
| 3 | The commonest error is miscounting who is left; error rates differ by role | vigilante 37%, investigator 0% | RECORD | — | KEEP (exhibit line) | `report.md` |
| 4 | The judge checks each statement against a fact sheet built from the game record (cheap reader, stronger re-reader of positives); pinned cases carry written expectations | 10 of 12 hand-checked right; both misses were a fact-sheet bug (one attacker named of two), fixed | LIVE | hallucination evaluation, generator-verifier separation | KEEP | `report.md` |
| 5 | The case freezes the game state, not the prompt, so any prompt version or model can replay it; old cases carry June-written history | — | LIVE | frozen-state replay | MERGE→block 70 | `report.md` |
| 6 | Four slices answer separate questions (fix check, model choice, false alarms, regression); compare models on the random slice, because the curated one leans toward the screen model's mistakes | 44 / 40 / 40 / 1 (v2 adds 4 pinned) | LIVE | eval-set design | KEEP (inside F4's block) | `report.md` |
| 7 | The bench caught its own leak: replayed vote turns saw their own result; the July ship test had the same flaw, so its vote error rates run high | caught by reading controls by hand | RECORD | data leakage | KEEP (cross-ref block 90) | `report.md` |
| 8 | A live invented investigator check cost the town the game; the wording of the results caused it | 20/20 old wording vs 0/20 new | RECORD | — | MERGE→`discussion_evidence.md` §6.2 | `report.md` |
| 9 | A code audit traced each fact from engine to prompt and found 12 holes (healer's own history, vote dropping the note, withheld speech kept as "said", engine facts and summaries alike, wolf night without census, and others) | 12 findings; offline checks only | LIVE (fixed) | data-flow audit | KEEP | `code_audit_2026_10_03.md` |
| 10 | A day later, 8 were addressed and 4 partly; the leftovers are listed (delivery warning lasts one day; compact claim ledger drops evidence; a dead investigator's check missing from extraction) | 8 + 4 of 12; 53 tests passed | LIVE | — | KEEP (inside F9's block) | `fix_verification_2026_10_04.md` |
| 11 | On the bench, the fixes moved errors in the right direction only | 97 → 86 → 82 of 267; 24 better / 14 worse; p=0.14 | LIVE (fixes deployed) | regression benchmark | KEEP | `fix_verification_2026_10_04.md` |
| 12 | Counting fix: "checkable statements" are whole messages and notes, not single factual claims | notes 77/155 vs 67/151 | RECORD | — | MERGE→F11 (caveat) | `fix_verification_2026_10_04.md` |
| 13 | Limits: nine-seat set does not render on ten-seat prompts; day turns only; selected cases, not a population rate | v1 125, v2 129 cases | LIVE limit | — | KEEP (Gaps) | `report.md`; `evaluation/src/replay/hallucination_bench.py` |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/evaluation/hallucination_bench/code_audit_2026_10_03.md` | Engine-to-prompt fact-flow audit, 12 findings | F9 |
| `evidence/evaluation/hallucination_bench/fix_verification_2026_10_04.md` | Re-check of the 12 fixes; bench before and after | F10, F11, F12 |
| `evidence/evaluation/hallucination_bench/report.md` | Bench design, v1 screen, trust notes | F1–F8, F13 |

### `evaluation/llm_judge`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Judges drove only two design calls: the extraction model and the version-2 application prompt, both in May, pre-v7 | 5–10 games; 120 cases from 3 games | RECORD | judge anchoring | KEEP (core of the new block) | `report.md` §1 |
| 2 | Three calls went to anchored tools because judges could not rank close options: a labelled key (situation summary), a downstream measure (retrieval depth), a read plus latency (day-summary model) | −0.08 option dropped, +0.06 kept | RECORD | judge anchoring | MERGE→new block (cross-ref 43, 92) | `report.md` §1 |
| 3 | Anchor ladder: outcome, then human key, then computation; a five-row table of fixes by kind of dimension | — | RECORD (method) | measurement validity / judge anchoring | KEEP | `report.md` §5 |
| 4 | Four judge failures: pinned dimension, saturation when the judge sees the answer, generate and judge in one pass, outcome halo | — | RECORD | LLM-as-judge | KEEP (in the new block) | `report.md` §5; `agent_decision.md` |
| 5 | Day-summary judge: two "is it present" dimensions sit at the maximum because the prompt forces those sections; the three grounded ones caught real failures but cannot rank versions | village dynamics 5.00 every run; evidence type 4.89–5.00; ±1 swing per pair; 18 pairs, 8 games | SUPERSEDED (day summary now transcription plus a code ledger, block 69) | LLM-as-judge | MERGE→new block (the saturation example) | `day_summary.md` |
| 6 | Extraction judge prompt bugs fixed (wrong field, wrong scope); the original 5 dimensions cluster at 4 | 2.81→4.00, 3.19→3.88; 48 games; only strategy depth (3.95) and novelty (2.95) varied | RECORD | judge validation | MERGE→block 79 | `extraction.md`; `report.md` |
| 7 | Retrieval judge: fewer than 2 items gets efficiency 5, averaged in with no counter; archived tables unaffected (an older judge returned nothing) | — | LIVE bug (`retrieval.py` l.24, l.49) | — | MERGE→block 45 (gap) | `agent_decision.md`; `report.md` §6 |
| 8 | Application judge: following a lesson stays near 50% across prompt versions; the calibration plan (about 28 blind cases, half a day) was never run | 49–52%; 120 cases from 3 games; one game swings v3 | PLAN / RECORD | — | MERGE→`memory_system/strategy_adoption/` | `agent_decision.md`; `report.md` §6 |
| 9 | Dedup quality judge: the merge writer invents details; a faster model invents none but drops fields; the same model writes and judges | 3 of 9 merges; 3.5 Flash 0% | OFF (merge path off) | — | MERGE→blocks 19, 22 | `report.md` §4 |
| 10 | The situation-retrieval golden set has two scoring formulas that disagree, and grew by model labels that no person re-checked | NDCG@10 0.83 (linear) vs 0.732 (exponential); about 20 human cases → 108 cases / 1,919 judgments | RECORD | — | MERGE→blocks 92–93 (caveat) | `agent_decision.md` |
| 11 | An instruction hidden in a schema field was ignored: the model skipped about a third of its notes, inflating engagement | about 0.70 → 0.55; coverage 0.27 → 0.97; 48 cases | RECORD | — | MERGE→`memory_system/strategy_adoption/` | `report.md` §1; `extraction.md` |
| 12 | A recall metric that counts parseable text was confounded by wordiness; a manual read found the same kill sequences | Flash-Lite 25% vs Pro 100%; 3 games | RECORD | metric validity | MERGE→`v7_final/` | `extraction.md` |
| 13 | Harness rules: one central model, judge ≠ generator, the same judge on both arms, failed parses dropped, backend stamped per run | — | PARTLY LIVE: central model yes; judge ≠ generator broken (judges and seats both Haiku 5.5) | — | MERGE→new block (caveat) | `report.md` §2 |
| 14 | Day-summary harness silently dropped failed pairs; fixed to report N of 18 | no historical pair dropped | RECORD | — | SKIP | `day_summary.md` |
| 15 | Reference-point golden set (the Pyramid / FActScore method: atomic points, the judge quotes before crediting, recall and precision apart) planned for the extraction-family judges | — | PLAN (never built) | reference-based evaluation | MERGE→block 78 (one gap line) | `golden_set_method.md` |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/evaluation/llm_judge/agent_decision.md` | Judges for situation summary, retrieval, application | F4, F7, F8, F10 |
| `evidence/evaluation/llm_judge/day_summary.md` | Day-summary judge note: saturation, silent drops | F5, F14 |
| `evidence/evaluation/llm_judge/extraction.md` | Extraction judge note: bug fixes, flat dimensions | F6, F11, F12 |
| `evidence/evaluation/llm_judge/golden_set_method.md` | Reference-point golden-set method, never built | plan only (F15) |
| `evidence/evaluation/llm_judge/report.md` | Audit of six judges and what they decided | F1–F4, F7–F9, F11, F13 |

### `evaluation/sampled_human_review`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Most nine-seat design calls were made by reading cases by hand, with no sampling and no record | — | RECORD | — | MERGE→llm_judge anchor-ladder block | `report.md` |
| 2 | Three ways to check quality, cheapest first: judge, then sampled reading, then golden labels; sampling feeds labelling | — | RECORD | — | MERGE→llm_judge block | `report.md`; `plan.md` |
| 3 | The sampler selects on a code decision score plus a code swing count, never the model's field | model's swing field 0.606, worse than a constant | BUILT, unused | — | MERGE→block 88 (one line) | `report.md` |
| 4 | Selecting on outcome raises an error, so the halo rule is code | 14 tests | BUILT, unused | — | MERGE→block 82 (one line) | `report.md`; `plan.md` |
| 5 | Test run: 9 packets, 1 placeholder verdict; never used for a real review | 9 cases (reasons 3 outlier + 3 swing + 4 stratified = 10) | RECORD | — | SKIP | `sampler_smoke/*` |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/evaluation/sampled_human_review/plan.md` | Sampler build plan, four steps | plan only (F2, F4) |
| `evidence/evaluation/sampled_human_review/report.md` | Why hand review needs a sampler; build note | F1–F5 |
| `evidence/evaluation/sampled_human_review/sampler_smoke/cohort_strata.json` | Test-run counts by role, phase, reason | data for F5 |
| `evidence/evaluation/sampled_human_review/sampler_smoke/review_packets.md` | Nine review packets from the test run | data for F5 |
| `evidence/evaluation/sampled_human_review/sampler_smoke/verdicts.jsonl` | One placeholder verdict exercising the record path | data for F5 |

### `extraction/tell_extraction`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Discovery is kept apart from measurement. The miner may see the roles, but its counts are never used. A role-blind detector counts in other games, and code joins the roles | — | OFF (`evaluation/src/loop/tells.py`, `LoopConfig.tells = False`) | generator-verifier separation, blind annotation | KEEP | report.md §1–2; experiment_log.md ① |
| 2 | A ban on role words was wrong both ways. The working rule became: could a reader who cannot see the roles check this behaviour? | v1 177, v2 184, v3 181 candidates; quote defects about 6% → 1%; quote checker 54 of 177 flagged → 11 after fixing punctuation (most flags were formatting) | OFF | prompt engineering, operational labelling rule (pairs with block 29) | KEEP (small) | experiment_log.md ②; report.md §1 |
| 3 | Split calls rescued the cheap miner. With the vote list removed, the discussion call stopped being drowned by it | Flash-Lite 116 → 213 candidates, exactly repeated wordings 0 → 19 rows; Pro single call 181 / 24; sweep estimate $15–30 → $2–3 (later shown too low) | OFF | task decomposition | MERGE→lesson 80 | experiment_log.md ③; report.md §4 |
| 4 | Merging duplicate wordings: word overlap found almost nothing, and embedding scores were bunched together, so judgments went to ranked nearest neighbours. Being common is no reason to drop a behaviour | Word overlap (TF-IDF) found 10 pairs, against about 14 variants of one behaviour found by reading; median embedding similarity 0.84, so a fixed cutoff let in 2,837 pairs; 213 rows → 166 entries (1 of 44 merges doubtful); strong-model review 166 → 107 | OFF | embedding limits | MERGE→embeddings topic (blocks 26, 39) | experiment_log.md ④ |
| 5 | No plateau. New wordings kept arriving, but few came back. So active measurement was capped, duplicate judgment was batched every ten games, and an entry's text is never rewritten | 1,109 candidates from 30 games → 740 entries, about 22 new a game in games 21–30; batch review 740 → 596 (24 identical-string bug), about 16 a game; share of new entries seen again 37% → 19% → 11%; the per-game judge made 5,350 calls (about 178 a game) and still split one behaviour across 3 wordings (seen 18, 11, 10 times) | OFF (cap of 48 in `tell_fold.py`, loop off) | bounded work, batch over online judgment | KEEP | report.md §5; experiment_log.md ⑤–⑦ |
| 6 | The role-blind detector was checked on 40 cases labelled by blind model adjudicators. A fix could help one channel and hurt the other; combining two views of the record recovered missed multi-day patterns | First detector: discussion 10 of 11 right, vote 7 of 10, found 67% / 54%. Combined: discussion 0.93 / 87%, vote 0.77 / 77% (0.83 / 77% cached). Half the cases came from the detector's own detections; about 36 calls a game | OFF | golden-set construction, blind annotation | KEEP | experiment_log.md ⑧; report.md §4 |
| 7 | Owner check: a two-phase protocol. First a blind read; then every tool's candidates are pooled, shuffled and shown with no source, so agreement cannot sway the owner, and recall is bounded by the pool. Only 1 of 6 games was done | 7 of 8 detections upheld (one rejected for "at the last moment"); four IDs described one event; the sampler's seeded picks shifted when the code changed, so the players were written into the bundle | RECORD | golden-set construction, pooled adjudication (pairs with block 93) | KEEP | outputs/owner_golden/README.md; owner_verdicts.json; experiment_log.md ⑪ |
| 8 | On 60 games the miner never saw, some behaviours separated roles strongly | 2,160 calls, 5,151 detections; counter-accuses using a role claim as a distraction 27 of 30 evil; discourages relying on vote records 41 of 48; calls accusations a diversion 60 of 76; publicly claims a role 0 of 28; refuses to give a source 10 of 11 investigator. About 96 behaviours scanned, 12 deals shared, no significance test | OFF | held-out validation of mined patterns | KEEP | report.md §4; experiment_log.md ⑨; heldout/provisional_lift_table.json |
| 9 | The paired memory arms reuse game IDs, so counting by ID alone merged distinct games. Fixed by keying on arm plus game. The same trap refuted one case of the old hallucination baseline (`generation_prompt/` F3) | 5 arms × 12 deals; this restores distinct games, not independent ones | RECORD | data provenance, join-key hygiene | KEEP (small; a cross-folder pair) | experiment_log.md ⑨; scripts/heldout_lift.py |
| 10 | The detection pass cost several times its estimate | $13 billed against $1.50–2.50 estimated (thinking tokens, old prices) | RECORD | cost attribution | MERGE→block 10 | experiment_log.md ⑨ |
| 11 | Caching made the detector less repeatable but no less accurate. Even uncached it was not exactly repeatable, which corrected an earlier "deterministic" reading. So every evaluation keeps the stored output, and a rerun counts as a new sample | Rows matched 0.56–0.83 between identical cached runs, against 0.90–1.00 uncached; minimum thinking found 0 of the labelled days against 2 (six cases) | OFF | reproducibility of a non-deterministic instrument | MERGE→`caching/` §4.7 (cost topic) | experiment_log.md ⑩; report.md §4 |
| 12 | Never merge a narrow behaviour that predicts roles into a broad one that does not | 7 broad behaviours with near-zero association contained narrower ones that had one | RECORD (not in `tell_fold.py`) | — | MERGE→`store_curation/tells.md` | experiment_log.md ⑪; granularity_screen.json |
| 13 | The book reaches decisions: replayed votes changed. The first book was filled entirely by discussion behaviours, so slots were reserved per role and channel | First book: 7 of 40 changed, correct 18 → 17. Balanced 12 entries: 11 of 40 changed, 20 → 24 (5 wrong → right, 1 right → wrong, one-sided p about 0.11); the no-book baseline itself moved (18 against 20) | OFF | replay screen | KEEP (small) | experiment_log.md ⑫; book_screen*.json |
| 14 | Books are chosen by how concentrated the role a behaviour points at is, town roles included (owner ruling: a shared book cuts both ways) | 34 entries; never replayed; some entries only +0.03–0.06 above their seat share | OFF | — | MERGE→card T1 | experiment_log.md ⑬ |
| 15 | Score = (c + 5p)/(n + 5) − p, pulled towards zero with few exhibitors; no correction for testing many behaviours | top entry 0.549 (10 of 11) | OFF | shrinkage for small samples | MERGE→block 59 | report.md §2 |
| 16 | The July learning run carried a 33-entry book alongside the town's lessons. An amendment dropped the arm that would have separated the two, so the tells' own effect is unknown | −0.147, p ≈ .06 (whole memory) | RECORD | — | MERGE→block 67 | experiment_log.md ⑭; report.md §6 |
| 17 | Not ready for ten seats: the v1 book cannot be read by today's hook, and 12 of the v2 book's 34 entries name roles the ten-seat game lacks | no ten-seat game mined or scanned | OFF | — | MERGE→block 62 (gap) | report.md §3; experiment_log.md ⑮ |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/extraction/tell_extraction/report.md` | Mechanism report, revised at `c0732f88` | F1, F2, F5, F6, F8, F13, F15, F16, F17 |
| `evidence/extraction/tell_extraction/experiment_log.md` | Dated build log ①–⑮ | F1–F17 |
| `evidence/extraction/tell_extraction/outputs/adj_input_*.json` | Per-game adjudicator inputs (5 games) | data for F6 |
| `evidence/extraction/tell_extraction/outputs/adjudication_raw_*.json` | Per-game raw adjudicator verdicts (5 games) | data for F6 |
| `evidence/extraction/tell_extraction/outputs/adjudication_cases.json` | The 40 labelled detector cases | data for F6 |
| `evidence/extraction/tell_extraction/outputs/golden_verdicts.json` | Merged 40 model-golden verdicts | data for F6 |
| `evidence/extraction/tell_extraction/outputs/transcripts/*.txt` | Role-blind transcripts for adjudicators (5) | data for F6 |
| `evidence/extraction/tell_extraction/outputs/checklist_v0.json` | Frozen v0 checklist the detector scanned | data for F6, F7 |
| `evidence/extraction/tell_extraction/outputs/book_screen.json` | First-book replay, 40 votes | data for F13 |
| `evidence/extraction/tell_extraction/outputs/book_screen_v2_balanced.json` | Balanced-book replay, 40 votes | data for F13 |
| `evidence/extraction/tell_extraction/outputs/canonicals_discussion.json` | 103 merged discussion entries | data for F4 |
| `evidence/extraction/tell_extraction/outputs/canonicals_vote.json` | 63 merged vote entries | data for F4 |
| `evidence/extraction/tell_extraction/outputs/canonicals_audited.json` | 107 entries after strong-model review | data for F4 |
| `evidence/extraction/tell_extraction/outputs/distinctness_review_discussion.json` | Strong-model keep/merge review, discussion | data for F4 |
| `evidence/extraction/tell_extraction/outputs/distinctness_review_vote.json` | Strong-model keep/merge review, vote | data for F4 |
| `evidence/extraction/tell_extraction/outputs/dedup_v0_clusters.json` | Word-overlap duplicate clusters | data for F4 |
| `evidence/extraction/tell_extraction/outputs/dedup_v0_1_clusters.json` | Embedding duplicate clusters | data for F4 |
| `evidence/extraction/tell_extraction/outputs/ledger_sim_metrics.jsonl` | Per-game metrics of 30-game simulation | data for F5 |
| `evidence/extraction/tell_extraction/outputs/ledger_sim_store.json` | 740-entry simulated store | data for F5 |
| `evidence/extraction/tell_extraction/outputs/consolidation_input_discussion.json` | Batch-review input, discussion | data for F5 |
| `evidence/extraction/tell_extraction/outputs/consolidation_input_vote.json` | Batch-review input, vote | data for F5 |
| `evidence/extraction/tell_extraction/outputs/consolidation_clusters_discussion.json` | Batch-review merge clusters, discussion | data for F5 |
| `evidence/extraction/tell_extraction/outputs/consolidation_clusters_vote.json` | Batch-review merge clusters, vote | data for F5 |
| `evidence/extraction/tell_extraction/outputs/consolidated_store.json` | 596-entry reviewed store | data for F5 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v1.jsonl` | First detector's detections | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v1_scanned.json` | Players the first detector scanned | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v1_smoke.jsonl` | Detector smoke-run detections | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v1_smoke_scanned.json` | Detector smoke-run scanned players | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v2.jsonl` | Second detector variant's detections | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v2_scanned.json` | Second variant's scanned players | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v3split.jsonl` | Split-view detector detections | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_det_v3split_scanned.json` | Split-view detector scanned players | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_union_v1v2.jsonl` | Union of two detector views | data for F6 |
| `evidence/extraction/tell_extraction/outputs/detector_union_v1v3.jsonl` | Union of two detector views | data for F6 |
| `evidence/extraction/tell_extraction/outputs/granularity_screen.json` | Broad-versus-narrow behaviour flags (7) | data for F12 |
| `evidence/extraction/tell_extraction/outputs/heldout/provisional_lift_table.json` | Held-out association table, 60 games | data for F8 |
| `evidence/extraction/tell_extraction/outputs/heldout/*.jsonl` | Held-out detections per arm and view (10) | data for F8, F9 |
| `evidence/extraction/tell_extraction/outputs/heldout/*_scanned.json` | Held-out scanned players per arm and view (10) | data for F8, F9 |
| `evidence/extraction/tell_extraction/outputs/mining_v1.jsonl` | Miner prompt v1 candidates | data for F2 |
| `evidence/extraction/tell_extraction/outputs/mining_v1_partial_seq.jsonl` | Partial v1 run (91 rows read) | data for F2 |
| `evidence/extraction/tell_extraction/outputs/mining_v2.jsonl` | Miner prompt v2 candidates | data for F2 |
| `evidence/extraction/tell_extraction/outputs/mining_v3.jsonl` | Miner prompt v3 candidates, Pro | data for F2, F3 |
| `evidence/extraction/tell_extraction/outputs/mining_v3_flash.jsonl` | v3 on Flash | data for F3 |
| `evidence/extraction/tell_extraction/outputs/mining_v3_flashlite.jsonl` | v3 on Flash-Lite, one call | data for F3 |
| `evidence/extraction/tell_extraction/outputs/mining_v4_flashlite_split.jsonl` | v4 split calls on Flash-Lite | data for F3 |
| `evidence/extraction/tell_extraction/outputs/mining_v4_games06_30.jsonl` | 25 more games mined (896 rows) | data for F5 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/README.md` | Two-phase blind owner protocol | F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/answer_sheet.md` | Owner's phase-1 blind answer sheet | F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/checklist_discussion.md` | Frozen discussion checklist for owner | F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/checklist_vote.md` | Frozen vote checklist for owner | F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/cells.json` | 24 owner cells (player, channel) | data for F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/owner_verdicts.json` | Owner's recorded verdicts, game 1 | F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/transcripts/*.txt` | Six role-blind owner transcripts | data for F7 |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/phase2_sheet.md` | Sealed pooled phase-2 sheet | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/det_v1_cached.jsonl` | Sealed detector answers | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/det_v1_cached_scanned.json` | Sealed detector scanned players | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/det_v3split_cached.jsonl` | Sealed detector answers | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/det_v3split_cached_scanned.json` | Sealed detector scanned players | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/games.jsonl` | Sealed game records with roles | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/opus_prelabels.json` | Sealed strong-model prelabels | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/pool.json` | Sealed pooled candidates | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/outputs/owner_golden/SEALED_do_not_open/pool_candidates.json` | Sealed pool before shuffling | not read: sealed for the owner's blind read |
| `evidence/extraction/tell_extraction/prompt_versions/v1.txt` | Miner prompt v1 | F2 |
| `evidence/extraction/tell_extraction/prompt_versions/v2.txt` | Miner prompt v2 | F2 |
| `evidence/extraction/tell_extraction/prompt_versions/v3.txt` | Miner prompt v3 (knowledge rule) | F2 |
| `evidence/extraction/tell_extraction/prompt_versions/v4_discussion.txt` | Split miner, discussion call | F3 |
| `evidence/extraction/tell_extraction/prompt_versions/v4_vote.txt` | Split miner, vote call | F3 |
| `evidence/extraction/tell_extraction/prompt_versions/det_v1.txt` | Detector prompt v1 | F6 |
| `evidence/extraction/tell_extraction/prompt_versions/det_v2.txt` | Detector prompt v2 | F6 |
| `evidence/extraction/tell_extraction/scripts/tell_mining_probe.py` | Mining probe (frozen) | F2, F3 |
| `evidence/extraction/tell_extraction/scripts/dedup_v0.py` | Duplicate-wording probe | F4 |
| `evidence/extraction/tell_extraction/scripts/ledger_sim.py` | 30-game lifecycle simulation | F5 |
| `evidence/extraction/tell_extraction/scripts/consolidation_prep.py` | Batch-review input builder | F5 |
| `evidence/extraction/tell_extraction/scripts/consolidation_apply.py` | Applies batch review, recomputes curve | F5 |
| `evidence/extraction/tell_extraction/scripts/detector_probe.py` | Detector probe | F6 |
| `evidence/extraction/tell_extraction/scripts/golden_sampler.py` | Samples the 40 golden cases | F6 |
| `evidence/extraction/tell_extraction/scripts/golden_score.py` | Scores detector against golden | F6 |
| `evidence/extraction/tell_extraction/scripts/owner_golden_build.py` | Builds the owner bundle | F7 |
| `evidence/extraction/tell_extraction/scripts/heldout_lift.py` | Held-out association table | F8, F9 |
| `evidence/extraction/tell_extraction/scripts/granularity_screen.py` | Broad-versus-narrow screen | F12 |
| `evidence/extraction/tell_extraction/scripts/build_seed_book.py` | Builds the 34-entry seed book | F14 |

### `game_play_enhancement`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Talk was thin because one exact source (the investigator) went uncontested; evil never claimed | claim-based accusations hit evil 34/35 vs 54–60% for votes/behaviour; investigator claimed in 24/28 games; 0 evil claims in 28 | LIVE (ten-seat roles answer it) | root-cause analysis on existing data | KEEP | discussion_evidence.md §2 |
| 2 | Most silence was the engine's invisible skip, so a turn-order fact went into the rules | 367 of 517 passes (71%); ~1 accusation in 8 rested on quietness | LIVE (`game_rules.py:44–48`) | — | MERGE→1 | §2.4, §3 P1 |
| 3 | A keyword count overstated summaries naming a quiet player; matches are now read before quoting | 32 by keyword vs 4 of 124 read | RECORD | — | SKIP | §2.4 |
| 4 | Phase 1 prompt switch (v2): turn-taking label fell, but the evil "you may claim" paragraph moved nothing | turn-taking 6% → 0 in 1 game; evil claims 0 in 2 games | SUPERSEDED (by the R11 cards) | — | SKIP (history line in 54) | §6.1, §6.3; live_* review sheets |
| 5 | A judge's label shares shift with its rubric, so both arms must be judged in one run with one rubric | "something said" 74% → 63% on re-judging, same messages | RECORD | measurement hygiene | MERGE→instruments topic (one line) | §6.1 |
| 6 | An invented investigator check came from the result wording, not from the seat's note | invented 20/20 old wording, 0/20 "you investigated"; note removed: still 20/20 | LIVE (results written as the seat's own action) | causal ablation by frozen-state replay | KEEP | §6.2; data/investigator_replay |
| 7 | A town won on a leaked premise, which led to the fidelity pass: silent night events stated, a private night record per role, "voted to eliminate", notes labelled fallible | bench bad samples 36% → 31%, 24 cases better / 14 worse, p = 0.14 (direction only) | LIVE | — | MERGE→49 | §6.4–6.5 |
| 8 | Summary v4: the model transcribes, code keeps the claim ledger; prompts shorter, errors unchanged | previous days 4,911 → ~2,600 chars; bad 31% vs 32%; stored summaries −55% | LIVE | — | MERGE→68–72 | §6.6 |
| 9 | Vote misquotes resisted structure: a per-player vote index and a "cite the record exactly" rule did nothing | messages 21% vs 26% (p = 0.69); misquotes 24 → 24 | OFF (neither found in code) | — | MERGE→10 | §6.6 follow-ups |
| 10 | Every pre-October game ran with zero reasoning tokens; reasoning is the lever, set per model | bad 31% → 10% at medium (36 better / 4 worse, p < 0.0001), 2.4× cost, 3.3× time; 3.1 Flash-Lite at low 15% for 1.3×; bigger Flash reasons at minimal at ~3× cost | LIVE (`catalog.py` `turn_thinking`) | reasoning budget as a measured setting | KEEP | §6.7 |
| 11 | Old records showed day 1 always empty and the lynched player usually most-accused; speaker tags good enough to count with | day 1 empty 28/28; lynched among most-accused 61/67; tags agree 145/183, miss 24, invent 1 | RECORD (shaped Phase 2) | — | MERGE→12 | §7.1 |
| 12 | The day with rounds: opening for all with an allow-list filter, closing for the most-accused, moderator line written by code, the cap drains instead of cutting | — | LIVE (`closing.py`, `round_filter.py`, `scheduler.py`) | multi-agent turn-taking design | KEEP | §7.2, §7.4 steps 1–5 |
| 13 | Asking quiet players in parallel gave near-identical lines, so the sweep went sequential with a per-line gate | 7 lines to keep 2; round filter held 17% (June) / 28% (smoke); a duplicate-publication bug; tag `phase2-parallel-proactive` | LIVE (sequential sweep) | multi-agent turn-taking design | KEEP | §7.4 4b–4c; round_echo_check; step4b smoke |
| 14 | The echo gate improved by restructuring its verdict, not by rewording | holds 29% → 27% (wording) → 18% (state what it adds first), 146 lines | LIVE (`echo_gate.py`) | judge design | KEEP | §7.4 4c; line_echo_check |
| 15 | Four test games: mechanics work, but the opening drew no contest and the closing changed no vote | 5/106 opening turns spoken; 7/7 defended lynched; ~30 calls a voting day, $0.34–0.55 a game | RECORD | — | MERGE→12 | §7.4 step 8; phase2_step8_games/report.md |
| 16 | The investigator lynch chain: the rounds turned a rare event into a certain one; held lines now count for nothing | lynched day 2 in 3 of 3 (7–1) vs 1 of 18 in June | LIVE (ruling) | emergent interaction of mechanics | KEEP | §7.4 step 8; report.md §6 |
| 17 | One missing accusation tag can silence an accused player for the day; the tags carry rules never measured | seen once (player_7, game 1); tags measured once (79%) | LIVE limitation | — | KEEP (Gap) | §9.8–9.9; report.md §1 |
| 18 | With no evidence the model takes the lowest seat number; the obvious fix (a shuffle) failed; an engine lot works | seat 1 took 78/96 night-1 actions; shuffle 95/96 still lowest; lot taken 95/96; one-player boards 16/32 → 0/32; example-named player_2 drew 40 tags vs ~8 | LIVE (`night_one_lot`) | positional/anchoring bias diagnosis | KEEP | §7.5; night1_target_bias |
| 19 | The ten-seat brief: several imperfect sources, evil muddies with block/conceal (no framer, so engine results stay true), engine-read wills, a claim enum | — | LIVE (`ROLE_SPECS`) | information design for a hidden-information game | KEEP | §8, §8.1; role_sheet.md |
| 20 | A read-only census before the switch listed silent failures no test would raise; an outside review still found six gaps after 1,394 tests | 6 gaps, all fixed with tests | RECORD | change-impact audit | KEEP (optional, engineering practice) | phase3_wiring_census.md; role_sheet change log |
| 21 | The first ten-seat games ran the mechanics; live play found two bugs, leak-check false positives and a rescue-path crash under load | 3 games; 5 at once overloaded Vertex | RECORD | — | MERGE→3 (leak false positives); rest SKIP | §8.2; phase3_games; phase3_balance README |
| 22 | The sigil's "immune" string named the serial killer in one step, so it now reads like a quiet night | before 3 of 6 SK lynches; after, SK won both games a sigil landed | LIVE | balance tuning from counts | KEEP | §8.3; role_sheet; phase3_balance, _2 |
| 23 | Evil lacked covers, not tools; a cover-story prompt raised claims; balance closed at batch 4 | pack aimed 34/56 kills at info roles; evil claim fields 4–8 → 19; town 14 / evil 4 over 18 games | LIVE | — | MERGE→22 and 54 | §8.3; phase3_balance_3, _4 |
| 24 | Balance tuned on Flash-Lite play is specific to that model | lesson, no number | RECORD | — | MERGE→22 (caveat) | §8.5 item 5 |
| 25 | Error audit by kind: invented facts are rare; summary errors and wrong deductions about abilities dominate | ~345 lines: invented 2, summary 22, invalid deduction 28 | RECORD | error analysis by kind | KEEP | §8.4; phase3_reads |
| 26 | A summary transcription error decided game e06; a record-check example was copied against true claims | 1 game; copied line 2/15 → 0/15 | LIVE | — | MERGE→71 | §8.4; phase3_reads; phase3_summary_replay |
| 27 | Replays with controls separated the prompt's limit from the model's; full games tempered the replay | Flash-Lite 17/40 → 6/40; Flash 1/40; controls 4–5/10 vs 0/10; full games 1 invalid deduction per 15 lines vs 12 | RECORD | controls in replay sets | KEEP | §8.4–8.5; phase3_turn_replay; phase3_flash_games |
| 28 | Stating a rule stops its first misreading, not a cascade already in the transcript | f02 cascade turns Flash 10 → 7 → 4 of 10 (rule, then "rules are exact"); Flash-Lite 10/10 throughout | LIVE (`game_rules.py:103`) | misinformation cascades among agents | KEEP | §8.4; phase3_turn_replay |
| 29 | A literal reader exposes unstated rules, and a fix checked on one model can regress another | Luna sentinel chain 11 of 14 invalid deductions; concede 10/10 → 0/10; illusionist 8/20 → 0/20; roleblock-as-denial 15/15 → 0/15 | LIVE (`roles/sentinel.py`) | cross-model prompt robustness | KEEP | §8.4–8.5; phase3_luna_games; role_sheet |
| 30 | The summary could not hold a denial; result words added | denials lost 30/30 → 7/30 (Flash-Lite), 0/30 (Flash) | LIVE (`schemas/output.py:26, 289`) | — | MERGE→70 | §8.4; phase3_summary_replay |
| 31 | Three seat models in full games: cost, time, talk; a summariser upgrade costed but not adopted | Flash $2.72 / Flash-Lite $0.72 / Luna $0.17 (22 min); 40 vs 29 lines heard; summariser upgrade est. +$0.06–0.12 | RECORD (summary uses the game model) | — | MERGE→`model_selection/` | §8.4–8.5; phase3_flash_games, phase3_luna_games |
| 32 | Most bad votes had no public reasoning, not contradicted reasoning; no "odd vote" was an unexplained change of mind | 70% of Flash-Lite town votes from a voter who accused no one vs 36% on Flash; own top suspect 81% / 90%; 11 odd votes checked | LIVE (led to the vote-reason line) | — | KEEP | §8.4; phase3_reads/votes/dossiers.md |
| 33 | Haiku read visits backwards; the shared rules now state the direction | bad public messages 16/35 → 5/35 (first misreading 5 → 2 of 15, cascade 11 → 3 of 20) | LIVE (`game_rules.py:70`) | — | KEEP | §8.6; haiku_turn_replay |
| 34 | A "don't repeat" line changed only how replies open; the fix needs the scheduler | 27/30 → 23/30 | LIVE line; structural fix PLAN | — | MERGE→33 | §8.6 |
| 35 | The vote-reason line failed until it asked seats to decide now; town only | passes 24/25 → 23 (v1) → 16 (v2); Haiku passed 61%, 10 of 21 votes from silent seats | LIVE (`day_discuss.py:100`) | diagnosing a prompt failure from the model's own notes | MERGE→32 | §8.6; haiku_turn_replay |
| 36 | "Compare the candidates" sentence dropped: its escape clause turned leans into abstentions | target ballot 7/10 → 0/10 (p = 0.003); day-4 citations 2 → 11/30 (p = 0.01); +35% output | OFF | prompt A/B on frozen votes with controls | KEEP | §8.7; haiku_vote_replay |
| 37 | The vote record went out of use across code versions; one wording change moves a case more than any effect tested | day-4 controls right 25 → 20 → 13 of 30 (p = 0.003); citations 19 → 12 → 2; ballot tag moved cases 4 → 9, 6 → 2 | LIVE, unresolved (layout suspected) | prompt sensitivity | KEEP (Gap; qualifies block 8) | §8.7; haiku_vote_replay |
| 38 | The sentinel vote: an unverified claim was penalised while silence counted as neutral | 1 game, read from the checkpoints | RECORD | — | MERGE→36 | haiku_sentinel_vote |
| 39 | A rewrite call for persona voices read better but changed facts; the code fact check missed them | 74/90 more natural; 19/90 changed something actionable; gate caught 1 | OFF | rewrite-fidelity measurement | KEEP | voice_rewrite |
| 40 | One voice line in the seat's prompt reads natural without moving stance beyond sampling noise | 25/30 more natural; stance differs 30% = plain-vs-plain 30% (10 pairs) | LIVE in served games | sampling-noise baseline | KEEP | persona_line; `run_config.py:38` |
| 41 | Paired games: voices did not hurt the readers; leak-check false positives fixed | Brier 0.155 → 0.129, 7 of 8 pairs (p ≈ 0.07); town wins 4 → 7 of 8 (noise) | LIVE | — | MERGE→40 | persona_voice_games |
| 42 | Seats cannot sort their own lines by rule text; one sentence set the volume, so the gate does the sorting | worth hearing: passes 57% vs posted 52%; speech 20 → 41 of 64; gate holds 12/29 restatements, 0/36 good; games 41% → 58%, 7/7 holds genuine; old gate fired 0 times in 16 games | LIVE (`day_discuss.py:92`, `echo_gate.py:96`) | measuring discrimination, not level | KEEP | silence_calibration |
| 43 | Evil covers: card text plus deduction lines made evil claim instead of deny; wolves started winning | claims 13 → 44, denials 21 → 0 (41 turns × 2); evil claimed 3 → 11 of 24; wolves 0 → 3 of 8 | LIVE | — | MERGE→54 | evil_cover_screen; evil_cover_games |
| 44 | A line naming each counter-claimant's account was dropped; it pulled votes to the named seat | 12/16 → 12/17 pooled; own case 7/4 → 5/7 | OFF | — | MERGE→54 | counter_claim_votes |
| 45 | The visit metaphor was not the cause of the visit arguments; injecting the conclusion fixed the first speaker, not the replies | mechanics errors DeepSeek 25% → 23%, Haiku 20% → 29%; A56/E19: own reports 15% → 5%, replies 31% → 31% | LIVE (A56/E19); target wording OFF | falsifying a hypothesis cheaply | KEEP | visit_wording_ab |
| 46 | Deferred and small items: a public evidence board (no cost case), a human's vote waiting on the slowest agent, the stage showing talk after the vote | board +0–18% est.; others no number | PLAN / frontend | — | SKIP | §9.5–9.7; §8.6 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/game_play_enhancement/discussion_evidence.md` | Three-phase running log of the discussion fixes | F1–F19, F22–F38, F46 |
| `evidence/game_play_enhancement/phase3_wiring_census.md` | Nine-seat assumptions census and the wiring plan | F20 |
| `evidence/game_play_enhancement/role_sheet.md` | Ten-seat rules with a change log of rulings | F19, F20, F22, F23, F29 |
| `evidence/game_play_enhancement/data/baseline_smoke/reads.jsonl` | Judge reads, one baseline game | data for F5 |
| `evidence/game_play_enhancement/data/baseline_smoke/review.md` | Judge review sheet for hand-checking labels | F5 |
| `evidence/game_play_enhancement/data/baseline_smoke/summary.json` | Judge summary, one baseline game | data for F5 |
| `evidence/game_play_enhancement/data/counter_claim_votes/README.md` | Counter-claim line vote replay and drop decision | F44 |
| `evidence/game_play_enhancement/data/counter_claim_votes/samples.jsonl` | Vote samples per arm | data for F44 |
| `evidence/game_play_enhancement/data/counter_claim_votes/scores.json` | Vote tallies per arm | data for F44 |
| `evidence/game_play_enhancement/data/evil_cover_games/README.md` | Paired games before/after evil covers | F43 |
| `evidence/game_play_enhancement/data/evil_cover_games/after/*` | Eight game captures and manifests, covers on | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_games/before/*` | Four game captures and manifests, old cards | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_games/games_scores.json` | Scored outcomes of the paired games | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/README.md` | Evil cover replay screen, steps 1–5 | F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/*blind_key.json` | Blinding keys, four judging rounds | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/*packet_*.md` | Blind judge packets, 20 files | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/samples*.jsonl` | Replayed samples, four steps | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/*scores.json` | Scored tables, four rounds | data for F43 |
| `evidence/game_play_enhancement/data/evil_cover_screen/*verdicts_*.jsonl` | Blind judge verdicts, four rounds | data for F43 |
| `evidence/game_play_enhancement/data/haiku_sentinel_vote/README.md` | Investigation of the vigilante's vote on the sentinel | F38 |
| `evidence/game_play_enhancement/data/haiku_sentinel_vote/source_excerpt.json` | Selected event and checkpoint records | data for F38 |
| `evidence/game_play_enhancement/data/haiku_turn_replay/README.md` | 18 Haiku turns replayed before/after the fixes | F33, F34, F35 |
| `evidence/game_play_enhancement/data/haiku_turn_replay/bench_summary*.json` | Bench summaries, two arms | data for F33–F35 |
| `evidence/game_play_enhancement/data/haiku_turn_replay/cases.jsonl` | Frozen turn cases with expectations | data for F33–F35 |
| `evidence/game_play_enhancement/data/haiku_vote_replay/README.md` | 11 votes replayed across five code arms | F36, F37 |
| `evidence/game_play_enhancement/data/haiku_vote_replay/bench_summary*.json` | Bench summaries, discussion and votes | data for F36, F37 |
| `evidence/game_play_enhancement/data/haiku_vote_replay/cases.jsonl` | Frozen vote cases | data for F36, F37 |
| `evidence/game_play_enhancement/data/haiku_vote_replay/votes.jsonl` | Every sample's vote, reads, note | data for F36, F37 |
| `evidence/game_play_enhancement/data/investigator_replay/prompt_*.txt` | The four replay prompt variants | data for F6 |
| `evidence/game_play_enhancement/data/investigator_replay/samples_*.jsonl` | 20 samples per variant | data for F6 |
| `evidence/game_play_enhancement/data/investigator_replay/summary.json` | Replay counts per variant | data for F6 |
| `evidence/game_play_enhancement/data/line_echo_check/README.md` | Echo gate offline check, three prompt versions | F14 |
| `evidence/game_play_enhancement/data/line_echo_check/report.md` | Held lines beside the lines they repeat | F14 |
| `evidence/game_play_enhancement/data/line_echo_check/results.jsonl` | Kept/held lines per day | data for F14 |
| `evidence/game_play_enhancement/data/live_baseline/reads.jsonl` | Judge reads, three pre-switch site games | data for F4, F5 |
| `evidence/game_play_enhancement/data/live_baseline/review.md` | Judge review sheet, baseline games | F4, F5 |
| `evidence/game_play_enhancement/data/live_baseline/summary.json` | Judge summary, baseline games | data for F4, F5 |
| `evidence/game_play_enhancement/data/live_v2/reads.jsonl` | Judge reads, first v2 game | data for F4, F5 |
| `evidence/game_play_enhancement/data/live_v2/review.md` | Judge review sheet, first v2 game | F4, F5 |
| `evidence/game_play_enhancement/data/live_v2/summary.json` | Judge summary, first v2 game | data for F4, F5 |
| `evidence/game_play_enhancement/data/live_v2_game2/reads.jsonl` | Judge reads, second v2 game | data for F4 |
| `evidence/game_play_enhancement/data/live_v2_game2/review.md` | Judge review sheet, second v2 game | F4 |
| `evidence/game_play_enhancement/data/live_v2_game2/summary.json` | Judge summary, second v2 game | data for F4 |
| `evidence/game_play_enhancement/data/night1_target_bias/README.md` | Night-1 target bias: shuffle run, lot run | F18 |
| `evidence/game_play_enhancement/data/night1_target_bias/results*.jsonl` | One row per call, both runs | data for F18 |
| `evidence/game_play_enhancement/data/night1_target_bias/summary.md` | Runner tables, plain vs lot | F18 |
| `evidence/game_play_enhancement/data/night1_target_bias/summary_order_check.md` | Runner tables, seat order vs shuffle | F18 |
| `evidence/game_play_enhancement/data/persona_line/README.md` | Persona line screen: naturalness and stance | F40 |
| `evidence/game_play_enhancement/data/persona_line/blind_key.json` | Blinding key | data for F40 |
| `evidence/game_play_enhancement/data/persona_line/*_packet_*.md` | Blind judge packets, naturalness and stance | data for F40 |
| `evidence/game_play_enhancement/data/persona_line/samples.jsonl` | Sampled lines per arm | data for F40 |
| `evidence/game_play_enhancement/data/persona_line/verdicts_*.jsonl` | Blind judge verdicts | data for F40 |
| `evidence/game_play_enhancement/data/persona_voice_games/README.md` | Eight paired games, voices off vs on | F41 |
| `evidence/game_play_enhancement/data/persona_voice_games/scores.json` | Read accuracy, Brier, votes per arm | data for F41 |
| `evidence/game_play_enhancement/data/persona_voice_games/voices-*.capture.json.gz` | Sixteen game captures | data for F41, F42 |
| `evidence/game_play_enhancement/data/persona_voice_games/voices-*.manifest.json` | Sixteen game manifests | data for F41, F42 |
| `evidence/game_play_enhancement/data/phase2_step4_smoke_game_2026-10-07.json` | First game on opening/closing rounds | data for F12 |
| `evidence/game_play_enhancement/data/phase2_step4b_smoke_game_2026-10-07.json` | Parallel proactive round smoke game | data for F13 |
| `evidence/game_play_enhancement/data/phase2_step4c_day_rerun_2026-10-07.json` | Sequential sweep day rerun | data for F13 |
| `evidence/game_play_enhancement/data/phase2_step8_games/README.md` | File guide for the four step 8 games | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/report.md` | Step 8 reading and the investigator chain | F15, F16, F17 |
| `evidence/game_play_enhancement/data/phase2_step8_games/counts.md` | Per-day counts table, games and baselines | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/counts.json` | Per-day counts, machine form | data for F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/baselines/replay_832404e9.json` | Cached v2 game replay | data for F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/game*` | Four games' calls, chunks, manifests, records | data for F15, F16, F17 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/*/reads.jsonl` | Judge reads, five games | data for F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/*/summary.json` | Judge summaries, five games | data for F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/step8_game1/review.md` | Judge review sheet, game 1 | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/step8_game2/review.md` | Judge review sheet, game 2 | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/step8_game3/review.md` | Judge review sheet, game 3 | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/step8_game4/review.md` | Judge review sheet, game 4 | F15 |
| `evidence/game_play_enhancement/data/phase2_step8_games/judge/v2-832404e9/review.md` | Judge review sheet, v2 game re-read | F15 |
| `evidence/game_play_enhancement/data/phase3_balance/README.md` | First balance batch: town 10 of 10 | F21, F22 |
| `evidence/game_play_enhancement/data/phase3_balance/b*.*` | Ten games' calls, chunks, manifests, records | data for F22, F25 |
| `evidence/game_play_enhancement/data/phase3_balance/logs/*.log` | Run logs and timings | data for F21 |
| `evidence/game_play_enhancement/data/phase3_balance/logs/*.sh` | Run scripts | data for F21 |
| `evidence/game_play_enhancement/data/phase3_balance/logs/failed_first_attempt/*.log` | Crashed first-attempt logs (overload) | data for F21 |
| `evidence/game_play_enhancement/data/phase3_balance_2/README.md` | Second batch: sigil ruling and caps | F22 |
| `evidence/game_play_enhancement/data/phase3_balance_2/c*.*` | Six games' captures | data for F22, F25 |
| `evidence/game_play_enhancement/data/phase3_balance_2/logs/*` | Run logs, script, timings | data for F22 |
| `evidence/game_play_enhancement/data/phase3_balance_3/README.md` | Third batch: necromancer and conceal buffs | F23 |
| `evidence/game_play_enhancement/data/phase3_balance_3/d*.*` | Six games' captures | data for F23, F25 |
| `evidence/game_play_enhancement/data/phase3_balance_3/logs/*` | Run logs, script, timings | data for F23 |
| `evidence/game_play_enhancement/data/phase3_balance_4/README.md` | Fourth batch: cover story epoch | F23 |
| `evidence/game_play_enhancement/data/phase3_balance_4/e*.*` | Six games' captures | data for F23, F25, F26 |
| `evidence/game_play_enhancement/data/phase3_balance_4/logs/*` | Run logs, script, timings | data for F23 |
| `evidence/game_play_enhancement/data/phase3_flash_games/README.md` | Six games on Gemini 3.5 Flash, audited | F27, F31, F32 |
| `evidence/game_play_enhancement/data/phase3_flash_games/f*.*` | Six games' captures | data for F27, F31 |
| `evidence/game_play_enhancement/data/phase3_flash_games/logs/*` | Run logs, script, timings | data for F31 |
| `evidence/game_play_enhancement/data/phase3_games/README.md` | First three ten-seat games | F19, F21 |
| `evidence/game_play_enhancement/data/phase3_games/game*` | Three games' captures | data for F21 |
| `evidence/game_play_enhancement/data/phase3_luna_games/README.md` | Four games on GPT-6 Luna, audited | F29, F31 |
| `evidence/game_play_enhancement/data/phase3_luna_games/l*.*` | Four games' captures | data for F29, F31 |
| `evidence/game_play_enhancement/data/phase3_luna_games/logs/*` | Run logs, script, timings, two stopped games | data for F31 |
| `evidence/game_play_enhancement/data/phase3_reads/README.md` | Fifteen games read by rubric; odd votes | F25, F26, F32 |
| `evidence/game_play_enhancement/data/phase3_reads/transcripts/*.md` | 25 rendered game transcripts | data for F25, F27, F29 |
| `evidence/game_play_enhancement/data/phase3_reads/votes/dossiers.md` | Eleven odd votes against voters' reasoning | F32 |
| `evidence/game_play_enhancement/data/phase3_summary_replay/README.md` | Summary replays: ledger, retention, roleblocks | F26, F30 |
| `evidence/game_play_enhancement/data/phase3_summary_replay/generations_*.jsonl` | Summariser samples per arm | data for F26, F30 |
| `evidence/game_play_enhancement/data/phase3_summary_replay/*.log` | Replay run logs | data for F30 |
| `evidence/game_play_enhancement/data/phase3_turn_replay/README.md` | Frozen turn replays: capability, rule cascades | F27, F28, F29 |
| `evidence/game_play_enhancement/data/phase3_turn_replay/bench_summary*.json` | Bench summaries, seven arms | data for F27–F29 |
| `evidence/game_play_enhancement/data/phase3_turn_replay/cases.jsonl` | Frozen turn cases with expectations | data for F27–F29 |
| `evidence/game_play_enhancement/data/round_echo_check/README.md` | Parallel round echo filter offline check | F13 |
| `evidence/game_play_enhancement/data/round_echo_check/report.md` | Held round lines beside their repeats | F13 |
| `evidence/game_play_enhancement/data/round_echo_check/results.jsonl` | Kept/held lines per round | data for F13 |
| `evidence/game_play_enhancement/data/silence_calibration/README.md` | Silence calibration steps 1–5 | F42 |
| `evidence/game_play_enhancement/data/silence_calibration/blind_key.json` | Blinding key | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/games/*` | Four game captures and manifests | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/games_scores.json` | Open-floor counts, before/after | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/gate_check*.jsonl` | Gate verdicts per candidate bar | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/gate_check*scores.json` | Gate hold tables | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/items.jsonl` | Drawn turns and forced lines | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/lever_samples.jsonl` | Samples with one lever removed | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/lever_scores.json` | Lever tables | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/packet_*.md` | Blind judge packets | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/variant_samples.jsonl` | Samples under the rewritten silence rule | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/variant_scores.json` | Rule-rewrite tables | data for F42 |
| `evidence/game_play_enhancement/data/silence_calibration/verdicts_*.jsonl` | Blind judge verdicts by kind | data for F42 |
| `evidence/game_play_enhancement/data/visit_wording_ab/README.md` | Visit-wording replay A/B and arm C | F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/judge_rubric.md` | Rubric for the blind judges | F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/case_context.md` | Per-case true roles and night records | F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/arm_b.diff` | Arm B's wording edits against the tag | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/cases.jsonl` | Nineteen frozen turns | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/blind.jsonl` | Shuffled lines, no arm | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/key.jsonl` | Opaque id to arm key | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/samples_*.jsonl` | Haiku samples, arms A, B, C | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/judge_batch_*.jsonl` | Judge input batches (Haiku run) | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/judged_*.jsonl` | Judge verdicts (Haiku run) | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/haiku_run_*.log` | Generation logs per arm | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/deduction_ac/*` | Arm A vs C blind judging set | data for F45 |
| `evidence/game_play_enhancement/data/visit_wording_ab/deepseek/*` | DeepSeek run samples and verdicts | data for F45 |
| `evidence/game_play_enhancement/data/voice_rewrite/README.md` | Voice rewrite screen: naturalness and fidelity | F39 |
| `evidence/game_play_enhancement/data/voice_rewrite/blind_key.json` | Blinding key | data for F39 |
| `evidence/game_play_enhancement/data/voice_rewrite/*_packet_*.md` | Blind judge packets, fidelity and naturalness | data for F39 |
| `evidence/game_play_enhancement/data/voice_rewrite/lines.jsonl` | Thirty source lines | data for F39 |
| `evidence/game_play_enhancement/data/voice_rewrite/rewrites.jsonl` | Ninety rewrites with gate result | data for F39 |
| `evidence/game_play_enhancement/data/voice_rewrite/verdicts_*.jsonl` | Blind judge verdicts | data for F39 |

### `generation_prompt`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Fact errors are common once private notes are read too; the night note is the worst surface; most errors are survivor arithmetic, and they spread through a day | 50 games, 7,846 texts; public ≈68 of 2,292 (≈3.0%); notes ≈222 of 5,554 (≈4.0%); night notes 113 of 1,179 (9.6%, ≈7.7% adjusted); arithmetic 221 of 368; 24 errors in one game-day; 7 deliberate lies kept apart; 0 votes cast for a dead player | LIVE (the census is the standing measure) | error analysis | KEEP | validation/hallucination_baseline.md; experiment_log.md §10.1 |
| 2 | How the census was built. Code finds every text naming a dead player, a dead role or a count, so recall is guaranteed inside that scope. A cheap model reads for recall, a stronger model rechecks its positives for precision, and a human checks both | 2,461 candidates → 641 → 368; the precision pass removed 273; 23-case calibration set; the owner read all 90 public positives, 25 of 278 notes, and 15 of 273 rejections (2–3 were real misses) | LIVE (`role_hallucination_screen.py`, `role_fact_read.py`) | programmatic screen with guaranteed recall, model cascading, human audit | KEEP | hallucination_baseline.md; validation_plan.md T1 |
| 3 | The roughly 20× jump over the old manual baseline came from a better instrument, not from changed games. One of the old 4 cases was refuted: it had been checked against the other paired arm's game | old 0.14 per 100 messages from 171 windows read by hand (a superseded floor, never to be cited) | SUPERSEDED | measurement validity | MERGE→F2 (pairs with `tell_extraction/` F9) | hallucination_baseline.md |
| 4 | Showing the answer did not fix it: with a correct "roles still in play" line listing no wolf, the model still hunted "the remaining wolf". The board ships as hygiene, not as a measured fix | the recurring case went 0/6 baseline, 2/6 board, 1/6 full board; the other 3 cases 0/6 in every arm; 72 calls | LIVE (board kept) | negative result, replay screen | KEEP | validation/t1b_results.md; experiment_log.md §10.2 |
| 5 | Adding reads broke nothing; the board costs no output tokens. Comparing against the original recorded action is mostly sampling noise, so arms are compared with each other | verdict coverage about 1.0 in every arm; output 375 → 384 tokens (board), +60% (reads); about half of actions differ from the original even in the unchanged arm | LIVE | regression testing, noise floor | KEEP (small) | validation/t2_results.md; regression_replay.py |
| 6 | Reads are honest but incomplete in mid-game. A missed player is one there was nothing to say about, so the misses are tolerated and imputed rather than retried. Wolves hedge about packmates in discussion, so honesty is probed at the vote | wolf packmate probe 9 of 9; role guess right 0.47–0.60 vs ~0.17 random (faction not above always-town); completeness 0.85 → 0.93 by listing names; voted for an unread player 1 of 80; evil ~12% of misses vs ~37% of seats; tripwire at 0.85 | LIVE (`{read_targets}`; monitor in `Agents/turn/agent_player.py`) | cost-benefit ruling, structured output | KEEP | t2_results.md; experiment_log.md §11.2 |
| 7 | Reads before the note triple how often an agent overrides a bad lesson, but the reads come out lazier on a cold start | override 0.17 vs 0.06; "unchanged" reasons 40% vs 17%; guess accuracy 0.47 vs 0.60 | LIVE (reads first in `TurnOutput`) | field ordering | MERGE→block 32 | t2_results.md |
| 8 | Ship test: the plan was changed after run 1 showed that context predicts errors, the new main measure was fixed in advance, and it was confirmed on fresh cases | run 1 controls 35% error; run 2, 100 fresh cases: 48% → 30%, 29 better / 11 worse, one-sided p = 0.003; about $3 | LIVE (graduated to the hallucination bench 2026-10-03) | pre-registration, paired A/B on frozen turns | KEEP | experiment_log.md §12; validation_plan.md T1c; t1c_ab_replay.py |
| 9 | The new leak check for private reads flagged both smoke games on shared words ("confirmed healer"), with no real leak. It was redesigned to look for a rendered read object | 2 games, 0 real leaks | LIVE (`check_reads_isolation`, `tests/engine/test_player_reads.py`) | invariant checks | MERGE→block 3 | experiment_log.md §12; validation_plan.md T4 |
| 10 | The prompt/memory boundary: tactics deleted from the role text; tone policing and canned openers fell | policing 24 of 119 → 8 of 79; day-1 canned 10 of 19 → 2 of 14; 2 games each, board-confounded | LIVE (principle) | bias removal at the source | KEEP (small) | prompt_boundary/experiment_log.md; markers.py |
| 11 | Tested tactics split: wolf blending holds, investigator concealment harms. The memory had re-learned the concealment from play | blend 38% vs 25% wins (122 games, p = 0.07; earlier 220 games p = 0.003); investigator asserted its confirmed read ~33–67% | LIVE (neutral investigator block since 2026-10-07) | testing prompt claims against outcomes | KEEP | prompt_claims_audit/experiment_log.md; blend_claim_test.py |
| 12 | Hand-written prose drifts. Four copies of the rules (some for eight players) became one, 17 near-duplicate templates became factories (output byte-identical), and the threat brief was generated from the role list after the wolf's copy left out the Serial Killer | — | LIVE in form (`game_rules.py`, `compose.py`); no threat brief in today's prompts | single source of truth | MERGE→parked "conditional prompt composition" | experiment_log.md §5, §8 |
| 13 | Asking for a commitment first changed the action, not just the label. Integer indexes replaced long ID strings. Added DO/DON'T rules gave no gain | adoption 4.00 → 4.38, action quality +0.50; ID strings corrupted ~30% | LIVE | field ordering, indexed references | MERGE→`memory_system/strategy_adoption/` (blocks 20, 32) | experiment_log.md §3 |
| 14 | Reasoning before the vote, plus one forced verdict per lesson, opened a channel from memory to the vote. The instruction's placement decided whether it was obeyed | agreement 75% → 92.5%; verdict coverage 0.27 → 0.97; `follow` on an abstain lesson → abstains 77% vs 32% | LIVE | field ordering, instruction placement | MERGE→`memory_system/effectiveness/decision_replay/` | experiment_log.md §7 |
| 15 | Required booleans beat optional fields; `pass_turn` comes before the message, because an agent that has written a message will not then decline to send it | — | LIVE (`DayDiscussOutput`) | structured output | MERGE→`sequential_discussion/` F7 | experiment_log.md §4 |
| 16 | The free gameplay-caching bet died at the first measurement | 0 cached tokens on 4 identical 15k-token sends; 2 hits in 600 generations | SUPERSEDED (Claude prefix layout since) | — | MERGE→block 9 | experiment_log.md §6 |
| 17 | The record is a reconstruction; early wordings are lost; schema changes are covered only by the git SHA, not the prompt hash | — | RECORD | — | SKIP | experiment_log.md §13 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/generation_prompt/experiment_log.md` | Reconstructed history of the action prompt | index; F1, F4–F8, F12–F17 |
| `evidence/generation_prompt/validation_plan.md` | Pre-registered tests T1–T5 with dated amendments | F2, F4, F8, F9 |
| `evidence/generation_prompt/prompt_boundary/experiment_log.md` | Tactics removed from role text, marker counts | F10 |
| `evidence/generation_prompt/prompt_boundary/markers.py` | Word-marker counter for policing and canned phrasing | F10 |
| `evidence/generation_prompt/prompt_boundary/pre_markers.txt` | Marker output, old prompts | data for F10 |
| `evidence/generation_prompt/prompt_boundary/post_markers.txt` | Marker output, new prompts | data for F10 |
| `evidence/generation_prompt/prompt_boundary/post_run.log` | Run log of the two post games | data for F10 |
| `evidence/generation_prompt/prompt_boundary/post_seq.jsonl` | Two post-change game records | data for F10 |
| `evidence/generation_prompt/prompt_claims_audit/experiment_log.md` | Audit of tactical claims in role text | F11 |
| `evidence/generation_prompt/prompt_claims_audit/blend_claim_test.py` | Wolf blending against wolf wins | F11 |
| `evidence/generation_prompt/validation/hallucination_baseline.md` | The 50-game fact-error census | F1, F2, F3 |
| `evidence/generation_prompt/validation/hallucination_candidates.jsonl` | 2,461 code-screened candidates | data for F1, F2 |
| `evidence/generation_prompt/validation/hallucination_verdicts.jsonl` | Cheap reader's verdicts (recall pass) | data for F1, F2 |
| `evidence/generation_prompt/validation/hallucination_verdicts_stage2.jsonl` | Stronger reader's re-read of 641 positives | data for F1, F2 |
| `evidence/generation_prompt/validation/hallucination_flags.jsonl` | Old manual baseline's 171 windows | superseded (F3) |
| `evidence/generation_prompt/validation/hallucination_cases.jsonl` | Old manual baseline's read cases | superseded (F3) |
| `evidence/generation_prompt/validation/t1b_results.md` | Replay with the board added | F4 |
| `evidence/generation_prompt/validation/t1b_replay.py` | Replay script, board arms | F4 |
| `evidence/generation_prompt/validation/t1b_outputs.jsonl` | 72 replay outputs | data for F4 |
| `evidence/generation_prompt/validation/t2_results.md` | Non-regression, reads soundness, order A/B | F5, F6, F7 |
| `evidence/generation_prompt/validation/regression_replay.py` | Four-arm replay script | F5, F6, F7 |
| `evidence/generation_prompt/validation/t2_outputs.jsonl` | 200 four-arm replay outputs | data for F5, F6, F7 |
| `evidence/generation_prompt/validation/t2_enum_outputs.jsonl` | 40 outputs with listed read names | data for F6 |
| `evidence/generation_prompt/validation/t1c_ab_replay.py` | Ship-test replay script | F8 |
| `evidence/generation_prompt/validation/t1c_outputs.jsonl` | Ship test run 1 outputs | data for F8 |
| `evidence/generation_prompt/validation/t1c2_outputs.jsonl` | Ship test run 2 outputs (fresh cases) | data for F8 |

### `memory_system/effectiveness`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Memory improved town decisions on the plain-retrieval arm | healer save 37% → 60% (p = 0.005); correct lynch 47% → 64% (p = 0.028); mislynch 53% → 36% (p = 0.036); vote accuracy 56% → 71% (p = 0.053); 30 paired boards | SUPERSEDED (observations not served) | paired A/B | KEEP | `report.md`, `paired_ab/report.md` |
| 2 | Town win rate rose on every arm but reached significance only on the reranked arm; "+17pp p = 0.013" fuses two arms | raw 27% → 43% p = 0.27; reranked 27% → 60% p = 0.013; all-memory 27% → 50% p = 0.17; 30 each | RECORD | claim audit | KEEP | `paired_ab/report.md`, `paired_ab/experiment_log.md` |
| 3 | No benefit for wolves or the lone killer from observations | wolf 33% → 30% (p = 1.0); killer 40% → 20% (p = 0.15); 30 each | RECORD | — | MERGE→F1 | `paired_ab/report.md` |
| 4 | A re-run of the old baseline had shifted with identical prompts; the model alias cannot be pinned or detected, so baselines are re-run alongside | 10 games: town 10% vs 67% (p = 0.0028) | LIVE (rule) | experimental controls (drift) | KEEP | `paired_ab/experiment_log.md` §Epoch-shift |
| 5 | Overnight drift doubled the memory-off town's wins and confounded an apparent −40-point "net-first collapse" | town win 27% → 51%, vote accuracy 0.560 → 0.699 over 59 canary games; about 2.5× same-day noise (Δ 0.056) | RECORD | experimental controls (drift) | KEEP | `paired_ab/experiment_log.md` §Drift exhibit, §Phase A conclusion |
| 6 | Pre-registered calls: all-memory did not collapse the town; reranking did no better than raw | rerank 0.686 vs raw 0.710 vote accuracy (p = 0.52); 30 | LIVE (reranking off by default) | pre-registration | MERGE→block 41 | `paired_ab/experiment_log.md` §Pre-registration, §Final |
| 7 | An unpaired pilot on a growing store said memory hurt the town and helped wolves; the paired design refuted it; an older best-of-six-cells win did not repeat | pilot town 67% → 35% (p = 0.043), wolves 7% → 40% (p = 0.0088), 30 vs 20 games; pre-rebuild 70% → 96.7% (p = 0.012) then 73.3% | RECORD | confounding, multiple comparisons | KEEP | `v5_baseline_proxy_analysis.md`, `report.md` |
| 8 | The game id became the single seed for the deal and the turn order, which makes pairing possible | deal reproduced on 20 of 20 games | LIVE (`Agents/nodes/orchestrator.py:89`) | reproducibility | MERGE→block 65 | `v5_seeding_plan.md`, `paired_ab/experiment_log.md` |
| 9 | The stock wolf-blending metric only counted days a wolf died, so it sampled disasters; the unconditioned version validates | r = +0.43 (baseline), +0.20 pooled (220 games); a wolf who broke from the vote was lynched next day 49% vs 31% | LIVE (`Agents/ten_seat_metrics.py:149`) | metric validity (selection bias) | KEEP | `paired_ab/experiment_log.md` §Diagnostic results |
| 10 | The investigator's apparent find-rate drop was a survival artifact (more checks late in wolf-thinned games); kill-timing metrics excluded for the same reason; the wolf's power-role targeting validated | wolves found per game 0.60 → 0.63 / 0.90 / 0.83; targeting r = +0.18 (p = 0.006, 240 games) | RECORD | metric validity | MERGE→F9 | `paired_ab/experiment_log.md` |
| 11 | Wolves broke from the vote echoing success-framed precedents, and none reasoned about the recorded cost | 0 of 22 paired flips | RECORD | — | MERGE→F12 | `paired_ab/experiment_log.md` §Echo read, `echo_read_decisions.json` |
| 12 | Net-first framing removed the killer's harm but not the wolf's, as pre-registered; adopted per role | killer lynched 80% → 63%, win 20% → 37%; wolf blending 0.64 → 0.67; 30 each, none significant | LIVE (`Agents/prompts/cell_prompt.py:42–72`, `Agents/schemas/memory.py:41`) | pre-registered differential prediction | KEEP | `paired_ab/report_nethorizon.md`, `nethorizon_design.md` |
| 13 | Net-first hurt the town (read as "don't be aggressive"), so town roles keep immediate-first; replay found no extra passivity per turn | memory engagement kept at 84% of the raw arm's (12 games); discussion passivity 0.889 → 0.872 | LIVE (town horizon immediate) | — | MERGE→F12 | `paired_ab/town_echo_read.md`, `paired_ab/experiment_log.md`, `decision_replay/experiment_log.md` |
| 14 | The schema emitted the vote before the reasoning; reasoning-first syncs vote and reasoning, but carries bad content into the vote | sync 75% → 92.5% (40); vote value 0.40 → 0.26 with no memory under reasoning-first (3 × 100) | LIVE (`Agents/schemas/output.py:69–102`) | structured-output field order | KEEP | `paired_ab/experiment_log.md` §Phase B A, `decision_replay/experiment_log.md` §Reorder, §D |
| 15 | An outcome label mixes the read, the action and luck, so lessons should be conditioned on the read, not the result | design reasoning | LIVE in spirit (halo rule, credit) | outcome bias | MERGE→blocks 81, 14 | `paired_ab/experiment_log.md` §Phase B C, §memory-content design |
| 16 | A decision-replay screen: freeze a decision, swap only the memory, regenerate, score by code | about $1 a question; replay matched the recording 87–93% | LIVE (`evaluation/src/studies/decision_replay.py`) | replay screens | KEEP | `decision_replay/report_screening_layer.md`, `experiment_log.md` |
| 17 | Pooling hid where memory helps: day 2 and endgame up, mid-game null; abstains had been scored as errors | day 2 +0.078 [+0.006, +0.149]; day 3 −0.006 (180); day 5+ +0.117; 20 of 23 induced abstains avoided a mislynch | RECORD | stratified analysis | KEEP | `decision_replay/experiment_log.md` §Validity analysis |
| 18 | The best outcome framing flips by stage: cautious helps on day 2, actionable helps nowhere tested | day 2 net +0.10 vs immediate −0.067 (30, p = 0.125) | RECORD | — | MERGE→F17 | `decision_replay/experiment_log.md` §Framing fact-check |
| 19 | A seat can judge which memory applies but does not use memory by default; forcing a verdict hurt on cautious content | planted lesson rejected 13 of 20; vote 0.75 → 0.55 (20); 59% of 130 memories ignored; 12–16% of votes change | OFF (per-memory verdict exists; observations not served) | capability vs adoption | MERGE→block 87 | `decision_replay/experiment_log.md` §Applicability, §three axes |
| 20 | The word-overlap engagement proxy did not track the judge and was retired | rank correlation 0.14 (p = 0.38, 40) | LIVE (deprecated in code) | instrument validation | KEEP | `decision_replay/experiment_log.md` §B, 2026-07-02 |
| 21 | Memory adds little where the role card already states the heuristic; the A/B's wolf night gain did not replicate in replay | wolf power-targeting 0.328 → 0.328 | RECORD | — | MERGE→F17 | `decision_replay/experiment_log.md` §5, §Unifying principle |
| 22 | The v6 town gain did not repeat because the memory-off baseline rose; a same-epoch replay scored both stores alike | town +6 points (p = 0.77, 30); memory-off win 27% → 37%; v5 0.625 vs v6 0.604 vs memory-off 0.667 (48) | RECORD | experimental controls | KEEP | `v6_sp_ab/experiment_log.md`, `report.md` §v6 |
| 23 | A lesson's "follow" verdict causes the action; "not relevant" is a true ablation | abstain-lesson followed 77% abstain vs 32% baseline; not relevant 30% | LIVE (credit counts "follow") | — | MERGE→block 60 | `v6_sp_ab/experiment_log.md` §Mechanism 1 |
| 24 | Lessons were followed but decisions did not improve; they copied the town's own weak play, which motivated scoring lessons by outcome | followed 63–66% right vs 69% baseline | LIVE (credit loop) | — | KEEP | `v6_sp_ab/experiment_log.md` §Mechanism 3–4 |
| 25 | Lessons alone hurt the killer; the obs+lesson "synergy" only cancelled that harm | killer win 30% vs 47% (p = 0.33); both 53% | OFF (`context.py:22`, combined arm only) | — | MERGE→F24 | `v6_sp_ab/experiment_log.md` |
| 26 | Memory made the vigilante fire 3–4× more with lower precision: behaviour, not skill | shots +0.53 (p = 0.001); precision 80% → 67% | RECORD | — | SKIP | `v6_sp_ab/experiment_log.md` |
| 27 | Investigator findings converted to lynches at the same rate with or without memory | wolf removed after a confirmed read 60–67% in every arm | RECORD | — | MERGE→block 53 | `v6_sp_ab/experiment_log.md` §Mechanism 5 |
| 28 | Every effectiveness test before v6 served observations only (lessons disabled) | 0 lessons in 545 killer decisions | RECORD | — | MERGE→F24 | `v6_sp_ab/procedural_memory_experiment.md` |
| 29 | A one-day replay harness designed with a hard survivor cross-check, never built | — | PLAN | — | SKIP | `day_replay/design.md` |
| 30 | Seeding plan kept temperature 1 (temperature 0 not reproducible on Vertex and dulls play) and made extraction run without saving | — | PLAN | — | SKIP | `v5_seeding_plan.md` |
| 31 | Proposed merging only observations with the same net verdict; reversed later (today's clusters drop the verdict on purpose) | — | SUPERSEDED (`Agents/prompts/extraction/cell.py:140`) | — | SKIP | `paired_ab/experiment_log.md` §BATCH-MERGE |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/memory_system/effectiveness/report.md` | hub report: verdict, drift, v6 non-replication | F1, F2, F4, F6, F7, F22 |
| `evidence/memory_system/effectiveness/v5_baseline_proxy_analysis.md` | unpaired pilot on growing store | F7 |
| `evidence/memory_system/effectiveness/v5_seeding_plan.md` | store seeding and seedability plan | F8, F30 (plan only) |
| `evidence/memory_system/effectiveness/regenerate_stats.py` | recomputes pilot and pre-rebuild statistics | F7 |
| `evidence/memory_system/effectiveness/batch_results/*.jsonl` | pre-rebuild batch A and B game records | data for F7 |
| `evidence/memory_system/effectiveness/day_replay/design.md` | unbuilt one-day replay spec | plan only (F29) |
| `evidence/memory_system/effectiveness/paired_ab/report.md` | full arm-by-arm A/B statistics | F1, F2, F3, F6 |
| `evidence/memory_system/effectiveness/paired_ab/experiment_log.md` | A/B design, drift, diagnostics, net-horizon, Phase B | F1–F15, F31 |
| `evidence/memory_system/effectiveness/paired_ab/report_nethorizon.md` | net-horizon arms scored against pre-registration | F12 |
| `evidence/memory_system/effectiveness/paired_ab/nethorizon_design.md` | net-first schema and prompt spec | F12 |
| `evidence/memory_system/effectiveness/paired_ab/town_echo_read.md` | town ignored-vs-misled read | F13 |
| `evidence/memory_system/effectiveness/paired_ab/analyze_ab.py` | paired A/B analysis script | F1, F2, F3, F6 |
| `evidence/memory_system/effectiveness/paired_ab/analyze_nethorizon.py` | net-horizon scoring script | F12 |
| `evidence/memory_system/effectiveness/paired_ab/diagnose_investigator_confound.py` | investigator find-rate denominator check | F10 |
| `evidence/memory_system/effectiveness/paired_ab/diagnose_wolf_blending.py` | unconditioned blending validation | F9 |
| `evidence/memory_system/effectiveness/paired_ab/echo_read.py` | wolf dissent echo-read script | F11 |
| `evidence/memory_system/effectiveness/paired_ab/echo_read_decisions.json` | the 47 dissent decisions read | data for F11 |
| `evidence/memory_system/effectiveness/paired_ab/town_echo_read.py` | town echo-read script | F13 |
| `evidence/memory_system/effectiveness/paired_ab/situation_sim.py` | net-horizon store retrieval-comparability check | F12 |
| `evidence/memory_system/effectiveness/paired_ab/arms_game_ids.json` | 30 paired game ids | data for F1, F8 |
| `evidence/memory_system/effectiveness/paired_ab/baseline_fresh_ids.json` | 10 fresh baseline ids | data for F1, F4 |
| `evidence/memory_system/effectiveness/paired_ab/recovered_ids.json` | 20 recovered ids re-run fresh | data for F4 |
| `evidence/memory_system/effectiveness/paired_ab/seed_set.json` | frozen seed set with recorded winners | data for F8 |
| `evidence/memory_system/effectiveness/paired_ab/canary_game_ids.json` | drift canary game ids | data for F5 |
| `evidence/memory_system/effectiveness/paired_ab/canary_ext20_game_ids.json` | extended drift canary ids | data for F5 |
| `evidence/memory_system/effectiveness/decision_replay/experiment_log.md` | replay screen journey and conclusions | F13, F14, F16–F21 |
| `evidence/memory_system/effectiveness/decision_replay/report_screening_layer.md` | screening-layer draft report section | F16, F17, F18, F19 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_town_run*.json` | town day-3+ replay runs | data for F17, F21 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_town_day2_run*.json` | town day-2 replay runs | data for F17 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_town_endgame_run*.json` | town endgame replay runs | data for F17 |
| `evidence/memory_system/effectiveness/decision_replay/causal_arms_town_run*.json` | old-store town replay runs | data for F18 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_wolf_run*.json` | wolf day-vote replay runs | data for F21 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_wolf_night_run*.json` | wolf night-kill replay runs | data for F21 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_sk_night_run*.json` | killer night replay runs | data for F21 |
| `evidence/memory_system/effectiveness/decision_replay/causal_nh_town_discussion_run*.json` | town discussion stance replay runs | data for F13 |
| `evidence/memory_system/effectiveness/decision_replay/causal_smoke_nh_town.json` | N=20 noise exhibit | data for F17 |
| `evidence/memory_system/effectiveness/decision_replay/adherence_scan_nh_town.json` | adherence judge scan, 40 decisions | data for F19 |
| `evidence/memory_system/effectiveness/decision_replay/applicability_probe_nh_town.json` | planted-lesson applicability probe | data for F19 |
| `evidence/memory_system/effectiveness/decision_replay/coherence_nh_town.json` | vote–reasoning sync by schema | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/condition_grid_5cases.json` | five cases across schemas | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/echo_consideration_nh_town.json` | word-overlap engagement by schema | data for F20 |
| `evidence/memory_system/effectiveness/decision_replay/echo_judge_validation_nh_town.json` | echo vs judge correlation | data for F20 |
| `evidence/memory_system/effectiveness/decision_replay/framing_rewrite_nh_town.json` | framing rewrite, day 3+ | data for F18 |
| `evidence/memory_system/effectiveness/decision_replay/framing_rewrite_nh_town_day2.json` | framing rewrite, day 2 | data for F18 |
| `evidence/memory_system/effectiveness/decision_replay/framing_rewrite_nh_town_day5plus.json` | framing rewrite, day 5+ | data for F18 |
| `evidence/memory_system/effectiveness/decision_replay/reorder_run*.json` | reasoning-first 2×2 runs | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/reorder_test_nh_town.json` | first reorder test | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/reorder_adoption_nh_town.json` | reorder adoption judge run 1 | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/reorder_adoption3_nh_town.json` | reorder adoption judge, memory-linked | data for F14 |
| `evidence/memory_system/effectiveness/decision_replay/content_pilot/immediate_rewrites*.json` | net vs immediate outcome rewrites | data for F18 |
| `evidence/memory_system/effectiveness/decision_replay/content_pilot/source_entries.json` | 28 frozen source observations | data for F19 |
| `evidence/memory_system/effectiveness/v6_sp_ab/experiment_log.md` | v6 six-arm A/B and mechanisms | F22–F27 |
| `evidence/memory_system/effectiveness/v6_sp_ab/procedural_memory_experiment.md` | lessons-channel design and step-1 check | F28 |
| `evidence/memory_system/effectiveness/v6_sp_ab/launch_arms.sh` | arm launcher, same-epoch interleave | F22–F25 |
| `evidence/memory_system/effectiveness/v6_sp_ab/game_ids.json` | 30 held-out paired game ids | data for F22 |

### `memory_system/strategy_adoption`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Putting the lessons-followed field before the action improved the report and the action | adoption 4.00 → 4.80, action 3.97 → 4.67 (30 vs 30, same judge, different games); report's pairing 4.00 → 4.38 (30 vs 120) | LIVE (`Agents/schemas/output.py:83–94`) | structured-output field order | KEEP | `report.md`, `eval_results/` |
| 2 | Behavioural wording beat "influenced"; DO/DON'T rules added nothing | v3 4.26 vs v2 4.38 (120 each) | LIVE in spirit (follow / override / not relevant) | prompt engineering | MERGE→F1 | `report.md` |
| 3 | One hallucinating game produced v3's apparent regression | 15 of 16 action-quality-1 scores from game `888e4e81` | RECORD | — | MERGE→F2 | `report.md` |
| 4 | A direction field showed errors were mostly under-claiming, reversing the 30-turn impression | 87 accurate, 23 under, 10 over (120) | RECORD | judge diagnostics | KEEP | `report.md` |
| 5 | The ~72% ceiling was blamed on two overlapping memory types, which motivated the observations-only ablation | 87 of 120 | RECORD | — | MERGE→`memory_system/ablation/` | `report.md` |
| 6 | Integer indices replaced 36-character ids, which the model garbled | about 30% garbled | LIVE (1-based index fields) | indexed references | MERGE→block 20 | `report.md` |
| 7 | Judge rigour should follow use: comparisons need consistency, quoted levels need a blind human spot-check; never run | plan: about 28 stratified blind labels | PLAN | judge calibration by use | KEEP | `judge_validation_protocol.md` |
| 8 | The per-memory instruction was followed only when stated in the prompt body, not the field description | 0.27 → 0.97 (302/300 verdicts) → 1.0 pinned; 60 decisions, 300 slots | LIVE (`Agents/prompts/memory/context.py:31–39`) | instruction placement | KEEP | `forced_schema_screen/experiment_log.md`, `run_variants_n60.json` |
| 9 | Under-coverage was not tail-dropping and not list-tracking; numbering did not help | coverage by rank 0.45–0.68, flat; numbered 0.117–0.233 vs 0.233–0.333 | RECORD | — | MERGE→F8 | `forced_schema_screen/experiment_log.md` |
| 10 | Partial coverage inflated the engagement metric because skipped rows were mostly inapplicable | "applies" 0.80 → about 0.55; does-not-apply 34 → 133 | RECORD | missing-not-at-random bias | MERGE→F8 | `forced_schema_screen/experiment_log.md` |
| 11 | Forcing per-memory reasoning hurt on cautious v5 content, not on v6; no memory arm beat no memory | v5 0.625 → 0.521; v6 0.604 → 0.625; memory-off 0.667 (48) | OFF (observations not served) | — | MERGE→`effectiveness/` F19, F22 | `forced_schema_screen/experiment_log.md`, `run_n48.json` |
| 12 | Full coverage held in discussion with natural messages | 200 of 200 verdicts; 34 of 40 spoke | LIVE (discussion schema) | — | MERGE→F8 | `forced_schema_screen/experiment_log.md`, `run_discussion_n40.json` |
| 13 | A higher thinking level was rejected as too costly for one field | — | RECORD | — | SKIP | `report.md` |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/memory_system/strategy_adoption/report.md` | Phase 1 adoption prompt report | F1–F6, F13 |
| `evidence/memory_system/strategy_adoption/judge_validation_protocol.md` | unexecuted judge calibration protocol | F7 (plan only) |
| `evidence/memory_system/strategy_adoption/eval_configs/*.json` | dataset-build and judge-run configs | data for F1, F2 |
| `evidence/memory_system/strategy_adoption/eval_sets/*.jsonl` | frozen turns, v1/v2/v3 games | data for F1, F2 |
| `evidence/memory_system/strategy_adoption/eval_sets/*.manifest.json` | eval-set manifests | data for F1, F2 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260523_174718.jsonl` | v1 judged, 30 turns | data for F1 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260523_185600.jsonl` | v2 judged, 30 turns, old judge | data for F1 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260524_014506.jsonl` | v3 judged, 30 turns, old judge | data for F2 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260524_020604.jsonl` | v3 judged, 30 turns, direction field | data for F2, F4 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260524_021749.jsonl` | v2 judged, 120 turns | data for F1, F4 |
| `evidence/memory_system/strategy_adoption/eval_results/captured_eval_20260524_021750.jsonl` | v3 judged, 120 turns | data for F2, F3, F4 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/experiment_log.md` | forced per-memory verdict screen log | F8–F12 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_n48.json` | store × schema 2×2 results | data for F11 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_n48.log` | run log for the above | data for F11 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_coverage_n60.json` | coverage by rank, unnumbered | data for F9 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_coverage_n60.log` | run log for the above | data for F9 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_coverage_n60_numbered.json` | coverage by rank, numbered | data for F9 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_coverage_n60_numbered.log` | run log for the above | data for F9 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_variants_n60.json` | field-description vs prompt-body vs pinned | data for F8, F10 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_variants_n60.log` | run log for the above | data for F8, F10 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_discussion_n40.json` | discussion coverage under live schema | data for F12 |
| `evidence/memory_system/strategy_adoption/forced_schema_screen/run_discussion_n40.log` | run log for the above | data for F12 |

### `memory_system/v8`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | A four-game pilot (one per lineup) ran extraction through to synthesis end to end before any bulk spend | 194 observations in all 36 cells; 51 lessons; about $2 a game | RECORD | pilot before scale | MERGE→block 77 (context) | `experiment_log.md` (pilot) |
| 2 | Seeding: 12 games covered every retrieved cell from 5–12 distinct games; a game with random fallback votes was replaced; three processes on one quota hit 429s ("two, not three") | 12 games, 553 observations kept | RECORD | — | SKIP (operations) | `experiment_log.md` (bulk seeding); `data/seeding/coverage.md`, `games.json` |
| 3 | Screening Flash-Lite's lessons against the rules found wrong mechanics, mostly synthesis over-generalising facts that were right | 14 of 150 (9%); one Opus read | SUPERSEDED (that store) | auditing generated knowledge against a spec | KEEP | `data/seeding/rule_screen.md`; `experiment_log.md` |
| 4 | The screen showed the agents' rules text was wrong (the pack "agrees" its carrier; the engine rotates by seat order), so the text was fixed | 2 lessons followed the wrong text | LIVE (fixed `af67dae3`) | spec audit | MERGE→#3 | `data/seeding/rule_screen.md`, `rule_screen_sonnet.md` |
| 5 | A stronger synthesis model wrote more wrong rules: longer lessons stating more mechanics | Sonnet 32 of 164 (20%) against 9%; about 3x longer | SUPERSEDED | — | KEEP (with #3) | `data/seeding/rule_screen_sonnet.md`; `experiment_log.md` 10-12 |
| 6 | Flash-Lite's advice was generic; Sonnet's had a trigger, move, reason and exception, but put day advice into town night lessons and so brought back town day advice | median 33 against 109 words; 31 of 34 town night lessons; one reader, 7 cells | SUPERSEDED | — | KEEP (with #7) | `experiment_log.md` 10-12 |
| 7 | A prompt rule (mechanics only as the rules state them; this phase only; one move in at most three sentences) cut the errors and the day advice | 19 of 176 (11%); 1 of 32; median 66 words | LIVE (`cell.py:169`) | prompt engineering, auditing generated knowledge | KEEP | `experiment_log.md`; `data/seeding/rule_screen_sonnet2.md` |
| 8 | Screen-and-exclude: flagged lessons stay marked in the working store, and the served store leaves them out | 40-game store 37 of 605 (6.1%); readers flagged 4 to 13 per quarter | LIVE (`ten_seat_v2`, 498) | data curation | KEEP (with #3) | `experiment_log.md` 10-13; `data/reextract/points/rules_part_*.jsonl` |
| 9 | Batched synthesis cost a third of direct calls | $1.51 against $4.02; the prompts differed | LIVE | batch inference | MERGE→block 11 | `experiment_log.md` 10-12 |
| 10 | Embedder swap: each threshold re-derived on labelled pairs, not by percentile (which would have carried an old miscalibration); thresholds per model; the store refuses another model's vectors; hosts pinned | percentile would have put keep at 0.90 / 0.69; two hosts' vectors differ (cosine about 0.998) | LIVE (`embeddings.py` `SIMILARITY_THRESHOLDS`; `postgres.py:73`) | embedding model migration | KEEP | `experiment_log.md` 10-12 embedder; `data/embedder_migration/` |
| 11 | The swap was checked on retrieval before use | top-5 overlap 81%, same first lesson 55%, 236 queries; 5 disagreements read: 2 / 2 / 1 | LIVE | regression check | KEEP (with #10) | `experiment_log.md` 10-12 embedder |
| 12 | The Gemini prefilter thresholds were never remapped after the July model change and auto-keep labelled duplicates | zero errors needs keep < 0.50, against production 0.81 / 0.935 | RECORD (path retiring) | — | MERGE→block 27 | `experiment_log.md`; `data/embedder_migration/golden_gemini_embedding_2.txt` |
| 13 | On Qwen the prefilter decides fewer pairs without a model call | observations 7.5%, lessons 16% of golden cases | LIVE | — | MERGE→block 24 | `data/embedder_migration/golden_qwen3_embedding_8b.txt` |
| 14 | Batching embeddings 64 to a call | 13 min → 40 s for 710 records | LIVE | — | SKIP (operations) | `experiment_log.md` |
| 15 | Extraction model: 2.5-pro's cost was mostly thinking; 3.8 Flash was cheaper with no seat ids; Flash-Lite leaked seat ids | $1.16–1.19 against about $0.34 a game; Flash-Lite 18 of 43 in one game; 2 games | SUPERSEDED (offline default Sonnet 5.5, `scripts/extract_batch.py:47`) | model selection | MERGE→block 76 | `experiment_log.md` 10-11; `data/extraction_model_comparison/` |
| 16 | Splitting the day into discussion and vote calls filled the discussion cells | 0 → 16 discussion observations, 1 game | LIVE | task decomposition | MERGE→block 77 | `experiment_log.md`; `decisions.md` §6 |
| 17 | The pilot's one factual error came from game state dropping a dying actor's night record; fixed in the data, marked "never told" | 1 of 66 | LIVE (`bbcba5cd`) | error analysis | MERGE→block 73 | `decisions.md` §6 |
| 18 | The smoke game showed the halo; an "outcome is not credit" prompt rule about halved it | town 21 of 28 positive, evil 7 of 11 negative; about 20% → 10%, one read | LIVE (prompt) | outcome bias | MERGE→blocks 14, 83 | `experiment_log.md` smoke game; `data/dehalo_compare/` |
| 19 | The de-halo judge was chosen from four on one game | Haiku 4 of 4 clear halos, 0 supported verdicts erased, $0.006; Gemini erased 3 | LIVE (`DehaloConfig` default Haiku) | generator-verifier separation | MERGE→block 83 | `experiment_log.md`; `data/dehalo_compare/dehalo_*.json` |
| 20 | At scale de-halo revises about a quarter of verdicts, mostly to "unclear", with a few over-corrections | 146 of 567 (26%); 25%; 29% | LIVE | — | MERGE→block 83 | `experiment_log.md`; `data/seeding/games.json` |
| 21 | Haiku's thinking counts against its output limit, so de-halo JSON was cut off on 4 games; fixed and backfilled | 4 of 12 games | LIVE | — | SKIP (operations) | `experiment_log.md` |
| 22 | Claude's prefix cache never hit, because each call's enforced schema is part of the cache key; the fix puts the schema as text after the prefix, validates in code and retries with the schema enforced | $2.69 against under $0.50; the prefix 3.6k tokens smaller | LIVE (`schema_in_prompt`, `Agents/llm_factory/structured.py`) | prompt caching | MERGE→blocks 7, 10 | `experiment_log.md` 10-12 batch check |
| 23 | Haiku writes seat ids into half its observations, so it is out for extraction | 74 of 146 (51%); Sonnet 9 of 136 | LIVE (default note) | programmatic evaluation | MERGE→block 76 | `experiment_log.md` |
| 24 | On 3.8 Flash, thinking is most of the extraction bill | $10.42 for 19 games; thinking $7.35 (71%) | SUPERSEDED | cost attribution | MERGE→block 10 | `experiment_log.md` re-extraction |
| 25 | The Sonnet batch cost double its estimate: retries wrote prefixes no one read, and batch requests missed the cache; retries now go in a second batch | $19.99 against about $9.50; $7.02 + $3.01 | LIVE (fix) | cost attribution | MERGE→block 10 | `experiment_log.md` remaining 21 games |
| 26 | Extraction leaves the game: each game saves its input and an offline job extracts; past inputs were rebuilt from records and checked | identical on 12 games except 1 vote line and 14 of 120 notes | LIVE | batch inference | MERGE→block 11 | `decisions.md` §11 |
| 27 | Model-written "uses left" checked against an engine replay; the definition helped but did not fix the some-vs-none error | 84% → 89% exact; some-vs-none wrong 4.4% (Sonnet 5.8%); fix from the record PLAN | LIVE field, fix PLAN | programmatic evaluation | MERGE→block 91 | `experiment_log.md` gate part two, re-extraction |
| 28 | Sonnet-extracted games weigh more in synthesis | about 45% more observations a game | RECORD | — | MERGE→block 84 (caveat) | `experiment_log.md` 40-game store |
| 29 | Lookup reuse: one per seat per day's discussion (fresh after a new claim), one per vote, one per night (a wolf's night split in two) | about 60 → 38 lookups on 1 game | LIVE (`lookup_cache.py`) | cutting calls (retrieval caching) | KEEP | `decisions.md` §10; `plan.md` §9.3 item 9 |
| 30 | Lookups are a large share of a memory-on game's cost | Luna 20–28%; Haiku about 40% before two caching fixes | RECORD | cost attribution | MERGE→#29 | `experiment_log.md` gate part one |
| 31 | Gate read: few lessons shown fit the decision | 39 of 268 (15%); 36 of 96 lookups; discussion 7%, vote 13%, night 19% | LIVE (problem stands) | retrieval evaluation | KEEP | `data/gate/read/`; `experiment_log.md` |
| 32 | The search matched the role, not the stage, and the score did not track fit | in one healer lookup worst fit 0.887, best 0.829 | LIVE | embedding limits | KEEP (with #31) | `data/gate/read/part_1_summary.md` |
| 33 | Seats rejected most misfits themselves; the mixed cases include a fitting lesson dismissed on a false premise and one confident follow on a bad analogy | sound 65, mixed 25, never wrong outright | LIVE | — | KEEP (with #31) | `data/gate/read/part_*_summary.md` |
| 34 | Situation errors: 37 lookups had one, 8 of them from the query's own code-written swing line (fixed); no concealed role stated as fact | 37 of 96; 8 | LIVE (`6c3d2329`) | — | MERGE→block 88 / parked note | `experiment_log.md`; `data/gate/read/part_*_summary.md` |
| 35 | The pass mark was set before running, and relevance failed | 1 in 7 fits | RECORD | decision rule fixed in advance | KEEP (with #31) | `plan.md` §8.7; `experiment_log.md` |
| 36 | A reader suspected some lessons came from the game being played; not verified, and the 12-game store predates the gate games | 1 game | RECORD | — | SKIP | `data/gate/read/part_4_summary.md` |
| 37 | The replay was checked before the filter result was trusted | 91 of 96 reproduced | RECORD | instrument validation | KEEP | `experiment_log.md` gate part two |
| 38 | Stage filter: fit rose, at the cost of a quarter of the fitting lessons; refilling the gaps mostly added misfits | 15% → 25%, 25 empty; drops 101 of 146 misfits and 10 of 39 fits; 2 of 28 refills fit | OFF (`DEFAULT_STAGE_FILTER = False`) | metadata filtering | KEEP | `data/gate/stage_filter/` |
| 39 | On the 40-game store, refilling from the same stage gives most lookups a fitting lesson; the remaining misfits are tied to events the stage fields do not record | 24% fit; 52 of 96 lookups; 2 empty; different readers | OFF (on in the demo run) | metadata filtering | KEEP (with #38) | `data/gate/stage_filter_40games/`; `data/reextract/fit/` |
| 40 | Some lessons were written from sources that disagreed on the stage label they carry; synthesis now splits by stage and the dedup refuses to merge across stages | partner-lost 17 of 72 (24%); uses-left 54 of 270 (20%) | LIVE (`synth_partition_key`; `08dea470`) | data consistency audit | KEEP (with #38) | `experiment_log.md` 10-13 |
| 41 | Readers found duplicates the lesson dedup missed, because it splits on noisy labels before comparing | 65 groups, 78 lessons (13%); 37 groups crossed the labels | LIVE (applied in `ten_seat_v2`) | near-duplicate clustering | MERGE→block 18 | `data/reextract/points/dups_part_*.jsonl`; `experiment_log.md` |
| 42 | A dry run of the dedup judge against the readers' groups: it caught few, and merged across stages and across different moves | 9 or 16 of 65; 25 of 55 drops across stages | LIVE (stage-refuse; dedup model now Haiku) | golden-set evaluation | MERGE→blocks 18, 23 | `data/reextract/dedup_dry_run/` |
| 43 | Showing the whole cell for cells of 3 or fewer lessons was not built | 10 of 24 cells | PLAN | — | SKIP | `decisions.md` §10 |
| 44 | Memory-off baselines graded by the new table look as the rules predict | Fortune Teller −0.60, Sigilist −0.35, pack kill +0.42 | LIVE | sanity check | MERGE→block 59 | `experiment_log.md` reopened |
| 45 | Four grading principles: grade what the actor controls; a predictable failure is the actor's; being seen is a cost; a wasted use is bad | — | LIVE (`grading.py`) | reward design | MERGE→block 58 | `decisions.md` §12; `plan.md` §9.6 item 10 |
| 46 | The Necromancer is left unscored and the Illusionist marked hard to gauge | — | LIVE | — | MERGE→block 58 | `decisions.md` §12 |
| 47 | Halo by game: verdicts follow the side winning about twice as strongly as the move's grade; de-halo cuts it on the losing side only | 482 observations, 19 games; losers' negatives 53% → 27%, winners' positives 57% → 54% | LIVE | bias measurement | MERGE→blocks 82, 83 | `data/halo/rows.jsonl`, `summary.json`; `decisions.md` §13 |
| 48 | Halo by observation holds in every phase; votes and discussion follow the result most | 1,472 observations, 40 games | LIVE | bias measurement | MERGE→block 82 | `data/halo/observation_*`; `decisions.md` §13 |
| 49 | Observations tagged with their decision, checked blind against a bar set beforehand | 98 of 102 (bar 90%); flagged set 24 of 25; text-day agreement 95–97%; $0.08 | LIVE (`decision_day` field) | blind annotation | MERGE→block 82 | `data/decision_tags/` |
| 50 | Served games graded from records rebuilt from the server's event log | 1,711 of 2,277 observations graded | LIVE | — | MERGE→block 84 | `experiment_log.md` reopened |
| 51 | A grade-variant store was built but not reviewed or compared | 568 lessons, $4.75 | PLAN | — | MERGE→block 84 | `experiment_log.md`; `decisions.md` §13 |
| 52 | Credit split into a free credit step after every game and a paid, batched learning step; prune and evict apply automatically; a merged duplicate's credit follows its survivor | thresholds from v7, unvalidated | LIVE (`tick.py` `credit` / `learn`) | — | MERGE→blocks 58, 62 | `decisions.md` §14 |
| 53 | Demo credit pass: the mechanism works on ten seats; one lesson was pruned on neutral grades alone, against a good memory-off baseline | 148 of 498 followed; 4 pruned, 4 evicted, 50 proven; 20 games | LIVE (490 lessons) | — | MERGE→block 59 | `experiment_log.md` 10-14 |
| 54 | Haiku copied the prompt example's "followed lesson 1" onto turns shown no lessons; such turns now get no verdict field or example | 426 turns | LIVE (`a1e47ad6`) | few-shot example copying | KEEP | `experiment_log.md` 10-14 |
| 55 | Without an enforced schema, seat replies broke; a broken reply is now asked again with the schema enforced | 74 replies, 6 to the rescue model | LIVE (`7f508c4d`, `68cef8b0`) | structured output | MERGE→#22 / block 7 | `experiment_log.md` 10-14 |
| 56 | An audit found the nine-seat cast hard-coded: silent mis-scores and 21 metrics reading 0 on every ten-seat game; ported | 21 metrics | LIVE (`fa6ce77e`, `e5763cd1`) | migration audit (silent failures) | KEEP | `decisions.md` §1–2, §8; `plan.md` §8.2–8.4 |
| 57 | The replay dropped later discussion turns; the server took memory on with the nine-seat store, so `WW_MEMORY_ENABLED` now gates it, off by default | — | LIVE | — | MERGE→block 62 | `decisions.md` §2; `plan.md` §8.6 |
| 58 | D1: town day lessons extracted for review, never retrieved, which closes the v7 abstain route by scope | — | LIVE (`plan_gating.py:18`) | scope narrowing | KEEP | `decisions.md` §5, §7; `plan.md` §9.1 |
| 59 | D2: no disclosure rule was added, because saved games showed the roles already report | Investigator 13 of 13 and 25 of 28; Sentinel 42 of 42; Trailseer 44 of 44; 28 games, rough counts | LIVE (no change) | check behaviour before legislating | KEEP (with #58) | `plan.md` §9.1; `decisions.md` §5 |
| 60 | D3: new roles reuse existing cell shapes, plus one "uses left" field group | — | LIVE | schema design | MERGE→block 87 | `plan.md` §9.1; `decisions.md` §5 |
| 61 | An outside review separated recorded fact, supported explanation and strategic conclusion; the evidence rule ("a sequence is not a cause") followed; counterfactual wording left as it was | about 6 of 66 hindsight verdicts in the pilot | LIVE (prompt) | faithfulness constraints | MERGE→block 75 | `decisions.md` §4, §6; `plan.md` §3, §9.2 |
| 62 | The leak screen flagged a wolf's own wolf-chat phrase as a leak | 4 false positives, 1 game | RECORD | — | MERGE→block 3 | `experiment_log.md` pilot |
| 63 | Sizing any future effect test: games per arm, and follows for the verdict-against-grade comparison | about 35 games per arm for +0.20, 60 for +0.15; about 1,000 follows per variant | PLAN | power analysis | MERGE→blocks 64, 84 | `plan.md` §9.6 item 9; `decisions.md` §13 |
| 64 | Investigator diagnostics split what the actor did from what the team did with it | — | PLAN | — | MERGE→parked "grade the decision, not the result" | `plan.md` §4 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/memory_system/v8/README.md` | Folder index and status as of 2026-10-11 | index |
| `evidence/memory_system/v8/experiment_log.md` | Run record: pilot to demo credit pass | F1–F42, F44, F47–F55, F62 |
| `evidence/memory_system/v8/decisions.md` | Owner rulings with the reasoning and commits | F16, F17, F26, F29, F43, F45–F47, F49, F52, F56–F61, F63 |
| `evidence/memory_system/v8/plan.md` | Plan; §9 final, earlier sections superseded | F35, F45, F56–F60, F61, F63, F64 (plan only beyond these) |
| `evidence/memory_system/v8/prompt_versions/seeding_2026-10-11.md` | Extraction and synthesis prompts before the mechanics rule | data for F3, F7 |
| `evidence/memory_system/v8/data/decision_tags/*.answers.json` | Blind reader's decision per sampled observation, 6 games | data for F49 |
| `evidence/memory_system/v8/data/decision_tags/disagreements.json` | The four tag/reader disagreements | data for F49 |
| `evidence/memory_system/v8/data/decision_tags/manifest.json` | Sampled observations per game, random and flagged | data for F49 |
| `evidence/memory_system/v8/data/decision_tags/summary.json` | Blind-read agreement, 98 of 102 | data for F49 |
| `evidence/memory_system/v8/data/decision_tags/tag_run.json` | Tagging pass counts, free checks, cost | data for F49 |
| `evidence/memory_system/v8/data/dehalo_compare/dehalo_*.json` | Four de-halo judges' verdicts on the smoke game | data for F19 |
| `evidence/memory_system/v8/data/dehalo_compare/extraction*.json` | Smoke-game extraction by three models | data for F18, F19 |
| `evidence/memory_system/v8/data/embedder_migration/embed_calibration.py` | Study script: embeds calibration texts on both models | data for F10 (study code, frozen) |
| `evidence/memory_system/v8/data/embedder_migration/remap.py` | Study script: percentile threshold remap (rejected method) | data for F10 (study code, frozen) |
| `evidence/memory_system/v8/data/embedder_migration/golden_*.txt` | Zero-error threshold sweeps per embedder | data for F10, F12, F13 |
| `evidence/memory_system/v8/data/extraction_model_comparison/*.json` | Two pilot games re-extracted by Flash and Flash-Lite | data for F15 |
| `evidence/memory_system/v8/data/gate/lookups.jsonl` | All 352 gate lookups with true roles | data for F30, F31 |
| `evidence/memory_system/v8/data/gate/read/part_*.jsonl` | Per-lesson fit judgements, four readers | data for F31–F34 |
| `evidence/memory_system/v8/data/gate/read/part_1_summary.md` | Reader 1 summary: fit, errors, inverted scores | F31, F32, F33, F34 |
| `evidence/memory_system/v8/data/gate/read/part_2_summary.md` | Reader 2 summary: fit, situation errors | F31, F33, F34 |
| `evidence/memory_system/v8/data/gate/read/part_3_summary.md` | Reader 3 summary: fit, verdict problems | F31, F33, F34 |
| `evidence/memory_system/v8/data/gate/read/part_4_summary.md` | Reader 4 summary; unverified provenance flag | F31, F33, F34, F36 |
| `evidence/memory_system/v8/data/gate/sample/part_1.md` | Rendered lookups given to reader 1 | data for F31 |
| `evidence/memory_system/v8/data/gate/sample/part_2.md` | Rendered lookups given to reader 2 | data for F31 |
| `evidence/memory_system/v8/data/gate/sample/part_3.md` | Rendered lookups given to reader 3 | data for F31 |
| `evidence/memory_system/v8/data/gate/sample/part_4.md` | Rendered lookups given to reader 4 | data for F31 |
| `evidence/memory_system/v8/data/gate/stage_filter/read.jsonl` | Reads of the 28 lessons the filter promoted | data for F38 |
| `evidence/memory_system/v8/data/gate/stage_filter/replay.jsonl` | 96 lookups replayed, filtered and unfiltered | data for F37, F38 |
| `evidence/memory_system/v8/data/gate/stage_filter/to_read.md` | Promoted lessons rendered for the reader | data for F38 |
| `evidence/memory_system/v8/data/gate/stage_filter_40games/replay.jsonl` | 96 lookups replayed on the 40-game store | data for F39 |
| `evidence/memory_system/v8/data/gate/stage_filter_40games/to_read.md` | 40-game replay lessons rendered for readers | data for F39 |
| `evidence/memory_system/v8/data/halo/rows.jsonl` | Per-role-per-game verdict, grade, side won | data for F47 |
| `evidence/memory_system/v8/data/halo/summary.json` | Halo fit and verdict mix, 482 observations | data for F47 |
| `evidence/memory_system/v8/data/halo/observation_rows.jsonl` | Per-observation verdict against its decision's grade | data for F48 |
| `evidence/memory_system/v8/data/halo/observation_summary.json` | Halo fit by phase, 1,472 observations | data for F48 |
| `evidence/memory_system/v8/data/reextract/dedup_dry_run/direction_honesty.jsonl` | Dry-run dedup groups, current split | data for F42 |
| `evidence/memory_system/v8/data/reextract/dedup_dry_run/honesty.jsonl` | Dry-run dedup groups, honesty-only split | data for F42 |
| `evidence/memory_system/v8/data/reextract/dedup_dry_run/summary.json` | Dry run against readers' 65 groups | data for F42 |
| `evidence/memory_system/v8/data/reextract/fit/part_1.md` | 40-game lookups rendered for fit reader 1 | data for F39 |
| `evidence/memory_system/v8/data/reextract/fit/part_2.md` | 40-game lookups rendered for fit reader 2 | data for F39 |
| `evidence/memory_system/v8/data/reextract/fit/part_3.md` | 40-game lookups rendered for fit reader 3 | data for F39 |
| `evidence/memory_system/v8/data/reextract/fit/part_4.md` | 40-game lookups rendered for fit reader 4 | data for F39 |
| `evidence/memory_system/v8/data/reextract/fit/read_part_*.jsonl` | Per-lesson fit judgements, 40-game store | data for F39 |
| `evidence/memory_system/v8/data/reextract/points/dups_part_*.jsonl` | Readers' duplicate groups with the lesson kept | data for F41 |
| `evidence/memory_system/v8/data/reextract/points/rules_part_*.jsonl` | Readers' wrong-rule flags (7, 13, 13, 4) | data for F8 |
| `evidence/memory_system/v8/data/reextract/points/part_1.md` | 40-game lessons by cell for reader 1 | data for F8, F41 |
| `evidence/memory_system/v8/data/reextract/points/part_2.md` | 40-game lessons by cell for reader 2 | data for F8, F41 |
| `evidence/memory_system/v8/data/reextract/points/part_3.md` | 40-game lessons by cell for reader 3 | data for F8, F41 |
| `evidence/memory_system/v8/data/reextract/points/part_4.md` | 40-game lessons by cell for reader 4 | data for F8, F41 |
| `evidence/memory_system/v8/data/reextract/rules.md` | Ten-seat rules block the readers judged against | data for F8, F39, F41 |
| `evidence/memory_system/v8/data/seeding/coverage.md` | Observations, games, lessons per cell, 12-game store | F2 |
| `evidence/memory_system/v8/data/seeding/games.json` | Per seeding game: lineup, winner, de-halo counts | data for F2, F20 |
| `evidence/memory_system/v8/data/seeding/rule_screen.md` | Flash-Lite lessons screen: 14 of 150; rules-text bug | F3, F4 |
| `evidence/memory_system/v8/data/seeding/rule_screen_sonnet.md` | Sonnet lessons screen: 32 of 164 | F4, F5 |
| `evidence/memory_system/v8/data/seeding/rule_screen_sonnet2.md` | Revised-prompt screen: 19 of 176 | F7 |
| `evidence/memory_system/v8/data/seeding/strategy_points*.json` | The three synthesized lesson sets screened | data for F3, F5, F7 |

### `metrics`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Grade each decision against the true roles, divide by the chances the seat had, keep only scores that move with their side's win in the direction written down beforehand | 48 tested, 11 kept, 3 used only to explain, 5 quarantined | LIVE (batch; ten-seat port unvalidated) | proxy-metric validation | KEEP | `report.md` §1–4, `experiment_log.md` DECISION, `candidate_ledger.md` |
| 2 | The town vote scores held on two batches | lynches that hit evil +0.65 on 50 games, +0.64 on 30 memory-off, +0.65 on 180; healer town-save +0.36 → +0.40 | LIVE (ported, unvalidated) | replication | KEEP (number for 1) | `proxy_win_monotonicity.md`, `report.md` §2 |
| 3 | Memory moves both a score and the win, so each check was also read on memory-off games alone | 30 of 50 games | RECORD | confound control | MERGE→1 | `report.md` §1, `proxy_win_monotonicity.md` |
| 4 | Count measures, not rows: 11 kept scores are 6 measures, two rows sum to 1 by construction; one primary score per measure, named in advance | 11 rows → 6 measures → 7 primaries | LIVE (convention in report) | multiple-comparison discipline | KEEP | `report.md` §2 |
| 5 | Finding a wolf did not track winning; turning the find into a lynch did | find rate −0.00 (169 games); find → lynch +0.40 (117 games) | LIVE (ported); fed the nine-seat investigator credit rule, which the ten-seat rule has replaced (`grading.py:248`) | metric validity | KEEP | `design/town_metric_refinement.md`, `report.md` §3 |
| 6 | A backwards result on a small sample vanished at a larger one | find day +0.38 (p=.039, 30 games) → +0.15, not significant (180) | RECORD | sample size | MERGE→block 37 | `proxy_win_monotonicity.md`, `metrics_audit/proxy_discovery_log.md` ③.A |
| 7 | A raw healer save rate meant nothing; splitting saves by who was saved worked; widening "wolf" to "any evil" helped one score and diluted another | save rate +0.10; town save +0.36; saving a wolf −0.31; power-role deaths −0.21 → −0.40 | LIVE | metric design | MERGE→1 | `proxy_win_monotonicity.md`, `design/town_metric_refinement.md` |
| 8 | Two counting bugs caught by recomputing on the real code path: a double-counted death, and an unsaved bullet count that silently cut a rate to the games where the vigilante shot | bullets saved in 0 of 180 records; rate shrank to 53 games, fixed to 180 | LIVE (fixed) | recompute verification | MERGE→1 | `design/town_metric_refinement.md` |
| 9 | A score can track winning only because it restates it; screen by correlation with survival | serial killer "suspicion drawn" −0.71 (≈ got lynched); killing a wolf +0.30 after the survival control | RECORD (tiers) | construct validity | MERGE→1 | `design/deceiver_metric_refinement.md`, `design/score_tier_design.md` |
| 10 | Wolves win by blending in, not by leading the lynch | leading −0.09 (53 games); blending +0.27 (180); no wolf among the accusers on 109 of 169 mislynch days | LIVE (credit's pack-vote rule, `grading.py:311`) | — | MERGE→block 58 | `design/deceiver_metric_refinement.md`, `design/discussion_scoring_plan.md`, `design/discussion_lead_vs_blend.py` |
| 11 | The scoring uses no model and runs the same code in both arms; model judges never decide a memory verdict; making agents output belief vectors was rejected because it would change play | — | LIVE (rule) | measurement design | MERGE→1 | `experiment_log.md`, `report.md` §5–6 |
| 12 | The tiers live in code; quarantined fields are pushed with a `dnu_` prefix | 3 frozensets | LIVE (`Agents/compute_metrics.py`) | — | MERGE→1 | `report.md` §3 |
| 13 | The figures do not carry over to a new game version; rerun the check before citing | vigilante shot in 72% of games, then 29% | LIVE caveat (ten-seat unvalidated) | — | MERGE→1 (gaps) | `report.md` §2 |
| 14 | The vigilante has no validated score; a "sign safe by logic, too few events to test" status was created | +0.18 on 53 shooter games; about 800 games needed | RECORD | power analysis | SKIP | `report.md` §3, `experiment_log.md` 2026-07-07 |
| 15 | A typed score object to stop double counting was designed, never built | — | PLAN | — | SKIP | `design/score_tier_design.md` |
| 16 | Plan to score discussion with a post-game tagger (built later in `discussion_tagger/`) | — | PLAN | — | SKIP | `design/discussion_scoring_plan.md` |
| 17 | Wolves cannot win in games where the serial killer is never lynched, so those games hid wolf skill; removing them rescued a wolf night score | 77 of 180 games; +0.31 on 103 games; halves +0.26 / +0.38 | LIVE (nine-seat, used only to explain) | stratification | MERGE→1 | `metrics_audit/proxy_discovery_log.md` ③.A |
| 18 | Discovery and confirmation halves split by deal, so the same deal under different memory arms never sits in both halves | 30 deals × 6 arms | RECORD | holdout validation | MERGE→1 | `metrics_audit/proxy_discovery_log.md` ③.0 |
| 19 | A direction written down in advance was wrong: wolves who accuse town players lose | −0.33, both halves | RECORD | pre-registration | MERGE→1 | `metrics_audit/proxy_discovery_log.md` ③.B |
| 20 | Town discussion adds nothing beyond the vote, because the vote is its only route to the result; deceivers' talk acts on others' votes | +0.34 raw → +0.02 with the vote held fixed (175 games); tagger town +0.02 vs wolf +0.56 / killer +0.60 (24 games) | RECORD; fed the July credit redesign (not traced into ten-seat code) | mediation analysis | KEEP | `experiment_log.md` 2026-07-07, `report.md` §3, `metrics_audit/proxy_discovery_log.md` ④ |
| 21 | Next-day convergence on a found wolf is a faster form of finding 5 | +0.31 (117 games) | LIVE (nine-seat, used only to explain) | — | SKIP | `metrics_audit/proxy_discovery_log.md` ③.C |
| 22 | Scores built on claims could not be tested: no saved claims existed | 0 of 180 games | RECORD | — | SKIP | `metrics_audit/proxy_discovery_log.md` ③.C |
| 23 | Spot check of accusation labels: one counter-defence labelled as an accusation | 1 of 20 | RECORD | — | SKIP | `metrics_audit/proxy_discovery_log.md` ③.B |
| 24 | Speaking order did not starve the investigator or wolf; unconverted finds were withheld or ignored, so no scheduler redesign | 58 of 58 spoke; 12 of 54 unconverted: 0 no floor, 0 late, 7 withheld, 5 ignored; wolves had the floor before the pile-on on 65 of 85 days | RECORD (a decision not to build) | hypothesis falsification | KEEP (in the case study) | `metrics_audit/scheduler_bias_log.md` A, C |
| 25 | A muted turn looked the same as a voluntary pass, so two fields were added to the record | 890 passes, 0 with text | LIVE (`game_events.py`) | instrumentation | MERGE→`tracing/` | `metrics_audit/scheduler_bias_log.md` B |
| 26 | A silent failed kill went unnoticed; told, the attacker acts; so every attacker is now told | wolves silent on 45 of 66 vs 38 of 123 after a heal; vigilante 8 of 9 | LIVE (`night_record.py:109`, commit `51de1917`) | error analysis by layer | KEEP | `metrics_audit/scheduler_bias_log.md` ③.E |
| 27 | Two find-conversion figures that disagreed were both right: different sets, averaging and roles | 60% vs 78% | RECORD | — | SKIP | `metrics_audit/scheduler_bias_log.md` ③.D |
| 28 | If the serial killer is never lynched, town and wolves both never win; attacking the killer did not change whether it was lynched | 0 town and 0 wolf wins; correlation +0.005 | RECORD (nine-seat) | — | MERGE→26 (motivation) | `design/deceiver_metric_refinement.md` |
| 29 | The rewritten scoring was checked by unit assertions and one live game | 25 of 25 | RECORD | — | SKIP | `experiment_log.md` Implementation |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/metrics/README.md` | Map of the scoring system across seven locations | index |
| `evidence/metrics/report.md` | How the scoring works; kept scores; tiers; gaps | F1, F2, F3, F4, F5, F11, F12, F13, F14, F20 |
| `evidence/metrics/candidate_ledger.md` | All 48 tested scores, by tier and role | F1 |
| `evidence/metrics/experiment_log.md` | June design journey; July follow-ups | F1, F11, F14, F20, F29 |
| `evidence/metrics/proxy_win_monotonicity.md` | 50-game score-versus-win table (June) | F2, F3, F6, F7 |
| `evidence/metrics/design/town_metric_refinement.md` | Town scores re-checked on 180 games; two bugs | F5, F7, F8 |
| `evidence/metrics/design/deceiver_metric_refinement.md` | Wolf and killer scores; survival screen | F9, F10, F28 |
| `evidence/metrics/design/score_tier_design.md` | Design of a typed score object, unbuilt | F9, F15 |
| `evidence/metrics/design/discussion_scoring_plan.md` | Plan to score discussion; wolf lead-vs-blend result | F10, F16 |
| `evidence/metrics/design/discussion_lead_vs_blend.py` | Script for the wolf lead-vs-blend test | data for F10 |
| `evidence/metrics/design/smoke_v2.jsonl` | One live game's computed scores | data for F29 |
| `evidence/metrics/design/smoke_v2.log` | Run log of that one game | data for F29 |
| `evidence/metrics/metrics_audit/proxy_discovery_log.md` | July audit: rescue and discovery, split halves | F6, F17, F18, F19, F20, F21, F22, F23 |
| `evidence/metrics/metrics_audit/scheduler_bias_log.md` | July audit: speaking order, muted turns, silent kills | F24, F25, F26, F27 |
| `evidence/metrics/metrics_audit/data/README.md` | Index of the audit's data files | index |
| `evidence/metrics/metrics_audit/data/accusation_label_sample.json` | 20 parsed accusations for a spot check | data for F23 |
| `evidence/metrics/metrics_audit/data/accusation_metrics.json` | Accusation-score correlations, full set and halves | data for F19, F20 |
| `evidence/metrics/metrics_audit/data/claim_conversion.json` | Claim coverage check; next-day convergence | data for F21, F22 |
| `evidence/metrics/metrics_audit/data/floor_access.json` | Turns per role; investigator and wolf floor | data for F24 |
| `evidence/metrics/metrics_audit/data/gate_silencing.json` | Pass markers: none carry text | data for F25 |
| `evidence/metrics/metrics_audit/data/proxy_followup_rescue.json` | Discussion held at the vote; vigilante retest | data for F14, F20 |
| `evidence/metrics/metrics_audit/data/proxy_rescue.json` | Wolf night and investigator rescue correlations | data for F6, F17 |
| `evidence/metrics/metrics_audit/data/reveal_withhold.json` | Unconverted finds sorted into floor, withheld, ignored | data for F24 |
| `evidence/metrics/metrics_audit/data/whiff_conversion.json` | Failed-kill conversion by attacker, set and layer | data for F26 |

### `refactor`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | The real gap was tests: three eval-critical paths had none, and their failure is a plausible wrong number a smoke game cannot catch; tests first, then the refactor | 27 tests, 22 on the scheduler; today 1,878 | LIVE (practice; winner test exists) | regression testing | MERGE→instruments topic | `evidence/refactor/structure_audit.md` §3, §5 |
| 2 | The top-level folders were one unlabelled pipeline, not duplicates | — | SUPERSEDED (data-plane reorg) | — | SKIP | `evidence/refactor/structure_audit.md` §1 |
| 3 | Plan to split `agents.py` into three, with an import hazard to fix first | — | SUPERSEDED (`agents.py` dissolved) | — | SKIP | `evidence/refactor/structure_audit.md` §2 |
| 4 | Six scripts reimplemented the eval loop around shared parts | 6 scripts | LIVE as a rule (`CLAUDE.md`) | — | MERGE→6 | `evidence/refactor/structure_audit.md` §4 |
| 5 | 16 per-role node functions collapsed into factories, accepted on tests, an identical fingerprint and a read of the span-naming code | 95 tests; prompt hash `c35e68e2d0cca9f0` | SUPERSEDED (both factories gone) | behaviour-neutral refactor | MERGE→`tracing/fingerprinting/` | `evidence/refactor/node_factory_pattern.md` |
| 6 | Code lives in `evaluation/`, the record in `evidence/` pointing back by fingerprint; old records frozen; code moves in only when adopted | — | LIVE (`CLAUDE.md`) | research record keeping | MERGE→`tracing/fingerprinting/` | `evidence/refactor/eval_architecture_convention.md` |
| 7 | The prompt freeze protected labels that did not exist yet; the constraint left was not to fold prompt changes into the refactor | — | RECORD | — | SKIP | `evidence/refactor/structure_audit.md` §5 |
| 8 | Deletion candidates: a stale notebook, a dead archive folder | 1,532 lines in the archive | RECORD | — | SKIP | `evidence/refactor/structure_audit.md` §6 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/refactor/structure_audit.md` | June repo audit: test gap, layout, sequencing | F1, F2, F3, F4, F7, F8 |
| `evidence/refactor/node_factory_pattern.md` | Node-function collapse into factories and its gate | F5 |
| `evidence/refactor/eval_architecture_convention.md` | Code-versus-record rule; freeze the archive | F6 |

### `retrieval/filtering`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Similarity search returns many versions of one lesson; the problem is repetition, not wrong topics | 12 observations for one investigator turn (uncapped run, range 3–12) | LIVE (the cap exists for this) | retrieval | KEEP (block 40) | `report.md`; `03_lambda08_flash_nocap.md` |
| 2 | One filter per kind of memory: drop near-copies of observations, diversity re-pick (MMR) for strategy points | — | OFF (all roles False) | retrieval filtering | MERGE→block 41 | `report.md` |
| 3 | A similarity line of 0.85 removed too much, so it was raised to 0.92; the line is now kept per embedding model | observations per turn 4.9→1.6, relevance 4.30→2.70; 5 of 10 cases cut to one, two of them from 15 and 16 candidates; 10 cases, 2.5 Pro judge; now 0.87 (gemini-embedding-2), 0.80 (Qwen) | LIVE as a per-model table; the filter is OFF | embedding limits | KEEP (block 46; could MERGE→27) | `01_baseline_threshold085_pro.md`; `report.md` |
| 4 | The report's "opposing lessons were merged" example is not in its own run 1 (the 0.85 line kept that pair) | 1 case | RECORD | — | MERGE→block 46 (already its caveat) | `01_baseline_threshold085_pro.md`; `report.md` addendum |
| 5 | Diversity weight λ=0.8 was chosen because lower values pulled in advice for the wrong phase | λ=0.8: strategy-point relevance 3.20 (run 3), 3.00 (run 4); runs at lower λ not found in the folder | OFF | — | SKIP (no run evidence; filter off) | `report.md`; `03_…`; `04_…` |
| 6 | A cap of 3 per situation always runs as a hard limit | uncapped 7.4 observations per turn (3–12); capped 5.0 (3–6); 5 cases | LIVE | context budget | MERGE→block 44 | `03_…`; `04_final_cap3_cluster_prompt.md`; `report.md` |
| 7 | The cheapest judge (Flash-Lite) could not tell sets apart and broke its schema | about 30% malformed (lists of 3 where the schema allowed 2); 2.5 Flash 0% | SUPERSEDED (judges now Haiku 5.5) | judge model choice | KEEP (inside block 45) | `02_threshold092_flashlite.md`; `report.md` |
| 8 | The judge contradicted itself; grouping items by lesson before scoring, and flipping redundancy to efficiency, fixed it | one 9-item set scored 5/5/5; 5 cases per run | LIVE (judge prompt) | LLM-as-judge, judge design | KEEP (block 45) | `03_…` l.221; `04_…`; `report.md` |
| 9 | Coverage limits retrieval: the healer's day-vote case scored relevance 1 in every setting because no lesson existed for it | 1 case | RECORD | coverage analysis | MERGE→block 38 (block 42) | `04_…`; `report.md` |
| 10 | Final filter setup scores: observations relevance 4.20, efficiency 3.40; strategy points 3.00 / 2.00 / 1.20 unique | 5 cases | OFF | — | SKIP (superseded the same day; it is the reranker's baseline) | `04_…`; `report.md` |
| 11 | Runs changed two things at once, and the same unfiltered retrieval scored relevance 4.30 under Pro but 3.00 under Flash-Lite: score levels do not carry across judge models | 4.30 (10 cases) vs 3.00 (4 of 5 scored) | RECORD | — | MERGE→block 45 (caveat) | `01_…`; `02_…`; `report.md` |
| 12 | "Reranking parked: similarity order was enough", overtaken the same day by `reranking/` | — | SUPERSEDED | — | SKIP | `report.md` |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/retrieval/filtering/01_baseline_threshold085_pro.md` | Run 1: 10 cases, 0.85 line, 2.5 Pro judge | F3, F4, F11 |
| `evidence/retrieval/filtering/02_threshold092_flashlite.md` | Run 2: 0.92 line, Flash-Lite judge, malformed outputs | F7, F11 |
| `evidence/retrieval/filtering/03_lambda08_flash_nocap.md` | Run 3: λ 0.8, 2.5 Flash judge, no cap | F1, F5, F6, F8 |
| `evidence/retrieval/filtering/04_final_cap3_cluster_prompt.md` | Run 4: cap 3, group-first judge prompt | F6, F8, F9, F10 |
| `evidence/retrieval/filtering/report.md` | Study report with 2026-10-14 addendum | F1–F12 |

### `retrieval/reranking`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | On the cleaned store, strategy points still came back right topic, wrong moment | efficiency 1.80, redundancy 72.3%, 1.20 distinct lessons; 5 cases (row from `dedup/store_retrieval_impact/`) | RECORD | retrieval | KEEP (block 40) | `report.md` |
| 2 | A model re-orders candidates by situation: Flash-Lite, shown only situations and candidates, skips at ≤3 items | one call per turn | OFF (`rerank_agent.py`; both switches False) | reranking | KEEP (block 41) | `report.md` |
| 3 | Re-ordering alone doubled strategy-point efficiency and cut repetition | efficiency 1.80→3.60, redundancy 72%→40%, relevance 3.20→3.80; 5 cases | OFF | reranking | KEEP (block 41) | `01_rerank_on_clean_store.md`; `report.md` |
| 4 | Filtering plus re-ordering scored below re-ordering alone | efficiency 2.20, relevance 3.00; 5 cases | OFF | — | KEEP (inside block 41) | `01_rerank_on_clean_store.md`; `report.md` |
| 5 | Observations did not need re-ordering | distinct lessons 3.00→2.00, relevance 4.60→4.40; 5 cases | OFF | — | MERGE→block 41 | `01_rerank_on_clean_store.md`; `report.md` |
| 6 | On the uncleaned store, re-ordering matched the cleaned store for strategy points | relevance 4.00, efficiency 3.40 vs 3.80 / 3.60; 5 cases | OFF | — | MERGE→block 41 (one clause) | `02_rerank_on_dirty_store.md`; `report.md` |
| 7 | The healer's day-vote case stayed at relevance 1: no lesson existed for it | 1 case | RECORD | — | MERGE→block 38 (block 42) | `01_rerank_on_clean_store.md`; `report.md` |
| 8 | The recommended setup never shipped; the served game reranks nothing; the paired A/B ran a reranked arm | — | RECORD | — | MERGE→`memory_system/effectiveness/` | `report.md` addendum |
| 9 | A cross-encoder was trained as a free replacement but never wired in | — | OFF | — | MERGE→block 44 / `fine_tuning/cross_encoder/` | `report.md` addendum |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/retrieval/reranking/01_rerank_on_clean_store.md` | Rerank-only and filter-plus-rerank on the cleaned store | F3, F4, F5, F7 |
| `evidence/retrieval/reranking/02_rerank_on_dirty_store.md` | Rerank-only on the uncleaned store | F6 |
| `evidence/retrieval/reranking/report.md` | Study report with 2026-10-14 addendum | F1–F9 |

### `sequential_discussion`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Fairness matters only at the vote. So the vote stays blind and simultaneous, and the discussion is free to go one speaker at a time; a random order was rejected because it ignores who the conversation needs | — | LIVE (`fan_out_vote`, `Agents/graphs/day.py`) | orchestration design | KEEP | report.md Motivation, §1; experiment_log.md §1–2 |
| 2 | Concurrent rounds hide redundancy by construction: five blind near-identical day-1 openers, four identical accusations in one round | 16 same-round echoes over 8 old games, mostly day 1 | SUPERSEDED | — | MERGE→S14 | quality_gate/experiment_log.md Dim. 1 |
| 3 | A weighted speaker score was replaced by two hard paths, because a score gives no guarantee, has no stable weights, gives no one-line reason and cannot be tested cleanly | — | LIVE (reactive path) | deterministic-first design | KEEP (lesson 16 instance) | experiment_log.md §2, §6, §7 |
| 4 | A cheap model tags whom each line addresses reliably and beats a keyword rule | 30 of 30 valid; 27 of 27 targets grounded, 0 invented; 63% agreement, all 11 disagreements in the model's favour | LIVE (`addressed_targets`) | structured output, model vs rule | KEEP (lesson 16 instance) | experiment_log.md §5 Smoke 1; smoke_act_fields.py |
| 5 | One speech-act label forced a coin-flip (a line is both a question and an accusation), so two axes: form × stance. A feared flood of accusation labels was a sampling artifact | 100% valid on both axes; 48 messages stratified by round, about 55% questions or accusations | LIVE (`AddressedTarget`) | schema design | MERGE→S4 | experiment_log.md §5 Smoke 1b |
| 6 | A separate judge rating a fixed line is reliable, and temperature does not move it | 20 of 20 both ways; 0 of 20 label flips at temp 1.0 | LIVE (form of the echo gate) | LLM-as-judge | MERGE→S7 | experiment_log.md §5 Smokes 2–3 |
| 7 | A seat judging its own point's novelty fails both ways: asked about the situation it calls nearly everything a repeat, asked about its contribution it calls nearly everything new. Adding the fields also shifted its summary | 12 cases each; shift 1 of 12 and 0 of 12; summary similarity 0.976 against a 0.997 noise floor | SUPERSEDED (dropped) | generator-verifier separation | KEEP (lesson 15's clearest instance) | experiment_log.md §5 Smoke 4; report.md §4; smoke_situation_novelty.py |
| 8 | The scheduler is stateless: every turn it recomputes from the transcript, so it cannot drift, is safe to resume, and a test can hand-write a transcript and assert the pick | 22 unit tests at the time | LIVE (`Agents/turn/scheduler.py`) | deterministic orchestration, testability | KEEP | report.md §2–3; experiment_log.md §7 |
| 9 | Feuds are bounded by two separate levers. A reworded re-accusation opens no new debt, because the key ignores wording. A per-pair cap of 2 resets after a cooldown, so it caps back-and-forth in a row rather than banning a topic for the day | cap 2; cooldown ⌈1.0 × survivors⌉ | LIVE (`Agents/config/game.py`) | — | MERGE→S8 | experiment_log.md §4, §7 |
| 10 | Speaker choice stays role-blind, because a guaranteed slot for the investigator would reveal the role | — | LIVE (seat-order sweep since 2026-10-07; quiet-first SUPERSEDED) | information leak by scheduling (boundary cross-reference) | MERGE→S1 | experiment_log.md §4, §7 |
| 11 | First live runs: domination (one seat picked 7 times, two turns word-for-word identical) was fixed by a turn brief and by letting a mention discharge a debt. Echo on quiet turns was the bigger, systematic problem, and the word-level metrics scored it clean | days 1–2 about 95% quiet turns, about 20 turns of agreement | LIVE (`firing_brief`) | metric blind spots | KEEP | experiment_log.md §8 |
| 12 | Novelty came back only as a separate judge, on quiet turns only, owning only silence | echo-heavy day's second round 24 → 9 turns; 3 of 4 days ended by passes; today: held 12 of 29 restatements, 0 of 36 worthwhile lines (minimal thinking held 9 of 29) | LIVE (`Agents/turn/echo_gate.py`) | output guardrail, generator-verifier separation | KEEP (the echo-gate block lesson 15 waits for) | report.md §4; experiment_log.md §8 |
| 13 | A "target=all" crashed the scheduler; the recursion limit was made pass-aware | — | LIVE (fixes) | — | SKIP | experiment_log.md §8 |
| 14 | Acceptance: the win is structural (blind-round repeats are gone by construction; the asked seat answers next) and seen in all games. The numbers are descriptive only, and the old design is frozen at tag `concurrent-baseline` so the decision can be reversed | repeats 0.00 vs 0.05–0.06; top speaker's share 0.25–0.26 vs 0.21–0.22; 4 new vs 8 old games, unpaired, judge = implementer, old backend and temperature not recorded | LIVE | acceptance testing, reversible decision via a baseline tag | KEEP | quality_gate/experiment_log.md; rubric.md; metrics.py |
| 15 | An unswept setting shipped wrong: the cooldown sat at 3 against an intended 1.0 for about 20 days, quietly turning the cap into a per-day rule | ~20 days; fixed 2026-06-24 | LIVE (1.0) | configuration validation | KEEP (small, Gaps) | report.md §5; experiment_log.md §11 |
| 16 | Two harness bugs found during the gate: the batch runner dropped transcripts, and the query embedding had no retry | — | LIVE (fixed) | — | SKIP | experiment_log.md §9 |
| 17 | An embedding filter for novelty was deferred: on-topic messages are all similar, so a margin would be thin | — | PLAN | embedding limits | MERGE→embeddings topic (block 26) | experiment_log.md §6; report.md §5 |
| 18 | Human turns break the transcript assumption (they carry no tags) | — | LIVE (closed: `Agents/turn/addressing_agent.py`) | — | MERGE→HITL / S8 gap | report.md §5; experiment_log.md §2 |
| 19 | Personas may vary voice, never disposition, and are assigned independently of role | — | OFF (voices off) | — | MERGE→persona voices memory | report.md §5; experiment_log.md §2 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/sequential_discussion/report.md` | Destination-first design report, status 2026-10-07 | F1, F3, F7, F8, F12, F14, F15, F17–F19 |
| `evidence/sequential_discussion/experiment_log.md` | Build journey from design to gate | F1, F3–F13, F15–F19 |
| `evidence/sequential_discussion/quality_gate/experiment_log.md` | Acceptance test, concurrent vs sequential | F2, F14 |
| `evidence/sequential_discussion/quality_gate/rubric.md` | Human scoring guide for the gate | F14 |
| `evidence/sequential_discussion/quality_gate/scripts/metrics.py` | Word-level repeat and fairness counts | F14 |
| `evidence/sequential_discussion/quality_gate/data/gate_sequential.jsonl` | Four sequential gate games | data for F14 |
| `evidence/sequential_discussion/quality_gate/data/gate_sequential_memon_retry.jsonl` | Retried memory-on gate game | data for F14 |
| `evidence/sequential_discussion/quality_gate/data/seq_run.log` | Gate run log | data for F14 |
| `evidence/sequential_discussion/quality_gate/data/seq_retry.log` | Gate retry log | data for F14 |
| `evidence/sequential_discussion/scripts/smoke_act_fields.py` | Smoke 1: speech-act tagging | F4 |
| `evidence/sequential_discussion/scripts/smoke_act_2d.py` | Smoke 1b: form × stance tagging | F5 |
| `evidence/sequential_discussion/scripts/smoke_act_2d_distribution.py` | Stance distribution, stratified by round | F5 |
| `evidence/sequential_discussion/scripts/smoke_novelty.py` | Smoke 2: standalone novelty judge | F6 |
| `evidence/sequential_discussion/scripts/smoke_novelty_temp.py` | Smoke 3: temperature effect on judge | F6 |
| `evidence/sequential_discussion/scripts/smoke_situation_novelty.py` | Smoke 4: self-judged novelty | F7 |
| `evidence/sequential_discussion/scripts/smoke_discussion.py` | Live tuning harness, domination diagnostics | F11 |
| `evidence/sequential_discussion/data/smoke_act_results.jsonl` | Smoke 1 per-case results | data for F4 |
| `evidence/sequential_discussion/data/smoke_act_2d_results.jsonl` | Smoke 1b per-case results | data for F5 |
| `evidence/sequential_discussion/data/smoke_act_2d_distribution_results.jsonl` | 48 stratified labelled messages | data for F5 |
| `evidence/sequential_discussion/data/smoke_novelty_results.jsonl` | Smoke 2 per-case results | data for F6 |
| `evidence/sequential_discussion/data/smoke_novelty_temp_results.jsonl` | Smoke 3 per-case results | data for F6 |
| `evidence/sequential_discussion/data/smoke_situation_novelty_results.jsonl` | Smoke 4 per-case results | data for F7 |

### `store_curation`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | An uncurated loop bloats the lesson store, which set the per-cell cap on untested lessons | 0 → 227 lessons in one run; cells about 34 vs about 5; cap 12 | LIVE (`synth_cell_unproven_cap` 12) | memory lifecycle management | KEEP | `report.md` §1, §5; `strategy_points.md` §2; `knobs.md` §3 |
| 2 | Synthesis re-wrote already-distilled clusters, and a net-change trigger stalled silently, so only new-evidence clusters synthesize and arrivals are counted | about 6× per run (5.4 → 34 per cell); stall at generation 6 | LIVE (`synth_min_new_obs` 4); new-clusters-only not checked in today's tick | — | MERGE→F11 | `strategy_points.md` §2; `report.md` §5 |
| 3 | The prune line cuts a repeatable signal | 8 of 9 flagged stayed negative on held-out half; r = +0.54; 31 lessons | LIVE (`prune_tau` −0.15, 8 follows) | — | MERGE→block 59 | `strategy_points.md` §6; `experiment_log.md` §7 |
| 4 | Evict only lessons rejected on the merits; "does not apply" blames the search, not the lesson | rule | LIVE (`evict_require_override`) | blame attribution | KEEP | `strategy_points.md` §4; `report.md` §5 row 6 |
| 5 | Nothing is removed for age alone; earned lessons are exempt from every drop rule | positive lift with at least 2 follows | LIVE (`protect_min_follow` 2) | memory lifecycle management | KEEP | `report.md` §2.3; `strategy_points.md` §4 |
| 6 | Count-scaled observation decay replaced a rule that made any repeated observation immortal | 4 × count generations; a window of 2 dropped about 250 a generation | LIVE (`obs_evict_min_age` 4; `Agents/memory/consolidation/db.py` decay clocks) | memory lifecycle management | KEEP | `observations.md` §3; `experiment_log.md` §4; `knobs.md` §4 |
| 7 | Item identity is protected: lesson text never merged, dedup keeps the older credited item, tell text never rewritten | rule | LIVE (lessons, observations); OFF (tells) | — | KEEP | `report.md` §2.3; `strategy_points.md` §3 |
| 8 | Every recurring paid cost is tied to new arrivals or a hard cap; clustering seeds from new arrivals only | 30 old + 2 new: 32 searches → 2 | LIVE (values); seed-from-new not checked in today's tick | cost bounded by inflow | KEEP | `report.md` §2.4; `strategy_points.md` §2; `experiment_log.md` §4 |
| 9 | Proven lessons rank first and the best unproven one gets a guaranteed slot, because credit only reaches shown lessons | at most 3 shown per situation | LIVE (`retrieval/plan_gating.py`, default on) | explore/exploit | KEEP | `strategy_points.md` §5; `experiment_log.md` §5 |
| 10 | The lesson writer is shown each old lesson's measured lift so it corrects losers instead of regenerating them | lessons with at least 5 follows; quality never judged | LIVE (`Agents/memory/strategy_synthesis.py:110–126`) | generation conditioned on measured outcome | KEEP | `strategy_points.md` §2; `report.md` §5 row 11 |
| 11 | Eleven store failures each got a named guard, with a column separating what runs showed from what reviews caught | 11 rows | RECORD | claim calibration | KEEP | `report.md` §5; `experiment_log.md` §6 |
| 12 | Per-game tell dedup was retired for a batch fold: costlier and less accurate; recurring core converges, a singleton tail keeps arriving | 178 calls a game; one tell split 18 + 11 + 10; store 740 → 596; about 140 core, about 16 new a game | OFF | batch vs online curation | MERGE→`extraction/tell_extraction/` | `tells.md` §2; `report.md` §5 |
| 13 | The tell fold refuses to publish if any recount shrinks or a top tell vanishes without a verdict | rule | OFF | data-integrity invariants | MERGE→`extraction/tell_extraction/` | `tells.md` §4; `experiment_log.md` §7 |
| 14 | The tell book became a manual for every role and collapses same-behaviour fragments; what pays credit differs from what informs | 34 seed entries, 6 roles; v1 book changed 27.5% of decisions | OFF | — | MERGE→`extraction/tell_extraction/` | `tells.md` §6; `report.md` §6.6, §6.9 |
| 15 | Settings were pinned with provenance, not tuned: a sweep is harder to detect than the main effect, tuned values do not transfer across epochs, and most settings are guards | 5 provenance classes; only the prune line checked | LIVE (same values carried to ten seats, unvalidated there) | settings governance | KEEP | `knobs.md` §1, §6 |
| 16 | Absolute similarity settings predate the finding that the embedding scale is compressed; a free percentile check was never run | 0.70 / 0.92; tell store median similarity about 0.84 | LIVE (values); check not found | — | MERGE→block 27 | `knobs.md` §5 |
| 17 | Removal barely fires within a run, so stores grow almost without pause; synthesis quality never judged | follow floors of 8; ten-seat pass pruned 4 and evicted 4 of 498 | LIVE (gap) | — | KEEP | `strategy_points.md` §6–7; `observations.md` §6; `evidence/memory_system/v8/experiment_log.md` (the 498) |
| 18 | The design retired observation injection, but the run path still injected them; a default and a fail-loud check now enforce it | run default was `both` | LIVE (served `observations: False`, `server/game/run_config.py:40`) | invariant checks | KEEP | `experiment_log.md` §8; `report.md` §6.8; `observations.md` §6 |
| 19 | The ownership review used a teach-back walkthrough instead of blind re-derivation | — | RECORD | — | SKIP | `experiment_log.md` §1 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/store_curation/report.md` | framework for three stores, pathology ledger, agenda | F1–F18 |
| `evidence/store_curation/strategy_points.md` | lesson store: synthesis, prune, evict, lanes | F1–F5, F8–F10, F17 |
| `evidence/store_curation/observations.md` | observation store: decay, admission, gaps | F6, F7, F17, F18 |
| `evidence/store_curation/tells.md` | tell ledger, fold, tripwire, book | F7, F12–F14 |
| `evidence/store_curation/knobs.md` | every setting with provenance and pinning policy | F1, F3, F6, F15, F16 |
| `evidence/store_curation/experiment_log.md` | review rulings log, July 14–15 | F2, F3, F6, F8, F9, F11, F13, F18, F19 |

### `tracing`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Save each gradable decision as a self-contained case when it is made, in one shape to the trace and a local file | 4 case types, 5 sites | LIVE | LLM tracing, eval-dataset capture | KEEP | `report.md` §1–2.4 |
| 2 | Some case fields exist only at decision time (pre-rerank pool, assembled private context, search queries), so the case cannot be rebuilt later | — | LIVE | — | MERGE→1 | `report.md` §2.3 |
| 3 | The tracer cannot be the dataset: reading cases back failed on long games; local-first fixed it | 3 of 5 games built, 2 refused; the cheap call returned 8.3 KB with no case vs 38 KB; then 20 of 20 built, identical ids in both copies | LIVE | observability-backend limits | KEEP | `report.md` §4, `implementation_notes/ISSUE_frozen_set_fetch.md`, `implementation_notes/frozen_set_fetch_explained.md` |
| 4 | Span names defined once, so the writer and reader cannot drift; one shared name prefix had to be resolved by structure | — | LIVE (`span_names.py`) | — | MERGE→3 | `implementation_notes/ISSUE_frozen_set_fetch.md`, `report.md` §2.5 |
| 5 | Night actions became cases with memory retrieval; the healer retrieved and used lessons on nights 2–4 | 3 smoke games; 3 observations + 3 lessons a night | LIVE | — | MERGE→1 | `implementation_notes/experiment_log.md`, smoke logs |
| 6 | Capture checked against each consumer's needs: 5 gaps found, 4 closed; live check of the closed ones | 72 of 72 store stamps; 46 of 72 pre-rerank pools | LIVE | data-requirements audit | KEEP | `implementation_notes/experiment_log.md` (second half), `report.md` §3 |
| 7 | Langfuse chosen over LangSmith (paid self-hosting) and Phoenix (automatic capture first), on fit, not a benchmark | — | LIVE | tool selection | MERGE→1 | `report.md` "Infrastructure decisions" |
| 8 | The code-version stamp must be set before the first Langfuse client starts, or every trace goes out unlabelled | — | LIVE (`Agents/tracing.py`) | — | MERGE→13 | `report.md` §2.1 |
| 9 | Per-game metrics and the case sink ride LangGraph's runtime context, not graph state, so games cannot cross | — | LIVE (`game_session.py:277`) | — | MERGE→parked LangGraph cross-reference | `report.md` §2.2 |
| 10 | Wolf-night discussion saves no case | open since 2026-06-06 | LIVE gap (no site in `pack.py`) | — | KEEP (gaps line) | `report.md` §5 |
| 11 | The SDK's read timeout was too short for a heavy trace | ~7 s on 1,439 spans; raised to 120 s | LIVE | — | SKIP | `implementation_notes/ISSUE_frozen_set_fetch.md` |
| 12 | Day-summary span names lacked the game id before 2026-06-11 | — | RECORD (fixed) | — | SKIP | `report.md` §5, `implementation_notes/ISSUE_frozen_set_fetch.md` |
| 13 | Three labels for a result: what was asked, what ran, which files fed it; drift shows up, exact reproduction is not claimed | — | LIVE | experiment provenance | KEEP | `fingerprinting/report.md` §1–6 |
| 14 | Prompts stay in git, not in Langfuse's prompt manager, to avoid two copies | — | LIVE | — | MERGE→13 | `fingerprinting/experiment_log.md` §2 |
| 15 | The fingerprint does real work: the v7 loop stops if any game's stamp differs | — | LIVE (`driver.py:343`) | — | MERGE→13 | `fingerprinting/report.md` §7 |
| 16 | Prompt-hash coverage drifted silently when prompts moved into sub-folders; no test failed | split on 2026-06-16; by grep today, `roles/` is also outside; 0 fingerprint tests | LIVE gap | coverage contracts | KEEP (gaps line) | `fingerprinting/experiment_log.md` §7, `fingerprinting/report.md` §9 |
| 17 | Moving or renaming covered files changed the hash with no prompt change; there is no schema version to tell the two apart | 2 changes on 2026-06-10 | LIVE gap | — | MERGE→16 | `fingerprinting/experiment_log.md` §5 |
| 18 | The backend field knows only Google or Vertex while the models moved on | NIM and Mistral then; Claude Haiku is the default today | LIVE gap | — | MERGE→16 | `fingerprinting/report.md` §3.3, §9 |
| 19 | An uncommitted run is detected but cannot be rebuilt; refusing uncommitted runs for citable batches is advised | — | LIVE gap | — | MERGE→13 | `fingerprinting/report.md` §6, §9 |
| 20 | Motivation: the same memory-on condition swung between batches after an unstamped store change (that lineage is demoted to non-citable, so cite the mechanism, not the figures) | 96.7% → 73.3% | RECORD | — | MERGE→13 (motivation only) | `report.md` §2.7 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/tracing/report.md` | Capture design, the 422 case study, gaps | F1, F2, F3, F6, F7, F8, F9, F10, F12, F20 |
| `evidence/tracing/implementation_notes/experiment_log.md` | Night-action cases and the capture audit | F5, F6 |
| `evidence/tracing/implementation_notes/ISSUE_frozen_set_fetch.md` | The 422 issue: cause, fix commits, acceptance | F3, F4, F11, F12 |
| `evidence/tracing/implementation_notes/frozen_set_fetch_explained.md` | Plain retelling of the 422 fix; reusable pattern | F3 |
| `evidence/tracing/implementation_notes/smoke_attrib.log` | One memory-off smoke game; purpose not written up | data for F5 |
| `evidence/tracing/implementation_notes/smoke_extgate.log` | One memory-off night smoke game; purpose not written up | data for F5 |
| `evidence/tracing/implementation_notes/smoke_memoff.log` | Memory-off night-case smoke game | data for F5 |
| `evidence/tracing/implementation_notes/smoke_memon.log` | Memory-on smoke, healer and investigator only | data for F5 |
| `evidence/tracing/implementation_notes/smoke_memon_all.log` | Memory-on smoke, all roles (the decisive run) | data for F5 |
| `evidence/tracing/fingerprinting/report.md` | How provenance works today, with its gaps | F13, F15, F16, F18, F19 |
| `evidence/tracing/fingerprinting/experiment_log.md` | Provenance build journey to the July audit | F14, F16, F17 |

### `v7_final`

#### Findings
| # | Finding (plain claim, one line) | Number and N | Today's design? | Candidate skill tag | Call | Source |
|---|---|---|---|---|---|---|
| 1 | Credit was silently zero from generation 2 in run 1 (path list joined into one search string); caught by the planned generation-3 read; the one-generation smoke could not catch it | 340 follows, 0 ledger keys; re-credited → 38 lessons | LIVE (fixed path expansion + guard) | experiment-integrity guards | KEEP | `experiment_log.md` §11a |
| 2 | An audit of the loop's seams found that broken inputs gave plausible wrong numbers, so guards that raise were built; four more shakedown bugs were fixed (synthesis stall, over-eager decay, prune before dedup, re-embedding); a smoke must run the real regime (2+ generations) | 5 bugs; 16 bad lessons leaked by prune ordering; decay minimum age 2 → 4 | LIVE (`evaluation/src/loop/invariants.py`, `obs_evict_min_age=4`) | experiment-integrity guards | KEEP | `experiment_log.md` §11b, §11h |
| 3 | Runs 1–2 had an invalid baseline: run 1 took it from the ~11% memory-off decisions inside memory-on games, and run 2 used unpaired boards; fixed with a dedicated memory-off arm on the same boards | ~$100 spent, no usable result | LIVE (deal seeded from `game_id`, `Agents/nodes/orchestrator.py:89`) | paired A/B | KEEP (in case study) | `experiment_log.md` §11g, §11j; `report.md` §3 |
| 4 | v2 gave memory to every faction, not town only; the "no-memory wolves" control did not exist; town was confounded because better wolves lower the town's vote grade; guard: crash at generation 1 unless the factions with memory match a declared list | v2 $15; estimate of a guard crash ≈$0.50 | LIVE (`assert_arm_factions`, `assert_arm_declared`) | experiment-integrity guards | KEEP | `experiment_log.md` §12f; `report.md` §5c; `runs/v2_full/run.log` |
| 5 | The +0.41 town / +0.556 discussion "lift" was a level against a base of zero, and a tag cache keyed by game served the memory-on tags to memory-off games; the same base-at-zero class returns in block 61 | town discussion properly differenced ≈ −0.12 | LIVE (`assert_baseline_coherence`, 2026-07-15) | experiment-integrity guards | KEEP (case study + lesson link to 61) | `experiment_log.md` §12f; `v2_salvage.py` |
| 6 | Positive lift did not mean better play: lessons' follow-weighted lift was positive while memory-on town scored below memory-off | +0.161 lift at generation 10; invalid baseline | RECORD | Goodhart | MERGE→61 | `experiment_log.md` §11g |
| 7 | The owner read a noisy streak (generations 5–8) as divergence; generation 10 broke it | run 1 on−off mean −0.101, spread 0.156, 5 games per arm; memory-off arm alone drifted 0.119 → 0.389 | RECORD | power analysis | MERGE→63/64 | `experiment_log.md` §11f–§11g |
| 8 | Pairing boards cancels luck only while games stay alike; one changed vote breaks the pair, so at generation level pairing ≈ unpaired; the log contradicts itself (2–4× cut against "pairing maxed") | per-game town grade swings ±0.9 on matched boards | RECORD (the July endpoint pairs per board) | paired A/B | MERGE→65 | `experiment_log.md` §11g, §12b; `report.md` §7 |
| 9 | Lessons piled up faster than they were followed; the gate built to stop it never fired at 1-generation synthesis × 4 games over 17 cells; the evictor could not fire because adoption counters were never merged back | v2 0 → 227 lessons, 15–17 of 17 cells resynthesised per generation; run 1 318 in its history (the log also says 537), median follows 1 | LIVE (proven-first tiering default on; `synth_cell_unproven_cap=12`; `synth_every_k_gens=2`; counters set in `consolidation/credit.py:349`) | memory consolidation | KEEP | `experiment_log.md` §12d, §12f; `report.md` §8; `runs/*/loop_history.json` |
| 10 | Run 1 cost double its estimate: the estimate left out dedup overhead, and a whole-file embedding cache re-embedded the growing store each generation; per-record reuse fixed it with identical vectors | $65.21 against ~$30 (games $43.00 for 163 games, observation dedup $10.57, lesson dedup $9.23); dedup 462 → 1,105 s over generations 1–4 | LIVE (`Agents/memory/persistence/seed.py` reuse index) | cost attribution | MERGE→10 | `experiment_log.md` §11c, §11h |
| 11 | v2's cost was captured per generation from Langfuse; every paid model pinned to the cheap tier on the driver's own process | $15.00 (games $13.43 + $1.57); 3 smokes ~$7.6 | LIVE (`TickConfig.env()`) | cost attribution | MERGE→cost topic (10/11) | `runs/v2_full/cost_report.json`; `experiment_log.md` §12 |
| 12 | Wolf memory showed a rising on−off trend in the confounded run | mean +0.077, slope +0.086 (~1.7 standard errors), 4 games per generation | RECORD | — | SKIP (do not cite) | `report.md` §5c; `v2_salvage.py` |
| 13 | Report headline claims: static memory "+17pp p=0.013", "agents demonstrably learn", "compounding OPEN" | fusion error; mechanism only; superseded by July's closed negative | SUPERSEDED | — | SKIP (do not cite) | `report.md` |
| 14 | Every v7 loop game ran at zero reasoning tokens | 222 loop records | RECORD | — | MERGE→67 | `report.md` scope addendum |
| 15 | The production plan: memory update as an out-of-band batch job after sampled games, half price, each game processed exactly once | — | LIVE in another form (offline batch + tick, block 11) | batch inference | MERGE→11 | `production_design.md` |
| 16 | Agents follow nearly every lesson shown, so override cannot score a lesson; credit = graded outcome of followed decisions | 334 follows against 3 overrides (town votes); overrides 0–5% across arms | LIVE (principle) | credit assignment | MERGE→56 | `plan.md` §5 G3a; `experiment_log.md` §1 |
| 17 | Before building credit, each decision type's grade was checked against its side winning, with a shuffled-label null; finding ≠ winning for the investigator | 180 games: town vote r=+0.56, healer block +0.42, Serial Killer kill +0.26, wolf blend +0.22; investigator night find 0.00; wolf night target −0.11 | LIVE (standing `instrument_validation/credit/g2_separability.py`; wolf blend and healer save grades in `grading.py`) | permutation test (signal above a null) | KEEP | `plan.md` §5 G2; `experiment_log.md` §1 |
| 18 | Accusations steer the vote toward threats | accused lynched 58% against 12%; accused-and-lynched were threats 72% against 61%; per-game r=+0.45 | SUPERSEDED (discussion credit redesigned) | — | SKIP | `gates/g3b_target_advocacy.py`; `plan.md` §5 |
| 19 | The similarity score cannot tell a useful retrieved lesson from a useless one; "not relevant" is self-reported and mixes correct declines with misses (an upper bound) | 7,534 retrievals, 58% not relevant; score 0.827 against 0.828 (r=−0.04); top-1 still 48% | LIVE context (served game retrieves by similarity) | embedding limits | KEEP (embeddings topic) | `gates/g3c_retrieval_applicability.py`; `plan.md` §5, §10b |
| 20 | Matching board fields cuts waste a little; the full gate replay came out flat, so gating ships off | stage −5 points, swing −6 points, still 56%; replay 38% → 36%, 24 votes | OFF | — | MERGE→89 | `gates/g3c_gating_efficacy.py`; `plan.md` §5 |
| 21 | High-stakes turns are do-or-die (a miss there loses), even though the gain from a hit is flat; use as a soft pointer for extraction, never a whitelist | P(win if missed) 0.23 → 0.00; gain +0.35 / +0.37 flat; town votes only | RECORD (standing code in `instrument_validation/proxies/`) | — | MERGE→14 / `extraction/selection/` | `plan.md` §5, §3D |
| 22 | The extractor's verdict tracks who won | r=+0.45 over 932 observations; positive 64% if won against 21% if lost; ~22% disagree | SUPERSEDED by block 82's count | outcome bias | MERGE→82 | `plan.md` §10f; `experiment_log.md` §5 |
| 23 | Raw credit looks good, but against memory-off play it washes out; the most-followed lesson loses | +0.43 → +0.03; ~20 help, ~18 hurt; 79-follow lesson lift −0.30 | LIVE (baseline comparison) | baseline comparison | MERGE→59 | `experiment_log.md` §2; `consolidation_design.md` §7; `credit_backfill_ledger.json` |
| 24 | Losers stay losers on held-out games; the one flip had 3 follows | 8 of 9 (89%) against 61% base; r=+0.54, 31 lessons; sample-stable, not epoch-stable | LIVE | held-out reproduction | MERGE→59 | `consolidation_design.md` §6b |
| 25 | Prune rule: drop only after 8 follows and lift ≤ −0.15; read off the noise (median 3 follows); a practical stand-in for a confidence interval; drop at 0 would hit harmless near-baseline lessons | 8 of 790 lessons (~1%), 298 follows prevented | LIVE (`Agents/memory/consolidation/config.py`) | decision rule under small samples | KEEP | `consolidation_design.md` §6a; `experiment_log.md` §3 |
| 26 | A longer credit window turns into win/loss, so credit stays per decision | survival vs immediate grade +0.14; correlation with the win label +0.14 → +0.37 → 1.0 | LIVE (per-decision grading) | credit assignment | MERGE→56 | `plan.md` §10f; `experiment_log.md` §6 |
| 27 | "Offense must be non-zero" dropped: the passive Serial Killer came from crediting a stand-in (heat drawn), so guard the measure, not the play | — | RECORD | Goodhart | MERGE→61 | `plan.md` §10a; `experiment_log.md` §5 |
| 28 | Lessons are never merged: two directives cannot be averaged, so keep / discard the worse / drop / revise | — | LIVE (dedup is merge-free, `TickConfig.dedup_model`) | memory consolidation | MERGE→33 | `consolidation_design.md` §4 |
| 29 | Credit stays one number per lesson (too few follows to slice by axis); verdicts hold within one model epoch only | median 3 follows | LIVE | — | MERGE→59 | `plan.md` §10a; `consolidation_design.md` §5 |
| 30 | "Not relevant" blames retrieval, not the lesson: eviction spares lessons that were mostly judged not relevant | — | LIVE (`evict_require_override`) | — | MERGE→19 | `plan.md` §10b; `experiment_log.md` §9 |
| 31 | A two-window "souring" drop rule was specified | — | PLAN (never built) | — | SKIP | `consolidation_design.md` §11 |
| 32 | Synthesis weighted by the extractor's verdict fixed the town's worst lesson but copied the Serial Killer's almost verbatim (halo and grade disagree there) | town "abstain" −0.20 / 69 follows flipped; Serial Killer "blend, abstain" −0.30 / 79 follows kept; lexical check underpowered | RECORD (motivates 33) | outcome bias | KEEP (with 33) | `experiment_log.md` §4; `synthesis_checks/sp_synthesis_quality_check.py` |
| 33 | Feeding synthesis each lesson's realized track record produced a conditioned rule that beat the best single lesson; no effect on night actions | 3 of 3 clusters, 2 cells, one role, a read | LIVE (`store_ops.py::_track_record`, `synth_track_min_follow=5`) | feedback-grounded generation | KEEP | `runs/synth_deluck_ab/*.md`; `experiment_log.md` §4; `plan.md` §3C |
| 34 | One lesson per game stage: a rule spanning stages would be retrieved in only one, so synthesis is told to split it | re-check gave 3 stage-scoped lessons | LIVE (`strategy_synthesis.py:133–138`) | — | MERGE→33 | `synthesis_checks/inspect_synth_dims.py`; `experiment_log.md` §4 |
| 35 | Flash-Lite matched Pro at synthesis, ~3× faster; synthesis must be incremental and concurrent | ~15 s against ~45 s a call; 2 cells | SUPERSEDED model (Sonnet 5.5); incremental LIVE | — | SKIP | `runs/synth_deluck_ab_flite/*.md`; `experiment_log.md` §4 |
| 36 | The extraction quota did not pad; since a missed lesson cannot be recovered and an extra one can be pruned, lean toward catching more | 2.78 observations per game and cell, 98% below the floor of 6, 0 near-repeats | RECORD (principle) | — | MERGE→78 | `extraction_screens/extraction_quota_screen.py`; `extraction_coverage_ab_spec.md` |
| 37 | Flash-Lite extraction viable; three models comparable in volume | 2.82 / 3.24 / 3.10 per cell, 3 games | SUPERSEDED (block 76) | — | SKIP | `extraction_screens/extraction_model_ab_compare.py` |
| 38 | Pointing the model at pivotal turns did not help, and the capture metric was wrong (it needed a parseable player count); a read found equal coverage | 3 of 12 flagged turns either way; "exhaustive" pass 116 < 123 observations | RECORD | instrument validation | MERGE→79 | `extraction_screens/recall_capture_metric.py`; `extraction_coverage_ab_spec.md` |
| 39 | Manual read: extraction recorded that passivity hurt the Serial Killer; synthesis turned it into "blend in" | 3 models, same games | RECORD | — | MERGE→32 | `experiment_log.md` §7 |
| 40 | Discussion design: 7 moves on 3 axes; tag fine, credit coarse | — | SUPERSEDED (block 57) | — | SKIP | `discussion_credit_design.md` |
| 41 | Free discussion floor reproduced on held-out games; most night kills of power roles had no day heat | 100 lessons credited, r=+0.51 (51); wolves 71%, Serial Killer 62% | SUPERSEDED | — | SKIP | `discussion_credit/discussion_coverage_check.py`, `discussion_credit_deterministic.py` |
| 42 | The tagger's one unique value was night read quality, separating good reads that missed from blind picks that hit | ~31% of night actions moved; 30 and 12; 8 games | SUPERSEDED (forerunner of block 57) | — | MERGE→57 | `experiment_log.md` §8b |
| 43 | Tagger framing tags matched faction | manipulative: town 7%, wolf 85%, Serial Killer 88%; 8 games | SUPERSEDED | — | SKIP | `discussion_credit/tagger_accuracy.py` |
| 44 | The tagger "leaks the outcome" claim shrank three times; blinded and controlled for verbosity, it still predicted deceiver wins beyond the vote grade | wolf +0.60 → +0.56, Serial Killer +0.55 → +0.60, town +0.02; N=24 | SUPERSEDED (retired from credit 2026-07-13) | — | MERGE→57 | `runs/v2_full/tagger_deleak_ablation.py`, `tagger_skill_retest.py`; `experiment_log.md` §12g |
| 45 | The owner commissioned a read-only evaluator agent with a brief giving facts and open questions, no author verdict | 8 findings, 5 axes | RECORD (method) | commissioned independent review | KEEP | `EVALUATOR_BRIEF.md`; `evaluator_review.md` |
| 46 | The review caught the "+17pp p=0.013" fusion in the owner's report | raw +17 points p=0.267; reranked +33 points p=0.013 | RECORD | independent review | KEEP (in 45) | `evaluator_review.md` F7 |
| 47 | The review found the retracted halo still live in loop credit (tagger at base 0, arm-blind cache) | — | LIVE fix (tagger retired 07-13; coherence guard 07-15) | independent review | KEEP (in 45) | `evaluator_review.md` F1 |
| 48 | Slope test too weak by construction; answer at the endpoint with a frozen store in a paired static test; slope becomes a diagnostic | slope ~1.7 standard errors at 5 generations; became the July 30-board design | LIVE (block 65's design; the execution-plan report does not cite this review) | experimental design | MERGE→65 (+ in 45) | `evaluator_review.md` F2–F3 |
| 49 | Bloat and the inert evictor named as an anti-compounding force; proven/reserve split specified | — | LIVE | — | MERGE→9 | `evaluator_review.md` F4, clarification 3 |
| 50 | Lift compares selected follows with the whole cell; baselines should be split by board state | — | OFF (not built; no stratification in code) | — | MERGE→62 | `evaluator_review.md` F5 |
| 51 | The review named the baseline that falls back to zero when a cell has no memory-off data; block 61's second cause is that fallback | found again 2026-10-22; why the 07-15 guard missed it: not found | RECORD | independent review | MERGE→61 (+ in 45) | `evaluator_review.md` F6 |
| 52 | Healer's best-separated action (blocking a kill) was not credited; a join was recommended | r=+0.42 (G2) | LIVE likely (healer protect graded by save in `grading.py::_grade_healer`; link not confirmed) | — | MERGE→58 | `evaluator_review.md` clarification 4 |

#### Files
| File | What it is (≤10 words) | Role |
|---|---|---|
| `evidence/v7_final/EVALUATOR_BRIEF.md` | Neutral brief for an outside evaluator agent | F45 |
| `evidence/v7_final/README.md` | Folder index, probe inventory, home rule | index |
| `evidence/v7_final/consolidation_design.md` | Credit-to-store design, prune thresholds, souring spec | F23, F24, F25, F28, F29, F31 |
| `evidence/v7_final/credit_backfill_ledger.json` | Per-lesson lift and follows, 127 lessons | data for F23, F24, F32 |
| `evidence/v7_final/discussion_credit/README.md` | Subfolder pointer | index |
| `evidence/v7_final/discussion_credit/discussion_coverage_check.py` | Free day-vote floor and night-exposure counts | F41 |
| `evidence/v7_final/discussion_credit/discussion_credit_deterministic.py` | Free accusation-correctness credit slice | F41 |
| `evidence/v7_final/discussion_credit/tagger_accuracy.py` | Tagger tags against ground truth | F43 |
| `evidence/v7_final/discussion_credit_design.md` | Discussion credit design and amendments | F40 |
| `evidence/v7_final/evaluator_review.md` | Evaluator verdicts, findings F1–F8, plan | F45, F46, F47, F48, F49, F50, F51, F52 |
| `evidence/v7_final/experiment_log.md` | Chronological build and run log | F1–F11, F16, F17, F21–F30, F32–F36, F39, F42, F44 |
| `evidence/v7_final/extraction_coverage_ab_spec.md` | Extraction recall and model A/B spec, pre-gate results | F36, F37, F38 |
| `evidence/v7_final/extraction_screens/README.md` | Subfolder pointer | index |
| `evidence/v7_final/extraction_screens/extraction_model_ab_compare.py` | Pro / 3.5-flash / Flash-Lite extraction compare | F37 |
| `evidence/v7_final/extraction_screens/extraction_quota_screen.py` | Quota-padding and near-repeat screens | F36 |
| `evidence/v7_final/extraction_screens/recall_capture_metric.py` | Pivotal-turn capture metric | F38 |
| `evidence/v7_final/gates/README.md` | Subfolder pointer | index |
| `evidence/v7_final/gates/g3b_target_advocacy.py` | Accusation-steers-vote gate | F18 |
| `evidence/v7_final/gates/g3c_gating_efficacy.py` | Per-field gating waste reduction | F20 |
| `evidence/v7_final/gates/g3c_retrieval_applicability.py` | Similarity score against applicability | F19 |
| `evidence/v7_final/plan.md` | Pre-registered v7 plan, gates, stopping rule | F16, F17, F19, F20, F21, F22, F26, F27, F29, F30 |
| `evidence/v7_final/production_design.md` | Async batch memory-update plan | F15 |
| `evidence/v7_final/report.md` | Pre-July v7 write-up and post-mortem | F3, F4, F9, F12, F13, F14 (headline superseded) |
| `evidence/v7_final/review_map.md` | Map of v7 decisions to code | index |
| `evidence/v7_final/runs/README.md` | Subfolder pointer | index |
| `evidence/v7_final/runs/loop_gate/gen*.jsonl` | One-game-per-arm end-to-end gate records | data for F1 |
| `evidence/v7_final/runs/smoke_2gen/gen*.jsonl` | Two-generation smoke game records | data for F2 |
| `evidence/v7_final/runs/smoke_parallel/gen*.jsonl` | Parallel-games smoke game records | data for F2 |
| `evidence/v7_final/runs/town_only_run1/gen*.jsonl` | Run 1 game records, generations 1–3 | data for F1, F3, F7 |
| `evidence/v7_final/runs/town_only_run2/gen*.jsonl` | Run 2 game records, generations 1–10 | data for F3, F6, F7, F10 |
| `evidence/v7_final/runs/v2_full/gen*.jsonl` | v2 game records, generations 1–7 | data for F4, F5, F12 |
| `evidence/v7_final/runs/v2_smoke/gen*.jsonl` | v2 warm smoke game records | data for F11 |
| `evidence/v7_final/runs/v2_smoke2/gen*.jsonl` | v2 parallel-arms smoke game records | data for F11 |
| `evidence/v7_final/runs/v2_smoke_cold/gen*.jsonl` | v2 cold-start smoke game records | data for F11 |
| `evidence/v7_final/runs/*/gen*.gameids.json` | Game ids per paired board | data for F3 |
| `evidence/v7_final/runs/*/loop_history.json` | Per-generation scores and credit distribution | data for F3, F4, F7, F9 |
| `evidence/v7_final/runs/*/obs_generations.json` | Observation decay clocks | data for F2 |
| `evidence/v7_final/runs/*/run.log` | Driver logs (v2 shows all factions enabled) | data for F4, F10 |
| `evidence/v7_final/runs/*/cost_report.json` | Langfuse cost per generation | data for F11 |
| `evidence/v7_final/runs/*/run_meta.json` | Run start timestamps | data for F11 |
| `evidence/v7_final/runs/*/store/*` | Final run stores (lessons, observations, base rates, embeddings) | data for F9 |
| `evidence/v7_final/runs/*/*/.last_dedup_at` | Dedup timestamps per store | data for F9 |
| `evidence/v7_final/runs/*/gen*_store/*.json` | Per-generation lesson and observation stores | data for F9 |
| `evidence/v7_final/runs/*/gen*_snapshot/*` | Generation-start snapshots used to resume | data for F9, F10 |
| `evidence/v7_final/runs/*/tags/*.json` | Cached tagger output per game | data for F5, F44 |
| `evidence/v7_final/runs/v2_full/tags_ablation/*.json` | Tagger 2×2 ablation inputs and outputs | data for F44 |
| `evidence/v7_final/runs/v2_full/tagger_deleak_ablation.py` | Outcome in/out × speakers ablation | F44 |
| `evidence/v7_final/runs/v2_full/tagger_skill_retest.py` | Blinded, verbosity-controlled tagger partial correlation | F44 |
| `evidence/v7_final/runs/v2_full/v2_salvage.py` | v2 repositioned as all-memory per-faction A/B | F4, F5, F12 |
| `evidence/v7_final/runs/synth_deluck_ab/serial_killer_day_vote.md` | Synthesis A/B output, Serial Killer day vote, Pro | F33 |
| `evidence/v7_final/runs/synth_deluck_ab/serial_killer_night_action.md` | Synthesis A/B output, Serial Killer night, Pro | F33 |
| `evidence/v7_final/runs/synth_deluck_ab_flite/serial_killer_day_vote.md` | Synthesis A/B output, day vote, Flash-Lite | F35 |
| `evidence/v7_final/runs/synth_deluck_ab_flite/serial_killer_night_action.md` | Synthesis A/B output, night, Flash-Lite | F35 |
| `evidence/v7_final/synthesis_checks/README.md` | Subfolder pointer | index |
| `evidence/v7_final/synthesis_checks/inspect_synth_dims.py` | Stage fields assigned to synthesised lessons | F34 |
| `evidence/v7_final/synthesis_checks/sp_synthesis_quality_check.py` | Carried-vs-dropped lesson lift check | F32 |

