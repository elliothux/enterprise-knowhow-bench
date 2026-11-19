import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import bench


class PublicBenchmarkTests(unittest.TestCase):
    def test_business_scores_match_published_receipts(self):
        seen = set()
        for path in (bench.ROOT/'results/cases').glob('*/history.json'):
            history = bench.read(path)
            runs = {s['run']:s for s in history['sessions']}
            for variant in history['variants']:
                suffix = '-clear' if variant['protocol'].startswith('ap-clear-register-') else ''
                case = bench.task_id(history['id'] + suffix)
                for name in variant['sessions']:
                    run = runs[name]
                    with self.subTest(case=case, session=name):
                        self.assertEqual(bench.business(case,run['first_delivery']['text'])['score'],run['score'])
                    seen.add(name)
        self.assertEqual(len(seen),224)

    def test_three_arm_remittance_history_matches_public_scorer_and_materials(self):
        batch = bench.ROOT / 'results/batches/remittance-distillers-20261119'
        index = bench.read(batch / 'index.json')
        schedule = bench.read(bench.ROOT / 'tasks/schedules/remittance-distillers.json')
        original = bench.read(bench.ROOT / 'tasks/schedule.json')['remittances']
        self.assertEqual(schedule, [dict(row, control='D') for row in original])
        self.assertEqual([row['case'] for row in schedule], [r['case'] for r in index['cases']])
        sessions = set()
        for case in index['cases']:
            name = case['case']
            attachment = (bench.ROOT / bench.TASKS[name]['arms']['D']).read_bytes()
            skill = attachment.split(b'Historical workflow Skill:\n', 1)[1]
            self.assertEqual(hashlib.sha256(skill).hexdigest(), index['plan']['skill'])
            history = bench.read(batch / case['history'])
            self.assertEqual(set(history['arms']), set('ABD'))
            for arm, run in history['arms'].items():
                submission = run['first_submission']
                self.assertEqual(hashlib.sha256(submission.encode()).hexdigest(), run['files']['delivery-001.csv'])
                self.assertEqual(bench.business(name, submission)['score'], case['scores'][arm])
                self.assertEqual(run['score'], case['scores'][arm])
                sessions.add(run['session'])
        self.assertEqual(len(sessions), 48)

    def test_packets_reject_duplicate_or_unassigned_ids(self):
        target = bench.read(bench.ROOT/'evaluation/answer-key.json')['RMT-716']
        first = target[0]
        row = ','.join([first['invoice'],*[f'{v/100:.2f}' for v in first['target'][:4]],first['target'][4]])
        self.assertEqual(bench.business('RMT-716',row)['score'],50)
        self.assertEqual(bench.business('RMT-716',row+'\n'+row)['score'],0)
        self.assertEqual(bench.business('RMT-716',row+'\nI-OTHER,REFER')['score'],0)

    def test_first_delivery_is_immutable(self):
        with tempfile.TemporaryDirectory() as root:
            run = Path(root)/'run'
            subprocess.run([sys.executable,str(bench.ROOT/'bench.py'),'prepare','T-320','--out',str(run)],check=True,capture_output=True)
            work=run/'work/work'
            subprocess.run([work,'read','rules'],check=True,capture_output=True)
            value='ticket,decision,reasons\nT-320,HOLD,DUPLICATE'
            subprocess.run([work,'submit',value],check=True,capture_output=True)
            other=subprocess.run([work,'submit','replacement'],capture_output=True)
            self.assertNotEqual(other.returncode,0)
            subprocess.run([sys.executable,str(bench.ROOT/'bench.py'),'score',str(run)],check=True,capture_output=True)
            result=json.loads((run/'score.json').read_text())
            self.assertEqual((result['score'],result['unassisted_score'],result['submission']),(100,0,value))

    def test_all_frozen_remittance_prompts_match_their_ledgers(self):
        for case, task in bench.TASKS.items():
            if task["type"] == "packet":
                with self.subTest(case=case):
                    rendered = bench.remittance_prompt(bench.ROOT / task["ledger"])
                    self.assertEqual(rendered, (bench.ROOT / task["prompt"]).read_text())

    def test_historical_rules_are_evaluator_only(self):
        fixtures = list((bench.ROOT / "evaluation/historical").glob("*/*.json"))
        self.assertTrue(fixtures)
        catalogue = (bench.ROOT / "tasks/README.md").read_text()
        for task in bench.TASKS.values():
            for source in task["resources"].values():
                self.assertFalse(source.startswith("evaluation/"))
        for path in fixtures:
            self.assertNotIn(str(path.relative_to(bench.ROOT)), catalogue)
            self.assertFalse((bench.ROOT / "mock/historical" / path.parent.name / path.name).exists())

    def test_all_scheduled_inputs_are_public(self):
        schedule=bench.read(bench.ROOT/'tasks/schedule.json')
        self.assertEqual([len(v) for v in schedule.values()],[40,16])
        self.assertEqual(sum(bool(r['control']) for r in schedule['finance']),30)
        for case, task in bench.TASKS.items():
            paths=[task['prompt'],*task['resources'].values(),*filter(None,task['arms'].values())]
            for file in paths:
                self.assertTrue((bench.ROOT/file).is_file(),(case,file))
            if 'fixtures' in task:self.assertTrue((bench.ROOT/task['fixtures']/'incoming.txt').is_file())


if __name__=='__main__':
    unittest.main()
