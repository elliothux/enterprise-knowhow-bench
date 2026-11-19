#!/usr/bin/env python3
"""Standalone offline workbook fixture/examiner; never imports the active runner.

Only explicit `grade --recalculate` starts LibreOffice. Workbook writes here are
examiner-only: blank source fixtures and copies for input perturbation, never a
participant's business solution. No service calls, seed/reset, model or CUA.
"""
import argparse
import copy
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases/workbook"
EVAL = ROOT / "evaluation/workbook"
SOFFICE = Path(os.environ.get("SOFFICE", "/Applications/LibreOffice.app/Contents/MacOS/soffice"))
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
HEADERS = {
    "Stock": ["sku", "location", "on_hand", "reserved"],
    "Inbound": ["sku", "quantity", "status", "eta"],
    "Plan": ["sku", "target_units", "pack_size", "available",
             "confirmed_due_inbound", "net_available", "reorder_units"],
}
MAX_ZIP = 8 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024
# Pure spreadsheet operations only; broaden after review if an equivalent needs it.
FUNCTIONS = {"SUM", "SUMIF", "SUMIFS", "SUMPRODUCT", "IF", "IFS", "IFERROR",
             "AND", "OR", "NOT", "MAX", "MIN", "ROUNDUP", "ROUND", "INT",
             "MOD", "ABS", "CEILING", "CEILING.MATH", "CEILING.PRECISE",
             "EXACT", "VALUE", "TEXT", "DATE", "DATEVALUE", "COUNTIF", "COUNTIFS",
             "CONCATENATE", "CONCAT", "LEN", "LEFT", "RIGHT", "MID", "TRIM",
             "CLEAN", "SUBSTITUTE", "REPLACE", "FIND", "SEARCH", "UPPER", "LOWER",
             "INDEX", "MATCH", "XMATCH", "LOOKUP", "VLOOKUP", "HLOOKUP", "XLOOKUP",
             "FILTER", "QUOTIENT", "FLOOR", "FLOOR.MATH", "FLOOR.PRECISE", "TRUNC",
             "ROUNDDOWN", "IFNA", "ISNUMBER", "ISTEXT", "ISERROR", "ISBLANK",
             "CHOOSE", "COUNT", "COUNTA", "ROWS", "COLUMNS", "ROW", "COLUMN",
             "LET", "TRUE", "FALSE", "N", "T"}
FORBIDDEN_FUNCTIONS = {"WEBSERVICE", "HYPERLINK", "RTD", "CALL", "REGISTER.ID",
                       "EXEC", "RUN", "SQL.REQUEST", "IMAGE", "IMPORTXML", "IMPORTRANGE"}


class EvaluatorIncompatible(ValueError):
    """Requires examiner review; must not count as a participant business failure."""


class ExaminerError(ValueError):
    """Engine/environment failure, not a participant business failure."""


@dataclass
class Cell:
    value: object = None
    formula: str | None = None


@dataclass
class Workbook:
    sheets: dict
    parts: dict
    sheet_paths: dict
    date1904: bool = False
    raw: bytes = b""


def tag(name):
    return f"{{{NS}}}{name}"


def xml(data):
    # Reject declarations even with UTF-16 interleaving before ElementTree parses.
    upper = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DTD/entities forbidden")
    return ET.fromstring(data)


def safe_formula(formula):
    bare = re.sub(r'"(?:[^"]|"")*"', '""', formula)
    if (any(c in bare for c in "|\\") or re.search(r"https?:|file:|dde", bare, re.I)
            or re.search(r"\[[^]]+\][^!]*!", bare)):
        raise ValueError("External/unsafe formula reference")
    if "[" in bare or "]" in bare:
        raise EvaluatorIncompatible("Structured/bracketed references need examiner review")
    functions = re.findall(r"([A-Za-z_][A-Za-z_0-9.]*)\s*\(", bare)
    for name in functions:
        pure = name.upper().removeprefix("_XLFN.").removeprefix("_XLWS.")
        if pure in FORBIDDEN_FUNCTIONS:
            raise ValueError(f"Active/external formula function: {name}")
        if pure not in FUNCTIONS:
            raise EvaluatorIncompatible(f"Formula function needs examiner review: {name}")


def read_workbook(path):
    """Bounded, non-extracting OOXML reader; reject active/external content first."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ZIP:
        raise ValueError("Workbook must be a regular, bounded .xlsx file")
    with path.open("rb") as stream:
        raw_book = stream.read(MAX_ZIP + 1)
    if len(raw_book) > MAX_ZIP:
        raise ValueError("Oversized workbook")
    with zipfile.ZipFile(io.BytesIO(raw_book)) as archive:
        infos = archive.infolist()
        if len(infos) > 512 or sum(i.file_size for i in infos) > MAX_EXPANDED:
            raise ValueError("Oversized ZIP")
        names = [i.filename for i in infos]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP paths")
        for i in infos:
            p = PurePosixPath(i.filename)
            if (p.is_absolute() or ".." in p.parts or "\\" in i.filename or
                    ":" in i.filename or str(p) != i.filename or
                    i.flag_bits & 1 or (i.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("Unsafe ZIP path/member")
            if i.file_size > 4 * 1024 * 1024 or i.file_size > max(4096, i.compress_size * 200):
                raise ValueError("Oversized ZIP member")
            lower = i.filename.lower()
            if (lower.endswith((".bin", ".vba", ".exe")) or any(s in lower for s in
                    ("externallinks/", "embeddings/", "activex/", "connections", "querytables/"))):
                raise ValueError("Active/external workbook content")
        parts = {i.filename: archive.read(i) for i in infos}
    trees = {name: xml(data) for name, data in parts.items()
             if name.endswith((".xml", ".rels"))}
    for name, tree in trees.items():
        if name.endswith(".rels"):
            for rel in tree:
                target = rel.get("Target", "")
                if (rel.get("TargetMode", "").lower() == "external" or
                        ":" in target or "\\" in target or ".." in PurePosixPath(target).parts):
                    raise ValueError("External/unsafe relationship")
        for node in tree.iter():
            if node.tag == tag("f"):
                safe_formula(node.text or "")
    types = parts.get("[Content_Types].xml", b"").lower()
    if b"macroenabled" in types or b"vba" in types:
        raise ValueError("Macros forbidden")
    book = trees["xl/workbook.xml"]
    if book.find(tag("definedNames")) is not None:
        # shortcut: named expressions are rejected, review if native export needs them.
        raise EvaluatorIncompatible("Defined names need examiner review")
    props = book.find(tag("workbookPr"))
    epoch = props is not None and props.get("date1904", "0").lower() in ("1", "true")
    rels = {r.get("Id"): r for r in trees["xl/_rels/workbook.xml.rels"]}
    strings = []
    if "xl/sharedStrings.xml" in trees:
        strings = ["".join(t.text or "" for t in si.iter(tag("t")))
                   for si in trees["xl/sharedStrings.xml"]]
    sheets, paths = {}, {}
    for sheet in book.find(tag("sheets")):
        name = sheet.get("name")
        if name in sheets:
            raise ValueError("Duplicate sheet")
        rel = rels[sheet.get(f"{{{REL}}}id")]
        if not rel.get("Type", "").endswith("/worksheet"):
            raise ValueError("Non-worksheet sheet")
        target = rel.get("Target", "")
        part = target.lstrip("/") if target.startswith("/") else "xl/" + target
        paths[name] = part
        grid = {}
        shared = {f.get("si"): f.text for f in trees[part].iter(tag("f"))
                  if f.get("t") == "shared" and f.text}
        for node in trees[part].iter(tag("c")):
            addr = node.get("r", "")
            if not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]{0,6}", addr) or addr in grid:
                raise ValueError("Invalid/duplicate cell address")
            f, v = node.find(tag("f")), node.find(tag("v"))
            formula = None if f is None else (f.text or shared.get(f.get("si")))
            scalar_array = f is not None and f.get("t") == "array" and f.get("ref") == addr
            if f is not None and ((f.get("t") not in (None, "normal", "shared") and not scalar_array) or not formula):
                raise EvaluatorIncompatible("Invalid/shared or array formula needs examiner review")
            kind = node.get("t", "n")
            raw = v.text if v is not None else None
            if kind == "inlineStr":
                value = "".join(t.text or "" for t in node.iter(tag("t")))
            elif kind == "s" and raw is not None:
                index = int(raw)
                if not 0 <= index < len(strings):
                    raise ValueError("Invalid shared string index")
                value = strings[index]
            elif kind == "d" and raw:
                value = date.fromisoformat(raw[:10])
            elif kind in ("n", "") and raw is not None:
                value = Decimal(raw)
                if not value.is_finite():
                    raise ValueError("Non-finite number")
            else:
                value = raw  # Errors/bools/text cannot pass a numeric result check.
            grid[addr] = Cell(value, formula)
        sheets[name] = grid
    return Workbook(sheets, parts, paths, epoch, raw_book)


def serial(day, epoch=False):
    day = date.fromisoformat(day) if isinstance(day, str) else day
    return Decimal((day - date(1904, 1, 1) if epoch else day - date(1899, 12, 30)).days)


def load_case(split):
    if split not in ("training", "evaluation"):
        raise ValueError("Unknown split")
    case = json.loads((EVAL / f"{split}.json").read_text())
    roster = [r[0] for r in case["plan"]]
    if len(roster) != (6 if split == "training" else 8) or len(set(roster)) != len(roster):
        raise ValueError("Invalid roster")
    for sku, target, pack in case["plan"]:
        if not isinstance(sku, str) or not sku or target < 0 or pack <= 0:
            raise ValueError("Invalid plan parameters")
    date.fromisoformat(case["as_of"])
    date.fromisoformat(case["cutoff"])
    for sku, location, on_hand, reserved in case["stock"]:
        if sku not in roster or not location or on_hand < 0 or reserved < 0:
            raise ValueError("Invalid stock fixture")
    for sku, qty, status, eta in case["inbound"]:
        if sku not in roster or qty < 0 or status not in ("CONFIRMED", "PENDING", "CANCELLED"):
            raise ValueError("Invalid inbound fixture")
        date.fromisoformat(eta)
    return case


def inputs(case):
    grids = {}
    for sheet, headers in HEADERS.items():
        grid = {f"{chr(65+i)}1": v for i, v in enumerate(headers)}
        for r, row in enumerate(case[sheet.lower()], 2):
            for col, value in enumerate(row):
                grid[f"{chr(65+col)}{r}"] = (date.fromisoformat(value)
                    if sheet == "Inbound" and col == 3 else value)
        grids[sheet] = grid
    grids["Plan"].update({"J1": "as_of", "K1": date.fromisoformat(case["as_of"]),
                           "J2": "cutoff", "K2": date.fromisoformat(case["cutoff"])})
    return grids


def oracle(case):
    """Decimal arithmetic from examiner inputs, independent of submitted cells."""
    result = {}
    for row, (sku, target, pack) in enumerate(case["plan"], 2):
        available = sum((Decimal(h) - Decimal(r) for s, _, h, r in case["stock"]
                         if s == sku), Decimal(0))
        inbound = sum((Decimal(q) for s, q, status, eta in case["inbound"]
                       if s == sku and status == "CONFIRMED" and eta <= case["cutoff"]), Decimal(0))
        net = available + inbound
        packs = ((Decimal(target) - net) / Decimal(pack)).to_integral_value(rounding=ROUND_CEILING)
        reorder = max(Decimal(0), packs * Decimal(pack))
        result.update({f"{col}{row}": v for col, v in zip("DEFG", (available, inbound, net, reorder))})
    return result


def write_zip(parts, destination):
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(parts.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def cell_xml(parent, addr, value, epoch=False):
    node = ET.SubElement(parent, tag("c"), r=addr)
    if isinstance(value, str):
        node.set("t", "inlineStr")
        ET.SubElement(ET.SubElement(node, tag("is")), tag("t")).text = value
    else:
        if isinstance(value, date):
            node.set("s", "1")
            value = serial(value, epoch)
        ET.SubElement(node, tag("v")).text = str(value)
    return node


def template_bytes(case):
    """Examiner fixture only. No output values or formulas are included."""
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    types += '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    types += '<Default Extension="xml" ContentType="application/xml"/>'
    for part, kind in [("workbook.xml", "sheet.main"), ("styles.xml", "styles"),
                       *[(f"worksheets/sheet{i}.xml", "worksheet") for i in range(1, 4)]]:
        types += f'<Override PartName="/xl/{part}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.{kind}+xml"/>'
    parts = {"[Content_Types].xml": (types + '</Types>').encode(),
             "_rels/.rels": f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>'.encode()}
    book = ET.Element(tag("workbook"))
    sheets = ET.SubElement(book, tag("sheets"))
    relationships = ET.Element(f"{{{PKG}}}Relationships")
    for i, (name, grid) in enumerate(inputs(case).items(), 1):
        ET.SubElement(sheets, tag("sheet"), name=name, sheetId=str(i), **{f"{{{REL}}}id": f"rId{i}"})
        ET.SubElement(relationships, f"{{{PKG}}}Relationship", Id=f"rId{i}", Type=f"{REL}/worksheet", Target=f"worksheets/sheet{i}.xml")
        tree = ET.Element(tag("worksheet"))
        data = ET.SubElement(tree, tag("sheetData"))
        rows = {}
        for addr, value in grid.items():
            row = int(re.search(r"\d+", addr)[0])
            rows.setdefault(row, []).append((addr, value))
        for row, cells in sorted(rows.items()):
            parent = ET.SubElement(data, tag("row"), r=str(row))
            for addr, value in sorted(cells, key=lambda c: (len(re.sub(r"\d", "", c[0])), c[0])):
                cell_xml(parent, addr, value)
        parts[f"xl/worksheets/sheet{i}.xml"] = ET.tostring(tree)
    ET.SubElement(relationships, f"{{{PKG}}}Relationship", Id="rId4", Type=f"{REL}/styles", Target="styles.xml")
    ET.SubElement(book, tag("calcPr"), calcId="0", fullCalcOnLoad="1", forceFullCalc="1", calcMode="auto")
    parts["xl/workbook.xml"] = ET.tostring(book)
    parts["xl/_rels/workbook.xml.rels"] = ET.tostring(relationships)
    parts["xl/styles.xml"] = f'''<styleSheet xmlns="{NS}">
      <numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy-mm-dd"/></numFmts>
      <fonts count="1"><font><sz val="11"/><name val="Arial"/></font></fonts>
      <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
      <borders count="1"><border/></borders>
      <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
      <cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>
      <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
    </styleSheet>'''.encode()
    stream = io.BytesIO()
    write_zip(parts, stream)
    return stream.getvalue()


def suite_entries():
    """Freeze public workbook inputs using the existing suite manifest shape."""
    entries = []
    for split in ("training", "evaluation"):
        case = load_case(split)
        paths = [CASES / split / "task.md", CASES / split / "template.xlsx", EVAL / f"{split}.json"]
        hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        freeze = EVAL / f"{split}.freeze.json"
        record = {"schema_version": 1, "case_id": case["id"], "sha256": hashes}
        if freeze.exists():
            if json.loads(freeze.read_text()) != record:
                raise ValueError("Frozen workbook inputs changed; create a new case version")
        else:
            freeze.write_text(json.dumps(record, indent=2) + "\n")
        task, source, fixture = (str(p.relative_to(ROOT)) for p in paths)
        entries.append({"id": case["id"], "family": "workbook", "split": split,
            "task_path": task, "task_sha256": hashes[task],
            "freeze_path": str(freeze.relative_to(ROOT)),
            "remote_dir": "Documents/Benchmark Suite/" + case["id"], "room_name": case["id"],
            "sources": [{"path": source, "filename": "template.xlsx", "sha256": hashes[source], "bytes": paths[1].stat().st_size}],
            "output": {"kind": "workbook", "filename": "replenishment.xlsx", "link_filename": "link.txt"},
            "time_budget_seconds": case["time_budget_seconds"],
            "oracle": {"algorithm": "workbook-v1", "fixture_path": fixture, "fixture_sha256": hashes[fixture]},
            "npc_policy": {"mode": "location_only", "facts": ["Use the assigned task.md and template.xlsx. No extra facts or computed answers are supplied."]}})
    return entries


def initial_scores(book, case):
    expected = oracle(case)
    cells = book.sheets.get("Plan", {})
    correct = {addr for addr, value in expected.items()
               if isinstance(cells.get(addr, Cell()).value, Decimal) and cells[addr].value == value}
    rows = len(case["plan"])
    correct_rows = sum(all(f"{col}{row}" in correct for col in "DEFG") for row in range(2, rows + 2))
    return {"expected_cells": len(expected), "correct_initial_cells": len(correct),
            "formula_cells": sum(bool(cells.get(addr, Cell()).formula) for addr in expected),
            "expected_rows": rows, "correct_rows": correct_rows, "row_accuracy": correct_rows / rows}


def check_workbook(book, case):
    errors = []
    expected = inputs(case)
    results = oracle(case)
    if set(book.sheets) != set(expected):
        return ["Sheet names must be exactly Stock, Inbound, Plan"]
    for sheet, grid in expected.items():
        actual = book.sheets[sheet]
        for addr, value in grid.items():
            cell = actual.get(addr, Cell())
            if isinstance(value, date) and isinstance(cell.value, Decimal):
                value = serial(value, book.date1904)
            if cell.formula is not None or type(cell.value) is bool or cell.value != value:
                errors.append(f"Input changed: {sheet}!{addr}")
        allowed = set(grid) | (set(results) if sheet == "Plan" else set())
        for addr, cell in actual.items():
            if addr not in allowed and (cell.value not in (None, "") or cell.formula is not None):
                errors.append(f"Unexpected content: {sheet}!{addr}")
    for addr, value in results.items():
        cell = book.sheets["Plan"].get(addr, Cell())
        if not cell.formula:
            errors.append(f"Formula missing: Plan!{addr}")
        if not isinstance(cell.value, Decimal) or cell.value != value:
            errors.append(f"Result incorrect/missing: Plan!{addr}; expected {value}, got {cell.value}")
    return errors


def perturbations(case):
    """Independent probes, always starting from the submitted original."""
    stock = copy.deepcopy(case)
    for i, row in enumerate(stock["stock"]):
        row[2], row[3] = row[2] + 17 + i * 3, row[3] + 2 + i
    yield "stock-balances", stock
    quantities = copy.deepcopy(case)
    for i, row in enumerate(quantities["inbound"]):
        row[1] += 13 + i
    yield "inbound-quantities", quantities
    eligibility = copy.deepcopy(case)
    for i, row in enumerate(eligibility["inbound"]):
        row[2] = "CANCELLED" if row[2] == "CONFIRMED" else "CONFIRMED"
        row[3] = (date.fromisoformat(case["cutoff"]) + timedelta(days=i % 3 - 1)).isoformat()
    yield "status-and-eta", eligibility
    for delta in (-3, 7):
        changed = copy.deepcopy(case)
        changed["cutoff"] = (date.fromisoformat(case["cutoff"]) + timedelta(days=delta)).isoformat()
        yield f"cutoff-{delta}", changed
    parameters = copy.deepcopy(case)
    for i, row in enumerate(parameters["plan"]):
        row[1], row[2] = row[1] + 73 + i, row[2] + 3 + i
    yield "targets-and-packs", parameters
    keys = copy.deepcopy(case)
    skus = [r[0] for r in case["plan"]]
    mapping = dict(zip(skus, skus[1:] + skus[:1]))
    for row in keys["stock"] + keys["inbound"]:
        row[0] = mapping[row[0]]
    yield "source-sku-rotation", keys


def rewrite_inputs(book, case, destination):
    """Examiner copy only; keep formulas, replace inputs, discard formula caches."""
    parts = dict(book.parts)
    for sheet, grid in inputs(case).items():
        tree = xml(parts[book.sheet_paths[sheet]])
        for node in tree.iter(tag("c")):
            addr = node.get("r")
            if addr in grid:
                attrs = dict(node.attrib)
                node.clear()
                node.attrib.update({k: v for k, v in attrs.items() if k != "t"})
                container = ET.Element("temp")
                new = cell_xml(container, addr, grid[addr], book.date1904)
                if isinstance(grid[addr], date) and "s" in attrs:
                    new.set("s", attrs["s"])
                node.attrib.update(new.attrib)
                node.extend(list(new))
            elif node.find(tag("f")) is not None:
                node.attrib.pop("t", None)
                for cache in list(node.findall(tag("v"))):
                    node.remove(cache)
        parts[book.sheet_paths[sheet]] = ET.tostring(tree)
    tree = xml(parts["xl/workbook.xml"])
    calc = tree.find(tag("calcPr"))
    if calc is None:
        calc = ET.SubElement(tree, tag("calcPr"))
    calc.attrib.update(calcMode="auto", fullCalcOnLoad="1", forceFullCalc="1", calcId="0")
    parts["xl/workbook.xml"] = ET.tostring(tree)
    # A stale calculation chain must not override forced recalculation.
    parts.pop("xl/calcChain.xml", None)
    for name in ("xl/_rels/workbook.xml.rels", "[Content_Types].xml"):
        tree = xml(parts[name])
        for node in list(tree):
            if "calcchain" in str(node.attrib).lower():
                tree.remove(node)
        parts[name] = ET.tostring(tree)
    write_zip(parts, destination)


def recalculate(source, directory, soffice=SOFFICE):
    """Explicit examiner operation. Fresh profile/output, failure evidence retained."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    profile, output = directory / "profile", directory / "output"
    (profile / "user").mkdir(parents=True)
    output.mkdir()
    # Defense in depth: archive/formula screening happens before this function.
    (profile / "user/registrymodifications.xcu").write_text('''<?xml version="1.0"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item>
</oor:items>''')
    read_workbook(source)  # Do not launch an engine for an unscreened archive.
    command = [str(soffice), f"-env:UserInstallation={profile.as_uri()}", "--headless",
               "--nologo", "--nodefault", "--nofirststartwizard", "--norestore",
               "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", str(output), str(Path(source).resolve())]
    (directory / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
    except OSError as error:
        (directory / "stdout.log").write_bytes(b"")
        (directory / "stderr.log").write_text(str(error))
        (directory / "failure.txt").write_text(str(error))
        raise ExaminerError(f"Recalculation failed; logs: {directory}") from error
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
    (directory / "stdout.log").write_bytes(stdout)
    (directory / "stderr.log").write_bytes(stderr)
    result = output / Path(source).name
    if timed_out or process.returncode or not result.is_file():
        (directory / "failure.txt").write_text(f"Timeout: {timed_out}; exit {process.returncode}; output present: {result.is_file()}")
        raise ExaminerError(f"Recalculation failed; logs: {directory}")
    return result


def grade(split, submission, artifacts, run_engine=False):
    artifacts = Path(artifacts)
    artifacts.mkdir(parents=True, exist_ok=False)
    report = {"split": split, "status": "failed", "workbook_pass": False,
              "delivery": "not_checked", "native_cua": "trace_review_required", "checks": {}}
    try:
        case = load_case(split)
        book = read_workbook(submission)
        report["scores"] = initial_scores(book, case)
        data = book.raw
        report["submission_sha256"] = hashlib.sha256(data).hexdigest()
        original = artifacts / "submitted.xlsx"
        original.write_bytes(data)
        report["checks"]["original"] = check_workbook(book, case)
        if report["checks"]["original"]:
            return report
        if not run_engine:
            report["status"] = "pending_recalculation"
            return report
        for name, changed in [("baseline", case), *perturbations(case)]:
            source_dir = artifacts / name
            source_dir.mkdir()
            source = source_dir / "probe.xlsx"
            rewrite_inputs(book, changed, source)
            output = recalculate(source, source_dir / "engine")
            report["checks"][name] = check_workbook(read_workbook(output), changed)
        report["workbook_pass"] = not any(report["checks"].values())
        report["status"] = "workbook_pass" if report["workbook_pass"] else "failed"
    except EvaluatorIncompatible as error:
        report["status"] = "evaluator_incompatible"
        report["error"] = str(error)
    except ExaminerError as error:
        report["status"] = "examiner_error"
        report["error"] = str(error)
    except (OSError, ValueError, KeyError, TypeError, ArithmeticError, zipfile.BadZipFile, ET.ParseError) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        (artifacts / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Create only blank source templates; no app execution")
    build.add_argument("--split", choices=("training", "evaluation"), required=True)
    evaluate = sub.add_parser("grade", help="Static checks by default; never a trial")
    evaluate.add_argument("--split", choices=("training", "evaluation"), required=True)
    evaluate.add_argument("--submission", type=Path, required=True)
    evaluate.add_argument("--artifacts", type=Path, required=True, help="New directory, must not exist")
    evaluate.add_argument("--recalculate", action="store_true", help="Explicit opt-in: START isolated headless LibreOffice")
    args = parser.parse_args()
    if args.command == "build":
        path = CASES / args.split / "template.xlsx"
        with path.open("xb") as stream:
            stream.write(template_bytes(load_case(args.split)))
        print(path)
        return 0
    report = grade(args.split, args.submission, args.artifacts, args.recalculate)
    print(json.dumps(report, indent=2))
    return 0 if report["workbook_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
