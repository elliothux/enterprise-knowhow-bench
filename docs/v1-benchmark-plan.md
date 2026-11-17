# Lynx Benchmark V1：基于 TheAgentCompany 的同任务经验复用对照

> 状态：开发与验收方案，未实现、未部署、未跑分。面向 AI/Codex 开发执行，Elliot/项目负责人验收。  
> 目标：两天内跑通一个真实跨软件任务，展示「执行 → 经验沉淀 → 固定 Skill → 重置后复用」的可审计闭环。  
> 本文的命令、配置、目录和接口均为**拟实现契约**，不是现有可运行功能。上游行为来自静态源码核查，当前镜像、依赖与环境仍须实测。

## 1. 要回答什么，不回答什么

唯一主问题：同一个 Agent，在相同任务、相同初始状态和预算下，加入由真实历史执行沉淀的固定 Skill，能否改善任务完成质量、成功次数和执行耗时？

V1 接受**同一道题重跑**。它是同任务经验复用试点，不是未见任务泛化评测，也不是 TheAgentCompany 官方排行榜成绩。第一次经历就是允许获得的训练经验，不能一面允许同题学习，一面声称无泄漏泛化。

- A：通用 Agent + 任务说明 + 相同工具，无历史记忆和 Skill。
- E：真实经验采集运行，可复用第一次 A；如人工纠错，单列纠错过程和成本。
- S：Lynx 将 E 的证据形成 Case/Procedure，经确认编译成固定 Skill。
- B：同一个通用 Agent + 同一任务 + 同一套工具 + 固定 Skill；环境重置，新会话。
- 推荐冻结 S 后再跑 A/B 各 3 次，顺序预先固定/随机化并落盘。时间不足最低各 1 次，只展示个案，不声称统计显著。
- 不保证 B 更快或更成功。失败也进入报告。严禁反复挑选最漂亮的一次。

V1 不做：全量 175 题、新建 ERP、Linux 版 Lynx 采集器、自研通用 Agent、30 道变体、模型训练、自动迭代 Skill、多组复杂消融。普通摘要/原始轨迹对照很有价值，但放入 V2；V1 不能据 A/B 差异声称“蒸馏优于普通记忆”。

## 2. 复用边界与架构

### 2.1 直接复用 TheAgentCompany

| 复用项 | 用法 | 不应误称 |
|---|---|---|
| Docker 企业测试服务及种子数据 | 复用 ownCloud、RocketChat；上游标准部署可能仍启动其完整套件 | 自建真实企业 ERP |
| task.md、PDF、NPC scenarios | 固定主任务和数据版本 | 动态真实客户任务 |
| base init/reset/healthcheck | 封装并验证初始化和持久数据恢复 | 换容器就完成重置 |
| 原始 evaluator/checkpoints | 在隔离评分区运行并保留原始结果 | 完整衡量业务推理、Skill 质量 |
| 官方外部 Agent 接入方式 | 保留独立 Agent，适配任务工作区和服务地址 | 必须重写 OpenHands |

GitLab、Plane 是上游环境的一部分，但主任务没有依赖它们。优先采用已经验证可用的官方部署路径，勿为了“最小化服务”临时重写整套初始化。只在不影响上游脚本的前提下裁剪资源。

### 2.2 自己开发的薄层

1. CLI 编排：doctor、初始化、reset、单轮运行、采集、Skill 固定、评分、报告。
2. Agent adapter：将同一 task.md 和允许的工具提供给通用 Agent，A/B 只改变 Skill 输入。
3. Lynx adapter：选择真实已验证的采集入口，绑定 Trace/Case/Procedure/Skill 版本。
4. 证据与 manifest：记录版本、随机顺序、模型、预算、输入摘要、原始输出、成本和人工干预。
5. 报告：原始分数 + 业务结果 + 时间 + 失败原因 + Skill 来源，不造分。

推荐拓扑：

```text
Linux/Docker 测试服务：ownCloud + RocketChat + NPC + reset 服务
                         ↑ 浏览器访问
macOS 执行主机：真实浏览器 + 通用 Agent + lynx-edge + 可观测下载目录
                         ↓ 明确挂载/传输与哈希校验
任务容器 /workspace：下载 PDF、输出 CSV、link.txt
                         ↓ 只读结果，Agent 不可访问
隔离 runner / evaluator → trial artifacts → comparison report
```

如果没有可用 macOS/真实采集权限，可以先验证 Agent 与 TAC，但必须将采集方式标为“轨迹导入/工具日志”，不能宣称已经验证 OS 级认知采集。远程 VNC 的像素不等于本机原生 AX 语义；容器内 headless 浏览器也不会自动被 Mac 采集器看到。

## 3. 唯一主任务：服务器供应商报价筛选

上游 task ID：`admin-get-best-vendor-quote`。

### 3.1 完整业务链

1. 在 RocketChat 向 Emma Lewis 查询报价文档位置。
2. 向 Sarah 查询采购要求。
3. 从 ownCloud 取得五份供应商 PDF。
4. 在本地读文档，按所有要求筛选符合条件的报价。
5. 生成 `valid-quotes.csv`，字段为 `name,price`。
6. 上传 ownCloud 的 `Documents/Administrative Specialist`。
7. 创建该文件的测试环境分享链接，写入任务工作区 `/workspace/link.txt`。

涉及 RocketChat、ownCloud、PDF/文件处理，具备明确的跨软件依赖。**不包含 ERP 采购单、审批、库存、合同或支付。**

给 Agent 的任务内容采用上游 task.md，不另塞金标准答案。NPC 的需求阈值、供应商报价和期望结果放在受限环境与评分区，不写入 Agent 的系统提示、演示脚本或预置 Skill。

### 3.2 数据契约

固定上游 commit 与镜像 digest，保留五份 PDF 的路径、字节数、哈希以及原始 NPC scenarios 的哈希。五份下载文件：

- `cloudtech_industries_quote.pdf`
- `datacore_enterprise_quote.pdf`
- `netsys_corporation_quote.pdf`
- `servermaster_systems_quote.pdf`
- `techpro_solutions_quote.pdf`

Agent 实际下载路径必须进入评分所见的 `/workspace`。浏览器主机与任务容器分离时，开发者需实现明确的同步/挂载方案，并验证上传选择器与评分器读的是同一份 CSV。不得悄悄用评分器答案替代文件。

NPC 不是可有可无的装饰：上游任务通过 scenarios 启动 NPC，Agent 的两个询问本身是任务步骤。冻结 NPC 的模型、prompt/scenarios、温度和预算，记录对话与耗时；若 API 不可用或 NPC 无回复，归类环境错误，不归因于 Skill。

### 3.3 Skill 应沉淀什么

建议内容：需求澄清顺序、去哪里找资料的方法、报价字段提取、全条件过滤、输出校验、上传分享、缺失信息与错误恢复。保留来源 Case/Procedure 版本和未决问题。

禁止把最终正确 CSV、固定供应商名单/价格、评分器源码或“直接输出答案”写进 Skill。同题不可避免记住路径和流程，但应明确这属于同任务经验复用；不能把答案缓存包装成抽象技能。

### 3.4 唯一备用任务

若报价任务在首日门槛前因 NPC/兼容性阻塞，采用 `finance-invoice-matching`：ownCloud 的 payments.xlsx 与 invoices_pdfs，识别拆分/合并付款及异常，输出 flagged_payments.xlsx（含 Payment_ID、Issue、TOTAL）。

备用任务跨软件展示较弱，只有 ownCloud 与本地文件处理。切换必须更新任务说明、评分适配、报告标题，并明确不是原报价任务成功。不要同时把两题都扩成大项目。

## 4. lynx-cognition 接入约束

已静态核查的 cognition 快照：`a4bf530811b629574cf720ffaf11b7b01f38c325`；实施前确认目标分支差异。

已存在的能力：macOS 桌面/语义与文件观察、Claude Code hooks/部分 trace 输入、Case → Procedure → 人工确认 → Markdown Skill 编译、带版本/hash 的持久化 Skill、MCP `search_skills`/`read_skill`。这些不等于任意 Agent 的自动轨迹适配已完成。

特别注意：

- 现有 payment skill execution 路径要求先 read_skill，并带对账领域提示，不能简单关闭 Skill 就当公平基线。
- A/B 必须共用一个通用执行器。可复用已有成熟执行器，但先验证它能访问真实浏览器、下载目录和服务。
- 首日选择一个已接通模型和工具的执行器并锁定，不以“兼容所有模型”为 V1 验收条件。
- `apps/web/e2e/payment-skill-fixture.ts` 与 `apps/server/scripts/skill-execution-fixture.ts` 属于脚本化 fixture。它们可做界面/协议测试，不能产生真实 benchmark 分数。
- Full lynx-edge 当前按 macOS 路径设计；Windows helper 或日志导入不能被说成完整跨平台采集。
- 如果使用非 Claude Code Agent，必须实测 trace 接入。没有通用 adapter 时，不要将 OpenHands/Playwright 日志直接称为原生 OS 采集。

B 首选固定 Skill 直接注入，减少检索随机性，使比较聚焦“有无经验”。若产品演示需要 MCP，则锁定 Skill ID/version/hash，用 read_skill 读取同一字节；明确 B 计时包含检索读取时间，记录是否实际读取。V1 不同时比较注入与检索两种模式。

编译和人工确认只做一次，之后冻结。后续运行发现问题，不能一边改 Skill 一边把结果混为同一实验；重新版本化并重新开始该批次。

## 5. 执行协议与公平性

### 5.1 经验阶段

- 先做不计分的开发者环境 walkthrough，只验证系统、NPC、文件流与评分；其轨迹不得冒充 Agent 学习。
- 正式 E 使用真实模型和真实操作。建议第一次 A 同时作为 E，但报告标明两者关系。
- E 失败可人工纠错继续收集，记录干预时间、操作者步骤、模型调用；该次不得记为“自主成功”。
- cognition 产出 Case/Procedure，人工确认再编译。记录所有修订来源，不访问评分金标准来修正 Skill。
- 无可靠成功证据或关键步骤仍未决时，不把未验证 Skill 宣称专家技能；可以展示未完成状态。

### 5.2 每轮 A/B 的固定条件

相同：task.md 字节、模型精确 ID/版本、温度/seed（供应商支持时）、工具、系统提示公共部分、允许的终端/API/UI 模式、权限、步数/token/time budget、主机资源、网络、NPC 配置、初始登录状态和工作区。

唯一差异：B 的固定 Skill。A 禁止访问旧会话、Case、Skill 存储、输出、浏览器历史及共享缓存。Agent 不能访问当前仓库的开发方案、scenarios、checkpoints、evaluator、管理 API 或结果目录。上游文件公开并不等于在试验中允许读答案。

若任务执行允许 shell/PDF 库，A/B 都允许且名称写入 manifest；不得 A 只能慢点 GUI、B 却使用数据库/API。若演示声称纯 UI，就两边都锁 UI。不能未经检查把所有工具开给 Agent。

### 5.3 reset 必须覆盖的状态

1. 获取全局试验锁，阻止另一轮使用同一服务。
2. 调用上游按 dependencies 重置 ownCloud/RocketChat；校验健康及种子文件。
3. 清理该轮工作区和下载/上传产物，创建新的 run ID。
4. 重置浏览器 profile 到同一干净模板；登录策略两边一致。
5. 新建 Agent 会话，禁用外部持久记忆。
6. 重启/确认 NPC 状态及模型配置，验证不会继承上轮对话。
7. 验证目标输出不存在、历史聊天不存在、五份种子文档存在且 hash 相同。
8. 全部通过才放行计时。失败保留 reset 日志并停止，禁止“带病”继续对比。

上游 reset 服务在 `:2999/api/reset-<service>`；只绑定隔离环境，不暴露公网、不连接生产数据。上游初始化健康等待可达约 15 分钟，不能承诺重置几秒完成。只创建新任务容器不会恢复持久服务。共享服务上的 A/B 必须串行，除非独立完整副本。

### 5.4 状态机与失败

`preflight → reset → ready → running → evaluating → archived`。

失败类型至少包括：`task_failed`、`timeout`、`infra_error`、`agent_error`、`human_assisted`、`aborted`。保存原始原因。基础设施错误不算模型成功率的有效样本，但必须报告数量与重跑，禁止静默删除。timeout/错误输出必须保留在任务结果分母。任何运行中的人工操作使自主成功为 false。

## 6. 评分、计时与结论口径

### 6.1 原始评分与业务评分分开

上游 evaluator 有 6 个一分检查点：与 Emma 私聊存在、与 Sarah 私聊存在、五份 PDF 文件存在、CSV 上传存在、link.txt 有链接、下载 CSV 内容符合固定答案。它对 CSV 的列、行和顺序有精确要求。

局限：对话存在不等于问对、文件存在不等于正确内容，固定行序可能拒绝业务语义等价结果。不衡量来源解释和 Skill 质量。**原始分保留为 official_raw_score，绝不悄悄改 evaluator 后还沿用“官方分”。**

独立业务 verifier（新增）至少检查：
- 可从分享链接读取正确输出，而不是仅存在字符串。
- CSV 的供应商和报价数值符合规则，无额外/遗漏；按受限金标准比较，不将 gold 暴露给 Agent。
- 输出路径与名称正确；没有重复/意外外部写入。
- 自主完成且没有越权获取 evaluator 或替写输出。

业务语义检查可忽略无关行序，报告中解释与官方分的差异。6/6 与业务成功分别显示，不能只挑较好的一列。预先使用故意错误的 CSV、缺链接、缺 PDF 验证 evaluator 会失败，这只是评分单元测试，不是真实 Agent 试验。

### 6.2 时间和成本定义

- `agent_wall_ms`：环境 ready 后提交任务开始，到 Agent 声明完成/预算终止；包含推理、工具、网络等待、B 的 Skill 读取，不含 setup/reset/evaluator。
- `setup_ms/reset_ms/evaluation_ms`：分别记录；另报 end-to-end 周转时间。
- `experience_ms/compile_ms/human_review_ms`：一次性学习成本单列，不消失。
- tool calls、模型请求、输入/输出 tokens、失败重试、已知价格口径下的模型成本；拿不到精确数据写 null/unknown，不填 0。
- NPC 和 distillation 模型的 token/成本单列，不与被测 Agent 混算。

同任务成功率只写“成功次数/有效尝试次数”。3 次重复不是 3 个独立任务。速度提升仅在可比的两侧成功结果上计算：

`speedup = median(A_success_wall) / median(B_success_wall)`

同时展示所有 trial（含失败、超时）的时间和结果，避免幸存者偏差；一侧无成功则速度提升为 N/A。样本极少只作描述，不输出显著性结论。

如讨论摊销，只使用实测：
`break_even_replays = ceil(learning_and_compile_cost / per_replay_saving)`，
单位必须一致；节省非正或未知则 N/A。V1 演示不把复用快直接解释成总成本已下降。

## 7. 环境搭建与一键体验设计

### 7.1 第一次配置（无法省略）

- Docker/Compose 和符合镜像架构的主机；官方要求 30GB+ 空闲磁盘。t3.2xlarge 是参考机器，不是通用最低配置。
- 若 Mac 承载 Docker，验证 host networking、域名解析和 Apple Silicon/MongoDB 兼容；推荐先用现有可用 Linux 服务主机。
- 官方容器 init 改容器 /etc/hosts，不会配置真实浏览器所在 Mac。doctor 必须检查浏览器主机到服务的解析、端口、HTTP/HTTPS 与登录。
- macOS 安装并配置 lynx-edge，按系统流程授予需要的采集权限；验证真实页面和文件事件，不能只看进程启动。
- 模型 API Key 通过环境变量/本地 secret 管理，不入 Git、不进录屏。被测 Agent、NPC、编译器配置独立。
- 只用上游合成公司数据和测试账号。分享链接仅在隔离测试服务内有效；不要连接生产企业或真实客户资料。

不要照抄 `chmod 666 /var/run/docker.sock`、未审查的 curl|sh、清空所有 Docker 容器/volume、全局关闭浏览器安全等操作。限制权限和清理对象到本实验项目。

### 7.2 拟实现配置

```yaml
# config.example.yaml：设计示例，不是当前可运行配置。
experiment:
  name: tac-vendor-quote-v1
  task: admin-get-best-vendor-quote
  tac_commit: REQUIRED_PIN
  cognition_commit: REQUIRED_PIN
  repeats_per_arm: 3
  order_seed: 17
  execution_mode: browser_and_local_files
  max_wall_seconds: 1200   # 首次试跑后两边一起冻结，非上游默认
  max_steps: 150           # 同上
agent:
  adapter: REQUIRED_VALIDATED_ADAPTER
  model: REQUIRED_EXACT_MODEL_ID
  api_key_env: AGENT_API_KEY
npc:
  model: REQUIRED_EXACT_MODEL_ID
  api_key_env: NPC_API_KEY
compiler:
  model: REQUIRED_EXACT_MODEL_ID
  api_key_env: COMPILER_API_KEY
capture:
  mode: macos_native       # 不可用则显式标 trajectory_import
  host_workspace: REQUIRED_MACOS_ABSOLUTE_PATH
  container_workspace: /workspace
skill:
  delivery: fixed_injection
  artifact_id: REQUIRED_AFTER_APPROVAL
  version: REQUIRED_AFTER_APPROVAL
  sha256: REQUIRED_AFTER_APPROVAL
```

用户所说“APK”暂按 API Key 理解；这里不需要 Android APK。运行时模型名/适配器必须选已验证组合，未填占位符一律 fail fast。

### 7.3 拟实现 CLI 契约

```bash
lynx-bench doctor --config config.local.yaml
lynx-bench setup --config config.local.yaml
lynx-bench experience --config config.local.yaml
lynx-bench compile --experience <run-id>  # 等待人工确认，不自动越过
lynx-bench run --config config.local.yaml --skill <fixed-artifact>
lynx-bench report --experiment <id>
```

其中 `run` 一次编排 reset、A/B、新会话、评分、归档和汇总。初次安装、模型密钥、系统权限和 Skill 人工确认不应被“一键”宣传隐藏。分为：
1. 首次建立经验：自动执行到确认点，确认后继续；
2. 已确认 Skill 的复验：一条命令跑全部 A/B 并生成结果。

每个阶段可恢复，不重复已完成的付费运行；恢复前验证配置和 Skill hash 没变。命令退出码需要区分基础设施故障与有效试验中的任务失败；报告不能因 CLI exit 0 就标注任务成功。

## 8. 开发产物和接口

建议目录（未来实现，当前只交付方案）：

```text
configs/              # 无密钥示例
src/cli/              # doctor/setup/experience/compile/run/report
src/adapters/tac/     # upstream pin、reset、health、workspace、evaluator
src/adapters/agent/   # 单一通用执行器
src/adapters/lynx/    # capture、case、procedure、skill 固定读取
src/report/          # JSON + Markdown/HTML
tests/               # state machine、错误结果、fixture 隔离
artifacts/<exp-id>/   # gitignored；脱敏导出另存
```

最小接口：
- `environment.reset(run_id) -> readiness + seed_hashes`
- `agent.run(task, tool_policy, optional_skill, budget) -> trace + outputs + usage`
- `capture.start/stop(run_id) -> evidence_refs + modality`
- `cognition.compile(evidence_refs) -> approval_required -> artifact_ref/hash`
- `evaluate(outputs, protected_gold) -> raw_score + business_checks`
- `report(trials, learning_cost) -> human_report + machine_result`

这些是本项目 adapter 接口，不宣称是 Lynx 现有 API。开发先探查真实接口再映射，不凭文档伪造端点。

每轮 artifacts 至少包含：
`manifest.json`（全部版本/配置hash/时间/模式）、`task.md`、`agent-trace.jsonl`、模型用量、NPC 对话、采集引用、输入/输出hash、`evaluation.json`、`result.json`、错误/重置日志及可选录屏。A 不可读取此目录。

`result.json` 最少字段：experiment_id、run_id、arm、task_id、status、autonomous_success、official_raw_score、official_max_score、business_success、agent_wall_ms、reset_ms、evaluation_ms、token_usage、cost_status、human_interventions、skill_hash（A 为 null）、capture_mode、artifact_refs。字段校验和 schema version 必需。

报告固定显示：全部试次表、样本量、成功数、官方分/业务分、可比时长、失败分类、一次性学习成本、Skill hash/来源、已知限制。录屏可作备份，但明确标“预录实测”，不得混作现场实时运行。

## 9. 两天实施顺序与停损门槛

时间为工作预算，不承诺镜像下载或健康检查一定按时结束。

### Day 1：先证明环境与真实闭环

| 顺序 | 工作 | 放行条件 |
|---|---|---|
| 0–2h | 固定版本、检查主机/API/磁盘/镜像与任务 | 两服务与 NPC 可用；不启动新 ERP 项目 |
| 2–4h | 手工 walkthrough、工作区映射、官方评分、完整 reset | 重置后无输出/聊天残留，数据 hash 一致 |
| 4–6h | 接一个真实通用 Agent，A/E 试跑；验证 OS 采集 | 真实模型调用与工具证据可追溯，非 fixture |
| 6–8h | Case/Procedure/确认/Skill；B smoke test | 固定 Skill 可读取，B 真正执行任务并能评分 |

第一天第 4 小时仍卡在 NPC/服务历史依赖：停止扩展，判断可定位修复还是切备用任务；报告降级边界。不通过采集门槛就不能宣传 OS 级采集。不通过评分/重置门槛则先交闭环工程 demo，不发布“性能提升”数字。

### Day 2：复验与展示

- 完成薄 CLI、manifest 和错误处理，不做炫技 dashboard。
- 冻结配置和 Skill，至少 1+1；优先 3+3，同任务串行。
- 验证失败也归档、超时不被跳过、复验期间无人工替写。
- 输出简洁对照报告与一段完整实测录屏；必要时现场只演示读取固定 Skill 后执行。
- Elliot/验收方按清单检查，开发执行方负责复现和解释缺项。

演示顺序：任务业务价值 → 无经验真实轨迹 → 从证据到 Skill → 重置后的有经验执行 → 实测对照与限制。只陈述已经发生的结果，例如“本次同题复验 B 成功/耗时为…”，不说“企业任务普遍提升 X%”。

## 10. 验收清单

### 文档与配置
- [ ] 上游/cognition/执行器 commit、镜像 digest、模型 ID 全部锁定。
- [ ] secrets 不在仓库或录屏；占位配置 fail fast。
- [ ] 执行模式、权限、预算和计时边界清楚，A/B 除 Skill 外一致。

### 环境与任务
- [ ] RocketChat 两位 NPC 真正回复，ownCloud 五份真实测试 PDF 可下载。
- [ ] 浏览器、主机文件、容器 /workspace 三者链路实测一致。
- [ ] 两次 reset 后初态一致；无 CSV、link、聊天及 Agent 记忆残留。
- [ ] 上游 evaluator 能正确区分正确/故意错误产物。
- [ ] 管理 API、金标准、scenarios 与评分实现对被测 Agent 隔离。

### Lynx 与真实执行
- [ ] A 使用真实模型而非 fixture；B 亦然，模型调用有证据。
- [ ] E 来源可追溯；人工纠错单列，不能标自主成功。
- [ ] Procedure 经过所需确认，Skill hash 冻结，无答案硬编码。
- [ ] B 实际读取/注入该 Skill；若宣称 OS 采集，证据来自真实操作主机。
- [ ] 两臂不是不同能力的执行器，不把 payment 专用路径当通用基线。

### 结果与演示
- [ ] 每个 trial 都有状态、原始评分、业务评分、时长与日志。
- [ ] 失败、超时、环境错误和重跑全部可见。
- [ ] 至少 A/B 各 1 次有效尝试；3 次仅方向性统计。
- [ ] 没有成功样本时相应提升为 N/A；没有编造成本。
- [ ] 明确“同题经验复用”，不声称泛化、官方排行或优于普通记忆。
- [ ] 已确认 Skill 的复验能以一个命令完成；首次权限/人工确认单列。
- [ ] 本文方案交付与以上实现验收严格分开，未做项目不勾选。

## 11. 待验证事项与 V2

首日必须确认：目标执行器及模型可用性、当前上游镜像可拉取、NPC 历史依赖兼容、Mac 采集权限、下载映射、真实 Lynx 接口、reset 覆盖、资源足够、评分隔离。当前无任何一项因写入本文就视为通过。

V2 再扩展：变更供应商/价格/阈值且同步更新 NPC/数据/答案、未见任务拆分、原始轨迹与普通摘要对照、多任务多 seed、多模型、检索消融、成本摊销、跨软件迁移、Skill 版本迭代。原题同题重复与 V2 测试集不得混在一个成功率分母里。

## 12. 上游依据与许可

实施时将下列 main 链接替换/补充为锁定 commit 链接以便复现。本文没有复制金标准答案；开发者只在受限评分环境检查 evaluator。

- [TheAgentCompany 仓库与说明](https://github.com/TheAgentCompany/TheAgentCompany)
- [环境配置](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/SETUP.md)
- [服务部署](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/servers/README.md)
- [评测接入](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/EVALUATION.md)
- [评测目录](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/evaluation/README.md)
- [任务工作区](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/workspaces/README.md)
- [主任务目录](https://github.com/TheAgentCompany/TheAgentCompany/tree/main/workspaces/tasks/admin-get-best-vendor-quote)
- [基础任务镜像和初始化](https://github.com/TheAgentCompany/TheAgentCompany/tree/main/workspaces/base_image)
- [备用任务](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/workspaces/tasks/finance-invoice-matching/task.md)
- [TheAgentCompany LICENSE](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/LICENSE)
- [lynx-cognition](https://github.com/elliothux/lynx-cognition)

TheAgentCompany 主仓采用 MIT；依赖软件、镜像、数据的许可分别核查。复用或分发源码时保留相应版权/许可文本，报告注明是其任务子集的适配实验。本仓库目前只新增方案，不捆绑上游代码、数据、镜像或密钥。
