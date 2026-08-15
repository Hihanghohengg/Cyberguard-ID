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

# Configuration
MODEL_DIR = Path("models/revision_v2")
CHECKPOINT_DIR = MODEL_DIR / "checkpoints"
EVAL_OUT_DIR = MODEL_DIR / "evaluation"
EVAL_OUT_DIR.mkdir(parents=True, exist_ok=True)

TEST_CSV = Path("data/processed/val.csv")
METADATA_PATH = CHECKPOINT_DIR / "final_test_metadata.json"

print(f"Model Path: {CHECKPOINT_DIR}")
print(f"Test Data Path: {TEST_CSV}")

LABEL2ID = {
    "normal": 0,
    "abusive": 1,
    "hate_speech_weak": 2,
    "hate_speech_moderate": 3,
    "hate_speech_strong": 4,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
LABEL_NAMES = list(LABEL2ID.keys())

print("Loading Test Data...")
test_df = pd.read_csv(TEST_CSV).dropna(subset=["text", "label"])
test_df["label_id"] = test_df["label"].map(LABEL2ID)

print("Loading Tokenizer and Model...")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
model.eval()

print("Tokenizing...")
def tokenize(texts):
    return tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")

inputs = tokenize(test_df["text"].tolist())
labels = torch.tensor(test_df["label_id"].tolist())

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
trainer_state_path = CHECKPOINT_DIR / "checkpoint-1731" / "trainer_state.json"
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
    "algorithm": "IndoBERT Revision V2 Validation",
    "model_name": "indobenchmark/indobert-base-p1",
    "classes": LABEL_NAMES,
    "eval_metrics": {
        "test_accuracy": round(acc, 6),
        "test_macro_f1": round(macro_f1, 6),
    },
    "per_class_metrics": per_class,
    "confusion_matrix": cm.tolist(),
    "best_checkpoint": best_checkpoint,
    "training_history": log_history
}

print(f"Saving Metadata to {EVAL_OUT_DIR}...")
metadata_path = EVAL_OUT_DIR / "validation_metadata.json"
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=4)

report_path = EVAL_OUT_DIR / "validation_classification_report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_dict, f, indent=4, ensure_ascii=False)

cm_path = EVAL_OUT_DIR / "validation_confusion_matrix.png"
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES)
plt.title("Validation Evaluation V2 - Baseline")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.savefig(cm_path)
plt.close()

print("Final Test Evaluation Complete!")
print(f"Accuracy: {acc:.4f}, Macro F1: {macro_f1:.4f}")
