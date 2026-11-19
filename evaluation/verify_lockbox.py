"""Independently verify global uniqueness, ERP suggestions and the published posting keys."""
from itertools import combinations
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def verify(case):
    data=ROOT/'mock/lockbox'/case
    source=json.loads((data/'records.json').read_text())
    ar={i:r['face']-r['credit'] for i,r in source['receivables'].items()}
    printed={}
    for line in (data/'erp-suggestions.txt').read_text().splitlines()[1:]:
        bank,triples=line.split(': ',1)
        printed[bank.split()[-1]]={tuple(sorted(g.split(','))) for g in re.findall(r'\[([^\]]+)\]',triples)}
    by_amount={}
    payers={v.get('payer') for v in source['receivables'].values()}
    for payer in payers:
        records=[i for i in sorted(ar) if source['receivables'][i].get('payer')==payer]
        for group in combinations(records,3):
            by_amount.setdefault((payer,sum(ar[i] for i in group)),[]).append(group)
    feasible={bank:{g for g in by_amount[receipt.get('payer'),receipt['cents']]
                     if set(receipt['confirmed_refs'])<=set(g)}
              for bank,receipt in source['receipts'].items()}
    if printed!=feasible:
        raise ValueError('Displayed candidates differ from the source ledgers')
    # Each choice covers its bank receipt and three distinct invoices. Every
    # one of those identifiers must occur once in a complete posting.
    choices={identifier:[] for identifier in (*ar,*feasible)}
    for bank,groups in feasible.items():
        for invoices in groups:
            row=(bank,*invoices)
            for identifier in row:
                choices[identifier].append(row)
    solutions=[]
    def extend(plan, used):
        if len(plan)==len(feasible):
            solutions.append(plan)
            return
        smallest=None
        for identifier in choices.keys()-used:
            options=[row for row in choices[identifier] if used.isdisjoint(row)]
            if not options:return
            if smallest is None or len(options)<len(smallest):
                smallest=options
        for row in smallest:
            extend({**plan,row[0]:row[1:]},used.union(row))
            if len(solutions)>1:return
    extend({},set())
    target=json.loads((ROOT/'evaluation/answer-key.json').read_text())[case]
    key={r['invoice']:tuple(sorted(r['matches'])) for r in target}
    if solutions!=[key] or len(set().union(*key.values()))!=len(ar):
        raise ValueError('The complete assignment is not unique or the key differs')
    return {k:len(v) for k,v in feasible.items()}


if __name__=='__main__':
    for case in ('lockbox-41','lockbox-76','lockbox-month-11','lockbox-month-23'):
        print(case,'one verified complete allocation;',sum(verify(case).values()),'local suggestions')
