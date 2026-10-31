<!-- claims review of writeup/context_engineering/context_engineering.md by claude (opus), 2026-10-30T05:07Z -->

I checked the page against the deduction log and report, the turn-prompt and day-summary reports, the factual-error census and the decision-replay log. Ten claims need changes. The two most serious are the 75% → 92.5% interpretation and the Healer excerpt.

## 1. Findings

**1.**
- **Claim:** "a separate model reading only the written reasoning could name the player voted for 92.5% of the time, against 75%: the vote followed the player's own assessment more closely, though that does not show the assessment itself got better" (Connecting the assessment to the action)
- **Source checked:** `evidence/memory_system/effectiveness/decision_replay/experiment_log.md` §D (coherence, N=40) and "Adoption confound + reorder test" step 2; `evidence/memory_system/effectiveness/detailed_results.md` table at line 190.
- **Verdict:** unsupported inference. It also leaves out a limitation that changes how to read the result.
- **Why:**
  - The gain comes from fewer "unclear" answers, where the written reasoning never named anyone (25% → 5%). In the vote-first arm the vote never went against the reasoning (desync 0.00), so the vote did not "follow the assessment more closely". What changed is that the reasoning committed to a player more often.
  - The same study's judge-free 2×2 found that reasoning first lowered the vote score: memory off 0.40 → 0.26, memory on 0.35 → 0.11, 3 × N=100. Its summary records that the reorder "could flip a correct vote to wrong on bad content". That is stronger than "does not show the assessment got better".
- **Suggested scope:** "the written reasoning named the player it voted for more often (92.5% against 75%), but in the same replays votes landed on a real threat less often when reasoning came first, so this shows a tighter link between reasoning and vote, not better votes."

**2.**
- **Claim:** the Healer excerpt, "Your night actions: Night 1 (last night): You were roleblocked: your protection of player_5 did not happen. …". Later: "Take the Healer's turn above … Its night record, as the game first showed it, also said it had 'learned nothing tonight'" (What a player needs; Computing selected conclusions in code)
- **Source checked:** `evidence/gameplay/deduction/data/healer_model_compare/turn_engine_on.md` line 245 and the "Worked out for you" block at 262–265; `turn_engine_off.md` line 241; the folder's README.
- **Verdict:** conflicts with source.
- **Why:**
  - "Your protection of player_5 did not happen" exists only in today's engine-on rendering. The game showed "your action was not carried out and you learned nothing tonight".
  - The ellipsis cuts the engine's own conclusion ("so the Chanteuse, a wolf, came to you that night"), and the engine's "Worked out for you" block is dropped too.
  - The result is a turn that never existed, offered as "one real turn" and then used as the turn whose premises the player failed to connect.
- **Suggested scope:** take the night line from `turn_engine_off.md` (the record as played), or label the excerpt as today's rendering with the engine's lines removed.

**3.**
- **Claim:** "What decided between them was cost and waiting time: a larger model costs twenty times or more as much a game, and more thinking slows every turn, while the engine works out the certain step once, in code." (Computing selected conclusions in code)
- **Source checked:** `deduction/experiment_log.md` §2 (Decision pending), §8 (dated 2026-10-30, run for the write-up); `deduction/report.md` §1; `turn_prompt/report.md` decision 15.
- **Verdict:** unsupported inference (wrong order of events).
- **Why:**
  - The larger-model and high-thinking arms were run on 2026-10-30, after the engine was built, so they could not have decided between the options.
  - Sonnet had been ruled out earlier on cost alone.
  - More thinking is still an open decision: decision 15 says moving votes to `medium` "remains an open decision".
- **Suggested scope:** "The engine came first; this later replay shows a larger model or more thinking also gets there on this turn, but at about nineteen times the cost a game (Sonnet) or nearly three times the wait, where the engine works out the certain step once, in code."

**4.**
- **Claim:** "in the first, nine-player version of the game about 3% of public messages held one" (What a player needs)
- **Source checked:** `evidence/metrics/experiment_log.md` line 61 ("the old game: 8 players, 2 factions"); `turn_prompt/experiment_log.md` §5 ("an 8-player game after the 9-player expansion"); `factual_errors/report.md` step 1 (July 2026, nine-seat).
- **Verdict:** conflicts with source.
- **Why:** an eight-player, two-faction game came before the nine-player one. The census was taken on the July nine-player game, not the first version.
- **Suggested scope:** "in an earlier, nine-player version of the game (July)".

**5.**
- **Claim:** "the game's current model reported no reasoning tokens in 4 samples of 10, so it skipped that thinking" (Connecting the assessment to the action)
- **Source checked:** `deduction/experiment_log.md` §8 Result 1 ("zero reasoning tokens do not show that no reasoning happened"); the authoring prompt, EVIDENCE DISCIPLINE.
- **Verdict:** overstated.
- **Why:** zero reported reasoning tokens does not establish that no thinking happened. Both the source and the evidence rules say so explicitly.
- **Suggested scope:** drop "so it skipped that thinking" and keep "reported no reasoning tokens in 4 samples of 10".

**6.**
- **Claim:** "other low-cost models have also reported no reasoning tokens under an enforced format at their low settings" (Connecting the assessment to the action)
- **Source checked:** `deduction/experiment_log.md` §8 "What it shows"; `discussion_evidence.md` lines 886–891; `evaluation/model_admission/report.md` lines 196–204.
- **Verdict:** unsupported inference.
- **Why:**
  - The sentence implies the enforced format caused the zero. Gemini 3.5 Flash-Lite's zero at minimal and low was measured only with structured output, with no text-format arm, and the log says "none a like-for-like text-format comparison".
  - The forced-tool case is a different mechanism: the API does not allow thinking with a forced tool call.
- **Suggested scope:** add "though none of these was a like-for-like comparison", or remove the sentence.

**7.**
- **Claim:** table row "Its own night results … In the first version? yes; reworded as its own action on a named night" (What a player needs)
- **Source checked:** `turn_prompt/report.md` decision 3 (2026-10-03).
- **Verdict:** conflicts with source.
- **Why:** until October "the healer had no record of its own protections". The fix added "a private night record for every night actor, written by the engine". The page's featured role is the Healer.
- **Suggested scope:** "partly: results such as checks, yes; a record for every night actor (the Healer's protections) added in October".

**8.**
- **Claim:** "so did the game's own model at its highest thinking setting (9 in 10)" (Computing selected conclusions in code)
- **Source checked:** `deduction/experiment_log.md` §8 Result 2 (Haiku `high`).
- **Verdict:** unclear (needs the owner).
- **Why:** the run used `high`. Nothing records whether `high` is the highest effort level available for Haiku 5.5.
- **Suggested scope:** "at a higher thinking setting".

**9.**
- **Claim:** "a larger model costs twenty times or more as much a game" (Computing selected conclusions in code)
- **Source checked:** `deduction/experiment_log.md` §2 and §8 (Sonnet about $2.30 against $0.12); the page's own sources note ("about 19 times").
- **Verdict:** overstated (minor).
- **Why:** the only per-game figure is Sonnet at about 19 times. No per-game figure for Opus is recorded, though its per-call cost on this case was higher.
- **Suggested scope:** "about twenty times as much a game".

**10.**
- **Claim:** "The rules state in full what each ability shows, because players filled any gap with a rule of their own." (Making the facts understandable)
- **Source checked:** `turn_prompt/report.md` decision 4.
- **Verdict:** overstated (minor).
- **Why:** the record shows specific games turning on rules the prompts did not state. It does not show that every gap was filled.
- **Suggested scope:** "because players filled gaps with rules of their own".

## 2. Checked and supported
- Census: about 3% of public messages (68 of 2,292). Lies were labelled separately from mistakes (`factual_errors/report.md`, "What does not count", step 1). Only the "first version" wording is wrong (finding 4).
- A correct "roles still in play" line did not stop a player hunting "the remaining wolf" (`turn_prompt/experiment_log.md` §10.2; `turn_prompt/report.md` decision 1, T1b).
- Board plus reads, tested as a bundle: 48% → 30% on 100 error-prone contexts (`turn_prompt/report.md` decision 1). It is credited to the pair, not to reads alone.
- After-action lesson labels read as rationalisations; credit for the 92.5% is shared by both changes, with the "earlier model" scoping (`turn_prompt/report.md` decision 10; decision_replay §D, N=40, gemini-3.1-flash-lite).
- Today's answer order is reads, verdicts (only when lessons are shown), note, then action (`turn_prompt/report.md` "What the seat must answer"; decision 10, Haiku 24 of 24 after the reorder).
- Sentinel: a player argued the Sentinel should appear in its own visitor list. The real Sentinel conceded and was voted out in three of four games, and the replay went 10/10 → 0/10 with the missing sentence (`discussion_evidence.md` §8.4; `turn_prompt/report.md` decision 4).
- Three blocks of earlier days, by author; the claims example line quoted verbatim; the ledger stays silent where the record fits more than one reading; a claim the record cannot contradict stays a claim (`day_summary/report.md` §3, §8).
- The summariser records and never judges; claims come from the speaker's fields, with the summary as fallback for a player who filled none, such as a human (`day_summary/report.md` §4; `turn_prompt/report.md` decision 13).
- e06: "I was roleblocked" was recorded as a Chanteuse claim. The speaker had set no claim field (a role field existed from 2026-10-09), it accepted the premise and was voted out 7 to 1. The fix covers both the summariser instruction and the ledger rule (`day_summary/report.md` §7; `day_summary/experiment_log.md` ③, commit `6248fc58`).
- Healer facts: roleblocked night 1; player_3 reported following player_7 to player_8 and player_7 admitted it; that is the only visit to the Healer reported (`turn_engine_on.md` transcript; `deduction/experiment_log.md` §4).
- Engine off 2/10 → engine on 8/10, Haiku at `low` in live mode; Sonnet 9/10 and Opus 10/10 with the engine off; Haiku `high` 9/10 at 17.4 s against 6.3 s. The comparison is scoped as replacing "learned nothing" plus adding general lines (`deduction/experiment_log.md` §8 Results 1–2 and scope note; `turn_engine_on.md` lines 245, 262–265).
- Naming player_7 is a suspicion, not a certainty, because another player could also have visited (`deduction/experiment_log.md` §4; `deduction/report.md` §2).
- Output mode: 0 reasoning tokens in 4 of 10 with the enforced schema, against every sample in `json_mode`; Haiku has sent the schema as text since 2026-10-14 (`deduction/experiment_log.md` §8 Result 1). Only the "so it skipped" inference is a problem (finding 5).
- The engine works from the seat's permitted view (`SeatView`), states each conclusion as certain, conditional or a list of possibilities, and has a test that changes hidden roles and requires the same output (`deduction/report.md` §2–§4).
- Authorship: the engine is AI-written; the owner set the requirements, the grading rule and the acceptance cases. The page says nothing about who wrote the tests, as the owner ruled (memory `project-code-authorship-split`).
- The strategy note carries the Healer's "stay quiet" stance forward after new evidence (`deduction/experiment_log.md` §5).
- Replay caveat: "not an error rate across whole games, which was not measured after these changes" (`turn_prompt/report.md` "What is not established"; `deduction/report.md` §5).
- Off-page items: none from the Handle-with-care list reached the copy. §8's run from uncommitted changes is not mentioned.

## 3. Not checked
- The "In the first version?" column for the strategy note and the day summary. The sources note cites `git log -S` (in the code from 2026-05-09; the project began 2026-05-01). I had no shell access to run git, so I could not confirm which prompt elements existed in the very first version.
- "I assumed a model could work out the rest from a context of this size." This is the owner's account of the first design, not something a record can confirm.
- Whether the July census games already had a dead-roster line on day prompts. `turn_prompt/experiment_log.md` §10.1 calls night "the one surface with no board at all", which is ambiguous. That bears only on the "added after miscounts" timing, not on the claim as worded.
