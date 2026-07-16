# Proxy Metrics — the memory A/B ruler, and how it works today

**Orientation.** This is the scoring layer that ranks *play skill* from finished games. It computes, for
every game, a fixed set of **per-role de-lucked outcome proxies** — decision-level rates scored against
the game's true hidden roles, each divided by the *opportunity* the agent actually had. Two properties make
it the ruler the whole eval rests on: the computation uses **zero LLM** — and the entire validated basket
reads only engine-recorded facts (votes, revealed roles, deaths, night targets; input provenance detailed in
§6) — so it runs post-hoc on any historical batch; and it is computed identically in the memory-on and
memory-off arms, so it can never favour one side of the A/B. A proxy is trusted only after it is shown to track its own
faction's win.

**Scope: this doc is the A/B ruler.** It covers the deterministic proxies — plus one semi-deterministic
diagnostic parsed from the agents' own in-game tags — that referee memory-on vs memory-off verdicts. The
credit system's LLM-tagged instruments inform the v7 compounding loop's *learning* signal, not A/B verdicts;
they are documented at their apparatus home ([`../discussion_tagger/report.md`](../discussion_tagger/report.md)),
and §5 is the boundary between the two.

> **Companion docs.** The path that produced this design is [experiment_log.md](experiment_log.md) (the
> v1 → v2 journey); the folder map is [README.md](README.md); and *which proxies are validated, and at what
> N*, is the apparatus-trust report [`../evaluation/metrics/report.md`](../evaluation/metrics/report.md).
> This doc lifts every trust verdict from that report — it does not re-derive them. Guiding principle: **a
> proxy grades decisions against ground truth at the grain where skill lives; win rate stays the headline,
> the basket is the variance-reducer.**

---

## 1. Why it exists

The system exists because the project's central claim needed a ruler. The memory pipeline's entire
justification is that episodic memory makes agents *play better* — and "better" has to be measured, or
every design iteration is judged by anecdote. The early eras did exactly that: v0 logged nothing (impact
was eyeballed from transcripts), and v1's LLM judges could describe memory quality but were subjective
and ran only in the memory arm, so they could never referee a memory-on vs memory-off comparison. That
left one objective, both-arm signal: the win. And the win is a poor ruler on its own. Here is how the
metrics layer is actually used against it: for every game, in both arms of a paired memory-on vs
memory-off A/B, it computes a fixed **basket** of decision-level proxies (§2), and the memory effect is
read as the per-proxy difference in the two arms' mean scores, with one pre-registered primary proxy per
construct (defined in §2) carrying the verdict. Denser, role-attributed signal is the whole point, because a real effect
then becomes visible at a feasible game count and can be *localized*: the readout says not just "memory
helped" but "town votes improved; healer saves did not."

A single game ends in one bit — one faction won — and that bit is heavy with luck. Which player the wolves
happened to target, which coin-flip a 50/50 vote landed on, and the hidden-role deal all move the result
without moving skill. To rank a design change off win rate alone at an affordable game count, you would need
hundreds of games to see a moderate effect through that noise. The metrics layer buys power a different way:
it extracts **many graded observations per game** — every vote, every night target, every healer
intercept — and grades each against the true roles. Dense signal has far lower per-game variance than the
lone win bit, so a real effect shows up at feasible N.

The luck reduction and the opportunity normalization are two different steps, and it is worth separating
them, because the house name for this layer hangs on only one of them.

**Step 1 — grade decisions, not outcomes.** Score each vote, save, and night kill against the true hidden
roles, and the luck the win bit carries falls away: the role draw, every other player's play, and the
downstream compounding of the game. A correct vote counts as correct even when the game is later lost on an
unrelated coin flip. This step is where most of the luck reduction actually happens.

**Step 2 — normalize by opportunity.** Divide each graded count by the chances the agent actually had. This
is normalization, not luck removal: it buys fairness across exposure. An agent that survived longer simply
had more chances to act, so a raw count confounds sheer volume with skill; dividing by opportunity removes
the volume, not the luck.

*Worked example — the healer.* Count "saves per game" and a healer who lived nine nights outscores one the
wolves killed on night 2, for no reason but survival. The proxy instead divides by `healer_action_nights` —
the nights the healer actually chose a protect target ([`compute_metrics.py`](../../Agents/compute_metrics.py)
`healer_town_save_rate`). Every action-night carries live attack pressure, because the wolves and the SK
always attack when they are alive, so an action-night *is* an opportunity by construction. The rate now
answers "of the protection chances this healer had, how many landed on a real threat to a townmate," which
is skill, not longevity.

**What remains, stated honestly.** One kind of luck survives both steps: per-decision *guess* luck. A
villager who votes blindly and happens to hit a wolf scores exactly like one who reasoned the read out. The
basket makes no attempt to separate luck from skill *inside* a single decision; that residue is zero-mean
noise, which the paired design averages out over N games rather than removing per decision. The one
instrument in the project that does attempt genuine per-decision luck-vs-skill separation is the credit-side
tagger (§5, §7), which grades the *reasoning* behind a night pick rather than whether the pick happened to
land.

**A note on the house label.** Throughout the project's code and records these are called the *de-lucked
proxies*, and this doc keeps that name because it is everywhere in the codebase. Read it as "less
luck-loaded than the win bit," not "luck-free": step 1 removes the outcome-lottery luck, step 2 is
opportunity normalization, and per-decision guess luck remains in the score.

**Trust by monotonicity.** A de-lucked rate is still only a *candidate* skill signal until it is shown to
move with winning. So every proxy is correlated (point-biserial) with its own faction's win across a real
batch, with the *expected sign* pre-registered; proxies that are flat or backwards are demoted out of the
basket. Faction win is the one ground-truth skill anchor that is not circular, which is why it is the judge
of the proxies rather than one of them.

One subtlety in that check is worth stating, and it is why several §2 rows report two figures — a pooled
n=50 and a memory-OFF-only n=30. The v5 validation ran on 50 games, of which 20 had memory ON. When the memory treatment lifts both a proxy and the
win, a pooled correlation across all 50 games is partly measuring "memory happened to be on in this game"
rather than "this skill wins games" — the two arms form two clusters that stretch the line. So the same
correlation is also read on the 30 memory-OFF games alone, where there is no treatment to drive anything. A
proxy that holds in both views, as the town rate proxies do, is validated free of that confound; a proxy
that holds only pooled is weaker.

## 2. The validated basket

These eleven fields are the trusted core — the set tagged `VALIDATED_BASKET_METRICS` in
[`compute_metrics.py`](../../Agents/compute_metrics.py) (line 622), the proxies that measure the memory
effect on decisions and that powered the static-memory proof. **Two validation campaigns stand behind the
figures, and each row's entry names its source.** The 2026-06-11 v5 check
([`proxy_win_monotonicity.md`](proxy_win_monotonicity.md)) ran on **50 games** — 30 memory-off plus 20
memory-on; its paired figures are *nested views of that one batch* (pooled n=50, and the 30 memory-OFF games
alone — §1's confound note), not two datasets. The 2026-07-02 audit ran on **180 games** of the current
3-faction epoch (v6ab). A row quoting n=50/n=30 was validated in the v5 campaign (all but the raw-count
`mislynches` were re-tested and held at N=180); a row quoting only N=180 was introduced or first validated
by the audit. Each figure is the point-biserial r of the proxy against its faction's win; both campaigns'
figures for every row are in the candidate ledger (§4). As of code at HEAD (2026-07-04) these eleven are exactly the
`VALIDATED_BASKET_METRICS` frozenset; its membership was last set by the 2026-07-02 N=180 audit's
promotions (the full field these were selected from is the candidate ledger in §4).

**How far to trust these figures on the next batch.** Every r here is an epoch-stamped estimate, not a
constant of the game. Three things move them: plain sampling noise (the v5 `found_wolf_day` wrong-sign
scare at n=30 dissolved to null at N=180; the vigilante promise went +0.43 → +0.18); behavioral epoch
drift — prompts, model version, backend, role set all change the game-generating process (the vigilante's
shot rate fell from 72% of v5 games to 29% of v6ab games, changing the opportunity structure itself); and
environment composition (the 77/180 wolves-can't-win share is a 3-faction-epoch property). What has already
survived a **cross-epoch replication** — the strongest robustness evidence available — is the town decision
cluster (+0.65 on both epochs) and the healer rate (+0.36 → +0.40); the conditioned and thin figures
(diagnostic and context tiers) should be read as epoch-local until re-confirmed. Standing rule: the
*definitions* transfer to any batch, the *figures* do not — the validation harness is deterministic and
recompute-only ($0), so re-run it on the first batch of any materially new epoch before citing basket trust
there.

| Proxy | Faction | Phase | What it measures | Opportunity denominator | Validation (lifted) |
|---|---|---|---|---|---|
| `town_vote_accuracy` | town | day vote | share of real town votes that hit a wolf/SK | non-abstain town votes | +0.62, p<0.001 (n=50); +0.57 (n=30) |
| ★ `correct_elimination_rate` | town | day vote | lynches of a threat (wolf+SK) over all lynches | total eliminations | +0.65, p<0.001 (both views) |
| `town_mislynch_rate` | town | day vote | lynches of a townmate over all lynches | total eliminations | −0.65, p<0.001 (both views) |
| `mislynches` | town | day vote | count of townmate lynches | (count, not a rate) | −0.57, p<0.001 (n=50); −0.55 (n=30) |
| ★ `serial_killer_lynched` | town | game flag | did the town remove the SK by day-vote (its only exit) | (0/1 flag) | +0.64 (n=50); +0.85 (n=30) |
| ★ `healer_town_save_rate` | town | night | intercepts of an attack on a townmate | healer action-nights | +0.36, p=0.010 (n=50); +0.33 (n=30) |
| ★ `investigator_find_to_lynch_rate` | town | night→day | confirmed wolves that reached a later lynch (conversion) | wolves confirmed | +0.40, p<0.001 (N=180) |
| ★ `wolf_unconditioned_blending_rate` | wolves | day vote | wolf votes aligned with the day's lynch (camouflage) | all living-wolf votes on lynch days | +0.27 (N=180) |
| ★ `sk_kill_rate` | serial killer | night | kills landed per night survived (survival-normalized offense) | SK nights survived | +0.258 (N=180) |
| `sk_power_roles_killed` | serial killer | night | SK night-kills that removed a town power role | (count) | +0.323 (N=180) |
| ★ `power_roles_killed_by_evil` | town | night | wolf+SK night-kills of power roles (town's protection failure) | (count, per-night victim-deduped) | −0.40 (N=180) vs wolf-only −0.21 |

**Eleven rows, six witnesses.** The town cluster is the trustworthy heart: `town_vote_accuracy`,
`correct_elimination_rate`, `town_mislynch_rate`, and `mislynches` all correlate with villager win at
|r|≈0.55–0.65, p<0.01, and the rate proxies hold in *both* the pooled and the treatment-free memory-off
view — the strongest and only unambiguously validated part of the basket. But eleven rows are not eleven
witnesses. Read for statistical independence, they collapse to **six constructs**, which forces one standing
rule up front: **triangulation counts constructs, not rows.** Five town rows moving together is one
construct speaking, not five, so any "several proxies agreed" claim in this project has to count constructs.

| # | Construct | Rows | Why the rows are one witness |
|---|---|---|---|
| 1 | Threat identification | `correct_elimination_rate`★, `town_mislynch_rate`, `mislynches`, `town_vote_accuracy` (plus `serial_killer_lynched`, coupled in as a subset event) | `correct_elimination_rate` and `town_mislynch_rate` are **exact complements** — both divide `total_eliminations`, and every lynch is either anti-town or town, so the two rates sum to 1 and correlate r=−1 by construction (`compute_metrics.py:516,518`); `mislynches` is the raw-count near-duplicate of the mislynch rate, kept as the historically pre-registered form; `town_vote_accuracy` is the per-vote grain of the same "town identifies threats" construct; `serial_killer_lynched` is a subset event (an SK lynch *is* an anti-town elimination), coupled here but earning its own ★ primary below |
| 2 | Healer night protection | `healer_town_save_rate`★ | single proxy |
| 3 | Investigator find→lynch transmission | `investigator_find_to_lynch_rate`★ | single proxy — the seat the channel earns through *conversion*, not finding (the find-rate proxies did not track wins, §3) |
| 4 | Wolf camouflage | `wolf_unconditioned_blending_rate`★ | single proxy |
| 5 | SK offense | `sk_kill_rate`★, `sk_power_roles_killed` | power-role kills are a subset of all kills; raw SK survival correlates +0.555 with SK win almost by definition, so the normalized `sk_kill_rate` carries the seat |
| 6 | Town power-role protection failure | `power_roles_killed_by_evil`★ | single proxy |

**Why `power_roles_killed_by_evil` is its own construct.** It is the outcome-side complement of healer night
protection: it counts the **landed** wolf and SK night-kills that removed a town power role, deduped per
night (`compute_metrics.py:254-261`). It earns a sixth construct rather than a second healer witness because
it has wider causes — it moves with enemy targeting, the healer's reads, and luck alike. The restriction to
*power* roles is a design choice, not a validated finding, because a generic town-night-death count has
almost no variance to correlate against (the wolves and SK land a kill on most nights by construction, so
only the power-role subset carries signal).

**Keep all eleven, mark one primary per construct.** Nothing above argues for *deleting* a proxy: each of
the eleven is the natural readout for some context (a rate for A/B power, a raw count for the historically
pre-registered form, a flag for the third-faction objective), all are computed for free, and dropping any of
them changes no statistic. The redundancy is a *reporting* hazard, not a computation one, so the fix is a
designation rather than a deletion. One proxy per construct is marked **★** in the §2 table as its
**pre-registered primary endpoint** — the single form that carries the claim and the multiple-comparison
count for that construct. The six constructs yield **seven** primaries, not six: `serial_killer_lynched`
gets its own ★ despite being a subset of threat identification, because it isolates the distinct
third-faction objective (the town removing the SK, its only exit). The typed `GameScore` projection (gap #4)
would enforce this one-per-construct discipline by construction, but it is unbuilt, so the ★ convention holds
the line until then.

**Why there is no vigilante row.** Not for lack of trying: seven vigilante candidates appear in the ledger
(§4) and none cleared the basket bar. The cause is structural — the role's two-bullet loadout makes shooting
a rare event, so the offense rates are undefined in the many games where the vigilante holds fire
(`vigilante_correct_shot_rate` exists in only 36 of the 50 v5 games and 21 of the 30 OFF games —
directionally promising there, but a 2026-07-07 re-test on the N=180 set found only 53 shooter games and
the promise diluted to +0.18, p=.20) and weak where always defined (the loadout-normalized
`vigilante_wolf_kills_rate`, +0.16 at N=180). The best-validated vigilante signal,
`vigilante_friendly_fire_shots` (v5 −0.29 / −0.36, direction held at N=180), is the *error* side, and the
audit rated the vigilante night pair "weak-but-informative" without promoting either form. Until a stronger
form validates, the ruler has no vigilante readout; the vigilante's decisions are still graded per-decision
in the loop's credit (§7).

## 3. Supporting tiers

Three tiers sort every computed field by *what a reader may do with it*. The basket (§2) is the top tier: a
basket field **may carry an A/B verdict**. The two lower tiers, both named as frozensets in
[`compute_metrics.py`](../../Agents/compute_metrics.py), exist to keep the other fields from being read as if
they could.

- **Diagnostic — may *explain* a verdict, never carry one.** A diagnostic field is legitimate context for
  *why* a basket proxy moved, but it is never counted as an independent witness in a triangulation.
- **Do-not-use — may do neither.** These fields are quarantined so they cannot be silently averaged into any
  conclusion.

**Diagnostic (`DIAGNOSTIC_METRICS`, 3 fields — line 642).** The subtlety worth stating: these fields *are*
win-validated on the N=180 audit set. The tier is not about validity; it is about *independence*. Each field
is conditioned on the environment, covaries with a basket proxy, or refines one, so citing it as a second
witness beside its basket sibling would double-count a single construct:

| Proxy | Validation (lifted, N=180) | Why diagnostic, not basket |
|---|---|---|
| `wolf_power_kill_rate` | +0.31 (p=.002, n=103, `sk_lynched=1` stratum); split-halves +0.26 / +0.38; pooled +0.13 (~null) | only expresses conditioned on `sk_lynched=1`; pooled it is diluted to null by the 77/180 games wolves cannot win (SK wins by default) |
| `town_accusation_precision` | +0.34 (p<.001, n=175); split-halves +0.30 / +0.39; covaries r=+0.558 with `town_vote_accuracy` | a genuinely different *surface* — accusations in discussion, upstream of votes, including players who never vote — but ~31% shared variance says it partly re-expresses the same "town IDs threats" construct, and the deciding test (2026-07-07 follow-up) found **no win signal beyond vote accuracy**: partial r = +0.02 (p=.76, n=175), halves −0.09/+0.17. It explains verdicts — localizing the construct upstream, on the discussion surface — but does not witness them |
| `investigator_find_next_round_convergence` | +0.306 (p=.001, n=117); split-halves +0.34 / +0.31 | a timing-sensitive refinement of the validated `investigator_find_to_lynch_rate`; its extra content is convergence *speed*, not a new signal |

**Why the discussion surface cannot witness for town — the mediation structure.** The partial-r null in
the `town_accusation_precision` row has a structural reading, not just a statistical one. For town, the
collective day vote is nearly the only actuator: discussion changes the outcome by *becoming votes*, so
`town_vote_accuracy` sits on the causal path between discussion quality and winning — a mediator, not a
confounder — and partialling out a mediator removes the causal route itself. Read that way, the null says
"no bypass path": whatever correct accusations contribute, they contribute by turning into votes (even the
conceivable non-vote channel — guiding the investigator's check or the vigilante's shot — is below detection
at n=175). It also makes a prediction: *any* town discussion proxy, however constructed, should partial to
~zero against win at game grain. An independent instrument agrees: the LLM tagger's discussion verdict,
partialled on the vote proxy, shows the same structure — **+0.02 town** vs **+0.56 wolf / +0.60 SK** (N=24;
a different instrument and sample, so qualitative agreement, lifted from
[`../discussion_tagger/report.md`](../discussion_tagger/report.md)) — because a deceiver's discussion acts on
*other players'* votes, a path its own vote proxy does not mediate. Two consequences, stated once: the ruler
loses nothing by having no town-discussion witness (full mediation means a real discussion improvement
*shows up in* `town_vote_accuracy`); and town discussion quality is teachable but not game-grain
measurable — its home is the decision-grain credit signal (§5, §7).

**Do-not-use** (`DO_NOT_USE_METRICS`, 5 fields — line 612). Every proxy carries a pre-registered expected
direction against its faction's win — finding wolves should help the town, so a find rate should correlate
*positively* with town wins. **Wrong-sign** means the measured correlation ran opposite to that registered
direction, so reading the field as skill would actively mislead; **uninterpretable** means no skill meaning
can be assigned to the number at all. The Langfuse push renames each quarantined field with a `dnu_` prefix
and a `tier="do_not_use"` tag so it can never be silently averaged into a verdict. Four of the five are the
investigator find-rate cluster: `investigator_threat_find_rate`, `investigator_wolf_find_rate`, and
`investigator_threat_find_lift` are flat-to-null in both campaigns, and `investigator_found_wolf_day`'s v5
wrong-sign scare dissolved to null at N=180 (gap #1) — so the cluster today is quarantined for nulls, not
robust backwardness. The fifth, `wolf_steering_rate`, is the uninterpretable case: in a deterministic parse,
a wolf voting where the town is already headed looks identical to a wolf that *drove* the town there, and
leading-versus-joining is a semantic question about the discussion's causal flow. The cheap explanation —
that wolves rarely get to speak — was tested and falsified (the scheduler audit, §8 note: wolves are among
the floor-richest speakers), so wolf day-offense is measurable only by an instrument that reads the
discussion, i.e. the LLM tagger (§5). Everything un-tiered defaults to `tier="diagnostic"` on push, so an
unvalidated field never masquerades as basket-grade.

### Cell coverage — the map the tiers don't show

The tiers answer "what may carry a verdict." They do not answer a question the memory pipeline needs
answered: **can every (role, phase) decision cell be read at all?** Memory is organized by cell, so a
per-cell A/B ("did wolf night memory improve wolf night decisions?") needs a per-cell readout. The map of
each cell's best deterministic readout:

| Cell | Best readout | Status |
|---|---|---|
| town · day vote | `correct_elimination_rate` ★ + the threat-identification cluster | basket |
| healer · night | `healer_town_save_rate` ★ | basket |
| investigator · night→day | `investigator_find_to_lynch_rate` ★ | basket — but the *pure night pick* has no validated readout: the find-rate cluster failed empirically (do-not-use above), so this cell is measurable only through conversion |
| wolf · day vote | `wolf_unconditioned_blending_rate` ★ | basket |
| SK · night | `sk_kill_rate` ★ | basket |
| wolf · night | `wolf_power_kill_rate` | diagnostic — expresses only in the `sk_lynched=1` environment; the event family is mirror-validated at basket strength from the town ledger (`power_roles_killed_by_evil` ★, −0.40) |
| vigilante · night | `vigilante_correct_shot_rate` | **logically-anchored decision endpoint** (below) — sign definitionally safe, win-linkage underpowered (+0.18 n.s., n=53) |
| SK · day vote | `sk_unconditioned_blending_rate` | context — suggestive (+0.20), sub-Bonferroni |
| all · day discussion | `town_accusation_precision` (town only) | diagnostic, and structurally mediated (the note above); deterministic wolf attempts failed (`wolf_steering_rate` do-not-use; `wolf_accusation_on_town_rate` sign-falsified) — discussion cells are the tagger's territory (§5) |

On the credit side, the tagger's night read-quality verdict additionally covers the four night cells'
*reasoning* (§7); this map is the deterministic ruler side only.

**The "logically-anchored decision endpoint" license (adopted 2026-07-07).** A small class of proxies has a
*definitionally closed* skill interpretation — a vigilante shot on evil is better than a shot on town by
game logic, with no empirical sign question — but a win-linkage too underpowered to validate, because the
action is a rare event (≤2 bullets, fired in 29% of current-epoch games). License: such a proxy **may read
its own cell in an A/B**, as a decision-quality endpoint pooled at *arm* level (rare events are compared by
pooling all shots per arm, not by per-game rates), and **may not carry the headline verdict** — that stays
with the win-validated basket. This is the same asymmetry credit already uses (§7): claims need empirical
validation; teaching and cell-local reads need sign-safety. The class deliberately does NOT cover proxies
whose sign is an empirical question (steering, blending) — those must earn seats through the gate, because
the find-rate cluster proved that obvious-sounding logic can hide a false step (finding wolves *sounded*
definitionally good; only conversion turned out to matter).

## 4. The full candidate ledger

The basket in §2 and the tiers in §3 are the *survivors* of a wider field. **Roughly four dozen distinct
proxy definitions were win-tested — 48 in all**, across two campaigns: 32 in the 2026-06-11 v5 monotonicity
check (pooled N=50 / memory-off-only N=30) and 16 more introduced or re-tested in the 2026-07-02 N=180
audit. **Eleven survived into the validated basket; three more became named diagnostics; five are
quarantined do-not-use** — the rest are validated-but-not-adopted context, rejected on a null or wrong sign,
or too degenerate to read. The full field — every candidate expanded with its definition, opportunity
denominator, both campaigns' figures, and why it landed in its tier, organized by tier then role — is its
own document: [`candidate_ledger.md`](candidate_ledger.md).

**Reading the ledger.** The five do-not-use rows, the two rejected wolf rows, and the four
degenerate/underpowered wolf-social rows are the honest cost of mining ~four dozen candidates — they are why
§2 counts *constructs, not proxies*, and why the multiple-comparison caveat (§8, gap #6) is load-bearing
rather than boilerplate.

## 5. The LLM-tagged family — the second instrument tier

> **Superseded as a credit source (2026-07-11, wiring pending).** The read/tactic credit redesign
> ([`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md))
> retires this family's one consumer role: the tagger becomes a **standing diagnostic** (its validated
> wolf/SK partial readout is what is kept), day-discussion credit adopts the validated day-vote
> **endpoint** (plus a move-grain advocacy rule) as *the* discussion credit rather than a fallback tier,
> and the night read-quality override is replaced by a read-partition over the deterministic outcome.
> The boundary rule below (tagger scores never referee the A/B) is unchanged — the family now simply has
> no credit role either. This section describes the as-built wiring until the rewiring lands.

Some of what makes play good is invisible to the engine's record. Whether a speech actually steered the
room, whether a night pick was a reasoned read or a blind stab — no vote count or death log grades those. A
second instrument family covers them: an LLM **tagger** reads the finished game's transcript and scores
exactly those channels. The rule that governs the whole family, stated before any of the history: **tagger
scores never referee the A/B; they only feed the learning loop's credit signal (§7).** That rule was set by
the v2 decision that created this system (the DECISION section of [experiment_log.md](experiment_log.md)
demoted every LLM-scored instrument out of the comparison basket). The family's apparatus record is
[`../discussion_tagger/`](../discussion_tagger/); its instrument-trust verdict lives in the eval
hub at [`../evaluation/discussion_tagger/`](../evaluation/discussion_tagger/).

**Where the blind spot is.** Discussion quality has no engine-resolvable ground truth, and the one
deterministic attempt at it — `town_accusation_precision` — turned out to re-express an existing basket proxy
(`town_vote_accuracy`, ~31% shared variance) rather than measure something new (gap #3); a 2026-07-07
partial-correlation follow-up made that direct (no win signal beyond the vote endpoint), and §3's mediation
note explains why it is structural for town — discussion acts only through the vote, so a better game-grain
discussion witness is not waiting to be found; what an LLM instrument buys is decision-grain teaching. A
small set of night cells has the same problem: the action has no mechanically-gradable right answer.

**Reason 1 — an LLM grader is not stable, and a verdict cannot absorb its bias.** A deterministic rate
computed on the same games returns the same answer forever; an LLM grader does not. Change the model version
or run it in a different month, and the scores can shift — call that drift. Worse, if the grader
systematically favors certain phrasing, every game is scored with the same tilt; that is a *bias*, and unlike
random noise no number of extra games averages it away, so a verdict built on it is just a tilted verdict.
The exclusion is nonetheless a *policy*, not an inability: the tagger reads plain transcripts, so it can
grade a memory-off game exactly as it grades a memory-on one — it *could* referee the A/B, the rule simply
says it must not. That is a stronger boundary than the one that excluded v1's pipeline judges, which required
memory-arm inputs (retrievals) and literally could not run in the memory-off arm at all. The tagger's
arm-symmetry is also what lets its OFF-window baselines exist, which §7's same-instrument guard depends on.

**Reason 2 — the learning loop can afford a noisier grader; a verdict cannot.** Credit (§7) hands out many
small per-decision rewards, so one mis-graded turn washes out over the many decisions that follow, and both
arms are graded by the same instrument, so the difference between them stays fair. A verdict has no such
averaging: an instrument bias lands directly in the conclusion. And the loop has no deterministic fallback
for these channels, so the real choice was a validated LLM signal or no learning signal at all.

Two guards keep that honest:

- **Instrument validation.** The tagger itself is validated in its eval-hub spoke; it is an instrument with
  a trust verdict, not an oracle.
- **Same-instrument baselines.** The rule in one line: *never difference a tagger-scored number against a
  number scored by anything else.* A tagger-graded *level* would otherwise masquerade as *lift* if
  differenced against a differently-graded floor, so every tagger channel is baselined against the tagger's
  own scores over the memory-OFF window (`tagger/<cell>` keys in `base_rates.json`; the baseline-coherence
  invariant, added 2026-07-05, fails loudly on any mixed-instrument comparison).

**Where the inventory lives.** The family's consumer is the credit system — the v7 compounding loop's
learning signal (§7). The full signal inventory (every LLM-tagged signal, its consumer, and its per-signal
validation status) lives at the tagger's apparatus home,
[`../discussion_tagger/report.md`](../discussion_tagger/report.md); this section is only the *boundary rule* that
keeps those signals out of the A/B basket.

## 6. How they are collected

The compute path is one function per game, all deterministic:

```
game JSONL record ─▶ _compute_base_metrics   (raw counts: votes, revealed roles, deaths, targets)
                  ─▶ _compute_derived_metrics (opportunity-conditioned rates from those counts)
                  ─▶ ComputedGameMetrics      (a flat, self-contained per-game artifact)
                  ─▶ push_scores_to_langfuse  (each field tagged with its tier)
```

`_compute_base_metrics` walks the day and night resolution records — who was lynched, who was targeted,
which kill landed, the faction sizes entering each night — and produces `BaseGameMetrics`: every numerator
beside its opportunity denominator. `_compute_derived_metrics` then takes the rates
(`_safe_div` returns `None` when a denominator is zero, so *absence is not zero performance* — a role that
never had the chance is not scored 0). The public artifact `ComputedGameMetrics` carries **63 fields** (27
derived rates plus the raw counts they came from), so a record is interpretable without re-deriving.

Two properties are structural, not conventional. **The computation calls no model**, so it runs on
historical batches with no re-generation. And it takes **no memory-side input** at all: the same code runs
over a memory-on game and a memory-off game and cannot behave differently by arm, which is exactly what lets
the two arms be compared.

**Input provenance — "deterministic" means the computation, so be precise about the inputs.** The fields
divide by where their raw facts come from:

- **Game-mechanics facts** (votes, revealed roles, deaths, night targets) — engine-recorded, no model
  involved at any stage. **All eleven basket proxies live entirely here.**
- **In-game model-emitted tags** — one diagnostic proxy, `town_accusation_precision`, parses the playing
  agents' own speech-act tags (`addressed_targets` with `stance == "accusation"`, emitted as structured
  output during day discussion). The arithmetic is deterministic, but the accusation label itself is
  authored by the playing model — a self-annotation, not an engine fact. It is still arm-symmetric (agents
  emit the tags in both arms as part of normal play) and the tags were smoke-validated (0 hallucinated
  targets), but it is one trust rung below the mechanics-only rows, which is part of why it sits in the
  diagnostic tier.
- **Eval-time LLM tagging** (a judge or tagger reading transcripts after the game) — **none, anywhere in
  this artifact.** Proxies of that kind are the LLM-tagged family (§5), consumed by the loop's credit
  layer (§7), never by `ComputedGameMetrics`.

One edge case: the single field that needs a game constant the record cannot recover — the vigilante's
starting bullet supply — is sourced from `GameConfig` rather than the record, because deriving it from
shots+unused would silently drop every held-bullet game on recompute.

## 7. The decision-grain cousin — v7 loop credit

v7 asks whether memory can *compound*: whether lessons distilled from earlier games measurably improve later
ones. Learning like that needs a per-decision reward — when an agent followed a stored strategy point and
then acted, was that one action good? That reward signal is **credit**. It is the same grade-against-true-roles
idea as the §2 basket, run at a different grain (one decision, not one game) for a different consumer (the
loop's consolidation step, not a human reading an A/B verdict).

**How a decision becomes a number — three steps.**

1. **Grade.** [`decision_scoring.py`](../../evaluation/src/loop/decision_scoring.py) scores one vote or night
   target against the true hidden roles, with no LLM: `score_vote` marks a town vote correct when it lands on
   a wolf or SK, and `score_night_target` reads a night action through a role-aware lens.
2. **Value.** The credit layer ([`credit_backfill.py`](../../evaluation/src/loop/credit_backfill.py)) maps
   each graded decision to a number via `VERDICT_VALUE = {positive: +1, neutral: 0, negative: −1}`.
3. **Lift.** The value is differenced against the memory-off baseline: `lift = utility − base_rate`, where
   `base_rate` is the *same* decision cell's mean outcome played with memory off. This is baseline-differencing,
   and this doc deliberately does *not* call it "de-luck": it is the credit-side mechanism, distinct from the
   basket's opportunity normalization (§1).

Why the baseline matters, in one concrete case ([`credit.py`](../../evaluation/src/loop/credit.py), ~line
304 comment): a raw "positive" can be *free*. The last-standing SK's night kill lands on most nights no
matter how well it played, so its base rate is near 1 and its lift-credit is ≈ 0. Lift measures what memory
*added* over the ambient, not what the role gets anyway. That lift, shrunk toward zero for strategy points
with few follows, is what `credit.py` writes onto each strategy point's counts, and it is what v7's SP credit
consumes.

**The credit channels, by grader.** Credit runs at decision grain only; these are the channels that become
credit numbers.

| Channel | Roles | Grader | Rule |
|---|---|---|---|
| Day vote | town, wolf, SK | deterministic `_vote_credit` | town: **+** on a threat (wolf/SK), **−** on a townmate; wolf: **+** when it blends with the day's plurality — bussing-aware by construction, and adopted *because* the basket validated blending (`_vote_credit` cites r=+0.22 G2 day-blend and r=+0.20 audit); SK: **+** on any non-self lynch; abstain neutral |
| Night action | investigator, vigilante, wolf, SK (`NIGHT_CREDIT_ROLES`) | deterministic `_night_credit` | investigator: **+** on a threat and never negative (the find-rate is a near-null channel, §3); vigilante: **+** on a threat, **−** on friendly fire; wolf/SK: **+** on a power-or-threat kill, plain-townie kill neutral; a held action neutral |
| Day discussion | all speakers | tagger holistic verdict (only under `discussion_mode="tagger"`) | the one channel with no deterministic proxy |
| Night action (tagger mode) | the same four roles | tagger read-quality verdict | **overrides** the deterministic night credit; grades the *reasoning*, not the hit |
| Healer | — | none | deliberately uncredited: absent from `NIGHT_CREDIT_ROLES`; a healer lens exists only screen-locally in [`checkpoint_replay.py`](../../evaluation/src/replay/decision_screen/checkpoint_replay.py) `_healer_night_credit`, and promoting it into production credit is a gated change |

> **2026-07-11 — channel table superseded by the read/tactic credit redesign**
> ([`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md),
> wiring pending). The two tagger rows are retired from credit (the tagger becomes a standing
> diagnostic). The day-vote row becomes the *endpoint* grain of day credit and gains a move-grain
> **advocacy** rule (persuasion-success × the same faction-relative target value `_vote_credit`
> already computes); night credit keeps its outcome rules but gains a **read-partition** (a town
> outcome reached through a wrong stated read is excluded from tactic credit and penalized at the
> read layer instead); deceivers gain a guarded per-day **concealment floor**. A second baseline
> family joins the OFF-cell base: the new tell ledger is baselined against **cast base-rates**, a
> baseline type to be registered under `assert_baseline_coherence`, while the `tagger/<cell>`
> same-instrument bases become diagnostic-optional.

**The boundary between basket and credit, stated once.** None of the eleven §2 basket proxies is a credit
input. The basket *informed credit design* — the wolf blend rule and the investigator leniency both descend
from basket validation findings (blending tracked the wolf win; the find-rate did not) — but no basket proxy
*value* is ever read by `_vote_credit`, `_night_credit`, or the tagger ledger. The two also differ in trust:
the basket is win-validated, while credit is the loop's internal reward and is *not* itself win-validated,
with some channels (the investigator find-rate credit) deliberately weak. Where a channel is tagger-graded
rather than deterministic, it is baselined against the same instrument (§5's guard), so a tagger level never
masquerades as lift.

*(A parallel deterministic quantity, `query_criticality` in `decision_scoring.py`, computes a board's
`players_alive` / `distance_to_parity` / `is_swing` from the true roles — since 2026-07-11 from all three
faction win-clocks, not wolf parity alone (ruling: [`../credit/report.md`](../credit/report.md) §6). It is
the decision-grain leverage anchor used by the dimension audit and criticality screen — offline only, never
shown to a live agent — not a credit input; see the situation-dimensions report.)*

## 8. Gaps ledger

Ordered by how much each limits trust, each dated for freshness. Verdicts are lifted from the apparatus
report [`../evaluation/metrics/report.md`](../evaluation/metrics/report.md) and scoped to what was tested.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **Investigator channel is only partially validated (🟡).** | The find-*rate* proxies are demoted to do-not-use (flat-to-wrong-sign vs win). Only conversion (`investigator_find_to_lynch_rate`, +0.40) is basket-trusted. The v5 wrong-sign scare on `investigator_found_wolf_day` (+0.38, p=0.039, n=30) **dissolved to +0.15 n.s. at N=180** — small-N noise plus mild length-coupling, not a robust backwards relationship. Verdict: partial, not broken. *(2026-07-02)* | Med |
| 2 | **Deceiver basket is split and thin (⚠️).** | The validated SK/wolf proxies are real but rest on a small wolf-win sample; the wolf's biggest single win-correlate (`sk_lynched`, +0.455) is an *environmental* event (the town removing the SK), not a wolf action. Wolf day-offense stays effectively unmeasured — `wolf_steering_rate` cannot separate leading a bandwagon from joining one. Scope: v6ab N=180, store v6_1. *(2026-07-02)* | Med |
| 3 | **Discussion-layer proxy is diagnostic, not independent (🔴→🟡).** | The first town-discussion proxy (`town_accusation_precision`, +0.34) validates but covaries ~31% with `town_vote_accuracy`, so it re-expresses a validated construct rather than confirming a new one — confirmed directly 2026-07-07: partial r vs win given vote accuracy = +0.02 n.s. The metrics-side wolf lead-vs-blend proxy stays null. The richer LLM discussion tagger is the LLM-tagged family's job (§5), never this basket's. *(2026-07-02; partial-r confirmation 2026-07-07)* | Med |
| 4 | **The full `GameScore` projection is unbuilt.** | Trust tiering shipped as three frozensets on the raw 63-field artifact (a guardrail), but the typed `GameScore` class that would stop double-counting coupled twins (`suspicion_drawn`↔blending, survival↔kill-rate) *by construction* is design-only in [`design/score_tier_design.md`](design/score_tier_design.md). Until then the guard is a naming and tag convention, not a structural one. *(2026-07-04)* | Low-Med |
| 5 | **Langfuse push is indiscriminate.** | `push_scores_to_langfuse` pushes every non-None field, tier-tagged but co-equal; two newly validated proxies (`investigator_find_to_lynch_rate`, `power_roles_killed_by_evil`) already live in the basket but nothing prioritizes them in the dashboard. Filter by the `tier` tag when reading. *(2026-07-02)* | Low |
| 6 | **Multiple-comparison exposure.** | ~30 proxies were tested against win in the v5 check alone, with no built-in Bonferroni (the full cross-campaign ledger is ~48 — see §4); the validation docs apply the correction by hand where it bites, and the monotonicity check explicitly ranks proxies by trustworthiness rather than claiming causal effects. Rows also share games, so they are not independent tests. *(2026-06-11; ledger 2026-07-02)* | Low |

**Not a gap — the wolf/SK nulls are not scheduler artifacts.** A sibling audit falsified the hypothesis that
the role-blind discussion scheduler starves these behaviors: investigator and wolf are the floor-richest
roles, and pending-find investigators speak before the vote 58/58 times. The nulls are agent and town
behavior, not measurement starvation. *(2026-07-02, lifted from the apparatus report.)*

## 9. Artifacts

| Artifact | Where | Role |
|---|---|---|
| Production compute | [`Agents/compute_metrics.py`](../../Agents/compute_metrics.py) + [`Agents/schemas/metrics.py`](../../Agents/schemas/metrics.py) | Emits `ComputedGameMetrics`; carries the three tier frozensets |
| Monotonicity record | [`proxy_win_monotonicity.md`](proxy_win_monotonicity.md) | The dated v5 proxy-vs-win table (the validation the design deferred) |
| Candidate ledger | [`candidate_ledger.md`](candidate_ledger.md) | The full field of all 48 win-tested proxies, by tier then role (the detail §4 stubs out) |
| Validation harness | [`evaluation/src/instrument_validation/proxies/`](../../evaluation/src/instrument_validation/proxies/) | The standing runners (`proxy_win_monotonicity`, `proxy_rescue`, `accusation_metrics`, `claim_conversion`, `diagnose_wolf_sk_proxies`, `leverage_anchor_separation`, `proxy_followup_rescue`); the monotonicity code graduated here from this folder on 2026-07-04, run via `poetry run python -m evaluation.src.instrument_validation.proxies.proxy_win_monotonicity` |
| N=180 audit logs | [`metrics_audit/`](metrics_audit/) | `proxy_discovery_log.md` + `scheduler_bias_log.md` — the 2026-07-02 proxy rescue/discovery and scheduler-bias falsification |
| Loop credit (decision grain) | [`evaluation/src/loop/decision_scoring.py`](../../evaluation/src/loop/decision_scoring.py) · [`credit_backfill.py`](../../evaluation/src/loop/credit_backfill.py) · [`credit.py`](../../evaluation/src/loop/credit.py) | Per-decision credit (baseline-differenced lift); v7 SP learning signal |
| LLM-tagged family | [`../discussion_tagger/`](../discussion_tagger/) (apparatus record) · [`../evaluation/discussion_tagger/`](../evaluation/discussion_tagger/) (trust verdict) | The second instrument tier (§5): discussion + unresolvable night cells, credit-side only |
| Regression tests | `tests/test_metrics_audit_proxies.py` · `test_diagnostic_metrics.py` · `test_wolf_blending_metrics.py` · `test_loop_credit_scale.py` · `test_credit_blend.py` | Lock the tiering, the audit-graduated proxies, and the credit scaling |
| Apparatus trust | [`../evaluation/metrics/report.md`](../evaluation/metrics/report.md) | The per-basket ✅/🟡/⚠️/🔴 instrument-trust verdicts this doc lifts from |
