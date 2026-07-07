# verdikta-sdk

Python SDK for the [Verdikta Bounties API](https://bounties.verdikta.org).

## Installation

```bash
pip install verdikta-sdk
```

Or from source:

```bash
git clone <repo-url>
cd verdikta-sdk
pip install .
```

## Authentication

All API calls require an API key. You can provide it in two ways:

1. **Environment variable** (recommended):
   ```bash
   export VERDIKTA_API_KEY="your-api-key-here"
   ```

2. **Constructor parameter:**
   ```python
   from verdikta_sdk import VerdiktaClient
   client = VerdiktaClient(api_key="your-api-key-here")
   ```

## Quickstart

### 1. Discover open bounties

```python
from verdikta_sdk import VerdiktaClient

client = VerdiktaClient()

# List all open bounties
jobs = client.list_jobs(status="open")
for job in jobs:
    print(f"{job.title} — ${job.bounty_usd} — {job.hours_left}h left")

# Search with filters
python_jobs = client.list_jobs(
    status="open",
    search="python",
    min_bounty_usd=100,
    limit=10,
)
```

### 2. Submit work to a bounty

```python
from verdikta_sdk import VerdiktaClient

client = VerdiktaClient()
job_id = "abc123"

# Optional: validate first
result = client.dry_run_submit(job_id, files=["solution.py", "report.pdf"])
print("Validation:", result)

# Submit for real
submission = client.submit(job_id, files=["solution.py", "report.pdf"])
print(f"Submitted! ID: {submission.id}, Status: {submission.status}")
```

### 3. Monitor evaluation results

```python
import time
from verdikta_sdk import VerdiktaClient, NotFoundError

client = VerdiktaClient()
job_id = "abc123"
submission_id = "sub456"

while True:
    try:
        evaluation = client.get_evaluation(job_id, submission_id)
        print(f"Score: {evaluation.score}, Passed: {evaluation.passed}")
        print(f"Feedback: {evaluation.feedback}")
        break
    except NotFoundError:
        print("Evaluation not ready yet, waiting...")
        time.sleep(30)
```

## API Reference

### `VerdiktaClient(api_key=None, base_url="https://bounties.verdikta.org/api")`

Create a client instance.

---

#### `list_jobs(**filters) → List[Job]`

List bounties with optional filters.

| Parameter | Type | Description |
|---|---|---|
| `status` | `str` | Filter by status (e.g. `"open"`, `"closed"`) |
| `work_product_type` | `str` | Filter by work product type |
| `min_hours_left` | `float` | Minimum hours remaining |
| `max_hours_left` | `float` | Maximum hours remaining |
| `min_bounty_usd` | `float` | Minimum bounty in USD |
| `max_bounty_usd` | `float` | Maximum bounty in USD |
| `search` | `str` | Full-text search query |
| `limit` | `int` | Max results to return |
| `offset` | `int` | Pagination offset |

---

#### `get_job(job_id) → Job`

Get full details for a single bounty.

---

#### `get_rubric(job_id) → Rubric`

Get the evaluation rubric/criteria for a bounty.

---

#### `dry_run_submit(job_id, files, filenames=None) → dict`

Validate a submission without committing it. `files` is a list of file paths (str) or file-like objects. Returns the raw API validation response.

---

#### `submit(job_id, files, filenames=None) → Submission`

Upload files and submit to a bounty. Returns a `Submission` object.

---

#### `submit_bundle(job_id, payload) → dict`

Submit a full JSON bundle. `payload` is an arbitrary dict.

---

#### `list_submissions(job_id) → List[Submission]`

List all submissions for a given bounty.

---

#### `get_evaluation(job_id, submission_id) → Evaluation`

Get evaluation results for a specific submission.

---

### Models

#### `Job`
- `id`, `title`, `description`, `status`
- `bounty_usd`, `hours_left`, `work_product_type`
- `created_at`, `updated_at`
- `raw` — full API response dict

#### `Submission`
- `id`, `job_id`, `status`, `submitted_at`, `raw`

#### `Evaluation`
- `id`, `submission_id`, `score`, `passed`, `feedback`, `criteria`, `raw`

#### `Rubric`
- `job_id`, `criteria`, `raw`

### Exceptions

All exceptions inherit from `VerdiktaError`.

| Exception | HTTP Code | Meaning |
|---|---|---|
| `AuthError` | 401, 403 | Invalid or missing API key |
| `NotFoundError` | 404 | Resource doesn't exist |
| `ValidationError` | 422 | Invalid request payload |
| `RateLimitError` | 429 | Too many requests |
| `VerdiktaAPIError` | other | Catch-all for API errors |
| `NetworkError` | — | Connection/timeout failure |

```python
from verdikta_sdk import VerdiktaClient, NotFoundError, AuthError

try:
    job = client.get_job("nonexistent")
except NotFoundError:
    print("Job not found")
except AuthError:
    print("Check your API key")
```

## Known Limitations / Gotchas

1. **Synchronous only** — this SDK uses `requests` and is blocking. For async use, consider running in a thread pool.
2. **No pagination helper** — `list_jobs` returns one page. Use `limit`/`offset` to paginate manually.
3. **File handles** — when passing file paths to `submit()`/`dry_run_submit()`, the SDK opens them for you. When passing file-like objects, you are responsible for their lifecycle.
4. **Timeout** — GET requests timeout after 30s, POST after 60s. These are not configurable yet.
5. **Rate limiting** — the SDK raises `RateLimitError` on 429 but does not implement automatic retry/backoff.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
