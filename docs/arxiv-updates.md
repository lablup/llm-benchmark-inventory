# arXiv discovery and two-model updates

The workflow runs at **11:30 Asia/Seoul** (`30 2 * * *`) on GitHub servers,
independently of the user's laptop. GitHub can delay a scheduled run.

## What gets updated

1. `arxiv_watch.py` reads arXiv RSS feeds for cs, econ, eess, math, physics,
   q-bio, q-fin and stat. RSS is a machine-readable list of announcements.
   Only `new` announcements enter from RSS; `pubDate` is stored as `announced_at`,
   separately from submission dates. Each feed retains its own edition date.
   Repeated or older editions do not reset processing. See the
   [official RSS specification](https://info.arxiv.org/help/rss_specifications.html).
   Titles/abstracts still pass the existing benchmark/evaluation/dataset and
   language-model keyword filter before model screening. Relevant papers with
   different wording can be missed.
   A separate OAI-PMH recovery path reads metadata changes for completed UTC
   days across all subject areas. It catches interrupted collection, capped RSS
   feeds and cross-listings without filtering by submission date. On migration
   it starts 30 days back; thereafter it continues from the unfinished day/page,
   with at most 30 recovery requests per run. Every page saves candidate IDs and
   its continuation token; the day advances only after its final page. An expired
   token restarts that unfinished day, with ID deduplication. Remaining days stay
   pending for later runs. OAI modification dates are not first-publication dates;
   recovered papers keep the announcement date unknown unless RSS supplied it.
   See [OAI-PMH recovery](https://info.arxiv.org/help/oa/index.html).
   Completed full-text investigations are skipped by arXiv ID. Unchanged title/
   abstract judgments are reused across sources and days, including the previous
   cache format. Metadata date enrichment alone does not trigger model calls.
   Changed text or screening policy may be screened again; pending body work and
   failed PDF downloads remain eligible.
2. `research_pipeline.py` first sends batches of up to 20 titles and abstracts
   to DeepSeek and GLM independently, without PDFs, inventory tables or official
   resource pages. Only agreement that an abstract is irrelevant skips full-text
   work. Relevant, uncertain, disagreeing, or malformed-but-accounted responses
   proceed to full-text investigation. Cached decisions are bound to the abstract,
   title, prompt and model configuration.
3. For passed candidates, download the PDF and try Poppler text extraction first.
   `pdf_evidence.py` retries with MinerU 2.7.6 when extraction fails, a page has
   sparse/broken text, or table captions/dense numeric columns are detected.
   This deliberately conservative heuristic can send simple tables to MinerU;
   it does not guarantee detection of every complex layout. Preserve physical
   page numbers, table HTML (including merged cells), the original Poppler text,
   the PDF SHA-256 and a page-JSON SHA-256. DeepSeek prepares a draft in the existing CSV schema. Useful
   dataset/question counts and evaluation metrics belong in the definition/task
   fields with their units, versions and conditions. The linked GitHub README or
   Hugging Face dataset card is also fetched.
4. **DeepSeek-V4.1-Flash and GLM-5.3-Flash each audit the same draft and evidence.**
   Their separate requests do not contain each other's votes. Both must approve
   every change, including numerical claims, task language and input modality.
   Both receive the same page-indexed text/table evidence extracted from the
   retained original PDF. These are text-model audits, not visual PDF inspection.
   Extraction disagreements and claims requiring unreadable figures or formulas
   must be rejected. MinerU is a parser, not a third LLM judge.
   An abstract pass alone never authorizes an inventory update.
5. Source quotes, physical page locations, official links, proposal hashes and
   the current inventory row are checked in code. Missing evidence or disagreement
   prevents inclusion without requesting human review. Known-usage parse/evidence
   failures are recorded; authentication, unknown-cost and transport failures stop
   the run with a saved checkpoint.
6. `review_proposals.py` applies agreed changes to the corresponding CSV, then
   regenerates the README, English copy, modality metadata and page data.
   Korean text updates appear in `korean.html`, English text in `english.html`;
   image-input tasks appear in the corresponding `?modality=vision` tab. Task
   language, not the paper's writing language, determines the destination.
   Validation failure rolls back the inventory changes.
7. After commit and deployment, a GitHub issue summarizes actual additions and
   changes and is closed as completed. No changes means no issue.

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
separate operational limits: up to 1,000 abstracts and 100 full-text attempts per
Korean calendar day. Process older pending candidates first. Abstracts use batches
of 20 and 3,000 output tokens; full-text calls use 6,000 output tokens. Requests
remain sequential, with up to two transport retries through the shared runner.
A 90-minute soft budget stops starting work; abstract screening gets at most
30 minutes, reserving time for full-text work. The hosted job allows 150 minutes
for in-flight requests, validation and deployment. Both quotas count attempts,
not successes. Completed records are saved incrementally; untouched candidates
remain pending for the next run. A failed model call can leave a stop checkpoint
that must be inspected, rather than being silently retried. Short
connection tests for both models passed with JSON response format and reasoning
disabled. This does not by itself prove extraction accuracy.

All model calls use the unchanged shared `llm_batch.py` snapshot documented in
`vendor/README.md`. Projects supply jobs and parsers only. Before model calls,
the workflow commits and pushes a stop flag so an interrupted runner cannot
lose its daily checkpoint. A completed paper clears the flag. Inspect recorded
usage and errors before clearing a stop left by a failed run. Bot commits are
deployed by the same run; they do not trigger another workflow.

The daily and elapsed-time limits can leave a backlog. Unprocessed candidates remain in the repository queue without assigning work
to the user. Transient RSS/OAI failures retain the affected source checkpoint while other
sources and cached investigations continue. Source-specific errors and recovery
progress remain in `new-papers.json`. A failed source cannot advance its cursor. Requests are sequential with ten seconds
between metadata pages and before fresh PDF downloads. HTTP 429 retries wait
60, 120, and 240 seconds, or longer when `Retry-After` requests it. Server
cooldowns longer than four minutes are saved for a later run rather than
shortened. Cached PDFs are reused within a run.
See [arXiv API terms](https://info.arxiv.org/help/api/tou.html) for the service
minimum (one request per three seconds, one connection at a time).
PDF failures retry on a later day. Completed
exclusions and evidence failures stay recorded without repeated notifications.
PDFs over 60 pages or 200,000 combined evidence characters and
unsupported official-source websites need another adapter. Scanned pages use
MinerU OCR. GitHub/Hugging Face
cards must be accessible through the implemented source adapters.

## PDF execution environment

Research runs use `ubuntu-24.04`, Python 3.12, Poppler and MinerU 2.7.6's
`pipeline` backend with CPU PyTorch 2.7.1 / torchvision 0.22.1. The shared
`.github/actions/pdf-tools` action installs these only for full-text runs and
the separate PDF smoke workflow, not ordinary site deployments or abstract tests.
Standard public Linux runners provide 4 CPUs and 16 GB RAM; see
[GitHub runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
No paid GPU runner or external PDF API is required by this configuration.

`prepare_mineru.py` downloads layout/OCR/table weights at the fixed
PDF-Extract-Kit revision recorded in `pdf_evidence.py`. Actions caches these
weights separately from paper evidence; changing the revision requires changing
the cache key. Only the MinerU version and CPU torch pair are pinned, not every
transitive Python dependency. The smoke workflow checks installation compatibility.
Formula recognition is disabled to bound CPU memory/runtime; formula-dependent
claims cannot be cleared through this adapter alone. Parsing is sequential, with
a ten-minute timeout per fallback. There is no new daily paper-count cap. The
existing 90-minute work budget still applies, so large PDFs can leave a backlog.
MinerU temporary images and duplicate PDFs are removed after each attempt.
Missing table HTML, missing physical pages, timeout or parser failure never
falls back to accepting a known-bad Poppler extraction. It stays pending for a
later daily attempt. Previously completed investigation records are not erased.

Run **Validate PDF extraction on hosted CPU** (`pdf-smoke.yml`) manually to test
plain text, a merged-cell table, and a scanned page without model credentials,
discovery, inventory edits or deployment. Its artifact records timings and
page evidence. `smoke_pdf_evidence.py --real-pdf PATH` additionally checks the
first two physical pages of a local research PDF, explicitly as a test subset.

## Records and recovery

`new-papers.json` stores the discovery queue and investigation status in GitHub;
it is not part of the public website artifact. `research/proposals.json` stores
abstract screening records separately from full-text drafts, source hashes,
model votes, the exact reviewed content hash, and application results. New investigations record the actual extraction model;
successful automatic applications record `applied_at`.

Model requests attach an explicit physical page number to each page's text,
including blank pages. The stored page JSON and original PDF retain their hashes.

### Re-audit an exact quote with an incorrect page number

The optional Pages workflow input `citation_replay_run` accepts a completed run
ID whose seven-day research artifact is still available. It skips discovery,
PDF installation/extraction and draft generation. `replay_citations.py` checks
the original PDF/page-JSON hashes and refuses replay if inventory CSVs, English
display copy or modality data have changed since that run's starting commit.

Only saved `needs_evidence` drafts rejected for quote location are considered.
A quote can move to another page only if its exact text, with the existing
whitespace normalization, occurs on exactly one physical page. Missing,
paraphrased, case-altered or ambiguous quotes retain the original failure.
Every other evidence/schema check still runs. This is not approval by itself.
At most ten eligible drafts receive fresh independent DeepSeek and GLM audits
against the retained PDF evidence and newly fetched official cards. Both votes
and the normal application checks are required to update inventory data.

The original response and archived failure remain available. The new record
stores `citation_replay`, the source run, original investigation time, corrected
page locations and quote hashes. A replayed record is not automatically replayed
again. Budget/crash checkpoints cover the new audit calls. Ordinary scheduled
runs keep their existing deduplication behavior.

```bash
python3 replay_citations.py --artifact PATH --base-commit FULL_SOURCE_RUN_SHA \
  --source-run RUN_ID --dry-run  # offline validation, no model calls
```

`build_research_records.py` exports only applied changes to `updates.json`.
The website shows the application date, benchmark name, a short description
of an addition or the fields changed, and source links. It does not display
excluded candidates, disagreements, or notices about having no updates.

Unapplied investigation results are archived in `research/archive/YYYY-MM/`,
using the investigation timestamp in Korea time. Each immutable snapshot has a
readable Markdown record and JSON evidence, with monthly indexes. A repeated
build creates no duplicate; a changed result creates a new snapshot. Old
snapshots remain even if a later investigation succeeds. Candidates still
waiting for investigation are not classified as exclusions. Abstract-only
exclusions get separate `*-abstract-*.md`/JSON records that explicitly say the
PDF was not read. Full-text audit agreement must not be inferred from an
abstract relevance judgment. Historical missing
model names stay unknown; an initial exclusion without audit votes must not be
presented as two-model agreement. Archives remain in GitHub, linked from the
website, and are excluded from the Pages artifact.

Original PDFs and page JSON remain in the ignored `.research-cache` while the
runner works. They and MinerU diagnostics/API response logs are retained as
Actions artifacts for seven days, readable by those who
can access this public repository. Keys are not included in requests' saved
metadata or logs. They are not committed to Git or included in GitHub Pages.
After artifact expiry, hashes, original arXiv URLs and investigation decisions
remain in the repository; the exact downloaded PDF is no longer guaranteed to
be recoverable from Actions. This is short-term diagnosis, not permanent storage.

Automatic updates preserve unrelated rows and roll back on validation failure.
A stale draft is skipped. Notification markers prevent duplicate digests after
retries, even if a run created an issue before losing its local state. Old
human-approval commands remain available in code for the disabled legacy mode;
current operation does not request human review.

GitHub assignment/mentions use the account's existing email notification
settings. The workflow cannot confirm inbox delivery. The former 100-candidate
review issue is closed and does not need to be completed.

```bash
python3 -m unittest -v test_arxiv_watch.py test_research.py test_research_records.py test_abstract_screening.py test_pdf_evidence.py test_replay_citations.py
python3 validate_inventory.py
python3 arxiv_watch.py                  # discover only
python3 research_pipeline.py --dry-run  # inspect one abstract batch request, no inference
python3 research_pipeline.py --screening-smoke # at most 10 cached abstracts; no PDFs
python3 research_pipeline.py            # investigate, using configured credentials
python3 review_proposals.py             # apply agreed changes; requires GH_TOKEN
python3 build_research_records.py       # refresh public history and monthly archives
```

Pull requests run offline checks without production secrets. Scheduled/manual
runs collect and investigate; other production runs synchronize accepted changes
and deploy. Check [workflow runs](https://github.com/lablup/llm-benchmark-inventory/actions/workflows/pages.yml)
for errors.

For a live abstract-format smoke test, manually dispatch the Pages workflow with
`screening_smoke=true`. It skips discovery, PDF tooling, inventory application
and notifications, and saves up to ten real abstract screenings and their
archives. A response-schema failure makes the smoke run fail visibly while
preserving its records. Hidden cache files are explicitly enabled for the
JSONL/manifest-only artifact paths. The normal schedule uses the complete pipeline. This is not a full-text
acceptance test. No automated model-ranking updates are included.
