"""CyberGuard-ID — Model Evaluation Script.

Mengevaluasi model IndoBERT (ONNX quantized) pada test set dengan metrik
klasifikasi lengkap: accuracy, macro F1, per-class precision/recall, dan
confusion matrix. Hasil disimpan ke artifacts/evaluations/.

Usage:
    python scripts/evaluate_model.py

Prerequisites:
    - Model ONNX harus tersedia di: models/indobert_cyberguard/model_quantized.onnx
    - Test data harus tersedia di:  data/processed/test.csv
      Format CSV: kolom 'text' (string) dan 'label' (salah satu dari:
      normal, abusive, hate_speech_weak, hate_speech_moderate, hate_speech_strong)
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Konfigurasi encoding UTF-8 untuk Windows agar output Bahasa Indonesia tampil benar
if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

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
from src.services.indo_bert_classifier import IndoBERTClassifier

# Label mapping IndoBERT (sesuai urutan class di model)
LABEL_NAMES = [
    "normal",
    "abusive",
    "hate_speech_weak",
    "hate_speech_moderate",
    "hate_speech_strong",
]

# Subset label yang dianggap high-risk untuk metrik khusus
HIGH_RISK_LABELS = {"hate_speech_moderate", "hate_speech_strong"}


def evaluate_model() -> None:
    """Evaluasi model IndoBERT ONNX pada test set dan simpan hasil ke artifacts."""
    config = load_config()
    setup_logging(log_level=config.log_level)

    model_dir = PROJECT_ROOT / "models" / "indobert_cyberguard"
    test_path = PROJECT_ROOT / "data" / "processed" / "test.csv"
    eval_dir = PROJECT_ROOT / "artifacts" / "evaluations"
    eval_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  CyberGuard-ID — Model Evaluation (IndoBERT ONNX)")
    print("=" * 60 + "\n")

    # --- Validasi file model ---
    onnx_path = model_dir / "model_quantized.onnx"
    if not onnx_path.exists():
        print(f"[ERROR] ONNX model tidak ditemukan: {onnx_path}")
        print("        Jalankan: python scripts/convert_to_onnx.py")
        sys.exit(1)

    # --- Validasi test data ---
    if not test_path.exists():
        print(f"[ERROR] Test data tidak ditemukan: {test_path}")
        print("        Pastikan data/processed/test.csv sudah tersedia.")
        print("        Lihat data/processed/README.md untuk format yang dibutuhkan.")
        sys.exit(1)

    # --- Load test data ---
    test_df = pd.read_csv(test_path).dropna(subset=["text", "label"])
    print(f"[OK] Test samples: {len(test_df)}")

    # Validasi label yang ada di test set
    unknown_labels = set(test_df["label"].unique()) - set(LABEL_NAMES)
    if unknown_labels:
        print(f"[WARN] Label tidak dikenal di test set: {unknown_labels}")
        print(f"       Label yang valid: {LABEL_NAMES}")

    # --- Preprocessing ---
    print("[INFO] Preprocessing teks...")
    preprocessor = TextPreprocessor(config.slang_dict)
    test_df["processed_text"] = preprocessor.batch_preprocess(test_df["text"].tolist())

    X_test = test_df["processed_text"].tolist()
    y_test = test_df["label"].tolist()

    # --- Load model IndoBERT ONNX ---
    print(f"[INFO] Memuat model ONNX dari {onnx_path.name} ({onnx_path.stat().st_size / 1e6:.1f} MB)...")
    classifier = IndoBERTClassifier(local_model_path=str(model_dir))
    classifier.load()

    # --- Prediksi ---
    print("[INFO] Menjalankan prediksi pada test set...")
    start_time = time.time()
    probas = classifier.predict_proba(X_test)
    inference_time = time.time() - start_time

    # Konversi probabilitas ke label prediksi
    pred_indices = np.argmax(probas, axis=1)
    y_pred = [LABEL_NAMES[i] for i in pred_indices]
    avg_confidence = float(np.mean(np.max(probas, axis=1)))

    # --- Hitung Metrik ---
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0, labels=LABEL_NAMES))
    macro_rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0, labels=LABEL_NAMES))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0, labels=LABEL_NAMES))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0, labels=LABEL_NAMES))
    inf_per_100 = float(inference_time / len(X_test) * 100) if X_test else 0.0

    # --- Tampilkan Ringkasan Metrik ---
    print(f"\n{'=' * 60}")
    print(f"  Accuracy:            {accuracy:.4f}  ({accuracy * 100:.2f}%)")
    print(f"  Macro Precision:     {macro_prec:.4f}")
    print(f"  Macro Recall:        {macro_rec:.4f}")
    print(f"  Macro F1-Score:      {macro_f1:.4f}")
    print(f"  Weighted F1-Score:   {weighted_f1:.4f}")
    print(f"  Avg Confidence:      {avg_confidence:.4f}  ({avg_confidence * 100:.1f}%)")
    print(f"  Waktu Inferensi:     {inference_time:.2f}s total ({inf_per_100:.4f}s / 100 sampel)")
    print(f"{'=' * 60}")

    # --- Classification Report per kelas ---
    print("\nPer-Class Classification Report:")
    print("-" * 60)
    report_str = classification_report(
        y_test, y_pred,
        labels=LABEL_NAMES,
        zero_division=0,
        digits=4,
    )
    print(report_str)

    # --- Confusion Matrix ---
    cm = confusion_matrix(y_test, y_pred, labels=LABEL_NAMES)
    print("Confusion Matrix:")
    print(f"{'':>24}", end="")
    for lbl in LABEL_NAMES:
        print(f"{lbl[:8]:>10}", end="")
    print()
    for i, lbl in enumerate(LABEL_NAMES):
        print(f"  {lbl:>22}", end="")
        for j in range(len(LABEL_NAMES)):
            print(f"{cm[i][j]:>10}", end="")
        print()

    # --- Per-class dict untuk JSON ---
    report_dict = classification_report(
        y_test, y_pred,
        labels=LABEL_NAMES,
        output_dict=True,
        zero_division=0,
    )
    per_class: dict[str, dict] = {}
    for label in LABEL_NAMES:
        if label in report_dict:
            per_class[label] = {
                "precision": round(report_dict[label]["precision"], 4),
                "recall": round(report_dict[label]["recall"], 4),
                "f1": round(report_dict[label]["f1-score"], 4),
                "support": int(report_dict[label]["support"]),
            }

    # --- High-Risk Recall ---
    high_risk_recalls = [
        per_class[lbl]["recall"]
        for lbl in HIGH_RISK_LABELS
        if lbl in per_class and per_class[lbl]["support"] > 0
    ]
    avg_high_risk_recall = float(np.mean(high_risk_recalls)) if high_risk_recalls else 0.0
    print(f"\nHigh-Risk Recall (C3+C4 avg): {avg_high_risk_recall:.4f}  ({avg_high_risk_recall * 100:.2f}%)")

    # --- Simpan Hasil JSON ---
    results = {
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "model": {
            "path": str(onnx_path),
            "size_mb": round(onnx_path.stat().st_size / 1e6, 1),
            "type": "IndoBERT ONNX int8 quantized",
            "base_model": "indobenchmark/indobert-base-p1",
        },
        "dataset": {
            "test_samples": len(test_df),
            "class_distribution": test_df["label"].value_counts().to_dict(),
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "avg_confidence": round(avg_confidence, 4),
            "inference_time_total_s": round(inference_time, 4),
            "inference_time_per_100_s": round(inf_per_100, 4),
            "avg_high_risk_recall": round(avg_high_risk_recall, 4),
        },
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "label_names": LABEL_NAMES,
    }

    results_path = eval_dir / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # --- Simpan Classification Report teks ---
    report_path = eval_dir / "classification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("CyberGuard-ID — Model Evaluation Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Model   : IndoBERT ONNX int8 quantized\n")
        f.write(f"Base    : indobenchmark/indobert-base-p1\n")
        f.write(f"File    : {onnx_path.name} ({onnx_path.stat().st_size / 1e6:.1f} MB)\n")
        f.write(f"Date    : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Samples : {len(test_df)}\n\n")
        f.write("Summary Metrics\n")
        f.write("-" * 40 + "\n")
        f.write(f"Accuracy:          {accuracy:.4f}  ({accuracy * 100:.2f}%)\n")
        f.write(f"Macro Precision:   {macro_prec:.4f}\n")
        f.write(f"Macro Recall:      {macro_rec:.4f}\n")
        f.write(f"Macro F1-Score:    {macro_f1:.4f}\n")
        f.write(f"Weighted F1-Score: {weighted_f1:.4f}\n")
        f.write(f"Avg Confidence:    {avg_confidence:.4f}  ({avg_confidence * 100:.1f}%)\n")
        f.write(f"High-Risk Recall:  {avg_high_risk_recall:.4f}  ({avg_high_risk_recall * 100:.2f}%)\n\n")
        f.write("Per-Class Report\n")
        f.write("-" * 40 + "\n")
        f.write(report_str)

    print(f"\n[OK] Hasil evaluasi disimpan ke: {results_path}")
    print(f"[OK] Classification report: {report_path}")

    # --- Peringatan jika dataset kecil ---
    if len(test_df) < 50:
        print("\n[WARN] PERINGATAN: Test set sangat kecil (<50 sampel).")
        print("  Metrik di atas TIDAK mewakili performa sesungguhnya di dunia nyata.")
        print("  Disarankan minimal 200+ sampel per kelas untuk evaluasi yang representatif.")

    print(f"\n{'=' * 60}")
    print("  Evaluasi selesai.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    evaluate_model()
