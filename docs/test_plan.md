# CyberGuard-ID — Test Plan

## 1. Unit Tests

| Module | Test Area | Expected Result |
|--------|-----------|----------------|
| config | Load YAML configs | All configs parsed without error |
| config | Label mapping | C0-C7 codes map correctly |
| config | Threshold values | Correct default thresholds |
| config | Salt detection | Default salt flagged |
| preprocessing | Empty input | Returns empty string |
| preprocessing | URL replacement | URLs → `<URL>` |
| preprocessing | Mention replacement | @user → `<MENTION>` |
| preprocessing | Slang normalization | Slang → standard form |
| preprocessing | Negation preservation | "tidak", "bukan" preserved |
| preprocessing | Profanity preservation | Swear words preserved |
| classifier | Model not found | ModelNotFoundError raised |
| classifier | Verification thresholds | Correct status assignment |
| classifier | C7 abstention | Low conf/margin → uncertain |
| classifier | Output schema | All Prediction fields populated |
| risk_engine | Base scores | Correct per-category scores |
| risk_engine | Additional indicators | Target/minor/incitement detected |
| risk_engine | Risk levels | Score-to-level mapping correct |
| risk_engine | Batch scoring | All predictions scored |
| repetition | Too few comments | Returns empty |
| repetition | No harmful | Returns empty |
| repetition | Similar harmful | Cluster detected |
| repetition | Indication levels | Correct level determination |
| workflow | Valid transitions | Accepted transitions pass |
| workflow | Invalid transitions | Rejected appropriately |
| workflow | All states exist | 13 states defined |
| storage | CRUD operations | Create/Read/Update work |
| storage | Review overwrite | Latest review kept |
| storage | Stats computation | Aggregates correct |
| storage | SQL injection | Parameterized queries safe |
| report | Local fallback | Template generates summary |
| report | CSV export | Valid CSV file created |
| report | JSON export | Valid JSON structure |
| report | HTML export | Valid HTML with disclaimer |

## 2. Integration Tests

| Scenario | Mock | Expected |
|----------|------|----------|
| YouTube URL success | YouTube API | Comments fetched, classified |
| Invalid URL | — | InvalidURLError |
| Comments disabled | YouTube API | CommentsDisabledError |
| Quota exhausted | YouTube API | QuotaExceededError |
| CSV success | File upload | Comments classified |
| Empty CSV | File upload | Error message |
| Missing model | Model file | Graceful degradation |
| Missing API keys | — | App boots, CSV mode |
| Gemini failure | Gemini API | Local template fallback |

## 3. Smoke Test

```bash
python run.py --check
```

Expected: All system checks pass (Python, config, database, directories).

## 4. Test Isolation

- No real API calls in tests
- Temporary SQLite databases
- Mocked external services
- Environment variables overridden

## 5. Running Tests

```bash
python run.py --test
# or directly:
pytest tests/ -v --tb=short
```
