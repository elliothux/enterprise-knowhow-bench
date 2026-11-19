import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from benchmark import services as bench, verify_case


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.oracle = json.loads((bench.ROOT / "evaluation/vendor-quote.json").read_text())
        self.expected = verify_case.expected_quotes(self.oracle)

    def test_actual_pdf_requirements_not_upstream_gold(self):
        self.assertEqual(set(self.expected), {"cloudtech industries", "techpro solutions"})
        wrong = b"name,price\nNetSys Corporation,12199.99\nDataCore Enterprise,11999.99\n"
        self.assertFalse(verify_case.check_csv(wrong, self.expected))

    def test_row_order_and_decimal_format_do_not_change_business_result(self):
        payload = b"name,price\nTechPro Solutions,12499.990\nCloudTech Industries,12799.99\n"
        self.assertTrue(verify_case.check_csv(payload, self.expected))
        for bad in (payload + b"TechPro Solutions,12499.99\n",
                    payload.replace(b"12499.990", b"12499.98"),
                    payload.replace(b"12499.990", b"NaN"),
                    payload.replace(b"name,price", b"name,price,extra"),
                    b"name,price\n", b"<html>Login</html>"):
            self.assertFalse(verify_case.check_csv(bad, self.expected))

    def test_local_share_boundary(self):
        for good in ("http://localhost:8092/index.php/s/Abc123", "http://127.0.0.1:8092/s/xyz/download",
                     "http://localhost:8092/index.php/s/abc/"):
            self.assertTrue(bench.valid_share_url(good))
        for bad in ("http://localhost:8092/index.php/s/abc;touch /tmp/x", "http://example.com/s/abc",
                    "http://localhost:8092/index.php/s/abc\nextra", "http://localhost:8092/index.php/s/abc?x=1",
                    "http://user@localhost:8092/s/abc", "http://localhost:8092/remote.php/webdav/file"):
            self.assertFalse(bench.valid_share_url(bad))

    def test_complete_delivery_requires_remote_bytes_and_both_real_replies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            (root / "evaluation").mkdir()
            for row in self.oracle["suppliers"]:
                content = b"%PDF-fixture:" + row["filename"].encode()
                (workspace / row["filename"]).write_bytes(content)
                row["sha256"] = hashlib.sha256(content).hexdigest()
            (root / "evaluation/vendor-quote.json").write_text(json.dumps(self.oracle))
            payload = b"name,price\nCloudTech Industries,12799.99\nTechPro Solutions,12499.99\n"
            (workspace / "valid-quotes.csv").write_bytes(payload)
            (workspace / "link.txt").write_text("http://localhost:8092/index.php/s/abc\n")

            def chat(path, data=None, headers=None):
                if path == "im.create":
                    return {"room": {"rid": data["username"]}}
                username = "emma_lewis" if "emma_lewis" in path else "sarah_johnson"
                return {"messages": [{"u": {"username": name}, "msg": "fixture"}
                                     for name in (bench.CREDENTIAL, username)]}

            with patch.object(bench, "ROOT", root), patch.object(bench, "login", return_value={}), \
                    patch.object(bench, "rc", side_effect=chat), \
                    patch.object(bench, "request", return_value=payload), \
                    patch.object(verify_case, "public_download", return_value=payload) as public:
                self.assertTrue(verify_case.verify(workspace)["business_checks_passed"])
                public.return_value = b"<html>Login</html>"
                result = verify_case.verify(workspace)
                self.assertFalse(result["business_checks_passed"])
                self.assertFalse(result["checks"]["anonymous_download_matches"])


if __name__ == "__main__":
    unittest.main()
