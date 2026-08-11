# CyberGuard-ID — Methodology

## 1. Dataset

### Requirements
- 13.169 raw → 12.934 usable sampel dari Ibrohim & Budi (2019)
- Bahasa Indonesia
- Label dipetakan ke C0–C4 (C5 sebagai abstention)
- Sumber dan lisensi terdokumentasi
- Username bukan feature

### Schema
```csv
id,text,label,source,source_group,created_at
```

### Label Distribution
Model memerlukan representasi seimbang dari setiap kategori. `class_weight="balanced"` digunakan untuk menangani ketidakseimbangan.

## 2. Preprocessing

Pipeline preprocessing:
1. Unicode normalization (NFKC)
2. Lowercase
3. URL replacement → `<URL>`
4. Mention replacement → `<MENTION>`
5. Repeated character normalization (4+ → 2)
6. Repeated punctuation normalization
7. Slang normalization (dictionary-based)
8. Whitespace normalization

### Yang TIDAK dilakukan
- Stemming agresif (merusak konteks)
- Menghapus negasi ("tidak", "bukan", "jangan")
- Menghapus kata target
- Menghapus kata kasar (diperlukan untuk klasifikasi)

## 3. Classifier: IndoBERT (Model Utama)

Sistem menggunakan model *deep learning* berbasis Transformers sebagai model utama untuk klasifikasi teks.
- **Model Dasar**: `indobenchmark/indobert-base-p1`
- **Tugas**: Sequence Classification (5 kelas training: C0, C1, C2, C3, C4)
- **Kapasitas**: Mampu menangkap konteks kalimat dan semantik bahasa gaul/colloquial Indonesia yang tidak bisa ditangkap oleh metode statistik tradisional.

## 4. Confidence & Verification

### Threshold Configuration
```yaml
highly_confident: 0.85
accepted: 0.70
mandatory_review: 0.55
minimum_margin: 0.10
strong_margin: 0.15
```

### Verification Status
| Status | Condition |
|--------|-----------|
| MODEL_VERIFIED | conf ≥ 0.85 AND margin ≥ 0.15 |
| RECOMMENDED_REVIEW | 0.70 ≤ conf < 0.85 AND margin ≥ 0.10 |
| MANDATORY_REVIEW | 0.55 ≤ conf < 0.70 |
| UNCERTAIN (C5) | conf < 0.55 OR margin < 0.10 |

## 5. Evaluation Metrics

### Primary Metrics
- **Macro F1** — overall classifier quality
- **Recall kelas high-risk** — ability to detect threats/hate/harassment

### Full Metrics
- Accuracy, Macro Precision, Macro Recall, Macro F1, Weighted F1
- Per-class Precision, Recall, F1, Support
- Confusion Matrix
- Inference time per 100 comments
- Model file size

## 6. Risk Scoring

### Base Scores
Per-category fixed scores (0–5).

### Additional Indicators
- Target individual detected: +1
- Target minor suspected: +1
- Repeated harmful (≥3): +1
- Unique authors (≥3): +1
- Incitement to attack: +2
- Doxxing indicator: +2

### Risk Levels
- Low: 0–1
- Medium: 2–3
- High: 4–5
- Critical: 6+

## 7. Repetition Detection

### Technique
TF-IDF cosine similarity pada harmful comments.

### Configuration
- similarity_threshold: 0.80
- minimum_harmful_comments: 3
- minimum_unique_authors: 3

### Indication Levels
- None → Early → Moderate → Strong → Critical

### Clustering
Greedy clustering + reply-thread grouping.

---

## 8. Caveat Metodologis & Validasi Eksternal

> [!WARNING]
> **Domain Shift (Twitter/X vs YouTube)**
> Dataset pelatihan (Ibrohim & Budi 2019) bersumber dari **Twitter/X**, sementara target operasional dan artefak dari CyberGuard-ID difokuskan pada kolom komentar **YouTube**. Terdapat perbedaan karakteristik bahasa, panjang teks, dan pola interaksi antara kedua platform.

Karena adanya *domain shift* ini, klaim performa model (Akurasi, F1) harus secara jujur dibatasi **hanya pada dataset pengujian (test set)**, bukan "akurasi pada YouTube".
Sebagai rekomendasi kuat untuk pengembangan selanjutnya, perlu dilakukan **Validasi Eksternal** secara berkala menggunakan sampel komentar YouTube berbahasa Indonesia yang dianotasi secara manual untuk memastikan performa model tetap konsisten di ranah produksi.
