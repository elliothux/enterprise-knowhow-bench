# Task catalog

The original finance and remittance schedules contain 56 cases. Further close, inspection, cutoff and lockbox schedules are listed below. The archive adds 15 historical cases, two of which have an additional ledger variant listed separately. Select a case ID to read the participant prompt. For a manual trial, run `python3 bench.py prepare CASE --arm A --out TRIAL` and give the participant the generated `TRIAL/work/TASK.md` and its assigned tools. Use a new trial directory for each arm. In native tasks the runner fills the double-brace placeholders with the trial's room, folder and Chrome Guest marker.

[Benchmark Overview](../README.md) · [Technical Report](../results/REPORT.md) · [Running and scoring](RUN.md) · [Training and extension tasks](../cases/README.md) · [Machine-readable task manifest](manifest.json) · [Frozen run order and controls](schedule.json)

## Native Chrome finance cases

| Case | Inputs | Available arms |
|---|---|---|
| [ap-1018](ap-1018/TASK.md) | [Case inputs](../mock/finance/ap-1018) | A / B / C / D |
| [ap-1026](ap-1026/TASK.md) | [Case inputs](../mock/finance/ap-1026) | A / B / C / D |
| [ap-1037](ap-1037/TASK.md) | [Case inputs](../mock/finance/ap-1037) | A / B / C / D |
| [ap-1059](ap-1059/TASK.md) | [Case inputs](../mock/finance/ap-1059) | A / B / C / D |
| [ap-723](ap-723/TASK.md) | [Case inputs](../mock/finance/ap-723) | A / B / C / D |
| [ap-741](ap-741/TASK.md) | [Case inputs](../mock/finance/ap-741) | A / B / C / D |
| [ap-762](ap-762/TASK.md) | [Case inputs](../mock/finance/ap-762) | A / B / C / D |
| [ap-779](ap-779/TASK.md) | [Case inputs](../mock/finance/ap-779) | A / B / C / D |
| [ap-806](ap-806/TASK.md) | [Case inputs](../mock/finance/ap-806) | A / B / C / D |
| [ap-815](ap-815/TASK.md) | [Case inputs](../mock/finance/ap-815) | A / B / C / D |
| [ap-839](ap-839/TASK.md) | [Case inputs](../mock/finance/ap-839) | A / B / C / D |
| [ap-854](ap-854/TASK.md) | [Case inputs](../mock/finance/ap-854) | A / B / C / D |
| [ap-907](ap-907/TASK.md) | [Case inputs](../mock/finance/ap-907) | A / B / C / D |
| [ap-911](ap-911/TASK.md) | [Case inputs](../mock/finance/ap-911) | A / B / C / D |
| [ap-924](ap-924/TASK.md) | [Case inputs](../mock/finance/ap-924) | A / B / C / D |
| [ap-953](ap-953/TASK.md) | [Case inputs](../mock/finance/ap-953) | A / B / C / D |
| [ar-21367](ar-21367/TASK.md) | [Case inputs](../mock/finance/ar-21367) | A / B / C / D |
| [ar-21489](ar-21489/TASK.md) | [Case inputs](../mock/finance/ar-21489) | A / B / C / D |
| [ar-21731](ar-21731/TASK.md) | [Case inputs](../mock/finance/ar-21731) | A / B / C / D |
| [ar-21943](ar-21943/TASK.md) | [Case inputs](../mock/finance/ar-21943) | A / B / C / D |
| [ar-22153](ar-22153/TASK.md) | [Case inputs](../mock/finance/ar-22153) | A / B / C / D |
| [ar-22279](ar-22279/TASK.md) | [Case inputs](../mock/finance/ar-22279) | A / B / C / D |
| [ar-22711](ar-22711/TASK.md) | [Case inputs](../mock/finance/ar-22711) | A / B / C / D |
| [ar-22803](ar-22803/TASK.md) | [Case inputs](../mock/finance/ar-22803) | A / B / C / D |
| [ar-23217](ar-23217/TASK.md) | [Case inputs](../mock/finance/ar-23217) | A / B / C / D |
| [ar-23387](ar-23387/TASK.md) | [Case inputs](../mock/finance/ar-23387) | A / B / C / D |
| [ar-23641](ar-23641/TASK.md) | [Case inputs](../mock/finance/ar-23641) | A / B / C / D |
| [ar-23951](ar-23951/TASK.md) | [Case inputs](../mock/finance/ar-23951) | A / B / C / D |
| [ar-24139](ar-24139/TASK.md) | [Case inputs](../mock/finance/ar-24139) | A / B / C / D |
| [ar-24397](ar-24397/TASK.md) | [Case inputs](../mock/finance/ar-24397) | A / B / C / D |
| [ar-24513](ar-24513/TASK.md) | [Case inputs](../mock/finance/ar-24513) | A / B / C / D |
| [ar-24857](ar-24857/TASK.md) | [Case inputs](../mock/finance/ar-24857) | A / B / C / D |
| [ar-25249](ar-25249/TASK.md) | [Case inputs](../mock/finance/ar-25249) | A / B / C / D |
| [ar-25407](ar-25407/TASK.md) | [Case inputs](../mock/finance/ar-25407) | A / B / C / D |
| [ar-25673](ar-25673/TASK.md) | [Case inputs](../mock/finance/ar-25673) | A / B / C / D |
| [ar-25811](ar-25811/TASK.md) | [Case inputs](../mock/finance/ar-25811) | A / B / C / D |
| [ar-26193](ar-26193/TASK.md) | [Case inputs](../mock/finance/ar-26193) | A / B / C / D |
| [ar-26437](ar-26437/TASK.md) | [Case inputs](../mock/finance/ar-26437) | A / B / C / D |
| [ar-26741](ar-26741/TASK.md) | [Case inputs](../mock/finance/ar-26741) | A / B / C / D |
| [ar-26905](ar-26905/TASK.md) | [Case inputs](../mock/finance/ar-26905) | A / B / C / D |

## Two-invoice remittances in the simulated ERP

| Case | Inputs | Available arms |
|---|---|---|
| [RMT-716](RMT-716/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-723](RMT-723/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-730](RMT-730/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-737](RMT-737/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-744](RMT-744/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-751](RMT-751/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-758](RMT-758/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-765](RMT-765/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-772](RMT-772/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-779](RMT-779/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-786](RMT-786/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-793](RMT-793/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-800](RMT-800/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-807](RMT-807/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-814](RMT-814/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |
| [RMT-821](RMT-821/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / C |

## Historical cases and ledger variants

| Case | Inputs | Available arms |
|---|---|---|
| [I-7103](I-7103/TASK.md) | [Case inputs](../mock/historical/I-7103) | A / B / C / D |
| [I-7381](I-7381/TASK.md) | [Case inputs](../mock/historical/I-7381) | A / B / C / D |
| [I-7423](I-7423/TASK.md) | [Case inputs](../mock/historical/I-7423) | A / B / C / D |
| [I-7547](I-7547/TASK.md) | [Case inputs](../mock/historical/I-7547) | A / B / C / D |
| [INV-8259](INV-8259/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8259-clear](INV-8259-clear/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B |
| [INV-8266](INV-8266/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8273](INV-8273/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8273-clear](INV-8273-clear/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B |
| [INV-8287](INV-8287/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8294](INV-8294/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8322](INV-8322/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8329](INV-8329/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8336](INV-8336/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8350](INV-8350/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [INV-8385](INV-8385/TASK.md) | [invoices-history](../tasks/materials/precedents-c74b38b6b289.txt) | A / B / C / D |
| [T-320](T-320/TASK.md) | [Use the trial lookup tool](RUN.md#run-a-case-manually) | A / B / C |

## Month-end cash application in native Chrome

Each task requires the operator to reconcile eight invoices across five documents in ownCloud and send one posting file as a message in Rocket.Chat. Each arm gets its own private room and folder. The assigned Skill and rubric are frozen before the first session. [Run guide](RUN.md) · [Schedule](schedules/month-end.json)

| Task | Participant packet | Available arms |
|---|---|---|
| [close-118](close-118/TASK.md) | [Journal, advice, approvals, register and closing instruction](../mock/month-end/close-118) | A / B / C |
| [close-204](close-204/TASK.md) | [Journal, advice, approvals, register and closing instruction](../mock/month-end/close-204) | A / B / C |

## Joint receivables and payables close in the simulated ERP

For each of eight counterparties, post two short payments, carry the collectible AR balance into AP and issue a payment decision under a scoped setoff mandate. Each shift produces 24 scored invoice instructions. [Run guide](RUN.md) · [Schedule](schedules/joint-close.json)

| Shift | Current ledgers | Available arms |
|---|---|---|
| [net-31](net-31/TASK.md) | [Current records and mandates](../mock/joint-close/net-31/current-registers.txt) | A / B / C |
| [net-42](net-42/TASK.md) | [Current records and mandates](../mock/joint-close/net-42/current-registers.txt) | A / B / C |

The [bank chargeback workbook cases](../cases/chargebacks/README.md) have a separate entry point for XLSX delivery and multi-state recalculation.

## Scanned proof-of-delivery claims

Each case provides two signed receiving diagrams. Read the bay quantities and marks, apply the supervisor's four amendments and submit eight claim postings. All arms see the same diagrams and ledger. [Three-arm schedule](schedules/pod-inspection.json)

| Case | North dock | South dock | Available arms |
|---|---|---|---|
| [pod-47](pod-47/TASK.md) | [Inspection sheet](../mock/pod-inspection/pod-47/North.png) | [Inspection sheet](../mock/pod-inspection/pod-47/South.png) | A / B / C |
| [pod-83](pod-83/TASK.md) | [Inspection sheet](../mock/pod-inspection/pod-83/North.png) | [Inspection sheet](../mock/pod-inspection/pod-83/South.png) | A / B / C |

## Bank lockbox matching

All 36 invoices and all twelve receipts are present. Each bank deposit covers three invoices. The ERP displays every locally balanced triple, and the operator must find a globally consistent posting without double allocation. [Run instructions](RUN.md#bank-lockbox-matching) · [Schedule](schedules/lockbox.json)

| Shift | Register and candidate suggestions | Available arms |
|---|---|---|
| [lockbox-41](lockbox-41/TASK.md) | [Ledger and ERP suggestions](../mock/lockbox/lockbox-41) | A / B / C |
| [lockbox-76](lockbox-76/TASK.md) | [Ledger and ERP suggestions](../mock/lockbox/lockbox-76) | A / B / C |

## Invoices still open at cutoff

Each eight-invoice shift includes a signed status register identifying external evidence still pending. Finance records the share actually posted correctly by cutoff and whether each invoice received the correct posting or escalation. [Schedule](schedules/cutoff.json) · [Scoring](RUN.md#invoices-still-open-at-cutoff)

| Shift | Status register and invoices | Available arms |
|---|---|---|
| [cutoff-19](cutoff-19/TASK.md) | [Evidence at 17:00](../mock/cutoff/cutoff-19/status-and-ledgers.txt) | A / B / C |
| [cutoff-27](cutoff-27/TASK.md) | [Evidence at 17:00](../mock/cutoff/cutoff-27/status-and-ledgers.txt) | A / B / C |

### Month-end lockbox shifts

For each larger shift the ERP contains 108 open invoices, 18 electronic remittances with references and 18 legacy remittances that require cross-receipt matching. The two payers have separate ledgers. [Schedule](schedules/monthly-lockbox.json) · [Independent uniqueness verifier](../evaluation/verify_lockbox.py)

| Shift | Source registers and exact candidate triples | Available arms |
|---|---|---|
| [lockbox-month-11](lockbox-month-11/TASK.md) | [Inputs](../mock/lockbox/lockbox-month-11) | A / B / C |
| [lockbox-month-23](lockbox-month-23/TASK.md) | [Inputs](../mock/lockbox/lockbox-month-23) | A / B / C |
