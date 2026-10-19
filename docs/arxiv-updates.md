# arXiv discovery and two-model updates

The workflow runs at **11:30 Asia/Seoul** (`30 2 * * *`) on GitHub servers,
independently of the user's laptop. GitHub can delay a scheduled run.

## What gets updated

1. `arxiv_watch.py` searches arXiv metadata using benchmark/evaluation/dataset
   and language-model keywords. This is keyword discovery, not semantic search
   or an agent browsing the whole web. Relevant papers without those terms can
   be missed. The first collection covers 30 days; later collections overlap
   the previous checkpoint by seven days. Pagination must finish before the
   checkpoint advances. Older paper revisions are not automatically researched.
2. `research_pipeline.py` downloads the PDF, extracts physical pages, and
   records its SHA-256 hash. DeepSeek prepares a draft in the existing CSV schema.
   The linked GitHub README or Hugging Face dataset card is also fetched.
3. **DeepSeek-V4.1-Flash and GLM-5.3-Flash each audit the same draft and evidence.**
   Each request is separate and does not contain the other model's vote. Both
   must approve the exact draft. This is agreement on a proposed change, not
   an exact-string comparison between two independently written summaries.
4. The code additionally checks source quotes, page locations, official links,
   proposal hashes, and whether the original inventory row changed. Missing
   evidence or disagreement prevents inclusion. It does not generate a review
   request. Parser/evidence failures with known usage are recorded and skipped;
   authentication, missing-cost, and transport failures stop the run.
5. `review_proposals.py` applies only agreed changes, regenerates the README,
   English copy, modality metadata, and site data, then validates all results.
   The workflow commits the changed CSVs and deploys GitHub Pages.
6. Only after deployment, a GitHub issue summarizes actual additions/changes.
   The issue is immediately closed as completed. It is an informational notice;
   no checkboxes or approval comments are needed. No changes means no issue.

Two models can share an error. Agreement is therefore combined with source
checks and conservative treatment of missing facts. Neither model may grant
new licensing permissions. New entries retain `확인 불가` for license,
commercial use, modification, redistribution, and lm-eval support until those
claims are separately verified. Existing license-check dates remain unchanged.
Recommended-model rankings are not updated by this description/catalog adapter.

## Connection and limits

Configuration is in `research/config.json`. The verified service endpoint is
`https://api.console.lablup.ai/v1`. The workflow reads `TOKEN_FACTORY_API_KEY`
from repository **Settings → Secrets and variables → Actions**. Never put the
key in code, an issue, or chat. Local execution may use `TOKEN_FACTORY_ENV_FILE`
to point to an existing environment file; it is not copied into this repository.

The inherited local configuration records company-provided access with no
charge, confirmed on 2026-10-12. Zero estimated user cost refers to that
allocation, not market pricing or a billing API assertion. Calls still have
strict operational limits: at most five papers per Korean calendar day,
sequential requests, explicit output limits, and a stop checkpoint. Short
connection tests for both models passed with JSON response format and reasoning
disabled. This does not by itself prove extraction accuracy.

All model calls use the unchanged shared `llm_batch.py` snapshot documented in
`vendor/README.md`. Projects supply jobs and parsers only. Before model calls,
the workflow commits and pushes a stop flag so an interrupted runner cannot
lose its daily checkpoint. A completed paper clears the flag. Inspect recorded
usage and errors before clearing a stop left by a failed run. Bot commits are
deployed by the same run; they do not trigger another workflow.

The five-paper limit can leave a backlog. Unprocessed candidates remain in the repository queue without assigning work
to the user. Transient arXiv API failures retain the last successful discovery checkpoint and
continue investigation of cached candidates. Discovery errors remain in the repository record. Requests are sequential with ten seconds
between metadata pages and before fresh PDF downloads. HTTP 429 retries wait
60, 120, and 240 seconds, or longer when `Retry-After` requests it. Server
cooldowns longer than four minutes are saved for a later run rather than
shortened. Cached PDFs are reused within a run.
See [arXiv API terms](https://info.arxiv.org/help/api/tou.html) for the service
minimum (one request per three seconds, one connection at a time).
PDF failures retry on a later day. Completed
exclusions and evidence failures stay recorded without repeated notifications.
PDFs over 60 pages or 200,000 extracted characters, scanned documents, and
unsupported official-source websites need another adapter. GitHub/Hugging Face
cards must be accessible through the implemented source adapters.

## Records and recovery

`new-papers.json` stores the discovery queue and investigation status in GitHub;
it is not part of the public website artifact. `research/proposals.json` stores
drafts, source hashes, model votes, the exact reviewed content hash, and
application results. New investigations record the actual extraction model;
successful automatic applications record `applied_at`.

`build_research_records.py` exports only applied changes to `updates.json`.
The website shows the application date, benchmark name, a short description
of an addition or the fields changed, and source links. It does not display
excluded candidates, disagreements, or notices about having no updates.

Unapplied investigation results are archived in `research/archive/YYYY-MM/`,
using the investigation timestamp in Korea time. Each immutable snapshot has a
readable Markdown record and JSON evidence, with monthly indexes. A repeated
build creates no duplicate; a changed result creates a new snapshot. Old
snapshots remain even if a later investigation succeeds. Candidates still
waiting for investigation are not classified as exclusions. Historical missing
model names stay unknown; an initial exclusion without audit votes must not be
presented as two-model agreement. Archives remain in GitHub, linked from the
website, and are excluded from the Pages artifact.

 Full PDFs and text remain in an ignored cache. API response
logs are retained as Actions artifacts for seven days, readable by those who
can access this public repository. Keys are not included in requests' saved
metadata or logs.

Automatic updates preserve unrelated rows and roll back on validation failure.
A stale draft is skipped. Notification markers prevent duplicate digests after
retries, even if a run created an issue before losing its local state. Old
human-approval commands remain available in code for the disabled legacy mode;
current operation does not request human review.

GitHub assignment/mentions use the account's existing email notification
settings. The workflow cannot confirm inbox delivery. The former 100-candidate
review issue is closed and does not need to be completed.

```bash
python3 -m unittest -v test_arxiv_watch.py test_research.py test_research_records.py
python3 validate_inventory.py
python3 arxiv_watch.py                  # discover only
python3 research_pipeline.py --dry-run  # inspect one request, no inference
python3 research_pipeline.py            # investigate, using configured credentials
python3 review_proposals.py             # apply agreed changes; requires GH_TOKEN
python3 build_research_records.py       # refresh public history and monthly archives
```

Pull requests run offline checks without production secrets. Scheduled/manual
runs collect and investigate; other production runs synchronize accepted changes
and deploy. Check [workflow runs](https://github.com/lablup/llm-benchmark-inventory/actions/workflows/pages.yml)
for errors.
