"""Multi-model labeling engine with rate limiting and checkpointing.

Handles the core loop: for each item, call N models in parallel with
per-model rate limits, save checkpoints, and support resumption.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from evaluation.labeling.base import LabelingAdapter, LabelItem, LabelResult
from evaluation.labeling.config import ModelSpec


class _RateLimiter:
    """Per-model token-bucket rate limiter (thread-safe)."""

    def __init__(self, models: list[ModelSpec]):
        self._intervals: dict[str, float] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._last_call: dict[str, float] = {}
        for m in models:
            if m.rpm_limit:
                self._intervals[m.name] = 60.0 / m.rpm_limit
                self._locks[m.name] = threading.Lock()
                self._last_call[m.name] = 0.0

    def wait(self, model_name: str) -> None:
        if model_name not in self._intervals:
            return
        interval = self._intervals[model_name]
        lock = self._locks[model_name]
        with lock:
            now = time.monotonic()
            elapsed = now - self._last_call[model_name]
            if elapsed < interval:
                time.sleep(interval - elapsed)
            self._last_call[model_name] = time.monotonic()


def _extract_text(content) -> str:
    """Pull plain text from various LLM response content formats."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return " ".join(texts).strip()
    return str(content).strip()


def _call_model(
    model: ModelSpec,
    prompt: str,
    adapter: LabelingAdapter,
    rate_limiter: _RateLimiter,
) -> int | str | None:
    """Call a single model and parse the response via the adapter."""
    from Agents.llm_factory import create_chat_model

    kwargs = {}
    if model.thinking_level:
        kwargs["thinking_level"] = model.thinking_level

    for attempt in range(model.max_retries):
        try:
            rate_limiter.wait(model.name)
            llm = create_chat_model(model.name, temperature=model.temperature, **kwargs)
            response = llm.invoke(prompt)
            text = _extract_text(response.content)
            label = adapter.parse_response(text)
            if label is not None:
                return label
            print(f"    WARNING: {model.name} returned unparseable: {text!r}")
            return None
        except Exception as e:
            if attempt < model.max_retries - 1:
                is_rate_limit = "429" in str(e)
                wait = 10 if is_rate_limit else 2 ** (attempt + 1)
                print(f"    Retry {attempt + 1} for {model.name}: {e}")
                time.sleep(wait)
            else:
                print(f"    FAILED {model.name}: {e}")
                return None
    return None


def label_items(
    items: list[LabelItem],
    models: list[ModelSpec],
    adapter: LabelingAdapter,
    output_path: Path,
    checkpoint_every: int = 1,
    resume: bool = False,
) -> list[dict]:
    """Label items with multiple models, saving checkpoints.

    Args:
        items: Items to label.
        models: Model specifications.
        adapter: Domain-specific adapter.
        output_path: Where to write checkpoint/final JSON.
        checkpoint_every: Save after this many items.
        resume: If True, skip items already in output_path.

    Returns:
        List of per-item result dicts with model_scores and item metadata.
    """
    rate_limiter = _RateLimiter(models)

    existing_keys: set[str] = set()
    existing_results: list[dict] = []
    if resume and output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
        for entry in data.get("results", []):
            composite = f"{entry['case_index']}:{entry['key']}"
            existing_keys.add(composite)
            existing_results.append(entry)
        print(f"Resuming: {len(existing_keys)} items already labeled")

    results = list(existing_results)
    labeled_count = len(existing_results)

    for i, item in enumerate(items):
        item_key = adapter.item_key(item)
        if item_key in existing_keys:
            continue

        prompt = adapter.format_prompt(item)

        scores: dict[str, int | str | None] = {}
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(_call_model, m, prompt, adapter, rate_limiter): m
                for m in models
            }
            for future in as_completed(futures):
                m = futures[future]
                scores[m.name] = future.result()

        labeled_count += 1
        result_entry = {
            "case_index": item.case_index,
            "key": item.key,
            "item_type": item.item_type,
            "model_scores": scores,
        }
        results.append(result_entry)

        _short = lambda m: m.split("/")[-1] if "/" in m else m.split("-")[-1]
        score_str = " ".join(f"{_short(m)}={s}" for m, s in scores.items())
        print(f"  [{labeled_count}/{len(items)}] {score_str} | "
              f"{item.context.get('situation', '')[:70]}...")

        if labeled_count % checkpoint_every == 0:
            _save_checkpoint(output_path, models, results)

    _save_checkpoint(output_path, models, results)
    print(f"\nLabeled {labeled_count} items total. Wrote: {output_path}")
    return results


def _save_checkpoint(output_path: Path, models: list[ModelSpec], results: list[dict]):
    """Write current results to disk."""
    output = {
        "models": [m.name for m in models],
        "total_items": len(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
