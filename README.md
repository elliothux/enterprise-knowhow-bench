# Lynx Benchmark

English · [简体中文](README.zh-CN.md)

Lynx Benchmark measures whether a model makes better finance decisions when it can use a workflow Skill distilled by Lynx Cognition from earlier demonstrations. In 40 synthetic cases fixed before evaluation, the same model used Chrome to read supporting documents in ownCloud and submit a decision to finance in Rocket.Chat. With the GLM-distilled Skill, the number of fully correct first submissions rose from **24/40 to 40/40**. Scores improved on 16 cases and stayed the same on 24.

| Task | Cases | Mean without Skill | Mean with GLM Skill | Fully correct first submissions, without → with |
|---|---:|---:|---:|---:|
| Apply short payments to receivables in Chrome | 24 | 70.83 | 100.00 | 12/24 → 24/24 |
| Review payments for release in Chrome | 16 | 75.00 | 100.00 | 12/16 → 16/16 |
| Apply two-invoice remittances in a simulated ERP CLI | 16 | 28.13 | 94.84 | 0/16 → 13/16 |

The receivables tasks score how the model allocates a short payment, balances the amounts and assigns follow-up. Payables tasks require the correct decision and every applicable reason. On one payables case, the baseline released a payment to a new bank account. With the Skill, the model placed it on hold because the account had yet to be verified. [Compare the submissions and action histories](results/cases/AP-1026/history.json).

The GLM and DeepSeek Skills both scored 100 on all 20 cases selected in advance for a head-to-head comparison. On six of those cases, both improved on the baseline by the same amount. Supplying the full policy also earned full marks on all ten cases scheduled for that control. These cases target the rules of two finance roles. Business scores use the first submission received by finance. The native report also gives scores under a stricter protocol that assigns zero when the browser trace fails verification. [Native finance report](results/finance.md) · [Simulated ERP report](results/remittances.md)

## Run a case

Use Python 3.10 or later. This two-invoice example runs with a signed-in Codex CLI and needs no Docker services. Arm A runs without a Skill. Arm B receives the GLM Skill. Use the same execution model for both arms. Select an available model with `--model`, or use your own agent. [Task catalog and inputs](tasks/README.md) · [Agent setup and scoring](tasks/RUN.md)

```sh
git clone https://github.com/elliothux/lynx-benchmark.git
cd lynx-benchmark
python3 bench.py list
runs=$(mktemp -d)
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
```

For a native cross-application case, start the local services described below and run `python3 bench.py run ar-22153 --arm A --out "$runs/chrome-A"`. The runner creates a case for this trial, loads two PDFs and scores the first submission to the finance queue. You can also run cases manually, execute a full batch or use the original training and extension tasks. [Run guide](tasks/RUN.md) · [11 additional task packets](cases/README.md)

## Run history

The archive contains 46 distinct cases with a documented improvement on at least one scored first submission. Of these, 31 come from the current batches and 15 from earlier experiments. Twenty used native Chrome and 26 used the simulated ERP CLI. Each record includes conditions, scores, first submissions, actions in order and checksums for the source logs. The reports use every case in the scheduled batch to calculate their results. [Archive of improved cases](results/README.md) · [All 40 native scores](results/finance-scores.csv) · [All 16 remittance scores](results/remittance-scores.json) · [Recorded environment](results/environment.json)

Later runs are grouped by frozen batch. The November 19 targeted RMT-716 rerun scored 0 without a Skill and 100 with the GLM Skill. [Additional batches and receipts](results/batches/README.md)

## Start the local services

Use Docker Compose v2.24 or later, Python 3 and a Docker engine that can run `linux/amd64` images. Run these commands at the repository root. The first start downloads upstream images pinned by digest and imports the initial Rocket.Chat data.

```sh
docker compose up -d --wait
python3 mock/seed.py --case ar-22153
```

In ownCloud, open `Documents/Enterprise review ar-22153` to read the current documents and the previous shift's handoff. In Rocket.Chat, open the private room `finance-review-ar-22153` for the initial request. Both services use `theagentcompany` as the demo username and password. The ports bind to the loopback interface. [Open ownCloud](http://localhost:8092) · [Open Rocket.Chat](http://localhost:13000)

Omit `--case` to load all 40 native finance cases. Rerunning the seed command checks existing files and reuses the initial messages. The seeding account sends the initial request. In the reported experiments, a separate finance account verified the operator's first submission. The published runs used a native macOS VM. Compose provides the corresponding business services and fixtures, and `bench.py` prepares, runs and scores cases. [Simulated ERP remittance data](mock/remittances)

The optional vendor-quote NPC uses Redis and a model API. Copy `.env.example` to `.env`, enter the NPC configuration and run `docker compose --profile vendor-quote up -d --wait`. To stop the services and retain their data, run `docker compose stop`.

## Maintainers

A standard public clone includes the tasks, participant materials, runner and business scoring. The public repository is the source for all released cases and scoring fixtures. The private runner reads those files from this checkout and keeps raw trial evidence in its own `archives/` directory. Maintainers with private repository access can also fetch the pinned internal runner with `git submodule update --init runner`.

The service images and base fixtures come from TheAgentCompany. The benchmark uses synthetic transactions and a test finance queue. [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany)

Run `shasum -a 256 -c SHA256SUMS` from the repository root to verify the task packets, participant materials, fixtures and published results.
