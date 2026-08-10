import pandas as pd
import json
import os

base_path = "data/processed/"
train = pd.read_csv(base_path + "train.csv")
val = pd.read_csv(base_path + "validation.csv")
test = pd.read_csv(base_path + "test.csv")

out = {}

def get_dist(df):
    dist = df['primary_label'].value_counts().to_dict()
    # Sort keys for consistent output
    return {k: dist.get(k, 0) for k in ["C0", "C1", "C2", "C3", "C4"]}

out["dist"] = {
    "train": get_dist(train),
    "validation": get_dist(val),
    "test": get_dist(test)
}

out["total"] = len(train) + len(val) + len(test)

t_ids = set(train['source_id'])
v_ids = set(val['source_id'])
te_ids = set(test['source_id'])

t_texts = set(train['text_clean'])
v_texts = set(val['text_clean'])
te_texts = set(test['text_clean'])

out["leakage"] = {
    "id_train_val": len(t_ids.intersection(v_ids)),
    "id_train_test": len(t_ids.intersection(te_ids)),
    "id_val_test": len(v_ids.intersection(te_ids)),
    "text_train_val": len(t_texts.intersection(v_texts)),
    "text_train_test": len(t_texts.intersection(te_texts)),
    "text_val_test": len(v_texts.intersection(te_texts)),
}

combined = pd.concat([train, val, test])
samples = {}
for label in ["C0", "C1", "C2", "C3", "C4"]:
    subset = combined[combined['primary_label'] == label]
    # sample 3 items
    sampled = subset.sample(min(3, len(subset)), random_state=42)
    cols = ['text_original', 'text_clean', 'HS', 'Abusive', 'HS_Weak', 'HS_Moderate', 'HS_Strong', 'primary_label']
    samples[label] = sampled[cols].to_dict('records')

out["samples"] = samples

with open("artifacts/scratch/check_report.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=4)
print("Done")
