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

## 3) The stage lags the server, so a timed clock can run before the player has seen the turn (2026-10-01) — OPEN

**What happened.** The live stage was changed to play every beat at its full hold, however
many are queued (until then a backlog of three or more drained at half speed, which made a
solo game race by). The agents play at machine speed, so the stage now lags the server by
design: a solo game's viewer watches at reading pace while the engine is turns ahead.

**Why it matters.** The server sends a seated human's turn prompt the moment the engine
reaches it, and the dock opens at once with the turn clock running on the server's deadline.
In a multiplayer game with deadlines, a player whose stage is still playing the earlier
speeches can therefore be asked to answer before they have watched what they are answering
to; worst case the clock runs out, the seat's agent speaks for them, and they never saw the
turn they lost. Solo games have no clock, so nothing changes there. This is not a privacy
leak: the server decides per event, per viewer, what each browser may receive (public,
wolves only, one seat, observer), and lag changes only *when* a viewer sees what they were
always entitled to, never *what*. The game-over backlog, which the server sends everyone, is
gated on the client until the stage reaches the ending (same pass).

**Status.** Open; the owner flagged it as major. Fix belongs to the server, not the client:
- *Pace the agents to the audience.* The engine already has a pacing tracker
  (`server/game/pacing.py`) that publishes progress bars; the missing piece is a minimum
  interval between public events (an agent's turn is not released until the previous beat's
  hold has elapsed for the slowest viewer, or simply a floor of a few seconds per turn), so
  the stage can keep up. This also makes the live game feel played rather than replayed.
- *Or start the clock at the stage.* Only the client knows when the turn beat is reached; a
  deadline that starts when the client reports "the turn is on stage" (an acknowledgement on
  the turn request) keeps the server authoritative on duration while the player gets the
  whole allowance. Needs an AFK bound so an absent client cannot hold the table.
Either way the stage's holds (beat sheet §0) become the game's tempo, which music will
later sit in. Pointers: `frontend/src/stage/containers/live-queue.ts` (the pacing rules),
`live-state.ts` (`advance`, the one-time prompt cut), beat sheet §12, design note
`frontend/docs/server_design_notes.md` §7 (the AFK clocks).
