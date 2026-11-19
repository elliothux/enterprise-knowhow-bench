# Cross-application finance handoffs

The scheduled evaluation covered 40 new finance cases and 110 independent model sessions on a macOS VM. In each case the operator used native Chrome to pick up a request in a private Rocket.Chat queue, read current and historical records in ownCloud, and submit cash application instructions or a payment release decision to finance. The two workflows used Skills distilled before the evaluation. All 40 cases were held out of training.

## Results for all scheduled cases

| Task | Cases | Mean without Skill | Mean with GLM Skill | Gain | Improved / tied / declined | Fully correct without Skill | Fully correct with GLM |
|---|---:|---:|---:|---:|---|---:|---:|
| Apply short payments to receivables | 24 | 70.83 | 100.00 | +29.17 | 12 / 12 / 0 | 12/24 | 24/24 |
| Review payments for release | 16 | 75.00 | 100.00 | +25.00 | 4 / 12 / 0 | 12/16 | 16/16 |

Across all 40 cases, fully correct first submissions rose from 24/40 to 40/40, a gain of 40.0 percentage points. The receivables rubric awards points for four criteria: discount and claims amounts, write-off and collectible balance, follow-up owner, and reconciliation of amounts. The payables rubric awards full credit only when the first decision and every applicable reason are correct. The means use each task's own rubric.

## Results by decision rule

| Rule tested | Cases | No Skill | GLM Skill | Gain | Improved / tied / declined |
|---|---:|---:|---:|---:|---|
| Shipment match and signed proof of delivery | 4 | 82.50 | 100.00 | +17.50 | 1 / 3 / 0 |
| Posted credits and the write-off base | 4 | 47.50 | 100.00 | +52.50 | 3 / 1 / 0 |
| Absolute and percentage write-off limits | 4 | 72.50 | 100.00 | +27.50 | 2 / 2 / 0 |
| Bank grace period and payment instruction timing | 4 | 55.00 | 100.00 | +45.00 | 3 / 1 / 0 |
| Cap on transfers to claims | 4 | 95.00 | 100.00 | +5.00 | 1 / 3 / 0 |
| Discount base and cap | 4 | 72.50 | 100.00 | +27.50 | 2 / 2 / 0 |
| Multiple independent payment release checks | 4 | 50.00 | 100.00 | +50.00 | 2 / 2 / 0 |
| Waiver scope, authority and expiry | 4 | 75.00 | 100.00 | +25.00 | 1 / 3 / 0 |
| New bank account and verification record | 4 | 75.00 | 100.00 | +25.00 | 1 / 3 / 0 |
| Authority and event order for closing a hold | 4 | 100.00 | 100.00 | +0.00 | 0 / 4 / 0 |

## What changed in the first submission

Invoice I-22711, which tests posted credits and the write-off base, had the largest receivables gain, from 0 to 100. The baseline submitted `REFER I-22711: SGD 4.76 remains after cash and posted credit; prior examples do not establish write-off treatment for this OTHER-labelled residual.` With the GLM Skill, the operator submitted `I-22711,0.00,0.00,0.00,4.76,COLLECTIONS`. Dropping each receivables rule group in turn left a mean gain of +24.50 to +34.00 on the remaining cases.

Invoice INV-15427, which tests multiple independent release checks, had the largest payables gain, from 0 to 100. The baseline submitted `INV-15427,RELEASE,NONE`. With the GLM Skill, the operator submitted `INV-15427,HOLD,BANK_UNVERIFIED`. Dropping each payables rule group in turn left a mean gain of +16.67 to +33.33.

## Operational errors, browser checks and elapsed time

| Measure, without Skill → with GLM Skill | Receivables | Payables |
|---|---:|---:|
| Referrals for manual review | 1 → 0 | 3 → 0 |
| Excessive concession on a short payment | 1 → 0 | — |
| Incorrect payment release | — | 1 → 0 |
| Passed automated native browser checks | 23/24 → 22/24 | 16/16 → 16/16 |
| Mean score counting each failed browser check as zero | 66.67 → 91.67 | 75.00 → 100.00 |
| Pairs in which both arms passed the browser checks | 21 | 16 |
| Mean gain on those pairs | +33.3333 | +25.0 |
| Median duration across all trials, seconds | 148 → 150 | 157 → 147 |

The business score uses the recipient's first delivery and the underlying message log. The strict protocol also requires a complete native trace, including automated evidence that the Guest window closed. Missing submissions score zero. The table includes trials that failed verification.

## Scheduled controls

| Control on the same cases | Task | Paired cases | GLM Skill mean | Control mean | Control minus GLM |
|---|---|---:|---:|---:|---:|
| DeepSeek Flash-distilled Skill | Receivables | 12 | 100.00 | 100.00 | +0.00 |
| Full policy text | Receivables | 6 | 100.00 | 100.00 | +0.00 |
| DeepSeek Flash-distilled Skill | Payables | 8 | 100.00 | 100.00 | +0.00 |
| Full policy text | Payables | 4 | 100.00 | 100.00 | +0.00 |

The main comparison measures what changes when operators who already have transaction records and closed cases also receive the company procedure as a Skill. The full-policy control supplies the source policy from the same training material. Each distillation model produced one product Skill per workflow, and both used DeepSeek Flash for the editing stage. The additional controls ran after the main pairs.

## Case selection and interpretation

The historical collection contained 45 protocol entries. After grouping repeat runs and variants of the same invoice and requiring an actual first business submission, 15 distinct historical cases had a verifiable gain. In this batch, 16 new cases improved with both arms' UI traces and the finance recipient's first delivery available as evidence. Historical simulated ERP cases, historical native cases and the two current native workflows are counted separately. Fewer policy lookups on a first question, better drafts and interrupted runs do not count as improved business submissions.

The cases are synthetic and deliberately exercise the boundaries of company rules. The operator performs business actions in real local applications. The improved-case archive supports regression testing. The gains in this report use the entire batch fixed before evaluation, including ties and any declines. The four cases targeting each rule are related. These figures describe the two finance roles evaluated here. [Scores for all 40 cases](finance-scores.csv) · [First-submission histories](README.md)

## GLM and DeepSeek on cases where a Skill improved the score

The table selects cases from the scheduled DeepSeek sample where at least one Skill beat the common baseline and all three UI traces and receipts were verified. Both Skills face the same selection criterion. This subset measures their gains on cases with an observed improvement. The scheduled controls above give the comparison across the full sample.

| Task | Case | No Skill | GLM | DeepSeek | GLM gain | DeepSeek gain | GLM minus DeepSeek |
|---|---|---:|---:|---:|---:|---:|---:|
| Receivables | ar-23951 | 30 | 100 | 100 | +70 | +70 | +0 |
| Receivables | ar-21731 | 45 | 100 | 100 | +55 | +55 | +0 |
| Receivables | ar-26437 | 30 | 100 | 100 | +70 | +70 | +0 |
| Receivables | ar-22803 | 45 | 100 | 100 | +55 | +55 | +0 |
| Receivables | ar-23217 | 45 | 100 | 100 | +55 | +55 | +0 |
| Payables | ap-1026 | 0 | 100 | 100 | +100 | +100 | +0 |

Both Skills gained an average of 61.00 points over baseline on the five receivables cases and 100.00 on the one payables case. They tied on every case in the subset.

The same receivables Skill was also evaluated on 16 independent two-invoice remittances in the simulated ERP. Those scores are reported separately. [Two-invoice remittance results](remittances.md)
