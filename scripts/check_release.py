#!/usr/bin/env python3
"""Check the current Git candidate set against this project's release policy.

This is a local packaging check, not a secret-scanning guarantee, a Git-history
audit, or a legal approval. It never stages, commits, or changes Git metadata.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


MAX_FILE_BYTES = 5 * 1024 * 1024
PROHIBITED_SUFFIXES = frozenset({
    ".7z", ".arrow", ".bin", ".bz2", ".cap", ".ckpt", ".csv", ".db",
    ".feather", ".gz", ".h5", ".hdf5", ".jsonl", ".key", ".ndjson",
    ".npy", ".npz", ".onnx", ".p12", ".parquet", ".pcap", ".pcapng",
    ".pem", ".pfx", ".pickle", ".pkl", ".pt", ".pth", ".rar",
    ".safetensors", ".sqlite", ".sqlite3", ".tar", ".tgz", ".tsv",
    ".xz", ".zip", ".zst",
})
IGNORE_PROBES = (
    "data/native_v4/__release_probe__.jsonl",
    "data/address_v1/__release_probe__.jsonl",
    "artifacts/checkpoints/__release_probe__.pt",
    "outputs/__release_probe__.json",
    ".env",
)
PRIVATE_USER_PATH = re.compile(
    r"(?<![\w./])/(?:home|Users)/[^\s/<>:\"'`\\]+(?:/|(?=[\s\"']|$))"
    r"|(?i:(?<!\w)[a-z]:[\\/]Users[\\/][^\\/\s<>:\"']+[\\/])"
)
PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
)
KNOWN_CREDENTIAL = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    r"gh[pousr]_[A-Za-z0-9]{36,}"
    r"|github_pat_[A-Za-z0-9_]{40,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{20,}"
    r"|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}"
    r")(?![A-Za-z0-9_])"
)
CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)(?<![\w])(?:[\"']?)(?:"
    r"api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
    r"secret[_-]?key|password|passwd|aws_secret_access_key|"
    r"aws_access_key_id|github_token|openai_api_key"
    r")(?:[\"']?)\s*[:=]\s*[\"']?([^\s\"'`#,;]+)"
)
EMAIL_ADDRESS = re.compile(
    r"(?i)(?<![\w.%+/@:-])[a-z0-9._%+-]+@"
    r"((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63})(?![\w-])"
)
RESERVED_EMAIL_DOMAINS = frozenset({"example.com", "example.net", "example.org"})
RESERVED_EMAIL_SUFFIXES = (".example", ".invalid", ".test", ".localhost")
IPV4_LITERAL = re.compile(r"(?<![\w.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?!\w|\.\w)")
IPV6_LITERAL = re.compile(
    r"(?<![\w:])(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F:.]*"
    r"(?:%[a-zA-Z0-9_.-]+)?(?![\w:])"
)
# Integer network definitions avoid embedding address literals in this scanner.
PRIVATE_IPV4_NETWORKS = tuple(ipaddress.IPv4Network(network) for network in (
    (0x0A000000, 8),    # RFC 1918
    (0xAC100000, 12),
    (0xC0A80000, 16),
    (0x64400000, 10),   # Shared carrier-grade NAT address space
    (0x7F000000, 8),    # Loopback
    (0xA9FE0000, 16),   # Link-local
))
PRIVATE_IPV6_NETWORKS = tuple(ipaddress.IPv6Network(network) for network in (
    (1, 128),          # Loopback; the unspecified address is not an identifier.
    (0xFC << 120, 7),  # Unique-local
    (0xFE80 << 112, 10),  # Link-local
    (0xFEC0 << 112, 10),  # Deprecated site-local
))
MAC_LITERAL = re.compile(
    r"(?i)(?<![\w:.-])(?:"
    r"[0-9a-f]{2}([:-])(?:[0-9a-f]{2}\1){4}[0-9a-f]{2}"
    r"|(?:[0-9a-f]{4}\.){2}[0-9a-f]{4})(?![\w:-]|\.\w)"
)
URL_AUTHORITY = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://([^\s/<>\"'`]+)")
URL_ENVIRONMENT_REFERENCE = re.compile(r"\$(?:[A-Za-z_]\w*|\{[A-Za-z_]\w*\})")
PLACEHOLDER_PREFIXES = (
    "example", "sample", "dummy", "fake", "placeholder", "redacted",
    "changeme", "change_me", "replace", "your_", "your-", "not_a_",
    "not-a-", "test_", "test-",
)


class CheckError(Exception):
    """A check could not be completed; messages must not contain file contents."""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a read-only Git command without including Git's stderr in reports."""
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise CheckError("git_unavailable") from exc


def candidate_paths(repo: Path) -> list[str]:
    result = git(repo, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise CheckError("not_git_repository")
    git_root = Path(result.stdout.decode("utf-8", "surrogateescape").rstrip("\r\n"))
    if git_root.resolve() != repo.resolve():
        raise CheckError("not_repository_root")
    result = git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if result.returncode:
        raise CheckError("git_candidate_query_failed")
    return sorted(set(
        item.decode("utf-8", "surrogateescape")
        for item in result.stdout.split(b"\0") if item
    ))


def safe_candidate(repo: Path, name: str) -> Path:
    """Reject unsafe paths and symlink components before opening any file."""
    relative = PurePosixPath(name)
    if (relative.is_absolute() or not relative.parts
            or any(part in {"..", ".git"} for part in relative.parts)):
        raise CheckError("unsafe_candidate_path")
    current = repo
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as exc:
            raise CheckError("missing_candidate") from exc
        except OSError as exc:
            raise CheckError("unreadable_candidate") from exc
        if stat.S_ISLNK(mode):
            raise CheckError("symlink")
    if not stat.S_ISREG(mode):
        raise CheckError("nonregular_candidate")
    return current


def looks_like_assigned_credential(value: str) -> bool:
    """Only flag long, varied literal values, not references or examples."""
    lowered = value.lower()
    if (len(value) < 20 or lowered.startswith(PLACEHOLDER_PREFIXES)
            or any(marker in value for marker in ("$", "<", ">", "(", ")", "{", "}"))):
        return False
    if len(set(value)) < 10:
        return False
    letters = any(char.isalpha() for char in value)
    digits = any(char.isdigit() for char in value)
    mixed_case = any(char.islower() for char in value) and any(char.isupper() for char in value)
    return letters and (digits or mixed_case)


def is_public_example_email(domain: str) -> bool:
    """Allow only reserved examples and GitHub's public noreply domain."""
    domain = domain.lower()
    return (
        domain.endswith(RESERVED_EMAIL_SUFFIXES)
        or any(domain == item or domain.endswith("." + item)
               for item in RESERVED_EMAIL_DOMAINS)
        or domain == "users.noreply.github.com"
        or domain.endswith(".users.noreply.github.com")
    )


def is_private_ip_literal(value: str) -> bool:
    """Validate addresses and restrict matches to internal-use network ranges."""
    try:
        address = ipaddress.ip_address(value.rstrip("."))
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        else:
            return any(address in network for network in PRIVATE_IPV6_NETWORKS)
    return any(address in network for network in PRIVATE_IPV4_NETWORKS)


def is_identifying_mac(value: str) -> bool:
    compact = value.replace(":", "").replace("-", "").replace(".", "").lower()
    return compact not in {"0" * 12, "f" * 12}


def has_url_authentication(authority: str) -> bool:
    """Flag literal URL userinfo, including credentials too short for token rules."""
    userinfo, separator, _host = authority.rpartition("@")
    if not separator or not userinfo:
        return False
    # Only complete environment references are exempt; dollar signs can occur
    # in real literal passwords and must not suppress their detection.
    return not all(URL_ENVIRONMENT_REFERENCE.fullmatch(part)
                   for part in userinfo.split(":"))


def text_findings(name: str, content: str) -> list[dict]:
    findings = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        categories = set()
        if PRIVATE_USER_PATH.search(line):
            categories.add("private_user_path")
        if PRIVATE_KEY.search(line):
            categories.add("private_key")
        if KNOWN_CREDENTIAL.search(line) or any(
            looks_like_assigned_credential(match.group(1))
            for match in CREDENTIAL_ASSIGNMENT.finditer(line)
        ):
            categories.add("credential")
        if any(not is_public_example_email(match.group(1))
               for match in EMAIL_ADDRESS.finditer(line)):
            categories.add("personal_email")
        if any(is_private_ip_literal(match.group())
               for pattern in (IPV4_LITERAL, IPV6_LITERAL)
               for match in pattern.finditer(line)):
            categories.add("private_ip_address")
        if any(is_identifying_mac(match.group()) for match in MAC_LITERAL.finditer(line)):
            categories.add("mac_address")
        if any(has_url_authentication(match.group(1))
               for match in URL_AUTHORITY.finditer(line)):
            categories.add("authenticated_url")
        for category in sorted(categories):
            findings.append({"path": name, "line": line_number, "category": category})
    return findings


def license_gate(repo: Path) -> dict:
    status = "manual_review_required"
    license_id = None
    try:
        path = safe_candidate(repo, "LICENSE")
        with path.open("rb") as handle:
            content = handle.read(MAX_FILE_BYTES + 1)
        if b"PENDING RIGHTS-HOLDER SELECTION" in content:
            status = "pending_rights_holder_selection"
        elif all(marker in content for marker in (
            b"Apache License", b"Version 2.0, January 2004",
            b"TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
            b"END OF TERMS AND CONDITIONS",
            b"http://www.apache.org/licenses/LICENSE-2.0",
        )):
            status = "selected_apache_2_0"
            license_id = "Apache-2.0"
    except (CheckError, OSError):
        status = "missing_or_unreadable"
    return {
        "status": "pending_manual_review",
        "license_file": "LICENSE",
        "license_notice_status": status,
        "license_id": license_id,
        "required_reviews": [
            "Rights holders must select or confirm the project license.",
            "Review third-party code, dataset, and checkpoint distribution rights.",
        ],
    }


def scan_repository(repo: Path) -> dict:
    """Return a deterministic report; findings never contain matched values."""
    repo = Path(repo).resolve()
    findings = []
    candidates = []
    checked_files = 0
    scanned_utf8_files = 0
    try:
        candidates = candidate_paths(repo)
    except CheckError as exc:
        findings.append({"path": ".", "line": None, "category": str(exc)})
    else:
        for name in candidates:
            try:
                path = safe_candidate(repo, name)
                checked_files += 1
                if path.suffix.lower() in PROHIBITED_SUFFIXES:
                    findings.append({"path": name, "line": None, "category": "prohibited_asset"})
                if path.stat().st_size > MAX_FILE_BYTES:
                    findings.append({"path": name, "line": None, "category": "oversized_file"})
                    continue
                with path.open("rb") as handle:
                    content = handle.read(MAX_FILE_BYTES + 1)
                if len(content) > MAX_FILE_BYTES:
                    findings.append({"path": name, "line": None, "category": "oversized_file"})
                    continue
                try:
                    decoded = content.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                scanned_utf8_files += 1
                findings.extend(text_findings(name, decoded))
            except CheckError as exc:
                findings.append({"path": name, "line": None, "category": str(exc)})
            except OSError:
                findings.append({"path": name, "line": None, "category": "unreadable_candidate"})
        for probe in IGNORE_PROBES:
            try:
                result = git(repo, "check-ignore", "--no-index", "--quiet", "--", probe)
                if result.returncode:
                    category = "ignore_policy_gap" if result.returncode == 1 else "git_ignore_query_failed"
                    findings.append({"path": probe, "line": None, "category": category})
            except CheckError as exc:
                findings.append({"path": probe, "line": None, "category": str(exc)})
    findings.sort(key=lambda item: (item["path"], item["line"] or 0, item["category"]))
    return {
        "schema_version": 1,
        "scope": "current_tracked_and_untracked_nonignored_working_tree",
        "candidate_count": len(candidates),
        "checked_file_count": checked_files,
        "scanned_utf8_file_count": scanned_utf8_files,
        "technical_ready": not findings,
        "public_license_approval": license_gate(repo),
        "release_approved": False,
        "policy": {
            "max_file_bytes": MAX_FILE_BYTES,
            "prohibited_suffixes": sorted(PROHIBITED_SUFFIXES),
            "exceptions": [],
            "ignore_probes": list(IGNORE_PROBES),
            "scans_git_history": False,
            "privacy_allowlist": {
                "reserved_email_domains": sorted(RESERVED_EMAIL_DOMAINS),
                "reserved_email_suffixes": list(RESERVED_EMAIL_SUFFIXES),
                "public_email_domain": "users.noreply.github.com (including subdomains)",
                "nonidentifying_mac_values": ["all-zero", "broadcast"],
                "upstream_notice_exemptions": [],
            },
        },
        "findings": findings,
        "limitations": [
            "Only the current working-tree candidate set is checked, not Git history or ignored files.",
            "Credential and personal-identifier detection is heuristic; manual review remains necessary.",
            "Content checks cover UTF-8 files within the size limit; other encodings are not scanned.",
            "Binary assets and PDF metadata or rendered content are not audited by this checker.",
            "Technical readiness is not permission to publish or an open-source license approval.",
        ],
    }


def write_report(repo: Path, relative_name: str, serialized: str) -> None:
    """Write an ignored JSON report without overwriting a release candidate."""
    relative = PurePosixPath(relative_name)
    if (relative.is_absolute() or ".." in relative.parts or ".git" in relative.parts
            or len(relative.parts) < 2 or relative.parts[0] != "outputs"
            or relative.suffix.lower() != ".json"):
        raise CheckError("report_path_must_be_a_relative_outputs_json_file")
    candidates = candidate_paths(repo)
    if relative.as_posix() in candidates:
        raise CheckError("report_path_is_a_release_candidate")
    result = git(repo, "check-ignore", "--no-index", "--quiet", "--", relative.as_posix())
    if result.returncode:
        raise CheckError("report_path_must_be_ignored")
    current = repo
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CheckError("report_path_contains_symlink")
    target = repo.joinpath(*relative.parts)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        raise CheckError("report_write_failed") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check tracked plus untracked, nonignored Git working-tree files against the "
            "local archival policy. Files larger than 5 MiB, prohibited dataset/checkpoint/"
            "capture/archive/key extensions, symlinks, private user paths, personal emails, "
            "internal IP and MAC literals, authenticated URLs, high-confidence credentials, "
            "and missing ignore rules fail the technical check. Reserved example emails, "
            "GitHub noreply addresses, and nonidentifying MAC constants are documented "
            "privacy exclusions, not asset exceptions. Git history is not scanned. "
            "Licensing always requires manual approval."
        ),
        epilog=(
            "Exit codes: 0 = technically ready (NOT approval to publish); "
            "1 = technical findings; 2 = invocation/report error. JSON is always printed "
            "for a completed scan. Findings contain relative paths, line numbers, and "
            "categories only, never matched content. No Git metadata is written."
        ),
    )
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1],
        help="Git repository root (default: the repository containing this script)",
    )
    parser.add_argument(
        "--report", nargs="?", const="outputs/release_check.json", metavar="PATH",
        help=("also write JSON to an ignored relative outputs/*.json path "
              "(default when specified without PATH: outputs/release_check.json)"),
    )
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    report = scan_repository(repo)
    serialized = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    sys.stdout.write(serialized)
    if args.report is not None:
        try:
            write_report(repo, args.report, serialized)
        except CheckError as exc:
            sys.stderr.write("Release report error: " + str(exc) + "\n")
            return 2
    return 0 if report["technical_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
