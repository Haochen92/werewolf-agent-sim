# Agent Information Boundaries: Leak Checks, Graph State, and What They Caught

**Date:** 2026-06-06
**Branch:** `feature-tracing` (commits `ef43342`, `8008623`, `e9d30ba`; fingerprint/pin context
in `31b2e8e`/`fcf0846`)
**Artifacts:** `leakwire_smoke.log` (pre-fix game, 109 flags), `leakfix_smoke.log` (post-fix game,
0 flags); JSONL records in `batch_results/leakwire_smoke.jsonl` / `leakfix_smoke.jsonl`.

---

## 1. The boundary model: what the system has in place

Werewolf is a hidden-information game, so the harness must guarantee each agent's prompt contains
only what its role is allowed to know. There are four layers between game state and a model's
context window. Knowing which ones actually *enforce* is the point of this document:

| # | Layer | What it does | Enforced at runtime? |
|---|---|---|---|
| 1 | **Graph-state TypedDicts** (`Agents/state.py` — `WolfDayState`, `HealerNightGraph`, …) | Document which fields each role's node should see | **No.** LangGraph hands a `Send`-dispatched node the raw payload dict; undeclared keys are not stripped. Documentation only. |
| 2 | **Payload construction** (`Send(...)` builders in `Agents/nodes.py`: `build_speaker_send`, `fan_out_day`, `wolf_fan_out`, night fan-outs) | Decide what data is physically present in a node's payload | **Yes — this is the real boundary.** If private data isn't in the payload, nothing downstream can expose it. |
| 3 | **Prompt-input formatting** (`Agents/prompt_inputs.py::build_agent_prompt_input`) | One superset formatter for all roles: emits *every* standard key with safe defaults/sentinels, forwarding whatever the payload contains | **No — deliberately permissive.** It widens, never narrows. |
| 4 | **`ChatPromptTemplate` placeholders** (`Agents/prompts/*.py`) | Each template interpolates only its declared `{placeholders}`; extra input keys are silently ignored (LangChain errors on *missing* variables only, never surplus) | **Incidental.** A rendering filter, not a guard: protection equals "which placeholders this template happens to declare," distributed across ~20 templates and re-decided on every prompt edit. |

Private fields and their single legitimate consumer:

- `surviving_wolves` / `surviving_villagers` (the wolf roster) → wolf nodes only (`{surviving_wolves}` renders only in WOLF_* templates + the wolf situation-summary template)
- `wolf_channel` (night coordination) → wolf night nodes only (`WolfNightState`; output_key `wolf_channel`)
- `investigator_results` → investigator only
- `vigilante_results` (SK-confirmation shot feedback) → vigilante only
- `healer_target` → nobody's prompt, ever

Layer-2 corollaries the design relies on: `WolfDayState` has **no** `wolf_channel` (wolves can't
cite night talk in day discussion), SK/vigilante payloads use role-blind `surviving_players`, and
the wolf night fan-out iterates `surviving_wolves` only.

## 2. What the leak checks verify

`tests/leak_test.py` — six `check_*` functions over the per-game `prompt_log` (the global in
`Agents/agents.py` that `_run_agent` appends every agent LLM call's `prompt_input` to; **all**
agent decision calls route through `_run_agent`, including the memory-informed day/night wrappers,
so coverage is total). Driven by `run_leak_tests(prompt_log, roles)`.

| Check | Invariant |
|---|---|
| `check_wolf_identity_isolation` | Non-wolf prompt inputs carry no `surviving_wolves` / wolf names |
| `check_wolf_channel_isolation` | `wolf_channel` content only in entries with output_key `wolf_channel` |
| `check_investigator_results_isolation` | Investigation results only in investigator entries |
| `check_vigilante_results_isolation` *(added today — checker set predated the 9p roster)* | Shot feedback only in vigilante entries |
| `check_healer_target_absent` | `healer_target` in no prompt input at all |
| `check_eliminated_players_excluded` | Dead players get no prompts (currently a no-op as wired — no `eliminated_players` passed) |

**Deliberately conservative layer choice:** the checks inspect the **prompt-input dict (layer 3
output)**, not the rendered prompt. A flag therefore means "private data crossed the payload
boundary," which may or may not have rendered — but it is always a violated invariant and always
one template edit away from real exposure. This conservatism is exactly what made today's catch
possible.

**Wiring (new today, `e9d30ba`):** `run_batch` runs the checks after every successful game
(`run_game` clears `prompt_log` at start, so the global holds exactly that game's prompts),
records the verdict in each JSONL record as `leak_check: {passed, leaks}`, prints `LEAK DETECTED`
per game, and exits non-zero if any game leaked — while still writing the game result. Before
today the checks only ran when someone executed a notebook cell; they had not run since the
sequential rewrite.

## 3. What it caught (first wired run)

**Timeline of the regression:**

- **May 9** — checkers written against the concurrent-era day fan-out, which role-filtered
  payloads. Passing.
- **June 3–4** — Phase A #1 sequential rewrite introduces `build_speaker_send`, which dispatched a
  **universal superset payload** to every speaker. Its docstring justified this with "LangGraph
  ignores extra keys on a Send payload" — true at layer 1, irrelevant at layer 3, where
  `_run_agent` builds the prompt-input dict straight from the payload. The vote path
  (`fan_out_day`) stayed correctly filtered, so contamination was discussion-turns only. Checks
  never ran (notebook-only), so nothing fired.
- **June 6** — checks wired into `run_batch`; **first live game flags 109 violations**
  (`leakwire_smoke.log`): wolf identities in 38 non-wolf prompt inputs (healer, investigator,
  villagers, SK), investigator results in 33 non-investigator inputs. Plus a third field no
  checker covered: `vigilante_results` handed to *every* speaker and *every* voter in both
  builders.

**Severity triage — no model ever saw any of it.** Verified by exhaustive grep that the private
placeholders render only in role-matched templates (`{surviving_wolves}`: WOLF day-discuss/vote,
wolf night, wolf situation-summary; `{investigator_results}`: investigator templates;
`{vigilante_results}`: vigilante templates). Layer 4 silently dropped the contraband for every
contaminated prompt. Two consequences: (a) all game results to date are unaffected — win patterns
(e.g. wolf/SK wins) are genuine dynamics, not leak artifacts; (b) directionally, this leak
*rendered* would have **helped the village** (it gave wolf identities to town roles), so it could
not have inflated wolf wins even in the worst case.

**Fix (`ef43342`):** `build_speaker_send` now attaches private fields role-gated, mirroring
`fan_out_day` (wolves → roster; investigator → results; vigilante → shot feedback; everyone else
gets none), and `fan_out_day` no longer puts `vigilante_results` in its base payload. Docstring
rewritten to state the invariant and why a superset is unsafe.

**Verification:** post-fix live game (`leakfix_smoke.log`): `=== Running Leak Tests ===` → 0
flags, `leak_check: {passed: true, leaks: []}`, batch exit 0. Test suite 27 passed. Both smoke
records also carry the runtime fingerprint (`evidence/prompt_versioning/`), so they're
self-describing.

## 4. Lessons

- **A boundary that doesn't reject isn't a boundary.** Both LangGraph state schemas and
  `ChatPromptTemplate` *tolerate* surplus data silently. Any security-shaped invariant resting on
  a permissive layer will eventually be violated without an error. Enforce where construction
  happens (layer 2), verify continuously (the wired checks).
- **"Harmless extra keys" claims must be checked against every consumer.** The superset rationale
  was correct for the graph and wrong for the prompt pipeline reading the same dict. The
  convenience refactor shipped with a documented justification — and the justification was the
  bug.
- **Checks that don't run on every pipeline execution decay into false confidence.** The checkers
  were correct and present for the entire regression window; they simply weren't in the path.
  Three days of "it passed last time someone ran it."
- **Audit checks at the data layer, not the presentation layer.** Checking prompt *inputs* flagged
  a violation the rendered prompts would have hidden; that asymmetry is the early warning, not a
  false positive.

## 5. Remaining gaps / future options

1. **Rendered-prompt audit (layer 4 verification).** A Langfuse-based spot check that wolf-only
   rendered phrases ("Your wolf allies:", "Known surviving wolves:") never appear in non-wolf
   generations' inputs would verify the last layer end-to-end. Cheap to script against stored
   traces; worth running once per major prompt rework.
2. **`check_eliminated_players_excluded` is a no-op as wired** (no `eliminated_players` arg).
   Wiring it needs the eliminated set with elimination days from game state — available in
   `day_channel` GM messages; parse or thread through when it matters.
3. **Fast unit regression for payload gating.** The live smoke run costs ~$0.15; a pure unit test
   calling `build_speaker_send`/`fan_out_day` per role and asserting absent private keys would
   catch re-introductions in CI for free.
4. **Memory-retrieval boundary not covered.** Retrieved observations/strategy points flow into
   prompts via store namespaces keyed by role; a cross-role namespace read would be a leak the
   prompt-input checks can't see (the content is free text). v5 DB rebuild is the moment to add a
   namespace-isolation assertion in the retrieval path.
5. **`prompt_log` only captures `_run_agent` calls.** Situation-summary generation
   (`_build_agent_prompt_input` at its second call site) doesn't append to `prompt_log`; it uses
   the same payload, so the layer-2 fix covers it, but it's invisible to the checker. Folding it
   into the log would close the visibility gap.
