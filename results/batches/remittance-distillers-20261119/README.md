# Two-invoice remittances with both distillers

All 16 previously scheduled packets appear in the index. It includes the frozen Skill digest, CLI build, model, environment and a link to each packet's history. Each history gives the invoice IDs, independent session IDs, first submissions, ordered business-tool calls, per-invoice scores and original log checksums for all three arms. Scores are the mean of the two invoice grades. [Batch index](index.json) · [Answer keys](../../../evaluation/answer-key.json)

The 32 original A/B sessions supplied the baseline and GLM receipts. The follow-up added one DeepSeek Flash session per packet using the frozen Skill-present harness slot, published as D. All 48 sessions had distinct IDs. Inputs and precedent digests matched across arms once the assigned Skill was removed from the prompt. The operator was gpt-6.1-terra with high reasoning effort and a 300-second budget per session. Each trial ran in a fresh simulated ERP workspace. The training demonstrations used native Chrome Computer Use and Lynx Cognition.

To rerun the full comparison, use the public runner and the follow-up schedule. [Run instructions](../../../tasks/RUN.md) · [Three-arm schedule](../../../tasks/schedules/remittance-distillers.json) · [Results across workflows](../../distillers.md)
