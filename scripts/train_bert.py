"""CyberGuard-ID — IndoBERT Fine-Tuning Script.

Fine-tunes the indobenchmark/indobert-base-p1 model on the CyberGuard-ID dataset
to achieve >85% accuracy on colloquial Indonesian hate speech.
"""

import os
import json
import logging
from pathlib import Path

import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_bert")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models" / "indobert_cyberguard"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MODEL_NAME = "indobenchmark/indobert-base-p1"
BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 2e-5

label2id = {
    "normal": 0,
    "abusive": 1,
    "hate_speech_weak": 2,
    "hate_speech_moderate": 3,
    "hate_speech_strong": 4,
}

id2label = {v: k for k, v in label2id.items()}

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average='macro')
    return {
        'accuracy': acc,
        'macro_f1': macro_f1
    }

def main():
    logger.info("Loading datasets...")
    train_df = pd.read_csv(PROCESSED_DIR / "train.csv").dropna(subset=['text', 'label'])
    val_df = pd.read_csv(PROCESSED_DIR / "val.csv").dropna(subset=['text', 'label'])
    
    # Map string labels to integer IDs
    train_df['label'] = train_df['label'].map(label2id)
    val_df['label'] = val_df['label'].map(label2id)
    
    train_dataset = Dataset.from_pandas(train_df[['text', 'label']])
    val_dataset = Dataset.from_pandas(val_df[['text', 'label']])
    
    logger.info("Loading tokenizer %s...", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding=False, truncation=True, max_length=128)
        
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    logger.info("Loading base model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=5,
        id2label=id2label,
        label2id=label2id
    )
    
    training_args = TrainingArguments(
        output_dir=str(MODEL_DIR / "checkpoints"),
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_dir=str(MODEL_DIR / "logs"),
        logging_steps=50,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    logger.info("Starting training...")
    trainer.train()
    
    logger.info("Evaluating best model...")
    eval_results = trainer.evaluate()
    logger.info("Eval Results: %s", eval_results)
    
    logger.info("Saving final model to %s", MODEL_DIR)
    trainer.save_model(str(MODEL_DIR))
    
    # Save metadata indicating we use IndoBERT
    metadata = {
        "algorithm": "IndoBERT",
        "model_name": MODEL_NAME,
        "classes": ["C0", "C1", "C2", "C3", "C4"],
        "eval_metrics": eval_results
    }
    
    with open(PROJECT_ROOT / "models" / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
        
    logger.info("Training complete. IndoBERT is ready for inference.")

if __name__ == "__main__":
    main()
