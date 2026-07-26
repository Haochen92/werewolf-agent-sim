# Prompt-boundary cleanup — experiment log

**Goal.** Enforce the prompt/memory division before Phase A #2 (roles): the *prompt*
governs how an agent contributes and what's true about the game (style, quality floor,
rules); the *memory system* governs what to conclude and what signals mean (the strategy
space). The day-discussion prompts were violating this — actively prescribing the
degenerate "tone/silence policing" pseudo-strategy — and that prescription floods the
transcripts and would be harvested into the v5 memory store the roles phase is built to
A/B-test.

**Why before roles.** (1) Contamination: the memory extractor learns strategy points from
games; generating the memory A/B on the current prompts bakes "evasiveness is a tell" into
the very store we measure. Fix the generator before generating the thing we measure.
(2) The CORE_STRATEGY blocks are per-role — locking the neutral template now means the new
SK/vigilante blocks are written correctly the first time. (3) Clean attribution: validate
the prompt change on the known-good current 4-role setup before stacking structural
win-condition changes on top.

**Does NOT reopen the sequential gate** (`evidence/sequential_discussion/quality_gate/`): that gate was
concurrent-vs-sequential on identical prompts — internally valid. This is a forward quality
improvement to the generator.

## Method (rigor without tests — eyeball + deterministic anchor)

- **Pinned (identical pre/post):** Vertex / gemini-3.1-flash-lite / temp 1.0 / 8-player
  default roles / sequential scheduler. **Memory OFF** (`all_disabled`) on both arms — the
  right isolation for a *prompt* change: no retrieved strategy points confounding the
  comparison, and no embedding 429s.
- **Pre (baseline):** the `all_disabled` games already on disk from the discussion-quality
  gate — `evidence/sequential_discussion/quality_gate/data/gate_sequential.jsonl` (2 games, 119 discussion msgs).
  These were generated on the *old* prompts, so they ARE the pre-change arm for free.
- **Post:** 2 fresh `all_disabled` games on the edited prompts → `post_seq.jsonl`.
- **Deterministic anchor:** [markers.py](markers.py) counts two pathologies over discussion
  messages (substring match, case-insensitive — a *lower bound*, misses paraphrase):
  - **STOCK** (goal 1, naturalness): canned formulas / mirroring openers ("I agree with…",
    "fair point", "classic wolf", …).
  - **POLICE** (goal 2, degenerate pseudo-strategy): suspicion manufactured from
    tone/volume/silence ("deflect", "defensive", "too quiet", "evasive", …).
  Same script run identically on both arms. Verdict is by eyeball against verbatim excerpts;
  the counts are a regression anchor, not a classifier (some POLICE hits are agents pushing
  *back* against tone-policing — the excerpts disambiguate).

## Reproduce

`poetry run` mis-resolves to py3.10 here — use the py3.11 venv binary:
`PY=~/.cache/pypoetry/virtualenvs/werewolf-game-v7lKgM40-py3.11/bin/python`

**The reported numbers replay exactly** (frozen transcripts + deterministic script):

```bash
# aggregate STOCK/POLICE + verbatim excerpts + day-1-vs-day>=2 phase split, both arms:
$PY evidence/generation_prompt/prompt_boundary/markers.py \
    evidence/sequential_discussion/quality_gate/data/gate_sequential.jsonl:all_disabled \
    evidence/generation_prompt/prompt_boundary/post_seq.jsonl:all_disabled
```

Pre arm = the discussion-quality gate's `all_disabled` games (`gate_sequential.jsonl`, old
prompts). Post arm = `post_seq.jsonl` (this experiment).

**Regenerating the post games** (fresh, not a replay — temp 1.0, unseeded roles → different
transcripts each run; direction is what reproduces, not the exact numbers). Pinned: Vertex /
gemini-3.1-flash-lite / temp 1.0 / 8-player default roles / sequential scheduler (all defaults
in `Agents/agents.py` + `.env`). Memory-off isolates the prompt; `--no-memory-*` removes the
only embedding calls (no 429s):

```bash
$PY scripts/run_batch.py --configs all_disabled --runs-per-config 2 \
    --no-memory-seed --no-memory-dump \
    --output evidence/generation_prompt/prompt_boundary/post_seq.jsonl --session-prefix pb_post
```

To compare against the **old** prompts, check out a commit before `93c7721` (or revert the two
prompt commits), regenerate, and rerun `markers.py` on the result.

## The change (4 edits)

1. **`Agents/prompts/roles.py` — strip strategy-reads from all 4 CORE_STRATEGY blocks**
   (the substantive edit; this is where the pathology was prescribed):
   - **Villager:** deleted the "Behavioral Analysis" block ("Scrutinize players who…
     deflect / echo… treat evasiveness as warning signs") and the "groupthink → treat the
     push as suspicious" co-voting read. Replaced with a neutral "Forming reads" para:
     base suspicion on concrete things (contradictions, the public voting record); when
     nothing is concrete, it's fine to hold off — *what behavior means is yours to judge*.
   - **Wolf:** removed "invent logical narratives from minor details" and "amplify existing
     village paranoia" (prescribing the manufacture-suspicion crutch from the wolf side);
     kept blend-in / vote-discipline / generic night-targeting of "most effective players."
   - **Healer/Investigator:** lighter touch — removed the behavioral-tell phrases
     ("proven alignment through pro-village actions", "steer toward a suspect's evasive
     behavior"); kept own-role play (survival, ability use, blending), now framed as the
     role's own judgment call.
2. **`common.py TONE_INSTRUCTION`** (goal 1): added an anti-formula / anti-mirroring clause
   — no canned openers, don't mirror the prior message's structure, short reactions are
   fine, if you agree add a new reason rather than seconding.
3. **`common.py DISCUSSION_SILENCE_RULE`** (goal 2): added the info-starved clause — when
   nothing is concrete, don't manufacture suspicion from tone/volume; it's OK to say
   there's little to go on; prefer information-generating moves (propose a test, name a
   contradiction, track the vote record). Mitigates the pass-spam / new-crutch risk.
4. **`common.py GAME_PREAMBLE`** (goal 3): replaced the stale concurrent game-flow
   ("discuss up to N rounds…") with the sequential model (speak/pass, winds down), and
   added neutral facts: votes are public & permanent, night actions hidden, role claims
   can't be system-verified. Removed the now-unused `{max_discussion_rounds_per_day}`
   placeholder (only consumer; kwarg still passed harmlessly).

## Results

### Pre-change (baseline, old prompts) — `pre_markers.txt`

```
2 games, 119 discussion messages
STOCK  msgs:  26 / 119  (21.8%)   total marker hits: 44   top: i agree×21, i agree with×15, good point×4
POLICE msgs:  24 / 119  (20.2%)   total marker hits: 27   top: deflect×10, defensive×8, been quiet×2
```

Smoking gun in the baseline — an agent reciting the villager CORE_STRATEGY block:
> d1 player_1: "…playing too passively is also a classic way f[or wolves to hide]…"

### Post-change (edited prompts) — `post_markers.txt`

2 fresh `all_disabled` games, embedding-free (`--no-memory-seed --no-memory-dump`, transcript-
equivalent to baseline since `all_disabled` never retrieves). Both villagers/day-3, 0 failures.

```
2 games, 79 discussion messages
STOCK  msgs:  11 / 79  (13.9%)   total marker hits: 19   top: i agree×10, i agree with×8, fair point×1
POLICE msgs:   8 / 79  (10.1%)   total marker hits:  8   top: deflect×6, stayed quiet×1, defensive×1
```

### Delta

| Metric | PRE | POST | Change |
|---|---|---|---|
| POLICE msgs † | 20.2% | 10.1% | **halved** |
| POLICE total hits † | 27 | 8 | −70% |
| `defensive` † | 8 | 1 | −88% |
| STOCK msgs | 21.8% | 13.9% | −36% |
| `good point` / `exactly what the wolves want` | 4 / 1 | 0 / 0 | gone |
| strategy-block recitation ("classic way for wolves to hide") | present | absent | — |

† **Board-confounded — read with care.** POLICE happens mostly on day 2+ (you can't call
someone evasive before they've said anything), and day-2+ depends on how the game unfolded.
This post board handed the town an easy lead, so the POLICE drop **cannot** be cleanly
separated from "easy game." The day-1 split below only rescues STOCK, not POLICE.

### Eyeball (what the substring counts can't show)

- **Goal-2 redirect fired, no pass-spam.** Post games converge on *information-generating*
  moves — a recurring "soft deadline / everyone put a name forward / we have no voting record
  so let's create one through pressure" pattern. The displaced energy went where the new clause
  pointed, not into silence. Both games still reached votes and resolved (villagers, day 3).
- **Residual `i agree` is agree-and-add, not empty seconding** ("I agree with player 2 that we
  need specific reads…") — matches the "add a new reason rather than just seconding" instruction.
  The marker can't distinguish; the text does.
- **Remaining `deflect` hits are mostly counter-speech or the deadline mechanic** ("I'm not
  trying to deflect, I'm responding to the request for a name") — not manufactured tone-suspicion.
- **The prescription-recitation is gone.** The pre-change smoking gun (an agent parroting the
  villager CORE_STRATEGY "too passive = classic wolf hide") has no analog post-change.

### Verdict

**In plain terms:** the bad behavior was being *told* to the agents by the prompt, not just
something they drifted into. We deleted the instruction. After the change, agents do it less —
clearly less canned-talk on the opening day, and less tone-sniping overall, though that second
number got help from an easy game. We keep the change either way (see below), and the numbers
back it up rather than decide it.

**We keep this change on principle, not on the deltas.** A prompt that prescribes strategy
breaks the design rule (prompt = how to talk + the rules; memory = what to conclude). That's
true regardless of effect size — we'd keep it if the drop were half as big, or zero. So the
experiment is **corroboration, not justification**: it confirms the direction, it isn't what
makes the decision.

Both targeted pathologies fell in the predicted direction; POLICE (the one the prompt actively
*prescribed*) halved and its recitation disappeared. Confidence: **HIGH on direction** (the
change removes the documented source; the drop is large and one-sided), **LOW on magnitude**
(N=2/arm, substring lower-bound, POLICE board-confounded, some POLICE hits are counter-speech).
No pass-spam regression.

**Goal 1 (naturalness) is really an opener-slot fix.** The STOCK win is concentrated on day 1
(the zero-content opening flood, 52.6%→14.3%); day-2+ STOCK barely moved (16.0%→13.8%, noise at
this N) and "i agree" is still the top hit in both arms. So once there's real content to phrase,
the anti-formula clause does little — it mainly killed the empty opener. The "agree-and-add not
empty seconding" read above is a *qualitative* improvement the marker can't see, but it's
eyeballed, not measured — don't bank it. Pushing naturalness further is dialogue fine-tuning
territory, not more prompt rules (FT plan, Phase 4).

The neutral CORE_STRATEGY template is now the template the Phase A #2 SK/vigilante blocks will be
written against.

### Day-1 segmentation (defuses the easy-board confound for goal 1)

The pathology is an *information-starved* artifact, and day 1 is zero-info on **every** board —
so a day-1 cut controls for board luck:

Raw counts shown (the percentages hide tiny denominators):

| Phase | PRE STOCK | POST STOCK | PRE POLICE | POST POLICE |
|---|---|---|---|---|
| Day 1 (zero-info, board-independent) | 52.6% (10/19) | 14.3% (2/14) | 10.5% (2/19) | 0.0% (0/14) |
| Day ≥2 | 16.0% (16/100) | 13.8% (9/65) | 22.0% (22/100) | 12.3% (8/65) |

- **Goal 1 is board-independent:** day-1 canned-formula flooding collapsed 52.6%→14.3%. Day-1
  openers don't depend on the board, so this is the prompt, not luck. **Caveat on the small n:**
  the *drop* is real (a per-message rate, so it isn't inflated by day 1 having fewer messages),
  but the post estimate is 2/14 — wide error bars; treat the exact 14.3% as soft. Also note the
  day-1 message count itself fell (19→14): the silence clause produced more passes, so there are
  simply fewer openers to be canned — a second, separate win the rate doesn't show.
- **POLICE is inherently day-2+** (you can't police behavior before there is any) and day-2+ is
  board-sensitive — so this favorable board (town got a free lead from the wolves' own kill)
  CANNOT fully separate "prompt fixed it" from "easy board" for the *policing* axis. The real
  POLICE-under-zero-info test is a board with no early lead; that arrives naturally across the
  many boards of the roles memory A/B. Watch-item, not a prompt todo.

### Caveats / honest limits

- N=2 per arm, unpaired (temp 1.0). Numbers are directional, not significant — same posture as
  the discussion-quality gate.
- Markers are a substring **lower bound** and not a classifier; the verdict leans on the eyeball.
- Measured **memory-off only** (isolates the prompt). Removing the prescription cleared the
  *prescribed* source; residual POLICE is nonzero (10.1%, 8 hits) and *emergent*. But that
  residual is low-risk for the store — fresh v5 carries no legacy, and an emergent tone-tell
  extracts as a diluted, dedup'd observation, not an adopted strategy (see open item 1).

## Open items (post-MVP / next session)

1. **Contamination clearance — LOW RISK, resolved by design (this was over-weighted in an
   earlier draft).** The worry was that the memory extractor would learn the tone-policing
   pseudo-strategy and bake it into the v5 store we're about to A/B. Two structural reasons it's
   not a real concern:
   - **v5 is built fresh on the fixed prompts**, so there's no *legacy* tone-policing carried in
     from old v4-era games. We never create the dirt rather than filtering it — the cleanest form
     of "fixed at source."
   - **Residual emergent tone-policing extracts as a diluted observation, not an adopted
     strategy.** A stray "you're being defensive" line becomes one *observation* among many —
     situational, and the mature dedup pipeline keeps it from being over-represented. It can't
     become a learned heuristic; it's noise in a retrieved set, not a confound.
   - **Load-bearing assumption:** observations-only retrieval / strategy-point adoption dormant.
     A diluted observation is harmless; an *adopted* strategy point would be more load-bearing —
     so the one trigger to re-glance at the store is **if strategy-point adoption is ever turned
     back on.** Otherwise nothing to do; no measurement pass, no filter required.

2. **Paired pre-arm (optional, low priority).** The pre-arm reuses on-disk gate transcripts
   rather than regenerating the old prompts same-session, so there's an unverified "nothing but
   the prompt drifted" assumption (low risk — scheduler/graph unchanged since the gate). To
   close it: check out before `93c7721`, regenerate `all_disabled` games, rerun `markers.py`.

3. **Naturalness beyond the opener slot → dialogue fine-tuning** (FT plan, Phase 4). Prompt is
   near its ceiling for diction/register; goal 1 only fixed the day-1 opener flood.

