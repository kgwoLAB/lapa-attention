# Public Release Checklist

Target: [kgwoLAB/lapa-attention](https://github.com/kgwoLAB/lapa-attention).
On 2026-09-13, the user requested a push to this repository, license selection,
and removal of sensitive information. Technical checks are not a complete
security, privacy, or legal audit. Earlier local preparation records are
preserved in [WORK_LOG.md](../WORK_LOG.md).

## 1. Licensing and distribution scope

- [x] Confirmed before initial publication that the specified repository was empty, public, and writable.
- [x] Selected [Apache-2.0](../LICENSE) for project-owned code and documentation.
- [x] Preserved the officially verified TAPE MIT and Apache-2.0 notices and complete texts in [LICENSES](../LICENSES/README.md).
- [x] Added attribution/modification comments only to three position-related modules and documented that historical file hashes no longer describe those annotated files.
- [x] Disclosed that CoPE is a local equation-level implementation and that an official software license was not verified.
- [x] Excluded raw data, weights, per-packet results, and local verification assets from publication.
- [ ] Finalize paper authorship and publication metadata: citation information remains a draft; no paper or DOI was invented.
- [ ] Approve dataset/weight redistribution: these are not part of this release and require separate review.

## 2. Sensitive information and history separation

- [x] Scanned text for personal home paths, emails, internal IP/MAC addresses, credentials, and authenticated URLs.
- [x] Replaced personal workspace paths and removed the previous private-repository address from public documentation.
- [x] Inspected metadata/chunks in 29 PNG files and XML/metadata in 29 SVG files.
- [x] Inspected extracted text, metadata, attachments, actions, and compressed streams in 15 PDFs covering all 41 pages.
- [x] Preserved legitimate paper citations and copyright notices; did not remove aggregate values or hashes by misclassifying them as credentials.
- [x] Selected a public GitHub noreply commit address instead of a personal email.
- [x] Preserved previous Git history in a local-only backup and confirmed the old commit was absent from the new object database.
- [x] Rechecked all 324 tracked files prepared for the new initial commit.

## 3. Research records and functional verification

- [x] Distinguished v18's 24 new models/600 updates from its 96 reused controls, preserving failures and limitations.
- [x] Kept correct-destination probability, NLL, Hit@1, F1, and the source-contribution lower bound distinct.
- [x] Left original study directories, datasets, and weights unchanged.
- [x] Documented the historical scripts' dependence on private assets and their original environment.
- [x] Rechecked all 209 archive hashes and numerical preservation after updating publication license notices.
- [x] Verified 84 unit tests, three default examples, and wheel build/isolated installation across eight conditions.
- [x] Passed the final candidate scan and staged-diff checks.

## 4. Publication and remote verification

- [x] The publication request covered the new sanitized public snapshot, not changes to the previous private remote.
- [x] Pushed a new initial commit to the target main branch without force.
- [x] Verified that remote initial commit `3667766` has no parents, matches all 324 file blobs, and uses the noreply identity.
- [x] Confirmed that the initial public commit's [GitHub CI](https://github.com/kgwoLAB/lapa-attention/actions/runs/34745839581) succeeded; remote CI success is distinct from local test success.
- [ ] Enable GitHub's read-only Archive setting: not requested and therefore not performed.

Automated checks may miss sensitive information. The unverified official CoPE
software license is a separate limitation. This checklist is not a guarantee
that every privacy or third-party rights issue has been resolved.
