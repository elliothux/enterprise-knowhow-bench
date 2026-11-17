# Lynx Benchmark

基于 TheAgentCompany 的同任务经验复用对照，验证 Agent 在真实跨软件任务中，使用 lynx-cognition 沉淀的固定 Skill 后，任务结果与耗时如何变化。

## V1 开发与验收方案

**[完整方案：docs/v1-benchmark-plan.md](docs/v1-benchmark-plan.md)**

- 主任务：RocketChat 询问要求与资料位置 → ownCloud 下载供应商 PDF → 筛选报价 → 生成并上传 CSV → 分享链接。
- 对照：同模型、同执行器、同工具、同初始状态；A 无 Skill，B 使用真实经验编译并确认的固定 Skill。
- 范围：两天内优先做一道题的真实闭环，至少 A/B 各一次，时间允许各三次。
- 内容：环境部署与重置、NPC、macOS 真实采集、Lynx 接口边界、一键编排设计、评分、成本、开发排期、验收及 V2 路线。

## 当前状态

本仓库目前只有**方案文档**，尚未实现 runner、部署测试服务、接通模型或产出 benchmark 成绩。方案中的 CLI、配置和目录是拟实现契约，不能直接运行。

V1 只衡量同题经验复用，不证明未见任务泛化，也不是 TheAgentCompany 官方排行榜结果。不预设 Skill 一定提升性能。真实模型执行与 fixture 测试必须分开。

## 上游

- [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany)
- [lynx-cognition](https://github.com/elliothux/lynx-cognition)

上游代码、服务、镜像和数据按各自许可使用；本仓库没有捆绑这些内容或任何密钥。
