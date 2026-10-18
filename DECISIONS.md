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
