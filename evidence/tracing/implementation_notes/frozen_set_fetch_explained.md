# Eval improvement: why we emit eval cases locally instead of re-fetching from Langfuse (plain version)

A plain-English companion to the fix plan and the technical issue record. For the implementation
detail see [`ISSUE_frozen_set_fetch.md`](ISSUE_frozen_set_fetch.md) (root cause + acceptance
criteria + resolution, colocated here); this doc is the *why*, written to be read by anyone.

## The setup (analogy)
Every game writes a big **diary** (the Langfuse "trace") — ~1,300 entries (one per agent action, LLM
call, etc.). The thing we actually want for a test set is **one page**: the "eval case" (e.g. the
post-game extraction summary).

## What the old method did, and why it broke
To get that one page, the code asked Langfuse: *"photocopy me **every** page of this diary, I'll find
the one I want myself."*
- On a **short** game (thin diary) — fine.
- On a **long** game (~1,300 pages) — Langfuse refuses (*"too big, narrow your request"*) → **the 422.**
- And it's wasteful: copying 1,300 pages to read 1.

It was written when games were short, so nobody noticed. v5's longer games exposed it. It's a
*latent inefficiency surfaced by scale*, not a regression.

## The fix (two parts, because there are two situations)

**1. Going forward — keep a local copy ("primary" fix).**
The game **already builds that one page** during play — it just mails it straight to Langfuse and
keeps no copy. The fix: *also drop a copy in a local folder as it's written.* Building a test set then
= read your own folder. No asking Langfuse, no photocopying, nothing to refuse. (Only helps games run
from now on — past games kept no copy.)

**2. For already-run games — ask smarter ("secondary" fix).**
Those only live in Langfuse, so:
- Ask for the **table of contents** only (`trace.get`) — cheap, lists every page's title, never refuses.
- Find the title of the page you want.
- Ask for **just that one page by name** — cheap, never refuses, returns it in full.

(You can't jump straight to "give me the one page" without its exact title — hence two steps.)

## Why it's better

| | Old (fetch-all) | New |
|---|---|---|
| Long games | **422, build fails** | always works (fetch only what you want) |
| Speed | pull ~1,300 to keep 1 | read 1 |
| Dependency | needs Langfuse queryable; also **truncates** big pages | local file you own — no dependency, no truncation |
| Future eval ideas | — | can still pull *any* page later, no re-running games |

Two bonus fixes folded in:
- **Drift bug:** the page's "name" was written in **two** places (game-side and reader-side)
  independently — rename one, the reader silently finds nothing. Now the name lives in **one shared
  module** both import → can't drift.
- **Elegance:** the local copy is saved in the *exact shape the reader already expects*, so the reader
  barely changes — it reads from a folder instead of from Langfuse. Little new code, reusing
  already-tested parts.

## One-line summary
The game already makes the thing we want — **stop throwing it away and re-fetching it the hard way.**
Keep a local copy (fast, durable, never breaks); for old games, ask Langfuse for *one page*, not *all*.

---

## ⭐ Generalizable pattern (adopt for future Langfuse/tracing projects)

**Headline: tracing is for *watching*; emit eval cases *locally* for *building*. Don't make your
tracing backend the primary eval-data store.**

A tracing backend (Langfuse, etc.) is built for observability — browsing/debugging runs. It is *not*
a reliable data store for building eval/test sets, because its read APIs are query-cost-guarded
(fetch-all chokes at scale → 422), may truncate large fields, and couple your eval pipeline to a
service's availability/quirks. So, as a default for any LLM/agent project where you'll build eval
sets from runs:

1. **Emit eval cases to a durable local artifact at run-time** — the moment you build the structured
   object, *tee a copy* to a per-run local file. That file is your eval-data source of truth: cheap,
   durable, no service dependency, no truncation, no query limits. Don't re-derive it later from the
   trace.
2. **Treat the tracing backend as the *secondary*, retrospective archive** — for mining spans you
   didn't pre-capture, or recovering old runs. When you read it: enumerate cheaply (whole-trace /
   table-of-contents call), then **point-lookup specific spans by name** — never "fetch-all then
   filter."
3. **Single source of truth for span names/ids** — define them once in a side-effect-free shared
   module imported by both producer (tracer) and consumer (eval reader) → no silent producer↔consumer
   drift.
4. **Make local and remote records the same shape** — so the same converters/selectors work on both
   sources; switching source is a one-line branch.
5. **Keep capture data-plane-only / behavior-neutral** — emitting eval cases must not change model I/O
   or run behavior, so it can be added anytime without invalidating prior results.

**When to skip:** tiny/throwaway projects with short traces — fetch-all from the tracer is fine until
it isn't. The local-emission pattern pays off when runs are large (many spans), you build eval sets
*repeatedly*, or you need durability/reproducibility. (For this project: 1,300 spans/game + repeated
frozen-set builds → it pays off clearly.)
