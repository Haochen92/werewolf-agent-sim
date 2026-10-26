# Learning behavioural tells: discovery kept apart from measurement

**Scope:** how the project learned *tells* (public behaviours that hint at a player's hidden role) from finished games: a model proposes behaviours, a detector that cannot see roles counts them in other games, and code joins the revealed roles afterwards. The work was built and tested in July 2026 for the older nine-seat game. It is research only: the ten-seat game does not use it.
**Revised against the code:** 2026-10-22 at `c0732f88`.
**Companion docs:** [build log](experiment_log.md) (the July experiments in date order) · [credit report](../../credit/report.md) §4 (why beliefs and tactics are scored apart) · [design record](../../credit/read_tactic_credit_redesign.md) · [tell store](../../store_curation/tells.md) (how the corpus is curated) · [caching report](../../caching/report.md) §4.7 (the detector's cost tradeoff).

> **Orientation: one behaviour's path from a game to a prompt.**
>
> **finished games → a model proposes candidate behaviours (it may see the roles) → a detector scans *other* games for a fixed checklist of those behaviours (it cannot see the roles) → code joins the roles revealed at game end and counts → the strongest associations form a small *tell book* → the book can be shown to agents before they state their suspicions**
>
> Everything below hangs on this path. Steps two and three are deliberately done by different calls with different inputs. That split is the point of the design.

---

## 1. What a tell is, and why discovery cannot be the measurement

Werewolf is a game of hidden roles. Each turn, an agent states its *reads*: its suspicions about which hidden role each other player holds. A tell is a claim that can improve those reads: "players who do X are usually role Y." Here is one from the project's tell book:

> A player asserts high confidence in an accusation while refusing to disclose the source of their information.

In the games where it was counted, 11 players did this, and 10 of them were the investigator.

The obvious way to find tells is to show a model finished games with the roles revealed and ask it what the wolves did differently. That finds interesting candidates, but it cannot say how predictive they are. A model that knows who the wolves were notices a wolf deflecting an accusation. It does not go back and count the villagers who deflected in the same way and were never suspected. Its examples are chosen with hindsight, so its counts lean towards the pattern it expected.

The design therefore gives three jobs to three steps, each with only the inputs its job needs:

1. **Propose.** A *miner* (a model call) reads one game-day of the public record, with the true roles in a header, and proposes behaviours. Its output is only a list of candidates. Its counts are never used to score anything.
2. **Detect.** A *detector* (a separate model call) reads the public transcript of a different game, with no role header and no private night reasoning. For each player it marks which behaviours on a fixed checklist that player showed, with a quote as evidence. It also records every player it scanned, so the count of players who did *not* show a behaviour exists too.
3. **Join and count.** Code, not a model, attaches each detected player's revealed role and counts how often the behaviour came from each role.

This keeps the hidden labels out of detection. It does not make the detector unbiased: a vague description or a misread relationship can still produce errors that correlate with role. §4 reports how far that was checked.

**A candidate must describe public behaviour.** "Votes for their accuser" can be checked from the transcript by someone who does not know the roles. "Defends their packmate" cannot: it asserts a hidden relationship. Role words are allowed only as public events, such as "claims to be the investigator" or "revealed on death as a wolf". The test is whether a reader who cannot see the roles could check the behaviour, not whether the sentence contains a role name.

## 2. What each step produces

### The miner proposes

For each game-day the miner makes two calls. The discussion call leaves out that day's vote tally, because the compact vote list otherwise drew the cheap model's attention away from the talk. The vote call keeps the discussion, because many voting patterns refer to what was said first ("votes without having voiced suspicion"). Each candidate names the player who showed it, the channel (discussion or vote) and a verbatim quote. A real candidate from a July game, with the role joined afterwards from the game record:

> **Behaviour (vote):** "A player who is the primary subject of discussion and accused by others chooses to abstain rather than voting for an alternative or voting for their accuser."
> **Evidence:** "player_4 voted for abstain" · game `678cdb3f`, day 4 · player_4 was a wolf.

Candidates go into a shared corpus. Wordings that describe the same behaviour are merged across roles within a channel, because a behaviour split by role could not be compared between roles.

### The detector counts

The detector takes up to 48 behaviours per channel from the corpus as its checklist and scans each player of each game. It runs twice per game with two views of the record: the full record, and one where the discussion is read without the vote tallies. The two passes' detections are combined. A real detection:

> **Behaviour `disc_67`:** "A player suggests that current accusations against them are merely a diversionary tactic used by others to avoid scrutiny on their own current behavior."
> **Detected:** player_4, game `678cdb3f`, day 3: "Player 8, asking me for 'value' after you spent the start of this discussion trying to get someone lynched with a fabricated claim is ironic."

### Code joins roles and scores

Each distinct player in each game counts once per behaviour, however many days they showed it. A behaviour's score is how much more often its exhibitors held a role than that role's share of the seats, pulled towards zero when there are few exhibitors.

> **The score**, for a behaviour shown by *n* players of whom *c* held the subject role, where the role holds share *p* of the seats:
>
> ```text
> score = (c + 5p) / (n + 5) − p
> ```
>
> Worked example (recomputed here from the book entry's fields): one investigator in nine seats gives p = 1/9; c = 10, n = 11 gives (10 + 0.56) / 16 − 0.11 = 0.549. The book records 0.5486, its highest score.
> Code: `subject_lift` and `lift_table` in `evaluation/src/loop/tell_credit.py`.

The damping (five imaginary exhibitors at the seat share) stops a behaviour seen twice from topping the list. It does not correct for testing many candidates or for games being related (§4).

### The book is a short prompt block

The book keeps, for each role and channel, the three highest-scoring behaviours with at least eight exhibitors and a positive score. It includes town roles. That is deliberate: the same book lets a wolf spot the investigator and lets the investigator see what gives it away. At each turn, entries about a role whose holders are all revealed dead are dropped. The block sits just above the instruction to state reads, in the day discussion, day vote and night prompts. Every seat in the game sees the same block. Its format, from `Agents/memory/tell_book.py`, with the entry above:

> == Behavior tells from past games (public study notes: how a behavior correlated with hidden roles) ==
> - A player asserts high confidence in an accusation while refusing to disclose the source of their information. (the exhibitor was a investigator 10/11 times observed)
> - …
> Use these as priors when forming your reads: a matching behavior shifts suspicion by the strength shown, it never proves a role.

### The work stays bounded as the corpus grows

New wordings kept arriving in every game (§5), so the corpus is never scanned whole. It has three tiers:

| Tier | What membership allows | Size |
|---|---|---|
| Book | Shown to agents | Up to 3 per role and channel |
| Active checklist | Scanned by the detector in each new game, including candidates not yet in the book | 48 per channel |
| Archive | Kept, and can return to the checklist | Not capped |

Every ten games a curation pass, the *fold*, matches new wordings against existing entries (an embedding search, then a model judgment), admits genuinely new ones on probation and publishes the next checklist. It never rewrites an existing entry's text, so an entry's counts always describe the same sentence. A stronger periodic review that would merge or split established entries was designed but is not wired into the loop.

## 3. What runs today

| Part | Where | Status |
|---|---|---|
| The prompt hook | `Agents/memory/tell_book.py`, slot `{tell_book}` in the day discussion, day vote and night templates | In the live prompts, but renders nothing unless the `WW_TELL_BOOK` environment variable names a book file. Nothing in `server/` or its deployment sets it. Its four unit tests pass at `c0732f88`. |
| Mining, detection, scoring, the fold | `evaluation/src/loop/` (`tells.py`, `tell_credit.py`, `tell_fold.py`) | Research loop for the nine-seat game. Off by default (`LoopConfig.tells = False`). |
| Seed books | `evaluation/frozen_eval_sets/tell_book_v1_seed.json` (12 entries), `tell_book_v2_seed.json` (34 entries) | Frozen July artifacts. The current hook cannot read v1: it expects fields that v1 names differently. |

The books do not fit the ten-seat game. They were counted on nine-seat games, whose roles included "wolf" and "villager". The ten-seat game has neither role name: its wolves are the Chanteuse and the Illusionist. Pointed at the 34-entry book, the hook would silently drop the 12 wolf and villager entries, and the remaining 22 would show nine-seat statistics. No ten-seat game has been mined or scanned. The hook is also independent of the ordinary memory switch, so turning memory on does not turn tells on.

## 4. How well each step was checked

Each check answers a narrower question than "do tells help agents play". All were run on the nine-seat game in July 2026, with Gemini models for mining and detection.

**Can a cheap model propose behaviours?** On the same five games, a single call per day to Gemini 3.1 Flash-Lite produced 116 candidates, and none of its wordings recurred across games. With the two-call split, it produced 213 candidates, with 19 rows in groups of exactly repeated wording. The larger Gemini 2.5 Pro, single call, gave 181 and 24. Recurring wording matters because it lets identical behaviours merge without a paid judgment. These are yields, not accuracy: review still found an inferred motive in about 1–2% of candidates.

**Does the detector find what is there?** On 40 labelled cases from five games, the combined detector was right on 0.93 of its discussion detections and found 87% of the labelled discussion behaviours. On votes the figures were 0.83 and 77%. The labels came from model adjudicators who did not see the detector's answers. The sample is small and partly drawn from the detector's own detections, so it supports using the detector experimentally, not a general accuracy claim.

**Does a human agree?** The project owner reviewed every detection in one game: 7 of 8 were upheld. One was rejected because its wording ("at the last moment") implied a change of heart the transcript did not show. A six-game human benchmark had been planned. After this one game the model labels were accepted as provisional and the rest was not done.

**Do the behaviours predict roles in games the miner never saw?** The detector scanned 60 games: 12 deals, each played under five memory settings, giving 5,151 detections. Some associations were strong. Evil players (two wolves and a lone killer) held a third of the seats:

| Behaviour | Exhibitors who were evil |
|---|---|
| Counter-accuses an accuser of using a role claim as a distraction | 27 of 30 |
| Discourages the group from relying on voting records | 41 of 48 |
| Calls the accusations against them a diversion | 60 of 76 |
| Publicly claims a special role | 0 of 28 |

Three things limit how far this reaches. The 60 games share 12 deals, so they are not 60 independent samples. About 96 behaviours were scanned, so a few strong-looking ones will be luck. And these are habits of the agents of that time: in these games no evil player faked a role claim, which a prompt or model change could easily alter.

**Does the book change an agent's decision?** Forty recorded day votes from older nine-seat games were replayed twice through the real prompt path, once with the 12-entry book and once without, with no other memory. A vote counts as correct if a town player voted for an evil one, or an evil player for a town one. The book changed 11 of the 40 votes. Correct votes went from 20 to 24: five changed from wrong to right and one from right to wrong. The direction favours the book. With six votes that changed correctness, the size is not established (the one-sided chance of a split this lopsided is about 11%). This shows the channel reaches decisions. The 34-entry book was built afterwards and never replayed this way.

**Does caching the detector change its answers?** Caching the shared transcript and checklist made repeated runs agree less (rows matched 0.56–0.83 between identical runs, against 0.90–1.00 uncached). Accuracy on the 40 cases was comparable, so caching became the default and every evaluation keeps the detector's stored output. The [caching report](../../caching/report.md) §4.7 has the detail.

## 5. Case study: the vocabulary that never stopped growing

**Verdict.** A 30-game simulation showed that new wordings never levelled off, but the behaviours that recurred formed a much smaller core. The design response was to cap active measurement and move duplicate judgment from every game to a batch every ten games. The experiment changed how the system spends its work, not a threshold.

**What happened.** The original plan was to mine a large sweep once and treat the result as a finished dictionary. To test that, 1,109 mined candidates from 30 games were replayed in order through the proposed curation rules. They produced 740 entries, and new ones were still arriving at about 22 a game in games 21–30. The simulation used mined recurrence, not detection, so it tested storage, not accuracy.

**Why.** Two explanations fitted. Either agents really kept inventing new behaviour, or the per-game duplicate judge was missing duplicates. The second had evidence: one leading behaviour sat in the store under three separate wordings, seen 18, 11 and 10 times. A strong model then reviewed each channel's whole corpus at once. It reduced 740 entries to 596. New entries still arrived at about 16 a game. But the share of each batch of new entries that was ever seen again fell from 37% (games 1–10) to 19% (11–20) to 11% (21–25). Most new entries were one-offs. Later batches had less time to recur, so this does not prove the core had stopped growing.

**The fix.** Three changes followed. The checklist is capped at 48 per channel, with an archive behind it, so detection cost depends on the number of games, not the corpus size. The per-game duplicate judge was retired: it had made 5,350 calls in 30 games (about 178 a game) and still split the leading behaviours that the batch review reunited. Its job moved to the fold every ten games. No agent needs a newly mined tell in the same game, so the delay costs little. Finally, an entry's text is never rewritten, so a reworded entry cannot inherit evidence gathered for a different sentence.

**What it shows.** When the corpus behaves differently from the plan, the fix can be to bound the work and move judgment to where it sees more context, rather than to tune a similarity threshold.

**Limits.** The core's size was measured on 30 games of one game version. The stronger review that would merge or split established entries is not wired, so duplicates can still split one behaviour's evidence between entries.

## 6. What is not established

- **No gameplay benefit.** The only full-game test that included tells was the July 30-deal test of the learning memory: its memory-on games carried a 33-entry tell book alongside the town's lessons. In that test the town decided worse with memory than without, by a margin that chance would produce about 6% of the time (see the [execution-plan report](../../memory_system/v7/execution_plan/report.md) §5). The design was amended before the test so that it no longer separated tells from lessons, so the tells' own effect is unknown.
- **No transfer to the ten-seat game** or to today's models and prompts. Nothing has been mined or detected on ten-seat games (§3).
- **Detector accuracy** rests on 40 model-labelled cases and one human-checked game.
- **The 34-entry book** was never replay-tested.

## Sources and implementation

| What | Where |
|---|---|
| The prompt hook and roles-alive filter | `Agents/memory/tell_book.py`; slot in `Agents/prompts/` (`day_discuss`, `day_vote`, `night`); tests `tests/memory/test_tell_book_injection.py` |
| Mining and detection | `evaluation/src/loop/tells.py`; prompts in `evaluation/src/loop/tell_prompts/` |
| Score and book selection | `evaluation/src/loop/tell_credit.py` |
| The fold, checklist cap and probation | `evaluation/src/loop/tell_fold.py` |
| Loop switches (`tells`, seed checklist and book) | `evaluation/src/loop/config.py`; module map `evaluation/src/loop/README.md` |
| Book replay screen | `evaluation/src/replay/decision_screen/tell_book_screen.py`; results [`outputs/book_screen.json`](outputs/book_screen.json), [`outputs/book_screen_v2_balanced.json`](outputs/book_screen_v2_balanced.json) |
| Held-out association table (60 games) | [`outputs/heldout/provisional_lift_table.json`](outputs/heldout/provisional_lift_table.json) |
| Human spot-check | [`outputs/owner_golden/owner_verdicts.json`](outputs/owner_golden/owner_verdicts.json) |
| Lifecycle simulation and batch review | [`outputs/ledger_sim_metrics.jsonl`](outputs/ledger_sim_metrics.jsonl), [`outputs/consolidated_store.json`](outputs/consolidated_store.json) |
| Seed books | `evaluation/frozen_eval_sets/tell_book_v1_seed.json`, `tell_book_v2_seed.json` (built by the frozen [`scripts/build_seed_book.py`](scripts/build_seed_book.py)) |
| The July learning run and its 30-deal test | `batch_results/v7_compound_town5/` (`tell_store/`), `batch_results/v7_endpoint_ab/` (`config.json`, `tell_book_final.json`) |
| Probe scripts and prompt versions (frozen records) | [`scripts/`](scripts/), [`prompt_versions/`](prompt_versions/) |
