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
