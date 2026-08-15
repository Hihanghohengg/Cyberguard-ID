import pandas as pd
from sklearn.model_selection import train_test_split
import sys
import os

# Ensure the root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.preprocessing import TextPreprocessor

def main():
    print("Membaca data Kaggle...")
    df = pd.read_csv("data/raw/data.csv", encoding='latin-1')
    
    # Membaca kamus alay
    print("Membaca kamus alay...")
    try:
        kamus_df = pd.read_csv("data/raw/new_kamusalay.csv", header=None, names=['slang', 'formal'], encoding='latin-1')
        slang_dict = dict(zip(kamus_df['slang'], kamus_df['formal']))
    except Exception as e:
        print(f"Error membaca new_kamusalay.csv: {e}")
        slang_dict = {}

    preprocessor = TextPreprocessor(slang_dict=slang_dict)

    print("Memproses teks...")
    # Preprocess text (Tweet column)
    df['text'] = df['Tweet'].apply(preprocessor.preprocess)

    print("Melakukan mapping label...")
    # Mapping label
    def map_label(row):
        if row.get('HS_Strong', 0) == 1:
            return 'hate_speech_strong'
        elif row.get('HS_Moderate', 0) == 1:
            return 'hate_speech_moderate'
        elif row.get('HS_Weak', 0) == 1:
            return 'hate_speech_weak'
        elif row.get('HS', 0) == 1: # Fallback if HS is 1 but none of the weak/mod/strong is 1
            return 'hate_speech_weak' 
        elif row.get('Abusive', 0) == 1:
            return 'abusive'
        else:
            return 'normal'

    df['label'] = df.apply(map_label, axis=1)

    print("\n--- DISTRIBUSI KELAS (Sebelum Balancing) ---")
    dist = df['label'].value_counts()
    print(dist)
    
    print("\n--- PERSENTASE ---")
    print(df['label'].value_counts(normalize=True) * 100)

    # Split dataset (70/15/15)
    print("\nMelakukan splitting 70/15/15 (Stratified)...")
    train, temp = train_test_split(df, test_size=0.3, random_state=42, stratify=df['label'])
    val, test = train_test_split(temp, test_size=0.5, random_state=42, stratify=temp['label'])
    
    print(f"Total data: {len(df)}")
    print(f"Train size: {len(train)}")
    print(f"Val size: {len(val)}")
    print(f"Test size: {len(test)}")

    print("\nMenyimpan ke data/processed/...")
    train.to_csv("data/processed/train.csv", index=False)
    val.to_csv("data/processed/val.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)
    print("Selesai!")

if __name__ == "__main__":
    main()
