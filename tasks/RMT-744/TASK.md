You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow.
ERP and bank reconciliation | receipt 46544 | SGD
Invoice I-46544, shipment S-46544. Merchandise 2020.00, freight 95.20, tax 24.80.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 2132.00. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-46544, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-46544. The customer's remittance label is OTHER, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.

ERP and bank reconciliation | receipt 46528 | SGD
Invoice I-46528, shipment S-46528. Merchandise 1320.00, freight 95.30, tax 24.70.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1434.90. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-46528, reserve 7.20, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-46528. The customer's remittance label is DAMAGE, with a separate damage deduction claim of SGD 5.10. The ledger extract is in the assigned cash-desk folder.
Desk practice has not changed since the archived shift.