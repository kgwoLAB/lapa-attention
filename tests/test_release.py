"""Release policy tests use temporary Git repositories, never the real index."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_release.py"
SPEC = importlib.util.spec_from_file_location("check_release", SCRIPT)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@unittest.skipUnless(shutil.which("git"), "Git is required for temporary-repository tests")
class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-check-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "--quiet")
        self.write(".gitignore", "data/native_v4/\ndata/address_v1/\nartifacts/checkpoints/\noutputs/\n.env\n")
        self.write("LICENSE", "LICENSE STATUS: PENDING RIGHTS-HOLDER SELECTION\n")
        self.write("README.md", "Small archival fixture.\n")
        self.git("add", ".gitignore", "LICENSE", "README.md")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def write(self, name, content):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def scan(self):
        return release.scan_repository(self.repo)

    def categories(self, report):
        return {finding["category"] for finding in report["findings"]}

    def test_clean_repository_is_technical_ready_but_never_license_approved(self):
        report = self.scan()
        self.assertTrue(report["technical_ready"])
        self.assertEqual(report["candidate_count"], 3)
        self.assertFalse(report["release_approved"])
        self.assertEqual(report["public_license_approval"]["status"], "pending_manual_review")
        self.assertEqual(
            report["public_license_approval"]["license_notice_status"],
            "pending_rights_holder_selection",
        )

    def test_license_text_cannot_automatically_approve_distribution(self):
        self.write("LICENSE", "MIT License\n")
        self.assertEqual(self.scan()["public_license_approval"]["status"], "pending_manual_review")

    def test_apache_selection_is_reported_but_never_approves_release(self):
        self.write("LICENSE", "\n".join((
            "Apache License", "Version 2.0, January 2004",
            "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
            "END OF TERMS AND CONDITIONS", "http://www.apache.org/licenses/LICENSE-2.0",
        )))
        report = self.scan()
        approval = report["public_license_approval"]
        self.assertEqual(approval["license_notice_status"], "selected_apache_2_0")
        self.assertEqual(approval["license_id"], "Apache-2.0")
        self.assertEqual(approval["status"], "pending_manual_review")
        self.assertFalse(report["release_approved"])

    def test_apache_title_alone_is_not_a_selected_license(self):
        self.write("LICENSE", "Apache License\nVersion 2.0, January 2004\n")
        approval = self.scan()["public_license_approval"]
        self.assertEqual(approval["license_notice_status"], "manual_review_required")
        self.assertIsNone(approval["license_id"])

    def test_untracked_files_are_checked_and_ignored_files_are_not(self):
        self.write("local.jsonl", "{}\n")
        self.write("data/native_v4/private.jsonl", "{}\n")
        report = self.scan()
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(report["findings"], [
            {"path": "local.jsonl", "line": None, "category": "prohibited_asset"},
        ])

    def test_tracked_files_still_checked_when_later_ignored(self):
        self.write("data/native_v4/tracked.jsonl", "{}\n")
        self.git("add", "--force", "data/native_v4/tracked.jsonl")
        report = self.scan()
        self.assertIn("prohibited_asset", self.categories(report))
        self.assertNotIn("ignore_policy_gap", self.categories(report))

    def test_all_prohibited_extensions_fail_without_exceptions(self):
        for suffix in release.PROHIBITED_SUFFIXES:
            self.write("asset" + suffix.upper(), b"fixture")
        report = self.scan()
        self.assertEqual(len(report["findings"]), len(release.PROHIBITED_SUFFIXES))
        self.assertEqual(self.categories(report), {"prohibited_asset"})
        self.assertEqual(report["policy"]["exceptions"], [])

    def test_size_limit_is_strictly_greater_than_five_mib(self):
        self.write("at-limit.txt", b"a" * release.MAX_FILE_BYTES)
        self.assertTrue(self.scan()["technical_ready"])
        self.write("over-limit.txt", b"a" * (release.MAX_FILE_BYTES + 1))
        report = self.scan()
        self.assertEqual(report["findings"], [
            {"path": "over-limit.txt", "line": None, "category": "oversized_file"},
        ])

    def test_private_user_paths_report_line_numbers_not_contents(self):
        private_paths = [
            "/" + "home" + "/fixture-person/research",
            "/" + "Users" + "/fixture-person/research",
            "C:" + "\\Users\\" + "fixture-person\\research",
        ]
        self.write("paths.txt", "Safe heading\n" + "\n".join(private_paths))
        report = self.scan()
        self.assertEqual([item["line"] for item in report["findings"]], [2, 3, 4])
        self.assertEqual(self.categories(report), {"private_user_path"})
        for private_path in private_paths:
            self.assertNotIn(private_path, json.dumps(report))

    def test_private_key_and_credentials_are_redacted(self):
        key_header = "-----BEGIN " + "PRIVATE KEY-----"
        token = "gh" + "p_" + "aBcDeF0123456789" * 3
        assigned_value = "AbCdEf0123456789GhIjKlMn"
        self.write("unsafe.txt", key_header + "\n" + token + "\nAPI_KEY=" + assigned_value)
        report = self.scan()
        self.assertEqual(self.categories(report), {"private_key", "credential"})
        self.assertEqual([item["line"] for item in report["findings"]], [1, 2, 3])
        serialized = json.dumps(report)
        for value in (key_header, token, assigned_value):
            self.assertNotIn(value, serialized)

    def test_placeholder_and_environment_reference_values_are_not_secrets(self):
        values = [
            "YOUR_API_KEY_HERE_123456789", "exampleAbCdEf0123456789",
            "${RESEARCH_API_KEY}", "os.environ.get('RESEARCH_API_KEY')",
            "<replace-with-your-key>", "012345678901234567890123456789",
        ]
        self.write("example.txt", "\n".join("API_KEY=" + value for value in values))
        self.assertTrue(self.scan()["technical_ready"])

    def test_personal_emails_are_redacted_including_fixture_and_license_paths(self):
        email = "fixture.person" + "@" + "mail-provider.com"
        for name in ("contacts.txt", "tests/fixture.txt", "LICENSES/unverified.txt"):
            self.write(name, "Contact\n" + email)
        report = self.scan()
        self.assertEqual(self.categories(report), {"personal_email"})
        self.assertEqual(len(report["findings"]), 3)
        self.assertEqual({item["line"] for item in report["findings"]}, {2})
        self.assertNotIn(email, json.dumps(report))

    def test_reserved_example_and_github_noreply_emails_are_allowed(self):
        domains = (
            "example.com", "example.net", "example.org", "docs.example.com",
            "example.invalid", "fixture.test", "fixture.example", "fixture.localhost",
            "users.noreply.github.com", "public.users.noreply.github.com",
        )
        self.write("examples.txt", "\n".join("fixture+123" + "@" + domain for domain in domains))
        self.assertTrue(self.scan()["technical_ready"])

    def test_similarly_named_real_email_domains_are_not_exempt(self):
        domains = (
            "notexample.com", "example.com.real-domain.com",
            "users.noreply.github.com.real-domain.com", "noreply.github.com",
        )
        self.write("contacts.txt", "\n".join("fixture" + "@" + domain for domain in domains))
        report = self.scan()
        self.assertEqual(len(report["findings"]), len(domains))
        self.assertEqual(self.categories(report), {"personal_email"})

    def test_internal_ipv4_and_ipv6_literals_are_validated_and_redacted(self):
        addresses = [
            "10." + "42.3.9", "172." + "16.20.30", "192." + "168.42.9",
            "100." + "64.2.3", "127." + "0.0.1", "169." + "254.2.3",
            "fd12:" + "3456::9", "fe80:" + ":1234%eth0", ":" + ":1",
            "::ffff:" + "192." + "168.42.9",
        ]
        self.write("network.txt", "Heading\n" + "\n".join(addresses))
        report = self.scan()
        self.assertEqual(self.categories(report), {"private_ip_address"})
        self.assertEqual([item["line"] for item in report["findings"]], list(range(2, 12)))
        for address in addresses:
            self.assertNotIn(address, json.dumps(report))

    def test_public_documentation_invalid_ips_and_versions_are_not_private_ips(self):
        values = [
            "192." + "0.2.8", "198." + "51.100.9", "203." + "0.113.7",
            "2001:" + "db8::9", "8." + "8.8.8", "10." + "999.3.4",
            "172." + "32.0.1", "version v10." + "2.3.4", "version 1.2.3",
            "range 10." + "2.3.4.5", "slice[::]",
        ]
        self.write("examples.txt", "\n".join(values))
        self.assertTrue(self.scan()["technical_ready"])

    def test_mac_literals_are_redacted_and_nonidentifying_constants_are_allowed(self):
        addresses = [
            "02:3a:" + "4b:5c:6d:7e", "12-34-" + "56-78-9a-bc",
            "023a." + "4b5c.6d7e",
        ]
        self.write("network.txt", "\n".join(addresses))
        self.write("constants.txt", ":".join(["00"] * 6) + "\n" + "-".join(["ff"] * 6))
        report = self.scan()
        self.assertEqual(self.categories(report), {"mac_address"})
        self.assertEqual([item["line"] for item in report["findings"]], [1, 2, 3])
        for address in addresses:
            self.assertNotIn(address, json.dumps(report))

    def test_sentence_punctuation_does_not_hide_network_identifiers(self):
        self.write("network.txt", "\n".join((
            "The host is " + "10." + "42.3.9.",
            "The host is " + "fd12:" + "3456::9.",
            "The interface is " + "02:3a:" + "4b:5c:6d:7e.",
        )))
        report = self.scan()
        self.assertEqual([item["line"] for item in report["findings"]], [1, 2, 3])
        self.assertEqual(self.categories(report), {"private_ip_address", "mac_address"})

    def test_authenticated_urls_are_redacted_even_with_short_or_encoded_passwords(self):
        values = [
            "https://" + "fixture:pw" + "@" + "example.invalid/path",
            "postgresql://" + "fixture:p%40ss" + "@" + "example.invalid/db",
            "https://" + "fixture:$3cr3t" + "@" + "example.invalid/path",
            "https://" + "opaque-token" + "@" + "example.invalid/path",
        ]
        self.write("urls.txt", "\n".join(values))
        report = self.scan()
        self.assertEqual(self.categories(report), {"authenticated_url"})
        self.assertEqual([item["line"] for item in report["findings"]], [1, 2, 3, 4])
        for value in values:
            self.assertNotIn(value, json.dumps(report))

    def test_public_urls_and_environment_userinfo_are_not_authentication_literals(self):
        self.write("urls.txt", "\n".join((
            "https://github.com/example/project", "https://arxiv.org/abs/2405.18719",
            "https://" + "${RELEASE_USER}:${RELEASE_PASSWORD}" + "@" + "example.invalid/path",
        )))
        self.assertTrue(self.scan()["technical_ready"])

    def test_scanner_source_and_regression_fixtures_do_not_self_trigger(self):
        for name, path in (("scanner.py", SCRIPT), ("regressions.py", Path(__file__))):
            self.write(name, path.read_text(encoding="utf-8"))
        self.assertTrue(self.scan()["technical_ready"])

    def test_symlink_is_rejected_without_reading_target(self):
        target = self.write("outputs/target.txt", "Do not read this target.\n")
        try:
            (self.repo / "link.txt").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        self.assertEqual(self.scan()["findings"], [
            {"path": "link.txt", "line": None, "category": "symlink"},
        ])

    def test_symlink_parent_is_rejected(self):
        self.write("nested/source.txt", "fixture")
        self.git("add", "nested/source.txt")
        (self.repo / "nested/source.txt").unlink()
        (self.repo / "nested").rmdir()
        (self.repo / "outputs").mkdir()
        try:
            (self.repo / "nested").symlink_to(self.repo / "outputs", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        self.assertIn("symlink", self.categories(self.scan()))

    def test_missing_tracked_file_fails(self):
        (self.repo / "README.md").unlink()
        self.assertIn("missing_candidate", self.categories(self.scan()))

    def test_ignore_gaps_are_reported_with_probe_paths(self):
        self.write(".gitignore", "")
        report = self.scan()
        self.assertEqual(self.categories(report), {"ignore_policy_gap"})
        self.assertEqual(
            {item["path"] for item in report["findings"]}, set(release.IGNORE_PROBES),
        )

    def test_non_utf8_input_does_not_crash_and_limitation_is_disclosed(self):
        self.write("binary.dat", b"\xff\xfe\x80")
        report = self.scan()
        self.assertTrue(report["technical_ready"])
        self.assertEqual(report["checked_file_count"], 4)
        self.assertEqual(report["scanned_utf8_file_count"], 3)
        self.assertTrue(any("UTF-8" in item for item in report["limitations"]))
        self.assertTrue(any("PDF" in item for item in report["limitations"]))

    def test_json_report_is_deterministic_and_does_not_change_git_index(self):
        index_before = (self.repo / ".git/index").read_bytes()
        before = self.scan()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = release.main(["--repo", str(self.repo), "--report"])
        self.assertEqual(result, 0)
        self.assertEqual(before, json.loads(stdout.getvalue()))
        self.assertEqual(
            stdout.getvalue(), (self.repo / "outputs/release_check.json").read_text(encoding="utf-8"),
        )
        self.assertEqual(before, self.scan())
        self.assertEqual(index_before, (self.repo / ".git/index").read_bytes())

    def test_cli_returns_nonzero_for_technical_findings(self):
        self.write("capture.pcap", b"fixture")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(release.main(["--repo", str(self.repo)]), 1)

    def test_report_path_cannot_overwrite_source_or_escape_repository(self):
        for name in ("README.md", "../release.json", ".git/report.json", "/tmp/release.json"):
            with self.subTest(name=name), self.assertRaises(release.CheckError):
                release.write_report(self.repo, name, "{}\n")
        self.assertEqual((self.repo / "README.md").read_text(), "Small archival fixture.\n")

    def test_report_path_cannot_overwrite_tracked_ignored_file(self):
        self.write("outputs/tracked.json", "preserve me")
        self.git("add", "--force", "outputs/tracked.json")
        with self.assertRaises(release.CheckError):
            release.write_report(self.repo, "outputs/tracked.json", "{}\n")
        self.assertEqual((self.repo / "outputs/tracked.json").read_text(), "preserve me")

    def test_non_repository_returns_structured_failure(self):
        unrelated = self.repo / "unrelated"
        unrelated.mkdir()
        self.assertIn("not_repository_root", self.categories(release.scan_repository(unrelated)))


if __name__ == "__main__":
    unittest.main()
