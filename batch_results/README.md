# batch_results/

Generation output from `scripts/run_batch.py` (and the v7 loop driver). Holds two
artifacts from the same runs — **game records** (one line = one finished game) and
**eval cases** (one line = one captured decision). **Gitignored** — this README is the
only tracked file.

There are two layouts. New runs should use the **experiment layout**; the **legacy flat
layout** is what older runs (and any run without `--experiment`) use, and still works.

## Experiment layout (default) — one self-describing folder per run

This is the **default**: `scripts/run_batch.py` puts every run under its own folder, named
by `--experiment <id>` if given, else the session prefix (the loop driver sets it too).
Everything for that run lands under one folder:

```
batch_results/<experiment>/
  config.json          # the descriptor — see below
  summary.json         # per-run outcome/status, merged across invocations
  games/<session_prefix>.jsonl              # game records (lines = games)
  eval_cases/<session_id>/<game_id>.jsonl   # per-game eval-case sidecars
```

**`config.json` is the headline.** It is a faithful mirror of the *resolved* run config
(what actually ran, not the nominal request) plus the `runtime_fingerprint`, led by a
scannable `overview` block (store version, the arms as their enabled factions, scale,
model, git). So a reader gets the gist of a run — and can spot an arms-race slip (an arm
enabling more factions than intended) — without opening a single game record. It is also
**re-runnable**: `source.argv` is the exact recipe. The folder name is a human slug; the
structured truth lives in `config.json`, so runs are discoverable by querying manifests,
not by hoping a token is in the filename.

## Legacy flat layout (older runs, or `run_batch --flat`)

```
batch_results/
  <session_prefix>.jsonl            # game records, flat (one file per run_batch invocation)
  eval_cases/<session_id>/<game_id>.jsonl
  legacy/                           # concluded smoke / superseded runs + non-game strays
```

Pass `run_batch.py --flat` to opt back into this. Flat files stay flat and are **never
renamed** — the filename (`<session_prefix>`) doubles as the Langfuse session link.
`legacy/` holds retired runs and analysis/cluster dumps.

## How the two halves connect

Each **game record** stores an `eval_cases_path` pointer (repo-relative) to its eval-case
sidecar, plus `runtime_fingerprint`, the resolved configs, `winner`, `computed_metrics`,
and survivor breakdown. Each **eval case** is one captured decision (`name` encodes
player/day/phase; `input`/`output`/`kind`/`trace_id`). Consumers (the frozen-set builder,
the loop's credit/measure/tagger) **follow the `eval_cases_path` pointer** — they never
reconstruct the directory — which is why both layouts work without per-reader changes.

## Loop campaigns

The v7 loop driver writes its game records + history + store snapshots into its
`--run-dir`, and routes eval cases + `config.json` (a `LoopConfig` mirror) under
`batch_results/<run-dir-name>/`. Pass `--experiment <campaign>` and the run-dir defaults to
`batch_results/<campaign>/`, so the whole campaign — games, eval_cases, config, history —
unifies in one folder (pass an explicit `--run-dir` to override).

See the **Data plane** section in [`../evaluation/README.md`](../evaluation/README.md).
