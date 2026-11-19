# Month-end bank lockboxes that every arm left incomplete

Both shifts contain enough evidence for a complete close. Each has 108 invoices, 36 bank receipts and one globally consistent assignment. Eighteen receipts include electronic invoice references. The other 18 identify the payer and the total but omit the invoice references. All three arms saw every outstanding amount and the ERP's complete list of locally balanced triples. The tested operator could use the same read-and-submit desk interface as in the twelve-receipt pilot. The 300-second budget and the archived invoice Skills were unchanged. All six processes exited normally with a valid first submission.

| Shift | No Skill | GLM-5.3 Skill | DeepSeek Flash Skill | Receipts fully matched per arm |
|---|---:|---:|---:|---:|
| [lockbox-month-11](lockbox-month-11/history.json) | 54/108 (50.00%) | 54/108 (50.00%) | 54/108 (50.00%) | 18/36 each |
| [lockbox-month-23](lockbox-month-23/history.json) | 57/108 (52.78%) | 57/108 (52.78%) | 57/108 (52.78%) | 19/36 each |

On the first shift all three submitted the 18 referenced receipts and referred all 18 legacy receipts. On the second shift all three placed one additional legacy receipt correctly. The baseline submitted a further incorrect allocation. The two Skills referred the remaining 17 receipts. The score credits each invoice posted once to its correct bank receipt.

The larger shifts were designed after the twelve-receipt pilot. Selection used the business constraints, complete source records, overlapping local matches and uniqueness of the full assignment. The two cases and all six trials were frozen before any monthly-shift score was observed. The verifier independently enumerates the 241 and 243 locally valid suggestions respectively, checks that each displayed suggestion is admissible and proves that exactly one complete set of disjoint postings exists. A solver can close each shift. This result measures operator performance in the simulated ERP, where a scripting console is unavailable. [Index and source digests](index.json) · [First ledger](../../../mock/lockbox/lockbox-month-11) · [Second ledger](../../../mock/lockbox/lockbox-month-23) · [Independent verifier](../../../evaluation/verify_lockbox.py) · [Run guide](../../../tasks/RUN.md#bank-lockbox-matching)
