import unittest
import torch
from lapa.attention.masks import masked_softmax, allowed_mask
from .common import setup


class MaskTests(unittest.TestCase):
    def test_empty_mask_is_zero(self):
        output = masked_softmax(torch.randn(2, 5), torch.zeros(2, 5, dtype=torch.bool))
        torch.testing.assert_close(output, torch.zeros(2, 5))

    def test_causal_mask_helper(self):
        mask = allowed_mask(torch.ones(1, 3, dtype=torch.bool), causal=True)
        self.assertFalse(mask[0, 0, 0, 2])
        self.assertTrue(mask[0, 0, 2, 0])

    def test_nonprefix_rejected(self):
        model, inputs, _ = setup()
        inputs.observed[0, 2] = False
        with self.assertRaises(ValueError):
            model(inputs)

    def test_invalid_byte_rejected(self):
        model, inputs, _ = setup()
        inputs.data[0, 0] = 256
        with self.assertRaises(ValueError):
            model(inputs)

    def test_padding_has_no_probability(self):
        model, inputs, _ = setup()
        self.assertEqual(model(inputs)["final"][1, 16:24].sum().item(), 0)
