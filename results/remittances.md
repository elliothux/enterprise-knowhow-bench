# First submissions on two-invoice remittances

The batch contained 16 independent remittances, each with two invoices to apply separately. Both arms ran each case in a fresh model session, yielding 32 source logs. The mean business score rose from 28.13 without a Skill to 94.84 with the GLM Skill. The number of remittances with two fully correct rows rose from 0/16 to 13/16.

Scores improved on 15 remittances and tied on one. All 16 had a compliant first submission in both arms, and each counted once. The native demonstrations and distilled Skill came from earlier short-payment training. The evaluation used a local simulated ERP CLI to measure cash application decisions. The [native finance report](finance.md) covers cross-application execution.

| Remittance | Invoices | No Skill | GLM Skill | Difference |
|---|---|---:|---:|---:|
| RMT-716 | I-47740, I-43890 | 0 | 100 | +100 |
| RMT-723 | I-47207, I-48588 | 0 | 100 | +100 |
| RMT-730 | I-44288, I-42209 | 0 | 100 | +100 |
| RMT-737 | I-48932, I-47888 | 0 | 100 | +100 |
| RMT-744 | I-46544, I-46528 | 0 | 100 | +100 |
| RMT-751 | I-48346, I-45573 | 50 | 100 | +50 |
| RMT-758 | I-47144, I-42701 | 0 | 100 | +100 |
| RMT-765 | I-42900, I-42320 | 72.5 | 72.5 | +0 |
| RMT-772 | I-45707, I-42877 | 72.5 | 100 | +27.5 |
| RMT-779 | I-45814, I-43665 | 22.5 | 100 | +77.5 |
| RMT-786 | I-43654, I-42376 | 15 | 72.5 | +57.5 |
| RMT-793 | I-42437, I-42625 | 0 | 72.5 | +72.5 |
| RMT-800 | I-46316, I-44746 | 72.5 | 100 | +27.5 |
| RMT-807 | I-47971, I-48952 | 72.5 | 100 | +27.5 |
| RMT-814 | I-42800, I-45699 | 0 | 100 | +100 |
| RMT-821 | I-46999, I-43731 | 72.5 | 100 | +27.5 |

## Referrals and invoice accuracy

Without a Skill, the model referred at least one invoice for manual review on 11 remittances, or 19 of the 32 invoice rows. With the GLM Skill, it referred none. Fully correct invoice rows rose from 6/32 to 29/32. Both arms could look up the same closed cases. The Skill also supplied the company's rules for handling short payments. The scores capture both the reduction in referrals and the accuracy of the amounts submitted.

[All case scores](remittance-scores.json) · [Frozen answer key](answer-key.json) · [Synthetic ledgers](../mock/remittances)
