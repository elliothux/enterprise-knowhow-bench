# Running and scoring the benchmark

Python 3.10 or later can list tasks, run the simulated ERP, read receipts and score submissions. The default agent adapter uses a signed-in Codex CLI. Give each arm a fresh directory and model session. Give the participant only the prepared `work/TASK.md` and the business tools specified for that trial. Keep answer keys, published histories and materials for other arms with the evaluator.

## Run one case or a batch

```sh
runs=$(mktemp -d)
python3 bench.py list
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
python3 bench.py batch remittances --out "$runs/packets"
```

The default adapter passes the prompt to Codex on standard input and runs it in the participant workspace with full access, using the signed-in user's configuration and plugins. Run it in your own test environment. Use `--codex /path/to/codex` to choose the executable or `--model MODEL` to choose the execution model. The default matches the report, `gpt-6.1-terra` with high reasoning effort. Keep the execution model the same in both arms.

To use another agent, put its command last, for example `python3 bench.py run RMT-716 --arm B --out "$runs/custom" --agent /path/to/my-agent`. The agent reads the prompt from standard input, uses the specified tools in the current directory and exits after submitting. The runner writes process output to `agent.log` and `stderr.log` and scores the actual submission.

For native tasks, start the local business services and provide Computer Use access to Google Chrome. To reproduce the reported interaction method, use native `cua_repl` on an idle desktop with a fresh Chrome Guest window. The example uses the local demo account.

```sh
docker compose up -d --wait
python3 bench.py run ar-22153 --arm B --out "$runs/native"
python3 bench.py batch finance --controls --out "$runs/finance"
```

The native batch runs 40 A/B pairs. Adding `--controls` runs the 20 scheduled D trials and ten C trials after the main pairs, for 110 independent sessions. The simulated ERP batch runs 16 A/B pairs. Batch results go to `summary.json`. Repeating the command with the same output directory skips scored sessions. If a run stops after submission but before the result reaches disk, inspect the trial log and the original submission before resuming. [Case selection, controls and run order](schedule.json)

## Run a case manually

```sh
runs=$(mktemp -d)
python3 bench.py prepare RMT-716 --arm A --out "$runs/manual"
cat "$runs/manual/work/TASK.md"
```

In `$runs/manual/work`, run `./work read invoices-history` to read the handoff records. Pass your two CSV rows as a single argument, for example `./work submit "$(cat /path/to/my-answer.csv)"`. The tool accepts the first submission and returns its SHA-256 digest. From the repository root, run `python3 bench.py score "$runs/manual"`. Manual runs require no model account.

Use `prepare` for a native case as well. Open the private room and ownCloud folder identified in the generated prompt, post one formal submission in the room and run `score`. Each trial gets its own room. Use `--cloud` and `--chat` to specify service endpoints. For a custom demo account, set `BENCH_USER` and `BENCH_PASSWORD` for the evaluator and give the operator the same credentials separately.

## Trial conditions

| Arm | Materials supplied in the 40 native finance cases |
|---|---|
| A | Current case documents and closed transactions |
| B | Arm A materials plus the archived GLM-distilled Skill |
| C | Arm A materials plus the original policy |
| D | Arm A materials plus the archived DeepSeek-distilled Skill |

The original two-invoice batch schedules A and B. Its follow-up adds the archived DeepSeek Skill as arm D on all 16 cases. To run one DeepSeek trial, use `python3 bench.py run RMT-765 --arm D --out "$runs/deepseek"`. To run the three-way comparison from scratch, use `python3 bench.py batch custom --schedule tasks/schedules/remittance-distillers.json --controls --out "$runs/three-way"`. [Matched scores and receipts](../results/distillers.md)

Historical approval tasks keep their original arm definitions, where D includes the policy and a Skill. For T-320, C provides an ordinary handoff. The workspace contains only the materials for its assigned arm. Archived Skills retain the language used in the experiments. Exported attachments represent absolute paths from the original machine as `<trial-workspace>`.

## How scores are calculated

| Receivables criterion | Points |
|---|---:|
| Discount and amount transferred to claims | 35 |
| Write-off and collectible balance | 35 |
| Follow-up owner | 20 |
| Amounts reconcile | 10 |

Score each invoice separately. For a two-invoice remittance, the case score is the average, and a fully correct case requires both rows to earn full marks. Payables cases require the correct decision and every applicable reason. Historical audit packets also require the complete set of evidence references. T-320 reports both business correctness and whether the first answer was correct without consulting the policy.

For native cases, the public runner grades the operator's first formal submission in the assigned Rocket.Chat room. Extra submissions, visible message edits, missing deliveries, process timeouts and abnormal exits score zero. For CLI cases, it grades the first submitted CSV. Each trial writes its result and receipt to `score.json`.

The published native report also gives a strict protocol score. That audit checks independent receipt against database writes, the native UI trace and Guest-window cleanup. The public runner reports the business score. It writes rerun results separately from the published archive. To check the public scorer against 224 published business receipts, run `python3 -m unittest discover -s tests`.

The evaluator stores historical rule-bearing fixtures and answer keys in `evaluation/`. Manual participants receive the workspace produced by `prepare`. For remittance cases the runner renders the prompt from the two invoice records in `mock/remittances/`. To refresh the frozen, browsable prompt copies after authoring a case, run `python3 -m benchmark.remittances --write`. Run the same command without the flag to check them.

For a custom batch, pass `bench.py batch custom --schedule SCHEDULE.json --out DIRECTORY`. Use a JSON array of rows such as `[{"case":"RMT-716","family":"two-invoice-remittance","order":"AB"}]`. Each case ID must be in the task manifest and appear once in the schedule. The runner freezes the inputs and schedule before the first session. Resume with the same schedule and directory. Published follow-up batches retain the full denominator. [Batch histories](../results/batches/README.md)

### Month-end cash application

Start ownCloud and Rocket.Chat, give the signed-in operator native Chrome Computer Use access, and run the following from the repository root on an idle desktop. Six sessions run sequentially, one Guest window per trial. A is the baseline, B receives the archived GLM-5.3 cash Skill and D the archived DeepSeek Flash cash Skill. Every arm receives the current controller instruction.

```sh
python3 bench.py batch custom --schedule tasks/schedules/month-end.json --controls --out "$runs/month-end"
```

Finance grades each invoice in the first unedited message. Correct discount and claim earn 35 points together, correct write-off and collectible balance earn 35 together, correct owner earns 20, and a balanced total earns 10. A missing invoice earns zero. A duplicate or unassigned ID invalidates the posting batch. The task score averages the eight invoice scores. Full completion requires all eight to earn 100.

### Joint receivables and payables close

Each shift has one simulated ERP receipt covering eight counterparties. The desk provides the current records with `./work read rules`, previous postings with `./work read invoices-history` and a write-once submission command. A receives those records. B and D also receive their respective distiller's archived cash application Skill and raw payment approval candidate.

```sh
python3 bench.py batch custom --schedule tasks/schedules/joint-close.json --controls --out "$runs/joint-close"
```

Each of the 16 AR rows uses the cash posting rubric above. Each of the eight AP rows earns 40 points for the exact collectible exposure carried from AR, 20 for the decision and 40 for the complete set of reasons. The mean across the 24 invoice instructions gives the business score. All 24 must be fully correct for a completed shift. A missing or referred item earns zero. A duplicate or unassigned invoice ID invalidates the submission.

### Scanned proof of delivery

Run `python3 bench.py batch custom --schedule tasks/schedules/pod-inspection.json --controls --out "$runs/inspections"`. Codex receives the two PNGs as image inputs. Manual participants and custom agents get the same original-resolution files in the trial workspace and can view both. The simulated desk accepts one eight-row message. It awards 25 points for confirmed damaged units, 20 for the loss amount, 25 for the authorized transfer, 20 for the collectible remainder and 10 for the correct owner. The case score is the mean across all eight invoices.

### Bank lockbox matching

Run `python3 bench.py batch custom --schedule tasks/schedules/lockbox.json --controls --out "$runs/lockbox"`. A receives the bank registers and the ERP's candidate suggestions. B and D also receive the archived invoice reconciliation Skill from the respective distiller. Each first submission receives one point per invoice posted to its verified bank receipt. An invoice used twice earns no credit. The score is the percentage of 36 placements correct. Use `python3 evaluation/verify_lockbox.py` to independently enumerate every locally balanced triple, verify the ERP suggestions and prove the full allocation is unique for each shift. The participant desk uses the same read-and-submit interface as the other simulated ERP tasks. The verifier runs outside the participant session.

### Invoices still open at cutoff

Run `python3 bench.py batch custom --schedule tasks/schedules/cutoff.json --controls --out "$runs/cutoff"`. Use the original cash Skills with the latest signed bank and controller status. The score is the share of eight invoices with an exact, authorized posting by 17:00. A justified wait stays open. The separate handling score gives a correct wait full credit and uses the standard cash rubric for invoices with sufficient evidence. The receipt also records any attempt to post against an unresolved incident.

The larger lockbox comparison uses `python3 bench.py batch custom --schedule tasks/schedules/monthly-lockbox.json --controls --out "$runs/monthly-lockbox"`. It uses the same invoice Skills, 300-second session budget and scoring rule. Each shift contains 36 bank receipts and 108 invoice placements, split equally between fully referenced EDI advice and legacy remittances.
