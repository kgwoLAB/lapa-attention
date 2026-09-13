# Running and reproducing

## Portable checks

```bash
python -m unittest discover -s tests -t . -v
python examples/compare_on_off.py
python scripts/prepare_research_archive.py --verify
python scripts/check_release.py --report
```

The examples now default to fixed numeric tensors and do not require the
Git-ignored data. They check the API of untrained models, not benchmark accuracy.

## Optional local-data workflow

The following commands require separately approved real datasets in the local
`data/native_v4/` directory. They do not work from a code-only clone until those
assets are supplied through an approved channel.

```bash
python scripts/train.py --attention sdpa --lapa on --steps 2 --output outputs/sdpa_smoke
python scripts/evaluate.py --checkpoint outputs/sdpa_smoke/model.pt \
  --max-messages 2 --output outputs/sdpa_smoke_eval
```

The unit tests use small numeric tensors, not a synthetic-protocol benchmark.
The optional local-data CLI smoke workflow uses real native records. A capped
evaluation is marked partial and never gets a four-protocol macro unless all
four protocol groups are present. Smoke metrics are functional evidence only.

## Historical checkpoints

The six locally preserved, Git-ignored checkpoints are the first predeclared seed 2026090720,
not a score-selected seed. Conversion preserves every state-dict tensor and
requires explicit backbone and mode. Existing metrics/thresholds accompany the
raw checkpoints where available. `artifacts/reference/native_v4/SUMMARY.json`
retains the historical ten-seed aggregate and is not recomputed from six models.

Use a historical checkpoint's recorded development-selected threshold to replay
its field output. The new default threshold .5 is a fixed CLI convenience, not
the historical threshold-selection result. Do not tune on evaluation records.

The initial package trainer retains balanced per-protocol batches and common on/off joint
supervision, but its initialization profile is a package port. New training
runs have their own seeds, checksums and curves and do not replace historical
results. `task=endpoint` is positive ordinal coordinate-NLL training, not the
older factorial's byte-NLL + coordinate-NLL objective.

This initial package default is not the corrected Off=endpoint-NLL-only training
policy used in the later archived comparisons. Consult each study's loss and
training snapshot; do not relabel a default package run as a historical result.
The v18 four-factor encoder is a separate research snapshot, not the default
`LapaModel` class. All archived training requires the original private lineage,
data and contracts; [the archive](../research_archive/README.md) describes what
can and cannot be reproduced from the public candidate.

No packet capture, network replay or external upload is performed by any normal
training/evaluation/example command. No pretrained online model is downloaded.
