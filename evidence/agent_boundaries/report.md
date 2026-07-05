# Agent Information Boundaries

**Scope:** how the harness guarantees each agent's prompt contains only what its role may know —
where that boundary is enforced, how it's verified, and the regression that proved the model real.
**First written:** 2026-06-06 · **Branch:** `feature-tracing` (`ef43342`, `8008623`, `e9d30ba`;
fingerprint/pin context in `31b2e8e`/`fcf0846`).
**Artifacts (raw run logs — the proof behind §4):** `leakwire_smoke.log` (pre-fix; the 109 `LEAK:`
lines are the signal, the rest is Langfuse/deprecation noise) · `leakfix_smoke.log` (post-fix; the
proof is the *absence* of `LEAK:` lines between `=== Running Leak Tests ===` and `=== Complete ===`,
plus `EXIT: 0`) · JSONL records in `batch_results/leak{wire,fix}_smoke.jsonl`.

> **Orientation — the prompt-assembly pipeline.** Every agent prompt is built along one path:
>
> **game state → `Send` payload → prompt-input dict → rendered prompt → model**
>
> Those four arrows are the four boundary layers in §2. Isolation is only as strong as the
> *narrowest* arrow — and, crucially, **only the second one narrows.** Every identifier below
> (`build_speaker_send`, `_run_agent`, `prompt_log`, `output_key`) hangs somewhere on this path.

---

## 1. The guarantee (current contract)

Werewolf is a hidden-information game, so the contract is: **each role's prompt contains only what
that role is allowed to know — enforced at payload construction (layer 2), continuously verified at
the data layer.**

**What is private** (field → its single legitimate consumer):

| Private field | Sole consumer |
|---|---|
| `surviving_wolves` / `surviving_villagers` (the wolf roster) | wolf nodes only |
| `wolf_channel` (night coordination) | wolf night nodes only (`output_key wolf_channel`) |
| `investigator_results` | investigator only |
| `vigilante_results` (SK-confirmation shot feedback) | vigilante only |
| `healer_target` | nobody's prompt, ever |

**Where it's enforced:** the `Send(...)` payload builders (layer 2) decide what data physically
reaches a node. Nothing downstream narrows — layers 1, 3, and 4 all forward or only incidentally
filter (§2) — so the payload is the *only* place the guarantee can live. Two payload-shaping
decisions carry the guarantee: SK/vigilante payloads use the role-blind `surviving_players` (never
the wolf-visible roster), and the wolf night fan-out iterates `surviving_wolves` only.

> *Game-scoping, not a leak boundary:* `WolfDayState` also carries no `wolf_channel`, so wolves
> can't cite night coordination during the day. That keeps night talk out of public day reasoning,
> but it is a **design-scoping** choice, not a cross-role isolation guarantee — `wolf_channel` is the
> wolf's own information, so giving it to a wolf would not be a leak. No leak check enforces it.

**How it's verified:** six `check_*` invariants run on **every batch game**, auditing the
prompt-input dict (one layer upstream of rendering) and exiting non-zero on any violation (§3).

**The rule, quotable:** *enforce at construction, verify continuously at the data layer.*

What this contract does **not** yet cover is collected in §5.

## 2. The boundary model — four layers, one enforcer

Knowing *which* layer enforces is the whole point. Three of the four only document or tolerate; one
rejects.

| # | Layer | What it does | Enforced at runtime? |
|---|---|---|---|
| 1 | **Graph-state TypedDicts** (`Agents/state/` pkg — `WolfDayState` in `state/day.py`, `HealerNightGraph` in `state/night/healer.py`, …) | Document which fields each role's node should see | **No.** LangGraph hands a `Send`-dispatched node the raw payload dict; undeclared keys are not stripped. Documentation only. *(Specific to the `Send` path: a compiled subgraph-as-node **does** filter inputs to its declared input schema — but these role nodes are `Send`-dispatched, so that filtering never applies here.)* |
| 2 | **Payload construction** (`Send(...)` builders in `Agents/nodes/` — day: `nodes/day/flow.py` (`build_speaker_send`, `fan_out_day`); night: `nodes/night/` (`wolf_fan_out` + night fan-outs)) | Decide what data is physically present in a node's payload | **Yes — this is the real boundary.** If private data isn't in the payload, nothing downstream can expose it. |
| 3 | **Prompt-input formatting** (`Agents/prompts/prompt_inputs.py::build_agent_prompt_input`) | One superset formatter for all roles: emits *every* standard key with safe defaults/sentinels, forwarding whatever the payload contains | **No — deliberately permissive.** It widens, never narrows. |
| 4 | **`ChatPromptTemplate` placeholders** (`Agents/prompts/*.py`) | Each template interpolates only its declared `{placeholders}`; surplus input keys are silently ignored (LangChain errors on *missing* variables only, never extra) | **Incidental.** A rendering filter, not a guard: protection equals "which placeholders this template happens to declare," spread across ~20 templates and re-decided on every prompt edit. |

The consequence: an isolation guarantee may rest **only** on layer 2. Layers 1 and 3 forward
whatever they're handed; layer 4's filtering is an accident of which placeholders a template
declares. Lean on any of the three and the boundary holds only until the next refactor — which is
exactly what §4 is.

*Framework note: the LangGraph/LangChain behaviors asserted here and in §4 — `Send` delivers the
payload verbatim, a compiled subgraph-as-node filters to its input schema, templates ignore surplus
keys and error only on missing ones — are described against the pinned version in the runtime
fingerprint (header). A reader on another version should re-confirm before relying on them.*

## 3. How we verify — the leak checks

`tests/leak_test.py` — six `check_*` functions over the per-game `prompt_log` (the global in
`Agents/turn/decision.py` that `_run_agent` appends every agent LLM call's `prompt_input` to). **All**
agent decision calls route through `_run_agent` — including the memory-informed day/night wrappers —
so coverage is total. Driven by `run_leak_tests(prompt_log, roles)`.

| Check | Invariant |
|---|---|
| `check_wolf_identity_isolation` | Non-wolf prompt inputs carry no `surviving_wolves` / wolf names |
| `check_wolf_channel_isolation` | `wolf_channel` content only in entries with output_key `wolf_channel` |
| `check_investigator_results_isolation` | Investigation results only in investigator entries |
| `check_vigilante_results_isolation` *(added 2026-06-06, `8008623` — the checker set predated the 9p roster)* | Shot feedback only in vigilante entries |
| `check_healer_target_absent` | `healer_target` in no prompt input at all |
| `check_eliminated_players_excluded` | Dead players get no prompts (currently a no-op as wired — no `eliminated_players` passed) |

**Audit the data layer, not the presentation layer.** The checks inspect the **prompt-input dict
(layer 3 output)**, not the rendered prompt.

A subtlety the DRY superset formatter forces: since layer 3 emits *every* private key for *every*
role (§2), the key is always *present* — so the checks key on the **value, not the key's presence**.
Missing private data defaults to an empty value or a sentinel (`"No investigations yet."`,
`"No messages yet."`, `"Nothing learned from your shots yet."`); a check fires only on *real* content
(a non-empty roster, a non-sentinel result string). And the only way real content reaches the dict is
if the **layer-2 payload carried it** — layer 3 just forwards `payload.get(field, default)`. So a
non-default value ⟺ the payload boundary was crossed.

A flag therefore means "private data crossed the payload boundary," which may or may not have
*rendered* — that is the separate layer-4 question of whether the role's template declares the
`{placeholder}` — but it is always a violated invariant and always one template edit from real
exposure. Auditing one layer *upstream* of where exposure becomes visible is what turned a latent
regression into an early warning (§4) rather than a silent time bomb.

**Wiring (`e9d30ba`):** `run_batch` runs the checks after every successful game (`run_game` clears
`prompt_log` at start, so the global holds exactly that game's prompts), records the verdict in each
JSONL record as `leak_check: {passed, leaks}`, prints `LEAK DETECTED` per game, and exits non-zero if
any game leaked — while still writing the game result. Before this, the checks ran only when someone
executed a notebook cell. That gap is the regression's enabling condition.

## 4. Case study — the 109-flag regression (2026-06-06)

A convenience refactor in the sequential rewrite shipped a superset payload that put private fields —
wolf identities, investigator results, and vigilante shot-feedback — into the prompt inputs of roles
that shouldn't see them, and the first wired run of the leak checks flagged **109 violations**
(`leakwire_smoke.log`). None of it reached a model: layer 4 (template placeholders) dropped every
contaminated field, confirmed by
exhaustive grep. So no past game result is tainted — and directionally the leak would have *helped*
the village, never the wolves. Role-gating the payload at layer 2 (`ef43342`) fixed it; the post-fix
run flags 0 with all six checks active.

*The rest of this section is the forensic detail behind that verdict — skip by subhead (Cause /
Composition / Vote path / Timeline / Severity / Fix / Verification) if the verdict is all you need.
This is also the incident that proved the §2 model: a layer-2 violation that every permissive layer
forwarded silently, caught only at the data layer.*

**The cause — a layer-2 violation built on a misread of LangGraph.** The 109 trace to one root: the
sequential rewrite's `build_speaker_send` dispatched a **universal superset payload** to every
speaker, justified in its own docstring by "LangGraph ignores extra keys on a Send payload."

That rationale is a misread of *where* LangGraph actually enforces a schema. Its input-schema
filtering is real but narrow — it applies to typed state channels and to **parent→child
compiled-subgraph boundaries** (a compiled subgraph filters its input to its declared schema). The
author generalized that to the `Send`-into-a-node path, where it does **not** hold: `Send` delivers
the payload verbatim to the destination node, the node's `TypedDict` annotation enforces nothing at
runtime (§2, layer 1), and `_run_agent` then builds the prompt-input dict straight from that payload.
So the claim was true of a boundary that wasn't on this path and false of the one that was. **The
documented justification was the bug** — and layers 1, 3, and 4 all forwarded the contraband
silently, exactly as the §2 model predicts.

**Composition of the 109 — flag events, not distinct inputs.** The count is leak-check *flag lines*,
not contaminated prompt inputs (the superset handed each input everything, so one input trips
multiple checks):
- **76** wolf-identity flags — `check_wolf_identity_isolation` emits two lines per contaminated input
  (one for the `surviving_wolves` field, one for the extracted names): **38 non-wolf inputs × 2**.
- **33** `investigator_results` flags (33 non-investigator inputs).
- **76 + 33 = 109.**

**Vote path too — and a third field outside the 109.** `vigilante_results` was *also* leaking, but
contributed **0** to the 109 because **no checker covered it yet** (`check_vigilante_results_isolation`
was added afterward, `8008623`). Found by inspection, it leaked through **two** builders: the
`build_speaker_send` superset (discussion turns) **and** `fan_out_day`'s base payload (to **every
voter**). So the contamination was *not* discussion-only — wolf-identity and investigator-result
leaks were discussion-turn artifacts of the superset, but vigilante shot-feedback additionally
reached the vote path.

**How it persisted (timeline).** The checkers were correct and present the whole time; they simply
weren't in the execution path.
- **May 9** — checkers written against the concurrent-era day fan-out (role-filtered payloads). Passing.
- **June 3–4** — Phase A #1 sequential rewrite introduces `build_speaker_send` and the superset
  payload. Checks ran only in a notebook, so nothing fired.
- **June 6** — checks wired into `run_batch`; first live game flags the 109.

**Severity — nothing rendered, on either path.** Exhaustive grep confirmed the private placeholders
render only in role-matched templates (`{surviving_wolves}`: wolf day-discuss/vote, wolf night, wolf
situation-summary; `{investigator_results}`: investigator templates; `{vigilante_results}`: vigilante
templates). Layer 4 silently dropped the contraband for every contaminated prompt — discussion **and**
vote. Two consequences: (a) all game results to date are unaffected — win patterns (wolf/SK wins) are
genuine dynamics, not leak artifacts; (b) directionally, even worst-case, the wolf-identity leak —
had it rendered — would have **helped the village** (handing wolf identities to town roles), not the
wolves.

**Fix (`ef43342`).** `build_speaker_send` now attaches private fields role-gated (wolves → roster;
investigator → results; vigilante → shot feedback; everyone else none), and `fan_out_day` no longer
puts `vigilante_results` in its base payload. The two builders were corrected in the same change, so
they now agree on the role-gated shape; the docstring was rewritten to state the invariant and why a
superset is unsafe — i.e. the layer-2 enforcement the §2 model demands.

**Verification.** Post-fix live game with all six checks active (`leakfix_smoke.log`):
`=== Running Leak Tests ===` → 0 flags, `leak_check: {passed: true, leaks: []}`, batch exit 0; test
suite 27 passed. Both smoke records carry the runtime fingerprint
(`evidence/prompt_versioning/`), so they're self-describing.

**Lessons.**
- **A boundary that doesn't reject isn't a boundary.** State schemas and `ChatPromptTemplate` both
  tolerate surplus data silently; any security-shaped invariant resting on a permissive layer is
  violated eventually, without an error. Enforce at construction; verify continuously.
- **"Harmless extra keys" must be checked against every consumer.** The superset rationale was right
  for the graph and wrong for the prompt pipeline reading the same dict — the documented
  justification *was* the bug.
- **Checks that don't run every execution decay into false confidence.** Three days of "it passed
  last time someone ran it."
- **Audit at the data layer, not the presentation layer.** Checking prompt *inputs* flagged a
  violation the rendered prompts would have hidden — that asymmetry is the early warning.

## 5. Known gaps — what isn't guaranteed yet

The second half of the §1 contract: where the boundary is *not* yet enforced or verified. Ordered by
criticality, defined across three axes — **is there a path by which private data reaches a model, how
likely is it today, and would the §3 checks catch it?** (HIGH = a *live* exposure path the checks can't
see; **medium–high** = structurally prevented today but unverified and invisible to the checks if the
structure ever breaks; medium = a real path the live checks *do* catch, but only late/expensively;
low = can't reach a model, already caught, or redundant/cosmetic.)
A gap stays on this list even when minor — the value of the list *is* the audit trail, so low
criticality earns a shorter entry, not deletion. Each carries a freshness date so a later reader knows
whether to trust it or re-confirm.

### Memory-retrieval cross-role boundary — criticality: medium–high

- **Gap.** Retrieved observations / strategy points are fetched from role-keyed namespaces —
  `("observations", role, action_phase)` / `("strategy_points", role, action_phase)`
  (`Agents/memory/retrieval/accessors.py:26,56`), where `role` is the requesting agent's own. So the
  boundary is **enforced by construction** (you can only query your own namespace) but — exactly like
  the layer-2 payload boundary before the §4 checks — **not independently verified**. And it's *worse*
  than the payload case: the §3 checks key on *structured* fields, so they are blind to free-text
  memory; a refactor that passed the wrong `role` would leak another role's memory **silently and
  undetected**. (It also isn't enumerated in the §1 contract — that omission is itself part of the gap.)
  The exposure is therefore **latent** — gated on a future refactor breaking the keying, not open
  today — which is why this rates *medium–high*, not HIGH: high impact and zero detectability, but low
  present likelihood. The gap is verification and refactor-resistance, not a live hole.
- **Considered solution.** Add the retrieval boundary to the §1 contract, and add a namespace-isolation
  assertion in the retrieval path (the requesting role == the namespace served) as a per-game check —
  the §3 set's memory-pipeline analogue, since the existing checks can't see this channel.
- **Status — open, verified 2026-06-24.** Previously framed as "add it during the v5 DB rebuild." That
  rebuild has since shipped (the live store is now `v6_1`) **without** the assertion, so this is now a
  standalone TODO, no longer gated on a future rebuild — and the window it was meant to ride is closed.

### Fast unit regression for payload gating — criticality: medium

- **Gap.** The only thing enforcing the §4 fix today is the live leak check (~$0.15/game, batch-only).
  A re-introduction is caught only when someone runs a full game.
- **Considered solution.** A pure unit test calling `build_speaker_send` / `fan_out_day` (now in
  `Agents/nodes/day/flow.py`) per role and asserting private keys are absent from the payload — catches
  re-introductions in CI for free. Payloads are `TypedDict`s, so this is an explicit assert-absent
  test; a Pydantic `extra='forbid'` model would be the *structural* alternative only if the payloads
  were converted to Pydantic (they aren't today).
- **Status — open, verified 2026-06-24.** No test references the builders.

### Lower-criticality (tracked, not yet closed — all verified open 2026-06-24)

- **Rendered-prompt audit (layer-4 verification).** A Langfuse spot-check that wolf-only rendered
  phrases ("Your wolf allies:", "Known surviving wolves:") never appear in non-wolf inputs would verify
  the last layer end-to-end. Belt-and-suspenders — the §4 case already grep-confirmed non-rendering — so
  worth one run per major prompt rework, not standing CI.
- **`check_eliminated_players_excluded` runs but is unfed.** The checker now has logic and accepts an
  `eliminated_players` arg, but `run_batch` calls `run_leak_tests` with the default empty set, so it's
  still effectively a no-op. Thread the eliminated set (with elimination days, from `day_channel` GM
  messages) to activate it. Low risk — dead players already aren't scheduled, so this is a redundant
  assertion rather than a live hole.
- **`prompt_log` only captures `_run_agent` calls.** Situation-summary generation
  (`_build_agent_prompt_input`'s second call site) still doesn't append (sole append:
  `Agents/turn/decision.py`), so it's invisible to the checks. The layer-2 fix covers it (same payload), so
  this is a checker-*visibility* gap, not an active leak; folding it into the log would close it.
