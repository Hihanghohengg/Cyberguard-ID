"""CyberGuard-ID — IndoBERT Fine-Tuning Script.

Fine-tunes `indobenchmark/indobert-base-p1` (IndoBERT) pada dataset komentar
YouTube berbahasa Indonesia untuk klasifikasi 5 kelas (C0–C4).

Taksonomi Label:
  C0  normal               — Komentar biasa/positif
  C1  abusive              — Bahasa kasar tanpa target
  C2  hate_speech_weak     — Ujaran kebencian ringan
  C3  hate_speech_moderate — Ujaran kebencian sedang
  C4  hate_speech_strong   — Ujaran kebencian ekstrem/ancaman

Hyperparameter:
  Model           : indobenchmark/indobert-base-p1
  Max seq length  : 128 token
  Batch size      : 16
  Learning rate   : 2e-5
  Epochs          : 3
  Weight decay    : 0.01
  Best metric     : macro F1

Prerequisites:
  pip install -r requirements-train.txt

Usage:
  python scripts/train_bert.py

Output:
  models/indobert_cyberguard/   — Fine-tuned model + tokenizer
  models/model_metadata.json    — Metadata training & evaluation metrics
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
from torch import nn
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("train_bert")

# --- Path Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models" / "indobert_cyberguard"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# --- Hyperparameter Configuration ---
MODEL_NAME = "indobenchmark/indobert-base-p1"
MAX_SEQ_LENGTH = 128
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
RANDOM_SEED = 42

# --- Label Mapping (sesuai taksonomi CyberGuard-ID) ---
LABEL2ID = {
    "normal": 0,
    "abusive": 1,
    "hate_speech_weak": 2,
    "hate_speech_moderate": 3,
    "hate_speech_strong": 4,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
LABEL_NAMES = list(LABEL2ID.keys())


def compute_metrics(pred) -> dict:
    """Hitung metrik evaluasi selama training.

    Args:
        pred: Objek EvalPrediction dari HuggingFace Trainer.

    Returns:
        Dict berisi accuracy dan macro F1.
    """
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)

    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
    }


def validate_dataset(df: pd.DataFrame, name: str) -> None:
    """Validasi DataFrame sebelum training.

    Args:
        df: DataFrame yang akan divalidasi.
        name: Nama dataset untuk pesan error.

    Raises:
        ValueError: Jika format atau label tidak valid.
    """
    required_cols = {"text", "label"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"[{name}] Kolom yang dibutuhkan tidak ditemukan: {missing}")

    unknown_labels = set(df["label"].unique()) - set(LABEL2ID.keys())
    if unknown_labels:
        raise ValueError(
            f"[{name}] Label tidak dikenal: {unknown_labels}. "
            f"Label yang valid: {list(LABEL2ID.keys())}"
        )

    if len(df) == 0:
        raise ValueError(f"[{name}] Dataset kosong.")

    logger.info(
        "[%s] %d sampel | Distribusi: %s",
        name,
        len(df),
        df["label"].value_counts().to_dict(),
    )


class ClassWeightedTrainer(Trainer):
    """Custom Trainer untuk menangani class imbalance."""
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        if self.class_weights is not None:
            loss_fct = nn.CrossEntropyLoss(weight=self.class_weights.to(model.device))
            loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        else:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def main() -> None:
    """Jalankan fine-tuning IndoBERT."""
    logger.info("=" * 60)
    logger.info("  CyberGuard-ID — IndoBERT Fine-Tuning")
    logger.info("  Model : %s", MODEL_NAME)
    logger.info("  Epoch : %d | LR: %g | Batch: %d | MaxLen: %d", EPOCHS, LEARNING_RATE, BATCH_SIZE, MAX_SEQ_LENGTH)
    logger.info("=" * 60)

    # --- Validasi ketersediaan data ---
    train_aug_path = PROCESSED_DIR / "train_augmented.csv"
    train_orig_path = PROCESSED_DIR / "train.csv"
    val_path = PROCESSED_DIR / "val.csv"

    if train_aug_path.exists():
        logger.info("Ditemukan dataset augmented: %s", train_aug_path)
        train_path = train_aug_path
    elif train_orig_path.exists():
        logger.info("Dataset augmented tidak ditemukan, menggunakan: %s", train_orig_path)
        train_path = train_orig_path
    else:
        logger.error("File training tidak ditemukan: %s", train_orig_path)
        logger.error("Buat split dataset terlebih dahulu. Lihat: data/processed/README.md")
        raise FileNotFoundError(f"Dataset training tidak ditemukan: {train_orig_path}")

    if not val_path.exists():
        logger.error("File validasi tidak ditemukan: %s", val_path)
        raise FileNotFoundError(f"Dataset validasi tidak ditemukan: {val_path}")

    # --- Load & validasi dataset ---
    logger.info("Memuat dataset...")
    train_df = pd.read_csv(train_path).dropna(subset=["text", "label"])
    val_df = pd.read_csv(val_path).dropna(subset=["text", "label"])

    validate_dataset(train_df, "train")
    validate_dataset(val_df, "val")

    # Map label string ke integer ID
    train_df["label"] = train_df["label"].map(LABEL2ID)
    val_df["label"] = val_df["label"].map(LABEL2ID)

    train_dataset = Dataset.from_pandas(train_df[["text", "label"]])
    val_dataset = Dataset.from_pandas(val_df[["text", "label"]])

    # --- Compute Class Weights ---
    logger.info("Menghitung class weights untuk class imbalance...")
    labels_array = train_df["label"].values
    class_weights_array = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(labels_array),
        y=labels_array
    )
    class_weights_tensor = torch.tensor(class_weights_array, dtype=torch.float32)
    logger.info("Class weights: %s", class_weights_tensor.tolist())

    # --- Load tokenizer ---
    logger.info("Memuat tokenizer %s...", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding=False,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
        )

    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # --- Load model ---
    logger.info("Memuat model dasar %s...", MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,  # Mengabaikan perbedaan ukuran classification head
    )

    # Log parameter model
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Total parameter   : %s", f"{total_params:,}")
    logger.info("Parameter trainable: %s", f"{trainable_params:,}")
    logger.info("Device            : %s", "CUDA" if torch.cuda.is_available() else "CPU")

    # --- Training arguments ---
    training_args = TrainingArguments(
        output_dir=str(MODEL_DIR / "checkpoints"),
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=WEIGHT_DECAY,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_dir=str(MODEL_DIR / "logs"),
        logging_steps=50,
        seed=RANDOM_SEED,
        report_to="none",  # Nonaktifkan wandb/tensorboard agar tidak membutuhkan login
    )

    # --- Training ---
    trainer = ClassWeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights_tensor,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    logger.info("Memulai fine-tuning...")
    train_result = trainer.train()
    logger.info("Training selesai dalam %.1f menit.", train_result.metrics.get("train_runtime", 0) / 60)

    # --- Evaluasi final ---
    logger.info("Evaluasi model terbaik pada validation set...")
    eval_results = trainer.evaluate()
    logger.info("Eval accuracy  : %.4f", eval_results.get("eval_accuracy", 0))
    logger.info("Eval macro F1  : %.4f", eval_results.get("eval_macro_f1", 0))

    # --- Simpan model & tokenizer ---
    logger.info("Menyimpan model ke %s...", MODEL_DIR)
    trainer.save_model(str(MODEL_DIR))
    tokenizer.save_pretrained(str(MODEL_DIR))

    # --- Simpan metadata kaya ---
    # Ambil per-class metrics dari validation set
    val_preds = trainer.predict(tokenized_val)
    y_pred = val_preds.predictions.argmax(-1)
    y_true = val_preds.label_ids
    report_dict = classification_report(
        y_true, y_pred,
        target_names=LABEL_NAMES,
        output_dict=True,
        zero_division=0,
    )
    per_class = {
        lbl: {
            "precision": round(report_dict[lbl]["precision"], 4),
            "recall": round(report_dict[lbl]["recall"], 4),
            "f1": round(report_dict[lbl]["f1-score"], 4),
            "support": int(report_dict[lbl]["support"]),
        }
        for lbl in LABEL_NAMES
        if lbl in report_dict
    }
    
    # Hitung Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(LABEL2ID.values()))

    metadata = {
        "algorithm": "IndoBERT",
        "model_name": MODEL_NAME,
        "model_version": "1.0.0",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "classes": LABEL_NAMES,
        "label2id": LABEL2ID,
        "hyperparameters": {
            "max_sequence_length": MAX_SEQ_LENGTH,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            "weight_decay": WEIGHT_DECAY,
            "random_seed": RANDOM_SEED,
        },
        "dataset": {
            "train_samples": len(train_df),
            "val_samples": len(val_df),
        },
        "eval_metrics": {
            "eval_loss": round(eval_results.get("eval_loss", 0), 6),
            "eval_accuracy": round(eval_results.get("eval_accuracy", 0), 6),
            "eval_macro_f1": round(eval_results.get("eval_macro_f1", 0), 6),
            "eval_runtime": eval_results.get("eval_runtime", 0),
            "eval_samples_per_second": eval_results.get("eval_samples_per_second", 0),
        },
        "per_class_metrics": per_class,
        "confusion_matrix": cm.tolist(),
    }

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("  Fine-tuning selesai!")
    logger.info("  Model disimpan di : %s", MODEL_DIR)
    logger.info("  Metadata          : %s", METADATA_PATH)
    logger.info("  Accuracy          : %.4f", eval_results.get("eval_accuracy", 0))
    logger.info("  Macro F1          : %.4f", eval_results.get("eval_macro_f1", 0))
    logger.info("=" * 60)
    logger.info("Langkah berikutnya: python scripts/convert_to_onnx.py")


if __name__ == "__main__":
    main()
