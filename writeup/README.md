# Werewolf Agent Sim — Project Write-up

The portfolio narrative for the whole project: what it is, what was built, what
the experiments found, and **why** each design choice was made. This is the story
layer — read this first.

- **How it works (technical reference):** [`../docs/`](../docs/)
- **The raw research record (the proof):** [`../evidence/`](../evidence/)

> **Status: skeleton.** Chapters are written during the evidence read pass. A
> chapter stays a flat file until it earns its own subfolder — structure grows
> from the content, not ahead of it.

## How to read this

_The spine — a few-minute linear tour of the project, filled in as chapters land._

## Chapters

1. **The game** — what Werewolf Agent Sim is: a 3-faction social-deduction game
   played by LLM agents.
2. **Game design & engine** — the design decisions (sequential discussion, the
   3-faction role set, abstain voting) and why they were made.
   _How → [`../docs/`](../docs/); proof → `../evidence/{role_set, sequential_discussion, refactor}`._
3. **Episodic memory system** _(the biggest component)_ — cross-game learning,
   v5 → v7: the memory substrate, the paired A/B program, and the compounding loop.
   _Proof → `../evidence/memory_system/`, `../evidence/{dedup, retrieval, extraction}`._
4. **Evaluation rigor** — de-lucked outcome proxies, paired-A/B methodology, and the
   de-luck credit signal.
   _Proof → `../evidence/metrics/`, `../evidence/evaluation/metrics/report.md`._
5. **Frontend** — _added after the build (replay + live spectator)._
