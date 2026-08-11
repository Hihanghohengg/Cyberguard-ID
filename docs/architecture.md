# CyberGuard-ID — Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Streamlit UI                      │
│  app.py ← pages/[1-5]_*.py ← src/ui/*              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Workflow Engine                         │
│  src/workflow/engine.py + state.py                   │
└──┬──────┬──────┬──────┬──────┬──────┬───────────────┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌──────┐
│ YT  ││ CSV ││Pre- ││Class││Rep. ││Risk  │
│Svc  ││Svc  ││proc ││ifier││Det. ││Eng.  │
└─────┘└─────┘└─────┘└─────┘└─────┘└──────┘
                                      │
                     ┌────────────────┤
                     ▼                ▼
              ┌───────────┐   ┌────────────┐
              │  Report   │   │   Gemini   │
              │  Service  │   │  Reporter  │
              └─────┬─────┘   └────────────┘
                    │
              ┌─────▼─────┐
              │  SQLite   │
              │  Storage  │
              └───────────┘
```

## Data Flow

```
URL/CSV → Validate → Collect → Process Metadata & Optional Anonymization → Preprocess →
  Classify → Detect Patterns → Score Risk → Verify →
  Human Review Queue → Generate Report → Export
```

## Workflow State Machine

```
INITIALIZED → VALIDATING_INPUT → COLLECTING_COMMENTS →
  PREPROCESSING → CLASSIFYING → DETECTING_REPETITION →
  SCORING_RISK → VERIFYING → WAITING_HUMAN_REVIEW →
  GENERATING_REPORT → COMPLETED

Any state → FAILED
COLLECTING_COMMENTS → COMPLETED_NO_DATA
```

## Storage Design

- **SQLite** (`artifacts/cyberguard.db`): analysis_runs, comments, predictions, clusters, cluster_members, reviews, reports
- **joblib**: trained model pipeline
- **JSON**: model metadata, report data
- **CSV**: data exports
- **HTML**: formatted reports

## API Boundaries

### YouTube Data API v3 (required for URL mode)
- Video metadata: `videos.list`
- Comments: `commentThreads.list`
- Replies: `comments.list`
- Error handling: quota, disabled, not found

### Gemini API (optional)
- Only receives aggregate statistics
- Never receives raw comments or usernames
- Used for executive summary generation
- Local template fallback if unavailable

## Failure Handling

| Failure | Response |
|---------|----------|
| No API key | CSV mode; setup instructions |
| No model | Boot app; show training instructions |
| YouTube quota | Error message + CSV suggestion |
| Comments disabled | Clear message |
| Gemini failure | Local template fallback |
| DB error | Logged; user-friendly message |
