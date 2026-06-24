# Discussion-quality A/B rubric — concurrent vs sequential

**Purpose:** close Phase A #1. Decide whether the sequential scheduler-driven day
discussion reads *better* than the concurrent fan-out baseline, judged by hand over
K=8 games (2 mem-off + 2 mem-on per arm). No LLM judge — this is the human scoring guide.

**Unit of comparison:** aggregate character across the 4+4 games (unpaired — temp=1.0,
unseeded roles). Read for *systematic* differences, not single-game luck.

**Pinned (identical both arms):** Vertex / gemini-3.1-flash-lite / temp 1.0 / 8-player
default roles / first_voting_day=2 / memory seeded from v4_deduped_v2 cache. Only the
discussion **design** differs (concurrent fan-out rounds vs sequential reactive/proactive
scheduler). Concurrent ran with max_discussion_rounds_per_day=4.

---

## Dimensions

### 1. Redundancy / parroting  *(concurrent's structural weak point)*
Do multiple agents independently land on the **same point** without acknowledging each
other? In concurrent fan-out, all players speak in one round *blind to each other*, so
echo is structural. Sequential conditions each turn on prior ones + has the proactive
novelty gate.
- **Look for:** near-duplicate accusations/claims in the same day; "I agree with X"
  pile-ups that add nothing; the *same* suspicion restated by 3+ players.
- **Better = ** fewer redundant utterances; later speakers build on / differ from earlier ones.

### 2. Responsiveness
When an agent is questioned or accused, does the **addressed** agent actually answer —
in a timely way, not 3 turns later or never? Sequential's reactive obligations *force*
the addressed agent to respond next; concurrent has no such mechanism.
- **Look for:** questions/accusations that go unanswered; defenses that arrive only after
  the topic moved on; vs. direct, prompt back-and-forth on a live accusation.
- **Better = ** accusations get answered, by the right person, soon.

### 3. Dogpiling
Does one target get piled on by many in a burst with no counter-pressure or new
information? Sequential's per-pair K-cap + proactive gate bound this.
- **Look for:** 4+ agents hitting one target in a row with redundant content; runaway
  consensus with no scrutiny; vs. bounded, information-bearing pressure.
- **Better = ** pressure is bounded and each pile-on adds something.

### 4. Turn-fairness
Is speaking time distributed, or does one agent dominate / do some never speak? Sequential
ranks quietest-first for proactive turns.
- **Look for:** one agent speaking far more than others in a day; silent survivors who
  never contribute; vs. roughly even participation.
- **Better = ** more even distribution; fewer total no-shows.

---

## Secondary observations (note, don't score)
- **Naturalness / flow:** does the day read like a conversation or like parallel monologues?
- **Convergence:** does the day reach a vote sensibly, or pad out / cut off abruptly?
- **Length / cost:** utterances per day per arm (sequential terminates on trailing passes;
  concurrent runs fixed rounds).
- **Memory on vs off:** does sequential's advantage hold in *both* conditions? (mem-off is
  where concurrent parroting should be worst — thin context to echo; mem-on gives agents
  retrieved material to differentiate on.)

## Verdict format (what I'll deliver)
Per dimension: concurrent vs sequential, 2-3 supporting excerpts each (player:message,
day/seq), and a short call (sequential better / no clear difference / concurrent better).
Then an overall: does sequential clear the bar to close Phase A #1? Plus the mem-on/off
split, so you can see if the win is robust to memory.
