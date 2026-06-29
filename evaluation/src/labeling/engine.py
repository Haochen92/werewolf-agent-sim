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

from evaluation.src.labeling.base import LabelingAdapter, LabelItem
from evaluation.src.labeling.config import ModelSpec


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
    item: LabelItem,
    prompt: str,
    adapter: LabelingAdapter,
    rate_limiter: _RateLimiter,
) -> tuple[int | str | None, dict | None]:
    """Call a single model and parse via the adapter.

    Returns ``(label, detail)``. ``detail`` is the structured-output audit dict
    when the adapter opts into ``response_schema``; it is ``None`` on the
    free-text path.
    """
    from Agents.llm_factory import create_chat_model

    kwargs = {}
    if model.thinking_level:
        kwargs["thinking_level"] = model.thinking_level

    schema = adapter.response_schema(item)

    for attempt in range(model.max_retries):
        try:
            rate_limiter.wait(model.name)
            llm = create_chat_model(model.name, temperature=model.temperature, **kwargs)
            if schema is not None:
                result = llm.with_structured_output(schema).invoke(prompt)
                return adapter.parse_structured(item, result)
            response = llm.invoke(prompt)
            text = _extract_text(response.content)
            label = adapter.parse_response(text)
            if label is not None:
                return label, None
            print(f"    WARNING: {model.name} returned unparseable: {text!r}")
            return None, None
        except Exception as e:
            if attempt < model.max_retries - 1:
                is_rate_limit = "429" in str(e)
                wait = 10 if is_rate_limit else 2 ** (attempt + 1)
                print(f"    Retry {attempt + 1} for {model.name}: {e}")
                time.sleep(wait)
            else:
                print(f"    FAILED {model.name}: {e}")
                return None, None
    return None, None


def label_items(
    items: list[LabelItem],
    models: list[ModelSpec],
    adapter: LabelingAdapter,
    output_path: Path,
    checkpoint_every: int = 1,
    resume: bool = False,
    max_item_workers: int = 1,
) -> list[dict]:
    """Label items with multiple models, saving checkpoints.

    Args:
        items: Items to label.
        models: Model specifications.
        adapter: Domain-specific adapter.
        output_path: Where to write checkpoint/final JSON.
        checkpoint_every: Save after this many items.
        resume: If True, skip items already in output_path.
        max_item_workers: Process this many items concurrently (default 1 =
            original sequential behavior). >1 overlaps slow per-item calls; the
            per-model rate limiter still bounds each model's request rate, so
            high-latency models (e.g. a thinking model) stop gating throughput.

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
    todo = [it for it in items if adapter.item_key(it) not in existing_keys]
    total = len(existing_results) + len(todo)
    write_lock = threading.Lock()
    counter = {"n": len(existing_results)}

    def _process(item: LabelItem) -> dict:
        prompt = adapter.format_prompt(item)
        scores: dict[str, int | str | None] = {}
        details: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(_call_model, m, item, prompt, adapter, rate_limiter): m
                for m in models
            }
            for future in as_completed(futures):
                label, detail = future.result()
                name = futures[future].name
                scores[name] = label
                if detail is not None:
                    details[name] = detail

        entry = {
            "case_index": item.case_index,
            "key": item.key,
            "item_type": item.item_type,
            "model_scores": scores,
        }
        if details:
            entry["model_details"] = details
        _short = lambda m: m.split("/")[-1] if "/" in m else m.split("-")[-1]
        score_str = " ".join(f"{_short(m)}={s}" for m, s in scores.items())
        with write_lock:
            results.append(entry)
            counter["n"] += 1
            print(f"  [{counter['n']}/{total}] {score_str} | "
                  f"{item.context.get('situation', '')[:70]}...")
            if counter["n"] % checkpoint_every == 0:
                _save_checkpoint(output_path, models, results)
        return entry

    if max_item_workers <= 1:
        for item in todo:
            _process(item)
    else:
        with ThreadPoolExecutor(max_workers=max_item_workers) as pool:
            for fut in as_completed([pool.submit(_process, it) for it in todo]):
                fut.result()

    _save_checkpoint(output_path, models, results)
    print(f"\nLabeled {counter['n']} items total. Wrote: {output_path}")
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
