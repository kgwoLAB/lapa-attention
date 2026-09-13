#!/usr/bin/env python3
"""Read a complete or split research-archive SUMMARY without modifying files.

A reference is exactly ``{"$archive_ref": "summary_parts/p000001.json"}``.
References in every part are relative to the initial SUMMARY's directory,
not to the directory of the part that contains them. This module has no
dependencies on the model package or the original experiment workspace.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import stat


class ArchiveSummaryError(ValueError):
    """A summary is invalid or cannot be reconstructed safely."""


def _require_regular_file(path: Path) -> None:
    """Check all path components before reading; never follow a symlink."""
    current = Path(path.anchor)
    try:
        for component in path.parts[1:]:
            current = current / component
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ArchiveSummaryError("summary paths must not contain symlinks")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ArchiveSummaryError("summary input must be a regular file")
    except OSError as exc:
        raise ArchiveSummaryError("summary input is missing or unreadable") from exc


def _invalid_constant(_value: str) -> None:
    raise ArchiveSummaryError("summary JSON must not contain non-finite numbers")


def read_summary(path: str | Path) -> object:
    """Load JSON and recursively replace exact singleton archive references.

    References must use canonical relative POSIX paths below ``summary_parts``
    and end in ``.json``. Absolute paths, traversal, symlinks and reference
    cycles are rejected. Dictionaries with additional keys are ordinary data,
    even if one key is ``$archive_ref``. Numeric values are not transformed.
    """
    source = Path(path).absolute()
    _require_regular_file(source)
    source = source.resolve(strict=True)
    study_root = source.parent
    active: set[Path] = set()

    def resolve_reference(value: object) -> Path:
        if not isinstance(value, str):
            raise ArchiveSummaryError("archive reference must be a string")
        parts = value.split("/")
        if (len(parts) < 2 or parts[0] != "summary_parts"
                or any(part in {"", ".", ".."} for part in parts)
                or "\\" in value or ":" in value or "\x00" in value
                or not parts[-1].endswith(".json")):
            raise ArchiveSummaryError(
                "archive reference must be a relative JSON path below summary_parts"
            )
        target = study_root.joinpath(*parts)
        _require_regular_file(target)
        resolved = target.resolve(strict=True)
        if not resolved.is_relative_to(study_root / "summary_parts"):
            raise ArchiveSummaryError("archive reference escapes summary_parts")
        return resolved

    def expand(value: object) -> object:
        if isinstance(value, dict):
            if set(value) == {"$archive_ref"}:
                return load(resolve_reference(value["$archive_ref"]))
            return {key: expand(child) for key, child in value.items()}
        if isinstance(value, list):
            return [expand(child) for child in value]
        if isinstance(value, float) and not math.isfinite(value):
            raise ArchiveSummaryError("summary JSON must not contain non-finite numbers")
        return value

    def load(filename: Path) -> object:
        if filename in active:
            raise ArchiveSummaryError("archive reference cycle detected")
        active.add(filename)
        try:
            try:
                with filename.open("r", encoding="utf-8") as stream:
                    value = json.load(stream, parse_constant=_invalid_constant)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ArchiveSummaryError("summary input is not readable UTF-8 JSON") from exc
            return expand(value)
        finally:
            active.remove(filename)

    try:
        return load(source)
    except RecursionError as exc:
        raise ArchiveSummaryError("summary nesting exceeds the reader's recursion limit") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="path to the study's SUMMARY.json")
    args = parser.parse_args(argv)
    try:
        summary = read_summary(args.summary)
    except (ArchiveSummaryError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
