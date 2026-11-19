# Task catalog

The two scheduled batches contain 56 cases. The archive adds 15 historical cases, two of which have an additional ledger variant listed separately. Select a case ID to read the participant prompt. For a manual trial, run `python3 bench.py prepare CASE --arm A --out TRIAL` and give the participant the generated `TRIAL/work/TASK.md` and its assigned tools. Use a new trial directory for each arm. In native tasks the runner fills the double-brace placeholders with the trial's room, folder and Chrome Guest marker.

[Running and scoring](RUN.md) · [Training and extension tasks](../cases/README.md) · [Machine-readable task manifest](manifest.json) · [Frozen run order and controls](schedule.json)

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
| [RMT-716](RMT-716/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-723](RMT-723/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-730](RMT-730/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-737](RMT-737/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-744](RMT-744/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-751](RMT-751/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-758](RMT-758/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-765](RMT-765/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-772](RMT-772/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-779](RMT-779/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-786](RMT-786/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-793](RMT-793/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-800](RMT-800/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-807](RMT-807/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-814](RMT-814/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |
| [RMT-821](RMT-821/TASK.md) | [invoices-history](../mock/remittances/prior-postings.txt) | A / B / D |

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
