# Credit: turning recorded decisions into memory evidence

> **Scope:** the strategy and tell scoring mechanisms developed for the July 2026 nine-seat
> research loop, with implementation boundaries checked on October 13, 2026. This is a mechanism
> reference, not a claim that credit-guided memory improves play. The ten-seat strategy-credit port
> has its own [decision record](../memory_system/v8/decisions.md).
>
> **Pipeline:** recorded decision → factual outcome → grading rule → memory attribution → baseline
> comparison → support adjustment → curation. Tells use a separate path: detected behavior → revealed
> role → role-frequency comparison → book selection.

## 1. What credit is for — and what is never credited

Credit gives the memory curator evidence about individual lessons. It supports retaining, pruning and
synthesizing strategy points, and selecting behavioral tells for an injected book. A game's win is too
coarse to grade every lesson used along the way, while an agent's “followed” verdict says it adopted
advice, not that the advice helped.

The design therefore uses intermediate outcomes. Strategy points receive grades for decisions at which
they were reportedly followed. Tells receive empirical role-association scores from detected exhibitors,
even when the tell was not shown to an agent. These are different evidence sources and remain separate.

Three objects do not receive this per-memory outcome credit:

- **Observations** are stored examples used in synthesis. Their extraction verdict is distinct from
  the credit assigned to a strategy later followed in play.
- **Agent read accuracy** measures beliefs against revealed roles. It does not identify which tell
  caused a particular belief.
- **Diagnostic judgments**, such as discussion quality or apparent influence, may explain results
  but do not feed the redesigned prune/protect/synthesis decisions.

Credit is an internal selection signal. A rise in credit cannot by itself validate the learning loop:
optimization can improve the chosen score while harming something it omits. The later
[blind-spot investigation](blindspot_fix/experiment_log.md) demonstrated why that distinction matters.

## 2. Separate facts from their value to a faction

The same event can help one faction and hurt another. The factual scorer records the chosen target,
its revealed role and the relevant resolution. The grading layer interprets those facts for the actor.
Separating them lets evaluation tools reuse one account of what happened without silently sharing a
reward policy they did not choose.

For example, an elimination of a town player is bad for town but may benefit its opponents. A wolf
voting with the room against a packmate can be scored as blending, although the loss of that packmate
has a separate strategic cost. The score names the skill it measures; it is not a complete value
function for the game.

Board criticality, meaning proximity to a faction's win condition, did not multiply July credit.
The design used it to select informative situations and audit cases instead. A pivotal board can make
a decision worth studying without making every lesson followed there intrinsically better.

## 3. The strategy-point ledger

### Attribute outcomes to reported follows

Recorded strategy indices are joined back to stored keys. Each followed strategy receives the decision's
grade. This supports per-item histories without another model call, but several followed strategies can
share one outcome, and a reported follow may not describe what the action actually did.

A seeded, AI-adjudicated spot-check found **13 enacted follows and 2 non-enacted follows out of 15**.
The stored one-sided 95% upper bound on the non-enactment rate is 36.3%, so the sample supports a modest
check, not a guarantee of reliable attribution.

The two misses were different: one agent passed after claiming to follow aggressive speech advice;
another spoke a conciliatory defense that contradicted the prescribed attack on its accuser. Requiring
a nonempty spoken turn prevents the first kind from receiving discussion credit, but does not fix the
second. Earlier prose incorrectly described both misses as passes.

Source: [the sampled decisions and adjudications](attribution_spot_check.json). Deterministic grading
does not establish that attribution errors are unbiased; reported follows remain selected observations.

### Grade the decision with a channel-specific rule

The table summarizes the July starting rules. They describe the nine-seat experiment, not the current
ten-seat grading table. Later legacy experiments also exposed switches such as the abstention rule.

| Channel | July rule | What it measures or misses |
|---|---|---|
| Town vote | Threat target positive; town target negative; abstention initially neutral | Target choice; the neutral-abstention blind spot was investigated later |
| Wolf vote | Matching the final plurality positive; otherwise negative | Blending, including voting with the room against a packmate |
| Serial-killer vote | A non-self target positive | A permissive survival-oriented rule with little discrimination |
| Discussion | Grade the day's lynch for the actor, with self-lynch negative; refine a landed accusation | Observable endpoint, not the speaker's causal influence |
| Evil concealment advice | Grade accusation pressure relative to room activity, requiring speech | A bounded concealment proxy; attention from opponents remains a confound |
| Investigator night | Finding a threat positive; miss neutral | Information obtained, not whether it was later converted into an elimination |
| Vigilante night | Threat target positive; town target negative; holding fire neutral | Target choice rather than whether protection or immunity prevented the kill |
| Wolf / serial-killer night | Power-role or rival-threat target positive; ordinary villager neutral | Target value under the historical rule |
| Healer night | Saving an attacked town player positive; protecting an attacked threat negative; unattacked target neutral | Protection against an actual attack |

These rules were motivated by the project's outcome-proxy studies, but those studies do not validate
every per-strategy attribution or establish the benefit of pruning on the resulting score. The
[metrics report](../metrics/report.md) owns the proxy evidence and its scope.

The discussion implementation refines the endpoint when an accusation lands on the lynched player.
For deceivers, the legacy rule treats a landed push as positive, including a bus of a packmate.
For town, a landed accusation against town is excluded as a read-error case. Concealment-typed
strategies use their own instrument and baseline rather than collecting both signals.

### Read exclusions: the implementation is narrower than the proposal

The [design record](read_tactic_credit_redesign.md) proposed protecting ordinary tactics from errors
in their input beliefs, while scoring risk-taking policies across all outcomes. The legacy night
scorer implements a narrower check: a negative outcome is excluded when the actor's recorded target
read was a high-confidence threat belief and the target was actually town. Missing or low-confidence
reads do not trigger it. Targeted discussion uses the accusation/lynch rule described above.

Two qualifications matter. This selects which failures reach the tactic ledger, so it can affect the
score systematically. Also, the legacy scorer does not read a strategy's `risk_policy` tag when making
this exclusion. The proposed policy exception should not be described as implemented. Agent read
accuracy is evaluated separately; exclusion is not a transfer of the same reward into another ledger.

### Compare against what happens without memory

A successful action can be common even without advice. The historical loop therefore subtracts the
memory-off mean for the corresponding role/action channel, computed with the same grading instrument.
Subtracting a differently graded baseline would manufacture a misleading difference.

The support-adjusted strategy score is:

```text
raw outcome mean = (positive counts − negative counts) / scored follows
adjusted lift = (raw outcome mean − memory-off mean) × follows / (follows + 5)
```

The factor reduces the influence of thin evidence. The historical held-out reproduction reported
r = +0.54 across 31 strategy points; that is evidence about repeatability of the ranking signal, not
proof that acting on the score improves gameplay. The
[held-out study record](../store_curation/strategy_points.md) gives the split and interpretation. Counts are recomputed from the supplied game window
rather than repeatedly added, allowing old evidence to age out when the caller advances that window.

Baseline coverage differs by implementation. The legacy helper can fall back to zero for an absent
channel. The ten-seat port instead leaves unsupported baselines unscored and stores a strategy's
follow-weighted channel baseline. A reader should not infer the latter guarantee for every historical
run. See the [ten-seat decisions](../memory_system/v8/decisions.md) and the code map below.

## 4. The tell ledger

A tell describes observable behavior. Its score asks how the roles of detected exhibitors differ from
the cast's role frequencies. It is an association score, not an assessment of whether exhibiting the
behavior was good play.

Only **detected** instances enter the lift calculation. Mined examples discover candidates, but are
selected with roles visible and cannot supply an unbiased numerator or denominator. Repeated sightings
of one tell in one player/game count once for this calculation.

For role count `c` among `n` exhibitors and cast prior `p`, the support adjustment is:

```text
shrunk role share = (c + 5 × p) / (n + 5)
shrunk lift = shrunk role share − p
```

The July code distinguishes two uses of this arithmetic:

- **Evil-lift eligibility** selects supported, positive evil associations under the historical credit
  policy. Negative evil-lift is not a second reward for looking town.
- **Book selection**, revised July 14, ranks by the subject role's concentration. It can include an
  investigator or healer association even when its evil-lift is negative. What informs a read is
  not identical to what the credit policy makes eligible.

The book selects up to three tells per subject-role/channel group, with at least eight exhibitors and
positive subject lift. The subject is identified from per-role exhibitor rates. At generation time,
entries whose subject roles are fully revealed dead are removed. There is no per-turn semantic retrieval.

One stored example is “A player asserts high confidence in an accusation while refusing to disclose
the source of their information”: 10 of 11 exhibitors were investigators in the historical data.
That is useful evidence to inspect, but the small support and old behavioral distribution prevent it
from being a current rule about investigators. The
[tell report](../extraction/tell_extraction/report.md) owns detector evaluation, held-out sampling,
and the distinction between the replayed and later seed books.

## 5. What stays diagnostic

The read ledger measures how accurately agents identify roles. The discussion judge assesses broader
qualities such as credibility. The first-link diagnostic examines whether an addressee's next read
moves after a push, with an adjustment for the preceding trend. None of these supplies credit to
individual tells merely because a belief improved afterward.

The influence diagnostic has two particular limits: public listeners are not untreated controls, and
stated reads are a coarse record of belief changes. The proposed route to stronger influence evidence
was a paired continuation replay with the utterance present versus removed. This was a conditional
experiment, not a completed validation or a required deployment task.

## 6. Evidence boundaries and current scope

The mechanism was implemented and exercised in research. That does not settle whether its reward
selects better advice. The later July investigation found that concealment and abstention advice could
benefit under a partial score while harming town play. The July 21 closure reported a negative-leaning
procedural-memory endpoint and declined a further live gate for the fixes. Its findings should not be
replaced by the earlier report's “run still pending” framing.

The [closure record](blindspot_fix/experiment_log.md) gives the result and scope: primary −0.147,
p approximately .06 over 30 paired boards, with fixes checked at the instrument/replay level rather than certified live.
The October addendum further limits the historical gameplay findings to players that generated no
reasoning tokens. These results do not isolate the tell channel's effect.

The ten-seat strategy port lives under `Agents/memory/consolidation/`. Its October decisions separate
the deterministic credit/prune pass from paid extraction and synthesis. The tell pipeline remains in
the research loop. Its prompt hook is implemented, but reads no book unless `WW_TELL_BOOK` is set.
That switch is independent of the ordinary memory setting, and the
[ten-seat plan](../memory_system/v8/plan.md) keeps tells outside the deployment scope.

## Sources and implementation

| Responsibility | Source |
|---|---|
| July architecture and alternatives | [Read/tactic decision record](read_tactic_credit_redesign.md) |
| Legacy scoring and diagnostics | [Research-loop module map](../../evaluation/src/loop/README.md): `credit`, `credit_backfill`, `read_ledger`, `first_link` |
| Ten-seat scoring and separate learning steps | `Agents/memory/consolidation/`; [v8 decisions](../memory_system/v8/decisions.md) §§12–14 |
| Tell arithmetic, lifecycle and evidence | [Tell report](../extraction/tell_extraction/report.md), [build log](../extraction/tell_extraction/experiment_log.md); research modules `tells`, `tell_credit`, `tell_fold` |
| Prompt injection | `Agents/memory/tell_book.py`; `Agents/prompts/prompt_inputs.py` |
| Attribution sample | [Frozen 15-case adjudication](attribution_spot_check.json), seed 20260713, July 13, 2026 |
| Later reward failure and research closure | [Blind-spot experiment log](blindspot_fix/experiment_log.md), especially closure and reasoning-scope addendum |

Historical scripts and result files are evidence of the runs that produced them. This editorial
revision does not rerun those experiments or certify their results for the current game.

Implementation pointers were checked against repository revision `d206680d` and the October 13, 2026
working tree. Historical measurements retain their linked run artifacts; this is an editorial review,
not a new experimental run.
