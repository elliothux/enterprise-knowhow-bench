# Where the operator finished the close, and where it stopped

[Technical Report](REPORT.md) · [Benchmark Overview](../README.md) · [简体中文报告](REPORT.zh-CN.md)

On two complete monthly bank ledgers, the unaided operator and both Skills correctly placed **54/108** and **57/108** invoices. Every arm submitted on time and every receipt was graded. Both ledgers admit one complete solution. The missing placements came from bank receipts with several individually valid invoice matches that had to be reconciled across the entire ledger. [All six first submissions and the uniqueness check](batches/monthly-lockbox-20261119/README.md)

| Workflow and interface | Cases | Metric | No Skill | GLM-5.3 | DeepSeek Flash |
|---|---:|---|---:|---:|---:|
| [Month-end bank lockbox, ERP desk](batches/monthly-lockbox-20261119/README.md) | 2 × 108 invoices | Correct invoice placements | 111/216 | 111/216 | 111/216 |
| [Smaller bank lockbox, ERP desk](batches/lockbox-20261119/README.md) | 2 × 36 invoices | Correct invoice placements | 45/72 | 72/72 | 45/72 |
| [Cutoff with external dependencies, ERP desk](batches/cutoff-20261119/README.md) | 2 × 8 invoices | Correct invoices posted by cutoff | 2/16 | 11/16 | 11/16 |
| [Month-end cash application, native Chrome](batches/month-end-20261119/README.md) | 2 × 8 invoices | Mean business points / 100 | 100 | 95.63 | 100 |
| [Joint AR/AP close, ERP desk](batches/joint-close-20261119/README.md) | 2 × 24 invoices | Mean business points / 100 | 50.31 | 100 | 100 |
| [Scanned proof of delivery, ERP desk](batches/pod-inspection-20261119/README.md) | 2 × 8 invoices | Mean business points / 100 | 100 | 100 | 100 |
| [Chargeback workbook, local authoring tools](batches/chargeback-office-20261119/README.md) | 2 workbooks | Fully correct first files | 2/2 | 2/2 | 2/2 |
| [Chargeback workbook, native Calc → ownCloud → Rocket.Chat](batches/chargeback-native-20261119/README.md) | 2 workbooks | Fully correct first files | 1/2 | 0/2 | 1/2 |

On cb-28 the first-delivery scores were 0/384 (0.00%), 140/384 (36.46%), 162/384 (42.19%) for no Skill, GLM and DeepSeek respectively. All three fell short of a complete workbook. In the original input state, the GLM file passed 17/48 checks and the DeepSeek file passed 19/48. For example, neither supplied the correct closing amounts for invoice N-103. On the baseline trial, Calc recovery also displayed a prior trial’s template, which the operator closed. The native report documents the isolation exception and crashes alongside the received files. [Received workbooks and cell-level histories](batches/chargeback-native-20261119/README.md)

**An unresolved dependency has a different business outcome from a missed match.** At cutoff, five invoices genuinely needed a response from a bank or controller. Both Skills correctly posted all 11 actionable invoices and sent all five waits to the right owner. Their handling score was 100, while only 68.75% of the total queue could close. In the monthly lockboxes all 216 invoices could close with the evidence available.

**A Skill could also reduce the score.** In the native Chrome shift close-118 the baseline posted all eight invoices correctly. The GLM Skill led to one incorrect discount and collectible balance, leaving the shift at 91.25. In lockbox-41, the GLM Skill placed 36/36 while the baseline and DeepSeek Skill each placed 9/36. [Native first messages](batches/month-end-20261119/close-118/history.json) · [Lockbox postings](batches/lockbox-20261119/lockbox-41/history.json)

These are exploratory stress tests from an evolving case design. Within each batch, the cases, inputs, schedule, scorer and all three conditions were fixed before the first session. Every tested case in a completed batch is shown, including ceiling results and regressions. Each arm has one independent session per case. The denominators count tasks, invoice placements or checks on a workbook as indicated. Differences here describe the fixed operator and the indicated tools. [Scores by case and condition](distiller-scores.csv) · [Case catalog](../tasks/README.md)
