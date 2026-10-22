# arXiv discovery and Claude-approved updates

The workflow runs at **11:30 Asia/Seoul** (`30 2 * * *`) on GitHub servers,
independently of the user's laptop. GitHub can delay a scheduled run.

## Claude subscription production policy

Decision 13 supersedes the two-model approval requirement. New abstracts and
full-text drafts use `claude-sonnet-5-5`; a separate Claude request audits each
validated draft against the full extracted evidence and fetched official cards.
Decision 14 additionally requires complete publication evidence and sourced model
scores. Claude approval cannot override these requirements. DeepSeek
and GLM votes are not required and their historical approvals cannot authorize
new changes. Completed screening of unchanged abstracts is reused on migration.

The official Claude Code CLI is pinned to 2.1.304. It uses only repository secret
`CLAUDE_CODE_OAUTH_TOKEN`, with isolated settings/HOME, no tools, no MCP servers,
and no API-key or cloud credentials. OAuth tokens never enter a custom API client.
The owner confirmed extra usage is disabled. On quota/authentication/runtime
failure, stop without a paid fallback. The CLI's token-cost estimate is not a
billing statement. See the [official CLI reference](https://code.claude.com/docs/en/cli-reference)
and [authentication documentation](https://code.claude.com/docs/en/authentication).

The earlier read-only subscription smoke (39375151752) and paper trial
(39375393782) remain diagnostic history. The latter correctly rejected an
unsupported QASU repository-license claim; it did not update the inventory.
Production now invokes the official CLI directly so a variable number of papers
can be processed sequentially with individual checkpoints.

## Research status page and daily summary

`build_research_status.py` (decision 22, item 4) derives `research-status.json`
from `new-papers.json`, `research/proposals.json` and `updates.json`: a stage per
collected paper (표에 반영, Claude 검증 대기, 근거 부족 보류, 본문 조사 후 제외, 초안
형식 검사 거부, 공식 자료 확인 실패, PDF 추출 실패, 초록 선별에서 제외, 본문 조사 대기),
its reason, retry date and, when published, the inventory link; plus per-day counts
built from the daily attempt lists. The file has no generation timestamp, so the
validate job checks it is current like `updates.json`. `papers.html#research`
renders it with a 14-day table and a filterable paper list, and the landing page
shows the latest day's line. After each scheduled or manual research run the
workflow runs `build_research_status.py --notify`, which appends one line per day
(idempotent by a `<!-- research-log:DAY -->` marker) to the open `research-log`
issue "[조사 일지]", creating it once, and writes the same line to the step summary.

## Current publication requirements

Decision 14 withdrew QASU's publication. QASU remains `held` in the research
ledger, including its former approval and publication history, but is absent
from the public CSV, page data and applied-update list. Scheduled runs skip held
records. Historical decision 13's unknown-field allowance no longer applies.
Other existing entries are preserved; this change is not a retroactive purge.

After the initial evidence draft and official card retrieval, Claude completes
the five license/usage/harness fields and a `recommendations` comparison block.
`publication_checks.py` rejects unresolved fields (including unknown synonyms),
missing usage evidence, missing model scores, nonnumeric values, absent physical
page quotes, unverified source URLs and unsupported public-weight claims.
Explicitly documented restrictions or non-support are allowed. Missing
information cannot be renamed to unsupported/not-applicable to pass the gate.

A separate Claude audit reviews all completed fields and the score table against
full source evidence. Its publication-policy marker and reviewed hash bind the
exact rows, recommendation results, metric, conditions and old-ranking hash.
Old approvals cannot publish under the new policy. The application step repeats
the completeness gate and checks stale inventory, English copy and score data.
All affected files, including `benchmark_top_models.csv`, roll back together if
any validation fails.

The recommendation adapter uses one paper's comparable experiment, preserving
metric, units, version, split and prompting/budget conditions. It sorts using the
metric direction and publishes up to three overall results and, only when
verified, up to three public-weight results. An unevidenced weight status never
makes a model public-weight or closed-weight. The cards retain their existing
layout and expose the paper/date/conditions under the source details. These are
paper-reported results, not a refreshed global leaderboard. Existing unrelated
scores are retained. Official live leaderboard ingestion is not implemented by
this paper-score adapter. Missing required evidence leaves the candidate held
without updating the website or asking the user to read the full paper.

## Historical production migration

Run [39377815541](https://github.com/lablup/llm-benchmark-inventory/actions/runs/39377815541)
revised QASU's unsupported license wording, obtained one Claude approval,
applied the English row and deployed it successfully. The actual inventory
change is [e4bc869](https://github.com/lablup/llm-benchmark-inventory/commit/e4bc8696022da56c24268fe3a107d46ba55a4a48);
notification [#19](https://github.com/lablup/llm-benchmark-inventory/issues/19)
was created after deployment. Public page data matched that deployed commit.
This QASU addition was subsequently withdrawn under decision 14.
The subsequent abstract smoke (39377904060) found no unprocessed/changed abstracts,
so it reused cached screening and made no new model calls. New-abstract parsing
and deduplication are covered by offline tests; this smoke is not a fresh model
quality measurement.

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
2. `research_pipeline.py` routes production to `claude_approval.py`. Claude reads
   batches of up to 20 titles and abstracts. Only a valid irrelevant decision
   skips full-text work; uncertain/relevant candidates continue. A missing or
   malformed response stops the run and is never treated as an exclusion.
3. For passed candidates, download the PDF and try Poppler text extraction first.
   `pdf_evidence.py` retries with MinerU 2.7.6 when extraction fails, a page has
   sparse/broken text, or table captions/dense numeric columns are detected.
   This deliberately conservative heuristic can send simple tables to MinerU;
   it does not guarantee detection of every complex layout. Preserve physical
   page numbers, table HTML (including merged cells), the original Poppler text,
   the PDF SHA-256 and a page-JSON SHA-256. Claude prepares a draft in the existing CSV schema. Useful
   dataset/question counts and evaluation metrics belong in the definition/task
   fields with their units, versions and conditions. The linked GitHub README or
   Hugging Face dataset card is also fetched.
4. After completing usage evidence and model scores, **Claude audits the full
   proposal in a separate request.** It receives the
   full page-indexed evidence and official cards, without any earlier model vote.
   Approval covers every change, numerical claim, language and modality. This is
   a text/table audit, not visual PDF inspection. Conflicting extraction or claims
   requiring unreadable figures/formulas are rejected. MinerU remains a parser.
   An abstract pass alone never authorizes an inventory update.
5. Source quotes, physical page locations, official links, proposal hashes and
   the current inventory row are checked in code. Missing evidence or a rejected audit
   prevents inclusion without requesting human review. Known-usage parse/evidence
   failures are recorded; authentication, unknown-cost and transport failures stop
   the run with a saved checkpoint.
6. `review_proposals.py` applies complete, Claude-approved inventory and model-score
   changes to the corresponding CSV files, then
   regenerates the README, English copy, modality metadata and page data.
   Korean text updates appear in `korean.html`, English text in `english.html`;
   image-input tasks appear in the corresponding `?modality=vision` tab. Task
   language, not the paper's writing language, determines the destination.
   Validation failure rolls back the inventory changes.
7. After commit and deployment, a GitHub issue summarizes actual additions and
   changes and is closed as completed. No changes means no issue.

Claude can make errors. Approval is combined with source checks and mandatory
publication completeness. Claude may report evidenced license terms but cannot
grant new permissions. A code license is not proof of dataset rights. The initial
internal draft may still use unknown placeholders while gathering sources; it
cannot be published in that form. All required information and model scores must
be completed before the final approval and write transaction.

## Connection and limits

Configuration is in `research/config.json`. The production route is
`pipeline: claude_subscription`, `approval_policy: claude_only`. Only the OAuth
secret is passed to research. The shared Token Factory runner remains available
for historical tests, but production no longer calls it or requires its key.

Limits remain 1,000 abstracts, 100 full-text attempts per Korean calendar day,
20 abstracts per batch and 90 minutes of work, with at most 30 minutes for new
abstract screening. Each CLI request is limited to two turns and ten minutes.
The hosted job allows 150 minutes including extraction, validation and deployment.
PDF extraction (decision 22) fails before MinerU when the Poppler text alone exceeds
the context budget, keeps a paper whose one table MinerU could not parse (the page
is marked `table_missing` and keeps its Poppler text), and drops the duplicate
Poppler copy on plain-text pages when both copies would exceed the budget. A PDF
that still cannot be extracted is retried after 7 days, then monthly
(`analysis_retry_after` in `new-papers.json`), instead of every day.
The draft validator accepts the official link as papers print it, without a scheme or
`www.`, with a trailing slash or broken across a line, as long as the proposed value is
the https form of a URL the PDF names (`research_pipeline.link_in_pdf`). The drafter and
auditor prompts treat a quoted task example, prompt template, instruction or answer
option in English or Korean as sufficient task-language evidence (decision 22, items 2
and 3).
Completed screenings and papers are persisted incrementally. Pending Claude
audits are resumed before new work; completed abstracts are not screened again
merely because the model changed. `--screening-smoke` processes at most ten
previously unprocessed/changed abstracts without PDF work.

Before an audit, the ledger saves `awaiting_claude`, the source run, context hash
and exact draft. A missing/malformed answer is not a rejection or approval.
The next run restores its seven-day evidence artifact, checks provenance and
current rows, and resumes the audit without drafting again. A draft that can no
longer be resumed (expired/missing artifact, changed hash, provenance or rows,
or a default value renamed after the draft was saved) holds only that candidate
as `needs_evidence` with the error in `resume_error`; later candidates and the
day's new papers still run, and a re-audit request revisits the held one.
Token and quota failures still stop the run so the budget checkpoint is kept
(decision 21 follow-up, 2026-10-22).
A completed response cache is bound to the full prompt hash. Old Token Factory
budget stop flags are preserved as historical records, not reused as Claude limits.
Already approved work can still be applied and deployed if a later call fails;
the workflow retains the failure status so the interruption remains visible.

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

### Revisit a held draft with Claude

Dispatch Pages with both `citation_replay_run` (original research artifact run)
and `claude_replay_key` (one held arXiv ID). The source PDF/page hashes and the
inventory baseline must still match. Claude revises the saved draft against the
original evidence and newly fetched official cards. The normal schema, quote,
page and link checks run again, followed by a fresh independent Claude audit.
Only approval of that final draft enables application. Historical monthly
snapshots remain unchanged. The legacy two-model `replay_citations.py` entry point
refuses execution under the new production policy.

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
python3 research_pipeline.py --dry-run  # validate configuration, no inference
python3 research_pipeline.py --screening-smoke # at most 10 cached abstracts; no PDFs
python3 research_pipeline.py            # investigate, using configured credentials
python3 review_proposals.py             # apply Claude-approved changes; requires GH_TOKEN
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
