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

The two-invoice batch uses arms A and B. Historical approval tasks keep their original arm definitions, where D includes the policy and a Skill. For T-320, C provides an ordinary handoff. The workspace contains only the materials for its assigned arm. Archived Skills retain the language used in the experiments. Exported attachments represent absolute paths from the original machine as `<trial-workspace>`.

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
