import json
from google import genai
from pydantic import BaseModel, Field
import os
from src.core.logging_config import get_logger
from src.core.schemas import Prediction, VerificationStatus, Comment
from time import sleep

logger = get_logger("gemini_arbiter")

class ArbiterDecision(BaseModel):
    comment_id: str = Field(description="ID komentar asli")
    predicted_label: str = Field(description="Pilihan: normal, abusive, hate_speech_weak, hate_speech_moderate, hate_speech_strong")
    confidence: float = Field(description="Tingkat keyakinan 0.0 - 1.0")
    reasoning: str = Field(description="Alasan singkat penentuan label ini")

class ArbiterResponse(BaseModel):
    decisions: list[ArbiterDecision]

class GeminiArbiter:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not found, GeminiArbiter will be disabled.")

    def resolve(self, uncertain_preds: list[Prediction], comments: list[Comment]):
        if not self.client or not uncertain_preds:
            return

        comment_map = {c.id: c for c in comments}
        
        # Process in batches of 50 to avoid token limits
        batch_size = 50
        for i in range(0, len(uncertain_preds), batch_size):
            batch_preds = uncertain_preds[i:i+batch_size]
            
            prompt = self._build_prompt(batch_preds, comment_map)
            
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': ArbiterResponse,
                        'temperature': 0.1,
                    },
                )
                
                if response.text:
                    result = json.loads(response.text)
                    self._apply_decisions(result.get("decisions", []), batch_preds)
                    
            except Exception as e:
                logger.error(f"Gemini Arbiter failed: {e}")
                
            sleep(1) # Simple rate limit backoff

    def _build_prompt(self, batch_preds: list[Prediction], comment_map: dict[str, Comment]) -> str:
        prompt = """Anda adalah ahli moderasi konten Bahasa Indonesia (CyberGuard-ID).
Tugas Anda adalah mengklasifikasikan komentar-komentar yang ambigu menjadi salah satu dari kategori berikut:
- normal: Aman, diskusi wajar, kutipan sejarah/agama, kritik membangun tanpa makian.
- abusive: Menggunakan kata kasar/makian (anjing, babi, bangsat) tapi TIDAK menargetkan SARA atau kelompok rentan.
- hate_speech_weak: Menyinggung SARA/kelompok tapi ringan (stereotip).
- hate_speech_moderate: Menghina/merendahkan SARA atau kelompok secara langsung.
- hate_speech_strong: Mengajak kekerasan, diskriminasi parah, atau ancaman pembunuhan berbasis SARA.

Perhatikan: Kata-kata seperti 'bunuh', 'dajjal', 'perang' jika berada dalam konteks kutipan agama/ceramah atau sejarah HARUS diklasifikasikan sebagai 'normal'.

Klasifikasikan komentar berikut:
"""
        for pred in batch_preds:
            comment = comment_map.get(pred.comment_id)
            if comment:
                text = comment.original_text.replace('\n', ' ')
                prompt += f"\nID: {pred.comment_id} | Teks: {text}"
                
        return prompt

    def _apply_decisions(self, decisions: list[dict], batch_preds: list[Prediction]):
        decision_map = {d["comment_id"]: d for d in decisions}
        for pred in batch_preds:
            decision = decision_map.get(pred.comment_id)
            if decision:
                pred.predicted_label = decision["predicted_label"]
                pred.confidence = decision["confidence"]
                pred.verification_status = VerificationStatus.MODEL_VERIFIED.value
                pred.second_label = "gemini_arbiter"
