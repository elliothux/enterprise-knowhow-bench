"""Offline examiner checks; no service, UI, model, seed or reset is executed."""
import copy
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from benchmark import suite_data as suite


def case(case_id):
    return suite.load(case_id)


def payload(rows, output):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=output["columns"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def http_error(code, detail=None):
    return urllib.error.HTTPError("http://localhost/fixture", code, "fixture", {}, io.BytesIO(json.dumps(detail or {}).encode()))


class OracleTests(unittest.TestCase):
    def test_landed_manual_arithmetic_and_new_revision_before_hardware(self):
        _, c = case("landed-cost-training")
        rows = suite.oracle(c)
        self.assertEqual([(r["vendor_id"], r["quote_id"], r["landed_total_sgd"], r["budget_remaining_sgd"]) for r in rows], [("ALDER", "AT-112", "10791.00", "209.00"), ("BIRCH", "BT-204", "11000.00", "0.00")])
        _, c = case("landed-cost-evaluation")
        self.assertEqual([(r["vendor_id"], r["landed_total_sgd"]) for r in suite.oracle(c)], [("FIR", "14861.61"), ("GINKGO", "15000.00")])

    def test_landed_rule_changes_recompute_instead_of_matching_saved_answers(self):
        _, c = case("landed-cost-training")
        c["rules"]["quantity"] = 3
        self.assertEqual(suite.oracle(c), [])
        _, c = case("landed-cost-evaluation")
        c["quotes"][0]["issued_on"] = "2026-11-18"
        self.assertIn("ELM", [r["vendor_id"] for r in suite.oracle(c)])
        self.assertEqual(suite.money("1.005"), "1.01")

    def test_invoice_manual_balances_copies_corrections_and_reversals(self):
        _, c = case("invoice-reconciliation-training")
        rows = suite.oracle(c)
        self.assertEqual([(r["invoice_id"], r["outstanding_sgd"], r["status"]) for r in rows], [("IN-501", "500.00", "OVERDUE"), ("IN-503", "450.00", "OPEN"), ("IN-502", "0.00", "SETTLED"), ("IN-504", "-50.00", "CREDIT_BALANCE")])
        self.assertEqual(rows[0]["gross_sgd"], "1320.00")
        self.assertEqual(rows[0]["paid_sgd"], "700.00")
        self.assertEqual(rows[-1]["paid_sgd"], "0.00")
        for register in c["registers"].values():
            register.extend(copy.deepcopy(register))
        self.assertEqual(suite.oracle(c), rows)

    def test_invoice_evaluation_vendor_key_and_void_credit(self):
        _, c = case("invoice-reconciliation-evaluation")
        rows = suite.oracle(c)
        self.assertEqual([(r["vendor_id"], r["invoice_id"], r["outstanding_sgd"], r["status"]) for r in rows], [("QUARTZ", "IV-8201", "500.00", "OPEN"), ("QUARTZ", "IV-8204", "-30.00", "CREDIT_BALANCE"), ("RIVER", "IV-8202", "0.00", "SETTLED"), ("SABLE", "IV-8201", "490.00", "OVERDUE")])
        c["registers"]["remittances"][0]["amount_sgd"] = "401.00"
        c["registers"]["remittances"][1]["amount_sgd"] = "401.00"
        self.assertEqual(suite.oracle(c)[0]["outstanding_sgd"], "499.00")

    def test_conflicting_duplicate_facts_fail_instead_of_arbitrarily_choosing(self):
        _, c = case("invoice-reconciliation-training")
        c["registers"]["invoices-history"][1]["gross_sgd"] = "999.00"
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            suite.oracle(c)

    def test_release_latest_eligible_revision_date_boundaries_and_missing(self):
        _, c = case("release-package-training")
        self.assertEqual([(r["doc_key"], r["document_id"], r["page"], r["status"]) for r in suite.oracle(c)], [("GUIDE", "OG-102", "2", "READY"), ("LABEL", "CL-301", "1", "READY"), ("SAFETY", "", "", "MISSING"), ("TEST", "VR-201", "1", "READY")])
        _, c = case("release-package-evaluation")
        rows = suite.oracle(c)
        self.assertEqual([(r["doc_key"], r["document_id"], r["status"]) for r in rows], [("GUIDE", "FM-512", "READY"), ("LABEL", "", "MISSING"), ("SAFETY", "HN-843", "READY"), ("TEST", "BC-623", "READY")])
        c["rules"]["as_of"] = "2026-11-20"
        self.assertEqual(suite.oracle(c)[-1]["document_id"], "BC-624")


class MaterialTests(unittest.TestCase):
    def test_six_frozen_cases_three_pairs_and_no_training_answer_reuse(self):
        manifest = json.loads(suite.MANIFEST.read_text())
        csv_cases = [entry for entry in manifest["cases"] if entry["family"] != "workbook"]
        self.assertEqual(len(csv_cases), 8)
        families = {}
        for entry in csv_cases:
            e, c = case(entry["id"])
            families.setdefault(e["family"], {})[e["split"]] = suite.oracle(c)
            self.assertIn(len(e["sources"]), (8,) if e["family"] == "payment-release" else (5, 6))
            for source in e["sources"]:
                self.assertEqual((suite.ROOT / source["path"]).read_bytes(), suite.pdf(suite.documents(c)[source["filename"]]))
            self.assertEqual((suite.ROOT / e["task_path"]).read_text(), suite.task(c))
        self.assertEqual(len(families), 4)
        for pair in families.values():
            self.assertEqual(set(pair), {"training", "evaluation"})
            self.assertNotEqual(pair["training"], pair["evaluation"])

    def test_first_training_original_frozen_bytes(self):
        e, _ = case("landed-cost-training")
        self.assertEqual(e["task_sha256"], "8d146dcfdb66006a6dfe3b0e1a057b072b7d12e309aee285b35c982a051e9af1")
        self.assertEqual(e["oracle"]["fixture_sha256"], "8bf65c956226a98a374060f674e9e30fb8ecf1cb8bf4524af4d93378a91b5b73")
        self.assertEqual({s["filename"]: s["sha256"] for s in e["sources"]}, {
            "rules.pdf": "a2930d406e4a9fd6079574619f34d7476fd7d25890e561ff7d5e744731c79e64",
            "quotes-alder.pdf": "3f46b7a3e72a66a13e67d6e6f5077c31417388f8782eb342ccb2a6d38b815ab8",
            "quotes-birch.pdf": "030a86f54b24d157f372e66b5924347f8b0aed0a9172c8cc335bd26ddaff550b",
            "quotes-cedar.pdf": "00e907b637ed60d34eb27d9454b41b89d6c1aa42c8f8bb7ae856cb003f9fa973",
            "quotes-dogwood.pdf": "0672eedf5c26a7fd56470ca9d6f116da7a67fb8b24f869e67f2adba25ebf94e4"})

    def test_pdf_xref_offsets_pages_and_escaping(self):
        data = suite.pdf([["Text (approved) \\ copy"], ["Second page"]])
        xref = int(data.split(b"startxref\n")[1].splitlines()[0])
        self.assertEqual(data[xref:xref + 4], b"xref")
        table = data[xref:].splitlines()
        count = int(table[1].split()[1])
        for number, row in enumerate(table[3:3 + count - 1], 1):
            offset = int(row[:10])
            self.assertTrue(data[offset:].startswith(f"{number} 0 obj\n".encode()))
        self.assertIn(b"/Count 2", data)
        self.assertIn(b"Text \\(approved\\) \\\\ copy", data)

    def test_build_idempotent_and_frozen_fixture_edit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("cases/suite", "evaluation/suite", "evaluation/fixtures"):
                shutil.copytree(suite.ROOT / folder, root / folder)
            with patch.object(suite, "ROOT", root), patch.object(suite, "FIXTURES", root / "evaluation/suite"), patch.object(suite, "MANIFEST", root / "evaluation/suite/manifest.json"), patch.object(suite.workbook_case, "suite_entries", return_value=[]):
                before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (root / "cases/suite").glob("*/*") if p.is_file()}
                suite.build()
                suite.build()
                self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})
                fixture = root / "evaluation/suite/landed-cost-training/fixture.json"
                c = json.loads(fixture.read_text())
                c["rules"]["quantity"] = 9
                fixture.write_text(json.dumps(c))
                with self.assertRaisesRegex(ValueError, "Frozen case changed"):
                    suite.build()
                with self.assertRaisesRegex(ValueError, "Frozen input changed"):
                    suite.load("landed-cost-training")


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.entry, self.case = case("landed-cost-training")
        self.rows = suite.oracle(self.case)
        self.output = self.entry["output"]

    def test_all_six_oracles_round_trip_and_reverse_row_order(self):
        for entry in json.loads(suite.MANIFEST.read_text())["cases"]:
            if entry["family"] == "workbook":
                continue
            e, c = case(entry["id"])
            rows = suite.oracle(c)
            score = suite.score_csv(payload(list(reversed(rows)), e["output"]), rows, e["output"])
            self.assertTrue(score["csv_correct"], entry["id"])

    def test_false_inclusion_duplicate_and_omission_are_distinct(self):
        score = suite.score_csv(payload(self.rows[:1], self.output), self.rows, self.output)
        self.assertEqual(score["row_accuracy"], 0.5)
        self.assertEqual(score["false_inclusion_count"], 0)
        extra = {**self.rows[0], "vendor_id": "CEDAR"}
        score = suite.score_csv(payload(self.rows + [extra, self.rows[0]], self.output), self.rows, self.output)
        self.assertEqual(score["row_accuracy"], 1)
        self.assertEqual(score["false_inclusion_count"], 2)
        self.assertEqual(score["false_inclusion_rate"], 0.5)
        self.assertFalse(score["csv_correct"])

    def test_wrong_values_and_malformed_numbers_cannot_complete(self):
        for value in ("NaN", "Infinity", "10791.001", "10790.00"):
            rows = copy.deepcopy(self.rows)
            rows[0]["landed_total_sgd"] = value
            self.assertFalse(suite.score_csv(payload(rows, self.output), self.rows, self.output)["csv_correct"])
        for bad in (b"<html>login</html>", b"vendor_id,quote_id\nALDER\n", b"\xff", payload(self.rows, self.output).replace(b"vendor_id", b"wrong_header", 1)):
            self.assertFalse(suite.score_csv(bad, self.rows, self.output)["schema_valid"])

    def test_numeric_format_and_bom_accepted(self):
        self.rows[0]["landed_total_sgd"] = "10791.000"
        self.rows[0]["cpu_cores"] = "032"
        self.rows[1]["budget_remaining_sgd"] = "-0.00"
        self.assertTrue(suite.score_csv(b"\xef\xbb\xbf" + payload(self.rows, self.output), suite.oracle(self.case), self.output)["csv_correct"])


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.entry, self.case = case("landed-cost-training")
        self.body = payload(suite.oracle(self.case), self.entry["output"])
        self.link = "http://localhost:8092/index.php/s/TestToken"

    def request(self, url, data=None, method=None, headers=None):
        if "/ocs/" in url:
            return json.dumps({"ocs": {"meta": {"statuscode": 100}, "data": [{"share_type": 3, "token": "TestToken", "path": "/" + self.entry["remote_dir"] + "/landed-cost.csv"}]}}).encode()
        if url.endswith("landed-cost.csv"):
            return self.body
        if url.endswith("task.md"):
            return (suite.ROOT / self.entry["task_path"]).read_bytes()
        source = next(s for s in self.entry["sources"] if url.endswith(s["filename"]))
        return (suite.ROOT / source["path"]).read_bytes()

    def chat(self, path, data=None, headers=None):
        if path.startswith("groups.info?"):
            return {"group": {"_id": "test-room"}}
        return {"messages": [{"u": {"username": suite.bench.CREDENTIAL}, "msg": self.link}]}

    def test_remote_bytes_anonymous_share_target_and_chat_required(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "landed-cost.csv").write_bytes(self.body)
            (workspace / "link.txt").write_text(self.link)
            for source in self.entry["sources"]:
                shutil.copyfile(suite.ROOT / source["path"], workspace / source["filename"])
            with patch.object(suite.bench, "request", side_effect=self.request), patch.object(suite.bench, "login", return_value={}), patch.object(suite.bench, "rc", side_effect=self.chat), patch.object(suite, "public_download", return_value=self.body) as public:
                result = suite.verify(self.entry, self.case, workspace, 603)
                self.assertEqual(result["completion"], 1)
                self.assertFalse(result["within_time_budget"])
                for source in self.entry["sources"]:
                    path = workspace / source["filename"]
                    for state in ("missing", "corrupt"):
                        with self.subTest(source=source["filename"], state=state):
                            if state == "missing":
                                path.unlink()
                            else:
                                path.write_bytes(b"%PDF-corrupt")
                            result = suite.verify(self.entry, self.case, workspace)
                            self.assertFalse(result["checks"]["local_source:" + source["filename"]])
                            self.assertTrue(result["checks"]["source:" + source["filename"]])
                            self.assertFalse(result["business_checks_passed"])
                            self.assertEqual(result["completion"], 0)
                    shutil.copyfile(suite.ROOT / source["path"], path)
                public.return_value = b"<html>Login</html>"
                result = suite.verify(self.entry, self.case, workspace)
                self.assertEqual(result["completion"], 0)
                self.assertFalse(result["checks"]["anonymous_download_matches"])
                self.assertIsNone(result["within_time_budget"])
                public.return_value = self.body
                with patch.object(suite.bench, "rc", return_value={"group": {"_id": "room"}, "messages": []}):
                    self.assertFalse(suite.verify(self.entry, self.case, workspace)["checks"]["share_posted_in_case_room"])
                def wrong_target(url, data=None, method=None, headers=None):
                    body = self.request(url, data, method, headers)
                    return body.replace(b"landed-cost.csv", b"copied-elsewhere.csv") if "/ocs/" in url else body
                with patch.object(suite.bench, "request", side_effect=wrong_target):
                    result = suite.verify(self.entry, self.case, workspace)
                    self.assertTrue(result["checks"]["anonymous_download_matches"])
                    self.assertFalse(result["checks"]["public_share_targets_output"])
                    self.assertEqual(result["completion"], 0)

    def test_public_download_has_no_credentials_and_rejects_external_redirect(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = self.body
        opener = unittest.mock.Mock()
        opener.open.return_value = response
        with patch.object(suite.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(suite.public_download(self.link), self.body)
        opener.open.assert_called_once_with(self.link + "/download", timeout=30)
        with self.assertRaises(ValueError):
            suite.public_download("https://example.com/s/TestToken")
        with self.assertRaises(ValueError):
            suite.ShareRedirect().redirect_request(None, None, 302, "", {}, "https://example.com/s/TestToken")

    def test_seed_prior_chat_shares_or_folder_never_overwritten(self):
        with patch.object(suite.bench, "login", return_value={}), patch.object(suite.bench, "rc", return_value={"group": {"_id": "old"}}), patch.object(suite.bench, "request") as request:
            with self.assertRaisesRegex(ValueError, "Prior suite chat"):
                suite.seed(self.entry)
            request.assert_not_called()
        for stale_share in (True, False):
            calls = []

            def request(url, data=None, method=None, headers=None):
                calls.append((method, url))
                if "/ocs/" in url:
                    shares = [{"path": "/" + self.entry["remote_dir"] + "/landed-cost.csv"}] if stale_share else []
                    return json.dumps({"ocs": {"meta": {"statuscode": 100}, "data": shares}}).encode()
                if method == "MKCOL":
                    raise http_error(405)
                raise AssertionError("Seed reached a mutation after detecting stale state")

            with patch.object(suite.bench, "login", return_value={}), patch.object(suite.bench, "rc", side_effect=http_error(400, {"errorType": "error-room-not-found"})), patch.object(suite.bench, "request", side_effect=request):
                with self.assertRaises((ValueError, urllib.error.HTTPError)) as failure:
                    suite.seed(self.entry)
                if isinstance(failure.exception, urllib.error.HTTPError):
                    failure.exception.close()
            self.assertNotIn("PUT", [method for method, _ in calls])

    def test_seed_success_uploads_only_public_files_and_static_facts(self):
        uploads, posts = {}, []

        def request(url, data=None, method=None, headers=None):
            if "/ocs/" in url:
                return b'{"ocs":{"meta":{"statuscode":100},"data":[]}}'
            if method == "MKCOL":
                return b""
            if method == "PUT":
                self.assertEqual(headers["If-None-Match"], "*")
                uploads[url] = data
                return b""
            return uploads[url]

        def chat(path, data=None, headers=None):
            if path.startswith("groups.info?"):
                raise http_error(400, {"errorType": "error-room-not-found"})
            posts.append((path, data))
            return {"group": {"_id": "new-room"}}

        with patch.object(suite.bench, "login", return_value={}), patch.object(suite.bench, "rc", side_effect=chat), patch.object(suite.bench, "request", side_effect=request):
            self.assertTrue(suite.seed(self.entry)["seeded"])
        self.assertEqual(len(uploads), 6)
        self.assertTrue(all(url.endswith((".pdf", "/task.md")) for url in uploads))
        self.assertEqual([path for path, _ in posts], ["groups.create", "chat.postMessage"])
        self.assertIn("EXAMINER FIXED FACTS", posts[-1][1]["text"])
        self.assertNotIn("10791.00", posts[-1][1]["text"])


if __name__ == "__main__":
    unittest.main()
