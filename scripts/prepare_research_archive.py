#!/usr/bin/env python3
"""Export a curated historical snapshot without changing frozen experiments.

Only explicitly selected source, reports, aggregate summaries, tables and
already-generated figures/PDFs are copied. This does not approve redistribution
or provide the private dependencies needed to rerun the historical workspace.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


STUDY_ROOT = Path(
    "openAI/packet_attention_v3m/paper/more_experiement/"
    "source_destination_decomposition/prior_method_field_study_v2"
)
STUDIES = ("formula_search_v16", "formula_search_v17", "four_factor_attention_v18")
MAX_JSON_BYTES = 4 * 1024 * 1024
MANIFEST_NAME = "MANIFEST.json"
HOME_PATH = re.compile(r"(?<![\w./])/(?:home|Users)/[^\s/<>:\"'`\\]+")
WINDOWS_HOME = re.compile(r"(?i:(?<!\w)[a-z]:[\\/]Users[\\/][^\\/\s<>:\"']+)")
MARKDOWN_BANNER = (
    "> Public archive copy — path-sanitized historical workspace snapshot.\n"
    "> Original checks and referenced seals below are historical, not proof of\n"
    "> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.\n"
    "> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.\n\n"
)
NOTICE = """# Historical archive notice

This is a curated, path-sanitized public-archive preparation copy, not a new
experiment or a runnable standalone workspace. Project-owned contributions
use Apache-2.0; root LICENSE, NOTICE and THIRD_PARTY_NOTICES.md preserve scope.
Raw data, weights and third-party-owned materials are not relicensed by this export.

The original study files are unchanged. Historical pass checks, frozen contract
hashes and seals retained in reports refer to the original workspace only;
they do not certify this transformed export. The archive-root MANIFEST.json records
original and exported hashes and every export transformation.

Absolute paths under the supplied workspace become WORKSPACE; other user-home
prefixes become USER_HOME. Python copies retain historical imports, command
assumptions and private dependencies. Do not run them as a portable package.
Raw data, weights, run/phase directories, per-packet arrays, original contracts
and full raw audit JSON are intentionally excluded. Full training reproduction
requires separately approved private assets and the original environment.

SUMMARY.json is an aggregate historical result, not a new accuracy claim.
Large summaries use singleton {"$archive_ref": "summary_parts/...json"} objects.
Use scripts/read_archive_summary.py from the repository root to reconstruct
the complete sanitized summary. No numerical values are rounded or removed.
Figures, tables and existing PDFs are copied byte-for-byte, not regenerated.
"""


def json_bytes(value):
    """Canonical compact JSON; Python integers and float round-trips stay exact."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def sanitize_text(text, workspace):
    prefix = str(Path(workspace).resolve()).rstrip("/")
    if not prefix:
        raise ValueError("The filesystem root cannot be used as the workspace")
    # A similarly named sibling is not part of the supplied workspace.
    boundary = r"(?=$|[/\s\"'`)\]},;:])"
    text, count = re.subn(re.escape(prefix) + boundary, "WORKSPACE", text)
    text, homes = HOME_PATH.subn("USER_HOME", text)
    text, windows = WINDOWS_HOME.subn("USER_HOME", text)
    return text, count + homes + windows


def sanitize_json(value, workspace):
    """Redact strings and object keys; reject key collisions, never round data."""
    if isinstance(value, str):
        return sanitize_text(value, workspace)
    if isinstance(value, list):
        result, count = [], 0
        for item in value:
            clean, replacements = sanitize_json(item, workspace)
            result.append(clean)
            count += replacements
        return result, count
    if isinstance(value, dict):
        result, count = {}, 0
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            clean_key, replacements = sanitize_text(key, workspace)
            if clean_key in result:
                raise ValueError("Path redaction would merge distinct JSON keys")
            clean, nested = sanitize_json(item, workspace)
            result[clean_key] = clean
            count += replacements + nested
        return result, count
    if value is None or isinstance(value, (bool, int, float)):
        return value, 0
    raise ValueError("Unsupported JSON value")


def split_summary_payloads(value, max_bytes=MAX_JSON_BYTES):
    """Recursively externalize container members in sorted-key order.

    Fail closed for an indivisible oversized scalar or a reference skeleton
    that itself cannot fit. No data are dropped to satisfy a size limit.
    """
    if not isinstance(max_bytes, int) or max_bytes < 128:
        raise ValueError("JSON part limit must be at least 128 bytes")
    payloads, counter = {}, 0

    def contains_reserved(item):
        if isinstance(item, dict):
            if set(item) == {"$archive_ref"}:
                raise ValueError("Source summary contains the reserved archive-reference marker")
            for child in item.values():
                contains_reserved(child)
        elif isinstance(item, list):
            for child in item:
                contains_reserved(child)

    def reference(item):
        nonlocal counter
        counter += 1
        name = f"summary_parts/p{counter:06d}.json"
        write_part(item, name)
        return {"$archive_ref": name}

    def write_part(item, name):
        encoded = json_bytes(item)
        if len(encoded) > max_bytes:
            if isinstance(item, dict):
                item = {key: reference(child) if isinstance(child, (dict, list))
                        or len(json_bytes(child)) > 64 else child
                        for key, child in sorted(item.items())}
            elif isinstance(item, list):
                item = [reference(child) for child in item]
            else:
                raise ValueError("An indivisible JSON value exceeds the part limit")
            encoded = json_bytes(item)
            if len(encoded) > max_bytes:
                raise ValueError("The JSON reference skeleton exceeds the part limit")
        payloads[name] = encoded

    contains_reserved(value)
    write_part(value, "SUMMARY.json")
    return dict(sorted(payloads.items()))


def _no_symlinks(path):
    """Validate all existing components without following a symlink silently."""
    path = Path(path).absolute()
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Symlinks are not permitted in archive paths")
    return path


def _write_new(path, content):
    _no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def write_split_summary(value, study_output_dir, max_bytes=MAX_JSON_BYTES):
    payloads = split_summary_payloads(value, max_bytes)
    output = _no_symlinks(study_output_dir)
    targets = [output / name for name in payloads]
    if any(path.exists() or path.is_symlink() for path in targets):
        raise FileExistsError("Refusing to overwrite an existing summary or part")
    for name, content in payloads.items():
        _write_new(output / name, content)
    return targets


def selected_sources(study):
    """Explicit allowlist: never recurse into training, raw assets or audits."""
    selected = set(study.glob("*.py")) | set(study.glob("*.md"))
    selected.add(study / "SUMMARY.json")
    mechanism = study / "MECHANISM_DIAGNOSIS.json"
    if mechanism.exists():
        selected.add(mechanism)
    selected.update((study / "tables").rglob("*.tex"))
    for suffix in ("*.png", "*.svg", "*.pdf"):
        selected.update((study / "figures").rglob(suffix))
    selected.update((study / "output" / "pdf").glob("*.pdf"))
    result = []
    for path in sorted(selected):
        _no_symlinks(path)
        if not path.is_file():
            raise ValueError("A selected archive source is missing or not a regular file")
        result.append(path)
    return result


def export_archive(workspace, output):
    workspace = _no_symlinks(workspace).resolve()
    output = _no_symlinks(output).resolve()
    if not workspace.is_dir() or workspace == Path(workspace.anchor):
        raise ValueError("An explicit, non-root workspace directory is required")
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing archive directory")
    study_root = workspace / STUDY_ROOT
    if output == study_root or study_root in output.parents:
        raise ValueError("The archive must not be written into frozen study sources")

    # Prepare every byte before creating the output directory. Selection,
    # sanitation or size failures leave no partially published archive.
    payloads, records, originals, expected_summaries = {}, [], {}, {}
    study_counts = {}
    conflicts = []

    def add(name, content, source=None, original=None, transforms=(), redactions=0):
        if name in payloads:
            raise ValueError("Duplicate archive destination")
        payloads[name] = content
        records.append({
            "path": name,
            "source_workspace_relativepath": None if source is None else source.relative_to(workspace).as_posix(),
            "original_sha256": None if original is None else sha256(original),
            "exported_sha256": sha256(content),
            "original_bytes": None if original is None else len(original),
            "exported_bytes": len(content),
            "transforms": list(transforms),
            "path_redactions": redactions,
        })
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return
        private_count = len(HOME_PATH.findall(text)) + len(WINDOWS_HOME.findall(text))
        if private_count:
            conflicts.append({"path": name, "private_path_matches": private_count})

    for study_name in STUDIES:
        study = study_root / study_name
        study_prefix = f"studies/{study_name}"
        if not study.is_dir():
            raise ValueError(f"Missing required study: {study_name}")
        for source in selected_sources(study):
            original = source.read_bytes()
            originals[source] = sha256(original)
            relative = source.relative_to(study)
            destination = f"{study_prefix}/{relative.as_posix()}"
            if relative.name in {"SUMMARY.json", "MECHANISM_DIAGNOSIS.json"}:
                parsed = json.loads(original)
                clean, count = sanitize_json(parsed, workspace)
                if relative.name == "SUMMARY.json":
                    parts = split_summary_payloads(clean)
                    expected_summaries[study_name] = clean
                    for name, content in parts.items():
                        transforms = ["json_canonical_compaction", "json_path_redaction"]
                        if len(parts) > 1:
                            transforms.append("lossless_recursive_summary_refs")
                        add(f"{study_prefix}/{name}", content, source, original,
                            transforms, count if name == "SUMMARY.json" else 0)
                else:
                    content = json_bytes(clean)
                    if len(content) > MAX_JSON_BYTES:
                        raise ValueError("Mechanism diagnosis exceeds the JSON file limit")
                    add(destination, content, source, original,
                        ["json_canonical_compaction", "json_path_redaction"], count)
            elif relative.parent == Path(".") and source.suffix in {".py", ".md"}:
                text, count = sanitize_text(original.decode("utf-8"), workspace)
                transforms = ["text_path_redaction"] if count else []
                if source.suffix == ".md":
                    text = MARKDOWN_BANNER + text
                    transforms.append("historical_archive_notice_prefix")
                else:
                    ast.parse(text)
                add(destination, text.encode("utf-8"), source, original, transforms, count)
            else:
                add(destination, original, source, original, ["byte_exact_copy"])
        add(f"{study_prefix}/ARCHIVE_NOTICE.md", NOTICE.encode("utf-8"),
            transforms=["generated_archive_notice"])
        study_counts[study_name] = sum(name.startswith(study_prefix + "/") for name in payloads)

    if conflicts:
        raise ValueError("Private paths remain in exact-copy assets: " +
                         ", ".join(item["path"] for item in conflicts))
    manifest = {
        "schema": "lapa-curated-research-archive-v1",
        "status": "CURATED_EXPORT_NOT_NEW_EXPERIMENT_OR_BLANKET_RIGHTS_CLEARANCE",
        "license_status": "PROJECT_APACHE_2_0_WITH_THIRD_PARTY_NOTICES",
        "source_root_workspace_relativepath": STUDY_ROOT.as_posix(),
        "workspace_path_placeholder": "WORKSPACE",
        "other_user_home_placeholder": "USER_HOME",
        "summary_part_max_bytes": MAX_JSON_BYTES,
        "summary_reconstruction": "Exact equality to path-sanitized parsed source JSON; no numeric rounding",
        "historical_seals": "Original referenced seals are historical, not verification of this export",
        "manifest_scope": "Exporter-created files only; MANIFEST.json self-hash and separately authored root README.md are excluded",
        "excluded": ["raw_data", "weights", "run_and_phase_directories", "per_packet_arrays",
                     "original_contracts", "full_raw_audit_json", "private_dependencies"],
        "file_count": len(records),
        "study_file_counts": study_counts,
        "total_exported_bytes": sum(len(content) for content in payloads.values()),
        "path_redaction_count": sum(record["path_redactions"] for record in records),
        "path_redaction_count_scope": "Each source JSON counted once on its root summary record, including redactions in externalized parts",
        "files": sorted(records, key=lambda record: record["path"]),
    }
    # Re-read the selected sources to catch concurrent edits before writing.
    if any(sha256(path.read_bytes()) != digest for path, digest in originals.items()):
        raise ValueError("A frozen source changed while export was being prepared")
    output.mkdir(parents=True, exist_ok=False)
    for name, content in sorted(payloads.items()):
        _write_new(output / name, content)
    try:
        from scripts.read_archive_summary import read_summary
    except ModuleNotFoundError:
        from read_archive_summary import read_summary
    for study_name, expected in expected_summaries.items():
        if read_summary(output / "studies" / study_name / "SUMMARY.json") != expected:
            raise ValueError("Archive summary reconstruction differs from sanitized source")
    _write_new(output / MANIFEST_NAME, json_bytes(manifest))
    return manifest


def _manifest_target(output, name):
    if not isinstance(name, str) or "\\" in name:
        raise ValueError("Unsafe manifest path")
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute() or any(part in {"", ".", "..", ".git"}
                                                 for part in name.split("/"))):
        raise ValueError("Unsafe manifest path")
    target = _no_symlinks(output / relative)
    if not target.is_relative_to(output) or not target.is_file():
        raise ValueError("Missing or unsafe manifest target")
    return target


def verify_archive(output):
    """Verify exported hashes only; do not rewrite or re-certify historical data."""
    output = _no_symlinks(output).resolve()
    manifest = json.loads(_manifest_target(output, MANIFEST_NAME).read_bytes())
    findings, seen = [], set()
    if not isinstance(manifest, dict) or manifest.get("schema") != "lapa-curated-research-archive-v1":
        raise ValueError("Unknown archive manifest schema")
    records = manifest.get("files")
    if not isinstance(records, list):
        raise ValueError("Invalid archive manifest file list")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid archive manifest file record")
        name = record.get("path")
        if not isinstance(name, str) or name in seen:
            raise ValueError("Invalid or duplicate manifest path")
        seen.add(name)
        try:
            content = _manifest_target(output, name).read_bytes()
        except (OSError, ValueError):
            findings.append({"path": name, "issue": "missing_or_unsafe_target"})
            continue
        if sha256(content) != record.get("exported_sha256"):
            findings.append({"path": name, "issue": "exported_hash_mismatch"})
    if manifest.get("file_count") != len(records):
        findings.append({"path": MANIFEST_NAME, "issue": "file_count_mismatch"})
    return {"valid": not findings, "checked_files": len(records),
            "scope": "Manifest-listed exported hashes only; not historical seals or release approval",
            "findings": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Explicit existing source workspace; required for export")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[1] / "research_archive")
    parser.add_argument("--verify", action="store_true", help="Read-only exported-manifest hash verification")
    args = parser.parse_args(argv)
    if not args.verify and args.workspace is None:
        parser.error("--workspace is required when exporting")
    try:
        if args.verify:
            report = verify_archive(args.output)
            print(json.dumps(report, sort_keys=True))
            return 0 if report["valid"] else 1
        manifest = export_archive(args.workspace, args.output)
    except (OSError, ValueError, SyntaxError, RecursionError) as exc:
        # Failures identify the operation or relative asset, never dump content.
        print(f"Archive preparation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: manifest[key] for key in
                      ("status", "file_count", "study_file_counts", "total_exported_bytes",
                       "path_redaction_count")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
