"""Run native LibreOffice Calc, ownCloud and Rocket.Chat chargeback trials on an idle Mac."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote
import uuid

from run import CASES, HERE, ROOT, SKILLS, save, sha
from grade import assess
sys.path.insert(0,str(ROOT))
import bench
from mock.seed import seed, request


def dav(args,folder,filename):
    user=os.getenv('BENCH_USER','theagentcompany')
    credentials=user+':'+os.getenv('BENCH_PASSWORD','theagentcompany')
    url=args.cloud+'/remote.php/dav/files/'+quote(user,safe='')+'/'+quote(folder+'/'+filename,safe='/')
    return url, {'Authorization':'Basic '+base64.b64encode(credentials.encode()).decode()}


def trial(args,root,case,arm):
    run=root/case/arm
    if (run/'score.json').exists():
        return
    if run.exists():
        raise RuntimeError(f'Incomplete trial at {run}. Preserve and examine its receipts.')
    work=run/'work'
    work.mkdir(parents=True)
    key=uuid.uuid4().hex[:12]
    name=case+'-'+key
    template=work/(name+'-template.xlsx')
    filename=name+'-close.xlsx'
    fixture=run/'seed'/case
    fixture.mkdir(parents=True)
    (fixture/'incoming.txt').write_text(f'Finance request {name}. Deliver the completed chargeback workbook as {filename} in the assigned ownCloud folder, then post its filename here once. Partial workbooks are accepted for partial credit.')
    room,=seed(argparse.Namespace(namespace='cb-'+key,cloud=args.cloud,chat=args.chat,case=None),[fixture])
    frozen=root/'frozen'
    shutil.copyfile(frozen/'cases/chargebacks'/case/'template.xlsx',template)
    url,auth=dav(args,room['folder'],'template.xlsx')
    request(url,'PUT',template.read_bytes(),{**auth,'If-None-Match':'*'})
    out_url,_=dav(args,room['folder'],filename)
    marker='LYNX-CB-'+key
    prompt=(frozen/'cases/chargebacks/native_task.md').read_text()
    fields={'MARKER_URL':'data:text/html,%3Ctitle%3E'+marker+'%3C/title%3E'+marker,'ROOM':args.chat+'/group/'+room['room'],
            'TEMPLATE':str(template),'WORKING':str(work/(name+'.numbers')),'EXPORT':str(work/filename),
            'CLOUD':args.cloud,'FOLDER':room['folder'],'FILENAME':filename}
    for k,v in fields.items():prompt=prompt.replace('{{'+k+'}}',v)
    rules=(frozen/'cases/chargebacks/task.md').read_text().split('All amounts are integer cents.',1)[1]
    prompt+='\nAll amounts are integer cents.'+rules
    if SKILLS[arm]:prompt+=(frozen/SKILLS[arm]).read_text()
    (work/'TASK.md').write_text(prompt)
    meta=dict(**room,chat=args.chat,case=case,arm=arm,marker=marker,filename=filename)
    save(run/'run.json',meta)
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_THREAD','CODEX_SESSION','CODEX_INTERNAL_ORIGINATOR','CODEX_APP_TOOLS_'))}
    command=[args.codex,'-a','never','exec','--skip-git-repo-check','-s','danger-full-access','-m',args.model,'-c','model_reasoning_effort="high"','--json','-']
    start=time.monotonic()
    first=None
    with (work/'TASK.md').open('rb') as inp,(run/'agent.log').open('wb') as log,(run/'stderr.log').open('wb') as err:
        proc=subprocess.Popen(command,cwd=work,stdin=inp,stdout=log,stderr=err,start_new_session=True,env=env)
        while True:
            if first is None:
                msg,receipt,valid=bench.native_delivery(meta)
                if receipt:
                    status,blob=request(out_url,headers=auth,allowed=(404,))
                    if status==200:(run/'received.xlsx').write_bytes(blob)
                    first=dict(message=msg,receipt=receipt,unedited_single=valid,http_status=status)
                    save(run/'first.json',first)
            status=proc.poll()
            if status is not None:break
            if time.monotonic()-start>=900:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
                status=124
                break
            time.sleep(4)
    msg,last,valid=bench.native_delivery(meta)
    # One final read covers a submission between the last poll and process exit.
    if first is None and last:
        st,blob=request(out_url,headers=auth,allowed=(404,))
        if st==200:(run/'received.xlsx').write_bytes(blob)
        first=dict(message=msg,receipt=last,unedited_single=valid,http_status=st)
        save(run/'first.json',first)
    received=run/'received.xlsx'
    eligible=bool(first and valid and first['unedited_single'] and first['message'].strip()==filename and msg.strip()==filename and received.is_file())
    result=dict(case=case,arm=arm,seconds=time.monotonic()-start,exit=status,first=first,valid_delivery=eligible,
                receipt=sha(received) if received.is_file() else None,score=0,exact=False)
    if eligible:
        result.update(assess(frozen/'cases/chargebacks'/case/'template.xlsx',received))
    save(run/'score.json',result)
    print(case,arm,result['score'],bool(first),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--case',choices=CASES)
    parser.add_argument('--arm',choices=SKILLS)
    parser.add_argument('--model',default='gpt-6.1-terra')
    parser.add_argument('--codex',default='codex')
    parser.add_argument('--cloud',default='http://localhost:8092')
    parser.add_argument('--chat',default='http://localhost:13000')
    args=parser.parse_args()
    app=Path('/Applications/LibreOffice.app/Contents/Info.plist')
    if not app.is_file():
        parser.error('Native LibreOffice Calc must be installed in /Applications')
    root=args.out.resolve()
    root.mkdir(exist_ok=True,parents=True)
    jobs=[(c,a) for c,arms in zip(CASES,('ABD','DBA')) for a in arms if (not args.case or args.case==c) and (not args.arm or args.arm==a)]
    files=[HERE/f for f in ('run.py','grade.py','native.py','native_task.md','task.md')]
    files += [ROOT/'bench.py',ROOT/'mock/seed.py',*(HERE/c/'template.xlsx' for c,a in jobs),*(ROOT/SKILLS[a] for c,a in jobs if SKILLS[a])]
    plan=dict(jobs=jobs,model=args.model,budget_seconds=900,app_info_sha256=sha(app),cli_sha256=sha(Path(shutil.which(args.codex))),
              inputs={str(p.relative_to(ROOT)):sha(p) for p in files})
    if not (root/'freeze.json').exists():
        for p in set(files):
            dest=root/'frozen'/p.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest)
        save(root/'freeze.json',plan)
    elif json.loads((root/'freeze.json').read_text())!=json.loads(json.dumps(plan)):
        raise ValueError('Frozen plan differs')
    for c,a in jobs:
        if (root/c/a/'score.json').is_file():
            continue
        trial(args,root,c,a)
        # An examiner can pause between sessions to clear a trial-owned window after timeout.
        if (root/'pause-after-trial').exists():break
