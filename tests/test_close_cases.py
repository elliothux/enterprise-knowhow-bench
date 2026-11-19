import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import bench


class CloseCaseTests(unittest.TestCase):
    def test_joint_posting_has_independent_rows_and_requires_the_offset_reason(self):
        keys = bench.read(bench.ROOT/'evaluation/answer-key.json')['net-31']
        rows = [','.join([e['invoice'], *(f'{c/100:.2f}' for c in e['target'][:4]), e['target'][4]])
                for e in keys['receivables']]
        rows.extend(','.join([e['invoice'], f"{e['exposure']/100:.2f}", e['decision'], ';'.join(e['reasons'])])
                    for e in keys['payables'])
        def grade(lines):
            return bench.business('net-31', '\n'.join(lines))
        self.assertEqual(grade(rows)['score'], 100)
        self.assertEqual(grade(rows[:-1])['line_scores'][-1], 0)
        self.assertEqual(grade(rows + [rows[0]])['score'], 0)
        offset = next(i for i,r in enumerate(rows) if 'SETOFF_REVIEW' in r)
        rows[offset] = rows[offset].replace('SETOFF_REVIEW','NONE')
        self.assertEqual(grade(rows)['line_scores'][offset], 60)
        self.assertEqual(grade(rows)['line_scores'].count(100), 23)

    def test_month_end_uses_the_first_submission_line_rubric(self):
        case = 'close-118'
        history = bench.read(bench.ROOT/f'results/batches/month-end-20261119/{case}/history.json')
        for arm in history['arms'].values():
            self.assertEqual(bench.business(case,arm['first_submission'])['line_scores'],arm['line_scores'])
        first_wrong = history['arms']['B']
        self.assertEqual(first_wrong['line_scores'],[100,100,100,100,100,30,100,100])

    def test_both_batches_include_every_planned_arm_and_grade_the_receipts(self):
        for family in ('month-end','joint-close'):
            base=bench.ROOT/'results/batches'/(family+'-20261119')
            plan=bench.read(bench.ROOT/'tasks/schedules'/(family+'.json'))
            index=bench.read(base/'index.json')
            self.assertEqual(plan,index['schedule'])
            sessions=set()
            for row in plan:
                case=row['case']
                arms=bench.read(base/case/'history.json')['arms']
                self.assertEqual(set(arms),set('ABD'))
                for label,trial in arms.items():
                    result=bench.business(case,trial['first_submission'])
                    self.assertEqual(result['score'],index['cases'][case][label]['score'])
                    self.assertEqual(result['line_scores'],trial['line_scores'])
                    sessions.add(trial['session'])
            self.assertEqual(len(sessions),6)

    def test_lockbox_solution_is_unique_and_duplicated_credits_do_not_count(self):
        from evaluation.verify_lockbox import verify
        for case in ('lockbox-41','lockbox-76'):
            with self.subTest(case=case):
                choices=verify(case)
                self.assertEqual(len(choices),12)
                self.assertTrue(any(count>1 for count in choices.values()))
                target=bench.read(bench.ROOT/'evaluation/answer-key.json')[case]
                rows=[[r['invoice'],*r['matches']] for r in target]
                render=lambda: '\n'.join(','.join(row) for row in rows)
                self.assertEqual(bench.business(case,render())['correct_placements'],36)
                rows[0][1]=rows[1][1]
                self.assertEqual(bench.business(case,render())['correct_placements'],34)

    def test_cutoff_wait_counts_as_safe_handling_and_stays_open(self):
        for case,open_items in [('cutoff-19',2),('cutoff-27',3)]:
            target=bench.read(bench.ROOT/'evaluation/answer-key.json')[case]
            rows=[]
            for t in target:
                if 'wait' in t:
                    rows.append(','.join([t['invoice'],'WAIT',t['wait']['owner'],t['wait']['ticket']]))
                else:
                    rows.append(','.join([t['invoice'],*(f'{a/100:.2f}' for a in t['target'][:4]),t['target'][4]]))
            result=bench.business(case,'\n'.join(rows))
            self.assertEqual(result['handling_score'],100)
            self.assertEqual(result['posted_correctly'],8-open_items)
            self.assertFalse(result['exact'])
            self.assertEqual(result['unsafe_postings'],0)

    def test_inspection_rubric_gives_partial_credit_for_separate_finance_fields(self):
        target=bench.read(bench.ROOT/'evaluation/answer-key.json')['pod-47']
        t=target[0]
        row=','.join([t['invoice'], str(t['units']+1), *(f'{t[k]/100:.2f}' for k in ('loss','claim','collectible')),t['owner']])
        result=bench.business('pod-47',row)
        self.assertEqual(result['line_scores'],[75,0,0,0,0,0,0,0])


    def test_native_image_arguments_and_participant_copies(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            adapter=root/'codex'
            adapter.write_text("#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nPath('args.json').write_text(json.dumps(sys.argv[1:]))\n")
            adapter.chmod(0o755)
            trial=root/'trial'
            subprocess.run([sys.executable,str(bench.ROOT/'bench.py'),'run','pod-47','--arm','B',
                            '--out',str(trial),'--codex',str(adapter)],check=True,capture_output=True)
            args=json.loads((trial/'work/args.json').read_text())
            pictures=[Path(args[i+1]) for i,opt in enumerate(args) if opt=='-i']
            originals=bench.TASKS['pod-47']['images']
            self.assertEqual([p.name for p in pictures],[Path(o).name for o in originals])
            for p,source in zip(pictures,originals):
                self.assertEqual(p.parent,(trial/'work').resolve())
                self.assertEqual(p.read_bytes(),(bench.ROOT/source).read_bytes())

    def test_monthly_ledgers_have_one_complete_solution_and_equal_payer_populations(self):
        from evaluation.verify_lockbox import verify
        for case in ('lockbox-month-11','lockbox-month-23'):
            counts=verify(case)
            self.assertEqual(len(counts),36)
            source=bench.read(bench.ROOT/'mock/lockbox'/case/'records.json')
            self.assertEqual(sum(v['payer']=='LegacyCo' for v in source['receipts'].values()),18)
            self.assertEqual(len(source['receivables']),108)
