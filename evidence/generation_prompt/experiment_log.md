# The generation prompt — evolution of the agent action call

> **What this is.** The chronological record of how the in-game agent action prompt (day discuss /
> day vote / night action) and its structured output schema became what they are: from a flat file
> of hand-written templates with "respond with valid JSON" in prose, through the arrival of memory
> context, the sequential-discussion schema rewrite, the caching investigation whose gameplay half
> died at first measurement, and the chain-of-thought reordering that put deliberation before
> action — ending at the current board-state work (dead roster, alive-roles, suspicion reads).
> Later entries supersede earlier ones; where a design was falsified, the falsification is shown in
> its place rather than edited away.
>
> **This log is a reconstruction.** It was assembled after the fact (2026-07-07, from git history
> and the evidence folders) because the prompt evolved as a side effect of many workstreams and was
> never logged as its own thread. Early-May beats predate the documentation habit and are
> best-effort, marked as such. Beats that have a full record elsewhere are retold here with enough
> of their method and reasoning to follow without leaving the page; the owning folder keeps the
> full detail.
>
> **Companion docs.** The current-state anatomy, stated destination-first, is
> [`docs/generation_prompt.md`](../../docs/generation_prompt.md). The current beat's pre-registered
> test suite is [`validation_plan.md`](validation_plan.md), its results in [`validation/`](validation/).
>
> **Two principles recur through every beat**, so they are worth naming up front. First: **the
> output schema is part of the prompt.** Under Gemini controlled generation the model emits fields
> in schema-declared order, so field order is generation order — a field placed before the action
> is deliberation the model must perform first, and a field placed after it is commentary. Second:
> **every field is required, never nullable**, because the weak game model silently drops optional
> fields. Where each principle was earned is told in place (§3, §4, §7).

---

## 0 · The call, as it stands today (orientation)

Every agent action in a game is **one LLM call**, and every such call is assembled the same way.
The model is flash-lite (weak and cheap), running at temp 1.0. Half the rules in this log exist because of that model choice: a stronger model would
tolerate prose instructions, nullable fields, and UUID keys; flash-lite reliably does not.

The call is built in three stages (the full anatomy lives in the companion doc). A **payload** is
constructed at the graph node — this is the system's only enforced privacy boundary, so an agent
can only ever be prompted with what its payload contains. Formatters in
`Agents/prompts/prompt_inputs.py` turn the payload into named string keys. A fixed per-phase
scaffold slots the keys into the template. The inputs, by group:

| group | keys |
|---|---|
| identity / turn | `player_id`, `player_role`, `current_day`, `firing_brief`, `abstain_instruction`, `vigilante_bullets` |
| public board | `surviving_players`, `dead_roster` (uncommitted), `day_summaries`, `day_channel` (plain `player: message` lines) |
| private (payload-gated) | `surviving_wolves`, `wolf_channel`, `investigator_results`, `vigilante_results`, `previous_strategy` |
| memory | `retrieved_observations` (numbered 1..N), `strategy_points` (numbered, `Action:`-prefixed), `synergy_instruction` (both-arms only), `role_lens` |
| standing instructions | game rules/preamble, role CORE_STRATEGY + threat brief, tone + silence rule (discuss), verdict/adoption instructions |

The **output** side (`Agents/schemas/output.py`) is where the first principle above does its work.
The current generation order:

```
strategy_verdicts        follow / override / not_relevant, one per strategy point
memory_applicability     fully / partly / does_not_apply, one per observation
updated_strategy         the agent's running private notes, fed back next turn
[pass_turn]              discuss only
THE ACTION               message / vote_target / *_target
[addressed_targets]      discuss only
```

Everything before the action is forced deliberation; everything is required; nothing is nullable.
How each of those facts got there — why verdicts exist at all, why silence is a boolean rather
than a null, why the notes come before the vote — is the rest of this log.

## 1 · Origin — hand-written templates, JSON by prose (2026-05-01, `db288e6`)

The first version was a flat `Agents/prompts.py`: per-role `ChatPromptTemplate`s over an 8-player
cast with a concurrent 3-round discussion. The system message was the game preamble, "You are
{player_id}, a {player_role}", a hand-written strategy paragraph, and the sentence *"You must
respond with a valid JSON: {"message": ...}"* — the schema described in prose, with no schema
objects anywhere. The human message carried the day/round, the surviving players, and the chat
history. No memory of any kind.

This was a defensible first cut, not a mistake: it made a playable game in a day, and every
simplification it took — prose JSON, hand-written strategy, one flat file, no memory — was the
cheapest correct choice before there was evidence against it. Every later era of this log replaces
exactly one of those simplifications.

## 2 · Memory arrives, and with it `updated_strategy` (2026-05-09, best-effort)

The adaptive-strategy cluster (`7d04344`/`62d873a`/`df7225b`, +591 lines to `prompts.py`) added
the first retrieved-strategy context blocks and the **`updated_strategy` output field**. The
field is a private chain-of-thought scratchpad, threaded back into the agent's own next prompt as
`previous_strategy`. Without it, every turn was memoryless — an agent could not build on its own
prior thinking within a game. With it, the agent has a private, evolving reasoning space that
serves two purposes: it is a decision aid (reason through the situation before acting) and an
inspectable artifact (what did the agent *think* it should do, versus what it *said* out loud?).
One commit created the field on the output schema, the next added the prompt section telling agents
to update their notes from new information, and the third wired the persistence loop that carries
the notes forward. This field outlives everything around it: it is still the feedback spine of the
schema today, and the model for how the suspicion reads will be fed back (§9). *(Best-effort: the
field was born in `7d04344`, the first of three same-day commits; pre-dating the schemas package.)*

Modularization followed within the week: the `prompts/` package split (`c5c8898`, 05-13), and
`schemas/output.py` was born (`dde8e0a`, 05-14). Prose-JSON gave way to structured output
schemas — the surface every later beat edits.

## 3 · The first ordering discovery — forcing commitment before action (~2026-05-23/24)

The strategy-adoption experiment set out to measure whether agents actually *use* the strategies
memory retrieves for them: the schema gained an `adopted_strategy_keys` field, and three prompt
versions were A/B'd on frozen game turns with an LLM judge scoring adoption accuracy and action
quality (full record:
[../memory_system/strategy_adoption/report.md](../memory_system/strategy_adoption/report.md)).
Three of its findings outlived the experiment and became prompt law:

- **The ordering lever.** v1 emitted `adopted_strategy_keys` *after* the action, and the labels
  read like rationalizations — the model picked a move, then decorated it with whichever strategy
  fit. v2 moved the field to the **first** position, forcing the commitment before the act. The
  result was the largest single improvement the experiment measured: adoption accuracy 4.00 → 4.38,
  and — the telling part — action_quality +0.50 alongside it. A reporting field should not change
  the quality of the action it reports on; that it did means the reorder changed *planning*, not
  labeling. The report's line became a house principle: *"field ordering in a structured output
  schema is a prompt engineering lever, not just a formatting choice."*
- **Integer indexing.** The keys were originally UUIDs, and flash-lite corrupted the 36-character
  strings roughly 30% of the time. Numbering items `[1..N]` in the prompt eliminated the failure
  class: an out-of-range integer is logged and skipped, while a corrupted UUID silently
  mis-attributes. This is the first appearance of the weak-model rule that shapes everything after.
- **Elaboration is not free.** A v3 that added DO/DON'T instruction rules was tested and
  **rejected** — statistically equivalent to v2 on flash-lite. More instruction text is a cost to
  be paid for, not a default.

## 4 · The sequential-discussion rewrite (2026-06-02 → 06-05)

The scheduler redesign — replacing the concurrent everyone-speaks-per-round discussion with a
sequential, obligation-driven one
([../sequential_discussion/experiment_log.md](../sequential_discussion/experiment_log.md) §7) —
forced the largest schema shift in the file's history, because the scheduler needed the *speaker*
to tag its own message and because silence changed owners. Five design rules from that build still
govern the prompt — each emerged from a different scheduler requirement, but together they define
the shape of an agent turn:

- **2-D speech acts** (`831b908`). The scheduler needed each message tagged with whom it addresses
  and how. A first cut used a single `act` label; the smoke test against it (Smoke 1b in the
  scheduler log) showed the 1-D label was under-determined rather than inaccurate — nearly every
  werewolf line is *simultaneously* a question by form and an accusation by stance, so one label
  forced a coin-flip. The shipped shape is `addressed_targets` carrying `form × stance` per target.
  The same commit replaced `round` with `seq`.
- **All-required, never nullable — the flash-lite rule, earned in two commits.** The original
  contract let an agent stay silent by returning `message: null`. Two things killed it: flash-lite
  silently drops nullable fields (so a null is indistinguishable from a parse failure), and in the
  sequential model silence became the *scheduler's* decision, not the agent's. `831b908` made
  `message` required; `07e9cf4` replaced the null contract with a required **`pass_turn` boolean**.
  The general rule this pair fixed in place: when a model must be able to say "not applicable," a
  forced enum or boolean always beats an optional field. One placement detail is deliberate:
  `pass_turn` sits *before* `message` — an agent that has already written a message will not then
  decline to send it (self-authorship optimism), so the decline must be asked for first.
- **Transcript display trimmed** (`bb1b83a`). Agents see plain `player: message` lines; `seq` and
  the speech-act tags are storage, not display. Roughly 10 characters saved on every line of every
  call — small, but it compounds across the transcript block, the largest input.
- **Tone, silence, and the prompt boundary** (`36da926`, `93c7721`). The role prompts had been
  *prescribing* what turned out to be a degenerate strategy — agents policed each other's tone and
  silence instead of playing. Stripping the prescriptive prose halved police-style messages and
  set the neutral CORE_STRATEGY template every later role block follows. The principle that
  survived: **the prompt teaches how to talk and what the rules are; memory owns what signals
  mean** ([../prompt_boundary/experiment_log.md](../prompt_boundary/experiment_log.md)).
- **`firing_brief`** (`5672e22`). Live runs showed a domination loop: an agent cleared of its
  obligation re-derived what to say from scratch and re-landed on the same generic line. The fix
  injects the scheduler's firing reason as a one-line turn brief ("you were addressed by X —
  respond"), pinning the turn to the obligation that caused it.

## 5 · The 3-faction expansion (2026-06-06 → 06-10)

The 3-faction expansion ([../role_set/experiment_log.md](../role_set/experiment_log.md)) touched
the prompt everywhere: SK and vigilante CORE_STRATEGY blocks written against §4's neutral
template, the 9-player preamble, and the memory-context block extended to night prompts
(`7195957`, `0bf471b`). The **abstain sentinel** (`1d37485`) is §4's flash-lite rule applied
again: abstention could have been `vote_target: null`; instead `vote_target` stays a required
`str` with a sentinel value. Two modularity refactors cleaned up what the expansion created:

- **Template factories** (`96c3055`). By this point 17 near-duplicate templates existed — one per
  role per phase, drifting independently. They collapsed into `_discuss/_vote/_night_template`
  factories: the shared scaffold authored once, each role a one-line entry, with the wolf keeping
  a roster framing and cover trailer as the single override. Output verified byte-identical at the
  time, so the refactor carried no prompt-epoch cost.
- **`GAME_RULES` single source** (`953d8e8`, 06-10). The rules text had drifted across four
  copies — some still describing an 8-player game after the 9-player expansion. Factored into one
  constant composed into both the play preamble and the extraction-family prompts, so play and
  extraction can no longer disagree about the rules. *(This beat had no evidence record until this
  log; recovered from git.)* The same day, `06dfa80` deleted the redundant role-identity framing:
  CORE_STRATEGY became the single identity source, which killed a recurring binary "find the
  wolves" bias — a leftover of the 2-faction era that misread the 3-faction game.

## 6 · The caching bet — falsified at first measurement

The plan ("layout c" in
[../caching/experiment_log.md](../caching/experiment_log.md)) was to reorder every in-game turn
stable-early / volatile-late — role, private info, and memory moved to the tail — so implicit
caching would reuse the shared head for free across all nine agents. Measured before building:
**implicit caching does not fire at all** on the game model/backend. An identical 15k-token
prefix sent four times back-to-back returned `cache_read = 0` on every call, and a production
cross-check found 2 cache hits in 600 recent generations. In the caching log's words: *"the
whole 'free gameplay caching via reorder' plan collapses here. This was the central bet; it died
at the first measurement."* The gameplay layout was left unchanged. The one survivor is
post-game **extraction**, which got a transcript-first reorder with explicit Vertex caching
(~97% cache_read). The honest caveat, owned by that report's gap list: the extraction reorder's
output-neutrality was never A/B'd.

## 7 · Reason-before-act — the chain-of-thought reorder (2026-06-12 → 06-16)

The schema asked for the vote before the reasoning. So the model picked a target first, then wrote
`updated_strategy` as the justification for a choice it had already made — snap first, rationalise
after. The [decision-replay study](../memory_system/effectiveness/decision_replay/experiment_log.md)
is what caught it. The method is one sentence: freeze a recorded decision exactly as the agent saw
it, change one thing, and regenerate live — because the two runs are paired at the same decision,
luck cancels and the one change is all that is left to explain any difference.

The first fix taught the lesson that where an instruction lives decides whether it is obeyed.
Asking the model to "assess each memory" inside a field's description did nothing; flash-lite read
it and went on writing its usual terse note. Making the assessment a required structured field
instead, one verdict per memory, is what actually got the model to reason about each one.

The reorder on its own changed nothing. But the reorder together with those forced fields opened a
channel from memory to reasoning to vote: coherence between the reasoning an agent stated and the
vote it actually cast rose 75% → 92.5%. The study's own summary line is the one to keep — content
is the lever, and the reorder is the enabler that lets it pull.

Four commits on 06-16 (`5375fb4..998d032`) put this into production. Every deliberation field moved
ahead of the action across all 7 decision schemas. The crude list of adopted keys from §3 became a
verdict per strategy point — follow, override, or not_relevant. And the instruction to write those
verdicts moved out of the field description and into the prompt body, which took verdict coverage
0.27 → 0.97 — the same delivery lesson a second time.

Two later results confirmed the verdicts are real decisions and not decoration. In the v6 SP A/B,
an agent that writes `follow` on a strategy point telling it to abstain then abstains 77% of the
time, against 32% at baseline, and an agent that writes `not_relevant` behaves just like baseline.
The synergy instruction then settled how the two memory types combine: the strategy point is the
directive, the observations are the fact-check, and an observation that contradicts a strategy's
premise should produce `override` rather than blind `follow`. That override mode is what rescued
strategy-alone memory from trending harmful — confirmed for the SK arm, though a town-both arm was
never run.

## 8 · Facts-only pressure on the hand-written prose (2026-06-17 → 06-19)

By mid-June the schema and its layout were driven by evidence, but two hand-written prose blocks
had never been held to the same standard.

The first was the cross-faction threat brief. It was maintained by hand for each role, and the
wolf's copy silently left out the serial killer — the kind of bug prose hides, because prose has no
schema to catch an omission. It is now generated from the role registry (`bbc7c5b`), so a new role
shows up in every faction's brief automatically.

The second was the [prompt-claims audit](../prompt_claims_audit/experiment_log.md), which took
every remaining tactical claim in the role prose and tested it against metrics the games already
track. The investigator's "conceal your findings, let consensus build" framing turned out to be
actively harmful. It suppressed the sharing of results, the suppression traced back to the prompt,
and it cost the town, so a neutral two-sided block became the default. The wolf's "blend with the
majority" claim was put through the same test, passed, and stayed.

The principle is that an untested claim does not just sit harmlessly in the prompt. Play enacts it,
extraction records it, and memory feeds it back — so a prose claim earns its place with evidence or
it goes.

## 9 · The board-state layer — design (2026-07-05 → shipped 2026-07-09)

The open workstream adds a deterministic public-board layer to the prompt, and one private
reasoning instrument alongside it. Mechanics first.

- **`wolf_channel` into the wolves' day turns** (`2a8792c`). The wolves now see their own night
  coordination during the day, gated by the payload like every other private block, so it reaches
  a wolf and never a non-wolf.
- **The dead-roster board** (built, day-only). One structured line lists who has died, the role
  each turned out to be, and when:

  ```
  == Dead so far (public) ==
  player_2 (villager, night 1), player_5 (wolf, lynched day 2)
  ```

  These are deterministic public facts. Before the board, every agent re-derived them each turn
  from the GM's prose, where the role reveals sit buried in the discussion threads — so the board
  just hands them the answer.
- **An alive-roles line** (shipped 2026-07-09). The cast minus the revealed deaths — public
  arithmetic the prompt can simply do for the agents. Withholding it buys no strategic depth, only
  bookkeeping noise.
- **The suspicion read list** (shipped 2026-07-09), and this is the bet of the whole beat. Before it acts,
  each agent must commit a one-line reason, a role guess, and a confidence for every living player,
  and it gets its own reads back the next turn. The reason it exists: an agent's free-text private
  notes rot — a stale or false belief written once gets carried forward turn after turn — and a
  forced, structured commitment is at once a reasoning aid and the substrate the discussion-credit
  work needs. The reasons are kept for inspection only and never scored, because agents confabulate
  them.

The whole beat was pre-registered before a single test ran. [validation_plan.md](validation_plan.md)
is the machine-readable protocol; the sections below tell what happened, in the order the questions
were asked (dates mark each answer's standing run).

## 10 · Measuring the premise (2026-07-07 → 07-08)

### 10.1 Is the problem real? (2026-07-08)

*Catches: agents look like they misstate who is dead and which roles remain, but is that real, and
how big is it?* The premise was face-valid and never measured.

The instrument is a screen plus a reader. A deterministic screen flags every message and private
note that touches a checkable fact — a dead player's name, a role word, a survivor count. A cheap
model then reads each flagged text against the game's true facts, and a human checks the model's
calls. Anything the screen names is caught by construction; the full method lives in the census
report.

The answer: about 3% of public messages carry a role-fact error, about 4% of private strategy notes
do, and about 10% of night-action notes do — night being the one surface with no board at all. Two
things give the number texture. The dominant error is simple survivor arithmetic, an agent hunting
"the remaining wolf" when no wolf is left alive. And the errors are contagious: once one agent
speaks a phantom-wolf premise out loud, it becomes the room's shared starting point for the day, and
the worst single game-day had two dozen confirmed errors. One example to keep is a wolf's private
note, *"I have successfully maneuvered player 1 out of the game,"* written while player 1 was still
alive.

The reader checks what the speaker privately knows, so a wolf's strategic lie counts as deception,
not hallucination — confusion and lying stay on opposite sides of the line.

The premise revised upward. The problem is real and bigger than assumed, which justified the board
and put direct evidence behind extending it to the night prompt. Full record:
[validation/hallucination_baseline.md](validation/hallucination_baseline.md).

### 10.2 Does showing the answer fix it? (2026-07-07)

*Catches: if the wrong survivor-math comes from a missing roster, does printing the correct roster
in the prompt end it?* Replaying the confirmed failing turns with the board added answered it: no.

The pre-registered expectation was that the errors would collapse once the facts were visible, and
it was falsified. In the starkest exhibit the prompt carried a verified-correct "roles still in
play" line with no wolf on it, and the model still went hunting "the remaining wolf." The failure is
reasoning under a confusing death pattern, not missing information.

Re-verifying the cases during this work also showed that one of the four originally confirmed
failures had been checked against the wrong game — the paired arms share ids — so that one is
refuted and three stand; the census report records it.

So the board demotes to cheap hygiene, and the real hope moves to the read list. An agent that has
just written five reads with no wolf among them would have to contradict its own output to then
assert one, so a composition-coherence check was added to the later tests to arbitrate exactly that.
Full record: [validation/t1b_results.md](validation/t1b_results.md).

## 11 · The reads instrument (2026-07-07)

### 11.1 Non-regression and read quality (2026-07-07)

*Catches: eight forced reads now sit in front of the verdict machinery §7 built, so does that
dilution degrade the memory application, and are the reads honest judgments or decorative filler?*

Nothing broke. Verdict coverage held at effectively perfect in every arm, the board costs no output
tokens, and the reads cost about 60% more output per call — the price predicted in advance, now
measured. The reads come back honestly filled: wolves privately label their packmates as wolves
every single time, the role guesses beat random by roughly a factor of three, and the distributions
read like healthy skepticism rather than noise.

The ordering question split rather than crowned a winner. Putting the reads before the strategy note
triples how often an agent overrides a bad strategy suggestion — the agent is checking that
suggestion against its own committed beliefs, which is exactly the behavior the memory system wants.
But those same reads come out lazier when there is no prior history to update from. Putting the
reads after the strategy note reverses the trade: the reads read better, but the override rate drops
back to the old level. So reads-first ships provisionally, to be re-judged live, where fed-back
reads from the previous turn should make the cold-start laziness disappear.

One method lesson came out of it. Comparing each regeneration against the original recorded action
turned out to be dominated by sampling noise at play temperature, so the later replays compare one
arm against another instead. Full record: [validation/t2_results.md](validation/t2_results.md).

### 11.2 The skipped-player problem (2026-07-07)

*Catches: agents sometimes leave a living player out of their read list — is that a hole worth
closing?* It was not the long lists that dropped players but the mid-game boards, and the dropped
players were precisely the ones there was nothing to say about. Listing the expected names in the
instruction itself halved the misses. An importance check then showed the leftover gaps are
harmless: across 120 checked decisions, an agent voted against a player it had left unread exactly
once.

The final policy was the owner's call. Ship the name-listing, impute a missing read as "unclear" at
analysis time, and watch it with a tripwire — but do not re-generate turns to chase completeness.
That accepts a roughly 7% soft denominator in exchange for zero added latency, a trade made
deliberately.

## 12 · The ship test (2026-07-08)

*Catches: before a single live game is paid for, does the shipped bundle causally reduce
hallucination on the inputs where it happens?* The test takes the situations where hallucinations
actually occurred, regenerates each one under the old prompt and under the ship bundle, judges every
output blind with the census reader, and compares the two in pairs. Frozen inputs, one variable —
and the read mechanism runs handicapped, because a replay cannot hand it any fed-back history from a
previous turn.

Run 1 pointed the right way and produced a surprise worth keeping. The "clean" control turns were
not clean: under the old prompt, turns from a confusing board freshly hallucinate about a third of
the time regardless of what the original output had done. What predicts an error is the context, not
luck. So the hypothesis was reformulated around all error-prone contexts pooled together, committed
to the plan as the new primary, and then tested on a hundred fresh cases with zero overlap with the
first run.

The result confirmed it: old prompt 48% bad, ship bundle 30%, with 29 paired cases improving against
11 worsening, at a one-sided p = 0.003. The effect size replicated run 1 almost exactly. Because the
reads ran cold the whole time, this is if anything an underestimate of the live effect.

So the bundle causally reduces hallucination where hallucination happens, and it does not induce
errors on the turns that were already fine. It cost about three dollars of replay to know that
before paying for a single live game. The claim about the population-level rate waits for the
post-ship re-measure. Pre-registration: [validation_plan.md](validation_plan.md) T1c; outputs
[validation/t1c_outputs.jsonl](validation/t1c_outputs.jsonl) and
[validation/t1c2_outputs.jsonl](validation/t1c2_outputs.jsonl).

**Shipped (2026-07-09).** The confirmed bundle went into the live pipeline the next day, exactly on
the tested surface: day discussion, day vote, and the four single-actor night roles — wolf-night
turns stay on the old prompt, because the test never covered them. The T4 harness checks shipped
with it: the reads and their reasons are private, so a new leak check in the boundaries suite scans
every other agent's prompt for them, and a monitor-only tripwire logs any turn that covers fewer
than 85% of its enumerated read targets (never a retry — that trade was decided in the plan). Each
turn's eval record now also carries the reads it committed and the board it saw, so future replays
come straight from the frozen case. Records from this date onward are a new prompt epoch — nothing
compares across it.

A two-game live smoke ran the same day, and the pipeline held: every in-scope turn emitted a full
read list (completeness 1.00 — the enumeration works better live than the replay's 0.93), the
memory verdicts kept firing on every turn that retrieved memories, and votes tracked the voter's
own stated suspicions. The smoke's one catch was the new leak check itself: it flagged both games,
and every flag traced to shared vocabulary — a why like "confirmed healer" also lives in public
discussion, in retrieved memories, and in the author's own notes — zero real leaks. The check was
redesigned around what a real regression would look like (a rendered read *object* in a prompt),
with the false-positive classes pinned as tests; the details are a dated amendment under the plan's
T4. One instrument note for later: wolves answer the read list honestly at vote time but hedge
about their packmate during discussion turns, so the honesty probe belongs on vote and night turns.

## 13 · Limitations of this record (freshness: 2026-07-08)

Ordered by criticality:

1. **Reconstruction, not contemporaneous.** The early-May era (§1–2) is commit-message
   archaeology; prompt wordings tried and reverted in place left no diff trail and are invisible
   to this method — some are certainly lost.
2. **`role_lens` fold was planned, not shipped.** A phase_b spec proposed folding
   `SITUATION_ROLE_LENS` into schema descriptions and deleting the constant; it is marked DEFER
   and the constant is still live. Any account claiming it was removed is wrong.
3. **The extraction transcript-first reorder was never A/B'd for output neutrality** — owned by
   the caching report's gap list; noted here because it is the one caching-era survivor (§6).
4. **`memory_applicability`'s probe→production promotion** has a commit (`5375fb4`) but no
   experiment-log entry of its own; its validation record is the decision-replay log (§7).
5. **Wolf-night turns still lack the board** (§9) — the 2026-07-09 ship covered day turns and the
   four single-actor night roles (the tested surface), but the wolf-night discussion was outside
   the A/B and stays on the old prompt. T1's census says night notes are the worst surface (≈9.6%
   machine count), so the wolf-night extension is the obvious post-ship candidate — arbitrated by
   the parked night re-measure (§10).

---

*Sources: git history (`db288e6` → `2a8792c` + working tree), assembled 2026-07-07, prose revised
for legibility 2026-07-08 (no verdicts or numbers changed); the owning records linked per-beat
above (strategy_adoption, sequential_discussion §7, prompt_boundary, role_set, caching,
decision_replay, v6_sp_ab, prompt_claims_audit, prompt_versioning). Current-state reference:
[`docs/generation_prompt.md`](../../docs/generation_prompt.md). Prompt provenance mechanism: every
run record carries `prompt_bundle_hash` + git SHA ([../prompt_versioning/](../prompt_versioning/))
— with its known gap: output schemas live outside `Agents/prompts/`, so schema changes are covered
only by the git SHA, not the bundle hash.*
