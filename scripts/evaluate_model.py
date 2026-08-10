"""CyberGuard-ID — Model Evaluation Script.

Loads the trained model and evaluates it on the test set with detailed metrics.
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.core.config import load_config
from src.core.logging_config import setup_logging
from src.services.preprocessing import TextPreprocessor


def evaluate_model() -> None:
    """Evaluate the trained model on the test set."""
    config = load_config()
    setup_logging(log_level=config.log_level)

    model_path = config.model_path
    test_path = config.project_root / "data" / "processed" / "test.csv"
    eval_dir = config.project_root / "artifacts" / "evaluations"
    eval_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== CyberGuard-ID Model Evaluation ===\n")

    if not model_path.exists():
        print("[ERROR] Model not found. Run 'python run.py --train' first.")
        sys.exit(1)

    if not test_path.exists():
        print("[ERROR] Test data not found. Run 'python scripts/prepare_dataset.py' first.")
        sys.exit(1)

    # Load model
    print("Loading model...")
    pipeline = joblib.load(model_path)
    classes = list(pipeline.classes_)
    print(f"  Classes: {classes}")

    # Load test data
    test_df = pd.read_csv(test_path)
    print(f"  Test samples: {len(test_df)}")

    # Preprocess
    preprocessor = TextPreprocessor(config.slang_dict)
    test_df["processed_text"] = preprocessor.batch_preprocess(test_df["text"].tolist())

    X_test = test_df["processed_text"].values
    y_test = test_df["label"].values

    # Predict
    print("\nRunning predictions...")
    start = time.time()
    y_pred = pipeline.predict(X_test)
    inf_time = time.time() - start

    # Probability predictions
    y_proba = pipeline.predict_proba(X_test)
    avg_confidence = float(np.mean(np.max(y_proba, axis=1)))

    # Metrics
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    inf_per_100 = float(inf_time / len(X_test) * 100)

    print(f"\n{'=' * 50}")
    print(f"  Accuracy:            {accuracy:.4f}")
    print(f"  Macro Precision:     {macro_prec:.4f}")
    print(f"  Macro Recall:        {macro_rec:.4f}")
    print(f"  Macro F1:            {macro_f1:.4f}")
    print(f"  Weighted F1:         {weighted_f1:.4f}")
    print(f"  Avg Confidence:      {avg_confidence:.4f}")
    print(f"  Inference/100:       {inf_per_100:.4f}s")
    print(f"{'=' * 50}")

    # Classification report
    print("\nPer-class results:")
    report_str = classification_report(y_test, y_pred, zero_division=0)
    print(report_str)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    print("Confusion Matrix:")
    print(f"{'':>22}", end="")
    for c in classes:
        print(f"{c[:8]:>10}", end="")
    print()
    for i, c in enumerate(classes):
        print(f"  {c:>20}", end="")
        for j in range(len(classes)):
            print(f"{cm[i][j]:>10}", end="")
        print()

    # Per-class metrics dict
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    per_class = {}
    high_risk_labels = {"hate_speech", "sexual_harassment", "threat_intimidation"}

    for label in classes:
        if label in report_dict:
            per_class[label] = {
                "precision": round(report_dict[label]["precision"], 4),
                "recall": round(report_dict[label]["recall"], 4),
                "f1": round(report_dict[label]["f1-score"], 4),
                "support": int(report_dict[label]["support"]),
            }

    # High-risk recall
    high_risk_recalls = []
    for label in high_risk_labels:
        if label in per_class:
            high_risk_recalls.append(per_class[label]["recall"])
    avg_high_risk_recall = float(np.mean(high_risk_recalls)) if high_risk_recalls else 0.0
    print(f"\nAvg High-Risk Recall: {avg_high_risk_recall:.4f}")

    # Save evaluation results
    results = {
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "test_samples": len(test_df),
        "metrics": {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "avg_confidence": round(avg_confidence, 4),
            "inference_time_per_100": round(inf_per_100, 4),
            "avg_high_risk_recall": round(avg_high_risk_recall, 4),
        },
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "classes": classes,
    }

    results_path = eval_dir / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save report text
    report_path = eval_dir / "classification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"CyberGuard-ID Model Evaluation\n{'=' * 40}\n\n")
        f.write(f"Test samples: {len(test_df)}\n\n")
        f.write(report_str)
        f.write(f"\nAccuracy: {accuracy:.4f}\n")
        f.write(f"Macro F1: {macro_f1:.4f}\n")
        f.write(f"Weighted F1: {weighted_f1:.4f}\n")
        f.write(f"Avg High-Risk Recall: {avg_high_risk_recall:.4f}\n")

    print(f"\n[OK] Results saved to {results_path}")
    print(f"[OK] Report saved to {report_path}")

    # Warning for small datasets
    if len(test_df) < 50:
        print("\n[WARN] PERINGATAN: Test set sangat kecil (<50 sampel).")
        print("  Metrik di atas TIDAK mewakili performa sesungguhnya.")


if __name__ == "__main__":
    evaluate_model()
