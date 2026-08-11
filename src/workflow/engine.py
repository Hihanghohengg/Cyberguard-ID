"""CyberGuard-ID — Workflow Engine.

Orchestrates the full analysis pipeline: input validation, comment collection,
preprocessing, classification, repetition detection, risk scoring, and reporting.
"""

from __future__ import annotations

import contextlib
import uuid
from datetime import datetime, timezone
from typing import Any

from src.core.config import AppConfig
from src.core.exceptions import (
    CyberGuardError,
    ModelNotFoundError,
)
from src.core.logging_config import get_logger
from src.core.schemas import (
    AnalysisRun,
    AnalysisStatus,
    Comment,
    ReportRecord,
    ReportSummary,
    VerificationStatus,
)
from src.services.classifier import ClassifierService
from src.services.csv_service import CSVService
from src.services.gemini_reporter import GeminiReporter, LocalReportGenerator
from src.services.preprocessing import TextPreprocessor
from src.services.repetition_detector import RepetitionDetector
from src.services.report_service import ReportService
from src.services.risk_engine import RiskEngine
from src.services.storage import StorageService
from src.services.youtube_service import YouTubeService, extract_video_id
from src.services.gemini_arbiter import GeminiArbiter
from src.workflow.state import is_valid_transition

logger = get_logger("engine")


class AnalysisEngine:
    """Orchestrates the end-to-end comment analysis workflow."""

    def __init__(self, config: AppConfig, storage: StorageService) -> None:
        self.config = config
        self.storage = storage
        self.preprocessor = TextPreprocessor(config.slang_dict)
        self.risk_engine = RiskEngine(
            base_scores=config.base_scores,
            additional_scores=config.risk_config.get("additional_scores"),
            risk_levels=config.risk_config.get("levels"),
        )
        self.repetition_detector = RepetitionDetector(
            similarity_threshold=config.repetition_config.get("similarity_threshold", 0.80),
            min_harmful_comments=config.repetition_config.get("minimum_harmful_comments", 3),
            min_unique_authors=config.repetition_config.get("minimum_unique_authors", 3),
        )
        self.report_service = ReportService(config.reports_path)

        # Adaptive Learning Memory
        from src.services.adaptive_learning import AdaptiveLearningService

        self.adaptive_service = AdaptiveLearningService(config.db_path)
        self.adaptive_service.initialize()

        # Gemini Arbiter for hybrid LLM verification
        self.gemini_arbiter = GeminiArbiter()

        # Classifier — loaded lazily
        self.classifier = ClassifierService(
            model_path=config.model_path,
            metadata_path=config.model_metadata_path,
            confidence_thresholds=config.confidence_thresholds,
            base_scores=config.base_scores,
            adaptive_service=self.adaptive_service,
        )

        # YouTube service — only if API key available
        self.youtube: YouTubeService | None = None
        if config.api_status.youtube_available:
            self.youtube = YouTubeService(
                api_key=config.youtube_api_key,
                salt=config.anonymization_salt,
            )

        self.csv_service = CSVService(
            salt=config.anonymization_salt,
            max_file_size_mb=config.settings.get("upload", {}).get("max_file_size_mb", 50),
            max_rows=config.settings.get("upload", {}).get("max_rows", 10000),
        )

    def _transition(self, analysis_id: str, current: str, target: str, **kwargs: Any) -> str:
        """Transition to a new state with validation."""
        if not is_valid_transition(current, target):
            logger.error("Invalid transition: %s -> %s", current, target)
        self.storage.update_analysis_status(analysis_id, target, **kwargs)
        logger.info("Analysis %s: %s -> %s", analysis_id, current, target)
        return target

    def run_youtube_analysis(
        self,
        url: str,
        name: str,
        max_comments: int = 500,
        include_replies: bool = True,
        progress_callback: Any = None,
        analysis_id: str | None = None,
    ) -> str:
        """Run full analysis on a YouTube video URL.

        Args:
            url: YouTube video URL.
            name: Name for this analysis run.
            max_comments: Maximum top-level comments to fetch.
            include_replies: Whether to fetch reply threads.
            progress_callback: Optional callable(step, message) for UI updates.
            analysis_id: Optional pre-allocated analysis ID.

        Returns:
            Analysis ID.
        """
        analysis_id = analysis_id or uuid.uuid4().hex[:16]

        # Create analysis run
        video_id = extract_video_id(url)
        run = AnalysisRun(
            id=analysis_id,
            name=name,
            source_type="youtube",
            source_url=url,
            video_id=video_id,
        )
        self.storage.create_analysis(run)
        status = AnalysisStatus.INITIALIZED.value

        try:
            # Step 1: Validate
            self._notify(progress_callback, 1, "Memvalidasi sumber...")
            status = self._transition(analysis_id, status, AnalysisStatus.VALIDATING_INPUT.value)

            if not self.youtube:
                raise CyberGuardError(
                    "YouTube API not configured",
                    user_message="YouTube API key belum dikonfigurasi.",
                )

            # Get metadata
            metadata = self.youtube.get_video_metadata(video_id)
            self.storage.update_analysis_status(
                analysis_id,
                status,
                video_title=metadata.title,
                channel_title=metadata.channel_title,
            )
            # Update the run object for later use
            run.video_title = metadata.title
            run.channel_title = metadata.channel_title

            # Step 2: Collect comments
            self._notify(progress_callback, 2, "Mengambil komentar...")
            status = self._transition(analysis_id, status, AnalysisStatus.COLLECTING_COMMENTS.value)

            comments = self.youtube.fetch_comments(
                video_id=video_id,
                max_comments=max_comments,
                include_replies=include_replies,
                analysis_id=analysis_id,
                store_original_username=True,
            )

            if not comments:
                self._transition(
                    analysis_id,
                    status,
                    AnalysisStatus.COMPLETED_NO_DATA.value,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
                return analysis_id

            # Continue with common pipeline
            self._run_pipeline(analysis_id, run, comments, status, progress_callback)

        except CyberGuardError as e:
            self._transition(
                analysis_id,
                status,
                AnalysisStatus.FAILED.value,
                error_message=e.user_message,
            )
            raise
        except Exception as e:
            self._transition(
                analysis_id,
                status,
                AnalysisStatus.FAILED.value,
                error_message=str(e)[:500],
            )
            raise

        return analysis_id

    def run_csv_analysis(
        self,
        file_content: bytes,
        name: str,
        progress_callback: Any = None,
        analysis_id: str | None = None,
    ) -> str:
        """Run analysis on uploaded CSV data.

        Args:
            file_content: Raw CSV bytes.
            name: Name for this analysis run.
            progress_callback: Optional callable for UI updates.
            analysis_id: Optional pre-allocated analysis ID.

        Returns:
            Analysis ID.
        """
        analysis_id = analysis_id or uuid.uuid4().hex[:16]

        run = AnalysisRun(
            id=analysis_id,
            name=name,
            source_type="csv",
        )
        self.storage.create_analysis(run)
        status = AnalysisStatus.INITIALIZED.value

        try:
            # Step 1: Validate
            self._notify(progress_callback, 1, "Memvalidasi file CSV...")
            status = self._transition(analysis_id, status, AnalysisStatus.VALIDATING_INPUT.value)

            # Step 2: Read CSV
            self._notify(progress_callback, 2, "Membaca komentar dari CSV...")
            status = self._transition(analysis_id, status, AnalysisStatus.COLLECTING_COMMENTS.value)

            comments = self.csv_service.read_csv(
                file_content=file_content,
                analysis_id=analysis_id,
            )

            if not comments:
                self._transition(
                    analysis_id,
                    status,
                    AnalysisStatus.COMPLETED_NO_DATA.value,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
                return analysis_id

            # Continue with common pipeline
            self._run_pipeline(analysis_id, run, comments, status, progress_callback)

        except CyberGuardError as e:
            self._transition(
                analysis_id,
                status,
                AnalysisStatus.FAILED.value,
                error_message=e.user_message,
            )
            raise
        except Exception as e:
            self._transition(
                analysis_id,
                status,
                AnalysisStatus.FAILED.value,
                error_message=str(e)[:500],
            )
            raise

        return analysis_id

    def _run_pipeline(
        self,
        analysis_id: str,
        run: AnalysisRun,
        comments: list[Comment],
        status: str,
        progress_callback: Any = None,
    ) -> None:
        """Run the common analysis pipeline after comments are collected."""
        # Step 3: Preprocess
        self._notify(progress_callback, 3, f"Menyiapkan teks ({len(comments)} komentar)...")
        status = self._transition(analysis_id, status, AnalysisStatus.PREPROCESSING.value)

        for c in comments:
            c.normalized_text = self.preprocessor.preprocess(c.original_text)

        self.storage.save_comments(comments)

        # Step 4: Classify
        self._notify(progress_callback, 4, "Menjalankan klasifikasi...")
        status = self._transition(analysis_id, status, AnalysisStatus.CLASSIFYING.value)

        if not self.classifier.is_loaded:
            try:
                self.classifier.load()
            except ModelNotFoundError:
                logger.warning("Model not found — skipping classification")
                self._transition(
                    analysis_id,
                    status,
                    AnalysisStatus.COMPLETED.value,
                    error_message="Model belum tersedia. Klasifikasi dilewati.",
                    total_comments=len(comments),
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
                return

        texts = [c.normalized_text or c.original_text for c in comments]
        raw_texts = [c.original_text for c in comments]
        ids = [c.id for c in comments]
        predictions = self.classifier.predict(
            texts, 
            ids, 
            raw_texts=raw_texts, 
            progress_callback=progress_callback
        )

        # Step 4.5: LLM Arbiter (Hybrid AI)
        uncertain_preds = [p for p in predictions if p.verification_status == VerificationStatus.UNCERTAIN.value]
        if uncertain_preds:
            self._notify(progress_callback, 4, f"Eskalasi {len(uncertain_preds)} komentar ambigu ke AI Arbiter...")
            try:
                self.gemini_arbiter.resolve(uncertain_preds, comments)
            except Exception as e:
                logger.error(f"Gemini Arbiter failed to resolve uncertain comments: {e}")
                self._notify(progress_callback, 4, "AI Arbiter sibuk, menggunakan hasil klasifikasi dasar...")

        # Re-compute base risk scores in case Arbiter changed the predicted_label
        for p in predictions:
            p.base_risk_score = self.classifier.base_scores.get(p.predicted_label, 0)

        # Step 5: Detect repetition
        self._notify(progress_callback, 5, "Mendeteksi pola serangan berulang...")
        status = self._transition(analysis_id, status, AnalysisStatus.DETECTING_REPETITION.value)

        clusters, members = self.repetition_detector.detect(
            comments,
            predictions,
            analysis_id,
        )

        # Build cluster map for risk scoring
        cluster_map: dict[str, dict[str, Any]] = {}
        for cl in clusters:
            for m in members:
                if m.cluster_id == cl.id:
                    cluster_map[m.comment_id] = {
                        "comment_count": cl.comment_count,
                        "unique_author_count": cl.unique_author_count,
                    }

        # Step 6: Risk scoring
        self._notify(progress_callback, 6, "Menghitung skor risiko...")
        status = self._transition(analysis_id, status, AnalysisStatus.SCORING_RISK.value)

        predictions = self.risk_engine.batch_score(predictions, comments, cluster_map)

        # Save predictions
        self.storage.save_predictions(predictions)

        # Save clusters
        if clusters:
            self.storage.save_clusters(clusters, members)

        # Step 7: Verify
        self._notify(progress_callback, 7, "Memverifikasi hasil...")
        status = self._transition(analysis_id, status, AnalysisStatus.VERIFYING.value)

        # Compute aggregate stats
        stats = self.storage.get_analysis_stats(analysis_id)

        # Update analysis run with counts
        self.storage.update_analysis_status(
            analysis_id,
            AnalysisStatus.WAITING_HUMAN_REVIEW.value,
            total_comments=stats.total_comments,
            harmful_count=stats.harmful_count,
            uncertain_count=stats.uncertain_count,
            high_count=stats.high_count,
            critical_count=stats.critical_count,
        )
        status = AnalysisStatus.WAITING_HUMAN_REVIEW.value

        # Set model version
        run.model_version = self.classifier.get_model_version()

        # Step 8: Generate initial report
        self._notify(progress_callback, 8, "Membuat laporan...")
        status = self._transition(analysis_id, status, AnalysisStatus.GENERATING_REPORT.value)

        self._generate_reports(analysis_id, run, stats)

        # Complete
        self._transition(
            analysis_id,
            status,
            AnalysisStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._notify(progress_callback, 9, "Analisis selesai!")

    def _generate_reports(
        self,
        analysis_id: str,
        run: AnalysisRun,
        stats: Any,
    ) -> None:
        """Generate reports (Gemini or local fallback)."""
        stats_dict = {
            "total_comments": stats.total_comments,
            "category_distribution": stats.category_distribution,
            "risk_distribution": stats.risk_distribution,
            "harmful_count": stats.harmful_count,
            "uncertain_count": stats.uncertain_count,
            "high_count": stats.high_count,
            "critical_count": stats.critical_count,
            "repeated_attack_clusters": stats.repeated_attack_clusters,
            "reviewed_count": stats.reviewed_count,
        }

        # Try Gemini first
        provider = "local"
        summary: ReportSummary

        if self.config.api_status.gemini_available:
            try:
                gemini = GeminiReporter(
                    api_key=self.config.gemini_api_key,
                    model=self.config.gemini_model,
                    temperature=self.config.settings.get("gemini", {}).get("temperature", 0.2),
                )
                summary = gemini.generate_summary(stats_dict, run.name)
                provider = "gemini"
                logger.info("Report generated via Gemini")
            except Exception as e:
                logger.warning("Gemini failed, using local template: %s", e)
                local = LocalReportGenerator()
                summary = local.generate_summary(stats_dict, run.name)
        else:
            local = LocalReportGenerator()
            summary = local.generate_summary(stats_dict, run.name)

        # Generate exports
        predictions = self.storage.get_predictions(analysis_id)
        analysis = self.storage.get_analysis(analysis_id) or run

        csv_path = self.report_service.generate_csv_all(predictions, analysis_id)
        self.report_service.generate_csv_priority(predictions, analysis_id)
        json_path = self.report_service.generate_json(
            analysis,
            stats,
            predictions,
            summary,
            analysis_id,
        )
        html_path = self.report_service.generate_html(
            analysis,
            stats,
            summary,
            provider,
            analysis_id,
        )

        # Save report record
        import json as json_mod

        report = ReportRecord(
            analysis_id=analysis_id,
            provider=provider,
            summary_json=json_mod.dumps(
                {
                    "executive_summary": summary.executive_summary,
                    "key_findings": summary.key_findings,
                    "recommended_actions": summary.recommended_actions,
                    "limitations": summary.limitations,
                },
                ensure_ascii=False,
            ),
            html_path=str(html_path),
            csv_path=str(csv_path),
            json_path=str(json_path),
        )
        self.storage.save_report(report)

    def regenerate_reports(self, analysis_id: str) -> None:
        """Regenerate reports for an existing analysis."""
        analysis = self.storage.get_analysis(analysis_id)
        if not analysis:
            return
        stats = self.storage.get_analysis_stats(analysis_id)
        self._generate_reports(analysis_id, analysis, stats)

    def _notify(
        self,
        callback: Any,
        step: int,
        message: str,
    ) -> None:
        """Notify progress callback if available."""
        if callback:
            with contextlib.suppress(Exception):
                callback(step, message)
