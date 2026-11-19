You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow.
ERP and bank reconciliation | receipt 47144 | SGD
Invoice I-47144, shipment S-47144. Merchandise 1300.00, freight 57.90, tax 42.10.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1391.60. Payment instruction 2026-11-13; bank value 2026-11-13; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Incident record for this transfer: NONE.
Carrier case: shipment PREV-47144, reserve 9.00, liability pending. Signed POD exception on invoiced shipment: YES.
Please post the short payment on invoice I-47144. The customer's remittance label is DAMAGE, with a separate damage deduction claim of SGD 8.40. The ledger extract is in the assigned cash-desk folder.

ERP and bank reconciliation | receipt 42701 | SGD
Invoice I-42701, shipment S-42701. Merchandise 1460.00, freight 97.80, tax 42.20.
Ledger credit on this invoice: 0.00, GOODS, POSTED.
Bank receipt 1593.85. Payment instruction 2026-11-13; bank value 2026-11-18; ERP imported 2026-11-18.
Contract prompt-payment rate 2%; prompt-payment deadline 2026-11-13.
Bank Operations confirmed a receiving-bank service interruption affecting this transfer on its value date.
Carrier case: shipment S-42701, reserve 0.00, liability pending. Signed POD exception on invoiced shipment: NO.
Please post the short payment on invoice I-42701. The customer's remittance label is TERMS, with a separate damage deduction claim of SGD 0.00. The ledger extract is in the assigned cash-desk folder.
Desk practice has not changed since the archived shift.