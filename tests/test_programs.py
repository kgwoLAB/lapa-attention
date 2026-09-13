import unittest
import torch
from lapa import Program, ProgramBank, native_bank
from lapa.programs.executor import execute
from lapa.programs.decode import decode


class ProgramTests(unittest.TestCase):
    def run_program(self, values, program):
        data = torch.tensor([values], dtype=torch.long)
        return execute(ProgramBank((program,)), data, torch.ones_like(data, dtype=torch.bool))

    def test_bank_order(self):
        bank = native_bank()
        self.assertEqual(len(bank), 68)
        self.assertEqual(bank.programs[5], Program(1, "big", "field_end_forward", signed=True))
        self.assertEqual(bank.fingerprint, native_bank().fingerprint)

    def test_endian(self):
        data = torch.tensor([[1, 2, 3]])
        observed = torch.ones_like(data, dtype=torch.bool)
        self.assertEqual(decode(data, observed, 2, "big")[0][0, 0], 258)
        self.assertEqual(decode(data, observed, 2, "little")[0][0, 0], 513)
        self.assertFalse(decode(data, observed, 2, "big")[1][0, -1])

    def test_length_end(self):
        result = self.run_program([3, 0, 0, 0], Program(1, base="field_end_forward"))
        self.assertTrue(result.valid[0, 0, 0])
        self.assertEqual(result.target[0, 0, 0], 4)

    def test_signed_relative(self):
        result = self.run_program([0, 0, 254, 0], Program(1, base="field_end_forward", signed=True))
        self.assertEqual(result.target[0, 2, 0], 1)
        self.assertTrue(result.valid[0, 2, 0])

    def test_mask_guard(self):
        p = Program(2, mask=0x3fff, guard_mask=0xc000, guard_value=0xc000)
        result = self.run_program([192, 2, 0, 0], p)
        self.assertEqual(result.target[0, 0, 0], 2)
        self.assertTrue(result.valid[0, 0, 0])
        self.assertFalse(self.run_program([0, 2, 0, 0], p).valid[0, 0, 0])

    def test_null_not_sink(self):
        result = self.run_program([4, 0, 0, 0, 0, 0], Program(2, "little", "offset_with_next_length"))
        self.assertTrue(result.null[0, 0, 0])
        self.assertEqual(result.target[0, 0, 0], 7)

    def test_out_of_range_is_invalid_candidate(self):
        result = self.run_program([255, 0], Program(1))
        self.assertTrue(result.candidate_mask[0, 0, 0])
        self.assertFalse(result.valid[0, 0, 0])
