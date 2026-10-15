# Information fidelity audit — 2026-10-03

Read-only review of agent code at `76ce221`. No gameplay/prompt changes and no paid model calls.
Scope: engine events → graph payloads → prompt rendering → summaries/private notes → extraction.
“Confirmed” below means a code path or information omission was verified, not that its effect on
hallucination frequency has been measured. Behavioral hypotheses require replay or live validation.
This is a new audit record, not a revision of earlier experimental results.

## Highest-priority findings

### 1. The healer has no durable, exact record of its own protections

**Confirmed omission; high behavioral risk.** `Agents/graphs/parent.py:151` builds the healer's
night payload without past targets. `Agents/nodes/day/flow.py:132` and `:209` likewise supply no
healer action history. `Agents/state/orchestrator.py` holds a current `healer_target`, reset by
`Agents/nodes/orchestrator.py:289`; private strategy prose is the only general cross-turn memory.
Public announcements reveal successful saves but not unattacked protection choices.

Consequently, a truthful healer cannot reliably answer “whom did you protect on night 2?” from
engine facts in its prompt. A strategy note may retain this information, but is neither complete
nor authoritative. This matters directly for checking another player's protection story.

Vigilante history is incomplete too: `Agents/nodes/night/resolution.py:123` appends private results
only for immune targets. Ordinary shots, held fire and healer-blocked shots do not enter a complete
private action ledger. SK past choices similarly rely on prose/public outcomes.

**Proposed fix:** actor-private, engine-written action history with night, chosen target, and only
the outcome the actor is allowed to know. Do not disclose unrelated attackers or hidden roles.
Test both an unattacked healer target and a target attacked by several factions.

### 2. Suppressed speech can survive as a private belief that it was spoken

**Confirmed pathway; downstream behavioral effect unmeasured.** In
`Agents/turn/resolve.py:124`, novelty rejection hides the message but returns the original
`TurnEffects`. `Agents/nodes/day/actors.py:101` still persists its strategy note.
`Agents/prompts/prompt_formatters.py:52` hides the rejected message, and the next turn receives no
specific notice that this draft was withheld.

Offline reproduction: stubbed the novelty judge to reject a draft whose strategy was
“I have now publicly revealed my finding.” The resolved action was gated, its public rendering
was “No messages yet.”, but its retained strategy was exactly the claim of disclosure.
This establishes that an erroneous note can survive suppression; it does not measure how often
models actually write such notes.

**Proposed fix:** record private delivery status separately from proposed speech; label previous
strategy as fallible planning, and make actual delivered messages authoritative. Preserve new
private reasoning without treating an unspoken draft as public history.

### 3. Voting drops the private strategy note, then can replace it

**Confirmed omission.** `build_agent_prompt_input` provides `previous_strategy`, and the vote
payload carries it, but `DAY_VOTE_MEMORY_CONTEXT` in `Agents/prompts/memory/context.py:80` does not
render it. The vote output nevertheless requests `updated_strategy`; the actor overwrites that
player's prior note in `Agents/nodes/day/actors.py:160`.

A sentinel note was present in a rendered healer discussion prompt and absent from its vote
prompt. Thus information remembered only in the note can disappear at the discussion→vote→night
boundary. Investigator results and wolf chat have separate input channels and are not lost this way.

**Proposed fix:** supply the previous note when asking for its update, and separate exact private
facts from the revisable strategy prose. Adding the note alone can also propagate existing errors;
give it explicitly lower authority than engine records.

### 4. The summary is asked to assess corroboration without authoritative context

**Confirmed input limitation.** `Agents/nodes/day/flow.py:285` supplies only today's non-moderator
messages. `Agents/nodes/day/summary_agent.py:34` supplies neither earlier summaries nor the dead
roster/public night records. Yet `Agents/prompts/extraction/day_summary.py:19` asks it to distinguish
death-confirmed roles and publicly corroborated claims.

It cannot reliably check a speaker's account of yesterday's save, death or vote from those inputs.
The risk is converting a second-hand story into apparent corroboration, especially for statements
like “we already established this yesterday.”

**Proposed fix:** either summarize assertions strictly as assertions, or supply the relevant
engine-written public evidence for corroboration. Do not give the summary hidden role mappings.

### 5. Public facts and model summaries lose their different authority when rendered

**Confirmed representation gap.** Engine vote/night announcements and model-generated discussion
summaries are all stored as `DaySummary`. `Agents/prompts/prompt_formatters.py:63` renders each as
`[Day N]` plus prose, without a source/type label. The structured fields are not consumed by players.

This does not delete the engine announcements: they are retained alongside the summaries. But a
false statement in the summary and a contradictory engine event have no explicit hierarchy in
the rendered section. An offline rendering confirmed both receive identical day headings.

**Proposed fix:** distinguish engine public events from attributed discussion summaries. Exact
events outrank paraphrases; a repeated accusation does not become an engine fact.

## Additional confirmed inconsistencies and omissions

### 6. Healer-save confirmation remains misstated in shared epistemic instructions

`Agents/prompts/standards.py:64` places “healer save announcement” under “role revealed by game
mechanics.” A save confirms an attack/protection event, not the saved player's role. The day-summary
prompt has the newer explicit correction, but this shared block is still used by situation-query
and extraction prompts (`Agents/prompts/memory/situation_summary.py`).

**Fix:** distinguish event confirmation from role confirmation consistently across prompts.
Replay a saved wolf; verify retrieval/extraction does not turn it into confirmed town.

### 7. The wolf-facing “villagers” list includes the serial killer

`Agents/nodes/orchestrator.py:310` documents `surviving_villagers` as the non-wolf bucket, including
SK. `Agents/prompts/day_discuss.py:240` and both wolf night templates nevertheless label it
“Surviving villagers.” This is an ambiguous faction label, not a private-role leak.

**Fix:** label the rendered list “living non-wolf players (town or serial killer)” without revealing
which player is SK. Renaming the entire internal state field is not necessary for the prompt fix.

### 8. Wolf night omits the structured public death/census blocks

`Agents/graphs/parent.py:121` and `Agents/nodes/night/wolf.py:94` omit the dead roster and cast
counts; `WOLF_NIGHT_DISCUSS` and `WOLF_NIGHT_VOTE` omit their rendered blocks. Other night roles
receive them. Template-variable inspection confirmed both wolf templates lack `dead_roster` and
`alive_roles`. Wolves can still reconstruct deaths from public history, but lose the deterministic
aid specifically introduced to avoid that reconstruction.

**Fix:** provide the same public census to wolf night. Never substitute hidden live-role identities.

### 9. Vigilante daytime prompts omit remaining bullets

Day payloads carry `vigilante_bullets`, but `Agents/prompts/day_discuss.py:266` and
`Agents/prompts/day_vote.py:157` render only the private shot-result prose. Zero bullets therefore
need not be visible in a discussion about taking a shot tonight. The night prompt does include
the counter, and night routing skips the vigilante when empty.

**Fix:** render remaining bullets in day discussion/voting too. Offline template inspection
confirmed the omission; test a zero-bullet claim of future shooting.

### 10. The healer's stated protection mechanics are incomplete

`Agents/prompts/night.py` and the healer playstyle describe protection against wolves or SK.
`Agents/rules/resolution.py:38` actually saves a protected non-immune target from any collected
attack, including the vigilante, and from multiple attacks on the same night. Offline kernel check:
vigilante-only attack + matching healer target → `saved`.

**Fix:** explicitly state protection covers all night attacks on the chosen player, subject to the
actual precedence rules. This is not evidence that players currently get every such inference wrong.

### 11. Claim revisions and attribution lack durable structured slots

`Agents/schemas/output.py:174` models an accusation as accusers/target/reasoning/defense and a role
claim as player/role/evidence. There is no required result target/night, source message, retraction,
or assertion status. `summary_agent.py:59` serializes these into prose. Revisions can be retained
in prose, but the schema does not require it or support reliable contradiction joins.

**Fix:** add narrow provenance/revision fields when building the claim ledger. Do not infer that
all existing summaries lose revisions; that needs a fidelity census on source messages.

### 12. Post-game extraction is not supplied a full private action ledger

`Agents/memory/extraction/inputs.py:70` constructs its evidence from the public transcript, wolf
chat, investigator results and final strategy notes. It omits exact healer/SK/vigilante action
histories and vigilante private result records. These may exist in runtime metrics/eval artifacts,
but are not provided by this builder. Omniscient framing in extraction prompts overstates the
actual input completeness. The extractor can infer a plausible night tactic without seeing the
actor's exact choice, and may treat a final strategy note as an accurate account of earlier play.

**Fix:** feed explicitly labeled post-game action/outcome records, including held actions and
undelivered results. This is allowed after the game; do not reuse that omniscient input in play.
Keep factual reconstruction separate from the already-diagnosed hindsight/credit problem.

## Lower-confidence risks worth focused replay, not automatic rewriting

- The novelty judge says reinforcement without a new angle is not novel
  (`Agents/turn/novelty_agent.py:30`). It has no explicit independent-corroboration exception.
  A second witness could be suppressed. Test the paired examples “I agree” versus “I independently
  observed the same visit.” This is already anticipated by scheduler plan S3.
- JSON examples repeatedly name `player_2` as a suspected wolf with a concrete invented rationale.
  These are intended format examples, but contamination into live reads is possible. Test equivalent
  templates with neutral examples rather than claim it is an established cause.
- `PlayerRead.why` permits “unchanged,” but reads are only logged, not carried as a structured
  player belief state (`Agents/turn/eval.py:39`). No full prior read map is supplied on the next turn.
  The private note can preserve some beliefs; it cannot reliably preserve every read/evidence link.
- Free-form private notes are recursively rewritten in 3–5 sentences, with no source references or
  requirement to retire disproven beliefs. They can retain a disproven premise after public correction.
  Carrying them into voting should be coupled with the authority distinction in finding 3.

## Previously identified issues and checks against false alarms

- “Voted for” remains in `Agents/nodes/orchestrator.py:214`; the requested unambiguous wording is
  not yet applied in this revision.
- The canonical rules do not explicitly describe silent immune attacks, although wolf daytime
  prompts already mark the wolf channel private and forbid referencing it publicly. The problem is
  not a total absence of a private-channel warning.
- Investigator result wording already names the actual night and the actor's own investigation;
  do not report the old “revealed as” wording as a current bug.
- Day-summary exclusion of today's summaries does not deprive night agents of today's vote:
  day resolution also appends the vote announcement to today's `day_channel`, which night prompts read.
- Private investigator results and wolf chat are gated by role in the reviewed day payload builders.
  This audit found semantic/provenance issues, not proof of an unrestricted hidden-role leak.
- Hidden/gated messages are intentionally excluded by player-facing formatters. The concern in
  finding 2 is the retained private note, not raw rejected speech leaking into everyone else's prompt.

## Recommended order and verification

First: exact private action histories; gated-message delivery feedback; vote-note continuity;
public-event versus claim provenance. These address missing or contradictory evidence directly.
Then: shared healer semantics, wolf roster labels/night census, and daytime ammunition display.
Only after these bounded corrections consider broader board-only prompt experiments.

Offline checks performed: rendered sentinel-note presence across discussion/vote; inspected actual
wolf/vigilante template variables; rendered equal-labeled model/engine summaries; exercised healer
resolution against a vigilante attack; forced novelty suppression and verified retained strategy.
No generated-game or hallucination-rate claim is made by these checks.

Existing focused regression suite: **31 passed** with
`poetry run pytest -q tests/engine/test_night_whiff_disclosure.py tests/engine/test_night_resolution_investigator.py tests/engine/test_discussion_prompt_flag.py tests/engine/test_wolf_night_sequential.py`.
These passing tests cover existing behavior; they do not invalidate the uncovered omissions above.
