# arXiv discovery, investigation, and approval

The daily workflow runs at **11:30 Asia/Seoul** (`30 2 * * *`) on GitHub's
servers. It does not require the reviewer's laptop. GitHub may delay a run.

## Current deployment status

Discovery and approval handling are installed. **Model-based investigation is
disabled until a provider, model, prices, and API secret are configured.**
The page displays this state. Collected papers are an investigation queue,
not a reading assignment. No raw-paper review issues are created.

## What changed after inspecting the original research

The September inventory used original papers and official sources, structured
per-benchmark JSON, and scripts mapping benchmark IDs to CSV rows. The local
research archive contains 57 PDFs and separate verification records. It was
not a continuously running arXiv-to-inventory service.

The new pipeline follows that sequence:

1. `arxiv_watch.py` discovers candidates and retains the collection checkpoint.
2. `research_pipeline.py` downloads PDFs, records SHA-256 hashes, and extracts
   physical pages with `pdftotext -layout`. It processes at most five papers
   per Korean calendar day, starting with the newest unprocessed candidates.
3. The model proposes complete rows in the existing Korean/English CSV schema,
   reusing existing IDs. Each changed factual field has a page and a short
   quotation. Quotations must occur on that page. Dataset language needs its
   own evidence; the paper's writing language is insufficient.
4. The official resource URL must occur in the PDF. The pipeline fetches the
   linked GitHub repository README or Hugging Face dataset card. Unsupported
   sites and unavailable resources remain `needs_evidence`.
5. A separate model call compares the change with the PDF and official card.
   This second pass uses the same configured model. It is not independent
   human verification or a guarantee of correctness.
6. Only proposals passing both checks enter a GitHub issue, at most five per
   day. The issue shows the actual before/after fields, English display copy,
   source pages, and remaining uncertainties.
7. Approval applies the exact proposal, rebuilds the README and site data,
   validates them, commits, and deploys. The bot confirms after deployment.

The raw PDF and full text stay in an ignored local cache. The repository keeps
short evidence excerpts, source hashes, proposals, and decisions. Diagnostic
API response logs are retained as Actions artifacts for seven days; these are
accessible to people who can read this public repository. API keys are never
included in jobs or logs.

## Reviewer commands

Post exactly one command per comment in the proposal's issue:

- `추가 2610.12345`: apply the displayed proposal to the inventory.
- `보류 2610.12345`: retain the proposal without repeated notifications.
- `제외 2610.12345`: reject it without changing the inventory.

Replace the example ID with the issue's arXiv ID. A held proposal may later be
accepted or rejected. Accepted/rejected proposals are terminal; corrections
require a new investigation. Editing an old comment does not undo a decision.
Checkboxes and closing an issue do not change the inventory.

Only the configured reviewer (`ARXIV_REVIEWER`, default `songys`) can apply
commands. A command must belong to a bot-authored proposal issue containing
the saved proposal hash. Duplicate comments are idempotent. If the original
CSV row or its English copy changed after investigation, approval fails instead
of overwriting it. Check the failed Actions run and regenerate the proposal.
If any part of a review synchronization fails, all its CSV writes roll back.

GitHub assignment/mentions use the reviewer's existing email notification
settings. The workflow cannot confirm delivery to an email inbox. The former
100-candidate issue is obsolete and does not need to be completed.

## Connect the model service

1. Select a provider/model and confirm its current input/output prices.
2. Add `OPENROUTER_API_KEY` or `OPENAI_API_KEY` in repository **Settings →
   Secrets and variables → Actions → New repository secret**. Never paste a
   key in an issue, this file, or chat.
3. Configure `research/config.json`: provider (`openrouter` or `openai`), model,
   USD prices per million tokens, daily paper limit, and budget. Leave
   `enabled: false` while preparing settings.
4. Use `python3 research_pipeline.py --dry-run` with the configuration enabled
   locally to inspect the request and cost estimate before the first paid run.
   The dry run downloads one PDF but makes no model call and writes no queue
   decisions. Set `enabled: true` in GitHub only after validating configuration.
5. Run the Pages workflow manually and inspect its first investigation results.

All model calls use an unchanged snapshot of the shared
`~/weekly-planner/scripts/llm_batch.py`; see `vendor/README.md`. The project
supplies jobs and parsers, not a separate API client. Calls are sequential,
with shared smoke checks, retries, balance checks where available, and cost
recording. The default **$1 daily stop threshold is a proposed configuration,
not an exact billing guarantee**: a completed request can exceed its estimate.
No model calls occur while disabled.

Before a paid call, the daily ledger records a stop flag. A failed call or
runner interruption leaves that day's research blocked to prevent an unnoticed
second allowance. Inspect the saved logs and actual spend before clearing the
flag or starting another day. Failed runs still persist the research checkpoint.

## Scope and limits

- Discovery covers a keyword-filtered arXiv submission window, not all papers,
  dataset releases, or leaderboard changes. First run: 30 days; later runs:
  seven days before the last successful checkpoint. Pagination must complete
  before the checkpoint advances. Old paper revisions outside this window
  are not tracked.
- The five-paper daily limit can leave a backlog. Unprocessed records are
  visible without creating reviewer tasks. PDF download failures retry on a
  later day. Completed `needs_evidence`/`exclude` decisions stay recorded and
  need an explicit re-investigation to be reconsidered.
- PDFs over 60 pages, over 150,000 extracted characters, scanned PDFs, and
  unsupported resource sites require another extraction/source adapter.
- New entries retain **확인 불가** for dataset license, commercial use,
  modification, redistribution, and lm-eval support. The pipeline does not
  infer dataset rights from a code license or relax existing judgments.
- **Recommended-model rankings are not updated by this pipeline.** The previous
  score-research JSON and `merge_results.py` remain the reference for a later
  score-specific adapter. Scores need explicit table/metric/setting verification;
  this implementation handles benchmark descriptions and categorization.
- Existing license-check dates are preserved. Adding a paper does not recheck
  every benchmark's license.

## Validation and operations

```bash
python3 -m unittest -v test_arxiv_watch.py test_research.py
python3 validate_inventory.py
python3 arxiv_watch.py                  # discovery only, no notifications
python3 research_pipeline.py --dry-run  # no paid model calls
python3 review_proposals.py             # GH_TOKEN required; applies authorized comments
```

Pull requests run offline checks without production secrets. Scheduled/manual
runs collect and investigate; ordinary pushes/comments synchronize proposals
and deploy. A `GITHUB_TOKEN` commit is deployed by the same run. A conflicting
human push must be resolved by rerunning, never force-pushing.

Check [workflow runs](https://github.com/lablup/llm-benchmark-inventory/actions/workflows/pages.yml)
for failure details. The page warns when discovery is over three days old.

Sources: [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html),
[GitHub issue-comment events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#issue_comment).
