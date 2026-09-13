import unittest
from unittest.mock import patch
import torch
from .common import setup


class OnOffTests(unittest.TestCase):
    def test_disabled_never_executes(self):
        model, inputs, _ = setup(enabled=False)
        with patch("lapa.routing.router.execute", side_effect=AssertionError("executor must not run")):
            output = model(inputs)
        self.assertIs(output["base"], output["final"])
        self.assertIsNone(output["route"])

    def test_shared_baseline_four_modes(self):
        model, inputs, _ = setup()
        for mode in ("sdpa", "rope", "cope", "tape"):
            off = model(inputs, attention=mode, lapa_enabled=False)
            on = model(inputs, attention=mode, lapa_enabled=True)
            self.assertTrue(torch.equal(off["base"], on["base"]))

    def test_labels_not_accepted(self):
        model, inputs, labels = setup()
        with self.assertRaises(TypeError):
            model(labels)

    def test_same_parameter_inventory(self):
        on, _, _ = setup(enabled=True)
        off, _, _ = setup(enabled=False)
        self.assertEqual(list(on.state_dict()), list(off.state_dict()))
        self.assertTrue(all(torch.equal(v, off.state_dict()[k]) for k, v in on.state_dict().items()))
