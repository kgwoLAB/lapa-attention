"""Archive-reader and exporter checks use only temporary, fabricated fixtures."""

import contextlib
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load_script("read_archive_summary")
exporter = load_script("prepare_research_archive")


class TemporaryArchiveTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="research-archive-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def symlink(self, link, target, directory=False):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")


class SummaryReaderTests(TemporaryArchiveTest):
    def test_plain_summary_preserves_numeric_types_and_values(self):
        summary = {"integer": 2**70, "float": 0.125, "negative_zero": -0.0,
                   "boolean": True, "null": None, "unicode": "측정",
                   "nested": [0, -3, 1.25e-25, {"ratio": 0.875}]}
        path = self.write_json("study/SUMMARY.json", summary)
        actual = reader.read_summary(path)
        self.assertEqual(actual, summary)
        self.assertIs(type(actual["integer"]), int)
        self.assertIs(type(actual["float"]), float)
        self.assertIs(type(actual["boolean"]), bool)
        self.assertEqual(math.copysign(1, actual["negative_zero"]), -1)

    def test_nested_references_are_always_anchored_to_study_root(self):
        path = self.write_json("study/SUMMARY.json", {
            "result": {"$archive_ref": "summary_parts/nested/first.json"},
        })
        self.write_json("study/summary_parts/nested/first.json", [
            1, {"$archive_ref": "summary_parts/second.json"},
        ])
        self.write_json("study/summary_parts/second.json", {"score": 0.875})
        self.assertEqual(reader.read_summary(path), {"result": [1, {"score": 0.875}]})

    def test_repeated_reference_is_not_a_cycle(self):
        ref = {"$archive_ref": "summary_parts/shared.json"}
        path = self.write_json("SUMMARY.json", [ref, ref])
        self.write_json("summary_parts/shared.json", [1, 2.5])
        self.assertEqual(reader.read_summary(path), [[1, 2.5], [1, 2.5]])

    def test_only_exact_singleton_is_a_reference(self):
        summary = {"$archive_ref": "plain descriptive value", "score": 0.5}
        self.assertEqual(reader.read_summary(self.write_json("SUMMARY.json", summary)), summary)

    def test_invalid_reference_paths_are_rejected(self):
        unsafe = [
            "/summary_parts/part.json", "../part.json", "summary_parts/../part.json",
            "summary_parts/./part.json", "summary_parts//part.json",
            "summary_parts/part.json/", "summary_parts/part.txt", "other/part.json",
            "summary_parts\\part.json", "C:/summary_parts/part.json",
            "summary_parts/C:part.json", "summary_parts/part\x00.json",
            "summary_parts", "", None, 12, ["summary_parts/part.json"],
        ]
        for reference in unsafe:
            with self.subTest(reference=reference):
                path = self.write_json("SUMMARY.json", {"$archive_ref": reference})
                with self.assertRaises(reader.ArchiveSummaryError):
                    reader.read_summary(path)

    def test_missing_reference_is_rejected(self):
        path = self.write_json("SUMMARY.json", {"$archive_ref": "summary_parts/missing.json"})
        with self.assertRaises(reader.ArchiveSummaryError):
            reader.read_summary(path)

    def test_direct_and_indirect_cycles_are_rejected(self):
        path = self.write_json("SUMMARY.json", {"$archive_ref": "summary_parts/a.json"})
        for target in ("a.json", "b.json"):
            with self.subTest(target=target):
                self.write_json("summary_parts/a.json", {"$archive_ref": "summary_parts/" + target})
                self.write_json("summary_parts/b.json", {"$archive_ref": "summary_parts/a.json"})
                with self.assertRaisesRegex(reader.ArchiveSummaryError, "cycle"):
                    reader.read_summary(path)

    def test_symlink_reference_file_is_rejected(self):
        path = self.write_json("study/SUMMARY.json", {"$archive_ref": "summary_parts/part.json"})
        target = self.write_json("outside.json", {"private": True})
        self.symlink(self.root / "study/summary_parts/part.json", target)
        with self.assertRaisesRegex(reader.ArchiveSummaryError, "symlink"):
            reader.read_summary(path)

    def test_symlink_reference_directory_is_rejected(self):
        path = self.write_json("study/SUMMARY.json", {"$archive_ref": "summary_parts/part.json"})
        self.write_json("outside/part.json", {"private": True})
        self.symlink(self.root / "study/summary_parts", self.root / "outside", directory=True)
        with self.assertRaisesRegex(reader.ArchiveSummaryError, "symlink"):
            reader.read_summary(path)

    def test_symlink_initial_summary_is_rejected(self):
        target = self.write_json("original.json", {"score": 1})
        self.symlink(self.root / "SUMMARY.json", target)
        with self.assertRaisesRegex(reader.ArchiveSummaryError, "symlink"):
            reader.read_summary(self.root / "SUMMARY.json")

    def test_symlink_study_directory_is_rejected(self):
        self.write_json("original/SUMMARY.json", {"score": 1})
        self.symlink(self.root / "linked", self.root / "original", directory=True)
        with self.assertRaisesRegex(reader.ArchiveSummaryError, "symlink"):
            reader.read_summary(self.root / "linked/SUMMARY.json")

    def test_invalid_json_and_nonfinite_values_are_rejected(self):
        path = self.root / "SUMMARY.json"
        for content in (b'{"score":', b'{} trailing', b'\xff', b'NaN', b'Infinity', b'1e999'):
            with self.subTest(content=content):
                path.write_bytes(content)
                with self.assertRaises(reader.ArchiveSummaryError):
                    reader.read_summary(path)

    def test_invalid_json_in_part_is_rejected(self):
        path = self.write_json("SUMMARY.json", {"$archive_ref": "summary_parts/part.json"})
        part = self.write_json("summary_parts/part.json", {})
        part.write_text("not JSON", encoding="utf-8")
        with self.assertRaises(reader.ArchiveSummaryError):
            reader.read_summary(path)

    def test_directory_cannot_be_read_as_summary(self):
        with self.assertRaises(reader.ArchiveSummaryError):
            reader.read_summary(self.root)

    def test_cli_prints_reconstructed_json_without_writing(self):
        path = self.write_json("SUMMARY.json", {"$archive_ref": "summary_parts/part.json"})
        self.write_json("summary_parts/part.json", {"score": 0.75})
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(reader.main([str(path)]), 0)
        self.assertEqual(json.loads(stdout.getvalue()), {"score": 0.75})
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_cli_invalid_summary_exits_with_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            reader.main([str(self.root / "missing.json")])
        self.assertEqual(error.exception.code, 2)


class ArchiveExporterTests(TemporaryArchiveTest):
    def test_text_redaction_retains_suffixes_and_respects_workspace_boundary(self):
        workspace = self.root / "workspace"
        unix_home = "/" + "home" + "/fixture-person"
        mac_home = "/" + "Users" + "/fixture-person"
        windows_home = "C:" + "\\Users\\" + "fixture-person"
        source = "\n".join([
            str(workspace / "study/result.json"), unix_home + "/notes.txt",
            mac_home + "/notes.txt", windows_home + "\\notes.txt",
            str(workspace) + "-sibling/result.json", "relative/result.json",
        ])
        clean, count = exporter.sanitize_text(source, workspace)
        self.assertEqual(count, 4)
        self.assertEqual(clean.splitlines(), [
            "WORKSPACE/study/result.json", "USER_HOME/notes.txt",
            "USER_HOME/notes.txt", "USER_HOME\\notes.txt",
            str(workspace) + "-sibling/result.json", "relative/result.json",
        ])
        self.assertEqual(exporter.sanitize_text(clean, workspace), (clean, 0))

    def test_json_redaction_preserves_numbers_types_and_original_object(self):
        workspace = self.root / "workspace"
        key = str(workspace / "key")
        source = {key: {"path": str(workspace / "study/result.json"),
                        "numbers": [2**80, 0.12345678901234567, -0.0, True, None]}}
        before = json.dumps(source)
        clean, count = exporter.sanitize_json(source, workspace)
        self.assertEqual(count, 2)
        self.assertEqual(clean["WORKSPACE/key"]["path"], "WORKSPACE/study/result.json")
        numbers = clean["WORKSPACE/key"]["numbers"]
        self.assertEqual(numbers, source[key]["numbers"])
        self.assertEqual([type(number) for number in numbers], [int, float, float, bool, type(None)])
        self.assertEqual(math.copysign(1, numbers[2]), -1)
        self.assertEqual(json.dumps(source), before)

    def test_redacted_key_collisions_fail_without_data_loss(self):
        home_prefix = "/" + "home" + "/"
        with self.assertRaisesRegex(ValueError, "merge"):
            exporter.sanitize_json({home_prefix + "person-a/key": 1,
                                    home_prefix + "person-b/key": 2}, self.root)

    def split_fixture(self):
        return {"model_" + str(model): [
            {"tokens": list(range(15)), "values": [123456.789012345] * 12,
             "large": 2**80, "ratio": 0.875, "enabled": True, "empty": None}
            for _ in range(3)
        ] for model in range(4)}

    def test_recursive_split_reassembles_all_numeric_results(self):
        source = self.split_fixture()
        output = self.root / "study"
        paths = exporter.write_split_summary(source, output, max_bytes=600)
        self.assertGreater(len(paths), 5)
        self.assertIn(output / "SUMMARY.json", paths)
        self.assertTrue(all(path.stat().st_size <= 600 for path in paths))
        self.assertEqual(reader.read_summary(output / "SUMMARY.json"), source)
        self.assertTrue(any(
            "$archive_ref" in path.read_text(encoding="utf-8")
            for path in paths if path.name != "SUMMARY.json"
        ))

    def test_splitting_is_deterministic_independent_of_dictionary_insertion_order(self):
        source = self.split_fixture()
        left, right = self.root / "left", self.root / "right"
        first = exporter.write_split_summary(source, left, max_bytes=600)
        second = exporter.write_split_summary(dict(reversed(list(source.items()))), right, max_bytes=600)
        self.assertEqual({p.relative_to(left): p.read_bytes() for p in first},
                         {p.relative_to(right): p.read_bytes() for p in second})

    def test_small_summary_is_single_valid_json_file(self):
        output = self.root / "study"
        paths = exporter.write_split_summary({"score": 0.875}, output, max_bytes=300)
        self.assertEqual(paths, [output / "SUMMARY.json"])
        self.assertEqual(reader.read_summary(paths[0]), {"score": 0.875})

    def test_unsplittable_or_reserved_values_fail_before_writing(self):
        fixtures = ["x" * 1000, [{"value": "x" * 100}] * 30,
                    {"nested": {"$archive_ref": "summary_parts/source.json"}},
                    {"score": float("nan")}]
        for index, source in enumerate(fixtures):
            with self.subTest(index=index):
                output = self.root / ("failure_" + str(index))
                with self.assertRaises(ValueError):
                    exporter.write_split_summary(source, output, max_bytes=300)
                self.assertFalse(output.exists())

    def test_summary_writer_refuses_overwrite(self):
        output = self.root / "study"
        paths = exporter.write_split_summary({"score": 1}, output)
        before = paths[0].read_bytes()
        with self.assertRaises(FileExistsError):
            exporter.write_split_summary({"score": 2}, output)
        self.assertEqual(paths[0].read_bytes(), before)

    def test_summary_writer_rejects_symlink_output(self):
        target = self.root / "elsewhere"
        target.mkdir()
        self.symlink(self.root / "linked", target, directory=True)
        with self.assertRaises(ValueError):
            exporter.write_split_summary({"score": 1}, self.root / "linked")
        self.assertEqual(list(target.iterdir()), [])

    def create_workspace(self):
        workspace = self.root / "workspace"
        for study_name in exporter.STUDIES:
            prefix = Path("workspace") / exporter.STUDY_ROOT / study_name
            source_path = workspace / exporter.STUDY_ROOT / study_name / "source.py"
            self.write_json(prefix / "SUMMARY.json", {
                "score": 0.12345678901234567, "count": 2**70,
                "source": str(source_path),
            })
            files = {
                "source.py": ("SOURCE = " + repr(str(source_path)) + "\n").encode("utf-8"),
                "REPORT.md": ("# Historical report\nSource: " + str(source_path) + "\n").encode("utf-8"),
                "tables/results.tex": b"score & 0.875 \\\\\n",
                "figures/plot.svg": b'<svg xmlns="http://www.w3.org/2000/svg"/>\n',
                "output/pdf/report.pdf": b"%PDF-1.4\n% fabricated fixture\n",
                "raw.jsonl": b"{}\n", "checkpoint.pt": b"not a checkpoint\n",
                "FROZEN_CONTRACT.json": b"{}\n", "RAW_AUDIT.json": b"{}\n",
                "phase1/private.py": b"PRIVATE = True\n",
                "runs/run0/SUMMARY.json": b"{}\n",
            }
            for name, content in files.items():
                target = self.root / prefix / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
        return workspace

    def test_archive_allowlist_manifest_and_original_immutability(self):
        workspace = self.create_workspace()
        before = {p.relative_to(workspace): p.read_bytes()
                  for p in workspace.rglob("*") if p.is_file()}
        output = self.root / "archive"
        manifest = exporter.export_archive(workspace, output)
        self.assertEqual(manifest["file_count"], 7 * len(exporter.STUDIES))
        for study_name in exporter.STUDIES:
            study_output = output / "studies" / study_name
            names = {p.relative_to(study_output).as_posix()
                     for p in study_output.rglob("*") if p.is_file()}
            self.assertEqual(names, {"SUMMARY.json", "source.py", "REPORT.md", "ARCHIVE_NOTICE.md",
                                     "tables/results.tex", "figures/plot.svg", "output/pdf/report.pdf"})
            summary = reader.read_summary(study_output / "SUMMARY.json")
            self.assertEqual(summary["score"], 0.12345678901234567)
            self.assertEqual(summary["count"], 2**70)
            self.assertTrue(summary["source"].startswith("WORKSPACE/"))
            for relative in ("tables/results.tex", "figures/plot.svg", "output/pdf/report.pdf"):
                self.assertEqual((study_output / relative).read_bytes(),
                                 (workspace / exporter.STUDY_ROOT / study_name / relative).read_bytes())
        after = {p.relative_to(workspace): p.read_bytes()
                 for p in workspace.rglob("*") if p.is_file()}
        self.assertEqual(after, before)
        self.assertTrue(exporter.verify_archive(output)["valid"])
        for record in manifest["files"]:
            content = (output / record["path"]).read_bytes()
            self.assertEqual(record["exported_sha256"], exporter.sha256(content))
            if record["source_workspace_relativepath"] is not None:
                original = (workspace / record["source_workspace_relativepath"]).read_bytes()
                self.assertEqual(record["original_sha256"], exporter.sha256(original))

    def test_verifier_reports_exported_content_mutation(self):
        output = self.root / "archive"
        exporter.export_archive(self.create_workspace(), output)
        target = output / "studies" / exporter.STUDIES[0] / "SUMMARY.json"
        target.write_text('{"score": 0}\n', encoding="utf-8")
        report = exporter.verify_archive(output)
        self.assertFalse(report["valid"])
        self.assertIn({"path": "studies/" + exporter.STUDIES[0] + "/SUMMARY.json",
                       "issue": "exported_hash_mismatch"}, report["findings"])

    def test_export_cli_works_from_unrelated_directory(self):
        workspace = self.create_workspace()
        output = self.root / "archive"
        command = [sys.executable, "-B", str(SCRIPTS / "prepare_research_archive.py")]
        result = subprocess.run(command + ["--workspace", str(workspace), "--output", str(output)],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["file_count"], 7 * len(exporter.STUDIES))
        verified = subprocess.run(command + ["--verify", "--output", str(output)],
                                  cwd=self.root, capture_output=True, text=True)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertTrue(json.loads(verified.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
