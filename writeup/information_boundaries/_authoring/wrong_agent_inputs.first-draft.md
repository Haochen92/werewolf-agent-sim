# Private fields in the wrong agent inputs

*Level 3 · [Information boundaries](information_boundaries.md) · first draft 2026-10-31*

## Page copy (draft)

In June 2026 a rewrite of the day's discussion gave every speaker one bundle of inputs holding every role's private fields. The first batch run with the post-game checks wired in reported 109 flags; the templates had not rendered any of those fields, so no model saw them, and building the bundle by role fixed it. The chapter page tells that much. This page explains where the bundle came from, what the 109 counted, how I established that nothing was rendered, why three days passed before anything fired, and how the same gap came back four months later in another form.

### What the checks found

The checks run after each game the batch runner plays (the script that plays games in bulk). Each agent turn records the bundle of inputs built for it just before the model is called, one step before those inputs are filled into the prompt text, and the checks read those records. A flag therefore says that private data crossed the boundary where access is enforced; it does not say the data reached a model. The check output labels every flag `LEAK:` regardless, so the lines below read more alarming than they were.

On 6 June 2026 the first game played with the checks in the batch runner produced 109 flags. They are flag lines, not 109 contaminated inputs: the wolf-identity check writes two lines for each input it catches, one for the roster field and one for the wolf names read out of it.

| Check | Inputs caught | Lines per input | Flags |
|---|---:|---:|---:|
| Wolf roster in a non-wolf's input | 38 | 2 | 76 |
| Investigator's results in another seat's input | 33 | 1 | 33 |
| Vigilante's shot feedback in another seat's input | — | no check yet | 0 |
| | | | **109** |

The third row is the part the count hid. The Vigilante's feedback on its shots was in the wrong inputs as well, through the vote step as well as the discussion turns, and it added nothing to the 109 because no check covered it. It was found by inspection, not by a check.

The two batch logs give the before and after. They hold the checks' output, not the recorded inputs themselves, so the exhibit is a flag pair and the clean verdict. Before the fix, the healer's input carried the wolf roster, and the check wrote its two lines for it:

```text
LEAK: player_2 (healer) received surviving_wolves: player_4, player_5
LEAK: player_2 (healer) received wolf identities: player_4, player_5
```

After the fix, the same block of the next game's log is empty between its banners, and the batch exits clean:

```text
=== Running Leak Tests ===
=== Leak Tests Complete ===
Completed leakfix_smoke_all_disabled_001: winner=wolves day=4
Batch complete: 1 succeeded, 0 failed
EXIT: 0
```

### Where the bundle came from

The rewrite made the day's speakers take turns instead of speaking at once (chapter 1 covers that change). The earlier design had built one bundle per role and handed each role its own. The rewrite built one bundle with everything in it and handed it to every speaker, and the comment on that function said the framework "ignores extra keys" on the message carrying the bundle, so each role's step would read only what it needed.

That was true of a boundary the bundle never crossed. The framework has one way of connecting steps that strips any field the receiving step did not declare, and another, the one this path used, that hands the step whatever it was sent. The step's declared field list documents what the role should see and enforces nothing when the game runs, and the code that turns the bundle into prompt variables reads straight from what arrived. The private fields rode through every stage. The documented justification was the bug.

### Did any model see it?

A flag says the data was in the input; whether a model saw it depends on the template. A template fills in only the placeholders it names and ignores the rest, so the question was whether any non-wolf template named the wolf roster, any other template the Investigator's results, and so on. I searched every template for each private placeholder. Each appeared only in its own role's templates: the roster in the wolf's discussion, vote, night and situation-summary templates, the results in the Investigator's, the shot feedback in the Vigilante's. So nothing rendered on either path, discussion or vote, and no recorded game result was affected.

That finding is scoped to the templates as they were that day. It was one search at the time of the incident, not a standing check of rendered prompts, and the templates have been rewritten since.

### Why it went unnoticed, and the fix

The checks were correct and present the whole time. They were not on the path that ran.

- 9 May: the checks are written against the earlier design, which built one bundle per role, and pass. They run from a notebook cell after a game.
- 3–4 June: the discussion rewrite lands with the shared bundle. Nothing runs the checks.
- 6 June: the checks are wired into the batch runner; the first game flags 109.
- 6 June, later: the fix; the next game flags none.

I put the selection back where the bundle is built. The shared bundle became a common bundle plus private fields attached by role: wolves get the roster, the Investigator its results, the Vigilante its feedback, everyone else none. The vote step stopped putting the Vigilante's feedback in every voter's bundle. The comment was rewritten to state the rule and why a shared bundle is unsafe, and a check was added for the field the count had missed. The next game, with every check active, flagged none.

The lesson is narrower than "write checks". The checks existed, and nothing fired for three days because they ran only when someone ran them.

### The same shape, four months later

In October 2026 the boundary record was re-read against the code before this write-up, and that found the second instance. By then the checks needed more than the recorded inputs: three of them also took the night records, the withheld lines and the list of eliminated players from the finished game. The batch runner was still passing only the recorded inputs, the roles and the reads, so those three checks ran on every game, received nothing, and reported nothing. The night-record check had replaced the Investigator and Vigilante checks when the game grew to ten seats, so night-result isolation had had no live check since 3 October; it was held by the input builders and verified in unit tests only.

The fix the same day lifted the three inputs out of the finished game's state and passed them to the checks. One check was also rewritten: the eliminated-player check had read the day of each death out of the game master's prose, and the ten-seat game no longer announced night deaths in that form, so even when fed it would have missed them. It now reads the death records.

### What this establishes

In the record's own words: a boundary that does not reject is not a boundary; a check outside the execution path verifies nothing; and audit the data layer, not the presentation layer. The last is what made June an early warning rather than a silent fault. The checks read the inputs one step before rendering, so they flagged a violation that the rendered prompts would have hidden.

The limits are the chapter page's. The audit inspects recorded inputs, not rendered prompts; "none rendered" is a finding about one search of the templates in June, not a standing guarantee; and the checks run after a game, so they detect rather than prevent. Games played on the site save the same inputs, and a nightly job is built to apply the same checks to them.

<!-- Sources (checked 2026-10-31).
Opening and §1: experiment_log.md §2 "Verdict" and "Composition of the 109" (76 wolf-identity flags =
38 non-wolf inputs × 2 lines, one for `surviving_wolves` and one for the names extracted from it; 33
`investigator_results` flags = 33 non-investigator inputs; 76 + 33 = 109); "A third field outside the
count" (`vigilante_results` leaked through `build_speaker_send` and `fan_out_day`'s base payload, 0 of
the 109, found by inspection, check added in 8008623). Counts confirmed in leakwire_smoke.log: 109
`LEAK:` lines, 38 "received surviving_wolves", 38 "received wolf identities", 33 "received
investigator_results". What a flag means and where the checks read: report.md §3 ("the checks inspect
the prompt-input dict, layer 3's output, not the rendered prompt"; "a flag therefore means private data
crossed the payload boundary, which may or may not have rendered"); the capture point is `prompt_log`,
appended by `run_agent` before generating. "After each game the batch runner plays": report §3 "Where
the checks run". The checkers return `LEAK:` lines: experiment_log §1.
Exhibit: the two lifted lines are lines 1–2 of the `=== Running Leak Tests ===` block in
leakwire_smoke.log (the log also ends `LEAK DETECTED in leakwire_smoke_all_disabled_001: 109 leak(s)`
and `Batch complete: 1 succeeded, 0 failed, 1 game(s) WITH PRIVATE-INFO LEAKS`); the after block is
lifted verbatim from leakfix_smoke.log (its banner reads `=== Leak Tests Complete ===`; a line
`Writing JSONL results to: .../batch_results/leakfix_smoke.jsonl` sits above the block and the
`Completed`/`Batch complete`/`EXIT: 0` lines follow it; the tracing-retry noise between is omitted).
Both logs hold check output only; the recorded inputs are in `batch_results/legacy/leak{wire,fix}_smoke.jsonl`.
Runtime fingerprints: pre-fix at f5d43a94 (dirty), post-fix at c58e5c8d (dirty), gemini-3.1-flash-lite
on Vertex, nine-seat game.
§2: experiment_log §2 "Cause"; report §2 (the layer table) and §4 "The cause was the documented
justification". The full docstring sentence, from the pre-fix side of ef43342's diff: "Every role gets
the same superset of fields; each role node reads only the subset it needs (LangGraph ignores extra
keys on a Send payload)." The page quotes only "ignores extra keys". Framework terms, kept here: the
builder `build_speaker_send` dispatched one payload per speaker with a LangGraph `Send` into a plain
node; a `Send` delivers its payload verbatim; input-schema filtering applies to typed state channels
and to a compiled subgraph used as a node, which filters its input to its declared schema; the node's
`TypedDict` annotation enforces nothing at runtime; `build_agent_prompt_input` (then in
`Agents/prompts/prompt_inputs.py`) forwards whatever the payload contains. These behaviours are stated
for the pinned `langgraph==1.1.10` and `langchain-core==1.3.3` (report §2 framework note;
pyproject.toml). The earlier design "built one role-filtered payload per role": experiment_log §1.
"Chapter 1 covers that change": the sequential-discussion rewrite, `writeup/game_design_orchestration/`.
§3: experiment_log §2 "Severity" (exhaustive grep; `{surviving_wolves}` in the wolf day-discuss, vote,
night and situation-summary templates; `{investigator_results}` in the investigator's;
`{vigilante_results}` in the vigilante's; "discussion and vote alike"; "every game result to date is
unaffected"). Templates ignore surplus keys and error only on missing ones: report §2 layer 4. "One
search at the time, not a standing check": report §5 "No standing audit of the rendered prompt";
content plan care list. "Rewritten since": the shared-prefix layout of 2026-10-14, experiment_log §5.
Left off (handle with care): "even rendered, the leak would have helped the village".
§4: timeline from experiment_log §2 "How it persisted" (May 9 written, notebook only; June 3 to 4
rewrite; June 6 wired, e9d30ba) and §1 (notebook cell; 2026-05-09, e290b2ff). Fix: experiment_log §2
"Fix (ef43342)" and the commit diff (role-gated private fields in `build_speaker_send`, mirroring
`fan_out_day`; `fan_out_day` no longer puts `vigilante_results` in its base payload; docstring rewritten
to state the invariant); check added 8008623; "post-fix live game with all six checks active: 0 flags,
leak_check: {passed: true, leaks: []}, batch exit 0". All three commits are dated 2026-06-06. Left off:
the check count, the day's test count (27 passed), the `test_*` → `check_*` rename.
§5: experiment_log §6 "Problem: three checkers were fed nothing" (`run_leak_tests` grew optional
arguments for the eliminated players, the held candidates and the night records; the batch runner and
the two capture scripts passed only the prompt log, the roles and the reads; so
`check_night_record_isolation`, `check_gated_candidate_isolation` and
`check_eliminated_players_excluded` ran over empty inputs; the night-record check is the ten-seat
successor of the investigator and vigilante checks, so night-result isolation had no live check since
2026-10-03, "guaranteed by the builders and verified only in unit tests"). Night records replace the
result fields on 2026-10-03 (f1b3017b): experiment_log §5. Fix: `leak_inputs(result)` lifts the three
inputs from the final game state; the eliminated-player check rewritten onto the death records because
it had parsed the game master's prose ("was killed by the wolves last night"), which the ten-seat
morning announcements no longer use: experiment_log §6, report §5 "Closed". Dates: the record says found
and closed 2026-10-14 (report §5); the commit carrying the fix, 94304a22, is dated 2026-10-15. Left off:
the test counts (1064; 1352), the served-game capture work of the same day (chapter 7), the memory leak
in the process-global capture list.
§6: lessons quoted from experiment_log §2 "Lessons" and report §4 "Lessons"; "early warning": report §3
last paragraph. Limits: report §5 (no standing audit of the rendered prompt; two un-logged call sites,
left to the parent); the audit detects after the game: parent page and content plan. Site games: report
§3 (capture per finished game; `leak-audit` in `server/housekeeping/` runs the same checks nightly,
"built 2026-10-14; live once the migration is applied and the cron line installed"); owner 2026-10-30:
mention the job without its status. Left off: whether it is installed, and anything it has found.
Handle with care, applied throughout: flags not leaks; "the first run with the checks in the batch";
"none rendered" scoped to one search; no "impossible to leak"; no test or check counts, no CI, no
AI-written tests; the deduction engine absent; no folder, file or function names in headings or body;
the later false alarms of the reads check (experiment_log §4) left off. -->
