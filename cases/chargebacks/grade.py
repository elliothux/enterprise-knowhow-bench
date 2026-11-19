"""Recalculate chargeback workbooks using the bank's independent event replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries

STATES = ('original','early_cutoffs','late_chargebacks','receipt_amendment','invoice_priority',
          'reordered_registers','early_overpayment','two_reversals')
TABLES = {'Invoices':(8,5), 'Bank events':(12,8), 'Cutoff':(1,2)}
OUTPUTS = {'Close':(8,3), 'Receipt control':(12,2)}


def inputs(book):
    return {s:[list(row) for row in book[s].iter_rows(min_row=2,max_row=count+1,max_col=width,values_only=True)]
            for s,(count,width) in TABLES.items()}


def change(data, state):
    events, invoices = data['Bank events'], data['Invoices']
    if state == 'early_cutoffs':
        data['Cutoff'][0] = [5,6]
    elif state == 'late_chargebacks':
        data['Cutoff'][0] = [11,12]
    elif state == 'receipt_amendment':
        events[0][6] //= 3
        events[3][6] += 17001
    elif state == 'invoice_priority':
        invoices[0][3] = 13
        invoices[7][2] = 9
    elif state == 'reordered_registers':
        invoices.reverse()
        events[:] = events[5:]+events[:5]
    elif state == 'early_overpayment':
        events[0][6] = 125100
        data['Cutoff'][0] = [10,11]
    elif state == 'two_reversals':
        events[4][6] = 19501
        events[7][6] = 36101
        events[0][6] = 41003
        data['Cutoff'][0] = [10,11]


def oracle(data):
    through,known = data['Cutoff'][0]
    invoices = data['Invoices']
    account = {i:[0,0,face if opened<=through else 0] for i,_,opened,_,face in invoices}
    control = {r[1]:[0,0] for r in data['Bank events']}
    lots = {}
    for _, event, entity, day, seen, kind, value, original in sorted(data['Bank events']):
        if day > through or seen > known:
            continue
        if kind == 'RECEIPT':
            lots[event] = []
            for inv,e,opened,_,_face in sorted(invoices,key=lambda r:(r[3],r[2],r[0])):
                if e != entity or opened > day:
                    continue
                payment = min(value, account[inv][2])
                if payment:
                    account[inv][0] += payment
                    account[inv][2] -= payment
                    lots[event].append([inv,payment])
                    value -= payment
            control[event][0] = value
        else:
            suspense = min(value, control[original][0])
            control[original][0] -= suspense
            value -= suspense
            for allocation in reversed(lots.get(original,[])):
                inv, remaining = allocation
                unwind = min(value,remaining)
                allocation[1] -= unwind
                account[inv][1] += unwind
                account[inv][2] += unwind
                value -= unwind
            control[event][1] = value
    return {'Close':account, 'Receipt control':control}


def formula_cells(book,sheet):
    cells = {c.coordinate for row in book[sheet] for c in row if c.data_type=='f'}
    for address in book[sheet].array_formulae.values():
        x1,y1,x2,y2=range_boundaries(address)
        cells.update(book[sheet].cell(y,x).coordinate for y in range(y1,y2+1) for x in range(x1,x2+1))
    return cells


def verify_package(file):
    with zipfile.ZipFile(file) as z:
        if sum(f.file_size for f in z.infolist()) > 64*1024*1024:
            raise ValueError('Workbook too large')
        for p in z.namelist():
            if any(s in p.lower() for s in ('vbaproject','externallinks/','embeddings/','connections.xml')):
                raise ValueError('External or embedded workbook content')
            if p.endswith('.rels') and b'TargetMode="External"' in z.read(p):
                raise ValueError('External relationships')
            if p.startswith('xl/worksheets/') and p.endswith('.xml') and re.search(
                    rb'(?:WEBSERVICE|DDE|RTD|HYPERLINK)\s*\(',z.read(p),re.I):
                raise ValueError('External formula')


def engine(file, directory):
    binary = os.getenv('SOFFICE') or shutil.which('soffice') or '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    target = directory/'converted'
    target.mkdir()
    proc = subprocess.run([binary,'-env:UserInstallation='+(directory/'profile').as_uri(),'--headless','--norestore',
                           '--convert-to','xlsx:Calc MS Excel 2007 XML','--outdir',str(target),str(file)],
                          capture_output=True, timeout=75)
    if proc.returncode or not (target/file.name).exists():
        raise RuntimeError(f'LibreOffice conversion failed with exit {proc.returncode}: {proc.stderr.decode()[:200]}')
    return load_workbook(target/file.name,data_only=True)


def assess(template, file):
    verify_package(file)
    base=load_workbook(template)
    source=load_workbook(file)
    if inputs(base)!=inputs(source):
        raise ValueError('Source records changed')
    all_cells = {s:formula_cells(source,s) for s in OUTPUTS}
    for s,(count,_) in OUTPUTS.items():
        if [source[s].cell(i,1).value for i in range(2,count+2)] != [base[s].cell(i,1).value for i in range(2,count+2)]:
            raise ValueError('Output identifiers changed')
    reports = {}
    with tempfile.TemporaryDirectory() as work:
        for state in STATES:
            folder = Path(work)/state
            folder.mkdir()
            data=inputs(base)
            change(data,state)
            expected=oracle(data)
            book=load_workbook(file)
            for sheet,records in data.items():
                for i,row in enumerate(records,2):
                    for col,value in enumerate(row,1):
                        book[sheet].cell(i,col).value=value
            staged=folder/'staged.xlsx'
            book.save(staged)
            result=engine(staged,folder)
            errors=[]
            for s,(count,width) in OUTPUTS.items():
                for i in range(2,count+2):
                    key=base[s].cell(i,1).value
                    for col in range(2,width+2):
                        cell=result[s].cell(i,col)
                        wanted=expected[s][key][col-2]
                        if (cell.coordinate not in all_cells[s] or type(cell.value) not in (float,int)
                                or abs(cell.value-wanted)>1e-6):
                            errors.append(dict(sheet=s,cell=cell.coordinate,id=key,expected=wanted,
                                               actual=cell.value,formula=cell.coordinate in all_cells[s]))
            reports[state]=dict(correct=48-len(errors),errors=errors)
    total=48*len(STATES)
    n=sum(r['correct'] for r in reports.values())
    return dict(checked=total,correct=n,score=100*n/total,exact=n==total,states=reports)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('template',type=Path)
    p.add_argument('submission',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.write_text(json.dumps(assess(args.template,args.submission),indent=2)+'\n')
