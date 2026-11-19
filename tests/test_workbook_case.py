"""Offline only: engine orchestration is mocked; never launch an app or subprocess."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET
import zipfile

from benchmark import workbook_case as wb


class WorkbookTests(unittest.TestCase):
    def setUp(self):
        # Keep all test writes inside the authorized new evaluation directory.
        self.temp = tempfile.TemporaryDirectory(prefix=".test-", dir=wb.EVAL)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Fail closed if an offline test accidentally reaches process launch.
        self.launch = patch.object(wb.subprocess, "Popen", side_effect=AssertionError("No real engine in offline tests"))
        self.launch.start()
        self.addCleanup(self.launch.stop)

    def template(self, split="evaluation"):
        path = self.root / f"{split}.xlsx"
        path.write_bytes(wb.template_bytes(wb.load_case(split)))
        return path

    def test_suite_freeze_preserves_materials_and_detects_changes(self):
        cases, evaluation = self.root / "cases", self.root / "evaluation"
        evaluation.mkdir()
        for split in ("training", "evaluation"):
            (cases / split).mkdir(parents=True)
            for name in ("task.md", "template.xlsx"):
                (cases / split / name).write_bytes((wb.CASES / split / name).read_bytes())
            (evaluation / f"{split}.json").write_bytes((wb.EVAL / f"{split}.json").read_bytes())
        with patch.object(wb, "ROOT", self.root), patch.object(wb, "CASES", cases), patch.object(wb, "EVAL", evaluation):
            entries = wb.suite_entries()
            self.assertEqual([e["id"] for e in entries], ["workbook-training", "workbook-evaluation"])
            self.assertEqual(wb.suite_entries(), entries)
            (cases / "evaluation/task.md").write_text("changed task")
            with self.assertRaisesRegex(ValueError, "Frozen"):
                wb.suite_entries()

    def test_initial_scores_distinguish_values_from_formulas(self):
        book = wb.read_workbook(self.simulated_submission(constants=True))
        scores = wb.initial_scores(book, wb.load_case("evaluation"))
        self.assertEqual(scores["correct_initial_cells"], 32)
        self.assertEqual(scores["correct_rows"], 8)
        self.assertEqual(scores["formula_cells"], 0)
        book.sheets["Plan"]["G2"].value = Decimal(-1)
        self.assertEqual(wb.initial_scores(book, wb.load_case("evaluation"))["correct_rows"], 7)

    def simulated_submission(self, split="evaluation", constants=False):
        """Examiner test double, never a participant artifact or real solution."""
        path = self.template(split)
        book = wb.read_workbook(path)
        tree = wb.xml(book.parts[book.sheet_paths["Plan"]])
        data = tree.find(wb.tag("sheetData"))
        rows = {int(row.get("r")): row for row in data}
        for addr, value in wb.oracle(wb.load_case(split)).items():
            node = wb.cell_xml(rows[int(addr[1:])], addr, value)
            if not constants:
                ET.SubElement(node, wb.tag("f")).text = f"SUM({value})"
        book.parts[book.sheet_paths["Plan"]] = ET.tostring(tree)
        wb.write_zip(book.parts, path)
        return path

    def edit_parts(self, path, mutate):
        book = wb.read_workbook(path)
        mutate(book.parts)
        wb.write_zip(book.parts, path)

    def test_independent_hand_checked_values(self):
        expected = {
            "training": [(23, 11, 34, 36), (35, 9, 44, 0), (-3, 4, 1, 24),
                         (60, 5, 65, 0), (0, 8, 8, 25), (16, 8, 24, 16)],
            "evaluation": [(18, 11, 29, 36), (32, 3, 35, 0), (-4, 6, 2, 32),
                           (75, 5, 80, 0), (0, 9, 9, 25), (24, 8, 32, 20),
                           (10, 5, 15, 0), (7, 4, 11, 18)],
        }
        for split, rows in expected.items():
            values = wb.oracle(wb.load_case(split))
            self.assertEqual([tuple(values[f"{c}{r}"] for c in "DEFG")
                              for r in range(2, len(rows) + 2)], rows)

    def test_decimal_rounding_exact_pack_and_overdue_no_lower_bound(self):
        case = wb.load_case("training")
        case["plan"] = [["000101", "35.1", "0.2"]]
        self.assertEqual(wb.oracle(case)["G2"], Decimal("1.2"))
        case["plan"][0][1] = "35.2"
        self.assertEqual(wb.oracle(case)["G2"], Decimal("1.2"))
        self.assertEqual(wb.oracle(wb.load_case("training"))["E3"], 9)

    def test_fixture_clean_split_and_deterministic_blank_templates(self):
        training, evaluation = (wb.load_case(s) for s in ("training", "evaluation"))
        self.assertTrue({r[0] for r in training["plan"]}.isdisjoint({r[0] for r in evaluation["plan"]}))
        self.assertIn("000101", {r[0] for r in training["plan"]})
        self.assertIn("101", {r[0] for r in training["plan"]})
        self.assertNotEqual(len(training["stock"]), len(evaluation["stock"]))
        self.assertNotEqual(len(training["inbound"]), len(evaluation["inbound"]))
        for split, count in (("training", 6), ("evaluation", 8)):
            case = wb.load_case(split)
            data = wb.template_bytes(case)
            self.assertEqual(data, wb.template_bytes(case))
            self.assertEqual((wb.CASES / split / "template.xlsx").read_bytes(), data)
            book = wb.read_workbook(self.template(split))
            self.assertEqual(set(book.sheets), {"Stock", "Inbound", "Plan"})
            self.assertTrue(all(c.formula is None for g in book.sheets.values() for c in g.values()))
            self.assertTrue(set(wb.oracle(case)).isdisjoint(book.sheets["Plan"]))
            self.assertEqual(len(case["plan"]), count)
            task = (wb.CASES / split / "task.md").read_text()
            self.assertIn("not a lower date bound", task)
            self.assertIn(str(case["time_budget_seconds"]), task)
        self.assertNotIn("001204", (wb.CASES / "training/task.md").read_text())

    def test_static_checks_reject_constants_changed_inputs_and_bad_cache(self):
        case = wb.load_case("evaluation")
        constant = wb.read_workbook(self.simulated_submission(constants=True))
        self.assertTrue(any("Formula missing" in e for e in wb.check_workbook(constant, case)))
        book = wb.read_workbook(self.simulated_submission())
        self.assertEqual(wb.check_workbook(book, case), [])
        book.sheets["Stock"]["A2"].value = Decimal(1204)
        book.sheets["Plan"]["G2"].value = Decimal(0)
        book.sheets["Inbound"]["A30"] = wb.Cell("extra")
        errors = wb.check_workbook(book, case)
        self.assertTrue(any("Stock!A2" in e for e in errors))
        self.assertTrue(any("Plan!G2" in e for e in errors))
        self.assertTrue(any("Unexpected content" in e for e in errors))
        book.sheets["Other"] = {}
        self.assertIn("Sheet names", wb.check_workbook(book, case)[0])

    def test_rewrite_inputs_preserves_formulas_removes_caches_and_handles_1904(self):
        case = wb.load_case("evaluation")
        book = wb.read_workbook(self.simulated_submission())
        book.date1904 = True
        tree = wb.xml(book.parts["xl/workbook.xml"])
        ET.SubElement(tree, wb.tag("workbookPr"), date1904="1")
        book.parts["xl/workbook.xml"] = ET.tostring(tree)
        for name, changed in wb.perturbations(case):
            target = self.root / f"{name}.xlsx"
            wb.rewrite_inputs(book, changed, target)
            reread = wb.read_workbook(target)
            self.assertEqual(reread.sheets["Plan"]["K2"].value, wb.serial(changed["cutoff"], True))
            for addr in wb.oracle(case):
                self.assertEqual(reread.sheets["Plan"][addr].formula, book.sheets["Plan"][addr].formula)
                self.assertIsNone(reread.sheets["Plan"][addr].value)
            self.assertNotEqual(wb.oracle(case), wb.oracle(changed), name)
        self.assertEqual(case, wb.load_case("evaluation"))

    def test_shared_formula_presence_and_formula_safety(self):
        path = self.simulated_submission()
        book = wb.read_workbook(path)
        tree = wb.xml(book.parts[book.sheet_paths["Plan"]])
        cells = {c.get("r"): c for c in tree.iter(wb.tag("c"))}
        cells["D2"].find(wb.tag("f")).attrib.update(t="shared", si="0", ref="D2:D3")
        follower = cells["D3"].find(wb.tag("f"))
        follower.attrib.update(t="shared", si="0")
        follower.text = None
        book.parts[book.sheet_paths["Plan"]] = ET.tostring(tree)
        wb.write_zip(book.parts, path)
        self.assertTrue(wb.read_workbook(path).sheets["Plan"]["D3"].formula)
        wb.safe_formula('SUMPRODUCT(EXACT(Stock!A2:A12,A2)*(Stock!C2:C12-Stock!D2:D12))')
        wb.safe_formula('SUMIFS(Inbound!B2:B17,Inbound!D2:D17,"<="&$K$2)')
        wb.safe_formula('QUOTIENT(FLOOR(INDEX(A2:A5,MATCH(CONCATENATE(A1,"x"),B2:B5,0)),1),LEN(C1))')
        wb.safe_formula('_xlfn._xlws.FILTER(A2:B5,EXACT(A2:A5,C1))')
        for formula in ('WEBSERVICE("https://example.com")', "[other.xlsx]Sheet1!A1", "cmd|' /C calc'!A1", 'HYPERLINK("file:///tmp/x")'):
            with self.assertRaises(ValueError):
                wb.safe_formula(formula)

    def test_unsupported_formula_is_evaluator_incompatibility(self):
        source = self.simulated_submission()
        def unknown(parts):
            name = "xl/worksheets/sheet3.xml"
            tree = wb.xml(parts[name])
            next(tree.iter(wb.tag("f"))).text = "SOMENEWPUREFUNCTION(A2)"
            parts[name] = ET.tostring(tree)
        self.edit_parts(source, unknown)
        report = wb.grade("evaluation", source, self.root / "incompatible", True)
        self.assertEqual(report["status"], "evaluator_incompatible")
        self.assertFalse(report["workbook_pass"])
        self.assertIn("examiner review", report["error"])

    def test_native_numbers_scalar_array_formulas(self):
        source = self.simulated_submission()
        def scalar_arrays(parts):
            name = "xl/worksheets/sheet3.xml"
            tree = wb.xml(parts[name])
            for cell in tree.iter(wb.tag("c")):
                formula = cell.find(wb.tag("f"))
                if formula is not None:
                    formula.attrib.update(t="array", ref=cell.get("r"))
            parts[name] = ET.tostring(tree)
        self.edit_parts(source, scalar_arrays)
        self.assertEqual(wb.check_workbook(wb.read_workbook(source), wb.load_case("evaluation")), [])

    def test_zip_xml_macro_external_and_size_boundaries(self):
        good = wb.read_workbook(self.template()).parts
        for name, content in (("../escape.xml", b"x"), ("/absolute.xml", b"x"),
                              ("xl/vbaProject.bin", b"x"), ("xl/externalLinks/a.xml", b"x"),
                              ("evil.xml", b'<!DOCTYPE x [<!ENTITY a "x">]><x/>'),
                              ("xl/_rels/evil.rels", f'<Relationships xmlns="{wb.PKG}"><Relationship TargetMode="External" Target="https://example.com"/></Relationships>'.encode()),
                              ("large.xml", b"a" * (4 * 1024 * 1024 + 1))):
            path = self.root / "unsafe.xlsx"
            wb.write_zip({**good, name: content}, path)
            with self.assertRaises(ValueError, msg=name):
                wb.read_workbook(path)
        duplicate = self.root / "duplicate.xlsx"
        with zipfile.ZipFile(duplicate, "w") as archive:
            archive.writestr("xl/a.xml", b"<x/>")
            with self.assertWarns(UserWarning):
                archive.writestr("xl/a.xml", b"<x/>")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            wb.read_workbook(duplicate)

    def test_grade_never_calls_engine_without_explicit_opt_in(self):
        source = self.simulated_submission()
        artifacts = self.root / "static"
        with patch.object(wb, "recalculate", side_effect=AssertionError("Engine disabled")):
            report = wb.grade("evaluation", source, artifacts)
        self.assertEqual(report["status"], "pending_recalculation")
        self.assertFalse(report["workbook_pass"])
        self.assertEqual(json.loads((artifacts / "report.json").read_text()), report)
        self.assertEqual((artifacts / "submitted.xlsx").read_bytes(), source.read_bytes())
        with self.assertRaises(FileExistsError):
            wb.grade("evaluation", source, artifacts)

    def test_mocked_recalc_catches_formula_wrapped_fixed_answers(self):
        source = self.simulated_submission()
        case = wb.load_case("evaluation")
        original = wb.oracle(case)
        def fixed_answers(probe, directory):
            book = wb.read_workbook(probe)
            tree = wb.xml(book.parts[book.sheet_paths["Plan"]])
            for node in tree.iter(wb.tag("c")):
                if node.get("r") in original:
                    ET.SubElement(node, wb.tag("v")).text = str(original[node.get("r")])
            book.parts[book.sheet_paths["Plan"]] = ET.tostring(tree)
            target = Path(probe).with_name("fixed.xlsx")
            wb.write_zip(book.parts, target)
            return target
        with patch.object(wb, "recalculate", side_effect=fixed_answers) as engine:
            report = wb.grade("evaluation", source, self.root / "fixed", True)
        self.assertEqual(engine.call_count, 8)
        self.assertEqual(report["checks"]["baseline"], [])
        self.assertTrue(report["checks"]["stock-balances"])
        self.assertFalse(report["workbook_pass"])
        self.assertEqual(report["status"], "failed")

    def test_mocked_dynamic_orchestration_and_engine_error_status(self):
        source = self.simulated_submission()
        case = wb.load_case("evaluation")
        variants = {"baseline": case, **dict(wb.perturbations(case))}
        def simulated_engine(probe, directory):
            book = wb.read_workbook(probe)
            expected = wb.oracle(variants[Path(probe).parent.name])
            tree = wb.xml(book.parts[book.sheet_paths["Plan"]])
            for node in tree.iter(wb.tag("c")):
                if node.get("r") in expected:
                    ET.SubElement(node, wb.tag("v")).text = str(expected[node.get("r")])
            book.parts[book.sheet_paths["Plan"]] = ET.tostring(tree)
            output = Path(probe).with_name("simulated.xlsx")
            wb.write_zip(book.parts, output)
            return output
        with patch.object(wb, "recalculate", side_effect=simulated_engine):
            report = wb.grade("evaluation", source, self.root / "dynamic", True)
        self.assertEqual(report["status"], "workbook_pass")
        self.assertTrue(report["workbook_pass"])
        self.assertEqual(len(report["checks"]), 9)
        self.assertEqual(report["delivery"], "not_checked")
        with patch.object(wb, "recalculate", side_effect=wb.ExaminerError("mock timeout")):
            report = wb.grade("evaluation", source, self.root / "engine-error", True)
        self.assertEqual(report["status"], "examiner_error")
        self.assertFalse(report["workbook_pass"])

    def test_engine_command_isolation_failure_logs_and_timeout_mock_only(self):
        source = self.template()
        fake = Mock(returncode=1)
        fake.communicate.return_value = (b"out", b"conversion failed")
        directory = self.root / "engine-failure"
        with patch.object(wb.subprocess, "Popen", return_value=fake) as launch:
            with self.assertRaisesRegex(ValueError, "logs"):
                wb.recalculate(source, directory)
        command = launch.call_args.args[0]
        self.assertIn(f"-env:UserInstallation={(directory / 'profile').as_uri()}", command)
        self.assertIn("--headless", command)
        self.assertTrue(launch.call_args.kwargs["start_new_session"])
        self.assertEqual((directory / "stderr.log").read_bytes(), b"conversion failed")
        self.assertTrue((directory / "failure.txt").is_file())
        timed = Mock(returncode=-9, pid=999999)
        timed.communicate.side_effect = [subprocess.TimeoutExpired(command, 60), (b"partial", b"timeout")]
        with patch.object(wb.subprocess, "Popen", return_value=timed), patch.object(wb.os, "killpg") as kill:
            with self.assertRaises(ValueError):
                wb.recalculate(source, self.root / "timeout")
            kill.assert_called_once_with(999999, wb.signal.SIGKILL)
        self.assertIn("Timeout: True", (self.root / "timeout/failure.txt").read_text())


if __name__ == "__main__":
    unittest.main()
