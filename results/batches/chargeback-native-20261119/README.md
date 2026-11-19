# Native chargeback workbook delivery

The operator read a private Finance request in Rocket.Chat, used native LibreOffice Calc to edit the synced template, uploaded an XLSX to its assigned ownCloud folder and posted the filename in the room. The receiver downloaded the file on the first delivery notice. After each trial, the examiner checked the room and folder again against the recorded SHA-256. An accepted file was recalculated in eight input states, 48 formula-backed amounts per state.

| Case | No Skill | GLM-5.3 | DeepSeek Flash |
|---|---:|---:|---:|
| cb-17 | [384/384](cb-17/A/history.json) | [0/384](cb-17/B/history.json) | [384/384](cb-17/D/history.json) |
| cb-28 | [0/384](cb-28/A/history.json) | [140/384](cb-28/B/history.json) | [162/384](cb-28/D/history.json) |

The baseline delivered one fully correct workbook out of two, GLM delivered none and DeepSeek delivered one. These are one session per arm on each of two templates.

On cb-28 the first-delivery scores were 0/384 (0.00%), 140/384 (36.46%), 162/384 (42.19%) for no Skill, GLM and DeepSeek respectively. All three fell short of a complete workbook. In the original input state, the GLM file passed 17/48 checks and the DeepSeek file passed 19/48. For example, neither supplied the correct closing amounts for invoice N-103. The grader also replayed seven input changes to test whether the formulas updated.

On cb-17 the GLM-assisted operator uploaded a workbook and notified Finance, but its output cells contained no scoreable formulas. The submitted file earned **0/384**. The baseline and DeepSeek files passed every check. The local authoring control passed 384/384 on both templates with all three conditions. This control shows the inputs and grader admit a working solution. The native and code-enabled conditions differ in their permitted tools and delivery workflow.

cb-17 had 2, 3, 2 recorded Calc crashes in A, B and D respectively. cb-28 had 2, 2, 2 recorded Calc crashes in A, B and D respectively. The histories link workbook correctness to the recipient's file hash and list the available macOS crash reports. The separate browser audit flagged the assigned local XLSX URL and could not confirm Guest closure in the six operator traces. During Calc recovery in cb-28, the baseline also displayed and closed the preceding GLM trial’s template before reopening its own file. The first received baseline workbook earned zero. This trial has a workspace isolation exception. The examiner independently checked and cleared each trial's windows after scoring. The table measures the business deliverable. A process crash alone does not identify what produced an incorrect cell. The Numbers availability preflight was excluded before running the six formal Calc sessions. [Native batch index](index.json) · [Local authoring control](../chargeback-office-20261119/README.md) · [Public templates, scorer and rerun instructions](../../../cases/chargebacks/README.md)
