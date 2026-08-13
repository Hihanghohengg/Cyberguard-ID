"""CyberGuard-ID — Data Augmentation Script.

Script ini digunakan untuk menyeimbangkan kelas minoritas (C2, C3, C4)
dengan melakukan teknik Data Augmentation menggunakan Contextual Word Embeddings 
berbasis model IndoBERT.

Requirements:
    pip install nlpaug transformers torch pandas
"""

import logging
from pathlib import Path

import pandas as pd
import nlpaug.augmenter.word as naw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("augment_data")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TRAIN_PATH = PROCESSED_DIR / "train.csv"
AUGMENTED_PATH = PROCESSED_DIR / "train_augmented.csv"

# Model yang digunakan untuk augmentasi (substitusi sinonim kontekstual)
MODEL_NAME = "indobenchmark/indobert-base-p1"


def main():
    logger.info("Memulai proses Data Augmentation...")

    if not TRAIN_PATH.exists():
        logger.error(f"File training tidak ditemukan: {TRAIN_PATH}")
        return

    df = pd.read_csv(TRAIN_PATH).dropna(subset=["text", "label"])
    logger.info(f"Distribusi kelas awal:\n{df['label'].value_counts()}")

    # Cari kelas mayoritas
    class_counts = df["label"].value_counts()
    max_count = class_counts.max()

    # Setup NLPaug (menggunakan IndoBERT)
    logger.info(f"Memuat model augmentasi: {MODEL_NAME} (Ini mungkin memakan waktu)")
    try:
        # action='substitute' akan mengganti kata dengan sinonim berdasar konteks
        aug = naw.ContextualWordEmbsAug(
            model_path=MODEL_NAME, 
            action="substitute",
            device="cpu" # Ubah ke 'cuda' jika ada GPU
        )
    except Exception as e:
        logger.error(f"Gagal memuat model augmentasi: {e}")
        return

    augmented_rows = []

    # Lakukan oversampling + augmentasi untuk kelas yang < max_count
    for label, count in class_counts.items():
        if count < max_count:
            diff = max_count - count
            logger.info(f"Augmentasi kelas {label} (+{diff} sampel)")
            
            # Ambil sampel dari kelas ini
            class_df = df[df["label"] == label]
            
            # Generate augmentasi sejumlah diff
            # Untuk efisiensi, kita loop over sampel yang ada secara random
            samples = class_df.sample(n=diff, replace=True, random_state=42)["text"].tolist()
            
            augmented_texts = aug.augment(samples)
            
            for text in augmented_texts:
                augmented_rows.append({"text": text, "label": label})

    if augmented_rows:
        aug_df = pd.DataFrame(augmented_rows)
        # Gabungkan dataset asli dan augmented
        final_df = pd.concat([df, aug_df], ignore_index=True)
        
        # Simpan hasilnya
        final_df.to_csv(AUGMENTED_PATH, index=False)
        logger.info(f"Dataset berhasil diaugmentasi. Disimpan di: {AUGMENTED_PATH}")
        logger.info(f"Distribusi kelas akhir:\n{final_df['label'].value_counts()}")
    else:
        logger.info("Dataset sudah seimbang. Tidak ada augmentasi yang dilakukan.")
        df.to_csv(AUGMENTED_PATH, index=False)

if __name__ == "__main__":
    main()
