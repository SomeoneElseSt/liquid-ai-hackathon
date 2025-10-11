from typing import cast
import os

from datasets import Dataset
from transformers import PreTrainedTokenizerBase
from trl import SFTConfig, SFTTrainer
from ray.train.huggingface.transformers import prepare_trainer

from leap_finetune.utils.load_models import load_model
from leap_finetune.utils.peft import apply_peft_to_model, merge_and_save_peft_model


def sft_run(training_config: dict) -> None:
    """SFT training loop for Ray Train"""

    train_dataset, test_dataset = cast(
        tuple[Dataset, Dataset], training_config.get("dataset")
    )

    train_config_filtered = {
        k: v
        for k, v in training_config.get("train_config").items()
        if k != "training_type"
    }
    # Configure W&B reporting if enabled via config
    job_name = training_config.get("job_name", "leap-ft-run")
    wandb_logging = bool(training_config.get("train_config", {}).get("wandb_logging", False))
    if wandb_logging:
        # If no API key set, run offline to avoid failures on workers
        if not os.environ.get("WANDB_API_KEY"):
            os.environ.setdefault("WANDB_MODE", "offline")
        # Default project if not provided by user
        os.environ.setdefault("WANDB_PROJECT", "leap-finetune")

    training_args = SFTConfig(
        report_to=["wandb"] if wandb_logging else [],
        run_name=job_name,
        **train_config_filtered,
    )
    peft_config = training_config.get("peft_config")

    model, tokenizer = load_model(training_config.get("model_name"))

    if peft_config:
        model = apply_peft_to_model(model, peft_config)

    # Initialize trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        processing_class=cast(PreTrainedTokenizerBase, tokenizer),
    )

    # Start training
    trainer = prepare_trainer(trainer)
    trainer.train()

    # Save PEFT model if applicable
    if peft_config:
        merge_and_save_peft_model(model, tokenizer, training_args.output_dir)
