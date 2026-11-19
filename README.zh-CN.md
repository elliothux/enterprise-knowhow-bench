# Enterprise Know-How Benchmark

[English](README.md) · 简体中文 · [评测报告](results/REPORT.zh-CN.md) · [公开题库](tasks/README.md) · [运行指南](tasks/RUN.md)

现在的 AI Agent Benchmark 大多只测两件事：要么把整理好的规则手册直接塞进提示词测阅读理解（纯测 Context），要么给一句明确指令测点屏幕、调工具和写代码（纯测执行）。

但真实企业的业务交接不是这样的。老员工脑子里的做事规矩很少完整写进文档，新接手的人往往只拿到眼前的待办单据和前几班留下的几条历史记录。**光看零散的历史记录，AI 能不能还原出背后的业务规矩？如果不能，直接从真实员工的日常操作中把企业经验（Know-How）蒸馏出来喂给它，能不能真正把业务跑通？**

Enterprise Know-How Benchmark 就是为了回答这个问题而建的经验还原基准。我们的跨软件办公环境基于 [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) 的自托管企业服务（`ownCloud`、`Rocket.Chat` 及同事 NPC）构建，聚焦财务核销、付款审批、采购对账与月底关账等核心后台工作流。

## 我们测的是什么样的真实业务场景？

这里选的不是理想化的单步问答或干净的现代 API 调用，而是**真实企业日常运转里的跨软件复杂场面**：

* **跨多个软件来回协同**：以财务岗位为例，Agent 需要像真人员工一样，在内部聊天软件（`Rocket.Chat`）里接单或向同事核实信息，去企业网盘（`ownCloud`）翻查多份 PDF 合同、银行水单和上一班交接记录，在本地桌面表格（`LibreOffice Calc`、`Numbers`）里搭公式算账，最后再回到业务队列完成正式交单。
* **繁琐软件操作里夹杂大量业务判断**：任务链路长，且每一步操作都混杂着细碎的业务权衡——已入账贷项扣不扣现金折扣基数、免赔销账卡绝对金额还是卡比例上限、跨法人主体的应收尾款怎么联动应付止付、截账时点哪些单据能落账而哪些必须挂起。错一个判断，整单结果就会偏掉。
* **直面老旧、难用的内部业务系统**：真实企业的后台远没有现代 SaaS 那么规整。题库专门纳入了没有现代 API 和脚本控制台、只能靠固定读写命令过账的**老旧内部 ERP 工作台**，缺失电子发票号的历史遗留银行回单（Legacy Remittances），带手写涂改痕迹的纸质月台签收扫描件，以及容易卡死崩溃的传统桌面电子表格软件。

## 为什么企业 Know-How 决定 AI 能不能落地？

在这些跨软件、重判断、带老系统的复杂工作流里，AI 会不会点按钮、会不会敲命令只是入场券；真正决定敢不敢上生产环境的，是它**懂不懂公司内部的隐性规矩**：

* 客户少付了几块钱，什么情况算正常现金折扣或免赔核销，什么情况必须转催收？
* 供应商换了新的收款银行账户但核验还没走完，这笔款能不能放？
* 月底关账截点到了，哪些单子现在就能入账，哪些必须挂起等银行或财务主管确认？

缺少这层 Know-How，Agent 表面上把软件操作走通了，实际上已经在制造生产事故。例如在应付工单 [AP-1026](results/cases/AP-1026/history.json) 中，不带岗位经验的模型看到单据表面齐全，直接把款项放行给了尚未核验的新银行账户（`RELEASE`）；而带上蒸馏出的岗位经验后，它会准确识别风险并暂扣（`HOLD,BANK_UNVERIFIED`）。真实财务交单没有撤回重来的机会，因此本基准全部按**接收方收到的第一份正式结果**判分，不允许靠多轮报错试错蒙混过关。

## 从真实员工操作蒸馏 Know-How：可行性与准确性

我们固定同一个执行模型（`gpt-6.1-terra`），按统一顺序对比四组实验条件：

* **Arm A（只看历史工单）**：只提供当期业务单据和上一班留下的已结案记录（无经验基线）
* **Arm B（Lynx Cognition · `GLM-5.3` 蒸馏 Skill）**：Arm A 资料 + 由 [Lynx Cognition](https://enterprise.lynxai.work) 调用 `GLM-5.3` 从真实员工桌面操作录制中自动蒸馏的岗位经验
* **Arm C（Lynx Cognition · `DeepSeek Flash` 蒸馏 Skill）**：Arm A 资料 + 同样通过 [Lynx Cognition](https://enterprise.lynxai.work)、改用轻量模型 `DeepSeek Flash` 从同一批员工操作录制中蒸馏的岗位经验
* **Arm D（完整书面制度原文）**：Arm A 资料 + 直接提供出题所依据的完整公司书面制度（上界对照）

| 业务场景 | 执行环境 | 预定规模 | Arm A：只看历史工单 | Arm B / C：+ 员工操作蒸馏 Know-How | 核心变化 |
|---|---|---:|---:|---:|---|
| [应收短付核销](results/finance.md) | 原生 Chrome（`ownCloud` + `Rocket.Chat`） | 24 单 | 12/24 全对（均分 70.8） | **24/24 全对（均分 100）** | 消除核销基数、双上限与银行宽限期误判 |
| [应付放款审批](results/finance.md) | 原生 Chrome（`ownCloud` + `Rocket.Chat`） | 16 单 | 12/16 全对（均分 75.0） | **16/16 全对（均分 100）** | 拦截未核验新账户误放款与越权、过期豁免 |
| [双发票组合核销](results/remittances.md) | 老旧 ERP 工作台（CLI） | 16 单 | 0/16 全对（均分 28.1） | **13/16（Arm B）/ 16/16（Arm C）** | 单票浏览器操作蒸馏的经验跨系统生效，转人工从 19/32 行降为 0 |
| [AR/AP 联合关账](results/batches/joint-close-20261119/README.md) | 老旧 ERP 工作台（CLI） | 48 条指令 | 15/48 全对（均分 50.3） | **48/48 全对（均分 100）** | 算准应收敞口并正确联动法定抵销暂扣 |
| [月结截点异常处理](results/batches/cutoff-20261119/README.md) | 老旧 ERP 工作台（CLI） | 16 张发票 | 入账 2/16（处置分 62.2） | **入账 11/16（处置分 100）** | 结清全部可办单据，5 张外部未决单精准挂起 |

实验结果验证了三个核心判断：

1. **无需先手写完美制度，从真实操作蒸馏的 Know-How 就能追平书面规程**：40 单原生跨软件财务交接的首交全对率从 **24/40（60%）拉满到 40/40（100%）**，单题耗时几乎不变（约 150 秒）。在预定的 10 单完整制度对照题上，蒸馏 Skill（Arm B / C）与直接给书面制度原文（Arm D）一样拿到了 **100 分**。企业不必花几个月先把隐性经验整理成文档，录下熟手操作就能还原规则。
2. **经验可跨新老系统迁移，轻量蒸馏模型同样有效**：从原生浏览器单票操作中提炼出的应收经验，原样放到老旧命令行 ERP 工作台做双发票核销依然有效；无论用 `GLM-5.3`（Arm B）还是轻量的 `DeepSeek Flash`（Arm C）做蒸馏，在 20 单原生同题抽测上均拿满分，双发票核销上 Arm C 更是拿到 **16/16 全满分**（[蒸馏对比](results/distillers.md)）。
3. **能力边界同样清楚**：我们也测试了光靠业务经验解决不了的问题。面对混有 18 笔缺发票号历史遗留回单、共 108 笔发票的月结银行锁箱（需要在 240 多种局部组合中找出唯一全局解，且老旧 ERP 工作台无脚本求解器），各组一致停在 **50%–53%**（[详情](results/batches/monthly-lockbox-20261119/README.md)）；强制在原生 `LibreOffice Calc` 里编辑复杂公式表时，会受软件崩溃与丢公式影响（[详情](results/batches/chargeback-native-20261119/README.md)），个别原生月结班次也出现过单笔算术偏差（`close-118`）。Know-How 负责让 AI **懂规矩**，代码工具与稳定执行环境负责**算得过来、填得进去**。完整数据与边界分析见[评测报告](results/REPORT.zh-CN.md)。

## 快速跑一单试试

需要 Python 3.10+。下面的双发票核销示例无需启动 Docker，直接对比同一个模型在“只看历史工单（`--arm A`）”和“加上蒸馏经验（`--arm B` 或 `--arm C`）”下的首交差异。默认调用本机已登录的 Codex CLI，也可通过 `--model` 切换模型或用 `--agent` 接入你自己的 Agent（[公开题库](tasks/README.md) · [运行与评分指南](tasks/RUN.md)）：

```sh
git clone https://github.com/elliothux/lynx-benchmark.git
cd lynx-benchmark
python3 bench.py list
runs=$(mktemp -d)
python3 bench.py run RMT-716 --arm A --out "$runs/A"
python3 bench.py run RMT-716 --arm B --out "$runs/B"
python3 bench.py compare "$runs/A" "$runs/B"
```

如果要跑原生跨软件工单（Chrome 读取 `ownCloud` 凭据并向 `Rocket.Chat` 交单，支持 `--arm A/B/C/D`），先启动下方的本地企业服务，再执行 `python3 bench.py run ar-22153 --arm B --out "$runs/chrome-B"`。另外 11 套训练与扩展题（到岸成本、发票对账、发版清单、Numbers 补货表及供应商询价 NPC）见 [cases/README.md](cases/README.md)。

## 启动本地业务环境

需要 Docker Compose v2.24+、Python 3 以及支持运行 `linux/amd64` 镜像的 Docker 引擎。在仓库根目录执行：

```sh
docker compose up -d --wait
python3 mock/seed.py --case ar-22153
```

启动后可在 [ownCloud](http://localhost:8092) 的 `Documents/Enterprise review ar-22153` 查看当期凭据与上一班交接单，在 [Rocket.Chat](http://localhost:13000) 的私有房间 `finance-review-ar-22153` 查看初始请求（默认演示账号与密码均为 `theagentcompany`，省略 `--case` 可一次导入全部 40 张原生财务工单）。如需启动供应商询价任务的同事 NPC，将 `.env.example` 复制为 `.env` 填入模型配置后运行 `docker compose --profile vendor-quote up -d --wait`。

## 报告与原始数据

所有结果均按预先固定的整批工单统计（包含持平、未完结账本、软件崩溃与回退样本），运行 `python3 -m unittest discover -s tests` 可在本地复核评分器与全部已发布回执：

* [完整评测报告](results/REPORT.zh-CN.md)
* [原生跨软件财务交接报告（40 单）](results/finance.md) · [逐单得分 CSV](results/finance-scores.csv)
* [双发票汇款核销报告（16 单）](results/remittances.md) · [蒸馏模型对比](results/distillers.md)
* [月结关账与工作簿边界报告](results/close-workflows.md) · [提分工单回执归档](results/README.md) · [追加批次](results/batches/README.md)

## 致谢与引用

本基准的容器化企业协作环境（`ownCloud`、`Rocket.Chat`）、基础模拟数据与供应商询价任务框架基于 [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) 构建；实验中评测的岗位经验 Skill 由 [Lynx Cognition](https://enterprise.lynxai.work) 从操作示范中蒸馏生成。所有账本与交易单据均为合成数据。

如在研究或评测中使用本项目，请同时引用 TheAgentCompany：

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
