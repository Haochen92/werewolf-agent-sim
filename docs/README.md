# Werewolf Agent Sim — Technical Documentation

How the system works, end to end. This is the **reference** layer — the
cross-cutting architecture that no single module's docstring captures. Per-module
detail lives in code docstrings and package READMEs (e.g.
[`../evaluation/README.md`](../evaluation/README.md)); this folder is the
**synthesis, not a duplicate**.

- **The story / why:** [`../writeup/`](../writeup/)
- **The raw research record:** [`../evidence/`](../evidence/)

> **Status: skeleton.** Written alongside the write-up. Flat files; nested only
> when a section earns it.

## Contents

1. **Architecture & game graph** — the LangGraph topology (parent graph, day /
   night subgraphs, the discussion scheduler, node wiring) and the end-to-end flow
   of a single game.
2. **Roles & win logic** — the 3-faction casting, night/day phases, win resolution.
   - [`generation_prompt.md`](generation_prompt.md) — how an agent's action prompt is
     assembled (payload boundary → formatters → scaffold), the block inventory, and
     the rules for adding a block.
3. **Memory pipeline** — extract → store → dedup → retrieve → enrich, and the
   v7 compounding loop that learns across games.
4. **Evaluation pipeline** — game generation, scoring, and the de-luck credit
   signal. See also [`../evaluation/README.md`](../evaluation/README.md); the credit
   layer's mechanism + rationale doc is
   [`../evidence/credit/report.md`](../evidence/credit/report.md).
5. **Running it** — playing a single game, running a batch, running the loop.
