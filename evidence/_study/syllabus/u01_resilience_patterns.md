# U1. Resilience patterns for remote calls

**Time** 90 min · **Category** 1 and 2 · **Depth** Explain · **Needs** U0
**Chapters served:** 7

**Diagnostic (answer before reading, two sentences, example not from this project):** What is a
circuit breaker for, and when is it the wrong tool?

## 1. The concept

Resilience patterns are the rules a service follows when something it calls is slow, failing or
gone. They answer four questions in order: how long do I wait, do I ask again, what do I do instead,
and when do I stop asking. A fifth covers a dependency the request could do without.

The worked example is a shop's checkout. A customer presses Pay, and the checkout service calls a
payment provider. Customers give up after about ten seconds. Each pattern below fixes a failure this
checkout runs into.

**The hang.** One day the provider accepts the connection and never answers. The checkout has a
handler for payment errors, but no error arrives, so the handler never runs and the spinner turns
forever. A hang is the one failure an error-driven design cannot see. The fix is a **timeout**: after
a set time, give up on this attempt and raise an error. Time becomes a failure, and the existing
error handling can act on it.

**Timeout or deadline?** A timeout limits one attempt. The customer cares when the whole checkout is
done. That is the **deadline**, one limit across every attempt and fallback. With a 10-second timeout
and two retries, the customer can wait 30 seconds. With a deadline, each step asks how much time is
left and sizes its own timeout from that. A well-built service passes the time remaining down to
every call it makes.

**The blip.** Sometimes the provider returns a 503 once and works a moment later, so asking again
fixes it. A **retry policy** says which failures to retry, how many attempts to allow, and how long
to wait between them. The wait doubles each time (**exponential backoff**) and takes a random share
(**jitter**), so a thousand checkouts that failed together do not retry in the same instant. Each
retry adds load to a struggling service and spends the customer's time.

**Which failures are worth a retry?** A timeout, a 429 "too many requests" or a 503 says the
provider is slow or full right now: a **transient** failure. A 400 "invalid card number" or a 401
"bad API key" fails the same way every time: a **permanent** failure. Retrying it burns the deadline
and hides the real problem, so a retry policy starts with **failure classification**. (A charge is
safe to retry only if the provider recognises the repeat; that is U4.)

**Retries in layers.** The checkout code retries three times; the payment SDK underneath retries
three times; the HTTP library under that retries three times. One slow request becomes 27 attempts,
each with its own timeout, and the customer waits minutes. Each layer looked sensible on its own.
This is **retry amplification**. The fix: retry at one layer, set the others to a single attempt, and
let the deadline cap the total.

**The outage.** Now the provider is down for twenty minutes, and retrying cannot help. A
**fallback** does the job another way. A second processor for the same card keeps the behaviour but
may share the outage, if the card network is down. A bank transfer fails for different reasons but
changes the customer's experience.

**Paying for the timeout every time.** Even with a fallback, every checkout waits out its timeout on
the dead provider before switching. A **circuit breaker** stops that. It counts recent failures of
one dependency. While things are fine it is **closed**, and calls go through. Past a threshold it
**opens**: for a cooldown, calls skip the dependency and go straight to the fallback, or fail at once.
After the cooldown it is **half-open** and lets one trial call through; a success closes it, a
failure opens it again. It saves the caller's time and gives the dependency room to recover.

**When is a breaker the wrong tool?** A breaker is for failures that belong to the dependency. If
they come from the requests, such as declined cards, it trips on customers' mistakes and blocks good
requests. With thin traffic, a few failures cannot tell an outage from bad luck. If one region of the
provider is down, a breaker over the whole provider blocks the healthy regions too. And with no
fallback, opening it only changes how quickly the customer sees an error.

**Nothing answers.** Both processors are down, and the checkout still has to end somewhere sensible.
**Graceful degradation** means ending on a **safe default**: an outcome that keeps the system's rules
true, even if it is worse than the real answer. Here, "order saved; we'll email you when payment goes
through", never an order marked paid.

**The optional dependency.** Customers can also pay with loyalty points, held by a separate service
that is now down. There are three choices: refuse the feature clearly ("points are unavailable; pay by
card"), disable it silently and charge the card in full, or let the whole checkout fail. Going ahead
without the dependency is **fail-open**; refusing is **fail-closed**. The choice turns on whether the
customer asked for the feature and what a silent change costs them. A clear refusal lets them decide.

**Two to recognise.** A **bulkhead** gives each dependency its own pool of connections or threads, so
a slow points service cannot use up the capacity payment needs. A **hedged request** sends a second
copy when the first runs slow and takes whichever answers first, at the price of extra load.

**What changes for LLM calls?** Two things. Under load a provider can hold a request in its queue for
minutes before answering or bouncing it, so the hang is common, and a system that switches models on
errors has a hole exactly there until a deadline makes time a failure. And a fallback to a different
model changes the behaviour as well as the route: it reasons, formats and costs differently.

### Terms

| Term | Meaning here |
|---|---|
| Per-attempt timeout | How long one attempt may take before it counts as failed |
| End-to-end deadline | When the whole operation must be finished, across attempts and fallbacks |
| Retry policy | Which failures to retry, how many attempts, how long to wait between |
| Exponential backoff, jitter | A wait that doubles each time, with a random share so callers spread out |
| Retry amplification | Retries at several layers multiplying into many attempts and long waits |
| Transient / permanent failure | Slow or full right now / wrong every time; only the first is worth a retry |
| Fallback | Another route or another provider that can do the same job |
| Circuit breaker | A failure count that, past a threshold, skips the dependency for a cooldown; closed, open, half-open |
| Graceful degradation, safe default | Ending on a worse but legal outcome when nothing answers |
| Fail-open / fail-closed | Going ahead without an optional dependency / refusing the request or feature |
| Bulkhead | A separate pool per dependency, so one slow dependency cannot use up shared capacity |
| Hedged request | A second copy sent when the first runs slow; the first answer wins |

### Depth boundary

Core: timeouts against deadlines, retry policy and its amplification, failure classification,
fallback, the breaker's three states and its misuses, safe defaults, and the three ways to treat an
optional dependency. Recognise only: bulkheads and hedged requests. Deferred: making a retry safe to
repeat (U4); retry budgets and load shedding (the AWS article in part 4); each SDK's retry internals
(pointed to in part 3).

## 2. Alternatives and trade-offs

| Design | What it buys | What it costs | Fits when |
|---|---|---|---|
| Retry with exponential backoff and jitter | Rides out brief blips | Spends the deadline; adds load to a struggling service | Failures are short and transient |
| Hedged requests | Cuts the slow tail | Extra load; for an LLM, a second bill | Calls are cheap, safe to repeat, and tail latency matters |
| Fallback to the same model on another route | Same behaviour | May share the outage | The fault is in the route, not the model |
| Fallback to a different model **(this project)** | Fails for different reasons | Changes behaviour and cost; needs testing in that role | A behaviour change is acceptable |
| Breaker per dependency | One shared count; everyone learns of an outage at once | One noisy caller or one bad region trips it for all | Failures belong to the whole dependency |
| Breaker per caller **(this project: per game)** | One caller's trouble stays its own | Every caller relearns the same outage | Callers use different keys, quotas or routes |
| Whole-request watchdog | Bounds the total; catches a hang anywhere | Must cancel cleanly; does not say which part hung | Many steps, and the total time is what users feel |
| Per-call deadlines only **(this project)** | Simple and local | The total is the sum of the parts; a hang outside a call goes unseen | Few calls per request |
| Optional dependency: refuse clearly **(this project)** | The user decides; no surprise | The feature is unavailable for a while | The user asked for the feature |
| Optional dependency: disable silently | The request succeeds | The user cannot tell what changed | The feature is a cosmetic extra |
| Optional dependency: let the request fail | Nothing to build | An optional part takes down the core | The dependency is in fact required |

My server runs games of hundreds of model calls, and every turn must end in a legal move. So I
bounded each call, made a stall hand the turn to a different model, and kept the stall count per
game, because each game can run on its own model and key. The lesson store is a feature the player
switches on, so the server refuses it clearly rather than quietly playing without it.

## 3. This project

**The request budget.** Each in-game model accessor asks for 30 s per attempt and 2 attempts in
all; the day summary asks for 90 s per attempt. Environment variables can change each value. The budget
covers the turn model, its rescue, the summary and its rescue, the judge and the extractor. **code**
([accessors.py](../../../Agents/llm_factory/accessors.py)::`_request_budget`); **test**
`test_every_in_game_model_carries_the_request_budget`, not run
([test_model_fallback.py](../../../tests/engine/test_model_fallback.py)).

**Which clients receive it.** The OpenAI-protocol clients (DeepSeek among them) and Claude get the
attempt count minus one, because their SDKs count retries after the first; Gemini's client takes it
unchanged. The Mistral client gets neither value.
**code** ([chat.py](../../../Agents/llm_factory/chat.py)::`_request_limits`;
[mistral.py](../../../Agents/llm_factory/providers/mistral.py)::`MistralChatModel`).

**Nothing bounds the turn as a whole.** On the stall path a turn can spend 2 × 30 s on the primary
and 2 × 30 s on the rescue, plus SDK backoff: about two minutes. A day summary can spend about six.
This is my arithmetic from the code, not a measurement. **code**
([agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`;
[summary_agent.py](../../../Agents/nodes/day/summary_agent.py)::`run_day_summary_agent`).

**Stall classification.** A failure is a stall when anything in its exception chain is a timeout,
has status 408, 429 or 5xx, or carries a marker such as "quota" or "timed out". A refused key (401,
403) is checked first, as permanent: on the primary it ends the game. A reply that broke the schema
is asked again on the same model. **code** ([embeddings.py](../../../Agents/llm_factory/embeddings.py)::`is_transient_provider_error`;
[agent_player.py](../../../Agents/turn/agent_player.py)::`_generate`); **test**
`test_transient_errors_are_the_provider_being_slow_or_full`,
`test_a_refused_key_on_the_primary_ends_the_game`, not run.

**A stall goes to the rescue once.** A stalled primary is not asked again that turn; the rescue gets
one call, with its own two attempts. If the rescue stalls too, the turn takes the safe default.
**code** ([agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`); **test**
`test_a_stalled_primary_is_not_asked_again_and_the_rescue_takes_the_turn`,
`test_both_models_stalled_falls_to_the_typed_fallback_not_a_crash`, not run.

**The breaker.** `ModelHealth` counts stalls in a row. At 2 it opens: for 300 s every turn starts on
the rescue. After the cooldown the primary gets a try; the count still stands at the threshold, so
one more stall reopens it; a good answer clears it. There is one per game. Unlike the textbook
breaker, it counts only stalls, routes to the fallback rather than failing fast, and acts only when a
rescue exists (`fallback_llm is not None`). **code**
([health.py](../../../Agents/llm_factory/health.py)::`ModelHealth`;
[agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`); **test**
`test_repeated_stalls_send_the_next_turns_straight_to_the_rescue`,
`test_after_the_cooldown_the_primary_is_tried_again`, not run.

**Where the rescue comes from.** A served game takes its catalogue row's `rescue_model`, on the
game's own credential, or, with a player's second-company key, that company's backup model. Batch
and CLI runs default to Sonnet 5.5. **code**
([accessors.py](../../../Agents/llm_factory/accessors.py)::`_rescue_model`;
[game_session.py](../../../server/game/game_session.py)::`GameSession.__init__`;
[model_catalog.py](../../../server/game/model_catalog.py)::`backup_model`).
The syllabus outline says the rescue comes "from another provider"; in the seed catalogue every
rescue is from the model's own provider, because it shares the credential. **code**
([catalog.py](../../../Agents/llm_factory/catalog.py)::`SEED_MODELS`).

**The house default has no rescue.** The only house-funded row in the seed, Claude Haiku 5.5, has an
empty rescue, and a house game has no player key to attach a backup to. So a stalled turn in a house
game on Haiku goes straight to the safe default, and the open breaker changes nothing. **code**
([catalog.py](../../../Agents/llm_factory/catalog.py)::`SEED_MODELS`;
[house.py](../../../server/house.py)::`HousePolicy._default_model`;
[_shared.py](../../../server/routes/_shared.py)::`resolve_backup`).

**The safe default.** A day or wolf discussion turn becomes a technical pass; a vote or a wolf kill
takes a random legal target; a night action takes the role's no-action word, or a random legal target
when the role has none. An unwritten day summary becomes the raw transcript. **code**
([agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`;
[summary_agent.py](../../../Agents/nodes/day/summary_agent.py)::`run_day_summary_agent`); **test**
`test_exhausted_day_discussion_records_technical_pass`,
`test_a_summary_with_no_working_rescue_is_the_raw_channel`, not run.

**The optional dependency.** The lesson store is unready when nothing has been published, when its
index was built by another embedder (the message names both), or when it holds no strategy points. A
memory-on game is then refused with a 409 giving the reason, and `GET /models` reports memory as
unavailable so the page can hold its switch off. A memory-off game skips the check. **code**
([postgres.py](../../../Agents/memory/persistence/postgres.py)::`unready_reason`;
[_shared.py](../../../server/routes/_shared.py)::`require_memory_available`); **test**
`test_an_unpublished_or_empty_store_is_not_ready`, not run
([test_postgres_publish.py](../../../tests/memory/test_postgres_publish.py)).

**Incidents on record:**

- The 301-second turn: 282 s of it sat inside the retrieval call. Vertex held requests for minutes, then
  bounced them with 429; the SDK and LangChain retried each bounce silently, and the rescue, keyed on
  errors, never fired. **incident** (2026-09-30,
  [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1).
- Every new game failed with a 500: the session rebuilt a stale file store for every game, memory on
  or off. The fix moved lessons to Postgres and added the readiness check. **incident** (2026-10-14,
  [deploy_log.md](../../../frontend/docs/deploy_log.md)).
- The budget reached only Gemini's clients for three weeks; a DeepSeek client waited its SDK's 600 s a
  try, three tries, before the rescue was asked. **incident** (2026-10-21, game `e45eda20`,
  [deploy_log.md](../../../frontend/docs/deploy_log.md)).

**Not established:**

- The stall rate since the fix: no record counts rescued or defaulted turns.
- Any whole-game watchdog: none exists, and a hang outside a model call goes undetected
  ([server_design_notes.md](../../../frontend/docs/server_design_notes.md) §5c, mode 4).
- Whether the budget reaches every provider's client: Mistral's takes none, and I did not check
  whether any current configuration reaches it.
- Whether the live catalogue table matches the seed; I did not read the table.
- The basis for 30 s: the "worst honest turn of 11 s" behind it has no recorded sample size.

**Framework specifics, pointed to:** the stacked google-genai and LangChain retry layers, in
[agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1; the OpenAI and
Anthropic SDK defaults, in the docstring of [chat.py](../../../Agents/llm_factory/chat.py)::`_request_limits`.

## 4. Reading

- [AWS Builders' Library, "Timeouts, retries, and backoff with jitter"](https://d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf),
  the timeouts and the retries-and-backoff sections: picking a timeout from the dependency's
  latency, why retries are selfish, and why retrying at several layers multiplies load.
- [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1: the hang that
  never raised an error, and the fixes in order.
- [health.py](../../../Agents/llm_factory/health.py), the whole file (51 lines): map each breaker state
  onto its methods.
- *Optional:* Martin Fowler, ["CircuitBreaker"](https://martinfowler.com/bliki/CircuitBreaker.html),
  the three states in one short account.

## 5. Checks

**Transfer.** A request calls a retrieval service and then a model, each with its own retry policy,
under a 20-second user-facing budget. Allocate the deadline across the two calls, say what happens
when retrieval fails, and say what you would want to know before setting the breaker's threshold.

**Project evidence.** A draft says: "every stalled turn moves to a rescue model". What stands behind
it, and what is the accurate wording?

## 6. Workbook

- **The concept in my own words:**
- **My transfer answer:**
- **The project claim and its support:**
- **Remaining gaps / questions to record:**
- **Time taken:**

---

## Answer keys

*Attempt the checks first.*

**Transfer.** Assumptions: retrieval normally answers in 300 ms, its slowest 1% in 800 ms; the model
answers in 4 s, its slowest 1% in 9 s; the answer is not streamed; the model can answer without
retrieved context, only less well.

Keep 1 s for my own work, which leaves 19 s. Retrieval gets at most 2 s: a 1 s timeout, and one
jittered retry if the failure is transient. The model gets about 17 s, with a 12 s timeout, above its
slowest 1%. A second model attempt goes only if a slow answer still fits: a 429 at second 1 leaves
room, a timeout at second 12 does not, so the request goes to a faster fallback model or a safe
default. The SDKs are set to one attempt so only my code retries, and each call gets the time left.

When retrieval fails, classify it. Transient with time left: retry once. Otherwise answer without
context and say so ("no sources found"): fail-open. If the product promises grounded answers, fail
closed and refuse clearly. With the retrieval breaker open, skip the call and give the model 18 s.

Before setting the threshold I want: the traffic per window, since a rate needs enough calls; the
normal error rate and its swing; whether failures are outages or bad queries; whether regions fail
separately; the usual recovery time, which sets the cooldown; and what a false trip costs against a
missed one. A starting point: open at 50% failures over at least 20 calls in
10 s, cool down 30 s, then let one call through.

**Project evidence.** A stalled turn goes to the rescue only when one exists. The house default, Haiku
5.5, has none in the seed catalogue, and a house game cannot carry a backup key, so its stalled turns
take the safe default. Where a rescue exists it gets one call, and if that stalls too the turn takes
the safe default as well. The agentic log's later note that Sonnet rescues Haiku describes batch and
CLI runs, not served games.

Accurate wording: "A stalled turn goes to the game's rescue model where the game has one, otherwise
to the legal fallback: a pass, a random legal target, or the role's no-action word."
