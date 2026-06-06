# Role Set Decision (Phase A #2 of the foundation rebuild)

> **⏩ READING GUIDE / CURRENT STATE (started 2026-06-01). Start here if picking this up fresh.**
> This logs the design discussion for the **role set** — one of the 5 foundation-rebuild changes
> (see [[project-ship-roadmap]] Phase A) and a *gating* one: the role set must be locked before
> role strata, per-role prompts, the v5 DB seed, and the keystone win-rate A/B can be designed.
> **⏸ PARKED behind Phase A #1 (sequential redesign) + a discussion-quality gate (decided 2026-06-01).**
> Sequential is built/validated on the *current* 4-role forced-vote game FIRST; if it fixes the bland
> discussion, roles are added afterwards for richness/keystone reasons only (not to fix discourse).
> Resume THIS workstream only after that gate passes. Active workstream now = `evidence/agent_speaking/`.
>
> **Status: casting + voting design LOCKED, no implementation yet, no role added.** The central
> reframe below — **two casting targets (lean-eval vs rich-ship)** — is the spine of the decision; the
> locked 9-player lean-eval casting and the relaxed-voting mechanism are ready to build. **Resume at
> "Still open — next dominoes" at the bottom; the next substantive step is the 3-faction win-condition
> rewrite.**
>
> **Hard rule already locked:** no action-redirection engine for v1 ship → **no Witch, no
> Bodyguard** (both require intercepting/redirecting another agent's night action). See §3.

## Motivation

Current game = 4 roles, 2 factions (see codebase grounding §1). Three problems motivate revisiting
the role set:
1. **Bland discussion.** Dialogue is generic/repetitive; agents don't coordinate (e.g. nobody ever
   pressures the investigator to reveal, despite prompts describing the role).
2. **Boring memory content.** Bland play → the episodic `observations` store is repetitive, which
   undercuts the thing the project is trying to demonstrate.
3. **Keystone needs a measurable vehicle.** The headline experiment is memory-on vs memory-off win
   rate ([[project-ship-roadmap]] Phase C); the role set determines what that A/B is measured on.

**Key diagnosis (do not conflate three causes):** the bland-discussion problem is *mostly not* a
role-count problem.
- "Nobody asks the investigator to come out" is a **structural coordination failure** of the current
  **parallel** day phase — agents speak simultaneously, so a question in round *r* can't be answered
  in round *r*. Fixed by the sequential redesign ([[project-sequential-discussion]]), **not** by roles.
- Generic dialogue is partly flash-lite, partly prompting.
- The role lever is **"claimspace"** (see §2 research), not raw power. More power roles can make
  discussion *worse* (mass-claim solves the game). Roles contribute "break the binary"; sequential
  structure + a vanilla floor contribute the rest.

## The central reframe: two casting targets

The discussion kept colliding because we were designing one casting for two different jobs. Split them:

- **Lean-eval casting** — the *minimum* role set that (a) makes the memory→win-rate effect cleanly
  measurable and (b) is non-degenerate/interesting enough to produce decent memory. This is what
  Phase A freezes, Phase B labels, and Phase C runs the A/B on. **Bias hard toward minimal** — every
  added role doubles namespaces and dilutes per-`(role,phase)` episode density (see §4), and raises
  per-game cost (~$0.20/game today). Cost and statistical power both push lean.
- **Rich-ship casting** — the fun, varied set for the portfolio demo + friends playing. Built
  **after** memory is proven (the user's own "prove it works, then add as many roles as we want").

Most of the exciting roles below (Survivor, Traitor, Vigilante, neutrals, flexible voting, wolf
abilities, bigger player count) are **rich-ship**, deferred. The lean-eval casting is small.

## Axis considerations (how roles are weighed)

Every candidate role is scored on five axes — the first three are the core eval axes, the last two
are the "is it worth shipping" sub-axes the user added:

1. **Memory-leverage** — does episodic recall of past games plausibly change this role's decisions?
   (High for decision-rich roles: investigator reads, SK target selection + bluffing, vigilante shots.)
2. **Measurability** — individual win condition (clean binary A/B on one agent) vs team proxy
   (diffuse, high-variance). Solo roles score high; team roles need denser proxy metrics.
3. **Implementation / rebalance cost** — LOW (standalone self/other-target action) / MED (reads the
   visit graph) / HIGH (intercepts or redirects another agent's action — needs a resolution engine).
   **HIGH is banned for v1.**
4. **Richness / interesting-to-play** — does it make the game more fun and the transcripts more
   interesting? (Rich-ship axis.)
5. **Claimspace contribution** — does it add fake-claim surface / forced-reveal pressure / break the
   town-vs-wolf binary? (The literature-backed lever for discussion richness, §2.4.)

## Research grounds (Town of Salem / Mafia / BotC design literature, 2026-06-01)

Web research into ToS 1/2, BotC, and Mafia design theory. These are the *grounds* for role selection.

**Implementation-complexity tiers** (the basis for the HIGH-ban):
- **LOW** (self/other-target, no engine): Survivor (self-vest), Executioner (win-flag), Guardian
  Angel, Doctor, Sheriff, Investigator, Mayor, Vigilante (+post-resolution faction check), Jester.
- **MED** (reads the visit graph): Serial Killer (roleblock-redirect), Veteran (alert/reflect),
  Lookout, Arsonist (persistent douse state), Werewolf-as-ToS (full-moon rampage).
- **HIGH** (intercept/redirect another agent's action — needs a resolution engine): **Witch**
  (puppeteer/control), **Bodyguard** (absorb+counter an attack on another), Pirate (duel+roleblock),
  Jailor (block+protect+intercept+stateful penalty, MED-HIGH).

**Balance principles:**
- **Killing-power scaling: ~1 killer per 5 players.** A 3rd killing faction in a sub-10-player game
  is a known way to collapse it (2–3 deaths/night before deduction). The current 8-player / 2-wolf
  game is *already at the killing budget* — adding any night-killer (SK, vigilante) requires more
  players, more protection, or it makes the too-short game shorter.
- **ToS standard 15-player balance** = 13 Town+Mafia + exactly **1 Neutral Evil + 1 Neutral Killing**;
  designers say those two neutral slots are what make it balanced. BotC scaling: evil is always a
  ~1-in-4-to-3.5 informed minority (7p = 5 good/1 minion/1 demon; 10p = 7/2/1).
- **Claimspace / vanilla floor (the discussion-richness lever):** "if everyone full-claimed day 1 and
  town could win on night actions alone, you have too many power roles — add vanilla townies."
  Heuristic: *roughly as many vanilla players as scum roles.* Vanilla villagers are load-bearing —
  they're **where fake-claims hide**. → Do **not** replace all villagers with power roles (the user's
  idea #3 as stated would *reduce* richness). Keep a vanilla floor.
- **Why neutrals exist:** they break the town-vs-wolf binary so "not-town ≠ wolf," making reads
  harder and rewarding behavioral deduction + fake-claiming over mechanical claim-counting.

**Sources:** townofsalem.io/roles; town-of-salem.fandom.com (Witch, Jester, Serial Killer,
Executioner, Survivor, Bodyguard, Veteran, Neutral, Game Modes); townofsalem.wiki.gg (ToS2 variants);
wiki.bloodontheclocktower.com (Setup, Teensyville, Character_Types); mafiauniverse.com Core Balance;
smogon.com Mafia Game Design Best Practices; wiki.mafiascum.net (Townie, Super Vanilla).
*Caveat:* role mechanics differ across ToS1 / ToS2 / BToS2 (notably Witch faction, Pirate win cond.);
treat ToS2 wiki.gg numbers as current canonical.

## Candidate verdicts (as of 2026-06-01)

| Candidate | Axes | Verdict |
|---|---|---|
| **Serial Killer** (Neutral Killing, solo) | mem-leverage HIGH, measurability HIGH (individual win), cost MED, balance hazard in small game | **Lean-eval: the keystone solo role** (pending confirm). Solo win = clean single-agent A/B. Needs player-count headroom or SK-tuning (e.g. no night-immunity / every-other-night) so it doesn't collapse the short game. |
| **Traitor** (Neutral Evil, sides w/ wolves, no kill, mutual unknown) | claimspace HIGH, cost LOW (win-flag only), mem-leverage MED | **Recommended substitute for Witch.** Delivers the "fake your faction / risk wrongful targeting" dynamic the user wanted, with zero redirection engine. Win-condition scoping is open (§ point 3). Likely **rich-ship**, not strictly needed for the SK keystone. |
| **Witch** (Neutral Evil, puppeteer) | cost **HIGH** | **Rejected for v1.** Needs a full action-redirection engine; awkward to narrate in text. Use Traitor instead. |
| **Survivor** (Neutral Benign) | cost LOW, claimspace MED, mem-leverage LOW | **Deferred to rich-ship.** Under current short/forced-vote rules its dominant strategy is trivial (claim survivor, vote with town, self-protect) → near-free win, low eval value. Becomes interesting only with more days + more killers (must choose an ally). |
| **Vigilante** (Town Killing) | mem-leverage HIGH, cost LOW-MED, adds a town night-kill | **Lean-eval (conditional on relaxed voting).** Swaps in for one villager (`4→3 villager + 1 vig`). Relaxed voting removes the lynch channel → headroom for its (3-bullet, guilt-limited) kills. Kills the boring-villager problem; gives town a kill to offset SK. **Caveat:** its memory benefit is *siloed* to the vigilante namespace (observations are per-role) — it does NOT enrich the SK keystone store; value is richer transcripts + a more complex board for the SK to face. SK remains sole A/B subject. |
| **Bodyguard / Jailor / Pirate** | cost HIGH / MED-HIGH | **Rejected/deferred for v1** (engine cost). |
| **Plain Villager ×N** | the vanilla floor | **Keep ≥2.** Deliberate design choice, not laziness — load-bearing for claimspace. |

## Current lean-eval casting (LOCKED direction as of 2026-06-01)

> **9 players:** villager ×3 · wolf ×2 · healer ×1 · investigator ×1 · **vigilante ×1** ·
> **serial killer ×1 (night-immune)** · **relaxed voting** (see mechanism below).
> SK = sole keystone A/B subject. Vanilla floor = **3 villagers** (locked). SK night-immunity protects
> the keystone subject from early vigilante sniping (vig shoots at night → whiffs on immune SK) → more
> SK episodes for the A/B.

## Relaxed voting + stall guard (DECIDED — mechanism, ready to implement)

Replaces forced-every-day voting. Designed against the existing tally code ([day_resolution()](Agents/nodes.py#L373-L461),
which is already **plurality** — only a tie-for-max yields no elimination — and there is currently **no
`max_days`**; games end only on a win condition, and night kills already guarantee termination).

- **Abstain = a sentinel vote target.** Add `"abstain"` to the valid vote targets. Keep
  `vote_target` a **required `str`** (do NOT make it nullable — flash-lite fails on optional/nullable
  fields, see [[feedback-flashlite-optional-fields]]). "abstain" is just another entry in the existing
  `Counter`: if **abstain wins the plurality or ties for it → no lynch** (reuses the existing no-elim
  branch). A player winning outright → lynched. Side benefit: kills the edge case where one lone vote
  could lynch someone (now it loses to the abstain bloc).
- **Stall guard — escalation.** Track `no_lynch_streak` in state; increment on any no-lynch day
  (abstain-plurality *or* tie), reset to 0 on a lynch. When it hits **K=2**, the next day is a
  **forced day**: drop `"abstain"` from valid targets (mandatory plurality vote). Keeps the daytime
  from going toothless (the real risk — not infinite stall, which night kills already prevent) and
  bounds the long tail. Don't try to *guarantee* a lynch on the forced day (random tiebreak-lynch is
  unfair); the day cap catches the pathological remainder.
- **Cost backstop.** Add a `max_days` config (~12), essentially never hit since night kills end games
  far sooner; at the cap, decide by surviving faction ratio or declare a draw.
- **Why:** abstain makes "act now vs wait for more info" a real strategic choice and lengthens games
  when the town is uncertain — the cheap length lever (no extra agents/round) vs scaling player count.
  Sequential + silence gate ([[project-sequential-discussion]]) further cuts per-day token cost.
- **Scope:** localized — `day_resolution` (abstain handling + streak), valid_targets construction,
  the vote prompt (when to abstain + forced-day rule), two config knobs (`abstain_enabled`,
  `max_days`), a `no_lynch_streak` state field. **No graph-structure change.**

## Resolved this session (2026-06-01)

- **Traitor** → wolves-only win condition if used (it can't co-win with a *solo* SK by definition);
  **rich-ship, not in the eval casting.**
- **Wolf abilities beyond killing** → **no** for lean-eval (clean informed-minority killer); a one-shot
  "frame" is a rich-ship option only.
- **Vanilla floor** → **3 villagers** (was "≥2").
- **Per-role extraction model** → flash-lite is fine as a cost lever (keep schemas all-required); the
  binding cost is per-namespace episode **density**, not extraction price (see §4).

## Still open — next dominoes (resume here)

1. **Confirm SK is the keystone solo role** (code currently has no SK — only the 4 roles). Everything
   above assumes yes.
2. **3-faction win-condition rewrite** — [check_game_end_day](Agents/nodes.py#L601-L608) currently
   lumps all non-wolves into `surviving_villagers`, so the SK is miscounted as a villager. Needs a real
   3-faction rewrite (village / wolves / SK). Pick the formulation when doing it; night-immune SK beats
   wolf 1v1 by mechanics → no special endgame rule needed (see Balance section). **This is the next
   substantive design step.**
3. **Implement relaxed voting + stall guard** (mechanism above — ready to build).
4. **Then:** how the locked set flows into **v5 DB seeding** ([[project-ship-roadmap]] #5) + **eval
   strata** (role × phase). Watch SK-namespace density and the baseline-run headroom sanity-check.

## §4 note — the real scaling cost is memory density, not extraction price

Memory is namespaced `(type, role, phase)`. Doubling roles ~doubles namespaces, halving episodes per
`(role,phase)` bucket per game. The **keystone SK namespace** specifically needs enough episodes for
the memory-on arm to have something to retrieve — a thin store shows "no effect" for the wrong reason.
→ More roles = more seed games needed to hold density. This is a stronger argument for the lean-eval
casting than per-game $ cost is. (Flash-lite extraction is fine as a cost lever; keep schemas
all-required per the flash-lite optional-fields JSON issue.)

## Balance is deliberately deprioritized for the eval (decided 2026-06-01)

The keystone measures a *difference* (SK memory-on vs memory-off, paired/seeded, identical rules both
arms) → the **absolute faction win rate doesn't bias the A/B**, so global balance is a non-issue for
Phase C. (Aside on direction: adding the night-immune SK squeezes the **village** more than the wolves
— SK is a shared enemy + lynch-sink + night-drainer; wolves' anti-wolf forces (vigilante, relaxed
voting reducing town self-mislynch) roughly wash, so wolves stay ~flat, village drops, SK takes a new
win share. But this doesn't matter for the experiment.)

**Two things that DO matter (neither is "fairness"):**
1. **Headroom** — SK win rate must not be floored/ceilinged, or memory has no room to move it. Likely
   fine: the hard part is *surviving day-lynches to reach* a winning endgame (SK is the lynch-sink),
   so SK won't be ceilinged even with a deterministic SK-favorable 1v1. **Sanity-check in the baseline run.**
2. **Win/termination determinism** — the SK-vs-wolf endgame must be *defined* so outcomes never hang
   (undefined parity = noise in the metric). With a **night-immune SK** this falls out for free: the
   wolf's night kill whiffs, the SK kills the wolf → SK wins the 1v1 by mechanics alone. **No special
   rule needed.** The "2-1 → wolf wins" / parity tweaks are *optional caps* held in reserve, used only
   if the baseline shows SK pinned high.

**De-risk via dense metrics over the binary win** (also addresses the roadmap's power worry): SK
survival length, kills landed, correct avoidance of healer-protected/identified targets, days-survived-
as-suspected. Lower-variance and less sensitive to endgame edge cases — memory can show up there even
when win/loss is noisy.

## Codebase grounding (current model, as of 2026-06-01)

- **Roles** (4): `Agents/constants.py:3` — `["villager", "wolf", "investigator", "healer"]`;
  `VALID_ACTION_PHASES_BY_ROLE` at :8.
- **Default config** (8 players): `Agents/game_config.py:8-39` — villager×4, wolf×2, healer×1,
  investigator×1; validator enforces healer + investigator present.
- **Per-role prompts already exist** (corrects the roadmap's "one prompt for all roles"):
  `Agents/prompts/roles.py` (`ROLE_CORE_STRATEGY`), `Agents/prompts/day.py` (per-role discuss/vote),
  `Agents/prompts/night.py`, `Agents/prompts/memory.py` (per-role situation summaries + role lens).
  → Adding a role is **additive** (new strategy block + prompts + dispatch branch + namespace), not a
  per-role refactor. Verify what "one prompt" referred to when Q3 is taken up.
- **Night actions:** `Agents/agents.py:1006-1018`; resolution `Agents/nodes.py:464-503`
  (kill fails if `wolves_target == healer_target`).
- **Win/factions** (2): `Agents/nodes.py:585-608` — villagers win iff no wolves; wolves win at parity.
  No solo role / third faction today.
- **Memory namespaces:** `Agents/memory.py:30-92` — `(type, role, action_phase)`.
- **Fan-out (parallel day):** `Agents/nodes.py:88-173`.

---

## Implementation & smoke verification (2026-06-06) — Phase A #2 BUILT

Lean-eval casting implemented and validated end-to-end on `feature-role-set` (13 commits off
`main`, memory-off smoke games). Build sequence: roles+config+9p casting → state → 3-faction
win conditions → multi-kill night resolution → relaxed voting → SK/vigilante night actions →
SK/vigilante day participation → memory lens/situation prompts → metrics+runner. Then two
post-smoke fixes and two prompt corrections (below).

### Locked rules as built
- **Win rule** (W=wolves, T=town incl. vigilante, S=SK 0/1), checked after each resolution:
  TOWN `W==0 & S==0`; SK `S==1 & (T+W)<=1`; WOLVES `S==0 & W>=T`; else continue; `max_days=12`
  survivor-majority draw backstop. `determine_winner()` in `Agents/nodes.py`.
- **SK**: solo, night-immune (silent whiffs — never announced, to protect its cover), kills any
  survivor every night (compulsive). Faction tracked by `serial_killer_player`; lives in the
  non-wolf `surviving_villagers` bucket (no separate list).
- **Vigilante**: town, 2 bullets, `hold_fire` sentinel, no guilt. Shooting the immune SK doesn't
  kill but yields a private, reliable SK confirmation (`vigilante_results`; a heal-stopped shot
  does NOT false-positive).
- **Relaxed voting**: `abstain` sentinel; `no_lynch_streak`; forced day at K=2.
- **Night order (two-group model)**: killers (wolves/SK/vigilante) + healer act first →
  KILL_RESOLUTION → investigator runs only if it survived the night AND the game isn't decided →
  NIGHT_FINALIZE (records investigation, emits one metric span/night).
- **Deaths** announced with attacker TYPE (killed by the wolves / stabbed by the serial killer /
  shot by the vigilante), never attacker identity.

### Reproduce
Use the py3.11 venv binary (poetry mis-resolves to 3.10):
`~/.cache/pypoetry/virtualenvs/werewolf-game-v7lKgM40-py3.11/bin/python`
```
<py3.11> scripts/run_batch.py --configs all_disabled --runs-per-config 1 \
    --no-memory-seed --no-memory-dump --session-prefix roleset_smoke --output evidence/role_set/smoke_run.jsonl
```
(9-player casting is the new `DEFAULT_GAME_CONFIG`; memory-off → no embeddings. Two games can run
as parallel processes — no shared store. Artifacts: `evidence/role_set/smoke_run*.{jsonl,log}`.)

### Results — 3 memory-off games, all `status=success`, 0 errors
| game | winner | days | notes |
|---|---|---|---|
| smoke3 | serial_killer | 4 | SK outlasts to a 1v1 vs vigilante (win rule verified by hand) |
| smoke_a | wolves | 4 | vigilante double-targeted & killed night 1; multi-attacker attribution |
| smoke_b | wolves | 5 | abstain vote fired; healer claimed then died; investigator leaked & mislynched |

Mechanics exercised live: 3-faction win incl. an SK victory; 0–3 deaths/night with attacker-typed
attribution; healer saves; SK night-immunity (silent); `abstain` plurality; SK-confirmation path
in place; `compute_metrics` ran on every winner (incl. SK) without error; parallel runs, no 429s.

### Key findings
- **GAME_PREAMBLE fix is a clear win.** Before: agents were never told the SK/vigilante exist (old
  8-player 2-faction preamble) → town ignored "stabbed by the serial killer" announcements, 0 SK
  mentions. After: 15 and 9 player messages reason about the SK as a distinct threat.
- **Vigilante is consistently passive (baseline).** It explicitly holds fire ("I still have my
  bullet and will wait for a clear opening") and dies with bullets unused — 0 vigilante kills in 3
  games. This is the neutral-prompt baseline for the memory A/B to improve, NOT a prompt bug; we
  deliberately did not prompt-steer aggressiveness.
- **Investigator is fragile** — died early in all 3 games (mislynch on an info-leak, or wolf kill).
  Recurring; a candidate behavior for memory to address.
- **Village looks wolf-leaning at N=3** (0/3 village wins). Deliberately NOT balanced: the keystone
  A/B measures a difference, so absolute win rate doesn't bias it. Only SK *headroom* matters →
  confirm in the baseline batch, not at N=3. Reserved levers if needed: SK every-other-night
  (config) or drop SK immunity (both trade against keystone density / clean endgame).

### Deferred to Phase A #3 (consolidated tracing / eval pass)
- Dense per-role SK/vigilante metrics (raw data already logged in `NightResolutionMetric`:
  per-attacker targets/roles, landed flags, faction snapshot).
- `run_batch` output doesn't serialize per-night targets / `vigilante_bullets` / `vigilante_results`
  → can't see night decisions from the JSONL (they're in Langfuse spans). Surface them.
- Orphan-trace bug: `day_resolution`/`night_finalize` emit standalone 1-observation Langfuse traces
  (manual spans not nested under the game/CallbackHandler trace) → nest under the game/session.
- Baseline batch (~10–20 games) for the SK-headroom sanity check.
