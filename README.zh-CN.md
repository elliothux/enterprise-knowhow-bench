# Lynx Benchmark

[English](README.md) · 简体中文

在 40 张预先冻结的合成财务工单上，同一操作模型用原生 Chrome 从 ownCloud 读取业务凭据，在 Rocket.Chat 向财务交付核销或审批指令。加入 Lynx Cognition 从先前示范中蒸馏的 GLM Skill 后，首次交付全对的工单从 **24/40 提高到 40/40**。16 张提分，24 张持平。

在另一组 4 张原生短付确认工单上，无 Skill、GLM 和 DeepSeek 均分分别为 **43.75、86.25、100**。在 32 次付款审批中，使用原始蒸馏稿时，首次决策全对率从 **78.13%** 提高到 **93.75%（DeepSeek）** 和 **100%（GLM）**。在需要用 Numbers 制表并跨软件交付的任务上，无 Skill 和有 Skill 都只成功了 **1/2 次**。[同题蒸馏模型对照、未完成任务和原始回执](results/distillers.md)

| 实验 | 工单数 | 无 Skill 均分 | GLM Skill 均分 | 两组首交全对 |
|---|---:|---:|---:|---|
| 原生跨软件应收核销 | 24 | 70.83 | 100.00 | 12/24 → 24/24 |
| 原生跨软件应付审批 | 16 | 75.00 | 100.00 | 12/16 → 16/16 |
| 双发票核销，模拟 ERP CLI | 16 | 28.13 | 94.84 | 0/16 → 13/16 |

应收核销同时考查折扣与理赔、销账与余额、跟进责任和金额对平。应付审批要求决定和全部适用原因均正确。一张应付工单的首次提交从直接放行变为暂扣，原因是新收款账户未完成核验。[该工单的两份回执与操作记录](results/cases/AP-1026/history.json)

两款蒸馏模型在预定的 20 张同题抽测上业务得分均为 100。其中 6 张相对无 Skill 确有提升，GLM 与 DeepSeek 在这 6 张上也都得到相同分数。另有 10 张直接给制度全文的对照得到满分。样本针对两个财务岗位的规则边界。业务得分以接收方首条交付为准，报告另列原生浏览器协议未通过时计零的成绩。[原生实验报告](results/finance.md) · [模拟 ERP 报告](results/remittances.md)

## 自己跑一道题

[公开题库](tasks/README.md)包含完整题面、输入资料和各组附件。使用 Python 3.10+，普通克隆即可运行。下面的双发票题无需 Docker；示例使用本机已登录的 Codex CLI。可用 `--model` 指定可访问的模型，或接入[自己的 Agent](tasks/RUN.md)。

```sh
git clone https://github.com/elliothux/lynx-benchmark.git
cd lynx-benchmark
python3 bench.py list
runs=$(mktemp -d)
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
```

跑原生跨软件题时先启动下方 Compose，然后执行 `python3 bench.py run ar-22153 --arm A --out "$runs/chrome-A"`。执行器会为本次运行新建工单、装入两份 PDF，并读取财务队列的首条交付评分。也可以人工操作、跑整批，或使用原始训练与扩展题。[运行与评分说明](tasks/RUN.md) · [其他 11 份题面](cases/README.md)

## 运行历史

[有效工单目录](results/README.md)收录 46 张至少一次正式业务首交提分的独立工单，含本轮 31 张和历史 15 张。其中 20 张走原生 Chrome，26 张走模拟 ERP CLI。每张记录保留正式对照的条件、得分、首次交付、操作顺序及原始日志哈希。目录按提分筛选；报告使用预定整批作为分母。[原生 40 张全部得分](results/finance-scores.csv) · [双发票 16 张全部得分](results/remittance-scores.json) · [实测环境](results/environment.json)

追加试次按冻结批次单独统计。11 月 19 日定向复跑 RMT-716，无 Skill 得 0 分，GLM Skill 得 100 分。[追加批次与回执](results/batches/README.md)

## 启动本地业务环境

需要 Docker Compose v2.24 以上、Python 3 和可运行 `linux/amd64` 镜像的 Docker 引擎。从普通克隆的项目根目录运行以下命令。首次启动会下载固定摘要的上游镜像并导入 Rocket.Chat 初始数据。

```sh
docker compose up -d --wait
python3 mock/seed.py --case ar-22153
```

打开 [ownCloud](http://localhost:8092)，在 Documents 下进入 `Enterprise review ar-22153` 查看当前凭据与上一班的交付。打开 [Rocket.Chat](http://localhost:13000) 的私有房间 `finance-review-ar-22153` 查看初始工单。两个系统的上游演示账户及密码均为 `theagentcompany`。端口只发布到回环地址。

省略 `--case` 会装入全部 40 张原生财务工单。重复执行会核对原文件并复用初始消息。初始请求由装载账户发出；正式实验另有独立财务接收账号核对操作员的首条提交。双发票 CLI 数据可直接在 [mock/remittances](mock/remittances) 查阅。发布成绩采自原生 macOS VM；Compose 提供相应的业务服务与样本，公开的 bench.py 负责出题、运行和业务评分。

可选供应商询价 NPC 使用 Redis 和模型 API。将 `.env.example` 复制为 `.env` 并填写 NPC 配置后，再执行 `docker compose --profile vendor-quote up -d --wait`。使用 `docker compose stop` 可保留当前业务数据并停止服务。

## 维护者

有私库读取权限的维护者可运行 `git submodule update --init runner` 获取锁定版本的执行器。题库、参评附件、公开执行器和业务评分均位于主仓库。已发布的题面和评分数据只在公库维护。私有执行器直接读取当前公库工作树，原始试次证据保存在私库的 `archives/`。

环境镜像和基础模拟数据来自 [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany)。企业工单使用合成交易，提交终点为测试财务队列。

在仓库根目录运行 `shasum -a 256 -c SHA256SUMS` 可校验题面、参评附件、题库数据和发布结果。
