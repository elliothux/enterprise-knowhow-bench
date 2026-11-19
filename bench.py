#!/usr/bin/env python3
"""Run a public Enterprise Know-How Benchmark task with a person, Codex, or a stdin-based agent."""
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

from benchmark import batch_inputs
from benchmark.remittances import render as remittance_prompt
from benchmark.grading import grade
from mock.seed import chat, login, seed

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


TASKS = read(ROOT/'tasks/manifest.json')
KEYS = {key.lower():key for key in TASKS}


def task_id(value):
    try:
        return KEYS[value.lower()]
    except KeyError:
        raise argparse.ArgumentTypeError(f'Unknown task {value}. See python3 bench.py list.')


def prepare(args):
    task = TASKS[args.case]
    if args.arm not in task['arms']:
        raise ValueError(f"Available arms: {', '.join(task['arms'])}")
    run = args.out.resolve()
    run.mkdir(parents=True, exist_ok=False)
    work = run/'work'
    work.mkdir()
    prompt = remittance_prompt(ROOT/task['ledger']) if task['type']=='packet' else (ROOT/task['prompt']).read_text()
    record = dict(case=args.case, arm=args.arm, type=task['type'])
    if task['type'].startswith('native-'):
        namespace='trial-'+uuid.uuid4().hex[:16]
        opts=argparse.Namespace(namespace=namespace, case=None, cloud=args.cloud.rstrip('/'), chat=args.chat.rstrip('/'))
        room, = seed(opts, [ROOT/task['fixtures']])
        record.update(room, chat=opts.chat)
        for key, value in {'ROOM_URL':opts.chat+'/group/'+room['room'], 'CLOUD_URL':opts.cloud,
                           'FOLDER':room['folder'], 'MARKER':'LYNX-CASH-'+uuid.uuid4().hex[:10]}.items():
            prompt = prompt.replace('{{'+key+'}}', value)
        if os.getenv('BENCH_USER') or os.getenv('BENCH_PASSWORD'):
            prompt=prompt.replace('theagentcompany / theagentcompany', 'the separately supplied demo account credentials')
    else:
        shutil.copyfile(ROOT/'benchmark/work.py', work/'work')
        (work/'work').chmod(0o755)
        for name, source in task['resources'].items():
            shutil.copyfile(ROOT/source, work/(name+'.txt'))
    for image in task.get('images', []):
        shutil.copyfile(ROOT/image, work/Path(image).name)
    attachment = task['arms'][args.arm]
    if attachment:
        prompt += (ROOT/attachment).read_text()
    (work/'TASK.md').write_text(prompt)
    save(run/'run.json', record)
    print(work/'TASK.md', flush=True)
    return run


def native_delivery(record):
    token=login(record['chat'])
    if token['X-User-Id'] != record['operator_id']:
        raise ValueError('Score with the same demo operator used for setup.')
    messages=[]
    offset=0
    while True:
        query=urlencode(dict(roomId=record['room_id'], count=100, offset=offset))
        _, page=chat(record['chat'], 'groups.history?'+query, headers=token)
        batch=page['messages']
        messages.extend(batch)
        offset+=len(batch)
        if not batch or offset>=page.get('total',offset):break
    if not any(m['_id']==record['seed_id'] for m in messages):
        raise ValueError('The assigned initial request is missing from the room.')
    posts=sorted((m for m in messages if m['_id']!=record['seed_id'] and not m.get('t')
                  and m['u']['_id']==record['operator_id']),key=lambda m:(m['ts'],m['_id']))
    if not posts:return '', {}, False
    first=posts[0]
    return first['msg'], {'message_id':first['_id'], 'timestamp':first['ts'], 'posts':len(posts)}, (
        len(posts)==1 and not first.get('editedAt'))


def business(case, text, reads=0):
    filename = 'historical-answers.json' if TASKS[case]['group']=='historical' else 'answer-key.json'
    return grade(TASKS[case]['type'], read(ROOT/'evaluation'/filename)[case], text, reads)


def score(run):
    record=read(run/'run.json')
    task=TASKS[record['case']]
    reads=0
    if task['type'].startswith('native-'):
        text, receipt, valid=native_delivery(record)
    else:
        delivery=run/'work/delivery.csv'
        valid=delivery.is_file()
        text=delivery.read_text() if valid else ''
        reads_file=run/'work/reads.log'
        reads=len(reads_file.read_text().splitlines()) if reads_file.exists() else 0
        receipt={'sha256':hashlib.sha256(delivery.read_bytes()).hexdigest()} if valid else {}
    execution=read(run/'execution.json') if (run/'execution.json').exists() else None
    eligible=valid and (execution is None or execution['exit']==0)
    value=business(record['case'], text if eligible else '',reads)
    result=dict(case=record['case'],arm=record['arm'],**value, submission=text,receipt=receipt,
                valid_delivery=valid, execution=execution)
    save(run/'score.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


def execute(args):
    cmd=args.agent or [args.codex,'-a','never','exec','--skip-git-repo-check','-s','danger-full-access',
                       '-m',args.model,'-c','model_reasoning_effort="high"','--json','-']
    if shutil.which(cmd[0]) is None:
        raise ValueError(f'Agent executable not found: {cmd[0]}')
    run=prepare(args)
    cwd=run/'work'
    if not args.agent:
        for image in TASKS[args.case].get('images', []):
            cmd[-1:-1] = ['-i', str(cwd/Path(image).name)]
    limit=600 if TASKS[args.case]['type'].startswith('native-') else 300
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_THREAD','CODEX_SESSION','CODEX_INTERNAL_ORIGINATOR','CODEX_APP_TOOLS_'))}
    start=time.monotonic()
    with (cwd/'TASK.md').open('rb') as prompt, (run/'agent.log').open('wb') as log, (run/'stderr.log').open('wb') as err:
        proc=subprocess.Popen(cmd,stdin=prompt,stdout=log,stderr=err,cwd=cwd,env=env,start_new_session=True)
        try:
            status=proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()
            status=124
    save(run/'execution.json',dict(exit=status, seconds=round(time.monotonic()-start,3), time_limit=limit,
         adapter=Path(cmd[0]).name, model=None if args.agent else args.model,
         prompt_sha256=hashlib.sha256((cwd/'TASK.md').read_bytes()).hexdigest()))
    score(run)
    return status


def batch(args):
    if args.suite == 'custom' and not args.schedule:
        raise ValueError('A custom batch requires --schedule PATH.')
    rows=read(args.schedule) if args.schedule else read(ROOT/'tasks/schedule.json')[args.suite]
    batch_inputs.validate(rows, TASKS)
    root=args.out.resolve()
    root.mkdir(parents=True,exist_ok=True)
    config=dict(suite=args.suite,controls=args.controls,agent=args.agent,codex=args.codex,
                model=args.model,cloud=args.cloud,chat=args.chat,rows=rows)
    config_file=root/'batch.json'
    if config_file.exists():
        if read(config_file)!=config:raise ValueError('Batch configuration differs from existing run.')
    elif any(root.iterdir()):
        raise ValueError('Use an empty directory for a new batch.')
    else:
        save(config_file,config)
    batch_inputs.freeze(root, ROOT, TASKS, rows)
    cells=[(row['case'],arm) for row in rows for arm in row['order']]
    if args.controls:
        cells.extend((row['case'],row['control']) for row in rows if row['control'])
    for case,arm in cells:
        directory=root/case/arm
        if (directory/'score.json').exists():
            result=read(directory/'score.json')
            if (result['case'],result['arm'])!=(case,arm):raise ValueError('Mismatched saved result.')
            continue
        if directory.exists():
            raise ValueError(f'Incomplete run at {directory}. Preserve its logs and inspect it before resuming.')
        execute(argparse.Namespace(**{**vars(args),'case':case,'arm':arm,'out':directory}))
    pairs=[]
    for row in rows:
        scores={arm:read(root/row['case']/arm/'score.json') for arm in 'AB'}
        pairs.append(dict(case=row['case'],family=row['family'],A=scores['A']['score'],B=scores['B']['score'],
                          delta=scores['B']['score']-scores['A']['score'],A_exact=scores['A']['exact'],
                          B_exact=scores['B']['exact']))
    summary=dict(assigned=len(rows),sessions=len(cells),wins=sum(r['delta']>0 for r in pairs),
                 ties=sum(r['delta']==0 for r in pairs),losses=sum(r['delta']<0 for r in pairs),
                 A_exact=sum(r['A_exact'] for r in pairs),B_exact=sum(r['B_exact'] for r in pairs))
    save(root/'summary.json',dict(summary=summary,pairs=pairs))
    print(json.dumps(summary,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list')
    for name in ('prepare','run','batch'):
        p=commands.add_parser(name)
        if name=='batch':
            p.add_argument('suite',choices=['finance','remittances','custom'])
            p.add_argument('--schedule', type=Path, help='JSON array of case, family, order and optional control')
            p.add_argument('--controls',action='store_true',help='include prescheduled C/D controls')
        else:
            p.add_argument('case',type=task_id)
            p.add_argument('--arm',choices=list('ABCD'),default='A')
        p.add_argument('--out',type=Path,required=True,help='a new run directory')
        p.add_argument('--cloud',default='http://localhost:8092')
        p.add_argument('--chat',default='http://localhost:13000')
        if name in ('run','batch'):
            p.add_argument('--codex',default='codex')
            p.add_argument('--model',default='gpt-6.1-terra')
            p.add_argument('--agent',nargs=argparse.REMAINDER,help='custom program and arguments; receives TASK.md on stdin')
    commands.add_parser('score').add_argument('directory',type=Path)
    p=commands.add_parser('compare')
    p.add_argument('baseline',type=Path)
    p.add_argument('candidate',type=Path)
    args=parser.parse_args()
    if args.command=='list':
        for key,t in TASKS.items():
            print(key,t['group'],t['type'],''.join(t['arms']),sep='\t')
    elif args.command=='prepare':prepare(args)
    elif args.command=='run':return execute(args)
    elif args.command=='batch':batch(args)
    elif args.command=='score':score(args.directory)
    else:
        a,b=[read(p/'score.json') for p in (args.baseline,args.candidate)]
        if a['case']!=b['case'] or a['arm']==b['arm']:parser.error('Compare two different conditions of the same task.')
        print(json.dumps(dict(case=a['case'],left=a['arm'],right=b['arm'],scores=[a['score'],b['score']],
                              difference=b['score']-a['score']),indent=2))
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        sys.exit(str(exc))
