# arXiv discovery and review

The [new papers page](https://lablup.github.io/llm-benchmark-inventory/papers.html)
lists candidates discovered from arXiv. It is separate from the curated
benchmark inventories. No model API, SMTP account, or third-party scheduler is
required.

## Daily operation

The existing `pages.yml` workflow runs at **11:30 Asia/Seoul** (02:30 UTC).
It runs on GitHub's servers, independently of the reviewer's laptop.
GitHub can delay scheduled runs. A manual **Run workflow** also fetches papers.
Ordinary pushes synchronize review status and deploy without querying arXiv.
Editing, closing, or reopening an `arxiv-review` issue also synchronizes its
checkboxes and deploys the result.

`arxiv_watch.py` searches titles for benchmark, bench, evaluation, or dataset
terms together with language-model and multimodal-model terms. A local rule
requires model relevance and a benchmark-like title, or a dataset/evaluation
title whose abstract introduces a benchmark. These are discovery heuristics:
some relevant papers will be missed and some candidates will be irrelevant.
This does not track every arXiv paper, dataset release, or model leaderboard.
It does not infer the benchmark's language from the paper's writing language.

The first run covers 30 days. Later runs start seven days before the last
successful collection, so interrupted runs catch up and recent indexing delays
are covered. Requests are paginated with a three-second delay and transient
errors are retried. A partial, malformed, duplicate, or oversized result set
fails without advancing the checkpoint. Older records and human review state
are retained. IDs are normalized across paper versions. Revisions to papers
outside the submission-date search window are not tracked.

## How to review

1. Open the issue assigned to you, or choose **검토 대기 보기** on the homepage.
2. Read the paper and check its official dataset/code, evaluation tasks, and
   license conditions. The discovery page supplies the original abstract.
3. Check the paper's box in the GitHub issue when you have reviewed it. Record
   **추가**, **보류**, or **제외**, with the reason, in a comment.
4. For an accepted candidate, update the appropriate inventory CSV with verified
   evidence, then regenerate and validate the site data. Checking a box or
   writing a comment alone never edits the curated CSVs.
5. Close the issue once all items have been reviewed. Closing it with unchecked
   items leaves those items pending. Unchecking an item restores pending status.

Only the checkboxes in the issue body control the site's review status.
Comments provide the decision record but are not automatically interpreted.
New daily issues mention and assign the reviewer. They contain at most 100
papers to keep the issue usable and below GitHub's body limit. Additional
unannounced candidates remain visible on the page and enter subsequent daily
issues. A rerun on the same Korean calendar day does not create another digest
or overwrite a reviewer's edits.

## GitHub email notifications

In [notification settings](https://github.com/settings/notifications), enable
email for participating conversations and mentions. Set a verified address as
the default notification address and check any organization-specific routing
for `lablup`. Do not ignore this repository. Optionally choose **Watch → Custom
→ Issues** on the repository to subscribe to all its issues.

The workflow creates GitHub notifications. Actual email delivery depends on
these account and organization settings; it cannot verify mailbox delivery.
Change the assignee using repository variable `ARXIV_REVIEWER` (default:
`songys`). A reviewer must be assignable in this repository.

## Reliability and troubleshooting

`new-papers.json` is the persisted collection checkpoint and review state.
Daily bot commits keep it in the repository. The collector reconciles all
`arxiv-review` issues, including closed ones, before creating a digest. If a
run creates an issue but fails before committing state, the next run recovers
the existing issue by its marker and paper IDs. Only issues authored by
`github-actions[bot]` or the configured reviewer are used.

The production workflow serializes collection and deployment. It grants
`contents: write`, `issues: write`, `pages: write`, and `id-token: write` to the
deployment job. Pull requests run offline validation only. A bot commit does
not trigger a new workflow, so the same run uploads and deploys the refreshed
files. A concurrent human push can reject the state push; rerun the workflow
instead of force-pushing. A failed collection or issue request prevents that
run's deployment and leaves the last successful public page in place.

The page warns if the last successful collection is more than three days old.
Check [workflow runs](https://github.com/lablup/llm-benchmark-inventory/actions/workflows/pages.yml)
for failures, disabled schedules, missing permissions, or arXiv outages.
GitHub may disable schedules in public repositories after prolonged inactivity.
Routine successful collection commits provide ongoing repository activity.

Local commands (Python standard library only):

```bash
python3 -m unittest -v test_arxiv_watch.py
python3 validate_inventory.py
# Fetch papers and preview the next issue without sending notifications:
python3 arxiv_watch.py --preview /tmp/arxiv-review.md
# GH_TOKEN must be supplied securely by the environment for real issue writes:
python3 arxiv_watch.py --github
python3 arxiv_watch.py --github --issues-only
```

The preview command updates the local JSON but does not call GitHub. The site
packager (`build_pages.py`) copies an explicit public-file list and tracked
assets into a fresh `_site/` directory. It excludes local drafts and source
scripts. Existing license-check dates remain unchanged by discovery runs.

Sources: [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html),
[GitHub scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[GitHub notification settings](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications).
