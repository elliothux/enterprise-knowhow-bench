# 原始训练与扩展题

以下 11 份题面和冻结输入供独立练习与评测，另行列于财务报告的 40 张原生工单、16 张双发票工单之外。[报告题库](../tasks/README.md)

| 任务 | 训练 | 评测 |
|---|---|---|
| 到岸成本与报价筛选 | [题面与 PDF](suite/landed-cost-training/task.md) | [题面与 PDF](suite/landed-cost-evaluation/task.md) |
| 发票对账 | [题面与 PDF](suite/invoice-reconciliation-training/task.md) | [题面与 PDF](suite/invoice-reconciliation-evaluation/task.md) |
| 交付文档清单 | [题面与 PDF](suite/release-package-training/task.md) | [题面与 PDF](suite/release-package-evaluation/task.md) |
| 付款建议文件 | [题面与 PDF](suite/payment-release-training/task.md) | [题面与 PDF](suite/payment-release-evaluation/task.md) |
| Numbers 补货工作簿 | [题面与模板](workbook/training/task.md) | [题面与模板](workbook/evaluation/task.md) |
| 供应商询价 | | [题面](vendor-quote/task.md) |

从仓库根目录启动干净的 Compose 环境，按原题 ID 装载文档和房间，随后让参评者阅读对应 task.md 并在独立工作目录交付。原题使用固定房间；重复试验请使用独立的干净服务实例。检查器会核对本地文件、共享链接及业务系统收到的交付。

```sh
docker compose up -d --wait
python3 benchmark/suite_data.py list
python3 benchmark/suite_data.py seed landed-cost-evaluation
# 完成题面要求的操作后
python3 benchmark/suite_data.py verify landed-cost-evaluation --workspace /path/to/submission
```

工作簿题需要原生 Numbers 操作和 LibreOffice 重算。供应商询价题先按[主说明](../README.md)启动 vendor-quote NPC profile，再按题面完成沟通、下载、上传和分享，运行 `python3 benchmark/verify_case.py --workspace /path/to/submission --output /path/to/grade.json`。
