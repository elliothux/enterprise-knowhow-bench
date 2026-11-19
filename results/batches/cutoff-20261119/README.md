# Receivables still open at 17:00

The queue measures how many invoices actually received the correct posting by cutoff. A correct dependency wait remains open. The handling score separately evaluates each cash posting or escalation, giving a justified wait full credit. Invoices with a signed unresolved exception cannot be posted by any operator under the closing mandate.

| Shift | Available to post | Correctly posted by cutoff, A / GLM / DeepSeek | Correct handling, A / GLM / DeepSeek |
|---|---:|---|---|
| [cutoff-19](cutoff-19/history.json) | 6 of 8 | 0 / 6 / 6 | 48.75 / 100 / 100 |
| [cutoff-27](cutoff-27/history.json) | 5 of 8 | 2 / 5 / 5 | 75.63 / 100 / 100 |

On cutoff-19, two invoices shared one unallocated bank transfer. On cutoff-27, one invoice awaited a bank trace, and two depended on the same credit memo with a truncated reference. The remaining invoices had sufficient evidence. Both Skills reached the available automation ceiling, **6/8 (75%)** and **5/8 (62.5%)**. No arm attempted an unauthorized posting against an open incident. Model quality and upstream evidence availability have different implications for this result. [Index and environment](index.json) · [First signed status register](../../../mock/cutoff/cutoff-19/status-and-ledgers.txt) · [Second signed status register](../../../mock/cutoff/cutoff-27/status-and-ledgers.txt)
