"""Render the participant prompt from the published ledger, in invoice order."""
import argparse
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS = "You are taking over the cash allocation queue. Post the first Finance instruction for the two invoices on the assigned remittance. Each receipt is already matched to its invoice. Use current desk practice; money is SGD. The previous shift's closed postings and source records are available via ./work read invoices-history. Output one CSV data row per invoice, no header: invoice_id,discount,transfer_to_claims,writeoff,collectible_balance,follow_up. Four amounts must reconcile the cash to the ledger. Use CLAIMS, COLLECTIONS, or CLOSED. For an unresolved invoice submit invoice_id,REFER instead. Independent lines may have different outcomes. Use only ./work read invoices-history and ./work submit with one quoted multiline CSV argument. No other commands, tools or files. The first submit receives an immutable receipt and no scoring feedback. Do not edit or resubmit. The complete handover records follow."
HANDOFF = 'Desk practice has not changed since the archived shift.'
INCIDENT = {
    "BANK_CONFIRMED": "Bank Operations confirmed a receiving-bank service interruption affecting this transfer on its value date.",
    "PAYER_CONFIRMED": "Payer IT confirmed a payer-side outage. Bank Operations reports normal receiving-bank service for this transfer.",
    "NONE": "Incident record for this transfer: NONE.",
}


def invoice_record(row):
    amounts = {k: f"{Decimal(row[k]) / 100:.2f}" for k in ("goods", "freight", "tax", "credit", "cash", "reserve", "ded")}
    fields = {**row, **amounts, "pod": "YES" if row["pod"] else "NO"}
    lines = [
        "ERP and bank reconciliation | receipt {key} | SGD",
        "Invoice {invoice}, shipment {shipment}. Merchandise {goods}, freight {freight}, tax {tax}.",
        "Ledger credit on this invoice: {credit}, {credit_class}, {credit_state}.",
        "Bank receipt {cash}. Payment instruction {sent}; bank value {value}; ERP imported {entered}.",
        "Contract prompt-payment rate {rate}; prompt-payment deadline {deadline}.",
        INCIDENT[row["incident"]],
        "Carrier case: shipment {claim_shipment}, reserve {reserve}, liability pending. Signed POD exception on invoiced shipment: {pod}.",
        "Please post the short payment on invoice {invoice}. The customer's remittance label is {kind}, with a separate damage deduction claim of SGD {ded}. The ledger extract is in the assigned cash-desk folder.",
    ]
    return "\n".join(line.format_map(fields) for line in lines)


def render(ledger):
    rows = json.loads(ledger.read_text())
    if len(rows) != 2 or rows[0]["invoice"] == rows[1]["invoice"]:
        raise ValueError(f"Expected two distinct invoices in {ledger}")
    return INSTRUCTIONS + "\n" + "\n\n".join(map(invoice_record, rows)) + "\n" + HANDOFF


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for task in json.loads((ROOT / "tasks/manifest.json").read_text()).values():
        if task["type"] == "packet":
            prompt = ROOT / task["prompt"]
            expected = render(ROOT / task["ledger"])
            if args.write:
                prompt.write_text(expected)
            elif prompt.read_text() != expected:
                parser.exit(1, f"Frozen prompt differs from its ledger: {prompt}\n")
