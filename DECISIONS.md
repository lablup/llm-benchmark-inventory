# Decisions

## 1. Automatically discover papers, curate inventory entries (2026-10-18)

New arXiv papers appear on a separate page as review candidates. Existing
benchmark CSVs, license judgments, and recommended models change only after
human review. Automatic discovery does not imply that a paper introduces a
usable benchmark or that its dataset has a particular license.

## 2. Notify through GitHub review issues (2026-10-18)

The user chose GitHub issues instead of a separate outbound email service.
Create at most one daily review issue when unannounced candidates exist and
assign it to the connected GitHub account, `songys`. Email delivery uses the
reviewer's GitHub notification preferences. Do not store a personal email
address or mail credentials in this public repository.

Issue checkboxes record that a paper was reviewed. They do not add a benchmark
to the curated inventory. Record inclusion, deferral, or exclusion in the issue
discussion and make inventory changes separately with source verification.

## 3. Run the daily update at 11:30 Korea time (2026-10-18)

The user requested 11:30 Asia/Seoul for daily collection and review
notifications. Use `30 2 * * *` in GitHub Actions. Execution happens on GitHub's
servers and does not require the reviewer's laptop to be on. GitHub may delay
the scheduled start when runners are busy.

## 4. Investigate before requesting review; apply approval comments (2026-10-18)

The user asked to incorporate the original research process and rejected a
workflow that made them read a large raw-paper queue. This supersedes decision
2's raw digests and checkbox-only review semantics. Preserve decision 3's
11:30 Korea-time schedule and GitHub notification channel.

Prepare evidence-backed CSV changes from paper text and official sources,
then ask the user to review the actual changes. Exact inclusion, deferral, or
exclusion comments control the saved proposal. Inclusion rebuilds and deploys
the inventory after validation. Raw candidates do not generate review tasks.

Implementation defaults are at most five investigations/proposals per day and
a $1 daily stop threshold. These are adjustable defaults, not user-selected
model or spending settings. Provider/model selection and API credentials are
still pending; keep model investigation disabled and disclose that state.
Recommended-model rankings remain outside this first investigation adapter.

## 5. Use Token Factory and apply only two-model agreement (2026-10-19)

The user chose the locally configured Token Factory service, with
DeepSeek-V4.1-Flash and GLM-5.3-Flash. Both models must approve the exact proposed
change against source evidence before it can be applied automatically to this
repository and deployed. A DeepSeek draft is audited separately by both models;
neither audit sees the other's vote. This supersedes decision 4's requirement
for an inclusion comment.

The user explicitly said that disagreement or insufficient evidence should
simply prevent inclusion. Keep those outcomes in the research record without
requesting human review. Notify through GitHub only after actual changes have
been committed and deployed. Preserve the daily 11:30 Asia/Seoul schedule.

Local Token Factory configuration records a company allocation with no charge,
confirmed on 2026-10-12. Record zero estimated user cost on that basis, not as a
claim that public model pricing is zero. Keep the key in GitHub Actions Secrets.

## 6. Use a restrained Apple-inspired design across the site (2026-10-19)

The user rejected the blue-tinted palette and approved a site-wide revision
with white and neutral gray surfaces, dark gray type, and blue limited to
links and primary actions. Use shared design tokens for color, typography,
spacing, navigation, and tables across the landing, Korean, English, serving,
and paper pages. Keep the roadmap as the landing's organizing idea, with
thinner connections and the paper summary below the main navigation.

## 7. Publish applied changes and archive unapplied research by month (2026-10-19)

The user chose GitHub monthly folders for papers discovered and investigated
but not added to the benchmark tables. Preserve their reasons and source/model
records under `research/archive/YYYY-MM/`, using the investigation date in Korea
time. Append new snapshots when a record changes; retain previous snapshots.
Do not present an early exclusion as agreement between both models.

Keep `papers.html` as the existing URL and rename it to update history. Publish
only actual applied changes through `updates.json`, with the application date,
benchmark name, a brief description of additions or changed fields, and source
links. The landing page shows the latest brief update. Link the monthly GitHub
archive from both pages. The user specifically asked not to emphasize an empty
update history, so omit zero-result notices and dates when no update exists.
Preserve the existing daily schedule and agreement/evidence requirements.

## 8. Keep process notes in an ignored local folder (2026-10-19)

The user requested a local process record under `_local/`, excluded from Git.
Keep the pipeline explanation, relevance criteria, and PDF retention behavior
in `_local/PROCESS.md`; commit only the ignore rule and this decision. This does
not change the investigation quota or delete cached PDFs.

## 9. Screen abstracts before reading full papers and increase throughput (2026-10-19)

The user rejected the five-paper daily limit and requested abstract screening
before full-text investigation to reduce token use. Screen title/abstract batches
with both configured models independently. Skip the PDF only when both classify
the abstract as irrelevant; pass relevant or uncertain candidates to full-text
investigation. Abstract judgments cannot authorize a table change. Preserve the
two independent full-text audits and source checks before applying changes.

Implementation defaults are 1,000 abstract screenings and 100 full-text attempts
per Korean calendar day, with 20 abstracts per request. Reserve part of a
90-minute soft run budget for full-text work and allow 150 minutes in the hosted
job for in-flight requests, validation and deployment. Use two transport retries
per model call. These are adjustable implementation limits, not user-selected
quotas. Process older uninvestigated candidates first to avoid starving a backlog.

Use task language and input modality to update the existing Korean/English CSVs
and rebuild their page data: Korean text to `korean.html`, English text to
`english.html`, and image-input benchmarks to the corresponding vision tab.
Extract supported benchmark counts and evaluation metrics into existing content
fields. Model rankings remain outside this adapter; their requested scope was
asked separately. Update the ignored `_local/PROCESS.md` with this process.

## 10. Discover new RSS announcements and recover gaps by metadata changes (2026-10-19)

The user chose new-publication RSS, arXiv ID/processing-record deduplication, and
an independent path to recover interrupted collection. Replace submission-date
search windows with RSS announcement editions. Preserve first announcement dates
separately from submission dates; never label an OAI modification date as first
publication. Read the eight configured RSS feeds and retain the existing relevance
keyword filter and two-model/full-text evidence requirements.

Recover closed UTC days through OAI-PMH metadata changes, persisting every page
and advancing a day only after pagination completes. Start with the previous
30 days on migration, then resume unfinished days. Use a bounded recovery budget
and retain pending work; expired continuation tokens restart the unfinished day.
Deduplicate by arXiv ID and preserve research/review status. Date precision changes
between sources must not repeat an unchanged abstract judgment. Keep 11:30 KST,
the daily investigation limits, and the language/modality page destinations.

## 11. Retry difficult PDFs with MinerU and retain page evidence (2026-10-19)

The user chose abstract screening, related-PDF extraction, conditional MinerU
re-extraction, two-model verification grounded in page-numbered JSON and the
original PDF, and application only after agreement. Keep the existing task-language
and modality routing and strict source checks.

Use the standard GitHub-hosted Ubuntu CPU runner, Python 3.12 and MinerU 2.7.6
pipeline, with cached pinned layout/OCR/table weights. Keep Poppler as the first
extractor. Preserve physical pages, original PDF hashes, structured table HTML
and extraction provenance. Retain originals and page JSON as seven-day Actions
artifacts rather than adding paper contents to the website or repository.

The current models receive text/table JSON derived from the PDF; this does not
claim visual inspection of PDF pages. Reject conflicting extraction evidence
or unsupported figure/formula claims. CPU formula recognition is disabled.
Failing/partial extraction holds the candidate; agreement does not override
missing evidence. The ten-minute per-PDF timeout is an operational safeguard,
not a new daily paper quota. Validate hosted installation and actual extraction
separately from LLM agreement and inventory application.

## 12. Use Claude within the existing subscription only (2026-10-20)

The user chose Claude subscription usage instead of adding metered GPT costs.
Integrate the official Claude Code GitHub Action using the repository secret
`CLAUDE_CODE_OAUTH_TOKEN`, issued with `claude setup-token`. Do not send that
credential through a custom API client or the existing OpenAI-compatible adapter.
Keep the existing shared runner for Token Factory calls.

The initial integration replaces GLM in the independent full-text audit with
Claude, keeping DeepSeek as the draft author and the other auditor. Preserve
the existing two-model abstract screening until its migration is separately
implemented and checked. Require both full-text approvals on the same draft
and evidence before applying any change. Keep the 11:30 Asia/Seoul schedule,
ID deduplication, source checks, and language/modality routing.

Claude must use the subscription allocation only. Do not enable paid extra
usage, spend usage credits, purchase credits, or fall back to an Anthropic API
key, GPT API, cloud provider, or another billable route. Verify that account
extra usage is disabled before the first model call; OAuth authentication alone
does not establish that condition. If authentication or billing mode cannot
be established, stop before calling the model.

On quota exhaustion, save progress and wait for the provider's reset before
resuming. On authentication failure, require credential repair. On interrupted
calls, reconcile saved responses and checkpoints before retrying. Never treat
missing, malformed, or truncated output as approval or substantive disagreement.
Preserve completed work; do not clear stop flags or repeat the entire queue
without inspecting the saved run.

At this decision's creation, the workflow still uses Token Factory and Claude
integration has not been implemented or tested. No Claude token is registered.
The local implementation and recovery instructions are in
`_local/CLAUDE_SUBSCRIPTION_HANDOFF.md`, intentionally ignored under decision 8.

The user subsequently confirmed that automatic usage-credit spending is disabled.
This account-setting prerequisite is satisfied; do not request the same confirmation
again unless evidence shows the setting changed. The repository secret `CLAUDE_CODE_OAUTH_TOKEN` was subsequently confirmed present.
Use the manual subscription smoke before enabling Claude in production.

Authentication trial `39375151752` and saved-paper trial `39375393782`
subsequently completed. Claude returned a valid rejection for QASU's unsupported
repository-license wording. Both workflows are read-only; the scheduled
production model configuration is unchanged. Preserve that distinction when
resuming the production migration.
