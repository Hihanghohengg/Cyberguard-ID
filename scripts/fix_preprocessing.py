import pandas as pd
import re
import json
import os

base_path = "data/processed/"
raw_path = "data/raw/ibrohim_budi_2019/"
artifacts = "artifacts/dataset_audit/"

# 2. Audit Kamus Alay
kamus_df = pd.read_csv(raw_path + "new_kamusalay.csv", encoding="latin-1", header=None, names=["slang", "formal"])
kamus_df["slang"] = kamus_df["slang"].astype(str)
kamus_df["formal"] = kamus_df["formal"].astype(str)

mapping_count = len(kamus_df)
duplicate_keys = kamus_df["slang"].duplicated().sum()
kamus_dict = dict(zip(kamus_df["slang"], kamus_df["formal"]))

short_mappings = kamus_df[kamus_df["slang"].str.len() <= 2]
phrase_mappings = kamus_df[kamus_df["formal"].str.contains(" ")]

kamus_audit_report = {
    "total_mappings": int(mapping_count),
    "duplicate_keys": int(duplicate_keys),
    "1_2_char_mappings_count": len(short_mappings),
    "phrase_mappings_count": len(phrase_mappings),
}

# 1. Buat 3 Representasi Text
def preprocess_model(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|\burl\b", "url", text)
    text = re.sub(r"rt user\b", "user", text)
    text = re.sub(r"@\w+", "user", text)
    text = re.sub(r"\\x[0-9a-f]{2}", " ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"[^a-z0-9\s.,?!]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def preprocess_normalized(text):
    text = preprocess_model(text)
    words = text.split()
    normalized_words = [kamus_dict.get(w, w) for w in words]
    return " ".join(normalized_words)

df = pd.read_csv(base_path + "dataset_cyberguard_id.csv")

# Ensure text_original exists
df["text_model"] = df["text_original"].apply(preprocess_model)
df["text_normalized"] = df["text_original"].apply(preprocess_normalized)

if "text_clean" in df.columns:
    df = df.drop(columns=["text_clean"])

# 4. Leakage Check Ulang
train = df[df["split"] == "train"]
val = df[df["split"] == "validation"]
test = df[df["split"] == "test"]

t_texts = set(train["text_model"])
v_texts = set(val["text_model"])
te_texts = set(test["text_model"])

leakage = {
    "normalized_text_model_duplicate_leakage": {
        "train_val": len(t_texts.intersection(v_texts)),
        "train_test": len(t_texts.intersection(te_texts)),
        "val_test": len(v_texts.intersection(te_texts)),
    }
}

with open(artifacts + "leakage_report.json", "w", encoding="utf-8") as f:
    json.dump(leakage, f, indent=4)

with open(artifacts + "preprocessing_report.md", "w", encoding="utf-8") as f:
    f.write("# Preprocessing Report\n\n")
    f.write("text_model: Conservative cleaning (lowercase, URL->url, USER->user, no slang replacement).\n")
    f.write("text_normalized: Includes kamus alay replacement.\n\n")
    f.write("## Kamus Alay Audit\n```json\n")
    f.write(json.dumps(kamus_audit_report, indent=4))
    f.write("\n```\n")

# 5. Output
cols = ["source_id", "text_original", "text_model", "text_normalized", "primary_label", "primary_label_id", 
        "HS", "Abusive", "HS_Weak", "HS_Moderate", "HS_Strong", 
        "HS_Individual", "HS_Group", "HS_Religion", "HS_Race", 
        "HS_Physical", "HS_Gender", "HS_Other", "split"]

df[cols].to_csv(base_path + "dataset_cyberguard_id.csv", index=False)
train[cols].to_csv(base_path + "train.csv", index=False)
val[cols].to_csv(base_path + "validation.csv", index=False)
test[cols].to_csv(base_path + "test.csv", index=False)

samples = df.sample(50, random_state=42)[["text_original", "text_model", "text_normalized"]]
samples.to_csv(artifacts + "preprocessing_samples.csv", index=False)

print(json.dumps({
    "dist_train": train["primary_label"].value_counts().to_dict(),
    "dist_val": val["primary_label"].value_counts().to_dict(),
    "dist_test": test["primary_label"].value_counts().to_dict(),
    "leakage": leakage,
    "10_samples": samples.head(10).to_dict("records"),
    "audit": kamus_audit_report,
    "totals": {"train": len(train), "val": len(val), "test": len(test)}
}))
