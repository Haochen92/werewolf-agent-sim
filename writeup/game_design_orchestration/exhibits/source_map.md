# Game design and orchestration exhibits: source map

Every exhibit on the drafted pages of this chapter (the Level 1 chapter page and Level 2 page 5): the
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
| L1-loop | The day-and-night loop in game terms: day (discussion, then a vote that may remove a player; day 1 has no vote) → night (private actions, resolved together) → morning report → next day; exit when a side meets its win condition, or at the day-12 backstop. No graph nodes. File: `day_night_loop.svg` | diagram | `evidence/gameplay/roles/report.md`, "The cast today", "How each side wins", "The deal and the vote"; `evidence/gameplay/discussion/report.md`, "A day today" (day 1: openings only); `evidence/gameplay/orchestration/report.md`, "The parent graph" (both end checks, day 12); `evidence/gameplay/roles/role_sheet.md`, "Death reveal" | drafted |
| L1-boundaries | Full game state → per-player input construction → two illustrative model calls, showing shared public records and permitted private fields. Mermaid diagram inline on the chapter page. | diagram | `evidence/agent_boundaries/report.md`, §§1–2 (input construction enforces the boundary); conceptual summary, not the complete prompt pipeline | drafted |

## Level 2: [Adding a human in the loop](../human_in_the_loop/human_in_the_loop.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| HS-incidents | What the framework did at the pause: two rows (duplicate interrupts; delayed human turn announcements), with the changed-ballot incident developed in prose; LangGraph 1.1.10 | content | `frontend/docs/server_encountered_challenges.md` §1–2; `evidence/gameplay/orchestration/report.md`, "Human seats" (table rows 1–2) and decision 3, "Costs" (`announce_human_turn`, 2026-10-06; the pack's skills, 2026-10-17) | drafted |
| HS-toy-graph | The two lines from the toy graph: with the parallel nodes in the parent, the AI sibling ran once across a human's pause and resume; inside a subgraph invoked from a wrapper, twice (LangGraph 1.1.10, 2026-10-26, no model) | content | `evidence/gameplay/orchestration/report.md`, "Human seats", last paragraph; map block 114 | drafted |
| HS-three-kept | Game checkpoint, AI node cache, provider prompt cache: what each holds, its scope and limit. The table chapter 6 points back to | content | `evidence/gameplay/orchestration/report.md`, "Checkpoints and the two caches serve different purposes"; six-hour lifetime from `Agents/config/langgraph.py` (`TURN_CACHE_TTL_SECONDS`) | drafted |
| HS-host-options | The three ways to run the synchronous engine in the async server, each with why it was kept or rejected | content | `frontend/docs/server_design_notes.md` §5; `evidence/gameplay/orchestration/report.md`, decision 13 | drafted |
| HS-pause-diagram | A pause and resume inside a parallel step: the wrapper node, the subgraph's vote step with AI and human seats, the checkpoint, the resume re-running the wrapper, the AI seats replayed from the cache, the human seat through its uncached node. Caption and footer state that reuse depends on cache entries surviving. File: `pause_and_resume.svg` | diagram | `frontend/docs/server_encountered_challenges.md` §2–5; `evidence/gameplay/orchestration/report.md`, decision 12 and "Human seats" | drafted |
| HS-cache-incident | The attributed cross-game replay and the scripted control's 5 → 0, summarised on page 5. Game identifiers and the side-by-side account belong to the Level 3 page | content | `evidence/gameplay/orchestration/report.md`, decision 12 ("The cross-game cache bug") and "What is not established"; `frontend/docs/deploy_log.md`, 2026-10-26 | drafted (prose); Level 3 table planned |

## Not yet drafted

Exhibits for pages 1–4 and the Level 3 page [`../human_in_the_loop/cache_key.md`](../human_in_the_loop/cache_key.md)
are specified in [`../content_plan.md`](../content_plan.md), "Level 2 page briefs" and "Level 3
candidates"; rows are added here when each page is drafted.
