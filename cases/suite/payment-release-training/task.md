# payment-release / payment-release-training

Prepare a simulated payment-release recommendation for every business key on the dossier roster.
This task produces advice only. Do not initiate, schedule or approve any actual payment.

ownCloud: http://localhost:8092, folder `Documents/Benchmark Suite/payment-release-training`.
Start with `01-readme-policy.pdf` (README/index); the source dossier is complete.
RocketChat: http://localhost:13000, room `suite-payment-release-training` (location only, no extra business facts).
Login for both services: `theagentcompany` / `theagentcompany`.

Create `payment-release.csv` with exactly these columns:
`invoice_id,vendor_id,decision,reason_codes,net_payable_sgd,bank_account_ref,evidence_refs`.
After generating the CSV, use TextEdit or another native text viewer through native CUA to open
the actual local CSV file and review EVERY row visibly. Do not rebuild its contents in a data:text
URL as a substitute for reading the file. Close the reviewed document, then return to this run's
Chrome Guest, bring it to the
foreground, and upload/share. This actual-file review must appear in the native recording/trace.
Upload the CSV to the same ownCloud folder, share that CSV publicly without password/login,
save only the URL in local `link.txt`, and post the URL in the assigned RocketChat room.

Download all eight original PDFs and read them through native CUA. Business reading, download,
review, upload, sharing and chat must use native CUA; local final-file generation is allowed.
Do not use HTTP/APIs, DOM, PDF parsers, shell downloads, hidden fixtures/oracle, or other runs.
Use only the assigned workspace and browser. A/B have identical task, sources and permissions.
Time budget: 1200 seconds. Report incomplete work honestly.
