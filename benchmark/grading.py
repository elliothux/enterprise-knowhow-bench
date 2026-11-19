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


def grade(kind, target, text, reads=0):
    rows = [row for line in text.splitlines() if (row := next(csv.reader([line.strip().strip('`').strip()]), []))]
    if kind == 'packet':
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
