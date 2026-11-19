#!/usr/bin/env python3
"""Examiner-only suite data builder, ownCloud/RocketChat preseed and verifier."""
import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import io
import json
import math
import re
from pathlib import Path
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request

if __package__:
    from . import services as bench, workbook_case
else:
    import services as bench
    import workbook_case

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation/suite"
MANIFEST = ROOT / "evaluation/suite/manifest.json"
OUTPUTS = {
    "landed-cost": {"filename": "landed-cost.csv", "columns": ["vendor_id", "quote_id", "cpu_cores", "ram_gb", "landed_total_sgd", "budget_remaining_sgd"], "key_fields": ["vendor_id"], "money_fields": ["landed_total_sgd", "budget_remaining_sgd"], "integer_fields": ["cpu_cores", "ram_gb"]},
    "invoice-reconciliation": {"filename": "reconciliation.csv", "columns": ["vendor_id", "invoice_id", "gross_sgd", "credit_sgd", "paid_sgd", "outstanding_sgd", "due_on", "status"], "key_fields": ["vendor_id", "invoice_id"], "money_fields": ["gross_sgd", "credit_sgd", "paid_sgd", "outstanding_sgd"], "integer_fields": []},
    "release-package": {"filename": "release-manifest.csv", "columns": ["doc_key", "document_id", "revision", "source_file", "page", "effective_on", "status", "issue"], "key_fields": ["doc_key"], "money_fields": [], "integer_fields": ["revision", "page"]},
    "payment-release": {"family": "payment-release", "filename": "payment-release.csv", "columns": ["invoice_id", "vendor_id", "decision", "reason_codes", "net_payable_sgd", "bank_account_ref", "evidence_refs"], "key_fields": ["vendor_id", "invoice_id"], "money_fields": ["net_payable_sgd"], "integer_fields": []},
}

PAYMENT_SOURCES = {
    "invoices": "04-invoice-revisions.pdf", "purchase_orders": "05-po-receipts.pdf",
    "receipts": "05-po-receipts.pdf", "bank_events": "06-bank-controls.pdf",
    "hold_events": "07-hold-events.pdf", "settlements": "08-settlement-register.pdf",
    "exceptions": "03-exception-bulletin.pdf",
}


def payment_documents(case):
    p = case["rules"]
    index = ["README / payment recommendation dossier", case["id"], "SIMULATION ONLY. No money is moved; do not initiate any payment.",
             "Review date / timezone: " + p["as_of"] + " / Singapore (UTC+08).",
             "Event cutoff (inclusive): " + p["event_cutoff"],
             "Recorded cutoff (inclusive): " + p["recorded_cutoff"],
             "", "Output roster: one recommendation for EACH of these eight business keys:"]
    index += [r["vendor_id"] + " / " + r["invoice_id"] for r in case["roster"]]
    index += ["", "Document index (read all eight PDFs; no other sources are required):",
              "01-readme-policy.pdf: this index and current policy, pages 2-3.",
              "02-archived-policy.pdf: prior policy retained for audit; check applicability.",
              "03-exception-bulletin.pdf: published exception approvals, with scope and limits.",
              "04-invoice-revisions.pdf: invoice versions; 05-po-receipts.pdf: PO and receipts.",
              "06-bank-controls.pdf: bank changes and verification; 07-hold-events.pdf: holds.",
              "08-settlement-register.pdf: credits, payments and duplicate assessments.",
              "", "Deliver payment-release.csv with the seven columns in the task.",
              "No rules, answers or approvals are supplied by chat. This dossier is complete."]
    policy = ["CURRENT PAYMENT RELEASE POLICY / " + p["policy_id"],
              "Status APPROVED; effective from " + p["policy_effective_from"] + "; no expiry.",
              "This replaces " + p["old_policy_id"] + ". Apply to this review's event cutoff.",
              "", "1. Scope and time", "Business key is (vendor_id, invoice_id), never invoice_id alone.",
              "For EVERY ledger, use a record only when BOTH event_on <= event cutoff AND",
              "recorded_on <= recorded cutoff (index page 1). Ignore other records completely.",
              "Select greatest numeric revision per invoice business key AFTER time filtering.",
              "Then check its status; never revert to an older POSTED revision if latest is VOID/DRAFT.",
              "Equal copies of the same revision/entry count once; conflicting copies are invalid data.",
              "PO versions group by (vendor_id,po_id); receipt versions by receipt_id; settlement",
              "versions by (vendor_id,entry_id). Select greatest revision before status checks.",
              "", "2. Evaluate ALL gates, without short-circuiting on an earlier failure",
              "NOT_POSTED: the selected invoice status is anything other than POSTED.",
              "DUPLICATE: a latest eligible DUPLICATE_AUDIT for that business key is CONFIRMED.",
              "NO_BALANCE: gross minus POSTED CREDIT minus SETTLED PAYMENT is <= 0.",
              "Only settlement entries matching BOTH vendor_id and invoice_id may be applied.",
              "All amounts include tax, in SGD. Round the final net to cents, half up.",
              "net_payable_sgd is this book balance, including on HOLD rows; do not zero it for HOLD.",
              "PO_MISMATCH: no matching selected APPROVED PO, or invoice gross exceeds its amount.",
              "RECEIPT_SHORT: total selected ACCEPTED receipt amounts for this vendor/invoice/PO",
              "is less than invoice gross. Exact cents; no percentage tolerance or cross-invoice netting."]
    controls = ["CURRENT POLICY continued / " + p["policy_id"],
                "3. Bank / hold / exception controls",
                "Bank records and hold events are immutable. Their order is (event_on, sequence).",
                "Choose latest eligible CHANGE per vendor even if its account is not verified.",
                "The latest CHANGE must have status ACTIVE. BANK_UNVERIFIED unless a VERIFY",
                "references that exact CHANGE ref AND account,",
                "has status VERIFIED, role " + p["bank_verifier_role"] + ", different actor_id from",
                "the CHANGE maker, and is strictly later in (event_on, sequence). Same timestamps",
                "require sequence comparison. Old account verification never verifies a newer change.",
                "bank_account_ref is the latest CHANGE account even on HOLD; blank only if none exists.",
                "ACTIVE_HOLD: any eligible OPEN has no later CLOSE for the SAME business key AND",
                "hold_id, by role " + "/".join(p["hold_close_roles"]) + ". Other roles or hold IDs cannot close it.",
                "A later OPEN reopens a hold; earlier closes cannot close that new OPEN.",
                "Exception approvals are in " + p["bulletin_id"] + ". Only role " + p["waiver_role"] + " may waive",
                ", ".join(p["waivable_reasons"]) + ", and only reasons explicitly named on that approval.",
                "Approval must match both business-key fields AND selected invoice revision; gross",
                "must be <= amount_cap_sgd and valid_until >= event cutoff. Both time cutoffs apply.",
                "NOT_POSTED, DUPLICATE, NO_BALANCE, BANK_UNVERIFIED, ACTIVE_HOLD can NEVER be waived.",
                "", "4. Output and auditable citations", "RELEASE if no unwaived failures remain; otherwise HOLD with ALL remaining reasons.",
                "reason_codes order: " + ";".join(p["reason_order"][:3]) + ";",
                ";".join(p["reason_order"][3:]) + ".",
                "Use semicolons, no skipped reasons. RELEASE reason_codes is NONE.",
                "Evidence is the EXACT SET of: this current policy ref; bulletin ref; selected invoice;",
                "selected matching PO; every selected matching receipt (any status); latest bank CHANGE;",
                "every eligible VERIFY referring to that change; every eligible hold event for this key;",
                "every selected settlement entry and every eligible exception for this key (even if invalid).",
                "Do not cite superseded, time-excluded, other-key records or the old policy. Missing data",
                "has no invented evidence ID. Use record ref values, not hold_id / invoice_id as citations.",
                "Separate evidence refs with ; (comma or | also accepted). Order and duplicates don't matter.",
                "A ref may also be written as its exact PDF filename#ref; both forms are equivalent."]
    archived = ["ARCHIVED POLICY / " + p["old_policy_id"], "Status ARCHIVED; expired immediately before " + p["policy_effective_from"],
                "Superseded by " + p["policy_id"] + ". Retained for audit, not applicable to this review.",
                "Legacy controls: receipt/PO shortfalls up to 5% permitted; same-day bank checks",
                "accepted without actor or sequence comparison; AP_CLERK could close a hold.",
                "These legacy terms must not be used after the expiry above."]
    docs = {"01-readme-policy.pdf": [index, policy, controls], "02-archived-policy.pdf": [archived]}
    # Fixed small packets keep download count at eight; records retain explicit source refs.
    groups = [("03-exception-bulletin.pdf", ["exceptions"], 5),
              ("04-invoice-revisions.pdf", ["invoices"], 4),
              ("05-po-receipts.pdf", ["purchase_orders", "receipts"], 8),
              ("06-bank-controls.pdf", ["bank_events"], 7),
              ("07-hold-events.pdf", ["hold_events"], 4),
              ("08-settlement-register.pdf", ["settlements"], 7)]
    for filename, collections, chunk in groups:
        records = [(name, row) for name in collections for row in case[name]]
        pages = []
        for start in range(0, len(records), chunk):
            lines = [filename + " / " + case["id"], "Published record refs; apply the policy in 01-readme-policy.pdf."]
            if filename == "03-exception-bulletin.pdf":
                lines += ["Bulletin ref: " + p["bulletin_id"], "Approval text cannot override the policy's non-waivable gates."]
            for collection, row in records[start:start + chunk]:
                lines += ["", collection + " / " + row["ref"],
                          "event_on=" + row["event_on"] + "; recorded_on=" + row["recorded_on"]]
                values = [f"{key}={','.join(value) if isinstance(value, list) else value}" for key, value in row.items() if key not in ("ref", "event_on", "recorded_on")]
                lines += ["; ".join(values)]
            pages.append(lines)
        docs[filename] = pages
    return docs


def payment_task(case):
    return f"""# payment-release / {case['id']}

Prepare a simulated payment-release recommendation for every business key on the dossier roster.
This task produces advice only. Do not initiate, schedule or approve any actual payment.

ownCloud: http://localhost:8092, folder `Documents/Benchmark Suite/{case['id']}`.
Start with `01-readme-policy.pdf` (README/index); the source dossier is complete.
RocketChat: http://localhost:13000, room `suite-{case['id']}` (location only, no extra business facts).
Login for both services: `theagentcompany` / `theagentcompany`.

Create `payment-release.csv` with exactly these columns:
`invoice_id,vendor_id,decision,reason_codes,net_payable_sgd,bank_account_ref,evidence_refs`.
After generating the CSV, use TextEdit or another native text viewer through native CUA to open
the actual local CSV file and review EVERY row visibly. Do not rebuild its contents in a data:text
URL as a substitute for reading the file. Close the reviewed document, then return to this run's
Chrome Guest, bring it to the
foreground, and upload/share. This actual-file review must appear in the native recording/trace.
Upload the CSV to the same ownCloud folder, share that CSV publicly without password/login,
save only the URL in local `link.txt`, and post the URL in the assigned RocketChat room.

Download all eight original PDFs and read them through native CUA. Business reading, download,
review, upload, sharing and chat must use native CUA; local final-file generation is allowed.
Do not use HTTP/APIs, DOM, PDF parsers, shell downloads, hidden fixtures/oracle, or other runs.
Use only the assigned workspace and browser. A/B have identical task, sources and permissions.
Time budget: {case['time_budget_seconds']} seconds. Report incomplete work honestly.
"""


def sha(value):
    return hashlib.sha256(value).hexdigest()


def money(value):
    amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if amount == 0 else format(amount, ".2f")


def pdf(pages):
    """Small text-only PDF with standard Helvetica, deterministic xref offsets."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        wrapped = [part for line in lines for part in (textwrap.wrap(line, width=92, break_long_words=False) or [""])]
        if len(wrapped) > 48:
            raise ValueError("PDF page exceeds 48 lines")
        commands = ["BT /F1 10 Tf 13 TL 40 800 Td"]
        for line in wrapped:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.extend([f"({escaped}) Tj", "T*"])
        stream = ("\n".join(commands) + "\nET\n").encode("ascii")
        page_id, stream_id = len(objects) + 1, len(objects) + 2
        kids.append(f"{page_id} 0 R")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>".encode())
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()
    value = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(value))
        value.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(value)
    value.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        value.extend(f"{offset:010d} 00000 n \n".encode())
    value.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(value)


def rules(case):
    if case["family"] == "payment-release":
        return ["Source location/index: 01-readme-policy.pdf in the assigned ownCloud case folder.",
                "Simulation only; submit recommendations, never initiate actual payments.",
                "No business rules or computed answers are supplied in chat."]
    p = case["rules"]
    lines = [f"Benchmark Suite / {case['id']}", "Authoritative rules - all dates inclusive; all money SGD.", f"Business cutoff: {p['as_of']}. Use this date, not the computer clock."]
    if case["family"] == "landed-cost":
        lines += [f"Order quantity: {p['quantity']}. Total order budget including tax: SGD {p['budget']}.", f"Minimum CPU cores {p['cpu_cores']}; RAM {p['ram_gb']} GB; warranty {p['warranty_months']} months.", f"Maximum delivery lead time: {p['lead_days']} days. Tax rate: {p['tax_rate']}.", "For each vendor first retain ACTIVE quotes issued on/before cutoff and valid_until on/after it.", "Choose the greatest (issued_on, revision) among those valid quotes for that vendor.", "Then test hardware, warranty, lead time and budget; never fall back to an older quote.", "Unit price is per server. Shipping is ONCE for the whole order, not per server.", "Tax basis applies to BOTH unit price and shipping; no other charges or discounts.", "EXCLUSIVE: landed = (quantity * unit price + shipping) * (1 + tax rate).", "INCLUSIVE: landed = quantity * unit price + shipping; do not add tax again.", "Round only the final landed total to cents, half up; compare rounded total <= budget.", "Budget remaining = budget - rounded landed total. Include EVERY qualifying vendor only."]
    elif case["family"] == "invoice-reconciliation":
        lines += ["Invoice business key = (vendor_id, invoice_id). Copies across registers are duplicates.", "Deduplicate invoices by greatest (updated_on, revision) on/before cutoff BEFORE filtering status.", "Only latest POSTED invoices issued on/before cutoff enter reconciliation; VOID/DRAFT excluded.", "Credit notes deduplicate by credit_id; payments by payment_id (greatest updated_on, revision).", "Apply only POSTED credits and SETTLED payments, with event_on and updated_on <= cutoff.", "Match both vendor_id and invoice_id. PENDING/FAILED/REVERSED payments do not reduce balance.", "Amounts are already tax-inclusive; do not recalculate tax. No cross-invoice netting.", "Balance = gross - applicable credits - settled payments, rounded half up to cents.", "Output ALL posted invoices, including zero balances and partially paid invoices.", "Status: negative=CREDIT_BALANCE; zero=SETTLED; positive and due_on<cutoff=OVERDUE;", "otherwise OPEN. A due date equal to cutoff is OPEN. Do not trust printed paid badges."]
    else:
        lines += [f"Target release: {p['release_id']}. Mandatory doc_key values: {', '.join(p['required'])}.", "The register is an index; status and effective/expiry dates on each document page govern.", "For each mandatory key retain only target-release pages with status APPROVED, approved_on", "and effective_on <= cutoff, and expires_on blank or >= cutoff. DRAFT/ARCHIVED excluded.", "Choose the greatest numeric revision among eligible pages, not the newest filename.", "A future approved revision does not displace an earlier eligible approved revision.", "Output one row per mandatory key. Selected page: status READY, issue blank.", "No eligible page: status MISSING; issue NO_APPROVED_EFFECTIVE_DOCUMENT;", "document_id,revision,source_file,page,effective_on must all be empty in a missing row.", "Use the original PDF filename and 1-based physical page number. Do not invent missing files."]
    output = OUTPUTS[case["family"]]
    lines += ["", f"Deliver {output['filename']} as UTF-8 CSV, exact header:", ",".join(output["columns"]), "Row order does not affect grading. Numbers without currency signs or thousands separators.", "Upload the CSV to the same ownCloud case folder. Share the CSV publicly (no password/login).", "Save only its public URL in local link.txt and post that URL in the suite RocketChat room."]
    return lines


def documents(case):
    if case["family"] == "payment-release":
        return payment_documents(case)
    docs = {"rules.pdf": [rules(case)]}
    family = case["family"]
    if family == "landed-cost":
        for vendor in sorted({q["vendor_id"] for q in case["quotes"]}):
            lines = [f"Supplier quotation file / {vendor}", "Amounts SGD; separate shipping charged once per order.", ""]
            for q in case["quotes"]:
                if q["vendor_id"] == vendor:
                    lines += [f"Quote {q['quote_id']} / revision {q['revision']} / {q['state']}", f"Issued {q['issued_on']}; valid through {q['valid_until']}", f"CPU cores {q['cpu_cores']}; RAM GB {q['ram_gb']}; warranty months {q['warranty_months']}", f"Lead days {q['lead_days']}; unit price {q['unit_price']}; shipping {q['shipping']}", f"Tax basis: {q['tax_basis']}", ""]
            docs[f"quotes-{vendor.lower()}.pdf"] = [lines]
    elif family == "invoice-reconciliation":
        for name, records in case["registers"].items():
            lines = [name.replace("-", " ").title(), "Latest record rules are in rules.pdf; repeated IDs are not new transactions.", ""]
            for row in records:
                lines += ["; ".join(f"{key}={value}" for key, value in row.items()), ""]
            docs[name + ".pdf"] = [lines]
    else:
        index = ["Release document register / index", f"Release requested: {case['rules']['release_id']}", "Open the listed pages; this index does not confer approval.", ""]
        for filename, records in case["packets"].items():
            docs[filename] = []
            for page, row in enumerate(records, 1):
                docs[filename].append([f"Controlled document / {row['document_id']}", ""] + [f"{key}: {value}" for key, value in row.items()] + ["", "Document body: " + row["body"]])
                index.append(f"{row['doc_key']} / {row['document_id']} / revision {row['revision']} -> {filename} page {page}")
        docs["document-register.pdf"] = [index]
    return docs


def task(case):
    if case["family"] == "payment-release":
        return payment_task(case)
    output = OUTPUTS[case["family"]]
    goal = {"landed-cost": "Compare procurement quotes and deliver every supplier meeting all specifications and the tax-inclusive order budget.", "invoice-reconciliation": "Reconcile the invoice registers, credit notes and remittances into current per-invoice balances.", "release-package": "Prepare a release manifest containing the latest approved effective document for each mandatory item and explicit missing items."}[case["family"]]
    return f"""# {case['family']} / {case['id']}

{goal}

Use ownCloud http://localhost:8092, folder `Documents/Benchmark Suite/{case['id']}`.
Read `rules.pdf` first and all other source PDFs. The complete business rules are public there.
RocketChat http://localhost:13000 private room `suite-{case['id']}` contains the same fixed-facts bulletin.
Login for both services: `theagentcompany` / `theagentcompany`.
Existing unrelated Emma/Sarah procurement conversations are not sources for this task.

Create `{output['filename']}` with exact columns `{','.join(output['columns'])}`.
Upload it into the source folder. Create a public share of that CSV accessible without login,
save only its URL in local `link.txt`, and post it to the suite RocketChat room.

Business download, reading and upload must use native CUA. Local CSV/file generation is allowed.
Do not read repository fixture, manifest, evaluator, tests or other runs. Do not use APIs, HTTP,
shell downloads, PDF parsers, browser DOM or scripts to inspect business files.
Use only this trial's workspace and browser context. Both A and B receive these same instructions,
sources and complete rules. Target time budget: 600 seconds; report failure honestly if incomplete.
"""


def build():
    entries = []
    fixtures = sorted(FIXTURES.glob("*/fixture.json")) + sorted((ROOT / "evaluation/fixtures").glob("payment-release-*/fixture.json"))
    for fixture in fixtures:
        case = json.loads(fixture.read_text())
        folder = ROOT / "cases/suite" / case["id"]
        folder.mkdir(parents=True, exist_ok=True)
        payloads = {folder / "task.md": task(case).encode("utf-8")}
        sources = []
        for filename, pages in documents(case).items():
            path = folder / filename
            payload = pdf(pages)
            payloads[path] = payload
            sources.append({"path": str(path.relative_to(ROOT)), "filename": filename, "sha256": sha(payload), "bytes": len(payload), "pages": len(pages)})
        hashes = {str(path.relative_to(ROOT)): sha(value) for path, value in payloads.items()}
        hashes[str(fixture.relative_to(ROOT))] = sha(fixture.read_bytes())
        freeze = fixture.with_name("freeze.json")
        if freeze.exists() and json.loads(freeze.read_text())["sha256"] != hashes:
            raise ValueError("Frozen case changed; create a new case ID instead: " + case["id"])
        for path, value in payloads.items():
            if not path.exists():
                path.write_bytes(value)
            elif path.read_bytes() != value:
                raise ValueError("Existing material differs; refusing overwrite: " + str(path))
        if not freeze.exists():
            freeze.write_text(json.dumps({"schema_version": 1, "case_id": case["id"], "sha256": hashes}, indent=2) + "\n")
        entries.append({"id": case["id"], "family": case["family"], "split": case["split"], "task_path": str((folder / "task.md").relative_to(ROOT)), "task_sha256": hashes[str((folder / "task.md").relative_to(ROOT))], "freeze_path": str(freeze.relative_to(ROOT)), "remote_dir": "Documents/Benchmark Suite/" + case["id"], "room_name": "suite-" + case["id"], "sources": sources, "output": {**OUTPUTS[case["family"]], "link_filename": "link.txt"}, "time_budget_seconds": case.get("time_budget_seconds", 600), "oracle": {"algorithm": case["family"] + "-v1", "fixture_path": str(fixture.relative_to(ROOT)), "fixture_sha256": sha(fixture.read_bytes())}, "npc_policy": {"mode": "static_facts_bulletin", "authoritative_source": "rules.pdf", "facts": rules(case), "no_dynamic_model": True, "no_answer_or_qualifying_ids": True, "out_of_scope_reply": "Use this case's published source PDFs; no extra facts or computed answers are available."}})
        if case["family"] == "payment-release":
            entry = entries[-1]
            entry["npc_policy"].update(mode="location_only", authoritative_source="01-readme-policy.pdf")
            aliases = {filename + "#" + row["ref"]: row["ref"] for collection, filename in PAYMENT_SOURCES.items() for row in case[collection]}
            aliases.update({"01-readme-policy.pdf#" + case["rules"]["policy_id"]: case["rules"]["policy_id"], "02-archived-policy.pdf#" + case["rules"]["old_policy_id"]: case["rules"]["old_policy_id"], "03-exception-bulletin.pdf#" + case["rules"]["bulletin_id"]: case["rules"]["bulletin_id"]})
            entry["output"]["evidence_aliases"] = aliases
            entry["capture_requirements"] = "Native CUA opens the actual generated CSV in TextEdit/text viewer; review every row; return to foreground Chrome Guest before upload/share. No reconstructed data:text preview. Trace audit required separately."
    entries.extend(workbook_case.suite_entries())
    manifest = {"schema_version": 1, "kind": "examiner_only_suite", "cases": entries}
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary.replace(MANIFEST)
    return manifest


def load(case_id):
    manifest = json.loads(MANIFEST.read_text())
    entry = next((c for c in manifest["cases"] if c["id"] == case_id), None)
    if entry is None:
        raise ValueError("Unknown case: " + case_id)
    fixture = ROOT / entry["oracle"]["fixture_path"]
    for path, digest in json.loads((ROOT / entry["freeze_path"]).read_text())["sha256"].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError("Frozen input changed: " + path)
    if sha(fixture.read_bytes()) != entry["oracle"]["fixture_sha256"]:
        raise ValueError("Fixture hash mismatch; rebuild and freeze materials before a trial")
    for item in [*entry["sources"], {"path": entry["task_path"], "sha256": entry["task_sha256"]}]:
        if sha((ROOT / item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("Source hash mismatch: " + item["path"])
    case = json.loads(fixture.read_text())
    return entry, case


def dav(path):
    return bench.OC + "/remote.php/webdav/" + urllib.parse.quote(path)


def latest(records, key_fields, cutoff):
    result = {}
    for row in records:
        if row["updated_on"] > cutoff:
            continue
        key = tuple(row[field] for field in key_fields)
        old = result.get(key)
        rank = (row["updated_on"], row["revision"])
        if old is None or rank > (old["updated_on"], old["revision"]):
            result[key] = row
        elif rank == (old["updated_on"], old["revision"]) and row != old:
            raise ValueError("Conflicting copies with identical business ID/revision")
    return list(result.values())


def payment_visible(records, rules):
    visible = {}
    for row in records:
        if row["event_on"] > rules["event_cutoff"] or row["recorded_on"] > rules["recorded_cutoff"]:
            continue
        if row["ref"] in visible and row != visible[row["ref"]]:
            raise ValueError("Conflicting payment record copies: " + row["ref"])
        visible[row["ref"]] = row
    return list(visible.values())


def payment_revisions(records, fields):
    selected = {}
    for row in records:
        key = tuple(row[field] for field in fields)
        old = selected.get(key)
        if old is None or row["revision"] > old["revision"]:
            selected[key] = row
        elif row["revision"] == old["revision"] and row != old:
            raise ValueError("Conflicting payment revisions: " + str(key))
    return list(selected.values())


def payment_oracle(case):
    """Independent rule evaluation; no submitted/model output or saved expected decisions."""
    p, rows = case["rules"], []
    visible = {collection: payment_visible(case[collection], p) for collection in PAYMENT_SOURCES}
    invoices = payment_revisions(visible["invoices"], ["vendor_id", "invoice_id"])
    orders = payment_revisions(visible["purchase_orders"], ["vendor_id", "po_id"])
    receipts = payment_revisions(visible["receipts"], ["receipt_id"])
    settlements = payment_revisions(visible["settlements"], ["vendor_id", "entry_id"])
    rank = lambda event: (event["event_on"], event["sequence"])
    for key in case["roster"]:
        same_key = lambda row: all(row[field] == key[field] for field in ("vendor_id", "invoice_id"))
        invoice = next((row for row in invoices if same_key(row)), None)
        if invoice is None:
            raise ValueError("Roster key has no eligible invoice revision: " + str(key))
        gross = Decimal(invoice["gross_sgd"])
        po = next((row for row in orders if row["vendor_id"] == key["vendor_id"] and row["po_id"] == invoice["po_id"]), None)
        goods = [row for row in receipts if same_key(row) and row["po_id"] == invoice["po_id"]]
        booked = [row for row in settlements if same_key(row)]
        reduction = sum((Decimal(row["amount_sgd"]) for row in booked if (row["kind"], row["status"]) in (("CREDIT", "POSTED"), ("PAYMENT", "SETTLED"))), Decimal(0))
        net = Decimal(money(gross - reduction))
        changes = [row for row in visible["bank_events"] if row["vendor_id"] == key["vendor_id"] and row["kind"] == "CHANGE"]
        change = max(changes, key=rank) if changes else None
        proofs = [row for row in visible["bank_events"] if row["kind"] == "VERIFY" and row["vendor_id"] == key["vendor_id"] and change and row["change_ref"] == change["ref"]]
        bank_ok = change and change["status"] == "ACTIVE" and any(row["account_ref"] == change["account_ref"] and row["status"] == "VERIFIED" and row["role"] == p["bank_verifier_role"] and row["actor_id"] != change["actor_id"] and rank(row) > rank(change) for row in proofs)
        events = [row for row in visible["hold_events"] if same_key(row)]
        active_hold = any(not any(close["action"] == "CLOSE" and close["hold_id"] == opened["hold_id"] and close["role"] in p["hold_close_roles"] and rank(close) > rank(opened) for close in events) for opened in events if opened["action"] == "OPEN")
        failed = {
            "NOT_POSTED": invoice["status"] != "POSTED",
            "DUPLICATE": any(row["kind"] == "DUPLICATE_AUDIT" and row["status"] == "CONFIRMED" for row in booked),
            "NO_BALANCE": net <= 0,
            "PO_MISMATCH": po is None or po["status"] != "APPROVED" or gross > Decimal(po["amount_sgd"]),
            "RECEIPT_SHORT": sum((Decimal(row["amount_sgd"]) for row in goods if row["status"] == "ACCEPTED"), Decimal(0)) < gross,
            "BANK_UNVERIFIED": not bank_ok,
            "ACTIVE_HOLD": active_hold,
        }
        approvals = [row for row in visible["exceptions"] if same_key(row)]
        for approval in approvals:
            if approval["role"] == p["waiver_role"] and approval["invoice_revision"] == invoice["revision"] and gross <= Decimal(approval["amount_cap_sgd"]) and approval["valid_until"] >= p["event_cutoff"]:
                for reason in set(approval["waive_reasons"]) & set(p["waivable_reasons"]):
                    failed[reason] = False
        reasons = [reason for reason in p["reason_order"] if failed[reason]]
        evidence = {p["policy_id"], p["bulletin_id"], invoice["ref"]}
        evidence.update(row["ref"] for row in [*goods, *booked, *proofs, *events, *approvals])
        if po:
            evidence.add(po["ref"])
        if change:
            evidence.add(change["ref"])
        rows.append({**key, "decision": "HOLD" if reasons else "RELEASE", "reason_codes": ";".join(reasons) if reasons else "NONE", "net_payable_sgd": money(net), "bank_account_ref": change["account_ref"] if change else "", "evidence_refs": ";".join(sorted(evidence))})
    return sorted(rows, key=lambda row: (row["vendor_id"], row["invoice_id"]))


def oracle(case):
    """Compute from published business facts, never from model output or saved gold rows."""
    if case["family"] == "payment-release":
        return payment_oracle(case)
    p, rows = case["rules"], []
    cutoff = p["as_of"]
    if case["family"] == "landed-cost":
        vendors = {}
        for quote in case["quotes"]:
            if quote["state"] != "ACTIVE" or not quote["issued_on"] <= cutoff <= quote["valid_until"]:
                continue
            old = vendors.get(quote["vendor_id"])
            if old is None or (quote["issued_on"], quote["revision"]) > (old["issued_on"], old["revision"]):
                vendors[quote["vendor_id"]] = quote
        for q in vendors.values():
            if any(q[key] < p[key] for key in ("cpu_cores", "ram_gb", "warranty_months")) or q["lead_days"] > p["lead_days"]:
                continue
            cost = p["quantity"] * Decimal(q["unit_price"]) + Decimal(q["shipping"])
            if q["tax_basis"] == "EXCLUSIVE":
                cost *= 1 + Decimal(p["tax_rate"])
            elif q["tax_basis"] != "INCLUSIVE":
                raise ValueError("Unspecified quote tax basis")
            total = Decimal(money(cost))
            if total <= Decimal(p["budget"]):
                rows.append(dict(vendor_id=q["vendor_id"], quote_id=q["quote_id"], cpu_cores=str(q["cpu_cores"]), ram_gb=str(q["ram_gb"]), landed_total_sgd=money(total), budget_remaining_sgd=money(Decimal(p["budget"]) - total)))
    elif case["family"] == "invoice-reconciliation":
        registers = case["registers"]
        invoices = latest(registers["invoices-current"] + registers["invoices-history"], ["vendor_id", "invoice_id"], cutoff)
        credits = latest(registers["credit-notes"], ["credit_id"], cutoff)
        payments = latest(registers["remittances"], ["payment_id"], cutoff)
        for invoice in invoices:
            if invoice["status"] != "POSTED" or invoice["issued_on"] > cutoff:
                continue
            key = (invoice["vendor_id"], invoice["invoice_id"])
            credit = sum((Decimal(c["amount_sgd"]) for c in credits if (c["vendor_id"], c["invoice_id"]) == key and c["status"] == "POSTED" and c["event_on"] <= cutoff), Decimal(0))
            paid = sum((Decimal(t["amount_sgd"]) for t in payments if (t["vendor_id"], t["invoice_id"]) == key and t["status"] == "SETTLED" and t["event_on"] <= cutoff), Decimal(0))
            balance = Decimal(money(Decimal(invoice["gross_sgd"]) - credit - paid))
            status = "CREDIT_BALANCE" if balance < 0 else "SETTLED" if balance == 0 else "OVERDUE" if invoice["due_on"] < cutoff else "OPEN"
            rows.append(dict(vendor_id=key[0], invoice_id=key[1], gross_sgd=money(invoice["gross_sgd"]), credit_sgd=money(credit), paid_sgd=money(paid), outstanding_sgd=money(balance), due_on=invoice["due_on"], status=status))
    elif case["family"] == "release-package":
        for key in p["required"]:
            candidates = []
            for filename, packet in case["packets"].items():
                for page, doc in enumerate(packet, 1):
                    if (doc["doc_key"] == key and doc["release_id"] == p["release_id"] and doc["status"] == "APPROVED" and doc["approved_on"] and doc["approved_on"] <= cutoff and doc["effective_on"] and doc["effective_on"] <= cutoff and (not doc["expires_on"] or doc["expires_on"] >= cutoff)):
                        candidates.append({"doc_key": key, "document_id": doc["document_id"], "revision": str(doc["revision"]), "source_file": filename, "page": str(page), "effective_on": doc["effective_on"], "status": "READY", "issue": ""})
            if candidates:
                rows.append(max(candidates, key=lambda row: int(row["revision"])))
            else:
                rows.append({"doc_key": key, "document_id": "", "revision": "", "source_file": "", "page": "", "effective_on": "", "status": "MISSING", "issue": "NO_APPROVED_EFFECTIVE_DOCUMENT"})
    else:
        raise ValueError("Unknown oracle family")
    return sorted(rows, key=lambda row: tuple(row[key] for key in OUTPUTS[case["family"]]["key_fields"]))


def normalize(row, output):
    row = {key: value.strip() for key, value in row.items()}
    if output.get("family") == "payment-release":
        aliases = output.get("evidence_aliases", {})
        refs = [ref.strip() for ref in re.split(r"[;,|\n]", row["evidence_refs"]) if ref.strip()]
        row["evidence_refs"] = ";".join(sorted({aliases.get(ref, ref) for ref in refs}))
        row["reason_codes"] = ";".join(code.strip() for code in row["reason_codes"].split(";"))
    for field in output["money_fields"]:
        number = Decimal(row[field])
        if not number.is_finite() or number != number.quantize(Decimal("0.01")):
            raise ValueError("Money must be finite and exact to cents")
        row[field] = money(number)
    for field in output["integer_fields"]:
        if row[field] == "":
            continue
        number = Decimal(row[field])
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError("Expected integer")
        row[field] = str(int(number))
    return row


def score_csv(payload, expected, output):
    result = {"schema_valid": False, "csv_correct": False, "expected_rows": len(expected), "submitted_rows": 0, "correct_rows": 0, "row_accuracy": 0.0, "false_inclusion_count": 0, "false_inclusion_rate": 0.0}
    try:
        if len(payload) > 1024 * 1024:
            raise ValueError("CSV exceeds 1 MiB")
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != output["columns"]:
            raise ValueError("CSV header differs from required columns")
        actual = []
        for row in reader:
            if len(actual) >= 1000 or set(row) != set(output["columns"]) or any(v is None for v in row.values()):
                raise ValueError("Malformed or oversized CSV rows")
            actual.append(normalize(row, output))
        key = lambda row: tuple(row[field] for field in output["key_fields"])
        gold = {key(row): normalize(row, output) for row in expected}
        counts = Counter(key(row) for row in actual)
        correct = {key(row) for row in actual if key(row) in gold and row == gold[key(row)]}
        false_count = sum(count if item not in gold else count - 1 for item, count in counts.items())
        result.update(schema_valid=True, submitted_rows=len(actual), correct_rows=len(correct), row_accuracy=len(correct) / len(gold) if gold else 1.0, false_inclusion_count=false_count, false_inclusion_rate=false_count / len(actual) if actual else 0.0, csv_correct=len(correct) == len(gold) and len(actual) == len(gold) and false_count == 0)
    except (UnicodeError, csv.Error, InvalidOperation, ValueError) as error:
        result["error"] = str(error)
    if output.get("family") == "payment-release":
        result.update(payment_metrics(payload, expected, output))
    return result


def payment_metrics(payload, expected, output):
    """Score each gate against rule-computed rows, including missing/unsafe recommendations."""
    fields = {"reason_correct_rows": "reason_codes", "amount_correct_rows": "net_payable_sgd", "bank_correct_rows": "bank_account_ref", "evidence_correct_rows": "evidence_refs", "decision_correct_rows": "decision"}
    result = {**dict.fromkeys(fields, 0), "decision_accuracy": 0.0, "false_release_count": 0, "false_hold_count": 0, "missing_rows": len(expected), "reason_gates": {code: {"correct_rows": 0, "expected_rows": len(expected)} for code in ("NOT_POSTED", "DUPLICATE", "NO_BALANCE", "PO_MISMATCH", "RECEIPT_SHORT", "BANK_UNVERIFIED", "ACTIVE_HOLD")}}
    try:
        if len(payload) > 1024 * 1024:
            return result
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != output["columns"]:
            return result
        submitted = []
        for row in reader:
            if len(submitted) >= 1000 or set(row) != set(output["columns"]) or any(value is None for value in row.values()):
                return result
            # Invalid money cannot suppress observed false releases or other field statistics.
            amount = row["net_payable_sgd"]
            row["net_payable_sgd"] = "0.00"
            row = normalize(row, output)
            try:
                row["net_payable_sgd"] = normalize({**row, "net_payable_sgd": amount}, output)["net_payable_sgd"]
            except (ValueError, InvalidOperation):
                row["net_payable_sgd"] = None
            submitted.append(row)
    except (UnicodeError, csv.Error, ValueError):
        return result
    key = lambda row: tuple(row[field] for field in output["key_fields"])
    gold = {key(row): normalize(row, output) for row in expected}
    by_key = {}
    for row in submitted:
        by_key.setdefault(key(row), []).append(row)
        target = gold.get(key(row))
        if row["decision"] == "RELEASE" and (target is None or target["decision"] == "HOLD"):
            result["false_release_count"] += 1
        if row["decision"] == "HOLD" and target and target["decision"] == "RELEASE":
            result["false_hold_count"] += 1
    result["missing_rows"] = len(gold.keys() - by_key.keys())
    for item, target in gold.items():
        candidates = by_key.get(item, [])
        for metric, field in fields.items():
            result[metric] += any(row[field] == target[field] for row in candidates)
        for code, gate in result["reason_gates"].items():
            gate["correct_rows"] += any((code in row["reason_codes"].split(";")) == (code in target["reason_codes"].split(";")) for row in candidates)
    result["decision_accuracy"] = result["decision_correct_rows"] / len(gold) if gold else 1.0
    return result


class ShareRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not bench.valid_share_url(newurl):
            raise ValueError("Share redirect outside local public share endpoint")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_download(link, max_bytes=1024 * 1024):
    if not bench.valid_share_url(link):
        raise ValueError("Invalid local ownCloud public share URL")
    url = link.rstrip("/")
    if not url.endswith("/download"):
        url += "/download"
    # A fresh opener has neither ownCloud credentials nor the browser's cookies.
    with urllib.request.build_opener(ShareRedirect()).open(url, timeout=30) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError("Public output exceeds download size limit")
        return payload


def verify(entry, case, workspace, elapsed_seconds=None):
    if elapsed_seconds is not None and (not math.isfinite(elapsed_seconds) or elapsed_seconds < 0):
        raise ValueError("elapsed_seconds must be finite and nonnegative")
    output = entry["output"]
    local_path, link_path = workspace / output["filename"], workspace / output["link_filename"]
    local = local_path.read_bytes() if local_path.is_file() else b""
    link = link_path.read_text().strip() if link_path.is_file() else ""
    workbook = entry.get("family") == "workbook"
    workbook_report = None
    if workbook:
        workbook_report = workbook_case.grade(entry["split"], local_path,
                                               workspace.parent / "workbook-grading", run_engine=True)
        scores = workbook_report.get("scores", {})
        checks = {"workbook_correct": workbook_report["workbook_pass"],
                  "public_link_format": bench.valid_share_url(link)}
    else:
        scores = score_csv(local, oracle(case), output)
        checks = {"csv_correct": scores["csv_correct"], "public_link_format": bench.valid_share_url(link)}
    errors = {}

    def check(name, action):
        try:
            checks[name] = bool(action())
        except (OSError, ValueError, KeyError) as error:
            checks[name] = False
            errors[name] = str(error)

    for source in entry["sources"]:
        check("local_source:" + source["filename"], lambda source=source: (workspace / source["filename"]).is_file() and sha((workspace / source["filename"]).read_bytes()) == source["sha256"])
    for source in [*entry["sources"], {"filename": "task.md", "sha256": entry["task_sha256"]}]:
        check("source:" + source["filename"], lambda source=source: sha(bench.request(dav(entry["remote_dir"] + "/" + source["filename"]), headers=bench.oc_headers())) == source["sha256"])
    check("uploaded_workbook_matches" if workbook else "uploaded_csv_matches", lambda: bool(local) and bench.request(dav(entry["remote_dir"] + "/" + output["filename"]), headers=bench.oc_headers()) == local)
    check("anonymous_download_matches", lambda: bool(local) and (
        public_download(link, workbook_case.MAX_ZIP) if workbook else public_download(link)) == local)

    def share_target():
        if not bench.valid_share_url(link):
            return False
        parts = urllib.parse.urlsplit(link).path.split("/")
        token = parts[parts.index("s") + 1]
        shares = json.loads(bench.request(bench.OC + "/ocs/v1.php/apps/files_sharing/api/v1/shares?format=json", headers={**bench.oc_headers(), "OCS-APIRequest": "true"}))
        return str(shares["ocs"]["meta"]["statuscode"]) == "100" and any(str(item.get("share_type")) == "3" and item.get("token") == token and item.get("path", "").lstrip("/") == entry["remote_dir"] + "/" + output["filename"] for item in shares["ocs"]["data"])

    check("public_share_targets_output", share_target)

    def chat_delivery():
        auth = bench.login()
        room = bench.rc("groups.info?" + urllib.parse.urlencode({"roomName": entry["room_name"]}), headers=auth)["group"]["_id"]
        messages = bench.rc("groups.history?" + urllib.parse.urlencode({"roomId": room, "count": 100}), headers=auth)["messages"]
        return bool(link) and any(m.get("u", {}).get("username") == bench.CREDENTIAL and m.get("msg", "").strip() == link for m in messages)

    check("share_posted_in_case_room", chat_delivery)
    passed = all(checks.values())
    report = {"kind": "suite_business_verification", "case_id": entry["id"], "business_checks_passed": passed, "completion": int(passed), "checks": checks, "scores": scores, "elapsed_seconds": elapsed_seconds, "within_time_budget": None if elapsed_seconds is None else elapsed_seconds <= entry["time_budget_seconds"], "errors": errors, "fixture_sha256": entry["oracle"]["fixture_sha256"], "protocol_audit": "required separately: native CUA, isolation, immutable Cognition-derived Skill, complete trial ledger; this report is business grading only"}
    if workbook_report is not None:
        report.update(workbook_grading_status=workbook_report["status"], workbook_grading=workbook_report)
        if workbook_report["status"] in ("evaluator_incompatible", "examiner_error", "pending_recalculation"):
            report.update(business_checks_passed=None, completion=None)
    return report


def seed(entry):
    """No reset, deletion, model invocation or oracle upload; refuse occupied case folders."""
    auth = bench.login()
    try:
        info = bench.rc("groups.info?" + urllib.parse.urlencode({"roomName": entry["room_name"]}), headers=auth)
    except urllib.error.HTTPError as error:
        detail = json.loads(error.read() or b"{}")
        if error.code not in (400, 404) or detail.get("errorType") != "error-room-not-found":
            raise
        error.close()
    else:
        if info.get("group"):
            raise ValueError("Prior suite chat exists; explicitly archive/clean before seeding")
        raise ValueError("Cannot establish chat absence; refusing seed")
    shares_url = bench.OC + "/ocs/v1.php/apps/files_sharing/api/v1/shares?format=json"
    shares = json.loads(bench.request(shares_url, headers={**bench.oc_headers(), "OCS-APIRequest": "true"}))
    if str(shares["ocs"]["meta"]["statuscode"]) != "100":
        raise ValueError("Cannot establish share absence; refusing seed")
    for share in shares["ocs"]["data"]:
        path = share["path"].lstrip("/")
        if path == entry["remote_dir"] or path.startswith(entry["remote_dir"] + "/"):
            raise ValueError("Prior suite share exists; explicitly archive/clean before seeding")
    for path in ("Documents", "Documents/Benchmark Suite"):
        try:
            bench.request(dav(path), method="MKCOL", headers=bench.oc_headers())
        except urllib.error.HTTPError as error:
            if error.code != 405:
                raise
            error.close()
    bench.request(dav(entry["remote_dir"]), method="MKCOL", headers=bench.oc_headers())
    materials = [(item["filename"], item["path"]) for item in entry["sources"]]
    materials.append(("task.md", entry["task_path"]))
    for filename, path in materials:
        payload = (ROOT / path).read_bytes()
        url = dav(entry["remote_dir"] + "/" + filename)
        bench.request(url, payload, "PUT", {**bench.oc_headers(), "If-None-Match": "*"})
        if bench.request(url, headers=bench.oc_headers()) != payload:
            raise ValueError("Seed readback mismatch: " + filename)
    room = bench.rc("groups.create", {"name": entry["room_name"], "members": []}, auth)["group"]["_id"]
    bulletin = "EXAMINER FIXED FACTS (not an NPC conversation)\n" + entry["remote_dir"] + "\n" + "\n".join(entry["npc_policy"]["facts"])
    bench.rc("chat.postMessage", {"roomId": room, "text": bulletin}, auth)
    return {"case_id": entry["id"], "seeded": True, "room_id": room, "remote_dir": entry["remote_dir"], "reset_performed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "build", "seed", "verify"))
    parser.add_argument("case_id", nargs="?")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--elapsed-seconds", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build()
    elif args.command == "list":
        result = [{"id": c["id"], "family": c["family"], "split": c["split"], "task_path": c["task_path"]} for c in json.loads(MANIFEST.read_text())["cases"]]
    else:
        if not args.case_id:
            parser.error("case_id is required")
        entry, case = load(args.case_id)
        if args.command == "seed":
            result = seed(entry)
        else:
            if args.workspace is None:
                parser.error("verify requires --workspace")
            result = verify(entry, case, args.workspace, args.elapsed_seconds)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 2 if args.command == "verify" and not result["business_checks_passed"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, StopIteration) as error:
        print(json.dumps({"business_checks_passed": False, "infrastructure_error": str(error)}))
        raise SystemExit(2)
