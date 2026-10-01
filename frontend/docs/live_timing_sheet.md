# Live timing sheet — server time, stage time, and the lag between them

> The companion of the entitlement sheet (`server_client_transport.md`): that one traced every
> event the graph emits and ruled who may receive it, and the SSE tiers fell out clean. This
> one traces the same events in **time**: when the server emits each, what each viewer's stage
> does with it and for how long, and how far each viewer's stage runs behind the server. The
> rulings at the foot come first; the code follows them. Drafted 2026-10-01 from a real game
> (`553a1875`, solo, the human at seat 1 as a wolf, `gemini-3.5-flash-lite`, memory on;
> Langfuse trace `0feb5de6`, 1,436 spans; 527 durable events) and the beat sheet's holds (§0).
> Companion records: beat sheet §12 (live pacing), `server_design_notes.md` §7 (the AFK
> clocks), `docs/agentic_ai_encountered_issues.md` entry 3 (how this came up).

## 0. The ruling, and how to read the sheet

**The human's turn is the tempo. Where there is no human turn, the stage either reads or
jumps, never hurries. Nothing on the server ever waits for a stage.**

The engine pauses in exactly two kinds of place: a human's turn (an interrupt; the engine
waits for the answer) and the night barrier (resolution waits for every actor). Both are pauses
in *generation*. Every time the engine waits for a person, every viewer's stage catches up.
Where no person is waited for, events arrive at the agents' response time, a few seconds apart,
and a stage that reads at a human pace falls behind by the difference at every beat.

Columns: **event** (the durable event, in log order) · **tier** (who receives it: P public,
F faction/wolves, S the one seat, O observer until game over) · **server** (when it is emitted,
seconds from the phase's start, from the trace) · one column per **viewer kind**, holding what
that viewer's stage plays for it and how long · **lag** (how far that stage is behind the server
when the event lands, if it matters). Viewer kinds: **V** a villager (sees public only), **W** a
wolf (public + the pack), **I** the investigator (public + own results), **H** the human whose
turn it is, **Sp** a spectator or a dead player (public, plus the pack if they were a wolf).

## 1. Representative durations

**Server (the trace, medians; p90 in brackets).** An agent's discussion turn 6.4 s (9.1) =
situation summary 2.3–2.9 s + retrieval 0.4 s + generation 2.6 s (4.0) + parse; a pass is the
same call. A vote 5.7 s per seat, the seats in parallel, the whole ballot 2.5–7 s. Night: every
role acts in parallel from the barrier's start; healer 2.3 s, investigator 2.5 s, vigilante
4.6 s, serial killer 5.1 s, a wolf's chat line ~4 s, the pack vote ~1.5 s; resolution 0 s. The
day summary 2–4 s between the last turn and the ballot. Game over → extraction (memory on):
tens of seconds to minutes; the longest single generation in this game was 105 s (a stall;
entry 1 of the issues record). A human's own turn: whatever they take (night 1 here: 116 s).

**Stage (beat sheet §0, normal speed).** A speech holds words ÷ 2.4 s, floor 5 s, cap 15 s;
in this game 20–58 words, so 9–15 s and mostly the cap. A pass 4 s. Night shutter 6 s; a card
read 4 s; your own card 8 s; your pack 6 s; the vote's opening 4 s, a chip 2.5 s, the lid 2.5 s,
the verdict 6 s; the morning roll 6 s + 2 s a death; a room's mark 4 s. The dock opens the
instant the prompt arrives (the beat on stage is cut short once, §12).

**The gap that matters:** an agent speaks in ~6.4 s and is read in ~12–15 s. Between two human
turns the stage loses ~6–9 s per agent turn.

## 2. Scenario A — solo, as played (one human, eight agents; no deadlines)

### Day 3, the first stretch (real events 176–212)

| seq | event | tier | server | V / I / Sp stage | H (seat 1) stage | lag of H |
|---|---|---|---|---|---|---|
| 176 | `phase_change` day 3 | P | 0.0 | the day opens (the morning roll just played, 6 s + 2 s) | same | 0 |
| 177–180 | turn, `speech` seat 5 (34 w) | P | +6.4 | rise, think, speak: 14 s | same | 8 |
| 183–186 | `speech` seat 8 (41 w) | P | +12.8 | 15 s | same | 16 |
| 190–193 | `speech` seat 9 (52 w) | P | +19.2 | 15 s | same | 25 |
| 197–200 | `pass` seat 7 | P | +25.6 | 4 s | same | 22 |
| 203–206 | `speech` seat 6 (58 w) | P | +32.0 | 15 s | same | 31 |
| 210–211 | turn seat 1, `input_request` | S | +32.1 | — (V sees "seat 1 is thinking") | **the dock opens at once**; the beat on stage (seat 6's line) is cut short; seat 1's turn beat plays next; the engine waits | ~31 → the stage reaches the turn ~16 s after the dock opened (seat 9 and 7 still to play) |
| 212 | `pass` seat 1 (the human passed) | P | +32.1 + *t_h* | 4 s | lands still (own line) | 0 — **everyone caught up while the human thought** |

*t_h* is the human's thinking time. Then the next stretch: seats 3, 5, 8, 9, 7, 6 → six agent
turns ≈ 38 s of generation against ≈ 69 s of reading → the stage is ~31 s behind when the next
prompt (seq 243) arrives, and so on. **The solo day's lag is bounded by one stretch between the
human's turns** (here 5–6 agent turns, ~30 s); it never accumulates across the day. Since
2026-10-01 the stage plays that stretch at reading pace and the human waits those ~30 s for
their turn beat after the dock has opened. Before, the stretch drained at half speed and read as
"the scenes race by". Solo has no clock, so no rule is needed beyond *read*.

### Night 2 (real events 141–176), the human is a wolf

| seq | event | tier | server | V stage | W = H (seat 1) stage | I stage | lag |
|---|---|---|---|---|---|---|---|
| 141 | `phase_change` night 2 | P | 0.0 | shutter 6 s, then **waits on the bar** ("Acted n of N", padded 20–30 s) | shutter 6 s, the pack room opens | shutter, own room | 0 |
| 142 | `input_request` wolf_discuss | S | +0.1 | — | **dock opens at once** (the pack room's line box); the engine waits | — | 0 |
| 158, 160 | `wolf_message` ×2 (the human's line, then the agent's, 31 w) | F | after *t_h*, +4 | — | own line lands still; the agent's line 13 s | — | W is 13 s behind at most |
| 162 | `input_request` wolf_discuss | S | +4.1 | — | dock opens again, the agent's line cut short | — | 0 |
| 163, 165 | `wolf_message` ×2 | F | after *t_h*, +4 | — | own still; the agent's 5 s | — | ≤ 5 |
| 168 | `input_request` wolf_vote | S | +4.1 | — | the ballot opens at once | — | 0 |
| 169–171 | `wolf_vote` ×2, `wolf_kill_decided` | F | after *t_h*, +1.5 | — | the mark lands, 4 s | — | 4 |
| (parallel) | healer, investigator, vigilante, SK acts | S each | +2–5 from the barrier | — | — | own room, result 4 s | 0 |
| 173 | `night_result` | P | +1.5 (resolution instant once the last actor is in) | the morning roll at once: 6 s + 2 s | **the morning queues behind the mark: ~4 s late** | the morning | W 4 s, V 0 |

**The living human wolf is a few seconds behind a villager at the morning, set by the mark and
any agent line after their last.** The server waited for the human at every pack turn, and
every other stage caught up during those waits.

### Night 4, the human dead (seat 1 lynched on day 3), spectating the pack (events 359–377)

| seq | event | tier | server | V stage | Sp = the dead wolf's stage | lag |
|---|---|---|---|---|---|---|
| 359 | night 4 | P | 0.0 | shutter 6 s, waits on the bar | shutter 6 s, the pack room opens (a dead wolf keeps the wolves' tier) | 0 |
| — | pack lines (agents, ~4 s each; 2–4 lines, 5–15 s read each) | F | +4, +8, +12… | — | each line read in full: **20–45 s of playback for ~12–16 s of generation** | grows ~6–10 s a line |
| 362–363 | `wolf_vote`, `wolf_kill_decided` | F | +14 | — | the mark 4 s | ~25 |
| 377 | `night_result` | P | +14 (barrier; the other roles finished earlier) | the morning at once | **the morning queues ~25–35 s behind the pack room** | 25–35 |

**This is the row that felt wrong in the owner's game**: nothing waits for a spectator, the pack
room plays at reading pace, and the morning lands mid-chat. The same shape holds for a
spectator of an all-agent game and for the landing's showcase.

### Game over (events 377 → 527)

`game_over` lands; the server sends every viewer the observer backlog (roles, results, the
file) at once. The stage may still be in the night: until 2026-10-01 the Reveal switch and File
tab unlocked on arrival ("the file unlocked halfway"); now they unlock when the stage reaches
`over.*`, and the live cut adds no X-ray beat before it. Extraction then runs (memory on) and
the replay row is filed only when the engine's run ends: the curtain shows "Winding the reels…"
until `GET /replays/{id}` answers (the status cannot say it while this viewer's stream holds the
game live).

## 3. Scenario B — four friends at a table (four humans, five agents; deadlines 120 s)

Seats: H1 wolf, H2 villager, H3 investigator, H4 villager; agents in the other five, one of them
the second wolf. Assumed: an agent turn 6.4 s, a human turn 20–60 s, speeches read 12–15 s.

| phase | server | what each human stage does | lag between the four | where the clock runs |
|---|---|---|---|---|
| Day, a stretch of agent turns | one every ~6.4 s | all four read every line at the same holds | **~0** (same events, same instant, same holds; ± network) | — |
| Day, H2's turn | the engine waits | H2: dock at once, clock from release. H1/H3/H4: stage catches up during H2's turn, then "seat 2 is thinking" | 0 after the catch-up | H2's 120 s runs from the prompt's release; if H2's stage was ~30 s behind, the turn beat arrives ~30 s into the clock (one hold cut short, the rest at reading pace) |
| Day, five agent turns in a row | ~32 s | read ~69 s | 0 between the four; each ~35 s behind the server | — |
| Ballot | 2.5–7 s | the opening 4 s, chips, lid, verdict 6 s | 0 | the humans' ballots: each clock from release; the engine waits for all four |
| Night | roles in parallel; the barrier waits for H1 (pack) and H3 (investigate) | H1: the pack room, its own lines landing still, the agent's lines read; H3: own room; H2/H4: shutter + the padded bar (20–30 s) | **H1 behind H2/H4 by the mark + any trailing agent line, a few seconds** | H1's and H3's clocks from their prompts' release; the padding hides whose turn it was |
| Night, a human dead (say H4 died night 2) | as above | H4 now a spectator: public only (or the pack if they were a wolf) | H4 reads at pace; nothing waits for them | — |
| A phone locked for 2 min | — | that stage stops; on return it is ~2 min behind | that one viewer only | their clock still ran if a prompt came: the agent took the turn at the deadline |
| Game over | the backlog at once | all four unlock at `over.*` on their own stage | small | — |

**Reading the table:** between four humans the lag is near zero at every row except a backgrounded
phone and the few seconds of the wolf's pack room, because they all receive the same events at
the same instant and hold them for the same time. The only real question in a timed game is the
*turn clock*: a stage ~30 s behind when the prompt arrives spends ~30 s of its 120 s reaching
the turn at reading pace (see the ruling below for the jump).

## 4. Where the engine pauses, and where a stage lags

| | engine pauses? | stage lags? | who is affected | bounded by |
|---|---|---|---|---|
| A human's turn (day line, ballot, night act, pack line) | **yes** (interrupt) | no: every stage catches up | — | the human |
| The night barrier | **yes** (resolution waits for all actors) | the pack room on W/Sp stages | a wolf a few seconds; a spectating wolf 20–45 s | the pack chat's reading length |
| A stretch of agent day turns | no | yes, ~6–9 s per agent turn | everyone; in solo the human waits for their turn beat after the dock opened | the stretch between human turns |
| An all-agent game / a dead viewer / the showcase | never | yes, without bound | spectators | nothing — the *jump* rule |
| A locked phone, a switched app | no | yes, by the time away | that viewer | the *jump* rule |
| A reconnect / refresh | no | lands **ahead** (still, at the latest) | that viewer | `historyLanding` |
| A draft (up to 3 × ≤ 20 s credit) | yes (the human's turn) | no | lengthens the table's wall time only | `DRAFT_CREDIT_CAP_S` |
| An LLM stall | generation slower than reading | no: everyone waits in step | everyone; the risk is dead air, not divergence | the request budget + rescue (issues entry 1) |
| Game over → extraction | the run continues | the X-ray waits for the stage | everyone | `seesXray`; the curtain's wait |

## 5. Rulings (owner, 2026-10-01)

1. **Holds are the reading floor and live in the browser**, one table (beat sheet §0). The server
   never needs them. "A speech takes 20 s" is a change there and nowhere else.
2. **Read.** With no clock running (solo; a spectator; an all-agent stretch) the stage plays at
   reading pace and lets the queue grow. Built 2026-10-01 (`live-queue.ts`: always normal).
3. **Jump.** When queued holds exceed **~45 s** in a timed game — a prompt far ahead, a phone
   back from its pocket, a dead wolf's pack room with the morning waiting — land still on the
   latest beat: one fold, no beats replayed, no trimmed holds (they flicker), with a strip notice
   "Caught up to the table · n lines in the transcript" that opens the drawer. The transcript is
   the catch-up; a replay of the missed beats inside the live game was considered and rejected.
   Solo games never jump. **Not built yet** (this sheet comes first).
4. **The server clock is authoritative** and starts when the prompt is released. A browser never
   holds the server's clock, for itself or for others; the seat's agent takes the turn at the
   deadline. A browser cursor acknowledgement, and a pull model (the browser asks for the next
   beat), were considered and set aside: they buy an exact clock at the price of per-viewer
   tempo, which in a four-human game makes the table wait on its slowest reader.
5. **Held for a real multiplayer game:** a server-side metered release (one shared tempo for all
   viewers, the pacing tracker's missing floor) and a night padding set from the pack chat's
   reading length instead of the fixed 20–30 s window, so a wolf's and a villager's mornings
   land together. Only if a shared live moment is wanted.
6. **A reconnect lands still** at the latest beat (as built); with ruling 3 in place, a short gap
   may play forward instead. Decide on a real game.

## 6. Open, to settle on a real four-human game

- The jump threshold (45 s is a guess from the solo stretches above; a timed game may want 30).
- Whether the human's turn beat should itself be allowed to jump the stage to the turn when the
  clock is short (< 60 s left), regardless of the threshold.
- Whether the night padding should follow the pack chat's length (ruling 5) once wolves are
  often human.
- A measurement: stamp each event with the server's emit time (the log has none today; the
  trace does) so a future sheet can be generated from a game rather than drafted by hand.
