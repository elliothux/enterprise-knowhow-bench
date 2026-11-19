You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow.
ERP and bank reconciliation | receipt 46316 | SGD
Invoice I-46316, shipment S-46316. Merchandise 2125.00, freight 110.70, tax 29.30.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 2256.95. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-46316, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-46316. The customer's remittance label is OTHER, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.

ERP and bank reconciliation | receipt 44746 | SGD
Invoice I-44746, shipment S-44746. Merchandise 1250.00, freight 95.60, tax 4.40.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1320.90. Payment instruction 2026-11-13; bank value 2026-11-17; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Bank Operations confirmed a receiving-bank service interruption affecting this transfer on its value date.
Carrier case: shipment S-44746, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-44746. The customer's remittance label is TERMS, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.
Desk practice has not changed since the archived shift.