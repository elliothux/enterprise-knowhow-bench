"""Public first-delivery business rubric. All target cash amounts are integer cents."""
import csv
from decimal import Decimal, InvalidOperation


def cash(target, rows):
    key = target['invoice']
    expected = target['target']
    candidates = []
    for row in rows:
        if len(row) != 6 or row[0].strip().upper() != key:
            continue
        try:
            cents = [Decimal(v.strip().upper().replace('SGD', '').strip()) * 100 for v in row[1:5]]
            if all(v.is_finite() and v >= 0 and v == v.to_integral_value() for v in cents):
                candidates.append([*map(int, cents), row[5].strip().upper()])
        except (InvalidOperation, OverflowError):
            continue
    if len(candidates) != 1:
        return 0
    post = candidates[0]
    return (35 * (post[:2] == expected[:2]) + 35 * (post[2:4] == expected[2:4])
            + 20 * (post[4] == expected[4]) + 10 * (sum(post[:4]) == sum(expected[:4])))


def joint_close(target, rows):
    receivables, payables = target['receivables'], target['payables']
    assigned = {line['invoice'] for line in [*receivables, *payables]}
    submitted = {row[0].strip().upper(): [v.strip().upper() for v in row] for row in rows}
    if len(submitted) != len(rows) or not submitted.keys() <= assigned:
        submitted = {}
    scores = [cash(line, [submitted[line['invoice']]]) if line['invoice'] in submitted else 0
              for line in receivables]
    for payable in payables:
        row = submitted.get(payable['invoice'], [])
        points = 0
        if len(row) == 4:
            try:
                value = Decimal(row[1])
                exposure_correct = value.is_finite() and value * 100 == payable['exposure']
            except (InvalidOperation, OverflowError):
                exposure_correct = False
            points = (40 * exposure_correct + 20 * (row[2] == payable['decision'])
                      + 40 * (sorted(row[3].split(';')) == payable['reasons']))
        scores.append(points)
    return {'score':sum(scores)/len(scores), 'line_scores':scores, 'exact':all(s==100 for s in scores)}


def inspection(target, rows):
    records = {r[0].strip().upper():r for r in rows}
    if len(records) != len(rows) or not records.keys() <= {line['invoice'] for line in target}:
        records = {}
    scores = []
    for line in target:
        r = records.get(line['invoice'], [])
        value = 0
        if len(r) == 6:
            for i,(key,multiplier,points) in enumerate([('units',1,25),('loss',100,20),
                    ('claim',100,25),('collectible',100,20)],1):
                try:
                    number=Decimal(r[i].strip())
                    if number.is_finite() and number*multiplier == line[key]:
                        value+=points
                except (InvalidOperation,OverflowError):
                    pass
            value+=10*(r[5].strip().upper()==line['owner'])
        scores.append(value)
    return {'score': sum(scores)/len(scores), 'line_scores':scores, 'exact':all(s==100 for s in scores)}


def cutoff_cash(target, rows):
    submitted={r[0].strip().upper():[v.strip().upper() for v in r] for r in rows}
    if len(submitted)!=len(rows) or not submitted.keys() <= {t['invoice'] for t in target}:
        submitted={}
    line_scores,handling=[],[]
    blocked=unsafe=0
    for item in target:
        row=submitted.get(item['invoice'],[])
        if 'wait' in item:
            wait=item['wait']
            correct=row==[item['invoice'],'WAIT',wait['owner'],wait['ticket']]
            blocked+=1
            unsafe+=int(len(row)==6)
            line_scores.append(0)
            handling.append(100*correct)
        else:
            grade=cash(item,[row]) if row else 0
            line_scores.append(100*int(grade==100))
            handling.append(grade)
    return {'score':sum(line_scores)/len(target),'line_scores':line_scores,'exact':all(line_scores),
            'posted_correctly':line_scores.count(100),'blocked_at_cutoff':blocked,'unsafe_postings':unsafe,
            'handling_score':sum(handling)/len(target),'handling_line_scores':handling,'handling_exact':all(v==100 for v in handling)}


def lockbox(target, rows):
    from collections import Counter
    submitted = {r[0].strip().upper(): [v.strip().upper() for v in r[1:]] for r in rows}
    if len(submitted) != len(rows) or not submitted.keys() <= {t['invoice'] for t in target}:
        submitted = {}
    occurrences = Counter(item for values in submitted.values() for item in values if item!='REFER')
    correct = []
    for receipt in target:
        assigned=submitted.get(receipt['invoice'],[])
        correct.append(sum(item in receipt['matches'] and occurrences[item]==1 for item in assigned)
                       if len(assigned)==3 else 0)
    total=sum(correct)
    return {'score':100*total/(3*len(target)), 'line_scores':[100*n/3 for n in correct],
            'correct_placements':total, 'exact_receipts':correct.count(3), 'exact':all(n==3 for n in correct)}


def grade(kind, target, text, reads=0):
    rows = [row for line in text.splitlines() if (row := next(csv.reader([line.strip().strip('`').strip()]), []))]
    if kind == 'lockbox':
        return lockbox(target,rows)
    if kind == 'cutoff-cash':
        return cutoff_cash(target,rows)
    if kind == 'damage-inspection':
        return inspection(target,rows)
    if kind == 'cross-ledger':
        return joint_close(target, rows)
    if kind in ('packet','native-cash-batch'):
        ids = [r[0].strip().upper() for r in rows]
        valid = len(ids) == len(set(ids)) and set(ids) <= {line['invoice'] for line in target}
        scores = [cash(line, rows) if valid else 0 for line in target]
        return {'score':sum(scores)/len(scores), 'line_scores':scores, 'exact':all(v==100 for v in scores)}
    if kind == 'native-ar':
        score = cash(target, rows)
        return {'score':score, 'exact':score == 100}
    key, decision, reasons, *refs = target['target']
    if kind == 'native-ap':
        candidates = [[s.strip().upper() for s in r] for r in rows if len(r)==3 and r[0].strip().upper()==key]
    else:
        header = ['ticket','decision','reasons'] if kind == 'ticket' else ['invoice_id','decision','reason_codes']
        if kind == 'evidence':
            header.append('evidence_refs')
        candidates = rows[1:] if rows and rows[0]==header else []
    exact = (len(candidates)==1 and len(candidates[0])==3+len(refs) and candidates[0][:2]==[key,decision]
             and sorted(candidates[0][2].split(';'))==sorted(reasons.split(';')))
    if exact and refs:
        exact = set(filter(None,candidates[0][3].split(';'))) == set(refs[0].split(';'))
    out = {'score':int(exact)*100, 'exact':exact}
    if kind == 'ticket':
        out.update(rule_lookups=reads, unassisted_score=100*int(exact and reads==0))
    return out
