# landed-cost / landed-cost-evaluation

Compare procurement quotes and deliver every supplier meeting all specifications and the tax-inclusive order budget.

Use ownCloud http://localhost:8092, folder `Documents/Benchmark Suite/landed-cost-evaluation`.
Read `rules.pdf` first and all other source PDFs. The complete business rules are public there.
RocketChat http://localhost:13000 private room `suite-landed-cost-evaluation` contains the same fixed-facts bulletin.
Login for both services: `theagentcompany` / `theagentcompany`.
Existing unrelated Emma/Sarah procurement conversations are not sources for this task.

Create `landed-cost.csv` with exact columns `vendor_id,quote_id,cpu_cores,ram_gb,landed_total_sgd,budget_remaining_sgd`.
Upload it into the source folder. Create a public share of that CSV accessible without login,
save only its URL in local `link.txt`, and post it to the suite RocketChat room.

Business download, reading and upload must use native CUA. Local CSV/file generation is allowed.
Do not read repository fixture, manifest, evaluator, tests or other runs. Do not use APIs, HTTP,
shell downloads, PDF parsers, browser DOM or scripts to inspect business files.
Use only this trial's workspace and browser context. Both A and B receive these same instructions,
sources and complete rules. Target time budget: 600 seconds; report failure honestly if incomplete.
