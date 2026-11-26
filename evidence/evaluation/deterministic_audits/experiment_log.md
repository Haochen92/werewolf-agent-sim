# Deterministic audits: the detailed record

This file holds the full detail behind [report.md](report.md). The "Detail" column of report.md's first
table gives each check's section here (§1a to §4), so you can jump from a check straight to its
detail. Read report.md first. Come here for how each check was built, how far it was tested, and every count, date and caveat.
Written 2026-10-23.

---

## Why these checks use code

Most evaluation in this project works by reading outputs and grading them. Either an AI model grades
another model's output (an *LLM judge*), or a person reads a sample of cases. Two guarantees are
checked by code instead, for different reasons:

- **No player's prompt contains another player's secrets.** Whether a prompt leaks is already in the
  data: who owns which secret, and which player each prompt went to. So code checks every prompt,
  exactly and for free. A judge reading thousands of prompts per game would cost money and could miss
  one, and a sample would probably miss a rare leak. (The exception is a reworded leak, which code
  misses and a judge could catch; see §1a.)
- **When the deduction engine tells a player something is certain, it really is certain.** That means
  true in every way the roles could have been dealt, given what the player knows. Checking it means
  trying all of those deals, a search an LLM cannot do reliably: the engine exists because the players,
  which are LLMs, kept getting this reasoning wrong. Code tries them all.

Both failures would also repeat. Once the bug is there, it happens in every game where the same
situation comes up.

**So both rest on code.** Some checks read every prompt a game sent. Other test code is an *oracle*:
code that works out the right answer from the rules on its own, so the engine's answer can be compared
with it. These oracles compare the engine with the rules over thousands of random games.

The same kind of check also serves two smaller needs:

- re-deriving a fact about how agents played from saved game records (the record audits, §3);
- stopping a run when the embedding model changes without notice (the embedding check, §4).

**Where they sit among the project's checking methods.** The hub ranks its checking methods on a ladder.
These checks are the bottom step, which the hub calls rung 0, below the LLM judge (rung ①). They are the
cheapest: they cost $0 and use no network, except for the embedding check's one embedding call. They are
also the least noisy. Their limit is not noise but scope. Each finds only what it was written to look
for.

**How they run.**

- The batch leak checks and the embedding check run automatically inside `run_batch`.
- The leak checks also run inside the capture runners under `evaluation/experiments/`.
- Everything else is a pytest test or a script that someone has to run.
- The repository has no CI. The `.github/` folder does not exist. CI is on the owner's pending list in
  [`writeup/_planning/map.md`](../../../writeup/_planning/map.md).

**State on 2026-10-23.** Every test file named in this file passed on the working tree that day. That
tree carries uncommitted edits to `Agents/deduction/`. The deduction tests took about 8 minutes, mostly
in the random-game oracles.

**Why this file never gives a test count.** The tests in `tests/` are largely AI-written and have not
been audited. So this file names specific tests that were written on purpose, and says what each one
asserts.

---

## 1. Leak checks

**The boundary model.** This comes from
[`agent_boundaries/report.md`](../../agent_boundaries/report.md) §2. Every prompt is built in four steps:

*game state → `Send` payload → prompt-input dict → rendered prompt → model*

- **`Send` payload:** the dict LangGraph hands a node it dispatches. It is what one seat is handed
  (a *seat* is one player's place at the table, `player_1` to `player_10`).
- **Prompt-input dict:** the named values the prompt template is filled from.
- **Rendered prompt:** the final text sent to the model.

Only one step narrows what a seat receives: building the payload. The other steps pass on whatever they
are given. So every check below sits at or near the payload step.

### 1a. Leak checks on every batch game: ✅

**What it is.** `tests/leak_test.py` holds eleven `check_*` functions. They are not pytest tests. Each
one takes a finished game's `prompt_log` and its role assignment, and returns a list of leaks.

- The `prompt_log` is every prompt-input dict a seat decision used. It is captured in
  `Agents/turn/eval.py`.
- `run_leak_tests` runs nine of the eleven functions.
- `leak_inputs(result)` takes three things out of the final game state for the checks that need them:
  the dead roster, the held lines and the night records.

Which functions run where:

| Functions | How many | Where they run |
|---|---|---|
| The set run by `run_leak_tests` | 9 | Every batch game, the capture runners, and the website audit (§1c) |
| ...of which: nine-seat result fields | 2 of the 9 | Same, but they do nothing on ten-seat games. They are kept so old logs still check. |
| Held lines reach only their author | 1 | Unit tests only |
| Round player lists are bare seat ids | 1 | Unit tests only |

What the nine check:

- No wolf roster or wolf name reaches a non-wolf.
- The pack's chat reaches only wolves, by night and by day.
- A night record's outcome text reaches only its actor. A pack record reaches only the wolves.
- `healer_target` appears in no prompt.
- A dead player gets no prompt after its death.
- A held line reaches nobody. A held line is a turn that the echo gate or the opening filter kept back.
- No read reaches another seat. A read is an agent's private suspicions about other seats' roles.
- Two check nine-seat result fields (see the table).

**How it works.**

- The checks read the prompt-input dict, one step before the prompt is rendered.
- The formatter writes every private key for every role. Each key gets an empty default or a sentinel (a
  fixed placeholder value). So a check fires on real content, never just because a key is present.
- A flag means private data crossed the payload boundary. That holds whether or not the template
  rendered it.
- The reads check makes two passes:
  - A structural pass looks for a rendered read object.
  - A prose pass looks for any private reason of 40 characters or more that turns up in another seat's
    prompt. Text that also appears in the public channel or the summaries does not count.

**Where it runs.**

- After every successful game in `run_batch`.
- In the capture runners: `phase2_step8_capture.py`, `phase3_capture.py` and `persona_voice_games.py`.
- Each JSONL game record carries a field `leak_check: {passed, leaks}`.
- The batch exits non-zero on any leak. It still writes the game.

**How far it was checked.**

*One confirmed true positive.* On 2026-06-06 the first wired run flagged 109 violations. They came from a
refactor that sent a superset payload to every speaker, so every speaker got everything
(`leakwire_smoke.log`). After the fix, the run flagged 0 (`leakfix_smoke.log`).

*False alarms, found and fixed.* Each one led to a narrower rule. The rules are kept in the checker's
docstrings.

| When | What was wrongly flagged |
|---|---|
| July smoke run | Shared game vocabulary |
| 2026-07-17 | A 40-character phrase. It wrongly halted the v7 run. |
| 2026-10-11 | The pack's own chat |
| 2026-10-18 | Two seats whose night records had identical sentences |

*Checks that had been checking nothing.* On 2026-10-14, three check functions were found to take
optional inputs that the batch runner never passed. They covered night records, held lines and
eliminated players. On every live game they had done nothing. That included the night-record check,
which had been the only live check on night results since 2026-10-03. `leak_inputs` fixed this the same
day. This finding is why this file rates the whole batch path, not just the check functions.

*So it can claim:* on every batch game, no structured private field crossed the payload boundary into the
wrong seat's prompt input. Both nine-seat and ten-seat games are covered.

**What it cannot claim.**

- **Memory.** It does not read free text from memory. Retrieved lessons come from namespaces keyed by
  role. Nothing asserts that the namespace served matches the role that asked. So a wrong role would leak
  without any alarm. This is an open gap (`agent_boundaries/report.md` §5).
- **Unlogged prompts.** Two places build a prompt input without logging it: the situation-summary query
  and the human seat. The checks cannot see them.
- **The rendered prompt.** No standing check reads it. The template step was checked once, by grep, in
  June 2026.
- **Reworded leaks.** The prose pass matches exact substrings. A paraphrased leak passes.

**Code and record.** `tests/leak_test.py`; the wiring in `scripts/run_batch.py`. Record:
[`agent_boundaries/report.md`](../../agent_boundaries/report.md) §3–5 and
[`agent_boundaries/experiment_log.md`](../../agent_boundaries/experiment_log.md).

### 1b. Leak tests on the payload builders: ✅

**What it is.** Unit tests that build payloads with the real builders from a fixed ten-seat state. They
assert, field by field, that each private field reaches its own role only. Then they run the standing
checks of §1a over the result.

| Test file | What it covers |
|---|---|
| `test_round_payload_leaks.py` | The opening round, the closing round and the sweep turn |
| `test_night_payload_leaks.py` | The solo and pack night builders, `leak_inputs`, and the eliminated-player rule |
| `test_wolf_channel_day_visibility.py` | The pack's chat on day payloads |
| `test_night_whiff_disclosure.py` | The pack's private record of a kill that failed because the target was immune |

**How it works.** The batch checks of §1a need a paid game to run. These tests pin the one enforced step,
building the payload, at no cost. Each test also plants a leak and asserts that the check catches it. So
they test the checker as well as the builder.

**How far it was checked.** `agent_boundaries/report.md` §5 lists both as "Closed". The day builders were
pinned on 2026-10-07 and the night builders on 2026-10-14.

**What it cannot claim.** The states are built by hand, not drawn from real games. A builder path that no
test builds is covered only by §1a on live games.

**Code and record.** `tests/engine/test_{round,night}_payload_leaks.py`,
`test_wolf_channel_day_visibility.py`, `test_night_whiff_disclosure.py`. Record:
`agent_boundaries/report.md` §3 and §5.

### 1c. Leak audit of games on the live site: 🟡 built and tested, not running

**What it is.** Games played on the website ran no leak check until 2026-10-14. Since then, each finished
website game saves one row in the `prompt_captures` table (alembic migration 0013). The row is gzipped.
It holds the game's prompts, its reads, and the six state fields the checks read.

**How it works.**

- `leak-audit` (`server/housekeeping/leak_audit.py`) runs the same nine checks as §1a.
- It reads every row not yet audited.
- It writes `audited_at` and `leaks` back onto the row.
- It exits 1 on a leak, or 2 on a row it cannot read.
- It runs from a checkout on the host, because the server image does not include `tests/`.

**How far it was checked.** `tests/server/test_leak_audit.py` checks that:

- a capture survives being compressed and read back;
- the audit finds a fixture game clean;
- it flags a planted leak and a prompt sent to a dead player;
- it records its verdicts;
- games running at the same time never write into each other's capture;
- a failed save never makes the game fail.

**Status: not running.**

- The module's docstring and `server/README.md` give a nightly cron line: 04:15, with its log at
  `/home/ubuntu/leak_audit.log`.
- On 2026-10-23 the cron job was found **not installed**. There was no crontab entry and no log.
- Games were already being captured by 2026-10-18. The prompt-size count (§2e) read 226 turns exported
  from `prompt_captures`.
- No record of an audit run over website games was found.
- So today no website game is known to have been leak-checked.

**What it cannot claim, even when running.** It has every limit of §1a. Also, a game resumed after a
server restart is captured only from the restart. Its row is marked partial, and the audit says so.

**Code and record.** `server/housekeeping/leak_audit.py`, `server/storage/prompt_captures.py`,
`tests/server/test_leak_audit.py`. Record: `agent_boundaries/report.md` §3 and §5, and
`agent_boundaries/experiment_log.md` (the 2026-10-14 entry). The cron is on the owner's pending list
(`writeup/_planning/map.md`).

### 1d. Tests of what each player is told: ✅ (narrow)

**What it is.** `tests/engine/test_information_fidelity.py` pins what each agent is told after the
information-fidelity pass of 2026-10-03.

**Background.** In game `46355b89`, agents cited private or missing information as if it were public. A
code audit followed
([`factual_errors/experiment_log.md`](../factual_errors/experiment_log.md) §8). It
led to the information-fidelity pass: revisions R-a to R-h in
[`discussion_evidence.md`](../../gameplay/discussion_evidence.md) §6.4.

**How it works.** The test asserts that:

- Each night actor gets a private record of what it did and what it may know. The record is gated to its
  owner. The pack's record reaches every wolf.
- A silent immunity is learned only by the attackers.
- A held-back draft reaches no transcript, not even its author's.
- Earlier days are shown in this order: the game master's record, then the claims on record, then the
  summaries.
- Votes are written "voted to eliminate" or "voted to abstain".
- The vote turn sees the note it replaces.
- The summariser receives the record and the claim ledger, and writes the v4 headings.

**How far it was checked.** It proves that the builders and formatters give agents these inputs.

*A stale docstring.* The file's module docstring still says a held draft is "shown to its author only".
The test itself asserts the current rule: nobody sees it. That rule dates from the shared-prefix layout
of 2026-10-14.

**What it cannot claim.** It says nothing about whether agents use these inputs. That is measured on the
[hallucination bench](../factual_errors/report.md) (§6.5 of `discussion_evidence.md`).

**Code and record.** `tests/engine/test_information_fidelity.py`. Record: `discussion_evidence.md`
§6.4–6.5.

---

## 2. Deduction engine tests

**What the engine is.** The deduction engine lives in `Agents/deduction/`. It was built from 2026-10-16
to 2026-10-21, for the ten-seat game only. It writes into each AI seat's prompt the conclusions that
follow from what that seat knows. Each line has one of three grades:

- *certain*;
- *follows if the named claims are true*;
- a complete list of *possible explanations*.

**Its rule.** The rule is absolute. No line may state as certain something that some legal game would
make false ([`gameplay/deduction/report.md`](../../gameplay/deduction/report.md) §2). Agents take up
injected text almost every time: 10 of 10 replays on the R1 turn. So a false line would be a falsehood in
every game that meets its conditions.

**What the tests prove.** They are built to prove **soundness**: nothing false is stated. They are not
built to prove **coverage**: nothing a careful person would conclude is missing. Only the four acceptance
cases (§2c) test coverage. The owner set a four-part bar for the build on 2026-10-16, in the
[catalogue](../../gameplay/deduction/deduction_catalogue.md) under "Build verification".

**Two terms from the catalogue.** A *row* is one kind of line the engine can write, with an id such as
A22(b) or F8. A *slice* is one numbered stage of the engine's build.

### 2a–b. Random games and the exhaustive check: ✅

#### 2a. Soundness over random legal nights

**What it is.** `tests/factories/random_nights.py` builds random games, and three tests check every line
the engine writes in them.

**How it works.**

1. It deals a random cast.
2. It kills some players on earlier nights and days.
3. It lets every living role make a random legal choice.
4. It resolves the night with the real engine: the rules, the records, and the resolution node that
   writes the morning.
5. Each surviving seat's lines are computed from that seat's own payload only.
6. Every fact a line states is checked against the true roles and the resolved night.

**Scale.**

| Test | What it covers | Size |
|---|---|---|
| `test_own_results.py` | The seat's own results | Runs until 20,000 nights are played, fixed seeds |
| `test_public_events.py` | The public events | Runs until 20,000 nights are played, fixed seeds |
| `test_candidates.py` | Each seat's possible roles | Runs until 20,000 nights are played, fixed seeds |
| `test_conditionals.py` | Lines built on random true and false claims | 4,000 nights |

Similar truth runs are in the tests for joins, comparisons, explanations and evil seats. Each of the
three 20,000-night tests also asserts that every built row actually fired. So a row cannot pass by never
appearing.

**How far the oracle itself was checked.** When each slice was built, rules were broken on purpose, to
see whether the random nights caught them. The catalogue's "Build status" records the results:

| Slice | Rules broken on purpose | Result |
|---|---|---|
| 1 | 3 | Each caught |
| 3 | 6 | Each caught |
| 5 | 6 | Each caught. One case (A36 read through a body) was caught only by the hand-built nights. |
| 6 | 5 | Each caught |
| 7 | 6 | Each caught |

These were one-time checks at build time. They are not standing tests.

**What it cannot claim.**

- Random play reaches rare conditions rarely. Row A22(b) fires about once in 20,000 random nights, so it
  is pinned only on hand-built nights.
- The checker encodes the rules by hand, in `fact_holds` and `public_fact_holds`. A rule misread the same
  way in the engine and in the checker would pass.

#### 2b. The exhaustive check (brute-force oracle)

**What it is.** `tests/factories/role_assignments.py` lists every way to deal the cast that agrees with
what a view knows. A view is either the public record or one seat's payload.

**How it works.**

- The oracle is built from the rules and from what each fact means. It is not built from the engine's own
  reasoning.
- It includes night immunity and how a hidden body narrows that body's role.
- It uses the real `determine_winner` and `is_draw`, because the game went on past every point.
- For a conditional line, it adds the line's premise.

**What the tests assert.**

- The true deal is always one of the allowed deals.
- Every certain item holds in all the allowed deals.
- The solver keeps every role that some allowed deal gives.

Where this is checked:

- on the hand-built acceptance games;
- on every view of 400 random games, which the test requires to be more than 8,000 seat views
  (`test_candidates.py`);
- for conditional lines, on 120 random games with random claims (`test_conditionals.py`);
- the comparisons and the covers have their own oracle runs.

**The leak half: no hidden peeking.** The engine reads one typed object, `SeatView`, built from the
seat's own payload. A *metamorphic test* changes something the output must not depend on, and asserts
that the output is unchanged. Here two things are changed:

- other seats' roles are swapped, within the legal deals;
- hidden state is planted on the payload: `roles`, and every seat's night records.

Every seat's lines must stay identical. This is checked on hand-built cases and on random games: 150
games in `test_candidates.py` and 2,000 random nights in `test_own_results.py`. It extends the leak
boundary of §1 into the engine.

**Role traits are derived, not declared.** `test_role_traits.py` derives each role's traits from the real
night engine. Traits include immune, blockable and visits, among others. The test fails on any
disagreement with the trait table the rows read. The catalogue records that all 168 single-trait flips
were caught when the table was introduced (2026-10-18).

**What it cannot claim.** The oracle and the engine draw on the same written knowledge of the game. A
fact that neither encodes is invisible to both. Agreement with the oracle is evidence of soundness
against the rules as written. It is not proof that the rules are complete.

**Code for 2a–b.** `tests/engine/deduction/`;
`tests/factories/{random_nights,random_claims,role_assignments}.py`. Record:
[`gameplay/deduction/report.md`](../../gameplay/deduction/report.md) §2 and §4; catalogue "Build
verification" and "Build status".

### 2c. Four real failure cases: 🟡 (the only test of coverage)

**What it is.** `tests/engine/deduction/test_acceptance.py` holds four cases, AC1 to AC4. Each is a real
failure from a Haiku game (`2f19d908` and `403f4dbc`).

**How it works.**

- Each case's turn is rebuilt from its frozen payload, exactly as the live pipeline builds it.
- The whole production prompt is rendered.
- Every sentence the case lists must appear word for word, in the right block. The blocks are the night
  record, the public block and the seat block.
- Nothing on the case's "must not say" list may appear.
- Example: AC1's forbidden sentence is "player_7 is the Chanteuse". A second visitor is always possible,
  so that sentence may appear only inside an either/or line.

**How far it was checked.** It shows that the four failures that led to the engine now get the lines a
careful person would draw, and not the tempting false ones.

**What it cannot claim.**

- These are four hand-written goldens (fixed expected outputs). Coverage elsewhere is untested.
- Some listed sentences do not render word for word. There the test pins what does render and says why.
  This applies to AC1 line 1, AC2 lines 3–5 and AC3 line 1. The reason is either an owner ruling or a
  gap in the frozen payload.
- The same-day claims in AC1 and AC3 are speaker fields filled in by hand. They are not the model's own
  output.

**Code and record.** `tests/engine/deduction/test_acceptance.py`. Record: catalogue "Acceptance cases";
[`gameplay/deduction/report.md`](../../gameplay/deduction/report.md) §4.

### 2d–e. Solver and prompt-size counts: ✅ / 🟡

#### 2d. Solver count: ✅ (one run)

**What it is.** The solver works out each seat's possible roles. It does this by passing constraints
along, without a full search. So in principle it could keep a role that a full search rules out.
`evaluation/experiments/deduction_solver_census.py` measures how often that happens. It uses the tests'
random-game generator and the brute-force oracle of §2b.

**How far it was checked.**

- 150 random games, seed 20261018.
- It checked 3,408 seat views and 525 public views.
- No view kept a role that no allowed deal gives. No view was left unsolved.

Timings on the host (an aarch64 machine). They give scale only.

| What was timed | Median | 99th percentile | N |
|---|---|---|---|
| One seat's possible roles | 0.45 ms | 1.65 ms | 3,408 |
| A whole turn, on AC2's frozen vote turn | 10.5 ms | (not given) | 30 |

**Provenance.** The run was on 2026-10-21. `census.json` records commit `e765a18e`, with a dirty tree
(uncommitted changes present). On 2026-10-23, three things were untracked in git: the runner, its output
folder, and `gameplay/deduction/report.md`.

**What it cannot claim.**

- Zero misses means no gap against the oracle. It does not mean completeness (see §2b).
- Some choices nobody sees keep both branches by design. Examples: a fortune teller's self-bet, or which
  body a borrowed action used.
- Conditional runs, where a claim is added as a premise, were not measured.

**Code and record.** `evaluation/experiments/deduction_solver_census.py` (untracked on 2026-10-23).
Record: `gameplay/deduction/report.md` §4; `gameplay/deduction/data/solver_census/census.json`.

#### 2e. Prompt-size count: 🟡 (descriptive)

**What it is.** `evaluation/experiments/deduction_block_census.py` renders both deduction blocks in
`full` mode on every saved turn. No model is involved. It measures each block in lines and characters.

**How it works.** Its turns come from two sources, 278 turns over 4 games in all:

- 52 frozen cases;
- 226 turns rebuilt from captured website games.

**How far it was checked.** It measures prompt cost and which rows fire.

- Over the 278 turns, the median combined block was 1,199 characters. The maximum was 3,583.
- The explanation row F8 fired on none of the 278 turns. This is the basis of the line "one level has
  never fired" in the deduction report (§5).
- Full counts are in `census.json`. The three longest blocks are written out in `longest_blocks.md`.

**What it cannot claim.**

- It is descriptive. It says how much text a seat gets, not whether that text is right or used.
- It ran on 2026-10-18. `census.json` records commit `07393835`, with a dirty tree. It has not been
  re-run.
- The engine has changed since: slice 17 on 2026-10-21, and uncommitted edits on 2026-10-23.
- Four games is a small sample, and all are Haiku games.

**Code and record.** `evaluation/experiments/deduction_block_census.py`. Record: catalogue "Build status",
slice 8; `gameplay/deduction/data/deduction_block_census/`.

---

## 3. Audits of old game records (nine-seat, July 2026)

**What these are.** `evaluation/src/audits/` holds checks that re-derive a fact about play from
`batch_results/` records. They use no model and no network, so in principle they can be re-run on a later
batch.

**Why they are nine-seat only.** The two audits below (§3a, §3b) were written for the nine-seat game. Both
hard-code its roles (`"wolf"`, `"vigilante"`). Both hard-code its record fields: `night_resolutions`, and
the lists of the 50-game and 180-game files. So they cannot read ten-seat records as written. Their
findings describe nine-seat play in July 2026.

### 3a. Speaking-order audit: 🟡

**What it is.** The discussion scheduler decides who speaks next, without knowing roles. Does it keep
some roles from speaking? This was a possible explanation for several metrics that showed no effect.

**How it works.** Three subcommands read the saved `day_channel`:

- **`floor-access`** gives, per role and per day: turns, the share of reactive and proactive turns, and
  pass rates.
- **`gate-silencing`** asks whether a turn silenced by the novelty gate can be told apart from a
  voluntary pass. The novelty gate is a filter that holds back a line that adds nothing new.
- **`reveal-withhold`** breaks down the investigator's confirmed finds that never led to a lynch.

Its definitions were registered before it ran (log §3, 2026-07-02).

**How far it was checked.** A brief result; the verdict belongs to the log.

- 50 v5 games, 3,843 entries.
- No role was starved of turns.
- Investigators with a find to report spoke before the vote on 58 of 58 days.
- None of the 12 unreported finds was a case of no turn or a late turn.

**What it cannot claim.**

- Turn timing is computed from structured fields, so it is exact.
- The 12 unreported finds were split into "withheld" and "said but ignored". That split rests on a
  keyword matcher for role claims, so it is soft. The log says so. The owner read all 7 withheld
  transcripts by hand.
- The gate question could not be answered from the July records. Instead the audit led to a change in
  what is recorded: the fields `gated` and `gated_candidate` were added to `DayChannel`.

**Code and record.** `evaluation/src/audits/scheduler_access_audit.py`. Logic tests on synthetic fixtures:
`tests/evaluation/test_scheduler_access_audit.py`. Record:
[`scheduler_bias_log.md`](../../metrics/metrics_audit/scheduler_bias_log.md) §3 A–C. Data:
`metrics/metrics_audit/data/{floor_access,gate_silencing,reveal_withhold}.json`.

### 3b. Failed-attack audit: 🟡

**What it is.** A *whiff* is an attack on the night-immune serial killer that fails silently. When one
happens, does the attacker act on it the next day? The attacker is either the wolves or the vigilante. If
not, which layer fails: what the attacker is shown (visibility), how it acts (behaviour), or whether it
gets to speak (floor)?

**How it works.**

- **Visibility** is a fact about the code. It is recorded as constants, with their file and line.
- **Behaviour** is a join over the records. Did the attacker accuse or vote for the target on a later
  day? This is compared with a control: targets that were healed.
- **Floor** reuses §3a.
- A "reasoning scan" reads the attacker's strategy notes. It uses keywords appearing together, not a
  judge.
- It ran on 50 v5 games and 180 v6ab games.

**How far it was checked.** A brief result.

- The layer that failed was visibility.
- The vigilante, which is told privately, acted on 6 of 8 and 8 of 9 deduped whiffs.
- The wolves, which were told nothing, did not mention the survival in 68% of their notes after a whiff
  (45 of 66).
- That supported change E, which is now built. The pack's night record now states the failed attack
  (`tests/engine/test_night_whiff_disclosure.py`).

**What it cannot claim.**

- The visibility layer is a fact about the code of that time.
- The rates are exact joins, but the vigilante's N is only 8 and 9.
- The "did not mention" count comes from keyword matching over free text. That is a rough method for a
  question about meaning. The log labels it as one.
- Since change E, the audit's premise no longer holds in current games: the wolves are no longer left
  with a silent whiff.

**Code and record.** `evaluation/src/audits/whiff_conversion_audit.py`. Logic tests:
`tests/evaluation/test_whiff_conversion_audit.py`. The log cites the older path
`tests/test_whiff_conversion_audit.py`. Record: `scheduler_bias_log.md` ③.E. Data:
`metrics/metrics_audit/data/whiff_conversion.json`.

### 3c. Pivotal-turn flags: ⚠️

**What it is.** `evaluation/src/audits/recall_flags.py` flags a game's do-or-die turns from its
structured record alone. A turn is flagged in either of two cases:

- the wolves are at or near parity with the rest;
- four or fewer players are alive.

**How it works.** It was built for the v7 extraction work as an *anchor*. The flagged turns are offered
to the extractor as a hint of where lessons are. They are also the denominator of a capture metric.
`evaluation/src/studies/reextract_cells.py` also imports it.

**How far it was checked.** The recall-arm pre-gate ran on 2026-06-19, on 3 games with 12 flagged turns.
The anchor did not raise flash-lite's capture: 3 of 12 with it, and 3 of 12 without it.

**What it cannot claim.**

- The definition of "pivotal" is a rule of thumb.
- It was never checked against people's labels of which turns mattered. No such labels were found.
- It has no unit tests.
- It encodes the nine-seat factions.

**Code and record.** `evaluation/src/audits/recall_flags.py`. Record:
[`memory_system/v7/extraction_coverage_ab_spec.md`](../../memory_system/v7/extraction_coverage_ab_spec.md) (the recall-arm
pre-gate); [`memory_system/v7/experiment_log.md`](../../memory_system/v7/experiment_log.md).

---

## 4. Embedding check: ✅ (batch runner only)

**What it is.** The memory store is keyed on an embedding model's name. If the model behind that name
changes, every stored vector and every query shifts. Search would still return plausible results, so
nothing would look wrong. `evaluation/src/audits/embedding_canary.py` closes that gap.

**How it works.**

- It embeds 12 fixed text pairs from the game's domain. They range from near-paraphrases to unrelated
  pairs.
- For each pair it computes the cosine similarity, and compares it with a pinned value.
- If any pair moves by more than 0.02, it raises `EmbeddingCanaryDrift`.
- It runs at the start of every `run_batch`, unless `--skip-embedding-canary` is passed.
- If the pin file is missing, it warns and skips rather than blocking.
- It was built in the hardening pass of 2026-07-02
  ([`hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md) §4.9).

**How far it was checked: the re-pin history.** The pins are re-computed only on a deliberate model
change. The pin file's history shows two:

| Date | Change | Why |
|---|---|---|
| 2026-07-16 | `gemini-embedding-001` to `gemini-embedding-2` | Forced by quota |
| 2026-10-12 | To `qwen/qwen3-embedding-8b`, 1536 dimensions | Now the default in `Agents/llm_factory/embeddings.py` |

*A stale docstring.* The module docstring still names `gemini-embedding-001`.

**What it cannot claim.**

- `scripts/run_batch.py` is its only caller. The server's lesson retrieval never runs it. So a silent
  model change on the live site would go unnoticed until the next batch.
- Twelve pairs and a tolerance of 0.02 catch a change that moves the geometry. They cannot rule out a
  small change that stays inside the band.
- How 0.02 was chosen was not found.
- It has no unit test.
- No record of it ever firing was found.

**Code and record.** `evaluation/src/audits/embedding_canary.py`, `embedding_canary_pins.json`;
`scripts/run_batch.py`. Record: [`hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md)
§4.9.

---

## 5. Model-written memory fields, recomputed by code

*Moved here on 2026-10-23 from `evaluation/dimension_extraction/`, which was dissolved: its checks
that use code alone are this section, and its blind read of the decision tags moved to
[`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md) (the decision-tag read). The text below is
kept as it was written, with its dated corrections. The memory holds two kinds of note:
*observations* (a model's account, written after a game, of one play and what it led to) and
*strategy points* (advice for a role, drawn from several observations). A model fills fields on each
note and on each in-game memory search; these checks recompute those fields from the game record.*

### 5a. The memory search filters, recomputed (2026-07-02, nine-seat)

#### How it works

- **The $0 deterministic audit** (`evaluation/src/instrument_validation/dimensions/dimension_audit.py`;
  the paid `--regen` arm hard-refuses pending spend sign-off). It recomputes deterministic truth for
  every LLM-filled query-side dimension in the loop-era sidecars and compares. Coverage: **~6,267
  cases-with-dims** (20,284 situation-rows) across town_only_run1 (25.9% / 30 games), town_only_run2
  (24.7% / 100 games), and v2_full (42.2% / 24 games — the only run carrying wolf/SK dims); the 5
  `legacy` smoke runs predate dimension capture and are excluded, stated not skipped. The ~25–42% rates
  are the structural ceiling (dims fill only on the retrieving memory-ON side), not missingness. Truth
  home `query_criticality` was lifted into a shared module so the audit and the criticality screen
  compute it identically. *Correction 2026-10-23: that module graduated to
  `Agents/memory/consolidation/decision_scoring.py` on 2026-07-21; `evaluation/src/loop/decision_scoring.py`
  is now an import shim.*
- **A mandatory epistemic split** so a mismatch is never mispriced: *agent-knowable* dims
  (`players_alive`, `bullets_left`, `ally_revealed`) are pure fill error; *vs-omniscient* dims
  (`distance_to_parity`, `is_swing`) conflate fill error with the agent's epistemic limit for town roles
  (a villager cannot know the wolf count), so only the wolf side reads as ~true fill accuracy.
  *Correction 2026-10-23: the premise of this split was later falsified. The cast is fixed and public and
  every death reveals the dead player's role, so the faction counts the clocks need are public too, and
  parity and swing are agent-knowable (owner, 2026-07-11; docstring of `_override_deterministic_dims`).
  The town-side `is_swing` row below is therefore a fill error, not only an epistemic limit. The audit's
  truth counted only the wolves' path to a win; the computed values were widened to all three sides the
  same day.*

#### Results, per field

| Dimension | class | n | exact acc | read |
|---|---|---|---|---|
| `players_alive` / `alive_bucket` (gate key) | agent-knowable | 6099 | 0.970 / **0.990** | sound — the gate's primary key held |
| `ally_revealed` (partner-absent) | agent-knowable (wolf) | 439 | **0.975** | sound |
| `bullets_left` | agent-knowable (vig) | 1109 | **0.164** | broken — under-counts (bias −0.68); day-2 accuracy 0.0 |
| `is_swing` — wolf-side (≈true) | ~true fill | 439 | **0.606** | **worse than a constant** — always-False scores 0.827 (base rate 0.173) |
| `is_swing` — town-side | vs-omniscient | 5282 | 0.469 | conflated with epistemic limit; not a fill verdict |
| `distance_to_parity` | vs-omniscient / ~true | 439/5660 | 0.09 / 0.05 | unusable as an exact key (matches its default-off status) |

The three agent-knowable numerics are the clean story. `players_alive` is filled well but is a value the
agent was literally handed — 3% wrong for no epistemic reason. `bullets_left` is mostly wrong: every
vigilante with 2 unspent bullets reports 1 on day 2 (accuracy 0.0), climbing only to ~0.35 by day 4.
Wolf-side `is_swing` is the finding: at 0.606 against a 0.173 base rate it *over-fires* "swing" (173
false positives vs 76 true positives), so it is materially worse than a constant.

- **A truth-computation catch, fixed in place (not laundered).** Wolf `night_action` cases persist an
  empty `surviving_players` roster (176 cases); the first pass scored fills against a bogus 0 and
  manufactured a wolf +2 over-count. The runner now counts these `no_roster` and skips criticality truth
  there; corrected wolf `players_alive` = 0.97. A deterministic checker is only as good as its inputs —
  it earned one bug fix before its first real read.
- **N is a decision count, not a game count.** 100 games in town_only_run2, but decisions are correlated
  within a game. Adequate for the per-decision fill-accuracy point; the percentages carry less certainty
  than their counts suggest.

#### The rule set before the run fired, and what it reopened

- **The pre-registered rule** (frozen before running): CONFIRM the negative gating verdict iff
  alive-bucket ≥ 0.90 **and** wolf-side `is_swing` ≥ 0.80 **and** the enum kappas ≥ 0.6; RE-OPEN if any
  gated dim < 0.80. Alive-bucket passed at 0.990, but wolf-side `is_swing` at 0.606 fired **RE-OPEN**.
  The enum-kappa clause is PENDING Phase-3 human labeling and cannot lift this to CONFIRM regardless.
- **What it means, bounded honestly.** The gating null is at least partly **uninformative, not a clean
  content verdict**: the gate keyed on one reliable dimension, one anti-informative one, and two enums no
  one has validated. Mean gated error ē ≈ 0.202 implies a true retrieval tilt would be attenuated to
  `1 − 2ē` ≈ 0.60 of its strength, so a screen reading ~0 could be masking a real but smaller effect.
- **Scope of the re-open, said plainly.** It re-opens **gating** only. The criticality *screen*'s query
  side was already deterministic (`query_criticality`), so it is untouched. This authorizes the ~$10–15
  gating re-screen — substitute deterministic `players_alive` + offline `is_swing` into
  `dimension_gating_screen.py` — before any prompt surgery on the enums. That spend is HELD.

> *Correction 2026-10-23.* Neither follow-up ran. The gating re-screen was never approved, and the
> human kappa check of the category labels was never done (a sampler to draw its cases was built; the
> labelling was not). In October 2026 a review of the ten-seat query removed the four category labels
> that only gating used (`exposure_class`, `info_landscape_class`, `consensus_direction`,
> `divergence_sign` are "no longer asked" on the query side). Stored lessons keep them, because the
> offline duplicate check and the replay page read them, and they remain unvalidated. The gating status
> is "no benefit measured", not "proven useless" (situation_dimensions/report.md §6).

### 5b. The fix: those fields computed by code (2026-07-02, extended 2026-07-11)

The structural corollary, green-lit as free. At query time, after the situation LLM returns,
`Agents/memory/retrieval/situation_agent.py::_override_deterministic_dims` overwrites the agent-knowable
dims from game state before dims and embeds are composed: `players_alive` from a shape-robust
living-player count, `bullets_left` from the vigilante's live counter, `ally_revealed` from pack-size vs
initial wolf count.

- **Two payload bugs surfaced and fixed** (assumption corrections): `players_alive` was never a plain
  `len(surviving_players)` — single-actor night payloads exclude the actor (off-by-one) and wolf payloads
  carry no role-blind roster — which retroactively explains part of the LLM's 3% error as payload
  ambiguity, not model sloppiness; and the vigilante's *day* payload dropped the bullets counter
  entirely, so `vigilante_bullets` had to be threaded through a new `DayGraphState.vigilante_bullets`.
- **Scope guarantees.** The corrected numerics carry no embed marker, so the override changes only the
  gating filter input — the composed embed string and retrieval matching are unchanged. Stored records
  are untouched: query-time only, so only future queries benefit.

> *Correction 2026-10-23.* Two things changed after the July text, both closing gaps it named.
> `distance_to_parity` and `is_swing` joined the computed set on 2026-07-11, from the public faction
> counts (`Agents/rules/board_clocks.py`); the July text said they would stay model-filled. And the query
> prompt is now handed every computed value as a known board fact before the model writes
> (`_known_board_facts`), so the stakes prose is written from the true numbers. The July residual (prose
> derived from the model's own wrong numbers) is therefore mitigated, though the prose itself is still
> the model's and is not overwritten. The override now normally changes nothing; it fires only when a
> model ignores the stated fact, and `_log_dim_override` records those cases. No count of them was found
> in the records. `uses_left` for the ten-seat limited-use roles is computed the same way.

### 5c. The stored uses-left check (2026-10-12, ten-seat)

**What it is.** On the stored side the numbers are still written by the extraction model, because an
observation drawn from a whole game has no single board to compute from. The July spoke rated the stored
side as not checkable offline. In October 2026 one stored field was checked: the count of a limited
ability's uses left (`uses_left`, or the vigilante's `bullets_left`), which the ten-seat stage filter
compares as "some left or none".

**How it works.** For each observation carrying the field, the true count is replayed from the game's
nights with the engine's own spending rule (`resolution._spent`) and compared. No model is involved. No
standalone runner was found; the record is the v8 log
([`../../memory_system/v8/experiment_log.md`](../../memory_system/v8/experiment_log.md), the entries of
2026-10-12).

**What it showed.**

| Extraction | Observations checked | Exact | "Some vs none" wrong |
|---|---|---|---|
| Seeding games, before the definition said "before acting" | 196 | 165 (84%) | 7 (3.6%) |
| 19 games re-extracted on Gemini 3.8 Flash, after the definition | 527 | 471 (89%) | 23 (4.4%) |
| 5 of the games extracted on Claude Sonnet 5.5 | 191 | 74% | 5.8% |

Most errors gave the count after the night's action instead of before it. The "some vs none" errors were
mostly a last use written as 0, which would hide a "spend your last one" lesson from the seats it is for.
Rewording the definition raised exact agreement but did not fix the comparison the stage filter makes.
The record's conclusion is to compute the count from the record once each observation names its
decision (the decision tags, now in [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md), the decision-tag read).

**Limits.** The check covers one field. The other stored numbers have only had internal-consistency
bounds (for example `|distance_to_parity| ≤ players_alive`, passed 100% on v6_1 in July), which rule
out gross corruption but not the errors found here.

### 5d. The verdict halo (2026-10-13, ten-seat)

**What it is.** Each observation carries `net_verdict` (positive, negative, mixed or unclear), written by
the extraction model from the end of the game. It reaches synthesis (which weights a cluster by the
spread of its verdicts), dedup (two observations with different verdicts are never merged) and the
replay page; never a seat, never credit. An *outcome halo* is a verdict that grades whether the side won
rather than whether the decision was good. The July 2026 case study
([`../../extraction/observation_quality/outcome_halo_case_study.md`](../../extraction/observation_quality/outcome_halo_case_study.md))
showed it on one human-seat game and named the test that would measure it. A *de-halo* pass, a second
model call that revises verdicts, had been spot-checked on one smoke game only.

**How it works.** `evaluation/experiments/v8_verdict_halo.py`, no model calls. Each verdict is coded
+1, −1 or 0 and fitted by least squares against two predictors: the deterministic grade of the decision
and whether the observer's side won. The grade comes from the ten-seat grading table
(`Agents/memory/consolidation/grading.py`: each turn graded ideal, neutral or undesirable from the game
record, an owner ruling). Two grains:
- **per role per game** (the first run): 482 night and vote observations from 19 games, before
  observations named their decision;
- **per observation** (`--grain observation`): 1,472 graded observations from all 40 games, each against
  the grade of its own decision.

**What it showed.** The verdict follows the side's win about twice as strongly as the decision.

| Grain | Weight on the grade | Weight on the side winning |
|---|---|---|
| Per role per game, as extracted (482) | +0.33 | +0.74 |
| Per role per game, after de-halo | +0.29 | +0.50 |
| Per observation, as extracted (1,472) | +0.40 | +0.80 |
| Per observation, after de-halo | +0.36 | +0.53 |

De-halo removes about a third of the win weight, and on one side: the losing side's negatives fall from
53% to 27%, mostly to "unclear", while the winning side's positives barely move (57% to 54%). The owner's
ruling followed from it: every observation names its decision, both the verdict and the grade are
stored, and which one synthesis reads is a setting (`TickConfig.synth_outcome`). Record:
[`../../memory_system/v8/decisions.md`](../../memory_system/v8/decisions.md) §13; data
`memory_system/v8/data/halo/` (`summary.json`, `observation_summary.json`, one row per observation).

**How far to trust it.**
- **The reference is a rule table, not a validated measure.** The fit says how far the verdict tracks
  the grading table. The table's own validity on the ten-seat game is not established: no play metric is
  re-validated on ten seats yet (`VALIDATED_ON_TEN_SEAT_METRICS` is empty in `Agents/compute_metrics.py`).
- **A linear fit to a three-valued code,** with observations correlated within a game. The records give
  the weights without intervals. The direction repeated across both grains and all three phases (day
  vote and discussion weigh the win at +0.84 each, night at +0.66), which is the strongest evidence that
  it is not noise.
- **Agent-only games on one extraction model per run** (Gemini 3.8 Flash for the 19-game fit). Whether a
  grade-reading synthesis writes better lessons than a verdict-reading one is not measured; the record
  estimates a fair test needs on the order of 1,000 follows per variant.

### 5e. Gaps (current 2026-10-23)

1. **⏸ The category labels on stored lessons are unvalidated.** `exposure_class`, `info_landscape_class`
   and their kin have no deterministic truth and were never checked against a human reading. The
   ten-seat query no longer writes them, but the offline duplicate check still splits on them. One is
   lopsided: in July, villagers marked themselves `safe` 2,164 times against 134 `exposed`.
2. **⚠️ Stored numerics beyond uses left have no truth check.** A stored lesson has no single board, so
   only consistency bounds apply. The planned fix computes stored counts from each observation's tagged
   decision (§5c; the decision tags are in [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md)).
3. **The verdict halo is measured against an unvalidated grade** (§5d). It shows the verdict follows the
   win; it cannot say the grade is the right measure of a good decision.
4. **The model-written prose is not audited.** The situation text on both sides and the observation's
   end-of-game rationale (`impact_on_final_game_outcome`) are read only by the sampled reads catalogued
   in [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md) (for example, the 40-game store read
   found 37 of 605 points stating a wrong rule). De-halo rewrites the verdict word, not that rationale.

---

## Cross-cutting limits

- **A code check finds only what it encodes.** The leak checks key on structured fields. The deduction
  oracle shares the engine's written rules. The record audits use keyword matching wherever the question
  is about meaning. Each section above names its own blind spot.
- **Automatic only inside the batch runner.** The leak checks and the embedding check run on every batch
  game. The website audit is not scheduled. No test runs in CI. So a regression is caught only when
  someone runs pytest, or at the next batch.
- **Seat count.**
  - The leak checks, the payload tests and the tests of what each player is told cover the ten-seat
    game. The leak checks also read nine-seat logs.
  - The deduction engine is ten-seat only. It runs only for the dealt roles and use limits it was
    verified for (`Agents/deduction/verified.py`).
  - The record audits and the pivotal-turn flags are nine-seat only.

## What would make these stronger

These are on the owner's pending list in [`writeup/_planning/map.md`](../../../writeup/_planning/map.md). They are not
scheduled.

- **Install the nightly `leak-audit` cron.** The line is in the module docstring. This would turn §1c from
  built into running. It is an outward change to the host, so it needs the owner's yes.
- **Add a pytest CI workflow over the deterministic tests.** It would include every test file named here.
  None of them calls a model.

A third gap has no plan: an assertion that the memory namespace served matches the role that asked. It is
the top open item in `agent_boundaries/report.md` §5. No plan for it was found.

## Sources

| What | Code | Record |
|---|---|---|
| Batch leak checks | `tests/leak_test.py`; `scripts/run_batch.py` (wiring, `leak_check` field); capture runners in `evaluation/experiments/` | `evidence/agent_boundaries/report.md` §3–5; `experiment_log.md`; `leakwire_smoke.log`, `leakfix_smoke.log` |
| Payload leak tests | `tests/engine/test_{round,night}_payload_leaks.py`, `test_wolf_channel_day_visibility.py`, `test_night_whiff_disclosure.py` | `agent_boundaries/report.md` §3, §5 |
| Live-site leak audit | `server/housekeeping/leak_audit.py`, `server/storage/prompt_captures.py`, `tests/server/test_leak_audit.py` | `agent_boundaries/report.md` §3, §5; `server/README.md`; cron status: `writeup/_planning/map.md` (checked 2026-10-23) |
| What each player is told | `tests/engine/test_information_fidelity.py` | `evidence/gameplay/discussion_evidence.md` §6.4–6.5; `../factual_errors/experiment_log.md` §8 |
| Deduction soundness and exhaustive check | `tests/engine/deduction/`; `tests/factories/{random_nights,random_claims,role_assignments}.py` | `evidence/gameplay/deduction/report.md` §2, §4; `deduction_catalogue.md` "Build verification", "Build status" |
| Acceptance cases | `tests/engine/deduction/test_acceptance.py` | `deduction_catalogue.md` "Acceptance cases" |
| Solver count | `evaluation/experiments/deduction_solver_census.py` (untracked 2026-10-23) | `gameplay/deduction/report.md` §4; `data/solver_census/census.json` |
| Prompt-size count | `evaluation/experiments/deduction_block_census.py` | `deduction_catalogue.md` slice 8; `data/deduction_block_census/` |
| Speaking-order audit | `evaluation/src/audits/scheduler_access_audit.py`; `tests/evaluation/test_scheduler_access_audit.py` | `evidence/metrics/metrics_audit/scheduler_bias_log.md` §3 A–C; `metrics_audit/data/` |
| Failed-attack audit | `evaluation/src/audits/whiff_conversion_audit.py`; `tests/evaluation/test_whiff_conversion_audit.py` | `scheduler_bias_log.md` ③.E; `metrics_audit/data/whiff_conversion.json` |
| Pivotal-turn flags | `evaluation/src/audits/recall_flags.py` | `evidence/memory_system/v7/extraction_coverage_ab_spec.md`; `memory_system/v7/experiment_log.md` |
| Embedding check | `evaluation/src/audits/embedding_canary.py`, `embedding_canary_pins.json`; `scripts/run_batch.py` | `../hardening_pass/experiment_log.md` §4.9 |
| Memory search filters, recomputed (§5a–b) | `evaluation/src/instrument_validation/dimensions/dimension_audit.py`; `Agents/memory/retrieval/situation_agent.py` (`_computed_dims`, `_override_deterministic_dims`); truth in `Agents/memory/consolidation/decision_scoring.py`, `Agents/rules/board_clocks.py` | `extraction/situation_dimensions/dimension_accuracy_audit/experiment_log.md` §4–6 |
| Stored uses-left check (§5c) | no standalone runner found | `memory_system/v8/experiment_log.md`, entries of 2026-10-12 |
| Verdict halo (§5d) | `evaluation/experiments/v8_verdict_halo.py`; grader `Agents/memory/consolidation/grading.py` | `memory_system/v8/decisions.md` §13; `memory_system/v8/data/halo/` |

*Written 2026-10-23 against the working tree on `feature-frontend-v1`. HEAD was `1a5c0da1`, with
uncommitted edits to `Agents/deduction/` and its tests. Every test file named here passed when run that
day. This file says how far each check can be trusted. Whether the boundary holds and whether the engine
helps are answered in the design folders linked from [report.md](report.md).*
