# Bank chargeback workbooks

Two held-out ledgers require Finance to close eight invoices after twelve bank events. A single receipt may pay several invoices. A chargeback must identify the specific receipt and undo its surviving applications in reverse order, even when later receipts have paid the same invoices. The two ledgers have the same shape and different amounts. This is an office workbook task with a local submission queue. [Participant instructions](task.md) · [cb-17 template](cb-17/template.xlsx) · [cb-28 template](cb-28/template.xlsx)

Use Python 3 with openpyxl, LibreOffice Calc and a signed-in Codex CLI. Set `SOFFICE` if your LibreOffice executable is outside PATH and the standard macOS application directory. The adapter puts its Python interpreter on the operator's PATH. The operator may use local spreadsheet tools and code. Arm A receives the business rules and template. Arms B and C additionally receive the same archived GLM and DeepSeek cash Skills used for the native cash tasks. The budget is 900 seconds per independent session. The first submitted workbook is bound to its SHA-256 receipt.

```sh
python3 cases/chargebacks/run.py --case cb-17 --arm B --out /tmp/my-chargeback-trial
python3 cases/chargebacks/run.py --out /tmp/my-chargeback-batch
python3 cases/chargebacks/grade.py cases/chargebacks/cb-17/template.xlsx path/to/delivery.xlsx --out /tmp/my-chargeback-grade.json
```

The examiner runs an independent bank-event replay and recalculates the file in a fresh LibreOffice profile for each of eight input states. Each state has 48 formula-backed amounts to verify. The score is the percentage correct out of 384. Complete delivery requires all 384. The eight states cover initial values, two cutoff changes, a receipt amendment, revised invoice priority, reordered source records, an early overpayment and two reversals on one receipt. Only submitted workbooks receive a score for their cells. The scorer records the affected sheet, cell, expected amount and actual amount for each discrepancy.

## Native desktop delivery

On macOS with LibreOffice Calc, ownCloud and Rocket.Chat running, use the native entry point. It stages a synced copy of the same template, creates a private room and folder for each session, and reads back the file received by Finance when the first delivery notice arrives. The operator edits through Calc, uploads through Chrome and posts the exact filename. Each arm uses the same 900-second budget and workbook grader. Run on an idle desktop with native Computer Use access to Calc and Chrome. [Native participant instructions](native_task.md)

```sh
python3 cases/chargebacks/native.py --case cb-17 --arm A --out /tmp/my-native-workbook
python3 cases/chargebacks/native.py --out /tmp/my-native-workbook-batch
```
