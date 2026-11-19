You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow.
ERP and bank reconciliation | receipt 46999 | SGD
Invoice I-46999, shipment S-46999. Merchandise 1290.00, freight 99.60, tax 10.40.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1381.00. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-46999, reserve 17.50, liability pending. Signed POD exception on invoiced shipment: YES.
Please post the short payment on invoice I-46999. The customer's remittance label is DAMAGE, with a separate damage deduction claim of SGD 14.60. The ledger extract is in the assigned cash-desk folder.

ERP and bank reconciliation | receipt 43731 | SGD
Invoice I-43731, shipment S-43731. Merchandise 1170.00, freight 114.50, tax 10.50.
Ledger credit on this invoice: 100.00, FREIGHT, POSTED.
Bank receipt 1165.70. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment S-43731, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-43731. The customer's remittance label is TERMS, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.
Desk practice has not changed since the archived shift.