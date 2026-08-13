#!/usr/bin/env python3
"""CyberGuard-ID — Konversi IndoBERT PyTorch → ONNX int8 Quantized.

Mengkonversi model fine-tuned IndoBERT dari format PyTorch (safetensors) ke
ONNX Runtime dengan quantisasi dinamis int8. Hasil konversi digunakan untuk
inferensi ringan tanpa membutuhkan PyTorch atau CUDA di runtime.

Alur Konversi:
  1. Load model safetensors dengan HuggingFace Optimum
  2. Export ke ONNX (full precision, ~440 MB)
  3. Terapkan int8 dynamic quantization (~110 MB, penghematan ~75%)
  4. Verifikasi output dengan 3 contoh komentar Indonesia
  5. Simpan model final & bersihkan file sementara

Keuntungan ONNX int8 vs PyTorch:
  - Ukuran model   : ~440 MB → ~110 MB (hemat ~75%)
  - RAM runtime    : hemat ~700 MB (tidak butuh PyTorch)
  - Inferensi CPU  : sebanding atau lebih cepat dari PyTorch (tergantung hardware)
  - Dependency     : hanya onnxruntime (tidak butuh torch, transformers)

Prerequisites:
  pip install -r requirements-train.txt
  # Model harus sudah di-fine-tune: python scripts/train_bert.py

Usage:
  python scripts/convert_to_onnx.py

Output:
  models/indobert_cyberguard/model_quantized.onnx
"""

import sys
import os
import shutil
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "models" / "indobert_cyberguard"
ONNX_DIR = MODEL_DIR / "onnx_export"
QUANTIZED_DIR = MODEL_DIR / "onnx_quantized"


def main():
    print("=" * 60)
    print("  IndoBERT -> ONNX Conversion (Optimum + int8 Quantization)")
    print("=" * 60)

    safetensors = MODEL_DIR / "model.safetensors"
    if not safetensors.exists():
        print(f"[ERROR] Model file not found: {safetensors}")
        sys.exit(1)

    print(f"[OK] Source: {safetensors.name} ({safetensors.stat().st_size / 1e6:.1f} MB)")

    # Step 1: Export using Optimum
    print("\n[STEP 1] Exporting to ONNX via Optimum...")
    from optimum.onnxruntime import ORTModelForSequenceClassification
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    ort_model = ORTModelForSequenceClassification.from_pretrained(
        str(MODEL_DIR),
        export=True,
    )
    ort_model.save_pretrained(str(ONNX_DIR))
    onnx_path = ONNX_DIR / "model.onnx"
    onnx_size = onnx_path.stat().st_size / 1e6
    print(f"[OK] ONNX exported: {onnx_size:.1f} MB")

    # Step 2: Quantize
    print("\n[STEP 2] Applying int8 dynamic quantization...")
    quantizer = ORTQuantizer.from_pretrained(str(ONNX_DIR))
    qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
    quantizer.quantize(save_dir=str(QUANTIZED_DIR), quantization_config=qconfig)
    q_onnx = QUANTIZED_DIR / "model_quantized.onnx"
    q_size = q_onnx.stat().st_size / 1e6
    print(f"[OK] Quantized ONNX: {q_size:.1f} MB")

    # Step 3: Copy quantized model to main model dir
    print("\n[STEP 3] Moving quantized model to models dir...")
    final_path = MODEL_DIR / "model_quantized.onnx"
    shutil.copy2(str(q_onnx), str(final_path))
    print(f"[OK] Final: {final_path}")

    # Step 4: Verify
    print("\n[STEP 4] Verifying ONNX model output...")
    import onnxruntime as ort
    import numpy as np
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    session = ort.InferenceSession(str(final_path))

    test_texts = [
        "Video ini sangat bagus dan bermanfaat",
        "Dasar bego lu, mati aja sana",
        "Kritik membangun untuk konten berikutnya",
    ]

    id2label = {0: "normal", 1: "abusive", 2: "hate_speech_weak", 3: "hate_speech_moderate", 4: "hate_speech_strong"}
    for text in test_texts:
        enc = tokenizer(text, return_tensors="np", padding="max_length", truncation=True, max_length=128)
        outputs = session.run(None, {
            "input_ids": enc["input_ids"].astype(np.int64),
            "attention_mask": enc["attention_mask"].astype(np.int64),
        })
        logits = outputs[0]
        exp_l = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probs = exp_l / exp_l.sum(axis=-1, keepdims=True)
        pred_class = int(np.argmax(probs, axis=-1)[0])
        confidence = float(probs[0][pred_class])
        print(f"  '{text[:45]}' -> {id2label[pred_class]} ({confidence:.1%})")

    # Step 5: Cleanup temp dirs
    print("\n[STEP 5] Cleaning up temporary files...")
    shutil.rmtree(str(ONNX_DIR), ignore_errors=True)
    shutil.rmtree(str(QUANTIZED_DIR), ignore_errors=True)
    # Remove model.onnx if it exists in MODEL_DIR
    stale_onnx = MODEL_DIR / "model.onnx"
    if stale_onnx.exists():
        stale_onnx.unlink()

    original_size = safetensors.stat().st_size / 1e6
    print(f"\n{'=' * 60}")
    print(f"  CONVERSION COMPLETE")
    print(f"  Original (safetensors): {original_size:.1f} MB")
    print(f"  Quantized (ONNX int8):  {q_size:.1f} MB")
    print(f"  Size reduction:         {(1 - q_size / original_size) * 100:.0f}%")
    print(f"  RAM savings:            ~700 MB (no PyTorch needed at runtime)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
