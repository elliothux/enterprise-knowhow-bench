# Enterprise Know-How Benchmark: Technical Report

English · [简体中文](REPORT.zh-CN.md) · [Benchmark Overview](../README.md) · [Task Catalog](../tasks/README.md) · [Run and Scoring Guide](../tasks/RUN.md)

Enterprise Know-How Benchmark evaluates whether a language model agent executing complex cross-software back-office workflows, combining multi-step software operations, dense business judgment, and legacy business systems, can apply company-specific operational rules on its first formal submission. Across real cross-application desktop sessions and a deterministic legacy-style ERP desk, the benchmark holds the execution operator, tools, and transaction inputs constant while varying only the procedural knowledge available at runtime: historical closed precedents alone (Arm A), workflow Skills captured and distilled from prior demonstrations by [Lynx Cognition](https://enterprise.lynxai.work) using `GLM-5.3` (Arm B) or `DeepSeek Flash` (Arm C), and the full written company policy where scheduled (Arm D).

The cross-application environment builds on the self-hosted service stack from [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) ([Xu et al., 2024](https://arxiv.org/abs/2412.14161)), using containerized `ownCloud` and `Rocket.Chat` instances alongside native desktop browsers, spreadsheet applications, and an optional coworker NPC service. Every score in this report reflects the recipient's immutable first delivery across complete, pre-scheduled cohorts, including ties, incomplete ledgers, application crashes, and regressions.

## Summary of Findings

1. **Closed precedents alone leave systematic rule gaps on held-out cases.** When given current transaction documents and prior shift postings without an explicit procedure, `gpt-6.1-terra` (high reasoning effort) produced fully correct first submissions on **24/40 (60.0%)** native Chrome finance handoffs and **0/16 (0.0%)** two-invoice ERP remittances, referring 19 of 32 remittance lines for manual review and releasing an unverified bank-account payment (`AP-1026`).
2. **Distilled workflow Skills match the written policy control on rule-governed handoffs and transfer across interfaces.** Adding the `GLM-5.3` Skill raised native finance completion from **24/40 to 40/40 (100.0%)** without increasing median session duration (`148s → 150s` on receivables, `157s → 147s` on payables). On scheduled controls, both the `DeepSeek Flash` Skill (Arm C, 20 cases) and the full source policy text (Arm D, 10 cases) also scored **100.00**. Reusing the single-invoice Chrome receivables Skill in the simulated ERP CLI raised two-invoice remittance scores from **28.13 to 94.84** (`GLM-5.3`, 13/16 exact) and **100.00** (`DeepSeek Flash`, 16/16 exact).
3. **Distiller choice and product review matter on boundary residuals.** Across six matched cohorts, `GLM-5.3` and `DeepSeek Flash` Skills both improved over the unaided baseline. Before review, raw `DeepSeek Flash` payment-approval candidates scored **30/32 (93.75%)** due to one false release and one referral; after standard review in [Lynx Cognition](https://enterprise.lynxai.work), both distillers reached **32/32 (100.0%)**. Conversely, `DeepSeek Flash` closed small residual balances on three two-invoice remittances (`RMT-765`, `RMT-786`, `RMT-793`) where `GLM-5.3` scored `72.5`.
4. **Procedural know-how stops at global combinatorial search and fragile native GUI state.** On two 108-invoice monthly bank lockboxes with a proven unique global assignment (`lockbox-month-11`, `lockbox-month-23`), all three arms stopped at **54/108 (50.00%)** and **57/108 (52.78%)** when no scripting solver was permitted. On formula-driven bank chargeback workbooks (`cb-17`, `cb-28`), all three arms passed **384/384** checks per file when allowed local Python and spreadsheet authoring tools, whereas native `LibreOffice Calc` GUI sessions experienced repeated process crashes, a baseline crash-recovery isolation exception, and a `0/384` formula-omission failure under `GLM-5.3` on `cb-17`. A single-invoice arithmetic slip also lowered the `GLM-5.3` score from `100.00` to `91.25` on native shift `close-118`.

| Evaluation cohort | Execution surface | Scheduled scope | Metric | Precedents only (Arm A) | `GLM-5.3` Skill (Arm B) | `DeepSeek Flash` Skill (Arm C) | Oracle policy (Arm D) |
|---|---|---|---|---:|---:|---:|---:|
| [AR short-payment application](finance.md) | Native Chrome (`ownCloud` + `Rocket.Chat`) | 24 cases | Mean business score (exact) | 70.83 (12/24) | 100.00 (24/24) | 100.00 (12/12¹) | 100.00 (6/6¹) |
| [AP payment release review](finance.md) | Native Chrome (`ownCloud` + `Rocket.Chat`) | 16 cases | Mean business score (exact) | 75.00 (12/16) | 100.00 (16/16) | 100.00 (8/8¹) | 100.00 (4/4¹) |
| [Two-invoice remittances](remittances.md) | Simulated ERP CLI | 16 cases | Mean business score (exact) | 28.13 (0/16) | 94.84 (13/16) | 100.00 (16/16) | — |
| [Payment approval, raw vs. reviewed](distillers.md) | Simulated ERP CLI | 16 cases × 2 rounds | Exact decisions (raw → reviewed) | 25/32 (78.13%) | 32/32 → 32/32 | 30/32 → 32/32 | 32/32² |
| [Joint AR/AP close](batches/joint-close-20261119/README.md) | Simulated ERP CLI | 2 shifts (48 lines) | Mean business score (exact lines) | 50.31 (15/48) | 100.00 (48/48) | 100.00 (48/48) | — |
| [17:00 cutoff close](batches/cutoff-20261119/README.md) | Simulated ERP CLI | 2 shifts (16 invoices) | Actionable posted / handling score | 2/16 / 62.19 | 11/16 / 100.00 | 11/16 / 100.00 | — |
| [Month-end cash application](batches/month-end-20261119/README.md) | Native Chrome (`ownCloud` + `Rocket.Chat`) | 2 shifts (16 invoices) | Mean business score (exact lines) | 100.00 (16/16) | 95.63 (15/16) | 100.00 (16/16) | — |
| [Scanned POD inspection](batches/pod-inspection-20261119/README.md) | Multimodal ERP CLI | 2 shifts (16 claims) | Mean business score | 100.00 | 100.00 | 100.00 | — |
| [12-receipt bank lockbox](batches/lockbox-20261119/README.md) | Simulated ERP CLI | 2 shifts (72 invoices) | Verified placements | 45/72 (62.50%) | 72/72 (100.00%) | 45/72 (62.50%) | — |
| [36-receipt monthly lockbox](batches/monthly-lockbox-20261119/README.md) | Simulated ERP CLI | 2 shifts (216 invoices) | Verified placements | 111/216 (51.39%) | 111/216 (51.39%) | 111/216 (51.39%) | — |
| [Chargeback workbooks, local authoring](batches/chargeback-office-20261119/README.md) | Local Python + XLSX queue | 2 workbooks (768 checks) | Accepted files (`cb-17` / `cb-28`) | 2/2 (384 / 384) | 2/2 (384 / 384) | 2/2 (384 / 384) | — |
| [Chargeback workbooks, native Calc](batches/chargeback-native-20261119/README.md) | Native Calc → `ownCloud` → `Rocket.Chat` | 2 workbooks (768 checks) | Accepted files (`cb-17` / `cb-28`) | 1/2 (384 / 0) | 0/2 (0 / 140) | 1/2 (384 / 162) | — |

¹ Scheduled control subsets on the 40 native finance cases (20 paired cases for `DeepSeek Flash`, 10 paired cases for Oracle policy).  
² Two-round full-policy control on the historical 16-ticket payment approval protocol (`32/32`).

---

## 1. Motivation and Relation to Prior Work

General-purpose workplace benchmarks have shown that autonomous agents remain brittle outside software engineering. In [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) ([Xu et al., 2024](https://arxiv.org/abs/2412.14161)), agents interacting with realistic web and collaboration services recorded their lowest completion rates on finance and administrative tasks. Related evaluations examine complementary slices of enterprise capability: [OSWorld](https://arxiv.org/abs/2404.07972) tests multimodal desktop manipulation across native applications, [$\tau$-bench](https://github.com/sierra-research/tau-bench) and [CRMArena-Pro](https://arxiv.org/abs/2505.18878) test policy adherence in customer-facing APIs, and [SkillsBench](https://arxiv.org/abs/2602.12670) measures paired pass-rate lift when curated procedural modules are attached to container tasks.

In day-to-day enterprise operations, an incoming operator rarely starts from a blank slate or from a clean, self-contained rulebook. Instead, the operator inherits an active queue (such as Rocket.Chat requests and ownCloud folders) plus closed postings from earlier shifts. Three distinct failure modes arise in that setting:

1. **Missing institutional know-how**: Prior closed tickets illustrate past outcomes, yet finite examples under-determine exact company boundaries such as dual dollar-and-percentage write-off caps, whether posted credit memos reduce the discount base, grace-period cutoffs on bank value dates, or whether a waiver from an expired authority clears a payment hold.
2. **Consequential first-submission risk**: In accounts payable and cash application, the first instruction posted to a downstream queue triggers real actions. Referring every ambiguous ticket stalls throughput, whereas guessing releases funds to unverified accounts or grants unauthorized concessions. Grading only final state after unlimited retries conceals these operational errors.
3. **Structural task limits**: Even when an operator knows every accounting rule, tasks that require global combinatorial matching across a large ledger or sustained formula editing inside crash-prone desktop spreadsheets can still fail without dedicated tools.

Enterprise Know-How Benchmark separates these three factors by testing the same execution model across native GUI and CLI surfaces, grading only the first formal delivery, and pairing positive rule-learning cohorts with stress tests designed to expose where procedural Skills stop working.

---

## 2. Environment, Tasks, and Experimental Protocol

### 2.1 Execution Surfaces and Recorded Environment

All reported runs executed on an isolated `arm64` macOS 26.4 (`25E246`) host using `codex-cli 0.169.0`, Python `3.12.16`, and `gpt-6.1-terra` with `high` reasoning effort ([recorded environment](environment.json)). Tasks run on two primary surfaces:

* **Native Cross-Application Desktop**: Containerized `ownCloud 10.0.10` and `Rocket.Chat 5.3` services derived from [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) run locally with pinned image digests. For each trial, the runner seeds an isolated private channel and document folder. The operator uses native Google Chrome (`158.0.8127.37`) in a fresh Guest session (600-second limit on native finance, 900 seconds on workbooks) to inspect source PDFs, prior shift handoffs, and templates before posting a formal decision back to finance. Workbook cohorts additionally invoke `LibreOffice Calc` or `Apple Numbers`.
* **Simulated Legacy ERP Desk**: A rigid command-line posting desk (`./work read`, `./work submit`, 300-second session limit) modeled on internal enterprise ERP terminals without modern REST APIs or scripting consoles. It presents synthetic ledgers, prior postings, unreferenced legacy bank remittances, candidate triples, or scanned dock inspection diagrams with handwritten edits (`PNG`), locking the workspace upon receiving the first submission and returning an immutable SHA-256 receipt.

### 2.2 Paired Experimental Conditions

Each scheduled case runs in an independent model session per arm with identical prompts, tools, and transaction fixtures:

| Arm | Condition | Runtime materials provided to the operator |
|---|---|---|
| **A** | Precedents only (baseline) | Current case documents or ledger entries plus closed transactions from the previous shift |
| **B** | Lynx Cognition (`GLM-5.3`) Skill | Arm A materials plus a frozen workflow Skill distilled by [Lynx Cognition](https://enterprise.lynxai.work) from earlier demonstrations using `GLM-5.3` |
| **C** | Lynx Cognition (`DeepSeek Flash`) Skill | Arm A materials plus a frozen workflow Skill likewise distilled by [Lynx Cognition](https://enterprise.lynxai.work) from the same demonstrations using `DeepSeek Flash` |
| **D** | Oracle written policy | Arm A materials plus the full source company policy text from which training tasks were constructed |

The workflow Skills in Arms B and C were captured from prior native demonstrations and compiled into Markdown Skills through [Lynx Cognition](https://enterprise.lynxai.work) before evaluation began. Both distillation pipelines used `DeepSeek Flash` for their standard editing pass unless explicitly marked as `raw` (unreviewed candidate). No evaluated case appeared in the demonstration set, and no Skill contained case-specific answers or evaluator code.

### 2.3 Immutable First-Submission Grading

* **Receivables rubric (0–100 points per invoice)**: Awards 35 points for exact discount and claims transfer amounts, 35 points for exact write-off and remaining collectible balance, 20 points for assigning the correct follow-up owner, and 10 points for arithmetic reconciliation. Multi-invoice packets average across assigned rows and require 100 on every row for an exact completion.
* **Payables rubric (0 or 100 points per invoice)**: Awards 100 only when both the release/hold decision and the complete set of applicable hold reason codes match the answer key.
* **Protocol hygiene**: Extra messages, edited chat submissions, duplicate or unassigned invoice IDs, process timeouts, and missing deliveries score zero. On native Chrome cohorts, we report both the **business score** (verified from the recipient's message log) and a **strict protocol score** that assigns zero to any trial whose UI trace lacks automated verification of Guest-window closure or clean navigation.

---

## 3. Core Evaluation: Finance Handoffs and Cross-Surface Transfer

### 3.1 Native Cross-Application Finance Handoffs (40 Cases)

The primary native schedule comprises 40 held-out cases (24 accounts receivable short payments, 16 accounts payable release reviews) and 110 independent sessions (40 A/B pairs, 20 Arm C trials, and 10 Arm D trials). Full per-case details appear in the [native finance report](finance.md) and [finance-scores.csv](finance-scores.csv).

Across all 40 cases, mean business score rose from **72.50** in Arm A to **100.00** in Arm B, and exact first submissions rose from **24/40 (60.0%)** to **40/40 (100.0%)** (`+40.0` percentage points, 16 improved, 24 tied, 0 declined). The 40 cases were constructed across 10 orthogonal decision rules (four cases per rule):

| Decision rule probed | Domain | Cases | Arm A (No Skill) | Arm B (`GLM-5.3` Skill) | Gain | Improved / tied / declined |
|---|---|---:|---:|---:|---:|---|
| Posted credits and the write-off base | AR | 4 | 47.50 | 100.00 | +52.50 | 3 / 1 / 0 |
| Multiple independent payment release checks | AP | 4 | 50.00 | 100.00 | +50.00 | 2 / 2 / 0 |
| Bank grace period and payment instruction timing | AR | 4 | 55.00 | 100.00 | +45.00 | 3 / 1 / 0 |
| Absolute and percentage write-off limits | AR | 4 | 72.50 | 100.00 | +27.50 | 2 / 2 / 0 |
| Discount base and cap | AR | 4 | 72.50 | 100.00 | +27.50 | 2 / 2 / 0 |
| Waiver scope, authority, and expiry | AP | 4 | 75.00 | 100.00 | +25.00 | 1 / 3 / 0 |
| New bank account and verification record | AP | 4 | 75.00 | 100.00 | +25.00 | 1 / 3 / 0 |
| Shipment match and signed proof of delivery | AR | 4 | 82.50 | 100.00 | +17.50 | 1 / 3 / 0 |
| Cap on transfers to claims | AR | 4 | 95.00 | 100.00 | +5.00 | 1 / 3 / 0 |
| Authority and event order for closing a hold | AP | 4 | 100.00 | 100.00 | +0.00 | 0 / 4 / 0 |

The gains were not driven by a single outlier rule: dropping each rule group in turn left a mean gain between `+24.50` and `+34.00` on the remaining receivables cases and between `+16.67` and `+33.33` on the remaining payables cases.

**Concrete shifts in first submissions:**
* *Eliminating unnecessary referrals and misclassified residuals (`ar-22711` / invoice `I-22711`)*: Without a Skill, the operator could not infer from prior shift postings how an `OTHER`-labelled residual interacted with a posted credit memo, submitting `REFER I-22711: SGD 4.76 remains after cash and posted credit; prior examples do not establish write-off treatment for this OTHER-labelled residual.` (score `0`). With the Skill, it submitted `I-22711,0.00,0.00,0.00,4.76,COLLECTIONS` (score `100`).
* *Preventing unauthorized payment releases (`AP-1026` and `INV-15427`)*: On payables cases where invoice amounts matched but the vendor's new bank account lacked completed verification or triggered multiple independent holds, Arm A released the payment (`RELEASE,NONE`, score `0`), whereas Arm B placed it on hold with the exact required reason (`HOLD,BANK_UNVERIFIED`, score `100`; see [AP-1026 action history](cases/AP-1026/history.json)).

**Operational errors, strict browser verification, and latency:**
* Manual referrals dropped from `4` (1 AR, 3 AP) in Arm A to `0` in Arm B; excessive AR concessions dropped from `1` to `0`; incorrect AP payment releases dropped from `1` to `0`.
* Automated native browser trace checks passed on `23/24` (Arm A) vs. `22/24` (Arm B) receivables trials and `16/16` vs. `16/16` payables trials. Under the strict protocol that zeroes any failed browser check, mean scores rose from **66.67 to 91.67** on receivables (`+33.33` across the 21 pairs where both arms passed trace checks) and from **75.00 to 100.00** on payables.
* Median trial duration remained essentially unchanged: **148s → 150s** on receivables and **157s → 147s** on payables.

### 3.2 Cross-Surface Transfer to Two-Invoice ERP Remittances (16 Cases)

To test whether procedural know-how captured during single-invoice browser sessions transfers to a different tool interface and multi-invoice packet structure, the archived native receivables Skills were evaluated without modification on 16 held-out two-invoice remittances in the simulated ERP CLI ([remittances.md](remittances.md), [remittance-distillers-20261119](batches/remittance-distillers-20261119/README.md)).

* **Arm A (Precedents only)**: Mean business score **28.13**, **0/16** fully correct packets, **6/32** fully correct invoice lines, and **19/32** invoice lines referred for manual review across 11 packets.
* **Arm B (`GLM-5.3` Skill)**: Mean business score **94.84** (`+66.72`), **13/16** fully correct packets, **29/32** exact invoice lines, and **0/32** referrals. Scores improved on 15 packets and tied on one (`RMT-765` at `72.5`).
* **Arm C (`DeepSeek Flash` Skill)**: Mean business score **100.00** (`+71.88`), **16/16** fully correct packets, **32/32** exact invoice lines, and **0/32** referrals.

A separate pre-registered rerun on `RMT-716` ([layout-regression-20261119](batches/layout-regression-20261119/README.md)) reproduced the `0 → 100` A/B gap under the public export pipeline.

---

## 4. Controlled Ablations: Oracle Policy, Distiller Models, and Review

### 4.1 Distilled Know-How vs. Full Written Policy (Arm D)

On 10 pre-scheduled native finance cases (6 receivables, 4 payables), Arm D supplied the underlying written company policy directly in place of a distilled Skill. Arm D achieved **100.00** on both receivables and payables, matching Arm B (`100.00`, difference `+0.00`). On the historical 16-ticket payment approval protocol (2 rounds, 32 trials per arm), full-policy controls likewise scored **32/32 (100.0%)**, identical to the reviewed distilled Skills. Where written SOPs do not yet exist or have drifted from desk practice, demonstration distillation recovered equivalent decision accuracy on these rule sets.

### 4.2 `GLM-5.3` vs. `DeepSeek Flash` Distillers and Review Stage

[distillers.md](distillers.md) and [distiller-scores.csv](distiller-scores.csv) compare Skills generated from the same demonstration sets by `GLM-5.3` and `DeepSeek Flash`:

* **Head-to-head native finance sample (20 cases)**: Both distillers scored **100.00** across all 12 receivables and 8 payables cases (`79.75` baseline mean). On the 6 cases where baseline fell short (`ar-23951`, `ar-21731`, `ar-26437`, `ar-22803`, `ar-23217`, `ap-1026`), both Skills gained an identical `+61.00` mean points on AR and `+100.00` on AP.
* **Short-payment confirmation cohort (4 native tickets)**: Baseline averaged `43.75`, `GLM-5.3` averaged `86.25`, and `DeepSeek Flash` averaged `100.00` (diverging on [I-7547](cases/I-7547/history.json): `30` vs. `45` vs. `100`).
* **Two-invoice residual handling (16 ERP packets)**: On `RMT-765`, `RMT-786`, and `RMT-793`, the `GLM-5.3` Skill left a small balance in `COLLECTIONS` on one of the two invoices where policy called for closing it, scoring `72.5` on each packet (`29/32` lines exact overall). `DeepSeek Flash` captured that boundary condition and scored `100.0` on all three (`32/32` lines exact).
* **Effect of Skill review before freeze (32 ERP approval trials)**: Evaluating unreviewed (`raw`) distiller outputs across two 16-ticket rounds gave `25/32 (78.13%)` for baseline, `32/32 (100.00%)` for `GLM-5.3`, and `30/32 (93.75%)` for `DeepSeek Flash` (which released `INV-8259` and referred `INV-8350` in round 1 where both required an unverified-bank hold). After the standard product review step, `DeepSeek Flash` reached `32/32 (100.00%)`.

---

## 5. Stress Tests and Operational Boundaries

Subsequent frozen batches ([close-workflows.md](close-workflows.md)) probed multi-entity setoffs, external cutoff dependencies, visual dock inspections, combinatorial lockbox matching, and formula-backed spreadsheets. Every scheduled case is retained regardless of outcome.

### 5.1 Multi-Counterparty Setoff and Cutoff Escalation

* **Joint AR/AP close ([joint-close-20261119](batches/joint-close-20261119/README.md))**: Across shifts `net-31` and `net-42` (8 counterparties and 24 scored instructions per shift), errors in AR cash application propagate into AP exposure and legal-entity setoff holds. Arm A scored `28.33` (`5/24` exact) and `72.29` (`10/24` exact), averaging **50.31**. Both `GLM-5.3` and `DeepSeek Flash` Skills scored **100.00** on both shifts (**48/48** exact instructions).
* **Open exceptions at 17:00 cutoff ([cutoff-20261119](batches/cutoff-20261119/README.md))**: Shifts `cutoff-19` and `cutoff-27` (16 invoices total) contained 11 actionable invoices and 5 invoices blocked by signed external dependencies (an unallocated shared bank transfer, a pending bank trace, and a truncated credit memo reference). Arm A posted only **2/16 (12.50%)** by cutoff and averaged **62.19** on handling. Both Skills posted all **11/16 (68.75%)** actionable invoices (the exact automation ceiling permitted by upstream evidence) and routed all 5 blocked items to the correct owner (`WAIT`), achieving a **100.00** handling score with zero unauthorized postings.
* **Scanned proof-of-delivery claims ([pod-inspection-20261119](batches/pod-inspection-20261119/README.md))**: On `pod-47` and `pod-83` (two 60-pallet raster dock diagrams with four supervisor amendments per shift), all three arms scored **100.00**, confirming that visual diagram reading was already within the base operator's capability on this template.

### 5.2 Boundary 1: Global Combinatorial Disambiguation in Bank Lockboxes

In bank lockbox matching, the ERP pre-computes every locally balanced three-invoice triple for each deposit, and the operator must submit a globally disjoint assignment across the shift within 300 seconds using only the desk's read-and-submit commands (no Python or solver console).

* **12-receipt shifts ([lockbox-20261119](batches/lockbox-20261119/README.md), 36 invoices per shift)**: On `lockbox-76` (120 candidate triples), all three arms placed `36/36`. On `lockbox-41` (142 candidate triples), Arm A and `DeepSeek Flash` placed `9/36 (25.0%)`, while `GLM-5.3` placed `36/36 (100.0%)`.
* **36-receipt monthly shifts ([monthly-lockbox-20261119](batches/monthly-lockbox-20261119/README.md), 108 invoices per shift)**: Each ledger (`lockbox-month-11`, `lockbox-month-23`) combined 18 EDI receipts carrying explicit invoice references with 18 unreferenced legacy receipts (`241` and `243` locally valid triples respectively). An independent verifier ([verify_lockbox.py](../evaluation/verify_lockbox.py)) proves that each ledger admits exactly one complete disjoint solution. **All three arms left both shifts incomplete**, placing **54/108 (50.00%)** on `lockbox-month-11` (all 18 referenced receipts) and **57/108 (52.78%)** on `lockbox-month-23` (19 receipts). Skills improved operational safety (both Skills referred the remaining 17 ambiguous legacy receipts on `lockbox-month-23`, whereas Arm A submitted an invalid allocation), yet procedural instructions did not substitute for combinatorial search at scale.

### 5.3 Boundary 2: Native GUI Spreadsheets and Skill Regressions

* **Code authoring vs. native LibreOffice Calc ([chargeback-office-20261119](batches/chargeback-office-20261119/README.md) vs. [chargeback-native-20261119](batches/chargeback-native-20261119/README.md))**: Tasks `cb-17` and `cb-28` require a formula-driven XLSX workbook that reconciles 8 invoices across 12 bank events and recalculates accurately across 8 replayed bank states (`8 × 48 = 384` cell checks, 900-second budget). When permitted local Python (`openpyxl`) and spreadsheet tools, **all three arms achieved 384/384 on both templates (6/6 workbooks)**. When restricted to editing via native `LibreOffice Calc`, uploading to `ownCloud`, and notifying `Rocket.Chat`:
  * `LibreOffice Calc` crashed 2 to 3 times per session across all six runs.
  * On `cb-28`, first-delivery scores dropped to **0/384 (0.00%)** for Arm A, **140/384 (36.46%)** for `GLM-5.3`, and **162/384 (42.19%)** for `DeepSeek Flash`; during Calc crash recovery, the Arm A session also briefly displayed a prior trial's template before closing it (documented as a workspace isolation exception).
  * On `cb-17`, Arm A and `DeepSeek Flash` delivered **384/384**, whereas `GLM-5.3` uploaded a file lacking scoreable output formulas (**0/384**).
  * A historical A/B stress test on `Apple Numbers → ownCloud → Rocket.Chat` ([workbook-trials.json](workbook-trials.json)) showed a parallel GUI bottleneck: both Arm A and Arm B completed **1/2** scheduled attempts (one Numbers hang in Arm B; partial formula export loss in Arm A).
* **Single-invoice regression on native month-end cash ([month-end-20261119](batches/month-end-20261119/README.md))**: On `close-204`, all three arms scored `100.00`. On `close-118`, Arm A and `DeepSeek Flash` scored `100.00` (`8/8` invoices), while `GLM-5.3` scored **91.25** (`7/8` invoices, miscalculating the discount on `I-7180` as `SGD 7.66` instead of `8.16`, plus an unconfirmed Guest-window closure in the strict trace check).

---

## 6. Limitations and Scope of Claims

1. **Single fixed execution operator**: All main comparisons hold the operator fixed at `gpt-6.1-terra` (`high` reasoning) via `codex-cli 0.169.0` to isolate the effect of runtime procedural inputs. Absolute baselines and Skill gains will differ for weaker, stronger, or differently scaffolded agents; the public runner supports `--model` and `--agent` to test other systems directly.
2. **Domain concentration and synthetic ledgers**: Tasks use synthetic transactions modeled on real accounts receivable, accounts payable, procurement, and month-end close controls so that complete answer keys, counterfactual replay states, and public receipts can be distributed without customer PII. Results describe rule-governed operational workflows rather than open-ended creative or engineering work.
3. **Sample sizes in stress-test cohorts**: While the core native finance (`n = 40` cases, `110` sessions), two-invoice remittance (`n = 16` cases, `48` sessions), and payment approval (`n = 32` trials per arm) cohorts support multi-case aggregation, the exploratory close and native workbook stress tests evaluate two shifts or templates per workflow (`1` session per arm per case) to surface structural failure modes.

---

## 7. Artifact Index, Verification, and Citation

All public prompts, participant attachments, frozen schedules, scorers, and published receipts are stored in this repository and verified by the automated test suite:

```sh
python3 -m unittest discover -s tests
```

* **Detailed sub-reports**: [Native finance handoffs](finance.md) · [Two-invoice remittances](remittances.md) · [Distiller comparison](distillers.md) · [Close and workbook stress tests](close-workflows.md) · [Improved-case regression index](README.md) · [Frozen follow-up batches](batches/README.md)
* **Machine-readable scores**: [finance-scores.csv](finance-scores.csv) · [remittance-scores.json](remittance-scores.json) · [distiller-scores.csv](distiller-scores.csv) · [workbook-trials.json](workbook-trials.json) · [environment.json](environment.json)

### Acknowledgements and Citation

The self-hosted cross-application service images (`ownCloud`, `Rocket.Chat`), base account conventions, and vendor-quote task foundation come from [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany). Distilled Skills evaluated in Arms B and C were produced with [Lynx Cognition](https://enterprise.lynxai.work). When referencing this benchmark or its cross-application environment, please cite both works:

```bibtex
@misc{xu2024theagentcompanybenchmarkingllmagents,
  title={TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks},
  author={Frank F. Xu and Yufan Song and Boxuan Li and Yuxuan Tang and Kritanjali Jain and Mengxue Bao and Zora Z. Wang and Xuhui Zhou and Zhitong Guo and Murong Cao and Mingyang Yang and Hao Yang Lu and Amaad Martin and Zhe Su and Leander Maben and Raj Mehta and Wayne Chi and Lawrence Jang and Yiqing Xie and Shuyan Zhou and Graham Neubig},
  year={2024},
  eprint={2412.14161},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2412.14161}
}
```
