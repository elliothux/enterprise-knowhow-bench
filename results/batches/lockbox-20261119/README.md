# Twelve-receipt bank lockboxes

Both shifts have complete records and a unique solution. The bank desk's candidate screen contained 142 locally balanced triples on lockbox-41 and 120 on lockbox-76. The score is the number of invoices allocated once to their correct receipt, out of 36. The same signed-in operator and simulated ERP interface were used throughout, with 300 seconds and one first submission per session.

| Shift | No Skill | GLM-5.3 | DeepSeek Flash |
|---|---:|---:|---:|
| [lockbox-41](lockbox-41/history.json) | 9/36 (25%) | 36/36 (100%) | 9/36 (25%) |
| [lockbox-76](lockbox-76/history.json) | 36/36 (100%) | 36/36 (100%) | 36/36 (100%) |

The candidate lists already perform the amount arithmetic. An operator still has to reconcile overlapping suggestions across the ledger. The published verifier checks all suggestions against the original amounts and enumerates complete assignments. The operator had the two ERP read commands and one final posting command. [Full six-session index](index.json) · [Independent feasibility check](../../../evaluation/verify_lockbox.py)
