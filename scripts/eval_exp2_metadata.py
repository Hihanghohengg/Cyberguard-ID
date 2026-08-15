import json
import os
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "models" / "experiment_2_focal"
CHECKPOINT_DIR = MODEL_DIR / "checkpoints" / "checkpoint-1731"
VAL_CSV = PROJECT_ROOT / "data" / "processed" / "val.csv"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

print(f"Model Path: {MODEL_DIR}")
print(f"Validation Data Path: {VAL_CSV}")

LABEL2ID = {
    "normal": 0,
    "abusive": 1,
    "hate_speech_weak": 2,
    "hate_speech_moderate": 3,
    "hate_speech_strong": 4,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
LABEL_NAMES = list(LABEL2ID.keys())

print("Loading Validation Data...")
val_df = pd.read_csv(VAL_CSV).dropna(subset=["text", "label"])
val_df["label_id"] = val_df["label"].map(LABEL2ID)

print("Loading Tokenizer and Model...")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
model.eval()

print("Tokenizing...")
def tokenize(texts):
    return tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")

inputs = tokenize(val_df["text"].tolist())
labels = torch.tensor(val_df["label_id"].tolist())

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

batch_size = 32
all_preds = []

print(f"Running Inference on {device}...", flush=True)
with torch.no_grad():
    for i in range(0, len(inputs["input_ids"]), batch_size):
        if i % 320 == 0:
            print(f"Processing batch {i}...", flush=True)
        batch_input_ids = inputs["input_ids"][i:i+batch_size].to(device)
        batch_attention_mask = inputs["attention_mask"][i:i+batch_size].to(device)
        outputs = model(input_ids=batch_input_ids, attention_mask=batch_attention_mask)
        preds = outputs.logits.argmax(dim=-1).cpu().numpy()
        all_preds.extend(preds)

y_pred = np.array(all_preds)
y_true = labels.numpy()

print("Calculating Metrics...")
acc = accuracy_score(y_true, y_pred)
macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

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

cm = confusion_matrix(y_true, y_pred, labels=list(LABEL2ID.values()))

# Extract history from trainer_state.json
trainer_state_path = CHECKPOINT_DIR / "trainer_state.json"
log_history = []
best_metric = None
best_checkpoint = None

if trainer_state_path.exists():
    with open(trainer_state_path, "r") as f:
        trainer_state = json.load(f)
    best_metric = trainer_state.get("best_metric")
    best_checkpoint = trainer_state.get("best_model_checkpoint")
    
    for log in trainer_state.get("log_history", []):
        if "eval_accuracy" in log or "eval_loss" in log:
            log_history.append({
                "epoch": log.get("epoch"),
                "eval_loss": log.get("eval_loss"),
                "eval_accuracy": log.get("eval_accuracy"),
                "eval_macro_f1": log.get("eval_macro_f1"),
                "step": log.get("step")
            })

metadata = {
    "algorithm": "IndoBERT Focal Loss",
    "model_name": "indobenchmark/indobert-base-p1",
    "classes": LABEL_NAMES,
    "eval_metrics": {
        "eval_accuracy": round(acc, 6),
        "eval_macro_f1": round(macro_f1, 6),
    },
    "per_class_metrics": per_class,
    "confusion_matrix": cm.tolist(),
    "best_checkpoint": best_checkpoint,
    "best_metric_from_training": best_metric,
    "training_history": log_history
}

print(f"Saving Metadata to {METADATA_PATH}...")
with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=4, ensure_ascii=False)

report_path = MODEL_DIR / "classification_report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_dict, f, indent=4, ensure_ascii=False)

cm_path = MODEL_DIR / "confusion_matrix.png"
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES)
plt.title("Confusion Matrix - Experiment 2 (Focal Loss)")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.savefig(cm_path)
plt.close()

print("Evaluation Complete!")
print(f"Accuracy: {acc:.4f}, Macro F1: {macro_f1:.4f}")
