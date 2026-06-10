# prompt_bundle_hash transition: rendering layer joins the bundle (2026-06-10)

One-time, **content-neutral** change to `prompt_bundle_hash`. Recorded here so anyone
comparing stamped records across the boundary knows the bump is a glob expansion, not a
prompt edit.

## What changed

`formatters.py` and `prompt_inputs.py` moved from the flat `Agents/` top level **into**
`Agents/prompts/`. `run_fingerprint.prompt_bundle_hash()` globs `Agents/prompts/*.py`, so
the two files now contribute to the hash.

| | value |
|---|---|
| bundle hash BEFORE | `9d82636a7697d4a6` |
| bundle hash AFTER  | `be56dd2794d31e77` |
| cause | `formatters.py` (`067bfe0c…`) + `prompt_inputs.py` (`fe391f84…`) entered the glob |

## Why it's not a prompt change

- All 9 pre-existing `prompts/*.py` are **byte-identical** across the move (per-file
  sha256 verified unchanged: `__init__ 6a6a89.. common 24ab19.. day 3e42e5.. dedup c59847..
  extraction bd52fb.. memory 1ed759.. night 89f909.. roles a4ced2.. standards c0354e..`).
- The two added files are byte-for-byte the old flat modules (a `git mv`), except
  `prompt_inputs.py`'s import lines were repointed to sibling submodules (`.formatters`,
  `.memory`, `.standards`) to avoid a package-init back-edge — same constants, same
  behaviour, no model-visible text changed.
- Model inputs are unchanged; only *which files the hash globs* changed.

## Why it's an improvement (the coverage gap it closes)

Before, editing a formatter (e.g. `format_day_channel`) changed what every agent's prompt
renders, yet **did not** bump `prompt_bundle_hash` — only the git SHA caught it. The
rendering layer is now inside the bundle, so formatter/input-assembly edits correctly bump
the hash going forward. The fingerprint's definition of "prompt surface" now matches reality.

## Implication for stamped records

Records (batch JSONL, trace metadata) stamped before this commit carry `9d82636a7697d4a6`;
after, `be56dd2794d31e77`. A bundle-hash difference **across this boundary alone** does not
indicate a prompt change. Within either side, the hash behaves as before.

## Addendum (same day): formatters.py renamed prompt_formatters.py

Immediately after the fold, `prompts/formatters.py` was renamed `prompts/prompt_formatters.py`
(symmetry with `prompt_inputs.py`). The bundle hash includes file *names*, so this is a second
content-neutral bump: `be56dd2794d31e77` → **`7a8542224196ca0e`** (file bytes unchanged; only
the hashed name changed). `7a8542224196ca0e` is the stable post-transition hash. No game was
generated between the two intermediate hashes, so in practice stamped records jump straight
from `9d82636a7697d4a6` to `7a8542224196ca0e`.
