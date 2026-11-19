# 运行自己的 Benchmark

Python 3.10+ 即可列题、运行模拟 ERP、读取回执和评分。默认模型适配器使用已登录的 Codex CLI。每组使用独立的新目录与模型会话。只将该次准备好的 `work/TASK.md` 和指定的业务工具交给参评者。答案、公开历史和下一组附件保留在考官侧。

## 单题和整批

```sh
runs=$(mktemp -d)
python3 bench.py list
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
python3 bench.py batch remittances --out "$runs/packets"
```

默认适配器把题面通过 stdin 交给 Codex，以参评工作目录执行，沿用已登录用户配置和插件，使用完整访问模式。请在自己的测试环境中运行。`--codex /path/to/codex` 选择 CLI，`--model MODEL` 选择操作模型；默认与报告一致，为 gpt-6.1-terra、high 推理档。两组保持同一操作模型。使用其他 Agent 时将命令放在末尾，例如 `python3 bench.py run RMT-716 --arm B --out "$runs/custom" --agent /path/to/my-agent`。适配器从 stdin 读题，在当前目录使用题面指定的工具，完成真实提交后退出。进程输出保存在 agent.log 和 stderr.log，评分取实际提交。

原生题需先在本机启动业务服务，并准备可操作 Google Chrome 的 Computer Use 工具；复用报告操作方式时使用原生 cua_repl、空闲桌面和新 Guest 窗口。示例使用默认的本地演示账号。

```sh
docker compose up -d --wait
python3 bench.py run ar-22153 --arm B --out "$runs/native"
python3 bench.py batch finance --controls --out "$runs/finance"
```

原生批次包含 40 对 A/B。加 `--controls` 会在主配对之后执行预定的 20 次 D 和 10 次 C，共 110 次独立会话。模拟 ERP 批次为 16 对 A/B。机器可读的[抽样及顺序](schedule.json)随题发布。整批结果保存在 summary.json；使用相同命令与目录可以跳过已评分会话。中断在提交和落盘之间时，先检查该目录的执行记录和原始交付。

## 人工操作

```sh
runs=$(mktemp -d)
python3 bench.py prepare RMT-716 --arm A --out "$runs/manual"
cat "$runs/manual/work/TASK.md"
```

在 `$runs/manual/work` 中使用 `./work read invoices-history` 查阅交接记录。把自己的两行 CSV 作为一个参数交给 `./work submit`，例如 `./work submit "$(cat /path/to/my-answer.csv)"`。工具仅接收第一份提交，返回其 SHA-256。完成后从仓库根目录运行 `python3 bench.py score "$runs/manual"`。这条人工路径无需模型账号。

原生题同样使用 `prepare`。打开生成题面指向的新私有房间和 ownCloud 文件夹，按题面在房间中正式交付一次，再执行 `score`。每次准备都会生成单独的房间，每组题面只指向自己的房间。服务端点可由 `--cloud`、`--chat` 指定；使用自定义演示账号时，考官设置 BENCH_USER、BENCH_PASSWORD，并单独给操作者提供相同账号。

## 条件与计分

- 40 张原生工单的 A 组使用当期凭据和已结交易；B 额外得到归档的 GLM Skill，C 得到原始制度，D 得到 DeepSeek Skill。历史审批题沿用各自的分组，D 为制度加 Skill；T-320 的 C 为普通交接。双发票批次提供 A、B。参评工作目录仅装载当前条件。导出附件中的旧机器绝对工作路径用 `<trial-workspace>` 表示。
- 应收单按折扣与理赔（35）、销账与余额（35）、责任方（20）和金额对平（10）评分。双发票分别计分后取均值，两行都全对才计整单全对。应付审批要求决定和全部原因正确。历史审计包还要求完整的凭据引用集合，T-320 同时报告业务正确分和无需查制度的首问分。
- 原生业务分取 Rocket.Chat 中该操作员在指定房间的正式首交。额外提交、可见的消息编辑、缺失交付或执行进程超时／异常退出会使本次公开运行计零。CLI 从首份 CSV 计分。每次结果和回执位于 score.json。历史报告的严格协议分还包括独立收件与数据库写入比对、原生 UI 轨迹和 Guest 清理审计；公开入口报告业务分，不签发该严格协议结论。
- 已发布的结果与复跑分开保存。运行 `python3 -m unittest discover -s tests` 可用公开评分器核对 224 份已发布业务回执。
