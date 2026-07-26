# Eval architecture: code vs. record — and why the archive stays frozen

**Date:** 2026-06-10
**Status:** Decision record. The operational form of this convention lives in `CLAUDE.md`
("Eval Architecture"); this is the narrative — the tension and why it was resolved this way.
Companion to [structure_audit.md](structure_audit.md) and
[the experiment-provenance report](../tracing/fingerprinting/report.md).

---

## 0. TL;DR

- An iteration-heavy eval project grows **two homes for "an experiment"** — the authoritative
  pipeline (`evaluation/`) and the experimental archive (`evidence/`) — and across iterations they
  blurred: study code lived ad-hoc in `scripts/` and wrote its outputs into `evidence/`, with no
  promotion path, each iteration doing it slightly differently.
- The convention is **three layers, one rule each**: `evaluation/` is the sole home of authoritative
  eval *code*; `evidence/<experiment>/` is the *record* (narrative + artifacts + a provenance pointer
  back to the code, never a copy of it); the data plane is *I/O*.
- The hard call is about the existing archive: **freeze it, don't retrofit.** Bulk-hoisting old study
  code into `evaluation/` would erase the journey it documents *and* pollute the authoritative
  pipeline with superseded methods. Graduation into `evaluation/` is **just-in-time** — only when v5
  actually adopts a study's method.
- This is not debt-shame. The journey is told by **records + git history**, not by keeping dead code
  alive in the tree. A clean-from-day-one eval architecture would be the suspicious outcome here, not
  this one.

---

## 1. The tension

The word "experiment" names two different things in this repo, and that is the whole problem:

- `evaluation/experiments/` — a **verb**: the runnable code that *executes* an eval.
- `evidence/<experiment>/` — a **noun**: the *record of* an eval that was run (write-up + artifacts).

They blurred because eval practice co-evolved with the research. The memory pipeline was the moving
target; the way we measured it changed alongside it. So experiment code accreted in `scripts/` as
one-offs, wrote outputs straight into `evidence/`, and each iteration reinvented its own
load-dataset → run → judge → write loop. The concrete symptom: you could not answer *"what is the
authoritative way to evaluate X?"* because there were three half-answers in three places, none
marked as canonical.

This is the gap. Not "the code is bad" — the code worked and the experiments were real — but
"there is no single source of truth for the eval method, and no rule for where method-code ends and
experiment-record begins."

## 2. The principle: three layers, one rule each

| Layer | What it holds | The one rule |
|---|---|---|
| `evaluation/` | authoritative eval **code** | one canonical runner per eval kind — what v5 runs on. `scripts/` keeps only generation entry + ops, never reusable eval logic. |
| `evidence/<experiment>/` | the **record** | narrative + data artifacts + a **pointer** back to the code that produced it. Store the pointer, never a copy of the function. |
| `evaluation/config/ evaluation/frozen_eval_sets/ evaluation/eval_results/ batch_results/` | pipeline **I/O** | the conveyor belt between the two; see the *Data plane* section in `evaluation/README.md`. |

The pointer is not aspirational: provenance records carry a Git revision and embedded config, while
batch records additionally carry the fuller `runtime_fingerprint`. Together they are the
back-reference from an evidence artifact to the `evaluation/` code and settings that produced it
(see [the experiment-provenance report](../tracing/fingerprinting/report.md)). That is what makes
"evidence points at code" a mechanism rather than a hope — and what lets the record avoid carrying
its own copy of the function.

## 3. The lifecycle that keeps the layers honest

- **Explore.** A new eval question is a thin runner in `evaluation/experiments/` *from the start*
  (reusing `components/` / `judges/`), not a fresh script. Its output + write-up land in
  `evidence/<experiment>/`.
- **Graduate.** When the approach becomes the way v5 does X, the runner goes config-driven and
  canonical, the README names it, and the evidence folder points at it.
- **Supersede.** A better method replaces it: delete the old runner (git history keeps it), or keep
  it *runnable* per the Versioning Design Variants policy (config flag vs. tag/worktree). The old
  evidence folder is never touched.

## 4. The decision: freeze the existing archive

The existing `evidence/` predates this standard and violates it in places — frozen eval_sets live
inside experiment folders, golds sit next to reports, and study code (self-summary judges, situation
generators, gate metrics) is scattered through `evidence/*/scripts/`. Two ways to respond:

**Option A — retrofit.** Hoist all study code into `evaluation/`, migrate the frozen datasets into
the live plane, make the archive conform. *Rejected.* It fails three ways: (1) it **erases the
journey** — the old code-as-it-was-then is itself the record of how the eval was done at that
iteration, and "correcting" it deletes the evidence of evolution; (2) it **pollutes the authoritative
pipeline** with a museum of superseded methods, defeating the "one canonical runner" rule it is
supposed to serve; (3) it is **high-churn and high-risk** across artifacts that reports and code
still cite, for no forward benefit, since none of it will be regenerated.

**Option B — freeze + just-in-time graduation.** *Chosen.* The existing archive stays exactly as is.
The standard applies forward. A study's code migrates into `evaluation/` **only when v5 actually
adopts its method**, at which point the evidence folder gets a one-line "graduated to
`evaluation/X`" note. No bulk sweep, no upfront audit.

The tradeoff of B, named plainly: `evidence/` stays internally inconsistent — old and new conventions
coexist, and some study code keeps living in the archive in apparent violation of the forward rule.
That is acceptable because that code is a **dated artifact, not live debt**: it is never imported by
the pipeline, and its "wrongness" is honest history, not neglect. The cost of the inconsistency is
borne entirely by the archive (where messiness is truthful); the authoritative pipeline stays clean.

The non-obvious part of this decision is the restraint. The reflex on finding structural drift is to
refactor it. Here the senior move is the opposite — recognizing that the archive's purpose is to be a
faithful record, and that refactoring it would destroy the thing it exists to preserve. *Knowing when
not to refactor* was the actual decision.

## 5. Why this is a strength, not a confession

The instinct to hide a refactor — "won't it look like I didn't do it right the first time?" — is
inverted here. A portfolio that shows a pristine eval architecture with no visible evolution reads as
either trivial or fabricated. What this records instead is the thing worth showing: structural debt
recognized, its cause diagnosed (infra co-evolving with research), and a deliberate, reasoned
resolution that includes the discipline *not* to over-correct. The evolution is the evidence of real
engineering; the records and the commit history carry it, so the live tree doesn't have to.

## 6. Lessons

- **Separate the record of an experiment from the code that ran it, and let the record point at the
  code by version rather than copy it.** A record that embeds its own logic rots into a fork; a
  record that points at a fingerprint stays a faithful, reproducible reference.
- **An archive of past methods should be frozen, not retrofitted** — retrofitting destroys the very
  history the archive exists to document.
- **Deciding *not* to refactor is a design decision with the same weight as refactoring**, and it is
  the right one whenever the cost lands on a layer whose job is to be a truthful record.
- **In a research codebase, infrastructure co-evolves with the research.** The architectural standard
  is a convergence point you name once the shape is clear — not something you were supposed to have
  from the first commit.

## 7. Scope and what's next

Forward-looking only. Nothing in `evidence/` is moved. The just-in-time graduations ride the v5
build, one experiment at a time. The provenance manifest (the data-plane reorg's Wave 2) is the
pointer mechanism this convention leans on; until it lands, the back-reference is the commit SHA +
config recorded by `runtime_fingerprint`. The operational rule — for anyone (or any agent) doing eval
work — is in `CLAUDE.md` under "Eval Architecture."
