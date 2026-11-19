#!/usr/bin/env python3
"""Load frozen task data, seed ownCloud/Rocket.Chat and verify business deliverables."""
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


def sha(value):
    return hashlib.sha256(value).hexdigest()


def money(value):
    amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if amount == 0 else format(amount, ".2f")


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
    parser.add_argument("command", choices=("list", "seed", "verify"))
    parser.add_argument("case_id", nargs="?")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--elapsed-seconds", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "list":
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
