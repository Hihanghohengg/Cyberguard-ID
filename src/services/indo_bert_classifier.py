"""CyberGuard-ID — IndoBERT Deep Learning Classifier.

Uses HuggingFace Transformers (indobenchmark/indobert-base-p1) for 
highly accurate colloquial Indonesian text classification.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.core.schemas import Prediction, VerificationStatus

logger = logging.getLogger("cyberguard.indo_bert")


class IndoBERTClassifier:
    """Deep learning classifier using IndoBERT for slang and context."""

    def __init__(
        self,
        model_name: str = "indobenchmark/indobert-base-p1",
        local_model_path: str = "models/indobert_cyberguard",
    ) -> None:
        self.model_name = model_name
        self.local_model_path = Path(local_model_path)
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded = False
        
        # Label mapping matching CyberGuard-ID taxonomy
        self.id2label = {
            0: "normal",
            1: "abusive",
            2: "hate_speech_weak",
            3: "hate_speech_moderate",
            4: "hate_speech_strong"
        }
        self.label2id = {v: k for k, v in self.id2label.items()}

    def load(self) -> None:
        """Load tokenizer and model from local path or HuggingFace."""
        try:
            if self.local_model_path.exists():
                logger.info("Loading IndoBERT from local path: %s", self.local_model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(str(self.local_model_path))
                self.model = AutoModelForSequenceClassification.from_pretrained(str(self.local_model_path))
            else:
                logger.info("Local model not found. Loading base IndoBERT from HuggingFace.")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name, 
                    num_labels=5,
                    id2label=self.id2label,
                    label2id=self.label2id
                )
            
            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            logger.info("IndoBERT loaded successfully on %s.", self.device)
        except Exception as e:
            logger.error("Failed to load IndoBERT: %s", e)
            raise

    def predict_proba(self, texts: list[str], progress_callback: Any | None = None) -> np.ndarray:
        """Predict probability scores for a batch of texts.
        
        Matches sklearn predict_proba signature.
        """
        if not self._loaded:
            self.load()

        if not texts:
            return np.array([])

        import numpy as np

        # Process in batches to avoid OOM
        batch_size = 32
        all_probs = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            if progress_callback and len(batch_texts) > 0:
                snippet = batch_texts[0][:50].replace("\n", " ").strip()
                progress_callback(4, f"Menganalisis: '{snippet}...'")

            inputs = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=128, 
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1)
                all_probs.append(probs.cpu().numpy())

        return np.vstack(all_probs)

