"""QLoRA fine-tuning for dedup classifier on Modal.

Trains small models (1-8B) with QLoRA adapters on the SFT dataset.

Setup:
    pip install modal
    modal token set          # authenticate
    modal secret create huggingface HF_TOKEN=hf_xxx

Usage:
    # Default (Qwen2.5-3B):
    modal run evidence/fine_tuning/dedup_classifier/train_modal.py

    # With weighted decision loss (10x weight on D/K token):
    modal run evidence/fine_tuning/dedup_classifier/train_modal.py \
        --base-model Qwen/Qwen3-4B-Instruct-2507 \
        --run-name qwen3_4b_weighted \
        --decision-weight 10

    # Custom config:
    modal run evidence/fine_tuning/dedup_classifier/train_modal.py \
        --base-model Qwen/Qwen3-4B-Instruct-2507 \
        --lora-rank 16 --epochs 3 --lr 2e-4
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

MODEL_1B = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_3B = "Qwen/Qwen2.5-3B-Instruct"

app = modal.App("dedup-classifier-finetune")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.6.0",
        "transformers>=4.51",
        "trl==0.16.1",
        "peft>=0.15",
        "accelerate>=1.4",
        "bitsandbytes>=0.45",
        "datasets>=3.0",
        "huggingface_hub",
    )
)

vol = modal.Volume.from_name("dedup-finetune-output", create_if_missing=True)


@app.function(
    image=image,
    gpu="L4",
    timeout=480 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def train(
    dataset_jsonl: str,
    base_model: str = MODEL_3B,
    lora_rank: int = 16,
    lora_alpha: int = 16,
    epochs: int = 3,
    lr: float = 2e-4,
    batch_size: int = 2,
    grad_accum: int = 4,
    max_seq_length: int = 4096,
    oversample_hard: int = 3,
    decision_weight: float = 1.0,
    run_name: str = "run_001",
):
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainerCallback
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig
    import torch
    import os

    class VolumeCommitCallback(TrainerCallback):
        def on_save(self, args, state, control, **kwargs):
            vol.commit()
            print(f"  Volume committed at step {state.global_step}")

    class WeightedDecisionTrainer(SFTTrainer):
        """SFTTrainer that upweights the decision token (D/K) in the loss."""

        def __init__(self, *args, decision_token_ids=None, weight=10.0, **kwargs):
            super().__init__(*args, **kwargs)
            self._decision_token_ids = decision_token_ids or set()
            self._decision_weight = weight

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits

            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()

            weights = torch.ones_like(shift_labels, dtype=shift_logits.dtype)
            for tid in self._decision_token_ids:
                weights[shift_labels == tid] = self._decision_weight

            loss_fct = torch.nn.CrossEntropyLoss(reduction="none", ignore_index=-100)
            flat_loss = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
            )
            loss = flat_loss.view(shift_labels.shape)

            valid = (shift_labels != -100).float()
            weighted_loss = (loss * weights * valid).sum() / (weights * valid).sum()

            return (weighted_loss, outputs) if return_outputs else weighted_loss

    os.environ["WANDB_DISABLED"] = "true"

    print(f"Loading base model: {base_model}")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_alpha,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=0,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.gradient_checkpointing_enable()

    print("Preparing dataset...")
    raw_examples = [json.loads(line) for line in dataset_jsonl.strip().split("\n")]

    oversampled = []
    for ex in raw_examples:
        difficulty = ex.get("metadata", {}).get("difficulty", 5)
        if difficulty <= 2:
            copies = oversample_hard
        else:
            copies = 1
        for _ in range(copies):
            oversampled.append(ex)

    print(f"  Raw examples: {len(raw_examples)}")
    print(f"  After oversampling (hard x{oversample_hard}): {len(oversampled)}")

    chat_examples = []
    for ex in oversampled:
        template_kwargs = dict(tokenize=False, add_generation_prompt=False)
        try:
            text = tokenizer.apply_chat_template(
                ex["messages"], **template_kwargs, enable_thinking=False,
            )
        except TypeError:
            text = tokenizer.apply_chat_template(
                ex["messages"], **template_kwargs,
            )
        chat_examples.append({"text": text})

    dataset = Dataset.from_list(chat_examples).shuffle(seed=42)

    decision_token_ids = set()
    if decision_weight > 1.0:
        d_ids = tokenizer.encode("DECISION: D", add_special_tokens=False)
        k_ids = tokenizer.encode("DECISION: K", add_special_tokens=False)
        decision_token_ids = {d_ids[-1], k_ids[-1]}
        print(f"  Decision weighting: {decision_weight}x on token IDs {decision_token_ids}")
        print(f"    'DECISION: D' tokens → {d_ids} → decision='{tokenizer.decode([d_ids[-1]])}'")
        print(f"    'DECISION: K' tokens → {k_ids} → decision='{tokenizer.decode([k_ids[-1]])}'")

    output_dir = f"/output/{run_name}"

    resume_from = None
    if os.path.exists(output_dir):
        checkpoints = sorted(
            [d for d in os.listdir(output_dir) if d.startswith("checkpoint-")],
            key=lambda x: int(x.split("-")[1]),
        )
        if checkpoints:
            resume_from = f"{output_dir}/{checkpoints[-1]}"
            print(f"  Resuming from checkpoint: {resume_from}")

    sft_config = SFTConfig(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=epochs,
        learning_rate=lr,
        warmup_steps=10,
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        optim="adamw_8bit",
        lr_scheduler_type="cosine",
        seed=42,
        max_seq_length=max_seq_length,
        dataset_text_field="text",
        packing=False,
    )

    trainer_cls = WeightedDecisionTrainer if decision_weight > 1.0 else SFTTrainer
    trainer_kwargs = {}
    if decision_weight > 1.0:
        trainer_kwargs["decision_token_ids"] = decision_token_ids
        trainer_kwargs["weight"] = decision_weight

    trainer = trainer_cls(
        model=model,
        train_dataset=dataset,
        args=sft_config,
        processing_class=tokenizer,
        callbacks=[VolumeCommitCallback()],
        **trainer_kwargs,
    )

    print("Starting training...")
    result = trainer.train(resume_from_checkpoint=resume_from)

    print(f"\nTraining complete!")
    print(f"  Loss: {result.training_loss:.4f}")
    print(f"  Steps: {result.global_step}")
    print(f"  Runtime: {result.metrics['train_runtime']:.0f}s")

    lora_path = f"{output_dir}/lora_adapter"
    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)
    print(f"  LoRA adapter saved to: {lora_path}")

    vol.commit()
    print(f"\nOutput committed to volume. Download with:")
    print(f"  modal volume get dedup-finetune-output {run_name}/ ./local_output/")

    return {
        "model": base_model,
        "loss": result.training_loss,
        "steps": result.global_step,
        "runtime_s": result.metrics["train_runtime"],
        "examples": len(raw_examples),
        "oversampled": len(oversampled),
        "lora_path": lora_path,
    }


@app.local_entrypoint()
def main(
    base_model: str = MODEL_3B,
    lora_rank: int = 16,
    epochs: int = 3,
    lr: float = 2e-4,
    oversample_hard: int = 3,
    decision_weight: float = 1.0,
    run_name: str = "",
    dataset_path: str = "evidence/fine_tuning/dedup_classifier/sft_dataset.jsonl",
    both: bool = False,
):
    from pathlib import Path

    data_path = Path(dataset_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    dataset_jsonl = data_path.read_text()
    n_examples = len([l for l in dataset_jsonl.strip().split("\n") if l.strip()])

    if both:
        models = [
            (MODEL_1B, "qwen1b_run1"),
            (MODEL_3B, "qwen3b_run1"),
        ]
    else:
        name = run_name or base_model.split("/")[-1].lower().replace("-", "_") + "_run1"
        models = [(base_model, name)]

    for model_name, rname in models:
        print(f"\n{'='*60}")
        print(f"Training: {model_name} → {rname}")
        print(f"  {n_examples} examples, rank={lora_rank}, epochs={epochs}, lr={lr}")
        print(f"  Hard case oversampling: {oversample_hard}x for difficulty 1-2")
        if decision_weight > 1.0:
            print(f"  Decision token weight: {decision_weight}x")
        print(f"{'='*60}\n")

        result = train.remote(
            dataset_jsonl=dataset_jsonl,
            base_model=model_name,
            lora_rank=lora_rank,
            epochs=epochs,
            lr=lr,
            oversample_hard=oversample_hard,
            decision_weight=decision_weight,
            run_name=rname,
        )

        print(f"\n=== {model_name} Results ===")
        for k, v in result.items():
            print(f"  {k}: {v}")
