"""CyberGuard-ID — IndoBERT ONNX Classifier.

Uses ONNX Runtime for ultra-lightweight inference of the fine-tuned
IndoBERT model. No PyTorch or Transformers needed at runtime.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from tokenizers import Tokenizer

logger = logging.getLogger("cyberguard.indo_bert")


class IndoBERTClassifier:
    """ONNX-based IndoBERT classifier — fits in 512 MB RAM."""

    def __init__(
        self,
        model_name: str = "indobenchmark/indobert-base-p1",
        local_model_path: str = "models/indobert_cyberguard",
    ) -> None:
        self.model_name = model_name
        self.local_model_path = Path(local_model_path)
        self.tokenizer: Tokenizer | None = None
        self.session: Any = None
        self._loaded = False

        # Label mapping matching CyberGuard-ID taxonomy
        self.id2label = {
            0: "normal",
            1: "abusive",
            2: "hate_speech_weak",
            3: "hate_speech_moderate",
            4: "hate_speech_strong",
        }
        self.label2id = {v: k for k, v in self.id2label.items()}

    def load(self) -> None:
        """Load ONNX model and tokenizer."""
        import onnxruntime as ort

        onnx_path = self.local_model_path / "model_quantized.onnx"
        tokenizer_path = self.local_model_path / "tokenizer.json"

        if not onnx_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found: {onnx_path}. "
                "Run 'python scripts/convert_to_onnx.py' to create it."
            )

        if not tokenizer_path.exists():
            raise FileNotFoundError(f"Tokenizer not found: {tokenizer_path}")

        try:
            logger.info("Loading ONNX model from %s", onnx_path)

            # Configure ONNX Runtime for minimal memory usage
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 2
            sess_options.inter_op_num_threads = 1
            sess_options.enable_mem_pattern = True
            sess_options.enable_cpu_mem_arena = False  # Save memory on constrained environments

            self.session = ort.InferenceSession(
                str(onnx_path),
                sess_options,
                providers=["CPUExecutionProvider"],
            )

            # Load tokenizer using HuggingFace tokenizers (pure Rust, very fast)
            self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
            self.tokenizer.enable_truncation(max_length=128)
            self.tokenizer.enable_padding(length=128, pad_id=0, pad_token="[PAD]")

            self._loaded = True
            model_size = onnx_path.stat().st_size / 1e6
            logger.info("ONNX model loaded successfully (%.1f MB).", model_size)

        except Exception as e:
            logger.error("Failed to load ONNX model: %s", e)
            raise

    def predict_proba(self, texts: list[str], progress_callback: Any | None = None) -> np.ndarray:
        """Predict probability scores for a batch of texts.

        Matches sklearn predict_proba signature for drop-in compatibility.
        """
        if not self._loaded:
            self.load()

        if not texts:
            return np.array([])

        # Process in batches
        batch_size = 32
        all_probs = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            if progress_callback and len(batch_texts) > 0:
                snippet = batch_texts[0][:50].replace("\n", " ").strip()
                progress_callback(4, f"Menganalisis: '{snippet}...'")

            # Tokenize batch
            encoded = self.tokenizer.encode_batch(batch_texts)

            input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

            # Run inference
            outputs = self.session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )

            logits = outputs[0]
            # Softmax
            exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
            probs = exp_logits / exp_logits.sum(axis=-1, keepdims=True)
            all_probs.append(probs)

        return np.vstack(all_probs)
