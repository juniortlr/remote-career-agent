import json
from pathlib import Path
import tempfile
import unittest
from career_agent.models import Job, evaluate
from career_agent.sources import parse_wwr, discover
from career_agent.store import Store, canonical_url
from career_agent.tailoring import prepare
from career_agent.submission import DisabledSubmission

ROOT = Path(__file__).resolve().parents[1]

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.job = Job(**json.loads((ROOT / 'examples/job.json').read_text()))
        self.profile = json.loads((ROOT / 'examples/profile.json').read_text())

    def test_qualified_requires_evidence_and_confirmed_currency(self):
        self.assertEqual(evaluate(self.job)['decision'], 'qualified')
        self.job.paid_in_usd = None
        self.assertEqual(evaluate(self.job)['decision'], 'needs_clarification')
        self.job.brazil_eligible = False
        self.assertEqual(evaluate(self.job)['decision'], 'excluded')

    def test_low_salary_excluded(self):
        self.job.monthly_usd = 3000
        self.assertEqual(evaluate(self.job)['decision'], 'excluded')

    def test_reject_invalid_flags_and_salary(self):
        for field, value in [('remote', 'false'), ('monthly_usd', float('nan'))]:
            with self.assertRaises(ValueError):
                Job(**(self.job.to_dict() | {field: value}))

    def test_persistence_and_duplicate_url(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'career.db'
            store = Store(path)
            key = store.add(self.job)
            duplicate = Job(**(self.job.to_dict() | {'source': 'another'}))
            self.assertEqual(store.add(duplicate), key)
            package = prepare(self.job, self.profile)
            store.save_draft(key, package)
            store.close()
            reopened = Store(path)
            self.assertEqual(len(reopened.jobs()), 1)
            self.assertEqual(reopened.applications()[0]['package'], package)
            reopened.close()

    def test_different_query_job_ids_are_not_deduplicated(self):
        self.assertNotEqual(canonical_url('https://example.com/job?id=1'), canonical_url('https://example.com/job?id=2'))

    def test_only_verified_evidence_and_no_invented_answer(self):
        self.profile['evidence'].append({'id':'unsafe','text':'Python data pipelines at NASA', 'verified':False})
        result = prepare(self.job, self.profile)
        self.assertNotIn('unsafe', [x['evidence_id'] for x in result['resume_bullets']])
        self.assertEqual(result['resume_bullets'][0]['evidence_id'], 'e1')
        self.assertIsNone(result['answers'][0]['answer'])
        self.assertEqual(result['answers'][0]['status'], 'needs_clarification')

    def test_rss_does_not_assume_usd_or_brazil(self):
        xml = b'<rss><channel><item><title>Example: AI Engineer</title><link>https://example.com/job</link><description>Remote role</description></item></channel></rss>'
        job = parse_wwr(xml)[0]
        self.assertEqual(job.title, 'AI Engineer')
        self.assertIsNone(job.brazil_eligible)
        self.assertEqual(evaluate(job)['decision'], 'needs_clarification')

    def test_reject_xml_entities_and_bad_board(self):
        with self.assertRaises(ValueError):
            parse_wwr(b'<!DOCTYPE x><rss/>')
        with self.assertRaises(ValueError):
            discover('greenhouse', '../../private')

    def test_no_live_submission(self):
        with self.assertRaises(NotImplementedError):
            DisabledSubmission().submit(prepare(self.job, self.profile))

if __name__ == '__main__':
    unittest.main()
