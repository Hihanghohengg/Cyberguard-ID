"""CyberGuard-ID — Dataset Preparation Script.

Prepares the Ibrohim & Budi 2019 dataset for training.
Performs auditing, preprocessing, label mapping, leakage checking,
and stratified splitting (70/15/15) without training the model.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ibrohim_budi_2019"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "dataset_audit"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def audit_dataset(df: pd.DataFrame) -> dict:
    # 1. Audit Dataset Asli
    audit_data = {
        "encoding": "latin-1 or utf-8",
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_tweets": int(df["Tweet"].duplicated().sum()),
        "sample_data": df.head(5).to_dict(orient="records"),
    }

    # Label distribution
    label_cols = [
        "HS", "Abusive", "HS_Individual", "HS_Group", "HS_Religion",
        "HS_Race", "HS_Physical", "HS_Gender", "HS_Other",
        "HS_Weak", "HS_Moderate", "HS_Strong",
    ]
    dist = {}
    for col in label_cols:
        if col in df.columns:
            dist[col] = df[col].value_counts().to_dict()

    audit_data["label_distribution"] = dist

    with open(ARTIFACTS_DIR / "dataset_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=4)

    orig_dist = []
    for col in label_cols:
        if col in df.columns:
            counts = df[col].value_counts()
            for val, count in counts.items():
                orig_dist.append({"Label": col, "Value": val, "Count": count})
    pd.DataFrame(orig_dist).to_csv(ARTIFACTS_DIR / "original_label_distribution.csv", index=False)

    return audit_data


def load_kamus_alay() -> dict:
    kamus_path = RAW_DIR / "new_kamusalay.csv"
    if not kamus_path.exists():
        return {}
    kamus_df = pd.read_csv(kamus_path, encoding="latin-1", header=None, names=["slang", "formal"])
    return dict(zip(kamus_df["slang"].astype(str), kamus_df["formal"].astype(str)))


KAMUS_ALAY = load_kamus_alay()


def preprocess_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    
    # URL removal
    text = re.sub(r"http\S+|www\S+|url", " ", text)
    
    # Mention/user normalization
    text = re.sub(r"rt user", "user", text)
    text = re.sub(r"@\w+", "user", text)
    
    # Karakter/control character cleanup (\x.. or \n)
    text = re.sub(r"\\x[0-9a-f]{2}", " ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"[^a-z0-9\s.,?!]", " ", text)  # keep basic punctuation
    
    # Normalisasi spasi
    text = re.sub(r"\s+", " ", text).strip()
    
    # Slang normalization
    words = text.split()
    normalized_words = [KAMUS_ALAY.get(w, w) for w in words]
    text = " ".join(normalized_words)
    
    return text


def check_conflicts_and_map_labels(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    conflicts = []
    valid_rows = []

    for idx, row in df.iterrows():
        hs = int(row.get("HS", 0))
        abusive = int(row.get("Abusive", 0))
        hs_weak = int(row.get("HS_Weak", 0))
        hs_mod = int(row.get("HS_Moderate", 0))
        hs_strong = int(row.get("HS_Strong", 0))
        hs_ind = int(row.get("HS_Individual", 0))
        hs_grp = int(row.get("HS_Group", 0))
        
        conflict_reasons = []
        
        if hs == 0 and (hs_weak == 1 or hs_mod == 1 or hs_strong == 1):
            conflict_reasons.append("HS=0 but Weak/Mod/Strong=1")
            
        if hs == 1 and hs_weak == 0 and hs_mod == 0 and hs_strong == 0:
            conflict_reasons.append("HS=1 but no Weak/Mod/Strong")
            
        if hs_weak + hs_mod + hs_strong > 1:
            conflict_reasons.append(f"Multiple HS levels active: W={hs_weak}, M={hs_mod}, S={hs_strong}")
            
        if hs_ind == 1 and hs_grp == 1:
            conflict_reasons.append("HS_Individual and HS_Group active simultaneously")
            
        primary_label = None
        primary_id = -1
        
        if hs == 0 and abusive == 0:
            primary_label = "C0"
            primary_id = 0
        elif hs == 0 and abusive == 1:
            primary_label = "C1"
            primary_id = 1
        elif hs == 1:
            if hs_weak == 1:
                primary_label = "C2"
                primary_id = 2
            elif hs_mod == 1:
                primary_label = "C3"
                primary_id = 3
            elif hs_strong == 1:
                primary_label = "C4"
                primary_id = 4
                
        if primary_label is None:
            conflict_reasons.append("Row without valid primary label")
            
        if conflict_reasons:
            row_dict = row.to_dict()
            row_dict["conflict_reasons"] = "; ".join(conflict_reasons)
            conflicts.append(row_dict)
        else:
            row_dict = row.to_dict()
            row_dict["primary_label"] = primary_label
            row_dict["primary_label_id"] = primary_id
            valid_rows.append(row_dict)
            
    conflicts_df = pd.DataFrame(conflicts)
    if not conflicts_df.empty:
        conflicts_df.to_csv(ARTIFACTS_DIR / "label_conflicts.csv", index=False)
        
    return pd.DataFrame(valid_rows), conflicts_df


def deduplicate_and_split(df: pd.DataFrame) -> tuple:
    exact_duplicates = int(df["text_original"].duplicated().sum())
    normalized_duplicates = int(df["text_clean"].duplicated().sum())
    
    duplicate_report = {
        "exact_duplicates": exact_duplicates,
        "normalized_duplicates": normalized_duplicates,
    }
    
    df_dedup = df.drop_duplicates(subset=["text_clean"]).copy()
    
    train_df, temp_df = train_test_split(
        df_dedup, test_size=0.3, stratify=df_dedup["primary_label_id"], random_state=42
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.5, stratify=temp_df["primary_label_id"], random_state=42
    )
    
    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()
    
    train_df["split"] = "train"
    val_df["split"] = "validation"
    test_df["split"] = "test"
    
    train_texts = set(train_df["text_clean"])
    val_texts = set(val_df["text_clean"])
    test_texts = set(test_df["text_clean"])
    
    leakage = {
        "train_val_leakage": len(train_texts.intersection(val_texts)),
        "train_test_leakage": len(train_texts.intersection(test_texts)),
        "val_test_leakage": len(val_texts.intersection(test_texts)),
    }
    
    with open(ARTIFACTS_DIR / "duplicate_report.json", "w", encoding="utf-8") as f:
        json.dump(duplicate_report, f, indent=4)
        
    with open(ARTIFACTS_DIR / "leakage_report.json", "w", encoding="utf-8") as f:
        json.dump(leakage, f, indent=4)
        
    final_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
    return final_df, train_df, val_df, test_df, duplicate_report, leakage


def main() -> None:
    try:
        df = pd.read_csv(RAW_DIR / "data.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(RAW_DIR / "data.csv", encoding="latin-1")
    
    audit_data = audit_dataset(df)
    
    df["text_original"] = df["Tweet"]
    df["text_clean"] = df["text_original"].apply(preprocess_text)
    
    valid_df, conflicts_df = check_conflicts_and_map_labels(df)
    
    final_df, train_df, val_df, test_df, dup_report, leakage = deduplicate_and_split(valid_df)
    
    final_df["source_id"] = final_df.index
    train_df["source_id"] = train_df.index
    val_df["source_id"] = val_df.index
    test_df["source_id"] = test_df.index
    
    cols = [
        "source_id", "text_original", "text_clean", "primary_label", "primary_label_id",
        "HS", "Abusive", "HS_Weak", "HS_Moderate", "HS_Strong",
        "HS_Individual", "HS_Group", "HS_Religion", "HS_Race", 
        "HS_Physical", "HS_Gender", "HS_Other", "split"
    ]
    
    for c in cols:
        if c not in final_df.columns:
            final_df[c] = ""
            train_df[c] = ""
            val_df[c] = ""
            test_df[c] = ""
            
    final_df[cols].to_csv(PROCESSED_DIR / "dataset_cyberguard_id.csv", index=False)
    train_df[cols].to_csv(PROCESSED_DIR / "train.csv", index=False)
    val_df[cols].to_csv(PROCESSED_DIR / "validation.csv", index=False)
    test_df[cols].to_csv(PROCESSED_DIR / "test.csv", index=False)
    
    primary_dist = final_df["primary_label"].value_counts().reset_index()
    primary_dist.columns = ["Label", "Count"]  # type: ignore
    primary_dist.to_csv(ARTIFACTS_DIR / "primary_label_distribution.csv", index=False)
    
    with open(ARTIFACTS_DIR / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "train": len(train_df),
            "validation": len(val_df),
            "test": len(test_df)
        }, f, indent=4)
        
    with open(ARTIFACTS_DIR / "preprocessing_report.md", "w", encoding="utf-8") as f:
        f.write("# Preprocessing Report\n\n- Lowercasing applied\n- Slang mapping from new_kamusalay.csv applied\n- URLs removed\n- Mentions normalized to 'user'\n- Kept character repetitions.\n")
        
    print("=" * 40)
    print("CyberGuard-ID Dataset Preparation")
    print("=" * 40)
    print("Source:\nIbrohim & Budi 2019\n")
    print(f"Raw rows               : {len(df)}")
    print(f"Exact duplicates       : {dup_report['exact_duplicates']}")
    print(f"Near duplicates        : {dup_report['normalized_duplicates']}")
    print(f"Invalid/conflict rows  : {len(conflicts_df)}")
    print(f"Usable rows            : {len(valid_df) - dup_report['normalized_duplicates']}\n")
    
    print("Primary label distribution:")
    dist_map = final_df["primary_label"].value_counts().to_dict()
    print(f"C0 NORMAL               : {dist_map.get('C0', 0)}")
    print(f"C1 ABUSIVE              : {dist_map.get('C1', 0)}")
    print(f"C2 HATE_SPEECH_WEAK     : {dist_map.get('C2', 0)}")
    print(f"C3 HATE_SPEECH_MODERATE : {dist_map.get('C3', 0)}")
    print(f"C4 HATE_SPEECH_STRONG   : {dist_map.get('C4', 0)}\n")
    
    print("Split:")
    print(f"Train                   : {len(train_df)}")
    print(f"Validation              : {len(val_df)}")
    print(f"Test                    : {len(test_df)}\n")
    
    print(f"Leakage train-val       : {leakage['train_val_leakage']}")
    print(f"Leakage train-test      : {leakage['train_test_leakage']}")
    print(f"Leakage val-test        : {leakage['val_test_leakage']}\n")
    
    print("Saved:")
    print("data/processed/dataset_cyberguard_id.csv")
    print("data/processed/train.csv")
    print("data/processed/validation.csv")
    print("data/processed/test.csv")
    print("=" * 40)


if __name__ == "__main__":
    main()
