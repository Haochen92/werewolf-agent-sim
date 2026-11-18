# U13. Testing: what to check, how to check it, and what a pass proves

<!-- Writing rules: docs/writing/core_rules.md. -->

**Reading time:** about 45 minutes for Parts 1 and 2 (estimate). The two-minute summary is in Part 3.

**Why this note.** A coding agent writes most of my test code. My part is to decide what has to be tested, to direct the agent, and to judge whether its tests are meaningful evidence. That needs an order of work that is short enough to remember.

Builds on U0 · Related: U3 (recovery), U5 (pause and resume), U10 (API-key leakage), U11 (prompt injection), U14 (release safety) · Feeds write-up chapters 7 and 8.

**The question:** When building or reviewing an application, how do I decide what deserves testing, which checks to use, and whether passing those checks means the application works?

## The central idea

A passing test establishes less than it might seem.

Suppose a test sends a €150 refund request for an order worth €100 and checks that the request is rejected. A pass shows that the refund was rejected under the conditions that test created. It does not show whether two refund requests arriving at the same time could get past the limit, whether the real payment provider behaves as expected, or whether an AI model will request sensible amounts. Each of those is a different claim that needs its own evidence.

**A test checks a particular claim about the system under particular conditions.** A testing strategy is the process of deciding which claims matter and what evidence would justify believing them.

There are five decisions to make.


| Step                       | Question                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| 1. Identify the claims     | What must work, what must never happen, and which failures matter most?                           |
| 2. Design the checks       | What must the test exercise, which dependencies can be replaced, and what will remain unverified? |
| 3. Find failure cases      | Which unusual inputs, failures and sequences of events could violate the claims?                  |
| 4. Make testing repeatable | How will people and coding agents run the checks reliably and automatically?                      |
| 5. Review the evidence     | Can the tests detect real faults, and what exactly do their results establish?                    |

The steps serve three uses. For a new system, the five decisions are made once when the testing strategy is set up, and revisited when a feature brings a new risk. For a design that exists only on paper, steps 1 to 3 are the reasoning. For tests that an agent wrote, steps 1, 2 and 5 are the ones to apply.

# Part 1 — Designing a testing strategy

The running example is a customer-support assistant. A language model reads customer emails and can request actions such as checking an order or issuing a refund. Ordinary application code decides whether a requested refund is allowed and communicates with the payment provider. Customers and staff use a website to view orders and refunds.

## 1. Identify what needs testing

### 1.1 Why start with claims instead of tests?

An application contains far more behaviour than anyone can test completely. Writing tests function by function can test simple calculations thoroughly and still overlook an important rule that several components can break. So the work begins by asking what the system must do correctly.

A **claim** is a statement about behaviour that should hold under specified conditions. Examples include:

* A refund request above the remaining refundable amount is rejected.
* Customers can view the status of their refunds.
* The refund service reads the correct order total from the order service.
* A previously fixed double-refund bug does not recur.

These statements describe what deserves verification. They do not yet specify how to verify it.

### 1.2 Four places to discover important claims


| Look for                          | Question to ask                                                    | Example                                                              |
| --------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------- |
| **Rules that must remain true**   | What must never happen, or must remain true as the system changes? | An order cannot be refunded for more than was paid                   |
| **Essential user workflows**      | What must users be able to complete?                               | A customer can request a refund and see its status                   |
| **Boundaries between components** | Where does one component rely on another's behaviour or data?       | The refund service receives the correct total from the order service |
| **Previous failures**             | What has already gone wrong and must not recur?                    | Retrying a request previously produced a second refund               |

These are sources of testing requirements, **not four separate categories of tests**.

A claim discovered through any of them may be tested at the unit, integration or end-to-end level, depending on what it involves.

Only the first row needs explaining before a claim can be written, and section 1.2.1 does that. For the other three rows the claim is easy to state and the difficulty is in the check, so they are taken up in step 2: user workflows under end-to-end tests (2.2) and the frontend levels (2.6), boundaries under contract tests (2.5), and previous failures under regression tests (2.5).

#### 1.2.1 The first row: what is an invariant, and when do I test one?

Consider an order for which the customer paid €100.

The customer may request a refund through the website. An employee may issue one through an administration tool. A background worker may retry a failed refund.

These operations use different parts of the application, but all can affect the amount refunded.

**The total successfully refunded must never exceed the €100 originally paid.**

This is a *system-state invariant*: a condition that must remain true as valid operations change the system's stored state.

It is different from asking whether an individual feature works. The website could correctly submit a refund request while the system still allows two concurrent requests to refund the same money.

An invariant is useful when a rule needs to survive multiple operations, different entry points, or sequences of state changes.

**How it affects testing.** First identify which operations could violate the rule. Then look at whether existing tests cover those risks.

For the refund invariant:


| Possible violation                                          | Useful check                                                                                   |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| A single request exceeds the remaining refundable amount    | Unit test of the refund validation logic                                                       |
| Two concurrent requests both read the same available amount | Integration test using concurrent requests and the real database                               |
| A completed request is processed again after a retry        | Test that repeats the operation and checks the cumulative refund                               |
| Several operations interact in an unexpected order | A test that performs a sequence of actions and checks the rule after each one (sometimes called a stateful test) |

These are ordinary testing techniques. There is no separate framework required simply because the claim is an invariant.

Some invariants deserve dedicated tests, particularly when many operations can violate them. Others can be checked inside existing feature tests.

**Not every test needs an invariant.** A test that formats a date or verifies that a button displays the correct text can simply check its expected output.

The practical value of identifying invariants is that they reveal important risks that might be missed when tests are written only feature by feature.

Invariants also exist in algorithms and other contexts. Here the term refers specifically to rules that should remain true of the application's state.

### 1.3 Prioritise the claims

Identifying claims does not mean writing a test for every one immediately.

Ask what would happen if each claim were false. Consider the consequences, how likely the failure is, and whether another check already covers the risk.

For the refund system, a possible ranking is:

| Rank | Claim | If the claim were false |
|---|---|---|
| 1 | An order cannot be refunded twice | Money is lost every time |
| 2 | Total refunds never exceed the amount paid | Money is lost |
| 3 | The refund service reads the correct order total | The check behind claim 2 uses a wrong number, so claim 2 fails without anyone seeing it |
| 4 | The correct currency is used | The customer is paid too much or too little |
| 5 | Customers can see their refund status | The customer has to write again, which costs staff time |
| 6 | The "approved" label is green | Almost nothing |

Testing effort goes to the top of the list first. Claim 6 may have no test at all, and that is acceptable when it was decided and not overlooked.

The precise ranking depends on the application. The important part is making the choice deliberately.

A short list of high-risk claims is more useful than a large inventory treated as equally important.

**How this works during development:** write the main claims when establishing the project. When a new feature is introduced, ask whether it creates a new important claim or can violate an existing one. Add or revise tests accordingly.

The whole testing strategy does not need to be worked out again for every change.

## 2. Design a check that can establish the claim

Once a claim is identified, the next decision is:

**Which parts of the system must actually run for a test to show whether the claim holds?**

This decision covers both the *test level* and which dependencies are real or replaced.

They should be considered together because replacing a dependency changes what the test can establish.

### 2.1 Start with the failure the check must detect

Take four different claims about refunds.


| Claim                                                 | What needs to run                                                 | What this check cannot establish                                          |
| ----------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------- |
| The refund validation rejects €150 for a €100 order | The validation code with fixed inputs                             | Whether concurrent operations bypass the limit                            |
| Two concurrent refunds cannot exceed the order total  | Refund service and a real test database, with concurrent requests | Whether the external payment provider processes requests correctly        |
| A customer can request a refund through the website   | Browser, application and relevant backend services                | Every possible failure of the external provider                           |
| The AI assistant rarely proposes excessive refunds    | The real model, tested on representative customer requests        | Behaviour on every future input, or whether the backend enforces the limit |

A test that replaces the database cannot demonstrate that the database transaction prevents concurrent double refunds. A test that replaces the model cannot show how often the real model requests an invalid refund.

This is why choosing the test boundary matters more than simply attaching a label such as "unit test" or "integration test."

### 2.2 The main test levels

Test levels describe how much of the system is exercised together.


| Level           | What runs                                                                            | Best suited to                                                                     |
| --------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| **Unit**        | A small piece of application logic, usually with dependencies controlled or replaced | Rules, calculations, validation and local edge cases                               |
| **Integration** | Multiple components working together, with the relevant real dependencies            | Database operations, API boundaries, persistence and interactions between services |
| **End-to-end**  | A complete user workflow through the system                                          | Whether the system's parts work together to accomplish a user's task               |

For example, a unit test might check the refund amount calculation. An integration test might verify that two concurrent transactions cannot both refund the same balance. An end-to-end test might complete a refund through the website.

The usual testing pyramid recommends many fast unit tests, fewer integration tests, and a smaller number of slower end-to-end tests.

This is a practical guideline, not a fixed ratio. The appropriate balance depends on the application and the risks being protected.

**Choose the smallest meaningful test boundary for a claim, then add broader checks for failures that the smaller boundary cannot detect.**

A unit test is attractive because it is cheap and isolates faults, but it is inadequate if the behaviour depends on a database transaction that is not being exercised.

### 2.3 What happens when a dependency is replaced?

A dependency may be slow, costly, unavailable during tests, or produce variable results. Common examples include payment providers, databases, clocks and language models.

A test can replace that dependency with a controlled implementation. The general term is a **test double**. Developers also often use "mock" informally to refer to test doubles.

The main forms are:


| Kind     | What it provides                                | Example                                             |
| -------- | ----------------------------------------------- | --------------------------------------------------- |
| **Stub** | A predetermined response                        | A model that always returns a valid refund request  |
| **Mock** | A replacement whose interactions can be checked | A payment client that records whether it was called |
| **Fake** | A simplified working implementation             | An order store implemented with a Python dictionary |

The three names matter less than the trade-off they share.

**Replacing a dependency gives control over it, but removes that dependency's real behaviour from the test.**

A scripted model can return perfectly valid JSON on every call. This makes it possible to verify that the rest of the application processes the response correctly. It shows nothing about how often the real model returns malformed JSON.

A dictionary-based order store might implement basic reads and writes correctly, but it does not reproduce the database's transaction isolation, uniqueness constraints or concurrency behaviour.

The replacement can even make a faulty test pass.

Suppose application code removes API keys from provider error messages before storing them. A test supplies a made-up API key and searches the stored error for it (U10 calls this a planted-key test).

If the test double produces a harmless error that never contains the key, the test passes even when the redaction code is broken.

To exercise the protection, the replacement must produce an error containing the planted key.

This is a recurring question when reviewing agent-written tests:

**Did the test create the conditions in which the claimed failure could actually happen?**

### 2.4 Real dependencies do not necessarily mean production dependencies

Not every test needs a replacement.

For example, an integration test can start the same Postgres software used by the application in a temporary container. That exercises real SQL and database constraints without using production data.

A payment provider might offer a sandbox environment that exercises its API without moving actual money.

Such tests can provide stronger evidence about the relevant dependency, but still do not reproduce every condition of production, such as live configuration, traffic volume or provider-specific production behaviour.

The options form one trade-off. The more of a check that is real, the more a pass shows, the more each run costs, and so the less often it can run (step 4):

| Choice | What a pass can show | Cost of a run | How often it can run |
|---|---|---|---|
| Test doubles around the code | The code's own logic | Milliseconds, free | On every change |
| A real dependency in a test environment | The code working with that dependency. Production's configuration, data size and load are still not reproduced | Seconds | On every change, or on every push |
| The full application with real services or the real model | The user's task, or the model's behaviour | Minutes, and often money | Before a release, on a schedule, or when a change is meant to alter behaviour |

This does not mean that the most realistic check is always best.

For each important claim, choose a check that is strong enough to detect the failures that matter. Use additional checks where replacing a dependency leaves an important gap.

### 2.5 Special checks for particular problems

Some testing techniques are best understood by the specific risk they address.

**Contract tests: when two components disagree**

Imagine the backend changes an API response from `order_total` to `total_amount`.

The backend's tests may pass. The frontend's tests may also pass if they use saved responses with the old field name.

The application can still break when the components are connected.

A contract test checks that both sides agree on the interface they use.

One approach uses the server's API description, a file the server can produce that lists every request it accepts and every field it returns (OpenAPI is the usual format). The description is saved, and the client's types are generated from the saved copy. A test then fails when the server's current description no longer matches the saved one, which means the client was built from a description that is out of date. The test must compare against the description the server produces now; comparing two saved copies with each other shows nothing.

This checks the shape of requests and responses. It does not check the rules or permissions behind the API.

**Golden or snapshot tests: when an output changes unnoticed**

A long model prompt can contain hundreds of lines. Someone may make a legitimate change in one part and accidentally alter another.

A golden test stores an approved version of the complete output and compares future output with it.

Any difference causes a failure.

That is useful for prompts, serialized events, generated API descriptions and screenshots.

But a golden only establishes that the output has or has not changed relative to the saved version. It does not establish that the saved output was correct.

It also stops protecting against accidental changes if the golden is regenerated without reviewing the difference.

**Regression tests: when a previous defect might return**

Suppose a refund was once issued twice because a worker retried a completed operation.

After fixing the defect, keep a test that reproduces the original scenario.

Ideally, demonstrate that it fails against the faulty behaviour and passes with the fix.

That test now protects against the same regression.

**Evaluations: when the behaviour belongs to the language model**

Suppose the refund assistant's prompt is changed to say:

"Never request a refund larger than the amount paid."

A test is **deterministic** when the same code and inputs give the same result on every run. A model's answer is not. A deterministic test can check whether that sentence appears in the generated prompt.

It cannot establish that the real model follows the instruction.

To investigate that, run a set of customer requests through the real model and measure how often it produces excessive refund requests.

For example, "7 of 50 requests exceeded the limit" is evidence from that sample, not a universal pass-or-fail guarantee.

A before-and-after comparison should use comparable inputs and scoring methods. Model variability, sample size and uncertainty matter when interpreting the result.

Where a rule must hold every time, enforce it in ordinary application code rather than depending solely on model behaviour.

### 2.6 Backend, frontend and LLM testing

The underlying reasoning is the same in all three areas. The claims and useful test boundaries differ.


| Area            | Typical questions                                                      | Useful checks                                                                     |
| --------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Backend         | Are rules enforced? Is data stored correctly? Are permissions checked? | Unit, integration and contract tests, including real database checks where needed |
| Frontend        | Can users complete tasks? Do screens reflect the current state?        | Logic/component tests, browser tests and screenshot comparisons                   |
| LLM application | Is the prompt correct? Is the model's output valid and useful?         | Deterministic tests of application code, plus evaluations with real model calls   |

Frontend testing has its own levels:

| Level | What runs | What it is for |
|---|---|---|
| Unit | The logic with no browser: the functions that turn server data into what the page shows | Fast checks of every state the data can be in |
| Component | One piece of the page rendered alone, with its data supplied by the test | That a piece shows the right text and reacts to a click |
| Browser | The real pages in a real browser, driven by a script that clicks and types | That a whole task works. Few of these, because each is slow |
| Screenshot comparison | A golden test on a picture of the page | An unintended change in appearance. A person has to look at each difference |

A browser test is not necessarily an end-to-end test of the entire application. If Playwright drives the real page but every server response is replaced with saved data, it exercises the frontend, not the actual backend.

Similarly, a whole-game test that uses the real LangGraph graph with a scripted model can verify orchestration without verifying the real model's decisions.

**The practical question is always: what was real in this check, and what was not?**

## 3. Find the failure cases

A test that checks only the normal path can pass while important failures remain.

Consider the refund service. A valid €20 refund against a €100 order is a useful normal case, but it says little about the conditions most likely to cause serious errors.

Two approaches help discover additional cases.

### 3.1 Vary the inputs

For each important input, consider empty values, one item, many items, values at the limit, invalid values and duplicates.

For a refund amount, that might mean €0, exactly €100, €100.01, a negative amount, text instead of a number, and a request that repeats an earlier refund.

These cases often exercise different branches of validation logic.

Not every variation needs a dedicated test. Focus on the cases that could change whether an important claim holds.

### 3.2 Examine what can happen between operations

Many difficult failures arise not from unusual inputs but from the sequence in which operations occur.

Suppose the service performs two actions: sends a refund to the payment provider, then records that refund in the database.

Four questions are particularly useful:

1. **What if execution stops here?** The provider may have processed the refund before the application records it.
2. **What if this operation runs again?** A retry may send the refund twice.
3. **What if two operations happen concurrently?** Both may read the same available balance.
4. **Was the result confirmed, or merely requested?** Sending a refund request does not necessarily mean the payment provider accepted it.

Each question suggests specific failure scenarios and tests.

These questions are especially relevant to asynchronous workers, distributed systems and agent workflows that resume after interruptions.

### 3.3 Area-specific failure cases

A frontend adds situations such as loading, empty and error states, smaller screens, repeated clicks, lost connections and returning to an interrupted task.

An LLM application adds malformed structured output, refusal, timeouts, unexpected tool calls, hostile instructions embedded in retrieved content, and variation between repeated calls.

A backend adds permission failures, concurrent writes, retries, partial failures and database constraints.

Rather than treating this as an exhaustive checklist, ask which situations could violate the prioritised claims from Step 1.

## 4. Make testing repeatable, automatic and usable by coding agents

Good tests provide little protection if nobody runs them or if their results cannot be trusted.

This part matters particularly when coding agents write and execute much of the test suite.

### 4.1 Give the project predictable test commands

A developer or coding agent should not need to discover the correct command for each change.

Establish a default set that runs without paid services or private credentials. Keep slower integration, browser and live-model checks separately selectable.

For example, a project might distinguish:


| Set              | What belongs in it                                 | When to run                                          |
| ---------------- | -------------------------------------------------- | ---------------------------------------------------- |
| Fast checks      | Unit tests, relevant static checks                 | During development and on pull requests              |
| Broader checks   | Real-database integration tests, browser workflows | Before merging, or on relevant changes               |
| Live evaluations | Calls to real models and external services         | On relevant behavioural changes or a planned schedule |

The exact commands depend on the project.

The important part is knowing which checks ran and which were excluded.

A test skipped because a database isn't configured is not equivalent to a test that passed against that database.

### 4.2 Use shared fixtures and test-data factories

Many tests require the same kinds of objects and environments.

A *fixture* supplies reusable test setup, such as a database connection, an API test client or a logged-in user.

A *factory* builds test data, such as an order with particular values or a legal game state.

Centralising these reduces duplicated setup and makes it easier to create realistic failure cases.

Tests should also have names that describe the claim being checked.

For example, `test_refund_above_remaining_amount_is_rejected` communicates its purpose more clearly than `test_refund_4`.

Folder organisation should make tests discoverable. Backend tests can follow the components they protect, while frontend tests may sit near the components or features they exercise. Integration and browser tests often benefit from separate locations because they require different environments.

The important requirement is consistency, not a universal directory structure.

### 4.3 Keep tests from depending on uncontrolled variation

A *flaky test* passes on some runs and fails on others without a relevant code change.

Common causes include:


| Cause                      | Example                                                                   |
| -------------------------- | ------------------------------------------------------------------------- |
| Shared random state        | Two threads consume numbers from one seeded generator in different orders |
| Timing assumptions         | A test waits a fixed half-second for work that sometimes takes longer     |
| Shared state between tests | One test leaves data that changes another test's result                   |
| External services          | A real service varies in response time or availability                    |

Flakiness damages confidence because people learn to rerun failing tests until they pass.

The repair depends on the cause.

Sometimes the environment should be controlled, such as by isolating test data or avoiding shared random generators. Sometimes the assertion should describe a property that remains true regardless of valid execution order.

For example, checking that a refund changes the stored balance by the correct amount can be more robust than requiring a particular log message to appear third.

**A test should fail when the protected behaviour is wrong, not because harmless variation changed the scenario.**

### 4.4 Continuous integration

Continuous integration (CI) runs selected checks automatically against a known code revision, usually when a change is pushed or proposed for merging.

It helps with three problems:

* Tests no longer depend entirely on someone remembering to run them.
* The checks execute in a reproducible environment rather than relying on files and packages left on one developer's machine.
* Results are associated with a particular revision.

CI does not make weak assertions strong. It only runs the checks that exist.

For a release guarantee, the release procedure must also ensure that the tested revision is the revision being deployed.

A successful CI run on one commit does not prove that a different deployed commit was tested.

**Detail: coverage.** **Test coverage** is the share of the code's lines that the tests executed. A high number shows little, because a line can run without any assertion checking its result. It is more useful the other way round: a line that no test runs is certainly not tested.

### 4.5 Setting up a project for agent-written tests

A coding agent can create hundreds of tests, but that does not mean those tests protect the system's most important behaviour.

Before delegating substantial work, establish three things in the project's instructions or testing guide.

**First: what correctness means.** Give the agent the relevant system claims, the behaviour expected from the change, and important failure cases. It can propose additional cases, but should not choose coverage solely by what is easy to test.

**Second: how testing works in the repository.** Document the test commands, folder organisation, reusable fixtures, test environments, test categories and rules for updating goldens.

**Third: what evidence is required before work is complete.** Require the agent to report the tests it ran, failures, skips, real or replaced dependencies, and the reason for changed goldens. For a defect fix, ask for evidence that the regression test detects the defect, when practical.

For a substantial change, the workflow is:

1. Agree on the expected behaviour and relevant failure cases.
2. Have the agent propose or write the checks.
3. Confirm that the checks can detect the intended fault, when feasible.
4. Implement or repair the behaviour.
5. Run affected tests and the agreed broader regression suite.
6. Review what passed and what remains unverified.

The agent can perform much of this work. The person reviewing remains responsible for deciding whether the evidence supports the important claims.

This is especially important when the same agent writes both the implementation and its tests: the agent may encode the same mistaken assumption in both.

The broader practices of managing coding agents belong in a separate note. U13 needs only the testing responsibilities and the reasoning behind them.

## 5. Review whether the evidence is meaningful

A large number of passing tests is not automatically strong evidence.

Three questions are particularly useful when reviewing a test written by someone else.


| Question                                 | What to inspect                                                                         |
| ---------------------------------------- | --------------------------------------------------------------------------------------- |
| **Can this test detect the fault?**      | Does the test fail when the relevant behaviour is deliberately broken?                   |
| **Does it check the intended behaviour?** | Is the assertion about the observable result, or merely about an implementation detail? |
| **What remains unverified?**             | Which inputs, dependencies, environments and behaviours were not exercised?              |

### 5.1 Can the test actually fail?

Suppose a test asserts that a function returned a non-null object. That assertion may pass even when the object contains an incorrect refund amount.

One useful verification technique is to introduce a deliberate fault and see whether the test detects it.

For a refund limit, temporarily remove the limit in a controlled test environment. If the test still passes, it was not protecting the rule.

This is the principle behind mutation testing: changing the implementation in ways that should violate behaviour to assess whether the tests detect those changes.

It need not be applied to every single test manually. It is particularly valuable for critical rules, regressions and tests whose assertions are difficult to judge.

### 5.2 Test behaviour, not only implementation details

Consider two assertions:

* "The function `check_refund_limit` was called once."
* "The excessive refund was rejected and no payment was issued."

The first checks an implementation detail. It may pass even if the function's result is ignored. It may also fail after a harmless refactor that preserves the behaviour.

The second checks the outcome that matters.

Interaction assertions are still useful when the interaction itself is part of the requirement, such as ensuring a payment provider is called at most once. But they should not substitute for checking the final state when the final state is what matters.

### 5.3 Be precise about what passed

A passing test establishes that an asserted property held for the tested code, inputs, environment and dependency behaviour.

It does not establish correctness on inputs that were not tried, against dependencies that were replaced, or for claims the test never asserted.

For model evaluations, the same discipline applies differently. Report the observed counts, sample sizes, relevant conditions and limitations rather than treating a favourable result as a universal guarantee.

Keep two terms separate:

* **Validated:** A particular behaviour was checked using specified tests or measurements.
* **Deployed:** A version is running where users can reach it.

A change can be deployed without adequate validation. It can also be validated locally without ever being deployed.

## One change taken through the five decisions

Suppose the support-assistant team wants to stop excessive refunds.


| Decision             | What the team does                                                                                                                                   |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Claims**        | Separate two claims: no excessive refund may be paid, and the model should rarely request one                                                        |
| **2. Checks**        | Test the refund service's enforcement in code, including a real-database check for concurrent refunds. Evaluate the model on saved customer requests |
| **3. Failure cases** | Exactly at the limit, one cent above it, partial refunds, repeated requests, concurrent requests and provider failures                               |
| **4. Running**       | Put deterministic checks in the routine suite; run the model evaluation when the prompt or model changes                                             |
| **5. Review**        | Show that removing enforcement makes the relevant test fail. Report the model evaluation's observed counts and limitations                           |

The table holds two separate claims. The application should not pay an excessive refund, even when the model asks for one. That guarantee belongs in the refund service.

The model evaluation answers a separate question: how often the model produces an excessive request.

A test that merely confirms the prompt contains an instruction establishes neither of those claims.

# Part 2 — The five decisions applied to my Werewolf project

**The system in brief.** A game has ten **seats**, each played by a model agent (an AI seat) or by a person. LangGraph runs the game as a **graph**: each step, such as one seat's turn, is a **node**, and the game's state is saved after each step. Each AI seat's prompt is built from the information that seat is allowed to know. The server turns the graph's output into events for the browser (the **translator**) and decides which seat may see which event. Games are played in two ways: **hosted games** on the website, and **batch games** run from the command line for experiments. Finished games also feed **lessons**, strategy notes extracted by a model and read by AI seats in later games.

Coding agents wrote most of the tests, alongside each feature. I did not write a ranked list of claims first. This part works the claims out afterwards and looks at what the tests protect. It was first written from counts and results read or run on 2026-11-17.

**What the clean-up of 2026-11-18 changed.** The next day I went through the backend tests with the five steps, and this part now describes the suite after that work. The counts are from 2026-11-18.

- **Cut.** Code left over from closed experiments was deleted together with its tests: 112 files, about 24,000 lines and 208 tests. A git tag, `pre-test-cut-2026-11-18`, marks the last commit that holds them.
- **Database tests on a real database.** A fixture starts one Postgres container for the test run and gives each test its own empty database. The tests that need it are in `integration` folders. No test is skipped for lack of a database any more, and no test uses the database my development settings point at.
- **Three gaps of this note closed with a test:** a restart test on real Postgres (step 1, last row), a planted-key test that searches every database table and the log after a whole game, and a test that two games on one server do not hold each other up.
- **A fault found by one of them.** The planted-key test found a player's key in a saved checkpoint. A provider's refusal can quote the key; my code raised that text to end the game, and LangGraph saves a raised error. The text is now scrubbed where the error is caught (U10, section 3.6).
- **Models passed in, not looked up.** The game's code used to fetch its models through module-level functions, so tests replaced those functions with `monkeypatch`. One object per game now carries the models, the player's key and the count of stalled turns, and a test passes its own.
- **Markers.** `live` became `contract`; `slow`, `integration` and `timing` were added.

## Step 1 in my system: the claims

The suite has thousands of tests. The more useful starting point is the claims that would cost most if false, with the evidence behind each:

| Claim | Existing evidence | Main gap |
|---|---|---|
| An AI seat's prompt never contains another seat's private information | Nine leak checks in the engine tests; seven of them also run on every batch game. (Eleven and nine until 2026-11-18, when two checks that searched for fields of the old nine-seat game were removed) | Hosted games: an audit that runs the same checks over a hosted game's saved prompts is written and tested, and is not scheduled, so nothing runs it. What a seat says is not checked |
| The engine settles each night's actions by the rules | Unit tests of the night rules | Not examined for this note |
| Every fact the deduction engine writes into a prompt is true. (The deduction engine is code that works out what a seat can deduce and adds it to that seat's prompt) | Thousands of random legal nights from fixed seeds, each settled by the real game code | Nights the generator cannot produce |
| A whole ten-seat game can be played to the end, and every step becomes browser events | Whole games on the real graph with a scripted model | Everything a real model does |
| A player's own API key is never written out | Planted-key tests for a dead game's error text and traceback, the crash report sent to Sentry, and the log of a failure after the game is over. A real call to each of the five providers with a made-up key: none returned the whole key in its error, and two returned part of it (U10, section 3.6) | Since 2026-11-18 a test plants a key, plays a whole game on real Postgres and searches every table and the log; a second one does the same for a game that a refused key ended. What is sent to the tracing service is still not searched. The scrubbing matches the whole key, so the part of a key that two providers return passes it |
| A prompt changes only on purpose | A golden of the day-discussion prompt for each of the ten roles | Whether the prompt is good. Sections that the golden's game state leaves empty |
| The server and the browser agree on the API | A test that fails when the saved API description is out of date | The separate rules for which seat may see which event |
| A hosted game survives a server restart | Recovery tests against test doubles; a manual restart check in August. Since 2026-11-18, a test that stops a hosted game on real Postgres while it waits on a person, builds a new server over the same database, and plays the game to its end | The test stops the server between two steps. It does not kill a process in the middle of a write |

The last row shows why the number of tests is a poor measure. Surviving a restart is near the top of the list by cost, and until 2026-11-18 its automatic tests replaced the main part of the real recovery mechanism. A ranked list written before the tests would have made that visible; writing this table is what made me build the test.

## Step 2 in my system: the checks, and what is real in each

**What the suite contains.**

| Folder | Tests | What they test |
|---|---|---|
| `tests/engine` | 1,321 | Game rules, night resolution, the deduction engine, prompt assembly, whole games with a scripted model |
| `tests/memory` | 499 | Lessons: extraction, removal of duplicates, storage and retrieval, and the pruning and synthesis that run in production. 4 are integration tests |
| `tests/evaluation` | 175 | The evaluation code itself: sampling, scoring, judging |
| `tests/server` | 320 | The game session, the API, the translator, durability. 7 are integration tests |
| `tests/contract` | 170 paid, 9 free | Every model a player can choose, asked for every seat's output format (170 cases, excluded by default); 9 free tests that a model is skipped when its provider's key is absent |

That is 2,494 Python tests. The quick default runs 2,314 of them: it leaves out the 170 paid ones and the ten slowest. The full local run, `poetry run pytest -m "not contract"`, runs 2,324. (Before the cut of 2026-11-18: 2,652, of which 2,482 ran by default.) The frontend has 1,607 unit tests in 73 files (Vitest, no browser), and a browser suite of 8 spec files with about 115 tests and 99 saved screenshots (Playwright).

**What is real and what is replaced.**

| Check | What actually runs | What is replaced or left out |
|---|---|---|
| Engine unit tests | Game rules, changes to the game state, prompt formatting | Nothing large; the inputs are built for the test |
| Whole-game engine tests | The real graph, and the server's translator | The model, by a **scripted model** that fills any output format with legal values chosen at random. Some supporting model calls are stubbed |
| Server tests | A real game session, and the real API application behind a test client | The game graph, by a test double that yields scripted output. Database writes are recorded instead of sent |
| Integration tests (11, since 2026-11-18) | The real graph, the real session and registry, the Postgres checkpoint saver, the game repository and the lesson store, on a Postgres container started for the run | The model, by the scripted model. The key check with the provider |
| Frontend unit tests | The frontend's logic, with no browser. A small group renders components to HTML to check that private data reaches only the reader allowed to see it | The server; the fixtures are saved games |
| Browser tests | The real pages in a headless Chromium browser | The whole server: every API call is answered from saved games. So these test the pages, not the system end to end |
| `contract` tests | Calls to real model providers | A game. They check output format only |
| Evaluations and batch games | Real models playing games, or replaying saved game states | Nothing. They are run by hand, and their results hold for the models, prompts and sample tested |

Three of these replacements hide something that matters:

- **The scripted model** makes it practical to check that a game runs to its end, that the state changes correctly and that every step becomes events. It cannot show what a real model says, how often its answer fails validation, or how long a turn takes. The real checks are the `contract` tests, whose own description records a run on 2026-09-10 (I did not look for later runs), and the evaluations.
- **The test-double graph in the server tests** means those recovery tests never use the code that saves game state to Postgres. A real kill and restart was last checked by hand in August (U3, section 3.8). The check that was missing when I first wrote this is now built (2026-11-18): a scripted game that saves to a test Postgres, is stopped and brought back, and is then checked for recovery. It needs no model calls. It stops the server object in one process; a kill of the process during a write is still not tested.
- **The browser suite keeps its own copy of the server's rules** for which seat may see which event, and uses that copy to decide what each seat is sent. If the rules change on the server, the browser suite does not detect it. The copy already lacks two event types that only their own seat may see, `uses_remaining` and `night_record`. The API description test does not cover this, because those rules are not part of the API's shape.

**Goldens.**

| Golden | What it protects | Built from |
|---|---|---|
| The day-discussion prompt | The exact text sent to each of the ten roles, in one game state on day 3 | A game state written by hand to have something in every section of the prompt |
| Two translator goldens | Every browser event produced for a whole game | Two real games, one with a human seat |
| The saved API description | The server's declared API, from which the frontend's types are generated. This is the contract test | The server itself |
| Frontend beat goldens | The list of moments the replay shows one after another (each called a beat) | Real games |
| Screenshot goldens | 99 pictures of pages and scenes, with 0.5% of pixels allowed to differ | The rendered pages |

The prompt golden matters most, because a prompt change alters how the AI seats behave without changing any Python interface. It protects only the game state it was built from: a section of the prompt that this state leaves empty is not checked. And it shows that the prompt has not changed, not that the prompt is good.

## Step 3 in my system: the failure cases

Failure cases in this suite were not found by asking the questions of step 3. They were added feature by feature. Three parts of the suite do correspond to those questions:

- **Varied inputs.** The deduction engine's tests draw thousands of random legal nights from fixed seeds, so combinations nobody thought of are tried on every run.
- **"What if this operation runs again?"** A person's turn stops the game and waits for their answer (U5). When the game resumes, the step that was waiting starts again from its beginning, so the night's turns run a second time. The Vigilante test (step 5 below) checks that this does not spend a bullet twice.
- **"What if execution stops here?"** The recovery tests cover this against test doubles, and since 2026-11-18 one test covers a stop between two steps on real Postgres.
- **"What if two run at once?"** Since 2026-11-18 one test runs two games on one server and holds up the first game's saves; the second game still finishes.

Not examined for this note: whether the engine and server tests cover the question of a result that was confirmed or only requested, or two operations at once inside one game, and whether the frontend tests cover the loading, empty and error states of each page.

## Step 4 in my system: how the tests are run

**Commands.** `poetry run pytest` runs the quick default. `poetry run pytest -m "not contract"` is the full local run, which adds the ten slowest tests. The paid tests carry the marker `contract` and run only with `-m contract`. On 2026-11-18 the full local run gave 2,324 passed and none skipped in 9 minutes 31 seconds. (On 2026-11-17, before the cut: 2,481 passed and 1 skipped in 13 minutes 38 seconds, on a machine that was also running other work; ten deduction-engine tests over random nights took about 10 of those minutes, and they are the ten now marked `slow`.) The frontend's unit tests all passed in 56 seconds. The browser suite was not run for this note; the frontend's testing guide estimates 16 minutes.

**Layout.** The test folders follow the parts of the system. Inside a part, a folder named `integration` holds the tests that need the Postgres container, and they get the marker `integration` from the folder. `tests/fixtures/` holds the fixtures, one file per resource, and the golden files. `tests/factories/` holds the functions that build test data, including the random nights. I asked the agent to copy this layout from my dota2pred project. In the frontend, each unit test file sits beside the code it tests, and the browser tests are in `frontend/e2e/`. Tests are named as sentences, for example `test_a_dead_player_gets_no_record_of_its_last_night`.

**A fixed environment.** The shared setup file switches tracing off, switches off a paid model call made after each game, and takes the list of models from the code instead of the live database. Until 2026-11-18 there was one exception: a few tests used a real Postgres database when a database address was set, as it is on my machine, and were skipped otherwise. So the same command tested more on my machine than on a clean one. Those tests now run on a Postgres container that the test run starts itself, so they need Docker and nothing from my settings. One limit remains: the whole-game tests play a different game on each run, because the scripted players share one random generator across threads (step 5 below). I chose to keep that and assert only what holds for any game.

**CI since 2026-11-18.** Until that day nothing ran the tests automatically: no CI configuration, no active git hook, no Makefile. The tests ran when I or an agent ran them, against the working folder, which often holds uncommitted edits from several pieces of work at once. So a pass meant: on my machine, on the files in the working folder at that moment, with the paid tests left out.

A workflow on GitHub Actions (`.github/workflows/ci.yml`) now runs from a clean checkout of the pushed commit, with no settings file, made-up provider keys and the packages of the lock file. Every push to any branch runs the quick tests (2,296 tests in about two minutes there). A push to `main`, a pull request to `main` or a run started by hand also runs the integration tests, the slow tests, and a build of the server image in which the server must start. So a green run is a record that one named commit passed on a machine that is not mine.

What it still does not give me: no step of a release checks for a green run (U14, section 3.1), so I can still deploy a commit that failed. And on 2026-11-18 only the short run had run on GitHub; the full run was rehearsed on my machine in a clean checkout, not yet run there.

Two things only the real run showed. Building the server image from the lock file failed on three packages the game imports that were never declared; they had been installed by hand. And the first run on GitHub failed before any test: the runner named "latest" had moved to a newer Ubuntu release for which my exact Python version is not built. I had rehearsed every test step on my machine and neither fault could appear there.

**What is written down for an agent.** [`docs/testing.md`](../../../docs/testing.md), written on 2026-11-17, holds the three things of section 4.5: the costliest claims, the commands with the folders and the way each golden is regenerated, and what to run and report before a change counts as finished. `CLAUDE.md` points to it. The clean-up of 2026-11-18 was done under it by coding agents that I briefed and checked; it has not yet been used by an agent working without that supervision.

## Step 5 in my system: two tests reviewed

### A prompt change, and a check it weakened

On 2026-11-17 I changed how a player's words appear in the AI seats' prompts. Each message is now one line inside quotation marks, with a caption line saying so. The change was a defence against a person typing a fake game-master announcement into their own message (U11, section 3.3). Four questions had to be answered, and each needed a different kind of evidence:

| Question | Evidence | Result |
|---|---|---|
| Does the prompt render as intended? | 10 tests of the quotation marks, 18 of the one-line rendering, and the prompt golden regenerated with its difference read | Passed |
| Does quoting reduce the effect of a forged announcement? | An experiment with real model calls (438 calls, $0.34), at three saved points in two games | The forged line named an innocent player. Votes for that player by seats on the village side fell from 24 of 33 to 14 of 33. The attack still worked often |
| Is the prompt the game now builds the same as the prompt the experiment tested? | The experiment had its own copy of the quoting code. A script rebuilt, through the game's code, the 22 prompts that contained a forged announcement | Identical, character for character, in all 22 |
| Does quoting change ordinary play? | A second experiment with no attack: 112 calls, $0.11 | No change it could detect. With 27 votes at the saved point it mainly used, it could miss a change of a few votes |

The deterministic tests answered the first question completely and could say nothing about the second: a test with a scripted model cannot show whether a real model believes a forged line. The result itself is a count from a few game states and one model. It shows that the effect fell, not by how much it falls in general.

The full run of the engine tests also showed a fault that the new tests could not. (Which test failed in that run is not recorded.) Three of the leak checks turned a seat's prompt input into one string with Python's `repr` and searched that string for private text. `repr` puts a string inside single quotation marks, and when the string itself contains both a single and a double quotation mark, it writes each apostrophe as `\'`. Once the discussion always contained double quotation marks, a leaked line such as `I'm the healer` would appear as `I\'m the healer`, and a search for the original text would not have found it. The checks now search the plain text as well. The game was not at fault. The change to the game had weakened a check on the game, and only running every test, not just the tests written for the change, showed it.

### A test that failed without the rule being broken

`test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume` plays a whole game in which a person's seat is the Vigilante, a role with two bullets to fire at night. The person's answers are scripted: shoot once, then hold fire. A shot goes ahead when it is fired and no other role has blocked the Vigilante that night. The test asserts that one shot went ahead and that one bullet is left.

It failed in 2 of 10 runs in one measurement and 4 of 10 in another (2026-11-12), and in 1 of 30 on 2026-11-17, with no change to the code. Two things in the test caused it:

- **Shared random state.** The scripted players draw from one random generator with a fixed seed, but the seats' night turns run on several threads. Which seat receives which number depends on which thread runs first, so a different game was played on each run.
- **The record it counted.** The test counts shots from the night records, and the engine, by its own rule, keeps no record of that night for a seat that dies the same night. In the failing runs the Vigilante fired, spent one bullet, and was killed that night, so the test counted zero shots.

A second explanation fitted the same symptom: Python changes how it orders sets of strings from one process to the next. A script replayed the test's game under four settings to separate the two:

| Setting | Replays | Different games played |
|---|---|---|
| Normal threads, string ordering varying | 20 | 20 |
| Normal threads, string ordering fixed | 20 | 20 |
| One thread at a time, string ordering varying | 20 | 1 |
| One thread at a time, string ordering fixed | 10 | 1 |

Fixing the string ordering changed nothing, and one thread at a time made every replay play the same game. So thread order is the source of the variation. In all 70 replays the bullet was spent once. The rule held; the test did not control what its result depended on.

**The repair** sets up a situation in which the variation cannot affect the result (the first kind of repair in section 4.3). No scripted player may choose the Vigilante as a target, so it cannot die and cannot be blocked, and its shot always goes ahead. The games still differ from run to run. The cost is that this test no longer covers games in which the Vigilante is killed or blocked. The alternative, asserting only that the bullets went down by one, was not chosen: in a game where no shot goes ahead, that test would pass while checking nothing.

**Can the repaired test still fail?** A repair that removes a failure has to answer the first question of step 5. The test was run against two deliberately broken versions of the engine. In the first, one shot spends two bullets. In the second, a bullet is spent every time the Vigilante's turn starts, so a turn that runs again after the pause spends a second bullet; this is the fault the test exists to catch. The repaired test failed on its bullet count under both, and passed on the unbroken engine. Each broken version was run once.

After the repair the test passed in 100 of 100 runs, and the full engine suite passed. The 100 passes alone would not show that the test still means anything; the two broken versions show that. The record is [vigilante_test/experiment_log.md](vigilante_test/experiment_log.md).

The other whole-game tests in the same file use the same scripted players, so their games also vary by thread order. None was seen to fail, and whether any can fail by chance was not examined.

## Known gaps and possible improvements

The order of the rows is not an order of urgency.

| Gap | Step | Why it matters | Possible improvement |
|---|---|---|---|
| 1. **Half closed on 2026-11-18.** Nothing ran the tests automatically, and no release step runs them | 4 | A pass is not tied to the released revision | Built: CI on every push. Still open: a release step that refuses a revision without a recorded pass |
| 2. **Partly closed on 2026-11-18.** The recovery tests replaced the real code that saves game state | 2 | A fault in recovery from Postgres would not be caught | Built: a restart test on a test Postgres with scripted players. Still open: a kill of the process in the middle of a write |
| 3. The other whole-game tests share the scripted players that made the Vigilante test vary by thread order | 4 | One of them could fail by chance | A scripted player that does not depend on thread order, for the whole file. Looked at on 2026-11-18 and left: the scripted model is not told which seat is asking, so it needs more than a small change |
| 4. The `contract` model check is run by hand | 2 | A provider change can break structured output until a real game fails | Run it on a schedule, and record each run |
| 5. The browser suite has its own copy of the rules for who sees what, already two event types behind | 2 | A change on the server is not detected | Generate the copy from the server, or compare the two in one test |
| 6. **Mostly closed on 2026-11-18.** The planted-key tests covered the error text, the crash report and one log, and the log line of a failed model call was not scrubbed | 2 | The gap was real: the new test found the key in a saved checkpoint | Built: a search of every database table and the log after a whole game, and scrubbing of every model call's error. Still open: what is sent to the tracing service, and a key returned in part (U10 gap 2) |
| 7. No check of accessibility (whether the pages can be used with a keyboard or a screen reader) runs | 1 | Nothing would catch a page that cannot be used by keyboard | An automated accessibility checker in the browser tests, and one keyboard-only test |
| 8. No ranked list of claims was written first, and no pass over the questions of step 3 | 1, 3 | A costly claim can have a weak check without anyone having decided that | Keep the table of step 1 as a short list, and ask the step 3 questions of the game session and the API |
| 9. The testing guide for agents is new and nothing enforced it | 4 | An agent can still report "all tests pass" after running only the tests it wrote | CI, which runs the quick set whatever the agent ran (built 2026-11-18). It checks a pushed commit, so it does not check an agent's claim about uncommitted work |
| 10. The frontend testing guide lists 5 browser spec files; the folder has 8 | 4 | The record of what is tested is incomplete | Add the three missing rows |

# Part 3 — Review

## The five decisions in two minutes

**1. Identify claims.** Find what must be true from four places: rules that must stay true, the tasks users must be able to finish, boundaries between components, and past faults. Rank them by what a false one would cost.
*My system:* no list was written first. The costliest claims each have a check, and some of those checks are partial: a restart is tested for a stop between two steps and not for a kill during a write, hosted games are not searched for leaks, and the key search does not cover what is sent to the tracing service.

**2. Design checks.** Decide what must actually run for a test to detect the fault. Replace a dependency when that is useful, and say what the replacement removes from the evidence. Unit tests, integration tests, end-to-end tests and evaluations with the real model answer different questions.
*My system:* 2,314 Python tests in the quick default and 2,324 in the full local run, 1,607 frontend unit tests, a browser suite, five kinds of golden, and evaluations run by hand. The model is scripted in every default test, the graph is replaced in the server tests except the eleven integration tests, and the server is replaced in the browser tests.

**3. Find failure cases.** Vary the inputs: empty, one, many, at the limit, invalid, duplicate. Ask of each operation: what if execution stops here, it runs again, two run at once, or the result was only requested and not confirmed?
*My system:* covered by generated random nights and by particular tests, not by a pass over these questions.

**4. Make testing repeatable.** Predictable commands, shared fixtures and factories, the same result on every run, and CI. For a coding agent, write down what must be protected, how tests are run, and what evidence it hands back.
*My system:* one command and a clear layout; a database container the test run starts itself; a testing guide for agents since 2026-11-17; CI since 2026-11-18, so a green run describes one pushed commit on a clean machine. No release step checks for it yet.

**5. Review the evidence.** Can the test fail? Does it check the intended behaviour? What does a pass not establish?
*My system:* the repaired Vigilante test was shown to fail against an engine broken on purpose; the full run caught a leak check that a prompt change had weakened; a planted-key test over the whole database found a key in a saved checkpoint.

The idea behind all five: decide what must be true, then choose checks that could show when it is false.

## Stopping check

Without looking back at the note, explain:

1. why looking for invariants finds tests that feature-by-feature testing misses, although most tests do not assert an invariant;
2. why testing a refund rule with a fake database can miss a fault that appears only when two requests arrive at once;
3. why the prompt golden cannot show that the quotation marks work as a defence;
4. why a coding agent can produce hundreds of passing tests without protecting the behaviour that matters most;
5. why 100 passing runs of the repaired Vigilante test did not, alone, show that the test still meant anything.

## Problem A: a new system

A team is building a service that accepts uploaded invoices, uses a language model to extract the supplier, the date and the total, and shows the result to an accountant to approve. Coding agents will write most of the code and the tests. Design the testing:

1. Three important claims, ranked.
2. A check for each claim, and which components must be real in it.
3. The dependencies that are replaced, and what each replacement hides.
4. At least four failure cases.
5. How the project is set up so that coding agents can run the tests reliably.
6. The evidence required before the work is accepted.

<details>
<summary>One possible answer</summary>

**Claims.** (1) The stored invoice is what the accountant approved. (2) An invoice submitted twice is not stored twice. (3) The model extracts the correct total often enough for the workflow, which is a rate.

**Checks.** Claims 1 and 2 are rules in code: unit tests of the approval and storage logic, plus an integration test against a real test database for claim 2, because a fake store has no uniqueness constraint and no behaviour under two writes at once. Claim 3 needs an evaluation: invoices with known totals, run through the real model, with the number correct and the sample size stated.

**Dependencies.** The model is replaced in the deterministic tests, which hides every wrong or malformed extraction. The database is real where its constraints matter. A fake file store hides size limits and failed uploads.

**Failure cases.** An empty file; the same invoice uploaded twice; an invoice with two totals, or a total in another currency; the model returning text where a number is required; the process stopping after the model answers and before the result is stored; two accountants approving the same invoice at once.

**Set up for the agents.** The claims and failure cases are given before the code is written. There is a default test command that needs no model and no credentials, a second command for the integration tests against a test database, and a separately started evaluation. Fixtures and factories are shared. Each change comes back with what ran, what passed and failed, what was skipped, and which dependencies were replaced. CI runs the default set and the integration tests on every push.

**Review.** The assertions for claims 1 and 2 are read by a person, and each is shown to fail against a deliberately broken version. A good evaluation result is reported as a count from a sample, not as a guarantee for every future invoice.
</details>

## Problem B: claims about my own system

For each sentence, say what evidence stands behind it and what remains uncertain.

1. "The AI seats' prompts never contain another seat's private information."
2. "A game survives a server restart."
3. "Putting players' words in quotation marks roughly halves the effect of a forged game-master line."

<details>
<summary>Answers</summary>

1. The leak checks search every seat's prompt input, in the engine tests over scripted games and in the batch runner over games with real models. They do not cover hosted games, and they do not check what a seat says. Accurate wording: "In every batch game, an automatic check searches each seat's prompt input for seven kinds of private information; hosted games are not checked."
2. The recovery logic is tested against test doubles, and since 2026-11-18 one test stops a hosted game on real Postgres while it waits on a person, rebuilds the server over the same database and plays the game to its end. It does not kill a process during a write. Accurate wording: "An automatic test restarts the server between two steps of a game and checks that the game continues; a crash in the middle of a write is not tested." (Before that test existed, the accurate wording was: "The recovery logic is tested against test doubles; a real restart was last checked by hand in August.")
3. An experiment with real models: 438 calls at three saved points in two games, one model. Votes for the named innocent player fell from 24 of 33 to 14 of 33. "Roughly halves" matches that count. It does not establish the size of the effect for other models, games or attacks.
</details>

# Appendix — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named; not run unless stated), **run** (executed for this note), **doc** (a written record, not re-checked in the code). Read and run on 2026-11-17; the entries changed by the clean-up were read and run again on 2026-11-18. Paths are from the repository root.*

**The suite**

- Test counts per folder, 2,494 in all, 170 marked `contract`, 11 `integration`, 10 `slow`, 6 `timing`: **run** on 2026-11-18 (`poetry run pytest --collect-only -q -m ''`, per folder, and with each marker)
- `contract` and `slow` excluded by default: **code** `pyproject.toml` (`[tool.pytest.ini_options]`)
- The full local run: **run** on 2026-11-18 (`poetry run pytest -q -m "not contract"`): 2,324 passed, 170 deselected, 571 s. The run of 2026-11-17 before the cut: 2,481 passed, 1 skipped, 170 deselected, 818 s
- The Postgres container and the database per test: **code** `tests/fixtures/database.py`; the tests that use it: `tests/server/integration/`, `tests/memory/integration/`
- What was cut and what was kept: **doc** [`u13_cut_list.md`](u13_cut_list.md), [`u13_test_map.md`](u13_test_map.md) (the map describes the suite before the cut)
- Frontend unit tests, 73 files, 1,607 tests, passed in 56 s: **run** (`npx vitest run` in `frontend/`)
- Browser spec files (8), `test(` declarations (115, counted by a text search), screenshots (99): **code** `frontend/e2e/`, `frontend/playwright.config.ts`; not run
- The shared setup, fixtures and factories: **code** [`tests/conftest.py`](../../../tests/conftest.py), `tests/fixtures/`, `tests/factories/`

**What is real and what is replaced**

- Random legal nights from fixed seeds: **code** `tests/factories/random_nights.py`, `tests/engine/deduction/`
- The scripted model: **code** [`tests/factories/scripted_model.py`](../../../tests/factories/scripted_model.py) (`fill`, `ScriptedModel`, `ScriptedModels`), the fixture `scripted_model` in `tests/fixtures/model.py`; the per-game models object a test passes in: `Agents/llm_factory/game_models.py`
- The test-double graph and the API test client: **code** [`tests/fixtures/server.py`](../../../tests/fixtures/server.py)
- Recovery without real Postgres: **code** `tests/server/test_durability.py`; the August manual check: **doc** U3 section 3.8; the restart on real Postgres: **test** `tests/server/integration/test_restart.py` (run 2026-11-18)
- Two games on one server: **test** `tests/server/integration/test_game_isolation.py` (run 2026-11-18; shown to fail with one shared saver)
- The browser suite's saved answers and its own copy of the visibility rules: **doc** [`frontend/docs/testing.md`](../../../frontend/docs/testing.md); **code** `frontend/e2e/live.spec.ts`
- The planted-key tests: **code** `tests/server/test_byok.py::test_dead_game_error_never_echoes_the_key` and `::test_dead_game_error_never_echoes_the_backup_key`; the search of every table and the log: **test** `tests/server/integration/test_planted_key.py` (run 2026-11-18); the other guarded places: **doc** U10 section 3.2; the real call to five providers: **doc** U10 section 3.6
- The paid model check and its recorded run: **code** `tests/contract/test_model_structured_output.py` (module note)
- Evaluation runners: **code** `evaluation/README.md`, `evaluation/experiments/` (62 files)

**Goldens and leak checks**

- The prompt golden: **code** `tests/fixtures/day_discuss_prompt_golden.py`; **test** `tests/engine/test_draft_preview.py::test_ai_discuss_prompt_is_byte_identical_to_the_golden`
- Translator goldens: **code** `tests/fixtures/translator_golden.py`
- The API description test: **code** `tests/server/test_openapi_snapshot.py`
- Beat and screenshot goldens, the 0.5% tolerance: **code** `frontend/playwright.config.ts`; **doc** `frontend/docs/testing.md`
- Nine leak checks, seven run on batch games (`run_leak_tests`): **code** [`tests/leak_test.py`](../../../tests/leak_test.py), `scripts/run_batch.py`

**The two reviewed tests**

- The quoting change and its tests: **test** `tests/engine/test_transcript_quoting.py` (10), `tests/engine/test_transcript_one_line.py` (18)
- The two experiments and the comparison of 22 prompts: **doc** [`evidence/agent_boundaries/forged_speaker/report.md`](../../agent_boundaries/forged_speaker/report.md) and its log; no model calls were made for this note
- The `repr` fault and its fix: **code** `tests/leak_test.py::_searchable`; **doc** the same report
- The Vigilante test, its replays, the repair and the two broken versions: **doc** [`vigilante_test/experiment_log.md`](vigilante_test/experiment_log.md); **code** `tests/engine/test_whole_game.py` (the test moved there on 2026-11-18), `measurements/u13_vig_probe.py`, `measurements/u13_vig_mutations.py` (the two scripts import the old file and no longer run as they are)

**How tests are run**

- No CI workflow, pre-commit configuration, Makefile or active git hook: **run** on 2026-11-17 (a file search and `git config`)
- The CI workflow and its first runs: **code** `.github/workflows/ci.yml`; **run** on GitHub, 2026-11-18: commit `bd91a155` failed at "Set up Python", commit `09647513` passed the short run (quick tests in 2 min 13 s). The full run's steps were run on my machine in a clean checkout: 2,296 quick, 6 timing, 11 integration and 10 slow tests passed, 1 skipped
- No tests in the release procedure: **doc** U14 section 3.1
- The testing guide and the pointer to it: **doc** [`docs/testing.md`](../../../docs/testing.md), `CLAUDE.md`
- That no ranked list of claims was written first, and that agents wrote the tests: my own account

**Not checked**

- The browser suite, the type check, the lint and the production build were not run.
- Whether the `contract` tests have been run since 2026-09-10.
- Which test caught the `repr` fault.
- Whether the night-rule tests leave anything out, and the two items listed as not examined under step 3.

**Further reading, only when needed:** Ham Vocke, "The Practical Test Pyramid", on Martin Fowler's site. Martin Fowler, "Eradicating Non-Determinism in Tests", for flaky tests.
