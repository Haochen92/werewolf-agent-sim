"""Modal (remote L4 GPU) execution backend — the only training backend.

Training always runs on Modal; local machines are inference-only (see
``evaluation.training.evaluator``). The flow keeps disk I/O on the launching side
and ships a plain JSON payload to the GPU container:

    local entrypoint:  adapter.read_raw()  ->  ship (adapter_name, config, raw)
    remote container:  engine.train(...)   ->  write manifest  ->  vol.commit()

Run it:

    poetry run modal run evaluation/training/runner/modal_runner.py \
        --adapter reranker --run-name reranker_v5 --epochs 20

    poetry run modal run evaluation/training/runner/modal_runner.py \
        --adapter dedup --run-name ce_minilm_dedup_v2 --epochs 10
"""
from __future__ import annotations

import json

import modal

MINUTES = 60

app = modal.App("cross-encoder-training")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "datasets>=3.0",
        "accelerate>=1.1.0",
        "huggingface_hub",
        "pydantic>=2.0",
        "python-dotenv",
        "numpy",
    )
    # Mount the repo's evaluation package so the container can import the
    # engine + adapters. Only the light evaluation.training.* chain is imported
    # at runtime; the rest of the package is never executed.
    .add_local_python_source("evaluation")
)

# Single shared volume for all runs through this module. Existing per-experiment
# volumes (cross-encoder-reranker-output, cross-encoder-finetune-output) still
# hold the historical models.
vol = modal.Volume.from_name("cross-encoder-training-output", create_if_missing=True)


@app.function(
    image=image,
    gpu="L4",
    timeout=30 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def _train_remote(adapter_name: str, config_json: str, raw: dict) -> dict:
    from evaluation.training import engine
    from evaluation.training.adapters import get_adapter
    from evaluation.training.config import TrainConfig
    from evaluation.training.manifest import write_manifest

    adapter = get_adapter(adapter_name)
    config = TrainConfig.model_validate_json(config_json)

    result = engine.train(adapter, config, raw)
    manifest = write_manifest(config, adapter_name, raw, result, config.output_dir)
    result["manifest"] = manifest

    vol.commit()
    print(f"\nDownload with:")
    print(f"  modal volume get cross-encoder-training-output {config.run_name}/ "
          f"./models/cross_encoder/{config.run_name}/")
    return result


@app.local_entrypoint()
def main(
    adapter: str = "reranker",
    run_name: str = "run1",
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-5,
    data_dir: str = "",
):
    from evaluation.training.adapters import get_adapter
    from evaluation.training.config import TrainConfig

    # read_raw runs locally (plain disk reads, no ML deps) so the GPU container
    # receives a ready-to-train payload. data_dir overrides the adapter's default
    # split location (e.g. the situation+action variant for the v5 ablation).
    adapter_kwargs = {"data_dir": data_dir} if data_dir else {}
    adapter_obj = get_adapter(adapter, **adapter_kwargs)
    raw = adapter_obj.read_raw()

    config = TrainConfig(
        base_model=base_model,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        run_name=run_name,
        output_dir=f"/output/{run_name}",  # Modal volume mount point
    )

    print(f"Launching '{adapter}' training on Modal: run={run_name} "
          f"base={base_model} epochs={epochs}")
    result = _train_remote.remote(adapter, config.model_dump_json(), raw)

    print("\n=== Results ===")
    print(json.dumps(result.get("metrics", {}), indent=2))
