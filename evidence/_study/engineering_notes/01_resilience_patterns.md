# U1. Resilience patterns for remote calls: the concepts, and a review of my system

**Reading time:** about 90 minutes · **Builds on:** U0 · **Feeds write-up chapter:** 7

**The question these notes answer:** a service I depend on is slow, failing or gone. How does my
system still end somewhere sensible?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

U0 drew the model providers outside the trust boundary: services I call, pay for and don't run.
These notes are about what a system does when one of them is slow, failing or gone.

## What these notes cover

1. Why a call that hangs is harder to handle than a call that fails, and what fixes it.
2. Which failures are worth asking again, and what goes wrong when several layers each retry.
3. A circuit breaker's three states, and the situations where it is the wrong tool.
4. One failing request traced from the first call to a safe ending, with the pattern at each step.
5. A review of what happens to a stalled turn in my Werewolf system, with its numbers and its gaps, ending with a claim the code supports.

**Covered in other notes:** making a repeated request safe (U4), what stops the server itself from
freezing while a call waits (U2), and reading a failed call in a trace (U8). Retry budgets and load
shedding are in the reading list only.

---

# Part 1 — What a service does when a call goes wrong

Resilience patterns are the rules a service follows when something it calls is slow, failing or
gone. "Something it calls" means anything reached over a network, in another process: a payment
provider, a model provider, and also a database in the next container on the same machine. What
makes a call remote is that the other side can be slow or gone while this side keeps running. The
patterns answer four questions:

1. **How long do I wait?** (timeout)
2. **Do I ask again?** (retry)
3. **When do I stop asking?** (circuit breaker)
4. **What do I do instead?** (fallback)

The first two are about one call. The third is about the calls after it: once a service has failed
several times, later requests skip it. The fourth is where the other three lead. A call that failed
after its retries and a call that was never made both end at the fallback, which is why it comes
last.

Every pattern below is an answer to one of the four. Held as a list, they give each new term a
place to go.

The example throughout is a shop's checkout. A customer presses Pay, and the checkout service calls
a payment provider. Customers give up after about ten seconds.

## 1.1 How long do I wait?

One day the payment provider accepts the connection and never answers.

The checkout has a handler for payment errors. But no error arrives, so the handler never runs, and
the customer's spinner turns forever. A hang is the one failure an error-driven design cannot see:
everything the checkout does about failures is triggered by an error, and a hang produces none.

The fix is a **timeout**: after a set time, give up on this attempt and raise an error. A timeout
turns time into a failure, so the error handling that already exists can act on it.

A timeout limits one attempt. The customer cares about something else: when the whole checkout is
done. That is the **deadline**, one limit across every attempt and everything tried instead. The
difference shows up as soon as there is more than one attempt. With a 10-second timeout and two
retries, the customer can wait 30 seconds, and every single attempt was within its limit. With a
deadline, each step asks how much time is left and sizes its own timeout from that.

### Check

A service sets a 5-second timeout on a call and allows three attempts. Nobody set a deadline. What
is the longest a user can wait, and what has to change to promise them 8 seconds?

<details>
<summary>Answer</summary>

About 15 seconds, plus any waiting between attempts. Either number can be cut to fit: 2.5 seconds ×
3 attempts, or 4 seconds × 2. But that bound is fixed in advance, and it costs twice. Every attempt
gets the short limit, even the first, so calls that would have answered at 3 seconds now fail. And
the sum still leaves out the waits between attempts and anything that runs after the call, such as
a fallback. A deadline of 8 seconds makes the promise directly: each attempt is given whatever time
is left, so the first can use 6 seconds and a retry the remaining 2.
</details>

## 1.2 Do I ask again?

Sometimes the provider returns an error once and works a moment later. Asking again fixes it. A
**retry policy** says which failures to retry, how many attempts to allow, and how long to wait
between them.

The wait between attempts doubles each time (**exponential backoff**) and includes a random share
(**jitter**). The reason is the other customers: when a thousand checkouts fail together, fixed
waits would have all thousand retry in the same instant and knock the provider over again. A retry
is never free. Each one adds load to a service that is already struggling and spends the customer's
time.

**Which failures are worth a retry?** A timeout, a 429 "too many requests" or a 503 says the
provider is slow or full right now. That is a **transient** failure, and a later attempt may
succeed. A 400 "invalid card number" or a 401 "bad API key" fails the same way every time. That is
a **permanent** failure. Retrying it burns the deadline and hides the real problem. So a retry
policy starts with **failure classification**: sort the failure first, then decide.

**Retries in layers.** The checkout code retries three times. The payment SDK underneath retries
three times. The HTTP library under that retries three times. One slow request becomes 27 attempts,
each with its own timeout, and the customer waits minutes. Every layer looked sensible on its own.
This is **retry amplification**. The fix is to retry at one layer, set the others to a single
attempt, and let the deadline cap the total.

### Check

For each failure: retry or not? (a) the connection timed out, (b) 401 unauthorised, (c) 429 too
many requests, (d) the reply arrived but is missing a required field.

<details>
<summary>Answer</summary>

(a) Yes: transient. (b) No: the key is wrong and will be wrong next time; surface it. (c) Yes, after
a wait, since asking at once adds to the overload. (d) It depends on the service. A payment
provider's malformed reply is a bug and retrying won't fix it. A language model's malformed reply is
different, because the same request can produce a different answer; Part 1.6 comes back to this.
</details>

## 1.3 When do I stop asking?

Now the provider is down for twenty minutes. Retrying cannot help, and it is wasteful: during the
outage every checkout waits out its full timeout, and its retry, on the dead provider before giving
up. Each customer pays for a failure the system already knows about.

A **circuit breaker** stops that. It counts recent failures of one dependency and has three states:

```text
            failures pass a threshold
  CLOSED ─────────────────────────────▶ OPEN
  calls go through                      calls skip the dependency
     ▲                                     │
     │ trial call succeeds                 │ cooldown ends
     │                                     ▼
     └──────────────────────────────── HALF-OPEN
           trial call fails ──▶ OPEN   one trial call is let through
```

While things are fine it is **closed**, and calls go through. Past a threshold it **opens**: for a
cooldown, calls skip the dependency. What they do instead is the next question (1.4). After the
cooldown it is **half-open** and lets one trial call through. A success closes it; a failure opens
it again. A breaker saves the caller's time and gives the dependency room to recover.

**When is a breaker the wrong tool?** A breaker assumes the failures belong to the dependency. Four
cases break that assumption:

- **The failures come from the requests.** Declined cards are not an outage. A breaker that counts
  them trips on customers' mistakes and blocks good requests.
- **Traffic is thin.** A few failures cannot tell an outage from bad luck.
- **Only part of the dependency is down.** If one region of the provider fails, a breaker over the
  whole provider blocks the healthy regions too.
- **There is nothing to do instead.** With no fallback (1.4), opening the breaker only changes how
  quickly the customer sees an error.

**How are the threshold and the cooldown chosen?** A breaker has two numbers: how many failures
open it, and how long it stays open. Four things decide them, and all four come from the caller's
own records, not from the provider:

| What to know | Why | Where it comes from |
|---|---|---|
| How many calls are made per minute | A rate such as "half of the calls failed" needs enough calls behind it. With thin traffic, a count of failures in a row is the form that works | The caller's own request counts |
| The error rate on a normal day | The threshold has to sit well above it, or ordinary failures trip the breaker | The caller's own logs. A provider's status page reports outages, not this caller's error rate |
| How long the service usually takes to recover | The cooldown should be about that long. Too short and callers keep testing a dead service; too long and they stay away from a healthy one | Past incidents, and any "retry after" time the service sends |
| What a wrong trip costs against a missed one | A cheap wrong trip allows a low threshold | The product: how good the fallback is, and how long a wasted timeout is |

The checkout makes hundreds of payment calls a minute, so it can use a rate: open when half of at
least 20 calls in 10 seconds have failed. A wrong trip sends customers to the second gateway, which
is cheap, so the threshold can be low.

### Check

A team adds a breaker around a search service. It opens several times a day, though the service's
own dashboard shows no outages. Two things to check?

<details>
<summary>Answer</summary>

What the breaker counts as a failure: if bad queries (400s) count, users are tripping it. And how
much traffic stands behind the threshold: "3 failures" out of 4 calls in a quiet hour is not
evidence of an outage. A third candidate is the timeout: if it is shorter than the service's normal
slow answers, healthy calls are being counted as failures.
</details>

## 1.4 What do I do instead?

Two kinds of checkout now arrive without a payment: one whose call failed after its retry, and one
that the open breaker never let call at all. Both still have to end somewhere.

There are three things a checkout can do at this point. The first two are both called a
**fallback**; the third is not one.

| What it does | Name | The checkout example | Does the checkout finish? |
|---|---|---|---|
| Gets a real answer another way | An **alternative source** | A second payment gateway | Yes, as normal |
| Supplies a fixed, safe result of its own | A **static fallback**, also called a default response or a **safe default** | "Order saved; we'll email you when payment goes through" | Yes, in a reduced form |
| Returns an error at once and hands the decision back | **Fail fast** | "Payment is unavailable; try another method" | No. The customer decides what to do next |

**An alternative source only helps if it fails for different reasons than the first.** A second
gateway helps when the first gateway is down. It does not help when the card network behind both is
down, because they share that outage. And it never helps when the card itself is the problem: that
is a permanent failure that comes from the request, sorted out in 1.2, and it should not reach a
fallback at all. The further an alternative is from the original, the fewer failures it shares and
the more it changes what the customer experiences: a bank transfer fails for different reasons than
any card gateway, but it is a different way to pay.

**A static fallback is judged by the rule it protects, not by how helpful it looks.** "Order saved"
keeps the shop's rule true: no order is marked paid without a payment. Ending on a result like
this, worse than the real answer but still correct, is what **graceful degradation** means.

**Fail fast is the right choice when no substitute is safe, or when the person is better placed to
choose.** It responds as quickly as a static fallback does. The difference is that the system
supplies no result.

The three are often used in order: the alternative source first, then the static fallback, and an
error only when neither exists. Which of them a product has depends on the product.

## 1.5 A soft dependency

A **hard dependency** is one the request cannot finish correctly without: the payment provider, for
a checkout. A **soft dependency** is one it can finish without, with a worse result. The words are
about whether the request can still complete, not about how much the feature matters. A soft
dependency can be central to the product's quality and still be soft.

Customers can also pay with loyalty points, held by a separate service that is now down. Paying by
card still works. There are three choices:

- Refuse the feature clearly: "points are unavailable; pay by card".
- Disable it silently and charge the card in full.
- Let the whole checkout fail.

Going ahead without the dependency is **fail-open**. Refusing is **fail-closed**. The choice turns
on whether the customer asked for the feature and what a silent change costs them. A customer who
chose to pay with points and was silently charged the full price has been surprised with their own
money; a clear refusal lets them decide.

## 1.6 What changes for LLM calls?

Everything so far holds for any remote call, and a model provider is one more service across a
network. Three things are different about it.

**1. The hang is common.** A provider under load does not always refuse a request. It often accepts
the request and puts it in a queue, and the caller waits with the connection open. The wait can end
in an answer, or minutes later in a 429 "too many requests". From the caller's side this is a hang:
no error, no answer. Two things make it worse than with an ordinary service:

- A healthy reply already takes several seconds, and longer for a long output, so there is no
  obvious point at which the wait has become abnormal.
- The provider libraries allow for those long replies with a generous default, around ten minutes
  per request. Left alone, a queued request is waited on for that long.

So a system that switches models only on errors has a hole exactly here, until a timeout makes time
a failure. The timeout is chosen from measured reply times: well above the slowest healthy reply,
and far below the default.

**2. A fallback model changes behaviour, not only the route.** A second payment gateway charges the
same card and the result is identical. A second model reasons, formats its output and costs
differently, so it has to be tested in the role before it is trusted with it.

**3. A wrong reply is a third kind of failure.** A model can answer on time and still break the
required format, or choose something the rules do not allow. That is not transient in the usual
sense, since the provider is healthy, and not permanent either, since the same request can produce
a different answer. Asking the same model again is cheap and often works. So an LLM system sorts
failures three ways: slow or full, key refused, and answer wrong.

## 1.7 One request, start to finish

All of Part 1 as one checkout, with a 10-second deadline.

```text
 0.0 s  Customer presses Pay. Deadline: 10 s.
        Breaker for provider A is CLOSED, so the call goes to A.
 0.0 s  Attempt 1 on A, timeout 3 s .................. (how long do I wait?)
 3.0 s  Timeout. Classify: transient. 7 s left, so retry once.
 3.4 s  Attempt 2 on A after a jittered wait ......... (do I ask again?)
 6.4 s  Timeout again. Attempts used up.
        Breaker counts 2 failures and OPENS .......... (when do I stop asking?)
 6.4 s  Fallback: provider B, timeout = the 3.6 s left  (what do I do instead?)
 7.1 s  B answers. Order paid.

 Next customer, one minute later:
 0.0 s  Breaker for A is OPEN. Skip A, call B at once.
 0.7 s  B answers. Order paid, with no 6-second wait.

 If B had failed too:
        Safe default: "order saved; we'll email you when payment goes through".
```

The first customer paid for the discovery. The breaker is what stops every later customer from
paying for it again.

**Two more patterns to recognise.** Neither answers a new question. Each covers something the
four above leave open, and neither is used in my project.

- **A bulkhead limits how many calls can be waiting on one dependency at the same time.** A timeout
  limits how long one call waits; it says nothing about how many are waiting. Suppose the checkout
  server can handle 50 requests at once and the points service hangs. Within seconds all 50 are
  waiting on points, each inside its timeout, and a customer paying by card cannot get in. A
  bulkhead gives points its own small share, say 10 of the 50, so the other 40 stay free for
  payment. The name comes from the walls that divide a ship's hull, so one flooded section does not
  sink the ship. It works beside the breaker: the breaker stops the calls once failures have been
  counted, and the bulkhead caps the damage before that.
- **A hedged request is a retry sent before the first attempt has failed.** A normal retry waits for
  the timeout, then asks again. A hedge sends a second copy as soon as the first is slower than
  usual, say after 1 second when most answers take 300 ms, and uses whichever answers first. It
  cuts the wait on the slow few. The price is extra load on the service, extra cost where each call
  is paid for, and the request must be safe to send twice (U4).

---

# Part 2 — The choices

The four questions are not alternatives to each other. A timeout, a retry policy, a breaker and a
fallback work together, as the timeline showed. The choices are inside each question. Within a
table, a system can use more than one row, in different places; the last column says where mine
uses each.

**How is the time bounded?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| A timeout on each call only | Simple and local | The total is the sum of the parts; a hang outside a call goes unseen | Few calls per request | Every model call and the embedding call |
| A deadline over the whole request | Bounds what the user feels; catches a hang anywhere | Must cancel cleanly; does not say which part hung | Many steps, and total time is what matters | Not used |

**What happens to a call that fails?**

These three are often used one after another, not one instead of another.

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| Retry with backoff and jitter | Rides out brief blips | Spends the deadline; adds load to a struggling service | Failures are short and transient | The provider's client makes a second attempt on each model call; the embedding call gets 5 attempts with doubling waits; a broken reply is asked again once |
| Fallback on the same model, another route | Nearly the same behaviour | May share the outage; hosts can differ slightly | The fault is in the route, not the model | The embedder: one model on two named hosts |
| Fallback to a different model | Fails for different reasons | Changes behaviour and cost; needs testing in that role | A behaviour change is acceptable | The game's model: the rescue |

**Whose failures does the breaker count?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| One breaker per dependency | Everyone learns of an outage at once | One noisy caller or one bad region trips it for all | Failures belong to the whole dependency | Not used |
| One breaker per caller | One caller's trouble stays its own | Every caller relearns the same outage | Callers use different keys, quotas or routes | One per game |

**What happens when a soft dependency is down?**

| Design | What it buys | What it costs | Fits when | In my system |
|---|---|---|---|---|
| Refuse the feature clearly | The user decides; no surprise | The feature is unavailable for a while | The user asked for the feature | A memory-on game is refused at creation when the lesson store is not ready |
| Disable it silently | The request succeeds | The user cannot tell what changed | The feature is a cosmetic extra, or stopping would cost more than going without | During a game: a failed lesson lookup plays the turn without lessons, and a failed echo check keeps the line |
| Let the request fail | Nothing to build | A soft dependency takes down the core | The dependency is in fact a hard one | Not by design; it happened once by accident (3.4) |

On the embedder's two hosts: the order is Nebius then DeepInfra, and no others, because a third
host serves a reduced-precision version. I tested the setting with a handful of live
requests. The two hosts' vectors for the same 10 sentences had a cosine of 0.9972 to 0.9979, which
I judge small against thresholds near 0.8. A host that cannot serve the model is skipped and the
next one on the list answers, so the list is walked in order. What the test did not show is the
case that matters most: whether a request moves to DeepInfra when Nebius is serving the model but
refuses this request. Nebius did return a 429 once during the test, so that case is real.

No row is the better design. Each one fits a situation, and the "Fits when" column says which.

---

# Part 3 — My Werewolf system

## 3.1 The turn that took 301 seconds

On 2026-09-30, one AI player's turn took 301 seconds. 282 of them sat inside one step, the memory
retrieval, waiting on the model provider.

The project already had a rescue model at that point: if the primary model raised an error, the
turn went to a second model. It never fired. The provider was holding requests in its queue for
minutes and then bouncing them with a 429. Two libraries underneath my code each retried the
bounce silently: the provider's SDK up to five times, and the framework wrapping it six times
around that. Thirty retries deep, no error ever reached my code. The call was simply still
running.

This is section 1.1 exactly: a fallback triggered by errors cannot see a hang. And it is section 1.2
as well: retries stacked in layers I had not set. Everything below was built in answer to that
turn.

## 3.2 What happens to a turn now

A game is hundreds of model calls, and the game has one rule that the failure handling protects:
**every turn must end in a legal move.** Here is how each of the four questions is answered.

**How long do I wait?** Every model call in a game is given 30 seconds per attempt and 2 attempts.
The day summary, which reads a whole day's discussion, gets 90 seconds per attempt. Both numbers
are passed to the provider's SDK, which does the timing and the second attempt. This is the one
layer where a slow call is retried. The 30 seconds sits well above a normal turn: across 13 served
games, the slowest 5% of discussion calls took 10.8 seconds.

**Do I ask again?** My code classifies every failed call three ways, and each gets a different
answer:

| What happened | How it is recognised | What the turn does |
|---|---|---|
| **Stall**: the provider is slow or full | A timeout, a 408, 429 or 5xx, or a message such as "quota" or "timed out", anywhere in the error's chain | Not asked again. The turn goes to the rescue model |
| **Key refused** | A 401 or 403, or a message such as "invalid api key" or "credit balance is too low" | On the primary model, the game ends and says why. No later turn could succeed |
| **Answer wrong**: the reply broke the format or chose an illegal move | The reply fails to parse, or the game's rules reject the decision | The same model is asked once more, with the format enforced where the provider allows it |

The first row is the design decision to remember. A stalled model has already had its 2 × 30
seconds inside the SDK. Asking it again from my code would be retry amplification, so my code
doesn't.

**When do I stop asking?** Each game has one stall counter, shared by every seat in that game. After
2 stalled turns in a row, the breaker opens: for 300 seconds, every turn in that game starts on the
rescue model and skips the primary. After the 300 seconds the primary gets one try. A good answer
clears the count; one more stall opens it again for another 300 seconds. That one try is a real
player's turn, with the full 2 × 30 seconds. If the primary is still stalled, that turn waits up to
a minute before the rescue takes it: the price of testing, paid once per 300 seconds. Two ways to
make the test cheaper, neither built: give the test turn one try or a shorter limit, or test with a
small separate call that is not a player's turn, at the cost of one paid call per test.

My breaker differs from the textbook one in three ways, and each is a deliberate fit:

- **It counts only stalls.** Wrong answers and refused keys don't count, which avoids the "failures come from the requests" misuse in 1.3.
- **It routes to the rescue; it never fails fast.** An open breaker with nowhere to go would help nobody.
- **It is one per game, not one per provider.** Each game can run on its own model and its own player's key, so one game's quota trouble says nothing about another's.

Why per game: a stall has two possible causes with different reach. The
provider can be short of capacity for a model, which hits every game on that model whatever its
key; the 2026-09-30 incident was this. Or one key can be over its own limit, which hits that key
only. The ideal breaker would count the first per model and the second per key. My code cannot tell
them apart reliably: the 2026-09-30 capacity problem arrived as a 429 "resource exhausted", which
reads like a quota error. A breaker per game is never wrong about whose trouble it is. Its cost is
that when a model is overloaded for everyone, each game learns it separately, at two stalled turns
each. A breaker shared by games on the same key and model would fit house games better, and would
change little today because house games have no rescue to move to. Two things here are outside my
code and may have changed since: how providers word the two causes, and that paid API accounts are
rate-limited by tier, which I state from general knowledge and did not check against current
provider pages.

How the two numbers stand against the four inputs of 1.3:

| Input | In my system |
|---|---|
| Calls per minute | Few: one game makes a model call every few seconds at most. A rate would mean nothing, so the breaker counts stalls in a row. Each counted stall is already two failed attempts |
| Normal error rate | Not known. Nothing totals the stalls (3.3, gap 2) |
| Recovery time | The 2026-09-30 incident held requests "for minutes". 300 seconds fits that, but no record says how it was chosen |
| Wrong trip against missed trip | A wrong trip puts the game on a tested rescue model for five minutes. A missed one costs each turn up to 60 seconds. That favours a low threshold, and 2 is low |

So the form (a count in a row) and the low threshold have reasons. The exact values, 2 and 300, are
defaults that have not been checked against data.

**What do I do instead?** A stalled turn, and every turn while the breaker is open, goes to the
**rescue model**. It gets one call, with its own 2 × 30 seconds. If the rescue also fails, the turn
takes a safe default chosen to keep the game legal:

- A discussion turn becomes a pass, recorded as a technical pass and not as the player choosing silence.
- A vote or a wolf kill takes a random legal target, because the phase cannot finish without one.
- A night action takes the role's "do nothing" option when it has one, and a random legal target when it doesn't.
- A day summary that could not be written becomes the raw transcript.

In the terms of 1.4, the rescue model is the alternative source and the safe default is the static
fallback. A stalled turn never fails fast, because an AI player has nobody to hand an error to and
the game needs a legal move. The one place my system does fail fast is a refused key: the game ends
and says why, since no later turn could succeed.

**The calls around the turn follow the same rules.** A turn can make three more remote calls
besides its own:

| Call | When it runs | A stall | While the breaker is open | If it fails |
|---|---|---|---|---|
| Situation summary: describes the player's position so lessons can be looked up | Memory on, before the turn | Counted, not asked again; the rescue model gets one try | Starts on the rescue model | A plain placeholder is used as the search text |
| Embedding of that search text | Memory on, inside the lookup | 30 seconds per request, up to 5 tries with growing waits; only my loop retries | Not affected: it is a different service | The turn is played without lessons |
| Echo check: judges whether a discussion line adds anything | Discussion turns where the player was given the floor | Counted | Skipped, and the line is kept | The line is kept |

One lookup's embedding can still take about three minutes in the worst case, and while it waits it
holds the lesson store's lock, so other seats' lookups queue behind it.

Put together, a turn where both models stall looks like this:

```text
  0 s   Primary model, attempt 1 (30 s limit) ........ times out
 30 s   Primary model, attempt 2, by the SDK .......... times out
 60 s   Classified as a stall. Stall count: 1. Not asked again.
        Rescue model, attempt 1 (30 s limit) .......... times out
 90 s   Rescue model, attempt 2 ....................... times out
120 s   Safe default: a pass, or a random legal target.

 Next turn stalls too: stall count 2, the breaker opens.
 For the next 300 s, every turn in this game starts on the rescue.
```

About two minutes, plus the SDK's short waits between attempts. Compare it with the 301 seconds of
the incident, which had no upper limit at all.

Two minutes is the plain stall path, not the longest one. All of
these are arithmetic from the code, not measurements:

| Path | Calls | Longest wait |
|---|---|---|
| Both models stall (the timeline above) | primary, rescue | 2 × 2 × 30 s = 120 s |
| The primary answers late with a broken reply, is asked again and stalls, then the rescue stalls | primary, primary, rescue | 3 × 2 × 30 s = 180 s |
| The same, on a discussion turn where the echo check also runs and stalls | primary, primary, rescue, judge | 4 × 2 × 30 s = 240 s |
| Memory on: the situation summary stalls first, and its rescue stalls too | summary, its rescue, then any path above | adds 2 × 2 × 30 s = 120 s |

So with memory on the bounded part of a turn can reach five to six minutes, when every model
involved stalls at once. Once the breaker is open the helper calls skip the primary as the turn
does, and those figures halve.

### Check

A model answers within 5 seconds, but its reply names a player who is already dead as its vote.
Does the stall counter go up? What happens next?

<details>
<summary>Answer</summary>

No. That is "answer wrong", not a stall, so the breaker doesn't count it. The same model is asked
once more. If the second answer is also unusable, the rescue model gets one call, and after that
the vote takes a random legal target.
</details>

## 3.3 Gaps

**1. A whole turn has no time limit.** Each call is limited, but nothing adds them up. With memory
on, the worst case is about five minutes, which is too long for someone watching one AI player
think. There are three ways to fix it:

| Fix | Good | Bad |
|---|---|---|
| Rewrite the engine as async code, with a real deadline | Can stop a call while it is waiting | A rewrite of working code |
| Check the clock between calls; past a budget, skip the rest and take the safe default | One number for the whole turn | Cannot stop a call already running, so the limit is the budget plus one call |
| Lower the timeouts or the attempts | No new code | To reach two minutes, each call gets about 20 seconds and one try, so some healthy slow replies become passes. House games lose their second try, which is their only protection |

My choice: lower the limits for the two helper calls only, since both have a harmless fallback, and
add the clock check for the turn. Not built.

**2. Nothing adds the failures up.** Each rescue and each safe default is written to the log as it
happens, and a pass caused by a failure is recorded as a technical pass. But nothing totals them, so
I cannot say how often a turn is rescued or defaulted. One case leaves no mark at all: a call whose
first try times out and whose second answers looks like a normal reply that came 30 seconds late.
This is a measurement gap more than a failure-handling one, and U8 takes it up. It still comes
before choosing a fix above.

**3. House games have no rescue model.** A rescue has to run on the same key as the game. The
house's model, Claude Haiku 5.5, has none listed, so a stalled turn in a house game goes straight
to the safe default. A player with their own key can add a second company's key and get a rescue.
This matters for wording: "every stalled turn moves to a rescue model" is false for the most common
kind of game.

## 3.4 The soft dependency: the lesson store

A player can switch on memory, which gives the AI players lessons from past games. The lessons live
in a store that can be unready for three reasons: nothing has been published to it, its index was
built with a different embedding model from the one the server now uses, or it holds no strategy
lessons.

This is the loyalty-points situation from 1.5, and the project takes the first choice: refuse
clearly. A game with memory switched on is refused with a 409 that states the reason, and the page
is told memory is unavailable so it can hold the switch off. A game with memory off skips the check
entirely.

That check runs once, when the game is created. During a game the system takes the second choice:
a lesson lookup that fails is skipped silently and the turn is played without lessons. Ending a
running game over one failed lookup would cost more than one turn without them.

The check exists because of an incident. On 2026-10-14 every new game failed with a 500, memory on
or off, because each game rebuilt a stale file store at start. A soft dependency was taking
down the core: the third and worst choice in 1.5, arrived at by accident.

---

# Part 4 — What would change at a larger scale?

One thing the current design would outgrow. The gaps that matter at today's size are in 3.3.

**A breaker that shares what it learns.** With a breaker per game, a hundred games on one provider
each pay for two stalled turns before skipping it. Where games share a key and a model, as house
games do, a shared breaker for that pair would let one game's discovery spare the rest. Games on
players' own keys should keep their own.

---

# Part 5 — Worked problems

Each is answered from memory first; my answers are in Appendix A.

## Problem A: The same concepts in another system

A user asks a question. The service calls a retrieval service to fetch relevant documents, then
calls a model to write the answer. The user gives up after 20 seconds.

- Retrieval normally answers in 0.3 seconds; its slowest 1% take 0.8 seconds.
- The model normally answers in 4 seconds; its slowest 1% take 9 seconds.
- The model can answer without the documents, only less well.

1. Split the 20 seconds between the two calls so the total cannot go over: the timeout for each,
   whether each gets a second try, and what decides that.
2. Retrieval fails. What does the request do next?
3. A breaker is to be put around the retrieval call. What has to be known before choosing how many
   failures open it?

## Problem B: My system, without Part 3 open

1. What happens to a turn when the model doesn't answer, step by step, with the numbers.
2. Why a stalled model is not asked again by my code, when a wrong answer is.
3. How my breaker differs from the textbook one, and why per game.

## Problem C: A claim, checked against the code

A draft sentence for the write-up:

> "Every stalled turn moves to a rescue model."

What in it is supported, what isn't, and what is the accurate wording?

## Problem D: The circuit breaker

What is a circuit breaker for, and when is it the wrong tool? Answer in four or five sentences, with
an example that is not the checkout and not this project.

---

# Part 6 — Summary

**1. Make time a failure.** A hang raises no error, so nothing that waits for errors will act. A
timeout bounds one attempt; only a deadline bounds what the user waits.

**2. Classify before retrying.** Slow or full may pass; wrong every time will not. For a model
there is a third kind, the wrong answer, which is worth asking again.

**3. Retry at one layer.** Retries at several layers multiply. Know what the SDK underneath
already does.

**4. A breaker saves a timeout already known to be wasted.** It only makes sense when the
failures belong to the dependency and there is somewhere else to go.

**5. End on something that keeps the rules true.** A fallback is another source of a real answer or
a fixed safe result; failing fast is neither. A safe default is judged by the rule it protects.
For a soft dependency behind a feature the user asked for, a clear refusal beats a silent change.

### My system in one paragraph

Every turn in my Werewolf game has to end in a legal move, even when a model provider stalls. Each
model call gets 30 seconds and two attempts. If the provider is slow or full, I don't ask the same
model again; the turn goes to a rescue model, and if that fails too the turn takes a safe default: a
pass, or a random legal target. A breaker per game counts stalls: after two in a row, that game's
turns start on the rescue for five minutes. I built it after one turn took 301 seconds because the
provider held the request without ever returning an error. Two limits I'd name: there is no
deadline over the whole turn, so the worst case is a sum of parts, two to four minutes with memory
off and longer with memory on; and the house's default model has no rescue, so its stalled turns go
straight to the safe default.

U2 takes up a question these notes skipped: while one call waits its 30 seconds, what keeps the
rest of the server moving?

---

# Appendix A — Answers to the problems

## Problem A: Retrieval, then a model

One assumption beyond the figures given: the answer is not streamed.

**1. The deadline.** Keep 1 s for my own work, which leaves 19 s. Retrieval gets at most 2 s: a 1 s
timeout, and one jittered retry if the failure is transient. The model gets about 17 s, with a 12 s
timeout, above its slowest 1%. A second model attempt goes only if a slow answer still fits: a 429
at second 1 leaves room, a timeout at second 12 does not, so the request goes to a faster fallback
model or a safe default. The SDKs are set to one attempt so only my code retries, and each call is
given the time left.

**2. Retrieval fails.** Classify it. Transient with time left: retry once. Otherwise answer without
context and say so ("no sources found"): fail-open. If the product promises grounded answers, fail
closed and refuse clearly. With the retrieval breaker open, skip the call and give the model 18 s.

**3. Before setting the threshold.** The traffic per window, since a rate needs enough calls; the
normal error rate and how much it swings; whether failures are outages or bad queries; whether
regions fail separately; the usual recovery time, which sets the cooldown; and what a false trip
costs against a missed one. A starting point: open at 50% failures over at least 20 calls in 10 s,
cool down 30 s, then let one call through.

## Problem B: Werewolf

**1. The steps.** The primary model gets 30 s per attempt and 2 attempts, timed by the SDK. A stall
is not asked again: the rescue model gets one call with its own 2 × 30 s. If that fails, the turn
takes a safe default: a technical pass in discussion, a random legal target for a vote or kill, the
role's no-action option at night. That path is about two minutes; a broken reply before the stall,
the echo check, and the situation summary with memory on can each add a minute or two.

**2. Stall against wrong answer.** A stalled model has already had two attempts inside the SDK and
is slow or full right now; asking again from my code would stack retries and spend more of the
player's wait on the same queue. A wrong answer came back quickly from a working model, and the same
request can produce a valid answer, so one more ask is cheap and often works.

**3. The breaker.** It counts only stalls, routes to the rescue and never fails fast, and moves
turns only when a rescue exists; without one, all it does is skip the echo check. It opens after 2
stalls in a row for 300 s, then tries the primary once. It is per game because each game can run on
its own model and key, and my code cannot tell a provider short of capacity from one key over its
limit, so one game's stall is not safe evidence about another's.

## Problem C: The claim

**Supported:** where a game has a rescue model, a stalled turn goes to it, for one call.

**Not supported:** "every". The house's default model has no rescue in the built-in list, and a
house game cannot carry a backup key, so its stalled turns take the safe default. Where a rescue
exists and stalls too, the turn also takes the safe default.

**Accurate wording:** "A stalled turn goes to the game's rescue model where the game has one,
otherwise to the legal fallback: a pass, a random legal target, or the role's no-action word."

## Problem D: The circuit breaker

It is for an outage the system already knows about. Without it, every request waits out the full
timeout on the dead dependency before going to the fallback; with it, after a threshold of failures,
requests skip the dependency for a cooldown and then one trial call tests whether it is back. It is
the wrong tool when the failures come from the requests and not the dependency, when traffic is too
thin for a few failures to mean an outage, when only part of the dependency is down and the breaker
covers all of it, and when there is no fallback, since then it only delivers the error sooner. My
example of the first: a breaker on a geocoding service that trips because users type addresses that
don't exist.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read),
**test** (named; not run unless stated), **incident** (a dated record). First read against the code
on 2026-10-31 and again on 2026-11-11. The embedding timeout and the helper calls' breaker handling
are in the code as of 2026-11-11 and not yet deployed.*

**How long do I wait**

- Each in-game model accessor asks for 30 s per attempt and 2 attempts in all; the day summary asks
  for 90 s per attempt. Environment variables can change each value. The budget covers the turn
  model, its rescue, the summary and its rescue, the judge and the extractor. **code**
  [accessors.py](../../../Agents/llm_factory/accessors.py)::`_request_budget`; **test**
  `test_every_in_game_model_carries_the_request_budget`, not run
  ([test_model_fallback.py](../../../tests/engine/test_model_fallback.py)).
- Which clients receive it: the OpenAI-protocol clients (DeepSeek among them) and Claude get the
  attempt count minus one, because their SDKs count retries after the first; Gemini's client takes
  it unchanged. The Mistral client gets neither value. **code**
  [chat.py](../../../Agents/llm_factory/chat.py)::`_request_limits`, `_build_chat_model`;
  [mistral.py](../../../Agents/llm_factory/providers/mistral.py)::`MistralChatModel`
- Nothing bounds the turn as a whole. On the stall path a turn can spend 2 × 30 s on the primary and
  2 × 30 s on the rescue, plus SDK backoff: about two minutes. A day summary can spend about six.
  Arithmetic from the code, not a measurement. **code**
  [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`;
  [summary_agent.py](../../../Agents/nodes/day/summary_agent.py)::`run_day_summary_agent`
- Longer paths. A reply that fails to parse is asked again, and that second ask
  can stall before the rescue runs: 3 calls. The echo check runs inside the resolver on a proactive
  discussion turn, after a rescued answer too: a 4th call. With memory on, the situation summary
  runs first. It and the echo check count a stall and skip the primary while the breaker is open;
  the summary then goes to the rescue (**test**
  `test_a_stalled_situation_summary_is_not_asked_again_and_the_rescue_writes_it`,
  `test_the_echo_gate_is_skipped_while_the_primary_keeps_stalling`, run and passing).
  Retrieval is skipped on day 1 and for town seats' day
  discussion. **code** [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`;
  [resolve.py](../../../Agents/turn/resolve.py)::`resolve_decision`;
  [situation_agent.py](../../../Agents/memory/retrieval/situation_agent.py)::`_generate_situations_for_agent`;
  [plan_gating.py](../../../Agents/memory/retrieval/plan_gating.py)
- The query embedder gets `EMBED_TIMEOUT_S` (30 s) and zero library retries; my loop around it
  allows 5 attempts with waits of 2, 4, 8 and 16 s. **test**
  `test_an_openrouter_embedding_request_is_timed_and_retried_at_one_layer_only`, run and passing
  ([test_embedding_model_switch.py](../../../tests/memory/test_embedding_model_switch.py)). **code**
  [embeddings.py](../../../Agents/llm_factory/embeddings.py)::`_create_openrouter_embeddings`,
  `_embed_with_retries`. That the store holds a lock while it embeds is measured in U2
  (section 3.5). That the Gemini client has a single retry layer comes from one read of the
  installed library, not checked a second time.

**Do I ask again**

- A failure is a stall when anything in its exception chain is a timeout, has status 408, 429 or
  5xx, or carries a marker such as "quota" or "timed out". A refused key (401, 403, or a marker such
  as "credit balance is too low") is checked first, as permanent: on the primary it ends the game.
  **code** [embeddings.py](../../../Agents/llm_factory/embeddings.py)::`is_transient_provider_error`,
  `is_key_rejected_error`; [agent_player.py](../../../Agents/turn/agent_player.py)::`_generate`;
  **test** `test_transient_errors_are_the_provider_being_slow_or_full`,
  `test_a_refused_key_on_the_primary_ends_the_game`, not run.
- A reply that failed to parse, or a decision the resolver rejected, is asked again on the same
  model, once (`max_retries=1`), with the schema enforced where the client supports it. A stall
  breaks out of that loop at once. **code**
  [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`

**When do I stop asking**

- `ModelHealth` counts stalls in a row. At 2 it opens: for 300 s every turn starts on the rescue.
  After the cooldown the primary gets a try; the count still stands at the threshold, so one more
  stall reopens it; a good answer clears it. One per game, shared by every seat's thread. It counts
  only stalls, routes to the fallback rather than failing fast, and acts only when a rescue exists
  (`fallback_llm is not None`). **code**
  [health.py](../../../Agents/llm_factory/health.py)::`ModelHealth`;
  [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`; **test**
  `test_repeated_stalls_send_the_next_turns_straight_to_the_rescue`,
  `test_after_the_cooldown_the_primary_is_tried_again`, not run.

**What do I do instead**

- A stalled primary is not asked again that turn; the rescue gets one call, with its own two
  attempts. If the rescue stalls too, the turn takes the safe default. **code**
  [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`; **test**
  `test_a_stalled_primary_is_not_asked_again_and_the_rescue_takes_the_turn`,
  `test_both_models_stalled_falls_to_the_typed_fallback_not_a_crash`, not run.
- Where the rescue comes from: a served game takes its catalogue row's `rescue_model`, on the game's
  own credential, or, with a player's second-company key, that company's backup model. Batch and CLI
  runs default to Sonnet 5.5. **code**
  [accessors.py](../../../Agents/llm_factory/accessors.py)::`_rescue_model`;
  [game_session.py](../../../server/game/game_session.py)::`GameSession.__init__`;
  [model_catalog.py](../../../server/game/model_catalog.py)::`backup_model`;
  [_shared.py](../../../server/routes/_shared.py)::`resolve_backup`
- My planning outline says the rescue comes "from another provider"; in the seed catalogue every
  rescue is from the model's own provider, because it shares the credential. **code**
  [catalog.py](../../../Agents/llm_factory/catalog.py)::`SEED_MODELS`
- The house default has no rescue: the only house-funded row in the seed, Claude Haiku 5.5, has an
  empty rescue ("No rescue (owner 2026-10-12)"), and a house game has no player key to attach a
  backup to. **code** [catalog.py](../../../Agents/llm_factory/catalog.py)::`SEED_MODELS`;
  [house.py](../../../server/house.py)::`HousePolicy._default_model`;
  [_shared.py](../../../server/routes/_shared.py)::`resolve_backup`
- The safe default: a day or wolf discussion turn becomes a technical pass; a vote or a wolf kill
  takes a random legal target; a night action takes the role's no-action word, or a random legal
  target when the role has none. An unwritten day summary becomes the raw transcript. **code**
  [agent_player.py](../../../Agents/turn/agent_player.py)::`run_agent`;
  [summary_agent.py](../../../Agents/nodes/day/summary_agent.py)::`run_day_summary_agent`; **test**
  `test_exhausted_day_discussion_records_technical_pass`,
  `test_a_summary_with_no_working_rescue_is_the_raw_channel`, not run.

**The embedder's two hosts**

- The embedder is `qwen/qwen3-embedding-8b` through OpenRouter, with the host order Nebius then
  DeepInfra and `allow_fallbacks` off. **code**
  [embeddings.py](../../../Agents/llm_factory/embeddings.py)::`OPENROUTER_EMBEDDING_PROVIDERS`,
  `_create_openrouter_embeddings`; **test**
  `test_a_model_id_with_a_slash_is_served_through_openrouter_on_pinned_hosts`, run and passing.
- The two hosts' vectors differ slightly: cosine min 0.99723, mean 0.99758, max 0.99790 over 10
  sentences. Host routing is honoured on the embeddings endpoint (a list holding only a host that
  cannot serve the model was refused with a 404), and with fallbacks off the list is walked in
  order (such a host placed first was skipped and DeepInfra served). **test**, a one-off live
  probe on 2026-11-11, 8 requests; its script and results were not kept in the repository. The
  earlier "about 0.998" in the migration log
  ([experiment_log.md](../../memory_system/v8/experiment_log.md), 2026-10-12) agrees with it.
- Whether a request moves to the second host when the first is serving the model but fails this
  request (a 429, a 5xx or a timeout): **none**. During the probe Nebius returned a 429 on a
  request whose list had no second host able to take it, so the case was not exercised.

**The soft dependency**

- The lesson store is unready when nothing has been published, when its index was built by another
  embedder (the message names both), or when it holds no strategy points. A memory-on game is then
  refused with a 409 giving the reason, and `GET /models` reports memory as unavailable so the page
  can hold its switch off. A memory-off game skips the check. **code**
  [postgres.py](../../../Agents/memory/persistence/postgres.py)::`unready_reason`;
  [_shared.py](../../../server/routes/_shared.py)::`require_memory_available`; **test**
  `test_an_unpublished_or_empty_store_is_not_ready`, not run
  ([test_postgres_publish.py](../../../tests/memory/test_postgres_publish.py)).

**Incidents on record**

- 2026-09-30, the 301-second turn: 282 s of it sat inside the retrieval call. Vertex held requests
  for minutes, then bounced them with 429; the SDK and LangChain retried each bounce silently, and
  the rescue, keyed on errors, never fired. **incident**
  [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1
- 2026-10-14: every new game failed with a 500: the session rebuilt a stale file store for every
  game, memory on or off. The fix moved lessons to Postgres and added the readiness check.
  **incident** [deploy_log.md](../../../frontend/docs/deploy_log.md)
- 2026-10-21, game `e45eda20`: the budget had reached only Gemini's clients for three weeks; a
  DeepSeek client waited its SDK's 600 s a try, three tries, before the rescue was asked.
  **incident** [deploy_log.md](../../../frontend/docs/deploy_log.md)

**Not established**

- The stall rate since the fix: no record counts rescued or defaulted turns.
- Any whole-game watchdog: none exists, and a hang outside a model call goes undetected
  ([server_design_notes.md](../../../frontend/docs/server_design_notes.md) §5c, mode 4).
- Whether the budget reaches every provider's client: Mistral's takes none, and no check was made of
  whether any current configuration reaches it.
- Whether the live catalogue table matches the seed; the table was not read.
- The original basis for 30 s: the "worst honest turn of 11 s" behind it has no recorded sample
  size. The figure measured since is the 13 served games of `frontend/docs/stage_fit/` (Haiku 5.5,
  slowest 5% of discussion calls 10.8 s), as noted on 2026-10-26 in
  [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1; that folder
  was not re-read for these notes.

**Framework specifics, pointed to**

- The stacked google-genai and LangChain retry layers:
  [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1.
- The OpenAI and Anthropic SDK defaults: the docstring of
  [chat.py](../../../Agents/llm_factory/chat.py)::`_request_limits`.

**Reading**

- [AWS Builders' Library, "Timeouts, retries, and backoff with jitter"](https://d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf),
  the timeouts and the retries-and-backoff sections: picking a timeout from the dependency's
  latency, why retries are selfish, and why retrying at several layers multiplies load.
- [agentic_ai_encountered_issues.md](../../../docs/agentic_ai_encountered_issues.md) §1: the hang that
  never raised an error, and the fixes in order.
- [health.py](../../../Agents/llm_factory/health.py), the whole file (51 lines): map each breaker state
  onto its methods.
- *Optional:* Martin Fowler, ["CircuitBreaker"](https://martinfowler.com/bliki/CircuitBreaker.html),
  the three states in one short account.
