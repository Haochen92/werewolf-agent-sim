# Werewolf Agent Sim: the portfolio write-up

The draft of the project's portfolio pages, written for a hiring reader who meets the project cold.
Pages are drafted here in Markdown and ported to the portfolio site later; only each page's
"Page copy" section goes to the site.

- **How it works (technical reference):** [`../docs/`](../docs/)
- **The record behind every claim:** [`../evidence/`](../evidence/)

## Chapters

The arrangement is [`_planning/structure_proposal.md`](_planning/structure_proposal.md) (v2): eight
chapters in four groups, under one overview page. Status as of 2026-10-31.

| # | Chapter | Folder | Status |
|---|---|---|---|
| | **A. How the game runs** | | |
| 1 | Game design and orchestration | [`game_design_orchestration/`](game_design_orchestration/game_design_orchestration.md) | Level 1 page, five Level 2 pages and two Level 3 pages drafted |
| 2 | Information boundaries | [`information_boundaries/`](information_boundaries/information_boundaries.md) | Level 1 page drafted and reviewed (2026-10-30); its one Level 3 page drafted and replaced by the owner's short version (2026-10-31) |
| | **B. Improving how agents play** | | |
| 3 | Context engineering | [`context_engineering/`](context_engineering/context_engineering.md) | Level 1 page drafted and reviewed (2026-10-30, revised 2026-10-31); four Level 2 pages drafted and reviewed 2026-10-31, owner's review in progress; one Level 3 after page 4 |
| 4 | Memory | [`memory/`](memory/memory.md) | Level 1 page, five Level 2 pages and their Level 3 pages drafted; claims bounded by [`memory_presented_set.md`](memory/memory_presented_set.md) |
| | **C. Knowing whether it worked** | | |
| 5 | Evaluation | [`evaluation/`](evaluation/evaluation.md) | Level 1 page approved 2026-10-25; eight Level 2 pages and four Level 3 pages drafted |
| | **D. Serving it to people** | | |
| 6 | Cost and latency | [`cost_and_latency/`](cost_and_latency/cost_and_latency_codex.md) | Self-contained Level 1 drafted (direction approved 2026-10-30); no Level 2; one Level 3 (caching across providers) drafted 2026-10-31, owner's review pending |
| 7 | Running it in production | [`running_in_production/`](running_in_production/content_plan.md) | Content plan only (candidate, not approved) |
| 8 | Frontend: the live stage and replays | — | Not started; source material in [`../frontend/docs/`](../frontend/docs/README.md) |

## What a chapter folder holds

- `<chapter>.md`: the Level 1 page.
- `<subject>/<subject>.md`: a Level 2 page, with its Level 3 pages beside it in the same folder.
- `content_plan.md`: the chapter's page plan; `editorial_notes.md`: claim changes made in editing.
- `exhibits/`: figures, and `source_map.md` saying where each exhibit comes from.
- `<subject>/_authoring/`: the writing skill's brief for a page (frame, evidence selection, open
  questions). Authoring material, never page copy.

## Elsewhere

- [`_planning/`](_planning/): the write-up's working files. [`map.md`](_planning/map.md) is the
  building-blocks ledger and holds each chapter's "Handle with care" list;
  [`triage.md`](_planning/triage.md) is the finished evidence triage the map's card numbers refer to;
  [`skills_inventory.md`](_planning/skills_inventory.md) the public skill tags;
  [`portfolio-agent-brief.md`](_planning/portfolio-agent-brief.md) the brief for building the site.
- The writing rules and the page workflow: the `write-portfolio-page` skill,
  [`../.agents/skills/write-portfolio-page/`](../.agents/skills/write-portfolio-page/SKILL.md).
