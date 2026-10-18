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
