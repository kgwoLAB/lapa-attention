import unittest
import torch
from lapa.routing.pushforward import pushforward
from lapa.routing.fusion import route_prior
from .common import setup


class RoutingTests(unittest.TestCase):
    def test_pushforward_and_gradient(self):
        values = torch.tensor([[[.1, .2], [.3, .4]]], requires_grad=True)
        targets = torch.tensor([[[0, 1], [0, 2]]])
        result = pushforward(targets, values, 3)
        torch.testing.assert_close(result, torch.tensor([[.4, .2, .4]]))
        result.sum().backward()
        torch.testing.assert_close(values.grad, torch.ones_like(values))

    def test_neutral_prior(self):
        support = torch.tensor([[True, True, False, True]])
        output = route_prior(torch.zeros(1, 4), support, .02)
        torch.testing.assert_close(output["bias"], torch.zeros(1, 4))
        self.assertEqual(output["sink"].item(), 1)

    def test_mass_conservation(self):
        model, inputs, _ = setup()
        route = model(inputs)["route"]
        torch.testing.assert_close(route["real"].sum(-1) + route["sink"], torch.ones(2))
        torch.testing.assert_close(route["prior"].sum(-1), torch.ones(2))
        self.assertTrue((route["prior"] >= 0).all())
