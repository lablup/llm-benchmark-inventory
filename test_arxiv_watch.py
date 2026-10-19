"""Offline regression tests for discovery, recovery, and human review semantics."""
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse
from xml.sax.saxutils import escape

import arxiv_watch as watch

NOW = datetime(2026, 10, 18, 1, 0, tzinfo=timezone.utc)


def empty():
    return {"schema_version": 1, "last_checked_at": None, "papers": []}


def paper(key="2610.12345", title="Example-Bench: A Benchmark for LLM Agents"):
    return {"arxiv_id": key, "title": title, "summary": "We introduce a benchmark for large language models.",
            "authors": ["Example Author"], "published": "2026-10-15T12:00:00Z", "updated": "2026-10-15T12:00:00Z",
            "categories": ["cs.CL"], "url": f"https://arxiv.org/abs/{key}", "first_seen_at": watch.iso(NOW),
            "review_status": "pending", "review_issue_url": None}


def issue(papers, checked=False, day="2026-10-18", author="github-actions[bot]"):
    body = "<!-- arxiv-review:v1:2026-10-18 -->"
    return {"number": 7, "html_url": f"https://github.com/{watch.REPOSITORY}/issues/7",
            "body": body, "state": "open", "user": {"login": author}}


def rss(papers=(), kind="new", date="Sat, 17 Oct 2026 00:00:00 -0400"):
    items = []
    for p in papers:
        items.append(f'''<item><title>{escape(p['title'])}</title><link>{p['url']}</link>
        <description>arXiv:{p['arxiv_id']}v1 Announce Type: {kind} Abstract: {escape(p['summary'])}</description>
        <pubDate>{date}</pubDate><a:announce_type>{kind}</a:announce_type>
        <d:creator>Example Author</d:creator><category>cs.CL</category></item>''')
    return (f'<rss xmlns:a="http://arxiv.org/schemas/atom" xmlns:d="http://purl.org/dc/elements/1.1/">'
            f'<channel><pubDate>{date}</pubDate>{"".join(items)}</channel></rss>').encode()


def oai(papers=(), day="2026-10-17", token="", error=None):
    records = []
    for p in papers:
        records.append(f'''<record><header><identifier>oai:arXiv.org:{p['arxiv_id']}</identifier>
        <datestamp>{day}</datestamp></header><metadata><arXiv xmlns="http://arxiv.org/OAI/arXiv/">
        <id>{p['arxiv_id']}</id><created>{p['published'][:10]}</created><updated>{p['updated'][:10]}</updated>
        <title>{escape(p['title'])}</title><abstract>{escape(p['summary'])}</abstract><categories>cs.CL</categories>
        <authors><author><forenames>Example</forenames><keyname>Author</keyname></author></authors>
        </arXiv></metadata></record>''')
    body = f'<error code="{error}"/>' if error else f'<ListRecords>{"".join(records)}<resumptionToken>{escape(token)}</resumptionToken></ListRecords>'
    return (f'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><responseDate>{watch.iso(NOW)}</responseDate>{body}</OAI-PMH>').encode()


def recovery_state(**extra):
    return {**empty(), "discovery": {"oai": {"next_day": "2026-10-17"}}, **extra}


class CollectionTests(unittest.TestCase):
    def test_rss_uses_announcement_date_and_skips_replacements(self):
        published, rows, count = watch.parse_rss(rss([paper()]))
        self.assertEqual(published, "2026-10-17T04:00:00Z")
        self.assertEqual(rows[0]["announced_at"], published)
        self.assertIsNone(rows[0]["published"])
        for kind in ("replace", "cross", "replace-cross"):
            self.assertEqual(watch.parse_rss(rss([paper()], kind))[1], [])

    def test_oai_recovers_delayed_old_submission_and_all_pages(self):
        delayed = paper(); delayed['published'] = delayed['updated'] = "2026-09-01T12:00:00Z"
        fetch = Mock(side_effect=[oai([delayed], token="page+2%foo"), oai([paper("2610.12346")])])
        saved, sleep = [], Mock()
        result = watch.collect(recovery_state(), NOW, fetch, sleep, feeds=(), checkpoint=saved.append)
        self.assertEqual(len(result['papers']), 2)
        self.assertEqual(result['discovery']['oai']['next_day'], '2026-10-18')
        params = parse_qs(urlparse(fetch.call_args_list[1].args[0]).query)
        self.assertEqual(params, {'verb':['ListRecords'], 'resumptionToken':['page+2%foo']})
        self.assertEqual(saved[0]['discovery']['oai']['next_day'], '2026-10-17')
        self.assertEqual(saved[0]['discovery']['oai']['resumption_token'], 'page+2%foo')
        sleep.assert_called_once_with(10)

    def test_rss_and_oai_deduplicate_and_preserve_review(self):
        old = paper(); old.update(review_status="reviewed", analysis_status="accepted", review_issue_url=issue([])['html_url'])
        state = recovery_state(papers=[old])
        fetch = Mock(side_effect=[rss([paper()]), rss([paper()]), oai([paper()])])
        result = watch.collect(state, NOW, fetch, Mock(), feeds=('cs','stat'))
        self.assertEqual(len(result['papers']), 1)
        kept = result['papers'][0]
        self.assertEqual(kept['analysis_status'], 'accepted')
        self.assertEqual(kept['review_status'], 'reviewed')
        self.assertEqual(kept['published'], old['published'])
        self.assertEqual(kept['first_seen_at'], old['first_seen_at'])
        self.assertIn('announced_at', kept)
        self.assertNotIn('announced_at', state['papers'][0])

    def test_same_feed_edition_is_not_processed_again(self):
        result = watch.collect(recovery_state(), NOW, Mock(side_effect=[rss([paper()]), oai()]), Mock(), feeds=('cs',))
        with patch.object(watch, 'merge_papers') as merge:
            watch.collect(result, NOW, Mock(return_value=rss([paper()])), Mock(), feeds=('cs',))
        merge.assert_not_called()

    def test_partial_failure_retains_page_and_restarts_from_token(self):
        saved = []
        error = watch.URLError('offline')
        fetch = Mock(side_effect=[oai([paper()], token='next'), error])
        result = watch.collect(recovery_state(), NOW, fetch, Mock(), feeds=(), allow_cached=True, checkpoint=saved.append)
        self.assertEqual(result['discovery']['oai']['next_day'], '2026-10-17')
        self.assertEqual(len(result['papers']), 1)
        retry = Mock(return_value=oai([paper('2610.12346')]))
        result = watch.collect(result, NOW, retry, Mock(), feeds=())
        self.assertIn('resumptionToken=next', retry.call_args.args[0])
        self.assertEqual(len(result['papers']), 2)
        self.assertNotIn('oai',result['discovery']['errors'])

    def test_expired_token_replays_only_unfinished_day(self):
        state = recovery_state(papers=[paper()]); state['discovery']['oai']['resumption_token']='expired'
        fetch = Mock(side_effect=[oai(error='badResumptionToken'),oai([paper()])])
        result = watch.collect(state,NOW,fetch,Mock(),feeds=())
        self.assertEqual(len(result['papers']),1)
        self.assertIn('from=2026-10-17',fetch.call_args.args[0])
        self.assertNotIn('resumption_token', result['discovery']['oai'])

    def test_failed_rss_does_not_prevent_oai_or_other_feeds(self):
        fetch = Mock(side_effect=[watch.URLError('offline'),rss([paper()]),oai([paper('2610.12346')])])
        result = watch.collect(recovery_state(),NOW,fetch,Mock(),feeds=('cs','stat'),allow_cached=True)
        self.assertEqual(len(result['papers']),2)
        self.assertNotIn('cs',result['discovery']['rss'])
        self.assertIn('rss:cs',result['discovery']['errors'])
        self.assertIsNone(result['last_checked_at'])

    def test_page_limit_retains_continuation_without_marking_day_complete(self):
        fetch = Mock(return_value=oai([paper()],token='next'))
        result = watch.collect(recovery_state(),NOW,fetch,Mock(),feeds=(),backfill_page_limit=1)
        self.assertTrue(result['discovery']['recovery_pending'])
        self.assertEqual(result['discovery']['oai']['next_day'],'2026-10-17')
        self.assertEqual(result['discovery']['oai']['resumption_token'],'next')

    def test_empty_days_and_migration_start(self):
        result = watch.collect(recovery_state(papers=[paper()]),NOW,Mock(return_value=oai(error='noRecordsMatch')),Mock(),feeds=())
        self.assertEqual(len(result['papers']),1)
        self.assertEqual(result['discovery']['oai']['completed_through'],'2026-10-17')
        result = watch.collect(empty(),NOW,Mock(),Mock(),feeds=(),backfill_page_limit=0)
        self.assertEqual(result['discovery']['oai']['next_day'],'2026-09-18')

    def test_empty_continuation_cannot_close_unfinished_day(self):
        state = recovery_state()
        state['discovery']['oai']['resumption_token'] = 'unfinished'
        with self.assertRaises(ValueError):
            watch.collect(state, NOW, Mock(return_value=oai(error='noRecordsMatch')), Mock(), feeds=())
        self.assertEqual(state['discovery']['oai']['next_day'], '2026-10-17')

    def test_next_day_resumes_from_last_completed_day_without_old_window(self):
        state = recovery_state()
        state['discovery']['oai']['next_day'] = '2026-10-18'
        tomorrow = NOW + timedelta(days=1)
        payload = oai(day='2026-10-18',error='noRecordsMatch').replace(watch.iso(NOW).encode(), watch.iso(tomorrow).encode())
        fetch = Mock(return_value=payload)
        result = watch.collect(state, tomorrow, fetch, Mock(), feeds=())
        self.assertIn('from=2026-10-18&until=2026-10-18', fetch.call_args.args[0])
        fetch.assert_called_once()
        self.assertFalse(result['discovery']['recovery_pending'])

    def test_older_rss_cannot_replace_recent_metadata(self):
        old = paper()
        old.update(title='Revised Benchmark for LLMs',updated='2026-10-17T12:00:00Z')
        state = recovery_state(papers=[old])
        result = watch.collect(state, NOW, Mock(side_effect=[rss([paper()]), oai()]), Mock(), feeds=('cs',))
        self.assertEqual(result['papers'][0]['title'], old['title'])
        self.assertEqual(result['papers'][0]['updated'], old['updated'])

    def test_invalid_xml_ids_dates_and_stuck_pagination_fail(self):
        for payload in (b'<html/>',rss([paper()]).replace(b'Abstract:',b'Missing:'),rss([paper()]).replace(b'Announce Type: new',b'Announce Type: new').replace(b'<a:announce_type>new',b'<a:announce_type>unknown')):
            with self.assertRaises(ValueError): watch.parse_rss(payload)
        for payload in (b'<html/>',oai([paper()],day='2026-10-16'),oai().replace(watch.iso(NOW).encode(),b'2026-10-17T00:00:00Z')):
            with self.assertRaises(ValueError): watch.collect(recovery_state(),NOW,Mock(return_value=payload),Mock(),feeds=())
        state=recovery_state();state['discovery']['oai']['resumption_token']='same'
        with self.assertRaises(ValueError):watch.collect(state,NOW,Mock(return_value=oai([paper()],token='same')),Mock(),feeds=())

    def test_metadata_filter_and_atomic_state(self):
        self.assertTrue(watch.candidate(paper()))
        self.assertFalse(watch.candidate(paper(title='A Faster Training Algorithm')))
        result=watch.collect(recovery_state(),NOW,Mock(side_effect=[rss([paper()]),oai()]),Mock(),feeds=('cs',))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json';watch.save_state(path,result)
            self.assertEqual(watch.load_state(path),result)


class RequestPacingTests(unittest.TestCase):
    def test_retry_after_seconds_date_and_fallback(self):
        self.assertEqual(watch.retry_delay({}, 0), 60)
        self.assertEqual(watch.retry_delay({}, 1), 120)
        self.assertEqual(watch.retry_delay({}, 2), 240)
        self.assertEqual(watch.retry_delay({'Retry-After':'600'},0),600)
        self.assertEqual(watch.retry_delay({'Retry-After':'Sun, 18 Oct 2026 01:05:00 GMT'},0,NOW),300)

    def test_source_specific_long_cooldown_does_not_block_other_source(self):
        error=watch.HTTPError('https://rss.arxiv.org/rss/cs',429,'Limited',{'Retry-After':'600'},None)
        self.addCleanup(error.close)
        state=recovery_state();state['discovery']['oai']['next_day']='2026-10-18'
        with patch.object(watch,'urlopen',side_effect=error) as request, patch.object(watch.time,'sleep') as sleep:
            result=watch.collect_with_cached_fallback(state,NOW,feeds=('cs',))
        self.assertEqual(request.call_count,1);sleep.assert_not_called()
        fetch=Mock(return_value=rss())
        result=watch.collect(result,NOW,fetch,Mock(),feeds=('cs','stat'),allow_cached=True)
        self.assertEqual(fetch.call_count,1)
        self.assertIn('/stat',fetch.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
