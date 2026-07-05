"""Thin CLI for the discussion-tagger validation runner (``eval-tagger`` console entry).

Keeps the thin-CLI seam: all load/tag/aggregate logic lives in
``evaluation.src.instrument_validation.tagger.tagger_validation`` (the instrument-validation home,
"does the deceiver-side ruler measure what it claims"). This file is only argument parsing +
orchestration + artifact write.

  poetry run eval-tagger --config evaluation/config/template/tagger_eval_example.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.src.core import manifest
from evaluation.src.instrument_validation.tagger.tagger_validation import (
    _clean,
    _print_summary,
    output_path,
    read_config,
    run,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the end-of-day discussion tagger (accuracy | skill | deleak).")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    cfg = read_config(args.config)
    result, sources = run(cfg)
    out = output_path(cfg.output, cfg.mode)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.embed(result, artifact=out, config=cfg, inputs=sources)
    out.write_text(json.dumps(_clean(result), indent=2) + "\n", encoding="utf-8")

    _print_summary(result)
    print(f"\nWrote {cfg.mode} results -> {out}", flush=True)


if __name__ == "__main__":
    main()
