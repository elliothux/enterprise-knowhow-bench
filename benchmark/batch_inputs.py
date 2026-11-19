"""Freeze the files and configuration used by a scheduled benchmark batch."""
import hashlib
import json
import platform
import re
import shutil
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(rows, tasks):
    if not isinstance(rows, list) or not rows:
        raise ValueError("A schedule must contain at least one case.")
    seen = set()
    for row in rows:
        case = row["case"]
        if case not in tasks or not re.fullmatch(r"[A-Za-z0-9_-]+", case) or case in seen:
            raise ValueError(f"Unknown, duplicate or invalid scheduled case: {case}")
        if row["order"] not in ("AB", "BA") or not set("AB") <= tasks[case]["arms"].keys():
            raise ValueError(f"Invalid paired conditions for {case}")
        if row.get("control") and row["control"] not in set(tasks[case]["arms"]) - set("AB"):
            raise ValueError(f"Unavailable control for {case}")
        if not row.get("family"):
            raise ValueError(f"Missing case family for {case}")
        seen.add(case)


def freeze(root, repository, tasks, rows):
    inputs = {"tasks/manifest.json", "bench.py", "mock/seed.py", "compose.yaml"}
    inputs.update(p.relative_to(repository).as_posix() for p in (repository / "benchmark").glob("*.py"))
    for row in rows:
        task = tasks[row["case"]]
        inputs.update([task["prompt"], *task["resources"].values(), *filter(None, task["arms"].values())])
        inputs.update(task.get("images", []))
        if "ledger" in task:
            inputs.add(task["ledger"])
        if "fixtures" in task:
            inputs.update(p.relative_to(repository).as_posix() for p in (repository / task["fixtures"]).iterdir() if p.is_file())
        key = "historical-answers.json" if task["group"] == "historical" else "answer-key.json"
        inputs.add("evaluation/" + key)
    hashes = {name: digest(repository / name) for name in sorted(inputs)}
    plan_hash = digest(root / "batch.json")
    file = root / "freeze.json"
    if file.exists():
        previous = json.loads(file.read_text())
        if previous["files"] != hashes or previous["plan_sha256"] != plan_hash:
            raise ValueError("Inputs or schedule changed since the batch was frozen.")
        for name, value in hashes.items():
            if digest(root / "frozen" / name) != value:
                raise ValueError(f"Frozen batch input changed: {name}")
        return
    if any((root / row["case"]).exists() for row in rows):
        # Pre-freeze releases can finish a run but cannot claim retrospective provenance.
        return
    for name in hashes:
        target = root / "frozen" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / name, target)
        if digest(target) != hashes[name]:
            raise ValueError(f"Input changed during freeze: {name}")
    info = dict(os=platform.platform(), architecture=platform.machine(), python=platform.python_version())
    pending = file.with_suffix(".tmp")
    pending.write_text(json.dumps(dict(plan_sha256=plan_hash, environment=info, files=hashes), indent=2) + "\n")
    pending.replace(file)
