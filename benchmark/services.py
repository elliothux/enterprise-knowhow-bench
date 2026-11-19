"""Local ownCloud and Rocket.Chat access for the original task suite."""
import base64
import json
import re
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RC="http://127.0.0.1:13000"
OC="http://127.0.0.1:8092"
CREDENTIAL="theagentcompany"


def request(url, data=None, method=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def rc(path, data=None, headers=None):
    headers = {"Content-Type": "application/json", **(headers or {})}
    body = None if data is None else json.dumps(data).encode()
    return json.loads(request(RC + "/api/v1/" + path, body, headers=headers))


def login():
    result = rc("login", {"user": CREDENTIAL, "password": CREDENTIAL})
    if result.get("status") != "success":
        raise RuntimeError("RocketChat login failed")
    return {"X-Auth-Token": result["data"]["authToken"], "X-User-Id": result["data"]["userId"]}


def oc_headers():
    return {"Authorization": "Basic " + base64.b64encode(
        f"{CREDENTIAL}:{CREDENTIAL}".encode()).decode()}


def valid_share_url(value):
    return bool(re.fullmatch(r"http://(?:localhost|127\.0\.0\.1):8092/(?:index\.php/)?s/[A-Za-z0-9]+(?:/download)?/?", value))
