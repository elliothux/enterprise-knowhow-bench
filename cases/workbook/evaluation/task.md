# Native Numbers replenishment / workbook-evaluation

Use this Mac's Apple Numbers 14.5 through native Computer Use to finish the supplied
`template.xlsx` and export `replenishment.xlsx`. Budget: 900 seconds.

ownCloud: http://localhost:8092, folder `Documents/Benchmark Suite/workbook-evaluation`.
RocketChat: http://localhost:13000, room `workbook-evaluation`.
Login for both: `theagentcompany` / `theagentcompany`. These locations will be prepared
by the examiner before a run; do not substitute another case or conversation.

The workbook has exactly three sheets, each with one table starting at A1. Retain
the names `Stock`, `Inbound`, `Plan`, row order, headers, and all original input cells.
Do not insert, delete, move or rename sheets, tables, columns or rows. Blank padding
is fine. Export must retain these exact sheet names and cell positions:

| Sheet | Header row 1 | Data rows |
| --- | --- | --- |
| Stock | A: sku, B: location, C: on_hand, D: reserved | 2–12 |
| Inbound | A: sku, B: quantity, C: status, D: eta | 2–17 |
| Plan | A: sku, B: target_units, C: pack_size, D: available, E: confirmed_due_inbound, F: net_available, G: reorder_units | 2–9 |

`Plan!J1` labels `as_of`; its fixed date is in `K1`. `Plan!J2` labels `cutoff`;
its fixed date is in `K2`. `Plan!B2:C9` contains the fixed per-SKU target and pack
parameters. Keep these inputs unchanged; formulas must refer to their cells.

For each of the eight Plan SKUs, fill D:G with live formulas, including intermediate
results. Every output cell must contain a formula and recalculate from the inputs:

- Match the **exact SKU string**, preserving every leading zero. `001204` and `1204`
  are different products; do not coerce SKU to a number.
- available = sum(on_hand − reserved) for that SKU across **all locations**.
  Allow negative available; do not clamp it to zero.
- confirmed_due_inbound = sum(quantity) for that SKU only where status is exactly
  `CONFIRMED` and eta **<= cutoff**, inclusive. Include dates before as_of: these
  represent overdue confirmed orders. as_of is context, **not a lower date bound**.
  Exclude `PENDING`, `CANCELLED`, and eta after cutoff. Each row is a separate order;
  cancelled orders are not negative offsets against other orders.
- net_available = available + confirmed_due_inbound.
- reorder_units = MAX(0, CEILING((target_units − net_available) / pack_size) × pack_size),
  where CEILING means round the pack count toward positive infinity to an integer.
  An exact pack multiple stays unchanged, and a surplus requires zero reorder.

Use native Numbers GUI to enter and fill formulas; equivalent dynamic formulas are
accepted. No formula text or calculated answer is provided in the source template.
Valid formulas the examiner cannot process require examiner review, not a business-failure score.
Do not type fixed result constants, hard-code source inputs inside formulas, or
change the input cells. The examiner checks original values, formulas, and independent
input changes followed by recalculation, including SKU strings, stocks, quantities,
status, eta, cutoff, targets and packs. A correct static screenshot is insufficient.

Download through the assigned fresh Chrome Guest window, then open in Numbers.
Immediately save a native working copy as `working.numbers` in the assigned workspace
before entering formulas (File > Save As); do not accept the default iCloud location.
The native working copy is allowed, but auxiliary tools still may create only link.txt.
All
business reading, formula entry, editing, saving/export, upload, share and chat must
use native `cua.getApp` desktop controls, AX, keyboard and screenshots. No browser DOM
APIs, Playwright, shell, AppleScript, HTTP/APIs, connectors, spreadsheet libraries,
code-generated/edited workbooks, other spreadsheet apps or headless tools. Auxiliary
file-writing tools may create **only `link.txt`**, containing only the final share URL.
Do not read examiner code, fixtures, gold, other runs or other skills. Only arm B may
read its examiner-staged recorded Skill. A and B otherwise have identical materials,
permissions, time budget and environment; arm A retains its normal reasoning ability.

Use exactly one fresh Chrome Guest window; do not use signed-in browser sessions or
close unrelated windows/documents. If a preexisting Guest window is present, stop
and report it. Keep the relevant Numbers or Guest window visibly foreground for its
actions. Every native Save/Export dialog must use Go to Folder and the full assigned
workspace path; verify that destination rather than accepting a remembered folder.

Export through Numbers to local `replenishment.xlsx` in the assigned workspace.
Visibly inspect the exported workbook in Numbers (not just the working document),
including all eight result rows and leading-zero IDs. Do not overwrite the source.
Upload `replenishment.xlsx` to the same ownCloud folder, publicly share that file
without a password or login, save the URL alone in local `link.txt`, and post the
same URL in the assigned RocketChat room. Close only this run's documents and Guest
window when done. Report incomplete work honestly; a final message is not delivery.
