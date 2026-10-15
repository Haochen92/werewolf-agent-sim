# Serving the agents in production: encountered issues

> What went wrong with the models while real people played the served game, what each problem
> turned out to be, and how it was settled. Written to be read cold, without the chat history
> or the code open. The research-era issues (alias drift, structured output on flash-lite, the
> leak checks, prompt epochs, judging LLM output) are recorded where they happened, in
> [`../evidence/`](../evidence/); this file is only the production pass. Companion logs for the
> other layers: [`../frontend/docs/server_encountered_challenges.md`](../frontend/docs/server_encountered_challenges.md)
> (the game server) and [`../frontend/docs/build_log.md`](../frontend/docs/build_log.md) (the
> frontend). Started 2026-10-01.

Each entry: **what happened** · **why** (the mechanism, named) · **how it was settled** · where to
look.

---

## 1) A turn held for minutes, and nothing ever failed (2026-09-30)

**What happened.** The owner played a solo game against the served backend on
`gemini-3.6-flash`. Drafting a line took five minutes; then the next character's turn did not
come at all. The browser's stream was healthy (keep-alives every few seconds, status polls
answering 200), so it looked like the frontend was stuck. It was not: one agent's draft had
taken 301 s, of which 282 s sat inside the retrieval call, and a turn's situation summary had
taken 105 s. The rescue model, configured for exactly this case, never fired.

**Why.** The served game runs on Vertex, because the server env has no `GOOGLE_API_KEY` and the
factory then picks the global Vertex endpoint. Vertex's *dynamic shared pool* for a newly
released model holds a request for 2–5 minutes and then bounces it with
`429 RESOURCE_EXHAUSTED`. The google-genai SDK re-sends each bounce up to five times with a
1–60 s backoff, and LangChain wraps that in six attempts of its own. Thirty silent retries deep,
no exception ever reached the code that chooses the model. The rescue path was keyed on
*errors*, and a hang is not an error. The log line "AFC is enabled with max remote calls: 10"
that appeared beside the hang was a red herring: it is google-genai's automatic-function-calling
banner, printed on every call, and this project registers no tool functions.

**How it was settled.** Time is now a failure, and a run of failures changes the model.

- *A request budget.* The game model waits `GAME_LLM_TIMEOUT_S` (30 s) and sends a request
  `GAME_LLM_ATTEMPTS` (2) times in all, then fails; the day summary waits
  `GAME_SUMMARY_TIMEOUT_S` (90 s), because its failure path is the raw transcript. Post-game
  extraction is untouched. The worst honest turn measured before the change was 11 s, so 30 s
  loses nothing (ruled with the owner, who first asked whether 60 s was safer).
- *A stall hands the turn over at once.* A timeout, a 429 or a 5xx is classified as a stall
  (`is_transient_provider_error`); the primary is not asked again that turn, and the rescue
  model takes it. The rescue for `gemini-3.6-flash` is `gemini-3.5-flash`: a different family
  and quota pool, stable GA, so it is a genuine rescue and not the same pool under another name.
- *Two stalls in a row move the game.* `GameLLM.health` counts stalls; after
  `GAME_STALL_RESCUE_AFTER` (2) in a row, every turn starts on the rescue model for
  `GAME_STALL_RESCUE_COOLDOWN_S` (300 s), then the primary gets one try, and a good answer
  clears the count. Drafts for the human seat share the path.

Commits `c67d47c` (the budget) and `c74284c` (the stall count). Code:
`Agents/llm_factory/accessors.py` (budget constants, `_request_budget()`),
`Agents/llm_factory/health.py` (`ModelHealth`), `Agents/llm_factory/embeddings.py`
(`is_transient_provider_error`), `Agents/turn/agent_player.py` (`_STALLED`, `run_agent`); tests in
`tests/engine/test_model_fallback.py`. Design note: `frontend/docs/server_design_notes.md`
§13 "Stalls".

**What to know.** The Developer-API pool was considered as an alternative to Vertex and not
adopted (unclear whether the free-trial credits cover it). The viewer is not told when a turn ran
on the rescue model; a transcript notice was offered and is not built. A game-level watchdog
("no part produced for N minutes") is still the open item in the server's fault model
(`server_design_notes.md` §5c, mode 4); the request budget narrows that gap, it does not close
it. **Status 2026-10-01: committed, not deployed; the owner's local backend has not been
restarted on it.**

## 2) A human's draft could stall the whole table (2026-09-30)

**What happened.** While a seated human waits for their agent's draft, the time it takes is
credited back to their clock so the draft is free. With the stall above, that credit could run
to minutes, and in a multiplayer game the other seats would wait on it. In the same pass the
agents' lines are asked to stay under about 120 words, while the human's box took 500
characters and the server took anything.

**How it was settled.** The credit is capped at `DRAFT_CREDIT_CAP_S` (20 s)
(`server/game/game_session.py`), and a human's line is refused over `MAX_LINE_CHARS` (700,
about the agents' 120 words) with the server's words shown under the box
(`Agents/turn/human_turn.py`); the frontend's box stops at the same 700 and counts from 600.
Commit `b7517ec`; frontend `8b5775a`.

## 3) Where no human turn sets the tempo, the stage plays at agent speed (2026-10-01) — OPEN

**What happened.** The live stage was changed to play every beat at its full hold, however
many are queued (until then a backlog of three or more drained at half speed, which made a
solo game race by). That fixed the solo game between turns, and surfaced the real shape of
the problem, which the owner put more clearly than the first draft of this entry did.

**The owner's explanation.** The engine pauses in exactly two kinds of place: a human's turn
and the night barrier (resolution waits for every actor). Both are pauses in *generation*.
A human's turn is therefore the game's only tempo control: every time the engine waits for a
person, every viewer's stage catches up. Where there is no human to pause the engine, the
events come at the agents' response time, a few seconds apart, which is too fast for a human
to read; the stage then either lags behind the server or hurries, and nothing on the server
waits for a stage (nor should it: a single slow browser must never hold the table, and the
seat's agent takes over when a human is late). A night with a human wolf in the pack
illustrates the rule: the agent's line arrives, the human's prompt follows at once and the
dock opens, the server waits while they read and type, and after their vote the resolution
runs; the human wolf sees the morning only a few seconds after a villager does (the mark beat,
perhaps the agent's last line). The wolves "needing more beats" after the response is real but
small. The large gap belongs to the viewer **with no turn to pause on**:

- a dead player spectating the pack room (two agents now, lines at generation speed, read at
  reading speed: 20–40 s behind by the morning, which then lands mid-chat);
- a living player watching the agents' day speeches between their own turns (eight agents in
  a solo game);
- the landing page's showcase game, and any all-agent stretch.

In each, every beat's reading time exceeds its generation time, so the queue grows by the
difference at every beat. (Drafts, by contrast, add no lag: the engine is paused at that
turn and the other stages catch up while the human drafts; a draft only lengthens the table's
wall time, capped at 20 s of credit each.)

**Why it is not a leak.** The server decides per event, per viewer, what each browser may
receive (public, wolves only, one seat, observer); lag changes only *when* a viewer sees
what they were always entitled to. The game-over backlog, sent to everyone, is gated on the
client until the stage reaches the ending (same pass).

**The ruling, to go at the head of the live timing sheet:** *the human's turn is the tempo;
where there is no human turn, the stage either reads or jumps, never hurries.* A growing
queue has two honest answers, and the sheet says which applies where:

- *Read.* Play on at reading pace and let the queue grow. Right for solo play between turns,
  where nothing is waiting on the viewer.
- *Jump.* Past a threshold (about 45 s of queued holds), land still on the latest beat, one
  fold, no beats replayed, with a strip notice ("Caught up to the table · n lines in the
  transcript") opening the drawer; the transcript is the catch-up. Right whenever a clock or
  other people are involved: a timed turn prompt far ahead, a backgrounded phone, a dead
  wolf's pack room when the morning has been waiting. Chosen (owner, 2026-10-01) over
  trimmed holds, which flicker, and over a replay-inside-the-game of the missed beats, which
  the transcript already covers. Solo games never jump.
- *The server clock stays authoritative* and starts when the prompt is released; the seat's
  agent takes the turn at the deadline. No cursor acknowledgement from the browser is needed
  under this ruling; it was considered and set aside.
- *Held for later:* a server-side metered release (one shared tempo for all viewers, the
  pacing tracker's missing floor; the night padding set from the pack chat's reading length
  rather than a fixed 20–30 s window) matters only if a shared live moment is wanted, e.g.
  four friends on their phones at a table. Not built until a real multiplayer game asks.

**Next.** Before code, a *live timing sheet* (`frontend/docs/live_timing_sheet.md`, the
companion of the entitlement sheet that produced the clean SSE tiers): one row per event the
graph emits, its tier, the server's emit time with representative durations from a real
trace, what each viewer's stage does with it and for how long (villager, wolf, investigator,
the human whose turn it is, spectator), and each viewer's running lag; solo and four-human
scenarios side by side; the rulings above written at its foot. Pointers:
`frontend/src/stage/containers/live-queue.ts` (the pacing rules), `live-state.ts`
(`advance`, the one-time prompt cut, `historyLanding`), `server/game/pacing.py` (the night
padding and the progress bars), beat sheet §12, design note
`frontend/docs/server_design_notes.md` §7 (the AFK clocks).
