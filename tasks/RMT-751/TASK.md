You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow.
ERP and bank reconciliation | receipt 48346 | SGD
Invoice I-48346, shipment S-48346. Merchandise 1125.00, freight 96.50, tax 28.50.
Ledger credit on this invoice: 65.00, GOODS, DRAFT.
Bank receipt 1243.95. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-48346, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-48346. The customer's remittance label is OTHER, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.

ERP and bank reconciliation | receipt 45573 | SGD
Invoice I-45573, shipment S-45573. Merchandise 1420.00, freight 76.60, tax 23.40.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1494.00. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-45573, reserve 19.80, liability pending. Signed POD exception on invoiced shipment: YES.
Please post the short payment on invoice I-45573. The customer's remittance label is DAMAGE, with a separate damage deduction claim of SGD 26.00. The ledger extract is in the assigned cash-desk folder.
Desk practice has not changed since the archived shift.