# Enterprise Know-How Benchmark

English · [简体中文](README.zh-CN.md) · [Benchmark Report](results/REPORT.md) · [Task Catalog](tasks/README.md) · [Run Guide](tasks/RUN.md)

Most AI agent benchmarks test one of two things: either pure context reading (handing the model a clean, complete rulebook in the prompt) or pure execution (clicking through apps and writing code from explicit instructions).

Real enterprise work rarely looks like either. Experienced employees carry operational rules in their heads rather than in up-to-date manuals, and whoever takes over a queue usually gets only the open tickets plus a few closed examples from the last shift. **Can an AI reconstruct company rules from a handful of prior tickets alone? And when it cannot, can we distill that enterprise know-how directly from real employee operations so the agent gets the job right?**

Enterprise Know-How Benchmark is built to test exactly that. Built on the self-hosted workplace stack (`ownCloud`, `Rocket.Chat`, and coworker NPCs) from [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany), it evaluates finance, procurement, and month-end close workflows where unwritten company rules determine whether a delivery is right or wrong.

## What Kind of Real Enterprise Workflows Do We Test?

Rather than isolated Q&A prompts or clean modern API calls, every task in this benchmark reflects **complex cross-software workflows from real enterprise operations**:

* **Multi-application coordination**: Taking finance as an example, the agent must work across tools just like a staff operator: picking up requests and checking with colleagues in `Rocket.Chat`, pulling multi-page PDFs, bank advices, and prior shift handoffs from `ownCloud`, building formula sheets in `LibreOffice Calc` or `Numbers`, and posting formal instructions back to the queue.
* **Dense business judgment woven into software operations**: Every operational step carries intertwined business decisions, such as whether posted credit memos reduce the cash-discount base, whether a short-payment write-off hits a dollar or percentage cap, how collectible AR balances trigger legal-entity AP setoff holds, or which open items can post before cutoff. Missing one judgment call throws off the entire submission.
* **Legacy business systems and messy back-office artifacts**: Real back-office operations rarely run on polished modern SaaS alone. Our tasks include **rigid legacy ERP desks** with fixed read/post commands and no modern APIs or scripting consoles, unreferenced legacy bank remittances missing electronic invoice IDs, scanned paper dock receipts with handwritten supervisor edits, and crash-prone traditional desktop spreadsheets.

## Why Enterprise Know-How Matters for Real-World AI Deployment

Across these cross-software, judgment-heavy, legacy-system workflows, knowing how to click UI buttons or run terminal commands is just table stakes. What actually decides whether an AI can be trusted in production is **whether it knows the company's tacit operational rules**:

* When a customer short-pays an invoice by a few dollars, when is it a valid discount or write-off, and when must it go to collections?
* When a vendor submits a new bank account that has not finished verification, can the payment go out?
* At month-end cutoff, which open items can be posted right away, and which ones must wait on the bank or controller?

Without that know-how, an agent can finish every software step smoothly and still cause a production incident. On payables ticket [AP-1026](results/cases/AP-1026/history.json), for example, the agent without workflow know-how saw matching paperwork and released funds to an unverified new bank account (`RELEASE`); with distilled operational know-how, it caught the risk and held the payment (`HOLD,BANK_UNVERIFIED`). Because real finance queues do not allow trial-and-error retries, every task in this benchmark grades the **first formal submission** received by finance.

## Distilling Know-How from Real Employee Operations: Does It Work?

Using the same execution model (`gpt-6.1-terra`), we compare four conditions in order:

* **Arm A (Prior tickets only)**: Current case documents plus closed examples from the last shift (unaided baseline)
* **Arm B (Lynx Cognition · `GLM-5.3` distilled Skill)**: Arm A materials + a workflow Skill automatically distilled from recorded employee desktop demonstrations by [Lynx Cognition](https://enterprise.lynxai.work) using `GLM-5.3`
* **Arm C (Lynx Cognition · `DeepSeek Flash` distilled Skill)**: Arm A materials + a workflow Skill likewise distilled by [Lynx Cognition](https://enterprise.lynxai.work) from the same employee demonstrations, using lightweight `DeepSeek Flash`
* **Arm D (Full written company policy)**: Arm A materials + the complete written company policy manual directly (oracle upper-bound control)

| Workflow | Environment | Scope | Arm A: Prior tickets only | Arms B / C: + Distilled Know-How | What changed |
|---|---|---:|---:|---:|---|
| [AR short-payment application](results/finance.md) | Native Chrome (`ownCloud` + `Rocket.Chat`) | 24 cases | 12/24 exact (mean 70.8) | **24/24 exact (mean 100)** | Eliminated write-off base, dual-cap, and bank grace-period errors |
| [AP payment release review](results/finance.md) | Native Chrome (`ownCloud` + `Rocket.Chat`) | 16 cases | 12/16 exact (mean 75.0) | **16/16 exact (mean 100)** | Blocked unverified bank releases and expired or unauthorized waivers |
| [Two-invoice remittances](results/remittances.md) | Legacy ERP desk (CLI) | 16 cases | 0/16 exact (mean 28.1) | **13/16 (Arm B) / 16/16 (Arm C)** | Single-ticket browser Know-How transferred to legacy ERP CLI; referrals dropped 19/32 → 0 |
| [Joint AR/AP close](results/batches/joint-close-20261119/README.md) | Legacy ERP desk (CLI) | 48 lines | 15/48 exact (mean 50.3) | **48/48 exact (mean 100)** | Carried accurate AR exposure into legal-entity AP setoff holds |
| [Month-end cutoff handling](results/batches/cutoff-20261119/README.md) | Legacy ERP desk (CLI) | 16 invoices | 2/16 posted (score 62.2) | **11/16 posted (score 100)** | Posted every actionable item and escalated all 5 externally blocked items |

Three practical takeaways stand out:

1. **Distilling from real employee operations matches hand-written policy manuals.** Across 40 held-out native Chrome finance tickets, exact first submissions jumped from **24/40 (60%) to 40/40 (100%)** with no added latency (~150s median per ticket). On the 10 scheduled written-policy control cases, the distilled Skills (Arms B / C) matched the full written policy (Arm D) at **100/100**. Teams do not need months of manual documentation before deploying agents; recording how experienced staff actually work recovers the rules.
2. **Distilled Know-How transfers across modern and legacy systems, even with lightweight distillers.** The receivables Skill learned from single-invoice browser demonstrations transferred directly to two-invoice remittances on a legacy ERP CLI desk. Both `GLM-5.3` (Arm B) and lightweight `DeepSeek Flash` (Arm C) hit **100** on the 20-ticket native head-to-head subset, and Arm C reached **16/16 exact** on two-invoice remittances ([distiller comparison](results/distillers.md)).
3. **The boundaries are clear too.** Stress tests show what operational know-how alone does not solve. On 108-invoice monthly bank lockboxes mixing 18 EDI advices with 18 unreferenced legacy remittances (requiring global combinatorial matching across 240+ local candidates on an ERP desk with no scripting solver), every setup stopped at **50%–53%** ([details](results/batches/monthly-lockbox-20261119/README.md)). Editing formula-heavy chargeback sheets inside native `LibreOffice Calc` hit app crashes and missing formulas ([details](results/batches/chargeback-native-20261119/README.md)), and one native month-end shift (`close-118`) saw a single-invoice discount slip. Know-how teaches the agent **company rules**; code tools and reliable software handle **heavy computation and fragile UIs**. See the full [Benchmark Report](results/REPORT.md).

## Run a case

Use Python 3.10 or later. The two-invoice example below needs no Docker services and compares the same model without know-how (`--arm A`) vs. with distilled know-how (`--arm B` or `--arm C`). It uses a signed-in Codex CLI by default; pass `--model` to pick another model or `--agent` to plug in your own agent ([Task catalog](tasks/README.md) · [Run and scoring guide](tasks/RUN.md)):

```sh
git clone https://github.com/elliothux/lynx-benchmark.git
cd lynx-benchmark
python3 bench.py list
runs=$(mktemp -d)
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
```

For a native cross-application ticket (using Chrome to read `ownCloud` PDFs and submit to `Rocket.Chat`, supporting `--arm A/B/C/D`), start the local services below and run `python3 bench.py run ar-22153 --arm B --out "$runs/chrome-B"`. Eleven additional training and extension packets (landed cost, invoice reconciliation, release manifests, Numbers workbooks, and vendor-quote NPCs) live in [cases/README.md](cases/README.md).

## Start the local services

Use Docker Compose v2.24+, Python 3, and a Docker engine that supports `linux/amd64` images. Run from the repository root:

```sh
docker compose up -d --wait
python3 mock/seed.py --case ar-22153
```

Open `Documents/Enterprise review ar-22153` in [ownCloud](http://localhost:8092) for the current documents and prior shift handoff, and `finance-review-ar-22153` in [Rocket.Chat](http://localhost:13000) for the incoming request (both use `theagentcompany` as username and password; omit `--case` to load all 40 native finance tickets). For the optional vendor-quote coworker NPC, copy `.env.example` to `.env`, set the model endpoint, and run `docker compose --profile vendor-quote up -d --wait`.

## Reports and Data

Published results include every case in each pre-scheduled batch (ties, incomplete ledgers, crashes, and regressions included). Run `python3 -m unittest discover -s tests` from the repository root to verify the public graders against all published receipts:

* [Full Benchmark Report](results/REPORT.md)
* [Native cross-application finance report (40 cases)](results/finance.md) · [All 40 scores CSV](results/finance-scores.csv)
* [Two-invoice remittance report (16 cases)](results/remittances.md) · [Distiller comparison](results/distillers.md)
* [Month-end close and workbook boundary report](results/close-workflows.md) · [Improved-case histories](results/README.md) · [Follow-up batches](results/batches/README.md)

## Acknowledgements and Citation

The containerized workplace services (`ownCloud`, `Rocket.Chat`), base fixtures, and vendor-quote task setup build on [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany). Distilled workflow Skills evaluated in this benchmark were generated from employee demonstrations using [Lynx Cognition](https://enterprise.lynxai.work). All ledger transactions are synthetic.

If you use Enterprise Know-How Benchmark in your research or evaluations, please cite TheAgentCompany:

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
