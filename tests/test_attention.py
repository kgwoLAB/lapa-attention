import unittest
import torch
from lapa.attention.sdpa import SDPABackend
from lapa.attention.rope import RoPEBackend, rope_state
from lapa.training.losses import joint_loss
from .common import setup


class AttentionTests(unittest.TestCase):
    def test_sdpa_equation(self):
        q = torch.randn(2, 2, 3, 8)
        k = torch.randn(2, 2, 5, 8)
        scores, _ = SDPABackend().logits(q, k)
        torch.testing.assert_close(scores, q @ k.transpose(-2, -1) / 8 ** .5)

    def test_rope_rectangular(self):
        q, k = torch.randn(2, 2, 1, 8), torch.randn(2, 2, 5, 8)
        state = rope_state(2, 2, torch.arange(-1, 5), 8, q.dtype, q.device)
        scores, _ = RoPEBackend().logits(q, k, state=state)
        self.assertEqual(scores.shape, (2, 2, 1, 5))

    def test_eight_modes_forward_backward(self):
        for mode in ("sdpa", "rope", "cope", "tape"):
            for enabled in (False, True):
                with self.subTest(mode=mode, enabled=enabled):
                    model, inputs, labels = setup(mode, enabled)
                    output = model(inputs)
                    loss, _ = joint_loss(output, labels)
                    loss.backward()
                    self.assertTrue(torch.isfinite(loss))
                    self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))
                    torch.testing.assert_close(output["final"].sum(-1), torch.ones(2))
                    self.assertEqual(output["final"][1, 16:24].sum().item(), 0)

    def test_tape_state_is_transported(self):
        model, inputs, _ = setup("tape")
        before = model(inputs)["tape_position"]
        with torch.no_grad():
            model.host.blocks[0].tape_transform.weight.fill_(.1)
        after = model(inputs)["tape_position"]
        self.assertFalse(torch.equal(before[0], after[0]))
