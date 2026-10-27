# Game design and orchestration exhibits: source map

Every exhibit on the drafted pages of this chapter: the
page and level it belongs to, its form, the evidence it is built from, and its state. Built exhibit
files (images, JSON exports, table files) go in this folder, named after the row's id. An exhibit is
drafted only from the source listed, never re-derived; a number in the source that has been corrected
since is taken from the correction.

Forms, as in the project exhibit menu ([`../../eval_exhibits.md`](../../eval_exhibits.md)): **content**
(a table, quote or number written into the page), **diagram**, **export** (an interactive piece fed by a
script-generated JSON, stamped with the commit), **link** (a replay on the live site).

States: **drafted** (in the page draft), **planned** (in the page brief, not built), **optional** (the
brief allows it if it clarifies).

Paths are from the repository root.

## Level 1: [Game design and orchestration](../game_design_orchestration.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| L1-loop | The day-and-night loop in game terms: day (discussion, then a vote that may remove a player; day 1 has no vote) → night (private actions, resolved together) → morning report → next day; exit when a side meets its win condition, or at the day-12 backstop. No graph nodes. File: `day_night_loop.svg`. Superseded on the chapter page by L1-glance (2026-10-27); file kept | diagram | `evidence/gameplay/roles/report.md`, "The cast today", "How each side wins", "The deal and the vote"; `evidence/gameplay/discussion/report.md`, "A day today" (day 1: openings only); `evidence/gameplay/orchestration/report.md`, "The parent graph" (both end checks, day 12); `evidence/gameplay/roles/role_sheet.md`, "Death reveal" | drafted |
| L1-boundaries | Full game state → per-player input construction → two illustrative model calls, showing shared public records and permitted private fields. Mermaid diagram, superseded on the chapter page by L1-isolation (2026-10-27) | diagram | `evidence/agent_boundaries/report.md`, §§1–2 (input construction enforces the boundary); conceptual summary, not the complete prompt pipeline | drafted |
| L1-glance | The four sides with their roles and goals; public and private information; one day and night with the win check. File: `game_at_a_glance.svg` | diagram | `evidence/gameplay/roles/role_sheet.md`, "The lineup", "Win logic"; `evidence/gameplay/discussion/report.md`, "A day today"; `evidence/gameplay/orchestration/report.md`, "The parent graph" | drafted |
| L1-isolation | Full state in three groups → the step that builds each player's input → what the Investigator and a wolf get and never get; the leak checks drawn as an after-the-game check, not a live gate. File: `context_isolation.svg` | diagram | `evidence/agent_boundaries/report.md`, §§1–3 | drafted |
| L1-phases | A day and a night by execution pattern: openings, closing defences and the vote all at once; discussion one at a time; the wolves' chat beside the solo roles; the wait for every choice; resolution; morning. File: `phase_execution.svg` | diagram | `evidence/gameplay/orchestration/report.md`, "The day subgraph", "The nights", "The parent graph" | drafted |
| L1-turn | One turn: input → reply → check → retry with the format enforced → legal fallback → speech published or a choice collected. File: `agent_turn.svg` (replaces the Mermaid chart) | diagram | `writeup/game_design_orchestration/agent_turn/agent_turn.md`, "Retry, then supply a legal fallback"; `evidence/gameplay/turn_prompt/report.md` | drafted |
| L1-human | A vote with one human: the pause, the repeated step without and with the cache (the first two-human test), the checkpoint and the cache with their lifetimes; no framework terms. File: `human_resume.svg` | diagram | `writeup/game_design_orchestration/human_in_the_loop/human_in_the_loop.md`, "What survives a pause or a restart?"; `evidence/gameplay/orchestration/report.md`, decision 12 | drafted |

## Level 2: [Adding a human in the loop](../human_in_the_loop/human_in_the_loop.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| HS-incidents | What the framework did at the pause: two rows (duplicate interrupts; delayed human turn announcements), with the changed-ballot incident developed in prose; LangGraph 1.1.10 | content | `frontend/docs/server_encountered_challenges.md` §1–2; `evidence/gameplay/orchestration/report.md`, "Human seats" (table rows 1–2) and decision 3, "Costs" (`announce_human_turn`, 2026-10-06; the pack's skills, 2026-10-17) | drafted |
| HS-toy-graph | The two lines from the toy graph: with the parallel nodes in the parent, the AI sibling ran once across a human's pause and resume; inside a subgraph invoked from a wrapper, twice (LangGraph 1.1.10, 2026-10-26, no model) | content | `evidence/gameplay/orchestration/report.md`, "Human seats", last paragraph; map block 114 | drafted |
| HS-three-kept | Game checkpoint, AI node cache, provider prompt cache: what each holds, its scope and limit. The table chapter 6 points back to | content | `evidence/gameplay/orchestration/report.md`, "Checkpoints and the two caches serve different purposes"; six-hour lifetime from `Agents/config/langgraph.py` (`TURN_CACHE_TTL_SECONDS`) | drafted |
| HS-host-options | The three ways to run the synchronous engine in the async server, each with why it was kept or rejected | content | `frontend/docs/server_design_notes.md` §5; `evidence/gameplay/orchestration/report.md`, decision 13 | drafted |
| HS-pause-diagram | A pause and resume inside a parallel step: the wrapper node, the subgraph's vote step with AI and human seats, the checkpoint, the resume re-running the wrapper, the AI seats replayed from the cache, the human seat through its uncached node. Caption and footer state that reuse depends on cache entries surviving. File: `pause_and_resume.svg` | diagram | `frontend/docs/server_encountered_challenges.md` §2–5; `evidence/gameplay/orchestration/report.md`, decision 12 and "Human seats" | drafted |
| HS-cache-incident | The attributed cross-game replay and the scripted control's 5 → 0, summarised on page 5. Game identifiers and the side-by-side account belong to the Level 3 page | content | `evidence/gameplay/orchestration/report.md`, decision 12 ("The cross-game cache bug") and "What is not established"; `frontend/docs/deploy_log.md`, 2026-10-26 | drafted (prose); Level 3 table planned |

## Level 2: [Designing evidence worth debating](../evidence_design/evidence_design.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| ED-roles | The role table: 12 roles, side, what each learns at night, uses; caption on the Necromancer's Suspicious night and the Serial Killer never reading Suspicious | content | `evidence/gameplay/roles/report.md`, "The cast today", "What each role does"; `evidence/gameplay/roles/role_sheet.md`, "Town information", "Neutral", "What players see: the exact strings" | drafted |
| ED-purpose | The added roles and what I intended each to add, labelled as design intentions (neutral bargaining not observed or searched for) | content | `evidence/gameplay/roles/report.md`, decision 1 (owner, 2026-10-26) | drafted (optional) |
| ED-wolf-instruction | The wolves' shared discussion instruction, four sentences, quoted | content | `evidence/gameplay/roles/report.md`, decision 10 step 3; code `Agents/prompts/roles/pack.py::DISCUSS_FRAMING` | drafted |
| ED-replay | The card-only replay table: 82 samples per arm (41 turns × 2), spoken lines, claims, denials, deflections, claims that fit, claims a careful town could show false; caption with one judge per line and the old-card notes | content | `evidence/gameplay/roles/report.md`, "Card-only replay"; `evidence/gameplay/data/evil_cover_screen/README.md`, "Results", "Limits" | drafted |
| ED-quotes | Two quoted lines: the Illusionist's healer claim (fits) and the Serial Killer's healer claim that contradicts the sighting it answers | content | `evidence/gameplay/data/evil_cover_screen/README.md`, "Reading" 1 and 3 | drafted |
| ED-paired | The four-row winners table for the eight paired Haiku games, scope caption beside it (bundle; diverge after first different line; direction, not win probability) | content | `evidence/gameplay/roles/report.md`, "The games: a bundle, eight pairs"; `evidence/gameplay/data/evil_cover_games/README.md` | drafted |
| ED-balance | The four-batch table: games, rules in force, town, evil; caption with batch sizes, lineup counts and the stand-in model's turns | content | `evidence/gameplay/roles/report.md`, "Balance: four batches and a hold"; `evidence/gameplay/data/phase3_balance/` to `phase3_balance_4/` READMEs | drafted |
| ED-night-sight | Optional diagram: one night seen by the three observers (see below) | diagram | `evidence/gameplay/roles/report.md`, "The cast today" (visit definition), decision 2; role sheet "What players see" | optional |

## Level 2: [Orchestrating the conversation](../conversation/conversation.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| CV-day-flow | The day's flow in two lines (day 1: opening round → summary → night; day 2 on: opening round → discussion → closing defence → summary → vote), with "about 30 model calls a voting day (four nine-seat test games, Flash-Lite, October 2026)" beneath | content | `evidence/gameplay/discussion/report.md`, "A day today", "Who decides what" footnote; `evidence/gameplay/discussion_evidence.md` §7.4 step 8 | drafted |
| CV-openers | Five of eight day-1 openers from one concurrent game, each "…Does anyone have any initial thoughts…", verbatim | content | `evidence/gameplay/discussion/report.md`, decision 1 | drafted |
| CV-exchange | The player_7 / player_9 exchange (`phase2-step8-game1`, day 2) with each speaker's tags, the prompt line "You were directly addressed by player_7. Respond to them this turn.", and the note that the reply defends but does not answer | content | `evidence/gameplay/discussion/report.md`, "Reactive turns"; `evidence/gameplay/data/phase2_step8_games/` | drafted |
| CV-three-sources | The three sources of silence as three counted lines: held 367 of 517 passes; never offered (28 of 28 day 1s, 8 of 96 voting days); chose to pass 150. 28 nine-seat games on the June design, Gemini 3.5 Flash-Lite, played 2026-09-17 | content | `evidence/gameplay/discussion_evidence.md` §2.4, §7.1; report decisions 12, 16 | drafted |
| CV-chain | The investigator-lynch chain as a numbered list of three links (three of three claimants, 7–1, nine-seat, Flash-Lite, 2026-10-07) | content | `evidence/gameplay/discussion/report.md`, decision 17; `discussion_evidence.md` §7.4 step 8, §7.5 | drafted |
| CV-volume-knob | The volume-knob table: open-floor turns spoken, worthwhile (13/35 → 23/35) and restating (7/29 → 18/29), with "a pass costs nothing here" and with it cut; all turns 20/64 → 41/64. Caption: one blind reader per line, one sample per turn and arm, Haiku 5.5, 2026-10-18 | content | `evidence/gameplay/data/silence_calibration/README.md`, step 3 (`lever_scores.json`) | drafted |
| CV-drift-pair | The drift pair ("your watch showing me at their door" → "your watch has you at their door") beside one voice line ("Brisk and polite, like a porter on a busy shift: short and practical"). Drafted inline in prose; could be set as a two-line block | content | `evidence/gameplay/data/voice_rewrite/README.md`; report "The voices", decision 21 | drafted (inline) |
| CV-held-defence | The held-defence case (October test game 1, day 3: untagged accusations, defence held, never re-asked, no closing, voted out as a villager without speaking), drafted as one limits bullet rather than two lines | content | `evidence/gameplay/discussion/report.md`, "What is not established"; `discussion_evidence.md` §9 item 9 | drafted (as a bullet) |
| CV-scheduler-flow | Optional "who speaks next" flowchart (below) | diagram | report "Reactive turns", "The sweeps", "Ending the day", "The closing defence"; `Agents/turn/scheduler.py::select_next_speaker` | optional |

## Level 2: [Executing a day and night](../day_and_night/day_and_night.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| DN-parent-graph | The main graph, start to end, game-labelled: deal → day (subgraph) → vote count → game over? → night begins → wolves' night (subgraph) ∥ one step per solo role acting tonight → resolve the night → game over? → next day / end and save. Inline Mermaid in the draft; optionally a drawn SVG `parent_graph.svg` | diagram | `Agents/graphs/parent.py::build_parent_graph` (docstring and wiring); `evidence/gameplay/orchestration/report.md`, "The parent graph" | drafted (Mermaid); SVG optional |
| DN-day-subgraph | The day subgraph, game-labelled: opening round (parallel) → collect and number → [day 1: summary] / [voting day: scheduler ⇄ one turn] → closing defences (parallel, if someone has two accusers) → collect → summary → vote (parallel) → collect votes. Human twins omitted, said in the caption. Inline Mermaid; optionally `day_subgraph.svg` | diagram | `Agents/graphs/day.py` (wiring lines 79–134); `evidence/gameplay/orchestration/report.md`, "The day subgraph" | drafted (Mermaid); SVG optional |
| DN-note-wipe | The note-wipe damage as a three-item list (every seat but the first night actor; nearly all blank from day 2; corrupted end-of-game map memory reads), then the fix and its two tests in prose | content | `evidence/gameplay/orchestration/report.md`, decision 9; `tests/engine/test_agent_strategies_merge.py` (module docstring, two tests); `interview_prep/langgraph_langfuse_issues.md` §1.2 | drafted |
| DN-shared-records | The four shared records as a four-line list: today's transcript, then the three trust-labelled records in trust order (game master's record, claim ledger, day summaries) | content | `evidence/gameplay/orchestration/report.md`, "What the agents share"; `evidence/gameplay/turn_prompt/report.md`, "The record of past days" | drafted |
| DN-fold-back-slice | The one-line slice `result["day_channel"][len(sent):]` beside the damage list (the map's block 112 exhibit) | content | `Agents/graphs/parent.py` (module docstring, `day_phase`) | optional (the draft explains it in prose; code names are kept off the page) |
| DN-pack-night | The wolves' night subgraph: chat loop (carrier first, ≤3 rounds, ends on a full round of passes; skipped by a lone wolf) → carrier's kill → each wolf's skill in parallel → collect | diagram | `Agents/graphs/night/pack.py` (wiring lines 34–56); orchestration report "The nights", decision 7 | optional (prose only in the draft) |

## Level 2: [One agent turn, from input to action](../agent_turn/agent_turn.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| AT-turn-flow | One turn's path: permitted input → one structured answer → valid? → (no) ask again with the schema enforced → rescue model if the game has one, then a legal fallback → accepted answer → speech published / vote or night choice collected, then resolved with every other choice. Mermaid inline. A deeper version of the chapter page's turn flowchart (adds the enforced retry and the rescue) | diagram | `evidence/gameplay/orchestration/report.md`, "One turn, end to end" step 5; `evidence/gameplay/turn_prompt/report.md`, "Model settings, validation and retries"; code `Agents/turn/agent_player.py::run_agent` | drafted |
| AT-who-decides | "Who decides what", eight rows, code against model, code names removed; the deduction row labelled "→ chapter 3" | content | `evidence/gameplay/orchestration/report.md`, "Who decides what"; map block 103 | drafted |
| AT-probe | The Haiku admission probe in one sentence: 51 calls (17 ten-seat schemas × 3, thinking medium, 2026-10-11); forced tool call 45 of 51 with 0 reasoning tokens; JSON schema 51 of 51, ~312 reasoning tokens a call | content | `evidence/evaluation/model_admission/experiment_log.md`, 2026-10-11 Claude entry; map block 100 | drafted |
| AT-contract | The output contract as three bold-led rules: required fields with "no" as a value (`pass_turn`, `abstain`, `no_check`, `hold_fire`); legal targets in the schema; fields read downstream (tags, claims) | content | `evidence/gameplay/turn_prompt/report.md`, "What the seat must answer", decisions 11, 13; code `Agents/turn/action_space.py::output_schema_with_legal_targets` | drafted |
| AT-cache-reads | The paired-games contrast in one sentence: Haiku, new layout, two games per arm on the same two deals; votes read 0% of input from cache enforced against 63% unenforced, night actions ~18% against 56% | content | `evidence/caching/experiment_log.md` §13, "Games" table | drafted (optional: a two-row table if the owner prefers it to prose) |
| AT-fallbacks | The fallback per kind of turn, three bullets: discussion → pass recorded as a failed generation; vote and the wolves' kill → random legal target; night ability with a declining word → declined, else random legal target | content | `Agents/turn/agent_player.py::run_agent` (lines after "Exhausted on the primary model"); `evidence/gameplay/turn_prompt/report.md`, "Model settings, validation and retries" | drafted |

## Level 3: [The cache key that crossed games](../human_in_the_loop/cache_key.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| CK-chain | The five links, each with its reason and its consequence ("so …"), ending in the shared answer | content (numbered list) + diagram (planned) | map block 115; `interview_prep/langgraph_langfuse_issues.md` §7.3 "How it traces back to the design"; `evidence/gameplay/orchestration/report.md` decision 12 "Failure mechanism" | drafted (list); diagram planned |
| CK-two-games | The two games side by side: id, model, time, day-1 openings, the Serial Killer at seat 9 | content (table) + diagram (optional) | orchestration report decision 12 "Recorded incident"; `frontend/docs/deploy_log.md` 2026-10-26 | drafted (table); diagram optional |
| CK-three-records | The attribution evidence in prose: capture (8 of 9 AI seats, none for seat 9), the `generation_failed` pass event, the ledger (142 calls, 0 failed) | content | `evidence/tracing/report.md` "The cross-game node cache" and the `pass_marker` JSON; map block 163 | drafted (prose). The side-by-side of the three records is chapter 7's exhibit (block 163); this page only names them |
| CK-collisions | 7 of 66 pairs among 12 freshly dealt games, 8 seats; unit stated | content | orchestration report decision 12; test `tests/engine/test_turn_cache_key.py::test_two_games_never_share_a_day_one_opening_key` | drafted |
| CK-control | The scripted-model control: before the fix 5, after 0; plus the two Haiku games on the fixed code (all ten opening calls each) | content (two-row table + sentence) | orchestration report "What is not established" bullet 5; `evidence/gameplay/report.md` "Execution reliability" | drafted |

## Level 3: [Silence calibration: a volume knob, not a filter](../conversation/silence_calibration.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| SC-1 | A pass that hid a question: one forced line (day 4, empty floor), its reader's kind | content | `evidence/gameplay/data/silence_calibration/items.jsonl` turn `voices-08.off:4:player_5:1`; verdict in `verdicts_*.jsonl` via `blind_key.json` | drafted |
| SC-2 | Open-floor lines by kind: held back (forced) against posted, 40 and 25 lines | content (table) | README step 1 "Results"; re-tallied from `blind_key.json` + `verdicts_1..4.jsonl` | drafted |
| SC-3 | Four prompt changes: worthwhile and restating turns spoken, before → after | content (table) | README steps 2–3; `variant_scores.json`, `lever_scores.json` | drafted |
| SC-4 | Gate bars on the 65 judged lines: restatements and worthwhile lines held | content (table) | README step 4; `gate_check_scores.json`, `gate_check_judge_low_scores.json`, `gate_check_ported.jsonl` | drafted |
| SC-5 | A line the gate catches: player_5's line and player_7's forced line, held as a repeat | content (quoted exchange) | `items.jsonl` turn `voices-07.on:2:player_7:1` (its `context.today`); `gate_check_ported.jsonl` (`held: "player_5"`) | drafted |
| SC-6 | Four whole games on the same deals: open-floor turns published, held, passed | content (table) | README step 5; `games_scores.json` | drafted |
| SC-7 | The study's pipeline (diagram below) | diagram | README steps 1–5 | optional |
