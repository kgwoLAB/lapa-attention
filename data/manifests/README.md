# Local asset provenance

The original `assets.json` manifest remains on the workstation, Git-ignored,
alongside the exact locally preserved dataset and checkpoint copies. A clone
does not include that raw-asset bundle or the manifest-bound reference files.

After obtaining the complete approved local bundle, `scripts/verify_assets.py`
can verify its hashes. Do not invent a replacement manifest or silently alter
payloads/splits to make a historical run appear reproduced.

The separate public-candidate research export has its own
[`research_archive/MANIFEST.json`](../../research_archive/MANIFEST.json).
Its hashes cover curated code, reports, aggregate statistics and figures, not
the omitted training/evaluation raw assets. Neither manifest grants a license.
