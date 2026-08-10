# CyberGuard-ID — Data Dictionary

## Database Tables

### analysis_runs
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Unique analysis identifier (16-char hex) |
| name | TEXT | User-given analysis name |
| source_type | TEXT | "youtube" or "csv" |
| source_url | TEXT | YouTube URL (if applicable) |
| video_id | TEXT | YouTube video ID |
| video_title | TEXT | Video title |
| channel_title | TEXT | Channel name |
| status | TEXT | Workflow state (AnalysisStatus enum) |
| started_at | TEXT | ISO 8601 timestamp |
| completed_at | TEXT | ISO 8601 timestamp |
| total_comments | INTEGER | Total comments processed |
| harmful_count | INTEGER | Comments in harmful categories |
| uncertain_count | INTEGER | Comments classified as C7 |
| high_count | INTEGER | Comments with HIGH risk |
| critical_count | INTEGER | Comments with CRITICAL risk |
| model_version | TEXT | Model version used |
| error_message | TEXT | Error description if failed |

### comments
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Internal comment ID |
| analysis_id | TEXT FK | References analysis_runs.id |
| external_comment_id | TEXT | Original YouTube comment ID |
| parent_id | TEXT | Parent comment ID (for replies) |
| author_hash | TEXT | Anonymized author identifier (USER_XXXXXX) |
| original_text | TEXT | Raw comment text |
| normalized_text | TEXT | Preprocessed text |
| published_at | TEXT | Original publish timestamp |
| like_count | INTEGER | Number of likes |
| is_reply | INTEGER | 1 if reply, 0 if top-level |

### predictions
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Prediction ID |
| comment_id | TEXT FK | References comments.id |
| predicted_label | TEXT | Model prediction (internal_name or "uncertain") |
| confidence | REAL | Top-1 probability [0.0, 1.0] |
| second_label | TEXT | Top-2 label |
| second_confidence | REAL | Top-2 probability |
| margin | REAL | confidence - second_confidence |
| verification_status | TEXT | MODEL_VERIFIED/RECOMMENDED_REVIEW/MANDATORY_REVIEW/UNCERTAIN |
| base_risk_score | INTEGER | Category-based score (0–5) |
| additional_risk_score | INTEGER | Additional indicator score |
| total_risk_score | INTEGER | base + additional |
| risk_level | TEXT | low/medium/high/critical |

### clusters
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Cluster ID |
| analysis_id | TEXT FK | References analysis_runs.id |
| cluster_key | TEXT | Identifier for the cluster group |
| dominant_label | TEXT | Most common label in cluster |
| comment_count | INTEGER | Number of comments in cluster |
| unique_author_count | INTEGER | Distinct authors |
| average_similarity | REAL | Mean cosine similarity |
| risk_level | TEXT | Cluster risk level |
| indication_level | TEXT | none/early/moderate/strong/critical |

### cluster_members
| Column | Type | Description |
|--------|------|-------------|
| cluster_id | TEXT FK | References clusters.id |
| comment_id | TEXT FK | References comments.id |
| similarity_score | REAL | Similarity to cluster center |

### reviews
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Review ID |
| comment_id | TEXT FK | References comments.id |
| reviewer_label | TEXT | Human-assigned label |
| reviewer_risk_level | TEXT | Human-assigned risk |
| decision | TEXT | agree/change_category/false_positive/keep/recommend_hide/recommend_report |
| note | TEXT | Reviewer notes |
| reviewed_at | TEXT | ISO 8601 timestamp |

### reports
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Report ID |
| analysis_id | TEXT FK | References analysis_runs.id |
| provider | TEXT | "gemini" or "local" |
| summary_json | TEXT | JSON structured summary |
| html_path | TEXT | Path to HTML report file |
| csv_path | TEXT | Path to CSV export file |
| json_path | TEXT | Path to JSON export file |
| generated_at | TEXT | ISO 8601 timestamp |

## Export CSV Columns

### All Comments CSV
analysis_id, comment_id, author_hash, published_at, original_text, normalized_text, predicted_label, confidence, second_label, second_confidence, margin, verification_status, base_risk_score, additional_risk_score, total_risk_score, risk_level, reviewer_label, review_decision, review_note

### Priority CSV
comment_id, author_hash, original_text, predicted_label, confidence, margin, verification_status, total_risk_score, risk_level
