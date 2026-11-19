"""Offline payment recommendations only: no UI, service calls or money movement."""
import copy
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from benchmark import suite_data as suite


def load(split="evaluation"):
    return suite.load("payment-release-" + split)


def target(rows, vendor, invoice):
    return next(row for row in rows if (row["vendor_id"], row["invoice_id"]) == (vendor, invoice))


def csv_bytes(rows, output):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=output["columns"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


class PaymentOracleTests(unittest.TestCase):
    def test_training_manual_decisions_and_decimal_balances(self):
        _, case = load("training")
        rows = suite.oracle(case)
        self.assertEqual([(r["vendor_id"], r["invoice_id"], r["decision"], r["reason_codes"], r["net_payable_sgd"]) for r in rows], [
            ("ASTER", "PX-101", "RELEASE", "NONE", "800.10"),
            ("ASTER", "PX-102", "RELEASE", "NONE", "750.00"),
            ("BAY", "PX-201", "HOLD", "NOT_POSTED", "500.00"),
            ("BAY", "PX-202", "HOLD", "DUPLICATE", "900.00"),
            ("COPPER", "PX-301", "HOLD", "BANK_UNVERIFIED", "1200.00"),
            ("COPPER", "PX-302", "HOLD", "BANK_UNVERIFIED", "640.00"),
            ("DELTA", "PX-101", "HOLD", "ACTIVE_HOLD", "800.00"),
            ("DELTA", "PX-402", "HOLD", "NO_BALANCE", "0.00")])

    def test_evaluation_manual_decisions_amounts_and_new_branch_combination(self):
        _, case = load()
        rows = suite.oracle(case)
        self.assertEqual([(r["vendor_id"], r["invoice_id"], r["decision"], r["reason_codes"], r["net_payable_sgd"]) for r in rows], [
            ("IRIS", "QX-701", "RELEASE", "NONE", "1150.20"),
            ("IRIS", "QX-702", "HOLD", "NOT_POSTED", "760.00"),
            ("JUNIPER", "QX-801", "RELEASE", "NONE", "920.00"),
            ("JUNIPER", "QX-802", "HOLD", "DUPLICATE", "680.00"),
            ("KITE", "QX-901", "HOLD", "BANK_UNVERIFIED;ACTIVE_HOLD", "860.00"),
            ("KITE", "QX-902", "HOLD", "RECEIPT_SHORT;BANK_UNVERIFIED", "1100.00"),
            ("LOTUS", "QX-1002", "HOLD", "NO_BALANCE;ACTIVE_HOLD", "-75.00"),
            ("LOTUS", "QX-701", "RELEASE", "NONE", "540.00")])
        _, training = load("training")
        self.assertNotIn("BANK_UNVERIFIED;ACTIVE_HOLD", {r["reason_codes"] for r in suite.oracle(training)})
        self.assertEqual(target(rows, "IRIS", "QX-701")["bank_account_ref"], "SIM-EV-IRIS-02")
        self.assertEqual(target(rows, "LOTUS", "QX-701")["bank_account_ref"], "SIM-EV-LOTUS-01")

    def test_both_cutoffs_filter_before_revision_and_latest_state_never_falls_back(self):
        _, case = load()
        late = next(row for row in case["invoices"] if row["ref"] == "INV-EV-LATE-R9")
        self.assertEqual(target(suite.oracle(case), "JUNIPER", "QX-801")["decision"], "RELEASE")
        late.update(event_on="2026-12-15T16:00:00", recorded_on="2026-12-16T10:00:00")
        self.assertEqual(target(suite.oracle(case), "JUNIPER", "QX-801")["decision"], "RELEASE")
        late["recorded_on"] = "2026-12-16T08:00:00"
        row = target(suite.oracle(case), "JUNIPER", "QX-801")
        self.assertEqual(row["reason_codes"], "NOT_POSTED;PO_MISMATCH;RECEIPT_SHORT")
        self.assertIn("INV-EV-LATE-R9", row["evidence_refs"])
        self.assertNotIn("INV-EV-3-R1", row["evidence_refs"])

    def test_same_timestamp_bank_sequence_independence_and_active_change(self):
        _, case = load("training")
        proof = next(row for row in case["bank_events"] if row["ref"] == "BV-TR-3-NEW")
        self.assertEqual(target(suite.oracle(case), "COPPER", "PX-301")["reason_codes"], "BANK_UNVERIFIED")
        proof["sequence"] = 7
        self.assertEqual(target(suite.oracle(case), "COPPER", "PX-301")["decision"], "RELEASE")
        proof["actor_id"] = "bank-maker"
        self.assertEqual(target(suite.oracle(case), "COPPER", "PX-301")["reason_codes"], "BANK_UNVERIFIED")
        proof["actor_id"] = "independent-checker"
        next(row for row in case["bank_events"] if row["ref"] == "BC-TR-3-NEW")["status"] = "BLOCKED"
        self.assertEqual(target(suite.oracle(case), "COPPER", "PX-301")["reason_codes"], "BANK_UNVERIFIED")

    def test_hold_close_requires_same_id_authorized_role_and_later_sequence(self):
        _, case = load("training")
        self.assertEqual(target(suite.oracle(case), "DELTA", "PX-101")["reason_codes"], "ACTIVE_HOLD")
        close = next(row for row in case["hold_events"] if row["ref"] == "HE-TR-4")
        close["role"] = "AP_CONTROLLER"
        self.assertEqual(target(suite.oracle(case), "DELTA", "PX-101")["decision"], "RELEASE")
        close["sequence"] = 2
        self.assertEqual(target(suite.oracle(case), "DELTA", "PX-101")["reason_codes"], "ACTIVE_HOLD")
        close["sequence"], close["hold_id"] = 4, "WRONG-HOLD"
        self.assertEqual(target(suite.oracle(case), "DELTA", "PX-101")["reason_codes"], "ACTIVE_HOLD")

    def test_po_and_receipt_latest_revisions_do_not_fall_back_to_approved(self):
        _, case = load()
        order = next(r for r in case["purchase_orders"] if r["ref"] == "POREC-EV-1")
        case["purchase_orders"].append({**order, "ref": "POREC-EV-1-R2", "revision": 2, "status": "REVOKED"})
        self.assertEqual(target(suite.oracle(case), "IRIS", "QX-701")["reason_codes"], "PO_MISMATCH")
        receipt = next(r for r in case["receipts"] if r["ref"] == "GR-EV-1")
        case["receipts"].append({**receipt, "ref": "GR-EV-1-R2", "revision": 2, "status": "REJECTED"})
        self.assertEqual(target(suite.oracle(case), "IRIS", "QX-701")["reason_codes"], "PO_MISMATCH;RECEIPT_SHORT")

    def test_exception_scope_caps_role_expiry_and_nonwaivable_gates(self):
        _, original = load()
        for update in ({"invoice_revision": 2}, {"amount_cap_sgd": "1099.99"}, {"role": "AP_CLERK"}, {"valid_until": "2026-12-15T16:59:59"}):
            case = copy.deepcopy(original)
            next(row for row in case["exceptions"] if row["ref"] == "EX-EV-3").update(update)
            self.assertEqual(target(suite.oracle(case), "KITE", "QX-902")["reason_codes"], "PO_MISMATCH;RECEIPT_SHORT;BANK_UNVERIFIED")
        case = copy.deepcopy(original)
        next(row for row in case["exceptions"] if row["ref"] == "EX-EV-3")["waive_reasons"] += ["RECEIPT_SHORT", "BANK_UNVERIFIED"]
        self.assertEqual(target(suite.oracle(case), "KITE", "QX-902")["reason_codes"], "BANK_UNVERIFIED")
        self.assertEqual(target(suite.oracle(original), "KITE", "QX-901")["reason_codes"], "BANK_UNVERIFIED;ACTIVE_HOLD")

    def test_evidence_is_computed_from_selected_records_not_a_saved_answer(self):
        _, case = load()
        expected = {"POL-EV-CURRENT", "BUL-EV-01", "INV-EV-1-R2", "POREC-EV-1", "GR-EV-1", "BC-EV-1-NEW", "BV-EV-1-NEW", "AUD-EV-1", "CR-EV-1", "PAY-EV-1", "PAY-EV-PENDING"}
        row = target(suite.oracle(case), "IRIS", "QX-701")
        self.assertEqual(set(row["evidence_refs"].split(";")), expected)
        next(r for r in case["settlements"] if r["ref"] == "PAY-EV-1")["amount_sgd"] = "231.25"
        self.assertEqual(target(suite.oracle(case), "IRIS", "QX-701")["net_payable_sgd"], "1149.20")
        # Same invoice_id at another vendor must not inherit IRIS payments or hold events.
        self.assertEqual(target(suite.oracle(case), "LOTUS", "QX-701")["net_payable_sgd"], "540.00")


class PaymentAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.entry, self.case = load()
        self.output = self.entry["output"]
        self.expected = suite.oracle(self.case)

    def score(self, rows):
        return suite.score_csv(csv_bytes(rows, self.output), self.expected, self.output)

    def test_all_fields_and_gates_scored_against_oracle(self):
        score = self.score(self.expected)
        self.assertTrue(score["csv_correct"])
        self.assertEqual(score["decision_accuracy"], 1)
        for name in ("decision_correct_rows", "reason_correct_rows", "amount_correct_rows", "bank_correct_rows", "evidence_correct_rows"):
            self.assertEqual(score[name], 8)
        self.assertEqual(score["missing_rows"], 0)
        self.assertTrue(all(gate == {"correct_rows": 8, "expected_rows": 8} for gate in score["reason_gates"].values()))

    def test_missing_all_hold_and_all_release_cannot_game_completion(self):
        empty = self.score([])
        self.assertEqual((empty["missing_rows"], empty["false_release_count"], empty["decision_accuracy"]), (8, 0, 0))
        for decision, false_releases, false_holds in (("HOLD", 0, 3), ("RELEASE", 5, 0)):
            rows = [{**r, "decision": decision} for r in self.expected]
            score = self.score(rows)
            self.assertFalse(score["csv_correct"])
            self.assertEqual((score["false_release_count"], score["false_hold_count"]), (false_releases, false_holds))
        partial = self.score(self.expected[1:])
        self.assertEqual((partial["missing_rows"], partial["false_release_count"], partial["decision_accuracy"]), (1, 0, 7 / 8))

    def test_wrong_bank_omitted_hold_wrong_invoice_version_amount_and_evidence_fail(self):
        mutations = [("bank_account_ref", "SIM-EV-IRIS-01", "bank_correct_rows"), ("reason_codes", "RECEIPT_SHORT", "reason_correct_rows"), ("net_payable_sgd", "1349.60", "amount_correct_rows"), ("evidence_refs", "POL-EV-ARCHIVE", "evidence_correct_rows")]
        for field, value, metric in mutations:
            rows = copy.deepcopy(self.expected)
            rows[0][field] = value
            score = self.score(rows)
            self.assertFalse(score["csv_correct"])
            self.assertEqual(score[metric], 7)
        rows = copy.deepcopy(self.expected)
        held = target(rows, "KITE", "QX-901")
        held["reason_codes"] = "BANK_UNVERIFIED"
        score = self.score(rows)
        self.assertEqual(score["reason_gates"]["ACTIVE_HOLD"]["correct_rows"], 7)
        # Even malformed money must not hide an observed false release.
        held.update(decision="RELEASE", reason_codes="NONE", net_payable_sgd="NaN")
        score = self.score(rows)
        self.assertFalse(score["csv_correct"])
        self.assertEqual(score["false_release_count"], 1)
        self.assertEqual(score["decision_accuracy"], 7 / 8)

    def test_evidence_order_duplicate_refs_and_published_aliases_are_equivalent(self):
        aliases = {ref: alias for alias, ref in self.output["evidence_aliases"].items()}
        rows = copy.deepcopy(self.expected)
        for row in rows:
            refs = list(reversed(row["evidence_refs"].split(";")))
            row["evidence_refs"] = " | ".join(aliases[ref] for ref in refs + refs[:1])
        self.assertTrue(self.score(rows)["csv_correct"])
        rows[0]["evidence_refs"] += ";wrong-document.pdf#POL-EV-CURRENT"
        self.assertFalse(self.score(rows)["csv_correct"])

    def test_submitting_older_posted_invoice_instead_of_latest_draft_is_unsafe(self):
        rows = copy.deepcopy(self.expected)
        row = target(rows, "IRIS", "QX-702")
        row.update(decision="RELEASE", reason_codes="NONE", net_payable_sgd="700.00")
        row["evidence_refs"] = row["evidence_refs"].replace("INV-EV-2-R2", "INV-EV-2-R1")
        score = self.score(rows)
        self.assertFalse(score["csv_correct"])
        self.assertEqual(score["false_release_count"], 1)
        self.assertEqual(score["amount_correct_rows"], 7)
        self.assertEqual(score["evidence_correct_rows"], 7)
        self.assertEqual(score["decision_accuracy"], 7 / 8)

    def test_each_wrong_field_alone_fails_complete_business_delivery(self):
        link = "http://localhost:8092/index.php/s/PaymentTest"
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "link.txt").write_text(link)
            for source in self.entry["sources"]:
                shutil.copyfile(suite.ROOT / source["path"], workspace / source["filename"])
            for field, value in ((None, None), ("bank_account_ref", "WRONG"), ("reason_codes", "ACTIVE_HOLD"), ("net_payable_sgd", "1.00"), ("evidence_refs", "POL-EV-ARCHIVE")):
                rows = copy.deepcopy(self.expected)
                if field:
                    rows[0][field] = value
                body = csv_bytes(rows, self.output)
                (workspace / self.output["filename"]).write_bytes(body)

                def request(url, *args, **kwargs):
                    if "/ocs/" in url:
                        return json.dumps({"ocs": {"meta": {"statuscode": 100}, "data": [{"share_type": 3, "token": "PaymentTest", "path": "/" + self.entry["remote_dir"] + "/payment-release.csv"}]}}).encode()
                    if url.endswith("payment-release.csv"):
                        return body
                    if url.endswith("task.md"):
                        return (suite.ROOT / self.entry["task_path"]).read_bytes()
                    return next((suite.ROOT / s["path"]).read_bytes() for s in self.entry["sources"] if url.endswith(s["filename"]))

                with patch.object(suite.bench, "request", side_effect=request), patch.object(suite.bench, "login", return_value={}), patch.object(suite.bench, "rc", return_value={"group": {"_id": "room"}, "messages": [{"u": {"username": suite.bench.CREDENTIAL}, "msg": link}]}), patch.object(suite, "public_download", return_value=body):
                    result = suite.verify(self.entry, self.case, workspace, 850)
                self.assertEqual(result["business_checks_passed"], field is None)
                self.assertEqual(result["completion"], int(field is None))
                self.assertTrue(result["checks"]["anonymous_download_matches"])


class PaymentMaterialTests(unittest.TestCase):
    def test_public_rules_workload_budget_capture_and_location_only_npc(self):
        for split, budget in (("training", 1200), ("evaluation", 900)):
            entry, case = load(split)
            self.assertEqual(entry["time_budget_seconds"], budget)
            self.assertEqual(len(entry["sources"]), 8)
            self.assertEqual(sum(s["pages"] for s in entry["sources"]), 16)
            self.assertEqual(len({(r["vendor_id"], r["invoice_id"]) for r in case["roster"]}), 8)
            self.assertEqual(len({r["vendor_id"] for r in case["roster"]}), 4)
            docs = suite.documents(case)
            for pages in docs.values():
                for page in pages:
                    self.assertLessEqual(sum(len(textwrap.wrap(line, width=92, break_long_words=False)) or 1 for line in page), 48)
            public = "\n".join(line for page in docs["01-readme-policy.pdf"] for line in page)
            self.assertIn("latest CHANGE must have status ACTIVE", public)
            self.assertIn("BOTH event_on", public)
            self.assertIn("different actor_id", public)
            self.assertIn("SAME business key AND", public)
            self.assertIn("can NEVER be waived", public)
            statement = suite.task(case)
            self.assertIn("TextEdit", statement)
            self.assertIn("actual local CSV file", statement)
            self.assertIn("Do not rebuild", statement)
            self.assertNotIn("BANK_UNVERIFIED", statement)
            self.assertEqual(entry["npc_policy"]["mode"], "location_only")
            self.assertNotIn(case["rules"]["event_cutoff"], "\n".join(entry["npc_policy"]["facts"]))

    def test_six_original_freeze_files_and_all_their_inputs_unchanged(self):
        original = {
            "landed-cost-training": "7ef27a1931b45d979622d2b8d88578ff6e7189bb5ac858e8b890c4f4d9e57101",
            "landed-cost-evaluation": "08b4016d4862f1f2ed30d25fec24ec1b6c045ad76181a181fe96a215b5740259",
            "invoice-reconciliation-training": "8489e18c1e17fb9b1947e4c944665bc8941858cc523a62d84b5b0b2b646a90cf",
            "invoice-reconciliation-evaluation": "1fc03e7353904f61f901358b800c608138b283e9a2f763683ac63a86b5f74656",
            "release-package-training": "a109a8d278f0139a738e8e9e954b883769b3122600efa73833a8be9654310842",
            "release-package-evaluation": "fe12726c8d8b1283efb852d2cf8c82edf60747ba795a8c02e6d829510920db5a"}
        for case_id, digest in original.items():
            path = suite.ROOT / "evaluation/suite" / case_id / "freeze.json"
            self.assertEqual(suite.sha(path.read_bytes()), digest)
            for filename, expected in json.loads(path.read_text())["sha256"].items():
                self.assertEqual(suite.sha((suite.ROOT / filename).read_bytes()), expected)


if __name__ == "__main__":
    unittest.main()
