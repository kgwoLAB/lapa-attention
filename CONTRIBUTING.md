# Collaboration

Active model development is paused. Preservation fixes, corrections to reported
results, and documentation improvements should retain the original evidence.
A new research direction belongs in a clearly separated experiment lineage;
do not rewrite an archived unsuccessful experiment into a success claim.

1. Work on a topic branch; use a pull request for changes to model/data contracts.
2. Run `python -m unittest discover -s tests -t . -v` before requesting review.
3. Keep model inputs separate from evaluator/training labels. Do not pass protocol,
   gold source, field count, program ID or target into `LapaModel.forward`.
4. Record changes to ordered program banks and checkpoint schema explicitly.
5. Preserve off-mode no-executor behavior and all four attention options.
6. Do not silently replace compact CoPE/TAPE with another implementation under
   the same checkpoint/profile name.
7. Do not overwrite original data, split identities or published result files.
8. Commit small code/config/docs changes. Keep raw data, credentials and large
   checkpoints out of public commits until permissions and privacy are reviewed.

The repository is modular for ownership by attention, routing/execution, and
data/evaluation contributors. The interface in `types.py` is the shared contract.
No particular collaborator or external account is assumed by these templates.

Project-controlled contributions are submitted under Apache-2.0. Preserve
third-party notices and license scope; do not add unlicensed upstream code or
raw research data under an assumed blanket project license. Use a GitHub
noreply commit email if your personal address should not be published.
