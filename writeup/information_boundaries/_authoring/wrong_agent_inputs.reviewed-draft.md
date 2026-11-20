# Private fields in the wrong agent inputs

*Level 3 · [Information boundaries](information_boundaries.md) · first draft 2026-10-31, revised the same day after two editorial reads and two claims reviews*

## Page copy (draft)

In June 2026 a rewrite of the day's discussion gave every speaker one shared bundle of inputs, which by 6 June carried three roles' private fields: the wolf roster, the Investigator's results, and the shot feedback of the Vigilante, a villager-side role that may shoot at night and is told privately what its shot revealed. The first batch run with the post-game checks wired in reported 109 flags; the templates had not rendered any of those fields, so no model saw them, and building the bundle by role fixed it. This page adds the cause, the count, the severity check, the three-day gap and October's repeat of it.

### What the checks found

The bundle of inputs is the chapter page's payload, and the checks read the prompt variables recorded from it, which copy its values unchanged. So a flag means private data crossed the boundary where access is enforced, not that a model saw it; the check output labels every flag `LEAK:` regardless.

On 6 June 2026 the batch runner, the script that plays games in bulk, ran its first game with the checks wired in and reported 109 flags. They are flag lines, not 109 contaminated inputs, and all are discussion turns: the wolf-identity check writes two lines for each input it catches, one for the roster field and one for the wolf names read out of it.

| Check | Inputs caught | Lines per input | Flags |
|---|---:|---:|---:|
| Wolf roster in a non-wolf's input | 38 | 2 | 76 |
| Investigator's results in another seat's input | 33 | 1 | 33 |
| Vigilante's shot feedback in another seat's input | — | no check yet | 0 |
| | | | **109** |

The third row is the part the count hid: the Vigilante's feedback was in the wrong inputs too, added nothing to the 109 because no check covered it, and was found by inspection. It had also reached every voter, not only the speakers; the next section says why.

The batch logs hold the checks' output, not the inputs; before the fix, the healer's input carried the wolf roster:

```text
=== Running Leak Tests ===
LEAK: player_2 (healer) received surviving_wolves: player_4, player_5
LEAK: player_2 (healer) received wolf identities: player_4, player_5
[107 more flag lines]
=== Leak Tests Complete ===
```

### Where the bundle came from

The rewrite made the day's speakers take turns instead of speaking at once (chapter 1 covers that change). The earlier design had built one bundle per role; the rewrite built one bundle with everything in it and handed it to every speaker, and its comment said the framework "ignores extra keys" on the message carrying the bundle, so each role's step would read only what it needed.

The framework has two ways of connecting steps. One strips any field the receiving step did not declare; the other hands the step whatever it was sent. The comment was true of the first, and this path used the second. The step's declared field list enforces nothing when the game runs, and the code that turns the bundle into prompt variables reads straight from what arrived, so the private fields rode through every stage up to the templates. The documented justification was the bug.

The Vigilante's feedback was a new field, added early on 6 June into the common part of both builders, so it reached speakers through the shared bundle and voters through the vote builder, and had been in place for hours, not days.

### Did any model see it?

Whether a model saw a field depends on the template, which fills in only the placeholders it names and ignores the rest. A search of every template for each private placeholder found each only in its own role's templates: the roster only in the wolf's, the results only in the Investigator's, the shot feedback only in the Vigilante's. Nothing rendered on either path, discussion or vote, and no recorded game result was affected. That finding is scoped to the templates as they were that day: one search at the time, not a standing check of rendered prompts, and the templates have been rewritten since.

### Why it went unnoticed, and the fix

The checks that existed were correct and present the whole time. They were not on the path that ran.

- 9 May: the checks are written and pass, run from a notebook cell after a game.
- 3–4 June: the discussion rewrite lands with the shared bundle. Nothing runs the checks.
- 6 June: the checks are wired into the batch runner; the first game flags 109.
- 6 June, later: the fix; a game played after it flags none.

I put the selection back where the bundle is built: a common bundle plus private fields attached by role (wolves the roster, the Investigator its results, the Vigilante its feedback, everyone else none), the vote step cleared of the Vigilante's feedback, the comment rewritten to state the rule, and a check added for the field the count had missed. In the log of the game played after the fix, the block between the two banners is empty and the batch exits clean:

```text
=== Running Leak Tests ===
=== Leak Tests Complete ===
[one line omitted]
Batch complete: 1 succeeded, 0 failed
EXIT: 0
```

### The same shape, found in October

Both cases share one pattern: a check that nothing on the running path feeds with real data. In June nothing ran the checks; in October the runner ran them without their inputs. A re-read of the project's record of this boundary against the code, before this write-up, found three checks that needed more than the recorded variables and the roles: the dead-player check needs the list of eliminated players, the withheld-line check needs those lines, and the night-record check needs the night records. The batch runner was still passing only the recorded variables, the roles and the reads, so those three ran on every game, received nothing, and reported nothing: the dead-player check from the first wiring on 6 June, the withheld-line check from its arrival on 2 July, the night-record check from its arrival on 9 October.

The night-record check mattered most. On 3 October, as the game moved from nine seats to ten, one record per night action replaced the Investigator's and Vigilante's result fields, and the check replacing their two checks followed on 9 October, so until 14 October night-result isolation had no live check at all; it was held by the input builders, with unit tests covering only part of them.

The fix lifted the three inputs out of the finished game's state, with unit tests that plant a night record and require the flag, and rewrote the dead-player check to read the death records instead of the engine's transcript announcements, which the ten-seat game no longer wrote in the form it parsed. Whether anything crossed the boundary in those windows is not known from a check: the record holds no re-audit of those games, and the builders, which select by role, are the reason to expect nothing did.

### What this establishes

The lessons, in the words of [the boundary record](../../evidence/agent_boundaries/report.md): "a boundary that does not reject is not a boundary"; "checks that do not run on every execution decay into false confidence"; "audit at the data layer, not the presentation layer". The first names the layers the comment trusted: a declared field list and a template both accept surplus data silently, so neither is a boundary; selection when the bundle is built is, and the checks are the detector behind it. The third is what made June an early warning: the shared bundle would have stayed harmless until a template edit named a private placeholder in the wrong role's template, and the checks, reading one step before rendering, flagged it while the rendered prompts still hid it.

The audit inspects recorded variables after the game, so it detects rather than prevents, and "none rendered" is a finding about one search in June. Games played on the site save the same variables together with the game-state fields the October fix added, and a nightly job is built to apply the same checks to them.

<!-- Sources (checked 2026-10-31; revised the same day after two editorial reads and two claims reviews).
Opening: the three fields: experiment_log.md §2 "Verdict" (the wolf roster, the investigator's results
and the vigilante's shot feedback; the healer's target and the wolf channel were not in the bundle:
the healer-target check flagged nothing, and the channel entered day inputs only in July, §3). "By 6
June": the Vigilante field was added that morning (below). The Vigilante in the nine-seat game: night
resolution wrote it an immune-shot line ("you shot X, but they were unharmed", Agents/nodes.py at
ef43342^); log §5 "the vigilante learned only immune shots"; "villager-side" = the town.
§1: what is recorded and where the checks read: report.md §3 (the capture point is the prompt-input
dict, layer 3's output, appended by `run_agent` before generating; "the checks inspect the prompt-input
dict, not the rendered prompt"; layer 3 "just forwards payload.get(field, default)", so "a non-default
value means the payload boundary was crossed"; "a flag therefore means private data crossed the payload
boundary, which may or may not have rendered"). Bundle = the parent's payload (report §2 layer 2).
"After each game the batch runner plays": report §3 "Where the checks run". The checkers return
`LEAK:` lines: experiment_log §1. The first batch was one game: leakwire_smoke.log "Planned runs: 1",
"Batch complete: 1 succeeded". "All discussion turns": the superset was in `build_speaker_send`
(discussion turns); the vote fan-out was already role-gated for the roster and the investigator's
results and leaked only `vigilante_results` (experiment_log §2 "A third field"; ef43342's message
"Gate private fields by role exactly like fan_out_day"). Composition: experiment_log §2 "Composition
of the 109" (76 = 38 non-wolf inputs × 2 lines, one for `surviving_wolves` and one for the names
extracted from it; 33 `investigator_results` flags = 33 non-investigator inputs); confirmed in
leakwire_smoke.log: 109 `LEAK:` lines, 38 "received surviving_wolves", 38 "received wolf identities",
33 "received investigator_results". Third field: experiment_log §2 "A third field outside the count"
(`vigilante_results` leaked through `build_speaker_send` and `fan_out_day`'s base payload, 0 of the
109, found by inspection; check added in 8008623).
Exhibits: the before block shows the two banners of leakwire_smoke.log with the first two `LEAK:`
lines between them; "[107 more flag lines]" is an elision marker, not a log line (the block holds
109 `LEAK:` lines; the log then prints `LEAK DETECTED in leakwire_smoke_all_disabled_001: 109
leak(s)` and `Batch complete: 1 succeeded, 0 failed, 1 game(s) WITH PRIVATE-INFO LEAKS`). The after
block is lifted from leakfix_smoke.log; "[one line omitted]" marks
`Completed leakfix_smoke_all_disabled_001: winner=wolves day=4` (the run name's `all_disabled` is the
memory-reranking setting of the run, not the checks; omitted to avoid that misreading). Both logs hold
check output only; the recorded inputs are in `batch_results/legacy/leak{wire,fix}_smoke.jsonl`.
Runtime fingerprints: pre-fix at f5d43a94 (dirty), post-fix at c58e5c8d (dirty), gemini-3.1-flash-lite
on Vertex, nine-seat game. "A game played after the fix", not "the next game": the record says "a
post-fix live game" (experiment_log §2 "Verification"); the post-fix fingerprint commit c58e5c8d
(12:41 UTC) predates the fix commits' timestamps (13:34 UTC), so the fix was run from the working tree
and committed after; the exact game order is not recorded.
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
pyproject.toml). "Up to the templates": report §2 layer 4 dropped the fields. The earlier design "built
one role-filtered payload per role": experiment_log §1. "Chapter 1 covers that change": the
sequential-discussion rewrite, `writeup/game_design_orchestration/`. The Vigilante field: commit
291668f3 (2026-06-06 02:43 UTC, "Give the vigilante neutral prompts and SK-confirmation feedback")
added `vigilante_results` to the base dict of both `build_speaker_send` and `fan_out_day`
(Agents/nodes.py at ef43342^, lines 165 and 211); the fix commits are 13:34 UTC the same day, hence
"hours, not days"; experiment_log §2 "A third field" ("not discussion-only").
§3: experiment_log §2 "Severity" (exhaustive grep; `{surviving_wolves}` in the wolf day-discuss, vote,
night and situation-summary templates; `{investigator_results}` in the investigator's;
`{vigilante_results}` in the vigilante's; "discussion and vote alike"; "every game result to date is
unaffected"). Templates ignore surplus keys and error only on missing ones: report §2 layer 4. "One
search at the time, not a standing check": report §5 "No standing audit of the rendered prompt";
content plan care list. "Rewritten since": the shared-prefix layout of 2026-10-14, experiment_log §5.
The search is written without "I": the record does not say who ran it. Left off (handle with care):
"even rendered, the leak would have helped the village".
§4: timeline from experiment_log §2 "How it persisted" (May 9 written, notebook only; June 3 to 4
rewrite; June 6 wired, e9d30ba) and §1 (notebook cell; 2026-05-09, e290b2ff). "The checks that
existed": the Vigilante field had no check (§1). Fix: experiment_log §2 "Fix (ef43342)" and the commit
diff (role-gated private fields in `build_speaker_send`, mirroring `fan_out_day`; `fan_out_day` no
longer puts `vigilante_results` in its base payload; docstring rewritten to state the invariant); check
added 8008623; "post-fix live game ... 0 flags, leak_check: {passed: true, leaks: []}, batch exit 0".
"With every check active" (the record's "all six checks active") is not on the page: e9d30ba's wiring
called `run_leak_tests(prompt_log, roles)` without the optional `eliminated_players` argument, so the
eliminated-player check ran with an empty input from the first wiring on (see §5). All three fix
commits are dated 2026-06-06. Left off: the check count, the day's test count (27 passed), the
`test_*` → `check_*` rename.
§5: experiment_log §6 "Problem: three checkers were fed nothing" (`run_leak_tests` grew optional
arguments for the eliminated players (May), the held candidates (July) and the night records
(October); the batch runner and the two capture scripts passed only the prompt log, the roles and the
reads; so `check_night_record_isolation`, `check_gated_candidate_isolation` and
`check_eliminated_players_excluded` ran over empty inputs; the night-record check is the ten-seat
successor of the investigator and vigilante checks, so night-result isolation had no live check since
2026-10-03, "guaranteed by the builders and verified only in unit tests"). "Found again", not "came
back": one of the three (the eliminated-player check) was fed nothing from the June wiring itself,
including in the post-fix June game. Inert windows: the runner's call `run_leak_tests(prompt_log,
roles)` from e9d30ba (2026-06-06) was unchanged until 94304a22, so the eliminated-player check was fed
nothing from the first wiring; `check_gated_candidate_isolation` arrived with f9f767d2 (2026-07-02,
experiment_log §4); `check_night_record_isolation` arrived 9b729aac (2026-10-09, experiment_log §5),
the result fields it succeeds having been replaced on 2026-10-03 (f1b3017b). The move to ten seats
came in stages during October (experiment_log §5 "The ten-seat game (2026-10-03 to 10-14)"); the page
dates only the night-record change and the check. "Unit tests covering only part of them": the day
builders pinned 2026-10-07 (3bc222ee), the night builders only by the October fix's own tests
(experiment_log §5, §6). Fix: `leak_inputs(result)` lifts the three inputs from the final game state;
tests feed a ten-seat night log and flag a planted record; the eliminated-player check rewritten onto
the death records because it had parsed the game master's prose ("was killed by the wolves last
night"), which the ten-seat morning announcements no longer use: experiment_log §6, report §5 "Closed".
"The announcements the engine writes into the transcript" = the game master's prose. Dates: the record
says found and closed 2026-10-14 (report §5); the commit carrying the fix, 94304a22, is dated
2026-10-15 08:30 UTC; the page gives no day for the fix. "No re-audit of the games played then": the
boundary record (experiment_log §6, report §5) records the unit tests and no live or retrospective run
of the fed checks; stated on the page as a limit, per the rule that a limitation that changes the
reading stays. Left off: the test counts (1064; 1352), the served-game capture work of the same session
(chapter 7), the memory leak in the process-global capture list.
§6: the three quoted lessons are verbatim from experiment_log §2 "Lessons" (also report §4 "Lessons");
the link is provenance for the quotation; "early warning": report §3 last paragraph; "always one
template edit from real exposure": report §3; "One template edit away from a real leak": ef43342's
message. The reading of the first lesson (state schemas and templates "tolerate surplus data
silently"; the payload is "the only place the guarantee can live"): experiment_log §2 "Lessons",
report §1 "Where it is enforced" and §2. Limits: report §5 (no standing audit of the rendered prompt;
the two un-logged call sites are left to the parent); the audit detects after the game: parent page
and content plan. Site games: report §3 and experiment_log §6 (each finished game saves the prompts,
the reads and the six state fields the checks read as one compressed row; `leak-audit` in
`server/housekeeping/` runs the same checks over every unaudited row; "built 2026-10-14; live once the
migration is applied and the cron line installed"); the claims review confirmed the saved state
fields include the three `leak_inputs` sources (`server/storage/prompt_captures.py`); owner
2026-10-30: mention the job without its status. Left off: whether it is installed, and anything it has
found.
Handle with care, applied throughout: flags not leaks; "the first run with the checks in the batch";
"none rendered" scoped to one search; no "impossible to leak"; no test or check counts, no CI, no
AI-written tests; the deduction engine absent; no folder, file or function names in headings or body;
the later false alarms of the reads check (experiment_log §4) left off. -->
