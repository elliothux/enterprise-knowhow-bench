#!/usr/bin/env python3
"""Examiner-only business checks against the actual seed; never give this to an agent."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

import services as bench


def expected_quotes(oracle):
    requirements = oracle["requirements"]
    return {row["name"].casefold(): Decimal(row["price"]) for row in oracle["suppliers"]
            if all(Decimal(str(row[key])) >= Decimal(str(value))
                   for key, value in requirements.items())}


def check_csv(payload, expected):
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != ["name", "price"]:
            return False
        actual = {}
        for row in reader:
            if set(row) != {"name", "price"} or not all(row.values()):
                return False
            name = row["name"].strip().casefold()
            price = Decimal(row["price"].strip())
            if name in actual or not price.is_finite():
                return False
            actual[name] = price
        return actual == expected
    except (UnicodeError, csv.Error, InvalidOperation, ValueError):
        return False


class LocalShareRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not bench.valid_share_url(newurl):
            raise ValueError("Share redirected outside the allowed local share endpoint")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_download(link):
    if not bench.valid_share_url(link):
        raise ValueError("Invalid public share URL")
    link = link.rstrip("/")
    url = link if link.endswith("/download") else link + "/download"
    # No cookies or Authorization header: this check must be genuinely anonymous.
    with urllib.request.build_opener(LocalShareRedirect()).open(url, timeout=30) as response:
        content = response.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise ValueError("CSV share is unexpectedly larger than 1 MiB")
        return content


def verify(workspace, oracle_path=None):
    oracle_path = oracle_path or bench.ROOT / "evaluation/vendor-quote.json"
    oracle = json.loads(oracle_path.read_text())
    checks, evidence = {}, {}
    for row in oracle["suppliers"]:
        path = workspace / row["filename"]
        checks["pdf:" + row["filename"]] = path.is_file() and hashlib.sha256(
            path.read_bytes()).hexdigest() == row["sha256"]
    local_path = workspace / "valid-quotes.csv"
    local = local_path.read_bytes() if local_path.is_file() else b""
    checks["csv_correct"] = check_csv(local, expected_quotes(oracle))
    remote_path = urllib.parse.quote("Documents/Administrative Specialist/valid-quotes.csv")
    try:
        remote = bench.request(bench.OC + "/remote.php/webdav/" + remote_path, headers=bench.oc_headers())
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        remote = b""
    checks["uploaded_csv_matches"] = bool(local) and remote == local
    link_path = workspace / "link.txt"
    link = link_path.read_text().strip() if link_path.is_file() else ""
    checks["public_link_format"] = bench.valid_share_url(link)
    checks["anonymous_download_matches"] = False
    if checks["public_link_format"]:
        try:
            checks["anonymous_download_matches"] = bool(local) and public_download(link) == local
        except urllib.error.HTTPError as error:
            if error.code not in (401, 403, 404):
                raise
            evidence["public_download_http_status"] = error.code
    auth = bench.login()
    for username in ("emma_lewis", "sarah_johnson"):
        room = bench.rc("im.create", {"username": username}, auth)["room"]["rid"]
        messages = bench.rc("im.history?" + urllib.parse.urlencode({"roomId": room, "count": 100}),
                            headers=auth)["messages"]
        senders = {m.get("u", {}).get("username") for m in messages if m.get("msg")}
        checks["conversation:" + username] = {bench.CREDENTIAL, username} <= senders
        evidence[username] = [{"username": m.get("u", {}).get("username"), "text": m.get("msg"),
                               "timestamp": m.get("ts")} for m in reversed(messages)]
    return {"kind": "independent_business_verification", "business_checks_passed": all(checks.values()),
            "checks": checks, "evidence": evidence, "oracle_sha256": hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
            "upstream_oracle_matches_actual_seed": False,
            "protocol_audit": "required separately: inspect native CUA calls, allowed local writes and NPC requirement replies"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=bench.ROOT / "workspace")
    parser.add_argument("--oracle", type=Path, default=bench.ROOT / "evaluation/vendor-quote.json")
    parser.add_argument("--output", type=Path, default=bench.ROOT / "artifacts/business-verification.json")
    args = parser.parse_args()
    try:
        result = verify(args.workspace, args.oracle)
    except (OSError, ValueError, KeyError) as error:
        result = {"kind": "independent_business_verification", "business_checks_passed": False,
                  "infrastructure_error": str(error)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "evidence"}, indent=2))
    return 0 if result["business_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
