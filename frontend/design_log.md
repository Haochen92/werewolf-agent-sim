# Frontend Design Log

Ideas log for a frontend to the werewolf agent sim. Status: **ideas only — nothing here is
implemented or scheduled.** Captured 2026-06-06 from a design discussion; this folder is for
frontend concerns only (the `Agents/` package stays backend-only).

Context: the project is primarily a portfolio piece, but the frontend should not preclude a
publishable MVP where real players sit in games with the agents.

---

## 1. Framing decision (the identity of the product)

A generic werewolf frontend competes with Wolvesville and dozens of Mafia apps — an unwinnable
fight. What this project uniquely has is **a fully observable AI mind on every seat**: Langfuse
traces, memory retrievals, situation summaries, the scheduler's reactive queue, enforced
information boundaries with leak checks.

> **Identity: "watch AIs deceive each other — and see exactly why."**
> Observability is not backend plumbing to hide; it IS the product. Human play is the MVP layer
> on top, not the core.

## 2. Features, in build-order tiers

### Tier 1 — Spectator / Replay Theater (portfolio core, cheapest to build)

- **Replay player** over existing batch artifacts (JSONL records + `day_channel` /
  `day_summaries`) — the backend already persists everything a replay needs. Timeline scrubber by
  day/phase; speech bubbles around a virtual table. Zero new game code.
- **The X-ray toggle** (the differentiator): click any agent mid-replay and see its private
  context — role, the actual retrieved memories (observations / strategy points), its
  `firing_reason`, what the novelty gate rejected. A **"thoughts vs. words" split pane**: what the
  agent *said* publicly vs. what its reasoning trace shows it was *doing*. This is the
  interview-screenshot artifact.
- **Scheduler visualization**: live mini-graph of the reactive queue — who got mentioned, whose
  obligation fired, pass-turn markers, trailing-pass termination. Phase A #1 made turn-taking
  legible; show it.
- **Dramatic irony meter**: spectators know all roles, so the UI can surface "the village is
  about to vote out the investigator" moments. Free tension from data that already exists.

### Tier 2 — Live mode

- Same view, streaming. LangGraph streams natively; an SSE/WebSocket relay is straightforward.
  **Sequential discussion is a gift for broadcast** — one speaker at a time is already a
  watchable format (concurrent fan-out would have been unwatchable).
- Spectator prediction overlay: "who's the SK?" bets that lock before reveal. Engagement without
  touching game logic.

### Tier 3 — Human-in-a-seat (the publishable MVP)

- One human takes a chair among 8 agents. Architecturally close: the scheduler is **stateless and
  recomputes from `day_channel`**, so a human turn is an external-input node with a timer.
- A vestigial `human_player` concept already exists in the codebase (currently slated for v5
  cleanup) — **this tier is the argument for keeping/reviving it rather than deleting it.**
- **Security story, verbatim from the backend**: the human client gets the same information
  surface the agent payload gating allows. Server-authoritative role-gated views, mirroring
  `build_speaker_send` / `fan_out_day`; the same leak-check invariants
  (`tests/leak_test.py`, see `evidence/agent_boundaries/`) guarantee the client never receives
  private state. The boundary doctrine becomes a user-facing feature.
- **Post-game reveal**: "here's what the AIs thought of *you*" — every memory/suspicion entry
  referencing the human player. The shareable screen.

### Tier 4 — Stretch / fun

- **Coach mode**: play with an AI whispering retrieved strategy points to you — the memory
  pipeline as a player-facing feature.
- **Public eval dashboard**: faction win rates, memory-on vs. memory-off — the Phase C A/B as a
  living page instead of a notebook.

## 3. Design theme

Skip cartoon-medieval (Wolvesville owns it) and generic dark-dashboard. Theme:
**"séance noir meets control room"** — the seam between story world and machine world is the
visual thesis of the whole project.

- **Table view (story world)**: candlelit; deep ink/charcoal palette; warm amber light pooling at
  the table center. Agents as minimal portrait cards — tarot-card framing, not 3D avatars (cheap,
  stylish, AI-generatable). Serif display type for speech. Night phase drops to blue-black with
  only acting roles' cards lit.
- **X-ray layer (machine world)**: deliberate contrast — flipping into an agent's mind goes
  clinical: monospace, thin cyan-on-dark, trace-viewer aesthetics. Warm deception on top, cold
  observability underneath.
- **Micro-touches**: retrieval events as a faint card-glow ("it's remembering something"); votes
  as chips physically sliding toward the accused; SK kills rendered differently from wolf kills
  (deaths are already attacker-typed in the backend).

## 4. If only one artifact gets built

**The replay theater with the thoughts-vs-words pane**, fed straight from existing batch
artifacts. Zero new game code, maximum "nobody else can show this" factor — and it doubles as a
debugging/inspection tool for Phase B labelling, so it isn't even scope creep.

## 5. Backend touchpoints to keep in mind (no action yet)

- Replay reads from batch JSONL + `day_channel`/`day_summaries` — keep those fields stable in
  v5 record schemas.
- Live mode wants a streaming relay over the LangGraph run — no graph changes, just a consumer.
- Tier 3 depends on the `human_player` vestige: don't hard-delete it in the v5 cleanup without
  noting this use case.
- Any client-facing view layer must be derived from role-gated payloads, never raw graph state —
  same invariant the leak checks enforce for prompts.
