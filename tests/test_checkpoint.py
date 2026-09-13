from pathlib import Path
import tempfile
import unittest
import torch
from lapa.training.checkpoint import save_checkpoint, load_checkpoint
from .common import setup


class CheckpointTests(unittest.TestCase):
    def test_round_trip(self):
        model, inputs, _ = setup("tape")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pt"
            save_checkpoint(path, model, {"seed": 19})
            loaded, meta = load_checkpoint(path)
            self.assertEqual(meta["seed"], 19)
            self.assertTrue(torch.equal(model(inputs)["final"], loaded(inputs)["final"]))
            with self.assertRaises(FileExistsError):
                save_checkpoint(path, model)

    def test_bank_tampering_rejected(self):
        model, _, _ = setup()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pt"
            save_checkpoint(path, model)
            payload = torch.load(path, weights_only=True)
            payload["bank_fingerprint"] = "changed"
            altered = Path(folder) / "altered.pt"
            torch.save(payload, altered)
            with self.assertRaises(ValueError):
                load_checkpoint(altered)
