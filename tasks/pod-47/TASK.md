Process the signed proof-of-delivery claim packet for pod-47. All figures are synthetic SGD. Two attached inspection diagrams show the North and South receiving docks. Each marked bay has a lot code and its pallet quantity. The shape legend is printed on both sheets. Use the complete quantity in damage-confirmed bays only. Apply the signed supervisor corrections to the specified dock and position before summing quantities by lot across both sheets. Pending QA and accepted bays earn no confirmed loss.

Final corrections:
North A4: final status accepted.
North D1: final status accepted.
South B5: final status accepted.
South D5: final status accepted.

Finance ledger: invoice / lot / replacement cost per unit / cash shortfall / active carrier reserve
AR-47019 / GV12 / 1.69 / 49.00 / 35.00
AR-47032 / JN74 / 1.26 / 7.95 / 92.00
AR-47045 / PC56 / 2.37 / 31.70 / 12.40
AR-47058 / RF20 / 1.89 / 38.10 / 64.00
AR-47071 / TL38 / 1.08 / 43.25 / 53.00
AR-47084 / UK95 / 2.14 / 26.90 / 25.00
AR-47097 / VS61 / 2.77 / 66.73 / 71.00
AR-47110 / ZX43 / 1.51 / 34.80 / 18.50

Calculate confirmed loss at replacement cost. Transfer the minimum of confirmed loss, shortfall and reserve to claims. Write off any remaining balance up to and including SGD 5.00; anything larger remains collectible in full. Follow-up is COLLECTIONS if collectible > 0, otherwise CLAIMS if transfer > 0, otherwise CLOSED.

Submit one CSV message, eight rows, no header: invoice,confirmed_units,confirmed_loss,claims_transfer,collectible,follow_up. Use decimal SGD in the three money columns. Each row earns respectively 25, 20, 25, 20 and 10 points for its five results. Use ./work submit with one quoted multiline argument. Inspect the supplied diagrams visually; native image viewing of North.png and South.png is available. No OCR, code-based pixel extraction, other files, external sources or post-submission edits. The first received message is scored.
