#!/usr/bin/env python3
"""Participant-side simulated ERP: read an assigned document or submit one receipt."""
import hashlib
import os
import sys
from pathlib import Path

base = Path(__file__).resolve().parent
args = sys.argv[1:]
if len(args) == 2 and args[0] == 'read' and args[1] in ('rules', 'invoices-history'):
    path = base / (args[1] + '.txt')
    if path.is_file():
        with (base/'reads.log').open('a') as log:
            print(args[1], file=log)
        print(path.read_text(), end='')
        sys.exit(0)
if len(args) == 2 and args[0] == 'submit':
    payload = args[1].encode()
    # Publish only a complete payload, even with simultaneous submitters.
    import tempfile
    with tempfile.NamedTemporaryFile(dir=base) as handle:
        handle.write(payload)
        handle.flush()
        try:
            os.link(handle.name, base/'delivery.csv')
        except FileExistsError:
            sys.exit('A first submission already exists.')
    print('Delivery 1, SHA256 '+hashlib.sha256(payload).hexdigest())
    sys.exit(0)
sys.exit('Use ./work read NAME or ./work submit CSV as specified in TASK.md.')
