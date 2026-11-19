"""Run one or both workbook cases using a signed-in Codex CLI and the local Calc engine."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import zipfile

from grade import assess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILLS = {'A':None,'B':'tasks/materials/attachment-132e238be20d.txt','C':'tasks/materials/cash-C-a59224b81247.txt'}
CASES = ('cb-17','cb-28')


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def save(file,data):
    file.write_text(json.dumps(data,indent=2)+'\n')


def freeze(args,root,jobs):
    files = [HERE/f for f in ('task.md','submit','grade.py','run.py')]
    files += [HERE/c/'template.xlsx' for c,_ in jobs]
    files += [ROOT/SKILLS[k] for _,k in jobs if SKILLS[k]]
    engine=os.getenv('SOFFICE') or shutil.which('soffice') or '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    plan = dict(jobs=jobs,model=args.model,reasoning='high',budget_seconds=900,cli_sha256=sha(Path(shutil.which(args.codex))),
                cli_version=subprocess.check_output([args.codex,'--version'],text=True).strip(),
                engine_version=subprocess.check_output([engine,'--version'],text=True).strip(),
                inputs={str(f.relative_to(ROOT)):sha(f) for f in files})
    if (root/'freeze.json').exists():
        if json.loads((root/'freeze.json').read_text())!=json.loads(json.dumps(plan)):
            raise ValueError('Frozen batch differs')
    else:
        if any(root.iterdir()):
            raise ValueError('Choose a new batch directory')
        for f in set(files):
            dest=root/'frozen'/f.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(f,dest)
        save(root/'freeze.json',plan)
    return root/'frozen'


def run(job,args,root,frozen):
    case,arm=job
    trial=root/case/arm
    score=trial/'score.json'
    if score.exists():
        return
    work=trial/'work'
    work.mkdir(parents=True)
    packet=frozen/'cases/chargebacks'
    shutil.copyfile(packet/case/'template.xlsx',work/'template.xlsx')
    shutil.copyfile(packet/'submit',work/'submit')
    (work/'submit').chmod(0o755)
    prompt=(packet/'task.md').read_text()
    if SKILLS[arm]:
        prompt+=(frozen/SKILLS[arm]).read_text()
    (work/'TASK.md').write_text(prompt)
    cmd=[args.codex,'-a','never','exec','--skip-git-repo-check','-s','danger-full-access','-m',args.model,
         '-c','model_reasoning_effort="high"','--json','-']
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_THREAD','CODEX_SESSION','CODEX_INTERNAL_ORIGINATOR','CODEX_APP_TOOLS_'))}
    env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env['PATH']
    with (work/'TASK.md').open('rb') as stdin,(trial/'agent.log').open('wb') as stdout,(trial/'stderr.log').open('wb') as stderr:
        proc=subprocess.Popen(cmd,stdin=stdin,stdout=stdout,stderr=stderr,cwd=work,env=env,start_new_session=True)
        try:
            status=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()
            status=124
    file=work/'delivery.xlsx'
    receipt=trial/'receipt.sha256'
    valid=file.exists() and receipt.exists() and sha(file)==receipt.read_text().strip()
    result=dict(case=case,arm=arm,exit=status,receipt=sha(file) if valid else None,prompt_sha256=sha(work/'TASK.md'))
    if valid:
        try:
            result.update(assess(packet/case/'template.xlsx',file))
        except (KeyError,ValueError,zipfile.BadZipFile) as exc:
            result.update(score=0,exact=False,reason=str(exc))
    else:
        result.update(score=0,exact=False,reason='No matching first workbook receipt')
    save(score,result)
    print(case,arm,result['score'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--case',choices=CASES)
    parser.add_argument('--arm',choices=SKILLS)
    parser.add_argument('--model',default='gpt-6.1-terra')
    parser.add_argument('--codex',default='codex')
    parser.add_argument('--workers',type=int,choices=(1,2,3),default=1)
    args=parser.parse_args()
    root=args.out.resolve()
    root.mkdir(exist_ok=True,parents=True)
    jobs=[(c,a) for c,arms in zip(CASES,('ABC','CBA')) for a in arms if (not args.case or args.case==c) and (not args.arm or args.arm==a)]
    frozen=freeze(args,root,jobs)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda job:run(job,args,root,frozen),jobs))
