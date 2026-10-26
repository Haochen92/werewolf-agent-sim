# Post-game extraction: journey log (May to October 2026)

> **What this is.** The path from one extraction call per finished game, run inside the game, to
> today's offline job that makes one call per dealt role and phase. Entries are in date order. Later
> entries supersede earlier ones, and a design that was later dropped is shown where it happened.
>
> **Companion docs.** The current design, destination first: [`report.md`](report.md).
> This log condenses this folder's earlier `experiment_log.md` (the May study, with its
> original lab report as Appendix A) and `report.md`, both in git history at `2382b34c`,
> plus the extraction entries of [the v8 log](../../memory_system/v8/experiment_log.md) and
> [v8 decisions](../../memory_system/v8/decisions.md) §6, §11 and §13. Terms used below
> (observation, lesson, synthesis, halo, de-halo) are defined in the report §1 and §4.

---

## ① Motivation: the write side bounds everything downstream

When a game ends, a model reads its whole record and writes *observations*: short accounts of one
role's move, the board at that moment, and the result. They are what later synthesis turns into
advice. Nothing downstream can recover a moment extraction never wrote down, and a vague observation
("after a mislynch") matches every game and so helps none.

By May 2026 extraction was one call per game on Gemini 2.5 Pro, run at the end of every nine-seat
game, writing observations and per-game advice for all six roles at once. That was a reasonable first
design: one call, one prompt, and the strongest model available. Its output had not been measured.
Three silent failures were possible: vague situations, claims not in the record, and
advice that assumed knowledge the role could not have had in play. The workstream began by building a
judge to look for them.

## ② The prompt before the study

The prompt had already gone through three versions. The first never mentioned that observations would
be searched later, and its situations were vague. The second told the model that a situation would be
matched by semantic search, so it must name the conditions that made the moment distinctive. The third
moved that standard into a shared block, used by extraction, dedup and the query a seat sends to
memory, and split the situation into separate descriptive fields that are joined for search.

## ③ Verify → decide

**2026-05-24 · The judge, checked before it was trusted (48 games).** *Catches:* the risk that the
judge's low scores were the judge's fault, not the extractor's. An AI judge (Gemini 3.5 Flash) scored
48 nine-seat extractions from 1 to 5 on five qualities.

- The lowest score, epistemic compliance at 2.81, came from scoring observations against a rule meant
  for advice. Observations are written after the game with every role known; only advice is shown to a
  player in play. Scoping the rule to advice: 4.00.
- Specificity at 3.19 came from showing the judge the one-line situation only, while the search
  matches the situation with its descriptive fields. Showing it those fields: 3.88.
- With both fixed, the original qualities clustered at 4 on nearly every game. The judge could now
  flag a broken extraction but not rank two good ones.

*Decision:* both fixes kept. The judge stays a floor alarm, not a ranking; no human-labelled answer key
was built.

**2026-05-24 · Seat ids, counted by a script.** *Catches:* observations naming `player_2`, which
means nothing in another game. A script, not the judge, found seat ids in 306 of 363 observations
(84.3%). The prompt had said "you may use actual roles", which the model read as permission, not as a
ban on ids. *Fix:* a naming rule ("never use player IDs") with good and bad examples. *Result:* 0% on
Gemini 2.5 Pro and on most models tried; Gemini 2.5 Flash still leaked a few percent. *Decision:*
kept. The count became the standing check for every later model choice.

**2026-05-24 to 05-26 · A model bake-off (5 to 10 games per model).** *Catches:* the risk that a
cheaper model would extract as well as 2.5 Pro. Five Gemini models were scored by a second judge
(Gemini 3.1 Pro preview). 2.5 Pro and 3.5 Flash scored near the top; a preview model scored as high
but took about two minutes a game; 3.1 Flash Lite wrote a fixed four observations a game whatever
happened. The scores sat near the top of the scale and moved when the judging backend changed, so
only the order within one run meant anything. One assumption was
falsified on the way: giving Flash Lite a larger thinking budget made it slower and worse, not better.
*Decision:* 2.5 Pro stayed. None of these models is used today, so the bake-off's numbers are history.

**2026-05-26 · One call per role against one call for all (5 games).** *Catches:* the risk that one
call cannot give every role its share. Until then each game got a single call; the new design made
one call per role, all reading the same game, and merged the results.

- With Gemini 2.5 Pro, the judge scored healer coverage at 1.20 and investigator coverage at 1.40 out
  of 5 for the single call; 3.40 and 3.80 with a call per role.
- Asked to pick the better output per game and role, the judge chose the per-role output in 16 of 20
  pairings. The single call won only the villager, the role it already favoured.
- Five of the single call's eight healer observations were versions of one moment (night one, choose
  whom to protect).

*A metric that marked the winner down.* On the Flash models tried first, the judge scored the per-role
output lower on diversity: it read four roles' accounts of one event as repetition. A manual read of
the investigator's observations showed the opposite. With Flash Lite, the single call wrote one
investigator observation per game, and the per-role call wrote three or four, on choices the single
call never covered.

*Decision:* per-role extraction, made on the manual read and the coverage scores, not on the judge's
average. Five games of the nine-seat game; the direction is clear, the size is not.

**2026-06-10 · Per-role extraction built.** One call per role, run concurrently, all sharing a prefix
(the rules and the whole game record) that differs only in a short tail naming the role. *Problem:*
six calls would pay six times for the same input. *Fix:* an explicit Vertex context cache built once per
game; a probe read 5,520 of 5,648 input tokens from cache per call. Caching removed the repeated input,
not the extra output: six calls still write six answers, so per-role stayed dearer than one call.

**2026-06-17 · The verdict halo, found.** *Catches:* the risk that the one-word verdict on each
observation (did the move help?) only restated who won. On 932 nine-seat observations, 64% of the
winning side's verdicts were positive and 65% of the losing side's negative, with few "unclear". The
[selection study](../observation_quality/) read this as the verdict mostly answering "did your side win?". A
later case on a game the project owner played (2026-07-26) showed it with known intent. *Decision:*
named as an open problem; a fix was proposed and not built before the nine-seat research closed.

**2026-06-19 · From roles to role-and-phase cells.** Each role's call was split into a day call and a
night call, one per *cell*, so that each kind of decision got its own share of the answer.

**2026-06-19 · A model check on three games.** *Catches:* the risk that the learning loop, which
re-extracts every game, was paying for Pro when a Flash model would do. Gemini 2.5 Pro, 3.5 Flash and
3.1 Flash Lite re-extracted three nine-seat games (144, 165 and 123 observations). A manual read found
all three caught the same pivotal moments; Flash Lite was correct but thinner. A metric for recall
(the share of pivotal turns captured) scored Flash Lite at 25% against Pro's 100%, but it only credited
observations that stated a parseable count of living players, which Pro's longer sentences did. On the
cell the metric flagged most, Flash Lite had captured the same kill sequence. The same read found the
observations right on a point where the synthesized lesson had it backwards, so the check pointed the
effort at synthesis, not at the extraction model. *Decision:* the read was trusted over the metric,
which would need rebuilding before any recall claim. Three games; a direction only.

**2026-06-21 · Per-game advice dropped.** The extractor stopped writing advice for each game. A piece
of advice earns its place by holding across games, so lessons are now written only by synthesis over
clusters of observations from many games. Extraction writes observations only.

**2026-10-11 · Ten seats: a cheaper model.** *Catches:* the risk that the ten-seat game's extraction
would cost more than the game. On the four-game pilot, extraction cost $1.00–1.19 a game on 2.5 Pro,
mostly its thinking. Two pilot games were re-extracted with the same prompts:

| Model | Cost per game | Observations (two games) | With a seat id |
|---|---|---|---|
| Gemini 2.5 Pro | $1.16 / $1.19 | 45 / 52 | 6 / 4 |
| Gemini 3.8 Flash | ~$0.36 / ~$0.32 | 32 / 34 | 0 / 0 |
| Gemini 3.5 Flash Lite | ~$0.07 / ~$0.06 | 45 / 43 | 5 / 18 |

One reader judged 3.8 Flash specific and mechanically right, and 2.5 Pro not clearly better. A read of
the 66 Flash observations against the engine's records found one factual error, caused by the input:
the game state dropped the night record of a player who died that night. *Decision (owner):* 3.8 Flash.
The saved input now carries every night's full record.

**2026-10-11 · The day split into discussion and vote.** *Problem:* one day call per role filed nearly
every day observation under the vote, because a day's talk ends in one. The discussion cells, which an
evil player's talk retrieves from, were almost empty. *Fix:* separate discussion and vote calls, each
told what belongs to the other. *Check:* one pilot game re-extracted went from 0 discussion
observations to 16, at about $0.50 a game instead of $0.32. This is the May per-role finding again,
one level down.

**2026-10-11 · Halo in the verdicts, and the de-halo pass.** *Catches:* the risk that verdicts follow
the result. On one smoke game, about 21 of the winning town's 28 verdicts were positive and 7 of the
losing side's 11 negative, including day-two abstains credited with a kill days later. Two prompt rules
were added: outcome is not credit, and a vote that only joined the majority is skipped. One reading put
the halo at about half what it had been. A second model pass was then added to rewrite verdicts the
record does not support. Of four judges tried on 40 observations, Claude Haiku 5.5 caught all four
clear cases a reader flagged, wrongly erased none of three supported verdicts, and cost about $0.006 a
game. *Decision (owner):* de-halo on by default, on Haiku, as a deliberate exception to the rule of no
extra model calls.

**2026-10-12 · Extraction leaves the game.** *Problem:* extraction slowed and cost every game, and the
store needed more source games per stage of the game. *Decision (owner):* a finished game saves its
extraction input and calls no model. An offline job extracts saved inputs in batches. Past games were
rebuilt from their records; on the 12 seeding games the rebuilt inputs matched what live extraction had
used, apart from one wolf-chat vote line and the later notes of seats that died in the night.

**2026-10-12 · A Claude batch check, and a cache that did not fire.** *Catches:* the risk that a Claude
batch would cost more than Gemini online. Two games, Haiku 5.5 and Sonnet 5.5, thinking off, 30 calls a
game. No call read the cache: Claude counts the enforced output schema as part of the cached prefix,
and every cell has its own schema. Haiku wrote a seat id in 74 of 146 observations (51%); Sonnet in 9
of 136. *Fix:* the schema goes as text after the prefix and the reply is checked in code; a three-call
probe then wrote the prefix once and read it twice. *Decision:* Haiku is out for extraction. The owner
kept the job on 3.8 Flash while the Gemini credit lasted.

**2026-10-12 · The 40 ten-seat games extracted.**

- *19 games on 3.8 Flash* (online, explicit cache): $10.42, about $0.55 a game, 71% of it thinking;
  872 observations, 1 with a seat id; de-halo revised 25% of verdicts.
- *21 games on Sonnet 5.5* (batched, schema as text): $19.99 against an estimate of about $9.50;
  1,405 observations, 18 with a seat id (1.3%); de-halo revised 29%. *Problem:* about 15% of replies
  failed validation and were retried direct, each writing its own copy of the prefix ($7.02), and about
  15% of batched requests wrote the prefix instead of reading it ($3.01). *Fix:* failed replies now go
  through a second batch first; only what fails again goes direct. No run with this fix is recorded.
- The Sonnet games gave about 45% more observations each. The 2,277 observations, deduplicated on the
  way in, became the source of the ten-seat lesson store `ten_seat_v2`.

**2026-10-13 · The halo measured.** *Catches:* the risk that the de-halo pass only looked like it
worked on one game. On 482 night and vote observations of 19 games, each verdict was fitted against the
rule-based grade of the role's decisions and whether its side won. The side's win weighed +0.74 and
the grade +0.33; after de-halo, +0.50 and +0.29. The pass removed about a third of the halo, almost all
on the losing side (its negative verdicts 53% → 27%; the winners' positives 57% → 54%). Repeated per
observation on all 40 games, the picture held. *Decision (owner):* every observation names the decision
it describes and stores both the verdict and the decision's grade; which one synthesis reads is a
setting. Which gives better lessons is not measured.

**2026-10-15 · Sonnet becomes the default.** The Gemini credits ran out. The code's default extraction
model became Claude Sonnet 5.5, with Haiku 5.5 as the backup on the online path. The batch script's own
`--model` default was not changed and is still Haiku.

## ④ Remaining questions

- **Recall.** How much of a game's important play the job captures has no working measure; the one
  attempt (2026-06-19) was overturned by a read.
- **Verdict or grade.** Whether synthesis writes better lessons from the de-haloed verdict or from the
  rule-based grade. Both are stored.
- **The judge.** It has no human-labelled anchor and has not been run on ten-seat output.
- **Served games.** Writing a memory-on game's lessons back into its replay is not built.
- **Effect on play.** Nothing here measures whether better observations make better play.

---

**Sources.** This folder: [`experiment_log.md`](experiment_log.md) §1–§8 and Appendix A (Runs 1–3,
the bake-off, Phases 4–6); `eval_results/extraction_eval_20260524_*.jsonl`; `model_comparison/` and
`model_comparison/v7_refresh/README.md`; `flash_extraction_5games.txt`,
`pro_reextraction_playerid_fix.txt`. Elsewhere: [`../../caching/experiment_log.md`](../../caching/experiment_log.md)
§5 and §9; [`../../v7_final/extraction_coverage_ab_spec.md`](../../v7_final/extraction_coverage_ab_spec.md);
[the v8 log](../../memory_system/v8/experiment_log.md) (2026-10-11 to 10-13);
[v8 decisions](../../memory_system/v8/decisions.md) §6, §11, §13; commits `03a196b0`, `9d653363`
(2026-06-10), `e68d8d6c` (2026-06-19), `90b8b38f` (2026-06-21), `4948f914` (2026-10-11), `d839e6f3`
(2026-10-15).
