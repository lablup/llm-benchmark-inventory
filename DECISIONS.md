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

## 13. Claude alone approves automatic inventory changes (2026-10-20)

The user explicitly retired the two-model approval requirement because of
repeated response-format failures. This supersedes the approval requirements
in decisions 5, 9, 11 and 12: one valid Claude approval of the exact final draft
is sufficient, together with deterministic evidence and inventory checks.
A DeepSeek or GLM approval is neither necessary nor sufficient. Historical
records keep their original policy and are not relabeled as Claude-approved.

Production uses the official subscription-authenticated Claude Code CLI for
abstract screening, draft preparation and a separate final audit. At migration,
GitHub exposed only the Claude OAuth secret, so retaining Token Factory for
screening/drafting would leave scheduled work dependent on a missing credential.
Reuse completed screening of unchanged text. No additional API service or paid
fallback is introduced. Pin the CLI and model; isolate settings, disable tools,
and check OAuth authentication before a call. The owner already confirmed paid
extra usage is off; do not request the same confirmation again.

Keep the 11:30 Korea schedule, RSS/OAI recovery, ID deduplication, source quotes,
physical PDF pages, official resource checks, conservative license fields,
language/modality routing and notifications after deployment. Store pending
Claude audits durably and resume from evidence artifacts after interruption.
Missing, malformed or truncated output never counts as approval. Substantive
rejections remain held. Actual additions/changes alone enter website history.

## 14. Hold QASU and publish only complete entries with model scores (2026-10-20)

The user withdrew QASU's publication and explicitly requested that unknown
fields no longer be allowed in new registrations. Remove only the newly added
QASU row, English copy, modality entry and public update entry; retain its draft,
prior approval and publication history in the held research record. It must not
be automatically re-added by a later run. Other existing inventory rows are not
part of this withdrawal.

Claude approval alone is necessary but not sufficient. Before publishing a new
or changed proposal, require resolved license, commercial-use, modification,
redistribution and lm-eval fields, with exact evidence from the paper or fetched
official resource. Unknown synonyms do not satisfy the requirement. Explicitly
documented non-support or restrictions may be recorded; missing documentation
must not be converted into a claim of non-support. A code license never proves
a dataset license. This replaces decision 13's inherited unknown-field allowance.

Include sourced model scores in the same proposal and approval. Store results
in benchmark_top_models.csv and generate the existing recommendation cards.
Scores must share a metric, units, version, dataset/split and experimental
conditions. Select up to three models from the paper's compared results; label
the source/conditions rather than claiming a current global leaderboard.
Include public-weight models only when weight availability is evidenced, never
invent entries to fill slots. Bind rankings to the reviewed proposal hash,
check for stale data and roll back inventory plus scores together on failure.
Incomplete proposals remain off the public site. Existing unrelated rankings
are preserved; this is not a claim that all historical scores were refreshed.

## 15. Present the landing roadmap as an icon grid with inline SVG (2026-10-21)

The user replaced the axis-and-branch roadmap diagram with a grid of five
entries (text Korean, text English, system resources, image Korean, image
English), each showing a line icon, a title, a one-line description, and the
item count. Draw icons as inline SVG in `index.html`, authored in this
repository, so no third-party image or icon license is involved and colors
follow the shared design tokens. Korean entries carry a "가" badge and English
entries an "A" badge. Keep the descriptions aligned with each detail page's
hero copy. Decision 6 still applies to the surrounding design; only the
roadmap's visual form changes.

## 16. Remove investigation-status badges from public cards (2026-10-21)

The owner will perform the final review and requested removal of labels such
as "일부 확인" (partially verified) from detail pages. Remove these badges
from recommendation cards shared by Korean and English benchmark pages and
from serving reference cards. Keep scores, sources, experimental conditions
and source-access dates available for review. Retain investigation status in
the source data; hiding a badge does not promote any record to verified or
change the publication pipeline.

## 17. Add all-smi to resource monitoring (2026-10-21)

The user approved adding Lablup all-smi after reviewing its monitoring role.
List it under resource monitoring, with GPU/NPU/CPU/memory coverage,
Prometheus/JSON/CSV output, and recording/replay. Use the official
[README](https://github.com/lablup/all-smi#readme) and
[API reference](https://github.com/lablup/all-smi/blob/main/API.md) as sources.
Hardware and drivers determine metric availability. Air-gapped local use
requires preparing the executable, drivers and libraries in advance.
Mark it as an adoption candidate, not an already integrated Benchpress tool.
No representative performance scores are attached to this monitoring tool.

## 18. Record unstated licenses as all rights reserved (2026-10-21)

The user chose two values instead of a single unknown marker. `미표기`
means the paper, dataset card and official repository were checked and state
no license; such a benchmark is treated as all rights reserved, so commercial
use, modification and redistribution read `저작권 전부 보유` and users must
ask the authors before use. `미확인` means the check itself could not be done
(private repository, card not fetched); these rows stay unpublished and are
re-investigated. `확인 불가` and `unknown` are no longer used. The draft
stage of the automated pipeline records `미확인`; the publication stage may
resolve a field to `미표기` only with absence evidence that the code verifies
against the fetched card and the PDF text. The rule is written in CLAUDE.md.

## 19. Keep QASU out of the inventory (2026-10-21)

The user decided not to add QASU (arXiv 2510.26238) after a full re-audit
under the current publication policy. The paper reports conflicting scores
for the same HTML Answer Lookup condition in Table 6 and Table 7 (Qwen3-32B,
Llama3-70B and Amazon Nova Lite differ; GPT-5-mini and Gemini-2.5-Flash
agree), so recommended models cannot be chosen from one consistent source,
and the repository states no license. The ledger keeps the candidate as
`needs_evidence` (its audit was not approved, so `held` does not apply) with
the decision in its reason and a `user_decision` field; the automated run
does not revisit a recorded candidate unless a re-audit is requested.

## 20. Watch serving tools and boards separately, without editing the table (2026-10-21)

The user asked for the serving and resource inventory to be watched
automatically as well. Those entries change through GitHub releases,
repository commits, PyPI uploads and result-page updates rather than arXiv
papers, so a separate watcher (`serving_watch.py`) polls hand-listed sources
in `serving-watch-sources.json` every day, records observations in
`serving-watch.json` and opens one `serving-watch` issue per day when
something changed. It never edits `serving_inventory.csv` or the reference
values; a person checks the source and updates the row, as Decision 1
requires for the benchmark tables. Details: docs/serving-watch.md.

## 21. Name the unchecked value `확인 불가`, not `미확인` (2026-10-22)

The user decided that the two-value scheme of decision 18 stays, but the
value for "the check itself could not be done" is `확인 불가` (could not be
checked), not `미확인`. `미표기(확인한 곳)` is unchanged. The draft stage of
the automated pipeline therefore records `확인 불가` again, and the
publication stage still refuses to publish any row that keeps it. The
scheduled run on 2026-10-22 had failed because a draft saved with
`확인 불가` on 2026-10-21 was re-validated against the renamed default; this
decision makes the saved draft valid. `build_benchmark_inventory.py` still
recognises `미확인` in old data and derives `확인 불가` from it.

## 22. Raise pipeline throughput before relaxing any publication rule (2026-10-22)

A review of two days under the Claude pipeline showed that no paper reached
the page not for lack of candidates but because the 90-minute budget was
spent on PDFs that cannot be extracted (27 of 46 attempts, about 50 minutes,
21 of them retried on both days) and because drafts fell at two formal
rules: the official link had to appear verbatim with `https://` in the PDF
text, and the task language needed an explicit sentence rather than an
English task example. The user approved the following order of work:

1. Remove the PDF waste: fail before MinerU when the Poppler text alone
   exceeds the context budget, keep a paper whose one table MinerU could not
   parse (the gap is marked), drop the duplicate Poppler copy on plain-text
   pages instead of discarding a long paper, and retry a failed PDF after 7
   days (then monthly), not daily.
2. Accept an official link written without a scheme or broken across lines,
   normalised to `https://`.
3. Accept an English or Korean task example, prompt template or instruction
   quoted from the paper as task-language evidence.
4. Publish a research status page and a one-line daily summary so the owner
   can see what was attempted, why it stopped and what reached the page.
5. Re-audit the 20 candidates left as unexplained format failures by the
   previous (DeepSeek) pipeline, among them KULTURE Bench.
6. Retry a rejected draft once immediately with the validator's message, and
   match model scores against table rows with HTML stripped.

Decision 14 (model scores and complete rights evidence before publication)
stays in force.

## 23. Record the API-equivalent cost of each day's Claude calls (2026-10-22)

The pipeline calls Claude with the subscription token, so no invoice shows what a
day of research used. The owner asked for the cost to be recorded as "API 환산
비용": the `total_cost_usd` the Claude Code CLI reports for each fresh call (what
the API would have charged; cached replays are free) is summed into the day's
run record (`claude_daily_runs[day].calls`, `.cost_usd`), published in
`research-status.json`, shown as a column on the status page and appended to the
daily summary line in the "[조사 일지]" issue. 2026-10-22 was back-filled from the
run artifacts: 65 calls, $25.74 (42 drafts, 13 completions, 4 votes, 2 draft
retries, 4 abstract-screening batches; all claude-sonnet-5-5).
