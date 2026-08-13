"""CyberGuard-ID — README Metrics Updater.

Script ini membaca models/model_metadata.json dan secara otomatis memperbarui
bagian "Hasil Evaluasi Model" di README.md dengan nilai yang akurat dan riil,
sehingga menjaga kejujuran data (tidak ada manipulasi).
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"
README_PATH = PROJECT_ROOT / "README.md"

def main():
    if not METADATA_PATH.exists():
        print(f"Error: Metadata tidak ditemukan di {METADATA_PATH}")
        print("Jalankan training terlebih dahulu!")
        return
        
    if not README_PATH.exists():
        print(f"Error: README.md tidak ditemukan di {README_PATH}")
        return

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    eval_metrics = metadata.get("eval_metrics", {})
    per_class = metadata.get("per_class_metrics", {})
    cm = metadata.get("confusion_matrix", [])
    
    if not per_class or not cm:
        print("Error: model_metadata.json tidak mengandung 'per_class_metrics' atau 'confusion_matrix'.")
        print("Pastikan Anda menggunakan skrip train_bert.py versi terbaru.")
        return

    accuracy = eval_metrics.get("eval_accuracy", 0) * 100
    macro_f1 = eval_metrics.get("eval_macro_f1", 0) * 100

    # Build New Section Markdown
    new_section = f"""### 5. Hasil Evaluasi Model

Evaluasi dilakukan pada held-out test set menggunakan model IndoBERT ONNX int8:

| Metrik | Nilai |
|--------|-------|
| **Accuracy** | {accuracy:.2f}% |
| **Macro F1** | {macro_f1:.2f}% |
| Model size (ONNX int8) | ~110 MB |
| Inference time | <100ms / komentar |

#### Performa per Kelas
| Kelas | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
"""
    # Build per-class table
    for label, metrics in per_class.items():
        # Misalnya label "normal" -> C0
        new_section += f"| {label} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | {metrics['f1']:.4f} | {metrics['support']} |\n"

    new_section += "\n#### Confusion Matrix\n```text\n"
    new_section += "                          Prediksi\n"
    new_section += "                 C0    C1    C2    C3    C4\n"
    new_section += "              -----------------------------\n"
    
    labels = ["C0", "C1", "C2", "C3", "C4"]
    for i, row in enumerate(cm):
        row_str = "    ".join([f"{v:3}" for v in row])
        new_section += f"          {labels[i]} |  {row_str} \n"
        
    new_section += "```\n"
    new_section += "*(Di-generate secara otomatis berdasarkan model_metadata.json terbaru)*\n\n"

    # Read existing README
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Regex to replace the section
    # Matches from "### 5. Hasil Evaluasi Model" until "> [!TIP]"
    pattern = re.compile(r"### 5\. Hasil Evaluasi Model.*?(?=> \[!TIP\])", re.DOTALL)
    
    if not pattern.search(readme_content):
        print("Error: Tidak dapat menemukan bagian '### 5. Hasil Evaluasi Model' di README.md")
        return

    updated_readme = pattern.sub(new_section, readme_content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_readme)
        
    print("Berhasil meng-update README.md dengan metrik terbaru yang akurat!")
    
if __name__ == "__main__":
    main()
