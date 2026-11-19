# Training and extension tasks

[Benchmark Overview](../README.md) · [Technical Report](../results/REPORT.md) · [Reported task catalog](../tasks/README.md)

These 11 task packets include frozen inputs for independent practice and evaluation on the [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) service stack. The reported batches cover a separate held-out set of 40 native finance cases, 16 two-invoice remittances, and subsequent close stress tests.

| Task | Training | Evaluation |
|---|---|---|
| Calculate landed cost and screen quotes | [Prompt and PDFs](suite/landed-cost-training/task.md) | [Prompt and PDFs](suite/landed-cost-evaluation/task.md) |
| Reconcile invoices | [Prompt and PDFs](suite/invoice-reconciliation-training/task.md) | [Prompt and PDFs](suite/invoice-reconciliation-evaluation/task.md) |
| Prepare a release package manifest | [Prompt and PDFs](suite/release-package-training/task.md) | [Prompt and PDFs](suite/release-package-evaluation/task.md) |
| Prepare payment release recommendations | [Prompt and PDFs](suite/payment-release-training/task.md) | [Prompt and PDFs](suite/payment-release-evaluation/task.md) |
| Build a replenishment workbook in Numbers | [Prompt and template](workbook/training/task.md) | [Prompt and template](workbook/evaluation/task.md) |
| Request a vendor quote | | [Prompt](vendor-quote/task.md) |

From the repository root, start a clean Compose environment and seed the documents and chat room for the chosen task ID. Give the participant the corresponding `task.md` and a separate workspace for the submission. Each task has a fixed room, so use a fresh service instance for each repeat. The verifier checks local files, shared links and the submission received by the business application.

```sh
docker compose up -d --wait
python3 benchmark/suite_data.py list
python3 benchmark/suite_data.py seed landed-cost-evaluation
# After the participant completes the task
python3 benchmark/suite_data.py verify landed-cost-evaluation --workspace /path/to/submission
```

The workbook tasks require native Numbers interaction and LibreOffice for recalculation. For the vendor quote, start the `vendor-quote` NPC profile, then follow the prompt to contact the vendor, download and upload the files, and share the result. Grade it with `python3 benchmark/verify_case.py --workspace /path/to/submission --output /path/to/grade.json`. [Service setup](../README.md#start-the-local-services)

Two additional bank chargeback cases require a formula-driven workbook that survives changes to the bank event stream. They have their own templates, runnable three-arm schedule and LibreOffice grader. [Bank chargeback task and reproduction commands](chargebacks/README.md)
