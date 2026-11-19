# U4 seed notes: delivery semantics and idempotency

Not a chapter. Points that came up early, in the U0 revision on 2026-11-11, kept here so U4 covers
them when it is written. U4's guiding question: *the same message or job arrives twice; how do you make
sure its effect happens once?*

## Points to cover

**The gap no transaction closes.** "Do the work" and "record that it was done" usually happen in two
different places (the email provider and our database). A crash between them leaves us not knowing
whether the work happened. Logging does not close the gap: the crashed process cannot log, and a log
is read by a person, not used to repair state.

**Choose which way to fail.** Never retry → the work may never happen (*at-most-once*). Retry → it may
happen twice (*at-least-once*). Most systems retry and make a repeat harmless:
**at-least-once delivery + safe-to-repeat work ≈ exactly-once results.**

The four parts of making a repeat harmless:

1. **Acknowledge last.** Tell the queue "done" only after the result is recorded; a crash before that
   means the job is delivered again.
2. **Idempotency key.** A unique id per action (`ticket-email-order-88`); the provider ignores a second
   request with the same key. Check the provider's API docs: payment providers almost always support
   it, email providers vary. Fallbacks when it doesn't: check our own record before calling; look the
   message up at the provider afterwards; or accept a rare duplicate when it is cheap (an email), never
   when it isn't (a charge).
3. **Record the intent first.** `pending → sending → sent`. A job stuck in `sending` is the uncertain
   case, now visible in the data.
4. **Ask the witness.** Resolve the uncertain case with the authority for that fact (the provider),
   the same reconciliation as in U0 1.2.

**The dual-write problem.** Two stores, no shared transaction. You can only make writes atomic within
one store. The fixes: put the facts that must change together in the same store, or accept a gap and
add a relay that retries.

**The outbox pattern** (know by name and the one problem it solves). Writing the order and then
publishing the "send email" message is a dual write; a crash between them loses the message. The
outbox writes the message into a database table *in the same transaction* as the order; a separate
relay later publishes it to the queue and marks it sent. It does not put the queue inside the
transaction. The relay can publish twice (crash before marking), so the consumer must still be safe to
repeat.

**A cache is not a record unless it survives the failure you care about.** Persistence alone does not
make a store authoritative either; authority is the role the design gives it.

## Worked example: dota2pred (our own queued pipeline)

Werewolf has no queue (the engine runs in the server process), so this is U4's main worked example.
Each stage of `live_orchestrator_app` commits to Postgres first, then runs one Redis MULTI/EXEC.
For feature engineering and prediction that's status `hset` + `xadd` to the next stream + `xack` the
input, via `_run_transaction_with_retry` in `redis_services/redis_service.py`. Completion and odds run
their own MULTI/EXEC without the retry, and delete, ack and `XDEL` instead of publishing. Redis-only
steps are atomic, the same insight the outbox reaches from the other side: keep the status next to the
queue. (Corrected 2026-11-11 after a code check; full detail with line refs in
`dota2pred/docs/2026-11-11-reliability-and-scale-review.md`.) Postgres + Redis is a dual write at
every stage. Checked 2026-11-11 by reading the code.

| Stage | Crash between the two writes | Safe to repeat? |
|---|---|---|
| Feature engineering | Input not acked → redelivered → re-run | Yes: features upserted (`ON CONFLICT DO UPDATE`) |
| Completion | Outcome may be saved without the history; redelivered | Yes (outcome `DO NOTHING`; history recomputed: inferred, not verified) |
| Prediction | Redelivered → model called again | Yes, but overwrites the earlier prediction and its `prediction_date` |
| Odds | Redelivered → snapshot re-captured | Yes, but stores later market prices |
| **New match** | **The match is lost** | **No (see below)** |

### Known bugs: I am fixing these by hand; no session fixes them

Found 2026-11-11, left in place on purpose. Paths are under
`dota2pred/live_orchestrator_app/src/live_orchestrator_app/`.

1. **New match: marked "seen" before it is handed on.** `_filter_new_matches`
   (`data_fetching/new_match_data_provider.py:72`) updates the Redis "seen" set first; then Postgres
   (`insert_match_details`); then the publish to `new_matches`. This stage starts from polling, so
   there is no input message to redeliver. A crash after the set update means the next poll treats the
   match as already seen, and it never gets a prediction. A failed transform or Postgres insert
   loses it the same way, not only a crash. It is the same mistake as acknowledging
   before the work is done. Possible fixes: mark the match seen in the same Redis transaction as the
   publish, or un-mark it when the publish fails.
2. **New match: a failed publish counts as a success.** `publish_new_match_to_feature_eng` catches its
   own exception and returns `False`; `data_fetching/new_match_orchestrator.py:63-64` ignores the return
   value and increments `count_success`. A Redis failure loses the match, and the log says it worked.
   (Verified by reading.)
3. **Prediction: a failed DB write may still publish (inferred, not verified).**
   `PredictionRepository.store_match_prediction`
   (`packages/dota_oracle_common/.../repositories/prediction_repository.py:25-38`) logs the exception
   without re-raising it, so the Redis publish may follow a failed Postgres write.

Also note: `stale_match_service` moves old pending messages to the dead-letter queue with
XPENDING/XCLAIM but does not check Postgres first. There is no outbox and no reconciliation job.

**Interview angle, once fixed:** "I checked my own pipeline for dual writes: four stages were safe
because of redelivery plus upserts; one lost matches; I fixed it." Write that up as a dated doc in
`dota2pred/docs/` after the fix, not before.

### At-least-once needs a way to stop (poison messages)

dota2pred's own incident shows this (`dota2pred/docs/2026-06-07-pending-completion-backlog.md`,
`2026-06-07-dlq-churn-and-opendota-cost.md`). `pending_completion` grew to 69,227 entries while only
~8 matches were live. Some messages had been redelivered up to 61 times. The dead-letter retry sweep
was re-injecting messages that could never succeed (a match whose data will never arrive), and that
burned OpenDota calls into 429s. U4 should cover: retry limits, a dead-letter queue as an end point
rather than a loop, and "terminal discard" for messages that can never succeed.

### A concurrency limit is a lock, and a dead holder blocks it

The live orchestrator runs with `concurrency_limit=1` (`live_orchestrator_app/.../deploy_service.py:67`),
so an over-long cycle waits instead of running beside the next one. But a deploy that kills the worker
mid-cycle leaves the run marked RUNNING, holding the only slot, and nothing runs after it.
`_crash_orphaned_runs` frees the slot on startup. U4/U5 should cover: a claim needs an expiry (a lease)
or a cleanup step, or a dead holder stops everything. This links to U0 Part 4: "what stops two workers
from running the same game at once?"

## Werewolf's version (for U4's project part)

- The AI turn nodes are cached by their input, with the game id in the key
  (`Agents/graphs/day.py:96-99`, `CachePolicy`). That is an idempotency key: when a human's answer
  makes LangGraph re-run the step, the AI siblings replay their recorded answers instead of making
  new paid calls.
- It is an `InMemoryCache` (`day.py:140`), so a process crash wipes it. After a restart the game
  resumes from the Postgres checkpoint and that step's model calls run again: paid twice, possibly a
  different line. Acceptable for a game; U3/U4 should state it plainly.

## Possible lesson for `../lessons/`

"At-least-once + safe to repeat" now shows up in both projects. That's a candidate cross-project
lesson once U4 exists. Don't write it before then.
